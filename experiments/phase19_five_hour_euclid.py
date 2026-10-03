"""Phase 19 long-horizon theorem-proving stress test.

Target: a strengthened Euclid theorem.

    ∀ n : Nat, 2 ≤ n →
      ∃ p : Nat, Nat.Prime p ∧ n < p ∧ Nat.gcd n p = 1

This combines the classical infinitude-of-primes theorem with an additional
coprimality obligation. It is deliberately not an open conjecture: the point is
to measure Gareen's proof orchestration, not to burn compute on an unsolved
mathematical problem.

The workflow permits up to five hours. The script itself keeps a safety margin
for setup and artifact upload.
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

ANCHOR_NAME = "euclid_anchor"
ANCHOR = "∀ n : Nat, ∃ p : Nat, Nat.Prime p ∧ n < p"

TARGET_NAME = "euclid_strengthened_coprime"
TARGET = (
    "∀ n : Nat, 2 ≤ n → ∃ p : Nat, "
    "Nat.Prime p ∧ n < p ∧ Nat.gcd n p = 1"
)

OUT = ROOT / ".gareen/phase19-five-hour-euclid.json"
MD = ROOT / ".gareen/phase19-five-hour-euclid.md"


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


def compact(result):
    return {
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
        "gareen_fallback": result.gareen_fallback,
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    require_lean_toolchain()

    # Quick sanity anchor: the classical infinitude-of-primes statement.
    anchor_planner = EcosystemStrategyPlanner(
        per_strategy_timeout=45,
        gareen_timeout=60,
        gareen_nodes=2500,
    )
    anchor = anchor_planner.prove(
        ANCHOR,
        theorem_name=ANCHOR_NAME,
        wall_clock_budget_seconds=240,
        stop_on_first_success=True,
        use_gareen_fallback=True,
    )
    print(json.dumps({
        "anchor_verified": anchor.verified,
        "anchor_winner": anchor.winning_strategy,
        "anchor_elapsed_seconds": anchor.elapsed_seconds,
    }, indent=2), flush=True)

    # Long-horizon target. Up to 15 minutes per ecosystem strategy and a much
    # larger recursive fallback budget. The overall script budget leaves ample
    # margin under the 5-hour GitHub job timeout for setup + evidence upload.
    planner = EcosystemStrategyPlanner(
        per_strategy_timeout=900,
        gareen_timeout=1200,
        gareen_nodes=100000,
    )
    target_started = time.monotonic()
    target = planner.prove(
        TARGET,
        theorem_name=TARGET_NAME,
        wall_clock_budget_seconds=13500,  # 3h45m before any fallback overrun
        stop_on_first_success=True,
        use_gareen_fallback=True,
    )
    target_elapsed = round(time.monotonic() - target_started, 3)

    payload = {
        "experiment": "phase19-five-hour-euclid",
        "experiment_status": "completed",
        "theorem_status": "proved" if target.verified else "unproved",
        "anchor_statement": ANCHOR,
        "anchor": compact(anchor),
        "target_statement": TARGET,
        "target": compact(target),
        "target_measured_elapsed_seconds": target_elapsed,
        "workflow_timeout_minutes": 300,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Phase 19 five-hour long-horizon theorem test",
        "",
        "## Sanity anchor",
        "",
        f"- Statement: `{ANCHOR}`",
        f"- Verified: {anchor.verified}",
        f"- Winner: {anchor.winning_strategy}",
        f"- Elapsed: {anchor.elapsed_seconds}s",
        "",
        "## Strengthened Euclid target",
        "",
        f"- Statement: `{TARGET}`",
        f"- Verified: {target.verified}",
        f"- Winner: {target.winning_strategy}",
        f"- Layer: {target.layer}",
        f"- Elapsed: {target_elapsed}s",
        "",
        "## Strategy attempts",
        "",
        "| Strategy | Verified | Timeout | Seconds |",
        "|---|---:|---:|---:|",
    ]
    for a in target.attempts:
        lines.append(
            f"| {a.strategy} | {a.verified} | {a.timed_out} | "
            f"{a.elapsed_seconds} |"
        )
    if target.gareen_fallback:
        lines.extend([
            "",
            "## Gareen recursive fallback",
            "",
            f"- Verified: {target.gareen_fallback['verified']}",
            f"- Winner: {target.gareen_fallback['winning_engine']}",
        ])
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "target_verified": target.verified,
        "target_winning_strategy": target.winning_strategy,
        "target_layer": target.layer,
        "target_elapsed_seconds": target_elapsed,
        "attempts": [
            {
                "strategy": a.strategy,
                "verified": a.verified,
                "timed_out": a.timed_out,
                "seconds": a.elapsed_seconds,
            }
            for a in target.attempts
        ],
        "gareen_fallback_verified": (
            target.gareen_fallback["verified"] if target.gareen_fallback else None
        ),
        "gareen_fallback_winner": (
            target.gareen_fallback["winning_engine"] if target.gareen_fallback else None
        ),
    }, indent=2), flush=True)

    print(
        "Experiment completed successfully. "
        f"Target theorem status: {'proved' if target.verified else 'unproved'}. "
        "An unproved target does not constitute a CI failure.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
