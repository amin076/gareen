import unittest

from math_world import (
    ADD_SUCC,
    ADD_ZERO,
    ARITHMETIC_PRIMITIVES,
    AXIOM_ADD_SUCCESSOR,
    AXIOM_ADD_ZERO,
    AXIOM_S_INJECTIVE,
    AXIOM_S_NONZERO,
    DEFINITIONS,
    INFERENCE_RULES,
    LOGICAL_PRIMITIVES,
    ONE,
    RULE_ASSUMPTION,
    RULE_AXIOM,
    RULE_FORALL_ELIM,
    RULE_FORALL_INTRO,
    RULE_INDUCTION,
    THREE,
    TWO,
    Add,
    Eq,
    ForAll,
    Not,
    Proof,
    ProofStep,
    Succ,
    X,
    Y,
    Z,
    ZERO,
    build_initial_knowledge,
    check_proof,
    normalize,
    rewrite_once,
)


class FormalWorldTests(unittest.TestCase):
    def test_arithmetic_primitives_are_explicit(self):
        self.assertEqual(
            [x.name for x in ARITHMETIC_PRIMITIVES],
            ["0", "S", "Add"],
        )

    def test_logical_primitives_are_explicit(self):
        self.assertEqual(
            [x.name for x in LOGICAL_PRIMITIVES],
            ["=", "¬", "→", "∀", "⊥"],
        )

    def test_numerals_are_definitions_not_primitives(self):
        self.assertEqual([x.name for x in DEFINITIONS], ["1", "2", "3"])
        self.assertEqual(ONE, Succ(ZERO))
        self.assertEqual(TWO, Succ(Succ(ZERO)))
        self.assertEqual(THREE, Succ(Succ(Succ(ZERO))))

    def test_axioms_are_formal_statements(self):
        self.assertIn("S(x)", str(AXIOM_S_NONZERO))
        self.assertIn("S(y)", str(AXIOM_S_INJECTIVE))
        self.assertIn("Add(x, 0)", str(AXIOM_ADD_ZERO))
        self.assertIn("Add(x, S(y))", str(AXIOM_ADD_SUCCESSOR))

    def test_inference_rules_are_declared(self):
        names = [rule.name for rule in INFERENCE_RULES]
        self.assertIn("FORALL_ELIM", names)
        self.assertIn("FORALL_INTRO", names)
        self.assertIn("MODUS_PONENS", names)
        self.assertIn("NEGATION_INTRO", names)
        self.assertIn("EQ_SUCC_CONGRUENCE", names)
        self.assertIn("EQ_TRANSITIVITY", names)
        self.assertIn("INDUCTION", names)


class ProofEngineTests(unittest.TestCase):
    def test_direct_universal_instance_is_verified(self):
        statement = Not(Eq(ONE, ZERO))
        proof = Proof(
            statement=statement,
            steps=(
                ProofStep(
                    conclusion=AXIOM_S_NONZERO.formula,
                    rule=RULE_AXIOM,
                    source=AXIOM_S_NONZERO.name,
                ),
                ProofStep(
                    conclusion=statement,
                    rule=RULE_FORALL_ELIM,
                    premises=(0,),
                    term=ZERO,
                ),
            ),
        )

        result = check_proof(proof)
        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.open_assumptions, frozenset())

    def test_open_assumption_is_rejected(self):
        assumption = Eq(ONE, TWO)
        proof = Proof(
            statement=assumption,
            steps=(
                ProofStep(
                    conclusion=assumption,
                    rule=RULE_ASSUMPTION,
                ),
            ),
        )

        result = check_proof(proof)
        self.assertFalse(result.valid)
        self.assertIn("open assumptions", " ".join(result.errors))

    def test_fake_axiom_reference_is_rejected(self):
        proof = Proof(
            statement=Eq(ONE, ONE),
            steps=(
                ProofStep(
                    conclusion=Eq(ONE, ONE),
                    rule=RULE_AXIOM,
                    source="NOT_A_REAL_AXIOM",
                ),
            ),
        )

        result = check_proof(proof)
        self.assertFalse(result.valid)

    def test_initial_knowledge_contains_verified_theorems(self):
        state = build_initial_knowledge()

        self.assertEqual(
            list(state.theorems),
            [
                "T1_ONE_NONZERO",
                "T2_ONE_NE_TWO",
                "T3_TWO_NE_THREE",
                "T4_TWO_PLUS_ZERO",
                "T5_ZERO_PLUS_X",
                "T6_SUCC_ADD",
                "T7_ADD_COMMUTATIVE",
            ],
        )
        self.assertEqual(
            state.theorems["T1_ONE_NONZERO"].statement,
            Not(Eq(ONE, ZERO)),
        )
        self.assertEqual(
            state.theorems["T2_ONE_NE_TWO"].statement,
            Not(Eq(ONE, TWO)),
        )
        self.assertEqual(
            state.theorems["T3_TWO_NE_THREE"].statement,
            Not(Eq(TWO, THREE)),
        )
        self.assertEqual(
            state.theorems["T4_TWO_PLUS_ZERO"].statement,
            Eq(Add(TWO, ZERO), TWO),
        )
        self.assertEqual(
            state.theorems["T5_ZERO_PLUS_X"].statement,
            ForAll(X, Eq(Add(ZERO, X), X)),
        )
        self.assertEqual(
            state.theorems["T6_SUCC_ADD"].statement,
            ForAll(
                X,
                ForAll(
                    Z,
                    Eq(Add(Succ(X), Z), Succ(Add(X, Z))),
                ),
            ),
        )
        self.assertEqual(
            state.theorems["T7_ADD_COMMUTATIVE"].statement,
            ForAll(
                X,
                ForAll(
                    Y,
                    Eq(Add(X, Y), Add(Y, X)),
                ),
            ),
        )

    def test_induction_theorem_depends_on_addition_axioms(self):
        state = build_initial_knowledge()
        dependencies = state.theorems["T5_ZERO_PLUS_X"].dependencies

        self.assertIn(AXIOM_ADD_ZERO.name, dependencies)
        self.assertIn(AXIOM_ADD_SUCCESSOR.name, dependencies)

    def test_invalid_induction_base_is_rejected(self):
        predicate = Eq(Add(ZERO, X), X)
        bad_base = Eq(Add(ZERO, ZERO), ONE)
        step_case = Eq(Add(ZERO, Succ(X)), Succ(X))

        proof = Proof(
            statement=ForAll(X, predicate),
            steps=(
                ProofStep(
                    conclusion=bad_base,
                    rule=RULE_ASSUMPTION,
                ),
                ProofStep(
                    conclusion=predicate,
                    rule=RULE_ASSUMPTION,
                ),
                ProofStep(
                    conclusion=step_case,
                    rule=RULE_ASSUMPTION,
                    premises=(),
                ),
                ProofStep(
                    conclusion=ForAll(X, predicate),
                    rule=RULE_INDUCTION,
                    premises=(0, 2),
                    variable=X,
                    discharge=1,
                ),
            ),
        )

        result = check_proof(proof)
        self.assertFalse(result.valid)
        self.assertIn("base case", " ".join(result.errors))

    def test_invalid_forall_intro_from_open_assumption_is_rejected(self):
        assumption = Eq(X, ZERO)
        proof = Proof(
            statement=ForAll(X, assumption),
            steps=(
                ProofStep(
                    conclusion=assumption,
                    rule=RULE_ASSUMPTION,
                ),
                ProofStep(
                    conclusion=ForAll(X, assumption),
                    rule=RULE_FORALL_INTRO,
                    premises=(0,),
                    variable=X,
                ),
            ),
        )

        result = check_proof(proof)
        self.assertFalse(result.valid)
        self.assertIn("free in open assumption", " ".join(result.errors))

    def test_commutativity_depends_on_prior_general_theorems(self):
        state = build_initial_knowledge()
        dependencies = state.theorems["T7_ADD_COMMUTATIVE"].dependencies

        self.assertIn("T5_ZERO_PLUS_X", dependencies)
        self.assertIn("T6_SUCC_ADD", dependencies)

    def test_later_theorem_depends_on_earlier_theorem(self):
        state = build_initial_knowledge()

        self.assertIn(
            "T2_ONE_NE_TWO",
            state.theorems["T3_TWO_NE_THREE"].dependencies,
        )

    def test_all_initial_theorem_proofs_recheck(self):
        state = build_initial_knowledge()
        accepted = []

        for theorem in state.theorems.values():
            result = check_proof(
                theorem.proof,
                known_theorems=tuple(
                    state.theorems[name]
                    for name in accepted
                ),
            )
            self.assertTrue(result.valid, (theorem.name, result.errors))
            accepted.append(theorem.name)


class SymbolicArithmeticTests(unittest.TestCase):
    def test_add_zero_rule(self):
        step = rewrite_once(Add(TWO, ZERO))
        self.assertIsNotNone(step)
        self.assertEqual(step.rule, ADD_ZERO)
        self.assertEqual(step.after, TWO)

    def test_add_successor_rule(self):
        step = rewrite_once(Add(ONE, Succ(TWO)))
        self.assertIsNotNone(step)
        self.assertEqual(step.rule, ADD_SUCC)
        self.assertEqual(step.after, Succ(Add(ONE, TWO)))

    def test_two_plus_three(self):
        five = Succ(Succ(Succ(Succ(Succ(ZERO)))))
        result, trace = normalize(Add(TWO, THREE))
        self.assertEqual(result, five)
        self.assertEqual(len(trace), 4)
        self.assertEqual(trace[-1].rule, ADD_ZERO)

    def test_normal_form(self):
        result, trace = normalize(THREE)
        self.assertEqual(result, THREE)
        self.assertEqual(trace, ())


if __name__ == "__main__":
    unittest.main()
