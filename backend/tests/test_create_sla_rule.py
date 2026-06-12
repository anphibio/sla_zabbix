import importlib
import os

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.schemas.sla_rule import SlaRuleCreate


@pytest.fixture
def database_url(tmp_path) -> str:
    database_path = tmp_path / "create-sla-rule.db"
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
    from app.application.sla import create_sla_rule as create_sla_rule_module
    from app.api.v1 import services as services_module
    from app.api.v1 import sla_rules as sla_rules_module
    from app.infrastructure.db import session as session_module
    from app.repositories import service_repository as service_repository_module
    from app.repositories import sla_rule_repository as sla_rule_repository_module
    from app import main as main_module

    monkeypatch.setenv("DATABASE_URL", database_url)

    importlib.reload(session_module)
    importlib.reload(service_repository_module)
    importlib.reload(sla_rule_repository_module)
    importlib.reload(create_service_module)
    importlib.reload(create_sla_rule_module)
    importlib.reload(services_module)
    importlib.reload(sla_rules_module)
    reloaded_main = importlib.reload(main_module)

    return TestClient(reloaded_main.app)


def test_sla_rule_create_schema_accepts_service_key() -> None:
    payload = SlaRuleCreate(
        service_key="postgresql-producao",
        name="Produção mensal",
        target_percentage="99.90",
    )

    assert payload.service_key == "postgresql-producao"


def test_sla_rule_create_schema_rejects_target_percentage_out_of_range() -> None:
    with pytest.raises(ValidationError):
        SlaRuleCreate(
            service_key="postgresql-producao",
            name="Produção mensal",
            target_percentage="100.01",
        )


def test_create_sla_rule_for_existing_service(build_client) -> None:
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
            "/api/v1/sla-rules",
            json={
                "service_key": "postgresql-producao",
                "name": "Produção mensal",
                "target_percentage": "99.90",
            },
        )

    assert service_response.status_code == 201
    assert response.status_code == 201
    assert response.json() == {
        "success": True,
        "data": {
            "service_key": "postgresql-producao",
            "name": "Produção mensal",
            "target_percentage": "99.90",
            "is_active": True,
        },
        "message": "Regra de SLA criada",
        "errors": [],
    }


def test_create_sla_rule_returns_404_when_service_is_missing(build_client) -> None:
    with build_client() as client:
        response = client.post(
            "/api/v1/sla-rules",
            json={
                "service_key": "postgresql-inexistente",
                "name": "Produção mensal",
                "target_percentage": "99.90",
            },
        )

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "data": None,
        "message": "Serviço não encontrado",
        "errors": ["service_not_found"],
    }
