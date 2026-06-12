from dataclasses import dataclass
from decimal import Decimal

from app.domain.sla.calculator import calculate_availability_percent
from app.domain.sla.value_objects import ServiceSlaSnapshot
from app.models.service import Service
from app.models.sla_rule import SlaRule
from app.repositories.service_repository import ServiceRepository
from app.repositories.sla_rule_repository import SlaRuleRepository


@dataclass(frozen=True)
class CalculateServiceSlaInput:
    total_minutes: int
    downtime_minutes: int

    def __post_init__(self) -> None:
        if self.total_minutes <= 0:
            raise ValueError("total_minutes must be greater than zero")
        if self.downtime_minutes < 0:
            raise ValueError("downtime_minutes must be zero or greater")
        if self.downtime_minutes > self.total_minutes:
            raise ValueError("downtime_minutes cannot be greater than total_minutes")


class CalculateServiceSlaUseCase:
    def execute(self, payload: CalculateServiceSlaInput) -> ServiceSlaSnapshot:
        availability_percent = calculate_availability_percent(
            total_minutes=payload.total_minutes,
            downtime_minutes=payload.downtime_minutes,
        )
        return ServiceSlaSnapshot(
            total_minutes=payload.total_minutes,
            downtime_minutes=payload.downtime_minutes,
            availability_percent=availability_percent,
        )


@dataclass(frozen=True)
class SlaPreviewInput:
    service_key: str
    total_minutes: int
    downtime_minutes: int

    def __post_init__(self) -> None:
        CalculateServiceSlaInput(
            total_minutes=self.total_minutes,
            downtime_minutes=self.downtime_minutes,
        )


@dataclass(frozen=True)
class SlaPreviewResult:
    service: Service
    rule: SlaRule
    total_minutes: int
    downtime_minutes: int
    availability_percent: float
    meets_target: bool

    @property
    def target_percentage(self) -> Decimal:
        return self.rule.target_percentage


class StoredServiceNotFoundError(Exception):
    pass


class ActiveSlaRuleNotFoundError(Exception):
    pass


class CalculateStoredServiceSlaUseCase:
    def __init__(
        self,
        service_repository: ServiceRepository,
        sla_rule_repository: SlaRuleRepository,
    ) -> None:
        self._service_repository = service_repository
        self._sla_rule_repository = sla_rule_repository
        self._calculator = CalculateServiceSlaUseCase()

    def execute(self, payload: SlaPreviewInput) -> SlaPreviewResult:
        service = self._service_repository.get_by_key(payload.service_key)

        if service is None:
            raise StoredServiceNotFoundError(payload.service_key)

        rule = self._sla_rule_repository.get_active_rule_by_service_id(service.id)

        if rule is None:
            raise ActiveSlaRuleNotFoundError(payload.service_key)

        snapshot = self._calculator.execute(
            CalculateServiceSlaInput(
                total_minutes=payload.total_minutes,
                downtime_minutes=payload.downtime_minutes,
            )
        )

        meets_target = Decimal(str(snapshot.availability_percent)) >= rule.target_percentage

        return SlaPreviewResult(
            service=service,
            rule=rule,
            total_minutes=snapshot.total_minutes,
            downtime_minutes=snapshot.downtime_minutes,
            availability_percent=snapshot.availability_percent,
            meets_target=meets_target,
        )
