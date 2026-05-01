# Infrastructure decisions

Catalog of non-functional infrastructure capabilities the framework
configures. The `/init-project` skill walks through the questions
below and crystalizes the answers in `.aidev/config/project.config.toml`.

> **Status:** `[SKELETON — fill in via init-project]`
> After init, replace the catalog with a section per chosen capability,
> documenting what was decided and why.

## How to read this document

Each section lists:
- **Question** the dev answers at init.
- **Default** suggested when there's no strong reason otherwise.
- **Options** with one-line trade-offs.
- **Generated artifacts** if chosen.
- **Watch-outs** that affect ongoing development.

---

## 1. Containerization

**Question:** Run in containers?
**Default:** Docker
**Options:**
- `docker` — `Dockerfile` + `docker-compose.yml` (dev), production
  image multi-stage.
- `podman` — same surface as Docker, rootless by default.
- `none` — host install with `pyenv`/`nvm`/`asdf`.

**Generated:** `Dockerfile`, `docker-compose.yml`, `.dockerignore`,
healthcheck, non-root user, multi-stage build.

**Watch-outs:** if no Node in production image, frontend build artifacts
must be precompiled and committed (see `pre_pr_check.py` sync rule).

---

## 2. Stack

**Question:** Primary language(s) and web framework?

### Rationale: language choice for AI-driven development

Two axes determine cost: **token cost** (how many tokens equivalent
code consumes) and **AI maintainability** (training-data depth, idiom
uniformity, type safety). They often pull against each other — a
verbose typed language costs more tokens to read but lets the agent
make safer changes.

**Top tier (best balance):**

| Language | Token cost (Python = 1.0×) | Training corpus | Idiom uniformity | Notes |
|---|---|---|---|---|
| **Python** + strict types (mypy/pyright) + Pydantic | 1.0× | huge | medium | Cheapest tokens, largest corpus. Strict typing closes the dynamic-typing risk. |
| **TypeScript** strict mode | ~1.3× | huge | medium-high | Strong types catch most refactor breakage. ~25% token premium pays off in fewer iterations. |
| **Go** | ~1.45× | high | **very high** | Token premium offset by extreme idiom uniformity — agent decisions are predictable. |

**Honorable mention:**
- **Kotlin** — modern JVM, less verbose than Java, less training data than top 3.
- **Rust** — compiler eliminates whole bug classes, but lifetime/borrow puzzles cost agent iterations. Use only when performance/safety justify it.

**Avoid for AI-driven maintenance unless forced:**
- **Plain JavaScript** — every refactor is a coin flip without types.
- **Java** without Kotlin — token-expensive, ceremonial.
- **Ruby + Rails** — auto-loading, monkey-patching, metaprogramming everywhere → magic at the wrong layer for an agent.
- **C++** — token-expensive, footguns, training corpus has too much obsolete style.
- **Clojure / Elixir / OCaml** — fine languages, but small training corpus = more cautious sessions, more iterations.

### Defaults by use case

| Use case | First choice | Second |
|---|---|---|
| Backend SaaS | Python (FastAPI) **or** TypeScript (Hono/Express) | Go (chi) |
| CLI tools | Go | Python |
| Service-oriented backend | Go | Rust |
| Frontend | TypeScript + Vite + React | Svelte |
| Data / ML pipelines | Python | — |
| Performance-critical service | Go | Rust |
| Mobile (Android) | Kotlin | — |
| Mobile (iOS) | Swift | — |

### Two non-obvious points

1. **Token economy at the session level matters more than at the file
   level.** Type-rich code costs more tokens to read but produces
   fewer wrong refactors. Total tokens consumed across a long-running
   project are lower with strict TypeScript than with plain
   JavaScript, even though TS files look longer.

2. **Idiom uniformity beats raw token economy.** Go is more verbose
   than Python, but every Go codebase looks the same — agent doesn't
   re-orient per project. Python codebases vary enormously
   (Django/FastAPI/Flask). `CODE_STYLE.md`'s "one canonical way per
   common operation" is meant to give Python codebases Go-like
   uniformity.

### Other choices (when applicable)

- Backend Python: **FastAPI** (recommended), Litestar, Starlette.
- Backend TS: **Hono** (modern, fast), Express (mature), Fastify.
- Backend Go: **chi** or **echo** (or `net/http` for ultra-minimal).
- Frontend: **React + Vite** or **Svelte/SvelteKit**.

If the team has strong reasons (existing codebase, hiring pool,
performance budget) to choose differently, respect it — but document
the trade-off in an ADR.

**Generated:** project skeleton, manifest with pinned versions
(latest stable, fetched at init), entry-point file, healthcheck route.

**Watch-outs:** stack drives the entire `QUALITY.md` table.

---

## 3. Database

**Question:** Primary persistence?
**Default:** Postgres
**Options:**
- `postgres` — robust, full-featured, requires server.
- `sqlite` — single file, zero-config, great for low-volume SaaS and
  embedded.
- `mysql` — when team/infra already standardizes on it.
- `mongodb` — for documents with weak schema.

**Generated:** connection layer, migration framework
(Alembic/Prisma/etc.), `models/` skeleton, test fixture using a
test DB.

**Watch-outs:** SQLite limits concurrent writes — fine until ~50
req/s of writes, then needs to migrate.

---

## 4. Multi-tenancy

**Question:** Tenancy model?
**Default:** none (single-tenant)
**Options:**
- `none` — single tenant. App.
- `shared-db` — `tenant_id` column in every tenant-scoped table,
  middleware enforces filtering.
- `db-per-tenant` — one database per tenant. Strongest isolation,
  more migration complexity.
- `schema-per-tenant` (Postgres) — schemas as namespaces.

**Generated:**
- Tenant model + middleware for resolution (subdomain / header / path).
- Filtering enforced at session/dependency layer (not by convention).
- Regression test verifying tenant A cannot see tenant B's data.
- Audit log scoped per tenant.

**Watch-outs:** any change to model schema in `db-per-tenant` requires
running migrations across all tenant DBs — plan a migration runner.

---

## 5. Authentication methods

**Question:** Which login methods are enabled?
**Default:** password + magic link
**Options (multi-select):**
- `password` — email + password, bcrypt/argon2.
- `magic-link` — email-only, short TTL token.
- `oauth-google` — Google OIDC.
- `oauth-microsoft` — Azure AD / Entra ID OIDC.
- `oauth-github` — GitHub OAuth.
- `oauth-apple` — Sign in with Apple.
- `saml-sso` — enterprise SAML/SSO (often gated to enterprise plans).
- `webauthn-passkeys` — passkey (FIDO2) — modern, no password.

**Generated:**
- Login routes per method, callback handlers for OAuth.
- Magic link issuance with `kind=login` (15 min) and `kind=invite`
  (7 days) — different TTLs.
- Password policy (12–256 chars, controls), reset-token flow (30 min,
  single-use).
- Generic responses (no email enumeration).
- Rate limiting on `/login`, `/forgot`, `/resend`, `/verify`.

**Watch-outs:** OAuth requires per-provider client_id/secret in secret
storage; never commit. CSRF protection on the OAuth callback is
mandatory.

---

## 6. Authorization model

**Question:** Permission model?
**Default:** simple RBAC scoped to tenant
**Options:**
- `none` — no authorization (only dev tools, internal demos).
- `simple-rbac` — fixed roles (e.g., `admin`, `member`, `viewer`).
- `scoped-rbac` — RBAC with scope (per tenant, per project, per group).
- `abac` — attribute-based — policy engine (OPA/Casbin) evaluates
  rules. Use only when scoped-RBAC isn't enough.
- `groups` — users belong to groups; permissions are attached to groups.

**Generated:**
- Role/Permission/Group models.
- Decorator/dependency for permission check on routes.
- Admin UI for assigning roles (gated to tenant admins).
- Audit log entry for every permission grant/revoke.

**Watch-outs:** test matrix grows quickly. Add at least one test per
sensitive route × role combination.

---

## 7. Admin areas

**Question:** Which admin surfaces?
**Default:** sysadmin (global) + tenant-admin
**Options (multi-select):**
- `sysadmin` — global admin (system config, tenants, users across
  tenants, impersonation, release notes).
- `tenant-admin` — per-tenant admin (tenant settings, users in this
  tenant, billing).
- `both` — both surfaces.
- `none` — no admin (internal tools only).

**Generated:**
- `/admin` routes gated by sysadmin role; `/<tenant>/admin` for tenant
  admin.
- Dashboard cards per admin capability (impersonation, tenants, users,
  feature flags).
- Audit log of every admin action.
- Auto-link in nav for every new admin feature (avoid orphaned pages).

**Watch-outs:** every new admin feature must be linked in the admin
navbar AND on the dashboard. The pre-PR check should catch orphaned
admin pages.

---

## 8. Logging

**Question:** Log format and destination?
**Default:** structured JSON + correlation ID, stdout
**Options:**
- `text` — human-readable single line.
- `json` — structured (recommended for any production system).
- `correlation-id` — every request gets a trace ID propagated through
  all logs.
- Sinks: stdout (container-friendly), file with rotation, syslog,
  aggregator (Loki/ELK/Datadog).

**Generated:** logging config, request middleware that injects
correlation ID, masking helpers for PII.

**Watch-outs:** never log tokens, API keys, passwords. SAST should
catch but reviewers must too. Mask PII (`r***@example.com`).

---

## 9. Observability

**Question:** Metrics, traces, healthcheck?
**Default:** healthcheck + readiness; metrics if Prometheus available
**Options:**
- `healthcheck` — `/healthz` (liveness) + `/readyz` (readiness).
- `metrics-prometheus` — `/metrics` exposing standard counters.
- `metrics-otel` — push to OpenTelemetry collector.
- `tracing-otel` — distributed traces.
- `error-tracking` — Sentry / Honeybadger / GlitchTip.

**Generated:** routes, middleware, default counters (request count,
error rate, p95 latency), trace spans on DB and HTTP calls.

**Watch-outs:** healthcheck must NOT touch the DB on liveness, only on
readiness. Otherwise a DB blip kills pods.

---

## 10. Feature flags

**Question:** Flag implementation?
**Default:** internal registry (lightweight)
**Options:**
- `internal-registry` — Python/JS dict + DB override per tenant.
  Cheap, sufficient for most SaaS.
- `unleash` — open-source server, per-tenant, gradual rollout.
- `growthbook` — A/B testing + feature flags.
- `launchdarkly` — paid, enterprise.

**Generated:** `FEATURE_FLAG_REGISTRY` source, `is_enabled(flag, tenant)`
check, admin UI to toggle, default new-feature template includes flag.

**Watch-outs:** every new feature ships behind a flag. Default may be
`True` but the flag must exist for fast disable in incidents.

---

## 11. Transactional email

**Question:** Email provider?
**Default:** SMTP (any provider)
**Options:**
- `smtp` — works with any provider (SES via SMTP, Mailgun, SendGrid,
  custom).
- `aws-ses` — direct SDK.
- `resend` — modern API, dev-friendly.
- `postmark` — focused on transactional.

**Generated:** email service with templates (login link, invite,
password reset, generic notification), encrypted credentials in
config.

**Watch-outs:** SPF/DKIM/DMARC must be configured at the DNS layer.
Test bounces in staging.

---

## 12. File storage

**Question:** Where do uploaded files live?
**Default:** filesystem (single-host) or S3-compatible (multi-host)
**Options:**
- `filesystem` — local, simple. Doesn't survive multi-replica.
- `s3` — AWS S3 or compatible (Spaces, R2, Minio).
- `local-with-s3-fallback` — dev local, prod S3.

**Generated:** storage abstraction, signed URL helpers, virus scan
hook (optional).

**Watch-outs:** never trust filenames from clients (path traversal).
Sanitize at upload. Limit MIME types and size.

---

## 13. Background jobs

**Question:** Async/scheduled jobs?
**Default:** none (until needed)
**Options:**
- `none` — synchronous everything.
- `framework-native` — APScheduler / FastAPI BackgroundTasks /
  node-cron — for small scheduled tasks.
- `celery` (Python) — robust, requires Redis/RabbitMQ.
- `rq` (Python) — simpler than Celery.
- `bullmq` (Node) — Redis-backed.
- `temporal` — workflow engine for durable orchestrations.

**Generated:** job runner config, retry policy, dead-letter queue,
monitoring.

**Watch-outs:** jobs must be idempotent. Always include a retry budget
and DLQ.

---

## 14. Cache

**Question:** Caching layer?
**Default:** none (until measured need)
**Options:**
- `none`
- `in-memory` — process-local. Doesn't share across replicas.
- `redis` — shared, supports pub/sub and queues.
- `memcached` — simpler than Redis if pure cache.

**Generated:** cache wrapper, TTL defaults, invalidation patterns.

**Watch-outs:** never cache tenant-scoped data with a tenant-agnostic
key. Cache keys always include tenant context.

---

## 15. AI integration

**Question:** AI/LLM integration?
**Default:** none (until product needs it)
**Options:**
- `none`.
- `litellm` — multi-provider abstraction (OpenAI, Anthropic, Bedrock,
  Gemini, Groq, etc.). Recommended for SaaS that lets tenants choose
  provider.
- `openai-direct` — single provider via official SDK.
- `anthropic-direct` — single provider via Anthropic SDK.

**Generated:** AI module with provider config encrypted per tenant,
playground page (sysadmin), feature flag, retry/timeout policy,
token usage tracking.

**Watch-outs:** API keys per tenant encrypted with same Fernet/AES
master key. Display only last 4 chars in UI. Never log prompts that
may contain PII unless dev opted in.

---

## 16. External webhooks

**Question:** Webhooks?
**Default:** none
**Options:**
- `none`.
- `receive` — accept webhook calls (Stripe, GitHub, etc.) — needs
  signature verification.
- `send` — send webhook calls to external systems on events — needs
  retry, signature signing.
- `both`.

**Generated:** webhook receiver routes with signature middleware,
sender service with retry/DLQ.

**Watch-outs:** always verify signatures; never trust webhook payloads
without signature.

---

## 17. Privacy/compliance

**Question:** Does the project handle PII? Is GDPR/LGPD applicable?
**Default:** assume yes for any SaaS handling user data
**Options (multi-select):**
- `pii-handling` — affects logging policy, masking, retention.
- `lgpd` — Brazilian privacy law. Requires retention policy, data
  export, account deletion.
- `gdpr` — EU privacy law. Requires export, deletion, data processing
  records.
- `audit-trail` — sensitive events in a separate auditable log.

**Generated:** retention runner (cron), data-export endpoint, account
deletion flow (with grace period), PII masking helpers, audit log
schema.

**Watch-outs:** retention runs delete data — test it heavily. Account
deletion may need to retain audit trail (legal hold) — separate model
for that.

---

## How this section gets populated

After `/init-project`, this `INFRASTRUCTURE.md` will look like:

```markdown
# Infrastructure decisions for <project name>

Decided on YYYY-MM-DD.

## Containerization
Decision: Docker (multi-stage, non-root).
Files: Dockerfile, docker-compose.yml, .dockerignore.

## Stack
Decision: Python 3.12 + FastAPI 0.115.x; React 19 + Vite 6 frontend.
...
```

Each section becomes a fact about the project, not a question. The
catalog above is collapsed / removed once decisions are taken.
