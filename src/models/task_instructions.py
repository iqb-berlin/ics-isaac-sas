from typing import List

from pydantic import StrictStr, Field, BaseModel


class TaskInstructions(BaseModel):
    item_prompt: StrictStr = Field(description="the prompt string (question) the answer was given in response for", alias="itemPrompt")
    item_targets: List[StrictStr] = Field(description="a list of correct reference answers for the current item", alias="itemTargets")
