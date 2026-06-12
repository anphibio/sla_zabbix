from time import monotonic

from fastapi import APIRouter

from app.core.config import settings


router = APIRouter()
START_TIME = monotonic()


@router.get("/ready")
def ready() -> dict[str, object]:
    return {"status": "pending", "checks": {"database": "pending"}}


@router.get("/metrics")
def metrics() -> dict[str, object]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "uptime_seconds": monotonic() - START_TIME,
        "requests_total": 0,
        "request_errors_total": 0,
    }
