from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.application.service_catalog.create_service import (
    CreateServiceInput,
    CreateServiceUseCase,
    ServiceAlreadyExistsError,
)
from app.infrastructure.db.session import get_db_session
from app.repositories.service_repository import ServiceRepository
from app.schemas.service import ServiceCreate, ServiceResponse


router = APIRouter(prefix="/api/v1/services", tags=["services"])


def get_service_repository(
    session: Session = Depends(get_db_session),
) -> ServiceRepository:
    return ServiceRepository(session)


def get_create_service_use_case(
    repository: ServiceRepository = Depends(get_service_repository),
) -> CreateServiceUseCase:
    return CreateServiceUseCase(repository)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_service(
    payload: ServiceCreate,
    use_case: CreateServiceUseCase = Depends(get_create_service_use_case),
) -> dict[str, object]:
    input_data = CreateServiceInput(
        name=payload.name,
        key=payload.key,
        source_type=payload.source_type,
        source_value=payload.source_value,
    )

    try:
        service = use_case.execute(input_data)
    except ServiceAlreadyExistsError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "data": None,
                "message": "Serviço com esta chave já existe",
                "errors": ["key_already_exists"],
            },
        )

    response = ServiceResponse(
        name=service.name,
        key=service.key,
        source_type=service.source_type,
        source_value=service.source_value,
        is_active=service.is_active,
    )

    return {
        "success": True,
        "data": response.model_dump(),
        "message": "Serviço criado",
        "errors": [],
    }
