"""Lean-backed research pipeline for Gareen.

Gareen remains responsible for research direction: conjecture generation,
ranking, campaign memory, and future lemma/concept invention.

Lean + Mathlib are responsible for formal acceptance.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Optional

from artificial_mathematician import generate_research_conjectures
from lean_bridge import LeanBridge, LeanVerificationResult
from math_world import Formula, KnowledgeState


@dataclass(frozen=True)
class LeanVerifiedDiscovery:
    name: str
    formula: Formula
    lean_statement: str
    tactic: str
    heuristic_score: int
    evidence: str


@dataclass(frozen=True)
class LeanResearchAttempt:
    name: str
    lean_statement: str
    verified: bool
    tactic: Optional[str]
    error: str


@dataclass(frozen=True)
class LeanResearchReport:
    generated_conjectures: int
    attempted_conjectures: int
    verified_discoveries: int
    attempts: tuple[LeanResearchAttempt, ...]
    discoveries: tuple[LeanVerifiedDiscovery, ...]


class LeanBackedResearcher:
    """Use Gareen for conjectures and Lean for formal acceptance."""

    def __init__(
        self,
        bridge: Optional[LeanBridge] = None,
        *,
        max_attempts: int = 5,
    ) -> None:
        self.bridge = bridge or LeanBridge()
        self.max_attempts = max_attempts

    def research(
        self,
        state: Optional[KnowledgeState] = None,
    ) -> LeanResearchReport:
        research_state = state or KnowledgeState()
        conjectures = generate_research_conjectures(research_state)

        attempts: list[LeanResearchAttempt] = []
        discoveries: list[LeanVerifiedDiscovery] = []

        for index, conjecture in enumerate(
            conjectures[: self.max_attempts],
            start=1,
        ):
            name = f"lean_auto_{index:03d}"
            result: LeanVerificationResult = self.bridge.verify_formula(
                conjecture.statement,
                theorem_name=name,
            )
            attempts.append(
                LeanResearchAttempt(
                    name=name,
                    lean_statement=result.statement,
                    verified=result.verified,
                    tactic=result.tactic,
                    error=result.error,
                )
            )
            if result.verified and result.tactic is not None:
                discoveries.append(
                    LeanVerifiedDiscovery(
                        name=name,
                        formula=conjecture.statement,
                        lean_statement=result.statement,
                        tactic=result.tactic,
                        heuristic_score=conjecture.heuristic_score,
                        evidence=conjecture.evidence,
                    )
                )

        return LeanResearchReport(
            generated_conjectures=len(conjectures),
            attempted_conjectures=len(attempts),
            verified_discoveries=len(discoveries),
            attempts=tuple(attempts),
            discoveries=tuple(discoveries),
        )


def report_to_json(report: LeanResearchReport) -> dict:
    return {
        "generated_conjectures": report.generated_conjectures,
        "attempted_conjectures": report.attempted_conjectures,
        "verified_discoveries": report.verified_discoveries,
        "attempts": [
            {
                "name": attempt.name,
                "statement": attempt.lean_statement,
                "verified": attempt.verified,
                "tactic": attempt.tactic,
                "error": attempt.error,
            }
            for attempt in report.attempts
        ],
        "discoveries": [
            {
                "name": discovery.name,
                "statement": discovery.lean_statement,
                "tactic": discovery.tactic,
                "heuristic_score": discovery.heuristic_score,
                "evidence": discovery.evidence,
            }
            for discovery in report.discoveries
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    bridge = LeanBridge()
    if not bridge.available():
        print("Lean/Lake is unavailable. Install Lean before running this pipeline.")
        return 2

    researcher = LeanBackedResearcher(
        bridge,
        max_attempts=max(1, args.limit),
    )
    report = researcher.research(KnowledgeState())

    print("Gareen Lean-backed research")
    print("===========================")
    print("Generated conjectures:", report.generated_conjectures)
    print("Attempted conjectures:", report.attempted_conjectures)
    print("Lean-verified discoveries:", report.verified_discoveries)

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

    return 0 if report.verified_discoveries else 1


if __name__ == "__main__":
    raise SystemExit(main())
