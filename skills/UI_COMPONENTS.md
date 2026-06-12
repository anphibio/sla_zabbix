# UI_COMPONENTS.md

## Objetivo

Definir componentes reutilizáveis obrigatórios para manter consistência visual.

## Componentes base

- AppLayout
- Sidebar
- Topbar
- Breadcrumb
- PageHeader
- Card
- StatCard
- DataTable
- Modal
- Drawer
- Toast
- ConfirmDialog
- EmptyState
- ErrorState
- LoadingState
- FormField
- SelectField
- DatePicker
- SearchInput
- FilterBar
- Pagination
- StatusBadge
- UserMenu
- ThemeToggle

## Regras

- Componentes devem ser reutilizáveis.
- Evitar duplicação visual.
- Evitar telas criando componentes locais sem necessidade.
- Estados de loading, erro e vazio devem ser padronizados.
- Ações destrutivas devem usar ConfirmDialog.
- Tabelas devem reutilizar DataTable.
- Feedbacks devem usar Toast ou componente equivalente.

## Relação com Impeccable

Todos os componentes devem seguir `IMPECCABLE_UI.md`.
