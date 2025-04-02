from typing import List, Optional

from pydantic import BaseModel, StrictStr

from models.data_chunk import DataChunk
from models.task_event import TaskEvent
from models.task_instructions import TaskInstructions
from models.task_type import TaskType

class Task(BaseModel):
    id: StrictStr
    label: StrictStr
    type: TaskType
    events: List[TaskEvent]
    instructions: Optional[TaskInstructions | str] = None
    data: List[DataChunk]
