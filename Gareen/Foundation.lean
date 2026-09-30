import Mathlib

/-!
# Gareen Lean Foundation

The Python formal world remains a small research sandbox.
Lean + Mathlib is the production-grade trusted formal backend.

These theorems are intentionally elementary: their purpose is to prove that
Gareen's arithmetic concepts live cleanly inside Lean's trusted kernel.
-/

namespace Gareen

theorem zero_add_nat (x : Nat) : 0 + x = x := by
  simp

theorem add_zero_nat (x : Nat) : x + 0 = x := by
  simp

theorem add_comm_nat (x y : Nat) : x + y = y + x := by
  simpa using Nat.add_comm x y

theorem add_assoc_nat (x y z : Nat) : (x + y) + z = x + (y + z) := by
  simpa using Nat.add_assoc x y z

theorem zero_mul_nat (x : Nat) : 0 * x = 0 := by
  simp

theorem mul_zero_nat (x : Nat) : x * 0 = 0 := by
  simp

theorem mul_one_nat (x : Nat) : x * 1 = x := by
  simp

theorem one_mul_nat (x : Nat) : 1 * x = x := by
  simp

theorem mul_comm_nat (x y : Nat) : x * y = y * x := by
  simpa using Nat.mul_comm x y

theorem mul_assoc_nat (x y z : Nat) : (x * y) * z = x * (y * z) := by
  simpa using Nat.mul_assoc x y z

theorem mul_add_nat (x y z : Nat) : x * (y + z) = x * y + x * z := by
  simpa using Nat.mul_add x y z

end Gareen
