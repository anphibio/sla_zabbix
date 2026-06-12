# Zabbix SLA

Monorepo base de uma aplicação de SLA orientada por métricas e eventos do Zabbix. O repositório já contém:

- backend em FastAPI com rotas de saúde, catálogo de serviços, regras de SLA, preview e integrações com Zabbix
- testes de unidade e API em `backend/tests`
- estrutura inicial de frontend em React/Vite com arquivos de teste em `frontend/tests`
- arquivos Docker Compose separados para banco, backend e frontend

## Estado atual do projeto

O projeto ainda está em fase de fundação, mas já cobre o primeiro fluxo persistido de SLA de ponta a ponta.

- O backend já possui catálogo de serviços persistido, regras de SLA, janelas de manutenção, exclusões aprovadas, snapshots mensais e relatórios executivos.
- O frontend ainda está como scaffold e não possui `package.json`, lockfile nem scripts prontos para execução.
- Por isso, o backend instala dependências diretamente no `backend/Dockerfile`, enquanto o container do frontend ainda encerra com uma mensagem informando que a aplicação web não foi preparada.

## Configuração de ambiente

1. Copie `.env.example` para `.env`.
2. Ajuste os valores conforme seu ambiente.

Variáveis importantes já previstas:

- `DATABASE_URL`
- `ZABBIX_API_URL`
- `ZABBIX_API_TOKEN`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_SENDER_EMAIL`
- `SMTP_USE_TLS`

Ao usar os arquivos Compose fornecidos, o backend tende a operar com PostgreSQL porque o `.env.example` aponta `DATABASE_URL` para o serviço `db`. Se quiser manter o fallback local em SQLite, remova `DATABASE_URL` do `.env`.

## Como rodar os testes

### Backend

Hoje, os testes executáveis diretamente no repositório são os do backend.

Dentro de `backend/`:

```bash
python3 -m pytest -p no:cacheprovider tests -q
```

Isso pressupõe que o ambiente Python local já tenha as dependências necessárias.

### Cobertura atual do backend

O backend já cobre:

- criação persistida de serviços com `POST /api/v1/services`
- criação persistida de regras de SLA com `POST /api/v1/sla-rules`
- cadastro de janelas de manutenção com `POST /api/v1/maintenance-windows`
- cadastro de exclusões aprovadas com `POST /api/v1/sla-exclusions`
- geração de snapshots mensais com `POST /api/v1/sla-results`
- histórico e tendência com `GET /api/v1/sla-results/history`
- visão executiva consolidada com `GET /api/v1/sla-results/executive`
- exportação executiva em XLSX com `GET /api/v1/sla-results/executive.xlsx`
- exportação executiva em PDF com `GET /api/v1/sla-results/executive.pdf`
- criação de agendamentos com `POST /api/v1/report-schedules`
- execução de agendamentos vencidos com `POST /api/v1/report-schedules/run-due`
- preview de SLA com `POST /api/v1/sla/preview`
- preview de SLA com eventos reais do Zabbix em `POST /api/v1/sla/preview/zabbix`
- validação de conectividade com Zabbix em `GET /api/v1/zabbix/validate`

O preview baseado em Zabbix já desconsidera janelas de manutenção persistidas e exclusões aprovadas tanto do período elegível quanto do downtime contabilizado, mantendo a auditoria do cálculo com minutos excluídos e intervalos rastreados.

O repositório também já persiste resultados mensais de SLA, o que sustenta histórico, tendência e relatórios gerenciais.

A camada de agendamento já suporta:

- agendamento mensal de relatórios executivos
- geração de arquivos PDF ou XLSX em `generated_reports/`
- envio automático por e-mail do arquivo gerado
- registro do status de entrega para distinguir relatório gerado de relatório efetivamente enviado

### Frontend

Existem arquivos de teste em `frontend/tests`, mas ainda não há `package.json`, lockfile nem scripts reproduzíveis dentro do repositório. Na prática, isso significa que o frontend ainda não está pronto para execução local completa.

## Docker Compose

Os arquivos Compose estão separados por responsabilidade e podem ser combinados conforme a necessidade.

Hoje, o fluxo recomendado de desenvolvimento é `db + backend`.

- `docker-compose.db.yml` sobe o PostgreSQL com healthcheck.
- `docker-compose.backend.yml` permanece válido isoladamente e, por isso, não declara `depends_on: db`.
- Essa separação favorece validação individual dos arquivos e um fluxo local flexível.
- Como o acesso ao banco ainda é lazy no backend, essa estratégia continua aceitável neste estágio.

### Apenas banco

```bash
cp .env.example .env
docker compose -f docker-compose.db.yml up -d
```

### Backend com banco

```bash
cp .env.example .env
docker compose -f docker-compose.db.yml -f docker-compose.backend.yml up --build
```

Esse é o caminho de execução recomendado neste momento.

O backend ficará disponível em `http://localhost:8000` e o endpoint de saúde é `GET /health`.

Se no futuro o backend passar a exigir conexão obrigatória com banco já no startup, vale revisar essa estratégia de Compose.

### Scaffold do frontend

```bash
cp .env.example .env
docker compose -f docker-compose.frontend.yml up --build
```

No estado atual, o container do frontend deve encerrar logo no início avisando que `frontend/package.json` ainda não existe. Esse comportamento é intencional.

### Montagem opcional do scaffold completo

```bash
cp .env.example .env
docker compose \
  -f docker-compose.db.yml \
  -f docker-compose.backend.yml \
  -f docker-compose.frontend.yml \
  up --build
```

Esse comando ainda não representa uma stack completa de produção. Use apenas se quiser observar o backend junto do scaffold atual do frontend.

## Validação dos arquivos Compose

Você pode validar os arquivos sem subir containers:

```bash
docker compose -f docker-compose.db.yml config
docker compose -f docker-compose.backend.yml config
docker compose -f docker-compose.frontend.yml config
docker compose -f docker-compose.db.yml -f docker-compose.backend.yml config
docker compose -f docker-compose.db.yml -f docker-compose.backend.yml -f docker-compose.frontend.yml config
```
