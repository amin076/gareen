"""Bridge between Gareen's Python research AST and Lean 4.

The bridge is intentionally one-way and conservative:
- Python may propose a statement.
- The bridge translates supported syntax to Lean.
- A proof provider supplies a tactic script.
- Lean is the authority that accepts or rejects the theorem.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Protocol

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
)


class LeanTranslationError(ValueError):
    pass


def _lean_identifier(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_']", "_", name)
    if not sanitized:
        raise LeanTranslationError("Lean identifier cannot be empty")
    if sanitized[0].isdigit():
        sanitized = f"v_{sanitized}"
    return sanitized


def expr_to_lean(expr: Expr) -> str:
    if isinstance(expr, Zero):
        return "0"
    if isinstance(expr, Var):
        return _lean_identifier(expr.name)
    if isinstance(expr, Succ):
        return f"Nat.succ ({expr_to_lean(expr.value)})"
    if isinstance(expr, Add):
        return f"({expr_to_lean(expr.left)} + {expr_to_lean(expr.right)})"
    if isinstance(expr, Mul):
        return f"({expr_to_lean(expr.left)} * {expr_to_lean(expr.right)})"
    raise LeanTranslationError(f"Unsupported expression: {type(expr)!r}")


def formula_to_lean(formula: Formula) -> str:
    if isinstance(formula, Eq):
        return f"{expr_to_lean(formula.left)} = {expr_to_lean(formula.right)}"
    if isinstance(formula, Not):
        return f"¬ ({formula_to_lean(formula.formula)})"
    if isinstance(formula, Implies):
        return (
            f"({formula_to_lean(formula.premise)}) → "
            f"({formula_to_lean(formula.conclusion)})"
        )
    if isinstance(formula, ForAll):
        variable = _lean_identifier(formula.variable.name)
        return f"∀ ({variable} : Nat), {formula_to_lean(formula.body)}"
    if isinstance(formula, Bottom):
        return "False"
    raise LeanTranslationError(f"Unsupported formula: {type(formula)!r}")


class LeanProofProvider(Protocol):
    def tactic_for(self, formula: Formula) -> str:
        """Return a Lean tactic block for the supplied formula."""


@dataclass(frozen=True)
class DeterministicTacticProvider:
    """Small tactic portfolio; no LLM or paid API required."""

    tactics: tuple[str, ...] = (
        "by\n  simp",
        "by\n  omega",
        "by\n  ring",
        "by\n  norm_num",
        "by\n  aesop",
    )

    def tactic_for(self, formula: Formula) -> str:
        return self.tactics[0]


@dataclass(frozen=True)
class LeanVerificationResult:
    accepted: bool
    theorem_name: str
    lean_statement: str
    tactic: str | None
    stdout: str
    stderr: str
    attempts: int


def theorem_source(
    theorem_name: str,
    formula: Formula,
    tactic: str,
    *,
    namespace: str = "Gareen.Generated",
) -> str:
    name = _lean_identifier(theorem_name)
    statement = formula_to_lean(formula)
    return (
        "import Mathlib\n\n"
        f"namespace {namespace}\n\n"
        f"theorem {name} : {statement} := {tactic}\n\n"
        f"end {namespace}\n"
    )


class LeanVerifier:
    """Verify Gareen statements by invoking Lean through Lake."""

    def __init__(
        self,
        *,
        project_dir: str | Path = ".",
        tactics: tuple[str, ...] | None = None,
        timeout_seconds: int = 60,
    ) -> None:
        self.project_dir = Path(project_dir).resolve()
        self.tactics = tactics or DeterministicTacticProvider().tactics
        self.timeout_seconds = timeout_seconds

    def verify(
        self,
        theorem_name: str,
        formula: Formula,
    ) -> LeanVerificationResult:
        lean_statement = formula_to_lean(formula)
        last_stdout = ""
        last_stderr = ""

        for attempt, tactic in enumerate(self.tactics, start=1):
            source = theorem_source(theorem_name, formula, tactic)
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".lean",
                prefix="gareen_",
                dir=self.project_dir,
                delete=False,
                encoding="utf-8",
            ) as handle:
                handle.write(source)
                path = Path(handle.name)

            try:
                completed = subprocess.run(
                    ["lake", "env", "lean", str(path)],
                    cwd=self.project_dir,
                    text=True,
                    capture_output=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
                last_stdout = completed.stdout
                last_stderr = completed.stderr
                if completed.returncode == 0:
                    return LeanVerificationResult(
                        accepted=True,
                        theorem_name=theorem_name,
                        lean_statement=lean_statement,
                        tactic=tactic,
                        stdout=completed.stdout,
                        stderr=completed.stderr,
                        attempts=attempt,
                    )
            finally:
                path.unlink(missing_ok=True)

        return LeanVerificationResult(
            accepted=False,
            theorem_name=theorem_name,
            lean_statement=lean_statement,
            tactic=None,
            stdout=last_stdout,
            stderr=last_stderr,
            attempts=len(self.tactics),
        )


def write_generated_module(
    path: str | Path,
    theorem_name: str,
    formula: Formula,
    tactic: str,
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        theorem_source(theorem_name, formula, tactic),
        encoding="utf-8",
    )
    return target


if __name__ == "__main__":
    from math_world import ONE, THREE, TWO

    goal = Eq(Add(TWO, ONE), THREE)
    target = write_generated_module(
        "Gareen/BridgeSmoke.lean",
        "bridge_two_plus_one",
        goal,
        "by\n  norm_num",
    )
    print(target)
