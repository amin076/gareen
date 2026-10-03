"""Dynamic Lean proof-state orchestration for Gareen Phase 19.

Unlike the earlier multi-subgoal planner, this module does not split the target
formula in Python.  It asks Lean to execute a decomposition tactic, captures
the actual resulting proof states emitted by Gareen.ProofStateProbe, routes
each emitted target independently, then assembles and audits the final proof.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
import time
from typing import Optional

from lean_proof_planner import _context_intro_names, _split_forall, _split_top_level
from multi_subgoal_proof_planner import MultiSubgoalProofPlanner, RoutedBranch
from recursive_proof_planner import audited, validate_statement

_STATE_PREFIX = "GAREEN_PROOF_STATE "
_RULE_PREFIX = "GAREEN_DECOMPOSITION_RULE "


@dataclass(frozen=True)
class DynamicSubgoal:
    index: int
    target: str
    locals: tuple[dict, ...]


@dataclass(frozen=True)
class DynamicProofStateResult:
    theorem_name: str
    statement: str
    verified: bool
    decomposition_tactic: Optional[str]
    probed_subgoals: tuple[DynamicSubgoal, ...]
    branches: tuple[RoutedBranch, ...]
    assembly_source_path: Optional[str]
    assembly_returncode: Optional[int]
    assembly_stdout: str
    assembly_stderr: str
    elapsed_seconds: float


def _prefix_from_statement(statement: str) -> str:
    binders, body = _split_forall(statement)
    antecedents: list[str] = []
    rest = body
    while True:
        split = _split_top_level(rest, "→")
        if split is None:
            break
        left, rest = split
        antecedents.append(left)
    parts: list[str] = []
    if binders:
        parts.append(f"∀ {binders},")
    if antecedents:
        parts.append(" → ".join(antecedents) + " →")
    return " ".join(parts).strip()


class DynamicProofStatePlanner:
    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self.repo_root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parent
        self.generated_dir = self.repo_root / ".gareen/dynamic_proof_state"
        self.router = MultiSubgoalProofPlanner(self.repo_root)

    @staticmethod
    def _parse_states(output: str) -> tuple[DynamicSubgoal, ...]:
        states: list[DynamicSubgoal] = []
        for line in output.splitlines():
            if _STATE_PREFIX not in line:
                continue
            raw = line.split(_STATE_PREFIX, 1)[1].strip()
            try:
                item = json.loads(raw)
            except json.JSONDecodeError:
                continue
            states.append(DynamicSubgoal(
                int(item.get("index", len(states))),
                str(item.get("target", "")).strip(),
                tuple(item.get("locals", [])),
            ))
        return tuple(states)

    @staticmethod
    def _parse_rule(output: str) -> Optional[str]:
        for line in output.splitlines():
            if _RULE_PREFIX in line:
                rule = line.split(_RULE_PREFIX, 1)[1].strip()
                if rule:
                    return rule
        return None

    def _probe(self, *, theorem_name: str, statement: str, timeout: float) -> tuple[Optional[str], tuple[DynamicSubgoal, ...], str, str, int]:
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        path = self.generated_dir / f"{theorem_name}_probe.lean"
        intro_names = _context_intro_names(statement)
        lines = [
            "import Mathlib",
            "import Gareen.ProofStateProbe",
            "",
            "namespace Gareen.DynamicProbeGenerated",
            "",
            f"theorem {theorem_name}_probe : {statement} := by",
        ]
        if intro_names:
            lines.append("  intro " + " ".join(intro_names))
        lines.append("  gareen_probe_auto")
        lines.extend(["", "end Gareen.DynamicProbeGenerated", ""])
        path.write_text("\n".join(lines), encoding="utf-8")
        try:
            proc = subprocess.run(
                ["lake", "env", "lean", str(path)],
                cwd=self.repo_root, capture_output=True, text=True,
                timeout=max(1.0, timeout), check=False,
            )
            out, err, rc = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as exc:
            def _txt(x):
                return x.decode(errors="replace") if isinstance(x, bytes) else (x or "")
            out, err, rc = _txt(exc.stdout), _txt(exc.stderr) + "\nProbe timed out.", 124
        path.with_suffix(".stdout.log").write_text(out, encoding="utf-8")
        path.with_suffix(".stderr.log").write_text(err, encoding="utf-8")
        combined = out + "\n" + err
        return self._parse_rule(combined), self._parse_states(combined), out, err, rc

    def prove(self, statement: str, *, theorem_name: str = "gareen_dynamic_goal", total_budget_seconds: float = 240.0) -> DynamicProofStateResult:
        started = time.monotonic()
        statement = validate_statement(statement)
        prefix = _prefix_from_statement(statement)

        chosen: Optional[str] = None
        states: tuple[DynamicSubgoal, ...] = ()
        remaining = total_budget_seconds - (time.monotonic() - started)
        if remaining > 5:
            rule, probed, _, _, _ = self._probe(
                theorem_name=theorem_name,
                statement=statement,
                timeout=min(25.0, remaining),
            )
            if rule is not None and len(probed) >= 2 and all(s.target for s in probed):
                chosen, states = rule, probed

        if chosen is None:
            return DynamicProofStateResult(
                theorem_name, statement, False, None, states, (), None, None, "", "",
                round(time.monotonic() - started, 3),
            )

        branch_results: list[RoutedBranch] = []
        branch_proofs: list[tuple[str, ...]] = []
        remaining_total = max(1.0, total_budget_seconds - (time.monotonic() - started) - 25.0)
        each_budget = remaining_total / len(states)

        for state in states:
            branch_statement = f"{prefix} {state.target}".strip()
            branch, proof = self.router._solve_branch(
                name=f"{theorem_name}_dynamic_{state.index}",
                statement=branch_statement,
                budget_seconds=each_budget,
            )
            branch_results.append(branch)
            branch_proofs.append(proof)

        if not all(b.verified for b in branch_results):
            return DynamicProofStateResult(
                theorem_name, statement, False, chosen, states, tuple(branch_results),
                None, None, "", "", round(time.monotonic() - started, 3),
            )

        self.generated_dir.mkdir(parents=True, exist_ok=True)
        path = self.generated_dir / f"{theorem_name}_assembled.lean"
        intro_names = _context_intro_names(statement)
        helper_names = [f"{theorem_name}_helper_{i}" for i in range(len(states))]
        branch_statements = [f"{prefix} {s.target}".strip() for s in states]

        lines = [
            "import Mathlib",
            "import Auto.Tactic",
            "import Gareen.RecursivePlanner",
            "import Gareen.RecursivePlannerLegacy",
            "",
            "namespace Gareen.DynamicAssembled",
            "",
        ]
        for helper, branch_statement, proof in zip(helper_names, branch_statements, branch_proofs):
            lines.append(f"theorem {helper} : {branch_statement} := by")
            lines.extend("  " + line for line in proof)
            lines.append("")

        lines.append(f"theorem {theorem_name} : {statement} := by")
        if intro_names:
            lines.append("  intro " + " ".join(intro_names))
        lines.append(f"  apply {chosen}")
        for helper, branch_statement in zip(helper_names, branch_statements):
            names = _context_intro_names(branch_statement)
            call = helper + (" " + " ".join(names) if names else "")
            lines.append(f"  · exact {call}")
        lines.extend([
            "",
            f"#print axioms Gareen.DynamicAssembled.{theorem_name}",
            "",
            "end Gareen.DynamicAssembled",
            "",
        ])
        path.write_text("\n".join(lines), encoding="utf-8")

        remaining = max(1.0, total_budget_seconds - (time.monotonic() - started))
        try:
            proc = subprocess.run(
                ["lake", "env", "lean", str(path)], cwd=self.repo_root,
                capture_output=True, text=True, timeout=remaining, check=False,
            )
            rc, out, err = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            def _txt(x):
                return x.decode(errors="replace") if isinstance(x, bytes) else (x or "")
            rc, out, err = 124, _txt(exc.stdout), _txt(exc.stderr) + "\nAssembly timed out."

        verified = audited(out + "\n" + err, rc)
        return DynamicProofStateResult(
            theorem_name, statement, verified, chosen, states, tuple(branch_results),
            str(path), rc, out, err, round(time.monotonic() - started, 3),
        )
