"""Phase 19 lean-auto integration validation.

Tests three diagnostically important goals:
1. Euclid anchor that native ecosystem strategy search previously missed.
2. Simple divisibility composition that ecosystem-only 4/5 diagnostic missed.
3. Hard double-coprime frontier theorem that all current strategies missed.

The same ecosystem orchestrator is used, now with lean-auto activated first.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ecosystem_strategy_planner import EcosystemStrategyPlanner

GOALS = [
    (
        "auto_euclid_anchor",
        "∀ n : Nat, ∃ p : Nat, Nat.Prime p ∧ n < p",
    ),
    (
        "auto_divisibility",
        "∀ d a b : Nat, d ∣ a → d ∣ b → d ∣ a + b",
    ),
    (
        "auto_double_coprime",
        "∀ n : Nat, Nat.gcd n (2 * n + 1) = 1 ∧ Nat.gcd (n + 1) (2 * n + 1) = 1",
    ),
]

OUT = ROOT / ".gareen/phase19-lean-auto-validation.json"
MD = ROOT / ".gareen/phase19-lean-auto-validation.md"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    planner = EcosystemStrategyPlanner(
        per_strategy_timeout=90,
        gareen_timeout=120,
        gareen_nodes=10000,
    )

    rows = []
    started = time.monotonic()
    for name, statement in GOALS:
        result = planner.prove(
            statement,
            theorem_name=name,
            wall_clock_budget_seconds=600,
            stop_on_first_success=True,
            use_gareen_fallback=True,
        )
        rows.append({
            "name": name,
            "statement": statement,
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
            "gareen_fallback": result.gareen_fallback,
        })
        OUT.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
        print(
            f"{name}: verified={result.verified}, winner={result.winning_strategy}, "
            f"layer={result.layer}, elapsed={result.elapsed_seconds}s",
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
        "# Phase 19 lean-auto validation",
        "",
        f"- Verified: {payload['verified']}/{payload['total']}",
        f"- Elapsed: {payload['elapsed_seconds']}s",
        "",
        "| Goal | Verified | Winner | Layer | Seconds |",
        "|---|---:|---|---|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['name']} | {r['verified']} | {r['winning_strategy'] or '-'} | "
            f"{r['layer'] or '-'} | {r['elapsed_seconds']} |"
        )
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(payload, indent=2), flush=True)
    return 0 if payload["verified"] == payload["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
