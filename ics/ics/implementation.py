from typing import List, Optional
from pydantic import BaseModel, StrictStr, StrictInt, Field
from fastapi import HTTPException
from ics_components.common import CoderRegistry as CoderRegistryInterface
from ics_models import Coder, Task as TaskBase, TaskUpdate as TaskUpdateBase
from ics.isaac_sas import fetch_stored_models, delete_model


class TaskInstructions(BaseModel):
    item_prompt: StrictStr = Field(description="the prompt string (question) the answer was given in response for", alias="itemPrompt")
    item_targets: List[StrictStr] = Field(description="a list of correct reference answers for the current item", alias="itemTargets")
    random_seed: StrictInt|None = Field(default=None, description="Leave out for true randomness or enter a id for replicable results", alias="randomSeed")
    @staticmethod
    def description() -> str:
        return "Isaac-SaS also uses a list of possible correct answers from the code book for training along with teh encoded training data."


class Task(TaskBase):
    instructions: Optional[TaskInstructions] = None

class TaskUpdate(TaskUpdateBase):
    instructions: Optional[TaskInstructions] = None

class CoderRegistry(CoderRegistryInterface):
    def list_coders(self) -> list[Coder]:
        coder_ids = fetch_stored_models()
        return [Coder(id=model_id, label=model_id) for model_id in coder_ids]

    def delete_coder(self, coder_id: str) -> None:
        try:
            delete_model(coder_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Coder id {coder_id} not found")
        except PermissionError:
            raise HTTPException(status_code=403, detail=f"Could not delete file of {coder_id}")