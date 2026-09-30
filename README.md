# Gareen

Gareen is a small research project for exploring whether a machine can grow formal mathematical knowledge from a deliberately limited symbolic world.

The project starts with the smallest useful experiment: define mathematical objects and legal transformations explicitly, execute them symbolically, and keep every derivation auditable.

## Phase 1 — Symbolic Arithmetic Core

Phase 1 contains no LLM, no agents, no Lean, and no modern number-theory library.

The object-world currently knows only:

- `0` — symbolic zero
- `S(x)` — symbolic successor
- `Add(a, b)` — symbolic addition
- two explicit recursive rewrite rules

```text
Add(a, 0)    -> a
Add(a, S(b)) -> S(Add(a, b))
```

For example, what humans call `2 + 3` is represented inside Gareen as:

```text
Add(S(S(0)), S(S(S(0))))
```

and is reduced only through the declared object-world rules until it reaches:

```text
S(S(S(S(S(0)))))
```

The object-world does not ask Python to evaluate `2 + 3`.

## Meta-level vs object-level

Gareen intentionally separates two layers:

```text
Host / meta-level
  Python, CPU, memory, loops, data structures

Mathematical / object-level
  Zero, Succ, Add, declared formal rules
```

The host machine inevitably uses its own arithmetic and Boolean logic to execute the program. That is not treated as mathematical knowledge available to the symbolic world.

A result counts as derived in Gareen only when its trace is built from rules explicitly declared inside the object-world.

## Current structure

```text
gareen/
├─ math_world.py
├─ tests/
│  └─ test_math_world.py
├─ README.md
├─ LICENSE
└─ .gitignore
```

## Run

Requires Python 3.10+ and no third-party packages.

```bash
python math_world.py
```

Run the tests with:

```bash
python -m unittest discover -s tests -v
```

## What Phase 1 establishes

Phase 1 establishes a minimal symbolic environment in which:

- mathematical objects are represented explicitly;
- legal transformations are declared explicitly;
- each transformation can be traced;
- host-language arithmetic is not used as an object-world proof step.

It does not yet attempt to discover theorems.

## Next direction

The next milestone is to move from expression rewriting to a small formal knowledge state containing:

```text
statement
proof
dependencies
knowledge state
```

Only after that foundation is reliable will it make sense to experiment with theorem generation, proof search, Lean verification, LLMs, or multi-agent exploration.

## Research question

The long-term question behind Gareen is:

> Can a machine autonomously expand a bounded formal mathematical knowledge state while every accepted result remains explicitly derivable and auditable?
