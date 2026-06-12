from dataclasses import dataclass

from app.infrastructure.zabbix.client import ZabbixClient


@dataclass(frozen=True)
class ValidateConnectionResult:
    status: str
    method: str
    url: str


class ValidateZabbixConnectionUseCase:
    def __init__(self, client: ZabbixClient) -> None:
        self.client = client

    def execute(self) -> ValidateConnectionResult:
        request = self.client.build_request(
            method="apiinfo.version",
            params={},
        )
        return ValidateConnectionResult(
            status="pending-live-check",
            method=str(request["method"]),
            url=self.client.url,
        )
