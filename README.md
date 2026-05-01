# ai-dev-framework

A scaffolding for AI-guided development: reusable documents, controls,
and automations that work in any project, agnostic to the technology stack.

The **persistent layer** (principles, processes, security policies) ships
identically into every project. The **tooling layer** (SAST, dependency
analysis, coverage, complexity, modularity) is decided at `init` time
based on the detected stack.

## Repository layout

Framework files live under `.aidev/` to keep the project root clean.
Only files that **must** be at the root by convention stay there.

```
/
├── CLAUDE.md                      # AI session instructions (short, with refs)
├── README.md                      # this file (replaced by project README on adoption)
├── CHANGELOG.md                   # release notes
├── .gitignore
├── .claude/                       # Claude Code config
│   ├── settings.json
│   ├── agents/                    # reusable subagents
│   └── skills/                    # skills (incl. init-project)
└── .aidev/                        # framework documents and tooling
    ├── CODE_STYLE.md              # how code should be written (AI-friendly)
    ├── DEPENDENCIES.md            # when and how to add/update libraries
    ├── PROCESS.md                 # workflows
    ├── QUALITY.md                 # automated controls (SAST/deps/coverage/...)
    ├── SECURITY.md                # security policies
    ├── INFRASTRUCTURE.md          # infra decisions taken at init
    ├── COMPONENTS.md              # catalog of reusable components
    ├── GLOSSARY.md                # domain terminology
    ├── adr/                       # Architecture Decision Records
    ├── memory-templates/          # AI memory formats
    ├── scripts/
    │   └── pre_pr_check.py        # parametrizable pre-PR checklist
    └── config/
        ├── project.config.toml.example
        └── pre_pr_check.toml.example
```

`CLAUDE.md` lives at the root because Claude Code reads it from there;
it imports the heavier docs from `.aidev/` lazily by reference.
`CHANGELOG.md` stays at the root by convention so external tools
(release tooling, GitHub Releases, package registries) can find it.

## Usage

### As a template

1. Use this repo as a **GitHub Template** or clone and remove `.git`.
2. Open the project in Claude Code.
3. Run `/init-project` — the skill detects the stack, asks about
   infrastructure choices (auth, multi-tenancy, logging, feature flags,
   AI integration, admin areas, etc.), proposes the tooling table
   (SAST, deps, coverage, complexity, modularity, secrets), and
   confirms gates with you.
4. The init generates a populated `.aidev/QUALITY.md`,
   `.aidev/INFRASTRUCTURE.md`, `.github/workflows/quality.yml`,
   `.pre-commit-config.yaml`, tool configs, and
   `.aidev/config/project.config.toml`.

### Why English

All framework content is in English on purpose:

- **Token efficiency:** English consumes ~20–30% fewer tokens than
  other languages on common LLM tokenizers. Persistent context
  multiplied across every session adds up.
- **Coherence with i18n:** keys, enums, identifiers, and code-facing
  variables are expected to be in English from day one in every
  project. Framework docs in another language would contradict that
  rule.

User-facing content of the project you build can be in any language —
that's a separate layer (i18n).

### Why `.aidev/`

A hidden directory signals "tooling/meta," not "documentation for
humans," similar to `.github/`, `.claude/`, `.vscode/`. It keeps the
project root visually clean — the dev sees `src/`, `tests/`, and
their own `README.md` at a glance, without 10 framework docs
competing for attention.

The AI agent finds `.aidev/` documents through `CLAUDE.md` references;
nothing is hidden from it.

### Philosophy

- **Documentation becomes code when possible.** Rules that depend on
  the agent "remembering" are fragile; hooks executed by the harness
  are deterministic.
- **Persistent layer doesn't change per stack.** UX principles, secret
  handling policy, bug-fix workflow, soft-delete patterns apply across
  any language.
- **Tooling is pluggable.** Trivy, Semgrep, gitleaks, SonarQube, etc.
  are choices; the function (scan deps, find secrets) is perennial.

See `.aidev/PROCESS.md` for the full development cycle.
