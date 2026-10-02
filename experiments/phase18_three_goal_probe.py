"""Focused Phase 18 probe for the three goals that missed the 47/50 benchmark.

This is diagnostic, not part of the main success-rate benchmark. It keeps the
same verified Lean planner but gives only these goals a larger search envelope
inside a shared 20-minute wall-clock budget.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import time

from recursive_proof_planner import RecursiveProofPlanner

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".gareen/phase18-three-goal-probe.json"
MD = ROOT / ".gareen/phase18-three-goal-probe.md"

GOALS = [
    ("composition_01", "∀ a b : Nat, Nat.gcd a b ∣ b + a"),
    ("composition_04", "∀ a b : Nat, Nat.gcd a b ∣ (a + b) + (b + a)"),
    ("logic_and_branching_07",
     "∀ a b : Nat, Nat.gcd a b ∣ a + b ∧ Nat.gcd a b ∣ b + a"),
]

TOTAL_SECONDS = 1200.0
PER_GOAL_SECONDS = 400.0


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    memory = OUT.with_suffix(".memory.json")
    memory.unlink(missing_ok=True)
    planner = RecursiveProofPlanner(
        timeout_seconds=PER_GOAL_SECONDS,
        max_depth=8,
        max_nodes=10000,
        max_candidates=96,
        memory_path=memory,
    )
    if not planner.available():
        print("Lean unavailable")
        return 2

    started = time.monotonic()
    rows = []
    for name, statement in GOALS:
        remaining = max(0.0, TOTAL_SECONDS - (time.monotonic() - started))
        budget = min(PER_GOAL_SECONDS, remaining)
        if budget <= 0:
            rows.append({
                "name": name, "statement": statement,
                "status": "not-attempted-global-budget", "verified": False
            })
            continue
        result = planner.prove(
            statement,
            theorem_name=f"probe_{name}",
            wall_clock_budget_seconds=budget,
            per_attempt_timeout_seconds=budget,
        )
        row = asdict(result)
        row["name"] = name
        rows.append(row)
        OUT.write_text(json.dumps({
            "total_budget_seconds": TOTAL_SECONDS,
            "per_goal_seconds": PER_GOAL_SECONDS,
            "rows": rows,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }, indent=2), encoding="utf-8")
        print(f"{name}: {result.status}, verified={result.verified}, nodes={result.expanded_nodes}", flush=True)

    payload = {
        "total_budget_seconds": TOTAL_SECONDS,
        "per_goal_seconds": PER_GOAL_SECONDS,
        "rows": rows,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "verified": sum(bool(r.get("verified")) for r in rows),
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        "# Phase 18 focused three-goal probe",
        "",
        f"- Total shared budget: {TOTAL_SECONDS:.0f}s",
        f"- Per-goal cap: {PER_GOAL_SECONDS:.0f}s",
        f"- Verified: {payload['verified']}/3",
        "",
        "| Goal | Verified | Status | Nodes |",
        "|---|---:|---|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['name']} | {r.get('verified', False)} | {r.get('status')} | {r.get('expanded_nodes', 0)} |"
        )
    MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "verified": payload["verified"],
        "elapsed_seconds": payload["elapsed_seconds"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
