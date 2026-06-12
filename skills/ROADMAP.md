# ROADMAP.md

## MVP

- [ ] Autenticação e perfis básicos
- [ ] Cadastro de serviços monitorados
- [ ] Integração inicial com Zabbix
- [ ] Associação por `tags` como regra principal
- [ ] Associação opcional por `hostgroups`
- [ ] Motor inicial de cálculo de SLA por período
- [ ] Regra híbrida com foco em `triggers`
- [ ] Suporte complementar a métricas específicas
- [ ] Regras básicas de exceção e coerência
- [ ] Dashboard técnico inicial
- [ ] Relatório web básico por serviço
- [ ] Histórico mensal
- [ ] Auditoria e logs estruturados
- [ ] Docker Compose funcional
- [ ] Documentação inicial
- [ ] Endpoints `/health`, `/ready` e `/metrics`

## Versão 1.0

- [ ] Drill-down completo de violações
- [ ] Detalhamento dos eventos considerados no cálculo
- [ ] Tendência e comparação entre períodos
- [ ] Filtros por ambiente, criticidade, unidade e tecnologia
- [ ] Dashboard executivo consolidado
- [ ] Exportação XLSX
- [ ] Exportação PDF
- [ ] Agendamento de relatórios
- [ ] Envio automático por e-mail ou canal interno
- [ ] Configuração de metas por serviço
- [ ] Monitoramento do próprio sistema via Zabbix
- [ ] Template Zabbix para a aplicação

## Versão 2.0

- [ ] Regras avançadas por tipo de serviço
- [ ] Pesos e composições de SLA/SLO
- [ ] Tratamento de manutenção planejada
- [ ] Exclusões aprovadas com rastreabilidade
- [ ] Múltiplas visões de apuração por serviço, time e tecnologia
- [ ] Benchmark entre áreas e grupos de serviço
- [ ] API pública para consumo externo
- [ ] Integrações com ITSM e inventário
- [ ] SSO
- [ ] LDAP/AD avançado

## Backlog futuro

- [ ] Multiempresa
- [ ] Portal para clientes internos
- [ ] Workflows de aprovação
- [ ] Assinatura eletrônica de relatórios
- [ ] Recomendação automática para ajuste de modelagem
- [ ] Previsão de risco de violação de SLA
