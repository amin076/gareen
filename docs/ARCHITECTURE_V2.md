# Gareen Architecture V2 — Lean-backed Artificial Mathematician

## Decision

Gareen will **not** attempt to become a replacement for Lean, Mathlib, or
state-of-the-art theorem provers.

The Python formal world built in Phases 1–11 remains valuable as:

- a transparent educational model;
- a research sandbox for conjecture generation;
- a place to prototype search and induction strategies;
- a regression suite for Gareen's early ideas.

It is no longer the trusted foundation for serious mathematical research.

## New trust boundary

```text
Gareen Research Layer (Python)
  ├─ observation / pattern mining
  ├─ conjecture generation
  ├─ research memory
  ├─ novelty / interestingness
  ├─ strategy selection
  ├─ lemma and definition proposals
  └─ campaign orchestration
              │
              ▼
        Python → Lean Bridge
              │
              ▼
Lean / Mathlib / external Lean provers
  ├─ simp / omega / ring / aesop / ...
  ├─ future BFS-Prover / Seed-Prover adapters
  └─ future LeanConjecturer comparison
              │
              ▼
          Lean Kernel
              │
              ▼
     Lean-verified Knowledge Base
```

## Source of truth

A candidate can be useful to Gareen's Python research loop without being a
mathematical theorem. A durable theorem is accepted only after a Lean proof is
kernel-checked.

The Python checker is therefore **sandbox-trusted**, while Lean is
**research-trusted**.

## Phase 12 — Lean foundation

- Pin a stable Lean toolchain.
- Pin the matching Mathlib release.
- Build a native Gareen Lean library.
- Re-express representative arithmetic laws in Lean.
- Start using Mathlib's number-theory vocabulary instead of recreating it.

## Phase 13 — Verification bridge

- Translate Gareen terms and formulas into Lean syntax.
- Emit auditable Lean source.
- Try a bounded tactic portfolio.
- Accept a candidate only when `lake env lean` succeeds.
- Keep generated files out of source control by default.

## Phase 14 — Lean-backed research

- Generate conjectures in Gareen.
- Verify them through Lean.
- Store a separate Lean-verified discovery record.
- Do not fake a Python `Proof` object for a Lean proof.
- Treat Lean verification provenance as first-class metadata.

## Future prover adapters

The bridge is intentionally narrower than a full prover integration. Future
backends should implement the same acceptance contract:

```text
candidate Lean proposition
      ↓
backend proposes Lean proof
      ↓
Lean kernel checks proof
      ↓
verified / rejected
```

Planned evaluation targets:

1. native Mathlib tactics (baseline);
2. BFS-Prover-V2;
3. Discover-and-Prove;
4. Seed-Prover;
5. LeanConjecturer for conjecture-generation comparison.

## What remains uniquely Gareen

Gareen should compete on the **research loop**, not on rebuilding a kernel:

- persistent research memory;
- failed-attempt analysis;
- long-horizon theory growth;
- theorem interestingness;
- dependency impact;
- autonomous lemma invention;
- definition/concept invention;
- choosing what mathematics to investigate next.

## Phase 17 — theorem retrieval and proof planning

Gareen now has a first explicit theorem-retrieval/planning backend.

For Lean-native number-theory goals it can:

1. ask Mathlib's `exact?` retrieval engine for a direct library proof;
2. introduce universally quantified variables and retry retrieval;
3. recognize a reusable structural schema such as `d ∣ x + y`;
4. decompose the goal into reusable subgoals;
5. retrieve Mathlib facts for the subgoals;
6. retrieve a library composition theorem from the local hypotheses;
7. accept the result only when Lean's kernel checks the generated proof.

The initial planner schema is intentionally general over the divisor and
addends. The GCD benchmark is a regression target, not a hard-coded proof.
Future schemas can add implication planning, transitivity, gcd/lcm structure,
modular arithmetic, induction and recursive lemma invention.

