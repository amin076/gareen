# Gareen

Gareen is a small research project for exploring whether a machine can grow formal mathematical knowledge from a deliberately limited symbolic world.

The project separates the host computer from the mathematical object-world. Python may use ordinary arithmetic internally to execute the program, but Gareen only accepts mathematical knowledge that is explicitly represented inside the object-world.

## Phase 2 — Explicit formal world

The current version now distinguishes four categories:

1. arithmetic primitives
2. logical primitives
3. definitions
4. axioms

### Arithmetic primitives

```text
0      constant
S      unary successor function
Add    binary addition function
```

### Logical primitive

```text
=      equality relation
```

Equality is intentionally kept in the logical layer rather than treated as an arithmetic symbol.

### Definitions

The numerals are definitions, not new primitives:

```text
1 := S(0)
2 := S(S(0))
3 := S(S(S(0)))
```

### Current axioms

```text
A1_SUCCESSOR_NONZERO
∀x. ¬(S(x) = 0)

A2_SUCCESSOR_INJECTIVE
∀x∀y. (S(x) = S(y)) → (x = y)

A3_ADD_ZERO
∀x. Add(x, 0) = x

A4_ADD_SUCCESSOR
∀x∀y. Add(x, S(y)) = S(Add(x, y))
```

The first two axioms constrain successor. The second pair recursively characterizes addition on the second argument.

## Symbolic execution

The expression humans call `2 + 3` is represented as:

```text
Add(S(S(0)), S(S(S(0))))
```

Gareen reduces it only with the declared arithmetic axioms:

```text
A4_ADD_SUCCESSOR
A4_ADD_SUCCESSOR
A4_ADD_SUCCESSOR
A3_ADD_ZERO
```

until it reaches:

```text
S(S(S(S(S(0)))))
```

No Python integer addition is used as an object-world proof step.

## Run

Python 3.10+ is enough; there are no third-party dependencies.

```bash
python math_world.py
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Current limitation

Gareen still does not prove arbitrary formulas. `A1` and `A2` are represented formally, but the engine currently executes only the two addition axioms as rewrite rules.

The next milestone is to add:

```text
statement
proof
inference rule
derived theorem
knowledge state
```

so the system can distinguish facts supplied as axioms from results actually derived by the machine.

## Research question

> Can a machine autonomously expand a bounded formal mathematical knowledge state while every accepted result remains explicitly derivable and auditable?
