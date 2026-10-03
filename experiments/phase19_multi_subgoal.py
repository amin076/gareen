"""Phase 19.5 heterogeneous multi-subgoal orchestration benchmark.

The theorem deliberately combines two branches with different proof character:
1. a Fermat-style prime/power existential branch;
2. a divisibility-over-addition branch.

Gareen must split the conjunction, route the branches independently, allow its
own recursive prover to compete, and finally assemble the two accepted branch
proofs into one Lean-verified theorem.
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

from multi_subgoal_proof_planner import MultiSubgoalProofPlanner

NAME = "phase19_multi_provider"
STATEMENT = (
    "∀ p a d x y : Nat, "
    "Nat.Prime p → "
    "¬ p ∣ a → "
    "d ∣ x → "
    "d ∣ y → "
    "((∃ k : Nat, a ^ (p - 1) = k * p + 1) ∧ d ∣ x + y)"
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

    planner = MultiSubgoalProofPlanner(ROOT)
    started = time.monotonic()
    result = planner.prove(
        STATEMENT,
        theorem_name=NAME,
        total_budget_seconds=300,
    )

    payload = asdict(result)
    payload.update({
        "experiment_status": "completed",
        "theorem_status": "proved" if result.verified else "unproved",
        "hard_job_cap_minutes": 10,
        "proof_budget_seconds": 300,
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
        "- Proof budget: 300s",
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
