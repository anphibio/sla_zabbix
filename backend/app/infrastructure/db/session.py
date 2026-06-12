import os
import sys
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.db.base import Base


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SQLITE_PATH = PROJECT_ROOT / "zabbix_sla.db"
PYTEST_SQLITE_PATH = PROJECT_ROOT / ".pytest_cache" / f"zabbix_sla_{os.getpid()}.db"


def build_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return database_url

    if "pytest" in sys.modules:
        PYTEST_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+pysqlite:///{PYTEST_SQLITE_PATH.as_posix()}"

    return f"sqlite+pysqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"


DATABASE_URL = build_database_url()

engine = create_engine(
    DATABASE_URL,
    future=True,
    connect_args={"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def load_db_models() -> None:
    import app.models.maintenance_window  # noqa: F401
    import app.models.report_schedule  # noqa: F401
    import app.models.report_schedule_run  # noqa: F401
    import app.models.service  # noqa: F401
    import app.models.sla_exclusion  # noqa: F401
    import app.models.sla_result  # noqa: F401
    import app.models.sla_rule  # noqa: F401
    import app.models.user  # noqa: F401


def initialize_database() -> None:
    load_db_models()
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
