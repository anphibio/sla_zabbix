from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.session import SessionLocal, initialize_database
from app.models.sla_exclusion import SlaExclusion


class SqlAlchemySlaExclusionRepository:
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

    def create_exclusion(
        self,
        *,
        service_id,
        name: str,
        reason: str,
        approved_by: str,
        start_at: datetime,
        end_at: datetime,
        eventid: Optional[str] = None,
        is_active: bool = True,
    ) -> SlaExclusion:
        with self._session_scope() as session:
            exclusion = SlaExclusion(
                service_id=service_id,
                name=name,
                reason=reason,
                approved_by=approved_by,
                start_at=start_at,
                end_at=end_at,
                eventid=eventid,
                is_active=is_active,
            )
            session.add(exclusion)
            session.commit()
            session.refresh(exclusion)
            return exclusion

    def get_active_exclusions_by_service_id_and_period(
        self,
        *,
        service_id,
        period_start: datetime,
        period_end: datetime,
    ) -> list[SlaExclusion]:
        with self._session_scope() as session:
            return list(
                session.execute(
                    select(SlaExclusion)
                    .where(SlaExclusion.service_id == service_id)
                    .where(SlaExclusion.is_active.is_(True))
                    .where(SlaExclusion.start_at < period_end)
                    .where(SlaExclusion.end_at > period_start)
                    .order_by(SlaExclusion.start_at.asc(), SlaExclusion.end_at.asc())
                ).scalars()
            )


SlaExclusionRepository = SqlAlchemySlaExclusionRepository
