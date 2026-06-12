import pytest

from app.application.sla.calculate_service_sla import CalculateServiceSlaInput
from app.domain.sla.calculator import calculate_availability_percent
from app.domain.sla.value_objects import ServiceSlaSnapshot


def test_calculates_availability_from_minutes() -> None:
    result = calculate_availability_percent(total_minutes=43200, downtime_minutes=18)

    assert result == 99.9583


def test_calculates_full_availability_with_zero_downtime() -> None:
    result = calculate_availability_percent(total_minutes=1440, downtime_minutes=0)

    assert result == 100.0


def test_raises_for_invalid_total_minutes() -> None:
    with pytest.raises(ValueError, match="total_minutes must be greater than zero"):
        calculate_availability_percent(total_minutes=0, downtime_minutes=0)


def test_raises_for_negative_downtime_minutes() -> None:
    with pytest.raises(ValueError, match="downtime_minutes must be zero or greater"):
        calculate_availability_percent(total_minutes=60, downtime_minutes=-1)


def test_raises_when_downtime_exceeds_total_minutes() -> None:
    with pytest.raises(
        ValueError,
        match="downtime_minutes cannot be greater than total_minutes",
    ):
        calculate_availability_percent(total_minutes=60, downtime_minutes=120)


def test_service_sla_snapshot_rejects_negative_minutes() -> None:
    with pytest.raises(ValueError, match="downtime_minutes must be zero or greater"):
        ServiceSlaSnapshot(
            total_minutes=60,
            downtime_minutes=-1,
            availability_percent=100.0,
        )


def test_service_sla_snapshot_rejects_availability_out_of_range() -> None:
    with pytest.raises(
        ValueError,
        match="availability_percent must be between 0 and 100",
    ):
        ServiceSlaSnapshot(
            total_minutes=60,
            downtime_minutes=0,
            availability_percent=100.1,
        )


def test_calculate_service_sla_input_rejects_negative_minutes() -> None:
    with pytest.raises(ValueError, match="downtime_minutes must be zero or greater"):
        CalculateServiceSlaInput(total_minutes=60, downtime_minutes=-1)
