# Design: Entrega de Relatorios por E-mail com Lista de Destinatarios e Templates

## Objetivo

Evoluir a entrega automatica dos relatorios executivos de SLA para que cada agendamento suporte:

- lista estruturada de destinatarios
- assunto customizavel com placeholders
- corpo do e-mail customizavel com placeholders

O foco desta etapa e aumentar o valor operacional da entrega para a equipe tecnica e para a gestao sem introduzir uma engine de templates complexa nem acoplamento excessivo com a camada de relatorios.

## Escopo

Esta etapa inclui:

- substituir o campo unico `recipient_email` por `recipient_emails`
- adicionar `body_template` ao agendamento
- manter `subject_template` como opcional
- permitir envio de um unico e-mail com varios destinatarios
- suportar placeholders basicos resolvidos no momento do envio
- manter fallback para assunto e corpo padrao quando templates nao forem informados
- cobrir validacao, testes automatizados e documentacao

Esta etapa nao inclui:

- copia oculta, copia separada por destinatario ou grupos de distribuicao
- anexos adicionais
- historico detalhado por destinatario
- retries, fila de entrega ou webhooks
- placeholders derivados de metricas consolidadas como media de SLA ou quantidade de servicos abaixo da meta
- engine de templates generica com condicionais, loops ou expressoes

## Motivacao

O envio atual ja permite gerar o arquivo e tentar a entrega, mas ainda e limitado para uso real. Em operacao, e comum um mesmo relatorio ser enviado para mais de uma pessoa, e a mensagem precisa contextualizar periodo, tipo de fonte e formato do arquivo. Sem isso, a equipe acaba ajustando o processo manualmente fora do sistema.

Ao introduzir lista de destinatarios e templates simples, o produto fica mais util sem comprometer a simplicidade do backend.

## Abordagem escolhida

Foi escolhida uma abordagem enxuta:

- destinatarios como lista estruturada no modelo de agendamento
- placeholders basicos e documentados
- renderizacao simples por substituicao de tokens conhecidos
- fallback para mensagem padrao quando nenhum template for definido

Essa abordagem foi escolhida porque entrega valor imediato, e simples de testar e abre caminho para enriquecer o contexto de templates no futuro sem reescrever a integracao de e-mail.

## Placeholders suportados

Nesta primeira versao, os templates suportarao apenas estes placeholders:

- `{{schedule_name}}`
- `{{period_start}}`
- `{{period_end}}`
- `{{source_type}}`
- `{{report_format}}`
- `{{generated_at}}`

### Regras de renderizacao

- `period_start` e `period_end` serao renderizados em formato ISO de data, por exemplo `2026-06-01`
- `generated_at` sera renderizado em formato ISO UTC completo
- `source_type` usara `todos` quando o agendamento nao tiver filtro definido
- placeholders desconhecidos nao serao interpretados e permanecerao no texto como vieram

Manter placeholders desconhecidos inalterados foi escolhido para evitar falha desnecessaria em execucao e para facilitar evolucao futura dos templates.

## Modelo de dados

### Agendamento de relatorio

O modelo de agendamento sera ajustado para:

- remover `recipient_email`
- adicionar `recipient_emails`
- adicionar `body_template`

### Representacao persistida

Como a base atual prioriza simplicidade, `recipient_emails` deve ser persistido de forma simples e previsivel, seguindo o melhor encaixe com o stack atual. A implementacao pode usar serializacao em texto ou coluna JSON, desde que:

- a API exponha sempre uma lista de strings
- a persistencia continue simples de consultar e manter
- os testes cubram leitura e escrita sem ambiguidade

A decisao de persistencia deve privilegiar o menor impacto estrutural no estado atual do projeto.

## API

### Criacao de agendamento

O endpoint `POST /api/v1/report-schedules` passara a aceitar:

- `recipient_emails: string[]`
- `subject_template: string | null`
- `body_template: string | null`

Exemplo conceitual:

```json
{
  "name": "Executivo Mensal Tag",
  "report_format": "pdf",
  "source_type": "tag",
  "recipient_emails": [
    "gestao@example.local",
    "tecnico@example.local"
  ],
  "subject_template": "SLA {{schedule_name}} - {{period_start}} a {{period_end}}",
  "body_template": "Segue o relatorio {{report_format}} gerado em {{generated_at}}.",
  "day_of_month": 5
}
```

### Resposta de agendamento

A resposta passara a devolver:

- `recipient_emails`
- `subject_template`
- `body_template`

### Execucao de agendamentos vencidos

O endpoint `POST /api/v1/report-schedules/run-due` nao precisa mudar de contrato nesta etapa. A mudanca acontece internamente na entrega.

## Validacoes

As seguintes validacoes serao aplicadas no cadastro do agendamento:

- `recipient_emails` deve existir
- `recipient_emails` nao pode ser vazio
- cada item deve ser string nao vazia
- cada item deve passar em validacao basica de e-mail
- `day_of_month` continua restrito ao intervalo atual
- `report_format` e `source_type` continuam respeitando as validacoes ja existentes

Validacao de placeholders:

- templates sao opcionais
- quando informados, sao tratados como texto livre
- placeholders suportados serao substituidos
- placeholders nao reconhecidos permanecem literais

Nao havera falha de cadastro apenas porque o usuario escreveu um placeholder desconhecido. Isso evita friccao operacional e mantem a primeira versao previsivel.

## Fluxo de execucao

Quando um agendamento vencido for executado:

1. O sistema localiza os resultados mensais persistidos do periodo.
2. Gera o payload executivo.
3. Gera o arquivo PDF ou XLSX.
4. Resolve o contexto dos placeholders.
5. Renderiza assunto e corpo a partir dos templates, ou usa fallback padrao.
6. Envia um unico e-mail para todos os destinatarios da lista.
7. Registra o status de entrega na execucao.

## Comportamento de fallback

### Assunto

Se `subject_template` nao for informado, o comportamento padrao continua equivalente ao atual, contendo nome do agendamento e periodo.

### Corpo

Se `body_template` nao for informado, o sistema gera um corpo padrao contendo:

- mensagem curta de encaminhamento
- periodo do relatorio
- tipo de fonte considerada
- indicacao de anexo

## Cliente de e-mail

O cliente de e-mail passara a aceitar lista de destinatarios.

Comportamento esperado:

- preencher o campo `To` com todos os destinatarios
- anexar o arquivo normalmente
- manter fluxo TLS e autenticacao como ja existe

Nao sera implementado envio individual por destinatario nesta etapa. O objetivo e simplicidade e previsibilidade operacional.

## Registro de execucao

O modelo de execucao de agendamento continuara registrando apenas o status agregado da entrega:

- `sent`
- `failed`
- `skipped`

Sem rastreamento individual por destinatario nesta fase.

## Tratamento de erros

- Se nao houver resultados mensais para o periodo, o comportamento permanece `no_data`.
- Se a geracao do arquivo funcionar mas o envio falhar, a execucao continua com `status = generated` e `delivery_status = failed`.
- Se a execucao ja existir para o periodo, o comportamento continua `already_generated`.

Isso preserva a regra importante ja aprovada: falha de entrega nao invalida a geracao do relatorio.

## Testes

Os testes desta etapa devem cobrir pelo menos:

- criacao de agendamento com lista de destinatarios
- erro ao criar agendamento com lista vazia
- erro ao criar agendamento com e-mail invalido
- execucao com envio para multiplos destinatarios
- renderizacao de `subject_template`
- renderizacao de `body_template`
- fallback de assunto e corpo quando templates nao forem enviados
- manutencao do comportamento `failed` quando o SMTP falhar
- manutencao do comportamento `sent` quando o SMTP funcionar

## Documentacao

O `README.md` deve ser atualizado para refletir:

- suporte a multiplos destinatarios
- suporte a templates de assunto e corpo
- placeholders suportados nesta fase

## Riscos e limites

- Persistir lista em uma base relacional simples pode exigir uma representacao menos elegante internamente, mas isso e aceitavel enquanto a API permaneça limpa.
- Deixar placeholders desconhecidos passarem sem erro reduz atrito, mas tambem reduz a capacidade de avisar configuracoes incorretas. Isso e um trade-off consciente para a primeira versao.
- Envio unico para varios destinatarios e suficiente para agora, mas nao resolve futuros cenarios de auditoria por pessoa.

## Evolucao futura

Se esta etapa funcionar bem, os proximos incrementos naturais sao:

- placeholders com dados agregados do relatorio
- multiplos perfis de entrega
- retries de envio
- historico detalhado por destinatario
- filtros de distribuicao por publico tecnico e executivo
