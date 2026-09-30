"""Gareen Phase 7: verified multiplication laws.

The host Python runtime is meta-level infrastructure. Mathematical knowledge is
accepted into Gareen only when it is represented in the object-world and passes
the proof checker using declared axioms, definitions, and inference rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple


class Expr:
    """Base class for arithmetic terms in Gareen's object-language."""


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


@dataclass(frozen=True)
class Mul(Expr):
    left: Expr
    right: Expr

    def __str__(self) -> str:
        return f"Mul({self.left}, {self.right})"


ZERO = Zero()
X = Var("x")
Y = Var("y")
Z = Var("z")
W = Var("w")


class Formula:
    """Base class for formulas in Gareen's object-language."""


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
class Bottom(Formula):
    def __str__(self) -> str:
        return "⊥"


BOTTOM = Bottom()


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
class InferenceRule:
    name: str
    description: str


@dataclass(frozen=True)
class FormalWorld:
    arithmetic_primitives: tuple[PrimitiveSymbol, ...]
    logical_primitives: tuple[PrimitiveSymbol, ...]
    definitions: tuple[Definition, ...]
    axioms: tuple[Axiom, ...]
    inference_rules: tuple[InferenceRule, ...]


ARITHMETIC_PRIMITIVES = (
    PrimitiveSymbol("0", "constant", 0, "Distinguished zero symbol."),
    PrimitiveSymbol("S", "function", 1, "Successor function symbol."),
    PrimitiveSymbol("Add", "function", 2, "Binary addition function symbol."),
    PrimitiveSymbol("Mul", "function", 2, "Binary multiplication function symbol."),
)

LOGICAL_PRIMITIVES = (
    PrimitiveSymbol("=", "relation", 2, "Logical equality relation."),
    PrimitiveSymbol("¬", "connective", 1, "Logical negation."),
    PrimitiveSymbol("→", "connective", 2, "Logical implication."),
    PrimitiveSymbol("∀", "quantifier", 1, "Universal quantifier."),
    PrimitiveSymbol("⊥", "logical constant", 0, "Contradiction / falsum."),
)

ONE = Succ(ZERO)
TWO = Succ(ONE)
THREE = Succ(TWO)

DEFINITIONS = (
    Definition("1", ONE, "One is the successor of zero."),
    Definition("2", TWO, "Two is the successor of one."),
    Definition("3", THREE, "Three is the successor of two."),
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
    "Addition is characterized recursively on the second argument.",
)

AXIOM_MUL_ZERO = Axiom(
    "A5_MUL_ZERO",
    ForAll(X, Eq(Mul(X, ZERO), ZERO)),
    "Multiplying by zero on the right gives zero.",
)

AXIOM_MUL_SUCCESSOR = Axiom(
    "A6_MUL_SUCCESSOR",
    ForAll(
        X,
        ForAll(
            Y,
            Eq(Mul(X, Succ(Y)), Add(Mul(X, Y), X)),
        ),
    ),
    "Multiplication is characterized recursively on the second argument.",
)

AXIOMS = (
    AXIOM_S_NONZERO,
    AXIOM_S_INJECTIVE,
    AXIOM_ADD_ZERO,
    AXIOM_ADD_SUCCESSOR,
    AXIOM_MUL_ZERO,
    AXIOM_MUL_SUCCESSOR,
)

RULE_AXIOM = "AXIOM"
RULE_THEOREM = "THEOREM"
RULE_ASSUMPTION = "ASSUMPTION"
RULE_FORALL_ELIM = "FORALL_ELIM"
RULE_FORALL_INTRO = "FORALL_INTRO"
RULE_MODUS_PONENS = "MODUS_PONENS"
RULE_EQ_SYMMETRY = "EQ_SYMMETRY"
RULE_CONTRADICTION = "CONTRADICTION"
RULE_NEGATION_INTRO = "NEGATION_INTRO"
RULE_EQ_SUCC_CONGRUENCE = "EQ_SUCC_CONGRUENCE"
RULE_EQ_ADD_LEFT_CONGRUENCE = "EQ_ADD_LEFT_CONGRUENCE"
RULE_EQ_ADD_RIGHT_CONGRUENCE = "EQ_ADD_RIGHT_CONGRUENCE"
RULE_EQ_MUL_LEFT_CONGRUENCE = "EQ_MUL_LEFT_CONGRUENCE"
RULE_EQ_MUL_RIGHT_CONGRUENCE = "EQ_MUL_RIGHT_CONGRUENCE"
RULE_EQ_TRANSITIVITY = "EQ_TRANSITIVITY"
RULE_INDUCTION = "INDUCTION"

INFERENCE_RULES = (
    InferenceRule(RULE_AXIOM, "Use a declared arithmetic axiom."),
    InferenceRule(RULE_THEOREM, "Reuse an already verified theorem."),
    InferenceRule(RULE_ASSUMPTION, "Open a temporary assumption for a subproof."),
    InferenceRule(RULE_FORALL_ELIM, "Instantiate ∀x.P(x) at a chosen term."),
    InferenceRule(
        RULE_FORALL_INTRO,
        "From P(x), derive ∀x.P(x) when x is not free in any open assumption.",
    ),
    InferenceRule(RULE_MODUS_PONENS, "From P→Q and P, derive Q."),
    InferenceRule(RULE_EQ_SYMMETRY, "From a=b, derive b=a."),
    InferenceRule(RULE_CONTRADICTION, "From P and ¬P, derive ⊥."),
    InferenceRule(
        RULE_NEGATION_INTRO,
        "If assumption P leads to ⊥, discharge P and derive ¬P.",
    ),
    InferenceRule(
        RULE_EQ_SUCC_CONGRUENCE,
        "From a=b, derive S(a)=S(b).",
    ),
    InferenceRule(
        RULE_EQ_ADD_LEFT_CONGRUENCE,
        "From a=b, derive Add(a,c)=Add(b,c).",
    ),
    InferenceRule(
        RULE_EQ_ADD_RIGHT_CONGRUENCE,
        "From a=b, derive Add(c,a)=Add(c,b).",
    ),
    InferenceRule(
        RULE_EQ_MUL_LEFT_CONGRUENCE,
        "From a=b, derive Mul(a,c)=Mul(b,c).",
    ),
    InferenceRule(
        RULE_EQ_MUL_RIGHT_CONGRUENCE,
        "From a=b, derive Mul(c,a)=Mul(c,b).",
    ),
    InferenceRule(
        RULE_EQ_TRANSITIVITY,
        "From a=b and b=c, derive a=c.",
    ),
    InferenceRule(
        RULE_INDUCTION,
        "From P(0) and a derivation of P(S(n)) under assumption P(n), derive ∀n.P(n).",
    ),
)

WORLD = FormalWorld(
    arithmetic_primitives=ARITHMETIC_PRIMITIVES,
    logical_primitives=LOGICAL_PRIMITIVES,
    definitions=DEFINITIONS,
    axioms=AXIOMS,
    inference_rules=INFERENCE_RULES,
)


@dataclass(frozen=True)
class RewriteStep:
    before: Expr
    after: Expr
    rule: str


ADD_ZERO = AXIOM_ADD_ZERO.name
ADD_SUCC = AXIOM_ADD_SUCCESSOR.name
MUL_ZERO = AXIOM_MUL_ZERO.name
MUL_SUCC = AXIOM_MUL_SUCCESSOR.name


def rewrite_once(expr: Expr) -> Optional[RewriteStep]:
    if isinstance(expr, Add):
        if isinstance(expr.right, Zero):
            return RewriteStep(expr, expr.left, ADD_ZERO)

        if isinstance(expr.right, Succ):
            return RewriteStep(
                expr,
                Succ(Add(expr.left, expr.right.value)),
                ADD_SUCC,
            )

        left_step = rewrite_once(expr.left)
        if left_step is not None:
            return RewriteStep(expr, Add(left_step.after, expr.right), left_step.rule)

        right_step = rewrite_once(expr.right)
        if right_step is not None:
            return RewriteStep(expr, Add(expr.left, right_step.after), right_step.rule)

        return None

    if isinstance(expr, Mul):
        if isinstance(expr.right, Zero):
            return RewriteStep(expr, ZERO, MUL_ZERO)

        if isinstance(expr.right, Succ):
            return RewriteStep(
                expr,
                Add(Mul(expr.left, expr.right.value), expr.left),
                MUL_SUCC,
            )

        left_step = rewrite_once(expr.left)
        if left_step is not None:
            return RewriteStep(expr, Mul(left_step.after, expr.right), left_step.rule)

        right_step = rewrite_once(expr.right)
        if right_step is not None:
            return RewriteStep(expr, Mul(expr.left, right_step.after), right_step.rule)

        return None

    if isinstance(expr, Succ):
        inner_step = rewrite_once(expr.value)
        if inner_step is None:
            return None
        return RewriteStep(expr, Succ(inner_step.after), inner_step.rule)

    if isinstance(expr, (Zero, Var)):
        return None

    raise TypeError(f"Unsupported expression type: {type(expr)!r}")


def normalize(
    expr: Expr,
    max_steps: int = 1000,
) -> Tuple[Expr, tuple[RewriteStep, ...]]:
    current = expr
    trace: list[RewriteStep] = []

    for _ in range(max_steps):
        step = rewrite_once(current)
        if step is None:
            return current, tuple(trace)
        trace.append(step)
        current = step.after

    raise RuntimeError("Normalization exceeded max_steps")


def substitute_expr(expr: Expr, variable: Var, replacement: Expr) -> Expr:
    if isinstance(expr, Var):
        return replacement if expr == variable else expr
    if isinstance(expr, Zero):
        return expr
    if isinstance(expr, Succ):
        return Succ(substitute_expr(expr.value, variable, replacement))
    if isinstance(expr, Add):
        return Add(
            substitute_expr(expr.left, variable, replacement),
            substitute_expr(expr.right, variable, replacement),
        )
    if isinstance(expr, Mul):
        return Mul(
            substitute_expr(expr.left, variable, replacement),
            substitute_expr(expr.right, variable, replacement),
        )
    raise TypeError(f"Unsupported expression type: {type(expr)!r}")


def free_vars_expr(expr: Expr) -> frozenset[Var]:
    if isinstance(expr, Var):
        return frozenset({expr})
    if isinstance(expr, Zero):
        return frozenset()
    if isinstance(expr, Succ):
        return free_vars_expr(expr.value)
    if isinstance(expr, Add):
        return free_vars_expr(expr.left) | free_vars_expr(expr.right)
    if isinstance(expr, Mul):
        return free_vars_expr(expr.left) | free_vars_expr(expr.right)
    raise TypeError(f"Unsupported expression type: {type(expr)!r}")


def free_vars_formula(formula: Formula) -> frozenset[Var]:
    if isinstance(formula, Eq):
        return free_vars_expr(formula.left) | free_vars_expr(formula.right)
    if isinstance(formula, Not):
        return free_vars_formula(formula.formula)
    if isinstance(formula, Implies):
        return free_vars_formula(formula.premise) | free_vars_formula(formula.conclusion)
    if isinstance(formula, ForAll):
        return free_vars_formula(formula.body) - frozenset({formula.variable})
    if isinstance(formula, Bottom):
        return frozenset()
    raise TypeError(f"Unsupported formula type: {type(formula)!r}")


def is_free_for(
    replacement: Expr,
    variable: Var,
    formula: Formula,
) -> bool:
    """Return whether replacement is free for variable in formula.

    Gareen currently rejects substitutions that would capture a free variable
    instead of silently alpha-renaming bound variables.
    """

    replacement_vars = free_vars_expr(replacement)

    if isinstance(formula, Eq):
        return True
    if isinstance(formula, Not):
        return is_free_for(replacement, variable, formula.formula)
    if isinstance(formula, Implies):
        return (
            is_free_for(replacement, variable, formula.premise)
            and is_free_for(replacement, variable, formula.conclusion)
        )
    if isinstance(formula, ForAll):
        if formula.variable == variable:
            return True
        if (
            formula.variable in replacement_vars
            and variable in free_vars_formula(formula.body)
        ):
            return False
        return is_free_for(replacement, variable, formula.body)
    if isinstance(formula, Bottom):
        return True
    raise TypeError(f"Unsupported formula type: {type(formula)!r}")


def substitute_formula(
    formula: Formula,
    variable: Var,
    replacement: Expr,
) -> Formula:
    if isinstance(formula, Eq):
        return Eq(
            substitute_expr(formula.left, variable, replacement),
            substitute_expr(formula.right, variable, replacement),
        )
    if isinstance(formula, Not):
        return Not(substitute_formula(formula.formula, variable, replacement))
    if isinstance(formula, Implies):
        return Implies(
            substitute_formula(formula.premise, variable, replacement),
            substitute_formula(formula.conclusion, variable, replacement),
        )
    if isinstance(formula, ForAll):
        if formula.variable == variable:
            return formula
        return ForAll(
            formula.variable,
            substitute_formula(formula.body, variable, replacement),
        )
    if isinstance(formula, Bottom):
        return formula
    raise TypeError(f"Unsupported formula type: {type(formula)!r}")


@dataclass(frozen=True)
class ProofStep:
    conclusion: Formula
    rule: str
    premises: tuple[int, ...] = ()
    source: Optional[str] = None
    term: Optional[Expr] = None
    variable: Optional[Var] = None
    discharge: Optional[int] = None
    note: str = ""


@dataclass(frozen=True)
class Proof:
    statement: Formula
    steps: tuple[ProofStep, ...]


@dataclass(frozen=True)
class ProofCheckResult:
    valid: bool
    errors: tuple[str, ...]
    open_assumptions: frozenset[int]


@dataclass(frozen=True)
class Theorem:
    name: str
    statement: Formula
    proof: Proof
    dependencies: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.name}: {self.statement}"


def _is_contradictory(left: Formula, right: Formula) -> bool:
    return (
        isinstance(left, Not) and left.formula == right
    ) or (
        isinstance(right, Not) and right.formula == left
    )


def check_proof(
    proof: Proof,
    axioms: tuple[Axiom, ...] = AXIOMS,
    known_theorems: tuple[Theorem, ...] = (),
) -> ProofCheckResult:
    axiom_map = {axiom.name: axiom.formula for axiom in axioms}
    theorem_map = {theorem.name: theorem.statement for theorem in known_theorems}

    errors: list[str] = []
    dependencies: list[frozenset[int]] = []

    for index, step in enumerate(proof.steps):
        prefix = f"step {index}"

        if any(premise < 0 or premise >= index for premise in step.premises):
            errors.append(f"{prefix}: premise index must refer to an earlier step")
            dependencies.append(frozenset())
            continue

        premise_steps = [proof.steps[i] for i in step.premises]
        premise_dependencies = [dependencies[i] for i in step.premises]
        inherited = frozenset().union(*premise_dependencies)

        if step.rule == RULE_AXIOM:
            if step.source not in axiom_map:
                errors.append(f"{prefix}: unknown axiom source {step.source!r}")
            elif axiom_map[step.source] != step.conclusion:
                errors.append(f"{prefix}: conclusion does not match axiom")
            dependencies.append(frozenset())
            continue

        if step.rule == RULE_THEOREM:
            if step.source not in theorem_map:
                errors.append(f"{prefix}: unknown theorem source {step.source!r}")
            elif theorem_map[step.source] != step.conclusion:
                errors.append(f"{prefix}: conclusion does not match theorem")
            dependencies.append(frozenset())
            continue

        if step.rule == RULE_ASSUMPTION:
            if step.premises:
                errors.append(f"{prefix}: assumption cannot have premises")
            dependencies.append(frozenset({index}))
            continue

        if step.rule == RULE_FORALL_ELIM:
            if len(premise_steps) != 1:
                errors.append(f"{prefix}: FORALL_ELIM needs one premise")
                dependencies.append(inherited)
                continue

            source_formula = premise_steps[0].conclusion
            if not isinstance(source_formula, ForAll):
                errors.append(f"{prefix}: premise is not universally quantified")
            elif step.term is None:
                errors.append(f"{prefix}: FORALL_ELIM requires a term")
            elif not is_free_for(
                step.term,
                source_formula.variable,
                source_formula.body,
            ):
                errors.append(
                    f"{prefix}: universal instantiation would capture a variable"
                )
            else:
                expected = substitute_formula(
                    source_formula.body,
                    source_formula.variable,
                    step.term,
                )
                if expected != step.conclusion:
                    errors.append(f"{prefix}: invalid universal instantiation")

            dependencies.append(inherited)
            continue

        if step.rule == RULE_FORALL_INTRO:
            if len(premise_steps) != 1:
                errors.append(f"{prefix}: FORALL_INTRO needs one premise")
                dependencies.append(inherited)
                continue

            if not isinstance(step.conclusion, ForAll):
                errors.append(f"{prefix}: FORALL_INTRO must conclude a universal formula")
                dependencies.append(inherited)
                continue

            variable = step.variable or step.conclusion.variable
            if variable != step.conclusion.variable:
                errors.append(f"{prefix}: generalized variable does not match conclusion")

            if step.conclusion.body != premise_steps[0].conclusion:
                errors.append(f"{prefix}: universal body does not match premise")

            for assumption_index in inherited:
                assumption_formula = proof.steps[assumption_index].conclusion
                if variable in free_vars_formula(assumption_formula):
                    errors.append(
                        f"{prefix}: generalized variable is free in open assumption "
                        f"{assumption_index}"
                    )

            dependencies.append(inherited)
            continue

        if step.rule == RULE_MODUS_PONENS:
            if len(premise_steps) != 2:
                errors.append(f"{prefix}: MODUS_PONENS needs two premises")
                dependencies.append(inherited)
                continue

            implication = premise_steps[0].conclusion
            premise = premise_steps[1].conclusion

            if not isinstance(implication, Implies):
                errors.append(f"{prefix}: first premise is not an implication")
            elif implication.premise != premise:
                errors.append(f"{prefix}: implication premise does not match")
            elif implication.conclusion != step.conclusion:
                errors.append(f"{prefix}: conclusion does not follow by modus ponens")

            dependencies.append(inherited)
            continue

        if step.rule == RULE_EQ_SYMMETRY:
            if len(premise_steps) != 1:
                errors.append(f"{prefix}: EQ_SYMMETRY needs one premise")
                dependencies.append(inherited)
                continue

            equality = premise_steps[0].conclusion
            if not isinstance(equality, Eq):
                errors.append(f"{prefix}: premise is not an equality")
            elif step.conclusion != Eq(equality.right, equality.left):
                errors.append(f"{prefix}: equality was not reversed correctly")

            dependencies.append(inherited)
            continue

        if step.rule == RULE_EQ_SUCC_CONGRUENCE:
            if len(premise_steps) != 1:
                errors.append(f"{prefix}: EQ_SUCC_CONGRUENCE needs one premise")
                dependencies.append(inherited)
                continue

            equality = premise_steps[0].conclusion
            if not isinstance(equality, Eq):
                errors.append(f"{prefix}: premise is not an equality")
            elif step.conclusion != Eq(Succ(equality.left), Succ(equality.right)):
                errors.append(f"{prefix}: successor congruence is malformed")

            dependencies.append(inherited)
            continue

        if step.rule == RULE_EQ_ADD_LEFT_CONGRUENCE:
            if len(premise_steps) != 1:
                errors.append(f"{prefix}: EQ_ADD_LEFT_CONGRUENCE needs one premise")
                dependencies.append(inherited)
                continue

            equality = premise_steps[0].conclusion
            if not isinstance(equality, Eq):
                errors.append(f"{prefix}: premise is not an equality")
            elif step.term is None:
                errors.append(f"{prefix}: EQ_ADD_LEFT_CONGRUENCE requires a term")
            elif step.conclusion != Eq(
                Add(equality.left, step.term),
                Add(equality.right, step.term),
            ):
                errors.append(f"{prefix}: left Add congruence is malformed")

            dependencies.append(inherited)
            continue

        if step.rule == RULE_EQ_ADD_RIGHT_CONGRUENCE:
            if len(premise_steps) != 1:
                errors.append(f"{prefix}: EQ_ADD_RIGHT_CONGRUENCE needs one premise")
                dependencies.append(inherited)
                continue

            equality = premise_steps[0].conclusion
            if not isinstance(equality, Eq):
                errors.append(f"{prefix}: premise is not an equality")
            elif step.term is None:
                errors.append(f"{prefix}: EQ_ADD_RIGHT_CONGRUENCE requires a term")
            elif step.conclusion != Eq(
                Add(step.term, equality.left),
                Add(step.term, equality.right),
            ):
                errors.append(f"{prefix}: right Add congruence is malformed")

            dependencies.append(inherited)
            continue

        if step.rule == RULE_EQ_MUL_LEFT_CONGRUENCE:
            if len(premise_steps) != 1:
                errors.append(f"{prefix}: EQ_MUL_LEFT_CONGRUENCE needs one premise")
                dependencies.append(inherited)
                continue

            equality = premise_steps[0].conclusion
            if not isinstance(equality, Eq):
                errors.append(f"{prefix}: premise is not an equality")
            elif step.term is None:
                errors.append(f"{prefix}: EQ_MUL_LEFT_CONGRUENCE requires a term")
            elif step.conclusion != Eq(
                Mul(equality.left, step.term),
                Mul(equality.right, step.term),
            ):
                errors.append(f"{prefix}: left Mul congruence is malformed")

            dependencies.append(inherited)
            continue

        if step.rule == RULE_EQ_MUL_RIGHT_CONGRUENCE:
            if len(premise_steps) != 1:
                errors.append(f"{prefix}: EQ_MUL_RIGHT_CONGRUENCE needs one premise")
                dependencies.append(inherited)
                continue

            equality = premise_steps[0].conclusion
            if not isinstance(equality, Eq):
                errors.append(f"{prefix}: premise is not an equality")
            elif step.term is None:
                errors.append(f"{prefix}: EQ_MUL_RIGHT_CONGRUENCE requires a term")
            elif step.conclusion != Eq(
                Mul(step.term, equality.left),
                Mul(step.term, equality.right),
            ):
                errors.append(f"{prefix}: right Mul congruence is malformed")

            dependencies.append(inherited)
            continue

        if step.rule == RULE_EQ_TRANSITIVITY:
            if len(premise_steps) != 2:
                errors.append(f"{prefix}: EQ_TRANSITIVITY needs two premises")
                dependencies.append(inherited)
                continue

            first = premise_steps[0].conclusion
            second = premise_steps[1].conclusion
            if not isinstance(first, Eq) or not isinstance(second, Eq):
                errors.append(f"{prefix}: both premises must be equalities")
            elif first.right != second.left:
                errors.append(f"{prefix}: middle equality terms do not match")
            elif step.conclusion != Eq(first.left, second.right):
                errors.append(f"{prefix}: transitive conclusion is malformed")

            dependencies.append(inherited)
            continue

        if step.rule == RULE_INDUCTION:
            if len(premise_steps) != 2:
                errors.append(f"{prefix}: INDUCTION needs base and step premises")
                dependencies.append(inherited)
                continue

            if not isinstance(step.conclusion, ForAll):
                errors.append(f"{prefix}: induction must conclude a universal formula")
                dependencies.append(inherited)
                continue

            variable = step.variable or step.conclusion.variable
            if variable != step.conclusion.variable:
                errors.append(f"{prefix}: induction variable does not match conclusion")

            predicate = step.conclusion.body
            expected_base = substitute_formula(predicate, variable, ZERO)
            expected_step = substitute_formula(predicate, variable, Succ(variable))

            if premise_steps[0].conclusion != expected_base:
                errors.append(f"{prefix}: base case does not match P(0)")
            if premise_steps[1].conclusion != expected_step:
                errors.append(f"{prefix}: induction step does not match P(S(n))")

            if step.discharge is None:
                errors.append(f"{prefix}: induction must discharge P(n)")
                dependencies.append(inherited)
                continue

            if step.discharge < 0 or step.discharge >= index:
                errors.append(f"{prefix}: invalid induction discharge step")
                dependencies.append(inherited)
                continue

            assumption_step = proof.steps[step.discharge]
            if assumption_step.rule != RULE_ASSUMPTION:
                errors.append(f"{prefix}: induction discharge target is not an assumption")
            elif assumption_step.conclusion != predicate:
                errors.append(f"{prefix}: induction assumption is not P(n)")
            elif step.discharge not in inherited:
                errors.append(f"{prefix}: induction assumption is not open")

            dependencies.append(inherited - frozenset({step.discharge}))
            continue

        if step.rule == RULE_CONTRADICTION:
            if len(premise_steps) != 2:
                errors.append(f"{prefix}: CONTRADICTION needs two premises")
            elif not isinstance(step.conclusion, Bottom):
                errors.append(f"{prefix}: contradiction must conclude ⊥")
            elif not _is_contradictory(
                premise_steps[0].conclusion,
                premise_steps[1].conclusion,
            ):
                errors.append(f"{prefix}: premises are not P and ¬P")

            dependencies.append(inherited)
            continue

        if step.rule == RULE_NEGATION_INTRO:
            if len(premise_steps) != 1:
                errors.append(f"{prefix}: NEGATION_INTRO needs one premise")
                dependencies.append(inherited)
                continue

            if not isinstance(premise_steps[0].conclusion, Bottom):
                errors.append(f"{prefix}: premise must be ⊥")

            if step.discharge is None:
                errors.append(f"{prefix}: no assumption selected for discharge")
                dependencies.append(inherited)
                continue

            if step.discharge < 0 or step.discharge >= index:
                errors.append(f"{prefix}: invalid discharge step")
                dependencies.append(inherited)
                continue

            assumption_step = proof.steps[step.discharge]
            if assumption_step.rule != RULE_ASSUMPTION:
                errors.append(f"{prefix}: discharge target is not an assumption")
            elif step.discharge not in inherited:
                errors.append(f"{prefix}: discharged assumption is not open")
            elif step.conclusion != Not(assumption_step.conclusion):
                errors.append(f"{prefix}: negation does not match assumption")

            dependencies.append(inherited - frozenset({step.discharge}))
            continue

        errors.append(f"{prefix}: unknown inference rule {step.rule!r}")
        dependencies.append(inherited)

    if not proof.steps:
        errors.append("proof has no steps")
        final_dependencies = frozenset()
    else:
        final_dependencies = dependencies[-1]
        if proof.steps[-1].conclusion != proof.statement:
            errors.append("last proof step does not match claimed statement")

    if final_dependencies:
        errors.append(
            "proof ended with open assumptions: "
            + ", ".join(str(i) for i in sorted(final_dependencies))
        )

    return ProofCheckResult(
        valid=not errors,
        errors=tuple(errors),
        open_assumptions=final_dependencies,
    )


@dataclass
class KnowledgeState:
    world: FormalWorld = WORLD
    theorems: dict[str, Theorem] = field(default_factory=dict)

    def add_theorem(self, name: str, proof: Proof) -> Theorem:
        if name in self.theorems:
            raise ValueError(f"Theorem {name!r} already exists")

        check = check_proof(
            proof,
            axioms=self.world.axioms,
            known_theorems=tuple(self.theorems.values()),
        )
        if not check.valid:
            raise ValueError("Invalid proof: " + "; ".join(check.errors))

        dependencies = []
        for step in proof.steps:
            if step.rule in (RULE_AXIOM, RULE_THEOREM) and step.source:
                if step.source not in dependencies:
                    dependencies.append(step.source)

        theorem = Theorem(
            name=name,
            statement=proof.statement,
            proof=proof,
            dependencies=tuple(dependencies),
        )
        self.theorems[name] = theorem
        return theorem


def build_initial_knowledge() -> KnowledgeState:
    state = KnowledgeState()

    one_nonzero = Not(Eq(ONE, ZERO))
    proof_t1 = Proof(
        statement=one_nonzero,
        steps=(
            ProofStep(
                conclusion=AXIOM_S_NONZERO.formula,
                rule=RULE_AXIOM,
                source=AXIOM_S_NONZERO.name,
            ),
            ProofStep(
                conclusion=one_nonzero,
                rule=RULE_FORALL_ELIM,
                premises=(0,),
                term=ZERO,
            ),
        ),
    )
    state.add_theorem("T1_ONE_NONZERO", proof_t1)

    injective_x_zero = ForAll(
        Y,
        Implies(Eq(ONE, Succ(Y)), Eq(ZERO, Y)),
    )
    one_equals_two_implies_zero_equals_one = Implies(
        Eq(ONE, TWO),
        Eq(ZERO, ONE),
    )
    proof_t2 = Proof(
        statement=Not(Eq(ONE, TWO)),
        steps=(
            ProofStep(
                conclusion=one_nonzero,
                rule=RULE_THEOREM,
                source="T1_ONE_NONZERO",
            ),
            ProofStep(
                conclusion=AXIOM_S_INJECTIVE.formula,
                rule=RULE_AXIOM,
                source=AXIOM_S_INJECTIVE.name,
            ),
            ProofStep(
                conclusion=injective_x_zero,
                rule=RULE_FORALL_ELIM,
                premises=(1,),
                term=ZERO,
            ),
            ProofStep(
                conclusion=one_equals_two_implies_zero_equals_one,
                rule=RULE_FORALL_ELIM,
                premises=(2,),
                term=ONE,
            ),
            ProofStep(
                conclusion=Eq(ONE, TWO),
                rule=RULE_ASSUMPTION,
                note="Assume 1 = 2 for negation introduction.",
            ),
            ProofStep(
                conclusion=Eq(ZERO, ONE),
                rule=RULE_MODUS_PONENS,
                premises=(3, 4),
            ),
            ProofStep(
                conclusion=Eq(ONE, ZERO),
                rule=RULE_EQ_SYMMETRY,
                premises=(5,),
            ),
            ProofStep(
                conclusion=BOTTOM,
                rule=RULE_CONTRADICTION,
                premises=(6, 0),
            ),
            ProofStep(
                conclusion=Not(Eq(ONE, TWO)),
                rule=RULE_NEGATION_INTRO,
                premises=(7,),
                discharge=4,
            ),
        ),
    )
    state.add_theorem("T2_ONE_NE_TWO", proof_t2)

    injective_x_one = ForAll(
        Y,
        Implies(Eq(TWO, Succ(Y)), Eq(ONE, Y)),
    )
    two_equals_three_implies_one_equals_two = Implies(
        Eq(TWO, THREE),
        Eq(ONE, TWO),
    )
    proof_t3 = Proof(
        statement=Not(Eq(TWO, THREE)),
        steps=(
            ProofStep(
                conclusion=Not(Eq(ONE, TWO)),
                rule=RULE_THEOREM,
                source="T2_ONE_NE_TWO",
            ),
            ProofStep(
                conclusion=AXIOM_S_INJECTIVE.formula,
                rule=RULE_AXIOM,
                source=AXIOM_S_INJECTIVE.name,
            ),
            ProofStep(
                conclusion=injective_x_one,
                rule=RULE_FORALL_ELIM,
                premises=(1,),
                term=ONE,
            ),
            ProofStep(
                conclusion=two_equals_three_implies_one_equals_two,
                rule=RULE_FORALL_ELIM,
                premises=(2,),
                term=TWO,
            ),
            ProofStep(
                conclusion=Eq(TWO, THREE),
                rule=RULE_ASSUMPTION,
                note="Assume 2 = 3 for negation introduction.",
            ),
            ProofStep(
                conclusion=Eq(ONE, TWO),
                rule=RULE_MODUS_PONENS,
                premises=(3, 4),
            ),
            ProofStep(
                conclusion=BOTTOM,
                rule=RULE_CONTRADICTION,
                premises=(5, 0),
            ),
            ProofStep(
                conclusion=Not(Eq(TWO, THREE)),
                rule=RULE_NEGATION_INTRO,
                premises=(6,),
                discharge=4,
            ),
        ),
    )
    state.add_theorem("T3_TWO_NE_THREE", proof_t3)

    two_plus_zero = Eq(Add(TWO, ZERO), TWO)
    proof_t4 = Proof(
        statement=two_plus_zero,
        steps=(
            ProofStep(
                conclusion=AXIOM_ADD_ZERO.formula,
                rule=RULE_AXIOM,
                source=AXIOM_ADD_ZERO.name,
            ),
            ProofStep(
                conclusion=two_plus_zero,
                rule=RULE_FORALL_ELIM,
                premises=(0,),
                term=TWO,
            ),
        ),
    )
    state.add_theorem("T4_TWO_PLUS_ZERO", proof_t4)

    zero_plus_x = Eq(Add(ZERO, X), X)
    zero_plus_zero = Eq(Add(ZERO, ZERO), ZERO)
    zero_plus_sx = Eq(Add(ZERO, Succ(X)), Succ(X))
    add_zero_sx = Eq(Add(ZERO, Succ(X)), Succ(Add(ZERO, X)))
    succ_ih = Eq(Succ(Add(ZERO, X)), Succ(X))

    proof_t5 = Proof(
        statement=ForAll(X, zero_plus_x),
        steps=(
            ProofStep(
                conclusion=AXIOM_ADD_ZERO.formula,
                rule=RULE_AXIOM,
                source=AXIOM_ADD_ZERO.name,
            ),
            ProofStep(
                conclusion=zero_plus_zero,
                rule=RULE_FORALL_ELIM,
                premises=(0,),
                term=ZERO,
            ),
            ProofStep(
                conclusion=zero_plus_x,
                rule=RULE_ASSUMPTION,
                note="Induction hypothesis P(x): 0 + x = x.",
            ),
            ProofStep(
                conclusion=AXIOM_ADD_SUCCESSOR.formula,
                rule=RULE_AXIOM,
                source=AXIOM_ADD_SUCCESSOR.name,
            ),
            ProofStep(
                conclusion=ForAll(
                    Y,
                    Eq(Add(ZERO, Succ(Y)), Succ(Add(ZERO, Y))),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(3,),
                term=ZERO,
            ),
            ProofStep(
                conclusion=add_zero_sx,
                rule=RULE_FORALL_ELIM,
                premises=(4,),
                term=X,
            ),
            ProofStep(
                conclusion=succ_ih,
                rule=RULE_EQ_SUCC_CONGRUENCE,
                premises=(2,),
            ),
            ProofStep(
                conclusion=zero_plus_sx,
                rule=RULE_EQ_TRANSITIVITY,
                premises=(5, 6),
            ),
            ProofStep(
                conclusion=ForAll(X, zero_plus_x),
                rule=RULE_INDUCTION,
                premises=(1, 7),
                variable=X,
                discharge=2,
            ),
        ),
    )
    state.add_theorem("T5_ZERO_PLUS_X", proof_t5)

    # T6: ∀x∀z. S(x) + z = S(x + z)
    succ_add_body = Eq(Add(Succ(X), Z), Succ(Add(X, Z)))
    succ_add_base = Eq(Add(Succ(X), ZERO), Succ(Add(X, ZERO)))
    succ_add_step = Eq(
        Add(Succ(X), Succ(Z)),
        Succ(Add(X, Succ(Z))),
    )

    proof_t6 = Proof(
        statement=ForAll(X, ForAll(Z, succ_add_body)),
        steps=(
            ProofStep(
                conclusion=AXIOM_ADD_ZERO.formula,
                rule=RULE_AXIOM,
                source=AXIOM_ADD_ZERO.name,
            ),
            ProofStep(
                conclusion=Eq(Add(Succ(X), ZERO), Succ(X)),
                rule=RULE_FORALL_ELIM,
                premises=(0,),
                term=Succ(X),
            ),
            ProofStep(
                conclusion=Eq(Add(X, ZERO), X),
                rule=RULE_FORALL_ELIM,
                premises=(0,),
                term=X,
            ),
            ProofStep(
                conclusion=Eq(Succ(Add(X, ZERO)), Succ(X)),
                rule=RULE_EQ_SUCC_CONGRUENCE,
                premises=(2,),
            ),
            ProofStep(
                conclusion=Eq(Succ(X), Succ(Add(X, ZERO))),
                rule=RULE_EQ_SYMMETRY,
                premises=(3,),
            ),
            ProofStep(
                conclusion=succ_add_base,
                rule=RULE_EQ_TRANSITIVITY,
                premises=(1, 4),
            ),
            ProofStep(
                conclusion=succ_add_body,
                rule=RULE_ASSUMPTION,
                note="Induction hypothesis: S(x) + z = S(x + z).",
            ),
            ProofStep(
                conclusion=AXIOM_ADD_SUCCESSOR.formula,
                rule=RULE_AXIOM,
                source=AXIOM_ADD_SUCCESSOR.name,
            ),
            ProofStep(
                conclusion=ForAll(
                    Y,
                    Eq(
                        Add(Succ(X), Succ(Y)),
                        Succ(Add(Succ(X), Y)),
                    ),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(7,),
                term=Succ(X),
            ),
            ProofStep(
                conclusion=Eq(
                    Add(Succ(X), Succ(Z)),
                    Succ(Add(Succ(X), Z)),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(8,),
                term=Z,
            ),
            ProofStep(
                conclusion=Eq(
                    Succ(Add(Succ(X), Z)),
                    Succ(Succ(Add(X, Z))),
                ),
                rule=RULE_EQ_SUCC_CONGRUENCE,
                premises=(6,),
            ),
            ProofStep(
                conclusion=ForAll(
                    Y,
                    Eq(Add(X, Succ(Y)), Succ(Add(X, Y))),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(7,),
                term=X,
            ),
            ProofStep(
                conclusion=Eq(
                    Add(X, Succ(Z)),
                    Succ(Add(X, Z)),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(11,),
                term=Z,
            ),
            ProofStep(
                conclusion=Eq(
                    Succ(Add(X, Succ(Z))),
                    Succ(Succ(Add(X, Z))),
                ),
                rule=RULE_EQ_SUCC_CONGRUENCE,
                premises=(12,),
            ),
            ProofStep(
                conclusion=Eq(
                    Succ(Succ(Add(X, Z))),
                    Succ(Add(X, Succ(Z))),
                ),
                rule=RULE_EQ_SYMMETRY,
                premises=(13,),
            ),
            ProofStep(
                conclusion=Eq(
                    Add(Succ(X), Succ(Z)),
                    Succ(Succ(Add(X, Z))),
                ),
                rule=RULE_EQ_TRANSITIVITY,
                premises=(9, 10),
            ),
            ProofStep(
                conclusion=succ_add_step,
                rule=RULE_EQ_TRANSITIVITY,
                premises=(15, 14),
            ),
            ProofStep(
                conclusion=ForAll(Z, succ_add_body),
                rule=RULE_INDUCTION,
                premises=(5, 16),
                variable=Z,
                discharge=6,
            ),
            ProofStep(
                conclusion=ForAll(X, ForAll(Z, succ_add_body)),
                rule=RULE_FORALL_INTRO,
                premises=(17,),
                variable=X,
            ),
        ),
    )
    state.add_theorem("T6_SUCC_ADD", proof_t6)

    # T7: ∀x∀y. x + y = y + x
    comm_body = Eq(Add(X, Y), Add(Y, X))
    comm_base = Eq(Add(X, ZERO), Add(ZERO, X))
    comm_step = Eq(Add(X, Succ(Y)), Add(Succ(Y), X))

    proof_t7 = Proof(
        statement=ForAll(X, ForAll(Y, comm_body)),
        steps=(
            ProofStep(
                conclusion=AXIOM_ADD_ZERO.formula,
                rule=RULE_AXIOM,
                source=AXIOM_ADD_ZERO.name,
            ),
            ProofStep(
                conclusion=Eq(Add(X, ZERO), X),
                rule=RULE_FORALL_ELIM,
                premises=(0,),
                term=X,
            ),
            ProofStep(
                conclusion=ForAll(X, Eq(Add(ZERO, X), X)),
                rule=RULE_THEOREM,
                source="T5_ZERO_PLUS_X",
            ),
            ProofStep(
                conclusion=Eq(Add(ZERO, X), X),
                rule=RULE_FORALL_ELIM,
                premises=(2,),
                term=X,
            ),
            ProofStep(
                conclusion=Eq(X, Add(ZERO, X)),
                rule=RULE_EQ_SYMMETRY,
                premises=(3,),
            ),
            ProofStep(
                conclusion=comm_base,
                rule=RULE_EQ_TRANSITIVITY,
                premises=(1, 4),
            ),
            ProofStep(
                conclusion=comm_body,
                rule=RULE_ASSUMPTION,
                note="Induction hypothesis: x + y = y + x.",
            ),
            ProofStep(
                conclusion=AXIOM_ADD_SUCCESSOR.formula,
                rule=RULE_AXIOM,
                source=AXIOM_ADD_SUCCESSOR.name,
            ),
            ProofStep(
                conclusion=ForAll(
                    Y,
                    Eq(Add(X, Succ(Y)), Succ(Add(X, Y))),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(7,),
                term=X,
            ),
            ProofStep(
                conclusion=Eq(
                    Add(X, Succ(Y)),
                    Succ(Add(X, Y)),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(8,),
                term=Y,
            ),
            ProofStep(
                conclusion=Eq(
                    Succ(Add(X, Y)),
                    Succ(Add(Y, X)),
                ),
                rule=RULE_EQ_SUCC_CONGRUENCE,
                premises=(6,),
            ),
            ProofStep(
                conclusion=Eq(
                    Add(X, Succ(Y)),
                    Succ(Add(Y, X)),
                ),
                rule=RULE_EQ_TRANSITIVITY,
                premises=(9, 10),
            ),
            ProofStep(
                conclusion=ForAll(X, ForAll(Z, succ_add_body)),
                rule=RULE_THEOREM,
                source="T6_SUCC_ADD",
            ),
            ProofStep(
                conclusion=ForAll(
                    Z,
                    Eq(Add(Succ(Y), Z), Succ(Add(Y, Z))),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(12,),
                term=Y,
            ),
            ProofStep(
                conclusion=Eq(
                    Add(Succ(Y), X),
                    Succ(Add(Y, X)),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(13,),
                term=X,
            ),
            ProofStep(
                conclusion=Eq(
                    Succ(Add(Y, X)),
                    Add(Succ(Y), X),
                ),
                rule=RULE_EQ_SYMMETRY,
                premises=(14,),
            ),
            ProofStep(
                conclusion=comm_step,
                rule=RULE_EQ_TRANSITIVITY,
                premises=(11, 15),
            ),
            ProofStep(
                conclusion=ForAll(Y, comm_body),
                rule=RULE_INDUCTION,
                premises=(5, 16),
                variable=Y,
                discharge=6,
            ),
            ProofStep(
                conclusion=ForAll(X, ForAll(Y, comm_body)),
                rule=RULE_FORALL_INTRO,
                premises=(17,),
                variable=X,
            ),
        ),
    )
    state.add_theorem("T7_ADD_COMMUTATIVE", proof_t7)

    # T8: associativity of addition.
    # We use x, z as fixed parameters and induct on w. Variable names are
    # immaterial; the theorem is the usual (a+b)+c = a+(b+c).
    assoc_body = Eq(
        Add(Add(X, Z), W),
        Add(X, Add(Z, W)),
    )
    assoc_base = Eq(
        Add(Add(X, Z), ZERO),
        Add(X, Add(Z, ZERO)),
    )
    assoc_step = Eq(
        Add(Add(X, Z), Succ(W)),
        Add(X, Add(Z, Succ(W))),
    )

    proof_t8 = Proof(
        statement=ForAll(X, ForAll(Z, ForAll(W, assoc_body))),
        steps=(
            ProofStep(
                conclusion=AXIOM_ADD_ZERO.formula,
                rule=RULE_AXIOM,
                source=AXIOM_ADD_ZERO.name,
            ),
            ProofStep(
                conclusion=Eq(Add(Add(X, Z), ZERO), Add(X, Z)),
                rule=RULE_FORALL_ELIM,
                premises=(0,),
                term=Add(X, Z),
            ),
            ProofStep(
                conclusion=Eq(Add(Z, ZERO), Z),
                rule=RULE_FORALL_ELIM,
                premises=(0,),
                term=Z,
            ),
            ProofStep(
                conclusion=Eq(
                    Add(X, Add(Z, ZERO)),
                    Add(X, Z),
                ),
                rule=RULE_EQ_ADD_RIGHT_CONGRUENCE,
                premises=(2,),
                term=X,
            ),
            ProofStep(
                conclusion=Eq(
                    Add(X, Z),
                    Add(X, Add(Z, ZERO)),
                ),
                rule=RULE_EQ_SYMMETRY,
                premises=(3,),
            ),
            ProofStep(
                conclusion=assoc_base,
                rule=RULE_EQ_TRANSITIVITY,
                premises=(1, 4),
            ),
            ProofStep(
                conclusion=assoc_body,
                rule=RULE_ASSUMPTION,
                note="Induction hypothesis for associativity.",
            ),
            ProofStep(
                conclusion=AXIOM_ADD_SUCCESSOR.formula,
                rule=RULE_AXIOM,
                source=AXIOM_ADD_SUCCESSOR.name,
            ),
            ProofStep(
                conclusion=ForAll(
                    Y,
                    Eq(
                        Add(Add(X, Z), Succ(Y)),
                        Succ(Add(Add(X, Z), Y)),
                    ),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(7,),
                term=Add(X, Z),
            ),
            ProofStep(
                conclusion=Eq(
                    Add(Add(X, Z), Succ(W)),
                    Succ(Add(Add(X, Z), W)),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(8,),
                term=W,
            ),
            ProofStep(
                conclusion=Eq(
                    Succ(Add(Add(X, Z), W)),
                    Succ(Add(X, Add(Z, W))),
                ),
                rule=RULE_EQ_SUCC_CONGRUENCE,
                premises=(6,),
            ),
            ProofStep(
                conclusion=Eq(
                    Add(Add(X, Z), Succ(W)),
                    Succ(Add(X, Add(Z, W))),
                ),
                rule=RULE_EQ_TRANSITIVITY,
                premises=(9, 10),
            ),
            ProofStep(
                conclusion=ForAll(
                    Y,
                    Eq(Add(Z, Succ(Y)), Succ(Add(Z, Y))),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(7,),
                term=Z,
            ),
            ProofStep(
                conclusion=Eq(
                    Add(Z, Succ(W)),
                    Succ(Add(Z, W)),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(12,),
                term=W,
            ),
            ProofStep(
                conclusion=Eq(
                    Add(X, Add(Z, Succ(W))),
                    Add(X, Succ(Add(Z, W))),
                ),
                rule=RULE_EQ_ADD_RIGHT_CONGRUENCE,
                premises=(13,),
                term=X,
            ),
            ProofStep(
                conclusion=ForAll(
                    Y,
                    Eq(Add(X, Succ(Y)), Succ(Add(X, Y))),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(7,),
                term=X,
            ),
            ProofStep(
                conclusion=Eq(
                    Add(X, Succ(Add(Z, W))),
                    Succ(Add(X, Add(Z, W))),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(15,),
                term=Add(Z, W),
            ),
            ProofStep(
                conclusion=Eq(
                    Add(X, Add(Z, Succ(W))),
                    Succ(Add(X, Add(Z, W))),
                ),
                rule=RULE_EQ_TRANSITIVITY,
                premises=(14, 16),
            ),
            ProofStep(
                conclusion=Eq(
                    Succ(Add(X, Add(Z, W))),
                    Add(X, Add(Z, Succ(W))),
                ),
                rule=RULE_EQ_SYMMETRY,
                premises=(17,),
            ),
            ProofStep(
                conclusion=assoc_step,
                rule=RULE_EQ_TRANSITIVITY,
                premises=(11, 18),
            ),
            ProofStep(
                conclusion=ForAll(W, assoc_body),
                rule=RULE_INDUCTION,
                premises=(5, 19),
                variable=W,
                discharge=6,
            ),
            ProofStep(
                conclusion=ForAll(Z, ForAll(W, assoc_body)),
                rule=RULE_FORALL_INTRO,
                premises=(20,),
                variable=Z,
            ),
            ProofStep(
                conclusion=ForAll(X, ForAll(Z, ForAll(W, assoc_body))),
                rule=RULE_FORALL_INTRO,
                premises=(21,),
                variable=X,
            ),
        ),
    )
    state.add_theorem("T8_ADD_ASSOCIATIVE", proof_t8)

    # T9: zero multiplied by any number is zero.
    zero_mul_y = Eq(Mul(ZERO, Y), ZERO)
    zero_mul_sy = Eq(Mul(ZERO, Succ(Y)), ZERO)

    proof_t9 = Proof(
        statement=ForAll(Y, zero_mul_y),
        steps=(
            ProofStep(
                conclusion=AXIOM_MUL_ZERO.formula,
                rule=RULE_AXIOM,
                source=AXIOM_MUL_ZERO.name,
            ),
            ProofStep(
                conclusion=Eq(Mul(ZERO, ZERO), ZERO),
                rule=RULE_FORALL_ELIM,
                premises=(0,),
                term=ZERO,
            ),
            ProofStep(
                conclusion=zero_mul_y,
                rule=RULE_ASSUMPTION,
                note="Induction hypothesis: 0*y = 0.",
            ),
            ProofStep(
                conclusion=AXIOM_MUL_SUCCESSOR.formula,
                rule=RULE_AXIOM,
                source=AXIOM_MUL_SUCCESSOR.name,
            ),
            ProofStep(
                conclusion=ForAll(
                    Y,
                    Eq(
                        Mul(ZERO, Succ(Y)),
                        Add(Mul(ZERO, Y), ZERO),
                    ),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(3,),
                term=ZERO,
            ),
            ProofStep(
                conclusion=Eq(
                    Mul(ZERO, Succ(Y)),
                    Add(Mul(ZERO, Y), ZERO),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(4,),
                term=Y,
            ),
            ProofStep(
                conclusion=AXIOM_ADD_ZERO.formula,
                rule=RULE_AXIOM,
                source=AXIOM_ADD_ZERO.name,
            ),
            ProofStep(
                conclusion=Eq(
                    Add(Mul(ZERO, Y), ZERO),
                    Mul(ZERO, Y),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(6,),
                term=Mul(ZERO, Y),
            ),
            ProofStep(
                conclusion=Eq(
                    Mul(ZERO, Succ(Y)),
                    Mul(ZERO, Y),
                ),
                rule=RULE_EQ_TRANSITIVITY,
                premises=(5, 7),
            ),
            ProofStep(
                conclusion=zero_mul_sy,
                rule=RULE_EQ_TRANSITIVITY,
                premises=(8, 2),
            ),
            ProofStep(
                conclusion=ForAll(Y, zero_mul_y),
                rule=RULE_INDUCTION,
                premises=(1, 9),
                variable=Y,
                discharge=2,
            ),
        ),
    )
    state.add_theorem("T9_ZERO_MUL_X", proof_t9)

    # T10: multiplying by one on the right leaves a number unchanged.
    mul_one_x = Eq(Mul(X, ONE), X)
    proof_t10 = Proof(
        statement=ForAll(X, mul_one_x),
        steps=(
            ProofStep(
                conclusion=AXIOM_MUL_SUCCESSOR.formula,
                rule=RULE_AXIOM,
                source=AXIOM_MUL_SUCCESSOR.name,
            ),
            ProofStep(
                conclusion=ForAll(
                    Y,
                    Eq(Mul(X, Succ(Y)), Add(Mul(X, Y), X)),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(0,),
                term=X,
            ),
            ProofStep(
                conclusion=Eq(
                    Mul(X, ONE),
                    Add(Mul(X, ZERO), X),
                ),
                rule=RULE_FORALL_ELIM,
                premises=(1,),
                term=ZERO,
            ),
            ProofStep(
                conclusion=AXIOM_MUL_ZERO.formula,
                rule=RULE_AXIOM,
                source=AXIOM_MUL_ZERO.name,
            ),
            ProofStep(
                conclusion=Eq(Mul(X, ZERO), ZERO),
                rule=RULE_FORALL_ELIM,
                premises=(3,),
                term=X,
            ),
            ProofStep(
                conclusion=Eq(
                    Add(Mul(X, ZERO), X),
                    Add(ZERO, X),
                ),
                rule=RULE_EQ_ADD_LEFT_CONGRUENCE,
                premises=(4,),
                term=X,
            ),
            ProofStep(
                conclusion=ForAll(X, Eq(Add(ZERO, X), X)),
                rule=RULE_THEOREM,
                source="T5_ZERO_PLUS_X",
            ),
            ProofStep(
                conclusion=Eq(Add(ZERO, X), X),
                rule=RULE_FORALL_ELIM,
                premises=(6,),
                term=X,
            ),
            ProofStep(
                conclusion=Eq(Mul(X, ONE), Add(ZERO, X)),
                rule=RULE_EQ_TRANSITIVITY,
                premises=(2, 5),
            ),
            ProofStep(
                conclusion=mul_one_x,
                rule=RULE_EQ_TRANSITIVITY,
                premises=(8, 7),
            ),
            ProofStep(
                conclusion=ForAll(X, mul_one_x),
                rule=RULE_FORALL_INTRO,
                premises=(9,),
                variable=X,
            ),
        ),
    )
    state.add_theorem("T10_MUL_ONE", proof_t10)

    # T11: successor in the left factor.
    left_succ_body = Eq(
        Mul(Succ(X), Z),
        Add(Mul(X, Z), Z),
    )
    left_succ_base = Eq(
        Mul(Succ(X), ZERO),
        Add(Mul(X, ZERO), ZERO),
    )
    left_succ_step = Eq(
        Mul(Succ(X), Succ(Z)),
        Add(Mul(X, Succ(Z)), Succ(Z)),
    )

    proof_t11 = Proof(
        statement=ForAll(X, ForAll(Z, left_succ_body)),
        steps=(
            ProofStep(AXIOM_MUL_ZERO.formula, RULE_AXIOM, source=AXIOM_MUL_ZERO.name),
            ProofStep(
                Eq(Mul(Succ(X), ZERO), ZERO),
                RULE_FORALL_ELIM,
                premises=(0,),
                term=Succ(X),
            ),
            ProofStep(
                Eq(Mul(X, ZERO), ZERO),
                RULE_FORALL_ELIM,
                premises=(0,),
                term=X,
            ),
            ProofStep(AXIOM_ADD_ZERO.formula, RULE_AXIOM, source=AXIOM_ADD_ZERO.name),
            ProofStep(
                Eq(Add(Mul(X, ZERO), ZERO), Mul(X, ZERO)),
                RULE_FORALL_ELIM,
                premises=(3,),
                term=Mul(X, ZERO),
            ),
            ProofStep(
                Eq(Add(Mul(X, ZERO), ZERO), ZERO),
                RULE_EQ_TRANSITIVITY,
                premises=(4, 2),
            ),
            ProofStep(
                Eq(ZERO, Add(Mul(X, ZERO), ZERO)),
                RULE_EQ_SYMMETRY,
                premises=(5,),
            ),
            ProofStep(
                left_succ_base,
                RULE_EQ_TRANSITIVITY,
                premises=(1, 6),
            ),
            ProofStep(
                left_succ_body,
                RULE_ASSUMPTION,
                note="Induction hypothesis for successor in the left factor.",
            ),
            ProofStep(
                AXIOM_MUL_SUCCESSOR.formula,
                RULE_AXIOM,
                source=AXIOM_MUL_SUCCESSOR.name,
            ),
            ProofStep(
                ForAll(
                    W,
                    Eq(
                        Mul(Succ(X), Succ(W)),
                        Add(Mul(Succ(X), W), Succ(X)),
                    ),
                ),
                RULE_FORALL_ELIM,
                premises=(9,),
                term=Succ(X),
            ),
            ProofStep(
                Eq(
                    Mul(Succ(X), Succ(Z)),
                    Add(Mul(Succ(X), Z), Succ(X)),
                ),
                RULE_FORALL_ELIM,
                premises=(10,),
                term=Z,
            ),
            ProofStep(
                Eq(
                    Add(Mul(Succ(X), Z), Succ(X)),
                    Add(Add(Mul(X, Z), Z), Succ(X)),
                ),
                RULE_EQ_ADD_LEFT_CONGRUENCE,
                premises=(8,),
                term=Succ(X),
            ),
            ProofStep(
                Eq(
                    Mul(Succ(X), Succ(Z)),
                    Add(Add(Mul(X, Z), Z), Succ(X)),
                ),
                RULE_EQ_TRANSITIVITY,
                premises=(11, 12),
            ),
            ProofStep(
                AXIOM_ADD_SUCCESSOR.formula,
                RULE_AXIOM,
                source=AXIOM_ADD_SUCCESSOR.name,
            ),
            ProofStep(
                ForAll(
                    W,
                    Eq(
                        Add(Add(Mul(X, Z), Z), Succ(W)),
                        Succ(Add(Add(Mul(X, Z), Z), W)),
                    ),
                ),
                RULE_FORALL_ELIM,
                premises=(14,),
                term=Add(Mul(X, Z), Z),
            ),
            ProofStep(
                Eq(
                    Add(Add(Mul(X, Z), Z), Succ(X)),
                    Succ(Add(Add(Mul(X, Z), Z), X)),
                ),
                RULE_FORALL_ELIM,
                premises=(15,),
                term=X,
            ),
            ProofStep(
                ForAll(X, ForAll(Z, ForAll(W, Eq(
                    Add(Add(X, Z), W),
                    Add(X, Add(Z, W)),
                )))),
                RULE_THEOREM,
                source="T8_ADD_ASSOCIATIVE",
            ),
            ProofStep(
                ForAll(Z, ForAll(W, Eq(
                    Add(Add(Mul(X, Z), Z), W),
                    Add(Mul(X, Z), Add(Z, W)),
                ))),
                RULE_FORALL_ELIM,
                premises=(17,),
                term=Mul(X, Z),
            ),
            ProofStep(
                ForAll(W, Eq(
                    Add(Add(Mul(X, Z), Z), W),
                    Add(Mul(X, Z), Add(Z, W)),
                )),
                RULE_FORALL_ELIM,
                premises=(18,),
                term=Z,
            ),
            ProofStep(
                Eq(
                    Add(Add(Mul(X, Z), Z), X),
                    Add(Mul(X, Z), Add(Z, X)),
                ),
                RULE_FORALL_ELIM,
                premises=(19,),
                term=X,
            ),
            ProofStep(
                ForAll(X, ForAll(Y, Eq(Add(X, Y), Add(Y, X)))),
                RULE_THEOREM,
                source="T7_ADD_COMMUTATIVE",
            ),
            ProofStep(
                ForAll(Y, Eq(Add(Z, Y), Add(Y, Z))),
                RULE_FORALL_ELIM,
                premises=(21,),
                term=Z,
            ),
            ProofStep(
                Eq(Add(Z, X), Add(X, Z)),
                RULE_FORALL_ELIM,
                premises=(22,),
                term=X,
            ),
            ProofStep(
                Eq(
                    Add(Mul(X, Z), Add(Z, X)),
                    Add(Mul(X, Z), Add(X, Z)),
                ),
                RULE_EQ_ADD_RIGHT_CONGRUENCE,
                premises=(23,),
                term=Mul(X, Z),
            ),
            ProofStep(
                ForAll(Z, ForAll(W, Eq(
                    Add(Add(Mul(X, Z), Z), W),
                    Add(Mul(X, Z), Add(Z, W)),
                ))),
                RULE_FORALL_ELIM,
                premises=(17,),
                term=Mul(X, Z),
            ),
            ProofStep(
                ForAll(W, Eq(
                    Add(Add(Mul(X, Z), X), W),
                    Add(Mul(X, Z), Add(X, W)),
                )),
                RULE_FORALL_ELIM,
                premises=(25,),
                term=X,
            ),
            ProofStep(
                Eq(
                    Add(Add(Mul(X, Z), X), Z),
                    Add(Mul(X, Z), Add(X, Z)),
                ),
                RULE_FORALL_ELIM,
                premises=(26,),
                term=Z,
            ),
            ProofStep(
                Eq(
                    Add(Mul(X, Z), Add(X, Z)),
                    Add(Add(Mul(X, Z), X), Z),
                ),
                RULE_EQ_SYMMETRY,
                premises=(27,),
            ),
            ProofStep(
                Eq(
                    Add(Add(Mul(X, Z), Z), X),
                    Add(Mul(X, Z), Add(X, Z)),
                ),
                RULE_EQ_TRANSITIVITY,
                premises=(20, 24),
            ),
            ProofStep(
                Eq(
                    Add(Add(Mul(X, Z), Z), X),
                    Add(Add(Mul(X, Z), X), Z),
                ),
                RULE_EQ_TRANSITIVITY,
                premises=(29, 28),
            ),
            ProofStep(
                Eq(
                    Succ(Add(Add(Mul(X, Z), Z), X)),
                    Succ(Add(Add(Mul(X, Z), X), Z)),
                ),
                RULE_EQ_SUCC_CONGRUENCE,
                premises=(30,),
            ),
            ProofStep(
                Eq(
                    Add(Add(Mul(X, Z), Z), Succ(X)),
                    Succ(Add(Add(Mul(X, Z), X), Z)),
                ),
                RULE_EQ_TRANSITIVITY,
                premises=(16, 31),
            ),
            ProofStep(
                ForAll(
                    W,
                    Eq(
                        Add(Add(Mul(X, Z), X), Succ(W)),
                        Succ(Add(Add(Mul(X, Z), X), W)),
                    ),
                ),
                RULE_FORALL_ELIM,
                premises=(14,),
                term=Add(Mul(X, Z), X),
            ),
            ProofStep(
                Eq(
                    Add(Add(Mul(X, Z), X), Succ(Z)),
                    Succ(Add(Add(Mul(X, Z), X), Z)),
                ),
                RULE_FORALL_ELIM,
                premises=(33,),
                term=Z,
            ),
            ProofStep(
                Eq(
                    Succ(Add(Add(Mul(X, Z), X), Z)),
                    Add(Add(Mul(X, Z), X), Succ(Z)),
                ),
                RULE_EQ_SYMMETRY,
                premises=(34,),
            ),
            ProofStep(
                Eq(
                    Add(Add(Mul(X, Z), Z), Succ(X)),
                    Add(Add(Mul(X, Z), X), Succ(Z)),
                ),
                RULE_EQ_TRANSITIVITY,
                premises=(32, 35),
            ),
            ProofStep(
                ForAll(
                    W,
                    Eq(Mul(X, Succ(W)), Add(Mul(X, W), X)),
                ),
                RULE_FORALL_ELIM,
                premises=(9,),
                term=X,
            ),
            ProofStep(
                Eq(Mul(X, Succ(Z)), Add(Mul(X, Z), X)),
                RULE_FORALL_ELIM,
                premises=(37,),
                term=Z,
            ),
            ProofStep(
                Eq(
                    Add(Mul(X, Succ(Z)), Succ(Z)),
                    Add(Add(Mul(X, Z), X), Succ(Z)),
                ),
                RULE_EQ_ADD_LEFT_CONGRUENCE,
                premises=(38,),
                term=Succ(Z),
            ),
            ProofStep(
                Eq(
                    Add(Add(Mul(X, Z), X), Succ(Z)),
                    Add(Mul(X, Succ(Z)), Succ(Z)),
                ),
                RULE_EQ_SYMMETRY,
                premises=(39,),
            ),
            ProofStep(
                Eq(
                    Mul(Succ(X), Succ(Z)),
                    Add(Add(Mul(X, Z), X), Succ(Z)),
                ),
                RULE_EQ_TRANSITIVITY,
                premises=(13, 36),
            ),
            ProofStep(
                left_succ_step,
                RULE_EQ_TRANSITIVITY,
                premises=(41, 40),
            ),
            ProofStep(
                ForAll(Z, left_succ_body),
                RULE_INDUCTION,
                premises=(7, 42),
                variable=Z,
                discharge=8,
            ),
            ProofStep(
                ForAll(X, ForAll(Z, left_succ_body)),
                RULE_FORALL_INTRO,
                premises=(43,),
                variable=X,
            ),
        ),
    )
    state.add_theorem("T11_MUL_SUCC_LEFT", proof_t11)

    # T12: commutativity of multiplication.
    mul_comm_body = Eq(Mul(X, Y), Mul(Y, X))
    mul_comm_base = Eq(Mul(X, ZERO), Mul(ZERO, X))
    mul_comm_step = Eq(Mul(X, Succ(Y)), Mul(Succ(Y), X))

    proof_t12 = Proof(
        statement=ForAll(X, ForAll(Y, mul_comm_body)),
        steps=(
            ProofStep(AXIOM_MUL_ZERO.formula, RULE_AXIOM, source=AXIOM_MUL_ZERO.name),
            ProofStep(
                Eq(Mul(X, ZERO), ZERO),
                RULE_FORALL_ELIM,
                premises=(0,),
                term=X,
            ),
            ProofStep(
                ForAll(Y, Eq(Mul(ZERO, Y), ZERO)),
                RULE_THEOREM,
                source="T9_ZERO_MUL_X",
            ),
            ProofStep(
                Eq(Mul(ZERO, X), ZERO),
                RULE_FORALL_ELIM,
                premises=(2,),
                term=X,
            ),
            ProofStep(
                Eq(ZERO, Mul(ZERO, X)),
                RULE_EQ_SYMMETRY,
                premises=(3,),
            ),
            ProofStep(
                mul_comm_base,
                RULE_EQ_TRANSITIVITY,
                premises=(1, 4),
            ),
            ProofStep(
                mul_comm_body,
                RULE_ASSUMPTION,
                note="Induction hypothesis for multiplication commutativity.",
            ),
            ProofStep(
                AXIOM_MUL_SUCCESSOR.formula,
                RULE_AXIOM,
                source=AXIOM_MUL_SUCCESSOR.name,
            ),
            ProofStep(
                ForAll(
                    Z,
                    Eq(Mul(X, Succ(Z)), Add(Mul(X, Z), X)),
                ),
                RULE_FORALL_ELIM,
                premises=(7,),
                term=X,
            ),
            ProofStep(
                Eq(Mul(X, Succ(Y)), Add(Mul(X, Y), X)),
                RULE_FORALL_ELIM,
                premises=(8,),
                term=Y,
            ),
            ProofStep(
                Eq(
                    Add(Mul(X, Y), X),
                    Add(Mul(Y, X), X),
                ),
                RULE_EQ_ADD_LEFT_CONGRUENCE,
                premises=(6,),
                term=X,
            ),
            ProofStep(
                Eq(
                    Mul(X, Succ(Y)),
                    Add(Mul(Y, X), X),
                ),
                RULE_EQ_TRANSITIVITY,
                premises=(9, 10),
            ),
            ProofStep(
                ForAll(X, ForAll(Z, Eq(
                    Mul(Succ(X), Z),
                    Add(Mul(X, Z), Z),
                ))),
                RULE_THEOREM,
                source="T11_MUL_SUCC_LEFT",
            ),
            ProofStep(
                ForAll(Z, Eq(
                    Mul(Succ(Y), Z),
                    Add(Mul(Y, Z), Z),
                )),
                RULE_FORALL_ELIM,
                premises=(12,),
                term=Y,
            ),
            ProofStep(
                Eq(
                    Mul(Succ(Y), X),
                    Add(Mul(Y, X), X),
                ),
                RULE_FORALL_ELIM,
                premises=(13,),
                term=X,
            ),
            ProofStep(
                Eq(
                    Add(Mul(Y, X), X),
                    Mul(Succ(Y), X),
                ),
                RULE_EQ_SYMMETRY,
                premises=(14,),
            ),
            ProofStep(
                mul_comm_step,
                RULE_EQ_TRANSITIVITY,
                premises=(11, 15),
            ),
            ProofStep(
                ForAll(Y, mul_comm_body),
                RULE_INDUCTION,
                premises=(5, 16),
                variable=Y,
                discharge=6,
            ),
            ProofStep(
                ForAll(X, ForAll(Y, mul_comm_body)),
                RULE_FORALL_INTRO,
                premises=(17,),
                variable=X,
            ),
        ),
    )
    state.add_theorem("T12_MUL_COMMUTATIVE", proof_t12)

    # T13: right distributivity of multiplication over addition.
    dist_body = Eq(
        Mul(X, Add(Y, W)),
        Add(Mul(X, Y), Mul(X, W)),
    )
    dist_base = Eq(
        Mul(X, Add(Y, ZERO)),
        Add(Mul(X, Y), Mul(X, ZERO)),
    )
    dist_step = Eq(
        Mul(X, Add(Y, Succ(W))),
        Add(Mul(X, Y), Mul(X, Succ(W))),
    )

    proof_t13 = Proof(
        statement=ForAll(X, ForAll(Y, ForAll(W, dist_body))),
        steps=(
            ProofStep(AXIOM_ADD_ZERO.formula, RULE_AXIOM, source=AXIOM_ADD_ZERO.name),
            ProofStep(
                Eq(Add(Y, ZERO), Y),
                RULE_FORALL_ELIM,
                premises=(0,),
                term=Y,
            ),
            ProofStep(
                Eq(Mul(X, Add(Y, ZERO)), Mul(X, Y)),
                RULE_EQ_MUL_RIGHT_CONGRUENCE,
                premises=(1,),
                term=X,
            ),
            ProofStep(AXIOM_MUL_ZERO.formula, RULE_AXIOM, source=AXIOM_MUL_ZERO.name),
            ProofStep(
                Eq(Mul(X, ZERO), ZERO),
                RULE_FORALL_ELIM,
                premises=(3,),
                term=X,
            ),
            ProofStep(
                Eq(
                    Add(Mul(X, Y), Mul(X, ZERO)),
                    Add(Mul(X, Y), ZERO),
                ),
                RULE_EQ_ADD_RIGHT_CONGRUENCE,
                premises=(4,),
                term=Mul(X, Y),
            ),
            ProofStep(
                Eq(Add(Mul(X, Y), ZERO), Mul(X, Y)),
                RULE_FORALL_ELIM,
                premises=(0,),
                term=Mul(X, Y),
            ),
            ProofStep(
                Eq(
                    Add(Mul(X, Y), Mul(X, ZERO)),
                    Mul(X, Y),
                ),
                RULE_EQ_TRANSITIVITY,
                premises=(5, 6),
            ),
            ProofStep(
                Eq(
                    Mul(X, Y),
                    Add(Mul(X, Y), Mul(X, ZERO)),
                ),
                RULE_EQ_SYMMETRY,
                premises=(7,),
            ),
            ProofStep(
                dist_base,
                RULE_EQ_TRANSITIVITY,
                premises=(2, 8),
            ),
            ProofStep(
                dist_body,
                RULE_ASSUMPTION,
                note="Induction hypothesis for distributivity.",
            ),
            ProofStep(
                AXIOM_ADD_SUCCESSOR.formula,
                RULE_AXIOM,
                source=AXIOM_ADD_SUCCESSOR.name,
            ),
            ProofStep(
                ForAll(
                    W,
                    Eq(Add(Y, Succ(W)), Succ(Add(Y, W))),
                ),
                RULE_FORALL_ELIM,
                premises=(11,),
                term=Y,
            ),
            ProofStep(
                Eq(Add(Y, Succ(W)), Succ(Add(Y, W))),
                RULE_FORALL_ELIM,
                premises=(12,),
                term=W,
            ),
            ProofStep(
                Eq(
                    Mul(X, Add(Y, Succ(W))),
                    Mul(X, Succ(Add(Y, W))),
                ),
                RULE_EQ_MUL_RIGHT_CONGRUENCE,
                premises=(13,),
                term=X,
            ),
            ProofStep(
                AXIOM_MUL_SUCCESSOR.formula,
                RULE_AXIOM,
                source=AXIOM_MUL_SUCCESSOR.name,
            ),
            ProofStep(
                ForAll(
                    W,
                    Eq(Mul(X, Succ(W)), Add(Mul(X, W), X)),
                ),
                RULE_FORALL_ELIM,
                premises=(15,),
                term=X,
            ),
            ProofStep(
                Eq(
                    Mul(X, Succ(Add(Y, W))),
                    Add(Mul(X, Add(Y, W)), X),
                ),
                RULE_FORALL_ELIM,
                premises=(16,),
                term=Add(Y, W),
            ),
            ProofStep(
                Eq(
                    Mul(X, Add(Y, Succ(W))),
                    Add(Mul(X, Add(Y, W)), X),
                ),
                RULE_EQ_TRANSITIVITY,
                premises=(14, 17),
            ),
            ProofStep(
                Eq(
                    Add(Mul(X, Add(Y, W)), X),
                    Add(Add(Mul(X, Y), Mul(X, W)), X),
                ),
                RULE_EQ_ADD_LEFT_CONGRUENCE,
                premises=(10,),
                term=X,
            ),
            ProofStep(
                Eq(
                    Mul(X, Add(Y, Succ(W))),
                    Add(Add(Mul(X, Y), Mul(X, W)), X),
                ),
                RULE_EQ_TRANSITIVITY,
                premises=(18, 19),
            ),
            ProofStep(
                ForAll(X, ForAll(Z, ForAll(W, Eq(
                    Add(Add(X, Z), W),
                    Add(X, Add(Z, W)),
                )))),
                RULE_THEOREM,
                source="T8_ADD_ASSOCIATIVE",
            ),
            ProofStep(
                ForAll(Z, ForAll(W, Eq(
                    Add(Add(Mul(X, Y), Z), W),
                    Add(Mul(X, Y), Add(Z, W)),
                ))),
                RULE_FORALL_ELIM,
                premises=(21,),
                term=Mul(X, Y),
            ),
            ProofStep(
                ForAll(W, Eq(
                    Add(Add(Mul(X, Y), Mul(X, W)), W),
                    Add(Mul(X, Y), Add(Mul(X, W), W)),
                )),
                RULE_FORALL_ELIM,
                premises=(22,),
                term=Mul(X, W),
            ),
            ProofStep(
                Eq(
                    Add(Add(Mul(X, Y), Mul(X, W)), X),
                    Add(Mul(X, Y), Add(Mul(X, W), X)),
                ),
                RULE_FORALL_ELIM,
                premises=(23,),
                term=X,
            ),
            ProofStep(
                Eq(
                    Mul(X, Add(Y, Succ(W))),
                    Add(Mul(X, Y), Add(Mul(X, W), X)),
                ),
                RULE_EQ_TRANSITIVITY,
                premises=(20, 24),
            ),
            ProofStep(
                Eq(Mul(X, Succ(W)), Add(Mul(X, W), X)),
                RULE_FORALL_ELIM,
                premises=(16,),
                term=W,
            ),
            ProofStep(
                Eq(
                    Add(Mul(X, Y), Mul(X, Succ(W))),
                    Add(Mul(X, Y), Add(Mul(X, W), X)),
                ),
                RULE_EQ_ADD_RIGHT_CONGRUENCE,
                premises=(26,),
                term=Mul(X, Y),
            ),
            ProofStep(
                Eq(
                    Add(Mul(X, Y), Add(Mul(X, W), X)),
                    Add(Mul(X, Y), Mul(X, Succ(W))),
                ),
                RULE_EQ_SYMMETRY,
                premises=(27,),
            ),
            ProofStep(
                dist_step,
                RULE_EQ_TRANSITIVITY,
                premises=(25, 28),
            ),
            ProofStep(
                ForAll(W, dist_body),
                RULE_INDUCTION,
                premises=(9, 29),
                variable=W,
                discharge=10,
            ),
            ProofStep(
                ForAll(Y, ForAll(W, dist_body)),
                RULE_FORALL_INTRO,
                premises=(30,),
                variable=Y,
            ),
            ProofStep(
                ForAll(X, ForAll(Y, ForAll(W, dist_body))),
                RULE_FORALL_INTRO,
                premises=(31,),
                variable=X,
            ),
        ),
    )
    state.add_theorem("T13_MUL_DISTRIBUTIVE", proof_t13)

    # T14: associativity of multiplication.
    mul_assoc_body = Eq(
        Mul(Mul(X, Y), Z),
        Mul(X, Mul(Y, Z)),
    )
    mul_assoc_base = Eq(
        Mul(Mul(X, Y), ZERO),
        Mul(X, Mul(Y, ZERO)),
    )
    mul_assoc_step = Eq(
        Mul(Mul(X, Y), Succ(Z)),
        Mul(X, Mul(Y, Succ(Z))),
    )

    proof_t14 = Proof(
        statement=ForAll(X, ForAll(Y, ForAll(Z, mul_assoc_body))),
        steps=(
            ProofStep(AXIOM_MUL_ZERO.formula, RULE_AXIOM, source=AXIOM_MUL_ZERO.name),
            ProofStep(
                Eq(Mul(Mul(X, Y), ZERO), ZERO),
                RULE_FORALL_ELIM,
                premises=(0,),
                term=Mul(X, Y),
            ),
            ProofStep(
                Eq(Mul(Y, ZERO), ZERO),
                RULE_FORALL_ELIM,
                premises=(0,),
                term=Y,
            ),
            ProofStep(
                Eq(
                    Mul(X, Mul(Y, ZERO)),
                    Mul(X, ZERO),
                ),
                RULE_EQ_MUL_RIGHT_CONGRUENCE,
                premises=(2,),
                term=X,
            ),
            ProofStep(
                Eq(Mul(X, ZERO), ZERO),
                RULE_FORALL_ELIM,
                premises=(0,),
                term=X,
            ),
            ProofStep(
                Eq(Mul(X, Mul(Y, ZERO)), ZERO),
                RULE_EQ_TRANSITIVITY,
                premises=(3, 4),
            ),
            ProofStep(
                Eq(ZERO, Mul(X, Mul(Y, ZERO))),
                RULE_EQ_SYMMETRY,
                premises=(5,),
            ),
            ProofStep(
                mul_assoc_base,
                RULE_EQ_TRANSITIVITY,
                premises=(1, 6),
            ),
            ProofStep(
                mul_assoc_body,
                RULE_ASSUMPTION,
                note="Induction hypothesis for multiplication associativity.",
            ),
            ProofStep(
                AXIOM_MUL_SUCCESSOR.formula,
                RULE_AXIOM,
                source=AXIOM_MUL_SUCCESSOR.name,
            ),
            ProofStep(
                ForAll(
                    W,
                    Eq(
                        Mul(Mul(X, Y), Succ(W)),
                        Add(Mul(Mul(X, Y), W), Mul(X, Y)),
                    ),
                ),
                RULE_FORALL_ELIM,
                premises=(9,),
                term=Mul(X, Y),
            ),
            ProofStep(
                Eq(
                    Mul(Mul(X, Y), Succ(Z)),
                    Add(Mul(Mul(X, Y), Z), Mul(X, Y)),
                ),
                RULE_FORALL_ELIM,
                premises=(10,),
                term=Z,
            ),
            ProofStep(
                Eq(
                    Add(Mul(Mul(X, Y), Z), Mul(X, Y)),
                    Add(Mul(X, Mul(Y, Z)), Mul(X, Y)),
                ),
                RULE_EQ_ADD_LEFT_CONGRUENCE,
                premises=(8,),
                term=Mul(X, Y),
            ),
            ProofStep(
                Eq(
                    Mul(Mul(X, Y), Succ(Z)),
                    Add(Mul(X, Mul(Y, Z)), Mul(X, Y)),
                ),
                RULE_EQ_TRANSITIVITY,
                premises=(11, 12),
            ),
            ProofStep(
                ForAll(
                    W,
                    Eq(Mul(Y, Succ(W)), Add(Mul(Y, W), Y)),
                ),
                RULE_FORALL_ELIM,
                premises=(9,),
                term=Y,
            ),
            ProofStep(
                Eq(Mul(Y, Succ(Z)), Add(Mul(Y, Z), Y)),
                RULE_FORALL_ELIM,
                premises=(14,),
                term=Z,
            ),
            ProofStep(
                Eq(
                    Mul(X, Mul(Y, Succ(Z))),
                    Mul(X, Add(Mul(Y, Z), Y)),
                ),
                RULE_EQ_MUL_RIGHT_CONGRUENCE,
                premises=(15,),
                term=X,
            ),
            ProofStep(
                ForAll(X, ForAll(Y, ForAll(W, Eq(
                    Mul(X, Add(Y, W)),
                    Add(Mul(X, Y), Mul(X, W)),
                )))),
                RULE_THEOREM,
                source="T13_MUL_DISTRIBUTIVE",
            ),
            ProofStep(
                ForAll(Y, ForAll(W, Eq(
                    Mul(X, Add(Y, W)),
                    Add(Mul(X, Y), Mul(X, W)),
                ))),
                RULE_FORALL_ELIM,
                premises=(17,),
                term=X,
            ),
            ProofStep(
                ForAll(W, Eq(
                    Mul(X, Add(Mul(Y, Z), W)),
                    Add(Mul(X, Mul(Y, Z)), Mul(X, W)),
                )),
                RULE_FORALL_ELIM,
                premises=(18,),
                term=Mul(Y, Z),
            ),
            ProofStep(
                Eq(
                    Mul(X, Add(Mul(Y, Z), Y)),
                    Add(Mul(X, Mul(Y, Z)), Mul(X, Y)),
                ),
                RULE_FORALL_ELIM,
                premises=(19,),
                term=Y,
            ),
            ProofStep(
                Eq(
                    Mul(X, Mul(Y, Succ(Z))),
                    Add(Mul(X, Mul(Y, Z)), Mul(X, Y)),
                ),
                RULE_EQ_TRANSITIVITY,
                premises=(16, 20),
            ),
            ProofStep(
                Eq(
                    Add(Mul(X, Mul(Y, Z)), Mul(X, Y)),
                    Mul(X, Mul(Y, Succ(Z))),
                ),
                RULE_EQ_SYMMETRY,
                premises=(21,),
            ),
            ProofStep(
                mul_assoc_step,
                RULE_EQ_TRANSITIVITY,
                premises=(13, 22),
            ),
            ProofStep(
                ForAll(Z, mul_assoc_body),
                RULE_INDUCTION,
                premises=(7, 23),
                variable=Z,
                discharge=8,
            ),
            ProofStep(
                ForAll(Y, ForAll(Z, mul_assoc_body)),
                RULE_FORALL_INTRO,
                premises=(24,),
                variable=Y,
            ),
            ProofStep(
                ForAll(X, ForAll(Y, ForAll(Z, mul_assoc_body))),
                RULE_FORALL_INTRO,
                premises=(25,),
                variable=X,
            ),
        ),
    )
    state.add_theorem("T14_MUL_ASSOCIATIVE", proof_t14)

    return state


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

    print("\nInference rules:")
    for rule in WORLD.inference_rules:
        print(f"  - {rule.name}")


def phase7_demo() -> None:
    print("Gareen Phase 7")
    print("================")
    print_world()

    state = build_initial_knowledge()
    print("\nVerified derived theorems:")
    for theorem in state.theorems.values():
        print(f"  - {theorem}")
        print(f"    dependencies: {', '.join(theorem.dependencies)}")

    expression = Add(TWO, THREE)
    result, trace = normalize(expression)
    print("\nSymbolic rewrite demo:")
    print("Start :", expression)
    for index, step in enumerate(trace, start=1):
        print(f"{index:>2}. {step.rule}")
        print("    ", step.before, "=>", step.after)
    print("Result:", result)

    product = Mul(TWO, THREE)
    product_result, product_trace = normalize(product)
    print("\nSymbolic multiplication demo:")
    print("Start :", product)
    for index, step in enumerate(product_trace, start=1):
        print(f"{index:>2}. {step.rule}")
        print("    ", step.before, "=>", step.after)
    print("Result:", product_result)


if __name__ == "__main__":
    phase7_demo()
