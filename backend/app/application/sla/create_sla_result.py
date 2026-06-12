from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.application.sla.preview_zabbix_service_sla import (
    ActiveSlaRuleNotFoundError,
    InvalidServiceSourceError,
    PreviewZabbixServiceSlaInput,
    PreviewZabbixServiceSlaUseCase,
    ServiceNotFoundError,
    SourceMappingNotFoundError,
    ZabbixQueryError,
)
from app.models.sla_result import SlaResult
from app.repositories.sla_result_repository import (
    SlaResultConflictError,
    SlaResultRepository,
)


@dataclass(frozen=True)
class CreateSlaResultInput:
    service_key: str
    period_start: datetime
    period_end: datetime

    def __post_init__(self) -> None:
        if self.period_start.tzinfo is None or self.period_end.tzinfo is None:
            raise ValueError("period boundaries must be timezone-aware")
        if self.period_end <= self.period_start:
            raise ValueError("period_end must be greater than period_start")


class CreateSlaResultUseCase:
    def __init__(
        self,
        preview_use_case: PreviewZabbixServiceSlaUseCase,
        sla_result_repository: SlaResultRepository,
    ) -> None:
        self._preview_use_case = preview_use_case
        self._sla_result_repository = sla_result_repository

    def execute(self, payload: CreateSlaResultInput) -> SlaResult:
        preview = self._preview_use_case.execute(
            PreviewZabbixServiceSlaInput(
                service_key=payload.service_key,
                period_start=payload.period_start,
                period_end=payload.period_end,
            )
        )

        return self._sla_result_repository.create_result(
            service_id=preview.service.id,
            sla_rule_id=preview.rule.id,
            period_start=preview.period_start,
            period_end=preview.period_end,
            total_minutes=preview.total_minutes,
            original_total_minutes=preview.original_total_minutes,
            downtime_minutes=preview.downtime_minutes,
            raw_downtime_minutes=preview.raw_downtime_minutes,
            maintenance_excluded_minutes=preview.maintenance_excluded_minutes,
            downtime_excluded_by_maintenance_minutes=preview.downtime_excluded_by_maintenance_minutes,
            sla_exclusion_minutes=preview.sla_exclusion_minutes,
            downtime_excluded_by_sla_exclusions_minutes=preview.downtime_excluded_by_sla_exclusions_minutes,
            availability_percent=Decimal(str(preview.availability_percent)),
            target_percentage=preview.target_percentage,
            meets_target=preview.meets_target,
            matched_problems_count=preview.matched_problems_count,
            merged_intervals_count=preview.merged_intervals_count,
            source_type=preview.service.source_type,
            source_value=preview.service.source_value,
        )
