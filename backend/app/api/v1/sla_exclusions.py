from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.application.sla.create_sla_exclusion import (
    CreateSlaExclusionInput,
    CreateSlaExclusionUseCase,
    ServiceNotFoundError,
)
from app.infrastructure.db.session import get_db_session
from app.repositories.service_repository import ServiceRepository
from app.repositories.sla_exclusion_repository import SlaExclusionRepository
from app.schemas.sla_exclusion import SlaExclusionCreate, SlaExclusionResponse


router = APIRouter(prefix="/api/v1/sla-exclusions", tags=["sla-exclusions"])


def get_service_repository(
    session: Session = Depends(get_db_session),
) -> ServiceRepository:
    return ServiceRepository(session)


def get_sla_exclusion_repository(
    session: Session = Depends(get_db_session),
) -> SlaExclusionRepository:
    return SlaExclusionRepository(session)


def get_create_sla_exclusion_use_case(
    service_repository: ServiceRepository = Depends(get_service_repository),
    sla_exclusion_repository: SlaExclusionRepository = Depends(
        get_sla_exclusion_repository
    ),
) -> CreateSlaExclusionUseCase:
    return CreateSlaExclusionUseCase(service_repository, sla_exclusion_repository)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_sla_exclusion(
    payload: SlaExclusionCreate,
    use_case: CreateSlaExclusionUseCase = Depends(get_create_sla_exclusion_use_case),
) -> dict[str, object]:
    try:
        exclusion = use_case.execute(
            CreateSlaExclusionInput(
                service_key=payload.service_key,
                name=payload.name,
                reason=payload.reason,
                approved_by=payload.approved_by,
                start_at=payload.start_at,
                end_at=payload.end_at,
                eventid=payload.eventid,
            )
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "data": None,
                "message": "Exclusão de SLA inválida",
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

    response = SlaExclusionResponse(
        service_key=payload.service_key,
        name=exclusion.name,
        reason=exclusion.reason,
        approved_by=exclusion.approved_by,
        start_at=payload.start_at,
        end_at=payload.end_at,
        eventid=exclusion.eventid,
        is_active=exclusion.is_active,
    )

    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": "Exclusão de SLA criada",
        "errors": [],
    }
