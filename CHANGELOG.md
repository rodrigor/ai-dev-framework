# Changelog

All notable changes to this project are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/).

---

## Unreleased

### changed
- **Repository layout reorganized.** Framework documents and tooling
  moved into `.aidev/` to keep the project root clean. Only
  `CLAUDE.md`, `README.md`, `CHANGELOG.md`, `.gitignore`, and
  `.claude/` remain at the root. Internal cross-references updated.
- `CLAUDE.md` slimmed down: it now contains the hard-rule summary
  with pointers into `.aidev/` for full rationale.
- `.aidev/scripts/pre_pr_check.py` looks for config at
  `.aidev/config/pre_pr_check.toml` (with backward-compat fallback
  to the legacy root location).

### added
- `INFRASTRUCTURE.md` "Stack rationale" section with a language
  ranking (token cost × AI maintainability) and per-use-case
  defaults: backend SaaS → Python (FastAPI) or TypeScript (Hono);
  service/CLI → Go; frontend → TypeScript + Vite + React.
- `init-project` skill recommends strict typing
  (mypy/pyright/`strict`) by default and documents the rationale
  inline.

### added
- `DEPENDENCIES.md`: full policy for adding/updating external deps —
  health checks (last release, maintainers, CVEs, license),
  latest-stable-version verification, pinning strategy by code type
  (app vs library vs dev), routine update cadence, transitive control,
  removal policy.
- `CODE_STYLE.md`: code-style guide focused on AI-maintainability —
  locality, explicit-over-implicit, type-everything, small pure
  functions, one-canonical-way, no premature abstraction. The
  "two costs" framing (token cost + bug-injection probability) drives
  every rule.
- `dependency-evaluator` subagent: evaluates a candidate library
  before it lands in the manifest. Verifies latest stable, no CVEs,
  license, maintenance signals; for major bumps fetches migration
  guide and produces old → new syntax mapping.
- `feedback_dep_template.md` memory pattern: captures new idiom on
  major-version adoption (e.g., Pydantic v2, React 19) so future
  sessions don't regress to deprecated syntax.
- CLAUDE.md sections referencing both new docs at the top of the
  rule list.

### changed

### added
- Initial scaffolding of `ai-dev-framework`: perennial documents
  (CLAUDE.md, SECURITY.md, PROCESS.md, QUALITY.md skeleton,
  COMPONENTS.md, GLOSSARY.md, INFRASTRUCTURE.md), memory templates
  (`feedback`, `project`, `debt`), ADR template, `init-project` skill,
  parametrizable `pre_pr_check.py`, declarative
  `project.config.toml.example`.
- Reusable subagents: `release-notes-writer`, `component-cataloger`,
  `test-quality-reviewer`, `schema-reviewer`.
- Test-quality and database-schema-quality sections in `QUALITY.md`
  covering mutation testing, smell linters, migration safety,
  schema-as-code, drift detection, ERD generation, and tenant-isolation
  regression tests.
- New pre-PR checks: `check_test_quality` (forbidden patterns in test
  files) and `check_migration_safety` (heuristic review of migrations,
  pointing at squawk/schema-reviewer for deep checks).

### changed
- All framework documentation translated to English for token
  efficiency and coherence with the i18n rule.

---

## [0.1.0] — YYYY-MM-DD

_First published version — TBD._
