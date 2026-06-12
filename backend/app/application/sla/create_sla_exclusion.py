from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.models.sla_exclusion import SlaExclusion
from app.repositories.service_repository import ServiceRepository
from app.repositories.sla_exclusion_repository import SlaExclusionRepository


@dataclass(frozen=True)
class CreateSlaExclusionInput:
    service_key: str
    name: str
    reason: str
    approved_by: str
    start_at: datetime
    end_at: datetime
    eventid: Optional[str] = None

    def __post_init__(self) -> None:
        if self.start_at.tzinfo is None or self.end_at.tzinfo is None:
            raise ValueError("exclusion boundaries must be timezone-aware")
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be greater than start_at")


class ServiceNotFoundError(Exception):
    pass


class CreateSlaExclusionUseCase:
    def __init__(
        self,
        service_repository: ServiceRepository,
        sla_exclusion_repository: SlaExclusionRepository,
    ) -> None:
        self._service_repository = service_repository
        self._sla_exclusion_repository = sla_exclusion_repository

    def execute(self, payload: CreateSlaExclusionInput) -> SlaExclusion:
        service = self._service_repository.get_by_key(payload.service_key)

        if service is None:
            raise ServiceNotFoundError(payload.service_key)

        return self._sla_exclusion_repository.create_exclusion(
            service_id=service.id,
            name=payload.name,
            reason=payload.reason,
            approved_by=payload.approved_by,
            start_at=payload.start_at,
            end_at=payload.end_at,
            eventid=payload.eventid,
        )
