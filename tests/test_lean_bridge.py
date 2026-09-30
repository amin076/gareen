import unittest

from lean_bridge import expr_to_lean, formula_to_lean, theorem_source
from math_world import (
    ONE,
    THREE,
    TWO,
    X,
    Add,
    Eq,
    ForAll,
    Mul,
    Succ,
    ZERO,
)
from prover_adapters import FutureExternalProver, LocalTacticPortfolio


class LeanBridgeTests(unittest.TestCase):
    def test_expression_translation(self):
        self.assertEqual(expr_to_lean(ZERO), "0")
        self.assertEqual(expr_to_lean(Succ(X)), "Nat.succ (x)")
        self.assertEqual(expr_to_lean(Add(TWO, ONE)), "((Nat.succ (Nat.succ (0))) + Nat.succ (0))")
        self.assertEqual(expr_to_lean(Mul(X, TWO)), "(x * Nat.succ (Nat.succ (0)))")

    def test_formula_translation(self):
        formula = ForAll(X, Eq(Add(ZERO, X), X))
        self.assertEqual(
            formula_to_lean(formula),
            "∀ (x : Nat), (0 + x) = x",
        )

    def test_theorem_source_is_self_contained(self):
        formula = Eq(Add(TWO, ONE), THREE)
        source = theorem_source(
            "two_plus_one",
            formula,
            "by\n  norm_num",
        )

        self.assertIn("import Mathlib", source)
        self.assertIn("theorem two_plus_one", source)
        self.assertIn("norm_num", source)

    def test_local_provider_has_deterministic_tactic_portfolio(self):
        provider = LocalTacticPortfolio()
        tactics = provider.candidates(ForAll(X, Eq(Add(ZERO, X), X)))

        self.assertGreaterEqual(len(tactics), 3)
        self.assertTrue(all(tactic.startswith("by") for tactic in tactics))

    def test_external_provider_is_explicitly_not_connected(self):
        provider = FutureExternalProver(
            name="bfs-prover-v2",
            endpoint_kind="local",
        )
        with self.assertRaises(NotImplementedError):
            provider.candidates(Eq(TWO, TWO))


if __name__ == "__main__":
    unittest.main()
