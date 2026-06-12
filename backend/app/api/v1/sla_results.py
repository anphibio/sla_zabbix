from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.application.reports.executive_payload import (
    ensure_utc,
    serialize_executive_payload,
)
from app.infrastructure.reports.pdf import build_executive_sla_pdf
from app.application.sla.create_sla_result import (
    CreateSlaResultInput,
    CreateSlaResultUseCase,
)
from app.application.sla.preview_zabbix_service_sla import (
    ActiveSlaRuleNotFoundError,
    InvalidServiceSourceError,
    PreviewZabbixServiceSlaUseCase,
    ServiceNotFoundError,
    SourceMappingNotFoundError,
    ZabbixQueryError,
)
from app.infrastructure.db.session import get_db_session
from app.infrastructure.reports.xlsx import build_executive_sla_xlsx
from app.infrastructure.zabbix.client import ZabbixClient
from app.repositories.maintenance_window_repository import MaintenanceWindowRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.sla_exclusion_repository import SlaExclusionRepository
from app.repositories.sla_result_repository import (
    SlaResultConflictError,
    SlaResultRepository,
)
from app.repositories.sla_rule_repository import SlaRuleRepository
from app.schemas.sla_result import (
    SlaExecutiveResponse,
    SlaExecutiveServiceItem,
    SlaExecutiveSummary,
    SlaResultCreate,
    SlaResultHistoryPoint,
    SlaResultHistoryResponse,
    SlaResultResponse,
    SlaResultTrendSummary,
)


router = APIRouter(prefix="/api/v1/sla-results", tags=["sla-results"])


def get_zabbix_client(request: Request) -> ZabbixClient:
    return request.app.state.zabbix_client


def get_preview_use_case(
    request: Request,
    session: Session = Depends(get_db_session),
) -> PreviewZabbixServiceSlaUseCase:
    return PreviewZabbixServiceSlaUseCase(
        service_repository=ServiceRepository(session),
        sla_rule_repository=SlaRuleRepository(session),
        maintenance_window_repository=MaintenanceWindowRepository(session),
        sla_exclusion_repository=SlaExclusionRepository(session),
        zabbix_client=get_zabbix_client(request),
    )


def get_sla_result_repository(
    session: Session = Depends(get_db_session),
) -> SlaResultRepository:
    return SlaResultRepository(session)


def get_create_sla_result_use_case(
    preview_use_case: PreviewZabbixServiceSlaUseCase = Depends(get_preview_use_case),
    sla_result_repository: SlaResultRepository = Depends(get_sla_result_repository),
) -> CreateSlaResultUseCase:
    return CreateSlaResultUseCase(preview_use_case, sla_result_repository)


def _serialize_result(result) -> dict[str, object]:
    response = SlaResultResponse(
        service_key=result.service.key,
        rule_name=result.sla_rule.name,
        period_start=ensure_utc(result.period_start),
        period_end=ensure_utc(result.period_end),
        source_type=result.source_type,
        source_value=result.source_value,
        total_minutes=result.total_minutes,
        original_total_minutes=result.original_total_minutes,
        downtime_minutes=result.downtime_minutes,
        raw_downtime_minutes=result.raw_downtime_minutes,
        maintenance_excluded_minutes=result.maintenance_excluded_minutes,
        downtime_excluded_by_maintenance_minutes=result.downtime_excluded_by_maintenance_minutes,
        sla_exclusion_minutes=result.sla_exclusion_minutes,
        downtime_excluded_by_sla_exclusions_minutes=result.downtime_excluded_by_sla_exclusions_minutes,
        availability_percent=result.availability_percent,
        target_percentage=result.target_percentage,
        meets_target=result.meets_target,
        matched_problems_count=result.matched_problems_count,
        merged_intervals_count=result.merged_intervals_count,
    )
    return response.model_dump(mode="json")


def _serialize_history(results, service_key: str) -> dict[str, object]:
    periods = [
        SlaResultHistoryPoint(
            period_start=ensure_utc(result.period_start),
            period_end=ensure_utc(result.period_end),
            availability_percent=result.availability_percent,
            target_percentage=result.target_percentage,
            meets_target=result.meets_target,
            downtime_minutes=result.downtime_minutes,
        )
        for result in results
    ]
    availability_values = [Decimal(str(result.availability_percent)) for result in results]
    current_value = availability_values[-1] if availability_values else None
    previous_value = availability_values[-2] if len(availability_values) > 1 else None

    if current_value is not None and previous_value is not None:
        delta_percent = current_value - previous_value
        if delta_percent > 0:
            trend_direction = "up"
        elif delta_percent < 0:
            trend_direction = "down"
        else:
            trend_direction = "stable"
    else:
        delta_percent = None
        trend_direction = "stable"

    summary = SlaResultTrendSummary(
        current_availability_percent=current_value,
        previous_availability_percent=previous_value,
        delta_percent=delta_percent,
        trend_direction=trend_direction,
        periods_count=len(results),
        best_availability_percent=max(availability_values) if availability_values else None,
        worst_availability_percent=min(availability_values) if availability_values else None,
    )

    response = SlaResultHistoryResponse(
        service_key=service_key,
        periods=periods,
        summary=summary,
    )
    return response.model_dump(mode="json")


def _serialize_executive(results, period_start: datetime, period_end: datetime, source_type: Optional[str]) -> dict[str, object]:
    payload = serialize_executive_payload(results, period_start, period_end, source_type)
    service_items = [
        SlaExecutiveServiceItem(**item)
        for item in payload["services"]
    ]
    summary = SlaExecutiveSummary(**payload["summary"])
    response = SlaExecutiveResponse(
        source_type=payload["source_type"],
        summary=summary,
        services=service_items,
    )
    return response.model_dump(mode="json")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_sla_result(
    payload: SlaResultCreate,
    use_case: CreateSlaResultUseCase = Depends(get_create_sla_result_use_case),
) -> dict[str, object]:
    try:
        result = use_case.execute(
            CreateSlaResultInput(
                service_key=payload.service_key,
                period_start=payload.period_start,
                period_end=payload.period_end,
            )
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "data": None, "message": "Período inválido", "errors": [str(exc)]},
        )
    except ServiceNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False, "data": None, "message": "Serviço não encontrado", "errors": ["service_not_found"]},
        )
    except ActiveSlaRuleNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False, "data": None, "message": "Regra de SLA ativa não encontrada", "errors": ["sla_rule_not_found"]},
        )
    except (InvalidServiceSourceError, SourceMappingNotFoundError) as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "data": None, "message": "Fonte do serviço inválida para consulta no Zabbix", "errors": [str(exc)]},
        )
    except ZabbixQueryError as exc:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"success": False, "data": None, "message": "Falha ao consultar o Zabbix", "errors": [str(exc)]},
        )
    except SlaResultConflictError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"success": False, "data": None, "message": "Resultado mensal já existe para este período", "errors": ["result_already_exists"]},
        )

    return {
        "success": True,
        "data": _serialize_result(result),
        "message": "Resultado mensal de SLA criado",
        "errors": [],
    }


@router.get("", status_code=status.HTTP_200_OK)
def list_sla_results(
    service_key: str = Query(...),
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    repository: SlaResultRepository = Depends(get_sla_result_repository),
) -> dict[str, object]:
    results = repository.get_by_service_key_and_period(
        service_key=service_key,
        period_start=period_start,
        period_end=period_end,
    )
    return {
        "success": True,
        "data": [_serialize_result(result) for result in results],
        "message": "Resultados mensais carregados",
        "errors": [],
    }


@router.get("/history", status_code=status.HTTP_200_OK)
def get_sla_results_history(
    service_key: str = Query(...),
    limit: int = Query(12, ge=1, le=60),
    repository: SlaResultRepository = Depends(get_sla_result_repository),
) -> dict[str, object]:
    results = repository.list_by_service_key(service_key=service_key, limit=limit)
    return {
        "success": True,
        "data": _serialize_history(results, service_key),
        "message": "Histórico de SLA carregado",
        "errors": [],
    }


@router.get("/executive", status_code=status.HTTP_200_OK)
def get_sla_results_executive(
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    source_type: Optional[str] = Query(None),
    repository: SlaResultRepository = Depends(get_sla_result_repository),
) -> dict[str, object]:
    results = repository.list_by_period(
        period_start=period_start,
        period_end=period_end,
        source_type=source_type,
    )
    return {
        "success": True,
        "data": _serialize_executive(results, period_start, period_end, source_type),
        "message": "Consolidação executiva de SLA carregada",
        "errors": [],
    }


@router.get("/executive.xlsx", status_code=status.HTTP_200_OK)
def download_sla_results_executive_xlsx(
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    source_type: Optional[str] = Query(None),
    repository: SlaResultRepository = Depends(get_sla_result_repository),
) -> Response:
    results = repository.list_by_period(
        period_start=period_start,
        period_end=period_end,
        source_type=source_type,
    )
    payload = _serialize_executive(results, period_start, period_end, source_type)
    file_bytes = build_executive_sla_xlsx(payload)
    source_suffix = source_type or "todos"
    filename = (
        "sla-executivo-"
        f"{period_start.date().isoformat()}-"
        f"{period_end.date().isoformat()}-"
        f"{source_suffix}.xlsx"
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(
        content=file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/executive.pdf", status_code=status.HTTP_200_OK)
def download_sla_results_executive_pdf(
    period_start: datetime = Query(...),
    period_end: datetime = Query(...),
    source_type: Optional[str] = Query(None),
    repository: SlaResultRepository = Depends(get_sla_result_repository),
) -> Response:
    results = repository.list_by_period(
        period_start=period_start,
        period_end=period_end,
        source_type=source_type,
    )
    payload = _serialize_executive(results, period_start, period_end, source_type)
    file_bytes = build_executive_sla_pdf(payload)
    source_suffix = source_type or "todos"
    filename = (
        "sla-executivo-"
        f"{period_start.date().isoformat()}-"
        f"{period_end.date().isoformat()}-"
        f"{source_suffix}.pdf"
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(
        content=file_bytes,
        media_type="application/pdf",
        headers=headers,
    )
