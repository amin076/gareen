"""Gareen Phase 1: a tiny symbolic arithmetic world.

Important boundary:
- Python executes this program at the meta-level.
- Arithmetic inside the object-world is NOT delegated to Python integers.
- Zero, successor, and addition are represented as symbolic expressions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


class Expr:
    """Base class for object-world expressions."""


@dataclass(frozen=True)
class Zero(Expr):
    def __str__(self) -> str:
        return "0"


@dataclass(frozen=True)
class Succ(Expr):
    value: Expr

    def __str__(self) -> str:
        return f"S({self.value})"


@dataclass(frozen=True)
class Add(Expr):
    left: Expr
    right: Expr

    def __str__(self) -> str:
        return f"Add({self.left}, {self.right})"


ZERO = Zero()


@dataclass(frozen=True)
class RewriteStep:
    before: Expr
    after: Expr
    rule: str


ADD_ZERO = "ADD_ZERO: Add(a, 0) -> a"
ADD_SUCC = "ADD_SUCC: Add(a, S(b)) -> S(Add(a, b))"


def rewrite_once(expr: Expr) -> Optional[RewriteStep]:
    """Apply exactly one legal object-world rewrite.

    Root rewrites are preferred. If none applies, the function searches
    subexpressions from left to right. Python performs tree manipulation only;
    it does not evaluate arithmetic for the object-world.
    """

    if isinstance(expr, Add):
        if isinstance(expr.right, Zero):
            return RewriteStep(expr, expr.left, ADD_ZERO)

        if isinstance(expr.right, Succ):
            after = Succ(Add(expr.left, expr.right.value))
            return RewriteStep(expr, after, ADD_SUCC)

        left_step = rewrite_once(expr.left)
        if left_step is not None:
            return RewriteStep(
                expr,
                Add(left_step.after, expr.right),
                left_step.rule,
            )

        right_step = rewrite_once(expr.right)
        if right_step is not None:
            return RewriteStep(
                expr,
                Add(expr.left, right_step.after),
                right_step.rule,
            )

        return None

    if isinstance(expr, Succ):
        inner_step = rewrite_once(expr.value)
        if inner_step is None:
            return None
        return RewriteStep(expr, Succ(inner_step.after), inner_step.rule)

    if isinstance(expr, Zero):
        return None

    raise TypeError(f"Unsupported expression type: {type(expr)!r}")


def normalize(expr: Expr, max_steps: int = 1000) -> Tuple[Expr, tuple[RewriteStep, ...]]:
    """Rewrite until no rule applies, while retaining a proof-like trace."""

    current = expr
    trace: list[RewriteStep] = []

    for _ in range(max_steps):
        step = rewrite_once(current)
        if step is None:
            return current, tuple(trace)
        trace.append(step)
        current = step.after

    raise RuntimeError("Normalization exceeded max_steps")


def phase1_demo() -> None:
    """Demonstrate two successors plus three successors symbolically.

    The object-world expression is built only from Zero, Succ, and Add.
    """

    one = Succ(ZERO)
    two = Succ(one)
    three = Succ(two)

    expression = Add(two, three)
    result, trace = normalize(expression)

    print("Gareen Phase 1")
    print("Start :", expression)
    for index, step in enumerate(trace, start=1):
        print(f"{index:>2}. {step.rule}")
        print("    ", step.before, "=>", step.after)
    print("Result:", result)


if __name__ == "__main__":
    phase1_demo()
