import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.models.service import Service
    from app.models.sla_rule import SlaRule


class SlaResult(Base):
    __tablename__ = "sla_results"
    __table_args__ = (
        UniqueConstraint(
            "service_id",
            "sla_rule_id",
            "period_start",
            "period_end",
            name="uq_sla_results_service_rule_period",
        ),
        CheckConstraint(
            "target_percentage >= 0 AND target_percentage <= 100",
            name="ck_sla_results_target_percentage_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    service_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("services.id"), nullable=False
    )
    sla_rule_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sla_rules.id"), nullable=False
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    original_total_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    downtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_downtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    maintenance_excluded_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    downtime_excluded_by_maintenance_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    sla_exclusion_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    downtime_excluded_by_sla_exclusions_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    availability_percent: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    target_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    meets_target: Mapped[bool] = mapped_column(Boolean, nullable=False)
    matched_problems_count: Mapped[int] = mapped_column(Integer, nullable=False)
    merged_intervals_count: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_value: Mapped[str] = mapped_column(String(255), nullable=False)

    service: Mapped["Service"] = relationship(back_populates="sla_results")
    sla_rule: Mapped["SlaRule"] = relationship(back_populates="sla_results")
