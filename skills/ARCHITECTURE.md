# ARCHITECTURE.md

## Visão geral

Arquitetura recomendada:

Frontend Web
↓
API REST
↓
Camada de Aplicação
↓
Camada de Domínio
↓
Infraestrutura
↓
PostgreSQL / Redis / Integrações

Em ambientes containerizados, `backend`, `frontend`, `worker` e `db` devem ser organizados em stacks independentes de Docker Compose para melhorar isolamento operacional, reuso entre projetos, escalabilidade e CI/CD.

## Stack

A stack oficial deve ser consultada em `STACK.md`.

## Estrutura backend recomendada

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── workers/
│   └── main.py
├── alembic/
└── tests/
```

## Estrutura frontend recomendada

```text
frontend/
├── src/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── layouts/
│   ├── pages/
│   ├── services/
│   ├── stores/
│   ├── types/
│   └── utils/
└── tests/
```

## Estrutura de containers recomendada

```text
docker-compose.backend.yml
docker-compose.frontend.yml
docker-compose.worker.yml
docker-compose.db.yml
```

## Princípios

- Clean Architecture
- SOLID
- Separação de responsabilidades
- Baixo acoplamento
- Alta coesão
- Repository Pattern
- Service Layer
- DTOs/Schemas para entrada e saída

## Regras

- API não deve acessar banco diretamente fora dos repositories.
- Frontend não deve espalhar chamadas HTTP em componentes.
- Regras de negócio não devem ficar em controllers.
- Migrations devem ser versionadas.
- Serviços externos devem ficar isolados em adapters.
- Superpowers deve ser usado preferencialmente em refatorações arquiteturais.
