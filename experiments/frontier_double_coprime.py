"""Harder frontier theorem with an explicit anti-shortcut comparison.

Main theorem:
  ∀ n : Nat,
    Nat.gcd n (2 * n + 1) = 1 ∧
    Nat.gcd (n + 1) (2 * n + 1) = 1

The experiment compares:
1. Phase-17 style Lean/Mathlib retrieval planner (direct/introduced exact? and its
   small handwritten dvd-add schema).
2. The Phase-18.5 Gareen two-engine recursive-search portfolio.

This does not remove Mathlib: Gareen intentionally uses Mathlib as its theorem
library. The scientific question is whether Gareen's own recursive planner is
needed to select/compose multiple facts and branches, rather than a single
one-shot library lookup solving the whole statement.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lean_proof_planner import LeanProofPlanner
from portfolio_proof_planner import PortfolioProofPlanner

NAME = "frontier_double_coprime"
STATEMENT = (
    "∀ n : Nat, "
    "Nat.gcd n (2 * n + 1) = 1 ∧ "
    "Nat.gcd (n + 1) (2 * n + 1) = 1"
)

OUT = ROOT / ".gareen/frontier-double-coprime.json"
MD = ROOT / ".gareen/frontier-double-coprime.md"


def accepted_decls(engine: dict | None) -> list[str]:
    if not engine:
        return []
    return list(dict.fromkeys(
        e.get("declaration")
        for e in engine.get("proof_graph", [])
        if e.get("status") == "accepted" and e.get("declaration")
    ))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / ".gareen/portfolio-advanced-memory.json").unlink(missing_ok=True)

    baseline = LeanProofPlanner(timeout_seconds=45)
    portfolio = PortfolioProofPlanner(
        advanced_timeout=60,
        legacy_timeout=60,
        advanced_nodes=5000,
        legacy_nodes=5000,
    )

    t0 = time.monotonic()
    before = baseline.prove(
        STATEMENT,
        theorem_name=NAME + "_phase17",
        wall_clock_budget_seconds=90,
        per_attempt_timeout_seconds=30,
    )
    baseline_elapsed = round(time.monotonic() - t0, 3)

    t1 = time.monotonic()
    result = portfolio.prove(STATEMENT, theorem_name=NAME)
    portfolio_elapsed = round(time.monotonic() - t1, 3)

    advanced = result.advanced
    legacy = result.legacy
    decls = accepted_decls(advanced) + accepted_decls(legacy)
    decls = list(dict.fromkeys(decls))

    payload = {
        "name": NAME,
        "statement": STATEMENT,
        "baseline": {
            "verified": before.verified,
            "winning_strategy": before.winning_strategy,
            "elapsed_seconds": baseline_elapsed,
            "attempts": [asdict(a) for a in before.attempts],
        },
        "portfolio": {
            "verified": result.verified,
            "winning_engine": result.winning_engine,
            "elapsed_seconds": portfolio_elapsed,
            "advanced_status": advanced["status"],
            "advanced_nodes": advanced["expanded_nodes"],
            "legacy_status": legacy["status"] if legacy else "not-run",
            "legacy_nodes": legacy["expanded_nodes"] if legacy else 0,
            "accepted_declarations": decls,
            "advanced": advanced,
            "legacy": legacy,
        },
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Gareen frontier test: double coprimality around 2n+1",
        "",
        f"- Statement: `{STATEMENT}`",
        f"- Phase-17 retrieval baseline verified: {before.verified}",
        f"- Portfolio verified: {result.verified}",
        f"- Portfolio winner: {result.winning_engine}",
        f"- Advanced nodes: {advanced['expanded_nodes']}",
        f"- Legacy status: {legacy['status'] if legacy else 'not-run'}",
        f"- Baseline elapsed: {baseline_elapsed}s",
        f"- Portfolio elapsed: {portfolio_elapsed}s",
        "",
        "## Accepted declarations in Gareen recursive proof",
    ]
    if decls:
        lines.extend(f"- `{d}`" for d in decls)
    else:
        lines.append("- none recorded")
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "statement": STATEMENT,
        "baseline_verified": before.verified,
        "baseline_winning_strategy": before.winning_strategy,
        "baseline_elapsed_seconds": baseline_elapsed,
        "portfolio_verified": result.verified,
        "portfolio_winning_engine": result.winning_engine,
        "portfolio_elapsed_seconds": portfolio_elapsed,
        "advanced_status": advanced["status"],
        "advanced_nodes": advanced["expanded_nodes"],
        "legacy_status": legacy["status"] if legacy else "not-run",
        "legacy_nodes": legacy["expanded_nodes"] if legacy else 0,
        "accepted_declarations": decls,
    }, indent=2), flush=True)

    # The frontier experiment is scientifically strongest if Gareen succeeds.
    # Baseline success/failure is reported rather than used as the CI gate.
    return 0 if result.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
