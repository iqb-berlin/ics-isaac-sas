from __future__ import annotations

from typing import Type

from models.code import Code
from models.service_info import ServiceInfo
from models.service_info_task_types import ServiceInfoTaskTypes
from models.task_type_info import TaskTypeInfo
from models.train import Train

def get_info() -> ServiceInfo:
    return ServiceInfo(
        id = 'server ID',  # TODO
        type = 'issac-sas-coding-service',
        version = '0.0.3', # TODO
        apiVersion = '0.0.3',
        taskTypes = ServiceInfoTaskTypes(
            train = TaskTypeInfo(
                instructionsText = '',
                instructionsSchema = get_schema(Train)
            ),
            code = TaskTypeInfo(
                instructionsText = '',
                instructionsSchema = get_schema(Code)
            )
        )
    )


def get_schema(model: Type[Code|Train]):
    json_schema = model.model_json_schema()
    json_schema['$id'] = 'iscs-instructions-schema-' + ('code' if model == Code else 'train')
    json_schema['$schema'] = "http://json-schema.org/draft-07/schema#"
    return json_schema