"""Frontier single-goal test after the Phase 18.5 50/50 milestone.

Goal:
    ∀ n : Nat, Nat.gcd n (n + 1) = 1

This is intentionally outside the fixed 50-goal ladder and is meant to test
whether the two-engine portfolio can transfer to a slightly harder, natural
number-theory theorem.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from portfolio_proof_planner import PortfolioProofPlanner

NAME = "frontier_consecutive_gcd"
STATEMENT = "∀ n : Nat, Nat.gcd n (n + 1) = 1"

OUT = ROOT / ".gareen/frontier-consecutive-gcd.json"
MD = ROOT / ".gareen/frontier-consecutive-gcd.md"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / ".gareen/portfolio-advanced-memory.json").unlink(missing_ok=True)

    planner = PortfolioProofPlanner(
        advanced_timeout=40,
        legacy_timeout=40,
        advanced_nodes=2500,
        legacy_nodes=2500,
    )

    started = time.monotonic()
    result = planner.prove(STATEMENT, theorem_name=NAME)
    elapsed = round(time.monotonic() - started, 3)

    payload = {
        "name": NAME,
        "statement": STATEMENT,
        "verified": result.verified,
        "winning_engine": result.winning_engine,
        "elapsed_seconds": elapsed,
        "advanced": result.advanced,
        "legacy": result.legacy,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    advanced = result.advanced
    legacy = result.legacy

    lines = [
        "# Gareen frontier test: consecutive numbers are coprime",
        "",
        f"- Statement: `{STATEMENT}`",
        f"- Verified: {result.verified}",
        f"- Winner: {result.winning_engine}",
        f"- Elapsed: {elapsed}s",
        f"- Advanced: {advanced['status']} / {advanced['expanded_nodes']} nodes",
        f"- Legacy: {(legacy['status'] if legacy else 'not-run')} / {(legacy['expanded_nodes'] if legacy else 0)} nodes",
        "",
        "## Accepted declarations",
    ]

    def accepted_decls(engine):
        if not engine:
            return []
        return [
            e.get("declaration")
            for e in engine.get("proof_graph", [])
            if e.get("status") == "accepted" and e.get("declaration")
        ]

    decls = accepted_decls(advanced) + accepted_decls(legacy)
    if decls:
        for d in dict.fromkeys(decls):
            lines.append(f"- `{d}`")
    else:
        lines.append("- none recorded")

    MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "verified": result.verified,
        "winning_engine": result.winning_engine,
        "elapsed_seconds": elapsed,
        "advanced_status": advanced["status"],
        "advanced_nodes": advanced["expanded_nodes"],
        "legacy_status": legacy["status"] if legacy else "not-run",
        "legacy_nodes": legacy["expanded_nodes"] if legacy else 0,
        "accepted_declarations": list(dict.fromkeys(decls)),
    }, indent=2), flush=True)

    return 0 if result.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
