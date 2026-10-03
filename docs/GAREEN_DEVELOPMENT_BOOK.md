# Gareen Development Book

## Purpose

This document is the long-form engineering and research record of Gareen. It is intentionally more detailed than the README. The goal is to preserve not only what worked, but also what failed, why design decisions changed, what evidence supported those decisions, and which open questions remain.

The central research question is:

> Can a machine autonomously grow useful formal mathematical knowledge while every accepted result remains explicitly derivable, auditable, and kernel-checked?

A second question emerged during Phase 18:

> How should a theorem prover decide whether a search branch is making meaningful progress, deserves more resources, or should be abandoned in favor of alternatives?

That second question is now central to Gareen's future search architecture.

---

# Part I — Origins: explicit symbolic mathematics

## Phase 1 — Symbolic arithmetic core

### Goal
Start with the smallest possible formal world and make the separation between host computation and mathematical knowledge explicit.

### Object language
- `0`
- `S(x)`
- `Add(a,b)`

### Rewrite rules
- `Add(a,0) -> a`
- `Add(a,S(b)) -> S(Add(a,b))`

### What was learned
A host language such as Python can execute the machinery, but object-level mathematical knowledge must not be silently imported from Python arithmetic. A derivation only counts if it can be traced to declared object-world rules.

### Boundary
No theorem discovery, no proof search, no Lean, no agents.

---

## Phase 2 — Formal primitives, definitions, and axioms

### Goal
Turn the symbolic calculator into an explicit formal system.

### Added distinctions
- arithmetic primitives
- logical primitives
- definitions
- axioms

### Arithmetic primitives
- zero
- successor
- addition

### Logical primitive
- equality

### Definitions
Numerals such as 1, 2, 3 became definitions in terms of successor rather than independent primitives.

### Axioms
- successor is nonzero
- successor is injective
- recursive addition base case
- recursive addition successor case

### Lesson
Representation matters. Gareen should distinguish what is primitive, what is defined, and what is assumed.

---

## Phase 3 — Auditable proof engine and knowledge growth

### Goal
Move from rewriting to derived mathematical knowledge.

### Added
- theorem objects
- proof steps
- inference rules
- proof checker
- theorem dependencies
- verified knowledge state

### First important transition
Gareen began to store results that were derived, not merely supplied.

Examples included:
- `1 != 0`
- `1 != 2`
- `2 != 3`
- `2 + 0 = 2`

The dependency graph began to matter because later theorems reused earlier verified theorems.

### Lesson
Knowledge growth must be dependency-aware. A theorem is useful not merely because it is true, but because it can become infrastructure for later proofs.

---

## Phase 4 — Induction and the first genuinely general theorem

### Goal
Move beyond finite examples.

### Added
- induction
- equality congruence
- equality transitivity

### Milestone
Gareen proved:

`forall x, Add(0,x)=x`

This was not an axiom. It was derived by induction.

### Lesson
A proof system becomes qualitatively more useful when it can generalize over infinitely many cases rather than only verify concrete examples.

---

## Phase 5 — Addition commutativity

### Goal
Use induction and helper results to prove a structurally stronger theorem.

### Milestone
Derived addition commutativity rather than adding it as an axiom.

### Lesson
Intermediate lemmas are not optional decoration. They are often the bridge between a theorem that is easy to state and a theorem that is feasible to prove.

---

## Phase 6 — Associativity and recursive multiplication

### Added
- addition associativity
- multiplication as a primitive operation
- recursive multiplication axioms
- additional equality congruence support
- variable-capture safety for universal instantiation

### Lesson
Formal correctness requires protecting the proof system from subtle variable-binding errors, not only proving arithmetic identities.

---

## Phase 7 — Core multiplication laws

### Goal
Grow the small theorem library enough to support increasingly compositional proofs.

### Outcome
The manually built theorem library reached the T1–T14 range and included basic addition and multiplication laws.

### Lesson
A theorem library can become a scaffold for autonomous search, but manually authored theorem chains are not themselves autonomous mathematics.

---

# Part II — Search and autonomous conjecturing

## Phase 8 — Automatic proof search

### Goal
Stop requiring every proof to be handwritten.

### Added
Automatic search for small ground goals using the existing proof system.

### Lesson
Once search is introduced, the problem changes. Correctness remains necessary, but search efficiency becomes a separate engineering problem.

---

## Phase 9 — Autonomous theorem search

### Goal
Generate candidate statements and attempt to verify them automatically.

### Reported experiment
A candidate pool was generated and a subset was verified, including simple results such as `1 + 1 = 2`.

### Lesson
Generating many true statements is easy compared with generating mathematically valuable statements.

---

## Phase 10 — General conjecture discovery

### Goal
Move from isolated numeric examples to patterns and general statements.

### Added
Pattern-based conjecture generalization.

### Lesson
Examples can support conjecture generation, but examples are not proofs and should not be confused with durable mathematical knowledge.

---

## Phase 11 — Artificial Mathematician prototype

### Goal
Coordinate:
- conjecture generation
- strategy selection
- induction synthesis
- helper-lemma proposals
- verification
- research notebook/memory

The demo deliberately started from axioms rather than loading the full handwritten theorem library.

### Lesson
The project was beginning to separate:
1. the trusted verifier,
2. the search/research layer,
3. the knowledge/memory layer.

That separation later became the basis of Architecture V2.

---

# Part III — Lean/Mathlib becomes the trusted foundation

## Phases 12–14 — Lean transformation

### Problem
Growing a custom Python proof checker toward full theorem-prover capability would duplicate decades of work already available in Lean and Mathlib.

### Decision
Lean 4 + Mathlib became the trusted formal foundation.

Python remained responsible for:
- conjecture generation
- pattern mining
- strategy proposals
- ranking
- memory
- experimentation
- future concept invention

Lean became responsible for:
- elaboration
- theorem verification
- kernel trust

### Architecture

```text
Python research/orchestration
        |
        v
Python -> Lean bridge
        |
        v
Lean 4 + Mathlib
        |
        v
Lean kernel
        |
        v
verified knowledge
```

### Lesson
Gareen should not reinvent the proof assistant. Its research value should come from how it chooses what to investigate and how it navigates proof search.

---

# Part IV — Throughput, value, and number theory

## Phase 15 — Throughput and proof-soundness hardening

### Problem
A roughly 15-minute autonomous campaign generated far more conjectures than the bridge could efficiently verify. Repeated Lean startup became a major bottleneck.

An early run generated about 1,361 conjectures, checked only 59, and proved 3 within the available run. Later batching dramatically increased throughput; a later report verified 981 out of 1,361 checked candidates in roughly 552 seconds. Those 981 were explicitly not claimed to be 981 new mathematical discoveries.

### Added
- batch Lean verification
- shared wall-clock budgets
- distinction between:
  - verified
  - unproved-in-budget
  - not-attempted
- candidate diversification
- routine-expression deprioritization
- process and timing metrics
- induction-dependency soundness fixes
- false controls

### Lesson
Throughput matters, but raw verified-count is not a research-value metric.

---

## Phase 16 — Mathematical research value and number-theory frontier

### Problem
The system could verify many true but routine identities.

### Added research-value filtering
Candidates were down-ranked when they were:
- ground numerical examples
- primitive rewrite consequences
- very close to already known theorems

The score rewarded:
- generality
- compression of existing knowledge
- reuse potential
- structural richness
- distance from known results

### Number-theory vocabulary
Gareen began using Mathlib's mature concepts rather than reimplementing them:
- divisibility
- quotient
- remainder
- gcd
- coprimality
- primality

### Lesson
The bottleneck was shifting from "can Lean verify this?" toward:
- what should Gareen try?
- what is mathematically interesting?
- which library knowledge is relevant?

---

# Part V — Retrieval and multi-step proof planning

## Phase 17 — Mathlib theorem retrieval and structured planning

### Triggering failure
The theorem

`forall a b : Nat, Nat.gcd a b divides a + b`

was simple mathematically but generic tactic search failed.

The problem was not that Mathlib lacked the knowledge. The needed facts already existed:
- gcd divides the left argument
- gcd divides the right argument
- a common divisor divides a sum

The missing capability was retrieval plus composition.

### Added
- Lean `exact?`-style theorem retrieval
- variable introduction
- a structured divisibility-over-addition decomposition
- theorem composition
- a reproducible before/after GCD benchmark

### Milestone
The previously failed GCD theorem became provable.

### Limitation
The planner still used a handwritten decomposition schema for one arithmetic shape. It did not yet recursively derive arbitrary subgoals from retrieved theorem premises.

### Lesson
Library knowledge is only useful when the search system can retrieve and compose it.

---

# Part VI — Phase 18: recursive proof search

## Phase 18 — Bounded recursive theorem retrieval and proof search

### Core idea
Instead of decomposing only one handwritten arithmetic form, let Lean retrieve applicable theorems and use their premises as recursive subgoals.

### Added
- bounded recursive backward search
- theorem application through Lean unification
- subgoal generation from theorem premises
- ranked alternatives
- full backtracking
- whole-agenda backtracking for shared metavariables
- maximum depth
- maximum node count
- candidate-width limit
- proof graph/event trace
- persistent theorem-use memory as a ranking hint
- kernel verification and axiom audit
- false controls
- fixed 50-goal benchmark

### Trust rule
Search failure means only "unproved in the current budget." It never means the theorem is false.

---

## Phase 18 benchmark history

### Initial full run
- 50 attempted
- 38 verified
- 76% success
- paired Phase 17 comparison: 5/10 vs Phase 18 10/10
- false-control handling exposed a timeout classification issue

### First ranking improvement
The planner began rewarding structural/local progress and weakening the influence of persistent memory.

A successful run reached:
- 45/50
- 90%
- controls healthy
- paired comparison 5/10 vs 9/10

### Context-aware ranking improvement
A regression test showed that divisibility transitivity could be missed because theorem application created shared metavariables. The ranking logic was extended so generated premises that can be discharged from local assumptions receive a strong bonus. Lean's definitional equality can instantiate shared metavariables while closing those premises.

The next full run reached:
- 47/50
- 94%
- controls sound
- controls terminated
- all workflow stages green
- paired comparison 5/10 vs 9/10

This was a major improvement, but it exposed a new search regression.

---

# Part VII — The Phase 18 ranking regression

## The three unstable goals

The final 47/50 run failed on:
- `composition_01`: `forall a b, gcd(a,b) divides b+a`
- `composition_04`: `forall a b, gcd(a,b) divides (a+b)+(b+a)`
- `logic_and_branching_07`: conjunction of the two symmetric gcd-sum goals

These goals had been solved in earlier Phase 18 runs.

A focused diagnostic run increased the envelope to:
- depth 8
- 10,000 nodes
- 96 candidates
- up to about 400 seconds per goal
- 20-minute shared budget

All three still failed at exactly 10,000 nodes. The three searches themselves used about 98 seconds total.

### Conclusion
The issue is not simply insufficient wall-clock time. It is search-direction instability.

---

## Root cause

The latest ranking improvement strongly rewards an applicable theorem when one or more of its generated premises can be immediately closed from the local context.

That is often excellent. For example, in a true transitivity goal:

```text
a divides b
b divides c
-----------
a divides c
```

a transitivity theorem generates premises that are already available, so it should be ranked very highly.

But the same heuristic can mislead the search.

For:

```text
gcd(a,b) divides b+a
```

a transitivity theorem may generate:

```text
gcd(a,b) divides b
b divides b+a
```

The first premise closes immediately, so the branch receives a large local-premise bonus. But the second premise is not genuine progress; it is generally harder and may push the prover toward another difficult or false-looking obligation such as `b divides a`.

The direct additive route is better:

```text
gcd(a,b) divides b
gcd(a,b) divides a
--------------------
gcd(a,b) divides b+a
```

The current heuristic notices "one premise closed" more strongly than it notices "the remaining premise is structurally worse."

### Key lesson
A local-premise bonus is valuable but insufficient. Search ranking must combine immediate success with a measure of residual difficulty.

---

# Part VIII — Research question: what does "progress" mean in proof search?

## Why this problem is fundamental

Theorem proving has enormous branching factors. Many branches are logically valid applications of theorems but strategically poor.

The central decision is:

> Should the prover spend more resources on the current branch, or should it backtrack and explore another branch?

This cannot be answered from elapsed time alone.

A branch may be:
- temporarily difficult but ultimately successful,
- permanently unproductive,
- cyclic,
- generating increasingly complex subgoals,
- making real progress hidden behind a difficult intermediate lemma,
- or repeatedly creating obligations farther from known facts.

Therefore Gareen needs an explicit notion of search-state value or progress.

---

# Part IX — What prior theorem-proving research says

## 1. Learning-guided automated reasoning

Modern automated reasoning literature treats combinatorial explosion as a central practical problem. Search systems contain many heuristic choice points, and learned predictors can guide premise selection and proof search.

Reference:
- L. Blaauwbroek et al., "Learning Guided Automated Reasoning: A Brief Survey", arXiv:2403.04017

Relevance to Gareen:
The current Phase 18 heuristic is a hand-engineered value function. The literature strongly supports the idea that proof search quality depends on predicting which choices are promising.

---

## 2. Premise retrieval — LeanDojo / ReProver

LeanDojo identifies premise selection as a major bottleneck and uses retrieval to choose useful library facts before proof generation.

Reference:
- Kaiyu Yang et al., "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models", arXiv:2306.15626

Relevance:
Gareen Phase 17 already rediscovered the importance of retrieval. Phase 18 now shows that retrieval alone is not enough: after retrieving applicable theorems, the system must rank their induced subgoals intelligently.

---

## 3. TacticToe — learned guidance + Monte Carlo tree search

TacticToe learns which tactics are appropriate in a proof state and uses Monte Carlo tree search to explore promising paths.

Reference:
- Thibault Gauthier et al., "TacticToe: Learning to Prove with Tactics", arXiv:1804.00596

Relevance:
This directly addresses the same question Gareen now faces: not all legal proof actions deserve equal search resources.

---

## 4. TacticZero — reinforcement learning and explicit backtracking

TacticZero models proof search as a sequential decision process and learns both tactic choice and when to abandon poor derivations.

Reference:
- Minchao Wu et al., "TacticZero: Learning to Prove Theorems from Scratch with Deep Reinforcement Learning", arXiv:2102.09756

Relevance:
Gareen's current backtracking is rule-based. A future learned policy/value model could estimate whether a state is likely to lead to a proof.

---

## 5. HyperTree Proof Search

HTPS uses an AlphaZero-inspired search process and online learning from previous proof searches.

Reference:
- Guillaume Lample et al., "HyperTree Proof Search for Neural Theorem Proving", arXiv:2205.11491

Important result:
The method learns from both successful and unsuccessful searches and uses search feedback to improve future guidance.

Relevance:
This is close to Gareen's long-term direction: proof traces should become training/evidence for later ranking, not merely logs.

---

## 6. DeepSeek-Prover-V1.5 / RMaxTS

DeepSeek-Prover-V1.5 combines proof-assistant feedback, reinforcement learning, and a Monte Carlo tree-search variant with intrinsic exploration reward.

Reference:
- Huajian Xin et al., "DeepSeek-Prover-V1.5", arXiv:2408.08152

Relevance:
This supports balancing exploitation of promising branches with exploration of alternatives. Gareen should not deterministically commit too much budget to the first apparently good branch.

---

## 7. Best-First Search remains competitive

BFS-Prover reports that carefully designed best-first search can be highly competitive, especially when the search score is trained to prefer productive state/tactic transitions.

Reference:
- Ran Xin et al., "BFS-Prover: Scalable Best-First Tree Search for LLM-based Automatic Theorem Proving", arXiv:2502.03438

Relevance:
Gareen does not necessarily need to jump immediately to a large neural MCTS system. A stronger best-first search with a better state-value function is a realistic intermediate step.

---

# Part X — A proposed Gareen definition of progress

This section is a research design proposal, not yet an implemented Phase 18 change.

A branch should not be ranked by one signal. It should receive a multi-component progress score.

For a transition from goal state `G` to residual subgoals `S1...Sk`, useful signals include:

## 1. Immediate closure
How many premises were solved immediately by:
- local assumptions
- reflexivity
- known verified facts

This is the useful Phase 18 local-premise bonus and should be retained.

## 2. Residual-goal complexity
Estimate whether the remaining subgoals are structurally simpler or harder than the parent.

Possible features:
- expression-tree size
- number of logical connectives
- number of quantifiers
- number of unresolved metavariables
- number of distinct variables
- depth of syntax tree
- number of algebraic operators
- whether a new predicate/relation was introduced
- whether terms became larger

## 3. Distance to known knowledge
Measure whether residual goals are closer to:
- local assumptions
- already verified Gareen theorems
- retrieved Mathlib declarations
- previously solved proof states

## 4. Novel obligation penalty
Penalize a branch if theorem application introduces a qualitatively new relation that was not present in the parent goal and is not immediately supported by local knowledge.

Example:
`gcd(a,b) divides b+a` -> `b divides b+a`

The latter removes gcd but introduces a stronger divisibility obligation involving `b`, which is not automatically progress.

## 5. Stagnation
Track progress over several consecutive expansions.

A branch should lose priority if:
- residual complexity does not fall,
- known-distance does not improve,
- the same structural pattern repeats,
- node use rises without new closures.

This is better than declaring a branch dead after a fixed number of nodes.

## 6. Cycle / near-cycle detection
Exact ancestor equality already helps, but structural near-cycles should also be detected.

## 7. Branch diversity
Do not spend the entire budget on one family of nearly identical theorem applications.

Reserve some budget for alternative proof shapes.

## 8. Historical branch success
Persistent memory should record not only theorem names but context-sensitive statistics:
- theorem used successfully for what goal shape?
- how many nodes did the resulting proof require?
- did this rule frequently create dead branches?
- what residual-goal patterns followed?

A global theorem popularity score is too coarse.

---

# Part XI — A practical decision policy

A practical next search policy for Gareen could be:

```text
score(branch) =
    strong bonus for all premises closed
  + bonus for each locally closed premise
  + bonus for reduction in residual complexity
  + bonus for closeness to known facts
  + weak context-specific historical bonus
  - penalty for harder residual subgoals
  - penalty for new unsupported predicates/relations
  - penalty for stagnation
  - penalty for repeated structural patterns
  - penalty for excessive branching
```

Then use best-first or multi-queue search instead of pure depth-first commitment.

A branch should receive additional budget when its score continues improving. It should be suspended, not permanently destroyed, when progress stalls. Suspended branches can be revisited if all higher-value alternatives fail.

This avoids the dangerous false choice:
- either search forever,
- or permanently abandon a branch too early.

The correct abstraction is resource scheduling among competing branches.

---

# Part XII — What can and cannot be predicted

## What can be predicted
We can estimate:
- probability that a branch will eventually close
- expected remaining proof cost
- whether recent expansions are improving the state
- whether a tactic/theorem is historically productive for similar goal shapes

## What cannot be guaranteed
For general theorem proving, there is no practical universal procedure that can always know in advance whether a branch will eventually produce a proof within finite resources.

Therefore Gareen should treat "progress prediction" as a calibrated heuristic estimate, not a logical truth.

This is not a circular definition. Progress can be grounded in observable state features and empirical outcomes:
- subgoal complexity
- closure count
- known-fact distance
- repeated patterns
- historical success
- nodes/time spent

Those measurable signals can predict future success without defining progress as "whatever eventually succeeds."

---

# Part XIII — Experimental protocol going forward

Any future search-ranking change should be evaluated on at least four dimensions:

1. total benchmark success rate
2. regressions: previously solved goals that become unsolved
3. search cost: nodes/time per solved goal
4. soundness controls

Additionally, Gareen should maintain a permanent "regression corpus" containing:
- goals newly solved by each phase
- goals that once regressed
- false controls
- representative easy, medium, and hard goals

A new heuristic should not be accepted only because the overall percentage rises.

The Phase 18 three-goal regression demonstrates why.

---

# Part XIV — Current open questions

1. How should residual proof-state complexity be measured?
2. Should Gareen use best-first search rather than ranked DFS?
3. Should branch budgets be adaptive rather than fixed?
4. Should theorem-memory scores be goal-shape specific?
5. How should near-cycles and semantic stagnation be detected?
6. Can proof traces train a lightweight value model before introducing a large neural prover?
7. When should Gareen invent an intermediate lemma instead of continuing direct search?
8. How should induction and case-split planning integrate with the same progress/value framework?
9. How can search-value estimates remain interpretable and auditable?

---

# Part XV — Current conclusion

Phase 18 is a success in capability but not yet a finished search architecture.

The evidence is deliberately mixed:
- large improvement in total solved goals
- healthy false controls
- successful recursive theorem retrieval and backtracking
- major reductions in node count on many goals
- but also a real regression where three previously solved goals became trapped in a bad search region

The correct lesson is not to discard Phase 18. The correct lesson is to preserve the useful local-premise signal while adding a broader concept of residual progress and resource allocation.

The next major architectural idea is therefore:

> Gareen should move from "rank theorem applications" toward "estimate the value of proof states and allocate search resources dynamically."

This is consistent with major directions in modern automated theorem proving, while remaining implementable incrementally and auditable inside Gareen.


---

# Part XVI — Phase 18.5: from single-engine tuning to a proof-search portfolio

## Why Phase 18.5 was necessary

Phase 18 reached a strong 47/50 result, but repeated heuristic tuning revealed a structural problem: a ranking change could recover one family of proofs while regressing another family that had previously been solved.

The most important example was the three-goal regression:
- `composition_01`
- `composition_04`
- `logic_and_branching_07`

A context-aware local-premise bonus improved many goals, but it over-ranked transitivity-style branches because one generated premise could close immediately while another sibling premise was strategically poor.

A focused 10,000-node probe confirmed that simply increasing time or nodes did not solve the problem.

## Failed experiment: relation-prefix progress

A first Phase 18.5 attempt tried rewarding residual goals that preserved the same head relation while simplifying the final argument.

This looked plausible but was too syntactic and over-general. It regressed the search from 2/3 recovered goals back to 0/3:
- `composition_01`: 10,000 nodes, unproved
- `composition_04`: unproved
- `logic_and_branching_07`: 10,000 nodes, unproved

Lesson: structural similarity by itself is not a reliable proxy for proof-state value.

## Failed experiment: iterative deepening alone

The next experiment kept the better ranking and added iterative-deepening resource scheduling.

Results:
- `composition_01`: solved at depth 2, 147 nodes
- `logic_and_branching_07`: solved at depth 3, 343 nodes
- `composition_04`: failed at depths 2, 3, 4, 5, and 6, including a 5,000-node attempt

Conclusion: the remaining problem was not only DFS depth commitment. Candidate ordering at shallow depth was still wrong.

## Root-ranking diagnostic

A diagnostic mode recorded the top 20 root candidates and their scores without changing proof semantics.

For `composition_04` before the fix:

```text
1. Nat.dvd_trans            score 2
2. Nat.ModEq.dvd_iff.mp     score 10
3. Nat.ModEq.dvd_iff.mpr    score 10
4. Nat.dvd_add              score 10
```

The bad `Nat.dvd_trans` branch created:
- `gcd(a,b) ∣ b`
- `b ∣ (a+b)+(b+a)`

The first child was easy, so the local/direct-closure bonuses made the whole branch look excellent even though the second child was strategically poor.

The direct additive decomposition was much better:
- `gcd(a,b) ∣ a+b`
- `gcd(a,b) ∣ b+a`

## Successful scoring fix: mixed easy/hard residual penalty

The advanced planner was changed so a state with some directly closable residual goals and some unsupported residual siblings receives a penalty after the direct-closure bonus.

This is generic; it does not hard-code `Nat.dvd_trans` or any gcd theorem.

After the change, the root ranking became:

```text
1. Nat.dvd_add              score 10
6. Nat.dvd_trans            score 22
7. Nat.ModEq.dvd_iff.mp     score 24
8. Nat.ModEq.dvd_iff.mpr    score 24
```

The focused three-goal probe then reached 3/3:
- `composition_01`: 291 nodes
- `composition_04`: 679 nodes
- `logic_and_branching_07`: 647 nodes

The permanent Lean regression suite also passed.

## Full benchmark after the fix

The full 50-goal run again verified 47/50. Importantly, the previous three regressions were recovered, including `composition_04` at 343 nodes.

The three positive failures had changed:
- `logic_and_branching_00`: timeout, 0 search nodes
- `composition_02`: timeout, 0 search nodes
- `composition_03`: unproved at 1,200 nodes

False controls remained sound, but one false control timed out before clean search termination:
- `∀ n : Nat, n + 1 = n`: timeout, 0 search nodes

So the workflow failed because `controls_terminated = false`, not because a false theorem was proved.

This revealed a second tension: the stronger residual lookahead can be expensive before normal search emits nodes.

## Architectural decision: stop forcing one heuristic to dominate every goal

At this point repeated single-engine tuning had produced a cycle:

1. improve one family of goals,
2. regress another family,
3. change scoring again,
4. recover the regression but expose another cost or ranking issue.

The project therefore adopted a new Phase 18.5 architecture:

> Use a portfolio of complementary proof-search engines instead of forcing one ranking policy to be best on every theorem.

The first portfolio contains two engines:

### Engine A — Advanced recursive planner

Uses the latest residual-lookahead and mixed easy/hard penalty.

Strengths demonstrated by experiment:
- `composition_04`
- `logic_and_branching_07`
- many routine/library/composition goals

### Engine B — Frozen legacy recursive planner

A frozen snapshot of the last stable Phase 18 planner before the newer residual-lookahead changes.

The legacy engine is intentionally not tuned further. Its purpose is to preserve a different search bias and act as a regression safety net.

### Cascade policy

```text
goal
  -> Advanced engine
       -> if verified: return proof
       -> otherwise: Legacy engine
            -> if verified: return proof
            -> otherwise: report unproved
```

This is currently sequential rather than truly parallel so successful advanced proofs avoid unnecessary second-engine cost.

Every accepted proof is still checked by Lean and the same axiom audit. Portfolio fallback changes search strategy, not the trust boundary.

## First five-goal portfolio experiment

A first implementation attempt produced only 3/5 because the frozen legacy module existed but was not exposed through the main Lean foundation, so fallback candidates could not execute correctly. This was an integration failure, not evidence against the portfolio idea.

The legacy module was then imported into `Gareen.lean`, and the five-goal experiment was rerun.

Final five-goal result: **5/5 verified** in about 140.7 seconds of test time.

| Goal | Advanced | Legacy fallback | Winner |
|---|---|---|---|
| `logic_and_branching_00` | verified, 49 nodes | not run | advanced |
| `composition_02` | timeout, 0 nodes | verified, 245 nodes | legacy |
| `composition_03` | unproved, 1,200 nodes | verified, 245 nodes | legacy |
| `composition_04` | verified, 343 nodes | not run | advanced |
| `logic_and_branching_07` | verified, 343 nodes | not run | advanced |

This is the first direct evidence that the two engines are genuinely complementary.

## Phase 18.5 decision

The project will now treat proof search as a portfolio/resource-allocation problem.

Immediate policy:
- keep the advanced engine,
- keep a frozen legacy fallback,
- do not delete failed experiments,
- preserve all traces and benchmark evidence,
- prefer small controlled experiments before full 50-goal reruns,
- only enlarge the benchmark after the portfolio demonstrates reliable cross-coverage.

Longer-term possibilities:
- best-first engine,
- iterative-deepening engine,
- learned state-value engine,
- adaptive engine selection from goal features,
- parallel portfolios when compute cost is justified.

The important architectural principle is:

> Different search biases are assets, not necessarily bugs. Gareen should preserve complementary solvers and orchestrate them rather than repeatedly destroying one behavior to optimize another.



## Controlled ten-goal portfolio validation

A ten-goal controlled validation was added after the five-goal success. The set deliberately mixed:
- the three failures from the latest advanced-engine 50-goal run,
- two recent regression recoveries,
- one routine goal,
- one library/transitivity goal,
- one larger composition goal,
- one deeper logic/divisibility goal,
- one challenge goal.

### First ten-goal attempt: failed because the timeout envelope was too tight

The first run used 18 seconds per engine in an attempt to guarantee a sub-10-minute wall-clock result.

This was too aggressive for CI startup/Lean elaboration overhead. Nine of ten goals timed out, most with zero emitted search nodes. Only `library_06` was recovered by the legacy engine.

Observed result:
- portfolio verified: 1/10
- total test time: about 361 seconds
- dominant failure pattern: `timeout, nodes=0`

This was not interpreted as a mathematical/search regression because goals already proven by the same engines in the five-goal test now timed out before normal search began.

### Decision from the failed run

A per-engine wall-clock limit must leave room for Lean process startup, imports, elaboration, retrieval, and proof search. A timeout that is close to the startup cost produces misleading `nodes=0` failures.

The ten-goal test was therefore rerun with the same 25-second per-engine envelope that had produced the successful five-goal result. The workflow itself remains capped at 10 minutes.



### Second ten-goal attempt: successful

The rerun restored a realistic 25-second per-engine budget while retaining the 10-minute workflow cap.

Result: **10/10 verified**.

- Advanced wins: 8
- Legacy recoveries: 2
- Test elapsed time: about 188.8 seconds (~3m 9s)

Detailed results:

| Goal | Advanced | Legacy fallback | Winner |
|---|---|---|---|
| `logic_and_branching_00` | verified, 49 nodes | not run | advanced |
| `composition_02` | unproved, 1,200 nodes | verified, 245 nodes | legacy |
| `composition_03` | unproved, 1,200 nodes | verified, 245 nodes | legacy |
| `composition_04` | verified, 343 nodes | not run | advanced |
| `logic_and_branching_07` | verified, 343 nodes | not run | advanced |
| `routine_07` | verified, 49 nodes | not run | advanced |
| `library_06` | verified, 49 nodes | not run | advanced |
| `composition_09` | verified, 245 nodes | not run | advanced |
| `logic_and_branching_08` | verified, 98 nodes | not run | advanced |
| `challenge_07` | verified, 98 nodes | not run | advanced |

This validates the main portfolio hypothesis on a controlled mixed set:
- the advanced engine retains its new strengths,
- the frozen legacy engine recovers goals the advanced engine still misses,
- the cascade avoids legacy cost when the advanced engine succeeds,
- the combined solver achieves coverage neither engine demonstrated alone on this set.

### Architectural status after the ten-goal test

The two-engine portfolio is now the preferred Phase 18.5 direction.

It should not yet be treated as universal evidence of 100% coverage. The next scale-up, if needed, is the fixed 50-goal benchmark with:
- the same two-engine cascade,
- explicit false controls,
- per-engine timing,
- recovery attribution,
- total wall-clock cost,
- and no deletion of failing cases.

The controlled 10/10 result is sufficient evidence to stop repeatedly retuning a single heuristic before that larger validation.


---

# Part XVII — First post-benchmark frontier theorem

After the Phase 18.5 portfolio reached 50/50 on the fixed benchmark, the next experiment deliberately moved outside the ladder to a slightly harder natural number-theory theorem:

```text
∀ n : Nat, Nat.gcd n (n + 1) = 1
```

This states that every natural number is coprime to its successor.

## Why this theorem was chosen

The fixed benchmark mostly tests direct library facts, divisibility composition, logic/branching, and modest theorem chaining. The new frontier goal changes the shape of the task:
- target is an exact gcd equality rather than only a divisibility fact,
- successful search may need to connect gcd, coprimality, divisibility, and addition,
- the statement was not one of the fixed 50 benchmark goals,
- it remains moderate enough that failure would be diagnostically useful rather than merely reflecting extreme theorem difficulty.

## Result

The two-engine portfolio verified the theorem successfully.

- Winner: advanced engine
- Advanced nodes: 147
- Legacy fallback: not run
- Proof-search time: about 15.49 seconds
- Workflow: success

Accepted Mathlib declarations recorded in the proof trace:
- `Nat.coprime_one_right`
- `Nat.dvd_refl`
- `Nat.coprime_add_iff_right`

The exact proof path is therefore not simply the informal human subtraction argument. Gareen found a coprimality/addition route through Mathlib and converted that route into a kernel-verified proof.

## Interpretation

This is an important transfer result, but it is not evidence that Gareen can yet solve broadly difficult number theory. It shows that the Phase 18.5 search architecture can move beyond the fixed benchmark and solve at least one new theorem requiring a different combination of library concepts.

The next frontier tests should increase difficulty gradually and preserve this protocol:
1. choose a theorem outside the fixed ladder,
2. explain the mathematical meaning before execution,
3. run the portfolio without adding theorem-specific hints,
4. record engine winner, nodes, time, retrieved/accepted declarations, and failure traces,
5. keep both successful and failed results in this development record.


---

# Part XVIII — Phase 19: ecosystem-first proof strategy orchestration

## Strategic change

After Phase 18.5 reached 50/50 on the fixed benchmark, Gareen failed on a harder
frontier theorem:

```text
∀ n : Nat,
  Nat.gcd n (2 * n + 1) = 1 ∧
  Nat.gcd (n + 1) (2 * n + 1) = 1
```

The Phase 17 retrieval baseline failed. The advanced recursive engine timed out
before emitting a search node, and the frozen legacy engine exhausted 5,000
nodes without proof.

A review of Lean and automated-theorem-proving infrastructure showed that many
capabilities Gareen was beginning to redesign already exist as mature
ecosystem components.

This changes the project strategy:

> Gareen should not reimplement generic theorem-proving machinery when a
> maintained, trusted, kernel-checkable implementation already exists.

Gareen will instead become an **ecosystem-first mathematical research and proof
orchestrator**. Custom research should be reserved for gaps that remain after
existing systems have been integrated and measured.

## Existing infrastructure adopted as proof strategies

The first Phase 19 strategy layer directly activates proof procedures already
available in the pinned Lean 4.34.1 + Mathlib environment:

- `grind`
- `aesop`
- `exact? +grind`
- `apply? +grind`
- `simp_all`
- `omega`
- `norm_num`
- `ring`
- `linarith`
- `nlinarith`
- contradiction via `by_contra ...; grind`
- contradiction via `by_contra ...; aesop`
- constructor/conjunction decomposition with `grind`
- constructor/conjunction decomposition with `aesop`
- `exact?`
- `apply?`
- bounded induction variants using simplification, `grind`, and `aesop`

Each strategy is run in an isolated generated Lean file. A strategy counts as a
success only if Lean compiles the proof and the same explicit axiom audit used
by Gareen's recursive engines passes.

The existing Gareen advanced+legacy recursive portfolio remains available as a
fallback strategy. It is no longer treated as the only general-purpose proof
engine.

## Why this is not abandoning Gareen

Mathlib supplies mathematical knowledge. Lean's kernel checks proof terms.
Aesop, grind, omega, arithmetic tactics, and related procedures provide
well-engineered search and domain automation.

Gareen's role moves upward:

- classify goals,
- choose and schedule proof strategies,
- preserve evidence and failures,
- compare strategies empirically,
- share verified intermediate results in later phases,
- learn which strategy works for which goal shape,
- discover auxiliary lemmas,
- run theorem-discovery/research campaigns,
- decide when external provers or neural systems are worth invoking.

This is intentionally analogous to adopting Lean/Mathlib instead of building a
new proof kernel or mathematical library.

## External ecosystem systems

The audit also identified systems that should be integrated when compatible:

- LeanHammer
- lean-auto
- Duper / external ATP pipelines
- Zipperposition
- cvc5 / SMT backends
- neural/retrieval provers such as ReProver/LeanDojo-style systems
- DeepSeek-Prover-class neural search
- BFS-Prover-style learned best-first search

These are **not silently marked active** in Phase 19.0.

The project is currently pinned to Lean 4.34.1. LeanHammer's published
installation instructions currently guarantee stable compatibility only
through Lean 4.32.0. Rather than destabilize the verified Gareen foundation by
downgrading Lean or pretending unsupported compatibility, Phase 19 first
integrates the strategies already native to the current toolchain and records
external systems as explicit adapters/dependencies to evaluate separately.

The rule from this phase onward is:

> Existing ecosystem capability first; Gareen-specific invention only after a
> reproducible gap has been demonstrated.

## Phase 19.0 implementation

`ecosystem_strategy_planner.py` is the first ecosystem strategy orchestrator.

For each theorem it runs bounded, isolated tactic strategies. It records:
- tactic/strategy name,
- verified or failed,
- timeout,
- wall-clock cost,
- generated proof source,
- compiler/audit output.

If no ecosystem strategy succeeds within the configured resource envelope, the
existing two-engine Gareen recursive portfolio is invoked as a fallback.

The first experiment deliberately retests the exact harder theorem that
defeated both previous Gareen engines. This makes the experiment a clean test
of whether ecosystem adoption removes a real custom-search limitation.

## Architectural direction

Phase 19 is not merely a larger sequential list of tactics. The intended
evolution is:

```text
Goal
  ↓
Strategy Orchestrator
  ├─ Lean/Mathlib automation
  ├─ classical contradiction/case strategies
  ├─ arithmetic/domain solvers
  ├─ Gareen recursive portfolio
  ├─ external hammer/ATP adapters
  └─ neural/search provers
         ↓
verified proof checkpoints / shared evidence
         ↓
Lean kernel
```

Later Phase 19 work may add:
- strategy selection by goal features,
- parallel/racing schedules,
- progress-aware resource allocation,
- verified checkpoint sharing,
- proof-state exchange where technically sound,
- context-specific strategy memory.

But those features should reuse existing theory/prover infrastructure wherever
possible rather than recreating it from scratch.


## Phase 19 diagnostic: five medium theorems

Because the first ecosystem-first hard theorem test failed, a separate diagnostic
was run to check whether the new strategy layer was functioning at all or
whether the negative result reflected an integration bug.

The diagnostic deliberately disabled Gareen's recursive fallback and tested
five medium theorems from different proof domains.

Results:

| Goal | Result | Ecosystem winner |
|---|---|---|
| monotone addition over Nat | verified | `grind` |
| quadratic ring identity over Int | verified | `grind` |
| `gcd n (n+1) = 1` | verified | `aesop` |
| common divisor divides a sum | unproved | none |
| propositional implication chain | verified | `grind` |

Overall result: **4/5 verified** by the ecosystem layer alone.

The four successful goals closed quickly:
- arithmetic: ~4.97s
- ring identity: ~4.95s
- consecutive gcd: ~9.92s
- logic chain: ~4.96s

The failed divisibility theorem was:

```text
∀ d a b : Nat, d ∣ a → d ∣ b → d ∣ a + b
```

This theorem is important diagnostically because Gareen's recursive planner had
already solved the same shape in the official Phase 18.5 benchmark. Therefore
the 4/5 result does **not** indicate that the ecosystem integration is broken.
It demonstrates complementarity: native automation is extremely effective on
several domains, while generic premise retrieval/composition can still miss a
simple library theorem under the current search envelope.

For the divisibility theorem:
- `grind` failed quickly,
- `aesop` failed quickly,
- `exact? +grind`, `apply? +grind`, `exact?`, and `apply?` each hit the
  bounded retrieval timeout,
- arithmetic/contradiction/induction-style tactics were not appropriate.

This experiment strengthens the Phase 19 architecture decision: Gareen should
orchestrate **complementary** existing solvers and its own verified recursive
search rather than assume one tactic family is universally stronger.

It also identifies premise selection as a major remaining gap and provides a
concrete reason to evaluate Hammer/ATP/retrieval systems next.


## Phase 19 long-horizon experiment: five-hour strengthened Euclid test

A long-horizon experiment was added to test whether substantially larger search
budgets change the frontier, rather than judging Gareen only from short CI runs.

GitHub-hosted standard runners permit jobs up to six hours; Gareen therefore
uses a five-hour workflow timeout to leave a margin under the platform limit.
Because the repository is public, standard GitHub-hosted Actions usage is not
billed by minute under GitHub's public-repository policy.

The chosen target is a strengthened form of Euclid's infinitude-of-primes
theorem:

```text
∀ n : Nat, 2 ≤ n →
  ∃ p : Nat, Nat.Prime p ∧ n < p ∧ Nat.gcd n p = 1
```

This is a proven theorem-shaped target, not an open conjecture. The purpose is
to measure proof orchestration, premise selection, strategy switching, and
long-horizon search. The target combines:
- existence of a prime above an arbitrary natural number,
- primality,
- an order constraint,
- and a derived coprimality/gcd obligation.

A short sanity anchor is run first:

```text
∀ n : Nat, ∃ p : Nat, Nat.Prime p ∧ n < p
```

This confirms that the environment can access the classical infinitude-of-primes
fact before spending a long budget on the strengthened target.

The workflow is configured for a maximum of 300 minutes. Ecosystem strategies
may receive up to 15 minutes each, while Gareen's recursive portfolio receives a
much larger node/time envelope if the ecosystem layer does not close the goal.
The script itself keeps a safety margin for Lean setup and artifact upload.

This experiment should be interpreted carefully:
- quick success is valuable evidence that existing ecosystem tools already cover
  the theorem shape;
- slow success reveals a real benefit from extra search budget;
- failure after the long budget identifies a stronger premise-selection or
  strategy-composition gap;
- it is not evidence about open conjectures or research-level novelty.


## Phase 19 lean-auto integration validation

The Lake manifest issue was repaired and independently validated with
`lake update auto`. The pinned `lean-auto` dependency then built successfully
inside the Gareen CI environment, so the following results are genuine proof
results rather than dependency/setup failures.

Three diagnostic goals were tested:

| Goal | Result | Winner |
|---|---|---|
| Euclid anchor: `∀ n, ∃ p, Nat.Prime p ∧ n < p` | unproved | none |
| divisibility: `d ∣ a → d ∣ b → d ∣ a+b` | verified | Gareen advanced |
| double-coprime frontier | unproved | none |

Overall result: **1/3 verified**.

The direct `auto` and `auto [*]` attempts executed successfully but returned
unproved quickly (about 1.7 seconds per attempt on these goals). The only
successful theorem was the divisibility composition, and it was recovered by
Gareen's advanced recursive fallback rather than by `lean-auto`.

This is important for interpreting the integration correctly. The current
Phase 19 adapter activates the base `auto` tactic, but it does **not yet**
activate the stronger external backends documented by lean-auto:
- SMT mode,
- TPTP / Zipperposition,
- native prover mode with Duper or another proof-producing backend.

Therefore this experiment should not be read as “lean-auto with ATP failed.”
It establishes only that the base tactic, as currently configured, did not
expand Gareen's frontier on these three goals.

The next integration step is to configure a proof-producing or externally
checked backend rather than spending more runtime on the same base `auto`
configuration.


---

# Part XIX — Feedback-aware proof loop


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


---

# Part XX — Context-aware feedback validation


## Phase 19.2 — context-aware feedback loop validated

A second feedback-loop iteration fixed two concrete orchestration defects.

First, Gareen's suggestion parser had only consumed Lean messages beginning with
`Try this:`.  The failing divisibility benchmark used a different diagnostic:

```text
found a proof, but the corresponding tactic failed:
  (expose_names; exact ...)
```

That diagnostic is now parsed as solver feedback.

Second, the planner had been querying retrieval before introducing the theorem's
outer variables and implication hypotheses into the local context.  Gareen now
builds stable context names for both forall binders and outer implication
hypotheses, then retries `exact?` and `apply?` after `intro`.  For the
divisibility theorem this changes the proof state from the whole quantified
statement to the useful local state:

```text
d a b : Nat
h1 : d ∣ a
h2 : d ∣ b
⊢ d ∣ a + b
```

A third scheduling defect was then found: the one-shot ecosystem cascade could
consume the entire per-theorem wall-clock budget before the feedback planner was
invoked.  Phase 19.2 therefore reserves a bounded portion of each theorem budget
for feedback-aware planning.

### Five-medium validation

After these fixes, the ecosystem-only five-medium diagnostic improved from 4/5
to **5/5 verified**:

| Goal | Verified | Winning layer/strategy |
| --- | --- | --- |
| Nat monotone addition | yes | `grind` |
| Int quadratic identity | yes | `grind` |
| consecutive gcd | yes | `aesop` |
| common divisor divides a sum | yes | `lean_feedback_loop / feedback_introduced_exact_retrieval` |
| propositional implication chain | yes | `grind` |

The previously missed theorem

```text
∀ d a b : Nat, d ∣ a → d ∣ b → d ∣ a + b
```

was therefore closed by the new feedback layer itself, with Gareen recursive
fallback disabled in this experiment.

This is the first controlled demonstration that Gareen can obtain value from a
solver response that is not already a complete one-shot success: it changes the
proof context, re-runs retrieval, and obtains a Lean-verified result.

### Hard frontier validation

The same repair also closed the previously unproved double-coprime frontier:

```text
∀ n : Nat,
  Nat.gcd n (2 * n + 1) = 1 ∧
  Nat.gcd (n + 1) (2 * n + 1) = 1
```

Result:

```text
verified = True
winning_strategy = feedback_introduced_apply_retrieval
layer = lean_feedback_loop
```

No Gareen recursive fallback was required for this accepted result.

This is stronger evidence than the five-medium recovery because this theorem had
previously remained outside the demonstrated coverage of the one-shot ecosystem
portfolio.

### Interpretation

The validated contribution is not a new trusted kernel and not a replacement for
Mathlib tactics.  The demonstrated Gareen capability is **proof orchestration**:

```text
goal
  -> one-shot solver attempts
  -> expose local proof context
  -> consume retrieval/prover feedback
  -> transform the next proof attempt
  -> retry under a reserved resource budget
  -> Lean kernel verification
```

The immediate next research direction is to generalize this from textual
suggestion repair to explicit proof-state/subgoal routing and cross-solver
checkpoint exchange.


---

# Part XXI — Hard Fermat-style composed benchmark

A harder Phase 19 benchmark tested a composed form of Fermat's little theorem:

```text
∀ p a : Nat,
  Nat.Prime p →
  ¬ p ∣ a →
  ∃ k : Nat, a ^ (p - 1) = k * p + 1
```

This asks for an explicit existential quotient form rather than ending at a
modulo/remainder statement. The benchmark therefore requires Gareen to expose
the local proof context and retrieve a proof after introducing the prime and
non-divisibility hypotheses.

Resource limits:
- GitHub Actions job hard cap: 10 minutes
- internal proof-search budget: 300 seconds

Result:
- theorem status: **proved**
- winning layer: `lean_feedback_loop`
- winning strategy: `feedback_introduced_apply_retrieval`
- planner elapsed: **155.544 seconds**
- total GitHub job elapsed: about **6m48s**
- Gareen recursive fallback: **not used**

All one-shot attempts failed or were audit-rejected before the context-aware
retrieval layer succeeded. The successful generated proof state was:

```lean
intro p a h1 h2
apply?
```

This is important to interpret accurately. The decisive Gareen contribution in
this run was context transformation and strategy scheduling: the same retrieval
tool was ineffective on the original quantified theorem, but succeeded after
Gareen introduced the variables and hypotheses into the local context.

This result extends the previous 5/5 medium benchmark and double-coprime
frontier success to a harder theorem involving primes, powers, divisibility,
existential witnesses, and Fermat-style modular structure.
