"""Proof-provider abstraction for Gareen's Lean backend.

Phase 12 ships only deterministic local tactics. External open-source provers
can implement the same interface later without changing Gareen's research loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from math_world import Formula


class ProofCandidateProvider(Protocol):
    name: str

    def candidates(self, formula: Formula) -> tuple[str, ...]:
        """Return Lean tactic/proof candidates. Lean remains the verifier."""


@dataclass(frozen=True)
class LocalTacticPortfolio:
    name: str = "local-tactics"

    def candidates(self, formula: Formula) -> tuple[str, ...]:
        return (
            "by\n  simp",
            "by\n  omega",
            "by\n  ring",
            "by\n  norm_num",
            "by\n  aesop",
        )


@dataclass(frozen=True)
class FutureExternalProver:
    """Configuration placeholder for an external open-source prover.

    This object deliberately does not execute network or model calls.
    It defines the boundary that BFS-Prover, Discover-and-Prove, or another
    Lean prover can implement in a later phase.
    """

    name: str
    endpoint_kind: str
    model_id: str | None = None

    def candidates(self, formula: Formula) -> tuple[str, ...]:
        raise NotImplementedError(
            f"{self.name} adapter is configured but not connected yet"
        )
