# SUPERPOWERS.md

## Objetivo

Definir quando e como usar Superpowers como preferência operacional no Codex.

## Regra principal

Quando o Superpowers estiver instalado e disponível no ambiente Codex, utilize-o preferencialmente em tarefas complexas, com risco de regressão ou com impacto em arquitetura, segurança, UI, testes, banco ou deploy.

## Quando usar

Use Superpowers para:

- Planejamento estruturado
- Análise de código existente
- Investigação de bugs
- Correção de bugs
- Refatoração segura
- Revisão de arquitetura
- Revisão de segurança
- Revisão de UI/UX
- Criação de testes
- Revisão de pull requests
- Preparação de releases

## Critério de decisão

Antes de iniciar uma tarefa, avalie:

- A tarefa altera múltiplos arquivos?
- Pode quebrar funcionalidade existente?
- Envolve autenticação, autorização, banco, deploy ou segurança?
- Envolve UI importante?
- Envolve refatoração ampla?
- Envolve bug difícil de reproduzir?
- Envolve testes ou release?

Se sim, prefira Superpowers.

## Limites

Superpowers não substitui nem pode contrariar:

- `SECURITY.md`
- `ARCHITECTURE.md`
- `DATABASE.md`
- `DEVOPS.md`
- `ENTERPRISE_RULES.md`
- `IMPECCABLE_UI.md`
- `OBSERVABILITY_FIRST.md`

Em caso de conflito, os arquivos de governança prevalecem.

## Checklist

Antes de concluir tarefa complexa:

- [ ] Avaliei se Superpowers era aplicável
- [ ] Usei Superpowers quando aplicável
- [ ] Mantive compatibilidade com a arquitetura
- [ ] Revisei segurança
- [ ] Revisei testes
- [ ] Revisei impacto em UI, API, banco e deploy
