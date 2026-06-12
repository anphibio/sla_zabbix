import importlib
import os

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.zabbix.client import ZabbixClient


@pytest.fixture
def database_url(tmp_path) -> str:
    database_path = tmp_path / "zabbix-sla-preview.db"
    return f"sqlite+pysqlite:///{database_path}"


@pytest.fixture
def build_client(monkeypatch: pytest.MonkeyPatch, database_url: str):
    original_database_url = os.environ.get("DATABASE_URL")

    def factory(fake_transport) -> TestClient:
        return _build_test_client(monkeypatch, database_url, fake_transport)

    yield factory

    if original_database_url is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", original_database_url)


def _build_test_client(
    monkeypatch: pytest.MonkeyPatch,
    database_url: str,
    fake_transport,
) -> TestClient:
    from app.application.service_catalog import create_service as create_service_module
    from app.application.sla import calculate_service_sla as calculate_service_sla_module
    from app.application.sla import create_maintenance_window as create_maintenance_window_module
    from app.application.sla import create_sla_exclusion as create_sla_exclusion_module
    from app.application.sla import create_sla_rule as create_sla_rule_module
    from app.application.sla import preview_zabbix_service_sla as preview_module
    from app.api.v1 import maintenance_windows as maintenance_windows_module
    from app.api.v1 import services as services_module
    from app.api.v1 import sla_exclusions as sla_exclusions_module
    from app.api.v1 import sla_rules as sla_rules_module
    from app.api.v1 import zabbix_sla_preview as preview_route_module
    from app.infrastructure.db import session as session_module
    from app.infrastructure.zabbix import client as zabbix_client_module
    from app.repositories import maintenance_window_repository as maintenance_window_repository_module
    from app.repositories import service_repository as service_repository_module
    from app.repositories import sla_exclusion_repository as sla_exclusion_repository_module
    from app.repositories import sla_rule_repository as sla_rule_repository_module
    from app import main as main_module

    monkeypatch.setenv("DATABASE_URL", database_url)

    importlib.reload(session_module)
    importlib.reload(zabbix_client_module)
    importlib.reload(maintenance_window_repository_module)
    importlib.reload(service_repository_module)
    importlib.reload(sla_exclusion_repository_module)
    importlib.reload(sla_rule_repository_module)
    importlib.reload(create_service_module)
    importlib.reload(create_maintenance_window_module)
    importlib.reload(create_sla_exclusion_module)
    importlib.reload(create_sla_rule_module)
    importlib.reload(calculate_service_sla_module)
    importlib.reload(preview_module)
    importlib.reload(maintenance_windows_module)
    importlib.reload(services_module)
    importlib.reload(sla_exclusions_module)
    importlib.reload(sla_rules_module)
    importlib.reload(preview_route_module)
    reloaded_main = importlib.reload(main_module)
    reloaded_main.app.state.zabbix_client = ZabbixClient(
        url="https://zabbix.example/api_jsonrpc.php",
        token="secret",
        transport=fake_transport,
    )

    return TestClient(reloaded_main.app)


def test_preview_from_zabbix_tag_returns_merged_downtime(build_client) -> None:
    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        assert url == "https://zabbix.example/api_jsonrpc.php"

        if payload["method"] != "event.get":
            raise AssertionError(payload)

        params = payload["params"]

        if "eventids" in params:
            return {
                "result": [
                    {"eventid": "2002", "clock": "1780272600", "value": "0"},
                    {"eventid": "2004", "clock": "1780273080", "value": "0"},
                ]
            }

        assert params["tags"] == [
            {"tag": "service", "value": "postgresql", "operator": 1}
        ]
        return {
            "result": [
                {
                    "eventid": "2001",
                    "clock": "1780272000",
                    "name": "PostgreSQL indisponivel",
                    "severity": "4",
                    "r_eventid": "2002",
                    "value": "1",
                },
                {
                    "eventid": "2003",
                    "clock": "1780272300",
                    "name": "PostgreSQL indisponivel",
                    "severity": "4",
                    "r_eventid": "2004",
                    "value": "1",
                },
            ]
        }

    with build_client(fake_transport) as client:
        service_response = client.post(
            "/api/v1/services",
            json={
                "name": "PostgreSQL Produção",
                "key": "postgresql-producao",
                "source_type": "tag",
                "source_value": "service:postgresql",
            },
        )
        rule_response = client.post(
            "/api/v1/sla-rules",
            json={
                "service_key": "postgresql-producao",
                "name": "Produção mensal",
                "target_percentage": "99.90",
            },
        )
        response = client.post(
            "/api/v1/sla/preview/zabbix",
            json={
                "service_key": "postgresql-producao",
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-07-01T00:00:00Z",
            },
        )

    assert service_response.status_code == 201
    assert rule_response.status_code == 201
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "data": {
            "service_key": "postgresql-producao",
            "service_name": "PostgreSQL Produção",
            "rule_name": "Produção mensal",
            "source_type": "tag",
            "source_value": "service:postgresql",
            "period_start": "2026-06-01T00:00:00Z",
            "period_end": "2026-07-01T00:00:00Z",
            "target_percentage": "99.90",
            "original_total_minutes": 43200,
            "total_minutes": 43200,
            "raw_downtime_minutes": 18,
            "downtime_minutes": 18,
            "maintenance_excluded_minutes": 0,
            "downtime_excluded_by_maintenance_minutes": 0,
            "sla_exclusion_minutes": 0,
            "downtime_excluded_by_sla_exclusions_minutes": 0,
            "availability_percent": 99.9583,
            "meets_target": True,
            "matched_problems_count": 2,
            "merged_intervals_count": 1,
            "problems": [
                {
                    "eventid": "2001",
                    "name": "PostgreSQL indisponivel",
                    "severity": 4,
                    "started_at": "2026-06-01T00:00:00Z",
                    "recovered_at": "2026-06-01T00:10:00Z",
                    "downtime_minutes": 10,
                },
                {
                    "eventid": "2003",
                    "name": "PostgreSQL indisponivel",
                    "severity": 4,
                    "started_at": "2026-06-01T00:05:00Z",
                    "recovered_at": "2026-06-01T00:18:00Z",
                    "downtime_minutes": 13,
                },
            ],
            "maintenance_windows": [],
            "sla_exclusions": [],
        },
        "message": "Prévia de SLA com dados do Zabbix calculada",
        "errors": [],
    }


def test_preview_from_zabbix_hostgroup_resolves_group_before_query(build_client) -> None:
    recorded_methods: list[str] = []

    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        assert url == "https://zabbix.example/api_jsonrpc.php"
        recorded_methods.append(str(payload["method"]))
        params = payload["params"]

        if payload["method"] == "hostgroup.get":
            assert params == {
                "output": ["groupid", "name"],
                "filter": {"name": ["Windows Servers"]},
            }
            return {"result": [{"groupid": "301", "name": "Windows Servers"}]}

        if payload["method"] == "event.get" and "eventids" not in params:
            assert params["groupids"] == ["301"]
            return {
                "result": [
                    {
                        "eventid": "3001",
                        "clock": "1780272000",
                        "name": "Windows indisponivel",
                        "severity": "3",
                        "r_eventid": "3002",
                        "value": "1",
                    }
                ]
            }

        if payload["method"] == "event.get" and "eventids" in params:
            return {
                "result": [
                    {"eventid": "3002", "clock": "1780273800", "value": "0"}
                ]
            }

        raise AssertionError(payload)

    with build_client(fake_transport) as client:
        service_response = client.post(
            "/api/v1/services",
            json={
                "name": "Windows Produção",
                "key": "windows-producao",
                "source_type": "hostgroup",
                "source_value": "Windows Servers",
            },
        )
        rule_response = client.post(
            "/api/v1/sla-rules",
            json={
                "service_key": "windows-producao",
                "name": "Produção diária",
                "target_percentage": "95.00",
            },
        )
        response = client.post(
            "/api/v1/sla/preview/zabbix",
            json={
                "service_key": "windows-producao",
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-06-02T00:00:00Z",
            },
        )

    assert service_response.status_code == 201
    assert rule_response.status_code == 201
    assert response.status_code == 200
    assert response.json()["data"]["downtime_minutes"] == 30
    assert response.json()["data"]["availability_percent"] == 97.9167
    assert response.json()["data"]["meets_target"] is True
    assert response.json()["data"]["sla_exclusions"] == []
    assert recorded_methods == ["hostgroup.get", "event.get", "event.get"]


def test_preview_from_zabbix_excludes_planned_maintenance_from_sla(build_client) -> None:
    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        assert url == "https://zabbix.example/api_jsonrpc.php"
        params = payload["params"]

        if payload["method"] == "event.get" and "eventids" not in params:
            return {
                "result": [
                    {
                        "eventid": "4001",
                        "clock": "1780272000",
                        "name": "PostgreSQL indisponivel",
                        "severity": "4",
                        "r_eventid": "4002",
                        "value": "1",
                    }
                ]
            }

        if payload["method"] == "event.get" and "eventids" in params:
            return {
                "result": [
                    {"eventid": "4002", "clock": "1780273800", "value": "0"}
                ]
            }

        raise AssertionError(payload)

    with build_client(fake_transport) as client:
        service_response = client.post(
            "/api/v1/services",
            json={
                "name": "PostgreSQL Produção",
                "key": "postgresql-producao",
                "source_type": "tag",
                "source_value": "service:postgresql",
            },
        )
        rule_response = client.post(
            "/api/v1/sla-rules",
            json={
                "service_key": "postgresql-producao",
                "name": "Produção diária",
                "target_percentage": "99.90",
            },
        )
        maintenance_response = client.post(
            "/api/v1/maintenance-windows",
            json={
                "service_key": "postgresql-producao",
                "name": "Patch mensal",
                "description": "Atualização planejada do banco",
                "start_at": "2026-06-01T00:10:00Z",
                "end_at": "2026-06-01T00:20:00Z",
            },
        )
        response = client.post(
            "/api/v1/sla/preview/zabbix",
            json={
                "service_key": "postgresql-producao",
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-06-02T00:00:00Z",
            },
        )

    assert service_response.status_code == 201
    assert rule_response.status_code == 201
    assert maintenance_response.status_code == 201
    assert response.status_code == 200
    assert response.json()["data"]["original_total_minutes"] == 1440
    assert response.json()["data"]["maintenance_excluded_minutes"] == 10
    assert response.json()["data"]["raw_downtime_minutes"] == 30
    assert response.json()["data"]["downtime_excluded_by_maintenance_minutes"] == 10
    assert response.json()["data"]["total_minutes"] == 1430
    assert response.json()["data"]["downtime_minutes"] == 20
    assert response.json()["data"]["availability_percent"] == 98.6014
    assert response.json()["data"]["maintenance_windows"] == [
        {
            "name": "Patch mensal",
            "description": "Atualização planejada do banco",
            "started_at": "2026-06-01T00:10:00Z",
            "ended_at": "2026-06-01T00:20:00Z",
            "excluded_minutes": 10,
        }
    ]
    assert response.json()["data"]["sla_exclusions"] == []


def test_preview_from_zabbix_excludes_approved_sla_exclusion_from_sla(build_client) -> None:
    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        assert url == "https://zabbix.example/api_jsonrpc.php"
        params = payload["params"]

        if payload["method"] == "event.get" and "eventids" not in params:
            return {
                "result": [
                    {
                        "eventid": "5001",
                        "clock": "1780272000",
                        "name": "PostgreSQL indisponivel",
                        "severity": "4",
                        "r_eventid": "5002",
                        "value": "1",
                    }
                ]
            }

        if payload["method"] == "event.get" and "eventids" in params:
            return {
                "result": [
                    {"eventid": "5002", "clock": "1780273800", "value": "0"}
                ]
            }

        raise AssertionError(payload)

    with build_client(fake_transport) as client:
        client.post(
            "/api/v1/services",
            json={
                "name": "PostgreSQL Produção",
                "key": "postgresql-producao",
                "source_type": "tag",
                "source_value": "service:postgresql",
            },
        )
        client.post(
            "/api/v1/sla-rules",
            json={
                "service_key": "postgresql-producao",
                "name": "Produção diária",
                "target_percentage": "99.90",
            },
        )
        exclusion_response = client.post(
            "/api/v1/sla-exclusions",
            json={
                "service_key": "postgresql-producao",
                "name": "Incidente fornecedor",
                "reason": "Falha elétrica externa aprovada para exclusão",
                "approved_by": "Gestão de Infra",
                "start_at": "2026-06-01T00:15:00Z",
                "end_at": "2026-06-01T00:25:00Z",
                "eventid": "5001",
            },
        )
        response = client.post(
            "/api/v1/sla/preview/zabbix",
            json={
                "service_key": "postgresql-producao",
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-06-02T00:00:00Z",
            },
        )

    assert exclusion_response.status_code == 201
    assert response.status_code == 200
    assert response.json()["data"]["original_total_minutes"] == 1440
    assert response.json()["data"]["sla_exclusion_minutes"] == 10
    assert response.json()["data"]["downtime_excluded_by_sla_exclusions_minutes"] == 10
    assert response.json()["data"]["total_minutes"] == 1430
    assert response.json()["data"]["downtime_minutes"] == 20
    assert response.json()["data"]["availability_percent"] == 98.6014
    assert response.json()["data"]["sla_exclusions"] == [
        {
            "name": "Incidente fornecedor",
            "reason": "Falha elétrica externa aprovada para exclusão",
            "approved_by": "Gestão de Infra",
            "eventid": "5001",
            "started_at": "2026-06-01T00:15:00Z",
            "ended_at": "2026-06-01T00:25:00Z",
            "excluded_minutes": 10,
        }
    ]
