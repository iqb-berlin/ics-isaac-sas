from enum import Enum
from pydantic import BaseModel, ConfigDict, create_model
from isaac_sas import core
from models.service_info_instructions_schema import ServiceInfoInstructionsSchema


def get_schema() -> ServiceInfoInstructionsSchema:
    onnx_models = core.fetch_stored_models()
    onnx_models_enum = Enum('AvailableModels', {value: value for value in onnx_models["modelIds"]})
    dynamic_model = create_model(
        'ISCSInstructionsSchema',
        model = (onnx_models_enum, ...)
    )
    json_schema = dynamic_model.model_json_schema()
    json_schema['$id'] = 'iscs-instructions-schema'
    json_schema['$schema'] = "http://json-schema.org/draft-07/schema#"
    return json_schema
