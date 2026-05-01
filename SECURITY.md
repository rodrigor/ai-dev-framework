# Políticas de segurança

Documento perene. Vale para qualquer projeto baseado neste framework.
Decisões específicas de stack (qual scanner, qual versão) ficam em
`QUALITY.md`.

## Pipeline de segurança automatizado (CI)

Toda mudança passa por três classes de scanner antes do merge:

1. **SAST** — análise estática de código (segredos em logs, injeção SQL,
   path traversal, criptografia fraca, etc.).
2. **Análise de dependências** — CVEs conhecidos em libs e ambiente.
3. **Detecção de segredos** — chaves, tokens, credenciais commitadas.

Antes de abrir PR: nenhum scanner reporta finding **HIGH** ou **CRITICAL**.

A escolha das ferramentas é definida em `QUALITY.md` baseada na stack.

## Credenciais e segredos

- **Sempre criptografados em repouso.** Use cifragem simétrica forte
  (Fernet/AES-GCM) com chave derivada de uma master key não commitada.
- Master key vem de variável de ambiente ou secret manager — **nunca** do
  código nem de arquivo versionado.
- Credenciais de tenants (API keys de IA, SMTP de empresa) seguem o mesmo
  padrão. Apenas os últimos 4 caracteres podem ser exibidos na UI.
- **Nunca logar** valores de tokens, API keys, senhas — mesmo em DEBUG.
  O SAST detecta e bloqueia.
- Credenciais saem da memória assim que possível (não persistir em
  variáveis globais).

## Autenticação

Padrões aplicáveis a qualquer fluxo de auth:

- **Senha:** mínimo 12 chars, máximo 256, sem caracteres de controle.
  Hash com bcrypt (rounds ≥ 12), Argon2id ou scrypt.
- **Magic link:** TTL curto para login (15 min), TTL longo para convite
  inicial (7 dias). Use `kind` separado no token.
- **Reset de senha:** token TTL 30 min, single-use, invalida pendentes
  do mesmo usuário.
- **Resposta genérica em login/forgot/resend:** nunca revele se o email
  existe. Mensagem padrão "se houver conta, enviamos um email".
- **Rate limiting** em endpoints de auth (login, forgot, resend, verify).

## Bugs em produção — fluxo obrigatório

1. Escreva um teste que reproduza o bug.
2. Confirme que falha.
3. Corrija.
4. Confirme que passa.

Bugs sem teste regridem. Não há exceção.

## Dependências externas — versão mais recente

Antes de adicionar lib ao manifesto, **busque a versão estável mais recente
no índice oficial** (PyPI/npm/crates.io/etc.) e fixe essa. Versões antigas
podem estar faltando patches de CVE.

Se a CI reportar CVE em lib transitiva, atualize o pin direto que puxa essa
transitiva — não ignore.

## Logs e PII

- Não logar PII (CPF, email completo, telefone) em nível INFO ou superior.
  Use DEBUG e mascare (`r***@example.com`).
- Tokens, senhas, chaves: **nunca** em qualquer nível.
- Stack traces que possam vazar dados sensíveis: sanitizar antes de
  enviar para serviço externo (Sentry/etc).

## Multi-tenancy (se aplicável)

- Toda query de leitura/escrita filtra por `tenant_id` na camada de
  middleware/dependency, não por convenção do desenvolvedor.
- Testes de regressão verificam que tenant A não vê dados de tenant B.
- Impersonação por sysadmin é auditada com timestamps de início/fim.

## Headers de segurança HTTP (web apps)

- `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY` (ou CSP frame-ancestors).
- `Content-Security-Policy` restritiva. Sem `unsafe-inline` em produção.
- Cookies de sessão: `Secure`, `HttpOnly`, `SameSite=Lax` (ou Strict).

## Auditoria

Eventos sensíveis (login, mudança de permissão, impersonação, exclusão
de dados, mudança de credencial) gravados em log de auditoria com:
ator, ação, alvo, timestamp, IP/user-agent. Retenção definida em política
do projeto.
