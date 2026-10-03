"""Phase 19.6 dynamic proof-state orchestration benchmark.

The decomposition is executed inside Lean. Gareen reads the actual subgoals
emitted by Gareen.ProofStateProbe, routes them independently, assembles the
proof, and requires final Lean axiom audit success.
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

from dynamic_proof_state_planner import DynamicProofStatePlanner
from ecosystem_strategy_planner import EcosystemStrategyPlanner

NAME = "phase19_dynamic_state"
STATEMENT = (
    "∀ d a b m n : Nat, "
    "d ∣ a → "
    "d ∣ b → "
    "m ≤ n → "
    "((m + 7 ≤ n + 7) ∧ d ∣ a + b)"
)

OUT = ROOT / ".gareen/phase19-dynamic-proof-state.json"
MD = ROOT / ".gareen/phase19-dynamic-proof-state.md"


def require_lean_toolchain() -> None:
    if shutil.which("lake") is None:
        raise RuntimeError("Lean infrastructure failure: lake not on PATH")
    probe = subprocess.run(
        ["lake", "env", "lean", "--version"], cwd=ROOT,
        capture_output=True, text=True, timeout=30, check=False,
    )
    if probe.returncode != 0:
        raise RuntimeError("Lean infrastructure failure: " + (probe.stderr or probe.stdout))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    require_lean_toolchain()
    started = time.monotonic()

    baseline = EcosystemStrategyPlanner(
        ROOT, per_strategy_timeout=8, gareen_timeout=20, gareen_nodes=1200
    ).prove(
        STATEMENT, theorem_name=NAME + "_baseline",
        wall_clock_budget_seconds=55, stop_on_first_success=True,
        use_gareen_fallback=False,
    )

    planner = DynamicProofStatePlanner(ROOT)
    result = planner.prove(
        STATEMENT, theorem_name=NAME, total_budget_seconds=180
    )

    payload = asdict(result)
    payload.update({
        "experiment_status": "completed",
        "theorem_status": "proved" if result.verified else "unproved",
        "direct_baseline_verified": baseline.verified,
        "direct_baseline_strategy": baseline.winning_strategy,
        "direct_baseline_layer": baseline.layer,
        "direct_baseline_elapsed_seconds": baseline.elapsed_seconds,
        "proof_budget_seconds": 235,
        "hard_job_cap_minutes": 10,
        "experiment_elapsed_seconds": round(time.monotonic() - started, 3),
    })
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Phase 19.6 dynamic Lean proof-state orchestration",
        "",
        f"- Statement: `{STATEMENT}`",
        f"- Direct baseline verified: {baseline.verified}",
        f"- Direct baseline strategy: {baseline.winning_strategy or '-'}",
        f"- Dynamic verified: {result.verified}",
        f"- Decomposition tactic: {result.decomposition_tactic or '-'}",
        f"- Lean-emitted subgoals: {len(result.probed_subgoals)}",
        f"- Total dynamic elapsed: {result.elapsed_seconds}s",
        "",
        "## Lean-emitted proof states",
        "",
    ]
    for s in result.probed_subgoals:
        lines.append(f"- Subgoal {s.index}: `{s.target}`")
    lines.extend([
        "",
        "## Routed branches",
        "",
        "| Branch | Verified | Provider | Strategy | Seconds |",
        "|---|---:|---|---|---:|",
    ])
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
        "direct_baseline_verified": baseline.verified,
        "verified": result.verified,
        "decomposition_tactic": result.decomposition_tactic,
        "subgoals": [s.target for s in result.probed_subgoals],
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
        "elapsed_seconds": result.elapsed_seconds,
    }, indent=2), flush=True)

    print(
        "Experiment completed. "
        f"Theorem status: {payload['theorem_status']}. "
        "Unproved is not a CI infrastructure failure.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
