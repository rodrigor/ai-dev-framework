# Quality controls — `QUALITY.md`

Single source of truth for automated controls. Filled by
`/init-project` based on the detected stack. Update whenever you add
or change a control.

> **Status:** `[SKELETON — fill in via init-project]`
> After init, remove the `[STACK X]` blocks that don't apply.

## Gate overview

A PR only passes if every gate below is green.

| Function | Tool | Blocks at | How to run locally |
|---|---|---|---|
| SAST | `[fill]` | severity ≥ HIGH | `[command]` |
| Deps/CVEs | `[fill]` | severity ≥ HIGH | `[command]` |
| Secrets | `gitleaks` | any match | `gitleaks detect` |
| Coverage | `[fill]` | < `[X]`% | `[command]` |
| Cyclomatic complexity | `[fill]` | rank ≥ E | `[command]` |
| Modularity / MI | `[fill]` | MI < 20 | `[command]` |
| Lint / format | `[fill]` | any error | `[command]` |
| Type checking (if applicable) | `[fill]` | any error | `[command]` |
| Dead code | `[fill]` | warning | `[command]` |

## CI pipeline

`.github/workflows/quality.yml` (or equivalent) runs all gates in
parallel and blocks merge if any fails.

## Reference table by stack

> Use init-project to fill in; keep only the project's stack here.

### [STACK Python]

| Function | Default | Alternatives |
|---|---|---|
| SAST | Semgrep + Bandit | CodeQL |
| Deps | pip-audit + Trivy fs | Safety, Snyk |
| Coverage | pytest-cov, gate `--cov-fail-under=X` | coverage.py |
| CC | `radon cc -s -a --min C` | xenon (gate) |
| MI | `radon mi -s` | wily |
| Lint | ruff | flake8, pylint |
| Format | black or ruff format | — |
| Types | mypy or pyright | — |
| Dead code | vulture | — |
| Secrets | gitleaks | trufflehog |

Standard commands:

```bash
# SAST
semgrep --config auto --error
bandit -r src/ -ll

# Deps
pip-audit
trivy fs --severity HIGH,CRITICAL .

# Coverage
pytest --cov=src --cov-fail-under=60

# Complexity (rank C or worse)
radon cc src -s -a --exclude "tests/*" --min C
radon mi src --exclude "tests/*" -s | grep -v "- A$"

# Churn (cross with complexity)
git log --since="3 months ago" --name-only --pretty=format: \
  -- "src/*.py" | grep "\.py$" | sort | uniq -c | sort -rn | head -20

# Lint/format
ruff check .
ruff format --check .

# Types
mypy src/

# Dead code
vulture src/

# Secrets
gitleaks detect --redact
```

### [STACK Node/TypeScript]

| Function | Default | Alternatives |
|---|---|---|
| SAST | Semgrep + ESLint security plugins | CodeQL, SonarJS |
| Deps | npm audit + Trivy + osv-scanner | Snyk |
| Coverage | vitest --coverage / jest --coverage | c8 |
| CC | eslint-plugin-complexity | complexity-report, plato |
| Modularity | madge (cycles) + dependency-cruiser | — |
| Lint+format | Biome (all-in-one) | ESLint + Prettier |
| Types | `tsc --noEmit` strict | — |
| Dead code | knip | ts-prune |
| Secrets | gitleaks | — |

```bash
# SAST
semgrep --config auto --error
npx eslint . --max-warnings 0

# Deps
npm audit --audit-level=high
trivy fs --severity HIGH,CRITICAL .

# Coverage
npx vitest run --coverage  # threshold in vitest.config

# Complexity — via ESLint rule "complexity": ["error", 10]
# or:
npx complexity-report -f json src/

# Modularity
npx madge --circular src/
npx depcruise src/

# Types
npx tsc --noEmit

# Dead code
npx knip

# Secrets
gitleaks detect --redact
```

### [STACK Go]

| Function | Default |
|---|---|
| SAST | gosec + Semgrep |
| Deps | govulncheck + Trivy |
| Coverage | `go test -cover` + go-test-coverage threshold |
| CC | gocyclo + gocognit |
| Modularity | go-mod-graph + goda |
| Lint | golangci-lint (aggregates ~40) |
| Secrets | gitleaks |

### [STACK Rust]

| Function | Default |
|---|---|
| SAST | clippy strict + Semgrep |
| Deps | cargo-audit + cargo-deny |
| Coverage | cargo-llvm-cov / tarpaulin |
| CC | rust-code-analysis |
| Lint | `clippy --all-targets -- -D warnings` |

### [STACK Java/Kotlin]

| Function | Default |
|---|---|
| SAST | SpotBugs+FindSecBugs + Semgrep |
| Deps | OWASP Dependency-Check + Trivy |
| Coverage | JaCoCo with threshold |
| CC/MI | PMD + Checkstyle |
| Modularity | JDepend or ArchUnit |
| Lint | ktlint/detekt (Kotlin), Checkstyle (Java) |

## Decision rule — complexity

After large features, run CC + MI and cross with churn.

| Metric | Threshold | Action |
|---|---|---|
| CC rank E or F | any churn | Decompose before next merge to the file |
| CC rank D | churn ≥ 15 commits / 3 months | Hotspot — refactor next sprint |
| MI rank B (< 20) | — | Priority refactor |
| MI rank C (< 10) | — | Block — decompose before any new feature |

## Test quality (beyond coverage)

Coverage measures lines executed, not whether tests would catch a
regression. Coverage is necessary but not sufficient.

### Layered defenses

1. **Branch coverage** in addition to line coverage. Untested `else`
   paths hide behind line-coverage numbers.
2. **Test smell linters** — forbid `sleep()` in tests, skipped tests
   without justification, empty assertions, hardcoded `now()`.
3. **Mutation testing** — mutates production code (flips operators,
   deletes lines) and verifies tests catch the mutation. Run weekly,
   not per-PR (slow).
4. **Bug-fix verification** — for `fix/*` branches, the new test must
   have failed against the previous commit (before the fix). Run by
   `test-quality-reviewer` subagent or `pre_pr_check.py`.
5. **Property-based testing** — at least one for each pure function
   in the domain core. Catches edge cases that example-based tests
   miss.
6. **Forbidden patterns** (linter-enforced):
   - `sleep()` in tests (use clock fakes / wait-for-condition)
   - Hardcoded dates without freezing (flaky)
   - Skipped tests without ticket reference
   - `assert True` / no-assertion tests
   - Mocking what you own (mock at boundaries)
   - Order-dependent tests

### Tools per stack

| Stack | Mutation | Smells | Property-based |
|---|---|---|---|
| Python | mutmut, cosmic-ray | flake8-pytest-style, pytest-deadfixtures | hypothesis |
| Node/TS | Stryker | eslint-plugin-jest, eslint-plugin-vitest | fast-check |
| Go | go-mutesting | golangci-lint (testifylint) | rapid, testing/quick |
| Rust | cargo-mutants | clippy | proptest, quickcheck |
| Java | PIT (pitest) | spotbugs-tests | jqwik |

### Mutation score gate

- Initial baseline: 60% (start lower if first run reveals gaps).
- Target: 80% within 6 months.
- Run weekly in CI on a dedicated job (not per-PR — too slow).
- Drops in mutation score block the next merge until investigated.

### What `test-quality-reviewer` checks

The `test-quality-reviewer` subagent runs the smell catalog above on
PR diffs (test files only). See `.claude/agents/test-quality-reviewer.md`.

---

## Database schema quality

Schema correctness, safety of migrations, and convention compliance.

### Migration safety

Every migration is reviewed for:

1. **Reversibility:** has `down`, OR explicitly marked one-way with
   reason.
2. **Backward-compatible deploys:** can run alongside old code without
   breaking it (no rename in single migration; no `DROP COLUMN`
   before deploy that stops using it).
3. **Locking on hot tables:** `NOT NULL` on existing column → 3-step
   pattern (add nullable, backfill, set NOT NULL). `ADD COLUMN
   DEFAULT <expr>` may rewrite the whole table on older Postgres.
4. **Index creation `CONCURRENTLY`** on Postgres for live tables.
5. **Tenant-scoped tables** (when `multi_tenancy = "shared-db"`) must
   include `tenant_id` + index + UNIQUE-with-tenant-scope.

### Migration linters per DB

| DB | Tool | Catches |
|---|---|---|
| Postgres | **squawk** | Long locks, unsafe ALTER, missing FK index |
| Postgres / generic | **atlas** | Schema diff, drift, lint rules |
| Rails-style | **strong_migrations** (Ruby) | Backward-incompat ops |
| Postgres + dev hooks | **pg_lint** | Naming, constraints |

Wired into CI on every PR that touches `migrations/`.

### Naming and structural conventions

Linter-enforced (or reviewed by `schema-reviewer`):

- Tables plural snake_case; columns snake_case.
- FK columns named `<referenced_table>_id` and indexed.
- Timestamps timezone-aware (`TIMESTAMPTZ`, `timestamp with time zone`).
- Audited tables have `created_at` and `updated_at`.
- Soft-deletable product entities have `deleted_at` (per framework
  policy in `CLAUDE.md`).
- Enum columns have `CHECK` constraint or FK to lookup table — never
  trust application code alone.

### Schema-as-code

- Generate `schema.sql` snapshot, commit on every migration.
- PR review shows the schema diff alongside the code diff.
- Catches accidental schema changes (ORM auto-create in dev).

### ERD generation

- Tool generates Mermaid/Graphviz diagram from current schema.
- Committed; PR shows visual diff.
- Reviewers catch unintended relationship changes faster.

### Drift detection

- Tools (atlas, liquibase) compare staging/prod actual schema vs
  committed `schema.sql`.
- Alerts when someone runs a manual `ALTER`.
- Run nightly in production environments.

### Multi-tenant safety regression

- Every tenant-scoped table has a regression test:
  - Insert as tenant A.
  - Query as tenant B.
  - Must return empty.
- Test fixture in `tests/regression/test_tenant_isolation.py` (or
  equivalent) loops over all tenant-scoped models.

### Performance gates

- `EXPLAIN ANALYZE` on common query patterns in CI fixture.
- Block on full-table-scan in hot paths.
- Slow-query log retained, reviewed weekly.

### What `schema-reviewer` checks

The `schema-reviewer` subagent runs the rule catalog above on PR diffs
that touch migrations or models. See `.claude/agents/schema-reviewer.md`.

---

## Test coverage

- **Initial baseline:** `[X]`% (fill in at init).
- **Policy:** rises 1pp per release, never drops. CI gate blocks
  regression.
- **Exclude:** seeds, fixtures, demos, one-shot migration scripts.

## Local hooks (pre-commit)

`.pre-commit-config.yaml` runs lint, format, and gitleaks before commit.
Doesn't replace CI but catches 80% of issues on the laptop.

## When to update this document

- Added/removed a CI workflow
- Changed a scanner version pin
- Changed policy (min coverage, blocking severity)
- New control introduced

Updates to `QUALITY.md` happen in the **same delivery** that touches
the control.
