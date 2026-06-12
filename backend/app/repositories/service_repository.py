from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.service_catalog.entities import ServiceCatalogItem
from app.infrastructure.db.session import SessionLocal, initialize_database
from app.models.service import Service


class ServiceKeyConflictError(Exception):
    pass


class SqlAlchemyServiceRepository:
    def __init__(self, session: Session | None = None) -> None:
        initialize_database()

        self._session = session
        self._lock = Lock()

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

    def create(self, service: ServiceCatalogItem) -> ServiceCatalogItem:
        created = self.create_service(
            name=service.name,
            key=service.key,
            source_type=service.source_type,
            source_value=service.source_value,
            is_active=service.is_active,
        )

        return ServiceCatalogItem(
            id=created.id,
            name=created.name,
            key=created.key,
            source_type=created.source_type,
            source_value=created.source_value,
            is_active=created.is_active,
        )

    def create_service(
        self,
        *,
        name: str,
        key: str,
        source_type: str,
        source_value: str,
        is_active: bool = True,
    ) -> Service:
        with self._lock:
            with self._session_scope() as session:
                service = Service(
                    name=name,
                    key=key,
                    source_type=source_type,
                    source_value=source_value,
                    is_active=is_active,
                )

                session.add(service)

                try:
                    session.commit()
                except IntegrityError as exc:
                    session.rollback()
                    raise ServiceKeyConflictError(key) from exc

                session.refresh(service)
                return service

    def get_by_key(self, key: str) -> Service | None:
        with self._session_scope() as session:
            return session.execute(
                select(Service).where(Service.key == key)
            ).scalar_one_or_none()


ServiceRepository = SqlAlchemyServiceRepository
