from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.db.session import SessionLocal, initialize_database
from app.models.sla_result import SlaResult


class SlaResultConflictError(Exception):
    pass


class SqlAlchemySlaResultRepository:
    def __init__(self, session: Session | None = None) -> None:
        initialize_database()
        self._session = session

    @contextmanager
    def _session_scope(self) -> Iterator[Session]:
        if self._session is not None:
            yield self._session
            return

        session = SessionLocal()

        try:
            yield session
        finally:
            session.close()

    def create_result(
        self,
        *,
        service_id,
        sla_rule_id,
        period_start: datetime,
        period_end: datetime,
        total_minutes: int,
        original_total_minutes: int,
        downtime_minutes: int,
        raw_downtime_minutes: int,
        maintenance_excluded_minutes: int,
        downtime_excluded_by_maintenance_minutes: int,
        sla_exclusion_minutes: int,
        downtime_excluded_by_sla_exclusions_minutes: int,
        availability_percent: Decimal,
        target_percentage: Decimal,
        meets_target: bool,
        matched_problems_count: int,
        merged_intervals_count: int,
        source_type: str,
        source_value: str,
    ) -> SlaResult:
        with self._session_scope() as session:
            result = SlaResult(
                service_id=service_id,
                sla_rule_id=sla_rule_id,
                period_start=period_start,
                period_end=period_end,
                total_minutes=total_minutes,
                original_total_minutes=original_total_minutes,
                downtime_minutes=downtime_minutes,
                raw_downtime_minutes=raw_downtime_minutes,
                maintenance_excluded_minutes=maintenance_excluded_minutes,
                downtime_excluded_by_maintenance_minutes=downtime_excluded_by_maintenance_minutes,
                sla_exclusion_minutes=sla_exclusion_minutes,
                downtime_excluded_by_sla_exclusions_minutes=downtime_excluded_by_sla_exclusions_minutes,
                availability_percent=availability_percent,
                target_percentage=target_percentage,
                meets_target=meets_target,
                matched_problems_count=matched_problems_count,
                merged_intervals_count=merged_intervals_count,
                source_type=source_type,
                source_value=source_value,
            )
            session.add(result)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise SlaResultConflictError("result_already_exists") from exc

            session.refresh(result)
            return result

    def get_by_service_key_and_period(
        self,
        *,
        service_key: str,
        period_start: datetime,
        period_end: datetime,
    ) -> list[SlaResult]:
        with self._session_scope() as session:
            return list(
                session.execute(
                    select(SlaResult)
                    .join(SlaResult.service)
                    .where(SlaResult.period_start == period_start)
                    .where(SlaResult.period_end == period_end)
                    .where(SlaResult.service.has(key=service_key))
                    .order_by(SlaResult.period_start.desc())
                ).scalars()
            )

    def list_by_service_key(
        self,
        *,
        service_key: str,
        limit: int = 12,
    ) -> list[SlaResult]:
        with self._session_scope() as session:
            return list(
                session.execute(
                    select(SlaResult)
                    .where(SlaResult.service.has(key=service_key))
                    .order_by(SlaResult.period_start.asc(), SlaResult.period_end.asc())
                    .limit(limit)
                ).scalars()
            )

    def list_by_period(
        self,
        *,
        period_start: datetime,
        period_end: datetime,
        source_type: Optional[str] = None,
    ) -> list[SlaResult]:
        with self._session_scope() as session:
            statement = (
                select(SlaResult)
                .where(SlaResult.period_start == period_start)
                .where(SlaResult.period_end == period_end)
                .order_by(SlaResult.availability_percent.desc(), SlaResult.period_start.asc())
            )

            if source_type is not None:
                statement = statement.where(SlaResult.source_type == source_type)

            return list(session.execute(statement).scalars())


SlaResultRepository = SqlAlchemySlaResultRepository
