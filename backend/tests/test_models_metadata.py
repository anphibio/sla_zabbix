from decimal import Decimal

from app.models.maintenance_window import MaintenanceWindow
from app.models.report_schedule import ReportSchedule
from app.models.report_schedule_run import ReportScheduleRun
from app.models.service import Service
from app.models.sla_exclusion import SlaExclusion
from app.models.sla_result import SlaResult
from app.models.sla_rule import SlaRule
from app.models.user import User


def test_core_models_have_tablenames() -> None:
    assert User.__tablename__ == "users"
    assert MaintenanceWindow.__tablename__ == "maintenance_windows"
    assert ReportSchedule.__tablename__ == "report_schedules"
    assert ReportScheduleRun.__tablename__ == "report_schedule_runs"
    assert Service.__tablename__ == "services"
    assert SlaExclusion.__tablename__ == "sla_exclusions"
    assert SlaResult.__tablename__ == "sla_results"
    assert SlaRule.__tablename__ == "sla_rules"


def test_unique_columns_are_not_declared_as_separate_indexes() -> None:
    assert User.__table__.c.email.unique is True
    assert User.__table__.c.email.index is None

    assert Service.__table__.c.key.unique is True
    assert Service.__table__.c.key.index is None


def test_sla_rule_target_percentage_uses_decimal_default() -> None:
    default = SlaRule.__table__.c.target_percentage.default

    assert default is not None
    assert default.arg == Decimal("99.90")


def test_maintenance_window_has_period_order_constraint() -> None:
    constraint_names = {
        constraint.name for constraint in MaintenanceWindow.__table__.constraints
    }

    assert any(
        name is not None and name.endswith("ck_maintenance_windows_period_order")
        for name in constraint_names
    )


def test_sla_exclusion_has_period_order_constraint() -> None:
    constraint_names = {
        constraint.name for constraint in SlaExclusion.__table__.constraints
    }

    assert any(
        name is not None and name.endswith("ck_sla_exclusions_period_order")
        for name in constraint_names
    )


def test_sla_result_has_unique_service_rule_period_constraint() -> None:
    constraint_names = {constraint.name for constraint in SlaResult.__table__.constraints}

    assert any(
        name is not None and name.endswith("uq_sla_results_service_rule_period")
        for name in constraint_names
    )


def test_report_schedule_has_day_of_month_constraint() -> None:
    constraint_names = {
        constraint.name for constraint in ReportSchedule.__table__.constraints
    }

    assert any(
        name is not None and name.endswith("ck_report_schedules_day_of_month_range")
        for name in constraint_names
    )
