import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.models.report_schedule_run import ReportScheduleRun


class ReportSchedule(Base):
    __tablename__ = "report_schedules"
    __table_args__ = (
        CheckConstraint("day_of_month >= 1 AND day_of_month <= 28", name="ck_report_schedules_day_of_month_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_format: Mapped[str] = mapped_column(String(10), nullable=False)
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_template: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    day_of_month: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    runs: Mapped[list["ReportScheduleRun"]] = relationship(back_populates="schedule")
