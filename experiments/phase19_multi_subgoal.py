"""Phase 19.5 heterogeneous multi-subgoal orchestration benchmark.

The theorem deliberately combines two branches with different proof character:
1. a monotone-arithmetic branch expected to be handled by a standard tactic;
2. a divisibility-over-addition branch routed first to Gareen's recursive prover.

The experiment also runs an unsplit ecosystem-only baseline first.  The key
success condition is that the direct whole-theorem baseline does not verify,
while split routing proves both branches with different providers and the final
assembled theorem passes Lean's axiom audit.
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
from multi_subgoal_proof_planner import MultiSubgoalProofPlanner

NAME = "phase19_multi_provider"
STATEMENT = (
    "∀ d a b m n : Nat, "
    "d ∣ a → "
    "d ∣ b → "
    "m ≤ n → "
    "((m + 7 ≤ n + 7) ∧ d ∣ a + b)"
)

OUT = ROOT / ".gareen/phase19-multi-subgoal.json"
MD = ROOT / ".gareen/phase19-multi-subgoal.md"


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
        raise RuntimeError(
            "Lean infrastructure failure: lake env lean --version failed: "
            + (probe.stderr or probe.stdout)
        )


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    require_lean_toolchain()

    started = time.monotonic()

    # Control: try the whole conjunction without Gareen recursive fallback.
    # If this succeeds directly, subgoal routing did not add evidence.
    baseline_planner = EcosystemStrategyPlanner(
        ROOT,
        per_strategy_timeout=8,
        gareen_timeout=20,
        gareen_nodes=1200,
    )
    baseline = baseline_planner.prove(
        STATEMENT,
        theorem_name=NAME + "_baseline",
        wall_clock_budget_seconds=55,
        stop_on_first_success=True,
        use_gareen_fallback=False,
    )

    planner = MultiSubgoalProofPlanner(ROOT)
    result = planner.prove(
        STATEMENT,
        theorem_name=NAME,
        total_budget_seconds=180,
    )

    payload = asdict(result)
    payload.update({
        "direct_baseline_verified": baseline.verified,
        "direct_baseline_strategy": baseline.winning_strategy,
        "direct_baseline_layer": baseline.layer,
        "direct_baseline_elapsed_seconds": baseline.elapsed_seconds,
        "experiment_status": "completed",
        "theorem_status": "proved" if result.verified else "unproved",
        "hard_job_cap_minutes": 10,
        "proof_budget_seconds": 235,
        "experiment_elapsed_seconds": round(time.monotonic() - started, 3),
    })
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Phase 19.5 heterogeneous multi-subgoal benchmark",
        "",
        f"- Statement: `{STATEMENT}`",
        f"- Verified: {result.verified}",
        f"- Theorem status: {payload['theorem_status']}",
        f"- Total elapsed: {result.elapsed_seconds}s",
        "- GitHub job hard cap: 10 minutes",
        "- Total proof budget: 235s (55s direct baseline + 180s split routing)",
        f"- Direct baseline verified: {baseline.verified}",
        f"- Direct baseline winner: {baseline.winning_strategy or '-'}",
        f"- Direct baseline layer: {baseline.layer or '-'}",
        "",
        "## Routed branches",
        "",
        "| Branch | Verified | Provider | Strategy | Seconds |",
        "|---|---:|---|---|---:|",
    ]
    for b in result.branches:
        lines.append(
            f"| {b.name} | {b.verified} | {b.provider or '-'} | "
            f"{b.strategy or '-'} | {b.elapsed_seconds} |"
        )
    lines.extend([
        "",
        "## Final assembly",
        "",
        f"- Source: {result.assembly_source_path or '-'}",
        f"- Return code: {result.assembly_returncode}",
        f"- Final Lean verification: {result.verified}",
    ])
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "verified": result.verified,
        "direct_baseline_verified": baseline.verified,
        "direct_baseline_strategy": baseline.winning_strategy,
        "direct_baseline_layer": baseline.layer,
        "theorem_status": payload["theorem_status"],
        "elapsed_seconds": result.elapsed_seconds,
        "branches": [
            {
                "name": b.name,
                "verified": b.verified,
                "provider": b.provider,
                "strategy": b.strategy,
                "seconds": b.elapsed_seconds,
            }
            for b in result.branches
        ],
        "assembly_returncode": result.assembly_returncode,
    }, indent=2), flush=True)

    print(
        "Experiment completed. "
        f"Theorem status: {payload['theorem_status']}. "
        "An unproved theorem is not a CI infrastructure failure.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
