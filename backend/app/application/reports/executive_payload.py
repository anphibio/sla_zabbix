from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def serialize_executive_payload(
    results,
    period_start: datetime,
    period_end: datetime,
    source_type: Optional[str],
) -> dict[str, object]:
    service_items = [
        {
            "service_key": result.service.key,
            "rule_name": result.sla_rule.name,
            "source_type": result.source_type,
            "availability_percent": result.availability_percent,
            "target_percentage": result.target_percentage,
            "meets_target": result.meets_target,
            "downtime_minutes": result.downtime_minutes,
            "total_minutes": result.total_minutes,
        }
        for result in results
    ]
    availability_values = [Decimal(str(result.availability_percent)) for result in results]
    total_minutes_sum = sum(result.total_minutes for result in results)
    weighted_numerator = sum(
        Decimal(str(result.availability_percent)) * Decimal(result.total_minutes)
        for result in results
    )
    weighted_availability = (
        (weighted_numerator / Decimal(total_minutes_sum)).quantize(Decimal("0.0001"))
        if total_minutes_sum > 0 and results
        else None
    )
    average_availability = (
        (sum(availability_values) / Decimal(len(availability_values))).quantize(Decimal("0.0001"))
        if availability_values
        else None
    )

    return {
        "source_type": source_type,
        "summary": {
            "period_start": ensure_utc(period_start),
            "period_end": ensure_utc(period_end),
            "services_count": len(results),
            "compliant_services_count": sum(1 for result in results if result.meets_target),
            "non_compliant_services_count": sum(1 for result in results if not result.meets_target),
            "weighted_availability_percent": weighted_availability,
            "average_availability_percent": average_availability,
            "best_availability_percent": max(availability_values) if availability_values else None,
            "worst_availability_percent": min(availability_values) if availability_values else None,
        },
        "services": service_items,
    }
