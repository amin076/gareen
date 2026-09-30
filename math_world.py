"""Gareen Phase 2: explicit primitives, definitions, axioms, and symbolic rewriting."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple

class Expr:
    pass

@dataclass(frozen=True)
class Var(Expr):
    name: str
    def __str__(self) -> str:
        return self.name

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
X = Var("x")
Y = Var("y")

class Formula:
    pass

@dataclass(frozen=True)
class Eq(Formula):
    left: Expr
    right: Expr
    def __str__(self) -> str:
        return f"{self.left} = {self.right}"

@dataclass(frozen=True)
class Not(Formula):
    formula: Formula
    def __str__(self) -> str:
        return f"¬({self.formula})"

@dataclass(frozen=True)
class Implies(Formula):
    premise: Formula
    conclusion: Formula
    def __str__(self) -> str:
        return f"({self.premise}) → ({self.conclusion})"

@dataclass(frozen=True)
class ForAll(Formula):
    variable: Var
    body: Formula
    def __str__(self) -> str:
        return f"∀{self.variable}. ({self.body})"

@dataclass(frozen=True)
class PrimitiveSymbol:
    name: str
    category: str
    arity: int
    description: str

@dataclass(frozen=True)
class Definition:
    name: str
    expression: Expr
    description: str
    def __str__(self) -> str:
        return f"{self.name} := {self.expression}"

@dataclass(frozen=True)
class Axiom:
    name: str
    formula: Formula
    description: str
    def __str__(self) -> str:
        return f"{self.name}: {self.formula}"

@dataclass(frozen=True)
class FormalWorld:
    arithmetic_primitives: tuple[PrimitiveSymbol, ...]
    logical_primitives: tuple[PrimitiveSymbol, ...]
    definitions: tuple[Definition, ...]
    axioms: tuple[Axiom, ...]

ARITHMETIC_PRIMITIVES = (
    PrimitiveSymbol("0", "constant", 0, "Distinguished zero symbol."),
    PrimitiveSymbol("S", "function", 1, "Successor function symbol."),
    PrimitiveSymbol("Add", "function", 2, "Binary addition function symbol."),
)

LOGICAL_PRIMITIVES = (
    PrimitiveSymbol("=", "relation", 2, "Logical equality relation."),
)

ONE = Succ(ZERO)
TWO = Succ(ONE)
THREE = Succ(TWO)

DEFINITIONS = (
    Definition("1", ONE, "One is defined as the successor of zero."),
    Definition("2", TWO, "Two is defined as the successor of one."),
    Definition("3", THREE, "Three is defined as the successor of two."),
)

AXIOM_S_NONZERO = Axiom(
    "A1_SUCCESSOR_NONZERO",
    ForAll(X, Not(Eq(Succ(X), ZERO))),
    "Zero is not the successor of any object.",
)

AXIOM_S_INJECTIVE = Axiom(
    "A2_SUCCESSOR_INJECTIVE",
    ForAll(X, ForAll(Y, Implies(Eq(Succ(X), Succ(Y)), Eq(X, Y)))),
    "Equal successors have equal predecessors.",
)

AXIOM_ADD_ZERO = Axiom(
    "A3_ADD_ZERO",
    ForAll(X, Eq(Add(X, ZERO), X)),
    "Adding zero on the right leaves a term unchanged.",
)

AXIOM_ADD_SUCCESSOR = Axiom(
    "A4_ADD_SUCCESSOR",
    ForAll(X, ForAll(Y, Eq(Add(X, Succ(Y)), Succ(Add(X, Y))))),
    "Addition is defined recursively on the second argument.",
)

AXIOMS = (
    AXIOM_S_NONZERO,
    AXIOM_S_INJECTIVE,
    AXIOM_ADD_ZERO,
    AXIOM_ADD_SUCCESSOR,
)

WORLD = FormalWorld(
    arithmetic_primitives=ARITHMETIC_PRIMITIVES,
    logical_primitives=LOGICAL_PRIMITIVES,
    definitions=DEFINITIONS,
    axioms=AXIOMS,
)

@dataclass(frozen=True)
class RewriteStep:
    before: Expr
    after: Expr
    rule: str

ADD_ZERO = AXIOM_ADD_ZERO.name
ADD_SUCC = AXIOM_ADD_SUCCESSOR.name

def rewrite_once(expr: Expr) -> Optional[RewriteStep]:
    if isinstance(expr, Add):
        if isinstance(expr.right, Zero):
            return RewriteStep(expr, expr.left, ADD_ZERO)
        if isinstance(expr.right, Succ):
            return RewriteStep(expr, Succ(Add(expr.left, expr.right.value)), ADD_SUCC)

        left_step = rewrite_once(expr.left)
        if left_step is not None:
            return RewriteStep(expr, Add(left_step.after, expr.right), left_step.rule)

        right_step = rewrite_once(expr.right)
        if right_step is not None:
            return RewriteStep(expr, Add(expr.left, right_step.after), right_step.rule)
        return None

    if isinstance(expr, Succ):
        inner_step = rewrite_once(expr.value)
        if inner_step is None:
            return None
        return RewriteStep(expr, Succ(inner_step.after), inner_step.rule)

    if isinstance(expr, (Zero, Var)):
        return None

    raise TypeError(f"Unsupported expression type: {type(expr)!r}")

def normalize(expr: Expr, max_steps: int = 1000) -> Tuple[Expr, tuple[RewriteStep, ...]]:
    current = expr
    trace: list[RewriteStep] = []
    for _ in range(max_steps):
        step = rewrite_once(current)
        if step is None:
            return current, tuple(trace)
        trace.append(step)
        current = step.after
    raise RuntimeError("Normalization exceeded max_steps")

def print_world() -> None:
    print("Arithmetic primitives:")
    for item in WORLD.arithmetic_primitives:
        print(f"  - {item.name} ({item.category}, arity={item.arity})")
    print("\nLogical primitives:")
    for item in WORLD.logical_primitives:
        print(f"  - {item.name} ({item.category}, arity={item.arity})")
    print("\nDefinitions:")
    for definition in WORLD.definitions:
        print(f"  - {definition}")
    print("\nAxioms:")
    for axiom in WORLD.axioms:
        print(f"  - {axiom}")

def phase2_demo() -> None:
    print("Gareen Phase 2")
    print("================")
    print_world()
    expression = Add(TWO, THREE)
    result, trace = normalize(expression)
    print("\nSymbolic run:")
    print("Start :", expression)
    for index, step in enumerate(trace, start=1):
        print(f"{index:>2}. {step.rule}")
        print("    ", step.before, "=>", step.after)
    print("Result:", result)

if __name__ == "__main__":
    phase2_demo()
