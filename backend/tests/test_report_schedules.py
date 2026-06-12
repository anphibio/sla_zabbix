import importlib
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def database_url(tmp_path) -> str:
    database_path = tmp_path / "report-schedules.db"
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
    from app.application.reports import create_report_schedule as create_report_schedule_module
    from app.application.reports import run_due_report_schedules as run_due_report_schedules_module
    from app.core import config as config_module
    from app.application.service_catalog import create_service as create_service_module
    from app.application.sla import create_sla_result as create_sla_result_module
    from app.application.sla import create_sla_rule as create_sla_rule_module
    from app.application.sla import preview_zabbix_service_sla as preview_module
    from app.api.v1 import report_schedules as report_schedules_module
    from app.api.v1 import services as services_module
    from app.api.v1 import sla_results as sla_results_module
    from app.api.v1 import sla_rules as sla_rules_module
    from app.infrastructure.db import session as session_module
    from app.infrastructure.email import client as email_client_module
    from app.infrastructure.zabbix import client as zabbix_client_module
    from app.repositories import maintenance_window_repository as maintenance_window_repository_module
    from app.repositories import report_schedule_repository as report_schedule_repository_module
    from app.repositories import report_schedule_run_repository as report_schedule_run_repository_module
    from app.repositories import service_repository as service_repository_module
    from app.repositories import sla_exclusion_repository as sla_exclusion_repository_module
    from app.repositories import sla_result_repository as sla_result_repository_module
    from app.repositories import sla_rule_repository as sla_rule_repository_module
    from app import main as main_module
    from app.infrastructure.zabbix.client import ZabbixClient

    monkeypatch.setenv("DATABASE_URL", database_url)

    importlib.reload(config_module)
    importlib.reload(session_module)
    importlib.reload(email_client_module)
    importlib.reload(zabbix_client_module)
    importlib.reload(maintenance_window_repository_module)
    importlib.reload(report_schedule_repository_module)
    importlib.reload(report_schedule_run_repository_module)
    importlib.reload(service_repository_module)
    importlib.reload(sla_exclusion_repository_module)
    importlib.reload(sla_result_repository_module)
    importlib.reload(sla_rule_repository_module)
    importlib.reload(create_report_schedule_module)
    importlib.reload(run_due_report_schedules_module)
    importlib.reload(create_service_module)
    importlib.reload(create_sla_result_module)
    importlib.reload(create_sla_rule_module)
    importlib.reload(preview_module)
    importlib.reload(report_schedules_module)
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


def test_create_report_schedule(monkeypatch: pytest.MonkeyPatch, build_client) -> None:
    monkeypatch.setenv("SMTP_HOST", "smtp.example.local")
    monkeypatch.setenv("SMTP_SENDER_EMAIL", "noreply@example.local")

    with build_client(lambda url, payload: {"result": []}) as client:
        response = client.post(
            "/api/v1/report-schedules",
            json={
                "name": "Executivo Mensal Tag",
                "report_format": "xlsx",
                "source_type": "tag",
                "recipient_email": "gestao@example.local",
                "subject_template": "SLA Executivo Mensal",
                "day_of_month": 5,
            },
        )

    assert response.status_code == 201
    assert response.json() == {
        "success": True,
        "data": {
            "name": "Executivo Mensal Tag",
            "report_format": "xlsx",
            "source_type": "tag",
            "recipient_email": "gestao@example.local",
            "subject_template": "SLA Executivo Mensal",
            "day_of_month": 5,
            "is_active": True,
        },
        "message": "Agendamento criado",
        "errors": [],
    }


def test_run_due_report_schedules_generates_file(
    monkeypatch: pytest.MonkeyPatch,
    build_client,
) -> None:
    event_sequences = [
        ("s1", "1780272000", "1780273080", "service:postgresql"),
        ("s2", "1780272000", "1780275600", "service:mysql"),
    ]
    state = {"index": 0}

    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        current = event_sequences[min(state["index"] // 2, len(event_sequences) - 1)]
        method = payload["method"]
        params = payload["params"]

        if method == "event.get" and "eventids" not in params:
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

    monkeypatch.setenv("SMTP_HOST", "smtp.example.local")
    monkeypatch.setenv("SMTP_SENDER_EMAIL", "noreply@example.local")

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

        schedule_response = client.post(
            "/api/v1/report-schedules",
            json={
                "name": "Executivo Mensal Tag",
                "report_format": "pdf",
                "source_type": "tag",
                "recipient_email": "gestao@example.local",
                "subject_template": "SLA Executivo Mensal",
                "day_of_month": 5,
            },
        )
        run_response = client.post(
            "/api/v1/report-schedules/run-due",
            json={"reference_date": "2026-07-05T10:00:00Z"},
        )

    assert schedule_response.status_code == 201
    assert run_response.status_code == 200
    data = run_response.json()["data"]
    assert len(data) == 1
    assert data[0]["schedule_name"] == "Executivo Mensal Tag"
    assert data[0]["report_format"] == "pdf"
    assert data[0]["status"] == "generated"
    assert data[0]["delivery_status"] == "failed"
    assert data[0]["period_start"] == "2026-06-01T00:00:00Z"
    assert data[0]["period_end"] == "2026-07-01T00:00:00Z"
    assert data[0]["file_path"] is not None
    generated_file = Path(data[0]["file_path"])
    assert generated_file.exists()
    assert generated_file.read_bytes().startswith(b"%PDF")


def test_run_due_report_schedules_marks_sent_when_email_succeeds(monkeypatch: pytest.MonkeyPatch, build_client) -> None:
    event_sequences = [("e1", "1780272000", "1780273080", "service:postgresql")]
    state = {"index": 0}

    class FakeSmtp:
        def __init__(self, host, port):
            self.host = host
            self.port = port
            self.started_tls = False
            self.logged_in = False
            self.sent = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            self.started_tls = True

        def login(self, username, password):
            self.logged_in = True

        def send_message(self, message):
            self.sent = True

    def fake_transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        current = event_sequences[min(state["index"] // 2, len(event_sequences) - 1)]
        method = payload["method"]
        params = payload["params"]

        if method == "event.get" and "eventids" not in params:
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
            state["index"] += 2
            return {
                "result": [
                    {"eventid": str(params["eventids"][0]), "clock": current[2], "value": "0"}
                ]
            }

        raise AssertionError(payload)

    monkeypatch.setenv("SMTP_HOST", "smtp.example.local")
    monkeypatch.setenv("SMTP_SENDER_EMAIL", "noreply@example.local")

    with build_client(fake_transport) as client:
        from app.infrastructure.email import client as email_client_module

        monkeypatch.setattr(email_client_module.smtplib, "SMTP", FakeSmtp)
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
                "name": "Mensal",
                "target_percentage": "99.90",
            },
        )
        client.post(
            "/api/v1/sla-results",
            json={
                "service_key": "postgresql-producao",
                "period_start": "2026-06-01T00:00:00Z",
                "period_end": "2026-07-01T00:00:00Z",
            },
        )
        client.post(
            "/api/v1/report-schedules",
            json={
                "name": "Executivo Mensal Tag",
                "report_format": "pdf",
                "source_type": "tag",
                "recipient_email": "gestao@example.local",
                "subject_template": "SLA Executivo Mensal",
                "day_of_month": 5,
            },
        )
        run_response = client.post(
            "/api/v1/report-schedules/run-due",
            json={"reference_date": "2026-07-05T10:00:00Z"},
        )

    assert run_response.status_code == 200
    assert run_response.json()["data"][0]["delivery_status"] == "sent"
