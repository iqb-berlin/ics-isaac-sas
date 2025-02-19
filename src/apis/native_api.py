# these are the endpoints provided in the original issac-sas implementation
from fastapi import APIRouter
from isaac_sas import core
from isaac_sas.models import LanguageDataRequest, PredictFromLanguageDataResponse, ModelIdResponse

router = APIRouter()

@router.get("/fetchStoredModels", response_model=ModelIdResponse)
def get_fetch_stored_models():
    return core.fetch_stored_models()

@router.post("/trainFromAnswers")
def post_train_from_answers(req: LanguageDataRequest):
    return core.trainFromAnswers(req)

@router.post("/predictFromAnswers", response_model=PredictFromLanguageDataResponse)
def post_predict_from_answers(req: LanguageDataRequest):
    return core.predictFromAnswers(req)

@router.get("/wipe_models")
def get_wipe_models():
    return core.wipe_models()
