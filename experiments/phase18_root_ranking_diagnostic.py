"""Inspect the root ranking for the remaining Phase 18.5 regression.

This experiment does not change search behavior. It runs the current planner on
composition_04 and extracts the diagnostic ranked-root events emitted by Lean so
we can see exactly which rules and scores appear above Nat.dvd_add.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recursive_proof_planner import RecursiveProofPlanner

STATEMENT = "∀ a b : Nat, Nat.gcd a b ∣ (a + b) + (b + a)"
OUT = ROOT / ".gareen/phase18-root-ranking-composition04.json"
MD = ROOT / ".gareen/phase18-root-ranking-composition04.md"


def main() -> int:
    memory = ROOT / ".gareen/phase18-root-ranking.memory.json"
    memory.unlink(missing_ok=True)
    planner = RecursiveProofPlanner(
        timeout_seconds=120,
        max_depth=4,
        max_nodes=2200,
        max_candidates=64,
        memory_path=memory,
    )
    result = planner.prove(
        STATEMENT,
        theorem_name="phase18_root_ranking_composition04",
        wall_clock_budget_seconds=120,
        per_attempt_timeout_seconds=120,
    )
    ranked = [
        e for e in result.proof_graph
        if e.get("status") == "ranked-root"
    ][:20]
    payload = {
        "statement": STATEMENT,
        "verified": result.verified,
        "status": result.status,
        "expanded_nodes": result.expanded_nodes,
        "ranked_root": ranked,
        "full_result": asdict(result),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Phase 18.5 root ranking — composition_04",
        "",
        f"- Verified in diagnostic run: {result.verified}",
        f"- Expanded nodes: {result.expanded_nodes}",
        "",
        "| Rank | Rule | Score | Residual goals |",
        "|---:|---|---:|---|",
    ]
    for i, e in enumerate(ranked, 1):
        children = "; ".join(e.get("children", []))
        lines.append(
            f"| {i} | `{e.get('rule','')}` | {e.get('score',0)} | {children} |"
        )
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "verified": result.verified,
        "expanded_nodes": result.expanded_nodes,
        "ranked_root": [
            {
                "rank": i,
                "rule": e.get("rule"),
                "score": e.get("score"),
                "children": e.get("children"),
            }
            for i, e in enumerate(ranked, 1)
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
