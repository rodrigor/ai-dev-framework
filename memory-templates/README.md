# Memory templates

Formats for the persistent memories the AI maintains across project
sessions.

## How they work

Memories live in the AI's `memory/` directory (outside the repo, in
user or project scope). The index (`MEMORY.md`) lists each memory with
a link and a one-line summary.

## Types

### `feedback_*`
Behavior rule the dev corrected. Use when the AI did something wrong
and the dev asked it to **always** behave differently. See
`feedback_template.md`.

### `project_*`
Living context of the project: ongoing initiative, decision taken,
environment setup, peculiarity. See `project_template.md`.

### `debt_*` (subset of `project_*`)
Cataloged technical debt with a revisit trigger ("when we pass N
users", "when lib Y bumps pin"). See `debt_template.md`.

## When to create a memory

- Dev corrected the AI explicitly ("always do X", "never do Y") →
  `feedback_*`.
- Important decision affecting future sessions → `project_*` or ADR.
- Debt the AI must remember to avoid recreating the problem → `debt_*`.

## When NOT to create a memory

- Pointwise bug fix (it's already in the code).
- Pattern derivable from the code (the AI discovers it by reading).
- Ephemeral session state.
- Something that fits better in CLAUDE.md, COMPONENTS.md, or an ADR.

## Periodic review

Use the `consolidate-memory` skill quarterly: merge duplicates, fix
stale facts, drop memories that became code (hook/script).
