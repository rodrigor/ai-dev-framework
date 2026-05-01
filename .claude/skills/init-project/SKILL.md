---
name: init-project
description: Initializes a project based on ai-dev-framework. Runs `.aidev/scripts/init_project.py` to do the mechanical work — stack detection, Q&A, latest-version lookup on PyPI/npm, generation of `.aidev/config/project.config.toml`, `.github/workflows/quality.yml`, and `.pre-commit-config.yaml`. Then reads the generated config and populates the prose docs (`.aidev/QUALITY.md`, `.aidev/INFRASTRUCTURE.md`) with project-specific decisions, trade-off rationale, and removed-irrelevant sections. Use when the user asks to initialize, configure, set up, or bootstrap a new project, or mentions "init project", "configure quality", "choose quality tools", "scaffold project".
---

# init-project

Bootstraps a project against the `ai-dev-framework`.

## Division of labor

- **Script (`.aidev/scripts/init_project.py`)** — mechanical work:
  detect stack, ask questions, look up latest versions, generate
  TOML/YAML config files. No prose.
- **You (this skill)** — judgment work: after the script runs, read
  `.aidev/config/project.config.toml` and edit the prose documents
  (`QUALITY.md`, `INFRASTRUCTURE.md`, optionally `COMPONENTS.md` /
  `GLOSSARY.md` stubs) so they reflect this specific project.

This split keeps the script small and the docs idiomatic.

## When to use

- Brand-new repository freshly cloned from the template.
- Existing project adopting the framework.
- Stack change requiring tool revision (run with `--reconfigure`).

## Procedure

### 1. Run the script

Default: interactive Q&A.

```bash
python .aidev/scripts/init_project.py
```

Useful flags:
- `--reconfigure` — force Q&A even if config exists.
- `--non-interactive` — use defaults (or existing config) without
  asking. Good for re-generating artifacts after editing the TOML.
- `--dry-run` — show what would change without writing.
- `--skip-versions` — skip live version lookup (offline).

The script writes:
- `.aidev/config/project.config.toml` — declarative state.
- `.github/workflows/quality.yml` — CI pipeline tailored to the
  detected stack.
- `.pre-commit-config.yaml` — local hooks.

### 2. Read the generated config

```bash
cat .aidev/config/project.config.toml
```

This is the source of truth for the project's choices.

### 3. Populate the prose docs

Edit (don't regenerate from scratch — keep the framework's catalog
content as reference):

#### `.aidev/QUALITY.md`
- At the top, add a "Project decisions" section summarizing the chosen
  tools per gate function (SAST, deps, coverage, complexity, etc.)
  with the **versions found by the script** (in
  `[quality.tool_versions]` of the TOML).
- Below that, keep the framework's reference table for context, but
  remove the `[STACK X]` sections that don't apply to this project.

#### `.aidev/INFRASTRUCTURE.md`
- At the top, add a "Project decisions" section enumerating each NFR
  with the chosen value and a 1-2 line rationale. Example:

  ```markdown
  ### Multi-tenancy: shared-DB
  Chosen because we expect ≤ 100 tenants in year 1; tenant_id column
  with strict middleware enforcement is sufficient. Revisit if we
  exceed 500 active tenants or need stronger isolation for an
  enterprise customer.
  ```

- Below the decisions section, the framework's full catalog stays as
  reference for future revisits.

#### `.aidev/COMPONENTS.md` (optional)
- If the project has standard components from day one (modal,
  date-formatter, logger), seed them.

#### `.aidev/GLOSSARY.md` (optional)
- Seed with at least the project's primary domain terms (e.g.,
  "Tenant", "User", "Subscription").

### 4. Add stack/infra-specific scaffolding (if requested)

When the user wants more than just config — e.g., they're starting
from a blank repo and want auth/admin scaffolding — generate:

- `Dockerfile` + `docker-compose.yml` if `container = "docker"`.
- Auth scaffolding (login routes, magic-link/OAuth handlers, password
  policy) per `infrastructure.auth.methods`.
- Tenant middleware if `multi_tenancy = "shared-db"`.
- Admin area shell per `admin_areas`.
- Healthcheck route.

Use the project's stack idioms (see `.aidev/CODE_STYLE.md`). Keep
modules small and typed.

### 5. Add the CHANGELOG entry

Add a "Project initialized via ai-dev-framework" entry under
**Unreleased** in `CHANGELOG.md`.

### 6. Final summary

Present:
- Detected stack(s)
- Selected tools (table with pinned versions)
- NFRs decided
- Created/modified files
- Next steps (run `pre-commit install`, configure CI secrets, fill
  `GLOSSARY.md` if seeded, mark repo as Template if applicable, etc.)

## Principles

- **Don't impose:** the script asks defaults; the dev decides. You,
  the skill, can suggest but don't override.
- **Latest version:** trust the versions resolved by the script; don't
  re-look-them-up from your training data.
- **Minimum viable:** start with conservative gates. Tighten over time.
- **Document the "why":** the prose docs you edit should explain
  trade-offs, not just restate the config values.
- **Idempotent:** rerunning `/init-project` should reconcile, not
  duplicate. The TOML is the state; you edit docs to match.
