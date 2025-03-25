from typing import List
from pydantic import BaseModel
from models.service_info_instructions_schema import ServiceInfoInstructionsSchema

class InstructionsTrain(BaseModel):
    itemPrompt: str
    itemTargets: List[str]

def get_schema() -> ServiceInfoInstructionsSchema:
    json_schema = InstructionsTrain.model_json_schema()
    json_schema['$id'] = 'iscs-instructions-schema-train'
    json_schema['$schema'] = "http://json-schema.org/draft-07/schema#"
    return json_schema
