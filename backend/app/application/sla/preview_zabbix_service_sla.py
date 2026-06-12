from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from app.application.sla.calculate_service_sla import (
    CalculateServiceSlaInput,
    CalculateServiceSlaUseCase,
)
from app.infrastructure.zabbix.client import ZabbixApiError, ZabbixClient
from app.models.maintenance_window import MaintenanceWindow
from app.models.service import Service
from app.models.sla_exclusion import SlaExclusion
from app.models.sla_rule import SlaRule
from app.repositories.maintenance_window_repository import MaintenanceWindowRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.sla_exclusion_repository import SlaExclusionRepository
from app.repositories.sla_rule_repository import SlaRuleRepository


@dataclass(frozen=True)
class PreviewZabbixServiceSlaInput:
    service_key: str
    period_start: datetime
    period_end: datetime

    def __post_init__(self) -> None:
        if self.period_start.tzinfo is None or self.period_end.tzinfo is None:
            raise ValueError("period boundaries must be timezone-aware")
        if self.period_end <= self.period_start:
            raise ValueError("period_end must be greater than period_start")


@dataclass(frozen=True)
class ZabbixProblemInterval:
    eventid: str
    name: str
    severity: int
    started_at: datetime
    recovered_at: datetime
    downtime_minutes: int


@dataclass(frozen=True)
class MaintenanceWindowInterval:
    name: str
    description: str
    started_at: datetime
    ended_at: datetime
    excluded_minutes: int


@dataclass(frozen=True)
class SlaExclusionInterval:
    name: str
    reason: str
    approved_by: str
    eventid: Optional[str]
    started_at: datetime
    ended_at: datetime
    excluded_minutes: int


@dataclass(frozen=True)
class PreviewZabbixServiceSlaResult:
    service: Service
    rule: SlaRule
    period_start: datetime
    period_end: datetime
    total_minutes: int
    original_total_minutes: int
    downtime_minutes: int
    raw_downtime_minutes: int
    maintenance_excluded_minutes: int
    downtime_excluded_by_maintenance_minutes: int
    sla_exclusion_minutes: int
    downtime_excluded_by_sla_exclusions_minutes: int
    availability_percent: float
    meets_target: bool
    matched_problems_count: int
    merged_intervals_count: int
    problems: list[ZabbixProblemInterval]
    maintenance_windows: list[MaintenanceWindowInterval]
    sla_exclusions: list[SlaExclusionInterval]

    @property
    def target_percentage(self) -> Decimal:
        return self.rule.target_percentage


class ServiceNotFoundError(Exception):
    pass


class ActiveSlaRuleNotFoundError(Exception):
    pass


class InvalidServiceSourceError(Exception):
    pass


class SourceMappingNotFoundError(Exception):
    pass


class ZabbixQueryError(Exception):
    pass


class PreviewZabbixServiceSlaUseCase:
    def __init__(
        self,
        service_repository: ServiceRepository,
        sla_rule_repository: SlaRuleRepository,
        maintenance_window_repository: MaintenanceWindowRepository,
        sla_exclusion_repository: SlaExclusionRepository,
        zabbix_client: ZabbixClient,
    ) -> None:
        self._service_repository = service_repository
        self._sla_rule_repository = sla_rule_repository
        self._maintenance_window_repository = maintenance_window_repository
        self._sla_exclusion_repository = sla_exclusion_repository
        self._zabbix_client = zabbix_client
        self._calculator = CalculateServiceSlaUseCase()

    def execute(
        self,
        payload: PreviewZabbixServiceSlaInput,
    ) -> PreviewZabbixServiceSlaResult:
        service = self._service_repository.get_by_key(payload.service_key)

        if service is None:
            raise ServiceNotFoundError(payload.service_key)

        rule = self._sla_rule_repository.get_active_rule_by_service_id(service.id)

        if rule is None:
            raise ActiveSlaRuleNotFoundError(payload.service_key)

        try:
            problem_events = self._load_problem_events(service, payload)
            problems = self._build_problem_intervals(
                period_start=payload.period_start,
                period_end=payload.period_end,
                problem_events=problem_events,
            )
        except ZabbixApiError as exc:
            raise ZabbixQueryError(str(exc)) from exc

        merged_intervals = self._merge_intervals(
            [(problem.started_at, problem.recovered_at) for problem in problems]
        )
        maintenance_windows = self._build_maintenance_intervals(
            period_start=payload.period_start,
            period_end=payload.period_end,
            windows=self._maintenance_window_repository.get_active_windows_by_service_id_and_period(
                service_id=service.id,
                period_start=payload.period_start,
                period_end=payload.period_end,
            ),
        )
        merged_maintenance_intervals = self._merge_intervals(
            [(window.started_at, window.ended_at) for window in maintenance_windows]
        )
        sla_exclusions = self._build_sla_exclusion_intervals(
            period_start=payload.period_start,
            period_end=payload.period_end,
            exclusions=self._sla_exclusion_repository.get_active_exclusions_by_service_id_and_period(
                service_id=service.id,
                period_start=payload.period_start,
                period_end=payload.period_end,
            ),
        )
        merged_sla_exclusion_intervals = self._merge_intervals(
            [(exclusion.started_at, exclusion.ended_at) for exclusion in sla_exclusions]
        )
        merged_non_sla_intervals = self._merge_intervals(
            merged_maintenance_intervals + merged_sla_exclusion_intervals
        )
        original_total_minutes = _duration_in_minutes(
            payload.period_start, payload.period_end
        )
        maintenance_excluded_minutes = sum(
            _duration_in_minutes(started_at, ended_at)
            for started_at, ended_at in merged_maintenance_intervals
        )
        sla_exclusion_minutes = sum(
            _duration_in_minutes(started_at, ended_at)
            for started_at, ended_at in merged_sla_exclusion_intervals
        )
        total_excluded_minutes = sum(
            _duration_in_minutes(started_at, ended_at)
            for started_at, ended_at in merged_non_sla_intervals
        )
        total_minutes = max(1, original_total_minutes - total_excluded_minutes)
        raw_downtime_minutes = sum(
            _duration_in_minutes(started_at, recovered_at)
            for started_at, recovered_at in merged_intervals
        )
        downtime_excluded_by_maintenance_minutes = self._calculate_overlap_minutes(
            merged_intervals,
            merged_maintenance_intervals,
        )
        downtime_excluded_by_sla_exclusions_minutes = self._calculate_overlap_minutes(
            merged_intervals,
            merged_sla_exclusion_intervals,
        )
        downtime_excluded_total_minutes = self._calculate_overlap_minutes(
            merged_intervals,
            merged_non_sla_intervals,
        )
        downtime_minutes = max(
            0,
            raw_downtime_minutes - downtime_excluded_total_minutes,
        )

        snapshot = self._calculator.execute(
            CalculateServiceSlaInput(
                total_minutes=total_minutes,
                downtime_minutes=downtime_minutes,
            )
        )

        meets_target = Decimal(str(snapshot.availability_percent)) >= rule.target_percentage

        return PreviewZabbixServiceSlaResult(
            service=service,
            rule=rule,
            period_start=payload.period_start,
            period_end=payload.period_end,
            total_minutes=snapshot.total_minutes,
            original_total_minutes=original_total_minutes,
            downtime_minutes=snapshot.downtime_minutes,
            raw_downtime_minutes=raw_downtime_minutes,
            maintenance_excluded_minutes=maintenance_excluded_minutes,
            downtime_excluded_by_maintenance_minutes=downtime_excluded_by_maintenance_minutes,
            sla_exclusion_minutes=sla_exclusion_minutes,
            downtime_excluded_by_sla_exclusions_minutes=downtime_excluded_by_sla_exclusions_minutes,
            availability_percent=snapshot.availability_percent,
            meets_target=meets_target,
            matched_problems_count=len(problems),
            merged_intervals_count=len(merged_intervals),
            problems=problems,
            maintenance_windows=maintenance_windows,
            sla_exclusions=sla_exclusions,
        )

    def _load_problem_events(
        self,
        service: Service,
        payload: PreviewZabbixServiceSlaInput,
    ) -> list[dict[str, object]]:
        time_from = int(payload.period_start.timestamp())
        time_till = int(payload.period_end.timestamp())

        if service.source_type == "tag":
            tag_name, tag_value = _parse_tag_source_value(service.source_value)
            return self._zabbix_client.get_trigger_events(
                time_from=time_from,
                time_till=time_till,
                tag_name=tag_name,
                tag_value=tag_value,
            )

        if service.source_type == "hostgroup":
            group = self._zabbix_client.get_hostgroup_by_name(service.source_value)

            if group is None:
                raise SourceMappingNotFoundError(service.source_value)

            return self._zabbix_client.get_trigger_events(
                time_from=time_from,
                time_till=time_till,
                groupids=[group["groupid"]],
            )

        raise InvalidServiceSourceError(service.source_type)

    def _build_problem_intervals(
        self,
        *,
        period_start: datetime,
        period_end: datetime,
        problem_events: list[dict[str, object]],
    ) -> list[ZabbixProblemInterval]:
        recovery_eventids = [
            str(event["r_eventid"])
            for event in problem_events
            if str(event.get("r_eventid", "0")) not in {"", "0"}
        ]
        recovery_events = self._zabbix_client.get_events_by_ids(recovery_eventids)
        recovery_by_id = {
            str(event["eventid"]): _clock_to_datetime(event["clock"])
            for event in recovery_events
        }
        problems: list[ZabbixProblemInterval] = []

        for event in problem_events:
            started_at = _clock_to_datetime(event["clock"])
            recovered_at = recovery_by_id.get(str(event.get("r_eventid", "0")), period_end)

            clipped_start = max(started_at, period_start)
            clipped_end = min(recovered_at, period_end)

            if clipped_end <= clipped_start:
                continue

            problems.append(
                ZabbixProblemInterval(
                    eventid=str(event["eventid"]),
                    name=str(event.get("name", "Evento Zabbix")),
                    severity=int(str(event.get("severity", "0"))),
                    started_at=clipped_start,
                    recovered_at=clipped_end,
                    downtime_minutes=_duration_in_minutes(clipped_start, clipped_end),
                )
            )

        return problems

    def _build_maintenance_intervals(
        self,
        *,
        period_start: datetime,
        period_end: datetime,
        windows: list[MaintenanceWindow],
    ) -> list[MaintenanceWindowInterval]:
        intervals: list[MaintenanceWindowInterval] = []

        for window in windows:
            window_start = _ensure_utc(window.start_at)
            window_end = _ensure_utc(window.end_at)
            clipped_start = max(window_start, period_start)
            clipped_end = min(window_end, period_end)

            if clipped_end <= clipped_start:
                continue

            intervals.append(
                MaintenanceWindowInterval(
                    name=window.name,
                    description=window.description,
                    started_at=clipped_start,
                    ended_at=clipped_end,
                    excluded_minutes=_duration_in_minutes(clipped_start, clipped_end),
                )
            )

        return intervals

    def _build_sla_exclusion_intervals(
        self,
        *,
        period_start: datetime,
        period_end: datetime,
        exclusions: list[SlaExclusion],
    ) -> list[SlaExclusionInterval]:
        intervals: list[SlaExclusionInterval] = []

        for exclusion in exclusions:
            exclusion_start = _ensure_utc(exclusion.start_at)
            exclusion_end = _ensure_utc(exclusion.end_at)
            clipped_start = max(exclusion_start, period_start)
            clipped_end = min(exclusion_end, period_end)

            if clipped_end <= clipped_start:
                continue

            intervals.append(
                SlaExclusionInterval(
                    name=exclusion.name,
                    reason=exclusion.reason,
                    approved_by=exclusion.approved_by,
                    eventid=exclusion.eventid,
                    started_at=clipped_start,
                    ended_at=clipped_end,
                    excluded_minutes=_duration_in_minutes(clipped_start, clipped_end),
                )
            )

        return intervals

    @staticmethod
    def _merge_intervals(
        intervals: list[tuple[datetime, datetime]],
    ) -> list[tuple[datetime, datetime]]:
        if not intervals:
            return []

        sorted_intervals = sorted(intervals, key=lambda interval: interval[0])
        merged: list[tuple[datetime, datetime]] = [sorted_intervals[0]]

        for started_at, recovered_at in sorted_intervals[1:]:
            last_started_at, last_recovered_at = merged[-1]

            if started_at <= last_recovered_at:
                merged[-1] = (
                    last_started_at,
                    max(last_recovered_at, recovered_at),
                )
                continue

            merged.append((started_at, recovered_at))

        return merged

    @staticmethod
    def _calculate_overlap_minutes(
        problem_intervals: list[tuple[datetime, datetime]],
        maintenance_intervals: list[tuple[datetime, datetime]],
    ) -> int:
        total = 0
        maintenance_index = 0

        for problem_start, problem_end in problem_intervals:
            while (
                maintenance_index < len(maintenance_intervals)
                and maintenance_intervals[maintenance_index][1] <= problem_start
            ):
                maintenance_index += 1

            current_index = maintenance_index

            while current_index < len(maintenance_intervals):
                maintenance_start, maintenance_end = maintenance_intervals[current_index]

                if maintenance_start >= problem_end:
                    break

                overlap_start = max(problem_start, maintenance_start)
                overlap_end = min(problem_end, maintenance_end)

                if overlap_end > overlap_start:
                    total += _duration_in_minutes(overlap_start, overlap_end)

                current_index += 1

        return total


def _parse_tag_source_value(source_value: str) -> tuple[str, str]:
    tag_name, separator, tag_value = source_value.partition(":")

    if separator == "" or not tag_name.strip() or not tag_value.strip():
        raise InvalidServiceSourceError(source_value)

    return tag_name.strip(), tag_value.strip()


def _clock_to_datetime(clock: object) -> datetime:
    return datetime.fromtimestamp(int(str(clock)), tz=timezone.utc)


def _duration_in_minutes(started_at: datetime, recovered_at: datetime) -> int:
    seconds = (recovered_at - started_at).total_seconds()
    return max(1, math.ceil(seconds / 60))


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)
