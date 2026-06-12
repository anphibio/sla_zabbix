from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.application.sla.preview_zabbix_service_sla import (
    ActiveSlaRuleNotFoundError,
    InvalidServiceSourceError,
    PreviewZabbixServiceSlaInput,
    PreviewZabbixServiceSlaUseCase,
    ServiceNotFoundError,
    SourceMappingNotFoundError,
    ZabbixQueryError,
)
from app.infrastructure.db.session import get_db_session
from app.infrastructure.zabbix.client import ZabbixClient
from app.repositories.maintenance_window_repository import MaintenanceWindowRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.sla_exclusion_repository import SlaExclusionRepository
from app.repositories.sla_rule_repository import SlaRuleRepository
from app.schemas.zabbix_sla_preview import (
    MaintenanceWindowIntervalResponse,
    SlaExclusionIntervalResponse,
    ZabbixProblemIntervalResponse,
    ZabbixSlaPreviewRequest,
    ZabbixSlaPreviewResponse,
)


router = APIRouter(prefix="/api/v1/sla", tags=["sla"])


def get_zabbix_client(request: Request) -> ZabbixClient:
    return request.app.state.zabbix_client


def get_preview_zabbix_service_sla_use_case(
    request: Request,
    session: Session = Depends(get_db_session),
) -> PreviewZabbixServiceSlaUseCase:
    service_repository = ServiceRepository(session)
    sla_rule_repository = SlaRuleRepository(session)
    maintenance_window_repository = MaintenanceWindowRepository(session)
    sla_exclusion_repository = SlaExclusionRepository(session)
    zabbix_client = get_zabbix_client(request)
    return PreviewZabbixServiceSlaUseCase(
        service_repository=service_repository,
        sla_rule_repository=sla_rule_repository,
        maintenance_window_repository=maintenance_window_repository,
        sla_exclusion_repository=sla_exclusion_repository,
        zabbix_client=zabbix_client,
    )


@router.post("/preview/zabbix", status_code=status.HTTP_200_OK)
def preview_sla_from_zabbix(
    payload: ZabbixSlaPreviewRequest,
    use_case: PreviewZabbixServiceSlaUseCase = Depends(
        get_preview_zabbix_service_sla_use_case
    ),
) -> dict[str, object]:
    try:
        result = use_case.execute(
            PreviewZabbixServiceSlaInput(
                service_key=payload.service_key,
                period_start=payload.period_start,
                period_end=payload.period_end,
            )
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "data": None,
                "message": "Período inválido",
                "errors": [str(exc)],
            },
        )
    except ServiceNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "data": None,
                "message": "Serviço não encontrado",
                "errors": ["service_not_found"],
            },
        )
    except ActiveSlaRuleNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "data": None,
                "message": "Regra de SLA ativa não encontrada",
                "errors": ["sla_rule_not_found"],
            },
        )
    except (InvalidServiceSourceError, SourceMappingNotFoundError) as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "data": None,
                "message": "Fonte do serviço inválida para consulta no Zabbix",
                "errors": [str(exc)],
            },
        )
    except ZabbixQueryError as exc:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "success": False,
                "data": None,
                "message": "Falha ao consultar o Zabbix",
                "errors": [str(exc)],
            },
        )

    response = ZabbixSlaPreviewResponse(
        service_key=result.service.key,
        service_name=result.service.name,
        rule_name=result.rule.name,
        source_type=result.service.source_type,
        source_value=result.service.source_value,
        period_start=result.period_start,
        period_end=result.period_end,
        target_percentage=result.target_percentage,
        original_total_minutes=result.original_total_minutes,
        total_minutes=result.total_minutes,
        raw_downtime_minutes=result.raw_downtime_minutes,
        downtime_minutes=result.downtime_minutes,
        maintenance_excluded_minutes=result.maintenance_excluded_minutes,
        downtime_excluded_by_maintenance_minutes=result.downtime_excluded_by_maintenance_minutes,
        sla_exclusion_minutes=result.sla_exclusion_minutes,
        downtime_excluded_by_sla_exclusions_minutes=result.downtime_excluded_by_sla_exclusions_minutes,
        availability_percent=result.availability_percent,
        meets_target=result.meets_target,
        matched_problems_count=result.matched_problems_count,
        merged_intervals_count=result.merged_intervals_count,
        problems=[
            ZabbixProblemIntervalResponse(
                eventid=problem.eventid,
                name=problem.name,
                severity=problem.severity,
                started_at=problem.started_at,
                recovered_at=problem.recovered_at,
                downtime_minutes=problem.downtime_minutes,
            )
            for problem in result.problems
        ],
        maintenance_windows=[
            MaintenanceWindowIntervalResponse(
                name=window.name,
                description=window.description,
                started_at=window.started_at,
                ended_at=window.ended_at,
                excluded_minutes=window.excluded_minutes,
            )
            for window in result.maintenance_windows
        ],
        sla_exclusions=[
            SlaExclusionIntervalResponse(
                name=exclusion.name,
                reason=exclusion.reason,
                approved_by=exclusion.approved_by,
                eventid=exclusion.eventid,
                started_at=exclusion.started_at,
                ended_at=exclusion.ended_at,
                excluded_minutes=exclusion.excluded_minutes,
            )
            for exclusion in result.sla_exclusions
        ],
    )

    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": "Prévia de SLA com dados do Zabbix calculada",
        "errors": [],
    }
