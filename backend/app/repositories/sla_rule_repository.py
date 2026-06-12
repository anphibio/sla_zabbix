from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.session import SessionLocal, initialize_database
from app.models.sla_rule import SlaRule


class SqlAlchemySlaRuleRepository:
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

    def create_rule(
        self,
        *,
        service_id,
        name: str,
        target_percentage: Decimal,
        is_active: bool = True,
    ) -> SlaRule:
        with self._session_scope() as session:
            rule = SlaRule(
                service_id=service_id,
                name=name,
                target_percentage=target_percentage,
                is_active=is_active,
            )

            session.add(rule)
            session.commit()
            session.refresh(rule)
            return rule

    def get_active_rule_by_service_id(self, service_id) -> SlaRule | None:
        with self._session_scope() as session:
            return session.execute(
                select(SlaRule)
                .where(SlaRule.service_id == service_id)
                .where(SlaRule.is_active.is_(True))
                .order_by(SlaRule.name.asc())
            ).scalars().first()


SlaRuleRepository = SqlAlchemySlaRuleRepository
