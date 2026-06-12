from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class ZabbixSlaPreviewRequest(BaseModel):
    service_key: str
    period_start: datetime
    period_end: datetime


class ZabbixProblemIntervalResponse(BaseModel):
    eventid: str
    name: str
    severity: int
    started_at: datetime
    recovered_at: datetime
    downtime_minutes: int


class MaintenanceWindowIntervalResponse(BaseModel):
    name: str
    description: str
    started_at: datetime
    ended_at: datetime
    excluded_minutes: int


class SlaExclusionIntervalResponse(BaseModel):
    name: str
    reason: str
    approved_by: str
    eventid: Optional[str]
    started_at: datetime
    ended_at: datetime
    excluded_minutes: int


class ZabbixSlaPreviewResponse(BaseModel):
    service_key: str
    service_name: str
    rule_name: str
    source_type: str
    source_value: str
    period_start: datetime
    period_end: datetime
    target_percentage: Decimal
    original_total_minutes: int
    total_minutes: int
    raw_downtime_minutes: int
    downtime_minutes: int
    maintenance_excluded_minutes: int
    downtime_excluded_by_maintenance_minutes: int
    sla_exclusion_minutes: int
    downtime_excluded_by_sla_exclusions_minutes: int
    availability_percent: float
    meets_target: bool
    matched_problems_count: int
    merged_intervals_count: int
    problems: list[ZabbixProblemIntervalResponse]
    maintenance_windows: list[MaintenanceWindowIntervalResponse]
    sla_exclusions: list[SlaExclusionIntervalResponse]
