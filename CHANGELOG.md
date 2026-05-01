# Changelog

All notable changes to this project are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/).

---

## Unreleased

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
