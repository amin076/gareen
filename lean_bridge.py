"""Lean verification bridge for Gareen.

The Python research layer may generate conjectures, strategies, and candidate
statements. Lean + Mathlib are the trusted formal authority for durable
mathematical claims.

Single-candidate verification is retained for interactive use. Research
campaigns should prefer batch verification so many candidates share the same
Lean process instead of paying process startup cost for every tactic attempt.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Iterable, Optional, Sequence

from math_world import (
    Add,
    Bottom,
    Eq,
    Expr,
    ForAll,
    Formula,
    Implies,
    Mul,
    Not,
    Succ,
    Var,
    Zero,
    X,
    Y,
    ZERO,
)


_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_']*$")
_LEAN_ERROR_RE = re.compile(r":(?P<line>\d+):(?P<column>\d+):\s+error:")
_TACTIC_SCRIPTS = {
    "simp": "simp",
    "omega": "omega",
    "ring": "ring",
    "norm_num": "norm_num",
    "nlinarith": "nlinarith",
    "aesop": "aesop",
    "simp_ring": "simp [Nat.succ_eq_add_one] <;> ring",
    "simp_nlinarith": "simp [Nat.succ_eq_add_one] <;> nlinarith",
}
_ALLOWED_TACTICS = tuple(_TACTIC_SCRIPTS)
_BATCH_TACTICS = (
    "simp",
    "omega",
    "simp_ring",
    "ring",
    "norm_num",
    "simp_nlinarith",
    "nlinarith",
)


@dataclass(frozen=True)
class LeanAttempt:
    tactic: str
    returncode: int
    stdout: str
    stderr: str
    source_path: str


@dataclass(frozen=True)
class LeanVerificationResult:
    theorem_name: str
    statement: str
    verified: bool
    tactic: Optional[str]
    attempts: tuple[LeanAttempt, ...]
    error: str = ""


@dataclass(frozen=True)
class LeanBatchCandidate:
    theorem_name: str
    formula: Formula


@dataclass(frozen=True)
class LeanBatchItemResult:
    theorem_name: str
    statement: str
    verified: bool
    tactic: Optional[str]
    attempted: bool = True
    error: str = ""


@dataclass(frozen=True)
class LeanBatchVerificationResult:
    results: tuple[LeanBatchItemResult, ...]
    process_invocations: int
    elapsed_seconds: float

    @property
    def verified_count(self) -> int:
        return sum(1 for item in self.results if item.verified)

    @property
    def unproved_count(self) -> int:
        return sum(
            1
            for item in self.results
            if item.attempted and not item.verified
        )

    @property
    def attempted_count(self) -> int:
        return sum(1 for item in self.results if item.attempted)


def _identifier(name: str) -> str:
    if not _SAFE_IDENTIFIER.fullmatch(name):
        raise ValueError(f"Unsafe Lean identifier: {name!r}")
    return name


def render_expr(expr: Expr) -> str:
    if isinstance(expr, Zero):
        return "0"
    if isinstance(expr, Var):
        return _identifier(expr.name)
    if isinstance(expr, Succ):
        return f"Nat.succ ({render_expr(expr.value)})"
    if isinstance(expr, Add):
        return f"({render_expr(expr.left)} + {render_expr(expr.right)})"
    if isinstance(expr, Mul):
        return f"({render_expr(expr.left)} * {render_expr(expr.right)})"
    raise TypeError(f"Unsupported Gareen expression: {type(expr)!r}")


def render_formula(formula: Formula) -> str:
    if isinstance(formula, Eq):
        return f"{render_expr(formula.left)} = {render_expr(formula.right)}"
    if isinstance(formula, Not):
        return f"¬ ({render_formula(formula.formula)})"
    if isinstance(formula, Implies):
        return (
            f"({render_formula(formula.premise)}) → "
            f"({render_formula(formula.conclusion)})"
        )
    if isinstance(formula, ForAll):
        variable = _identifier(formula.variable.name)
        return f"∀ ({variable} : Nat), {render_formula(formula.body)}"
    if isinstance(formula, Bottom):
        return "False"
    raise TypeError(f"Unsupported Gareen formula: {type(formula)!r}")


def render_theorem_source(
    formula: Formula,
    *,
    theorem_name: str,
    tactic: str,
) -> str:
    theorem_name = _identifier(theorem_name)
    if tactic not in _ALLOWED_TACTICS:
        raise ValueError(f"Unsupported tactic {tactic!r}")

    return f"""import Mathlib

namespace Gareen.Generated

theorem {theorem_name} : {render_formula(formula)} := by
  {_TACTIC_SCRIPTS[tactic]}

end Gareen.Generated
"""


def render_batch_source(
    candidates: Sequence[LeanBatchCandidate],
    *,
    tactic: str,
) -> tuple[str, dict[str, tuple[int, int]]]:
    """Render many independent theorems into one Lean module.

    The returned line ranges let the verifier map Lean diagnostics back to the
    candidate that failed while allowing successful declarations in the same
    process to be retained.
    """

    if tactic not in _ALLOWED_TACTICS:
        raise ValueError(f"Unsupported tactic {tactic!r}")

    names = [_identifier(item.theorem_name) for item in candidates]
    if len(names) != len(set(names)):
        raise ValueError("Batch theorem names must be unique")

    lines = [
        "import Mathlib",
        "",
        "namespace Gareen.GeneratedBatch",
        "",
    ]
    ranges: dict[str, tuple[int, int]] = {}

    for item in candidates:
        name = _identifier(item.theorem_name)
        start_line = len(lines) + 1
        lines.append(f"theorem {name} : {render_formula(item.formula)} := by")
        lines.append(f"  {_TACTIC_SCRIPTS[tactic]}")
        end_line = len(lines)
        ranges[name] = (start_line, end_line)
        lines.append("")

    lines.append("end Gareen.GeneratedBatch")
    return "\n".join(lines) + "\n", ranges


def _failed_names_from_diagnostics(
    diagnostics: str,
    ranges: dict[str, tuple[int, int]],
) -> tuple[frozenset[str], bool]:
    """Map Lean error diagnostics to theorem names.

    Returns (failed_names, has_unmapped_error). Any unmapped compiler error
    makes the round conservative: no candidate is marked successful from that
    process.
    """

    failed: set[str] = set()
    unmapped = False

    for line in diagnostics.splitlines():
        if "error:" not in line:
            continue
        match = _LEAN_ERROR_RE.search(line)
        if match is None:
            unmapped = True
            continue

        line_number = int(match.group("line"))
        owners = [
            name
            for name, (start, end) in ranges.items()
            if start <= line_number <= end
        ]
        if len(owners) == 1:
            failed.add(owners[0])
        else:
            unmapped = True

    return frozenset(failed), unmapped


class LeanBridge:
    """Translate Gareen formulas and ask Lean's kernel to verify them."""

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        *,
        generated_dir: str = ".gareen/lean_candidates",
        timeout_seconds: int = 120,
    ) -> None:
        self.repo_root = (
            Path(repo_root).resolve()
            if repo_root is not None
            else Path(__file__).resolve().parent
        )
        self.generated_dir = self.repo_root / generated_dir
        self.timeout_seconds = timeout_seconds

    def available(self) -> bool:
        return shutil.which("lake") is not None

    def emit(
        self,
        formula: Formula,
        *,
        theorem_name: str,
        tactic: str,
    ) -> Path:
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        theorem_name = _identifier(theorem_name)
        filename = f"{theorem_name}_{tactic}.lean"
        path = self.generated_dir / filename
        path.write_text(
            render_theorem_source(
                formula,
                theorem_name=theorem_name,
                tactic=tactic,
            ),
            encoding="utf-8",
        )
        return path

    def verify_formula(
        self,
        formula: Formula,
        *,
        theorem_name: str = "gareen_candidate",
        tactics: Iterable[str] = _ALLOWED_TACTICS,
    ) -> LeanVerificationResult:
        statement = render_formula(formula)
        theorem_name = _identifier(theorem_name)

        if not self.available():
            return LeanVerificationResult(
                theorem_name=theorem_name,
                statement=statement,
                verified=False,
                tactic=None,
                attempts=(),
                error="Lean/Lake is not installed or not on PATH.",
            )

        attempts: list[LeanAttempt] = []
        for tactic in tactics:
            if tactic not in _ALLOWED_TACTICS:
                raise ValueError(f"Unsupported tactic {tactic!r}")

            source_path = self.emit(
                formula,
                theorem_name=theorem_name,
                tactic=tactic,
            )
            try:
                relative = source_path.relative_to(self.repo_root)
                command_path = str(relative)
            except ValueError:
                command_path = str(source_path)

            try:
                completed = subprocess.run(
                    ["lake", "env", "lean", command_path],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
                attempt = LeanAttempt(
                    tactic=tactic,
                    returncode=completed.returncode,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                    source_path=str(source_path),
                )
            except subprocess.TimeoutExpired as exc:
                attempt = LeanAttempt(
                    tactic=tactic,
                    returncode=124,
                    stdout=exc.stdout or "",
                    stderr=(exc.stderr or "") + "\nLean verification timed out.",
                    source_path=str(source_path),
                )

            attempts.append(attempt)
            if attempt.returncode == 0:
                return LeanVerificationResult(
                    theorem_name=theorem_name,
                    statement=statement,
                    verified=True,
                    tactic=tactic,
                    attempts=tuple(attempts),
                )

        return LeanVerificationResult(
            theorem_name=theorem_name,
            statement=statement,
            verified=False,
            tactic=None,
            attempts=tuple(attempts),
            error=(
                "No tactic in the bounded portfolio produced a Lean-checked "
                "proof. This means unproved within the current budget, not false."
            ),
        )

    def verify_batch(
        self,
        candidates: Sequence[LeanBatchCandidate],
        *,
        tactics: Iterable[str] = _BATCH_TACTICS,
        batch_size: int = 64,
        round_timeout_seconds: Optional[int] = None,
        wall_clock_budget_seconds: Optional[float] = None,
    ) -> LeanBatchVerificationResult:
        """Verify many independent candidates with amortized Lean startup cost."""

        started = time.monotonic()
        ordered = tuple(candidates)
        if not ordered:
            return LeanBatchVerificationResult(
                results=(),
                process_invocations=0,
                elapsed_seconds=0.0,
            )

        if batch_size < 1:
            raise ValueError("batch_size must be positive")

        names = [_identifier(item.theorem_name) for item in ordered]
        if len(names) != len(set(names)):
            raise ValueError("Batch theorem names must be unique")

        tactics_tuple = tuple(tactics)
        for tactic in tactics_tuple:
            if tactic not in _ALLOWED_TACTICS:
                raise ValueError(f"Unsupported tactic {tactic!r}")

        if not self.available():
            unavailable = tuple(
                LeanBatchItemResult(
                    theorem_name=item.theorem_name,
                    statement=render_formula(item.formula),
                    verified=False,
                    tactic=None,
                    attempted=False,
                    error="Lean/Lake is not installed or not on PATH.",
                )
                for item in ordered
            )
            return LeanBatchVerificationResult(
                results=unavailable,
                process_invocations=0,
                elapsed_seconds=time.monotonic() - started,
            )

        timeout = round_timeout_seconds or self.timeout_seconds
        deadline = (
            started + wall_clock_budget_seconds
            if wall_clock_budget_seconds is not None
            else None
        )
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        resolved: dict[str, LeanBatchItemResult] = {}
        attempted_names: set[str] = set()
        process_invocations = 0

        for chunk_index in range(0, len(ordered), batch_size):
            chunk = ordered[chunk_index : chunk_index + batch_size]
            pending = {item.theorem_name: item for item in chunk}

            for tactic in tactics_tuple:
                if not pending:
                    break
                if deadline is not None and time.monotonic() >= deadline:
                    break

                round_candidates = tuple(pending.values())
                source, ranges = render_batch_source(
                    round_candidates,
                    tactic=tactic,
                )
                source_path = self.generated_dir / (
                    f"batch_{chunk_index:06d}_{tactic}.lean"
                )
                source_path.write_text(source, encoding="utf-8")

                try:
                    try:
                        relative = source_path.relative_to(self.repo_root)
                        command_path = str(relative)
                    except ValueError:
                        command_path = str(source_path)

                    try:
                        effective_timeout = timeout
                        if deadline is not None:
                            remaining = deadline - time.monotonic()
                            if remaining <= 0:
                                break
                            effective_timeout = min(
                                timeout,
                                max(1.0, remaining),
                            )

                        completed = subprocess.run(
                            ["lake", "env", "lean", command_path],
                            cwd=self.repo_root,
                            capture_output=True,
                            text=True,
                            timeout=effective_timeout,
                            check=False,
                        )
                        returncode = completed.returncode
                        stdout = completed.stdout
                        stderr = completed.stderr
                    except subprocess.TimeoutExpired as exc:
                        returncode = 124
                        stdout = exc.stdout or ""
                        stderr = (
                            (exc.stderr or "")
                            + "\nLean batch verification timed out."
                        )
                finally:
                    source_path.unlink(missing_ok=True)

                process_invocations += 1
                attempted_names.update(pending)

                if returncode == 0:
                    successful_names = set(pending)
                    failed_names: frozenset[str] = frozenset()
                    unmapped_error = False
                elif returncode == 124:
                    successful_names = set()
                    failed_names = frozenset(pending)
                    unmapped_error = True
                else:
                    diagnostics = stdout + "\n" + stderr
                    failed_names, unmapped_error = _failed_names_from_diagnostics(
                        diagnostics,
                        ranges,
                    )
                    if unmapped_error or not failed_names:
                        successful_names = set()
                    else:
                        successful_names = set(pending) - set(failed_names)

                for name in successful_names:
                    item = pending[name]
                    resolved[name] = LeanBatchItemResult(
                        theorem_name=name,
                        statement=render_formula(item.formula),
                        verified=True,
                        tactic=tactic,
                    )

                if successful_names:
                    pending = {
                        name: item
                        for name, item in pending.items()
                        if name not in successful_names
                    }

            for name, item in pending.items():
                resolved[name] = LeanBatchItemResult(
                    theorem_name=name,
                    statement=render_formula(item.formula),
                    verified=False,
                    tactic=None,
                    attempted=name in attempted_names,
                    error=(
                        (
                            "Unproved within the configured Lean tactic "
                            "portfolio and wall-clock budget; this is not "
                            "evidence that the statement is false."
                        )
                        if name in attempted_names
                        else (
                            "Not attempted because the shared wall-clock "
                            "budget was exhausted before this candidate."
                        )
                    ),
                )

        return LeanBatchVerificationResult(
            results=tuple(resolved[item.theorem_name] for item in ordered),
            process_invocations=process_invocations,
            elapsed_seconds=time.monotonic() - started,
        )


def _ci_demo() -> int:
    bridge = LeanBridge()

    candidates = (
        (
            "gareen_zero_add",
            ForAll(X, Eq(Add(ZERO, X), X)),
        ),
        (
            "gareen_add_comm",
            ForAll(X, ForAll(Y, Eq(Add(X, Y), Add(Y, X)))),
        ),
        (
            "gareen_mul_distrib",
            ForAll(
                X,
                ForAll(
                    Y,
                    Eq(
                        Mul(X, Add(Y, ZERO)),
                        Add(Mul(X, Y), Mul(X, ZERO)),
                    ),
                ),
            ),
        ),
    )

    failures = 0
    for name, formula in candidates:
        result = bridge.verify_formula(formula, theorem_name=name)
        print(
            f"{name}: verified={result.verified} "
            f"tactic={result.tactic or '-'}"
        )
        if not result.verified:
            failures += 1
            print(result.error)
            for attempt in result.attempts:
                print(attempt.stderr)

    batch = bridge.verify_batch(
        tuple(
            LeanBatchCandidate(theorem_name=name + "_batch", formula=formula)
            for name, formula in candidates
        ),
        batch_size=16,
    )
    print(
        "batch:",
        f"verified={batch.verified_count}/{len(batch.results)}",
        f"process_invocations={batch.process_invocations}",
        f"elapsed={batch.elapsed_seconds:.3f}s",
    )
    if batch.verified_count != len(batch.results):
        failures += 1

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ci-demo",
        action="store_true",
        help="Run end-to-end Lean verification on representative Gareen formulas.",
    )
    args = parser.parse_args()

    if args.ci_demo:
        return _ci_demo()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
