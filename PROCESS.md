# Processo de desenvolvimento

Workflows perenes do projeto. Como o ciclo "IA implementa, dev guia"
funciona na prática.

## Ciclo padrão de uma mudança

```
1. Entender pedido
   └─ ler CLAUDE.md, GLOSSARY.md se for domínio novo
2. Explorar código existente
   └─ knowledge graph PRIMEIRO; Grep/Read só se graph não cobre
3. Consultar COMPONENTS.md
   └─ tem helper/macro/service que resolve? reuse ou generalize
4. Propor abordagem (curta) — esperar OK do dev em mudanças não-triviais
5. Implementar
   ├─ se for bug: TESTE PRIMEIRO (vê falhar) → fix → vê passar
   ├─ se for feature: feature flag obrigatória
   └─ se criar componente reutilizável: catalogar em COMPONENTS.md
6. Atualizar release notes / CHANGELOG (seção "Em desenvolvimento")
7. Rodar checklist pré-PR (scripts/pre_pr_check.py)
8. Abrir PR — todos os scanners verdes (HIGH/CRITICAL = bloqueio)
```

## Workflow de bug em produção

1. Reproduzir o bug.
2. **Escrever teste** que falha pelo motivo do bug.
3. Corrigir.
4. Teste passa.
5. Entry em release notes (`fixed`).
6. PR.

Sem teste → bug regride. Não há exceção.

## Workflow de feature nova

1. Registrar feature flag no registry.
2. Proteger rota e UI com `is_enabled(flag)`.
3. Default da flag pode ser `True`, mas a flag **deve existir** para
   permitir desligar em incidente sem deploy.
4. Testes cobrindo flag ON e OFF (a UI/rota se comporta corretamente
   nos dois estados).
5. Entry em release notes (`added`).
6. Se a feature criar componente reutilizável → catalogar.

## Release notes

A fonte da verdade é `CHANGELOG.md` (ou arquivo equivalente do projeto).

- Toda mudança funcional registra entrada na seção **Em desenvolvimento**.
- Tipos: `added`, `changed`, `fixed`, `removed`, `security`.
- Se houver distinção usuário-final vs admin/infra: duas trilhas separadas.
- Ao publicar versão: substitua "Em desenvolvimento" por
  `{version, date, ...}` e crie nova seção vazia acima.

## Checklist pré-PR

`scripts/pre_pr_check.py` valida automaticamente. Cobertura mínima:

- [ ] Release notes atualizado (entry em "Em desenvolvimento")
- [ ] `COMPONENTS.md` atualizado se criou helper/serviço/macro reutilizável
- [ ] Feature flag registrada se criou rota/feature nova
- [ ] Sincronizações específicas do projeto (definidas em `CLAUDE.md`)
- [ ] Build artifacts gerados se aplicável (CSS compilado, schemas gerados)
- [ ] Testes existentes passam, novos testes cobrem mudança
- [ ] Scanners SAST/deps/segredos sem HIGH/CRITICAL

## Análise periódica de complexidade

Após **grandes features** (módulo novo, refactor amplo, fix grande), rode
os comandos definidos em `QUALITY.md` na seção "Complexidade" e cruze com
churn (git log dos últimos 3 meses).

Hotspots (alta complexidade × alto churn) entram na fila de refactor
prioritário antes da próxima feature no mesmo arquivo.

## Decisões arquiteturais → ADR

Decisões que afetam estrutura do sistema (escolha de DB, multi-tenancy,
estratégia de cache, framework principal, modelo de auth) viram ADR em
`docs/adr/NNNN-titulo.md`. Use o template `0000-template.md`.

Memórias de IA (`project_*`) são voláteis e individuais; ADR é versionado
e revisável por todo o time.

## Memórias mantidas pela IA

A IA mantém memórias persistentes para acelerar sessões futuras. Ver
`memory-templates/` para os formatos. Tipos:

- **`feedback_*`** — regra de comportamento que o dev corrigiu/validou.
  Ex: "sempre rebuild Tailwind antes de commitar templates".
- **`project_*`** — contexto vivo de iniciativas, decisões e dívidas.
  Ex: "migração para multi-tenancy em fase 2".
- **`debt_*`** (subgrupo de `project_*`) — dívida técnica catalogada com
  trigger de revisita.

Memórias **não** substituem ADR nem documentação. São atalhos para a IA
não repetir erros conhecidos.

## Revisão periódica

- **Memórias:** consolidação trimestral (skill `consolidate-memory`).
  Memórias `project_*` envelhecem rápido; revisar.
- **Dívidas técnicas:** revisitar quando o trigger é atingido (passou de
  X usuários, biblioteca Y subiu pin, etc.).
- **CLAUDE.md:** revisar a cada release maior — regras que viraram código
  (hooks, scripts) podem sair daqui.

## Princípio: documentação vira código quando possível

Regras que dependem de a IA "lembrar" são frágeis. Quando uma regra
aparecer 3x em CLAUDE.md ou em memórias `feedback_*`, considere
transformá-la em hook/script/subagente que o harness executa
deterministicamente.
