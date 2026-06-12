from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.zabbix.client import ZabbixClient


def test_zabbix_client_builds_payload() -> None:
    client = ZabbixClient(
        url="https://zabbix.example/api_jsonrpc.php",
        token="secret",
    )

    payload = client.build_request(method="apiinfo.version", params={})

    assert payload["jsonrpc"] == "2.0"
    assert payload["method"] == "apiinfo.version"
    assert payload["params"] == {}
    assert payload["id"] == 1
    assert payload["auth"] == "secret"


def test_zabbix_client_calls_transport_and_returns_result() -> None:
    calls: list[dict[str, object]] = []

    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        calls.append({"url": url, "payload": payload})
        return {"result": [{"eventid": "10"}]}

    client = ZabbixClient(
        url="https://zabbix.example/api_jsonrpc.php",
        token="secret",
        transport=fake_transport,
    )

    result = client.call("event.get", {"output": ["eventid"]})

    assert result == [{"eventid": "10"}]
    assert calls == [
        {
            "url": "https://zabbix.example/api_jsonrpc.php",
            "payload": {
                "jsonrpc": "2.0",
                "method": "event.get",
                "params": {"output": ["eventid"]},
                "id": 1,
                "auth": "secret",
            },
        }
    ]


def test_zabbix_client_builds_trigger_event_query_from_tag() -> None:
    captured_payloads: list[dict[str, object]] = []

    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        captured_payloads.append(payload)
        return {"result": []}

    client = ZabbixClient(
        url="https://zabbix.example/api_jsonrpc.php",
        token="secret",
        transport=fake_transport,
    )

    client.get_trigger_events(
        time_from=1717200000,
        time_till=1717286400,
        tag_name="service",
        tag_value="postgresql",
    )

    assert captured_payloads[0]["method"] == "event.get"
    assert captured_payloads[0]["params"] == {
        "output": ["eventid", "clock", "name", "severity", "r_eventid", "value"],
        "source": 0,
        "object": 0,
        "value": 1,
        "problem_time_from": 1717200000,
        "problem_time_till": 1717286400,
        "sortfield": ["clock", "eventid"],
        "sortorder": "ASC",
        "selectTags": "extend",
        "evaltype": 0,
        "tags": [
            {
                "tag": "service",
                "value": "postgresql",
                "operator": 1,
            }
        ],
    }


def test_validate_connection_endpoint_returns_safe_metadata_only() -> None:
    app.state.zabbix_client = ZabbixClient(
        url="https://zabbix.example/api_jsonrpc.php",
        token="super-secret",
    )
    client = TestClient(app)

    response = client.get("/api/v1/zabbix/validate")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {
            "status": "pending-live-check",
            "method": "apiinfo.version",
            "url": "https://zabbix.example/api_jsonrpc.php",
        },
        "message": "Conectividade validada",
        "errors": [],
    }
    assert "auth" not in response.text
