from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SlaExclusionCreate(BaseModel):
    service_key: str
    name: str
    reason: str
    approved_by: str
    start_at: datetime
    end_at: datetime
    eventid: Optional[str] = None


class SlaExclusionResponse(BaseModel):
    service_key: str
    name: str
    reason: str
    approved_by: str
    start_at: datetime
    end_at: datetime
    eventid: Optional[str]
    is_active: bool
