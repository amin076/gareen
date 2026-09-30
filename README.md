# Gareen

Gareen is a small research project for exploring whether a machine can grow formal mathematical knowledge from a deliberately limited symbolic world.

The host computer and the mathematical object-world are kept separate. Python may use ordinary arithmetic, Boolean logic, memory, and control flow to execute the program, but mathematical knowledge is accepted by Gareen only when it is represented inside the formal world and passes the proof checker.

## Phase 8 — Automatic proof search

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

Gareen now has a separate bounded proof-search layer. The searcher proposes proof trees from existing axioms, theorems, universal instantiation, equality symmetry, congruence, and transitivity; the original trusted checker remains the only component allowed to accept a proof.

### Arithmetic primitives

```text
0      constant
S      unary successor function
Add    binary addition function
Mul    binary multiplication function
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

A5_MUL_ZERO
∀x. Mul(x, 0) = 0

A6_MUL_SUCCESSOR
∀x∀y. Mul(x, S(y)) = Add(Mul(x, y), x)
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
EQ_ADD_LEFT_CONGRUENCE
EQ_ADD_RIGHT_CONGRUENCE
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

### Associativity of addition

Gareen next derives:

```text
T8_ADD_ASSOCIATIVE
∀a∀b∀c. (a + b) + c = a + (b + c)
```

The proof is again by induction on the third argument. Two explicit equality-congruence rules allow an already verified equality to be used inside either argument of `Add`. No associativity axiom is added.

### Multiplication enters the language

Multiplication is now a new arithmetic primitive:

```text
Mul(x, y)
```

Its behavior is introduced only through two recursive axioms:

```text
A5: Mul(x, 0) = 0
A6: Mul(x, S(y)) = Add(Mul(x, y), x)
```

So multiplication is not delegated to Python integers. The symbolic rewrite engine can now reduce expressions such as `2 × 3` using A5/A6 together with the existing addition rules.

Two initial multiplication theorems are derived:

```text
T9_ZERO_MUL_X
∀x. 0 × x = 0

T10_MUL_ONE
∀x. x × 1 = x
```

Notice the asymmetry: `x × 0 = 0` is an axiom, while `0 × x = 0` is a theorem proved by induction.

### Core multiplication laws

Gareen first proves the helper lemma:

```text
T11_MUL_SUCC_LEFT
∀x∀v. S(x) × v = (x × v) + v
```

That lemma is then reused to prove multiplication commutativity:

```text
T12_MUL_COMMUTATIVE
∀x∀z. x × z = z × x
```

Next, Gareen derives right distributivity:

```text
T13_MUL_DISTRIBUTIVE
∀x∀u∀v. x × (u + v) = (x × u) + (x × v)
```

Finally, distributivity becomes a dependency of multiplication associativity:

```text
T14_MUL_ASSOCIATIVE
∀x∀u∀w. (x × u) × w = x × (u × w)
```

The dependency chain now includes:

```text
addition axioms
      ↓
addition theorems
      ↓
T11 left-successor multiplication
      ↓
T12 multiplication commutativity

T8 addition associativity
      ↓
T13 multiplication distributivity
      ↓
T14 multiplication associativity
```

None of these four multiplication laws is inserted as a new arithmetic axiom.

### Automatic proof search

`proof_search.py` is intentionally separate from the trusted checker.

The Phase 8 searcher currently accepts **closed / ground goals** and performs a bounded search. It:

```text
collects terms from the goal
instantiates universal axioms and verified theorems
indexes concrete facts
searches equality paths
uses symmetry, congruence, and transitivity
compiles the candidate derivation into ordinary ProofStep objects
sends the final proof back to check_proof()
```

The first demonstration goal is:

```text
2 + 1 = 3
```

There is no hand-written proof for this target in the search module. The search layer must combine available facts and equality rules to construct a candidate proof. Only after `check_proof()` validates the complete result may it be added to the knowledge state as:

```text
AUTO_TWO_PLUS_ONE
```

This establishes a trust boundary:

```text
untrusted search / future AI
          ↓
candidate proof
          ↓
trusted deterministic checker
          ↓
verified theorem
```

Phase 8 deliberately does not yet search induction proofs or open-variable theorems. Those remain future work.

### Capture-safe universal instantiation

`FORALL_ELIM` now checks whether substituting a term would accidentally capture one of its free variables under an inner quantifier. Gareen rejects such a proof step instead of silently accepting an invalid substitution.

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

Gareen now includes addition, recursive multiplication, universal quantification, and a deliberately small induction rule, but it still does **not** include:

- existential quantification;
- a general equality substitution rule;
- induction-aware automatic theorem search;
- open-variable / universally quantified proof search;
- theorem-interest scoring;
- Lean;
- LLMs or agents.

Those should be added gradually, only after each lower layer is testable and auditable.

## Next milestone

The next step is to expand search without weakening the trust boundary:

```text
search universally quantified goals
search induction proofs
record failed search branches
rank candidate lemmas
discover useful intermediate statements
```

The verifier should remain deterministic and separate even if future search is guided by heuristics, agents, or an LLM.

## Research question

> Can a machine autonomously expand a bounded formal mathematical knowledge state while every accepted result remains explicitly derivable and auditable?
