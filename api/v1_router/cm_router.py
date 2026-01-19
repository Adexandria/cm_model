from fastapi import APIRouter, Depends, Body, UploadFile
import pandas
from api.models.user import PredictionExplanationResponse, PredictionResponse, TrainModelRequest, TrainModelResponse
from sqlalchemy.orm import Session
from database import get_db
from pipeline import model_pipeline
import pandas as pd
from api import auth
from api import crud
from inference import inference, inference_explanation
from blob.push_blob import upload_blob
from exception import unauthorizedException, serverErrorException

router = APIRouter(
    tags=["content moderation"],
    responses={404: {"description": "Not found"}},
)

@router.post("/train-model",response_model=TrainModelResponse, responses={401: {"description": "Unauthorized"}, 500: {"description": "Server Error"}})
async def train_model(model_name: str, file : UploadFile,hyperparameters: TrainModelRequest= Depends(TrainModelRequest.as_form()), is_authenticated: bool = Depends(auth.authenticate_user_by_token)):
    """Endpoint to trigger model training."""
    try:
        if(not is_authenticated):
            raise unauthorizedException()

        data = pd.read_csv(file.file)

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
        print(e)
        raise serverErrorException(message=str(e))
    
@router.post("/predict",response_model=PredictionResponse, responses={401: {"description": "Unauthorized"}, 500: {"description": "Server Error"}})
async def predict_model_content(contents: list[str], model_name: str = "logistic_regression", is_authenticated: bool = Depends(auth.authenticate_user_by_token)):
    """Endpoint to predict content categories and generate explanations."""
    try:
        if(not is_authenticated):
            raise unauthorizedException()
    
        labels, predictions = inference(contents, model_path=f"{model_name}_model.pth")

        return PredictionResponse(
            labels=labels,
            predictions=predictions
        )
    except Exception as e:
        raise serverErrorException(message=str(e))

@router.post("/explain", response_model=PredictionExplanationResponse, responses={401: {"description": "Unauthorized"}, 500: {"description": "Server Error"}})
async def explain_model_content(contents: list[str], predicted_categories: list[str], is_authenticated: bool = Depends(auth.authenticate_user_by_token)):
    """Endpoint to generate explanations for predicted categories."""
    try:
        if(not is_authenticated):
            raise unauthorizedException()
    
        explanation = inference_explanation(input_texts=contents, labels=predicted_categories)
        return PredictionExplanationResponse(
            explanation=explanation
        )
    except Exception as e:
        raise serverErrorException(message=str(e))


