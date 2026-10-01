"""Lean-backed number-theory frontier for Gareen.

The legacy Python sandbox intentionally stays small. Serious number-theory
research uses Lean/Mathlib's canonical meanings for division, divisibility,
remainder, gcd, coprimality, and primality.

Phase 17 adds a second proving layer for selected structural goals:
generic tactics are tried first; unresolved planner-benchmark goals are then
sent to Gareen's theorem-retrieval / proof-planning layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from lean_bridge import LeanBatchCandidate, LeanBatchVerificationResult, LeanBridge
from lean_proof_planner import LeanProofPlanner, PlannedProofResult


@dataclass(frozen=True)
class NumberTheoryConcept:
    name: str
    lean_syntax: str
    kind: str
    meaning: str


NUMBER_THEORY_VOCABULARY = (
    NumberTheoryConcept(
        "divides",
        "a ∣ b",
        "relation",
        "There exists c with b = a * c.",
    ),
    NumberTheoryConcept(
        "quotient",
        "n / d",
        "function",
        "Natural-number quotient.",
    ),
    NumberTheoryConcept(
        "remainder",
        "n % d",
        "function",
        "Natural-number remainder.",
    ),
    NumberTheoryConcept(
        "gcd",
        "Nat.gcd a b",
        "function",
        "Greatest common divisor.",
    ),
    NumberTheoryConcept(
        "coprime",
        "Nat.Coprime a b",
        "predicate",
        "The gcd of a and b is 1.",
    ),
    NumberTheoryConcept(
        "prime",
        "Nat.Prime p",
        "predicate",
        "p is a natural prime.",
    ),
)


@dataclass(frozen=True)
class NumberTheoryFrontierCandidate:
    name: str
    statement: str
    concepts: tuple[str, ...]
    role: str


@dataclass(frozen=True)
class NumberTheoryPlannerRecovery:
    candidate_name: str
    result: PlannedProofResult


def generate_number_theory_frontier() -> tuple[NumberTheoryFrontierCandidate, ...]:
    """General vocabulary probes for the enlarged research domain."""

    return (
        NumberTheoryFrontierCandidate(
            "nt_one_divides_all",
            "∀ n : Nat, 1 ∣ n",
            ("divides",),
            "core-vocabulary",
        ),
        NumberTheoryFrontierCandidate(
            "nt_self_divides",
            "∀ n : Nat, n ∣ n",
            ("divides",),
            "core-vocabulary",
        ),
        NumberTheoryFrontierCandidate(
            "nt_div_one",
            "∀ n : Nat, n / 1 = n",
            ("quotient",),
            "core-vocabulary",
        ),
        NumberTheoryFrontierCandidate(
            "nt_mod_one",
            "∀ n : Nat, n % 1 = 0",
            ("remainder",),
            "core-vocabulary",
        ),
        NumberTheoryFrontierCandidate(
            "nt_two_prime",
            "Nat.Prime 2",
            ("prime",),
            "core-vocabulary",
        ),
        NumberTheoryFrontierCandidate(
            "nt_division_algorithm",
            "∀ n d : Nat, n % d + d * (n / d) = n",
            ("quotient", "remainder"),
            "structural-benchmark",
        ),
        NumberTheoryFrontierCandidate(
            "nt_gcd_divides_left",
            "∀ a b : Nat, Nat.gcd a b ∣ a",
            ("gcd", "divides"),
            "structural-benchmark",
        ),
        NumberTheoryFrontierCandidate(
            "nt_gcd_divides_right",
            "∀ a b : Nat, Nat.gcd a b ∣ b",
            ("gcd", "divides"),
            "structural-benchmark",
        ),
        NumberTheoryFrontierCandidate(
            "nt_coprime_symmetric",
            "∀ a b : Nat, Nat.Coprime a b ↔ Nat.Coprime b a",
            ("coprime", "gcd"),
            "structural-benchmark",
        ),
        NumberTheoryFrontierCandidate(
            "nt_divides_transitive",
            "∀ a b c : Nat, a ∣ b → b ∣ c → a ∣ c",
            ("divides",),
            "structural-benchmark",
        ),
        NumberTheoryFrontierCandidate(
            "nt_gcd_divides_sum",
            "∀ a b : Nat, Nat.gcd a b ∣ a + b",
            ("gcd", "divides", "addition"),
            "planner-benchmark",
        ),
    )


def verify_number_theory_frontier(
    bridge: Optional[LeanBridge] = None,
) -> LeanBatchVerificationResult:
    verifier = bridge or LeanBridge(timeout_seconds=60)
    frontier = generate_number_theory_frontier()
    return verifier.verify_batch(
        tuple(
            LeanBatchCandidate(
                theorem_name=item.name,
                formula=item.statement,
            )
            for item in frontier
        ),
        tactics=("simp", "norm_num", "omega", "aesop"),
        batch_size=16,
        round_timeout_seconds=30,
    )


def recover_planner_benchmarks(
    generic_result: LeanBatchVerificationResult,
    *,
    planner: Optional[LeanProofPlanner] = None,
    wall_clock_budget_seconds: float = 180.0,
) -> tuple[NumberTheoryPlannerRecovery, ...]:
    """Run theorem retrieval/planning only on unresolved planner benchmarks."""

    engine = planner or LeanProofPlanner(timeout_seconds=60)
    frontier = generate_number_theory_frontier()
    by_name = {
        item.theorem_name: item
        for item in generic_result.results
    }
    recoveries: list[NumberTheoryPlannerRecovery] = []

    planner_targets = [
        item
        for item in frontier
        if item.role == "planner-benchmark"
        and not by_name[item.name].verified
    ]
    if not planner_targets:
        return ()

    per_target_budget = max(
        30.0,
        wall_clock_budget_seconds / len(planner_targets),
    )
    for item in planner_targets:
        result = engine.prove(
            item.statement,
            theorem_name=item.name + "_planned",
            wall_clock_budget_seconds=per_target_budget,
            per_attempt_timeout_seconds=60,
        )
        recoveries.append(
            NumberTheoryPlannerRecovery(
                candidate_name=item.name,
                result=result,
            )
        )

    return tuple(recoveries)


def main() -> int:
    bridge = LeanBridge()
    if not bridge.available():
        print("Lean/Lake is unavailable.")
        return 2

    frontier = generate_number_theory_frontier()
    result = verify_number_theory_frontier(bridge)
    recoveries = recover_planner_benchmarks(result)
    recovery_by_name = {
        item.candidate_name: item.result
        for item in recoveries
    }

    print("Gareen number-theory frontier")
    print("=============================")
    print("Vocabulary concepts:", len(NUMBER_THEORY_VOCABULARY))
    print("General probes:", len(frontier))
    print("Generic-tactic verified probes:", result.verified_count)

    by_name = {item.theorem_name: item for item in result.results}
    for item in frontier:
        outcome = by_name[item.name]
        planner_result = recovery_by_name.get(item.name)
        print(
            f"  - {item.name}: generic={outcome.verified} "
            f"tactic={outcome.tactic or '-'} role={item.role} "
            f"planner={planner_result.verified if planner_result else '-'}"
        )
        if planner_result is not None:
            print(
                "      planner strategy:",
                planner_result.winning_strategy or "-",
            )
            print(
                "      retrieved:",
                planner_result.retrieved_constants or "-",
            )

    core_names = {
        item.name
        for item in frontier
        if item.role == "core-vocabulary"
    }
    core_ok = all(by_name[name].verified for name in core_names)

    planner_names = {
        item.name
        for item in frontier
        if item.role == "planner-benchmark"
    }
    planner_ok = all(
        by_name[name].verified
        or (
            name in recovery_by_name
            and recovery_by_name[name].verified
        )
        for name in planner_names
    )

    print("Core vocabulary healthy:", core_ok)
    print("Planner benchmark healthy:", planner_ok)
    return 0 if core_ok and planner_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
