"""Gareen Phase 10: general conjecture discovery.

The explorer mines symbolic patterns from finite observations, proposes
universally quantified conjectures, and then demands a symbolic proof.

Finite agreement is evidence for proposing a conjecture, never evidence for
accepting it as mathematics.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Optional

from math_world import (
    ONE,
    THREE,
    TWO,
    X,
    ZERO,
    Add,
    Eq,
    Expr,
    ForAll,
    Formula,
    KnowledgeState,
    Mul,
    Proof,
    ProofCheckResult,
    ProofStep,
    Succ,
    Theorem,
    build_initial_knowledge,
    check_proof,
    free_vars_expr,
    normalize,
    substitute_expr,
    substitute_formula,
    RULE_FORALL_INTRO,
)
from proof_search import BoundedProofSearcher, SearchStats


@dataclass(frozen=True)
class PatternObservation:
    expression: Expr
    outputs: tuple[Expr, ...]


@dataclass(frozen=True)
class GeneralConjecture:
    body: Eq
    statement: ForAll
    left_observation: PatternObservation
    right_observation: PatternObservation
    heuristic_score: int


@dataclass(frozen=True)
class GeneralProofResult:
    conjecture: GeneralConjecture
    found: bool
    proof: Optional[Proof]
    check: Optional[ProofCheckResult]
    search_stats: Optional[SearchStats]


@dataclass(frozen=True)
class GeneralDiscoveryAttempt:
    statement: Formula
    status: str
    proof_steps: int
    heuristic_score: int
    reason: str = ""


@dataclass(frozen=True)
class GeneralDiscoveryRecord:
    theorem_name: str
    statement: Formula
    proof_steps: int
    heuristic_score: int
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class GeneralDiscoveryReport:
    generated_expressions: int
    pattern_classes: int
    generated_conjectures: int
    attempted_conjectures: int
    accepted_theorems: int
    attempts: tuple[GeneralDiscoveryAttempt, ...]
    discoveries: tuple[GeneralDiscoveryRecord, ...]


def _expr_size(expr: Expr) -> int:
    if expr == ZERO:
        return 1
    if isinstance(expr, Succ):
        return 1 + _expr_size(expr.value)
    if isinstance(expr, (Add, Mul)):
        return 1 + _expr_size(expr.left) + _expr_size(expr.right)
    return 1


def _operator_count(expr: Expr) -> int:
    if isinstance(expr, Succ):
        return 1 + _operator_count(expr.value)
    if isinstance(expr, (Add, Mul)):
        return 1 + _operator_count(expr.left) + _operator_count(expr.right)
    return 0


def _contains_variable(expr: Expr) -> bool:
    return bool(free_vars_expr(expr))


def _contains_mul(expr: Expr) -> bool:
    if isinstance(expr, Mul):
        return True
    if isinstance(expr, Succ):
        return _contains_mul(expr.value)
    if isinstance(expr, Add):
        return _contains_mul(expr.left) or _contains_mul(expr.right)
    return False


def generate_unary_expression_grammar() -> tuple[Expr, ...]:
    """Create a bounded grammar without specifying a theorem target."""

    bases: tuple[Expr, ...] = (X, ZERO, ONE, TWO)
    expressions: set[Expr] = set()

    for item in bases:
        expressions.add(item)
        expressions.add(Succ(item))

    for left in bases:
        for right in bases:
            expressions.add(Add(left, right))
            expressions.add(Mul(left, right))

    # A small second layer provides enough structure for pattern mining while
    # keeping Phase 10 deterministic and inexpensive.
    expressions.update(
        {
            Succ(Succ(X)),
            Add(Succ(X), ONE),
            Add(ONE, Succ(X)),
            Mul(Succ(X), ONE),
            Mul(ONE, Succ(X)),
            Add(X, X),
            Mul(X, TWO),
            Mul(TWO, X),
        }
    )

    return tuple(
        sorted(
            (expr for expr in expressions if _contains_variable(expr)),
            key=lambda expr: (_expr_size(expr), str(expr)),
        )
    )


def observe_expression(
    expr: Expr,
    samples: tuple[Expr, ...] = (ZERO, ONE, TWO, THREE),
) -> PatternObservation:
    outputs: list[Expr] = []

    for sample in samples:
        grounded = substitute_expr(expr, X, sample)
        normal, _ = normalize(grounded)
        outputs.append(normal)

    return PatternObservation(
        expression=expr,
        outputs=tuple(outputs),
    )


def mine_pattern_classes(
    expressions: tuple[Expr, ...],
) -> dict[tuple[Expr, ...], tuple[PatternObservation, ...]]:
    groups: dict[tuple[Expr, ...], list[PatternObservation]] = {}

    for expr in expressions:
        observation = observe_expression(expr)
        groups.setdefault(observation.outputs, []).append(observation)

    return {
        signature: tuple(items)
        for signature, items in groups.items()
        if len(items) >= 2
    }


def _canonical_equality(left: Expr, right: Expr) -> tuple[str, str]:
    a, b = str(left), str(right)
    return tuple(sorted((a, b)))


def _canonical_unary_statement(formula: Formula) -> Optional[tuple[str, str]]:
    if not isinstance(formula, ForAll):
        return None
    if isinstance(formula.body, ForAll):
        return None
    if not isinstance(formula.body, Eq):
        return None

    body = substitute_formula(formula.body, formula.variable, X)
    if not isinstance(body, Eq):
        return None
    return _canonical_equality(body.left, body.right)


def _conjecture_score(left: Expr, right: Expr) -> int:
    score = _operator_count(left) + _operator_count(right)
    if type(left) is not type(right):
        score += 3
    if _contains_mul(left) or _contains_mul(right):
        score += 2
    score += abs(_expr_size(left) - _expr_size(right))
    return score


def generate_general_conjectures(
    expressions: tuple[Expr, ...],
    state: KnowledgeState,
) -> tuple[GeneralConjecture, ...]:
    pattern_classes = mine_pattern_classes(expressions)

    existing_keys = {
        key
        for axiom in state.world.axioms
        if (key := _canonical_unary_statement(axiom.formula)) is not None
    }
    existing_keys.update(
        key
        for theorem in state.theorems.values()
        if (key := _canonical_unary_statement(theorem.statement)) is not None
    )

    conjectures: dict[tuple[str, str], GeneralConjecture] = {}

    for observations in pattern_classes.values():
        for left_obs, right_obs in combinations(observations, 2):
            left = left_obs.expression
            right = right_obs.expression

            if left == right:
                continue

            key = _canonical_equality(left, right)
            if key in existing_keys:
                continue

            body = Eq(left, right)
            statement = ForAll(X, body)

            conjectures.setdefault(
                key,
                GeneralConjecture(
                    body=body,
                    statement=statement,
                    left_observation=left_obs,
                    right_observation=right_obs,
                    heuristic_score=_conjecture_score(left, right),
                ),
            )

    return tuple(
        sorted(
            conjectures.values(),
            key=lambda item: (
                _expr_size(item.body.left) + _expr_size(item.body.right),
                -item.heuristic_score,
                str(item.statement),
            ),
        )
    )


class GeneralProofSearcher:
    """Prove an open equality, then close it universally."""

    def __init__(
        self,
        searcher: Optional[BoundedProofSearcher] = None,
    ) -> None:
        self.searcher = searcher or BoundedProofSearcher(
            max_depth=5,
            max_terms=28,
            instantiation_rounds=1,
            allow_open_goals=True,
        )

    def prove(
        self,
        conjecture: GeneralConjecture,
        state: KnowledgeState,
    ) -> GeneralProofResult:
        body_result = self.searcher.prove(conjecture.body, state)

        if not body_result.found or body_result.proof is None:
            return GeneralProofResult(
                conjecture=conjecture,
                found=False,
                proof=None,
                check=body_result.check,
                search_stats=body_result.stats,
            )

        body_steps = body_result.proof.steps
        if not body_steps:
            return GeneralProofResult(
                conjecture=conjecture,
                found=False,
                proof=None,
                check=None,
                search_stats=body_result.stats,
            )

        proof = Proof(
            statement=conjecture.statement,
            steps=body_steps
            + (
                ProofStep(
                    conclusion=conjecture.statement,
                    rule=RULE_FORALL_INTRO,
                    premises=(len(body_steps) - 1,),
                    variable=X,
                ),
            ),
        )

        check = check_proof(
            proof,
            axioms=state.world.axioms,
            known_theorems=tuple(state.theorems.values()),
        )

        return GeneralProofResult(
            conjecture=conjecture,
            found=check.valid,
            proof=proof if check.valid else None,
            check=check,
            search_stats=body_result.stats,
        )


def _next_general_name(state: KnowledgeState) -> str:
    index = 1
    while f"G{index}_AUTO" in state.theorems:
        index += 1
    return f"G{index}_AUTO"


class GeneralConjectureExplorer:
    """Mine patterns, propose universal laws, prove, verify, and store them."""

    def __init__(
        self,
        *,
        max_attempts: int = 10,
        max_discoveries: int = 3,
        min_proof_steps: int = 4,
        proof_searcher: Optional[GeneralProofSearcher] = None,
    ) -> None:
        self.max_attempts = max_attempts
        self.max_discoveries = max_discoveries
        self.min_proof_steps = min_proof_steps
        self.proof_searcher = proof_searcher or GeneralProofSearcher()

    def explore(self, state: KnowledgeState) -> GeneralDiscoveryReport:
        expressions = generate_unary_expression_grammar()
        pattern_classes = mine_pattern_classes(expressions)
        conjectures = generate_general_conjectures(expressions, state)

        attempts: list[GeneralDiscoveryAttempt] = []
        discoveries: list[GeneralDiscoveryRecord] = []

        for conjecture in conjectures:
            if len(attempts) >= self.max_attempts:
                break
            if len(discoveries) >= self.max_discoveries:
                break

            result = self.proof_searcher.prove(conjecture, state)

            if not result.found or result.proof is None:
                attempts.append(
                    GeneralDiscoveryAttempt(
                        statement=conjecture.statement,
                        status="unproved",
                        proof_steps=0,
                        heuristic_score=conjecture.heuristic_score,
                        reason=(
                            "Finite observations suggested the law, but bounded "
                            "symbolic proof search did not verify it."
                        ),
                    )
                )
                continue

            proof_steps = len(result.proof.steps)
            if proof_steps < self.min_proof_steps:
                attempts.append(
                    GeneralDiscoveryAttempt(
                        statement=conjecture.statement,
                        status="skipped-too-direct",
                        proof_steps=proof_steps,
                        heuristic_score=conjecture.heuristic_score,
                        reason="Verified but too direct for Phase 10 discovery storage.",
                    )
                )
                continue

            theorem_name = _next_general_name(state)
            theorem = state.add_theorem(theorem_name, result.proof)

            discoveries.append(
                GeneralDiscoveryRecord(
                    theorem_name=theorem.name,
                    statement=theorem.statement,
                    proof_steps=proof_steps,
                    heuristic_score=conjecture.heuristic_score,
                    dependencies=theorem.dependencies,
                )
            )
            attempts.append(
                GeneralDiscoveryAttempt(
                    statement=conjecture.statement,
                    status="accepted",
                    proof_steps=proof_steps,
                    heuristic_score=conjecture.heuristic_score,
                )
            )

        return GeneralDiscoveryReport(
            generated_expressions=len(expressions),
            pattern_classes=len(pattern_classes),
            generated_conjectures=len(conjectures),
            attempted_conjectures=len(attempts),
            accepted_theorems=len(discoveries),
            attempts=tuple(attempts),
            discoveries=tuple(discoveries),
        )


def phase10_demo() -> None:
    state = build_initial_knowledge()
    explorer = GeneralConjectureExplorer(
        max_attempts=8,
        max_discoveries=2,
        min_proof_steps=4,
    )

    report = explorer.explore(state)

    print("Gareen Phase 10")
    print("=================")
    print("Generated expressions:", report.generated_expressions)
    print("Pattern classes:", report.pattern_classes)
    print("Generated general conjectures:", report.generated_conjectures)
    print("Attempted conjectures:", report.attempted_conjectures)
    print("Accepted general theorems:", report.accepted_theorems)

    print("\nGeneral discoveries:")
    for discovery in report.discoveries:
        print(
            f"  - {discovery.theorem_name}: {discovery.statement} "
            f"[steps={discovery.proof_steps}, score={discovery.heuristic_score}]"
        )
        print(
            "    dependencies:",
            ", ".join(discovery.dependencies) or "(none)",
        )

    print("\nAttempt log:")
    for attempt in report.attempts:
        print(
            f"  - {attempt.status}: {attempt.statement} "
            f"[steps={attempt.proof_steps}]"
        )


if __name__ == "__main__":
    phase10_demo()
