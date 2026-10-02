import Gareen.RecursivePlanner

-- Non-arithmetic domains: these have no Nat schema and use local implications.
example (P Q R : Prop) (h₁ : P → Q) (h₂ : Q → R) (h₃ : P) : R := by
  gareen_search 5 300 24

-- The first branch cannot prove P; the second branch must remain available.
example (P Q : Prop) (a_dead : P → Q) (z_good : True → Q) : Q := by
  gareen_search 5 300 24

example (P Q R : Prop) (hp : P) (hq : Q) (hr : R) : P ∧ (Q ∧ R) := by
  gareen_search 5 400 32

-- A dependent witness is shared by sibling goals. The x = 0 route must be
-- undone when its sibling requires x = 1. This detects incomplete backtracking.
example (P Q : Nat → Prop) (a_zero : P 0) (b_one : P 1) (c_one : Q 1) :
    ∃ x, P x ∧ Q x := by
  gareen_search 6 600 32


-- Ranking regression: the useful transitivity rule creates premises already
-- present in the local context and should outrank unrelated library branches.
example (a b c : Nat) (hab : a ∣ b) (hbc : b ∣ c) : a ∣ c := by
  gareen_search 5 500 32

-- Structural-progress regression: for d ∣ a * c, prefer the multiplication
-- rule reducing to d ∣ a (a literal prefix/subgoal) over the symmetric dead end.
example (a b c : Nat) : Nat.gcd a b ∣ a * c := by
  gareen_search 5 500 32


-- Symmetric gcd-sum regression: these were solved before context-aware ranking,
-- then regressed because a transitivity branch closed one premise locally while
-- leaving a strategically worse residual divisibility goal.
example (a b : Nat) : Nat.gcd a b ∣ b + a := by
  gareen_search 6 800 48

example (a b : Nat) : Nat.gcd a b ∣ (a + b) + (b + a) := by
  gareen_search 6 1000 48

example (a b : Nat) :
    Nat.gcd a b ∣ a + b ∧ Nat.gcd a b ∣ b + a := by
  gareen_search 6 1000 48
