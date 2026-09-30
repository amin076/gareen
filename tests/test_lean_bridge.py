import unittest

from lean_bridge import (
    render_expr,
    render_formula,
    render_theorem_source,
)
from math_world import (
    X,
    Y,
    ZERO,
    Add,
    Eq,
    ForAll,
    Mul,
    Succ,
)


class LeanBridgeTranslationTests(unittest.TestCase):
    def test_renders_arithmetic_expression(self):
        expr = Add(Succ(ZERO), Mul(X, Y))
        rendered = render_expr(expr)

        self.assertIn("Nat.succ", rendered)
        self.assertIn("*", rendered)
        self.assertIn("+", rendered)

    def test_renders_nested_universal_formula(self):
        formula = ForAll(
            X,
            ForAll(
                Y,
                Eq(Add(X, Y), Add(Y, X)),
            ),
        )
        rendered = render_formula(formula)

        self.assertIn("∀ (x : Nat)", rendered)
        self.assertIn("∀ (y : Nat)", rendered)
        self.assertIn("=", rendered)

    def test_source_imports_mathlib(self):
        formula = ForAll(X, Eq(Add(ZERO, X), X))
        source = render_theorem_source(
            formula,
            theorem_name="zero_add_candidate",
            tactic="omega",
        )

        self.assertIn("import Mathlib", source)
        self.assertIn("theorem zero_add_candidate", source)
        self.assertIn("omega", source)

    def test_rejects_unsafe_theorem_identifier(self):
        formula = ForAll(X, Eq(X, X))

        with self.assertRaises(ValueError):
            render_theorem_source(
                formula,
                theorem_name="bad name",
                tactic="simp",
            )

    def test_rejects_unapproved_tactic(self):
        formula = ForAll(X, Eq(X, X))

        with self.assertRaises(ValueError):
            render_theorem_source(
                formula,
                theorem_name="safe_name",
                tactic="run_tac IO.println \"oops\"",
            )


if __name__ == "__main__":
    unittest.main()
