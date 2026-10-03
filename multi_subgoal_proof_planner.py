"""Reusable heterogeneous multi-subgoal orchestration for Gareen Phase 19.

The planner handles top-level conjunctions after forall/implication prefixes.
It routes each branch independently, keeps Gareen's recursive engines as real
providers, then assembles helper proofs into one final Lean-verified theorem.

Current routing policy is intentionally small and auditable:
- prime/power goals -> context-aware Lean feedback retrieval first;
- divisibility/addition goals -> Gareen recursive portfolio first;
- otherwise -> ecosystem planner first.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import subprocess
import time
from typing import Optional

from ecosystem_strategy_planner import EcosystemStrategyPlanner
from lean_proof_planner import (
    LeanProofPlanner,
    _context_intro_names,
    _split_forall,
    _split_top_level,
    _strip_outer_parens,
)
from portfolio_proof_planner import PortfolioProofPlanner
from recursive_proof_planner import audited, validate_statement


@dataclass(frozen=True)
class RoutedBranch:
    name: str
    statement: str
    verified: bool
    provider: Optional[str]
    strategy: Optional[str]
    elapsed_seconds: float


@dataclass(frozen=True)
class MultiSubgoalResult:
    theorem_name: str
    statement: str
    verified: bool
    branches: tuple[RoutedBranch, ...]
    assembly_source_path: Optional[str]
    assembly_returncode: Optional[int]
    assembly_stdout: str
    assembly_stderr: str
    elapsed_seconds: float


def _split_prefix_and_conjunction(statement: str) -> tuple[str, str, str]:
    binders, body = _split_forall(statement)
    antecedents: list[str] = []
    rest = body
    while True:
        split = _split_top_level(rest, "→")
        if split is None:
            break
        left, rest = split
        antecedents.append(left)

    target = _strip_outer_parens(rest)
    pair = _split_top_level(target, "∧")
    if pair is None:
        raise ValueError("Expected a top-level conjunction after introductions")
    left, right = pair

    prefix_parts = []
    if binders:
        prefix_parts.append(f"∀ {binders},")
    if antecedents:
        prefix_parts.append(" → ".join(antecedents) + " →")
    prefix = " ".join(prefix_parts).strip()
    return prefix, left.strip(), right.strip()


def _branch_statement(prefix: str, target: str) -> str:
    return f"{prefix} {target}".strip()


def _helper_call(helper: str, statement: str) -> str:
    names = _context_intro_names(statement)
    return helper + (" " + " ".join(names) if names else "")


class MultiSubgoalProofPlanner:
    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self.repo_root = (
            Path(repo_root).resolve()
            if repo_root is not None
            else Path(__file__).resolve().parent
        )
        self.generated_dir = self.repo_root / ".gareen/multi_subgoal"
        self.feedback = LeanProofPlanner(
            self.repo_root,
            generated_dir=".gareen/multi_subgoal_feedback",
            timeout_seconds=35,
            max_feedback_rounds=3,
        )
        self.gareen = PortfolioProofPlanner(
            self.repo_root,
            advanced_timeout=45,
            legacy_timeout=45,
            advanced_nodes=5000,
            legacy_nodes=5000,
        )
        self.ecosystem = EcosystemStrategyPlanner(
            self.repo_root,
            per_strategy_timeout=12,
            gareen_timeout=35,
            gareen_nodes=3500,
        )

    @staticmethod
    def _route(statement: str) -> tuple[str, ...]:
        """Route from the branch target, not from shared hypotheses."""
        _, body = _split_forall(statement)
        rest = body
        while True:
            split = _split_top_level(rest, "→")
            if split is None:
                break
            _, rest = split
        target = _strip_outer_parens(rest)

        if "Nat.Prime" in target and "^" in target:
            return ("feedback", "ecosystem", "gareen")
        if "∣" in target and "+" in target:
            return ("gareen", "feedback", "ecosystem")
        return ("ecosystem", "feedback", "gareen")

    def _solve_branch(
        self,
        *,
        name: str,
        statement: str,
        budget_seconds: float,
    ) -> tuple[RoutedBranch, tuple[str, ...]]:
        started = time.monotonic()
        deadline = started + budget_seconds

        for provider in self._route(statement):
            remaining = deadline - time.monotonic()
            if remaining <= 1:
                break

            if provider == "feedback":
                result = self.feedback.prove(
                    statement,
                    theorem_name=name + "_feedback",
                    wall_clock_budget_seconds=remaining,
                    per_attempt_timeout_seconds=min(35, max(10, int(remaining))),
                )
                if result.verified:
                    winning = next(
                        a for a in result.attempts
                        if a.verified and a.strategy == result.winning_strategy
                    )
                    source = Path(winning.source_path).read_text(encoding="utf-8")
                    proof = self._extract_proof_lines(source)
                    return (
                        RoutedBranch(
                            name, statement, True, "lean_feedback_loop",
                            result.winning_strategy,
                            round(time.monotonic() - started, 3),
                        ),
                        proof,
                    )

            elif provider == "gareen":
                result = self.gareen.prove(statement, theorem_name=name + "_gareen")
                if result.verified:
                    data = result.advanced if result.winning_engine == "advanced" else result.legacy
                    assert data is not None
                    attempts = data.get("attempts", [])
                    winning_attempt = next(a for a in attempts if a.get("verified"))
                    source = Path(winning_attempt["source_path"]).read_text(encoding="utf-8")
                    proof = self._extract_proof_lines(source)
                    return (
                        RoutedBranch(
                            name, statement, True,
                            f"gareen_{result.winning_engine}",
                            data.get("winning_strategy"),
                            round(time.monotonic() - started, 3),
                        ),
                        proof,
                    )

            else:
                result = self.ecosystem.prove(
                    statement,
                    theorem_name=name + "_ecosystem",
                    wall_clock_budget_seconds=remaining,
                    stop_on_first_success=True,
                    use_gareen_fallback=False,
                )
                if result.verified and result.layer == "lean_mathlib_ecosystem":
                    winning = next(
                        a for a in result.attempts
                        if a.verified and a.strategy == result.winning_strategy
                    )
                    source = Path(winning.source_path).read_text(encoding="utf-8")
                    proof = self._extract_proof_lines(source)
                    return (
                        RoutedBranch(
                            name, statement, True, result.layer,
                            result.winning_strategy,
                            round(time.monotonic() - started, 3),
                        ),
                        proof,
                    )

        return (
            RoutedBranch(
                name, statement, False, None, None,
                round(time.monotonic() - started, 3),
            ),
            (),
        )

    @staticmethod
    def _extract_proof_lines(source: str) -> tuple[str, ...]:
        marker = ":= by\n"
        start = source.find(marker)
        if start < 0:
            raise ValueError("Could not locate proof body in generated Lean source")
        tail = source[start + len(marker):]
        lines: list[str] = []
        for line in tail.splitlines():
            if line.startswith("end ") or line.startswith("#print axioms"):
                break
            if not line.strip():
                if lines:
                    break
                continue
            if line.startswith("  "):
                line = line[2:]
            lines.append(line)
        if not lines:
            raise ValueError("Generated proof body was empty")
        return tuple(lines)

    def prove(
        self,
        statement: str,
        *,
        theorem_name: str = "gareen_multi_subgoal_goal",
        total_budget_seconds: float = 300.0,
    ) -> MultiSubgoalResult:
        started = time.monotonic()
        statement = validate_statement(statement)
        prefix, left_target, right_target = _split_prefix_and_conjunction(statement)
        left_statement = _branch_statement(prefix, left_target)
        right_statement = _branch_statement(prefix, right_target)

        # Reserve assembly time and divide search budget between branches.
        assembly_reserve = min(30.0, total_budget_seconds * 0.15)
        branch_pool = max(2.0, total_budget_seconds - assembly_reserve)
        each_budget = branch_pool / 2.0

        left, left_proof = self._solve_branch(
            name=theorem_name + "_left",
            statement=left_statement,
            budget_seconds=each_budget,
        )
        right, right_proof = self._solve_branch(
            name=theorem_name + "_right",
            statement=right_statement,
            budget_seconds=each_budget,
        )

        if not left.verified or not right.verified:
            return MultiSubgoalResult(
                theorem_name, statement, False, (left, right), None, None,
                "", "", round(time.monotonic() - started, 3),
            )

        self.generated_dir.mkdir(parents=True, exist_ok=True)
        path = self.generated_dir / f"{theorem_name}_assembled.lean"

        intro_names = _context_intro_names(statement)
        left_helper = theorem_name + "_left_helper"
        right_helper = theorem_name + "_right_helper"

        lines = [
            "import Mathlib",
            "import Auto.Tactic",
            "import Gareen.RecursivePlanner",
            "import Gareen.RecursivePlannerLegacy",
            "",
            "namespace Gareen.MultiSubgoalGenerated",
            "",
            f"theorem {left_helper} : {left_statement} := by",
        ]
        lines.extend("  " + line for line in left_proof)
        lines.extend([
            "",
            f"theorem {right_helper} : {right_statement} := by",
        ])
        lines.extend("  " + line for line in right_proof)
        lines.extend([
            "",
            f"theorem {theorem_name} : {statement} := by",
        ])
        if intro_names:
            lines.append("  intro " + " ".join(intro_names))
        lines.extend([
            "  constructor",
            f"  · exact {_helper_call(left_helper, left_statement)}",
            f"  · exact {_helper_call(right_helper, right_statement)}",
            "",
            f"#print axioms Gareen.MultiSubgoalGenerated.{theorem_name}",
            "",
            "end Gareen.MultiSubgoalGenerated",
            "",
        ])
        path.write_text("\n".join(lines), encoding="utf-8")

        remaining = max(1.0, total_budget_seconds - (time.monotonic() - started))
        try:
            proc = subprocess.run(
                ["lake", "env", "lean", str(path)],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=remaining,
                check=False,
            )
            rc, out, err = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            rc = 124
            out = exc.stdout or ""
            err = (exc.stderr or "") + "\nAssembly timed out."

        verified = audited(out + "\n" + err, rc)
        return MultiSubgoalResult(
            theorem_name, statement, verified, (left, right), str(path), rc,
            out, err, round(time.monotonic() - started, 3),
        )
