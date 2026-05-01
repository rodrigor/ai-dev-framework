#!/usr/bin/env python3
"""
Pre-PR checklist — deterministic validations that must pass before
opening a Pull Request.

Parametrized by `pre_pr_check.toml` at the project root. Without the
file, only universal checks run.

Usage:
    python scripts/pre_pr_check.py              # current branch vs main
    python scripts/pre_pr_check.py --base develop
    python scripts/pre_pr_check.py --staged     # only staged changes
    python scripts/pre_pr_check.py --strict     # warnings become blocks

Exit codes:
    0  — all OK
    1  — at least one BLOCK
    2  — internal script error
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib  # py311+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "pre_pr_check.toml"


# ---------------------------------------------------------------------------
# Result and severity
# ---------------------------------------------------------------------------

BLOCK = "BLOCK"
WARN = "WARN"
OK = "OK"


@dataclass
class Finding:
    rule: str
    severity: str  # BLOCK | WARN | OK
    message: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, rule: str, severity: str, message: str) -> None:
        self.findings.append(Finding(rule, severity, message))

    def has_blocks(self) -> bool:
        return any(f.severity == BLOCK for f in self.findings)

    def render(self) -> str:
        lines = []
        symbols = {BLOCK: "✗", WARN: "!", OK: "✓"}
        for f in self.findings:
            lines.append(f"  {symbols.get(f.severity, '?')} [{f.severity}] {f.rule}: {f.message}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def run(cmd: list[str], cwd: Path | None = None) -> str:
    res = subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return res.stdout


def changed_files(base: str, staged_only: bool) -> list[Path]:
    if staged_only:
        out = run(["git", "diff", "--name-only", "--cached"])
    else:
        out = run(["git", "diff", "--name-only", f"{base}...HEAD"])
    files = [REPO_ROOT / line.strip() for line in out.splitlines() if line.strip()]
    return [f for f in files if f.exists()]


def matches_any(path: Path, patterns: list[str]) -> bool:
    return any(path.match(p) or p in str(path) for p in patterns)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("rb") as fh:
        return tomllib.load(fh)


# ---------------------------------------------------------------------------
# Universal checks
# ---------------------------------------------------------------------------


def check_release_notes(report: Report, files: list[Path], cfg: dict) -> None:
    """If there's a functional change, require an entry in CHANGELOG/release_notes."""
    notes_paths = cfg.get("release_notes", {}).get(
        "paths", ["CHANGELOG.md", "release_notes.md"]
    )
    code_globs = cfg.get("release_notes", {}).get("code_globs", ["src/**", "app/**", "lib/**"])

    code_changed = any(matches_any(f.relative_to(REPO_ROOT), code_globs) for f in files)
    if not code_changed:
        report.add("release-notes", OK, "no production code changes")
        return

    notes_touched = any(
        any(str(f).endswith(p) for p in notes_paths) for f in files
    )
    if not notes_touched:
        report.add(
            "release-notes",
            BLOCK,
            f"code changed but no release notes file ({', '.join(notes_paths)}) was updated",
        )
    else:
        report.add("release-notes", OK, "release notes updated")


def check_components_md(report: Report, files: list[Path], cfg: dict) -> None:
    """If a new helper/service was created, COMPONENTS.md must be updated."""
    helper_globs = cfg.get("components", {}).get(
        "helper_globs", ["**/utils/**", "**/helpers/**", "**/services/**"]
    )

    new_helpers = []
    out = run(["git", "diff", "--name-status", cfg.get("base", "main") + "...HEAD"])
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] == "A":
            p = REPO_ROOT / parts[-1]
            if matches_any(p.relative_to(REPO_ROOT), helper_globs):
                new_helpers.append(p)

    if not new_helpers:
        report.add("components-md", OK, "no new helpers")
        return

    components_touched = any(str(f).endswith("COMPONENTS.md") for f in files)
    if not components_touched:
        report.add(
            "components-md",
            BLOCK,
            f"new helpers detected ({len(new_helpers)}) but COMPONENTS.md was not updated",
        )
    else:
        report.add("components-md", OK, "COMPONENTS.md updated")


def check_secrets(report: Report, files: list[Path], cfg: dict) -> None:
    """Run gitleaks if available."""
    has_gitleaks = subprocess.run(
        ["which", "gitleaks"], capture_output=True, text=True
    ).returncode == 0
    if not has_gitleaks:
        report.add("secrets", WARN, "gitleaks not installed — skipping")
        return

    res = subprocess.run(
        ["gitleaks", "detect", "--no-banner", "--redact"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        report.add("secrets", BLOCK, "gitleaks detected a possible secret")
    else:
        report.add("secrets", OK, "no secrets detected")


def check_feature_flag(report: Report, files: list[Path], cfg: dict) -> None:
    """Heuristic: new routes should sit behind a feature flag."""
    route_patterns = cfg.get("feature_flag", {}).get(
        "route_globs", ["**/routers/**", "**/routes/**", "**/controllers/**"]
    )
    flag_marker = cfg.get("feature_flag", {}).get("marker", "is_enabled")

    route_files = [
        f for f in files if matches_any(f.relative_to(REPO_ROOT), route_patterns)
    ]
    if not route_files:
        report.add("feature-flag", OK, "no new/changed routes")
        return

    missing = []
    for f in route_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if flag_marker not in content:
            missing.append(str(f.relative_to(REPO_ROOT)))

    if missing:
        report.add(
            "feature-flag",
            WARN,
            f"routes without `{flag_marker}` marker: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}",
        )
    else:
        report.add("feature-flag", OK, "routes use feature flag")


_TEST_FILE_PATTERN = re.compile(
    r"(^|/)(test_[^/]+|[^/]+_test|[^/]+\.test|tests?/.+)\.(py|js|ts|jsx|tsx|go|rs|java|kt)$"
)
_FORBIDDEN_TEST_PATTERNS = [
    (re.compile(r"\btime\.sleep\("), "time.sleep in test — use clock fakes"),
    (re.compile(r"\bawait\s+sleep\("), "await sleep in test — use fake timers"),
    (re.compile(r"\bsetTimeout\("), "setTimeout in test — use fake timers"),
    (re.compile(r"@(pytest\.mark\.)?skip\b(?![\s\S]{1,200}reason\s*=)"), "skipped test without reason="),
    (re.compile(r"\.(skip|todo)\([\"']"), "skipped/todo test — add ticket reference"),
    (re.compile(r"\bassert\s+(True|1\s*==\s*1)\b"), "placeholder assertion (assert True / 1==1)"),
]


def check_test_quality(report: Report, files: list[Path], cfg: dict) -> None:
    """Detect common test smells in changed test files."""
    if not cfg.get("pre_pr_check", {}).get("test_quality", True):
        return

    test_files = [
        f for f in files if _TEST_FILE_PATTERN.search(str(f.relative_to(REPO_ROOT)))
    ]
    if not test_files:
        report.add("test-quality", OK, "no test files changed")
        return

    issues: list[str] = []
    for f in test_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat, msg in _FORBIDDEN_TEST_PATTERNS:
            if pat.search(content):
                issues.append(f"{f.relative_to(REPO_ROOT)}: {msg}")

    if issues:
        report.add(
            "test-quality",
            BLOCK,
            f"{len(issues)} smell(s): " + "; ".join(issues[:3])
            + ("..." if len(issues) > 3 else ""),
        )
    else:
        report.add("test-quality", OK, f"{len(test_files)} test file(s) clean")


_MIGRATION_PATH_PATTERN = re.compile(
    r"(^|/)(migrations?|alembic|prisma/migrations)/", re.IGNORECASE
)
_UNSAFE_MIGRATION_PATTERNS = [
    (re.compile(r"\bDROP\s+COLUMN\b", re.I), "DROP COLUMN — needs two-phase deploy"),
    (re.compile(r"\bRENAME\s+(TO|COLUMN)\b", re.I), "RENAME without alias — breaks rolling deploys"),
    (re.compile(r"\bSET\s+NOT\s+NULL\b", re.I), "SET NOT NULL — verify 3-step pattern (nullable → backfill → not null)"),
    (re.compile(r"CREATE\s+(UNIQUE\s+)?INDEX\s+(?!CONCURRENTLY)", re.I), "CREATE INDEX without CONCURRENTLY (Postgres locks writes)"),
]


def check_migration_safety(report: Report, files: list[Path], cfg: dict) -> None:
    """Heuristic safety review of migration files."""
    if not cfg.get("pre_pr_check", {}).get("migration_safety", True):
        return

    migrations = [
        f for f in files if _MIGRATION_PATH_PATTERN.search(str(f.relative_to(REPO_ROOT)))
    ]
    if not migrations:
        report.add("migration-safety", OK, "no migrations changed")
        return

    issues: list[str] = []
    for f in migrations:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat, msg in _UNSAFE_MIGRATION_PATTERNS:
            if pat.search(content):
                issues.append(f"{f.relative_to(REPO_ROOT)}: {msg}")

    severity = WARN  # heuristic-only; real review by schema-reviewer / squawk
    if issues:
        report.add(
            "migration-safety",
            severity,
            f"{len(issues)} potential issue(s): " + "; ".join(issues[:3])
            + ("..." if len(issues) > 3 else "")
            + " — also run squawk / schema-reviewer",
        )
    else:
        report.add("migration-safety", OK, f"{len(migrations)} migration(s) clean")


def check_custom_sync(report: Report, files: list[Path], cfg: dict) -> None:
    """Project-specific synchronizations (defined in pre_pr_check.toml).

    Format in .toml:
        [[sync]]
        name = "okr-draft"
        when_any_changes = ["app/templates/okr_form.html"]
        require_all_change = ["app/models.py", "app/routers/drafts.py"]
    """
    rules = cfg.get("sync", [])
    if not rules:
        return

    file_strs = {str(f.relative_to(REPO_ROOT)) for f in files}
    for rule in rules:
        name = rule.get("name", "sync")
        triggers = rule.get("when_any_changes", [])
        required = rule.get("require_all_change", [])

        triggered = any(t in file_strs for t in triggers)
        if not triggered:
            continue

        missing = [r for r in required if r not in file_strs]
        if missing:
            report.add(
                f"sync:{name}",
                BLOCK,
                f"trigger fired but missing change in: {', '.join(missing)}",
            )
        else:
            report.add(f"sync:{name}", OK, "sync complete")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-PR checklist")
    parser.add_argument("--base", default=None, help="base branch (default: main)")
    parser.add_argument("--staged", action="store_true", help="check only staged changes")
    parser.add_argument("--strict", action="store_true", help="warnings become blocks")
    args = parser.parse_args()

    cfg = load_config()
    base = args.base or cfg.get("base", "main")

    files = changed_files(base, args.staged)
    if not files:
        print("No files changed.")
        return 0

    report = Report()
    check_release_notes(report, files, cfg)
    check_components_md(report, files, cfg)
    check_feature_flag(report, files, cfg)
    check_test_quality(report, files, cfg)
    check_migration_safety(report, files, cfg)
    check_custom_sync(report, files, cfg)
    check_secrets(report, files, cfg)

    print(f"Pre-PR check ({len(files)} files changed vs {base}):")
    print(report.render())

    blocks = [f for f in report.findings if f.severity == BLOCK]
    warns = [f for f in report.findings if f.severity == WARN]

    if blocks or (args.strict and warns):
        print(f"\n✗ {len(blocks)} block(s), {len(warns)} warn(s) — failed")
        return 1

    print(f"\n✓ ok ({len(warns)} non-blocking warn(s))")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"Internal error: {exc}", file=sys.stderr)
        sys.exit(2)
