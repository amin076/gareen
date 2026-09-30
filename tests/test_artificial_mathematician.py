import unittest

from artificial_mathematician import (
    ArtificialMathematician,
    InductionSynthesizer,
    ResearchConjecture,
    StrategySelector,
    generate_bivariate_conjectures,
    generate_research_conjectures,
)
from math_world import (
    X,
    Y,
    ZERO,
    Add,
    Eq,
    ForAll,
    KnowledgeState,
    check_proof,
)
from proof_search import BoundedProofSearcher


class ArtificialMathematicianTests(unittest.TestCase):
    def test_induction_synthesizer_rediscovers_zero_plus_x_from_axioms_only(self):
        state = KnowledgeState()
        statement = ForAll(X, Eq(Add(ZERO, X), X))
        conjecture = ResearchConjecture(
            statement=statement,
            body=Eq(Add(ZERO, X), X),
            variables=(X,),
            heuristic_score=1,
            evidence="Synthetic test conjecture.",
        )

        selector = StrategySelector(
            direct_searcher=BoundedProofSearcher(
                max_depth=5,
                max_terms=28,
                instantiation_rounds=1,
                allow_open_goals=True,
            ),
            induction=InductionSynthesizer(
                BoundedProofSearcher(
                    max_depth=6,
                    max_terms=32,
                    instantiation_rounds=1,
                    allow_open_goals=True,
                )
            ),
        )

        result = selector.solve(conjecture, state, lemma_budget=0)

        self.assertTrue(result.found)
        self.assertEqual(result.strategy, "induction")
        self.assertIsNotNone(result.proof)
        self.assertIsNotNone(result.check)
        self.assertTrue(result.check.valid, result.check.errors)
        self.assertIn("INDUCTION", [step.rule for step in result.proof.steps])

    def test_bivariate_miner_proposes_addition_commutativity_from_samples(self):
        state = KnowledgeState()
        conjectures = generate_bivariate_conjectures(state)

        targets = {
            str(ForAll(X, ForAll(Y, Eq(Add(X, Y), Add(Y, X))))),
            str(ForAll(X, ForAll(Y, Eq(Add(Y, X), Add(X, Y))))),
        }

        self.assertTrue(
            targets.intersection({str(item.statement) for item in conjectures})
        )

    def test_research_conjectures_include_unary_and_bivariate_laws(self):
        state = KnowledgeState()
        conjectures = generate_research_conjectures(state)

        self.assertGreater(len(conjectures), 0)
        self.assertTrue(any(len(item.variables) == 1 for item in conjectures))
        self.assertTrue(any(len(item.variables) == 2 for item in conjectures))

    def test_artificial_mathematician_accepts_verified_theorem_from_seed_state(self):
        mathematician = ArtificialMathematician(
            max_attempts=6,
            max_discoveries=1,
            lemma_budget=1,
        )

        state, notebook = mathematician.research(KnowledgeState())

        self.assertGreater(notebook.generated_conjectures, 0)
        self.assertGreater(notebook.attempted_conjectures, 0)
        self.assertGreaterEqual(notebook.accepted_theorems, 1)

        discovery = notebook.discoveries[0]
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

    def test_false_general_statement_is_not_synthesized_by_induction(self):
        state = KnowledgeState()
        false_statement = ForAll(X, Eq(X, ZERO))
        conjecture = ResearchConjecture(
            statement=false_statement,
            body=Eq(X, ZERO),
            variables=(X,),
            heuristic_score=1,
            evidence="Deliberately false test.",
        )

        synthesizer = InductionSynthesizer(
            BoundedProofSearcher(
                max_depth=4,
                max_terms=20,
                instantiation_rounds=1,
                allow_open_goals=True,
            )
        )
        proof = synthesizer.synthesize(conjecture, state)

        self.assertIsNone(proof)


if __name__ == "__main__":
    unittest.main()
