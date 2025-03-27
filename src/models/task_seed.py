from pydantic import BaseModel, StrictStr
from models.task_type import TaskType

class TaskSeed(BaseModel):
    label: StrictStr
    type: TaskType
