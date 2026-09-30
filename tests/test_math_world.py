import unittest

from math_world import (
    ADD_SUCC, ADD_ZERO, ARITHMETIC_PRIMITIVES,
    AXIOM_ADD_SUCCESSOR, AXIOM_ADD_ZERO, AXIOM_S_INJECTIVE, AXIOM_S_NONZERO,
    DEFINITIONS, LOGICAL_PRIMITIVES, ONE, THREE, TWO,
    Add, Succ, ZERO, normalize, rewrite_once,
)

class FormalWorldTests(unittest.TestCase):
    def test_arithmetic_primitives_are_explicit(self):
        self.assertEqual([x.name for x in ARITHMETIC_PRIMITIVES], ["0", "S", "Add"])

    def test_equality_is_logical_primitive(self):
        self.assertEqual([x.name for x in LOGICAL_PRIMITIVES], ["="])

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
