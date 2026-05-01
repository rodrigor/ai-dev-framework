# Development instructions

This file is loaded into every AI session. Framework documents live
under `.aidev/` to keep the repo root clean. Imports below load them
into context.

> Adapt the `[ADAPT]` section at the bottom to your project. Everything
> else is perennial.

---

## Hard rules (in order of priority)

The full rationale for each rule is in the linked document. The
summary here is what the AI must always remember.

### 1. Code style — see `.aidev/CODE_STYLE.md`

Code is written to be cheap to read and safe to change by an AI agent.
Two costs guide every decision: **token cost** and **bug-injection
probability**.

- **Locality:** a function's behavior is determined by its arguments.
  No spooky action via globals, monkey-patching, or import-time side
  effects.
- **Explicit over implicit:** no metaclasses or decorators that mutate
  at import time; no auto-discovery; explicit registration.
- **Type everything** in typed languages. Forbid `Any` / `unknown` in
  production code.
- **Small, pure functions:** ≤ 40 lines target, ≤ 80 hard, CC ≤ 10.
- **One canonical way per common operation.** No two HTTP clients,
  two date libs, two ways to log.
- **No premature abstraction.** Three concrete duplicates is the
  earliest you should extract.
- **Comments explain why, not what.** Module headers explain purpose
  and contracts.
- **Errors typed and documented.** Forbid `except: pass` and bare
  `Exception`.
- **Search-friendly, consistent names.** `tenant_id` everywhere — not
  `tenantId` here, `company_id` there.

### 2. Component reuse — see `.aidev/COMPONENTS.md`

Before implementing any helper, module, service, or reusable logic
block, **consult `.aidev/COMPONENTS.md`**. Hard rules:

- Do not reimplement what exists. Reuse it.
- If you need a variation, generalize the existing component.
- If you find duplication during a refactor, unify and update
  `.aidev/COMPONENTS.md`.
- When you create something genuinely new and reusable, catalog it
  in the same delivery — path, signature, purpose.

### 3. External dependencies — see `.aidev/DEPENDENCIES.md`

- **Default answer is "don't add."** Stdlib first, existing code
  second, third-party last.
- **Always look up the latest stable version online** before pinning.
  Never trust memory.
- **Run health checks** on the candidate (active maintenance, no open
  CVEs in the proposed version, license compatible). Use the
  `dependency-evaluator` subagent.
- **Major-version upgrades** require reading the migration guide and
  writing code in the **new idiom** from day one. Create a
  `feedback_dep_<lib>_v<version>.md` memory capturing old → new
  syntax patterns.
- **Remove unused deps** in the same PR that drops the last consumer.

### 4. Production bug workflow

1. **Write a test** that reproduces the bug before fixing.
2. Confirm the test fails.
3. Fix the bug.
4. Confirm the test passes.

No exceptions.

### 5. Release notes — register every functional change

Source of truth: `CHANGELOG.md`. Every functional change records an
entry under **Unreleased**. Types: `added`, `changed`, `fixed`,
`removed`, `security`. Full process: `.aidev/PROCESS.md`.

### 6. Security — see `.aidev/SECURITY.md`

- Credentials always encrypted at rest. Never plaintext, never in env
  vars without need.
- **Never log** values of tokens, API keys, passwords — even at DEBUG.
- Auth flows: **never reveal whether an email/user exists**. Generic
  response in login / forgot / resend.
- Before opening a PR: no scanner finding at HIGH or CRITICAL
  severity.

### 7. UX/UI principles

The interface is **intuitive and minimalist** — fewest visual elements
needed to accomplish the task. Less is more, prioritize the essential,
smart defaults, suggest simplifications proactively, consistent
visual language.

### 8. Soft-delete policy

Three ways to "remove" — choose by entity type:

1. **Hard-delete** — ephemeral tokens, logs after retention.
2. **Soft-delete** (`deleted_at` nullable) — product entities that may
   be restored.
3. **Status enum** (`CANCELLED`, `ARCHIVED`) — domain state machines.

Don't introduce a fourth.

### 9. Feature flags on every new feature

Every new feature ships behind a feature flag (registry + check at
route and UI levels). Default may be `True`, but the flag must exist
to allow rapid disable in incidents.

### 10. Internationalization

Keys, enums, identifiers, and code-facing variables are written in
**English** from day one. User-visible strings go through an i18n
system.

---

## Document index

Full rules and rationale:

- `.aidev/CODE_STYLE.md` — how code should be written (AI-friendly).
- `.aidev/DEPENDENCIES.md` — when and how to add/update libraries.
- `.aidev/PROCESS.md` — workflows (bug, feature, release notes, pre-PR).
- `.aidev/QUALITY.md` — automated controls (SAST, deps, coverage,
  complexity, tests, schema).
- `.aidev/SECURITY.md` — security policies.
- `.aidev/INFRASTRUCTURE.md` — infra decisions taken at init time
  (auth, multi-tenancy, logging, feature flags, AI integration, etc.).
- `.aidev/COMPONENTS.md` — catalog of reusable components.
- `.aidev/GLOSSARY.md` — domain terminology.
- `.aidev/adr/` — Architecture Decision Records.
- `.aidev/memory-templates/` — formats for AI persistent memories.
- `.aidev/scripts/pre_pr_check.py` — pre-PR checklist.

Subagents in `.claude/agents/`:

- `release-notes-writer` — drafts CHANGELOG entries from diff.
- `component-cataloger` — proposes COMPONENTS.md additions.
- `test-quality-reviewer` — smell catalog + bug-fix verification.
- `schema-reviewer` — migration safety, multi-tenant correctness.
- `dependency-evaluator` — evaluates a candidate library.

---

## Periodic complexity & maintainability

After any **large feature** (new module, broad refactor, big fix),
run the commands in `.aidev/QUALITY.md` ("Complexity" section) and
cross with churn (git log of last 3 months).

| Metric | Threshold | Action |
|---|---|---|
| CC rank E or F | any churn | Decompose before next merge |
| CC rank D | high churn | Hotspot — refactor next sprint |
| MI rank B (< 20) | — | Priority refactor |
| MI rank C (< 10) | — | Block — decompose before next feature |

---

## [ADAPT] Project domain

List the **domain-specific rules** here: mandatory file
synchronizations, critical modules, demos to maintain, open technical
debts. See `.aidev/memory-templates/` for the catalog of memory types
the AI maintains.

## [ADAPT] Knowledge graph / code navigation

If the project uses a knowledge graph (code-review-graph or similar),
prefer it over Grep/Glob/Read.

| Task | Tool |
|---|---|
| Explore | semantic search on the graph |
| Impact | impact_radius / get_affected_flows |
| Code review | detect_changes + get_review_context |
| Relationships | callers / callees / imports / tests |

Fall back to Grep/Read **only** when the graph doesn't cover the need.
