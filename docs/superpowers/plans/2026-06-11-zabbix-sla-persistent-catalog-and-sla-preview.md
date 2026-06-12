# Plano de Implementação: Catálogo Persistente e Prévia de SLA

> **Para agentes de execução:** SUB-SKILL OBRIGATÓRIA: usar `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar este plano tarefa por tarefa. As etapas usam checklist com `- [ ]`.

**Objetivo:** Substituir o catálogo de serviços em memória por persistência em banco e adicionar o primeiro fluxo de prévia de SLA ligado a serviços e regras armazenados.

**Arquitetura:** Esta fatia transforma o catálogo atual, que hoje vive no processo, em um repositório baseado em SQLAlchemy. Em seguida, adiciona um caso de uso mínimo de prévia de SLA que lê um serviço e uma regra persistidos e aplica o cálculo puro de SLA que já existe no domínio. A camada HTTP continua fina: as rotas traduzem payloads em inputs da aplicação, os repositórios encapsulam persistência e a matemática de SLA continua no domínio.

**Stack:** FastAPI, SQLAlchemy, Alembic, PostgreSQL/SQLite fallback, Pydantic, Pytest

---

## Checagem de escopo

O próximo gargalo funcional é persistência. O catálogo de serviços atual existe só em memória, o que bloqueia qualquer visão mensal confiável, histórico de apuração ou fluxo entre múltiplas requisições. Por isso, este plano cobre:

1. Catálogo de serviços persistido
2. Criação persistida mínima de regras de SLA
3. Primeiro endpoint de prévia de SLA usando entidades armazenadas

Este plano ainda não cobre drill-down completo de violações, ingestão real de eventos do Zabbix, histórico mensal consolidado, exportações ou relatórios executivos.

## Estrutura de arquivos proposta

- `backend/app/infrastructure/db/session.py`: reaproveitar engine e sessão para a camada de persistência
- `backend/app/models/service.py`: modelo persistido de serviço
- `backend/app/models/sla_rule.py`: modelo persistido de regra/meta de SLA
- `backend/app/repositories/service_repository.py`: sair de memória e ir para SQLAlchemy com create/get/list
- `backend/app/repositories/sla_rule_repository.py`: repositório persistido de regras
- `backend/app/application/service_catalog/`: casos de uso do catálogo de serviços
- `backend/app/application/sla/`: casos de uso da prévia persistida de SLA
- `backend/app/schemas/service.py`: schemas de request/response do catálogo persistido
- `backend/app/schemas/sla_rule.py`: schemas de request/response das regras
- `backend/app/schemas/sla_preview.py`: schemas do fluxo de prévia
- `backend/app/api/v1/services.py`: rotas do catálogo persistido
- `backend/app/api/v1/sla_rules.py`: rotas de criação de regras
- `backend/app/api/v1/sla_preview.py`: rotas da prévia de SLA
- `backend/app/main.py`: registrar repositórios e rotas
- `backend/tests/`: cobertura de regressão para os fluxos persistidos

### Tarefa 1: Ajuste da sessão de banco e contrato do repositório

**Arquivos:**
- Modificar: `backend/app/infrastructure/db/session.py`
- Modificar: `backend/app/repositories/service_repository.py`
- Criar: `backend/tests/test_service_repository.py`

- [ ] **Passo 1: Escrever o teste falhando de persistência do repositório**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.db.base import Base
from app.repositories.service_repository import SqlAlchemyServiceRepository


def test_repository_persists_and_reads_service_by_key():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    repository = SqlAlchemyServiceRepository(session)

    created = repository.create_service(
        name="PostgreSQL Produção",
        key="postgresql-producao",
        source_type="tag",
        source_value="service:postgresql",
    )

    loaded = repository.get_by_key("postgresql-producao")

    assert created.key == "postgresql-producao"
    assert loaded is not None
    assert loaded.key == "postgresql-producao"
```

- [ ] **Passo 2: Rodar o teste para confirmar a falha**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests/test_service_repository.py -q`
Esperado: FAIL por ausência de `SqlAlchemyServiceRepository` ou dos métodos de persistência

- [ ] **Passo 3: Refatorar o repositório para implementação baseada em SQLAlchemy**

```python
class SqlAlchemyServiceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session
```

- [ ] **Passo 4: Adicionar os métodos mínimos `create_service` e `get_by_key`**

```python
def get_by_key(self, key: str) -> Service | None:
    return self._session.execute(
        select(Service).where(Service.key == key)
    ).scalar_one_or_none()
```

- [ ] **Passo 5: Rodar o teste e verificar que passa**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests/test_service_repository.py -q`
Esperado: PASS

- [ ] **Passo 6: Commit**

```bash
git add backend/app/infrastructure/db/session.py backend/app/repositories/service_repository.py backend/tests/test_service_repository.py
git commit -m "feat: adiciona repositório persistente de serviços"
```

### Tarefa 2: Persistência real do catálogo de serviços

**Arquivos:**
- Modificar: `backend/app/schemas/service.py`
- Modificar: `backend/app/application/service_catalog/create_service.py`
- Modificar: `backend/app/api/v1/services.py`
- Modificar: `backend/app/main.py`
- Modificar: `backend/tests/test_create_service.py`

- [ ] **Passo 1: Escrever o teste falhando de duplicidade persistida**

```python
def test_create_service_endpoint_rejects_duplicate_key_from_database():
    payload = {
        "name": "Redis Produção",
        "key": "redis-producao",
        "source_type": "tag",
        "source_value": "service:redis",
    }

    first_response = client.post("/api/v1/services", json=payload)
    second_response = client.post("/api/v1/services", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
```

- [ ] **Passo 2: Rodar o teste para confirmar a falha no wiring atual**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests/test_create_service.py -q`
Esperado: FAIL porque a aplicação ainda estará usando o caminho antigo em memória

- [ ] **Passo 3: Ligar a criação de serviços a uma sessão de banco por requisição**

```python
def get_service_repository(
    session: Session = Depends(get_db_session),
) -> SqlAlchemyServiceRepository:
    return SqlAlchemyServiceRepository(session)
```

- [ ] **Passo 4: Manter o contrato da rota estável enquanto muda a persistência**

```python
return {
    "success": True,
    "data": response.model_dump(),
    "message": "Serviço criado",
    "errors": [],
}
```

- [ ] **Passo 5: Rodar os testes da rota de serviços**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests/test_create_service.py tests/test_service_repository.py -q`
Esperado: PASS

- [ ] **Passo 6: Commit**

```bash
git add backend/app/schemas/service.py backend/app/application/service_catalog/create_service.py backend/app/api/v1/services.py backend/app/main.py backend/tests/test_create_service.py
git commit -m "feat: persiste catálogo de serviços no banco"
```

### Tarefa 3: Criação persistida de regra de SLA

**Arquivos:**
- Criar: `backend/app/repositories/sla_rule_repository.py`
- Criar: `backend/app/schemas/sla_rule.py`
- Criar: `backend/app/application/sla/create_sla_rule.py`
- Criar: `backend/app/api/v1/sla_rules.py`
- Criar: `backend/tests/test_create_sla_rule.py`

- [ ] **Passo 1: Escrever o teste falhando de criação de regra**

```python
def test_create_sla_rule_for_existing_service():
    response = client.post(
        "/api/v1/sla-rules",
        json={
            "service_key": "postgresql-producao",
            "name": "Produção mensal",
            "target_percentage": "99.90",
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["target_percentage"] == "99.90"
```

- [ ] **Passo 2: Rodar o teste para confirmar a falha**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests/test_create_sla_rule.py -q`
Esperado: FAIL por ausência de rota ou schema

- [ ] **Passo 3: Criar schema mínimo e repositório da regra**

```python
class SlaRuleCreate(BaseModel):
    service_key: str
    name: str
    target_percentage: Decimal
```

- [ ] **Passo 4: Implementar caso de uso que resolve o serviço e persiste a regra**

```python
class CreateSlaRuleUseCase:
    def execute(self, payload: CreateSlaRuleInput) -> SlaRule:
        service = self._service_repository.get_by_key(payload.service_key)
        if service is None:
            raise ServiceNotFoundError(payload.service_key)
        return self._sla_rule_repository.create_rule(...)
```

- [ ] **Passo 5: Expor `POST /api/v1/sla-rules`**

```python
router = APIRouter(prefix="/api/v1/sla-rules", tags=["sla-rules"])
```

- [ ] **Passo 6: Rodar os testes**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests/test_create_sla_rule.py tests/test_create_service.py -q`
Esperado: PASS

- [ ] **Passo 7: Commit**

```bash
git add backend/app/repositories/sla_rule_repository.py backend/app/schemas/sla_rule.py backend/app/application/sla/create_sla_rule.py backend/app/api/v1/sla_rules.py backend/tests/test_create_sla_rule.py
git commit -m "feat: adiciona criação persistida de regra de sla"
```

### Tarefa 4: Prévia de SLA a partir de dados armazenados

**Arquivos:**
- Criar: `backend/app/schemas/sla_preview.py`
- Modificar: `backend/app/application/sla/calculate_service_sla.py`
- Criar: `backend/app/api/v1/sla_preview.py`
- Criar: `backend/tests/test_sla_preview.py`

- [ ] **Passo 1: Escrever o teste falhando da prévia de SLA**

```python
def test_preview_returns_service_rule_and_availability():
    response = client.post(
        "/api/v1/sla/preview",
        json={
            "service_key": "postgresql-producao",
            "total_minutes": 43200,
            "downtime_minutes": 18,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["availability_percent"] == 99.9583
    assert response.json()["data"]["target_percentage"] == "99.90"
```

- [ ] **Passo 2: Rodar o teste para confirmar a falha**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests/test_sla_preview.py -q`
Esperado: FAIL por ausência de rota ou schema de prévia

- [ ] **Passo 3: Adicionar schemas de request e response da prévia**

```python
class SlaPreviewRequest(BaseModel):
    service_key: str
    total_minutes: int
    downtime_minutes: int
```

- [ ] **Passo 4: Estender o caso de uso existente para devolver contexto persistido**

```python
class CalculateStoredServiceSlaUseCase:
    def execute(self, payload: SlaPreviewInput) -> SlaPreviewResult:
        ...
```

- [ ] **Passo 5: Expor `POST /api/v1/sla/preview`**

```python
router = APIRouter(prefix="/api/v1/sla", tags=["sla"])
```

- [ ] **Passo 6: Rodar os testes da prévia**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests/test_sla_preview.py tests/test_sla_calculator.py -q`
Esperado: PASS

- [ ] **Passo 7: Commit**

```bash
git add backend/app/schemas/sla_preview.py backend/app/application/sla/calculate_service_sla.py backend/app/api/v1/sla_preview.py backend/tests/test_sla_preview.py
git commit -m "feat: adiciona endpoint persistido de prévia de sla"
```

### Tarefa 5: Registro de rotas e regressão final

**Arquivos:**
- Modificar: `backend/app/main.py`
- Modificar: `backend/tests/test_app_boot.py`
- Modificar: `backend/tests/test_system_endpoints.py`
- Modificar: `README.md`

- [ ] **Passo 1: Registrar as novas rotas**

```python
app.include_router(services_router)
app.include_router(sla_rules_router)
app.include_router(sla_preview_router)
```

- [ ] **Passo 2: Rodar a suíte completa de regressão do backend**

Rodar: `cd backend && python3 -m pytest -p no:cacheprovider tests -q`
Esperado: PASS

- [ ] **Passo 3: Atualizar o README com as novas fatias persistidas**

```markdown
- catálogo de serviços persistido com SQLAlchemy
- endpoint de criação de regras de SLA
- endpoint de prévia de SLA para teste de apuração mensal
```

- [ ] **Passo 4: Rodar as validações de compose após os ajustes**

Rodar: `docker compose -f docker-compose.db.yml config`
Esperado: PASS

Rodar: `docker compose -f docker-compose.backend.yml config`
Esperado: PASS

- [ ] **Passo 5: Commit**

```bash
git add backend/app/main.py backend/tests README.md
git commit -m "test: valida catálogo persistido e prévia de sla"
```

## Auto-revisão

- Cobertura do spec: este plano cobre o pré-requisito de persistência que hoje bloqueia relatórios de SLA confiáveis e acrescenta a primeira prévia de SLA baseada em dados armazenados. Ainda não cobre ingestão real de eventos do Zabbix, histórico mensal consolidado, linha do tempo de violações, exportações ou dashboards executivos.
- Varredura de placeholders: não há `TODO`, `TBD` ou passos vagos pendentes.
- Consistência de tipos: `ServiceSourceType`, `CreateServiceInput`, `SlaRuleCreate` e os DTOs da prévia devem permanecer alinhados entre domínio, aplicação e API durante a execução.
