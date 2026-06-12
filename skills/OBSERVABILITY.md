# OBSERVABILITY.md

## Objetivo

Definir padrões gerais de logs, métricas e rastreabilidade.

Para regras obrigatórias por funcionalidade, consultar:

- `OBSERVABILITY_FIRST.md`
- `MONITORING.md`

## Modelo de métricas

Neste template, a própria API publica `/metrics`.

O Zabbix consome `/metrics` como fonte principal.

Prometheus não é obrigatório.

## Logs

Padrão:

- JSON estruturado
- request_id
- user_id quando autenticado
- ip
- método HTTP
- rota
- status code
- tempo de resposta

## Métricas publicadas pela API

A API deve publicar, quando aplicável:

- Total de requisições
- Latência
- Erros por rota ou por categoria
- Status do banco
- Latência do banco
- Jobs
- Integrações
- Autenticação
- Recursos básicos

## Dashboards

Preferência:

- Zabbix como monitor principal
- Grafana opcional, preferencialmente consumindo dados do Zabbix quando fizer sentido

Dashboards recomendados:

- Saúde da API
- Erros
- Latência
- Banco de dados
- Jobs
- Autenticação
- Integrações
