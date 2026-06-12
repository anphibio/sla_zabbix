# MONITORING.md

## Objetivo

Definir padrões de monitoramento para aplicações corporativas.

## Modelo padrão deste template

A própria API deve publicar os endpoints de saúde e métricas.

O Zabbix será o consumidor principal das métricas expostas pela aplicação.

Prometheus pode ser usado futuramente como opção complementar, mas não é obrigatório para o funcionamento do monitoramento neste padrão.

## Endpoints obrigatórios

A API deve expor:

```text
/health
/ready
/metrics
```

## /health

Objetivo:

Informar se a aplicação está viva.

Deve retornar status simples e rápido.

Exemplo:

```json
{
  "status": "healthy",
  "service": "nome-do-servico",
  "version": "1.0.0"
}
```

## /ready

Objetivo:

Informar se a aplicação está pronta para receber tráfego.

Deve validar dependências críticas:

- Conexão com banco
- Cache quando aplicável
- Filas/workers quando aplicável
- Integrações obrigatórias quando aplicável

Exemplo:

```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "cache": "ok"
  }
}
```

## /metrics

Objetivo:

Publicar métricas da aplicação para consumo pelo Zabbix.

O endpoint `/metrics` deve ser exposto pela própria API.

O Zabbix deve consumir esse endpoint via:

- HTTP Agent
- Web scenario
- Item dependente
- Preprocessing JSONPath ou Prometheus pattern, conforme formato adotado

## Formato das métricas

### Opção preferencial: JSON

Mais simples para consumo via Zabbix HTTP Agent + JSONPath.

Exemplo:

```json
{
  "service": "nome-do-servico",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "requests_total": 12500,
  "request_errors_total": 12,
  "request_duration_avg_ms": 85,
  "request_duration_p95_ms": 240,
  "database_status": 1,
  "database_latency_ms": 7,
  "active_users": 14,
  "jobs_pending": 0,
  "jobs_failed_total": 1
}
```

### Opção alternativa: formato Prometheus text exposition

Pode ser usado se facilitar reaproveitamento futuro com Prometheus.

Exemplo:

```text
app_requests_total 12500
app_request_errors_total 12
app_request_duration_avg_ms 85
app_database_status 1
app_database_latency_ms 7
```

## Recomendação prática

Para ambientes baseados em Zabbix, usar `/metrics` em JSON como padrão inicial.

Isso simplifica:

- Criação de itens HTTP Agent
- Uso de JSONPath
- Criação de triggers
- Criação de dashboards
- Integração com templates Zabbix

## Métricas mínimas recomendadas

A API deve publicar, quando aplicável:

- `uptime_seconds`
- `requests_total`
- `request_errors_total`
- `request_duration_avg_ms`
- `request_duration_p95_ms`
- `database_status`
- `database_latency_ms`
- `active_users`
- `login_success_total`
- `login_failure_total`
- `jobs_pending`
- `jobs_running`
- `jobs_failed_total`
- `disk_usage_percent`
- `memory_usage_percent`
- `cpu_usage_percent`

## Padrão para status

Usar valores numéricos para facilitar triggers no Zabbix:

```text
1 = OK
0 = Falha
```

Exemplos:

- `database_status: 1`
- `ldap_status: 1`

## Zabbix

Para cada aplicação, criar ou preparar um template Zabbix contendo:

- Item HTTP Agent para `/health`
- Item HTTP Agent para `/ready`
- Item HTTP Agent principal para `/metrics`
- Itens dependentes extraídos do `/metrics`
- Triggers para indisponibilidade
- Triggers para erro elevado
- Triggers para latência elevada
- Triggers para banco indisponível
- Dashboard básico

## Triggers recomendadas

Exemplos:

- API indisponível
- `/ready` diferente de ready
- `database_status = 0`
- `request_errors_total` acima do limite esperado
- `request_duration_p95_ms` acima do limite esperado
- `disk_usage_percent > 85`
- `memory_usage_percent > 90`

## Segurança do /metrics

O endpoint `/metrics` não deve expor:

- Senhas
- Tokens
- Dados pessoais
- Headers de autorização
- Queries com dados sensíveis
- Informações internas desnecessárias

Em ambientes sensíveis, proteger `/metrics` por:

- Rede interna
- Allowlist de IP do Zabbix
- Autenticação por token técnico
- Proxy reverso com controle de acesso

## Grafana

Grafana pode ser utilizado consumindo dados do Zabbix ou de outra fonte configurada.

Neste template, Grafana é opcional e não substitui o Zabbix como consumidor principal.
