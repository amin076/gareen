"""Gareen Phase 9: bounded autonomous theorem discovery.

This module generates its own candidate statements inside a deliberately small
formal world. Candidate generation and ranking are heuristic and untrusted.
Every accepted theorem must still pass the existing proof search and the
trusted deterministic proof checker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from math_world import (
    ONE,
    THREE,
    TWO,
    ZERO,
    Add,
    Eq,
    Expr,
    Formula,
    KnowledgeState,
    Mul,
    Proof,
    Succ,
    Theorem,
    build_initial_knowledge,
    normalize,
)
from proof_search import BoundedProofSearcher


@dataclass(frozen=True)
class CandidateStatement:
    statement: Formula
    source_term: Expr
    normal_form: Expr
    heuristic_score: int


@dataclass(frozen=True)
class DiscoveryAttempt:
    statement: Formula
    status: str
    proof_steps: int
    heuristic_score: int
    reason: str = ""


@dataclass(frozen=True)
class DiscoveryRecord:
    theorem_name: str
    statement: Formula
    proof_steps: int
    heuristic_score: int
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class DiscoveryReport:
    generated_candidates: int
    attempted_candidates: int
    verified_candidates: int
    accepted_theorems: int
    attempts: tuple[DiscoveryAttempt, ...]
    discoveries: tuple[DiscoveryRecord, ...]


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


def _contains_mul(expr: Expr) -> bool:
    if isinstance(expr, Mul):
        return True
    if isinstance(expr, Succ):
        return _contains_mul(expr.value)
    if isinstance(expr, Add):
        return _contains_mul(expr.left) or _contains_mul(expr.right)
    return False


def _candidate_score(source: Expr, normal: Expr) -> int:
    """Prefer nontrivial expressions without making truth decisions.

    The score is only a search-order heuristic. It is not mathematical
    significance and cannot make a candidate trusted.
    """

    score = 2 * _operator_count(source)
    score += max(0, _expr_size(source) - _expr_size(normal))
    if _contains_mul(source):
        score += 2
    return score


def _canonical_statement_key(statement: Formula) -> str:
    return str(statement)


def generate_closed_terms(
    *,
    include_multiplication: bool = True,
) -> tuple[Expr, ...]:
    """Generate a small finite term universe without receiving a theorem goal."""

    atoms: tuple[Expr, ...] = (ZERO, ONE, TWO, THREE)
    terms: set[Expr] = set(atoms)

    for value in atoms:
        terms.add(Succ(value))

    for left in atoms:
        for right in atoms:
            terms.add(Add(left, right))
            if include_multiplication:
                terms.add(Mul(left, right))

    return tuple(
        sorted(
            terms,
            key=lambda term: (_expr_size(term), str(term)),
        )
    )


def generate_candidate_statements(
    terms: Iterable[Expr],
) -> tuple[CandidateStatement, ...]:
    """Turn self-generated terms into candidate equalities.

    Normalization is used only as an untrusted conjecture generator. The
    equality is not accepted because both terms normalize to the same result;
    the separate proof searcher and checker must still construct and validate
    a formal proof.
    """

    candidates: dict[str, CandidateStatement] = {}

    for term in terms:
        normal, trace = normalize(term)
        if not trace or normal == term:
            continue

        statement = Eq(term, normal)
        candidate = CandidateStatement(
            statement=statement,
            source_term=term,
            normal_form=normal,
            heuristic_score=_candidate_score(term, normal),
        )
        candidates.setdefault(_canonical_statement_key(statement), candidate)

    return tuple(
        sorted(
            candidates.values(),
            key=lambda item: (
                _expr_size(item.source_term),
                -item.heuristic_score,
                str(item.statement),
            ),
        )
    )


def _next_discovery_name(state: KnowledgeState) -> str:
    index = 1
    while f"D{index}_AUTO" in state.theorems:
        index += 1
    return f"D{index}_AUTO"


class AutonomousTheoremExplorer:
    """Generate, prove, verify, and store bounded candidate theorems."""

    def __init__(
        self,
        *,
        max_attempts: int = 32,
        max_discoveries: int = 5,
        min_proof_steps: int = 4,
        include_multiplication: bool = True,
        searcher: Optional[BoundedProofSearcher] = None,
    ) -> None:
        self.max_attempts = max_attempts
        self.max_discoveries = max_discoveries
        self.min_proof_steps = min_proof_steps
        self.include_multiplication = include_multiplication
        self.searcher = searcher or BoundedProofSearcher(
            max_depth=6,
            max_terms=64,
            instantiation_rounds=1,
        )

    def explore(self, state: KnowledgeState) -> DiscoveryReport:
        terms = generate_closed_terms(
            include_multiplication=self.include_multiplication,
        )
        candidates = generate_candidate_statements(terms)

        existing = {
            _canonical_statement_key(axiom.formula)
            for axiom in state.world.axioms
        }
        existing.update(
            _canonical_statement_key(theorem.statement)
            for theorem in state.theorems.values()
        )

        attempts: list[DiscoveryAttempt] = []
        discoveries: list[DiscoveryRecord] = []
        verified_count = 0

        for candidate in candidates:
            if len(attempts) >= self.max_attempts:
                break
            if len(discoveries) >= self.max_discoveries:
                break

            key = _canonical_statement_key(candidate.statement)
            if key in existing:
                attempts.append(
                    DiscoveryAttempt(
                        statement=candidate.statement,
                        status="skipped-existing",
                        proof_steps=0,
                        heuristic_score=candidate.heuristic_score,
                        reason="Statement already exists exactly in the knowledge state.",
                    )
                )
                continue

            result = self.searcher.prove(candidate.statement, state)
            if not result.found or result.proof is None:
                attempts.append(
                    DiscoveryAttempt(
                        statement=candidate.statement,
                        status="unproved",
                        proof_steps=0,
                        heuristic_score=candidate.heuristic_score,
                        reason="Bounded proof search found no verified proof.",
                    )
                )
                continue

            verified_count += 1
            proof_steps = len(result.proof.steps)

            if proof_steps < self.min_proof_steps:
                attempts.append(
                    DiscoveryAttempt(
                        statement=candidate.statement,
                        status="skipped-too-direct",
                        proof_steps=proof_steps,
                        heuristic_score=candidate.heuristic_score,
                        reason=(
                            "Verified, but treated as a direct/trivial instance "
                            "for this discovery phase."
                        ),
                    )
                )
                continue

            theorem_name = _next_discovery_name(state)
            theorem = state.add_theorem(
                theorem_name,
                result.proof,
            )
            existing.add(key)

            discoveries.append(
                DiscoveryRecord(
                    theorem_name=theorem.name,
                    statement=theorem.statement,
                    proof_steps=proof_steps,
                    heuristic_score=candidate.heuristic_score,
                    dependencies=theorem.dependencies,
                )
            )
            attempts.append(
                DiscoveryAttempt(
                    statement=candidate.statement,
                    status="accepted",
                    proof_steps=proof_steps,
                    heuristic_score=candidate.heuristic_score,
                )
            )

        return DiscoveryReport(
            generated_candidates=len(candidates),
            attempted_candidates=len(attempts),
            verified_candidates=verified_count,
            accepted_theorems=len(discoveries),
            attempts=tuple(attempts),
            discoveries=tuple(discoveries),
        )


def phase9_demo() -> None:
    state = build_initial_knowledge()
    explorer = AutonomousTheoremExplorer(
        max_attempts=24,
        max_discoveries=4,
        min_proof_steps=4,
    )

    report = explorer.explore(state)

    print("Gareen Phase 9")
    print("================")
    print("Generated candidates:", report.generated_candidates)
    print("Attempted candidates:", report.attempted_candidates)
    print("Verified candidates:", report.verified_candidates)
    print("Accepted discoveries:", report.accepted_theorems)

    print("\nAutonomously accepted theorems:")
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
    phase9_demo()
