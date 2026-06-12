from os import getenv

from fastapi import FastAPI

from app.api.v1.maintenance_windows import router as maintenance_windows_router
from app.api.v1.report_schedules import router as report_schedules_router
from app.api.v1.services import router as services_router
from app.api.v1.sla_exclusions import router as sla_exclusions_router
from app.api.v1.sla_preview import router as sla_preview_router
from app.api.v1.sla_results import router as sla_results_router
from app.api.v1.sla_rules import router as sla_rules_router
from app.api.v1.system import router as system_router
from app.api.v1.zabbix_sla_preview import router as zabbix_sla_preview_router
from app.api.v1.zabbix import router as zabbix_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.infrastructure.db.session import initialize_database
from app.infrastructure.zabbix.client import ZabbixClient


logger = configure_logging()
initialize_database()

app = FastAPI(title="Zabbix SLA")
app.state.zabbix_client = ZabbixClient(
    url=getenv("ZABBIX_API_URL", "https://zabbix.example/api_jsonrpc.php"),
    token=getenv("ZABBIX_API_TOKEN", ""),
)
app.include_router(system_router)
app.include_router(maintenance_windows_router)
app.include_router(report_schedules_router)
app.include_router(services_router)
app.include_router(sla_exclusions_router)
app.include_router(sla_preview_router)
app.include_router(sla_results_router)
app.include_router(sla_rules_router)
app.include_router(zabbix_sla_preview_router)
app.include_router(zabbix_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": settings.app_name}
