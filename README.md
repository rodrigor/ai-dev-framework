# ai-dev-framework

Arcabouço para desenvolvimento guiado por IA: documentos, controles e
automações reutilizáveis em qualquer projeto, agnósticos a stack.

A camada perene (princípios, processos, segurança) entra igual em todo
projeto. A camada de **ferramentas** (SAST, análise de deps, cobertura,
complexidade, modularidade) é decidida no `init` baseado na stack detectada.

## O que tem aqui

- `CLAUDE.md` — instruções carregadas em toda sessão de IA
- `QUALITY.md` — esqueleto dos controles automáticos (preenchido no init)
- `SECURITY.md` — políticas perenes de segurança
- `PROCESS.md` — workflows (bug-fix, feature, release notes, pré-PR)
- `COMPONENTS.md` — catálogo de componentes reutilizáveis (vazio inicialmente)
- `GLOSSARY.md` — terminologia do domínio (preenchido pelo projeto)
- `docs/adr/` — Architecture Decision Records
- `memory-templates/` — formatos de memória mantidos pela IA
- `.claude/` — hooks, subagentes, slash commands, skills (inclui `init-project`)
- `scripts/pre_pr_check.py` — checklist pré-PR parametrizável

## Uso

### Como template

1. Use este repo como **GitHub Template** ou clone e remova `.git`.
2. Abra o projeto no Claude Code.
3. Rode `/init-project` — a skill detecta a stack e propõe a tabela de
   ferramentas (SAST, deps, cobertura, complexidade, modularidade, segredos).
4. Confirme as escolhas. O init gera `QUALITY.md` preenchido,
   `.github/workflows/quality.yml`, `.pre-commit-config.yaml` e configs
   das ferramentas.

### Filosofia

- **Documentação perene vira código quando possível.** Regras que dependem
  de o agente "lembrar" são frágeis; hooks que o harness executa são
  determinísticos.
- **Camada perene não muda por stack.** Princípios UX, política de segredos,
  workflow de bug-fix, soft-delete patterns valem em qualquer linguagem.
- **Ferramentas são plugáveis.** Trivy, Semgrep, gitleaks, SonarQube etc.
  são escolhas; a função (escanear deps, achar segredo) é perene.

Veja `PROCESS.md` para o ciclo completo.
