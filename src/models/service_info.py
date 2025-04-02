from pydantic import BaseModel, Field, StrictStr
from typing import Optional
from typing_extensions import Annotated

from models.service_info_instructions_schema import ServiceInfoInstructionsSchema


class ServiceInfo(BaseModel):
    id: Optional[StrictStr] = None
    type: Optional[StrictStr] = None
    version: Optional[Annotated[str, Field(strict=True)]] = None
    api_version: Optional[Annotated[str, Field(strict=True)]] = Field(default=None, alias="apiVersion")
    instructions_text: Optional[StrictStr] = Field(default=None, alias="instructionsText")
    instructions_schema: ServiceInfoInstructionsSchema = Field(alias="instructionsSchema")
