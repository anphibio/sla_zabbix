# SECURITY.md

## Segurança obrigatória

Todo sistema deve considerar OWASP Top 10.

## Autenticação

Preferencialmente:

- JWT com expiração curta
- Refresh token seguro
- Senhas com hash forte
- Integração futura com LDAP/AD
- Integração futura com SSO

## Autorização

- RBAC quando houver perfis
- Separar permissões por ação
- Validar permissões no backend
- Nunca confiar apenas no frontend

## Senhas e secrets

Proibido:

- Hardcoded secrets
- Token em repositório
- Senha em log
- Chave privada em código

Obrigatório:

- `.env`
- `.env.example`
- Secrets fora do Git

## APIs

- Validar todas as entradas
- Sanitizar dados quando necessário
- Usar queries parametrizadas
- Aplicar rate limit
- Aplicar CORS restritivo
- Não expor stack trace
- Não retornar dados sensíveis

## Logs

Nunca logar:

- Senhas
- Tokens
- Cookies
- Headers de autorização
- Dados sensíveis sem necessidade

## Auditoria

Registrar ações críticas conforme `OBSERVABILITY_FIRST.md`.
