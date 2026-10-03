"""Phase 19 ecosystem-first retest of the first failed frontier theorem.

This reuses the exact theorem that defeated:
- Phase 17 retrieval baseline,
- Phase 18.5 advanced recursive search,
- Phase 18.5 frozen legacy fallback.

The goal is to determine whether established Lean/Mathlib proof strategies solve
it before Gareen's custom recursive engines are invoked.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ecosystem_strategy_planner import EcosystemStrategyPlanner

NAME = "phase19_double_coprime"
STATEMENT = (
    "∀ n : Nat, "
    "Nat.gcd n (2 * n + 1) = 1 ∧ "
    "Nat.gcd (n + 1) (2 * n + 1) = 1"
)

OUT = ROOT / ".gareen/phase19-double-coprime.json"
MD = ROOT / ".gareen/phase19-double-coprime.md"


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
        per_strategy_timeout=25,
        gareen_timeout=60,
        gareen_nodes=5000,
    )
    result = planner.prove(
        STATEMENT,
        theorem_name=NAME,
        wall_clock_budget_seconds=360,
        stop_on_first_success=True,
    )

    payload = asdict(result)
    payload["experiment_status"] = "completed"
    payload["theorem_status"] = "proved" if result.verified else "unproved"
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Phase 19 ecosystem-first retest",
        "",
        f"- Statement: `{STATEMENT}`",
        f"- Verified: {result.verified}",
        f"- Winning strategy: {result.winning_strategy}",
        f"- Winning layer: {result.layer}",
        f"- Total elapsed: {result.elapsed_seconds}s",
        "",
        "## Strategy attempts",
        "",
        "| Strategy | Verified | Timeout | Seconds |",
        "|---|---:|---:|---:|",
    ]
    for attempt in result.attempts:
        lines.append(
            f"| {attempt.strategy} | {attempt.verified} | "
            f"{attempt.timed_out} | {attempt.elapsed_seconds} |"
        )
    if result.gareen_fallback:
        lines.extend([
            "",
            "## Gareen recursive fallback",
            "",
            f"- Verified: {result.gareen_fallback['verified']}",
            f"- Winner: {result.gareen_fallback['winning_engine']}",
        ])
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "verified": result.verified,
        "winning_strategy": result.winning_strategy,
        "winning_layer": result.layer,
        "elapsed_seconds": result.elapsed_seconds,
        "attempts": [
            {
                "strategy": a.strategy,
                "verified": a.verified,
                "timed_out": a.timed_out,
                "seconds": a.elapsed_seconds,
            }
            for a in result.attempts
        ],
        "gareen_fallback_verified": (
            result.gareen_fallback["verified"]
            if result.gareen_fallback else None
        ),
        "gareen_fallback_winner": (
            result.gareen_fallback["winning_engine"]
            if result.gareen_fallback else None
        ),
    }, indent=2), flush=True)

    print(
        "Experiment completed successfully. "
        f"Theorem status: {'proved' if result.verified else 'unproved'}. "
        "An unproved theorem does not constitute a CI failure.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
