from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.session import SessionLocal, initialize_database
from app.models.report_schedule import ReportSchedule


class SqlAlchemyReportScheduleRepository:
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

    def create_schedule(
        self,
        *,
        name: str,
        report_format: str,
        source_type: Optional[str],
        recipient_email: str,
        subject_template: Optional[str],
        day_of_month: int,
        is_active: bool = True,
    ) -> ReportSchedule:
        with self._session_scope() as session:
            schedule = ReportSchedule(
                name=name,
                report_format=report_format,
                source_type=source_type,
                recipient_email=recipient_email,
                subject_template=subject_template,
                day_of_month=day_of_month,
                is_active=is_active,
            )
            session.add(schedule)
            session.commit()
            session.refresh(schedule)
            return schedule

    def list_active_schedules_due_on_day(self, day_of_month: int) -> list[ReportSchedule]:
        with self._session_scope() as session:
            return list(
                session.execute(
                    select(ReportSchedule)
                    .where(ReportSchedule.is_active.is_(True))
                    .where(ReportSchedule.day_of_month == day_of_month)
                    .order_by(ReportSchedule.name.asc())
                ).scalars()
            )


ReportScheduleRepository = SqlAlchemyReportScheduleRepository
