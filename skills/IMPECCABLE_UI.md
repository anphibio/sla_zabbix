# IMPECCABLE_UI.md

## Fonte única de UX/UI

Toda interface do projeto deve seguir os princípios da metodologia Impeccable.

## Regra principal

Nenhuma tela nova ou alterada deve ser considerada concluída sem revisão Impeccable.

## Princípios

- Clareza acima de criatividade visual desnecessária
- Hierarquia visual forte
- Espaçamento consistente
- Tipografia bem definida
- Baixo ruído visual
- Feedback claro para o usuário
- Estados bem tratados
- Responsividade real
- Consistência entre telas
- Acessibilidade básica obrigatória

## Hierarquia visual

Toda tela deve responder:

- O usuário sabe onde olhar primeiro?
- Existe uma ação principal clara?
- Os elementos secundários estão visualmente subordinados?
- O layout guia o usuário naturalmente?

## Espaçamento

- Usar escala baseada em múltiplos de 4.
- Evitar elementos colados.
- Evitar telas excessivamente densas.
- Priorizar espaço em branco.
- Agrupar informações relacionadas.

## Tipografia

Escala recomendada:

- 12
- 14
- 16
- 20
- 24
- 32
- 40

Evitar tamanhos aleatórios.

## Estados obrigatórios

Toda tela relevante deve possuir:

- Loading
- Erro
- Vazio
- Sucesso/feedback
- Confirmação para ação destrutiva

## Dashboard

Todo dashboard deve priorizar:

- KPI principal
- KPIs secundários
- Tendências
- Alertas
- Ações rápidas
- Filtros por período quando aplicável

## Tabelas

Tabelas devem possuir, quando aplicável:

- Busca
- Paginação
- Ordenação
- Filtros
- Ações por linha
- Exportação

## Formulários

Formulários devem possuir:

- Labels visíveis
- Validação clara
- Mensagens de erro próximas ao campo
- Botão principal evidente
- Loading no submit
- Proteção contra duplo envio

## Revisão obrigatória

Ao finalizar UI, executar:

```text
prompts/IMPECCABLE_REVIEW.md
```
