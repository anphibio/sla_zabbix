# OBSERVABILITY_FIRST.md

## Regra principal

Toda funcionalidade relevante deve nascer observável.

## Modelo padrão

A própria API deve publicar métricas em `/metrics`.

O Zabbix deve consumir `/health`, `/ready` e `/metrics`.

Prometheus não é obrigatório neste template.

## Obrigatório por funcionalidade

Ao criar ou alterar funcionalidade, avaliar:

- Logs estruturados
- Auditoria
- Métricas publicadas pela API em `/metrics`
- Healthcheck
- Readiness check
- Item ou template Zabbix
- Triggers Zabbix
- Dashboard Zabbix ou Grafana via Zabbix
- Rastreamento de erro

## Logs

Registrar eventos importantes com:

- timestamp
- nível
- request_id
- user_id quando autenticado
- ação
- recurso afetado
- resultado
- duração quando aplicável

## Auditoria

Registrar ações críticas:

- Login
- Logout
- Falha de login
- Criação
- Alteração
- Exclusão
- Exportação
- Importação
- Mudança de permissão
- Alteração de configuração
- Ações administrativas

## Métricas mínimas para APIs

Publicar em `/metrics`, quando aplicável:

- requests_total
- request_errors_total
- request_duration_avg_ms
- request_duration_p95_ms
- active_users
- login_success_total
- login_failure_total

## Métricas mínimas para banco

Publicar em `/metrics`, quando aplicável:

- database_status
- database_latency_ms
- database_connections_active
- database_connections_idle

## Métricas mínimas para jobs

Publicar em `/metrics`, quando aplicável:

- jobs_pending
- jobs_running
- jobs_failed_total
- job_duration_avg_ms
- last_job_status

## Métricas mínimas para integrações

Publicar em `/metrics`, quando aplicável:

- integration_status
- integration_errors_total
- integration_latency_ms
- last_successful_sync_timestamp

## Critério de aceite

Uma funcionalidade crítica só é considerada concluída se:

- [ ] Possui logs adequados
- [ ] Possui auditoria quando necessário
- [ ] Publica métrica em `/metrics` ou possui justificativa para não publicar
- [ ] Pode ser monitorada pelo Zabbix
- [ ] Não expõe dados sensíveis
- [ ] Pode ser diagnosticada em produção
