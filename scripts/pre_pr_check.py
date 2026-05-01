#!/usr/bin/env python3
"""
Checklist pré-PR — validações determinísticas que devem passar antes
de abrir Pull Request.

Parametrizado por `pre_pr_check.toml` na raiz do projeto. Sem o arquivo,
roda apenas as verificações universais.

Uso:
    python scripts/pre_pr_check.py              # checa branch atual vs main
    python scripts/pre_pr_check.py --base develop
    python scripts/pre_pr_check.py --staged     # só o que está staged
    python scripts/pre_pr_check.py --strict     # warnings viram block

Saída:
    Exit 0  — tudo OK
    Exit 1  — pelo menos um BLOCK
    Exit 2  — erro interno do script
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
# Resultado e severidade
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
# Helpers de git
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
# Verificações universais
# ---------------------------------------------------------------------------


def check_release_notes(report: Report, files: list[Path], cfg: dict) -> None:
    """Se há mudança funcional, exige entry em CHANGELOG/release_notes."""
    notes_paths = cfg.get("release_notes", {}).get(
        "paths", ["CHANGELOG.md", "release_notes.md"]
    )
    code_globs = cfg.get("release_notes", {}).get("code_globs", ["src/**", "app/**", "lib/**"])

    code_changed = any(matches_any(f.relative_to(REPO_ROOT), code_globs) for f in files)
    if not code_changed:
        report.add("release-notes", OK, "sem mudança em código de produção")
        return

    notes_touched = any(
        any(str(f).endswith(p) for p in notes_paths) for f in files
    )
    if not notes_touched:
        report.add(
            "release-notes",
            BLOCK,
            f"código alterado mas nenhum arquivo de release notes ({', '.join(notes_paths)}) foi atualizado",
        )
    else:
        report.add("release-notes", OK, "release notes atualizado")


def check_components_md(report: Report, files: list[Path], cfg: dict) -> None:
    """Se criou helper/serviço novo, COMPONENTS.md deve ser atualizado."""
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
        report.add("components-md", OK, "nenhum helper novo")
        return

    components_touched = any(str(f).endswith("COMPONENTS.md") for f in files)
    if not components_touched:
        report.add(
            "components-md",
            BLOCK,
            f"novos helpers detectados ({len(new_helpers)}) mas COMPONENTS.md não foi atualizado",
        )
    else:
        report.add("components-md", OK, "COMPONENTS.md atualizado")


def check_secrets(report: Report, files: list[Path], cfg: dict) -> None:
    """Roda gitleaks se disponível."""
    has_gitleaks = subprocess.run(
        ["which", "gitleaks"], capture_output=True, text=True
    ).returncode == 0
    if not has_gitleaks:
        report.add("secrets", WARN, "gitleaks não instalado — pulando")
        return

    res = subprocess.run(
        ["gitleaks", "detect", "--no-banner", "--redact"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        report.add("secrets", BLOCK, "gitleaks detectou possível segredo")
    else:
        report.add("secrets", OK, "nenhum segredo detectado")


def check_feature_flag(report: Report, files: list[Path], cfg: dict) -> None:
    """Heurística: nova rota deve estar atrás de feature flag."""
    route_patterns = cfg.get("feature_flag", {}).get(
        "route_globs", ["**/routers/**", "**/routes/**", "**/controllers/**"]
    )
    flag_marker = cfg.get("feature_flag", {}).get("marker", "is_enabled")

    route_files = [
        f for f in files if matches_any(f.relative_to(REPO_ROOT), route_patterns)
    ]
    if not route_files:
        report.add("feature-flag", OK, "nenhuma rota nova/alterada")
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
            f"rotas sem `{flag_marker}` aparente: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}",
        )
    else:
        report.add("feature-flag", OK, "rotas usam feature flag")


def check_custom_sync(report: Report, files: list[Path], cfg: dict) -> None:
    """Sincronizações específicas do projeto (definidas em pre_pr_check.toml).

    Formato no .toml:
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
                f"trigger ativado mas faltou alterar: {', '.join(missing)}",
            )
        else:
            report.add(f"sync:{name}", OK, "sincronização completa")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Checklist pré-PR")
    parser.add_argument("--base", default=None, help="branch base (default: main)")
    parser.add_argument("--staged", action="store_true", help="checar só staged")
    parser.add_argument("--strict", action="store_true", help="warnings viram block")
    args = parser.parse_args()

    cfg = load_config()
    base = args.base or cfg.get("base", "main")

    files = changed_files(base, args.staged)
    if not files:
        print("Nenhum arquivo alterado.")
        return 0

    report = Report()
    check_release_notes(report, files, cfg)
    check_components_md(report, files, cfg)
    check_feature_flag(report, files, cfg)
    check_custom_sync(report, files, cfg)
    check_secrets(report, files, cfg)

    print(f"Pre-PR check ({len(files)} arquivos alterados vs {base}):")
    print(report.render())

    blocks = [f for f in report.findings if f.severity == BLOCK]
    warns = [f for f in report.findings if f.severity == WARN]

    if blocks or (args.strict and warns):
        print(f"\n✗ {len(blocks)} block(s), {len(warns)} warn(s) — falhou")
        return 1

    print(f"\n✓ ok ({len(warns)} warn(s) não-bloqueantes)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"Erro interno: {exc}", file=sys.stderr)
        sys.exit(2)
