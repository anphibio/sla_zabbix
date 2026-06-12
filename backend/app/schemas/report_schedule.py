from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReportScheduleCreate(BaseModel):
    name: str
    report_format: str
    source_type: Optional[str] = None
    recipient_email: str
    subject_template: Optional[str] = None
    day_of_month: int


class ReportScheduleResponse(BaseModel):
    name: str
    report_format: str
    source_type: Optional[str]
    recipient_email: str
    subject_template: Optional[str]
    day_of_month: int
    is_active: bool


class ReportScheduleRunRequest(BaseModel):
    reference_date: datetime


class ReportScheduleRunResponse(BaseModel):
    schedule_name: str
    report_format: str
    source_type: Optional[str]
    status: str
    delivery_status: Optional[str]
    file_path: Optional[str]
    period_start: datetime
    period_end: datetime
    message: Optional[str]
