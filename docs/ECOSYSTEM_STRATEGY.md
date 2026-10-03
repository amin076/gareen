# Gareen Ecosystem Strategy

## Principle

Before implementing a mathematical capability in Gareen, ask:

1. Does Lean already provide the trusted logical/formal mechanism?
2. Does Mathlib already formalize the mathematical concept?
3. Does an open-source Lean prover already solve the proof-search problem?
4. Does an open-source conjecture system already cover the generation task?
5. If yes, what specifically remains a Gareen research contribution?

The default is **reuse and integrate**, not rebuild.

## Capability ownership

| Capability | Gareen should own? | Preferred foundation |
| --- | --- | --- |
| Trusted kernel | No | Lean 4 |
| Formal standard library | No | Mathlib |
| Divisibility / primes / gcd / modular arithmetic | No | Mathlib |
| Basic tactics | No | Mathlib / Lean tactics |
| Neural proof search | Usually no | BFS-Prover-V2 / Seed-Prover / other Lean provers |
| Conjecture-generation baseline | Compare, do not blindly rebuild | LeanConjecturer and related work |
| Long-horizon research memory | Yes | Gareen |
| Research agenda selection | Yes | Gareen |
| Failure analysis across campaigns | Yes | Gareen |
| Interestingness / novelty / reuse scoring | Yes | Gareen |
| Dependency-impact analysis | Yes | Gareen |
| Concept / definition proposal | Yes, experimentally | Gareen |
| Multi-prover orchestration | Yes | Gareen |
| Auditable research notebook | Yes | Gareen |

## Near-term integration order

### 1. Native Lean/Mathlib baseline

Status: implemented in Phases 12–14.

Purpose:

- stable trust boundary;
- deterministic verification;
- inexpensive baseline tactics;
- direct access to Mathlib.

### 2. BFS-Prover-V2 evaluation

Why:

- open-source Lean prover;
- explicit proof-search implementation;
- local-model option;
- planner + prover architecture is relevant to Gareen.

Do not vendor or fork immediately. First build a thin backend adapter and benchmark
it against native Mathlib tactics on the same Gareen-generated conjectures.

### 3. Discover-and-Prove evaluation

Why:

- separates discovery/reasoning from formal proving;
- architecturally close to Gareen's research/prover separation;
- useful comparison for hard-mode problem solving.

Gareen's differentiator should remain long-horizon theory growth rather than
single-problem natural-language answer discovery.

### 4. Seed-Prover evaluation

Why:

- very strong Lean proving;
- long-running multi-agent inference;
- conjecture/lemma pools in heavy mode.

This is an especially important benchmark because it overlaps substantially with
Gareen's lemma-pool and long-horizon ambitions. We should not claim novelty in
those areas without a direct comparison.

### 5. LeanConjecturer comparison

Compare:

- number of generated conjectures;
- proof rate;
- nontriviality;
- duplicate rate;
- dependency impact;
- downstream usefulness.

## Fork policy

Do **not** fork a large project merely because it is powerful.

Fork only when:

- the upstream architecture blocks a necessary Gareen experiment;
- a small adapter cannot expose the required functionality;
- the license permits the intended work;
- we can maintain the fork.

Otherwise use the upstream project as a backend.

## Gareen's intended research question

The project should increasingly focus on:

> Can an autonomous research system choose useful mathematical directions,
> grow a Lean-verified theory over long horizons, learn from failed research
> attempts, and invent reusable concepts/lemmas with minimal human guidance?

That question is different from:

> Can we build another theorem prover?

The second question is no longer Gareen's goal.


## Phase 19.1 — feedback-aware proof orchestration

The repaired Phase 19 ecosystem diagnostic changed the interpretation of the
earlier failures. Once the Lean/Mathlib/lean-auto integration path was fixed,
the ecosystem-only five-medium benchmark moved from an invalid apparent 0/5 to
a reproducible 4/5 result:

| Goal | Result | Winner |
| --- | --- | --- |
| Nat monotone addition | verified | `grind` |
| Int quadratic identity | verified | `grind` |
| consecutive gcd | verified | `aesop` |
| common divisor divides a sum | unproved by one-shot ecosystem tactics | none |
| propositional implication chain | verified | `grind` |

This demonstrates that the previous all-strategy failure was an integration
failure rather than evidence that the standard tactics were ineffective.

The remaining divisibility goal is especially valuable:

```text
∀ d a b : Nat, d ∣ a → d ∣ b → d ∣ a + b
```

One-shot tactics did not close the theorem, but Lean retrieval tools produced
useful proof suggestions and identified relevant Mathlib declarations such as
`Nat.dvd_add_iff_right`. In one run, the generated candidate did not type-check
without further repair. Gareen's recursive fallback could nevertheless prove the
same theorem. This exposes a concrete orchestration gap rather than a missing
mathematical fact.

### New Gareen value proposition

The important research contribution is no longer merely "run many tactics".
It is:

> consume partial proof information from one solver, transform it into the next
> proof state/candidate, retry it, and continue across complementary solvers
> until Lean kernel verification succeeds or the bounded search is exhausted.

This turns the prover ecosystem into a cooperative proof process.

### Feedback loop architecture

The first implementation now lives in `lean_proof_planner.py`:

```text
goal
  -> exact?/apply? retrieval
  -> parse "Try this" suggestions
  -> replace the next retrieval checkpoint
  -> generate small generic repair variants
  -> retry with Lean
  -> consume any new suggestions
  -> repeat for a bounded number of rounds
  -> kernel/type-check acceptance
```

The current generic repair layer includes:
- parsing Lean `Try this:` output;
- extracting referenced Mathlib constants;
- preserving indentation while replacing the next `exact?`/`apply?` checkpoint;
- retrying the suggested proof;
- trying a generic `simpa using (...)` variant for `exact` suggestions;
- repeating suggestion -> repair -> retry for a bounded number of rounds;
- preserving all attempts for audit/debugging.

The feedback planner is inserted between the one-shot ecosystem tactic cascade
and Gareen's advanced+legacy recursive portfolio.

Therefore the current orchestration order is:

```text
Goal
  -> one-shot Lean/Mathlib/lean-auto tactics
  -> Lean suggestion feedback/repair loop
  -> Gareen advanced recursive engine
  -> Gareen legacy recursive engine
  -> Lean verification boundary
```

This is deliberately generic. No theorem-specific lemma was hard-coded for the
divisibility benchmark.

### Failure semantics

Phase 19.1 also distinguishes:
- `SUCCESS`
- `TACTIC_FAILED`
- `LEAN_COMPILE_ERROR`
- `IMPORT_ERROR`
- `TIMEOUT`
- `AUDIT_REJECTED`
- `INFRASTRUCTURE_ERROR`

An unproved theorem must not be confused with broken proof infrastructure.

### Validation target

The immediate validation target is the previously missed divisibility theorem.
A successful feedback-loop proof would demonstrate a capability that neither a
single one-shot ecosystem tactic nor a simple sequential tactic runner provided:
Gareen would have used solver feedback as an intermediate mathematical state and
continued the proof process.

Even if that first target still requires additional repair rules, the design
establishes the reusable feedback channel needed for later subgoal routing,
lemma-signature inspection, proof-state exchange, and cross-prover orchestration.
