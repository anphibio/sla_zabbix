# ENTERPRISE_RULES.md

## Regra principal

Todo sistema deve nascer preparado para ambiente corporativo.

## Obrigatório em todos os projetos

- Docker
- Docker Compose
- Healthcheck
- Logs estruturados
- Auditoria
- API documentada
- Banco com migrations
- Configuração por `.env`
- `.env.example`
- README
- Testes mínimos
- Tratamento de erro
- Interface responsiva
- Controle de acesso quando aplicável
- Observabilidade mínima

## Fontes específicas

- Superpowers: `SUPERPOWERS.md`
- Impeccable UI: `IMPECCABLE_UI.md`
- Stack: `STACK.md`
- Componentes UI: `UI_COMPONENTS.md`
- Monitoramento: `MONITORING.md`
- Observabilidade por funcionalidade: `OBSERVABILITY_FIRST.md`

## Não aceitar como solução final

- Mock permanente
- Dados fixos no código
- Senhas hardcoded
- Banco SQLite para produção
- Endpoint administrativo sem autenticação
- Tela sem estado de erro
- Código sem tratamento de exceção
- Deploy manual sem documentação
- Funcionalidade crítica sem logs ou auditoria
