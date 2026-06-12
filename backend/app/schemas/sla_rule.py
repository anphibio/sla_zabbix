from decimal import Decimal

from pydantic import BaseModel, Field


class SlaRuleCreate(BaseModel):
    service_key: str
    name: str
    target_percentage: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("100"),
        max_digits=5,
        decimal_places=2,
    )


class SlaRuleResponse(BaseModel):
    service_key: str
    name: str
    target_percentage: Decimal
    is_active: bool
