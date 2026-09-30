import unittest

from math_world import (
    ADD_SUCC,
    ADD_ZERO,
    Add,
    Succ,
    ZERO,
    normalize,
    rewrite_once,
)


class SymbolicArithmeticTests(unittest.TestCase):
    def test_add_zero_rule(self) -> None:
        a = Succ(Succ(ZERO))
        expr = Add(a, ZERO)

        step = rewrite_once(expr)

        self.assertIsNotNone(step)
        assert step is not None
        self.assertEqual(step.rule, ADD_ZERO)
        self.assertEqual(step.after, a)

    def test_add_successor_rule(self) -> None:
        a = Succ(ZERO)
        b = Succ(Succ(ZERO))
        expr = Add(a, Succ(b))

        step = rewrite_once(expr)

        self.assertIsNotNone(step)
        assert step is not None
        self.assertEqual(step.rule, ADD_SUCC)
        self.assertEqual(step.after, Succ(Add(a, b)))

    def test_symbolic_two_plus_three_normalizes_to_five_successors(self) -> None:
        one = Succ(ZERO)
        two = Succ(one)
        three = Succ(two)
        five = Succ(Succ(Succ(Succ(Succ(ZERO)))))

        result, trace = normalize(Add(two, three))

        self.assertEqual(result, five)
        self.assertEqual(len(trace), 4)
        self.assertEqual(trace[-1].rule, ADD_ZERO)

    def test_normal_form_has_no_available_rewrite(self) -> None:
        normal = Succ(Succ(Succ(ZERO)))

        result, trace = normalize(normal)

        self.assertEqual(result, normal)
        self.assertEqual(trace, ())


if __name__ == "__main__":
    unittest.main()
