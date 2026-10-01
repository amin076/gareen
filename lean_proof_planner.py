"""Lean/Mathlib theorem retrieval and small proof planning for Gareen.

Phase 17 adds a missing layer between conjecture generation and kernel
verification:

    goal
      -> structural decomposition
      -> Mathlib theorem retrieval (Lean exact?)
      -> lemma composition
      -> Lean kernel verification

This module intentionally does not hard-code the theorem names needed for the
GCD benchmark.  Mathlib's `exact?` tactic is used as the retrieval engine.
Gareen contributes the research/proof-plan structure; Lean/Mathlib retrieves
library facts that close each subgoal and the final composition step.

The first reusable planner schema is divisibility over addition:

    d ∣ x + y
      -> prove d ∣ x
      -> prove d ∣ y
      -> ask Mathlib to retrieve the composition theorem

This schema is independent of gcd and can be reused for any natural-number
divisibility goal with a top-level sum.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Optional


_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_']*$")
_TRY_THIS_RE = re.compile(r"Try this:\s*(.+)")
_IDENT_RE = re.compile(r"(?:exact|apply)\s+\(?([A-Za-z_][A-Za-z0-9_'.]*)")
_QUALIFIED_CONST_RE = re.compile(
    r"\b(?:[A-Za-z_][A-Za-z0-9_']*\.)+[A-Za-z_][A-Za-z0-9_']*\b"
)


@dataclass(frozen=True)
class DvdAddDecomposition:
    binders: str
    intro_names: tuple[str, ...]
    divisor: str
    left_addend: str
    right_addend: str
    body: str


@dataclass(frozen=True)
class PlannerAttempt:
    strategy: str
    verified: bool
    returncode: int
    elapsed_seconds: float
    timed_out: bool
    source_path: str
    suggestions: tuple[str, ...]
    retrieved_constants: tuple[str, ...]
    stdout: str
    stderr: str


@dataclass(frozen=True)
class PlannedProofResult:
    theorem_name: str
    statement: str
    verified: bool
    winning_strategy: Optional[str]
    attempts: tuple[PlannerAttempt, ...]

    @property
    def retrieved_constants(self) -> tuple[str, ...]:
        seen: list[str] = []
        for attempt in self.attempts:
            for name in attempt.retrieved_constants:
                if name not in seen:
                    seen.append(name)
        return tuple(seen)


def _safe_identifier(name: str) -> str:
    if not _SAFE_IDENTIFIER.fullmatch(name):
        raise ValueError(f"Unsafe theorem identifier: {name!r}")
    return name


def _strip_outer_parens(text: str) -> str:
    value = text.strip()
    while value.startswith("(") and value.endswith(")"):
        depth = 0
        wraps = True
        for index, char in enumerate(value):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0 and index != len(value) - 1:
                    wraps = False
                    break
        if not wraps or depth != 0:
            break
        value = value[1:-1].strip()
    return value


def _find_top_level(text: str, needle: str) -> int:
    depth = 0
    index = 0
    while index <= len(text) - len(needle):
        char = text[index]
        if char in "([{":
            depth += 1
            index += 1
            continue
        if char in ")]}":
            depth -= 1
            index += 1
            continue
        if depth == 0 and text.startswith(needle, index):
            return index
        index += 1
    return -1


def _split_top_level(text: str, needle: str) -> Optional[tuple[str, str]]:
    index = _find_top_level(text, needle)
    if index < 0:
        return None
    return text[:index].strip(), text[index + len(needle) :].strip()


def _split_forall(statement: str) -> tuple[str, str]:
    text = statement.strip()
    if not text.startswith("∀"):
        return "", text

    rest = text[1:].strip()
    split = _split_top_level(rest, ",")
    if split is None:
        return "", text
    binders, body = split
    return binders.strip(), body.strip()


def _intro_names(binders: str) -> tuple[str, ...]:
    if not binders:
        return ()

    parenthesized = re.findall(
        r"\(([A-Za-z_][A-Za-z0-9_']*)\s*:",
        binders,
    )
    if parenthesized:
        return tuple(parenthesized)

    # Current Gareen native propositions commonly use:
    #   ∀ a b : Nat, ...
    before_type = binders.split(":", 1)[0].strip()
    names = tuple(
        token
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_']*", before_type)
        if token not in {"Nat", "Int", "Prop"}
    )
    return names


def decompose_dvd_add(statement: str) -> Optional[DvdAddDecomposition]:
    """Recognize a top-level natural-number goal of the form d ∣ x + y."""

    binders, body = _split_forall(statement)
    body = _strip_outer_parens(body)

    dvd_split = _split_top_level(body, "∣")
    if dvd_split is None:
        return None
    divisor, dividend = dvd_split
    dividend = _strip_outer_parens(dividend)

    add_split = _split_top_level(dividend, "+")
    if add_split is None:
        return None
    left, right = add_split

    intro_names = _intro_names(binders)
    return DvdAddDecomposition(
        binders=binders,
        intro_names=intro_names,
        divisor=_strip_outer_parens(divisor),
        left_addend=_strip_outer_parens(left),
        right_addend=_strip_outer_parens(right),
        body=body,
    )


def _render_source(theorem_name: str, statement: str, proof_lines: tuple[str, ...]) -> str:
    name = _safe_identifier(theorem_name)
    lines = [
        "import Mathlib",
        "",
        "namespace Gareen.GeneratedPlanner",
        "",
        f"theorem {name} : {statement} := by",
    ]
    lines.extend(f"  {line}" if line else "" for line in proof_lines)
    lines.extend(["", "end Gareen.GeneratedPlanner", ""])
    return "\n".join(lines)


def _extract_suggestions(stdout: str, stderr: str) -> tuple[str, ...]:
    """Extract both one-line and current multiline Lean `Try this` messages."""

    suggestions: list[str] = []
    lines = (stdout + "\n" + stderr).splitlines()

    for index, line in enumerate(lines):
        if "Try this:" not in line:
            continue

        tail = line.split("Try this:", 1)[1].strip()
        if tail:
            suggestion = tail
        else:
            suggestion = ""
            for following in lines[index + 1 :]:
                candidate = following.strip()
                if not candidate:
                    continue
                # Lean 4.34 currently prefixes exact? suggestions with
                # annotations such as `[apply]`.
                candidate = re.sub(r"^\[[^]]+\]\s*", "", candidate)
                suggestion = candidate
                break

        if suggestion and suggestion not in suggestions:
            suggestions.append(suggestion)

    return tuple(suggestions)


def _constants_from_suggestions(suggestions: tuple[str, ...]) -> tuple[str, ...]:
    constants: list[str] = []
    for suggestion in suggestions:
        # Qualified Mathlib constants can appear under parentheses or inside
        # a composed proof term, not only immediately after `exact`.
        for name in _QUALIFIED_CONST_RE.findall(suggestion):
            if name not in constants:
                constants.append(name)
        for match in _IDENT_RE.finditer(suggestion):
            name = match.group(1)
            if name not in constants:
                constants.append(name)
    return tuple(constants)


class LeanProofPlanner:
    """Retrieve Mathlib facts and compose a small structured proof."""

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        *,
        generated_dir: str = ".gareen/planner_candidates",
        timeout_seconds: int = 90,
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

    def _attempt(
        self,
        *,
        theorem_name: str,
        statement: str,
        strategy: str,
        proof_lines: tuple[str, ...],
        timeout_seconds: float,
    ) -> PlannerAttempt:
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        source = _render_source(theorem_name, statement, proof_lines)
        path = self.generated_dir / f"{theorem_name}_{strategy}.lean"
        path.write_text(source, encoding="utf-8")

        try:
            relative = path.relative_to(self.repo_root)
            command_path = str(relative)
        except ValueError:
            command_path = str(path)

        started = time.monotonic()
        timed_out = False
        try:
            completed = subprocess.run(
                ["lake", "env", "lean", command_path],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=max(1.0, timeout_seconds),
                check=False,
            )
            returncode = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            returncode = 124
            stdout = exc.stdout or ""
            stderr = (exc.stderr or "") + "\nLean planner attempt timed out."

        elapsed = time.monotonic() - started
        suggestions = _extract_suggestions(stdout, stderr)
        return PlannerAttempt(
            strategy=strategy,
            verified=returncode == 0,
            returncode=returncode,
            elapsed_seconds=round(elapsed, 3),
            timed_out=timed_out,
            source_path=str(path),
            suggestions=suggestions,
            retrieved_constants=_constants_from_suggestions(suggestions),
            stdout=stdout,
            stderr=stderr,
        )

    def _strategies(self, statement: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
        strategies: list[tuple[str, tuple[str, ...]]] = [
            ("direct_library_retrieval", ("exact?",)),
        ]

        binders, _ = _split_forall(statement)
        intro_names = _intro_names(binders)
        if intro_names:
            strategies.append(
                (
                    "introduced_library_retrieval",
                    (
                        "intro " + " ".join(intro_names),
                        "exact?",
                    ),
                )
            )

        decomposition = decompose_dvd_add(statement)
        if decomposition is not None and decomposition.intro_names:
            intro = "intro " + " ".join(decomposition.intro_names)
            left_goal = (
                f"{decomposition.divisor} ∣ {decomposition.left_addend}"
            )
            right_goal = (
                f"{decomposition.divisor} ∣ {decomposition.right_addend}"
            )
            strategies.append(
                (
                    "dvd_add_decompose_retrieve_compose",
                    (
                        intro,
                        f"have gareen_left : {left_goal} := by",
                        "  exact?",
                        f"have gareen_right : {right_goal} := by",
                        "  exact?",
                        "exact?",
                    ),
                )
            )

        return tuple(strategies)

    def prove(
        self,
        statement: str,
        *,
        theorem_name: str = "gareen_planned_goal",
        wall_clock_budget_seconds: float = 300.0,
        per_attempt_timeout_seconds: Optional[int] = None,
    ) -> PlannedProofResult:
        theorem_name = _safe_identifier(theorem_name)
        if not self.available():
            return PlannedProofResult(
                theorem_name=theorem_name,
                statement=statement,
                verified=False,
                winning_strategy=None,
                attempts=(),
            )

        started = time.monotonic()
        deadline = started + max(1.0, wall_clock_budget_seconds)
        timeout = per_attempt_timeout_seconds or self.timeout_seconds
        attempts: list[PlannerAttempt] = []

        for strategy, proof_lines in self._strategies(statement):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            attempt = self._attempt(
                theorem_name=theorem_name,
                statement=statement,
                strategy=strategy,
                proof_lines=proof_lines,
                timeout_seconds=min(float(timeout), remaining),
            )
            attempts.append(attempt)
            if attempt.verified:
                return PlannedProofResult(
                    theorem_name=theorem_name,
                    statement=statement,
                    verified=True,
                    winning_strategy=strategy,
                    attempts=tuple(attempts),
                )

        return PlannedProofResult(
            theorem_name=theorem_name,
            statement=statement,
            verified=False,
            winning_strategy=None,
            attempts=tuple(attempts),
        )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--statement",
        default="∀ a b : Nat, Nat.gcd a b ∣ a + b",
    )
    parser.add_argument("--name", default="gareen_planner_demo")
    parser.add_argument("--seconds", type=int, default=300)
    args = parser.parse_args()

    planner = LeanProofPlanner()
    result = planner.prove(
        args.statement,
        theorem_name=args.name,
        wall_clock_budget_seconds=max(1, args.seconds),
    )

    print("Gareen theorem-retrieval planner")
    print("================================")
    print("Statement:", result.statement)
    print("Verified:", result.verified)
    print("Winning strategy:", result.winning_strategy or "-")
    print("Retrieved constants:", result.retrieved_constants or "-")
    for attempt in result.attempts:
        print(
            f"  - {attempt.strategy}: verified={attempt.verified} "
            f"elapsed={attempt.elapsed_seconds}s "
            f"retrieved={attempt.retrieved_constants or '-'}"
        )
        for suggestion in attempt.suggestions:
            print("      suggestion:", suggestion)

    return 0 if result.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
