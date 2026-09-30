import Mathlib

namespace Gareen

/-!
A small compatibility layer showing that Gareen's early arithmetic laws now
live on top of Lean/Mathlib instead of a custom trusted kernel.
-/

theorem zero_add_verified (n : Nat) : 0 + n = n := by
  simp

theorem add_zero_verified (n : Nat) : n + 0 = n := by
  simp

theorem add_comm_verified (a b : Nat) : a + b = b + a := by
  omega

theorem add_assoc_verified (a b c : Nat) : (a + b) + c = a + (b + c) := by
  omega

theorem one_mul_verified (n : Nat) : 1 * n = n := by
  simp

theorem mul_one_verified (n : Nat) : n * 1 = n := by
  simp

theorem mul_comm_verified (a b : Nat) : a * b = b * a := by
  ring

theorem mul_assoc_verified (a b c : Nat) : (a * b) * c = a * (b * c) := by
  ring

theorem mul_add_verified (a b c : Nat) : a * (b + c) = a * b + a * c := by
  ring

end Gareen
