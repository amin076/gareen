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
