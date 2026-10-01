# Gareen

Gareen is a research project for exploring whether a machine can grow useful formal mathematical knowledge with minimal human guidance.

**Architecture V2 changes the trust boundary.** Gareen no longer aims to grow its Python proof checker into a competing proof assistant. Lean 4 + Mathlib are now the trusted formal foundation for serious mathematical research, while Python remains the research/orchestration layer for conjecture generation, strategy selection, memory, ranking, and future concept invention.

The original Python formal world from Phases 1–11 is retained as a transparent educational and research sandbox. It is valuable for experimentation, but new durable mathematical claims should be checked by Lean's kernel.

## Phase 18 — Recursive theorem-retrieval planner

The number-theory proof path now uses bounded recursive backward search.
Lean's indexed library lookup retrieves applicable theorems; their premises
become subgoals, and ranked alternatives are explored with full backtracking.
There are no domain-specific decomposition templates in this new planner.

The planner records its proof graph, failed branches, resource use and checked
proof source. Successful theorem use improves persistent ranking hints; every
new result is still independently elaborated and axiom-audited by Lean.

A fixed 50-goal ladder includes the original gcd target, nested arithmetic
composition, propositions, and harder number-theory goals. Phase 17 remains
available for paired baseline runs. See [Phase 18 design, limitations and
reproduction](docs/PHASE18.md). Recursive lemma invention and general induction
planning remain future work.

## Phase 17 — Mathlib theorem retrieval + multi-step proof planning

Phase 16 exposed the next bottleneck: Gareen knew the vocabulary for gcd and
divisibility, but generic tactics could not prove even a simple multi-step goal
such as:

```text
∀ a b : Nat, Nat.gcd a b ∣ a + b
```

Phase 17 adds a retrieval/planning layer between a research goal and Lean
verification:

```text
goal
  ↓
try direct Mathlib retrieval
  ↓
structural decomposition when needed
  ↓
retrieve lemmas for subgoals with Lean exact?
  ↓
retrieve the composition step
  ↓
Lean kernel verification
```

The first reusable structural schema handles divisibility over addition:
`d ∣ x + y` is decomposed into `d ∣ x` and `d ∣ y`. The planner does
**not** hard-code the GCD lemma names used by the regression test; Mathlib's
retrieval engine must find the relevant facts.

The exact GCD target that failed before Phase 17 is now a permanent
planner-benchmark in `number_theory_frontier.py`. The before/after regression
is reproducible with:

```bash
python experiments/gcd_proof_trial_v2.py --seconds 300
```

The report records the old generic-tactic baseline, positive/false controls,
planner strategy, retrieved Mathlib constants, timing, and final kernel-checked
result.

## Phase 16 — Mathematical research value + number-theory frontier

Phase 15 proved that throughput alone is not enough: Gareen can verify many
true identities, but most of them may be mathematically routine. Phase 16 adds
an explicit research-value gate before expensive proving.

A candidate is now filtered out of the research queue when:

- it is only a ground numerical instance; such examples remain useful as
  conjecture evidence;
- both sides are explained entirely by primitive arithmetic rewrites;
- it is reachable from already verified Gareen theorems in fewer than three
  local theorem-rewrite steps;
- or its combined research-value score is below the configured threshold.

The score rewards:

```text
generality
+ compression of existing results
+ reuse potential across current open conjectures
+ structural richness
+ distance from already verified knowledge
```

The "three-step" rule is a **local derivation-distance heuristic**, not a claim
about the globally shortest Lean proof. Lean tactics such as `omega` can hide
many internal inference steps, so Gareen records this measure honestly as an
estimate.

Lean-backed research now starts with Gareen's verified T1–T14 knowledge rather
than an empty theorem memory, so identities such as `x * 1 = x` are not
rediscovered as research results.

### Enlarged number-theory vocabulary

The serious research layer now exposes canonical Mathlib concepts rather than
reimplementing them:

```text
Divides    a ∣ b
Quotient   n / d
Remainder  n % d
GCD        Nat.gcd a b
Coprime    Nat.Coprime a b
Prime      Nat.Prime p
```

`Gareen/NumberTheory.lean` provides stable Gareen names and kernel-checked
sanity theorems. `number_theory_frontier.py` exposes the same concepts to the
Python orchestration layer through general, Lean-native propositions.

The legacy Python `{0,S,+,*}` world remains a sandbox; no custom division or
prime axioms are introduced.

## Phase 15 — Throughput and proof-soundness hardening

The first 15-minute autonomous campaign exposed a clear bottleneck: Gareen
could generate far more conjectures than the old bridge could send through
Lean. Phase 15 changes the proving path rather than merely increasing the
candidate count.

Key changes:

- batch many independent conjectures into shared Lean processes;
- run tactic rounds only on candidates still unproved;
- enforce a shared wall-clock budget for research campaigns;
- distinguish `verified`, `unproved-in-budget`, and `not-attempted`;
- diversify unary and bivariate candidate selection;
- deprioritize statements already explained by Gareen's primitive rewrites;
- record Lean process count and verification elapsed time;
- harden the legacy induction checker against invalid dependency discharge.

An unproved candidate is **not** treated as false. Only a kernel-checked Lean
proof makes a durable theorem.

The reproducible benchmark utility is:

```bash
python experiments/throughput_campaign.py --seconds 900
```

It uses false control statements, target-free pattern mining, a fixed wall-clock
budget, and JSON/Markdown reporting.

## Phases 12–14 — Lean transformation

### Current architecture

```text
Gareen research layer (Python)
  ├─ pattern mining
  ├─ conjecture generation
  ├─ research memory
  ├─ strategy / lemma proposals
  └─ future interestingness + concept invention
              │
              ▼
        Python → Lean bridge
              │
              ▼
Lean 4 + Mathlib + prover backends
              │
              ▼
          Lean kernel
              │
              ▼
     verified knowledge
```

The repository pins Lean/Mathlib to the stable `v4.34.1` line. Representative arithmetic theorems now live in `Gareen/Arithmetic.lean`, and `Gareen/NumberTheory.lean` begins using Mathlib's mature divisibility and primality vocabulary.

`lean_bridge.py` translates Gareen formulas to Lean propositions and checks them with a bounded tactic portfolio. `lean_research.py` connects Gareen's conjecture generator to that bridge and records only Lean-verified discoveries.

See:

- `docs/ARCHITECTURE_V2.md`
- `docs/LEAN_MIGRATION.md`

## Legacy sandbox — Phases 1–11

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

Gareen now coordinates conjecture generation, strategy selection, automatic induction synthesis, helper-lemma proposal, formal verification, and a research notebook. The Phase 11 demo deliberately starts from the axioms only, without loading the hand-authored T1–T14 theorem library.

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

### Autonomous theorem search

`autonomous_discovery.py` no longer requires a human-supplied theorem goal.

The Phase 9 explorer:

```text
generates a bounded universe of closed terms
normalizes terms only to propose conjectures
builds candidate equalities
orders candidates with a simple heuristic
runs bounded proof search
rechecks every candidate proof with check_proof()
rejects direct/trivial instances below a proof-length threshold
stores accepted discoveries in KnowledgeState
records accepted, skipped, and failed attempts
```

Normalization is **not** treated as proof. It is only a conjecture generator. A candidate such as:

```text
Add(1, 1) = 2
```

must still be independently reconstructed by the proof searcher and then verified by the deterministic checker before it can become a theorem.

Autonomous discoveries receive state-aware names:

```text
D1_AUTO
D2_AUTO
D3_AUTO
...
```

and each record keeps:

```text
statement
proof length
heuristic score
dependencies
attempt status
```

The trust boundary is therefore:

```text
candidate generator / heuristic
            ↓
bounded proof search
            ↓
candidate proof
            ↓
trusted deterministic checker
            ↓
verified autonomous theorem
```

This is still **bounded discovery**, not a claim of novel human mathematics. The current candidate universe is intentionally small and uses closed arithmetic expressions built from the existing symbols.

### General conjecture discovery

`general_conjecture.py` moves Gareen from closed numerical instances to symbolic patterns with variables.

Phase 10 does **not** hard-code a theorem target. Instead it generates a bounded expression grammar containing forms such as:

```text
x
S(x)
x + 0
0 + x
x + 1
1 + x
x + x
x × 1
1 × x
x × 2
2 × x
```

Each expression is evaluated symbolically on the sample terms:

```text
0, 1, 2, 3
```

Expressions with matching output signatures are grouped into the same empirical pattern class. For example, the system can notice that:

```text
x + 1
S(x)
```

produce the same outputs on the sample set and therefore propose:

```text
∀x. x + 1 = S(x)
```

But finite agreement is **never treated as proof**.

The pipeline is:

```text
symbolic expression grammar
        ↓
finite observations
        ↓
pattern classes
        ↓
general conjectures
        ↓
open-formula proof search
        ↓
FORALL_INTRO
        ↓
trusted deterministic checker
        ↓
verified general theorem
```

The bounded proof searcher can now optionally work with formulas containing free variables. After it constructs a proof of the open body, Phase 10 adds a checked `FORALL_INTRO` step and re-runs the trusted verifier on the complete universal theorem.

Existing unary axioms and theorems are canonicalized so Gareen does not simply rediscover them with equality reversed.

Autonomously accepted general theorems receive names such as:

```text
G1_AUTO
G2_AUTO
G3_AUTO
...
```

This phase is the first point where Gareen can move from observations like:

```text
0 + 1 = 1
1 + 1 = 2
2 + 1 = 3
3 + 1 = 4
```

to a proposed general law:

```text
∀x. x + 1 = S(x)
```

and then demand a formal symbolic proof of that law.

### Artificial Mathematician prototype

`artificial_mathematician.py` adds a bounded research loop above the existing conjecture and proof engines.

The prototype has four explicit research components:

```text
Conjecture Generator
Strategy Selector
Induction Synthesizer
Lemma Proposer
```

The campaign can start from:

```text
primitives + definitions + axioms
```

with no preloaded hand-authored theorem library.

The conjecture generator combines the unary pattern miner from Phase 10 with a new two-variable grammar. Two-variable expressions are observed over a 3×3 sample grid:

```text
x,y ∈ {0,1,2}
```

so patterns such as:

```text
x + y
y + x
```

can become candidate universal laws. Sample agreement is still only conjectural evidence.

For each conjecture the Strategy Selector tries:

```text
1. bounded direct symbolic proof
2. automatic induction synthesis
3. lower-complexity helper-lemma proposal
4. retry after verified lemmas are added
```

The Induction Synthesizer constructs the induction structure itself:

```text
P(0)
P(n)  [temporary induction hypothesis]
  ↓
P(S(n))
  ↓
INDUCTION
  ↓
∀n P(n)
```

The induction hypothesis is represented as an actual open `ASSUMPTION` in the candidate derivation. It must be discharged by the trusted `INDUCTION` rule before the theorem can enter the knowledge state.

The proof-search layer now exposes an untrusted derivation API so higher-level strategies can search under temporary assumptions. That derivation is never accepted directly; the Artificial Mathematician assembles a complete proof and re-runs `check_proof()`.

If direct proof and induction both fail, the Lemma Proposer selects lower-complexity conjectures. A helper lemma is usable only after it is independently proved and stored as a verified theorem.

The research notebook records:

```text
generated conjectures
attempted conjectures
successful strategy
proof length
invented helper lemmas
dependencies
failed strategies and reasons
```

The intended research loop is now:

```text
observe
  ↓
conjecture
  ↓
choose proof strategy
  ├── direct search
  ├── induction
  └── invent lemma → verify lemma → retry
  ↓
trusted proof checker
  ↓
new knowledge
  ↓
research notebook
```

This is an **Artificial Mathematician prototype inside Gareen's small formal arithmetic world**, not a claim of a general autonomous mathematician.

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

### Python research sandbox

Requires Python 3.10+ and no third-party Python packages:

```bash
python -m unittest discover -s tests -v
python artificial_mathematician.py
```

### Lean foundation

Install Lean via `elan`, then:

```bash
lake update
lake exe cache get
lake build
```

Run the Python → Lean verification bridge:

```bash
python lean_bridge.py --ci-demo
```

Run a small Lean-backed Gareen research campaign:

```bash
python lean_research.py --limit 3
```

## Current boundary

The Python sandbox is intentionally a tiny formal world and will no longer be expanded to duplicate mature proof-assistant functionality.

Lean/Mathlib now gives Gareen access to a much larger mathematical foundation, including number-theory concepts that we should reuse rather than rebuild. Gareen itself still lacks:

- strong external Lean prover integration;
- persistent multi-day research campaigns;
- recursive lemma invention;
- robust theorem interestingness / novelty scoring;
- concept and definition invention;
- large-scale benchmark evaluation;
- comparison against LeanConjecturer and modern Lean provers;
- LLM-guided research strategy.

The next work should improve those research capabilities rather than recreating Lean internals.

## Next milestone

The next milestone is **prover and benchmark integration**, not another custom arithmetic layer:

```text
baseline: native Mathlib tactics
        ↓
BFS-Prover-V2 / Discover-and-Prove adapters
        ↓
Seed-Prover evaluation
        ↓
LeanConjecturer comparison
        ↓
persistent research memory + failure analysis
        ↓
novelty / reuse / dependency-impact scoring
        ↓
recursive lemma and concept invention
```

The research layer may eventually use agents or LLMs, but mathematical acceptance remains delegated to Lean's kernel.

## Research question

> Can a machine autonomously expand a bounded formal mathematical knowledge state while every accepted result remains explicitly derivable and auditable?
