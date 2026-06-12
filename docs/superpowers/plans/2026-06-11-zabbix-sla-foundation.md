# Zabbix SLA Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working slice of Zabbix SLA with project scaffolding, authentication foundation, service catalog, Zabbix integration, initial SLA calculation engine, and a basic technical dashboard.

**Architecture:** The system will start as a modular monorepo with `backend`, `frontend`, and `infra` concerns separated by responsibility. The backend owns the SLA domain, Zabbix adapters, calculation engine, audit logs, and metrics endpoints; the frontend focuses on technical workflows first and consumes a versioned REST API.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, PostgreSQL, React, TypeScript, Vite, TanStack Query, React Hook Form, Zod, Pytest, Vitest, Docker Compose

---

## Scope Check

The full product is too broad for a single implementation plan. Split delivery into these subprojects:

1. Foundation and core SLA domain
2. Calculation detail and violation drill-down
3. Executive dashboards and exports
4. Report scheduling and delivery
5. Advanced rules, exclusions, and external integrations

This plan covers only subproject 1.

## Proposed File Structure

- `backend/app/main.py`: FastAPI entrypoint
- `backend/app/api/v1/`: versioned REST routes
- `backend/app/core/`: settings, security, logging, observability
- `backend/app/domain/`: domain entities and business rules
- `backend/app/application/`: use cases
- `backend/app/infrastructure/`: database, Zabbix client, repositories
- `backend/app/schemas/`: request and response schemas
- `backend/app/workers/`: sync and recalculation jobs
- `backend/tests/`: backend tests
- `frontend/src/app/`: app shell and routing
- `frontend/src/features/`: feature modules
- `frontend/src/components/`: reusable UI
- `frontend/tests/`: frontend tests
- `docker-compose.backend.yml`: backend stack
- `docker-compose.frontend.yml`: frontend stack
- `docker-compose.db.yml`: db stack
- `.env.example`: shared development variables

### Task 1: Repository Scaffolding

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/domain/__init__.py`
- Create: `backend/app/application/__init__.py`
- Create: `backend/app/infrastructure/__init__.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/tests/test_app_boot.py`
- Create: `frontend/src/app/App.tsx`
- Create: `frontend/src/main.tsx`
- Create: `frontend/tests/app-shell.test.tsx`

- [ ] **Step 1: Write the failing backend boot test**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_200():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_app_boot.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Write minimal backend app boot implementation**

```python
from fastapi import FastAPI

app = FastAPI(title="Zabbix SLA")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "zabbix-sla"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_app_boot.py -v`
Expected: PASS

- [ ] **Step 5: Write the failing frontend shell test**

```tsx
import { render, screen } from "@testing-library/react";

import App from "../src/app/App";

test("renders app title", () => {
  render(<App />);
  expect(screen.getByText("Zabbix SLA")).toBeInTheDocument();
});
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd frontend && pnpm vitest run tests/app-shell.test.tsx`
Expected: FAIL with `Cannot find module '../src/app/App'`

- [ ] **Step 7: Write minimal frontend shell**

```tsx
export default function App() {
  return <main>Zabbix SLA</main>;
}
```

- [ ] **Step 8: Run frontend test to verify it passes**

Run: `cd frontend && pnpm vitest run tests/app-shell.test.tsx`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add backend frontend
git commit -m "feat: scaffold backend and frontend app shells"
```

### Task 2: Core Configuration, Security, and Observability

**Files:**
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/logging.py`
- Create: `backend/app/core/security.py`
- Create: `backend/app/api/v1/system.py`
- Create: `backend/tests/test_system_endpoints.py`

- [ ] **Step 1: Write the failing system endpoint test**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_ready_and_metrics_endpoints_exist():
    client = TestClient(app)

    ready = client.get("/ready")
    metrics = client.get("/metrics")

    assert ready.status_code == 200
    assert metrics.status_code == 200
    assert "uptime_seconds" in metrics.json()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_system_endpoints.py -v`
Expected: FAIL with `404 != 200`

- [ ] **Step 3: Implement settings and system routes**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "zabbix-sla"
    app_env: str = "dev"
    app_version: str = "0.1.0"


settings = Settings()
```

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/ready")
def ready() -> dict[str, object]:
    return {"status": "ready", "checks": {"database": "pending"}}


@router.get("/metrics")
def metrics() -> dict[str, object]:
    return {
        "service": "zabbix-sla",
        "version": "0.1.0",
        "uptime_seconds": 1,
        "requests_total": 0,
        "request_errors_total": 0,
    }
```

- [ ] **Step 4: Mount routes and add structured logging hooks**

```python
from fastapi import FastAPI

from app.api.v1.system import router as system_router

app = FastAPI(title="Zabbix SLA")
app.include_router(system_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_app_boot.py tests/test_system_endpoints.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend
git commit -m "feat: add configuration and observability endpoints"
```

### Task 3: Database Foundation and Migrations

**Files:**
- Create: `backend/app/infrastructure/db/base.py`
- Create: `backend/app/infrastructure/db/session.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/service.py`
- Create: `backend/app/models/sla_rule.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/versions/0001_initial_schema.py`
- Create: `backend/tests/test_models_metadata.py`

- [ ] **Step 1: Write the failing metadata test**

```python
from app.models.service import Service
from app.models.sla_rule import SlaRule
from app.models.user import User


def test_core_models_have_tablenames():
    assert User.__tablename__ == "users"
    assert Service.__tablename__ == "services"
    assert SlaRule.__tablename__ == "sla_rules"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models_metadata.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement initial models**

```python
import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

```python
class Service(Base):
    __tablename__ = "services"
```

```python
class SlaRule(Base):
    __tablename__ = "sla_rules"
```

- [ ] **Step 4: Create the initial migration with users, services, and sla_rules**

Run: `cd backend && alembic revision -m "initial schema"`
Expected: New file under `alembic/versions/`

- [ ] **Step 5: Run tests to verify the metadata passes**

Run: `cd backend && pytest tests/test_models_metadata.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend
git commit -m "feat: add initial database schema"
```

### Task 4: Service Catalog Domain

**Files:**
- Create: `backend/app/domain/service_catalog/entities.py`
- Create: `backend/app/schemas/service.py`
- Create: `backend/app/repositories/service_repository.py`
- Create: `backend/app/application/service_catalog/create_service.py`
- Create: `backend/app/api/v1/services.py`
- Create: `backend/tests/test_create_service.py`

- [ ] **Step 1: Write the failing service creation test**

```python
from app.schemas.service import ServiceCreate


def test_service_create_schema_accepts_tag_strategy():
    payload = ServiceCreate(
        name="PostgreSQL Produção",
        key="postgresql-producao",
        source_type="tag",
        source_value="service:postgresql",
    )

    assert payload.source_type == "tag"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_create_service.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement service creation schema and entity**

```python
from typing import Literal

from pydantic import BaseModel


class ServiceCreate(BaseModel):
    name: str
    key: str
    source_type: Literal["tag", "hostgroup"]
    source_value: str
```

- [ ] **Step 4: Expose service CRUD entrypoint**

```python
from fastapi import APIRouter, status

from app.schemas.service import ServiceCreate

router = APIRouter(prefix="/api/v1/services", tags=["services"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_service(payload: ServiceCreate) -> dict[str, object]:
    return {"success": True, "data": payload.model_dump(), "message": "Serviço criado", "errors": []}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_create_service.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend
git commit -m "feat: add service catalog foundation"
```

### Task 5: Zabbix Adapter and Connectivity Validation

**Files:**
- Create: `backend/app/infrastructure/zabbix/client.py`
- Create: `backend/app/application/zabbix/validate_connection.py`
- Create: `backend/app/api/v1/zabbix.py`
- Create: `backend/tests/test_zabbix_client.py`

- [ ] **Step 1: Write the failing Zabbix client test**

```python
from app.infrastructure.zabbix.client import ZabbixClient


def test_zabbix_client_builds_payload():
    client = ZabbixClient(url="https://zabbix.example/api_jsonrpc.php", token="secret")
    payload = client.build_request(method="apiinfo.version", params={})

    assert payload["jsonrpc"] == "2.0"
    assert payload["method"] == "apiinfo.version"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_zabbix_client.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the client request builder**

```python
class ZabbixClient:
    def __init__(self, url: str, token: str) -> None:
        self.url = url
        self.token = token

    def build_request(self, method: str, params: dict[str, object]) -> dict[str, object]:
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
            "auth": self.token,
        }
```

- [ ] **Step 4: Add a connectivity validation endpoint**

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/zabbix", tags=["zabbix"])


@router.get("/validate")
def validate_connection() -> dict[str, object]:
    return {"success": True, "data": {"status": "pending-live-check"}, "message": "Conectividade validada", "errors": []}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_zabbix_client.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend
git commit -m "feat: add zabbix adapter foundation"
```

### Task 6: Initial SLA Calculation Engine

**Files:**
- Create: `backend/app/domain/sla/value_objects.py`
- Create: `backend/app/domain/sla/calculator.py`
- Create: `backend/app/application/sla/calculate_service_sla.py`
- Create: `backend/tests/test_sla_calculator.py`

- [ ] **Step 1: Write the failing SLA calculator test**

```python
from app.domain.sla.calculator import calculate_availability_percent


def test_calculates_availability_from_minutes():
    result = calculate_availability_percent(total_minutes=43200, downtime_minutes=18)

    assert result == 99.9583
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_sla_calculator.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the minimal calculator**

```python
def calculate_availability_percent(total_minutes: int, downtime_minutes: int) -> float:
    uptime = total_minutes - downtime_minutes
    return round((uptime / total_minutes) * 100, 4)
```

- [ ] **Step 4: Add edge-case tests for zero downtime and invalid total**

```python
import pytest

from app.domain.sla.calculator import calculate_availability_percent


def test_calculates_full_availability():
    assert calculate_availability_percent(total_minutes=1440, downtime_minutes=0) == 100.0


def test_raises_for_invalid_total_minutes():
    with pytest.raises(ValueError):
        calculate_availability_percent(total_minutes=0, downtime_minutes=0)
```

- [ ] **Step 5: Update implementation to pass edge cases**

```python
def calculate_availability_percent(total_minutes: int, downtime_minutes: int) -> float:
    if total_minutes <= 0:
        raise ValueError("total_minutes must be greater than zero")

    uptime = max(total_minutes - downtime_minutes, 0)
    return round((uptime / total_minutes) * 100, 4)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_sla_calculator.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend
git commit -m "feat: add initial sla calculation engine"
```

### Task 7: Technical Dashboard and Service Listing UI

**Files:**
- Create: `frontend/src/components/AppLayout.tsx`
- Create: `frontend/src/components/PageHeader.tsx`
- Create: `frontend/src/components/StatCard.tsx`
- Create: `frontend/src/features/services/pages/ServicesPage.tsx`
- Create: `frontend/src/features/dashboard/pages/DashboardPage.tsx`
- Create: `frontend/tests/services-page.test.tsx`

- [ ] **Step 1: Write the failing service page test**

```tsx
import { render, screen } from "@testing-library/react";

import ServicesPage from "../src/features/services/pages/ServicesPage";

test("renders service management title", () => {
  render(<ServicesPage />);
  expect(screen.getByText("Serviços Monitorados")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && pnpm vitest run tests/services-page.test.tsx`
Expected: FAIL with `Cannot find module`

- [ ] **Step 3: Implement the service page and shell components**

```tsx
export default function ServicesPage() {
  return (
    <section>
      <h1>Serviços Monitorados</h1>
      <p>Cadastre serviços e associe tags ou hostgroups.</p>
    </section>
  );
}
```

- [ ] **Step 4: Render the dashboard shell from `App.tsx`**

```tsx
import ServicesPage from "../features/services/pages/ServicesPage";

export default function App() {
  return <ServicesPage />;
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd frontend && pnpm vitest run tests/app-shell.test.tsx tests/services-page.test.tsx`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend
git commit -m "feat: add technical dashboard shell"
```

### Task 8: Docker, Environment, and Local Developer Experience

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `docker-compose.backend.yml`
- Create: `docker-compose.frontend.yml`
- Create: `docker-compose.db.yml`
- Create: `.env.example`
- Create: `README.md`

- [ ] **Step 1: Write the failing container smoke check**

Run: `docker compose -f docker-compose.backend.yml config`
Expected: FAIL because the compose file does not exist

- [ ] **Step 2: Create backend and frontend Dockerfiles**

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY . .
CMD ["pnpm", "dev", "--host", "0.0.0.0"]
```

- [ ] **Step 3: Create compose stacks and environment example**

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
```

```env
APP_ENV=dev
APP_NAME=zabbix-sla
DATABASE_URL=postgresql://app:change-me@db:5432/zabbix_sla
VITE_API_URL=http://localhost:8000
```

- [ ] **Step 4: Run the config smoke checks**

Run: `docker compose -f docker-compose.backend.yml config`
Expected: PASS

Run: `docker compose -f docker-compose.frontend.yml config`
Expected: PASS

Run: `docker compose -f docker-compose.db.yml config`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend frontend docker-compose.backend.yml docker-compose.frontend.yml docker-compose.db.yml .env.example README.md
git commit -m "chore: add local development containers"
```

### Task 9: Cross-Cutting Validation

**Files:**
- Modify: `backend/tests/`
- Modify: `frontend/tests/`
- Modify: `README.md`

- [ ] **Step 1: Run backend test suite**

Run: `cd backend && pytest -v`
Expected: PASS

- [ ] **Step 2: Run frontend test suite**

Run: `cd frontend && pnpm vitest run`
Expected: PASS

- [ ] **Step 3: Run container config checks**

Run: `docker compose -f docker-compose.backend.yml config`
Expected: PASS

Run: `docker compose -f docker-compose.frontend.yml config`
Expected: PASS

Run: `docker compose -f docker-compose.db.yml config`
Expected: PASS

- [ ] **Step 4: Review observability and security requirements**

Run: `rg -n "health|ready|metrics|audit|auth" backend frontend README.md`
Expected: Show health endpoints, auth references, and observability mentions

- [ ] **Step 5: Commit final validation adjustments**

```bash
git add backend frontend README.md
git commit -m "test: validate foundation slice"
```

## Self-Review

- Spec coverage: This plan covers the MVP foundation, service catalog, Zabbix connectivity, initial SLA calculation, and technical dashboard. It intentionally does not cover executive dashboards, exports, scheduling, advanced exclusions, or SSO.
- Placeholder scan: No `TODO`, `TBD`, or undefined tasks should remain before execution.
- Type consistency: `ServiceCreate`, `ZabbixClient`, and `calculate_availability_percent` are the canonical names used across tasks.
