# Development process

Perennial workflows. How the "AI implements, dev guides" cycle works
in practice.

## Standard cycle for a change

```
1. Understand the request
   └─ read CLAUDE.md, GLOSSARY.md if domain is new
2. Explore existing code
   └─ knowledge graph FIRST; Grep/Read only if graph doesn't cover
3. Consult COMPONENTS.md
   └─ is there a helper/macro/service that solves this? reuse or generalize
4. Propose approach (briefly) — wait for dev OK on non-trivial changes
5. Implement
   ├─ if a bug: TEST FIRST (see it fail) → fix → see it pass
   ├─ if a feature: feature flag is mandatory
   └─ if creating a reusable component: catalog it in COMPONENTS.md
6. Update release notes / CHANGELOG ("Unreleased" section)
7. Run pre-PR checklist (scripts/pre_pr_check.py)
8. Open PR — all scanners green (HIGH/CRITICAL = block)
```

## Production bug workflow

1. Reproduce the bug.
2. **Write a test** that fails for the bug's reason.
3. Fix.
4. Test passes.
5. Entry in release notes (`fixed`).
6. PR.

No test → bug regresses. No exceptions.

## New feature workflow

1. Register the feature flag in the registry.
2. Guard route and UI with `is_enabled(flag)`.
3. Default may be `True`, but the flag **must exist** so it can be
   disabled in an incident without redeploy.
4. Tests covering flag ON and OFF (UI/route behaves correctly in both
   states).
5. Entry in release notes (`added`).
6. If the feature creates a reusable component → catalog it.

## Release notes

Source of truth: `CHANGELOG.md` (or the project's equivalent).

- Every functional change records an entry in the **Unreleased** section.
- Types: `added`, `changed`, `fixed`, `removed`, `security`.
- If the project distinguishes user-facing vs admin/infra: keep two
  parallel tracks.
- When publishing a version: replace "Unreleased" with
  `{version, date, ...}` and create a new empty section above it.

## Pre-PR checklist

`scripts/pre_pr_check.py` validates automatically. Minimum coverage:

- [ ] Release notes updated (entry in "Unreleased")
- [ ] `COMPONENTS.md` updated if a reusable helper/service/macro was created
- [ ] Feature flag registered if a new route/feature was created
- [ ] Project-specific synchronizations (defined in `CLAUDE.md`)
- [ ] Build artifacts generated when applicable (compiled CSS,
      generated schemas)
- [ ] Existing tests pass; new tests cover the change
- [ ] SAST/deps/secrets scanners with no HIGH/CRITICAL

## Periodic complexity analysis

After **large features** (new module, broad refactor, big fix), run the
commands defined in `QUALITY.md` ("Complexity" section) and cross with
churn (git log of the last 3 months).

Hotspots (high complexity × high churn) go into the priority refactor
queue before the next feature in the same file.

## Architectural decisions → ADR

Decisions affecting system structure (DB choice, multi-tenancy, caching
strategy, primary framework, auth model) become an ADR in
`docs/adr/NNNN-title.md`. Use the `0000-template.md`.

AI memories (`project_*`) are volatile and individual; an ADR is
versioned and reviewable by the whole team.

## AI-maintained memories

The AI keeps persistent memories to accelerate future sessions. See
`memory-templates/` for the formats. Types:

- **`feedback_*`** — behavior rule the dev corrected/validated.
  E.g., "always rebuild Tailwind before committing templates".
- **`project_*`** — living context of initiatives, decisions, debts.
  E.g., "phase 2 of multi-tenancy migration".
- **`debt_*`** (subset of `project_*`) — cataloged technical debt with
  a revisit trigger.

Memories **don't replace** ADRs or documentation. They are shortcuts
so the AI doesn't repeat known mistakes.

## Periodic review

- **Memories:** quarterly consolidation (skill `consolidate-memory`).
  `project_*` memories age fast; revisit them.
- **Technical debts:** revisit when the trigger fires (passed N users,
  lib Y bumped pin, etc.).
- **CLAUDE.md:** review at every major release — rules that became
  code (hooks, scripts) can leave it.

## Principle: documentation becomes code when possible

Rules that depend on the AI "remembering" are fragile. When a rule
appears 3× in CLAUDE.md or in `feedback_*` memories, consider turning
it into a hook/script/subagent that the harness executes
deterministically.
