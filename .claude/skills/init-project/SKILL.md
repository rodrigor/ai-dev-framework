---
name: init-project
description: Initializes a project based on ai-dev-framework. Detects the technology stack (Python, Node/TypeScript, Go, Rust, Java/Kotlin) by reading project manifests, asks the developer about non-functional requirements (containerization, auth methods, authorization model, multi-tenancy, logging, feature flags, AI integration, admin areas, email, file storage, background jobs, cache), proposes the tooling table (SAST, deps, coverage, cyclomatic complexity, modularity, secrets, lint, format, types), confirms gates (min coverage, blocking severity), and generates the populated artifacts — QUALITY.md, INFRASTRUCTURE.md, CI workflow, .pre-commit-config.yaml, tool configs, project.config.toml. Use when the user asks to initialize, configure, set up, or bootstrap a new project, or mentions "init project", "configure quality", "choose quality tools".
---

# init-project

Initializes a project based on the `ai-dev-framework`.

## When to use

- Brand-new repository freshly cloned from the template.
- Existing project adopting the framework.
- Stack change requiring tool revision.

## Procedure

### 1. Detect the stack

Read, in parallel, the manifests present:

| File | Stack |
|---|---|
| `pyproject.toml`, `requirements.txt`, `setup.py`, `Pipfile` | Python |
| `package.json` (+ `tsconfig.json` → TypeScript) | Node/TS |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pom.xml`, `build.gradle*` | Java/Kotlin |
| `Gemfile` | Ruby |
| `composer.json` | PHP |

There may be more than one stack (e.g., Python backend + TS frontend).
Handle each.

### 2. Ask about non-functional requirements (NFRs)

Use `.aidev/INFRASTRUCTURE.md` as the catalog. Walk through the questions in
this order (one at a time, with a suggested default):

**Layer 1 — Structural decisions**
1. Primary stack (language + web framework). Defaults by use case
   (see `.aidev/INFRASTRUCTURE.md` "Stack" section for the full rationale):
   - Backend SaaS → **Python (FastAPI)** or **TypeScript (Hono)**
   - Service / CLI → **Go**
   - Frontend → **TypeScript + Vite + React**
   - ML / data → **Python**
   Always recommend strict typing (mypy/pyright for Python, `strict`
   for TS).
2. Database (Postgres / SQLite / MySQL / Mongo)
3. Multi-tenancy? (none / shared-DB with `tenant_id` / DB-per-tenant)
4. Containerization (Docker / none)

**Layer 2 — Auth & authorization**
5. Auth methods (password, magic link, Google, Microsoft, GitHub, SAML SSO)
6. Authorization model (none / simple RBAC / RBAC with scope / ABAC)
7. Admin areas (sysadmin global, tenant admin, both, none)

**Layer 3 — Operations**
8. Logging (text / structured JSON / with correlation ID)
9. Healthcheck/readiness endpoints
10. Metrics (Prometheus / none)
11. Distributed tracing (OpenTelemetry / none)
12. Log retention (days)

**Layer 4 — Product features that become infra**
13. Feature flags (yes — internal registry / Unleash / none)
14. Transactional email (SMTP / SES / Resend / Postmark)
15. Background jobs (Celery / RQ / framework-native / none)
16. File storage (filesystem / S3-compatible)
17. Cache (Redis / in-memory / none)

**Layer 5 — AI and integrations**
18. AI integration (none / LiteLLM multi-provider / direct provider SDK)
19. External webhooks (receive / send / both / none)

**Layer 6 — Compliance/policy**
20. Project handles PII? (affects logging, retention, exports)
21. LGPD / GDPR applicable? (generates retention policy, export, delete)
22. Audit log (sensitive events in separate log / none)

Persist all answers into `.aidev/config/project.config.toml`.

### 3. Propose the tooling table

Based on `.aidev/QUALITY.md` ("Reference table by stack" section). For each
function (SAST, deps, coverage, complexity, modularity, secrets,
lint, format, types, dead code), present:

- Suggested default tool
- Alternatives
- Install/use command

Present as a table and ask for confirmation per row. Allow the dev to
override any choice.

### 4. Ask about gates

Ask the following (one at a time, with a default):

- **Initial minimum coverage?** (default: 60%, +1pp per release)
- **Branch coverage in addition to line?** (default: yes)
- **Mutation testing cadence?** (default: weekly CI job; alternatives:
  per-PR / off)
- **Initial mutation-score floor?** (default: 60%, target 80% in 6 months)
- **Dep severity that blocks?** (default: HIGH and CRITICAL)
- **Max accepted CC without review?** (default: rank D — `radon` or
  equivalent)
- **Min MI?** (default: 20)
- **Secrets policy?** (default: gitleaks blocks any match)
- **Run on local pre-commit?** (default: lint + format + gitleaks)

### 4b. Ask about database schema quality (if `database != "none"`)

- **Migration linter?** (default: `squawk` for Postgres,
  `strong_migrations` for Rails-style, `atlas` for generic)
- **Schema snapshot committed?** (default: yes — generate `schema.sql`
  on every migration, diff visible in PRs)
- **ERD generation in CI?** (default: yes)
- **Drift detection in staging/prod?** (default: yes if Postgres/MySQL)
- **Tenant-isolation regression test?** (default: yes if
  `multi_tenancy = "shared-db"`)

### 5. Before pinning versions — fetch the latest

For each chosen tool, **fetch the latest stable version online** (PyPI
/ npm / crates.io / GitHub releases) before pinning in the manifest.
Don't trust known values — they may be stale.

### 6. Generate artifacts

Create/update:

1. **`.aidev/QUALITY.md`** — populated with the real tools and gates. Remove
   the `[STACK X]` sections that don't apply.
2. **`.aidev/INFRASTRUCTURE.md`** — populated with the dev's NFR answers.
3. **`.aidev/config/project.config.toml`** — declarative configuration that
   crystalizes the answers (drives regeneration later).
4. **`.github/workflows/quality.yml`** (or GitLab CI / Bitbucket) with
   one job per gate.
5. **`.pre-commit-config.yaml`** with local hooks.
6. **Tool configs:**
   - Python: `pyproject.toml [tool.ruff]`, `[tool.mypy]`,
     `[tool.pytest.ini_options]`
   - Node: `eslint.config.js` or `biome.json`, strict `tsconfig.json`,
     `vitest.config.ts`
   - Others by stack
7. **`.gitleaks.toml`** with a minimal allowlist.
8. **Initial entry in `CHANGELOG.md`** documenting the init.
9. **Stack/infra-specific scaffolding** (when applicable):
   - `Dockerfile` + `docker-compose.yml` if containerization
   - Auth scaffolding (login routes, magic-link/OAuth handlers,
     password policy)
   - Tenant middleware if multi-tenant
   - Admin area shell if requested

### 7. Smoke test

For each installed tool, run in `--version` mode or against an empty
diff to confirm it's functional. Report what passed and what failed.

### 8. Final summary

Present:
- Detected stack(s)
- Selected tools (table)
- Configured gates
- NFRs decided (auth methods, multi-tenancy, etc.)
- Created/modified files
- Next steps (run `pre-commit install`, configure CI secrets, fill
  `.aidev/GLOSSARY.md`, etc.)

## Principles

- **Don't impose:** always present default + alternatives. Dev decides.
- **Latest version:** always fetch before pinning.
- **Minimum viable:** start with conservative gates. Tighten over time.
- **Document the "why":** when generating `.aidev/QUALITY.md`, briefly comment
  the reason for each choice.
- **Idempotent:** rerunning `/init-project` should reconcile, not
  duplicate. Use `.aidev/config/project.config.toml` as state.
