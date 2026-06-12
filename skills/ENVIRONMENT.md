# ENVIRONMENT.md

## Ambientes

- DEV
- HML
- PRD

## Configuração

Toda configuração deve vir de variável de ambiente.

## Arquivos

- `.env.example` deve existir.
- `.env` real não deve ser versionado.
- Em DEV, preferir um único `.env`, organizado por blocos de `backend`, `frontend`, `worker` e `db`.
- Em HML/PRD com stacks separadas, cada servidor pode ter seu próprio `.env` contendo apenas as variáveis da stack implantada.

## Variáveis comuns

```text
# Backend
APP_ENV=dev
APP_NAME=nome-do-projeto
DATABASE_URL=postgresql://user:pass@db:5432/app
JWT_SECRET=change-me
JWT_EXPIRE_MINUTES=30
LOG_LEVEL=INFO

# Frontend
CORS_ORIGINS=http://localhost:3000
VITE_API_URL=http://localhost:8000

# Worker
WORKER_CONCURRENCY=2

# Database
POSTGRES_DB=app
POSTGRES_USER=app
POSTGRES_PASSWORD=change-me
```
