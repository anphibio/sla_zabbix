import importlib
import os


def test_repository_persists_and_reads_service_by_key(monkeypatch, tmp_path) -> None:
    database_path = tmp_path / "service-repository.db"
    database_url = f"sqlite+pysqlite:///{database_path}"
    original_database_url = os.environ.get("DATABASE_URL")

    from app.infrastructure.db import session as session_module
    from app.repositories import service_repository as repository_module

    monkeypatch.setenv("DATABASE_URL", database_url)

    try:
        importlib.reload(session_module)
        importlib.reload(repository_module)

        first_repository = repository_module.SqlAlchemyServiceRepository()
        first_repository.create_service(
            name="PostgreSQL Produção",
            key="postgresql-producao",
            source_type="tag",
            source_value="service:postgresql",
        )

        second_repository = repository_module.SqlAlchemyServiceRepository()
        loaded = second_repository.get_by_key("postgresql-producao")

        assert loaded is not None
        assert loaded.key == "postgresql-producao"
        assert loaded.name == "PostgreSQL Produção"
    finally:
        if original_database_url is None:
            monkeypatch.delenv("DATABASE_URL", raising=False)
        else:
            monkeypatch.setenv("DATABASE_URL", original_database_url)

        importlib.reload(session_module)
        importlib.reload(repository_module)
