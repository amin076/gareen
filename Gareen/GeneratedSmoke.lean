import Mathlib

/-!
This file is a checked-in smoke target for the Python→Lean bridge.
The Python bridge can generate equivalent modules dynamically in CI.
-/

namespace Gareen.GeneratedSmoke

theorem two_plus_one : (2 : Nat) + 1 = 3 := by
  norm_num

theorem symbolic_successor (x : Nat) : x + 1 = Nat.succ x := by
  omega

theorem symbolic_zero_left (x : Nat) : 0 + x = x := by
  simp

end Gareen.GeneratedSmoke
