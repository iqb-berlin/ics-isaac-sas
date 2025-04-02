from pydantic import BaseModel, StrictInt, StrictStr
from typing import Optional
from models.task_event_type import TaskEventType

class TaskEvent(BaseModel):
    status: Optional[TaskEventType] = None
    message: Optional[StrictStr] = None
    timestamp: Optional[StrictInt] = None
