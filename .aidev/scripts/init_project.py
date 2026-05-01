#!/usr/bin/env python3
"""
init_project — bootstraps an ai-dev-framework project.

Mechanical work only:
- Detect stack(s) from manifests at the repo root.
- Q&A (interactive) or read non-interactive config.
- Look up latest stable versions on PyPI / npm.
- Write `.aidev/config/project.config.toml`.
- Generate `.github/workflows/quality.yml` per stack.
- Generate `.pre-commit-config.yaml`.
- Print next steps.

Prose work (writing populated QUALITY.md / INFRASTRUCTURE.md docs) is
handled by the Claude `init-project` skill, which reads the generated
config and edits the docs.

Usage:
    python .aidev/scripts/init_project.py                   # interactive
    python .aidev/scripts/init_project.py --reconfigure     # re-run Q&A
    python .aidev/scripts/init_project.py --non-interactive # use defaults
    python .aidev/scripts/init_project.py --dry-run         # show, don't write
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

def _load_tomllib():
    """Lazy import of tomllib — only needed when reading existing config."""
    try:
        import tomllib
        return tomllib
    except ModuleNotFoundError:
        try:
            import tomli  # type: ignore
            return tomli
        except ModuleNotFoundError:
            return None


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = REPO_ROOT / ".aidev" / "config" / "project.config.toml"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "quality.yml"
PRECOMMIT_PATH = REPO_ROOT / ".pre-commit-config.yaml"


# ---------------------------------------------------------------------------
# Stack detection
# ---------------------------------------------------------------------------


STACK_MANIFESTS: dict[str, list[str]] = {
    "python": ["pyproject.toml", "requirements.txt", "setup.py", "Pipfile"],
    "node": ["package.json"],
    "go": ["go.mod"],
    "rust": ["Cargo.toml"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
    "ruby": ["Gemfile"],
    "php": ["composer.json"],
}


def detect_stacks(root: Path) -> list[str]:
    found: list[str] = []
    for stack, files in STACK_MANIFESTS.items():
        if any((root / f).exists() for f in files):
            found.append(stack)
    # TypeScript signal sits on top of Node detection.
    if "node" in found and (root / "tsconfig.json").exists():
        found = [s if s != "node" else "typescript" for s in found]
    return found


# ---------------------------------------------------------------------------
# Latest-version lookup (PyPI + npm)
# ---------------------------------------------------------------------------


def _http_json(url: str, timeout: float = 6.0) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def latest_pypi(package: str) -> str | None:
    data = _http_json(f"https://pypi.org/pypi/{package}/json")
    return data.get("info", {}).get("version") if data else None


def latest_npm(package: str) -> str | None:
    data = _http_json(f"https://registry.npmjs.org/{package}/latest")
    return data.get("version") if data else None


# ---------------------------------------------------------------------------
# Question helpers
# ---------------------------------------------------------------------------


@dataclass
class Answer:
    """One question's resolved value."""

    key: str
    value: object


@dataclass
class Config:
    """Flat collected answers; serialized to project.config.toml."""

    project_name: str = "my-project"
    project_description: str = ""
    stack_backend: str = "python"
    stack_frontend: str = "none"
    typescript: bool = False
    backend_framework: str = "fastapi"
    container: str = "docker"
    database: str = "postgres"
    multi_tenancy: str = "none"
    auth_methods: list[str] = field(default_factory=lambda: ["password", "magic-link"])
    authorization: str = "simple-rbac"
    admin_areas: list[str] = field(default_factory=list)
    logging: str = "json"
    correlation_id: bool = True
    metrics: str = "none"
    feature_flags: str = "internal-registry"
    email: str = "smtp"
    file_storage: str = "filesystem"
    background_jobs: str = "none"
    cache: str = "none"
    ai_provider: str = "none"
    pii_handling: bool = True
    audit_trail: bool = True
    coverage_min: int = 60
    mutation_testing: str = "weekly"
    deps_block_severity: list[str] = field(
        default_factory=lambda: ["HIGH", "CRITICAL"]
    )
    cc_block_rank: str = "E"
    mi_block_min: int = 10
    versions: dict[str, str] = field(default_factory=dict)


def _ask(prompt: str, default: str, choices: list[str] | None = None) -> str:
    """Ask a single-string question; reprompt on invalid choice."""
    suffix = f" [{default}]"
    if choices:
        suffix = f" ({'/'.join(choices)}) [{default}]"
    while True:
        raw = input(f"{prompt}{suffix}: ").strip()
        value = raw or default
        if choices and value not in choices:
            print(f"  → must be one of {choices}")
            continue
        return value


def _ask_bool(prompt: str, default: bool) -> bool:
    d = "y" if default else "n"
    raw = input(f"{prompt} (y/n) [{d}]: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes", "true", "1")


def _ask_multi(prompt: str, default: list[str], choices: list[str]) -> list[str]:
    print(f"{prompt}")
    print(f"  Options: {', '.join(choices)}")
    print(f"  Default: {', '.join(default)}")
    raw = input("  (comma-separated, blank for default): ").strip()
    if not raw:
        return default
    items = [x.strip() for x in raw.split(",") if x.strip()]
    invalid = [x for x in items if x not in choices]
    if invalid:
        print(f"  → ignoring invalid: {invalid}")
        items = [x for x in items if x in choices]
    return items or default


def _ask_int(prompt: str, default: int) -> int:
    raw = input(f"{prompt} [{default}]: ").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"  → not an int, using {default}")
        return default


# ---------------------------------------------------------------------------
# Q&A flow
# ---------------------------------------------------------------------------


def _suggest_stack(detected: list[str]) -> str:
    if not detected:
        return "python"
    # Prefer typed/dynamic options that match framework defaults.
    for pref in ("python", "typescript", "go", "node", "rust", "java"):
        if pref in detected:
            return pref
    return detected[0]


def run_questions(detected: list[str], existing: Config | None) -> Config:
    cfg = existing or Config()

    print("=" * 72)
    print("  ai-dev-framework — project initialization")
    print("=" * 72)

    if detected:
        print(f"\nDetected stack(s): {', '.join(detected)}")
    else:
        print("\nNo stack manifest found at repo root.")

    cfg.project_name = _ask("Project name", cfg.project_name or REPO_ROOT.name)
    cfg.project_description = _ask("One-line description", cfg.project_description)

    print("\n--- Stack ---")
    cfg.stack_backend = _ask(
        "Backend language",
        _suggest_stack(detected) if not existing else cfg.stack_backend,
        choices=["python", "typescript", "node", "go", "rust", "java", "kotlin", "ruby", "php"],
    )
    cfg.typescript = cfg.stack_backend == "typescript" or _ask_bool(
        "TypeScript on frontend?",
        cfg.stack_backend == "typescript" or cfg.typescript,
    )
    cfg.stack_frontend = _ask(
        "Frontend",
        cfg.stack_frontend,
        choices=["none", "react-vite", "nextjs", "sveltekit", "vue"],
    )
    if cfg.stack_backend == "python":
        cfg.backend_framework = _ask(
            "Backend framework",
            cfg.backend_framework,
            choices=["fastapi", "litestar", "starlette", "django", "flask"],
        )
    elif cfg.stack_backend in ("typescript", "node"):
        cfg.backend_framework = _ask(
            "Backend framework", "hono", choices=["hono", "express", "fastify", "nest"]
        )
    elif cfg.stack_backend == "go":
        cfg.backend_framework = _ask(
            "Backend framework", "chi", choices=["chi", "echo", "net/http", "gin"]
        )

    print("\n--- Infrastructure ---")
    cfg.container = _ask("Containerization", cfg.container, choices=["docker", "podman", "none"])
    cfg.database = _ask(
        "Database", cfg.database, choices=["postgres", "sqlite", "mysql", "mongodb", "none"]
    )
    cfg.multi_tenancy = _ask(
        "Multi-tenancy",
        cfg.multi_tenancy,
        choices=["none", "shared-db", "db-per-tenant", "schema-per-tenant"],
    )

    print("\n--- Auth ---")
    cfg.auth_methods = _ask_multi(
        "Auth methods",
        cfg.auth_methods,
        ["password", "magic-link", "oauth-google", "oauth-microsoft", "oauth-github", "oauth-apple", "saml-sso", "webauthn-passkeys"],
    )
    cfg.authorization = _ask(
        "Authorization",
        cfg.authorization,
        choices=["none", "simple-rbac", "scoped-rbac", "abac", "groups"],
    )
    cfg.admin_areas = _ask_multi(
        "Admin areas",
        cfg.admin_areas or (["sysadmin", "tenant-admin"] if cfg.multi_tenancy != "none" else ["sysadmin"]),
        ["sysadmin", "tenant-admin"],
    )

    print("\n--- Operations ---")
    cfg.logging = _ask("Logging format", cfg.logging, choices=["text", "json"])
    cfg.correlation_id = _ask_bool("Correlation ID per request?", cfg.correlation_id)
    cfg.metrics = _ask("Metrics", cfg.metrics, choices=["none", "prometheus", "otel"])

    print("\n--- Product features ---")
    cfg.feature_flags = _ask(
        "Feature flags", cfg.feature_flags,
        choices=["none", "internal-registry", "unleash", "growthbook", "launchdarkly"],
    )
    cfg.email = _ask("Email", cfg.email, choices=["none", "smtp", "aws-ses", "resend", "postmark"])
    cfg.file_storage = _ask(
        "File storage", cfg.file_storage, choices=["filesystem", "s3", "local-with-s3-fallback"]
    )
    cfg.background_jobs = _ask(
        "Background jobs", cfg.background_jobs,
        choices=["none", "framework-native", "celery", "rq", "bullmq", "temporal"],
    )
    cfg.cache = _ask("Cache", cfg.cache, choices=["none", "in-memory", "redis", "memcached"])

    print("\n--- AI & compliance ---")
    cfg.ai_provider = _ask(
        "AI integration", cfg.ai_provider,
        choices=["none", "litellm", "openai-direct", "anthropic-direct"],
    )
    cfg.pii_handling = _ask_bool("Project handles PII?", cfg.pii_handling)
    cfg.audit_trail = _ask_bool("Audit trail for sensitive events?", cfg.audit_trail)

    print("\n--- Quality gates ---")
    cfg.coverage_min = _ask_int("Min coverage %", cfg.coverage_min)
    cfg.mutation_testing = _ask(
        "Mutation testing cadence", cfg.mutation_testing, choices=["off", "per-pr", "weekly"]
    )

    return cfg


# ---------------------------------------------------------------------------
# Latest-version resolution
# ---------------------------------------------------------------------------


PYPI_TOOLS = ["ruff", "mypy", "pytest", "pytest-cov", "hypothesis", "radon",
              "bandit", "vulture", "pip-audit", "mutmut"]
NPM_TOOLS = ["typescript", "vitest", "eslint", "@biomejs/biome", "knip",
             "stryker-mutator/core"]


def resolve_versions(cfg: Config) -> dict[str, str]:
    versions: dict[str, str] = {}
    if cfg.stack_backend == "python":
        for pkg in PYPI_TOOLS:
            v = latest_pypi(pkg)
            if v:
                versions[pkg] = v
    if cfg.stack_backend in ("typescript", "node") or cfg.typescript:
        for pkg in NPM_TOOLS:
            v = latest_npm(pkg)
            if v:
                versions[pkg] = v
    return versions


# ---------------------------------------------------------------------------
# TOML serialization (no external dep)
# ---------------------------------------------------------------------------


def _toml_value(v: object) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        # Escape backslashes and double quotes; wrap in double quotes.
        s = v.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{s}"'
    if isinstance(v, list):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f'{k} = {_toml_value(x)}' for k, x in v.items()) + "}"
    raise TypeError(f"Unsupported TOML type: {type(v)}")


def render_config_toml(cfg: Config) -> str:
    lines: list[str] = []
    lines.append("# project.config.toml — generated by .aidev/scripts/init_project.py")
    lines.append("# Edit and re-run init to regenerate artifacts coherently.")
    lines.append("")
    lines.append("[project]")
    lines.append(f'name = {_toml_value(cfg.project_name)}')
    lines.append(f'description = {_toml_value(cfg.project_description)}')
    lines.append("")
    lines.append("[stack]")
    lines.append(f'backend = {_toml_value(cfg.stack_backend)}')
    lines.append(f'backend_framework = {_toml_value(cfg.backend_framework)}')
    lines.append(f'frontend = {_toml_value(cfg.stack_frontend)}')
    lines.append(f'typescript = {_toml_value(cfg.typescript)}')
    lines.append("")
    lines.append("[infrastructure]")
    lines.append(f'container = {_toml_value(cfg.container)}')
    lines.append(f'database = {_toml_value(cfg.database)}')
    lines.append(f'multi_tenancy = {_toml_value(cfg.multi_tenancy)}')
    lines.append(f'admin_areas = {_toml_value(cfg.admin_areas)}')
    lines.append("")
    lines.append("[infrastructure.auth]")
    lines.append(f'methods = {_toml_value(cfg.auth_methods)}')
    lines.append(f'authorization = {_toml_value(cfg.authorization)}')
    lines.append("")
    lines.append("[infrastructure.observability]")
    lines.append(f'logging = {_toml_value(cfg.logging)}')
    lines.append(f'correlation_id = {_toml_value(cfg.correlation_id)}')
    lines.append(f'metrics = {_toml_value(cfg.metrics)}')
    lines.append("")
    lines.append("[infrastructure.product]")
    lines.append(f'feature_flags = {_toml_value(cfg.feature_flags)}')
    lines.append(f'email = {_toml_value(cfg.email)}')
    lines.append(f'file_storage = {_toml_value(cfg.file_storage)}')
    lines.append(f'background_jobs = {_toml_value(cfg.background_jobs)}')
    lines.append(f'cache = {_toml_value(cfg.cache)}')
    lines.append("")
    lines.append("[infrastructure.ai]")
    lines.append(f'provider = {_toml_value(cfg.ai_provider)}')
    lines.append("")
    lines.append("[infrastructure.compliance]")
    lines.append(f'pii_handling = {_toml_value(cfg.pii_handling)}')
    lines.append(f'audit_trail = {_toml_value(cfg.audit_trail)}')
    lines.append("")
    lines.append("[quality]")
    lines.append(f'coverage_min = {_toml_value(cfg.coverage_min)}')
    lines.append(f'mutation_testing = {_toml_value(cfg.mutation_testing)}')
    lines.append(f'deps_block_severity = {_toml_value(cfg.deps_block_severity)}')
    lines.append(f'cc_block_rank = {_toml_value(cfg.cc_block_rank)}')
    lines.append(f'mi_block_min = {_toml_value(cfg.mi_block_min)}')
    if cfg.versions:
        lines.append("")
        lines.append("[quality.tool_versions]")
        for pkg, v in sorted(cfg.versions.items()):
            # Replace slashes (npm scoped names) and `-` to be valid TOML keys.
            key = re.sub(r"[^a-zA-Z0-9_]", "_", pkg)
            lines.append(f'{key} = {_toml_value(v)}  # {pkg}')
    lines.append("")
    return "\n".join(lines)


def load_existing_config() -> Config | None:
    if not CONFIG_PATH.exists():
        return None
    tomllib = _load_tomllib()
    if tomllib is None:
        print("note: existing project.config.toml found but tomllib/tomli unavailable;",
              "starting fresh.", file=sys.stderr)
        return None
    try:
        data = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError):
        return None
    cfg = Config()
    cfg.project_name = data.get("project", {}).get("name", cfg.project_name)
    cfg.project_description = data.get("project", {}).get("description", "")
    s = data.get("stack", {})
    cfg.stack_backend = s.get("backend", cfg.stack_backend)
    cfg.backend_framework = s.get("backend_framework", cfg.backend_framework)
    cfg.stack_frontend = s.get("frontend", cfg.stack_frontend)
    cfg.typescript = s.get("typescript", cfg.typescript)
    i = data.get("infrastructure", {})
    cfg.container = i.get("container", cfg.container)
    cfg.database = i.get("database", cfg.database)
    cfg.multi_tenancy = i.get("multi_tenancy", cfg.multi_tenancy)
    cfg.admin_areas = i.get("admin_areas", cfg.admin_areas)
    auth = i.get("auth", {})
    cfg.auth_methods = auth.get("methods", cfg.auth_methods)
    cfg.authorization = auth.get("authorization", cfg.authorization)
    obs = i.get("observability", {})
    cfg.logging = obs.get("logging", cfg.logging)
    cfg.correlation_id = obs.get("correlation_id", cfg.correlation_id)
    cfg.metrics = obs.get("metrics", cfg.metrics)
    prod = i.get("product", {})
    cfg.feature_flags = prod.get("feature_flags", cfg.feature_flags)
    cfg.email = prod.get("email", cfg.email)
    cfg.file_storage = prod.get("file_storage", cfg.file_storage)
    cfg.background_jobs = prod.get("background_jobs", cfg.background_jobs)
    cfg.cache = prod.get("cache", cfg.cache)
    cfg.ai_provider = i.get("ai", {}).get("provider", cfg.ai_provider)
    comp = i.get("compliance", {})
    cfg.pii_handling = comp.get("pii_handling", cfg.pii_handling)
    cfg.audit_trail = comp.get("audit_trail", cfg.audit_trail)
    q = data.get("quality", {})
    cfg.coverage_min = q.get("coverage_min", cfg.coverage_min)
    cfg.mutation_testing = q.get("mutation_testing", cfg.mutation_testing)
    return cfg


# ---------------------------------------------------------------------------
# Workflow generation
# ---------------------------------------------------------------------------


def render_quality_workflow(cfg: Config) -> str:
    if cfg.stack_backend == "python":
        return _python_workflow(cfg)
    if cfg.stack_backend in ("typescript", "node"):
        return _node_workflow(cfg)
    if cfg.stack_backend == "go":
        return _go_workflow(cfg)
    return _generic_workflow(cfg)


def _python_workflow(cfg: Config) -> str:
    return textwrap.dedent(f"""\
        # Generated by .aidev/scripts/init_project.py
        # Re-run init to regenerate from .aidev/config/project.config.toml
        name: quality
        on:
          pull_request:
          push:
            branches: [main]

        jobs:
          lint-format:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.12"
              - run: pip install ruff mypy
              - run: ruff check .
              - run: ruff format --check .
              - run: mypy src || true  # set strict in pyproject.toml first

          tests:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.12"
              - run: pip install -e ".[dev]" || pip install -r requirements.txt
              - run: pytest --cov --cov-fail-under={cfg.coverage_min} --cov-branch

          security:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.12"
              - run: pip install pip-audit bandit
              - run: pip-audit
              - run: bandit -r src/ -ll
              - uses: aquasecurity/trivy-action@master
                with:
                  scan-type: fs
                  severity: HIGH,CRITICAL
                  exit-code: "1"
              - uses: gitleaks/gitleaks-action@v2

          complexity:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.12"
              - run: pip install radon
              - run: radon cc src -s -a --min C
              - run: radon mi src -s

          pre-pr-check:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
                with:
                  fetch-depth: 0
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.12"
              - run: python .aidev/scripts/pre_pr_check.py --base origin/main
        """)


def _node_workflow(cfg: Config) -> str:
    return textwrap.dedent(f"""\
        # Generated by .aidev/scripts/init_project.py
        name: quality
        on:
          pull_request:
          push:
            branches: [main]

        jobs:
          lint-types:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-node@v4
                with:
                  node-version: "20"
              - run: npm ci
              - run: npx biome check . || npx eslint . --max-warnings 0
              - run: npx tsc --noEmit

          tests:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-node@v4
                with:
                  node-version: "20"
              - run: npm ci
              - run: npx vitest run --coverage

          security:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-node@v4
                with:
                  node-version: "20"
              - run: npm audit --audit-level=high
              - uses: aquasecurity/trivy-action@master
                with:
                  scan-type: fs
                  severity: HIGH,CRITICAL
                  exit-code: "1"
              - uses: gitleaks/gitleaks-action@v2

          pre-pr-check:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
                with:
                  fetch-depth: 0
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.12"
              - run: python .aidev/scripts/pre_pr_check.py --base origin/main
        """)


def _go_workflow(cfg: Config) -> str:
    return textwrap.dedent(f"""\
        name: quality
        on:
          pull_request:
          push:
            branches: [main]

        jobs:
          lint:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-go@v5
                with:
                  go-version: stable
              - uses: golangci/golangci-lint-action@v6

          tests:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-go@v5
                with:
                  go-version: stable
              - run: go test -race -cover ./...

          security:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-go@v5
                with:
                  go-version: stable
              - run: go install golang.org/x/vuln/cmd/govulncheck@latest
              - run: govulncheck ./...
              - uses: gitleaks/gitleaks-action@v2
        """)


def _generic_workflow(cfg: Config) -> str:
    return textwrap.dedent(f"""\
        name: quality
        on: [pull_request, push]
        jobs:
          security:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: aquasecurity/trivy-action@master
                with:
                  scan-type: fs
                  severity: HIGH,CRITICAL
                  exit-code: "1"
              - uses: gitleaks/gitleaks-action@v2
        """)


# ---------------------------------------------------------------------------
# Pre-commit config generation
# ---------------------------------------------------------------------------


def render_precommit(cfg: Config) -> str:
    blocks: list[str] = [
        "# Generated by .aidev/scripts/init_project.py",
        "repos:",
        "  - repo: https://github.com/gitleaks/gitleaks",
        "    rev: v8.21.2",
        "    hooks:",
        "      - id: gitleaks",
    ]
    if cfg.stack_backend == "python":
        blocks += [
            "  - repo: https://github.com/astral-sh/ruff-pre-commit",
            "    rev: v0.7.0",
            "    hooks:",
            "      - id: ruff",
            "      - id: ruff-format",
        ]
    if cfg.stack_backend in ("typescript", "node") or cfg.typescript:
        blocks += [
            "  - repo: https://github.com/biomejs/pre-commit",
            "    rev: v0.5.0",
            "    hooks:",
            "      - id: biome-check",
        ]
    return "\n".join(blocks) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def write_file(path: Path, content: str, dry_run: bool) -> None:
    rel = path.relative_to(REPO_ROOT)
    if dry_run:
        print(f"[dry-run] would write {rel} ({len(content)} bytes)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  ✓ wrote {rel}")


def print_next_steps(cfg: Config) -> None:
    print()
    print("=" * 72)
    print("  Init complete — next steps")
    print("=" * 72)
    print()
    print("1. Review .aidev/config/project.config.toml.")
    print("2. Have Claude run the `/init-project` skill so it can populate")
    print("   .aidev/QUALITY.md and .aidev/INFRASTRUCTURE.md with prose")
    print("   based on your decisions.")
    print("3. Install hooks:")
    print("     pip install pre-commit && pre-commit install   (if Python)")
    print("4. Verify CI: push a branch and watch .github/workflows/quality.yml")
    print("5. Add a CHANGELOG entry under 'Unreleased' for this init.")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="ai-dev-framework init")
    parser.add_argument(
        "--reconfigure",
        action="store_true",
        help="Force the Q&A flow even if config exists.",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Use defaults (or existing config) without asking.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without writing files.",
    )
    parser.add_argument(
        "--skip-versions",
        action="store_true",
        help="Skip live version lookup (offline mode).",
    )
    args = parser.parse_args()

    detected = detect_stacks(REPO_ROOT)
    existing = load_existing_config()

    if existing and not args.reconfigure and not args.non_interactive:
        print(f"Found existing {CONFIG_PATH.relative_to(REPO_ROOT)}.")
        print("Use --reconfigure to re-run Q&A, or --non-interactive to regenerate")
        print("artifacts from the existing config without prompting.")
        return 0

    if args.non_interactive:
        cfg = existing or Config()
        if not detected and not existing:
            print("Warning: no stack detected and no existing config — using defaults.",
                  file=sys.stderr)
    else:
        try:
            cfg = run_questions(detected, existing)
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.", file=sys.stderr)
            return 130

    if not args.skip_versions:
        print("\nLooking up latest stable versions of common tools...")
        cfg.versions = resolve_versions(cfg)
        print(f"  found {len(cfg.versions)} package versions")

    print("\nGenerating artifacts...")
    write_file(CONFIG_PATH, render_config_toml(cfg), args.dry_run)
    write_file(WORKFLOW_PATH, render_quality_workflow(cfg), args.dry_run)
    write_file(PRECOMMIT_PATH, render_precommit(cfg), args.dry_run)

    print_next_steps(cfg)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"Internal error: {exc}", file=sys.stderr)
        sys.exit(2)
