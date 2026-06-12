from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.application.sla.calculate_service_sla import (
    ActiveSlaRuleNotFoundError,
    CalculateStoredServiceSlaUseCase,
    SlaPreviewInput,
    StoredServiceNotFoundError,
)
from app.infrastructure.db.session import get_db_session
from app.repositories.service_repository import ServiceRepository
from app.repositories.sla_rule_repository import SlaRuleRepository
from app.schemas.sla_preview import SlaPreviewRequest, SlaPreviewResponse


router = APIRouter(prefix="/api/v1/sla", tags=["sla"])


def get_sla_preview_use_case(
    session: Session = Depends(get_db_session),
) -> CalculateStoredServiceSlaUseCase:
    service_repository = ServiceRepository(session)
    sla_rule_repository = SlaRuleRepository(session)
    return CalculateStoredServiceSlaUseCase(service_repository, sla_rule_repository)


@router.post("/preview", status_code=status.HTTP_200_OK)
def preview_sla(
    payload: SlaPreviewRequest,
    use_case: CalculateStoredServiceSlaUseCase = Depends(get_sla_preview_use_case),
) -> dict[str, object]:
    input_data = SlaPreviewInput(
        service_key=payload.service_key,
        total_minutes=payload.total_minutes,
        downtime_minutes=payload.downtime_minutes,
    )

    try:
        preview = use_case.execute(input_data)
    except StoredServiceNotFoundError:
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

    response = SlaPreviewResponse(
        service_key=preview.service.key,
        service_name=preview.service.name,
        rule_name=preview.rule.name,
        target_percentage=preview.target_percentage,
        total_minutes=preview.total_minutes,
        downtime_minutes=preview.downtime_minutes,
        availability_percent=preview.availability_percent,
        meets_target=preview.meets_target,
    )

    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": "Prévia de SLA calculada",
        "errors": [],
    }
