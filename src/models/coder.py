from pydantic import BaseModel, StrictStr


class Coder(BaseModel):
    id: StrictStr = None
    label: StrictStr = None
