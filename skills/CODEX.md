# CODEX.md

## Comportamento esperado no Codex

Antes de iniciar qualquer tarefa, leia e respeite os arquivos de governança do projeto.

## Modo de trabalho

Para cada solicitação:

1. Entenda o objetivo funcional.
2. Verifique se a solicitação conflita com algum arquivo de governança.
3. Avalie riscos de segurança.
4. Avalie impacto técnico.
5. Avalie impacto em banco, API, UI, testes, deploy e observabilidade.
6. Consulte `SUPERPOWERS.md` quando a tarefa for complexa.
7. Consulte `IMPECCABLE_UI.md` quando houver alteração visual.
8. Proponha plano curto.
9. Implemente com qualidade.
10. Gere testes.
11. Atualize documentação, se necessário.
12. Entregue resumo técnico.

## Regras de implementação

- Gere código completo.
- Evite soluções simplificadas demais.
- Evite duplicação.
- Prefira componentes reutilizáveis.
- Prefira funções pequenas e testáveis.
- Prefira validações explícitas.
- Prefira tipagem forte.
- Prefira configuração por ambiente.
- Prefira logs estruturados.
- Prefira migrations versionadas.

## Proibido

- Implementar autenticação fictícia em produção.
- Usar banco em memória para produção.
- Ignorar validação de entrada.
- Expor stack trace para usuário final.
- Retornar informações sensíveis em APIs.
- Criar endpoints privados sem autenticação.
- Criar telas sem loading, erro e vazio.
- Criar código sem considerar Docker.
- Criar funcionalidade sem observabilidade quando aplicável.

## Saída esperada

Ao final, sempre responder com:

- Resumo do que foi feito
- Arquivos principais alterados
- Comandos para executar/testar
- Checklist de validação
- Riscos restantes
