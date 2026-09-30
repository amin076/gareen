"""Gareen Phase 3: a tiny formal arithmetic world with auditable proofs.

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


ZERO = Zero()
X = Var("x")
Y = Var("y")


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

AXIOMS = (
    AXIOM_S_NONZERO,
    AXIOM_S_INJECTIVE,
    AXIOM_ADD_ZERO,
    AXIOM_ADD_SUCCESSOR,
)

RULE_AXIOM = "AXIOM"
RULE_THEOREM = "THEOREM"
RULE_ASSUMPTION = "ASSUMPTION"
RULE_FORALL_ELIM = "FORALL_ELIM"
RULE_MODUS_PONENS = "MODUS_PONENS"
RULE_EQ_SYMMETRY = "EQ_SYMMETRY"
RULE_CONTRADICTION = "CONTRADICTION"
RULE_NEGATION_INTRO = "NEGATION_INTRO"

INFERENCE_RULES = (
    InferenceRule(RULE_AXIOM, "Use a declared arithmetic axiom."),
    InferenceRule(RULE_THEOREM, "Reuse an already verified theorem."),
    InferenceRule(RULE_ASSUMPTION, "Open a temporary assumption for a subproof."),
    InferenceRule(RULE_FORALL_ELIM, "Instantiate ∀x.P(x) at a chosen term."),
    InferenceRule(RULE_MODUS_PONENS, "From P→Q and P, derive Q."),
    InferenceRule(RULE_EQ_SYMMETRY, "From a=b, derive b=a."),
    InferenceRule(RULE_CONTRADICTION, "From P and ¬P, derive ⊥."),
    InferenceRule(
        RULE_NEGATION_INTRO,
        "If assumption P leads to ⊥, discharge P and derive ¬P.",
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
    raise TypeError(f"Unsupported expression type: {type(expr)!r}")


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


def phase3_demo() -> None:
    print("Gareen Phase 3")
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


if __name__ == "__main__":
    phase3_demo()
