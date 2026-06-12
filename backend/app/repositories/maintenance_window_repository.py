from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.session import SessionLocal, initialize_database
from app.models.maintenance_window import MaintenanceWindow


class SqlAlchemyMaintenanceWindowRepository:
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

    def create_window(
        self,
        *,
        service_id,
        name: str,
        description: str,
        start_at: datetime,
        end_at: datetime,
        is_active: bool = True,
    ) -> MaintenanceWindow:
        with self._session_scope() as session:
            window = MaintenanceWindow(
                service_id=service_id,
                name=name,
                description=description,
                start_at=start_at,
                end_at=end_at,
                is_active=is_active,
            )
            session.add(window)
            session.commit()
            session.refresh(window)
            return window

    def get_active_windows_by_service_id_and_period(
        self,
        *,
        service_id,
        period_start: datetime,
        period_end: datetime,
    ) -> list[MaintenanceWindow]:
        with self._session_scope() as session:
            return list(
                session.execute(
                    select(MaintenanceWindow)
                    .where(MaintenanceWindow.service_id == service_id)
                    .where(MaintenanceWindow.is_active.is_(True))
                    .where(MaintenanceWindow.start_at < period_end)
                    .where(MaintenanceWindow.end_at > period_start)
                    .order_by(
                        MaintenanceWindow.start_at.asc(),
                        MaintenanceWindow.end_at.asc(),
                    )
                ).scalars()
            )


MaintenanceWindowRepository = SqlAlchemyMaintenanceWindowRepository
