from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.application.reports.executive_payload import serialize_executive_payload
from app.infrastructure.email.client import EmailClient, EmailDeliveryError
from app.infrastructure.reports.pdf import build_executive_sla_pdf
from app.infrastructure.reports.storage import write_report_file
from app.infrastructure.reports.xlsx import build_executive_sla_xlsx
from app.repositories.report_schedule_repository import ReportScheduleRepository
from app.repositories.report_schedule_run_repository import (
    ReportScheduleRunConflictError,
    ReportScheduleRunRepository,
)
from app.repositories.sla_result_repository import SlaResultRepository


@dataclass(frozen=True)
class RunDueReportSchedulesInput:
    reference_date: datetime

    def __post_init__(self) -> None:
        if self.reference_date.tzinfo is None:
            raise ValueError("reference_date must be timezone-aware")


@dataclass(frozen=True)
class ReportScheduleRunResult:
    schedule_name: str
    report_format: str
    source_type: Optional[str]
    status: str
    delivery_status: Optional[str]
    file_path: Optional[str]
    period_start: datetime
    period_end: datetime
    message: Optional[str]


class RunDueReportSchedulesUseCase:
    def __init__(
        self,
        schedule_repository: ReportScheduleRepository,
        run_repository: ReportScheduleRunRepository,
        sla_result_repository: SlaResultRepository,
        email_client: EmailClient,
    ) -> None:
        self._schedule_repository = schedule_repository
        self._run_repository = run_repository
        self._sla_result_repository = sla_result_repository
        self._email_client = email_client

    def execute(self, payload: RunDueReportSchedulesInput) -> list[ReportScheduleRunResult]:
        due_schedules = self._schedule_repository.list_active_schedules_due_on_day(
            payload.reference_date.day
        )
        period_start, period_end = _previous_month_period(payload.reference_date)
        results: list[ReportScheduleRunResult] = []

        for schedule in due_schedules:
            sla_results = self._sla_result_repository.list_by_period(
                period_start=period_start,
                period_end=period_end,
                source_type=schedule.source_type,
            )

            if not sla_results:
                try:
                    self._run_repository.create_run(
                        schedule_id=schedule.id,
                        reference_date=payload.reference_date,
                        period_start=period_start,
                        period_end=period_end,
                        status="no_data",
                        delivery_status="skipped",
                        message="Nenhum resultado mensal encontrado para o período",
                    )
                except ReportScheduleRunConflictError:
                    pass

                results.append(
                    ReportScheduleRunResult(
                        schedule_name=schedule.name,
                        report_format=schedule.report_format,
                        source_type=schedule.source_type,
                        status="no_data",
                        delivery_status="skipped",
                        file_path=None,
                        period_start=period_start,
                        period_end=period_end,
                        message="Nenhum resultado mensal encontrado para o período",
                    )
                )
                continue

            payload_data = serialize_executive_payload(
                sla_results,
                period_start,
                period_end,
                schedule.source_type,
            )

            if schedule.report_format == "xlsx":
                content = build_executive_sla_xlsx(payload_data)
                extension = "xlsx"
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                content = build_executive_sla_pdf(payload_data)
                extension = "pdf"
                mime_type = "application/pdf"

            filename = (
                f"{schedule.name.lower().replace(' ', '-')}-"
                f"{period_start.date().isoformat()}-"
                f"{period_end.date().isoformat()}."
                f"{extension}"
            )
            file_path = write_report_file(filename, content)
            subject = schedule.subject_template or (
                f"{schedule.name} - {period_start.date().isoformat()} a {period_end.date().isoformat()}"
            )
            body = (
                "Segue em anexo o relatório executivo de SLA.\n\n"
                f"Período: {period_start.date().isoformat()} até {period_end.date().isoformat()}\n"
                f"Fonte: {schedule.source_type or 'todos'}\n"
            )

            try:
                self._email_client.send_report(
                    recipient_email=schedule.recipient_email,
                    subject=subject,
                    body=body,
                    attachment_name=filename,
                    attachment_content=content,
                    attachment_mime_type=mime_type,
                )
                delivery_status = "sent"
                message = "Relatório gerado e enviado com sucesso"
            except EmailDeliveryError as exc:
                delivery_status = "failed"
                message = f"Relatório gerado, mas envio falhou: {exc}"

            try:
                self._run_repository.create_run(
                    schedule_id=schedule.id,
                    reference_date=payload.reference_date,
                    period_start=period_start,
                    period_end=period_end,
                    status="generated",
                    delivery_status=delivery_status,
                    file_path=file_path,
                    message=message,
                )
                status = "generated"
            except ReportScheduleRunConflictError:
                status = "already_generated"
                delivery_status = "skipped"
                message = "Execução já registrada para este período"

            results.append(
                ReportScheduleRunResult(
                    schedule_name=schedule.name,
                    report_format=schedule.report_format,
                    source_type=schedule.source_type,
                    status=status,
                    delivery_status=delivery_status,
                    file_path=file_path,
                    period_start=period_start,
                    period_end=period_end,
                    message=message,
                )
            )

        return results


def _previous_month_period(reference_date: datetime) -> tuple[datetime, datetime]:
    current = reference_date.astimezone(timezone.utc)
    current_month_start = datetime(current.year, current.month, 1, tzinfo=timezone.utc)
    previous_month_end = current_month_start
    if current.month == 1:
        previous_month_start = datetime(current.year - 1, 12, 1, tzinfo=timezone.utc)
    else:
        previous_month_start = datetime(current.year, current.month - 1, 1, tzinfo=timezone.utc)
    return previous_month_start, previous_month_end
