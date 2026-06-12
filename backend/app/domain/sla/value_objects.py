from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceSlaSnapshot:
    total_minutes: int
    downtime_minutes: int
    availability_percent: float

    def __post_init__(self) -> None:
        if self.total_minutes <= 0:
            raise ValueError("total_minutes must be greater than zero")
        if self.downtime_minutes < 0:
            raise ValueError("downtime_minutes must be zero or greater")
        if self.downtime_minutes > self.total_minutes:
            raise ValueError("downtime_minutes cannot be greater than total_minutes")
        if not 0 <= self.availability_percent <= 100:
            raise ValueError("availability_percent must be between 0 and 100")
