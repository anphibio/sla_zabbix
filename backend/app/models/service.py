import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.models.maintenance_window import MaintenanceWindow
    from app.models.sla_exclusion import SlaExclusion
    from app.models.sla_result import SlaResult
    from app.models.sla_rule import SlaRule


class Service(Base):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_value: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    maintenance_windows: Mapped[list["MaintenanceWindow"]] = relationship(
        back_populates="service"
    )
    sla_exclusions: Mapped[list["SlaExclusion"]] = relationship(
        back_populates="service"
    )
    sla_results: Mapped[list["SlaResult"]] = relationship(back_populates="service")
    sla_rules: Mapped[list["SlaRule"]] = relationship(back_populates="service")
