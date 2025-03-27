import time

from pydantic import StrictStr, StrictInt

import warnings

from models.code import Code
from models.task import Task
from models.task_events_inner import TaskEventsInner
from models.task_seed import TaskSeed
from models.task_type import TaskType
from models.train import Train

warnings.filterwarnings( action='error', message='')


def create(create_task: TaskSeed) -> Task:
    task = Task(
        id = 'a',
        label = create_task.label or 'new: ' + create_task.type,
        type = create_task.type,
        events = [
            TaskEventsInner(
                status = StrictStr('create'),
                timestamp = StrictInt(time.time())
            )
        ],
        data = list()
    )
    return task

st = create(TaskSeed(
    type = TaskType('unknown'),
    label = 'weil weil'
))

t = Task.model_validate_json(""" {
    "id": "67d6857c-f153-433a-9a46-430090d73c29",
    "label": "<corrupted task>",
    "type": "unknown",
    "events": [
        {
            "status": "fail",
            "message": "sss",
            "timestamp": 0
        }
    ],
    "instructions": null,
    "data": []
} """)


c = t.__pydantic_serializer__.to_python(t)
print(c)


