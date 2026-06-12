from typing import Literal

from pydantic import BaseModel


class ServiceCreate(BaseModel):
    name: str
    key: str
    source_type: Literal["tag", "hostgroup"]
    source_value: str


class ServiceResponse(BaseModel):
    name: str
    key: str
    source_type: Literal["tag", "hostgroup"]
    source_value: str
    is_active: bool
