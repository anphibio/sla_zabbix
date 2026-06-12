from dataclasses import dataclass
from datetime import datetime

from app.models.maintenance_window import MaintenanceWindow
from app.repositories.maintenance_window_repository import MaintenanceWindowRepository
from app.repositories.service_repository import ServiceRepository


@dataclass(frozen=True)
class CreateMaintenanceWindowInput:
    service_key: str
    name: str
    description: str
    start_at: datetime
    end_at: datetime

    def __post_init__(self) -> None:
        if self.start_at.tzinfo is None or self.end_at.tzinfo is None:
            raise ValueError("maintenance boundaries must be timezone-aware")
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be greater than start_at")


class ServiceNotFoundError(Exception):
    pass


class CreateMaintenanceWindowUseCase:
    def __init__(
        self,
        service_repository: ServiceRepository,
        maintenance_window_repository: MaintenanceWindowRepository,
    ) -> None:
        self._service_repository = service_repository
        self._maintenance_window_repository = maintenance_window_repository

    def execute(self, payload: CreateMaintenanceWindowInput) -> MaintenanceWindow:
        service = self._service_repository.get_by_key(payload.service_key)

        if service is None:
            raise ServiceNotFoundError(payload.service_key)

        return self._maintenance_window_repository.create_window(
            service_id=service.id,
            name=payload.name,
            description=payload.description,
            start_at=payload.start_at,
            end_at=payload.end_at,
        )
