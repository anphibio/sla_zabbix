import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.models.sla_result import SlaResult


class SlaRule(Base):
    __tablename__ = "sla_rules"
    __table_args__ = (
        CheckConstraint(
            "target_percentage >= 0 AND target_percentage <= 100",
            name="ck_sla_rules_target_percentage_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("services.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("99.90")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sla_results: Mapped[list["SlaResult"]] = relationship(back_populates="sla_rule")
    service: Mapped["Service"] = relationship(back_populates="sla_rules")
