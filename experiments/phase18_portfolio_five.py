"""Fast five-goal portfolio smoke test for Phase 18.

Three goals are current advanced-engine failures from run #91.
Two are recent regressions that the advanced engine now solves, to verify that
the cascade preserves its strengths while the frozen legacy engine provides
fallback coverage.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from portfolio_proof_planner import PortfolioProofPlanner

GOALS = [
    ("logic_and_branching_00", "∀ P Q : Prop, P → Q → P ∧ Q"),
    ("composition_02", "∀ a b : Nat, Nat.gcd a b ∣ a + (a + b)"),
    ("composition_03", "∀ a b : Nat, Nat.gcd a b ∣ (a + b) + b"),
    ("composition_04", "∀ a b : Nat, Nat.gcd a b ∣ (a + b) + (b + a)"),
    ("logic_and_branching_07",
     "∀ a b : Nat, Nat.gcd a b ∣ a + b ∧ Nat.gcd a b ∣ b + a"),
]

OUT = ROOT / ".gareen/phase18-portfolio-five.json"
MD = ROOT / ".gareen/phase18-portfolio-five.md"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / ".gareen/portfolio-advanced-memory.json").unlink(missing_ok=True)
    planner = PortfolioProofPlanner(
        advanced_timeout=25,
        legacy_timeout=25,
        advanced_nodes=1200,
        legacy_nodes=1200,
    )

    rows = []
    started = time.monotonic()

    for name, statement in GOALS:
        result = planner.prove(statement, theorem_name=f"portfolio_{name}")
        advanced = result.advanced
        legacy = result.legacy
        row = {
            "name": name,
            "statement": statement,
            "verified": result.verified,
            "winning_engine": result.winning_engine,
            "elapsed_seconds": result.elapsed_seconds,
            "advanced_status": advanced["status"],
            "advanced_nodes": advanced["expanded_nodes"],
            "legacy_status": legacy["status"] if legacy else "not-run",
            "legacy_nodes": legacy["expanded_nodes"] if legacy else 0,
        }
        rows.append(row)
        OUT.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
        print(
            f"{name}: portfolio={'verified' if result.verified else 'failed'}, "
            f"winner={result.winning_engine}, "
            f"advanced={row['advanced_status']}/{row['advanced_nodes']}, "
            f"legacy={row['legacy_status']}/{row['legacy_nodes']}, "
            f"elapsed={row['elapsed_seconds']}s",
            flush=True,
        )

    payload = {
        "verified": sum(r["verified"] for r in rows),
        "total": len(rows),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Phase 18 two-engine portfolio: five-goal smoke test",
        "",
        f"- Verified: {payload['verified']}/{payload['total']}",
        f"- Elapsed: {payload['elapsed_seconds']}s",
        "",
        "| Goal | Advanced | Legacy fallback | Winner | Portfolio |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['name']} | {r['advanced_status']} ({r['advanced_nodes']}) | "
            f"{r['legacy_status']} ({r['legacy_nodes']}) | "
            f"{r['winning_engine'] or '-'} | {'✓' if r['verified'] else '✗'} |"
        )
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0 if payload["verified"] == payload["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
