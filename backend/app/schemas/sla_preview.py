from decimal import Decimal

from pydantic import BaseModel, Field


class SlaPreviewRequest(BaseModel):
    service_key: str
    total_minutes: int = Field(gt=0)
    downtime_minutes: int = Field(ge=0)


class SlaPreviewResponse(BaseModel):
    service_key: str
    service_name: str
    rule_name: str
    target_percentage: Decimal
    total_minutes: int
    downtime_minutes: int
    availability_percent: float
    meets_target: bool
