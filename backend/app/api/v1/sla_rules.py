from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.application.sla.create_sla_rule import (
    CreateSlaRuleInput,
    CreateSlaRuleUseCase,
    ServiceNotFoundError,
)
from app.infrastructure.db.session import get_db_session
from app.repositories.service_repository import ServiceRepository
from app.repositories.sla_rule_repository import SlaRuleRepository
from app.schemas.sla_rule import SlaRuleCreate, SlaRuleResponse


router = APIRouter(prefix="/api/v1/sla-rules", tags=["sla-rules"])


def get_service_repository(
    session: Session = Depends(get_db_session),
) -> ServiceRepository:
    return ServiceRepository(session)


def get_sla_rule_repository(
    session: Session = Depends(get_db_session),
) -> SlaRuleRepository:
    return SlaRuleRepository(session)


def get_create_sla_rule_use_case(
    service_repository: ServiceRepository = Depends(get_service_repository),
    sla_rule_repository: SlaRuleRepository = Depends(get_sla_rule_repository),
) -> CreateSlaRuleUseCase:
    return CreateSlaRuleUseCase(service_repository, sla_rule_repository)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_sla_rule(
    payload: SlaRuleCreate,
    use_case: CreateSlaRuleUseCase = Depends(get_create_sla_rule_use_case),
) -> dict[str, object]:
    input_data = CreateSlaRuleInput(
        service_key=payload.service_key,
        name=payload.name,
        target_percentage=payload.target_percentage,
    )

    try:
        rule = use_case.execute(input_data)
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

    response = SlaRuleResponse(
        service_key=payload.service_key,
        name=rule.name,
        target_percentage=rule.target_percentage,
        is_active=rule.is_active,
    )

    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": "Regra de SLA criada",
        "errors": [],
    }
