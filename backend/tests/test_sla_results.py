import importlib
import os
from io import BytesIO
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def database_url(tmp_path) -> str:
    database_path = tmp_path / "sla-results.db"
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
    from app.application.sla import create_sla_result as create_sla_result_module
    from app.application.sla import create_sla_rule as create_sla_rule_module
    from app.application.sla import preview_zabbix_service_sla as preview_module
    from app.api.v1 import services as services_module
    from app.api.v1 import sla_results as sla_results_module
    from app.api.v1 import sla_rules as sla_rules_module
    from app.infrastructure.db import session as session_module
    from app.infrastructure.zabbix import client as zabbix_client_module
    from app.repositories import maintenance_window_repository as maintenance_window_repository_module
    from app.repositories import service_repository as service_repository_module
    from app.repositories import sla_exclusion_repository as sla_exclusion_repository_module
    from app.repositories import sla_result_repository as sla_result_repository_module
    from app.repositories import sla_rule_repository as sla_rule_repository_module
    from app import main as main_module
    from app.infrastructure.zabbix.client import ZabbixClient

    monkeypatch.setenv("DATABASE_URL", database_url)

    importlib.reload(session_module)
    importlib.reload(zabbix_client_module)
    importlib.reload(maintenance_window_repository_module)
    importlib.reload(service_repository_module)
    importlib.reload(sla_exclusion_repository_module)
    importlib.reload(sla_result_repository_module)
    importlib.reload(sla_rule_repository_module)
    importlib.reload(create_service_module)
    importlib.reload(create_sla_result_module)
    importlib.reload(create_sla_rule_module)
    importlib.reload(preview_module)
    importlib.reload(services_module)
    importlib.reload(sla_results_module)
    importlib.reload(sla_rules_module)
    reloaded_main = importlib.reload(main_module)
    reloaded_main.app.state.zabbix_client = ZabbixClient(
        url="https://zabbix.example/api_jsonrpc.php",
        token="secret",
        transport=fake_transport,
    )

    return TestClient(reloaded_main.app)


def test_create_monthly_sla_result_and_read_it_back(build_client) -> None:
    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        params = payload["params"]

        if payload["method"] == "event.get" and "eventids" not in params:
            return {
                "result": [
                    {
                        "eventid": "9001",
                        "clock": "1780272000",
                        "name": "PostgreSQL indisponivel",
                        "severity": "4",
                        "r_eventid": "9002",
                        "value": "1",
                    }
                ]
            }

        if payload["method"] == "event.get" and "eventids" in params:
            return {
                "result": [
                    {"eventid": "9002", "clock": "1780273080", "value": "0"}
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
                "name": "Produção mensal",
                "target_percentage": "99.90",
            },
        )
        create_response = client.post(
            "/api/v1/sla-results",
            json={
                "service_key": "postgresql-producao",
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-07-01T00:00:00Z",
            },
        )
        list_response = client.get(
            "/api/v1/sla-results",
            params={
                "service_key": "postgresql-producao",
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-07-01T00:00:00Z",
            },
        )

    assert service_response.status_code == 201
    assert rule_response.status_code == 201
    assert create_response.status_code == 201
    assert create_response.json()["data"]["availability_percent"] == "99.9583"
    assert create_response.json()["data"]["rule_name"] == "Produção mensal"
    assert list_response.status_code == 200
    assert list_response.json()["data"] == [create_response.json()["data"]]


def test_create_monthly_sla_result_rejects_duplicate_period(build_client) -> None:
    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        params = payload["params"]

        if payload["method"] == "event.get" and "eventids" not in params:
            return {
                "result": [
                    {
                        "eventid": "9001",
                        "clock": "1780272000",
                        "name": "PostgreSQL indisponivel",
                        "severity": "4",
                        "r_eventid": "9002",
                        "value": "1",
                    }
                ]
            }

        if payload["method"] == "event.get" and "eventids" in params:
            return {
                "result": [
                    {"eventid": "9002", "clock": "1780273080", "value": "0"}
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
                "name": "Produção mensal",
                "target_percentage": "99.90",
            },
        )
        first_response = client.post(
            "/api/v1/sla-results",
            json={
                "service_key": "postgresql-producao",
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-07-01T00:00:00Z",
            },
        )
        second_response = client.post(
            "/api/v1/sla-results",
            json={
                "service_key": "postgresql-producao",
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-07-01T00:00:00Z",
            },
        )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "success": False,
        "data": None,
        "message": "Resultado mensal já existe para este período",
        "errors": ["result_already_exists"],
    }


def test_sla_results_history_returns_series_and_trend_summary(build_client) -> None:
    event_payloads = [
        (
            "1780272000",
            "1780273080",
            "2026-06-01T00:00:00Z",
            "2026-07-01T00:00:00Z",
        ),
        (
            "1782864000",
            "1782864600",
            "2026-07-01T00:00:00Z",
            "2026-08-01T00:00:00Z",
        ),
    ]
    call_index = {"value": 0}

    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        current_pair = event_payloads[min(call_index["value"] // 2, len(event_payloads) - 1)]
        if payload["method"] == "event.get" and "eventids" not in payload["params"]:
            return {
                "result": [
                    {
                        "eventid": f"hist-{call_index['value']}",
                        "clock": current_pair[0],
                        "name": "PostgreSQL indisponivel",
                        "severity": "4",
                        "r_eventid": f"hist-r-{call_index['value']}",
                        "value": "1",
                    }
                ]
            }

        if payload["method"] == "event.get" and "eventids" in payload["params"]:
            response = {
                "result": [
                    {
                        "eventid": str(payload["params"]["eventids"][0]),
                        "clock": current_pair[1],
                        "value": "0",
                    }
                ]
            }
            call_index["value"] += 2
            return response

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
                "name": "Produção mensal",
                "target_percentage": "99.90",
            },
        )
        first_create = client.post(
            "/api/v1/sla-results",
            json={
                "service_key": "postgresql-producao",
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-07-01T00:00:00Z",
            },
        )
        second_create = client.post(
            "/api/v1/sla-results",
            json={
                "service_key": "postgresql-producao",
                "period_start": "2026-07-01T00:00:00Z",
                "period_end": "2026-08-01T00:00:00Z",
            },
        )
        history_response = client.get(
            "/api/v1/sla-results/history",
            params={"service_key": "postgresql-producao", "limit": 12},
        )

    assert first_create.status_code == 201
    assert second_create.status_code == 201
    assert history_response.status_code == 200
    assert history_response.json() == {
        "success": True,
        "data": {
            "service_key": "postgresql-producao",
            "periods": [
                {
                    "period_start": "2026-06-01T00:00:00Z",
                    "period_end": "2026-07-01T00:00:00Z",
                    "availability_percent": "99.9583",
                    "target_percentage": "99.90",
                    "meets_target": True,
                    "downtime_minutes": 18,
                },
                {
                    "period_start": "2026-07-01T00:00:00Z",
                    "period_end": "2026-08-01T00:00:00Z",
                    "availability_percent": "99.9776",
                    "target_percentage": "99.90",
                    "meets_target": True,
                    "downtime_minutes": 10,
                },
            ],
            "summary": {
                "current_availability_percent": "99.9776",
                "previous_availability_percent": "99.9583",
                "delta_percent": "0.0193",
                "trend_direction": "up",
                "periods_count": 2,
                "best_availability_percent": "99.9776",
                "worst_availability_percent": "99.9583",
            },
        },
        "message": "Histórico de SLA carregado",
        "errors": [],
    }


def test_sla_results_executive_returns_consolidated_summary(build_client) -> None:
    event_sequences = [
        ("9801", "1780272000", "1780273080", "service:postgresql", "postgresql-producao", "tag"),
        ("9802", "1780272000", "1780275600", "service:mysql", "mysql-producao", "tag"),
        ("9803", "1780272000", "1780272600", "Windows Servers", "windows-producao", "hostgroup"),
    ]
    state = {"index": 0}

    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        current = event_sequences[min(state["index"] // 2, len(event_sequences) - 1)]
        method = payload["method"]
        params = payload["params"]

        if method == "hostgroup.get":
            return {"result": [{"groupid": "501", "name": "Windows Servers"}]}

        if method == "event.get" and "eventids" not in params:
            if "tags" in params:
                expected_value = current[3].split(":", 1)[1]
                assert params["tags"][0]["value"] == expected_value
            if "groupids" in params:
                assert params["groupids"] == ["501"]
            return {
                "result": [
                    {
                        "eventid": current[0],
                        "clock": current[1],
                        "name": "Indisponibilidade",
                        "severity": "4",
                        "r_eventid": f"{current[0]}-r",
                        "value": "1",
                    }
                ]
            }

        if method == "event.get" and "eventids" in params:
            response = {
                "result": [
                    {
                        "eventid": str(params["eventids"][0]),
                        "clock": current[2],
                        "value": "0",
                    }
                ]
            }
            state["index"] += 2
            return response

        raise AssertionError(payload)

    with build_client(fake_transport) as client:
        for name, key, source_type, source_value, target in [
            ("PostgreSQL Produção", "postgresql-producao", "tag", "service:postgresql", "99.90"),
            ("MySQL Produção", "mysql-producao", "tag", "service:mysql", "99.90"),
            ("Windows Produção", "windows-producao", "hostgroup", "Windows Servers", "95.00"),
        ]:
            client.post(
                "/api/v1/services",
                json={
                    "name": name,
                    "key": key,
                    "source_type": source_type,
                    "source_value": source_value,
                },
            )
            client.post(
                "/api/v1/sla-rules",
                json={
                    "service_key": key,
                    "name": "Mensal",
                    "target_percentage": target,
                },
            )
            client.post(
                "/api/v1/sla-results",
                json={
                    "service_key": key,
                    "period_start": "2026-06-01T00:00:00Z",
                    "period_end": "2026-07-01T00:00:00Z",
                },
            )

        executive_response = client.get(
            "/api/v1/sla-results/executive",
            params={
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-07-01T00:00:00Z",
            },
        )
        tags_only_response = client.get(
            "/api/v1/sla-results/executive",
            params={
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-07-01T00:00:00Z",
                "source_type": "tag",
            },
        )

    assert executive_response.status_code == 200
    assert executive_response.json() == {
        "success": True,
        "data": {
            "source_type": None,
            "summary": {
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-07-01T00:00:00Z",
                "services_count": 3,
                "compliant_services_count": 2,
                "non_compliant_services_count": 1,
                "weighted_availability_percent": "99.9321",
                "average_availability_percent": "99.9321",
                "best_availability_percent": "99.9769",
                "worst_availability_percent": "99.8611",
            },
            "services": [
                {
                    "service_key": "windows-producao",
                    "rule_name": "Mensal",
                    "source_type": "hostgroup",
                    "availability_percent": "99.9769",
                    "target_percentage": "95.00",
                    "meets_target": True,
                    "downtime_minutes": 10,
                    "total_minutes": 43200,
                },
                {
                    "service_key": "postgresql-producao",
                    "rule_name": "Mensal",
                    "source_type": "tag",
                    "availability_percent": "99.9583",
                    "target_percentage": "99.90",
                    "meets_target": True,
                    "downtime_minutes": 18,
                    "total_minutes": 43200,
                },
                {
                    "service_key": "mysql-producao",
                    "rule_name": "Mensal",
                    "source_type": "tag",
                    "availability_percent": "99.8611",
                    "target_percentage": "99.90",
                    "meets_target": False,
                    "downtime_minutes": 60,
                    "total_minutes": 43200,
                },
            ],
        },
        "message": "Consolidação executiva de SLA carregada",
        "errors": [],
    }
    assert tags_only_response.status_code == 200
    assert tags_only_response.json()["data"]["source_type"] == "tag"
    assert tags_only_response.json()["data"]["summary"]["services_count"] == 2


def test_sla_results_executive_xlsx_download_returns_workbook(build_client) -> None:
    event_sequences = [
        ("9901", "1780272000", "1780273080", "service:postgresql"),
        ("9902", "1780272000", "1780275600", "service:mysql"),
    ]
    state = {"index": 0}

    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        current = event_sequences[min(state["index"] // 2, len(event_sequences) - 1)]
        method = payload["method"]
        params = payload["params"]

        if method == "event.get" and "eventids" not in params:
            assert params["tags"][0]["value"] == current[3].split(":", 1)[1]
            return {
                "result": [
                    {
                        "eventid": current[0],
                        "clock": current[1],
                        "name": "Indisponibilidade",
                        "severity": "4",
                        "r_eventid": f"{current[0]}-r",
                        "value": "1",
                    }
                ]
            }

        if method == "event.get" and "eventids" in params:
            response = {
                "result": [
                    {
                        "eventid": str(params["eventids"][0]),
                        "clock": current[2],
                        "value": "0",
                    }
                ]
            }
            state["index"] += 2
            return response

        raise AssertionError(payload)

    with build_client(fake_transport) as client:
        for name, key, source_value in [
            ("PostgreSQL Produção", "postgresql-producao", "service:postgresql"),
            ("MySQL Produção", "mysql-producao", "service:mysql"),
        ]:
            client.post(
                "/api/v1/services",
                json={
                    "name": name,
                    "key": key,
                    "source_type": "tag",
                    "source_value": source_value,
                },
            )
            client.post(
                "/api/v1/sla-rules",
                json={
                    "service_key": key,
                    "name": "Mensal",
                    "target_percentage": "99.90",
                },
            )
            client.post(
                "/api/v1/sla-results",
                json={
                    "service_key": key,
                    "period_start": "2026-06-01T00:00:00Z",
                    "period_end": "2026-07-01T00:00:00Z",
                },
            )

        export_response = client.get(
            "/api/v1/sla-results/executive.xlsx",
            params={
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-07-01T00:00:00Z",
                "source_type": "tag",
            },
        )

    assert export_response.status_code == 200
    assert (
        export_response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment; filename=" in export_response.headers["content-disposition"]

    with ZipFile(BytesIO(export_response.content)) as workbook:
        names = set(workbook.namelist())
        assert "[Content_Types].xml" in names
        assert "xl/workbook.xml" in names
        assert "xl/worksheets/sheet1.xml" in names
        assert "xl/worksheets/sheet2.xml" in names

        summary_xml = workbook.read("xl/worksheets/sheet1.xml").decode("utf-8")
        services_xml = workbook.read("xl/worksheets/sheet2.xml").decode("utf-8")

    assert "Quantidade de servicos" in summary_xml
    assert "2" in summary_xml
    assert "postgresql-producao" in services_xml
    assert "mysql-producao" in services_xml


def test_sla_results_executive_pdf_download_returns_pdf(build_client) -> None:
    event_sequences = [
        ("9951", "1780272000", "1780273080", "service:postgresql"),
        ("9952", "1780272000", "1780275600", "service:mysql"),
    ]
    state = {"index": 0}

    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        current = event_sequences[min(state["index"] // 2, len(event_sequences) - 1)]
        method = payload["method"]
        params = payload["params"]

        if method == "event.get" and "eventids" not in params:
            assert params["tags"][0]["value"] == current[3].split(":", 1)[1]
            return {
                "result": [
                    {
                        "eventid": current[0],
                        "clock": current[1],
                        "name": "Indisponibilidade",
                        "severity": "4",
                        "r_eventid": f"{current[0]}-r",
                        "value": "1",
                    }
                ]
            }

        if method == "event.get" and "eventids" in params:
            response = {
                "result": [
                    {
                        "eventid": str(params["eventids"][0]),
                        "clock": current[2],
                        "value": "0",
                    }
                ]
            }
            state["index"] += 2
            return response

        raise AssertionError(payload)

    with build_client(fake_transport) as client:
        for name, key, source_value in [
            ("PostgreSQL Produção", "postgresql-producao", "service:postgresql"),
            ("MySQL Produção", "mysql-producao", "service:mysql"),
        ]:
            client.post(
                "/api/v1/services",
                json={
                    "name": name,
                    "key": key,
                    "source_type": "tag",
                    "source_value": source_value,
                },
            )
            client.post(
                "/api/v1/sla-rules",
                json={
                    "service_key": key,
                    "name": "Mensal",
                    "target_percentage": "99.90",
                },
            )
            client.post(
                "/api/v1/sla-results",
                json={
                    "service_key": key,
                    "period_start": "2026-06-01T00:00:00Z",
                    "period_end": "2026-07-01T00:00:00Z",
                },
            )

        export_response = client.get(
            "/api/v1/sla-results/executive.pdf",
            params={
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-07-01T00:00:00Z",
                "source_type": "tag",
            },
        )

    assert export_response.status_code == 200
    assert export_response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in export_response.headers["content-disposition"]
    assert export_response.content.startswith(b"%PDF")
    assert b"Consolidacao Executiva de SLA" in export_response.content
    assert b"postgresql-producao" in export_response.content
    assert b"mysql-producao" in export_response.content
