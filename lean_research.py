"""Lean-backed research gateway for Gareen.

This is the new trust path:
Gareen conjecture -> proof candidate -> Lean 4 + Mathlib -> accepted/rejected.

The Python proof checker remains available as a research sandbox, but accepted
records in this module are explicitly Lean-verified.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from artificial_mathematician import generate_research_conjectures
from lean_bridge import LeanVerificationResult, LeanVerifier
from math_world import Formula, KnowledgeState
from prover_adapters import LocalTacticPortfolio, ProofCandidateProvider


@dataclass(frozen=True)
class LeanResearchAttempt:
    theorem_name: str
    statement: Formula
    accepted: bool
    tactic: str | None
    attempts: int
    provider: str


@dataclass(frozen=True)
class LeanResearchReport:
    generated_conjectures: int
    attempted_conjectures: int
    lean_verified: int
    attempts: tuple[LeanResearchAttempt, ...]


class LeanResearchGateway:
    def __init__(
        self,
        *,
        verifier: Optional[LeanVerifier] = None,
        provider: Optional[ProofCandidateProvider] = None,
        max_attempts: int = 5,
    ) -> None:
        self.provider = provider or LocalTacticPortfolio()
        self.verifier = verifier or LeanVerifier()
        self.max_attempts = max_attempts

    def verify_formula(
        self,
        theorem_name: str,
        statement: Formula,
    ) -> LeanVerificationResult:
        tactics = self.provider.candidates(statement)
        verifier = LeanVerifier(
            project_dir=self.verifier.project_dir,
            tactics=tactics,
            timeout_seconds=self.verifier.timeout_seconds,
        )
        return verifier.verify(theorem_name, statement)

    def research(self, state: Optional[KnowledgeState] = None) -> LeanResearchReport:
        research_state = state or KnowledgeState()
        conjectures = generate_research_conjectures(research_state)
        attempts: list[LeanResearchAttempt] = []

        for index, conjecture in enumerate(conjectures[: self.max_attempts], start=1):
            name = f"LEAN_AUTO_{index}"
            result = self.verify_formula(name, conjecture.statement)
            attempts.append(
                LeanResearchAttempt(
                    theorem_name=name,
                    statement=conjecture.statement,
                    accepted=result.accepted,
                    tactic=result.tactic,
                    attempts=result.attempts,
                    provider=self.provider.name,
                )
            )

        return LeanResearchReport(
            generated_conjectures=len(conjectures),
            attempted_conjectures=len(attempts),
            lean_verified=sum(1 for item in attempts if item.accepted),
            attempts=tuple(attempts),
        )


def phase12_demo() -> None:
    gateway = LeanResearchGateway(max_attempts=3)
    report = gateway.research(KnowledgeState())

    print("Gareen Phase 12 — Lean-backed research")
    print("=======================================")
    print("Generated conjectures:", report.generated_conjectures)
    print("Attempted in Lean:", report.attempted_conjectures)
    print("Lean-verified:", report.lean_verified)
    for attempt in report.attempts:
        print(
            f"  - {attempt.theorem_name}: accepted={attempt.accepted} "
            f"provider={attempt.provider} tactic={attempt.tactic}"
        )
        print("    ", attempt.statement)


if __name__ == "__main__":
    phase12_demo()
