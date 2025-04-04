from typing import List, Optional
from pydantic import StrictStr, Field, BaseModel, StrictInt


class TaskInstructions(BaseModel):
    item_prompt: StrictStr = Field(description="the prompt string (question) the answer was given in response for", alias="itemPrompt")
    item_targets: List[StrictStr] = Field(description="a list of correct reference answers for the current item", alias="itemTargets")
    random_seed: StrictInt|None = Field(default=None, description="Leave out for true randomness or enter a id for replicable results", alias="randomSeed")
