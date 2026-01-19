import os
from fastapi import APIRouter, Cookie, Request,UploadFile
from api.models.user import PredictionExplanationRequest, TrainModelRequestWithValidation,DbUser, PredictionRequest, TrainModelResponse
from sqlalchemy.orm import Session
from database import get_db
from api import crud, auth, dataset_validator
from fastapi import Depends
from exception import badRequestException, notFoundException, serverErrorException
import pandas as pd
from pipeline import model_pipeline
from blob.push_blob import upload_blob

from inference import inference, inference_explanation
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(
    tags=["content moderation"],
    responses={404: {"description": "Not found"}},
)

limiter = Limiter(key_func=get_remote_address)


@router.post("/train-model", response_model=TrainModelResponse, responses={400: {"description": "Bad Request"}, 500: {"description": "Server Error"}})
@limiter.limit("5/minute")
async def train_model(request: Request, model_name: str, file : UploadFile, hyperparameters: TrainModelRequestWithValidation = Depends(TrainModelRequestWithValidation.as_form()), current_user: DbUser = Depends(auth.get_current_admin)):
    """Endpoint to trigger model training."""
    try:
        if not file.filename.lower().endswith(".csv"):
            raise notFoundException(message="Only CSV files are supported.")

        if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
            raise notFoundException(message="Invalid content type")
        
        contents = await file.read()

        is_valid, validation_message = dataset_validator.validate_dataset(contents)
        if not is_valid:
            return badRequestException(message=validation_message)

        data = pd.read_csv("sanitized_dataset.csv")
        kwargs = {
            "out_path": "processed_data.csv",
            "model_path": f"{model_name}_model.pth",
            "n_estimators": hyperparameters.n_estimators,
            "max_depth": hyperparameters.max_depth,
            "class_weight": hyperparameters.class_weight.value,
            "random_state": hyperparameters.random_state,
            "use_augmentation": hyperparameters.use_augmentation
            }
        
        accuracy, report = model_pipeline(data=data, **kwargs)
        url = upload_blob(report, blob_name=f"{model_name}_report.json")

        return TrainModelResponse(
                    message="Model training initiated successfully",
                    report_url=url,
                    accuracy=accuracy,
                    model_path=f"{model_name}_model.pth"
                    )
    except Exception as e:
        raise serverErrorException(message=str(e))
        

@router.post("/api-key", responses={ 500: {"description": "Server Error"}})
async def generate_api_key(current_user: DbUser = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Generate an API key for the current user."""
    try:
        api_key = auth.generate_api_key()
        crud.set_user_api_key(db, current_user.id, api_key)
        return {
            "message": "API key generated successfully, please store it securely as it will not be shown again.",
            "api_key": api_key
        }
    except Exception as e:
        raise serverErrorException(message=str(e))
    

@router.get("/api-keys", responses={500: {"description": "Server Error"}})
async def get_api_keys(current_user: DbUser = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Retrieve all API keys for the current user."""
    try:
        api_keys = crud.get_api_keys_by_user(db, current_user.id)
        return {
            "api_keys": api_keys
        }
    except Exception as e:
        raise serverErrorException(message=str(e))
    

@router.delete("/api-keys", responses={404: {"description": "Not Found"}, 500: {"description": "Server Error"}})
async def delete_api_key(api_key_name: str, current_user: DbUser = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Delete an API key for the current user."""
    try:
        
        api_key = crud.get_authenticated_user_by_api_key(db, current_user.id, api_key_name)
        if not api_key:
            raise notFoundException(message="API key not found.") 
        crud.delete_api_key(db, current_user.id, api_key_name)
        return {
            "message": "API key deleted successfully."
        }
    except Exception as e:
        raise serverErrorException(message=str(e))


@router.post("/predict",responses={401: {"description": "Unauthorized"}, 500: {"description": "Server Error"}})
@limiter.limit("5/minute")
async def predict_content(request: Request, prediction_request: PredictionRequest, model_name: str = "logistic_regression", user: DbUser = Depends(auth.get_user_by_api_key)):
    """Endpoint to predict content categories and generate explanations."""
    try:
        labels, _ = inference(prediction_request.contents, model_path=f"{model_name}_model.pth")
        return {
            "labels": labels
        }
    except Exception as e:
        raise serverErrorException(message=str(e))

@router.post("/explain", responses={401: {"description": "Unauthorized"}, 500: {"description": "Server Error"}})
@limiter.limit("5/minute")  
async def explain_content(request: Request, prediction_explanation_request: PredictionExplanationRequest, user: DbUser = Depends(auth.get_user_by_api_key)):
    """Endpoint to explain content based on predicted categories."""
    try:
        explanations = inference_explanation(input_texts=prediction_explanation_request.contents, labels=prediction_explanation_request.predicted_categories, use_flagged_prompt=True)

        return {
            "explanations": explanations
        }
    except Exception as e:
        raise serverErrorException(message=str(e))
    

