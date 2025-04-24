from typing import Dict
from typing import List
from typing import Union
from pydantic import BaseModel, StrictStr, StrictInt, Field

from lib.feature_extraction.data import ShortAnswerInstance

# api models

class TaskInstructions(BaseModel):
    item_prompt: StrictStr = Field(description="the prompt string (question) the answer was given in response for", alias="itemPrompt")
    item_targets: List[StrictStr] = Field(description="a list of correct reference answers for the current item", alias="itemTargets")
    random_seed: StrictInt|None = Field(default=None, description="Leave out for true randomness or enter a id for replicable results", alias="randomSeed")

# internal models

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

