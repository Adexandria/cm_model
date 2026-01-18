import os
from fastapi import APIRouter, Cookie,UploadFile
from api.models.user import PredictionExplanationRequest, TrainModelRequest,DbUser, PredictionRequest, TrainModelResponse
from sqlalchemy.orm import Session
from database import get_db
from api import crud, auth
from fastapi import Depends
from exception import unauthorizedException, notFoundException, serverErrorException
import pandas as pd
from pipeline import model_pipeline
from blob.push_blob import upload_blob

from inference import inference, inference_explanation

router = APIRouter(
    tags=["content moderation"],
    responses={404: {"description": "Not found"}},
)

@router.post("/train-model", response_model=TrainModelResponse, responses={400: {"description": "Bad Request"}, 500: {"description": "Server Error"}})
async def train_model(model_name: str, file : UploadFile, train_model_request: TrainModelRequest = Depends(TrainModelRequest.as_form()), current_user: DbUser = Depends(auth.get_current_admin)):
    """Endpoint to trigger model training."""
    try:
        data = pd.read_csv(file.file)
        kwargs = {
            "out_path": "processed_data.csv",
            "model_path": f"{model_name}_model.pth",
            "n_estimators": train_model_request.n_estimators,
            "max_depth": train_model_request.max_depth,
            "class_weight": train_model_request.class_weight.value,
            "random_state": train_model_request.random_state,
            "use_augmentation": train_model_request.use_augmentation
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
async def predict_content(request: PredictionRequest, model_name: str = "logistic_regression", user: DbUser = Depends(auth.get_user_by_api_key)):
    """Endpoint to predict content categories and generate explanations."""
    try:
        labels, _ = inference(request.contents, model_path=f"{model_name}_model.pth")
        return {
            "labels": labels
        }
    except Exception as e:
        raise serverErrorException(message=str(e))

@router.post("/explain", responses={401: {"description": "Unauthorized"}, 500: {"description": "Server Error"}})
async def explain_content(request: PredictionExplanationRequest, user: DbUser = Depends(auth.get_user_by_api_key)):
    """Endpoint to explain content based on predicted categories."""
    try:
        explanations = inference_explanation(input_texts=request.contents, labels=request.predicted_categories, use_flagged_prompt=True)

        return {
            "explanations": explanations
        }
    except Exception as e:
        raise serverErrorException(message=str(e))
    

