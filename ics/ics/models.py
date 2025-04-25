from typing import Dict
from typing import List
from typing import Union
from pydantic import BaseModel

from lib.feature_extraction.data import ShortAnswerInstance

# there are internal models from Isaac-sas

class LanguageDataRequest(BaseModel):
    """A request with language data, used for training and predicting."""
    instances: List[ShortAnswerInstance]
    modelId: str

class SinglePrediction(BaseModel):
    """A single prediction result, including probabilities for individual classes."""
    prediction: Union[int, str]
    classProbabilities: Dict[Union[str, int], float]

class PredictFromLanguageDataResponse(BaseModel):
    """A response containing one or more prediction results."""
    predictions: List[SinglePrediction]

class ModelIdResponse(BaseModel):
    """A response containing the IDs of the models currently available."""
    modelIds: List[str]

