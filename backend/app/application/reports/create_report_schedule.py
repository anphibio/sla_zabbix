from dataclasses import dataclass
from typing import Optional

from app.models.report_schedule import ReportSchedule
from app.repositories.report_schedule_repository import ReportScheduleRepository


@dataclass(frozen=True)
class CreateReportScheduleInput:
    name: str
    report_format: str
    source_type: Optional[str]
    recipient_email: str
    subject_template: Optional[str]
    day_of_month: int

    def __post_init__(self) -> None:
        if self.report_format not in {"xlsx", "pdf"}:
            raise ValueError("report_format must be xlsx or pdf")
        if self.source_type not in {None, "tag", "hostgroup"}:
            raise ValueError("source_type must be tag, hostgroup or null")
        if "@" not in self.recipient_email:
            raise ValueError("recipient_email must be a valid email")
        if not 1 <= self.day_of_month <= 28:
            raise ValueError("day_of_month must be between 1 and 28")


class CreateReportScheduleUseCase:
    def __init__(self, repository: ReportScheduleRepository) -> None:
        self._repository = repository

    def execute(self, payload: CreateReportScheduleInput) -> ReportSchedule:
        return self._repository.create_schedule(
            name=payload.name,
            report_format=payload.report_format,
            source_type=payload.source_type,
            recipient_email=payload.recipient_email,
            subject_template=payload.subject_template,
            day_of_month=payload.day_of_month,
        )
