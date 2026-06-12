from dataclasses import dataclass
from decimal import Decimal

from app.models.sla_rule import SlaRule
from app.repositories.service_repository import ServiceRepository
from app.repositories.sla_rule_repository import SlaRuleRepository


@dataclass(frozen=True)
class CreateSlaRuleInput:
    service_key: str
    name: str
    target_percentage: Decimal


class ServiceNotFoundError(Exception):
    pass


def _validate_target_percentage(target_percentage: Decimal) -> None:
    if not Decimal("0") <= target_percentage <= Decimal("100"):
        raise ValueError("target_percentage must be between 0 and 100")


class CreateSlaRuleUseCase:
    def __init__(
        self,
        service_repository: ServiceRepository,
        sla_rule_repository: SlaRuleRepository,
    ) -> None:
        self._service_repository = service_repository
        self._sla_rule_repository = sla_rule_repository

    def execute(self, payload: CreateSlaRuleInput) -> SlaRule:
        _validate_target_percentage(payload.target_percentage)
        service = self._service_repository.get_by_key(payload.service_key)

        if service is None:
            raise ServiceNotFoundError(payload.service_key)

        return self._sla_rule_repository.create_rule(
            service_id=service.id,
            name=payload.name,
            target_percentage=payload.target_percentage,
        )
