# feedback_<slug>.md

> Template para memórias do tipo `feedback_*` — regras de comportamento
> que o dev corrigiu/validou.

---

# <Título curto e imperativo>

**Quando:** <gatilho exato — ex: "ao mexer em template HTML">
**Faça:** <ação obrigatória — ex: "rode `npm run build:css` antes de
commitar">
**Não faça:** <ação proibida ou anti-padrão>

## Por quê

<1-3 linhas explicando a razão. Inclua a conta que justifica a regra:
incidente que aconteceu, retrabalho que evita, risco que cobre.>

## Como verificar

<comando ou critério objetivo de verificação. Se virou hook, mencione.>

---

## Exemplo preenchido

# Sempre rebuildar CSS antes de commitar

**Quando:** Tocar qualquer arquivo em `templates/`.
**Faça:** Rodar `npm run build:css` e adicionar `static/css/app.css` ao
commit.
**Não faça:** Commitar template sem rebuild — CI quebra com erro
"app.css desatualizado".

## Por quê

O container de runtime não tem Node. CSS é compilado e versionado.
Pipeline tem gate explícito que falha se hash do CSS não bate com hash
das classes nos templates.

## Como verificar

`scripts/pre_pr_check.py` valida automaticamente.
