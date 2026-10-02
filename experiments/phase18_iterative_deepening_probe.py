"""Phase 18.5 experiment: iterative-deepening resource scheduling.

Motivation: ranked DFS can spend the entire node budget inside the first attractive
branch. Iterative deepening gives shallow proof shapes a fair chance before deeper
branches consume the search budget. This is diagnostic and does not change the
trusted Lean kernel or proof rules.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recursive_proof_planner import RecursiveProofPlanner

OUT = ROOT / ".gareen/phase18-iterative-deepening.json"
MD = ROOT / ".gareen/phase18-iterative-deepening.md"

GOALS = [
    ("composition_01", "∀ a b : Nat, Nat.gcd a b ∣ b + a"),
    ("composition_04", "∀ a b : Nat, Nat.gcd a b ∣ (a + b) + (b + a)"),
    ("logic_and_branching_07",
     "∀ a b : Nat, Nat.gcd a b ∣ a + b ∧ Nat.gcd a b ∣ b + a"),
]

# Shallow searches get tried first. Later attempts receive larger node budgets.
SCHEDULE = [
    (2, 500),
    (3, 800),
    (4, 1200),
    (5, 2400),
    (6, 5000),
]
PER_ATTEMPT_SECONDS = 90.0
PER_GOAL_SECONDS = 360.0


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    all_rows = []

    for name, statement in GOALS:
        goal_start = time.monotonic()
        attempts = []
        verified = False
        winner = None

        memory = ROOT / f".gareen/{name}.iterative.memory.json"
        memory.unlink(missing_ok=True)

        for depth, nodes in SCHEDULE:
            remaining = PER_GOAL_SECONDS - (time.monotonic() - goal_start)
            if remaining <= 0:
                break

            planner = RecursiveProofPlanner(
                timeout_seconds=min(PER_ATTEMPT_SECONDS, remaining),
                max_depth=depth,
                max_nodes=nodes,
                max_candidates=48,
                memory_path=memory,
            )
            result = planner.prove(
                statement,
                theorem_name=f"id_{name}_d{depth}_n{nodes}",
                wall_clock_budget_seconds=min(PER_ATTEMPT_SECONDS, remaining),
                per_attempt_timeout_seconds=min(PER_ATTEMPT_SECONDS, remaining),
            )
            row = {
                "depth": depth,
                "node_budget": nodes,
                "verified": result.verified,
                "status": result.status,
                "expanded_nodes": result.expanded_nodes,
                "elapsed_seconds": result.attempts[0].elapsed_seconds if result.attempts else 0,
                "retrieved_constants": list(result.retrieved_constants),
            }
            attempts.append(row)
            print(
                f"{name}: depth={depth}, budget={nodes}, "
                f"verified={result.verified}, status={result.status}, "
                f"nodes={result.expanded_nodes}",
                flush=True,
            )
            if result.verified:
                verified = True
                winner = row
                break

        all_rows.append({
            "name": name,
            "statement": statement,
            "verified": verified,
            "winner": winner,
            "attempts": attempts,
            "elapsed_seconds": round(time.monotonic() - goal_start, 3),
        })
        OUT.write_text(json.dumps({"rows": all_rows}, indent=2), encoding="utf-8")

    payload = {
        "strategy": "iterative-deepening-ranked-search",
        "schedule": [{"depth": d, "node_budget": n} for d, n in SCHEDULE],
        "verified": sum(r["verified"] for r in all_rows),
        "rows": all_rows,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Phase 18.5 iterative-deepening probe",
        "",
        f"- Verified: {payload['verified']}/3",
        "",
        "| Goal | Verified | Winning depth | Winning node budget | Expanded nodes |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in all_rows:
        w = r["winner"] or {}
        lines.append(
            f"| {r['name']} | {r['verified']} | {w.get('depth','-')} | "
            f"{w.get('node_budget','-')} | {w.get('expanded_nodes','-')} |"
        )
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "verified": payload["verified"],
        "goals": {r["name"]: r["verified"] for r in all_rows},
    }, indent=2))
    return 0 if payload["verified"] == 3 else 1


if __name__ == "__main__":
    raise SystemExit(main())
