from pydantic import BaseModel, StrictStr
from typing import Optional

from models.task_instructions import TaskInstructions
from models.task_type import TaskType

class TaskUpdate(BaseModel):
    label: Optional[StrictStr] = None
    type: Optional[TaskType] = None
    instructions: Optional[TaskInstructions] = None
