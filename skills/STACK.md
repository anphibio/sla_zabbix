# STACK.md

## Objetivo

Definir a stack padrão do projeto em um único local.

> Altere este arquivo quando o projeto usar tecnologias diferentes.

## Backend padrão

- Python 3.13+
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- PostgreSQL 17+
- Redis opcional
- Pytest

## Frontend padrão

- React
- TypeScript
- Vite
- Shadcn/ui ou Material UI
- TanStack Query
- React Hook Form
- Zod
- Vitest
- Playwright

## Infraestrutura padrão

- Docker
- Docker Compose
- Arquivos compose independentes para `backend`, `frontend`, `worker` e `db`
- GitLab CI/CD
- Nginx ou Traefik como proxy reverso quando aplicável

## Monitoramento padrão

- A própria API publica `/health`, `/ready` e `/metrics`
- Zabbix consome `/metrics`
- Zabbix é o monitor principal
- Grafana é opcional
- Prometheus é opcional e não obrigatório

## Autenticação corporativa

Preparar para:

- LDAP/AD
- SSO
- OIDC
- SAML 2.0
- AD FS
- Keycloak
