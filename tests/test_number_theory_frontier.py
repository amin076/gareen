import unittest

from number_theory_frontier import (
    NUMBER_THEORY_VOCABULARY,
    generate_number_theory_frontier,
)


class NumberTheoryFrontierTests(unittest.TestCase):
    def test_required_number_theory_concepts_are_exposed(self):
        names = {item.name for item in NUMBER_THEORY_VOCABULARY}

        self.assertTrue(
            {"divides", "quotient", "remainder", "gcd", "coprime", "prime"}
            <= names
        )

    def test_frontier_uses_general_statements_not_many_ground_examples(self):
        frontier = generate_number_theory_frontier()
        statements = [item.statement for item in frontier]

        self.assertGreaterEqual(len(frontier), 8)
        self.assertTrue(any("∀ n : Nat" in statement for statement in statements))
        self.assertTrue(any("∀ a b : Nat" in statement for statement in statements))
        self.assertTrue(any("∣" in statement for statement in statements))
        self.assertTrue(any("/" in statement and "%" in statement for statement in statements))

    def test_division_and_divisibility_are_distinct_concepts(self):
        concepts = {item.name: item for item in NUMBER_THEORY_VOCABULARY}

        self.assertEqual(concepts["divides"].kind, "relation")
        self.assertEqual(concepts["quotient"].kind, "function")


if __name__ == "__main__":
    unittest.main()
