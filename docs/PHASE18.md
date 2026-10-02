# Phase 18 — bounded recursive proof planning

## Problem and scope

Phase 17 could retrieve a theorem or split `d ∣ x + y` using a handwritten
schema. Phase 18 obtains subgoals from the actual premises of retrieved Lean
theorems. It contains no gcd/divisibility lemma names or arithmetic templates.
It is a bounded symbolic planner, not an LLM, a new kernel, or a claim of novel
mathematics.

## Search and trust boundary

`Gareen/RecursivePlanner.lean` runs inside Lean. At each goal it introduces
binders, tries local hypotheses and reflexivity, and queries Lean 4.34.1's
indexed `LibrarySearch.libSearchFindDecls`. Lean unification and `MVarId.apply`
match theorem conclusions and create premises as metavariable goals, including
implicit parameters and typeclass obligations. Both directions of indexed iff
lemmas are supported.

Inductive constructors are retrieved generically from the target type.
Applicable candidates are ranked by number of premises, preference for
constructors, a penalty for non-shrinking printed subgoals and data witness
goals, and prior successful use. Printed size is only a heuristic, not a
termination argument. A bounded ranked depth-first search
backtracks over the **whole remaining agenda**, restoring the complete
metavariable context when a branch fails. This matters when sibling goals
share an existential witness. This is not global best-first search. Ancestor
checks, depth, total expansion/application budget, candidate width, Lean
heartbeats and a subprocess wall-clock timeout bound the search.

The search must close every goal. It rejects remaining metavariables and
`sorry` terms. Python additionally checks the compiler exit status and
`#print axioms`, admitting only Lean's standard `propext`, `Classical.choice`
and `Quot.sound` dependencies (or no axioms). Missing audit output never counts
as proof. Search failure and timeout mean unproved, never false.

## Integration and memory

`recursive_proof_planner.py` is the Phase 18 entry point. The number-theory
frontier uses it by default. The Phase 17 class remains unchanged as a baseline
and for its original before/after experiment.

For every attempt, the emitted Lean source and a JSON report are retained under
`.gareen/planner_candidates`. Reports contain the actual goal/rule graph with
parent IDs, failed alternatives, accepted choices, node counts, timing and
compiler diagnostics. Only fully verified proofs teach persistent lemma-use
ranking in `.gareen/proof-memory.json`. Proof metadata points at the retained
source and trace. Memory does not bypass verification and does not import new
axioms. The current memory favors previously useful rules; it does not yet
compile earlier discoveries into a growing imported Lean theorem library.

## Reproduce

```bash
lake build
python -m unittest discover -s tests -v
python recursive_proof_planner.py --statement '∀ a b : Nat, Nat.gcd a b ∣ a + b'
python experiments/recursive_benchmark.py --seconds 1600 --per-goal 25 --baseline-limit 10
```

The fixed ladder has 50 distinct positive goals in five workload groups:
routine, library lookup, composition, logic/branching, and challenge. These are
workload groups, not certified minimum proof depths or novelty levels. Three
false controls are separate from the success-rate denominator. The first ten
interleaved problems are also run with Phase 17 under the same maximum
per-goal time. Timing can depend on CI hardware and Mathlib startup. Reports
record exactly which comparisons ran; unattempted goals are never failures.

A successful CI gate requires all goals to be attempted, healthy controls, and
success on the original gcd sum, nested gcd sum and a propositional conjunction.
Challenge goals may remain unproved and are reported honestly. Benchmark memory
is isolated for each run, but learns between successive Phase 18 goals. Phase
17 has no persistent ranking memory; this distinction is part of the comparison.

## Boundaries

- This is retrieval and recursive composition, not autonomous lemma invention.
- No induction/case-split strategy synthesis or model-guided ranking is added.
- Indexed lookup plus finite candidate/depth limits is incomplete.
- Cycles are checked along ancestors; no global negative cache is used because
  assumptions and metavariable assignments can change a goal's solvability.
- Saving proof artifacts is not evidence that those proofs are mathematically
  new. Research-value filtering remains a separate layer.
- Persistent files are local to an execution workspace; copy them deliberately
  when moving a campaign. Benchmark artifacts are uploaded by GitHub Actions.


## Phase 18 search-regression finding

The strongest current Phase 18 run verified 47/50 fixed benchmark goals with all false controls sound and terminating. This improvement exposed an important regression: three goals that had succeeded in earlier Phase 18 runs became unproved after context-aware ranking changes.

A focused probe raised the search envelope to depth 8, 10,000 nodes, 96 candidates, and a shared 20-minute budget. All three still exhausted 10,000 nodes. The search itself used roughly 98 seconds in total. This is evidence of search-direction instability rather than a simple wall-clock shortage.

The current diagnosis is that the local-premise bonus is useful but can over-rank a theorem application that closes one premise while leaving a harder residual obligation. For example, a transitivity route may close `gcd(a,b) ∣ b` immediately yet leave the strategically poor subgoal `b ∣ b+a`, outranking a direct additive decomposition whose two premises are both simple gcd facts.

The next ranking change should therefore preserve the local-premise bonus but add a residual-progress penalty/value estimate. The design and literature review are recorded in `docs/GAREEN_DEVELOPMENT_BOOK.md`.

No search-policy fix for this finding should be considered complete unless it is tested against:
- the full 50-goal benchmark,
- the permanent three-goal regression set,
- node/time cost,
- and false controls.
