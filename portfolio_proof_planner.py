"""Two-engine portfolio for Gareen Phase 18.

Engine A is the current advanced recursive planner. Engine B is a frozen copy of
the last stable Phase 18 recursive planner. The portfolio is a cascade: try A,
then B only if A does not verify the theorem. Every accepted proof is checked by
Lean and the same axiom audit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

from lean_proof_planner import LeanProofPlanner, PlannerAttempt, _safe_identifier
from recursive_proof_planner import (
    RecursiveProofPlanner,
    RecursiveResult,
    audited,
    parse_events,
    validate_statement,
)


class LegacyRecursiveProofPlanner(LeanProofPlanner):
    def __init__(self, repo_root=None, *, max_depth=6, max_nodes=1200,
                 max_candidates=48, **kwargs):
        super().__init__(repo_root, **kwargs)
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.max_candidates = max_candidates

    def prove(self, statement, *, theorem_name="gareen_legacy_goal",
              wall_clock_budget_seconds=120.0, per_attempt_timeout_seconds=None):
        name = _safe_identifier(theorem_name)
        statement = validate_statement(statement)
        empty = dict(theorem_name=name, statement=statement, verified=False,
                     winning_strategy=None, attempts=(), memory_hints=())
        if wall_clock_budget_seconds <= 0:
            return RecursiveResult(**empty, status="not-attempted")
        if not self.available():
            return RecursiveResult(**empty, status="backend-unavailable")

        started = time.monotonic()
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256((name + statement).encode()).hexdigest()[:12]
        path = self.generated_dir / f"{name}_{key}_legacy.lean"
        source = (
            "import Gareen.RecursivePlannerLegacy\n"
            "set_option maxHeartbeats 2000000\n"
            "namespace Gareen.GeneratedLegacy\n"
            f"theorem {name} : {statement} := by\n"
            f"  gareen_search_legacy {self.max_depth} {self.max_nodes} {self.max_candidates}\n"
            "end Gareen.GeneratedLegacy\n"
            f"#print axioms Gareen.GeneratedLegacy.{name}\n"
        )
        path.write_text(source, encoding="utf-8")
        timeout = min(wall_clock_budget_seconds,
                      per_attempt_timeout_seconds or self.timeout_seconds)
        try:
            proc = subprocess.run(
                ["lake", "env", "lean", str(path)],
                cwd=self.repo_root, capture_output=True, text=True,
                timeout=timeout, check=False,
            )
            rc, out, err, timed_out = proc.returncode, proc.stdout, proc.stderr, False
        except subprocess.TimeoutExpired as exc:
            def _text(x):
                return x.decode(errors="replace") if isinstance(x, bytes) else (x or "")
            rc, out, err, timed_out = 124, _text(exc.stdout), _text(exc.stderr), True

        elapsed = time.monotonic() - started
        verified = audited(out + "\n" + err, rc)
        graph = parse_events(out)
        constants = tuple(dict.fromkeys(
            e["declaration"] for e in graph
            if e["status"] == "accepted" and e.get("declaration")
        )) if verified else ()
        counts = re.findall(r"GAREEN_NODES (\d+)", out)
        attempt = PlannerAttempt(
            "legacy_recursive_library_search", verified, rc, round(elapsed, 3),
            timed_out, str(path), (), constants, out, err
        )
        return RecursiveResult(
            name, statement, verified,
            "legacy_recursive_library_search" if verified else None,
            (attempt,), graph, int(counts[-1]) if counts else 0,
            "verified" if verified else ("timeout" if timed_out else "unproved-in-budget"),
            (),
        )


@dataclass(frozen=True)
class PortfolioResult:
    theorem_name: str
    statement: str
    verified: bool
    winning_engine: str | None
    advanced: dict
    legacy: dict | None
    elapsed_seconds: float


class PortfolioProofPlanner:
    def __init__(self, repo_root=None, *, advanced_timeout=25,
                 legacy_timeout=25, advanced_nodes=1200, legacy_nodes=1200):
        root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parent
        self.advanced = RecursiveProofPlanner(
            root, timeout_seconds=advanced_timeout, max_nodes=advanced_nodes,
            memory_path=root / ".gareen/portfolio-advanced-memory.json",
        )
        self.legacy = LegacyRecursiveProofPlanner(
            root, timeout_seconds=legacy_timeout, max_nodes=legacy_nodes,
        )
        self.advanced_timeout = advanced_timeout
        self.legacy_timeout = legacy_timeout

    def prove(self, statement, *, theorem_name="gareen_portfolio_goal"):
        started = time.monotonic()
        advanced = self.advanced.prove(
            statement,
            theorem_name=theorem_name + "_advanced",
            wall_clock_budget_seconds=self.advanced_timeout,
            per_attempt_timeout_seconds=self.advanced_timeout,
        )
        if advanced.verified:
            return PortfolioResult(
                theorem_name, statement, True, "advanced",
                asdict(advanced), None, round(time.monotonic() - started, 3)
            )

        legacy = self.legacy.prove(
            statement,
            theorem_name=theorem_name + "_legacy",
            wall_clock_budget_seconds=self.legacy_timeout,
            per_attempt_timeout_seconds=self.legacy_timeout,
        )
        return PortfolioResult(
            theorem_name, statement, legacy.verified,
            "legacy" if legacy.verified else None,
            asdict(advanced), asdict(legacy),
            round(time.monotonic() - started, 3),
        )
