import unittest

from lean_proof_planner import (
    LeanProofPlanner,
    _constants_from_suggestions,
    _extract_suggestions,
    decompose_dvd_add,
)


class ProofPlannerStructureTests(unittest.TestCase):
    def test_decomposes_generic_divisibility_over_addition(self):
        decomposition = decompose_dvd_add(
            "∀ a b : Nat, Nat.gcd a b ∣ a + b"
        )

        self.assertIsNotNone(decomposition)
        self.assertEqual(decomposition.intro_names, ("a", "b"))
        self.assertEqual(decomposition.divisor, "Nat.gcd a b")
        self.assertEqual(decomposition.left_addend, "a")
        self.assertEqual(decomposition.right_addend, "b")

    def test_dvd_add_schema_is_not_specific_to_gcd(self):
        decomposition = decompose_dvd_add(
            "∀ d x y : Nat, d ∣ x + y"
        )

        self.assertIsNotNone(decomposition)
        self.assertEqual(decomposition.intro_names, ("d", "x", "y"))
        self.assertEqual(decomposition.divisor, "d")
        self.assertEqual(decomposition.left_addend, "x")
        self.assertEqual(decomposition.right_addend, "y")

    def test_non_additive_divisibility_goal_is_not_forced_into_schema(self):
        self.assertIsNone(
            decompose_dvd_add("∀ a b : Nat, Nat.gcd a b ∣ a")
        )

    def test_planner_uses_library_retrieval_not_hardcoded_gcd_lemmas(self):
        planner = LeanProofPlanner()
        strategies = planner._strategies(
            "∀ a b : Nat, Nat.gcd a b ∣ a + b"
        )
        combined = "\n".join(
            line
            for _, lines in strategies
            for line in lines
        )

        self.assertIn("exact?", combined)
        self.assertIn("have gareen_left", combined)
        self.assertIn("have gareen_right", combined)
        self.assertNotIn("Nat.gcd_dvd_left", combined)
        self.assertNotIn("Nat.gcd_dvd_right", combined)
        self.assertNotIn("Nat.dvd_add_right", combined)

    def test_extracts_mathlib_suggestions_and_constants(self):
        stdout = (
            "info: Try this: exact Nat.gcd_dvd_left a b\n"
            "info: Try this: exact (Nat.dvd_add_right gareen_left).2 "
            "gareen_right\n"
        )
        suggestions = _extract_suggestions(stdout, "")
        constants = _constants_from_suggestions(suggestions)

        self.assertIn("exact Nat.gcd_dvd_left a b", suggestions)
        self.assertIn("Nat.gcd_dvd_left", constants)
        self.assertIn("Nat.dvd_add_right", constants)


if __name__ == "__main__":
    unittest.main()
