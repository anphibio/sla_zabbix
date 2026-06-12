# DEVOPS.md

## Deploy padrão

Todo projeto deve rodar com Docker Compose.

Para facilitar CI/CD em produção, a aplicação deve separar `backend`, `frontend`, `worker` e `db` em arquivos de compose independentes, sem dependência obrigatória entre eles.

## Arquivos esperados

- Dockerfile backend
- Dockerfile frontend
- Dockerfile worker ou estratégia documentada de reaproveitamento da imagem do backend
- docker-compose.backend.yml
- docker-compose.frontend.yml
- docker-compose.worker.yml
- docker-compose.db.yml quando o banco fizer parte do projeto
- Makefile apenas para rotinas de desenvolvimento local
- .env.example

## Estratégia de `.env`

Em DEV, preferir um único arquivo `.env`, separado por blocos para `backend`, `frontend`, `worker` e `db`.

Em HML e PRD, quando as stacks estiverem em servidores diferentes, cada stack deve receber apenas o seu próprio conjunto de variáveis de ambiente.

## Containers

- Não rodar como root.
- Usar multi-stage build.
- Definir healthcheck.
- Definir restart policy.
- Separar volumes persistentes.
- Não embutir secrets na imagem.
- Configurar logs em todos os containers para facilitar troubleshooting e debug.

## Stacks esperadas no Compose

- `backend`
- `frontend`
- `worker`
- `db` quando o banco for hospedado pelo próprio projeto

Cada stack deve poder ser implantada isoladamente, inclusive em servidores diferentes.

O `worker` deve ser executado como stack separada, sem exposição de porta pública, permitindo deploy, escala e reinício independentes.

## Ambientes

- DEV
- HML
- PRD

## CI/CD

Pipeline mínimo:

1. Lint
2. Test
3. Build backend
4. Build frontend
5. Build worker
6. Security scan
7. Docker build por stack
8. Publicação de imagens por stack
9. Deploy HML
10. Deploy PRD manual

## Monitoramento

Seguir `MONITORING.md` e `OBSERVABILITY_FIRST.md`.

A aplicação deve expor:

- `/health`
- `/ready`
- `/metrics`

O Zabbix deve consumir estes endpoints, principalmente `/metrics`.

Prometheus não é obrigatório neste padrão.
