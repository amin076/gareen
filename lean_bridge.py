"""Lean verification bridge for Gareen.

The Python research layer may generate conjectures, strategies, and candidate
statements. Lean + Mathlib are the trusted formal authority for durable
mathematical claims.

This module deliberately does not translate Gareen's custom Python proofs.
Instead it translates formulas to Lean propositions and asks Lean to construct
and kernel-check a proof using a small tactic portfolio.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
from typing import Iterable, Optional

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
_ALLOWED_TACTICS = (
    "simp",
    "omega",
    "ring",
    "norm_num",
    "aesop",
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
  {tactic}

end Gareen.Generated
"""


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
            error="No tactic in the bounded portfolio produced a Lean-checked proof.",
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
