"""Before/after retest for Gareen Phase 17 theorem retrieval.

The mathematical target is intentionally identical to the failed Phase-16
trial:

    ∀ a b : Nat, Nat.gcd a b ∣ a + b

The script first reruns the old generic-tactic baseline and then invokes the
new theorem-retrieval/planning layer. Full attempts and Mathlib suggestions are
saved so a success or failure remains auditable.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lean_bridge import LeanBatchCandidate, LeanBridge
from lean_proof_planner import LeanProofPlanner


PRIMARY_NAME = "gareen_gcd_divides_sum"
PRIMARY_STATEMENT = "∀ a b : Nat, Nat.gcd a b ∣ a + b"

POSITIVE_NAME = "control_gcd_divides_left"
POSITIVE_STATEMENT = "∀ a b : Nat, Nat.gcd a b ∣ a"

FALSE_NAME = "control_false_gcd_divides_one"
FALSE_STATEMENT = "∀ a b : Nat, Nat.gcd a b ∣ 1"

BASELINE_TACTICS = (
    "simp",
    "norm_num",
    "omega",
    "ring",
    "nlinarith",
    "aesop",
    "simp_ring",
    "simp_nlinarith",
)


def _baseline(bridge: LeanBridge, *, seconds: float) -> dict:
    result = bridge.verify_batch(
        (
            LeanBatchCandidate(
                theorem_name=PRIMARY_NAME + "_baseline",
                formula=PRIMARY_STATEMENT,
            ),
        ),
        tactics=BASELINE_TACTICS,
        batch_size=1,
        round_timeout_seconds=45,
        wall_clock_budget_seconds=seconds,
    )
    item = result.results[0]
    return {
        "verified": item.verified,
        "tactic": item.tactic,
        "attempted": item.attempted,
        "error": item.error,
        "process_invocations": result.process_invocations,
        "elapsed_seconds": round(result.elapsed_seconds, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path(".gareen/gcd-proof-retake.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(".gareen/gcd-proof-retake.md"),
    )
    args = parser.parse_args()

    started = time.monotonic()
    budget = max(120, args.seconds)

    bridge = LeanBridge(timeout_seconds=60)
    planner = LeanProofPlanner(timeout_seconds=90)

    baseline_budget = min(180.0, budget * 0.30)
    baseline = _baseline(bridge, seconds=baseline_budget)

    elapsed = time.monotonic() - started
    remaining = max(30.0, budget - elapsed)

    positive = planner.prove(
        POSITIVE_STATEMENT,
        theorem_name=POSITIVE_NAME,
        wall_clock_budget_seconds=min(120.0, remaining),
        per_attempt_timeout_seconds=60,
    )
    elapsed = time.monotonic() - started
    remaining = max(30.0, budget - elapsed)

    false_control = planner.prove(
        FALSE_STATEMENT,
        theorem_name=FALSE_NAME,
        wall_clock_budget_seconds=min(120.0, remaining),
        per_attempt_timeout_seconds=60,
    )
    elapsed = time.monotonic() - started
    remaining = max(30.0, budget - elapsed)

    primary = planner.prove(
        PRIMARY_STATEMENT,
        theorem_name=PRIMARY_NAME,
        wall_clock_budget_seconds=remaining,
        per_attempt_timeout_seconds=90,
    )

    elapsed = time.monotonic() - started
    controls_ok = positive.verified and not false_control.verified
    improved = (not baseline["verified"]) and primary.verified

    payload = {
        "budget_seconds": budget,
        "elapsed_seconds": round(elapsed, 3),
        "target": PRIMARY_STATEMENT,
        "baseline": baseline,
        "positive_control": asdict(positive),
        "false_control": asdict(false_control),
        "planner": asdict(primary),
        "controls_ok": controls_ok,
        "improved_over_baseline": improved,
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Gareen GCD proof retake — Phase 17",
        "",
        f"- Target: `{PRIMARY_STATEMENT}`",
        f"- Budget: {budget} seconds",
        f"- Actual elapsed: {elapsed:.1f} seconds",
        f"- Old generic-tactic baseline verified: {baseline['verified']}",
        f"- Positive control verified: {positive.verified}",
        f"- False control verified (expected False): {false_control.verified}",
        f"- Controls healthy: {controls_ok}",
        f"- New planner verified target: {primary.verified}",
        f"- Winning strategy: {primary.winning_strategy or '-'}",
        f"- Retrieved constants: {', '.join(primary.retrieved_constants) or '-'}",
        f"- Improved over old baseline: {improved}",
        "",
        "## Planner attempts",
        "",
    ]

    for attempt in primary.attempts:
        lines.append(
            f"- `{attempt.strategy}`: verified={attempt.verified}, "
            f"rc={attempt.returncode}, elapsed={attempt.elapsed_seconds}s, "
            f"retrieved={', '.join(attempt.retrieved_constants) or '-'}"
        )
        for suggestion in attempt.suggestions:
            lines.append(f"  - suggestion: `{suggestion}`")

    args.markdown_out.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print("\n".join(lines))
    print("JSON log:", args.json_out)
    print("Markdown log:", args.markdown_out)

    return 0 if controls_ok and primary.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
