# Instruções de desenvolvimento — projeto baseado em ai-dev-framework

Este arquivo é carregado em toda sessão de IA. Regras aqui têm precedência
sobre defaults do agente.

> Adapte as seções marcadas `[ADAPTAR]` ao seu projeto. As demais são perenes
> e devem permanecer.

---

## ⚠️ Reutilização de componentes — consulte SEMPRE antes de codar

Antes de implementar qualquer helper, módulo, dependência, service, macro
ou bloco de lógica reutilizável, **consulte `COMPONENTS.md`** (na raiz).
Ele cataloga tudo que já existe.

Regra dura:
- **Não reimplemente** algo que já existe. Reutilize.
- **Se precisa variar**, generalize o componente existente (parâmetros,
  função comum extraída) em vez de criar uma variante.
- **Se encontrar duplicação** durante refactor, unifique e atualize
  `COMPONENTS.md`.
- **Ao criar algo genuinamente novo e reutilizável**, adicione ao catálogo
  na mesma entrega — caminho, assinatura, propósito.

`COMPONENTS.md` é fonte da verdade. Mantenha-o vivo.

---

## Princípios de UX/UI (obrigatórios em qualquer interface)

A interface deve ser **intuitiva e minimalista** — o menor número de
elementos visuais necessários para cumprir a tarefa.

1. **Menos é mais.** Cada elemento precisa justificar a presença. Prefira
   esconder (collapse, abas, modais) a empilhar tudo.
2. **Priorize o essencial.** Campos importantes no topo; secundários em
   seções colapsáveis com default sensato.
3. **Priorize a informação nas exibições.** Status/nome/progresso primeiro;
   metadados (autor, data, IDs) em segundo plano.
4. **Defaults inteligentes.** Todo campo opcional tem default que cobre
   80% dos casos.
5. **Sugira simplificações proativamente.** Se notar excesso de campos,
   etapas redundantes ou rótulos verbosos, **aponte antes de implementar**.
   Não simplifique silenciosamente.
6. **Comunicação visual consistente.** Reuse padrões/componentes
   existentes em vez de criar variantes.

Estas regras têm precedência sobre estética pontual.

---

## Workflow de bug em produção

1. **Escreva um teste** que reproduza o bug antes de corrigir.
2. Confirme que o teste falha.
3. Corrija o bug.
4. Confirme que o teste passa.

Bugs sem teste regridem. Não corrija sem teste.

---

## Release notes — registrar toda mudança funcional

A fonte da verdade do histórico é o arquivo de release notes do projeto
(`CHANGELOG.md` ou equivalente). Sempre que adicionar, alterar, remover
ou corrigir uma funcionalidade, registre uma entrada na seção **Em
desenvolvimento** (primeiro item):

- `added` — nova funcionalidade
- `changed` — alteração em funcionalidade existente
- `fixed` — correção de bug
- `removed` — funcionalidade removida
- `security` — correção de segurança

Ao publicar versão: substitua "Em desenvolvimento" por
`{version, date, ...}` e crie nova seção vazia acima.

Se o projeto tem distinção entre mudanças visíveis ao usuário e mudanças
admin/infra, mantenha duas trilhas separadas.

---

## Dependências externas — sempre versão mais recente

Antes de adicionar qualquer biblioteca ao manifesto de deps (`requirements.txt`,
`package.json`, `go.mod`, `Cargo.toml`, etc.), **busque na internet a versão
estável mais recente** (PyPI / npm / crates.io / pkg.go.dev / Maven Central) e
fixe essa versão. Nunca assuma que uma versão conhecida é a atual — pode estar
faltando patches de CVE.

---

## Segurança — políticas duras (ver `SECURITY.md`)

- Credenciais sempre criptografadas em repouso. Nunca em plaintext nem em env
  vars sem necessidade.
- **Nunca logar** valores de tokens, API keys, senhas, mesmo em DEBUG. Os
  scanners SAST detectam e bloqueiam.
- Em fluxos de auth, **nunca revelar se um email/usuário existe**. Resposta
  genérica em login/forgot/resend.
- Antes de PR: nenhum scanner com finding HIGH ou CRITICAL.

---

## Política de soft-delete

Três maneiras de "remover" — escolha por tipo:

1. **Hard-delete** (`DELETE` físico): tokens efêmeros, logs após retenção,
   dados sensíveis com TTL.
2. **Soft-delete** (`deleted_at` nullable): entidades de produto que podem
   ser restauradas. Lista padrão omite `deleted_at IS NOT NULL`.
3. **Status enum** (`CANCELLED`, `ARCHIVED`, `CLOSED`): estado de máquina
   de domínio onde a história importa. Não use `deleted_at` aqui.

Casos especiais (User.active, Tenant.archived_at) — não duplicar padrão.
**Não introduza um quarto.**

---

## Análise periódica de complexidade e manutenibilidade

Após qualquer **grande feature** (módulo novo, refactor amplo, fix grande),
rode os comandos definidos em `QUALITY.md` (seção "Complexidade") e cruze
com churn (git log dos últimos 3 meses).

**Réguas de decisão (genéricas; valores exatos em `QUALITY.md`):**

| Métrica | Limiar | Ação |
|---------|--------|------|
| CC rank E ou F | qualquer churn | Decompor antes do próximo merge no arquivo |
| CC rank D | churn alto | Hotspot — planejar decomposição na próxima sprint |
| MI rank B (< 20) | — | Refactor prioritário |
| MI rank C (< 10) | — | Bloqueio — decompor antes de qualquer feature nova |

---

## Controles automáticos — `QUALITY.md`

**Fonte única dos controles** (CI, pre-commit, scanners, testes,
cobertura, complexidade, modularidade) é `QUALITY.md`.

Consulte **antes de**:
- Adicionar/remover workflow de CI
- Introduzir novo linter/scanner
- Mudar política (cobertura mínima, severidade que bloqueia, etc.)
- Investigar falha de CI

Ao introduzir novo controle, **atualize `QUALITY.md`** na mesma entrega:
caminho do script, o que verifica, o que bloqueia, como rodar localmente.

---

## Confirmação de ações destrutivas

Use o componente de modal do projeto. **Nunca** `alert()` / `confirm()`
nativos. Defina o padrão único em `COMPONENTS.md`.

---

## Feature flags em toda nova funcionalidade

Toda feature nova nasce atrás de feature flag (registry + checagem na rota
e na UI). Default pode ser `True` mas a flag deve existir para permitir
desativação rápida em incidente.

---

## Internacionalização

Chaves, enums, identificadores e variáveis nascem em **inglês** desde o
início. Strings visíveis ao usuário passam por sistema de i18n.

---

## [ADAPTAR] Domínio do projeto

Liste aqui as **regras específicas do seu domínio**: sincronizações
obrigatórias entre arquivos, módulos críticos, demos a manter, dívidas
técnicas em aberto. Veja `MEMORY.md` para o catálogo de memórias.

---

## [ADAPTAR] Knowledge graph / navegação de código

Se o projeto usa knowledge graph (code-review-graph ou similar), priorize-o
sobre Grep/Glob/Read.

| Tarefa | Ferramenta |
|---|---|
| Explorar | semantic search no graph |
| Impacto | impact_radius / get_affected_flows |
| Code review | detect_changes + get_review_context |
| Relacionamentos | callers/callees/imports/tests |

Fall back para Grep/Read **só** quando o graph não cobre.
