# Code style — writing for AI maintainability

How to write code so the next AI agent (or human) can change it
safely, cheaply, and without breaking things.

This goes beyond formatting. Formatting is a solved problem (the
formatter handles it). This document is about **structure, locality,
and predictability** — properties that determine how many tokens an
agent must read before changing a line, and how likely the change is
to break something else.

---

## The two costs

Every line of code carries:

1. **Token cost** — how much an agent must read to understand it
   before changing.
2. **Bug-injection probability** — chance that a change here breaks
   something elsewhere, or here, or both.

Good code minimizes both. Bad code is "clever" — high local density,
high coupling, costly to read, fragile to change.

---

## Locality: the agent should rarely need more than one file

The single biggest cost in agent-driven development is having to read
many files to make a small change.

**Rules:**

1. **A function's behavior is determined by its arguments** — not by
   global state, not by import-time side effects, not by hidden caches.
2. **A module's contract is documented at the top.** First 10 lines
   say what it does, what it depends on, what it exports.
3. **Tests live next to code.** `foo.py` ↔ `test_foo.py`. The agent
   doesn't have to scan a separate tree.
4. **Domain types are co-located.** Don't split `User` model from
   `User` service across distant directories.
5. **Cross-cutting concerns** (auth middleware, logging, tenancy) live
   in **one** known location, referenced from `INFRASTRUCTURE.md`.

**Anti-pattern:** "the meaning of `process_order()` is in 6 decorators,
4 mixins, 2 metaclasses, and a config file."

---

## Explicit over implicit

Magic destroys agent-friendliness. Every implicit behavior is a hidden
rule the agent must learn before being safe to change anything.

**Avoid:**
- Metaclasses that mutate classes at definition time.
- Decorators that perform I/O at import.
- Monkey-patching of stdlib or framework internals.
- Implicit type coercion in critical paths.
- Auto-discovery / auto-import (e.g., "every file in `routes/` becomes
  a route automatically").
- Dynamic attribute access (`getattr(obj, name)`) when a dispatch dict
  would do.

**Prefer:**
- Explicit registration (`router.include(routes)`) over auto-discovery.
- Plain functions over decorators when behavior is non-trivial.
- Composition over inheritance, especially deep hierarchies.
- `__init__.py` files that re-export specific names, not `*`.

---

## Type hints are documentation that the type checker validates

In typed languages (Python via mypy/pyright, TS, Go, Rust), **always
add type annotations**. The agent reads `def f(x: User) -> Order` and
knows the contract without inferring.

- **Forbid `Any` / `unknown`** in production code (allow in narrow
  conversion seams).
- **Use `TypedDict` / discriminated unions / sum types** for
  structured data instead of free-form dicts.
- **Validate at boundaries** with Pydantic / zod / serde — turn `dict`
  into typed model immediately on entry.

A typed function in 5 lines can be read in seconds. An untyped 20-line
function needs the agent to read every caller to understand inputs.

---

## Functions: small, pure, single-purpose

- **Cyclomatic complexity ≤ 10** (rank A or B in radon). Anything
  bigger gets decomposed.
- **Length ≤ 40 lines** as a soft target, ≤ 80 as a hard limit. Long
  functions consume tokens linearly.
- **One thing per function.** If you need "and" in the docstring, the
  function does too much.
- **Side-effect-free where possible.** Pure logic in a core; I/O and
  side effects at the edges (hexagonal lite).
- **Inputs in, outputs out** — no surprise mutations of arguments.

**Heuristic:** if a function is hard to test in isolation, its design
is wrong, not its tests.

---

## Modules: clear contracts, narrow surfaces

Every module has:

1. **A docstring/header** explaining purpose, contracts, non-goals.
2. **A small public surface.** Re-export only what callers need; keep
   helpers private (`_underscore` prefix in Python, lowercase in Go,
   `pub(crate)` in Rust).
3. **One reason to change.** Modules with multiple unrelated
   responsibilities will be touched by every PR — high churn, high
   conflict.

**Module size:** ≤ 400 lines as a soft target. Bigger modules are a
smell; split by concern.

---

## Naming: descriptive and consistent

- **Verbs for functions** (`create_user`, `validate_email`).
- **Nouns for data** (`user`, `email_address`).
- **Same concept, same name.** If it's `tenant_id` in one place, it's
  `tenant_id` everywhere — never `tenantId` here, `company_id` there.
- **Avoid abbreviations** unless the abbreviation is a domain
  convention (`url`, `id`, `db`).
- **Search-friendly names.** `create_user` is better than `add` because
  the agent's grep finds the right thing.

A consistent vocabulary across the codebase reduces token cost: the
agent can predict names instead of reading them.

---

## Errors: explicit, typed, recoverable

- **Define a small hierarchy of exceptions / error types.** Don't raise
  bare `Exception` / `Error`.
- **Errors are part of the function's contract.** Document what raises
  what.
- **No `except: pass`** in production code. Catching everything hides
  real bugs.
- **Validate at boundaries**, then trust internal data. Don't
  defensive-code everywhere.
- **Recoverable vs fatal:** distinguish in the type system or by
  exception class.

---

## Comments: explain "why", not "what"

Code already says what. The agent reads code fast. What it can't
recover is **why** a decision was made.

**Good comments:**
```python
# Use bcrypt rounds=12 — measured 250ms on prod hardware in 2024-Q4,
# which is the upper acceptable bound for login latency.
```

**Bad comments:**
```python
# Hash the password
hash = bcrypt(password, rounds=12)
```

Heuristic: if removing the comment loses information that isn't in the
code, keep it. Otherwise, delete.

**Module headers** are different — they explain purpose and contracts.
Always include them.

---

## State and mutation

- **Immutable by default.** Frozen dataclasses, readonly types,
  `const` where the language supports it.
- **No global mutable state** in business logic. If you must (caches,
  registries), wrap behind an explicit interface.
- **Database is the only state of record.** Caches are caches —
  invalidatable, never authoritative.

Mutable shared state is the hardest thing for an agent to reason
about. Eliminate it where possible; quarantine it where you can't.

---

## Dependency injection over globals

```python
# Bad — implicit global
def create_user(payload):
    user = db.session.add(User(**payload))   # which db?
    mailer.send_welcome(user.email)           # which mailer?
    return user

# Good — explicit deps
def create_user(payload, *, session, mailer):
    user = User(**payload)
    session.add(user)
    mailer.send_welcome(user.email)
    return user
```

Or pass a request-scoped context object. The agent reads the signature
and knows what the function touches. Tests don't need to mock globals.

---

## One way to do common things

Every common operation has **one** canonical implementation. Examples:

- One way to log (the project's logger; not `print` + `logging` mixed).
- One way to make HTTP requests.
- One way to parse dates.
- One way to handle errors in API routes.
- One way to render dates/numbers in the UI.

When there are two ways, the agent will pick one randomly per PR, and
the codebase fragments. Document the canonical way in
`COMPONENTS.md`.

---

## Avoid premature abstraction

Three concrete duplicates is the **earliest** you should extract an
abstraction. Two duplicates is a coincidence.

**Anti-pattern:** building a pluggable framework for one use case
because "we might extend it later." The framework is dead weight until
the second consumer exists; until then, it's tokens the agent must
read for nothing.

**Heuristic:** abstractions earn their place by serving real, distinct
consumers. No consumer = no abstraction.

---

## Avoid clever tricks

Clever:
```python
result = next((x for x in items if x.valid), None) or default()
```

Clear:
```python
valid = [x for x in items if x.valid]
result = valid[0] if valid else default()
```

The clear version is one more line and infinitely more readable. The
agent doesn't need to mentally parse a generator + `next` + `or`
chain.

**Forbid:**
- Triple-nested comprehensions (split into loops).
- Operator-overload abuse (`__add__` for non-arithmetic).
- One-letter variable names outside trivial loop indices.
- Bit-twiddling without a comment.

---

## Documentation that earns its place

- **Module headers**: always.
- **Function docstrings**: when the signature isn't self-explanatory,
  or when there are non-obvious side effects / errors.
- **`COMPONENTS.md`**: every reusable helper.
- **`GLOSSARY.md`**: every domain term that has potential synonyms.
- **ADRs**: every non-trivial architectural decision.

Don't write docs that restate the code. Don't write docs that will
rot (specific line numbers, specific values that change).

---

## Test code is real code

- Same style rules apply to tests (small, descriptive names, no
  clever tricks).
- Test names describe the behavior tested:
  `test_create_user_rejects_duplicate_email`, not `test_user_2`.
- One concept per test.
- AAA structure: Arrange / Act / Assert, visually separated.
- Test fixtures over setup boilerplate; share via the test framework's
  fixtures, not module-level globals.

(See `QUALITY.md` "Test quality" for smell linters and mutation
testing.)

---

## Refactor opportunistically, but bounded

When changing a file:
- **In scope:** rename for clarity, extract a helper used twice in the
  diff, fix obvious dead code.
- **Out of scope:** "while I'm here, let me also refactor this whole
  module."

Out-of-scope refactors balloon the diff, hide the real change, and
introduce risk. Catalog them as `debt_*` memories or open a separate
PR.

---

## Token economy at the file level

Specific guidelines that compound:

- **Concise but descriptive names.** `validate_email` not
  `perform_email_validation_check_and_return_result`.
- **No ceremonial wrappers.** Don't wrap a one-line stdlib call in a
  function unless you're adding meaning.
- **Strip dead code aggressively.** The dead-code linter blocks PRs
  with unused exports.
- **Avoid file headers full of legal/license noise** in source files;
  put it in `LICENSE`. Source files start with the module docstring.
- **Avoid generated boilerplate** committed to the repo (e.g.,
  protobuf stubs) unless necessary; .gitignore them.

---

## Project-level signals that AI maintainability is degrading

Watch for:

- **Average file size growing** over releases → split modules.
- **Cross-file change ratio** rising (one PR touches many files) →
  coupling increased.
- **Test/code ratio dropping** → coverage backsliding.
- **CC rank D/E hotspots** appearing repeatedly in churn analysis →
  refactor before next feature.
- **`Any` / `unknown` types appearing** in new code → tightening
  required.

`PROCESS.md` "Periodic complexity analysis" describes the routine.

---

## Summary heuristics

- **Default to small, typed, pure functions.**
- **One file should rarely need more than itself to be understood.**
- **Explicit over implicit, every time.**
- **One canonical way per common operation.**
- **Comments explain why; code shows what.**
- **No abstraction without a second concrete consumer.**
- **Search-friendly names, consistent vocabulary.**
- **Forbid `Any`, forbid clever tricks, forbid silent error
  swallowing.**
