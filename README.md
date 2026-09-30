# Gareen

Gareen is a small research project for exploring whether a machine can grow formal mathematical knowledge from a deliberately limited symbolic world.

The host computer and the mathematical object-world are kept separate. Python may use ordinary arithmetic, Boolean logic, memory, and control flow to execute the program, but mathematical knowledge is accepted by Gareen only when it is represented inside the formal world and passes the proof checker.

## Phase 5 — Generalization and commutativity of addition

Gareen now distinguishes:

```text
primitive symbols
definitions
axioms
inference rules
proofs
verified theorems
knowledge state
```

Gareen now verifies nested universal theorems and derives commutativity of addition from the small starting system. Universal introduction is checked so a variable cannot be generalized while it remains free in an open assumption.

### Arithmetic primitives

```text
0      constant
S      unary successor function
Add    binary addition function
```

### Logical primitives

```text
=      equality
¬      negation
→      implication
∀      universal quantifier
⊥      contradiction / falsum
```

### Definitions

```text
1 := S(0)
2 := S(S(0))
3 := S(S(S(0)))
```

The numerals 1, 2, and 3 are definitions, not additional primitives.

### Arithmetic axioms

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

### Current inference rules

The proof checker currently supports a deliberately small logic:

```text
AXIOM
THEOREM
ASSUMPTION
FORALL_ELIM
FORALL_INTRO
MODUS_PONENS
EQ_SYMMETRY
EQ_SUCC_CONGRUENCE
EQ_TRANSITIVITY
CONTRADICTION
NEGATION_INTRO
INDUCTION
```

These are logical proof operations. They are not additional arithmetic facts.

## First derived theorems

`build_initial_knowledge()` constructs a knowledge state and accepts a theorem only after its proof passes the checker.

The current derived knowledge is:

```text
T1_ONE_NONZERO
¬(1 = 0)

T2_ONE_NE_TWO
¬(1 = 2)

T3_TWO_NE_THREE
¬(2 = 3)

T4_TWO_PLUS_ZERO
2 + 0 = 2
```

Internally the numerals are still successor terms, so for example `1 = 2` means:

```text
S(0) = S(S(0))
```

### The first induction theorem

The important new result is:

```text
T5_ZERO_PLUS_X
∀x. Add(0, x) = x
```

This theorem is **not** an axiom. Gareen receives only:

```text
A3: Add(x, 0) = x
A4: Add(x, S(y)) = S(Add(x, y))
```

The proof checked by Gareen has the usual induction structure:

```text
Base:
  Add(0, 0) = 0                 from A3

Induction hypothesis:
  Add(0, x) = x

Step:
  Add(0, S(x)) = S(Add(0, x))  from A4
  S(Add(0, x)) = S(x)          by successor congruence
  Add(0, S(x)) = S(x)          by equality transitivity

Therefore:
  ∀x. Add(0, x) = x            by induction
```

The temporary induction hypothesis is tracked as an open assumption and must be discharged by the `INDUCTION` rule before the theorem is accepted.

### Successor on the left

Before proving commutativity, Gareen derives the helper theorem:

```text
T6_SUCC_ADD
∀x∀z. Add(S(x), z) = S(Add(x, z))
```

The proof is by induction on `z`. Its base case uses `A3_ADD_ZERO`; its induction step uses `A4_ADD_SUCCESSOR`, successor congruence, equality symmetry, and equality transitivity.

After induction produces a theorem with free `x`, `FORALL_INTRO` generalizes over `x`. The checker rejects this step if `x` occurs free in an open assumption.

### Commutativity of addition

Gareen then derives:

```text
T7_ADD_COMMUTATIVE
∀x∀y. Add(x, y) = Add(y, x)
```

The proof is by induction on `y`.

Base case:

```text
x + 0 = x        from A3
0 + x = x        from T5
therefore x + 0 = 0 + x
```

Induction step, assuming:

```text
x + y = y + x
```

Gareen derives:

```text
x + S(y)
= S(x + y)       from A4
= S(y + x)       by successor congruence
= S(y) + x       from T6
```

and then discharges the induction hypothesis and universally quantifies both variables.

So commutativity is stored as **derived knowledge**, not as an axiom.

### Why T3 matters

`T3_TWO_NE_THREE` reuses the already verified theorem `T2_ONE_NE_TWO`.

So the knowledge graph has begun to grow:

```text
A1 ──> T1
A2 + T1 ──> T2
A2 + T2 ──> T3

A3 ──> T4
```

That is the first concrete version of:

```text
starting knowledge
      ↓
verified derivation
      ↓
new reusable knowledge
```

## Proof checking

A theorem is rejected if:

- it cites an unknown axiom or theorem;
- a universal instantiation is wrong;
- Modus Ponens does not match;
- an equality symmetry step is malformed;
- a contradiction is not genuinely `P` together with `¬P`;
- a negation proof fails to discharge its assumption;
- any temporary assumption remains open;
- or the last proof line does not equal the claimed theorem.

The checker therefore does not trust a theorem merely because Python created an object with that label.

## Symbolic arithmetic

The earlier rewrite experiment is still retained.

What humans call `2 + 3` is represented as:

```text
Add(S(S(0)), S(S(S(0))))
```

and reduces through `A4` three times followed by `A3` once to:

```text
S(S(S(S(S(0)))))
```

The object-world never asks Python to calculate integer `2 + 3`.

## Run

Requires Python 3.10+ and no third-party packages.

```bash
python math_world.py
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Current boundary

This is still a tiny fragment, not full Peano Arithmetic.

Gareen now includes a deliberately small, explicit induction rule, but it still does **not** include:

- multiplication;
- existential quantification;
- a general equality substitution rule;
- automatic theorem search;
- theorem-interest scoring;
- Lean;
- LLMs or agents.

Those should be added gradually, only after each lower layer is testable and auditable.

## Next milestone

The next mathematically meaningful targets are associativity of addition and then multiplication:

```text
(x + y) + z = x + (y + z)
x × 0 = 0
x × S(y) = (x × y) + x
```

Multiplication should be introduced only after the addition layer is sufficiently proven and tested.

## Research question

> Can a machine autonomously expand a bounded formal mathematical knowledge state while every accepted result remains explicitly derivable and auditable?
