# these are the endpoints provided in the original issac-sas implementation
from fastapi import APIRouter

import ics.isaac_sas as isaac_sas
from ics.models import LanguageDataRequest, PredictFromLanguageDataResponse, ModelIdResponse

router = APIRouter()

@router.get("/fetchStoredModels", response_model=ModelIdResponse)
def get_fetch_stored_models():
    return {"modelIds": isaac_sas.fetch_stored_models()}

@router.post("/trainFromAnswers")
def post_train_from_answers(req: LanguageDataRequest):
    return isaac_sas.train_from_answers(req)

@router.post("/predictFromAnswers", response_model=PredictFromLanguageDataResponse)
def post_predict_from_answers(req: LanguageDataRequest):
    return isaac_sas.predict_from_answers(req)

@router.get("/wipe_models")
def get_wipe_models():
    return isaac_sas.wipe_models()
