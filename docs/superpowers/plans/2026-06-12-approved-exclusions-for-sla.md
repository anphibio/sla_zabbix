# Plano de Implementação: Exclusões Aprovadas na Apuração de SLA

> **Para agentes de execução:** SUB-SKILL OBRIGATÓRIA: usar `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar este plano tarefa por tarefa. As etapas usam checklist com `- [ ]`.

**Objetivo:** Permitir registrar exclusões aprovadas com motivo, aprovador e vínculo opcional a evento do Zabbix, aplicando-as automaticamente na prévia de SLA.

**Arquitetura:** A solução adiciona uma entidade persistida de exclusão aprovada vinculada ao serviço. A prévia do SLA baseada em Zabbix passa a considerar manutenção planejada e exclusões aprovadas como intervalos removidos do período elegível e da indisponibilidade auditável.

**Stack:** FastAPI, SQLAlchemy, Pydantic, Pytest

---

## Escopo desta fatia

- Cadastro persistido de exclusão aprovada por serviço
- Campo opcional `eventid` para rastrear o evento relacionado
- Aplicação automática da exclusão no cálculo da prévia de SLA
- Transparência de minutos excluídos na resposta
