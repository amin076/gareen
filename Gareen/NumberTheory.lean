import Mathlib

namespace Gareen

/-!
Lean-backed number-theory vocabulary for Gareen.

Gareen does not redefine mature mathematics.  These abbreviations expose the
canonical Nat/Mathlib concepts under stable research-layer names so the Python
orchestration layer can grow beyond the original {0,S,+,*} sandbox.
-/

abbrev Divides (a b : Nat) : Prop := a ∣ b
abbrev Quotient (n d : Nat) : Nat := n / d
abbrev Remainder (n d : Nat) : Nat := n % d
abbrev GCD (a b : Nat) : Nat := Nat.gcd a b
abbrev Coprime (a b : Nat) : Prop := Nat.Coprime a b
abbrev IsPrime (n : Nat) : Prop := Nat.Prime n

/-! Basic divisibility and primality checks retained from the first migration. -/

theorem one_divides_all (n : Nat) : Divides 1 n := by
  simp [Divides]

theorem divides_self (n : Nat) : Divides n n := by
  simp [Divides]

theorem zero_divides_iff (n : Nat) : Divides 0 n ↔ n = 0 := by
  simp [Divides]

theorem two_is_prime : IsPrime 2 := by
  norm_num [IsPrime]

theorem three_is_prime : IsPrime 3 := by
  norm_num [IsPrime]

theorem two_divides_ten : Divides 2 10 := by
  norm_num [Divides]

/-! New Phase-16 vocabulary sanity theorems. -/

theorem divides_iff_exists_factor (a b : Nat) :
    Divides a b ↔ ∃ c : Nat, b = a * c := by
  rfl

theorem quotient_remainder_reconstruct (n d : Nat) :
    Remainder n d + d * Quotient n d = n := by
  simpa [Remainder, Quotient] using Nat.mod_add_div n d

theorem gcd_divides_left (a b : Nat) : Divides (GCD a b) a := by
  simpa [Divides, GCD] using Nat.gcd_dvd_left a b

theorem gcd_divides_right (a b : Nat) : Divides (GCD a b) b := by
  simpa [Divides, GCD] using Nat.gcd_dvd_right a b

theorem gcd_commutative (a b : Nat) : GCD a b = GCD b a := by
  simpa [GCD] using Nat.gcd_comm a b

theorem coprime_iff_gcd_one (a b : Nat) :
    Coprime a b ↔ GCD a b = 1 := by
  simpa [Coprime, GCD] using (Nat.coprime_iff_gcd_eq_one : a.Coprime b ↔ a.gcd b = 1)

theorem prime_has_only_trivial_divisors {p d : Nat}
    (hp : IsPrime p) (hd : Divides d p) :
    d = 1 ∨ d = p := by
  exact (hp.eq_one_or_self_of_dvd d hd)

end Gareen
