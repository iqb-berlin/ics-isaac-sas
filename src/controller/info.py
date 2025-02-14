from models.service_info import ServiceInfo
from models.service_info_instructions_schema import ServiceInfoInstructionsSchema


def get_info() -> ServiceInfo:
    schema = ServiceInfoInstructionsSchema.from_dict({
        "$schema": "https://json-schema.org/draft-07/schema",
        "$id": "issac-sas-coding-service-options",
        "description": "",
        "type": "object",
        "properties": {},
        "required": []
    })

    return ServiceInfo.from_dict({
        "id": 'server ID',  # TODO
        "type": 'issac-sas-coding-service',
        "version": '0.0.1', # TODO
        "api_version": '0.0.2',
        "instructions_schema": schema,
    })


