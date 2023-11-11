from typing import Optional, Type
from pydantic import BaseModel


class Setting(BaseModel):
    name: str
    value: object = None
    type: str | object
    default: object
    description: str
    example: Optional[str] = None
