import unittest

from artificial_mathematician import ResearchConjecture
from math_world import (
    Add,
    Eq,
    ForAll,
    KnowledgeState,
    Mul,
    ONE,
    TWO,
    X,
    Y,
    ZERO,
    build_initial_knowledge,
)
from research_value import (
    assess_research_value,
    known_derivation_distance,
    primitive_rewrite_distance,
    rank_research_conjectures,
)


def unary(left, right):
    return ResearchConjecture(
        statement=ForAll(X, Eq(left, right)),
        body=Eq(left, right),
        variables=(X,),
        heuristic_score=5,
        evidence="test",
    )


def bivariate(left, right):
    return ResearchConjecture(
        statement=ForAll(X, ForAll(Y, Eq(left, right))),
        body=Eq(left, right),
        variables=(X, Y),
        heuristic_score=8,
        evidence="test",
    )


class ResearchValueTests(unittest.TestCase):
    def test_x_plus_zero_is_routine_primitive_rewrite(self):
        conjecture = unary(Add(X, ZERO), X)

        assessment = assess_research_value(
            conjecture,
            KnowledgeState(),
        )

        self.assertFalse(assessment.accepted)
        self.assertTrue(assessment.primitive_rewrite_equivalent)
        self.assertEqual(assessment.primitive_rewrite_steps, 1)

    def test_nested_zero_variant_is_filtered_before_proving(self):
        conjecture = unary(
            Add(X, Add(X, ZERO)),
            Add(X, X),
        )

        assessment = assess_research_value(
            conjecture,
            KnowledgeState(),
        )

        self.assertFalse(assessment.accepted)
        self.assertIn("primitive arithmetic rewrites", assessment.reason)

    def test_ground_numeric_example_is_evidence_not_discovery(self):
        conjecture = ResearchConjecture(
            statement=Eq(Add(TWO, ZERO), TWO),
            body=Eq(Add(TWO, ZERO), TWO),
            variables=(),
            heuristic_score=1,
            evidence="numeric observation",
        )

        assessment = assess_research_value(
            conjecture,
            KnowledgeState(),
        )

        self.assertFalse(assessment.accepted)
        self.assertIn("ground numerical instance", assessment.reason)

    def test_existing_commutativity_is_one_step_from_known_theorem(self):
        state = build_initial_knowledge()
        conjecture = bivariate(
            Add(X, Y),
            Add(Y, X),
        )

        distance = known_derivation_distance(
            conjecture,
            state,
            max_steps=2,
        )
        assessment = assess_research_value(
            conjecture,
            state,
            min_reasoning_steps=3,
        )

        self.assertEqual(distance, 1)
        self.assertFalse(assessment.accepted)
        self.assertIn("too close to existing verified knowledge", assessment.reason)

    def test_commutativity_can_be_research_worthy_without_prior_theorem(self):
        conjecture = bivariate(
            Add(X, Y),
            Add(Y, X),
        )

        assessment = assess_research_value(
            conjecture,
            KnowledgeState(),
            min_reasoning_steps=3,
        )

        self.assertTrue(assessment.accepted)
        self.assertIsNone(assessment.known_derivation_distance)
        self.assertGreaterEqual(assessment.score, 14)

    def test_x_times_one_is_filtered_when_prior_theorem_is_loaded(self):
        state = build_initial_knowledge()
        conjecture = unary(Mul(X, ONE), X)

        assessment = assess_research_value(
            conjecture,
            state,
            min_reasoning_steps=3,
        )

        self.assertFalse(assessment.accepted)
        self.assertEqual(assessment.known_derivation_distance, 1)

    def test_one_times_x_is_filtered_as_two_step_known_consequence(self):
        state = build_initial_knowledge()
        conjecture = unary(Mul(ONE, X), X)

        assessment = assess_research_value(
            conjecture,
            state,
            min_reasoning_steps=3,
        )

        self.assertFalse(assessment.accepted)
        self.assertEqual(assessment.known_derivation_distance, 2)

    def test_ranking_places_research_worthy_before_routine(self):
        interesting = bivariate(Add(X, Y), Add(Y, X))
        routine = unary(Add(X, ZERO), X)

        ranked = rank_research_conjectures(
            (routine, interesting),
            KnowledgeState(),
        )

        self.assertTrue(ranked[0].assessment.accepted)
        self.assertEqual(ranked[0].conjecture, interesting)
        self.assertFalse(ranked[-1].assessment.accepted)


if __name__ == "__main__":
    unittest.main()
