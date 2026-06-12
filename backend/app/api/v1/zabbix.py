from fastapi import APIRouter, Depends, Request

from app.application.zabbix.validate_connection import (
    ValidateZabbixConnectionUseCase,
)
from app.infrastructure.zabbix.client import ZabbixClient


router = APIRouter(prefix="/api/v1/zabbix", tags=["zabbix"])


def get_zabbix_client(request: Request) -> ZabbixClient:
    return request.app.state.zabbix_client


def get_validate_connection_use_case(
    client: ZabbixClient = Depends(get_zabbix_client),
) -> ValidateZabbixConnectionUseCase:
    return ValidateZabbixConnectionUseCase(client)


@router.get("/validate")
def validate_connection(
    use_case: ValidateZabbixConnectionUseCase = Depends(
        get_validate_connection_use_case
    ),
) -> dict[str, object]:
    result = use_case.execute()

    return {
        "success": True,
        "data": {
            "status": result.status,
            "method": result.method,
            "url": result.url,
        },
        "message": "Conectividade validada",
        "errors": [],
    }
