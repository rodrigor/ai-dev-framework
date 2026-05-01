---
name: init-project
description: Inicializa um projeto baseado no ai-dev-framework. Detecta a stack tecnológica (Python, Node/TypeScript, Go, Rust, Java/Kotlin) lendo manifestos do projeto, propõe a tabela de ferramentas (SAST, análise de deps, cobertura, complexidade ciclomática, modularidade, segredos, lint, format, tipagem), pergunta os gates ao desenvolvedor (cobertura mínima, severidade que bloqueia), e gera os artefatos preenchidos — QUALITY.md, workflow CI, .pre-commit-config.yaml, configs das ferramentas. Use quando o usuário pedir para inicializar, configurar, fazer setup ou bootstrap de um novo projeto, ou quando mencionar "init project", "configurar quality", "escolher ferramentas de qualidade".
---

# init-project

Inicializa um projeto baseado no `ai-dev-framework`.

## Quando usar

- Repositório novo recém-clonado do template.
- Projeto existente que vai adotar o arcabouço.
- Mudança de stack que exige rever ferramentas.

## Procedimento

### 1. Detectar a stack

Leia, em paralelo, os manifestos presentes:

| Arquivo | Stack |
|---|---|
| `pyproject.toml`, `requirements.txt`, `setup.py`, `Pipfile` | Python |
| `package.json` (+ `tsconfig.json` → TypeScript) | Node/TS |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pom.xml`, `build.gradle*` | Java/Kotlin |
| `Gemfile` | Ruby |
| `composer.json` | PHP |

Pode haver mais de uma stack (ex: backend Python + frontend TS). Trate
cada uma.

### 2. Propor tabela de ferramentas

Baseie-se em `QUALITY.md` (seção "Tabela de referência por stack"). Para
cada função (SAST, deps, cobertura, complexidade, modularidade, segredos,
lint, format, tipagem, dead code) apresente:

- Ferramenta padrão sugerida
- Alternativas
- Comando de instalação/uso

Apresente como tabela e peça confirmação por linha. Permita o dev
sobrescrever qualquer escolha.

### 3. Perguntar gates

Faça as seguintes perguntas (uma de cada vez, com default sugerido):

- **Cobertura mínima inicial?** (default: 60%, sobe 1pp por release)
- **Severidade de deps que bloqueia?** (default: HIGH e CRITICAL)
- **CC máximo aceito sem revisão?** (default: rank D — `radon` ou
  equivalente)
- **MI mínimo?** (default: 20)
- **Política de segredos?** (default: gitleaks bloqueia qualquer match)
- **Roda em pre-commit local?** (default: lint + format + gitleaks)

### 4. Antes de fixar versões — buscar a mais recente

Para cada ferramenta escolhida, **busque na internet a versão estável
mais recente** (PyPI / npm / crates.io / GitHub releases) antes de
fixar no manifesto. Não confiar em valores conhecidos — podem estar
desatualizados.

### 5. Gerar artefatos

Crie/atualize:

1. **`QUALITY.md`** — preenchido com tabela real de ferramentas e gates.
   Remova as seções `[STACK X]` que não se aplicam.
2. **`.github/workflows/quality.yml`** (ou GitLab CI/Bitbucket) com
   um job por gate.
3. **`.pre-commit-config.yaml`** com hooks locais.
4. **Configs das ferramentas:**
   - Python: `pyproject.toml [tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`
   - Node: `eslint.config.js` ou `biome.json`, `tsconfig.json` strict, `vitest.config.ts`
   - Outras conforme stack
5. **`.gitleaks.toml`** com allowlist mínima.
6. **Entry inicial em `CHANGELOG.md`** documentando o init.

### 6. Smoke test

Para cada ferramenta instalada, rode em modo `--version` ou em diff vazio
para confirmar que está funcional. Reporte o que passou e o que falhou.

### 7. Resumo final

Apresente:
- Stack(s) detectada(s)
- Ferramentas escolhidas (tabela)
- Gates configurados
- Arquivos criados/modificados
- Próximos passos (rodar `pre-commit install`, configurar secrets do CI,
  preencher `GLOSSARY.md`, etc.)

## Princípios

- **Não imponha:** sempre apresente padrão e alternativas. O dev decide.
- **Versão mais recente:** sempre buscar antes de fixar.
- **Mínimo viável:** começar com gates conservadores. Apertar com o tempo.
- **Documente o "porquê":** ao gerar `QUALITY.md`, comente brevemente o
  motivo de cada escolha.
