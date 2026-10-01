"""Lean-backed research pipeline for Gareen.

Gareen remains responsible for research direction: conjecture generation,
ranking, campaign memory, and future lemma/concept invention.

Lean + Mathlib are responsible for formal acceptance. Failure to find a proof
within a bounded tactic portfolio is recorded as *unproved*, never as false.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Optional, Sequence

from artificial_mathematician import ResearchConjecture, generate_research_conjectures
from lean_bridge import (
    LeanBatchCandidate,
    LeanBatchVerificationResult,
    LeanBridge,
    LeanVerificationResult,
)
from math_world import Formula, KnowledgeState, build_initial_knowledge, normalize
from research_value import (
    ResearchValueAssessment,
    assess_research_value,
    rank_research_conjectures,
)


@dataclass(frozen=True)
class LeanVerifiedDiscovery:
    name: str
    formula: Formula
    lean_statement: str
    tactic: str
    proof_class: str
    heuristic_score: int
    research_value_score: int
    reuse_potential: int
    known_derivation_distance: Optional[int]
    evidence: str


@dataclass(frozen=True)
class LeanResearchAttempt:
    name: str
    lean_statement: str
    status: str
    verified: bool
    tactic: Optional[str]
    error: str
    heuristic_score: int
    variable_count: int
    direct_rewrite_equivalent: bool
    research_value_score: int
    research_value_reason: str
    known_derivation_distance: Optional[int]
    reuse_potential: int


@dataclass(frozen=True)
class LeanResearchReport:
    generated_conjectures: int
    filtered_low_value: int
    selected_conjectures: int
    attempted_conjectures: int
    verified_candidates: int
    routine_verified: int
    verified_discoveries: int
    unproved_conjectures: int
    process_invocations: int
    verification_elapsed_seconds: float
    attempts: tuple[LeanResearchAttempt, ...]
    discoveries: tuple[LeanVerifiedDiscovery, ...]


def _direct_rewrite_equivalent(item: ResearchConjecture) -> bool:
    """Detect conjectures already explained by Gareen's primitive rewrites."""

    try:
        left, _ = normalize(item.body.left, max_steps=500)
        right, _ = normalize(item.body.right, max_steps=500)
    except RuntimeError:
        return False
    return left == right


def _proof_class(
    tactic: Optional[str],
    conjecture: Optional[ResearchConjecture] = None,
) -> str:
    if tactic in {"simp", "norm_num"}:
        return "routine-simplification"
    if tactic is None:
        return "unproved"

    # The legacy Gareen grammar contains only elementary Nat identities over
    # 0, successor, addition and multiplication. A one-variable identity in
    # that tiny language should not become a "research discovery" merely
    # because omega/ring needed more automation than simp.
    if (
        conjecture is not None
        and len(conjecture.variables) <= 1
        and tactic in {"omega", "ring", "nlinarith"}
    ):
        return "routine-elementary-arithmetic"

    return "solver-verified"


def _conjecture_priority(item: ResearchConjecture) -> tuple[int, int, int, int, str]:
    """Prefer nontrivial, multi-variable, structurally richer conjectures."""

    return (
        1 if _direct_rewrite_equivalent(item) else 0,
        -len(item.variables),
        -item.heuristic_score,
        -len(str(item.statement)),
        str(item.statement),
    )


def select_research_conjectures(
    conjectures: Sequence[ResearchConjecture],
    *,
    limit: int,
    state: Optional[KnowledgeState] = None,
    min_reasoning_steps: int = 3,
    min_research_value: int = 14,
) -> tuple[ResearchConjecture, ...]:
    """Select only research-worthy conjectures, then preserve arity diversity.

    Numerical examples and short consequences of existing knowledge can still
    be used upstream as evidence, but they no longer consume Lean proof budget.
    """

    if limit < 1:
        return ()

    research_state = state or KnowledgeState()
    ranked = rank_research_conjectures(
        conjectures,
        research_state,
        min_reasoning_steps=min_reasoning_steps,
        min_score=min_research_value,
    )

    buckets: dict[int, list[ResearchConjecture]] = {}
    for item in ranked:
        if not item.assessment.accepted:
            continue
        buckets.setdefault(len(item.conjecture.variables), []).append(
            item.conjecture
        )

    arities = sorted(buckets, reverse=True)
    selected: list[ResearchConjecture] = []

    while len(selected) < limit:
        progressed = False
        for arity in arities:
            bucket = buckets[arity]
            if not bucket:
                continue
            selected.append(bucket.pop(0))
            progressed = True
            if len(selected) >= limit:
                break
        if not progressed:
            break

    return tuple(selected)


class LeanBackedResearcher:
    """Use Gareen for conjectures and Lean for formal acceptance."""

    def __init__(
        self,
        bridge: Optional[LeanBridge] = None,
        *,
        max_attempts: int = 50,
        batch_size: int = 64,
        min_reasoning_steps: int = 3,
        min_research_value: int = 14,
    ) -> None:
        self.bridge = bridge or LeanBridge()
        self.max_attempts = max_attempts
        self.batch_size = batch_size
        self.min_reasoning_steps = min_reasoning_steps
        self.min_research_value = min_research_value

    def _verify_selected(
        self,
        selected: Sequence[ResearchConjecture],
    ) -> tuple[
        dict[str, tuple[bool, Optional[str], str]],
        int,
        float,
    ]:
        named = tuple(
            (
                f"lean_auto_{index:04d}",
                conjecture,
            )
            for index, conjecture in enumerate(selected, start=1)
        )

        verify_batch = getattr(self.bridge, "verify_batch", None)
        if callable(verify_batch):
            candidates = tuple(
                LeanBatchCandidate(
                    theorem_name=name,
                    formula=conjecture.statement,
                )
                for name, conjecture in named
            )

            # Cheap theorem-value gate: if simp/norm_num closes a statement
            # immediately, record it as verified-routine and do not spend the
            # stronger prover portfolio on it.
            try:
                routine_batch: LeanBatchVerificationResult = verify_batch(
                    candidates,
                    tactics=("simp", "norm_num"),
                    batch_size=self.batch_size,
                )
                routine_outcomes = {
                    item.theorem_name: item
                    for item in routine_batch.results
                    if item.verified
                }
                remaining = tuple(
                    item
                    for item in candidates
                    if item.theorem_name not in routine_outcomes
                )

                strong_batch = (
                    verify_batch(
                        remaining,
                        tactics=("omega", "ring", "nlinarith", "aesop"),
                        batch_size=self.batch_size,
                    )
                    if remaining
                    else LeanBatchVerificationResult(
                        results=(),
                        process_invocations=0,
                        elapsed_seconds=0.0,
                    )
                )
                strong_outcomes = {
                    item.theorem_name: item
                    for item in strong_batch.results
                }

                outcomes: dict[str, tuple[bool, Optional[str], str]] = {}
                for name, _ in named:
                    item = routine_outcomes.get(name) or strong_outcomes[name]
                    outcomes[name] = (
                        item.verified,
                        item.tactic,
                        item.error,
                    )

                return (
                    outcomes,
                    routine_batch.process_invocations
                    + strong_batch.process_invocations,
                    routine_batch.elapsed_seconds
                    + strong_batch.elapsed_seconds,
                )
            except TypeError:
                # Compatibility with small test doubles/custom bridges whose
                # batch API predates tactic selection.
                batch: LeanBatchVerificationResult = verify_batch(
                    candidates,
                    batch_size=self.batch_size,
                )
                return (
                    {
                        item.theorem_name: (
                            item.verified,
                            item.tactic,
                            item.error,
                        )
                        for item in batch.results
                    },
                    batch.process_invocations,
                    batch.elapsed_seconds,
                )

        # Compatibility fallback for small test doubles and custom bridges.
        outcomes: dict[str, tuple[bool, Optional[str], str]] = {}
        for name, conjecture in named:
            result: LeanVerificationResult = self.bridge.verify_formula(
                conjecture.statement,
                theorem_name=name,
            )
            outcomes[name] = (
                result.verified,
                result.tactic,
                result.error,
            )
        return outcomes, len(named), 0.0

    def research(
        self,
        state: Optional[KnowledgeState] = None,
    ) -> LeanResearchReport:
        research_state = state or build_initial_knowledge()
        conjectures = generate_research_conjectures(research_state)
        ranked = rank_research_conjectures(
            conjectures,
            research_state,
            min_reasoning_steps=self.min_reasoning_steps,
            min_score=self.min_research_value,
        )
        filtered_low_value = sum(
            1 for item in ranked if not item.assessment.accepted
        )
        assessment_by_statement: dict[str, ResearchValueAssessment] = {
            str(item.conjecture.statement): item.assessment
            for item in ranked
        }

        selected = select_research_conjectures(
            conjectures,
            limit=min(self.max_attempts, len(conjectures)),
            state=research_state,
            min_reasoning_steps=self.min_reasoning_steps,
            min_research_value=self.min_research_value,
        )

        outcomes, process_invocations, elapsed = self._verify_selected(selected)
        attempts: list[LeanResearchAttempt] = []
        discoveries: list[LeanVerifiedDiscovery] = []

        for index, conjecture in enumerate(selected, start=1):
            name = f"lean_auto_{index:04d}"
            verified, tactic, error = outcomes[name]
            assessment = assessment_by_statement[str(conjecture.statement)]
            proof_class = _proof_class(tactic, conjecture)
            status = (
                "verified-routine"
                if verified and proof_class.startswith("routine-")
                else "verified"
                if verified
                else "unproved-in-budget"
            )

            attempts.append(
                LeanResearchAttempt(
                    name=name,
                    lean_statement=str(conjecture.statement),
                    status=status,
                    verified=verified,
                    tactic=tactic,
                    error=error,
                    heuristic_score=conjecture.heuristic_score,
                    variable_count=len(conjecture.variables),
                    direct_rewrite_equivalent=_direct_rewrite_equivalent(
                        conjecture
                    ),
                    research_value_score=assessment.score,
                    research_value_reason=assessment.reason,
                    known_derivation_distance=assessment.known_derivation_distance,
                    reuse_potential=assessment.reuse_potential,
                )
            )

            if (
                verified
                and tactic is not None
                and not proof_class.startswith("routine-")
            ):
                from lean_bridge import render_formula

                discoveries.append(
                    LeanVerifiedDiscovery(
                        name=name,
                        formula=conjecture.statement,
                        lean_statement=render_formula(conjecture.statement),
                        tactic=tactic,
                        proof_class=proof_class,
                        heuristic_score=conjecture.heuristic_score,
                        research_value_score=assessment.score,
                        reuse_potential=assessment.reuse_potential,
                        known_derivation_distance=assessment.known_derivation_distance,
                        evidence=conjecture.evidence,
                    )
                )

        verified_candidates = sum(1 for item in attempts if item.verified)
        routine_verified = sum(
            1 for item in attempts if item.status == "verified-routine"
        )

        return LeanResearchReport(
            generated_conjectures=len(conjectures),
            filtered_low_value=filtered_low_value,
            selected_conjectures=len(selected),
            attempted_conjectures=len(attempts),
            verified_candidates=verified_candidates,
            routine_verified=routine_verified,
            verified_discoveries=len(discoveries),
            unproved_conjectures=sum(
                1 for item in attempts if not item.verified
            ),
            process_invocations=process_invocations,
            verification_elapsed_seconds=elapsed,
            attempts=tuple(attempts),
            discoveries=tuple(discoveries),
        )


def report_to_json(report: LeanResearchReport) -> dict:
    return {
        "generated_conjectures": report.generated_conjectures,
        "filtered_low_value": report.filtered_low_value,
        "selected_conjectures": report.selected_conjectures,
        "attempted_conjectures": report.attempted_conjectures,
        "verified_candidates": report.verified_candidates,
        "routine_verified": report.routine_verified,
        "verified_discoveries": report.verified_discoveries,
        "unproved_conjectures": report.unproved_conjectures,
        "process_invocations": report.process_invocations,
        "verification_elapsed_seconds": report.verification_elapsed_seconds,
        "attempts": [
            {
                "name": attempt.name,
                "statement": attempt.lean_statement,
                "status": attempt.status,
                "verified": attempt.verified,
                "tactic": attempt.tactic,
                "error": attempt.error,
                "heuristic_score": attempt.heuristic_score,
                "variable_count": attempt.variable_count,
                "direct_rewrite_equivalent": attempt.direct_rewrite_equivalent,
                "research_value_score": attempt.research_value_score,
                "research_value_reason": attempt.research_value_reason,
                "known_derivation_distance": attempt.known_derivation_distance,
                "reuse_potential": attempt.reuse_potential,
            }
            for attempt in report.attempts
        ],
        "discoveries": [
            {
                "name": discovery.name,
                "statement": discovery.lean_statement,
                "tactic": discovery.tactic,
                "proof_class": discovery.proof_class,
                "heuristic_score": discovery.heuristic_score,
                "research_value_score": discovery.research_value_score,
                "reuse_potential": discovery.reuse_potential,
                "known_derivation_distance": discovery.known_derivation_distance,
                "evidence": discovery.evidence,
            }
            for discovery in report.discoveries
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--min-reasoning-steps", type=int, default=3)
    parser.add_argument("--min-research-value", type=int, default=14)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    bridge = LeanBridge()
    if not bridge.available():
        print("Lean/Lake is unavailable. Install Lean before running this pipeline.")
        return 2

    researcher = LeanBackedResearcher(
        bridge,
        max_attempts=max(1, args.limit),
        batch_size=max(1, args.batch_size),
        min_reasoning_steps=max(1, args.min_reasoning_steps),
        min_research_value=max(0, args.min_research_value),
    )
    report = researcher.research(build_initial_knowledge())

    print("Gareen Lean-backed research")
    print("===========================")
    print("Generated conjectures:", report.generated_conjectures)
    print("Filtered as low research value:", report.filtered_low_value)
    print("Selected conjectures:", report.selected_conjectures)
    print("Attempted conjectures:", report.attempted_conjectures)
    print("Lean-verified candidates:", report.verified_candidates)
    print("Routine verified:", report.routine_verified)
    print("Promoted discoveries:", report.verified_discoveries)
    print("Unproved in current budget:", report.unproved_conjectures)
    print("Lean process invocations:", report.process_invocations)
    print(
        "Verification elapsed seconds:",
        round(report.verification_elapsed_seconds, 3),
    )

    for discovery in report.discoveries:
        print(
            f"  - {discovery.name}: {discovery.lean_statement} "
            f"[tactic={discovery.tactic}]"
        )

    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report_to_json(report), indent=2),
            encoding="utf-8",
        )

    return 0 if report.attempted_conjectures else 1


if __name__ == "__main__":
    raise SystemExit(main())
