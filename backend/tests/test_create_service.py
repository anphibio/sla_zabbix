import importlib
import os

import pytest
from fastapi.testclient import TestClient

from app.schemas.service import ServiceCreate


@pytest.fixture
def database_url(tmp_path) -> str:
    database_path = tmp_path / "create-service.db"
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
    from app.api.v1 import services as services_module
    from app.infrastructure.db import session as session_module
    from app.repositories import service_repository as repository_module
    from app import main as main_module

    monkeypatch.setenv("DATABASE_URL", database_url)

    importlib.reload(session_module)
    importlib.reload(repository_module)
    importlib.reload(create_service_module)
    importlib.reload(services_module)
    reloaded_main = importlib.reload(main_module)

    return TestClient(reloaded_main.app)


def test_service_create_schema_accepts_tag_strategy() -> None:
    payload = ServiceCreate(
        name="PostgreSQL Produção",
        key="postgresql-producao",
        source_type="tag",
        source_value="service:postgresql",
    )

    assert payload.source_type == "tag"


def test_create_service_endpoint_returns_created_service(build_client) -> None:
    with build_client() as client:
        response = client.post(
            "/api/v1/services",
            json={
                "name": "PostgreSQL Produção",
                "key": "postgresql-producao",
                "source_type": "tag",
                "source_value": "service:postgresql",
            },
        )

        assert response.status_code == 201
        assert response.json() == {
            "success": True,
            "data": {
                "name": "PostgreSQL Produção",
                "key": "postgresql-producao",
                "source_type": "tag",
                "source_value": "service:postgresql",
                "is_active": True,
            },
            "message": "Serviço criado",
            "errors": [],
        }


def test_create_service_endpoint_rejects_duplicate_key_from_database(
    build_client,
) -> None:
    payload = {
        "name": "Redis Produção",
        "key": "redis-producao",
        "source_type": "tag",
        "source_value": "service:redis",
    }

    with build_client() as first_client:
        first_response = first_client.post("/api/v1/services", json=payload)

    with build_client() as second_client:
        duplicate_response = second_client.post("/api/v1/services", json=payload)

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "success": False,
        "data": None,
        "message": "Serviço com esta chave já existe",
        "errors": ["key_already_exists"],
    }
