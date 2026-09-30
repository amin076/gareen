import unittest

from general_conjecture import (
    GeneralConjecture,
    GeneralConjectureExplorer,
    GeneralProofSearcher,
    PatternObservation,
    generate_general_conjectures,
    generate_unary_expression_grammar,
    mine_pattern_classes,
    observe_expression,
)
from math_world import (
    ONE,
    X,
    ZERO,
    Add,
    Eq,
    ForAll,
    Succ,
    build_initial_knowledge,
    check_proof,
)
from proof_search import BoundedProofSearcher


class GeneralConjectureDiscoveryTests(unittest.TestCase):
    def test_pattern_mining_generates_general_conjectures_without_goal(self):
        state = build_initial_knowledge()
        expressions = generate_unary_expression_grammar()
        classes = mine_pattern_classes(expressions)
        conjectures = generate_general_conjectures(expressions, state)

        self.assertGreater(len(expressions), 4)
        self.assertGreater(len(classes), 0)
        self.assertGreater(len(conjectures), 0)
        self.assertTrue(
            all(isinstance(item.statement, ForAll) for item in conjectures)
        )

    def test_existing_zero_right_addition_is_not_rediscovered(self):
        state = build_initial_knowledge()
        expressions = generate_unary_expression_grammar()
        conjectures = generate_general_conjectures(expressions, state)

        existing = ForAll(X, Eq(Add(X, ZERO), X))
        reversed_existing = ForAll(X, Eq(X, Add(X, ZERO)))

        statements = {str(item.statement) for item in conjectures}
        self.assertNotIn(str(existing), statements)
        self.assertNotIn(str(reversed_existing), statements)

    def test_pattern_miner_proposes_x_plus_one_equals_successor(self):
        state = build_initial_knowledge()
        expressions = generate_unary_expression_grammar()
        conjectures = generate_general_conjectures(expressions, state)

        target_keys = {
            str(ForAll(X, Eq(Add(X, ONE), Succ(X)))),
            str(ForAll(X, Eq(Succ(X), Add(X, ONE)))),
        }

        self.assertTrue(
            target_keys.intersection(
                {str(item.statement) for item in conjectures}
            )
        )

    def test_general_proof_search_can_prove_symbolic_x_plus_one(self):
        state = build_initial_knowledge()
        left = observe_expression(Add(X, ONE))
        right = observe_expression(Succ(X))
        conjecture = GeneralConjecture(
            body=Eq(Add(X, ONE), Succ(X)),
            statement=ForAll(X, Eq(Add(X, ONE), Succ(X))),
            left_observation=left,
            right_observation=right,
            heuristic_score=1,
        )

        searcher = GeneralProofSearcher(
            BoundedProofSearcher(
                max_depth=5,
                max_terms=24,
                instantiation_rounds=1,
                allow_open_goals=True,
            )
        )
        result = searcher.prove(conjecture, state)

        self.assertTrue(result.found)
        self.assertIsNotNone(result.proof)
        self.assertIsNotNone(result.check)
        self.assertTrue(result.check.valid, result.check.errors)
        self.assertEqual(result.proof.statement, conjecture.statement)
        self.assertEqual(result.proof.steps[-1].rule, "FORALL_INTRO")

    def test_false_general_law_is_not_proved(self):
        state = build_initial_knowledge()
        searcher = BoundedProofSearcher(
            max_depth=4,
            max_terms=20,
            instantiation_rounds=1,
            allow_open_goals=True,
        )

        result = searcher.prove(Eq(X, ZERO), state)

        self.assertFalse(result.found)
        self.assertIsNone(result.proof)

    def test_explorer_accepts_at_least_one_verified_general_theorem(self):
        state = build_initial_knowledge()
        initial_names = set(state.theorems)

        explorer = GeneralConjectureExplorer(
            max_attempts=6,
            max_discoveries=1,
            min_proof_steps=4,
            proof_searcher=GeneralProofSearcher(
                BoundedProofSearcher(
                    max_depth=5,
                    max_terms=24,
                    instantiation_rounds=1,
                    allow_open_goals=True,
                )
            ),
        )
        report = explorer.explore(state)

        self.assertGreater(report.generated_conjectures, 0)
        self.assertGreater(report.attempted_conjectures, 0)
        self.assertGreaterEqual(report.accepted_theorems, 1)

        discovery = report.discoveries[0]
        self.assertNotIn(discovery.theorem_name, initial_names)
        self.assertIn(discovery.theorem_name, state.theorems)
        self.assertIsInstance(discovery.statement, ForAll)

        theorem = state.theorems[discovery.theorem_name]
        known = tuple(
            other
            for name, other in state.theorems.items()
            if name != discovery.theorem_name
        )
        check = check_proof(
            theorem.proof,
            axioms=state.world.axioms,
            known_theorems=known,
        )
        self.assertTrue(check.valid, check.errors)


if __name__ == "__main__":
    unittest.main()
