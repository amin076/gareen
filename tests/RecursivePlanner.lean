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
