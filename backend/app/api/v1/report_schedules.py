from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.application.reports.create_report_schedule import (
    CreateReportScheduleInput,
    CreateReportScheduleUseCase,
)
from app.application.reports.run_due_report_schedules import (
    RunDueReportSchedulesInput,
    RunDueReportSchedulesUseCase,
)
from app.core.config import settings
from app.infrastructure.db.session import get_db_session
from app.infrastructure.email.client import EmailClient
from app.repositories.report_schedule_repository import ReportScheduleRepository
from app.repositories.report_schedule_run_repository import ReportScheduleRunRepository
from app.repositories.sla_result_repository import SlaResultRepository
from app.schemas.report_schedule import (
    ReportScheduleCreate,
    ReportScheduleResponse,
    ReportScheduleRunRequest,
    ReportScheduleRunResponse,
)


router = APIRouter(prefix="/api/v1/report-schedules", tags=["report-schedules"])


def get_report_schedule_repository(
    session: Session = Depends(get_db_session),
) -> ReportScheduleRepository:
    return ReportScheduleRepository(session)


def get_report_schedule_run_repository(
    session: Session = Depends(get_db_session),
) -> ReportScheduleRunRepository:
    return ReportScheduleRunRepository(session)


def get_sla_result_repository(
    session: Session = Depends(get_db_session),
) -> SlaResultRepository:
    return SlaResultRepository(session)


def get_create_report_schedule_use_case(
    repository: ReportScheduleRepository = Depends(get_report_schedule_repository),
) -> CreateReportScheduleUseCase:
    return CreateReportScheduleUseCase(repository)


def get_run_due_report_schedules_use_case(
    schedule_repository: ReportScheduleRepository = Depends(get_report_schedule_repository),
    run_repository: ReportScheduleRunRepository = Depends(
        get_report_schedule_run_repository
    ),
    sla_result_repository: SlaResultRepository = Depends(get_sla_result_repository),
) -> RunDueReportSchedulesUseCase:
    email_client = EmailClient(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        sender_email=settings.smtp_sender_email,
        use_tls=settings.smtp_use_tls,
    )
    return RunDueReportSchedulesUseCase(
        schedule_repository,
        run_repository,
        sla_result_repository,
        email_client,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_report_schedule(
    payload: ReportScheduleCreate,
    use_case: CreateReportScheduleUseCase = Depends(get_create_report_schedule_use_case),
) -> dict[str, object]:
    try:
        schedule = use_case.execute(
            CreateReportScheduleInput(
                name=payload.name,
                report_format=payload.report_format,
                source_type=payload.source_type,
                recipient_email=payload.recipient_email,
                subject_template=payload.subject_template,
                day_of_month=payload.day_of_month,
            )
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "data": None,
                "message": "Agendamento inválido",
                "errors": [str(exc)],
            },
        )

    response = ReportScheduleResponse(
        name=schedule.name,
        report_format=schedule.report_format,
        source_type=schedule.source_type,
        recipient_email=schedule.recipient_email,
        subject_template=schedule.subject_template,
        day_of_month=schedule.day_of_month,
        is_active=schedule.is_active,
    )
    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": "Agendamento criado",
        "errors": [],
    }


@router.post("/run-due", status_code=status.HTTP_200_OK)
def run_due_report_schedules(
    payload: ReportScheduleRunRequest,
    use_case: RunDueReportSchedulesUseCase = Depends(
        get_run_due_report_schedules_use_case
    ),
) -> dict[str, object]:
    try:
        runs = use_case.execute(
            RunDueReportSchedulesInput(reference_date=payload.reference_date)
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "data": None,
                "message": "Data de referência inválida",
                "errors": [str(exc)],
            },
        )

    response = [
        ReportScheduleRunResponse(
            schedule_name=run.schedule_name,
            report_format=run.report_format,
            source_type=run.source_type,
            status=run.status,
            delivery_status=run.delivery_status,
            file_path=run.file_path,
            period_start=run.period_start,
            period_end=run.period_end,
            message=run.message,
        ).model_dump(mode="json")
        for run in runs
    ]
    return {
        "success": True,
        "data": response,
        "message": "Rotina de agendamentos executada",
        "errors": [],
    }
