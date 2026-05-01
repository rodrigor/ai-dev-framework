# Security policies

Perennial document. Applies to any project based on this framework.
Stack-specific decisions (which scanner, which version) live in
`QUALITY.md`.

## Automated security pipeline (CI)

Every change passes through three classes of scanner before merge:

1. **SAST** — static code analysis (secrets in logs, SQL injection,
   path traversal, weak crypto, etc.).
2. **Dependency analysis** — known CVEs in libraries and runtime.
3. **Secret detection** — keys, tokens, credentials committed.

Before opening a PR: no scanner reports a finding at **HIGH** or
**CRITICAL** severity.

Tool selection is defined in `QUALITY.md` based on the stack.

## Credentials and secrets

- **Always encrypted at rest.** Use strong symmetric encryption
  (Fernet/AES-GCM) with a key derived from a non-committed master key.
- Master key comes from an environment variable or secret manager —
  **never** from code or a versioned file.
- Tenant credentials (AI API keys, company SMTP) follow the same
  pattern. Only the last 4 characters may be displayed in the UI.
- **Never log** values of tokens, API keys, passwords — even at DEBUG.
  SAST detects and blocks.
- Credentials leave memory as soon as possible (do not persist in
  global variables).

## Authentication

Patterns applicable to any auth flow:

- **Password:** minimum 12 chars, maximum 256, no control characters.
  Hash with bcrypt (rounds ≥ 12), Argon2id, or scrypt.
- **Magic link:** short TTL for login (15 min), long TTL for initial
  invite (7 days). Use a separate `kind` on the token.
- **Password reset:** token TTL 30 min, single-use, invalidates pending
  tokens for the same user.
- **Generic response in login/forgot/resend:** never reveal whether the
  email exists. Standard message: "if there is an account, we sent an
  email".
- **Rate limiting** on auth endpoints (login, forgot, resend, verify).

## Production bug — mandatory flow

1. Write a test that reproduces the bug.
2. Confirm it fails.
3. Fix.
4. Confirm it passes.

Bugs without tests regress. No exceptions.

## External dependencies — latest version

Before adding a lib to the manifest, **search for the latest stable
version on the official index** (PyPI/npm/crates.io/etc.) and pin that.
Old versions may be missing CVE patches.

If CI reports a CVE in a transitive dep, update the direct pin that
pulls it — don't ignore.

## Logs and PII

- Do not log PII (national ID, full email, phone) at INFO or above.
  Use DEBUG and mask (`r***@example.com`).
- Tokens, passwords, keys: **never** at any level.
- Stack traces that may leak sensitive data: sanitize before sending
  to external service (Sentry/etc).

## Multi-tenancy (when applicable)

- Every read/write query filters by `tenant_id` at the
  middleware/dependency layer, not by developer convention.
- Regression tests verify that tenant A cannot see tenant B's data.
- Sysadmin impersonation is audited with start/end timestamps.

## HTTP security headers (web apps)

- `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY` (or CSP frame-ancestors).
- Restrictive `Content-Security-Policy`. No `unsafe-inline` in
  production.
- Session cookies: `Secure`, `HttpOnly`, `SameSite=Lax` (or Strict).

## Audit log

Sensitive events (login, permission change, impersonation, data
deletion, credential change) recorded in an audit log with: actor,
action, target, timestamp, IP/user-agent. Retention defined in the
project's policy.
