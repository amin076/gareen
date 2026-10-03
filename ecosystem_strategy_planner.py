"""Phase 19 ecosystem-first proof strategy orchestrator.

Gareen no longer reimplements generic proof tactics that Lean/Mathlib already
provides. This planner treats established tactics as independent proof
strategies, runs them in a bounded cascade, kernel-verifies every success, and
falls back to Gareen's own recursive portfolio only when the ecosystem does not
close the goal.

The first implementation deliberately uses only tactics already available in
the pinned Lean 4.34.1 + Mathlib environment. External systems (LeanHammer,
lean-auto, neural provers) are represented in the architecture/documentation
but are not silently claimed as active unless their dependencies are installed
and version-compatible.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Optional

from portfolio_proof_planner import PortfolioProofPlanner
from recursive_proof_planner import validate_statement, audited


_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_']*$")


@dataclass(frozen=True)
class StrategyAttempt:
    strategy: str
    verified: bool
    returncode: int
    elapsed_seconds: float
    timed_out: bool
    source_path: str
    stdout: str
    stderr: str


@dataclass(frozen=True)
class EcosystemProofResult:
    theorem_name: str
    statement: str
    verified: bool
    winning_strategy: Optional[str]
    layer: Optional[str]
    attempts: tuple[StrategyAttempt, ...]
    gareen_fallback: Optional[dict]
    elapsed_seconds: float


class EcosystemStrategyPlanner:
    """Bounded portfolio over established Lean/Mathlib strategies + Gareen."""

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        *,
        generated_dir: str = ".gareen/ecosystem_candidates",
        per_strategy_timeout: float = 20.0,
        gareen_timeout: int = 60,
        gareen_nodes: int = 5000,
    ) -> None:
        self.repo_root = (
            Path(repo_root).resolve()
            if repo_root is not None
            else Path(__file__).resolve().parent
        )
        self.generated_dir = self.repo_root / generated_dir
        self.per_strategy_timeout = per_strategy_timeout
        self.gareen = PortfolioProofPlanner(
            self.repo_root,
            advanced_timeout=gareen_timeout,
            legacy_timeout=gareen_timeout,
            advanced_nodes=gareen_nodes,
            legacy_nodes=gareen_nodes,
        )

    def available(self) -> bool:
        return shutil.which("lake") is not None

    @staticmethod
    def _first_nat_binder(statement: str) -> Optional[str]:
        m = re.match(
            r"\s*∀\s+([A-Za-z_][A-Za-z0-9_']*)\s*:\s*Nat\s*,",
            statement,
        )
        return m.group(1) if m else None

    def _strategies(self, statement: str) -> list[tuple[str, tuple[str, ...]]]:
        # Ordered from broad, high-value ecosystem automation to more specific
        # classical/arithmetic/search transformations. Each strategy is isolated:
        # a failure cannot corrupt another attempt.
        strategies: list[tuple[str, tuple[str, ...]]] = [
            ("auto", ("auto",)),
            ("auto_all_hypotheses", ("auto [*]",)),
            ("grind", ("grind",)),
            ("aesop", ("aesop",)),
            ("exact_grind", ("exact? +grind",)),
            ("apply_grind", ("apply? +grind",)),
            ("simp_all", ("simp_all",)),
            ("omega", ("omega",)),
            ("norm_num", ("norm_num",)),
            ("ring", ("ring",)),
            ("linarith", ("linarith",)),
            ("nlinarith", ("nlinarith",)),
            ("contradiction_grind", ("by_contra h", "grind")),
            ("contradiction_aesop", ("by_contra h", "aesop")),
            ("split_grind", ("constructor <;> grind",)),
            ("split_aesop", ("constructor <;> aesop",)),
            ("exact_search", ("exact?",)),
            ("apply_search", ("apply?",)),
        ]
        binder = self._first_nat_binder(statement)
        if binder:
            strategies.extend([
                (
                    "induction_simp",
                    (f"intro {binder}", f"induction {binder} <;> simp_all"),
                ),
                (
                    "induction_grind",
                    (f"intro {binder}", f"induction {binder} <;> grind"),
                ),
                (
                    "induction_aesop",
                    (f"intro {binder}", f"induction {binder} <;> aesop"),
                ),
            ])
        return strategies

    def _render(
        self,
        theorem_name: str,
        statement: str,
        proof_lines: tuple[str, ...],
        *,
        include_auto: bool = False,
    ) -> str:
        if not _SAFE_IDENTIFIER.fullmatch(theorem_name):
            raise ValueError(f"Unsafe theorem identifier: {theorem_name!r}")
        lines = [
            "import Mathlib",
        ]
        if include_auto:
            lines.append("import Auto.Tactic")
        lines.extend([
            "",
            "namespace Gareen.EcosystemGenerated",
            "",
            f"theorem {theorem_name} : {statement} := by",
        ])
        lines.extend(f"  {line}" for line in proof_lines)
        lines.extend([
            "",
            f"#print axioms Gareen.EcosystemGenerated.{theorem_name}",
            "",
            "end Gareen.EcosystemGenerated",
            "",
        ])
        return "\n".join(lines)

    def _run_strategy(
        self,
        *,
        theorem_name: str,
        statement: str,
        strategy: str,
        proof_lines: tuple[str, ...],
        timeout: float,
    ) -> StrategyAttempt:
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        safe_strategy = re.sub(r"[^A-Za-z0-9_]+", "_", strategy)
        path = self.generated_dir / f"{theorem_name}_{safe_strategy}.lean"
        path.write_text(
            self._render(
                theorem_name,
                statement,
                proof_lines,
                include_auto=strategy.startswith("auto"),
            ),
            encoding="utf-8",
        )

        started = time.monotonic()
        try:
            proc = subprocess.run(
                ["lake", "env", "lean", str(path)],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=max(1.0, timeout),
                check=False,
            )
            rc, out, err, timed_out = (
                proc.returncode,
                proc.stdout,
                proc.stderr,
                False,
            )
        except subprocess.TimeoutExpired as exc:
            def _txt(value):
                if isinstance(value, bytes):
                    return value.decode(errors="replace")
                return value or ""
            rc = 124
            out = _txt(exc.stdout)
            err = _txt(exc.stderr) + "\nStrategy timed out."
            timed_out = True

        elapsed = round(time.monotonic() - started, 3)
        # Same trust rule as Gareen recursive search: compiler success plus
        # explicit axiom audit allowlist.
        verified = audited(out + "\n" + err, rc)
        return StrategyAttempt(
            strategy=strategy,
            verified=verified,
            returncode=rc,
            elapsed_seconds=elapsed,
            timed_out=timed_out,
            source_path=str(path),
            stdout=out,
            stderr=err,
        )

    def prove(
        self,
        statement: str,
        *,
        theorem_name: str = "gareen_ecosystem_goal",
        wall_clock_budget_seconds: float = 300.0,
        stop_on_first_success: bool = True,
        use_gareen_fallback: bool = True,
    ) -> EcosystemProofResult:
        statement = validate_statement(statement)
        if not _SAFE_IDENTIFIER.fullmatch(theorem_name):
            raise ValueError(f"Unsafe theorem identifier: {theorem_name!r}")
        if not self.available():
            return EcosystemProofResult(
                theorem_name, statement, False, None, None, (), None, 0.0
            )

        started = time.monotonic()
        attempts: list[StrategyAttempt] = []

        for index, (strategy, proof_lines) in enumerate(self._strategies(statement)):
            remaining = wall_clock_budget_seconds - (time.monotonic() - started)
            if remaining <= 0:
                break
            attempt = self._run_strategy(
                theorem_name=f"{theorem_name}_{index}",
                statement=statement,
                strategy=strategy,
                proof_lines=proof_lines,
                timeout=min(self.per_strategy_timeout, remaining),
            )
            attempts.append(attempt)
            if attempt.verified and stop_on_first_success:
                return EcosystemProofResult(
                    theorem_name,
                    statement,
                    True,
                    strategy,
                    "lean_mathlib_ecosystem",
                    tuple(attempts),
                    None,
                    round(time.monotonic() - started, 3),
                )

        remaining = wall_clock_budget_seconds - (time.monotonic() - started)
        gareen_result = None
        if use_gareen_fallback and remaining > 0:
            # Gareen's recursive portfolio is retained as an additional research
            # strategy, not the foundation for generic automation.
            r = self.gareen.prove(statement, theorem_name=theorem_name + "_gareen")
            gareen_result = asdict(r)
            if r.verified:
                return EcosystemProofResult(
                    theorem_name,
                    statement,
                    True,
                    f"gareen_{r.winning_engine}",
                    "gareen_recursive_portfolio",
                    tuple(attempts),
                    gareen_result,
                    round(time.monotonic() - started, 3),
                )

        return EcosystemProofResult(
            theorem_name,
            statement,
            False,
            None,
            None,
            tuple(attempts),
            gareen_result,
            round(time.monotonic() - started, 3),
        )
