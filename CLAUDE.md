# Development instructions — project based on ai-dev-framework

This file is loaded into every AI session. Rules here take precedence
over agent defaults.

> Adapt sections marked `[ADAPT]` to your project. The rest is perennial
> and should remain.

---

## ⚠️ Code style — see `CODE_STYLE.md`

Code is written to be cheap to read and safe to change by an AI agent.
Hard rules (full rationale in `CODE_STYLE.md`):

- **Locality:** a function's behavior is determined by its arguments.
  No spooky action via globals, monkey-patching, or import-time side
  effects.
- **Explicit over implicit:** no metaclasses/decorators that mutate at
  import; no auto-discovery; explicit registration.
- **Type everything** in typed languages. Forbid `Any`/`unknown` in
  production code.
- **Small, pure functions:** ≤ 40 lines target, ≤ 80 hard, CC ≤ 10.
- **One canonical way per common operation.** No two HTTP clients,
  two date libs, two ways to log.
- **No premature abstraction.** Three concrete duplicates is the
  earliest you should extract.
- **Comments explain why, not what.** Module headers explain purpose
  and contracts.
- **Errors are typed and documented.** Forbid `except: pass` and bare
  `Exception`.
- **Search-friendly, consistent names.** `tenant_id` everywhere — not
  `tenantId` here, `company_id` there.

---

## ⚠️ Component reuse — ALWAYS check before coding

Before implementing any helper, module, dependency, service, macro, or
reusable logic block, **consult `COMPONENTS.md`** at the repo root.
It catalogs everything that already exists.

Hard rule:
- **Do not reimplement** something that already exists. Reuse it.
- **If you need a variation**, generalize the existing component
  (parameters, extracted common function) instead of forking it.
- **If you find duplication** during a refactor, unify and update
  `COMPONENTS.md`.
- **When you create something genuinely new and reusable**, catalog it
  in the same delivery — path, signature, purpose.

`COMPONENTS.md` is the source of truth. Keep it alive.

---

## UX/UI principles (mandatory in any interface)

The interface must be **intuitive and minimalist** — the smallest number
of visual elements needed to accomplish the task.

1. **Less is more.** Every element must justify its presence. Prefer
   hiding (collapse, tabs, modals) over stacking everything.
2. **Prioritize the essential.** Important fields at the top; secondary
   ones in collapsible sections with sensible defaults.
3. **Prioritize information in displays.** Status / name / progress
   first; metadata (author, date, IDs) in the background.
4. **Smart defaults.** Every optional field has a default that covers
   80% of cases.
5. **Suggest simplifications proactively.** If you notice excess fields,
   redundant steps, or verbose labels, **flag it before implementing**.
   Don't simplify silently.
6. **Consistent visual language.** Reuse existing patterns/components
   instead of creating variants.

These rules take precedence over point aesthetic preferences.

---

## Production bug workflow

1. **Write a test** that reproduces the bug before fixing.
2. Confirm the test fails.
3. Fix the bug.
4. Confirm the test passes.

Bugs without tests regress. No exceptions.

---

## Release notes — register every functional change

The source of truth is the project's release notes file (`CHANGELOG.md`
or equivalent). Whenever you add, change, remove, or fix a feature,
record an entry under the **Unreleased** section (top of file):

- `added` — new feature
- `changed` — change to an existing feature
- `fixed` — bug fix
- `removed` — feature removed
- `security` — security fix

When publishing a version: replace "Unreleased" with
`{version, date, ...}` and create a new empty section above it.

If the project distinguishes user-visible from admin/infra changes,
maintain two parallel tracks.

---

## External dependencies — see `DEPENDENCIES.md`

Full policy in `DEPENDENCIES.md`. Hard rules:

- **Default answer is "don't add."** Stdlib first, existing code
  second, third-party last.
- **Always look up the latest stable version online** before pinning.
  Never trust memory. Use `pip index versions`, `npm view`, etc.
- **Run health checks** on the candidate (active maintenance, no
  open CVEs in the proposed version, license compatible). Use the
  `dependency-evaluator` subagent.
- **Major-version upgrades** require reading the migration guide and
  writing code in the **new idiom** from day one. Create a
  `feedback_<lib>_v<version>.md` memory capturing old → new syntax
  patterns so future sessions don't regress.
- **Remove unused deps** in the same PR that drops the last consumer.

---

## Security — hard policies (see `SECURITY.md`)

- Credentials always encrypted at rest. Never plaintext, never in env
  vars without need.
- **Never log** values of tokens, API keys, passwords, even at DEBUG.
  SAST scanners detect and block.
- In auth flows, **never reveal whether an email/user exists**. Generic
  response in login / forgot / resend.
- Before opening a PR: no scanner finding at HIGH or CRITICAL severity.

---

## Soft-delete policy

Three ways to "remove" — choose by entity type:

1. **Hard-delete** (physical `DELETE`): ephemeral tokens, logs after
   retention, sensitive data with TTL.
2. **Soft-delete** (`deleted_at` nullable): product entities that may
   be restored. Default listing omits `deleted_at IS NOT NULL`.
3. **Status enum** (`CANCELLED`, `ARCHIVED`, `CLOSED`): domain state
   machine where history matters. Don't use `deleted_at` here.

Special cases (User.active, Tenant.archived_at) — don't duplicate the
pattern. **Don't introduce a fourth.**

---

## Periodic complexity & maintainability analysis

After any **large feature** (new module, broad refactor, big fix), run
the commands defined in `QUALITY.md` ("Complexity" section) and cross
with churn (git log of the last 3 months).

**Decision thresholds (generic; exact values in `QUALITY.md`):**

| Metric | Threshold | Action |
|---|---|---|
| CC rank E or F | any churn | Decompose before next merge to the file |
| CC rank D | high churn | Hotspot — plan refactor next sprint |
| MI rank B (< 20) | — | Priority refactor |
| MI rank C (< 10) | — | Block — decompose before any new feature |

---

## Automated controls — `QUALITY.md`

**Single source of truth for all controls** (CI, pre-commit, scanners,
tests, coverage, complexity, modularity) is `QUALITY.md`.

Consult it **before**:
- Adding/removing CI workflows
- Introducing a new linter/scanner
- Changing policy (min coverage, blocking severity, etc.)
- Investigating a CI failure

When introducing a new control, **update `QUALITY.md`** in the same
delivery: script path, what it checks, what it blocks, how to run it
locally.

---

## Confirmation of destructive actions

Use the project's modal component. **Never** native `alert()` /
`confirm()`. Define the single pattern in `COMPONENTS.md`.

---

## Feature flags on every new feature

Every new feature ships behind a feature flag (registry + check at the
route and UI levels). Default may be `True`, but the flag **must exist**
to allow rapid disable during incidents without redeploy.

---

## Internationalization

Keys, enums, identifiers, and code-facing variables are written in
**English** from the start. User-visible strings go through an i18n
system.

---

## [ADAPT] Project domain

List here the **domain-specific rules**: mandatory file synchronizations,
critical modules, demos to maintain, open technical debts. See
`memory-templates/` for the catalog of memory types the AI maintains.

---

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

---

## [ADAPT] Infrastructure choices

Infrastructure decisions taken at init time live in `INFRASTRUCTURE.md`
(authentication, authorization, multi-tenancy, logging, feature flags,
AI integration, admin areas, etc.). Consult it before adding/changing
any of those concerns.
