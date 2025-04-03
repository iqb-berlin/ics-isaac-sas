from pydantic import StrictStr, Field, BaseModel


class ServiceInfoInstructionsSchema(BaseModel, extra = 'allow'):
    id: StrictStr = Field(alias="$id")
    s_schema: StrictStr = Field(alias="$schema")
