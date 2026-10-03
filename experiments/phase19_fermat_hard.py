"""Phase 19.3 hard Fermat-style benchmark.

Test a composed form of Fermat's little theorem rather than a direct named
Mathlib statement:

    for prime p and p not dividing a,
    there exists k : Nat with a^(p-1) = k*p + 1.

This is equivalent to saying a^(p-1) has remainder 1 modulo p, but the
existential quotient form forces proof composition instead of merely accepting
the modulo statement as the final goal.

The experiment is evidence-first:
- theorem unproved => experiment still completes successfully;
- only infrastructure failures should make CI red;
- GitHub job has a hard 10-minute cap;
- internal proof budget is 300 seconds, leaving setup/artifact margin.
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

NAME = "phase19_fermat_composed"
STATEMENT = (
    "∀ p a : Nat, "
    "Nat.Prime p → "
    "¬ p ∣ a → "
    "∃ k : Nat, a ^ (p - 1) = k * p + 1"
)

OUT = ROOT / ".gareen/phase19-fermat-hard.json"
MD = ROOT / ".gareen/phase19-fermat-hard.md"


def require_lean_toolchain() -> None:
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
        per_strategy_timeout=20,
        gareen_timeout=45,
        gareen_nodes=5000,
    )

    started = time.monotonic()
    result = planner.prove(
        STATEMENT,
        theorem_name=NAME,
        wall_clock_budget_seconds=300,
        stop_on_first_success=True,
        use_gareen_fallback=True,
    )

    payload = asdict(result)
    payload.update({
        "experiment_status": "completed",
        "theorem_status": "proved" if result.verified else "unproved",
        "benchmark": "fermat-little-theorem-composed-existential",
        "hard_job_cap_minutes": 10,
        "proof_budget_seconds": 300,
        "experiment_elapsed_seconds": round(time.monotonic() - started, 3),
    })
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Phase 19.3 hard Fermat-style benchmark",
        "",
        f"- Statement: `{STATEMENT}`",
        "- Experiment status: completed",
        f"- Theorem status: {payload['theorem_status']}",
        f"- Verified: {result.verified}",
        f"- Winning strategy: {result.winning_strategy or '-'}",
        f"- Winning layer: {result.layer or '-'}",
        f"- Planner elapsed: {result.elapsed_seconds}s",
        "- Proof budget: 300s",
        "- GitHub job hard cap: 10 minutes",
        "",
        "## Ecosystem attempts",
        "",
        "| Strategy | Outcome | Verified | Timeout | Seconds |",
        "|---|---|---:|---:|---:|",
    ]
    for a in result.attempts:
        lines.append(
            f"| {a.strategy} | {a.outcome} | {a.verified} | "
            f"{a.timed_out} | {a.elapsed_seconds} |"
        )

    if result.gareen_fallback:
        lines.extend([
            "",
            "## Gareen recursive fallback",
            "",
            f"- Verified: {result.gareen_fallback['verified']}",
            f"- Winner: {result.gareen_fallback['winning_engine'] or '-'}",
            f"- Elapsed: {result.gareen_fallback['elapsed_seconds']}s",
        ])

    MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "statement": STATEMENT,
        "verified": result.verified,
        "winning_strategy": result.winning_strategy,
        "winning_layer": result.layer,
        "elapsed_seconds": result.elapsed_seconds,
        "theorem_status": payload["theorem_status"],
    }, indent=2), flush=True)

    print(
        "Experiment completed. "
        f"Theorem status: {payload['theorem_status']}. "
        "An unproved theorem is a mathematical experiment result, not a CI failure.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
