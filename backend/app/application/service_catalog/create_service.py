from dataclasses import dataclass

from app.domain.service_catalog.entities import ServiceCatalogItem, ServiceSourceType
from app.repositories.service_repository import (
    ServiceKeyConflictError,
    ServiceRepository,
)


@dataclass(frozen=True)
class CreateServiceInput:
    name: str
    key: str
    source_type: ServiceSourceType
    source_value: str


class ServiceAlreadyExistsError(Exception):
    pass


class CreateServiceUseCase:
    def __init__(self, repository: ServiceRepository) -> None:
        self._repository = repository

    def execute(self, payload: CreateServiceInput) -> ServiceCatalogItem:
        service = ServiceCatalogItem(
            name=payload.name,
            key=payload.key,
            source_type=payload.source_type,
            source_value=payload.source_value,
        )

        try:
            return self._repository.create(service)
        except ServiceKeyConflictError as exc:
            raise ServiceAlreadyExistsError(payload.key) from exc
