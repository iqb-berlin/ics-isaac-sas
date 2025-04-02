from typing import ClassVar, List

from pydantic import StrictStr, Field, BaseModel


class ServiceInfoInstructionsSchema(BaseModel):
    id: StrictStr = Field(alias="$id")
    _schema: StrictStr = Field(alias="$schema")
    __properties: ClassVar[List[str]] = ["$id", "$schema"]
