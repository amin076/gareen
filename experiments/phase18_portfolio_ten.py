"""Controlled ten-goal validation of the Phase 18 two-engine portfolio.

The set intentionally mixes:
- current advanced-engine failures recovered by legacy,
- recent advanced-engine regression recoveries,
- easy/library/composition/logic/challenge representatives.

The goal is fast architectural validation, not a replacement for the 50-goal benchmark.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from portfolio_proof_planner import PortfolioProofPlanner

GOALS = [
    # Current advanced-engine failures from full run #91
    ("logic_and_branching_00", "∀ P Q : Prop, P → Q → P ∧ Q"),
    ("composition_02", "∀ a b : Nat, Nat.gcd a b ∣ a + (a + b)"),
    ("composition_03", "∀ a b : Nat, Nat.gcd a b ∣ (a + b) + b"),
    # Recent regressions recovered by the advanced engine
    ("composition_04", "∀ a b : Nat, Nat.gcd a b ∣ (a + b) + (b + a)"),
    ("logic_and_branching_07", "∀ a b : Nat, Nat.gcd a b ∣ a + b ∧ Nat.gcd a b ∣ b + a"),
    # Additional controlled diversity
    ("routine_07", "∀ n : Nat, n ∣ n"),
    ("library_06", "∀ a b c : Nat, a ∣ b → b ∣ c → a ∣ c"),
    ("composition_09", "∀ a b m n : Nat, Nat.gcd a b ∣ a * m + b * n"),
    ("logic_and_branching_08", "∀ d a b c : Nat, d ∣ a → d ∣ b → d ∣ c → d ∣ a + (b + c)"),
    ("challenge_07", "∀ a b : Nat, Nat.Coprime a b → Nat.gcd a b = 1"),
]

OUT = ROOT / ".gareen/phase18-portfolio-ten.json"
MD = ROOT / ".gareen/phase18-portfolio-ten.md"


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
        result = planner.prove(statement, theorem_name=f"portfolio10_{name}")
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
        "advanced_wins": sum(r["winning_engine"] == "advanced" for r in rows),
        "legacy_recoveries": sum(r["winning_engine"] == "legacy" for r in rows),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Phase 18 two-engine portfolio: controlled ten-goal test",
        "",
        f"- Verified: {payload['verified']}/{payload['total']}",
        f"- Advanced wins: {payload['advanced_wins']}",
        f"- Legacy recoveries: {payload['legacy_recoveries']}",
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
