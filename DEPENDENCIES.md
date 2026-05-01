# Dependency policy

How to add, update, and audit external dependencies.

The fewer dependencies, the less risk: every dep is a future security
incident, breaking change, or abandonware risk. Default answer to "do
we need this lib?" is **no** — until proven otherwise.

---

## When you may add a dependency

Pass **all** of these tests before adding:

1. **Real need.** The functionality is non-trivial, well-specified, and
   used in ≥ 2 places (or will be). Don't pull a lib for a 10-line
   utility you can write yourself.
2. **No equivalent already in the project.** Check `COMPONENTS.md` and
   the existing dependency tree.
3. **No reasonable standard-library option.** Prefer the runtime's
   stdlib where it suffices.
4. **Active maintenance.** See "Health checks" below.
5. **License compatible** with the project's license.
6. **No critical CVE in the latest stable.** Run `pip-audit` / `npm
   audit` / `cargo audit` against a throwaway install.

If any test fails, don't add. Document the alternative chosen in
`COMPONENTS.md` (or write the helper inline).

---

## Health checks for a candidate library

Before pinning, verify (the AI agent must do this and report findings):

| Signal | Where | Threshold |
|---|---|---|
| Last release | PyPI / npm / crates.io / GitHub Releases | < 12 months ago |
| Open issues vs closed | GitHub Insights | active triage; not unbounded backlog |
| Last commit on default branch | GitHub | < 6 months |
| Maintainer count | GitHub contributors | ≥ 2 active (bus factor) |
| Stars/downloads | registry / GitHub | rough sanity — not the only signal |
| Security policy | `SECURITY.md` in repo | exists, with disclosure process |
| Open CVEs | osv.dev / GitHub Advisories | none unfixed in latest |
| Tests / CI | repo CI badge | green; meaningful test suite |
| Type definitions | repo / DefinitelyTyped | available for typed languages |
| Breaking-change history | CHANGELOG / release notes | predictable cadence |

**Yellow flags** (proceed with caution, document in ADR):
- Single maintainer / "abandonware" pattern
- Last release > 12 months ago but the lib is small and stable
- Heavy dependency tree (transitive risk)
- License clauses that may limit commercial use

**Red flags** (do not add):
- Repository archived / no commits in > 18 months
- Known critical CVE without backport
- Maintainer history of supply-chain incidents (typosquatting,
  malicious updates)
- License incompatible (GPL into proprietary, etc.)

---

## Always pin the latest stable version

Before writing any pin in the manifest:

1. **Look up the latest stable version online.** Don't trust memory
   or examples.
   - Python: `pip index versions <pkg>` or `https://pypi.org/project/<pkg>/`
   - Node: `npm view <pkg> version` or `https://www.npmjs.com/package/<pkg>`
   - Rust: `cargo search <pkg>` or `https://crates.io/crates/<pkg>`
   - Go: `https://pkg.go.dev/<module>`
   - Java: `https://search.maven.org/`
2. **Pin that exact version** (or the appropriate range — see
   "Pinning strategy" below).
3. **Verify CVE status** of that version (`pip-audit`, `npm audit`,
   `cargo-audit`, `osv-scanner`, `trivy fs`).

> Why: AI memory of versions is often stale by months. Pinning a known
> version may skip CVE patches released since.

### Pinning strategy

- **Application code (deployable):** pin exact versions
  (`==1.2.3`, `1.2.3`, `=1.2.3`). Reproducible builds.
- **Library code (published):** range pins
  (`>=1.2,<2`, `^1.2`) so consumers can resolve.
- **Dev dependencies:** range pins are acceptable; keep updated.

---

## When the new version requires new syntax

A new major version of a dependency often introduces:

- New API patterns (e.g., Pydantic v1 → v2: `BaseModel.dict()` →
  `model_dump()`).
- Removal/rename of helpers.
- New configuration shape.
- Async by default vs sync.
- Different type-hint conventions.

**Hard rule:** when adopting a new major version, code is written in
the new idiom from day one. Don't write the old syntax just because
"that's what we know."

**Procedure:**

1. Read the **migration guide** in the lib's documentation. Most
   well-maintained libs publish one (e.g., Pydantic v2 migration,
   FastAPI 0.x → 1.x, React 18 → 19).
2. List the breaking changes that affect this project (search the
   codebase for old-API usages).
3. **Create a `feedback_<lib>_v<version>.md` memory** capturing the
   new idiom (see `memory-templates/feedback_template.md`). The memory
   must include:
   - Old syntax → new syntax mapping (concrete examples)
   - Common pitfalls during migration
   - Where to find the migration guide URL
4. Update existing usages in the same PR, in batches if large.
5. Add SAST/lint rules where possible to forbid the old syntax.

**Why a memory:** future sessions of the AI agent (or new contributors)
won't read old-version examples and re-introduce deprecated syntax.
The memory is the contract.

---

## Updating dependencies (routine)

### Cadence

- **Security-critical (HIGH/CRITICAL CVE):** within 24 hours of CVE
  disclosure.
- **Routine patches:** weekly review, monthly merge.
- **Minor versions:** monthly evaluation.
- **Major versions:** evaluated case-by-case; ADR if non-trivial.

### Update procedure

1. Read the lib's CHANGELOG between current and target versions.
2. Run the test suite against the new version locally.
3. Run SAST + dep-audit + the project's `pre_pr_check.py`.
4. If new syntax is required → see section above.
5. Open the PR with the lib's CHANGELOG link in the description.

### Tooling

- **Renovate** or **Dependabot** to open PRs automatically.
- Configure to group patch updates and isolate majors.
- Auto-merge patch updates that pass CI; require review for minors and
  majors.

---

## Removing dependencies

A dep that's no longer used costs nothing to import but keeps:
- Risk of supply-chain incident
- A line in the lockfile that audit scanners must process
- A potential CVE you'll have to triage

**Hard rule:** when a feature using a unique dep is removed, the dep is
removed in the **same PR**. The `dependency-evaluator` subagent (or
`knip` / `vulture` / `cargo machete` / `unimport`) detects unused deps.

---

## License audit

- Track every dep's license in a generated `LICENSES.md` or via a
  license scanner (`pip-licenses`, `license-checker`, `cargo-deny`).
- CI fails on incompatible licenses (define allowlist in
  `project.config.toml`).
- Common allowlist for proprietary projects: MIT, BSD-2/3, Apache-2.0,
  ISC, MPL-2.0 (sometimes).
- Review case-by-case: GPL/AGPL/LGPL, custom EULAs.

---

## Transitive dependency control

- Pin direct deps to specific versions; let the resolver pick
  transitives.
- If a CVE is in a transitive dep:
  - Identify the direct dep that pulls it.
  - Update that direct dep to a version that pulls a patched
    transitive.
  - If the direct dep doesn't have such a version, override the
    transitive (`pip-tools` `--constraint`, npm `overrides`,
    `pnpm.overrides`, `cargo` `[patch]`).
  - Track the override with a `debt_<lib>.md` memory and a revisit
    trigger ("when direct dep ships fix").

---

## What `dependency-evaluator` does

The `dependency-evaluator` subagent (in `.claude/agents/`) runs all the
health checks above when the dev proposes adding/updating a dep, and
reports a recommendation. See
`.claude/agents/dependency-evaluator.md`.

---

## Rules of thumb

- **Default:** don't add the dep.
- **Stdlib first**, then well-known framework, then third-party.
- **Latest stable** — always.
- **One way** to do a thing — don't have two HTTP clients, two ORMs,
  two date libs in the same project.
- **Document trade-offs** in ADRs when the choice is non-obvious.
- **Memory new syntax** when adopting major versions.
