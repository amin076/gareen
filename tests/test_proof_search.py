import unittest

from math_world import (
    ONE,
    THREE,
    TWO,
    X,
    Add,
    Eq,
    build_initial_knowledge,
    check_proof,
)
from proof_search import BoundedProofSearcher


class AutomaticProofSearchTests(unittest.TestCase):
    def test_search_proves_two_plus_one_equals_three(self):
        state = build_initial_knowledge()
        searcher = BoundedProofSearcher(
            max_depth=5,
            instantiation_rounds=1,
        )
        goal = Eq(Add(TWO, ONE), THREE)

        result = searcher.prove(goal, state)

        self.assertTrue(result.found)
        self.assertIsNotNone(result.proof)
        self.assertIsNotNone(result.check)
        self.assertTrue(result.check.valid, result.check.errors)
        self.assertEqual(result.proof.statement, goal)
        self.assertGreater(len(result.proof.steps), 1)

        rules = [step.rule for step in result.proof.steps]
        self.assertIn("FORALL_ELIM", rules)
        self.assertIn("EQ_TRANSITIVITY", rules)

    def test_generated_proof_rechecks_with_trusted_checker(self):
        state = build_initial_knowledge()
        searcher = BoundedProofSearcher(
            max_depth=5,
            instantiation_rounds=1,
        )
        goal = Eq(Add(TWO, ONE), THREE)

        result = searcher.prove(goal, state)
        self.assertIsNotNone(result.proof)

        check = check_proof(
            result.proof,
            axioms=state.world.axioms,
            known_theorems=tuple(state.theorems.values()),
        )

        self.assertTrue(check.valid, check.errors)

    def test_search_can_add_only_verified_theorem(self):
        state = build_initial_knowledge()
        searcher = BoundedProofSearcher(
            max_depth=5,
            instantiation_rounds=1,
        )
        goal = Eq(Add(TWO, ONE), THREE)

        theorem = searcher.prove_and_add(
            state,
            "AUTO_TWO_PLUS_ONE",
            goal,
        )

        self.assertEqual(theorem.statement, goal)
        self.assertIn("AUTO_TWO_PLUS_ONE", state.theorems)
        self.assertGreater(len(theorem.dependencies), 0)

    def test_search_rejects_open_variable_goal(self):
        state = build_initial_knowledge()
        searcher = BoundedProofSearcher()
        goal = Eq(Add(X, ONE), Add(ONE, X))

        with self.assertRaisesRegex(ValueError, "ground goals"):
            searcher.prove(goal, state)

    def test_bounded_search_does_not_prove_false_equality(self):
        state = build_initial_knowledge()
        searcher = BoundedProofSearcher(
            max_depth=4,
            instantiation_rounds=1,
        )
        goal = Eq(ONE, TWO)

        result = searcher.prove(goal, state)

        self.assertFalse(result.found)
        self.assertIsNone(result.proof)


if __name__ == "__main__":
    unittest.main()
