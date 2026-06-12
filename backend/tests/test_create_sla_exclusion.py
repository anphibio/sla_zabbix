import importlib
import os

import pytest
from fastapi.testclient import TestClient

from app.schemas.sla_exclusion import SlaExclusionCreate


@pytest.fixture
def database_url(tmp_path) -> str:
    database_path = tmp_path / "create-sla-exclusion.db"
    return f"sqlite+pysqlite:///{database_path}"


@pytest.fixture
def build_client(monkeypatch: pytest.MonkeyPatch, database_url: str):
    original_database_url = os.environ.get("DATABASE_URL")

    def factory() -> TestClient:
        return _build_test_client(monkeypatch, database_url)

    yield factory

    if original_database_url is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", original_database_url)


def _build_test_client(
    monkeypatch: pytest.MonkeyPatch,
    database_url: str,
) -> TestClient:
    from app.application.service_catalog import create_service as create_service_module
    from app.application.sla import create_sla_exclusion as create_sla_exclusion_module
    from app.api.v1 import services as services_module
    from app.api.v1 import sla_exclusions as sla_exclusions_module
    from app.infrastructure.db import session as session_module
    from app.repositories import service_repository as service_repository_module
    from app.repositories import sla_exclusion_repository as sla_exclusion_repository_module
    from app import main as main_module

    monkeypatch.setenv("DATABASE_URL", database_url)

    importlib.reload(session_module)
    importlib.reload(service_repository_module)
    importlib.reload(sla_exclusion_repository_module)
    importlib.reload(create_service_module)
    importlib.reload(create_sla_exclusion_module)
    importlib.reload(services_module)
    importlib.reload(sla_exclusions_module)
    reloaded_main = importlib.reload(main_module)

    return TestClient(reloaded_main.app)


def test_sla_exclusion_schema_accepts_eventid() -> None:
    payload = SlaExclusionCreate(
        service_key="postgresql-producao",
        name="Incidente fornecedor",
        reason="Falha elétrica externa aprovada para exclusão",
        approved_by="Gestão de Infra",
        start_at="2026-06-15T01:00:00Z",
        end_at="2026-06-15T02:00:00Z",
        eventid="5001",
    )

    assert payload.eventid == "5001"


def test_create_sla_exclusion_for_existing_service(build_client) -> None:
    with build_client() as client:
        service_response = client.post(
            "/api/v1/services",
            json={
                "name": "PostgreSQL Produção",
                "key": "postgresql-producao",
                "source_type": "tag",
                "source_value": "service:postgresql",
            },
        )
        response = client.post(
            "/api/v1/sla-exclusions",
            json={
                "service_key": "postgresql-producao",
                "name": "Incidente fornecedor",
                "reason": "Falha elétrica externa aprovada para exclusão",
                "approved_by": "Gestão de Infra",
                "start_at": "2026-06-15T01:00:00Z",
                "end_at": "2026-06-15T02:00:00Z",
                "eventid": "5001",
            },
        )

    assert service_response.status_code == 201
    assert response.status_code == 201
    assert response.json() == {
        "success": True,
        "data": {
            "service_key": "postgresql-producao",
            "name": "Incidente fornecedor",
            "reason": "Falha elétrica externa aprovada para exclusão",
            "approved_by": "Gestão de Infra",
            "start_at": "2026-06-15T01:00:00Z",
            "end_at": "2026-06-15T02:00:00Z",
            "eventid": "5001",
            "is_active": True,
        },
        "message": "Exclusão de SLA criada",
        "errors": [],
    }


def test_create_sla_exclusion_returns_400_for_invalid_period(build_client) -> None:
    with build_client() as client:
        service_response = client.post(
            "/api/v1/services",
            json={
                "name": "PostgreSQL Produção",
                "key": "postgresql-producao",
                "source_type": "tag",
                "source_value": "service:postgresql",
            },
        )
        response = client.post(
            "/api/v1/sla-exclusions",
            json={
                "service_key": "postgresql-producao",
                "name": "Incidente fornecedor",
                "reason": "Falha elétrica externa aprovada para exclusão",
                "approved_by": "Gestão de Infra",
                "start_at": "2026-06-15T02:00:00Z",
                "end_at": "2026-06-15T01:00:00Z",
            },
        )

    assert service_response.status_code == 201
    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "data": None,
        "message": "Exclusão de SLA inválida",
        "errors": ["end_at must be greater than start_at"],
    }
