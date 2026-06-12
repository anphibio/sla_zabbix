# API_STANDARDS.md

## Padrão

API REST versionada.

Base:

```text
/api/v1
```

## Resposta padrão

```json
{
  "success": true,
  "data": {},
  "message": "Operação realizada com sucesso",
  "errors": []
}
```

## Erro padrão

```json
{
  "success": false,
  "data": null,
  "message": "Erro ao processar solicitação",
  "errors": []
}
```

## Obrigatório

- Paginação
- Filtros
- Ordenação
- OpenAPI
- Swagger
- Autenticação em endpoints privados
- Autorização em endpoints administrativos
- Logs e métricas em rotas críticas
