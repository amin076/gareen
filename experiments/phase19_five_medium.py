"""Five medium theorem diagnostic for Phase 19 ecosystem strategies.

Purpose: verify that the native Lean/Mathlib strategy layer is actually
functional on a varied set of medium-difficulty theorems, without allowing the
custom Gareen recursive fallback to hide failures.

Each theorem is deliberately chosen to stress a different standard strategy:
- arithmetic normalization / omega,
- ring normalization,
- gcd/coprimality library reasoning,
- divisibility composition,
- propositional chaining.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ecosystem_strategy_planner import EcosystemStrategyPlanner

GOALS = [
    (
        "medium_arithmetic",
        "∀ a b : Nat, a ≤ b → a + 7 ≤ b + 7",
    ),
    (
        "medium_ring",
        "∀ x y : Int, (x + y) * (x + y) = x*x + 2*x*y + y*y",
    ),
    (
        "medium_consecutive_gcd",
        "∀ n : Nat, Nat.gcd n (n + 1) = 1",
    ),
    (
        "medium_divisibility",
        "∀ d a b : Nat, d ∣ a → d ∣ b → d ∣ a + b",
    ),
    (
        "medium_logic_chain",
        "∀ P Q R : Prop, (P → Q) → (Q → R) → P → R",
    ),
]

OUT = ROOT / ".gareen/phase19-five-medium.json"
MD = ROOT / ".gareen/phase19-five-medium.md"


def require_lean_toolchain() -> None:
    """Fail CI only when the Lean toolchain itself is unavailable."""
    if shutil.which("lake") is None:
        raise RuntimeError("Lean infrastructure failure: 'lake' is not on PATH")
    probe = subprocess.run(
        ["lake", "env", "lean", "--version"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if probe.returncode != 0:
        detail = (probe.stderr or probe.stdout).strip()
        raise RuntimeError(
            "Lean infrastructure failure: 'lake env lean --version' failed "
            f"with exit code {probe.returncode}: {detail}"
        )


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    require_lean_toolchain()
    planner = EcosystemStrategyPlanner(
        per_strategy_timeout=15,
        gareen_timeout=30,
        gareen_nodes=1200,
    )

    rows = []
    started = time.monotonic()

    for name, statement in GOALS:
        result = planner.prove(
            statement,
            theorem_name=name,
            wall_clock_budget_seconds=120,
            stop_on_first_success=True,
            use_gareen_fallback=False,
        )
        row = {
            "name": name,
            "statement": statement,
            "status": "proved" if result.verified else "unproved",
            "verified": result.verified,
            "winning_strategy": result.winning_strategy,
            "layer": result.layer,
            "elapsed_seconds": result.elapsed_seconds,
            "attempts": [
                {
                    "strategy": a.strategy,
                    "verified": a.verified,
                    "timed_out": a.timed_out,
                    "returncode": a.returncode,
                    "elapsed_seconds": a.elapsed_seconds,
                }
                for a in result.attempts
            ],
        }
        rows.append(row)
        OUT.write_text(
            json.dumps({"experiment_status": "running", "rows": rows}, indent=2),
            encoding="utf-8",
        )
        print(
            f"{name}: verified={result.verified}, "
            f"winner={result.winning_strategy}, "
            f"elapsed={result.elapsed_seconds}s",
            flush=True,
        )

    proved = sum(r["verified"] for r in rows)
    unproved = len(rows) - proved
    theorem_status = (
        "all-proved" if proved == len(rows)
        else "unproved" if proved == 0
        else "partially-proved"
    )
    payload = {
        "experiment_status": "completed",
        "theorem_status": theorem_status,
        "proved": proved,
        "unproved": unproved,
        "total": len(rows),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Phase 19 ecosystem-only five-medium diagnostic",
        "",
        "- Experiment status: completed",
        f"- Theorem status: {theorem_status}",
        f"- Proved: {proved}/{len(rows)}",
        f"- Unproved: {unproved}/{len(rows)}",
        f"- Elapsed: {payload['elapsed_seconds']}s",
        "",
        "| Goal | Verified | Winning strategy | Seconds |",
        "|---|---:|---|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['name']} | {r['verified']} | "
            f"{r['winning_strategy'] or '-'} | {r['elapsed_seconds']} |"
        )
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(payload, indent=2), flush=True)
    print(
        f"Experiment completed successfully: {proved} proved, {unproved} unproved. "
        "Unproved goals do not constitute a CI failure.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
