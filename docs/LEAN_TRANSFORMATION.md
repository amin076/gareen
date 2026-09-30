# Gareen Lean Transformation

## Why this change

Gareen's Python formal world taught us how the pieces fit together:

- syntax
- axioms
- proof rules
- proof search
- induction
- conjecture generation
- research memory

That sandbox remains useful for experimentation. It should not become a second Lean.

From Phase 12 onward, the production-grade trust path is Lean 4 + Mathlib.

## Architecture

```text
Gareen Research Layer (Python)
  ├─ conjecture generation
  ├─ pattern mining
  ├─ strategy selection
  ├─ research memory
  ├─ novelty / interestingness (future)
  └─ provider selection
          ↓
Python → Lean Bridge
          ↓
Proof Candidate Provider
  ├─ local deterministic tactics   [implemented]
  ├─ BFS-Prover-V2                [adapter target]
  ├─ Discover-and-Prove           [adapter target]
  └─ other Lean provers           [adapter target]
          ↓
Lean 4 + Mathlib
          ↓
Lean Kernel
          ↓
Lean-verified research record
```

## Phase 12A — Lean foundation

Pinned:

- Lean 4.34.0
- Mathlib v4.34.0
- Lake project at repository root
- Lean library namespace `Gareen`

The file `Gareen/Foundation.lean` verifies the arithmetic laws that the Python
sandbox previously derived manually. These Lean theorems are not meant to be
new mathematics; they establish the formal backend.

## Phase 12B — Python → Lean bridge

`lean_bridge.py` translates the current Gareen AST:

```text
Zero
Var
Succ
Add
Mul
Eq
Not
Implies
ForAll
Bottom
```

into Lean propositions over `Nat`.

Example:

```text
ForAll(X, Eq(Add(ZERO, X), X))
```

becomes:

```lean
∀ (x : Nat), (0 + x) = x
```

## Phase 12C — Lean verification gateway

`LeanVerifier` sends a generated theorem to:

```text
lake env lean <generated-file>
```

and records Lean's accepted/rejected result.

The initial proof provider is a zero-cost deterministic tactic portfolio:

```text
simp
omega
ring
norm_num
aesop
```

The provider proposes proof code. Lean decides whether it is valid.

## Phase 12D — Dual CI

Python CI continues to test the research sandbox.

A separate Lean CI job:

1. installs the pinned Lean toolchain;
2. downloads the Mathlib cache;
3. runs `lake build`;
4. generates a theorem through the Python bridge;
5. asks Lean to compile that generated theorem;
6. runs a small Lean-backed research campaign.

A PR is not considered healthy if either backend fails.

## Phase 12E — Prover adapters

`prover_adapters.py` defines the boundary for stronger open-source provers.

The first targets are:

- BFS-Prover-V2
- Discover-and-Prove
- future Lean-compatible provers

These systems are **proof providers**, not trust authorities. Their output must
still be accepted by Lean.

## What we stop rebuilding

Gareen will not spend its main development effort on:

- a replacement for Lean's kernel;
- a replacement for Mathlib;
- a general-purpose tactic language;
- reproducing mature theorem-prover infrastructure.

The Python formal world remains a pedagogical and experimental sandbox.

## What remains uniquely Gareen's job

The research layer should focus on:

- what question to investigate next;
- conjecture generation;
- concept and definition proposal;
- research memory;
- failure analysis;
- lemma invention;
- theorem-interest scoring;
- dependency impact;
- autonomous research campaigns;
- coordination of multiple proof providers.

That is the level at which Gareen can become an autonomous mathematical
research system instead of another theorem prover.
