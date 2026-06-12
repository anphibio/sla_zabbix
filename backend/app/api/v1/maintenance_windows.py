from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.application.sla.create_maintenance_window import (
    CreateMaintenanceWindowInput,
    CreateMaintenanceWindowUseCase,
    ServiceNotFoundError,
)
from app.infrastructure.db.session import get_db_session
from app.repositories.maintenance_window_repository import MaintenanceWindowRepository
from app.repositories.service_repository import ServiceRepository
from app.schemas.maintenance_window import (
    MaintenanceWindowCreate,
    MaintenanceWindowResponse,
)


router = APIRouter(prefix="/api/v1/maintenance-windows", tags=["maintenance-windows"])


def get_service_repository(
    session: Session = Depends(get_db_session),
) -> ServiceRepository:
    return ServiceRepository(session)


def get_maintenance_window_repository(
    session: Session = Depends(get_db_session),
) -> MaintenanceWindowRepository:
    return MaintenanceWindowRepository(session)


def get_create_maintenance_window_use_case(
    service_repository: ServiceRepository = Depends(get_service_repository),
    maintenance_window_repository: MaintenanceWindowRepository = Depends(
        get_maintenance_window_repository
    ),
) -> CreateMaintenanceWindowUseCase:
    return CreateMaintenanceWindowUseCase(
        service_repository,
        maintenance_window_repository,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_maintenance_window(
    payload: MaintenanceWindowCreate,
    use_case: CreateMaintenanceWindowUseCase = Depends(
        get_create_maintenance_window_use_case
    ),
) -> dict[str, object]:
    try:
        window = use_case.execute(
            CreateMaintenanceWindowInput(
                service_key=payload.service_key,
                name=payload.name,
                description=payload.description,
                start_at=payload.start_at,
                end_at=payload.end_at,
            )
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "data": None,
                "message": "Janela de manutenção inválida",
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

    response = MaintenanceWindowResponse(
        service_key=payload.service_key,
        name=window.name,
        description=window.description,
        start_at=payload.start_at,
        end_at=payload.end_at,
        is_active=window.is_active,
    )

    return {
        "success": True,
        "data": response.model_dump(mode="json"),
        "message": "Janela de manutenção criada",
        "errors": [],
    }
