import unittest

from lean_bridge import (
    LeanBatchCandidate,
    _failed_names_from_diagnostics,
    render_batch_source,
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

    def test_batch_source_tracks_candidate_line_ranges(self):
        candidates = (
            LeanBatchCandidate(
                theorem_name="first_candidate",
                formula=ForAll(X, Eq(Add(ZERO, X), X)),
            ),
            LeanBatchCandidate(
                theorem_name="second_candidate",
                formula=ForAll(X, Eq(X, X)),
            ),
        )

        source, ranges = render_batch_source(candidates, tactic="simp")

        self.assertIn("theorem first_candidate", source)
        self.assertIn("theorem second_candidate", source)
        self.assertEqual(set(ranges), {"first_candidate", "second_candidate"})
        self.assertLess(ranges["first_candidate"][0], ranges["second_candidate"][0])

    def test_batch_diagnostics_map_only_failed_candidate(self):
        candidates = (
            LeanBatchCandidate(
                theorem_name="first_candidate",
                formula=ForAll(X, Eq(Add(ZERO, X), X)),
            ),
            LeanBatchCandidate(
                theorem_name="second_candidate",
                formula=ForAll(X, Eq(X, X)),
            ),
        )
        _, ranges = render_batch_source(candidates, tactic="simp")
        failed_line = ranges["second_candidate"][1]
        diagnostics = (
            f"/tmp/batch.lean:{failed_line}:3: error: tactic failed\n"
        )

        failed, unmapped = _failed_names_from_diagnostics(
            diagnostics,
            ranges,
        )

        self.assertEqual(failed, frozenset({"second_candidate"}))
        self.assertFalse(unmapped)

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
