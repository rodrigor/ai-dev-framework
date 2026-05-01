# ai-dev-framework

A scaffolding for AI-guided development: reusable documents, controls,
and automations that work in any project, agnostic to the technology stack.

The **persistent layer** (principles, processes, security policies) ships
identically into every project. The **tooling layer** (SAST, dependency
analysis, coverage, complexity, modularity) is decided at `init` time
based on the detected stack.

## What's here

- `CLAUDE.md` — instructions loaded into every AI session
- `QUALITY.md` — skeleton for automated controls (filled by init-project)
- `SECURITY.md` — perennial security policies
- `PROCESS.md` — workflows (bug fix, feature, release notes, pre-PR)
- `INFRASTRUCTURE.md` — catalog of infra capabilities the framework configures
- `COMPONENTS.md` — reusable component catalog (empty initially)
- `GLOSSARY.md` — domain terminology (filled by the project)
- `project.config.toml.example` — declarative project configuration
- `docs/adr/` — Architecture Decision Records
- `memory-templates/` — formats for AI persistent memories
- `.claude/` — hooks, subagents, slash commands, skills (incl. `init-project`)
- `scripts/pre_pr_check.py` — parametrizable pre-PR checklist

## Usage

### As a template

1. Use this repo as a **GitHub Template** or clone and remove `.git`.
2. Open the project in Claude Code.
3. Run `/init-project` — the skill detects the stack, asks about
   infrastructure choices (auth, multi-tenancy, logging, feature flags,
   AI integration, admin areas, etc.), proposes the tooling table
   (SAST, deps, coverage, complexity, modularity, secrets), and
   confirms gates with you.
4. The init generates a populated `QUALITY.md`, `INFRASTRUCTURE.md`,
   `.github/workflows/quality.yml`, `.pre-commit-config.yaml`, and
   tool configs.

### Why English

All framework content is in English on purpose:

- **Token efficiency:** English consumes ~20–30% fewer tokens than other
  languages on common LLM tokenizers. Persistent context multiplied across
  every session adds up.
- **Coherence with i18n:** keys, enums, identifiers, and code-facing
  variables are expected to be in English from day one in every project.
  Framework docs in another language would contradict that rule.

User-facing content of the project you build can be in any language —
that's a separate layer (i18n).

### Philosophy

- **Documentation becomes code when possible.** Rules that depend on the
  agent "remembering" are fragile; hooks executed by the harness are
  deterministic.
- **Persistent layer doesn't change per stack.** UX principles, secret
  handling policy, bug-fix workflow, soft-delete patterns apply across
  any language.
- **Tooling is pluggable.** Trivy, Semgrep, gitleaks, SonarQube, etc.
  are choices; the function (scan deps, find secrets) is perennial.

See `PROCESS.md` for the full development cycle.
