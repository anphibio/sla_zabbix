from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.db.session import SessionLocal, initialize_database
from app.models.report_schedule_run import ReportScheduleRun


class ReportScheduleRunConflictError(Exception):
    pass


class SqlAlchemyReportScheduleRunRepository:
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

    def create_run(
        self,
        *,
        schedule_id,
        reference_date: datetime,
        period_start: datetime,
        period_end: datetime,
        status: str,
        delivery_status: Optional[str] = None,
        file_path: Optional[str] = None,
        message: Optional[str] = None,
    ) -> ReportScheduleRun:
        with self._session_scope() as session:
            run = ReportScheduleRun(
                schedule_id=schedule_id,
                reference_date=reference_date,
                period_start=period_start,
                period_end=period_end,
                status=status,
                delivery_status=delivery_status,
                file_path=file_path,
                message=message,
            )
            session.add(run)
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise ReportScheduleRunConflictError("run_already_exists") from exc
            session.refresh(run)
            return run

    def list_by_schedule_id(self, schedule_id) -> list[ReportScheduleRun]:
        with self._session_scope() as session:
            return list(
                session.execute(
                    select(ReportScheduleRun)
                    .where(ReportScheduleRun.schedule_id == schedule_id)
                    .order_by(ReportScheduleRun.period_start.desc())
                ).scalars()
            )


ReportScheduleRunRepository = SqlAlchemyReportScheduleRunRepository
