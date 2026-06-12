import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.models.report_schedule import ReportSchedule


class ReportScheduleRun(Base):
    __tablename__ = "report_schedule_runs"
    __table_args__ = (
        UniqueConstraint(
            "schedule_id",
            "period_start",
            "period_end",
            name="uq_report_schedule_runs_schedule_period",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("report_schedules.id"), nullable=False
    )
    reference_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    delivery_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    schedule: Mapped["ReportSchedule"] = relationship(back_populates="runs")
