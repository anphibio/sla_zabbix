# PRODUCT.md

## Nome do projeto

Zabbix SLA

## Descrição curta

Plataforma para calcular, auditar e apresentar SLA/SLO de serviços com base em dados do Zabbix, com foco em regras mais fiéis à disponibilidade real do serviço.

## Objetivo

Construir um sistema robusto de gestão de SLA/SLO que use o Zabbix como fonte operacional de eventos e métricas, mas tenha um motor próprio de modelagem e cálculo. O objetivo é substituir relatórios pobres e pouco explicáveis por uma solução confiável, auditável e útil tanto para a equipe técnica quanto para a gestão.

O sistema deve priorizar a apuração por `tags`, pois isso permite granularidade por serviço e evita distorções causadas por alertas do host que não representam indisponibilidade real do componente monitorado. `Hostgroups` continuarão suportados como visão complementar e agregada.

## Público-alvo

- Equipe técnica de monitoramento e infraestrutura
- Equipes responsáveis por operação de serviços
- Gestores que consomem relatórios executivos
- Áreas internas que precisam de evidências de disponibilidade

## Problemas que o sistema resolve

- Relatórios atuais mostram apenas o percentual final e não explicam claramente como o SLA foi calculado
- Alertas genéricos do host podem distorcer o SLA de serviços específicos
- Falta uma camada própria para modelar serviço, regra, exceção, janela e criticidade
- A equipe técnica precisa gastar tempo consolidando e explicando dados manualmente para a gestão
- A gestão não possui visão histórica, tendência, drill-down e contexto suficiente para tomada de decisão

## Proposta de valor

O produto será uma camada de inteligência sobre o Zabbix:

- O Zabbix continua como fonte operacional principal
- O sistema define quais eventos e métricas representam indisponibilidade real de cada serviço
- O cálculo do SLA/SLO fica transparente, auditável e reproduzível
- A equipe técnica ganha controle operacional sobre as regras
- A gestão recebe relatórios executivos consistentes e confiáveis

## Modelo funcional

O sistema deve operar em duas camadas:

- Camada técnica para cadastrar serviços, associar `tags` e `hostgroups`, configurar regras, revisar violações e validar coerência do cálculo
- Camada executiva para apresentar indicadores consolidados, histórico, tendência e relatórios compartilháveis

## Principais módulos

- Autenticação e controle de acesso
- Cadastro de serviços monitorados
- Integração com Zabbix
- Motor de cálculo de SLA/SLO
- Regras por `tags`
- Regras complementares por `hostgroups`
- Regras híbridas com foco em `triggers` e suporte a métricas
- Dashboard técnico
- Dashboard executivo
- Relatórios web
- Exportação PDF e XLSX
- Agendamento e envio automático de relatórios
- Auditoria e rastreabilidade

## Regras principais de apuração

- Base principal de cálculo: `tags`
- Base complementar de cálculo: `hostgroups`
- Fonte principal de indisponibilidade: `triggers` e eventos do Zabbix
- Fonte complementar: métricas específicas quando necessário
- O sistema deve permitir separar indisponibilidade real do serviço de incidentes acessórios do host
- O sistema deve preservar evidências do que entrou e do que ficou fora do cálculo

## Integrações previstas

- Zabbix
- PostgreSQL
- LDAP/AD ou SSO futuramente
- E-mail para envio automático de relatórios
- Integrações futuras com ITSM, inventário e mensageria interna

## Requisitos não funcionais

- Rodar em Docker
- Suportar ambientes DEV, HML e PRD
- Possuir logs estruturados
- Possuir auditoria
- Possuir documentação de API
- Expor `/health`, `/ready` e `/metrics`
- Ser monitorável pelo próprio Zabbix
- Ter rastreabilidade das regras e dos cálculos
- Suportar evolução para SSO
- Permitir diagnósticos claros em produção

## Fora do escopo inicial

- Multiempresa
- Portal externo para clientes
- App mobile
- Motor avançado de predição
- Workflows complexos de aprovação
