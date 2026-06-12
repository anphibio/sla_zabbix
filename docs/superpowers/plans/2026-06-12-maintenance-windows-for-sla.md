# Plano de Implementação: Janelas de Manutenção na Apuração de SLA

> **Para agentes de execução:** SUB-SKILL OBRIGATÓRIA: usar `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar este plano tarefa por tarefa. As etapas usam checklist com `- [ ]`.

**Objetivo:** Permitir cadastrar janelas de manutenção planejada por serviço e excluí-las automaticamente da apuração de SLA.

**Arquitetura:** A solução adiciona uma entidade persistida de janela de manutenção vinculada ao serviço. A prévia de SLA baseada em Zabbix passa a consultar janelas ativas no período, remover esses intervalos do tempo elegível e também da indisponibilidade computada, preservando rastreabilidade na resposta.

**Stack:** FastAPI, SQLAlchemy, Pydantic, Pytest

---

## Estrutura de arquivos proposta

- `backend/app/models/maintenance_window.py`
- `backend/app/repositories/maintenance_window_repository.py`
- `backend/app/application/sla/create_maintenance_window.py`
- `backend/app/schemas/maintenance_window.py`
- `backend/app/api/v1/maintenance_windows.py`
- `backend/app/application/sla/preview_zabbix_service_sla.py`
- `backend/app/schemas/zabbix_sla_preview.py`
- `backend/tests/test_create_maintenance_window.py`
- `backend/tests/test_zabbix_sla_preview.py`

## Escopo desta fatia

- Cadastro persistido de manutenção planejada
- Busca de janelas ativas por período
- Exclusão da manutenção no cálculo da prévia de SLA do Zabbix
- Transparência de minutos excluídos e janelas aplicadas na resposta

## Fora desta fatia

- Fluxo de aprovação
- Tipos avançados de exceção
- Integração automática com manutenção do Zabbix
- Histórico consolidado mensal salvo em tabela de resultados
