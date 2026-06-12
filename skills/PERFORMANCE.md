# PERFORMANCE.md

## Backend

- Usar paginação em listas.
- Evitar N+1 queries.
- Usar índices no banco.
- Usar cache quando fizer sentido.
- Definir timeout para integrações externas.
- Usar jobs assíncronos para tarefas demoradas.

## Frontend

- Evitar renderizações desnecessárias.
- Usar lazy loading.
- Usar cache de requisições.
- Paginar tabelas grandes.

## Banco

- Monitorar queries lentas.
- Criar índices para filtros frequentes.
- Evitar consultas sem limite.
- Usar EXPLAIN em consultas críticas.
