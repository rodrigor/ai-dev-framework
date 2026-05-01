# Controles de qualidade — `QUALITY.md`

Fonte única dos controles automáticos. Preenchido pelo `/init-project`
baseado na stack detectada. Atualize sempre que adicionar/alterar
controle.

> **Status:** `[ESQUELETO — preencher no init-project]`
> Após o init, remova os blocos `[STACK X]` que não se aplicam.

## Visão geral dos gates

Um PR só passa se todos os gates abaixo estiverem verdes.

| Função | Ferramenta | Gate (bloqueia em) | Como rodar local |
|---|---|---|---|
| SAST | `[preencher]` | severidade ≥ HIGH | `[comando]` |
| Deps/CVEs | `[preencher]` | severidade ≥ HIGH | `[comando]` |
| Segredos | `gitleaks` | qualquer match | `gitleaks detect` |
| Cobertura | `[preencher]` | < `[X]`% | `[comando]` |
| Complexidade ciclomática | `[preencher]` | rank ≥ E | `[comando]` |
| Modularidade / MI | `[preencher]` | MI < 20 | `[comando]` |
| Lint / format | `[preencher]` | qualquer erro | `[comando]` |
| Tipagem (se aplicável) | `[preencher]` | qualquer erro | `[comando]` |
| Dead code | `[preencher]` | warning | `[comando]` |

## Pipeline CI

`.github/workflows/quality.yml` (ou equivalente) roda todos os gates em
paralelo e bloqueia merge se qualquer um falha.

## Tabela de referência por stack

> Use o init-project para preencher; deixe aqui apenas a stack do projeto.

### [STACK Python]

| Função | Padrão | Alternativas |
|---|---|---|
| SAST | Semgrep + Bandit | CodeQL |
| Deps | pip-audit + Trivy fs | Safety, Snyk |
| Cobertura | pytest-cov, gate `--cov-fail-under=X` | coverage.py |
| CC | `radon cc -s -a --min C` | xenon (gate) |
| MI | `radon mi -s` | wily |
| Lint | ruff | flake8, pylint |
| Format | black ou ruff format | — |
| Tipagem | mypy ou pyright | — |
| Dead code | vulture | — |
| Segredos | gitleaks | trufflehog |

Comandos padrão:

```bash
# SAST
semgrep --config auto --error
bandit -r src/ -ll

# Deps
pip-audit
trivy fs --severity HIGH,CRITICAL .

# Cobertura
pytest --cov=src --cov-fail-under=60

# Complexidade (rank C ou pior)
radon cc src -s -a --exclude "tests/*" --min C
radon mi src --exclude "tests/*" -s | grep -v "- A$"

# Churn (cruzar com complexidade)
git log --since="3 months ago" --name-only --pretty=format: \
  -- "src/*.py" | grep "\.py$" | sort | uniq -c | sort -rn | head -20

# Lint/format
ruff check .
ruff format --check .

# Tipagem
mypy src/

# Dead code
vulture src/

# Segredos
gitleaks detect --redact
```

### [STACK Node/TypeScript]

| Função | Padrão | Alternativas |
|---|---|---|
| SAST | Semgrep + ESLint security plugins | CodeQL, SonarJS |
| Deps | npm audit + Trivy + osv-scanner | Snyk |
| Cobertura | vitest --coverage / jest --coverage | c8 |
| CC | eslint-plugin-complexity | complexity-report, plato |
| Modularidade | madge (cycles) + dependency-cruiser | — |
| Lint+format | Biome (tudo-em-um) | ESLint + Prettier |
| Tipagem | `tsc --noEmit` strict | — |
| Dead code | knip | ts-prune |
| Segredos | gitleaks | — |

```bash
# SAST
semgrep --config auto --error
npx eslint . --max-warnings 0

# Deps
npm audit --audit-level=high
trivy fs --severity HIGH,CRITICAL .

# Cobertura
npx vitest run --coverage  # com threshold em vitest.config

# Complexidade — via ESLint rule "complexity": ["error", 10]
# ou:
npx complexity-report -f json src/

# Modularidade
npx madge --circular src/
npx depcruise src/

# Tipagem
npx tsc --noEmit

# Dead code
npx knip

# Segredos
gitleaks detect --redact
```

### [STACK Go]

| Função | Padrão |
|---|---|
| SAST | gosec + Semgrep |
| Deps | govulncheck + Trivy |
| Cobertura | `go test -cover` + go-test-coverage threshold |
| CC | gocyclo + gocognit |
| Modularidade | go-mod-graph + goda |
| Lint | golangci-lint (agrega ~40) |
| Segredos | gitleaks |

### [STACK Rust]

| Função | Padrão |
|---|---|
| SAST | clippy strict + Semgrep |
| Deps | cargo-audit + cargo-deny |
| Cobertura | cargo-llvm-cov / tarpaulin |
| CC | rust-code-analysis |
| Lint | `clippy --all-targets -- -D warnings` |

### [STACK Java/Kotlin]

| Função | Padrão |
|---|---|
| SAST | SpotBugs+FindSecBugs + Semgrep |
| Deps | OWASP Dependency-Check + Trivy |
| Cobertura | JaCoCo com threshold |
| CC/MI | PMD + Checkstyle |
| Modularidade | JDepend ou ArchUnit |
| Lint | ktlint/detekt (Kotlin), Checkstyle (Java) |

## Régua de decisão — complexidade

Após grandes features, rode CC + MI e cruze com churn.

| Métrica | Limiar | Ação |
|---|---|---|
| CC rank E ou F | qualquer churn | Decompor antes do próximo merge no arquivo |
| CC rank D | churn ≥ 15 commits/3 meses | Hotspot — refactor na próxima sprint |
| MI rank B (< 20) | — | Refactor prioritário |
| MI rank C (< 10) | — | Bloqueio — decompor antes de qualquer feature nova |

## Cobertura de testes

- **Baseline inicial:** `[X]`% (preencher no init).
- **Política:** sobe 1pp a cada release, nunca desce. Gate em CI impede
  regressão.
- **Excluir:** seeds, fixtures, demos, scripts de migração one-shot.

## Hooks locais (pre-commit)

`.pre-commit-config.yaml` roda lint, format e gitleaks antes do commit.
Não substitui o CI mas pega 80% dos problemas no laptop.

## Quando atualizar este documento

- Adicionou/removeu workflow CI
- Mudou pin de versão de scanner
- Mudou política (cobertura mínima, severidade que bloqueia)
- Novo controle introduzido

Atualizações em `QUALITY.md` na **mesma entrega** que mexe no controle.
