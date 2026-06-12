from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class SlaResultCreate(BaseModel):
    service_key: str
    period_start: datetime
    period_end: datetime


class SlaResultResponse(BaseModel):
    service_key: str
    rule_name: str
    period_start: datetime
    period_end: datetime
    source_type: str
    source_value: str
    total_minutes: int
    original_total_minutes: int
    downtime_minutes: int
    raw_downtime_minutes: int
    maintenance_excluded_minutes: int
    downtime_excluded_by_maintenance_minutes: int
    sla_exclusion_minutes: int
    downtime_excluded_by_sla_exclusions_minutes: int
    availability_percent: Decimal
    target_percentage: Decimal
    meets_target: bool
    matched_problems_count: int
    merged_intervals_count: int


class SlaResultHistoryPoint(BaseModel):
    period_start: datetime
    period_end: datetime
    availability_percent: Decimal
    target_percentage: Decimal
    meets_target: bool
    downtime_minutes: int


class SlaResultTrendSummary(BaseModel):
    current_availability_percent: Optional[Decimal]
    previous_availability_percent: Optional[Decimal]
    delta_percent: Optional[Decimal]
    trend_direction: str
    periods_count: int
    best_availability_percent: Optional[Decimal]
    worst_availability_percent: Optional[Decimal]


class SlaResultHistoryResponse(BaseModel):
    service_key: str
    periods: list[SlaResultHistoryPoint]
    summary: SlaResultTrendSummary


class SlaExecutiveServiceItem(BaseModel):
    service_key: str
    rule_name: str
    source_type: str
    availability_percent: Decimal
    target_percentage: Decimal
    meets_target: bool
    downtime_minutes: int
    total_minutes: int


class SlaExecutiveSummary(BaseModel):
    period_start: datetime
    period_end: datetime
    services_count: int
    compliant_services_count: int
    non_compliant_services_count: int
    weighted_availability_percent: Optional[Decimal]
    average_availability_percent: Optional[Decimal]
    best_availability_percent: Optional[Decimal]
    worst_availability_percent: Optional[Decimal]


class SlaExecutiveResponse(BaseModel):
    source_type: Optional[str]
    summary: SlaExecutiveSummary
    services: list[SlaExecutiveServiceItem]
