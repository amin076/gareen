import Mathlib

namespace Gareen

/-!
The first step beyond Gareen's toy arithmetic language.

These examples intentionally use Mathlib's mature number-theory vocabulary,
so Gareen can build research workflows on existing mathematics rather than
reimplementing divisibility and primality from scratch.
-/

theorem one_divides_all (n : Nat) : 1 ∣ n := by
  simp

theorem divides_self (n : Nat) : n ∣ n := by
  simp

theorem zero_divides_iff (n : Nat) : 0 ∣ n ↔ n = 0 := by
  simp

theorem two_is_prime : Nat.Prime 2 := by
  norm_num

theorem three_is_prime : Nat.Prime 3 := by
  norm_num

theorem two_divides_ten : 2 ∣ 10 := by
  norm_num

end Gareen
