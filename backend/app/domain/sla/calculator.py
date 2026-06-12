def calculate_availability_percent(total_minutes: int, downtime_minutes: int) -> float:
    if total_minutes <= 0:
        raise ValueError("total_minutes must be greater than zero")
    if downtime_minutes < 0:
        raise ValueError("downtime_minutes must be zero or greater")
    if downtime_minutes > total_minutes:
        raise ValueError("downtime_minutes cannot be greater than total_minutes")

    uptime_minutes = total_minutes - downtime_minutes
    return round((uptime_minutes / total_minutes) * 100, 4)
