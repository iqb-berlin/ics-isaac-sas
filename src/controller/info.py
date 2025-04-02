from __future__ import annotations

from typing import Type

from models.service_info import ServiceInfo
from models.task_instructions import TaskInstructions

def get_info() -> ServiceInfo:
    return ServiceInfo(
        id = 'server ID',  # TODO
        type = 'issac-sas-coding-service',
        version = '0.0.3', # TODO
        apiVersion = '0.0.3',
        instructionsText = '',
        instructionsSchema = get_schema(TaskInstructions)
    )


def get_schema(model: Type[TaskInstructions]):
    json_schema = model.model_json_schema()
    json_schema['$id'] = 'ics-is-instructions-schema'
    json_schema['$schema'] = "http://json-schema.org/draft-07/schema#"
    return json_schema
