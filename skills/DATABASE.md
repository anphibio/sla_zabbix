# DATABASE.md

## Banco padrão

PostgreSQL 17+

## Regras gerais

- Todas as tabelas devem possuir chave primária.
- Preferir UUID para entidades expostas em API.
- Usar timestamps.
- Usar constraints.
- Usar foreign keys.
- Usar índices para consultas frequentes.
- Usar migrations versionadas.
- Evitar lógica crítica apenas no frontend.

## Campos padrão

Quando fizer sentido:

- id
- created_at
- updated_at
- deleted_at
- created_by
- updated_by
- is_active

## Soft delete

Para dados administrativos importantes, preferir soft delete.

## Performance

- Criar índices em FKs.
- Criar índices em campos usados em filtros.
- Evitar N+1 queries.
- Usar paginação.
- Monitorar queries lentas.
