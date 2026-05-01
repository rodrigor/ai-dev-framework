# Memory templates

Formatos das memórias persistentes que a IA mantém ao longo do projeto.

## Como funcionam

Memórias ficam num diretório `memory/` da IA (fora do repo, no scope de
usuário ou projeto). O índice (`MEMORY.md`) lista cada memória com link
e resumo de uma linha.

## Tipos

### `feedback_*`
Regra de comportamento que o dev corrigiu. Usar quando a IA fez algo errado
e o dev pediu pra **sempre** fazer diferente. Ver `feedback_template.md`.

### `project_*`
Contexto vivo do projeto: iniciativa em curso, decisão tomada, configuração
de ambiente, peculiaridade. Ver `project_template.md`.

### `debt_*` (subgrupo de `project_*`)
Dívida técnica catalogada com trigger de revisita ("quando passar de X
usuários", "quando lib Y subir pin"). Ver `debt_template.md`.

## Quando criar memória

- Dev corrigiu a IA explicitamente ("sempre faça X", "nunca faça Y") →
  `feedback_*`.
- Decisão importante tomada que afeta sessões futuras → `project_*` ou ADR.
- Dívida que a IA tem que lembrar para não recriar o problema → `debt_*`.

## Quando NÃO criar memória

- Solução de bug pontual (já está no código).
- Padrão derivável do código (a IA descobre lendo).
- Estado efêmero da sessão.
- Algo que cabe melhor em CLAUDE.md, COMPONENTS.md ou ADR.

## Revisão periódica

Use a skill `consolidate-memory` trimestralmente: merge duplicatas, fix
fatos obsoletos, remove memórias que viraram código (hook/script).
