from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, StrictStr

from models.code import Code
from models.data_chunk import DataChunk
from models.task_events_inner import TaskEventsInner
from models.task_type import TaskType
from models.train import Train

class Task(BaseModel):
    id: StrictStr
    label: StrictStr
    type: TaskType
    events: List[TaskEventsInner]
    instructions: Optional[Train|Code] = None
    data: List[DataChunk]
