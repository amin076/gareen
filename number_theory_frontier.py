"""Lean-backed number-theory frontier for Gareen.

The legacy Python sandbox intentionally stays small.  Serious number-theory
research uses Lean/Mathlib's canonical meanings for division, divisibility,
remainder, gcd, coprimality, and primality.

This module exposes those concepts to Gareen's orchestration layer and provides
general (not ground-instance) frontier probes.  The probes are benchmarks and
vocabulary checks, not claims of novel mathematics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from lean_bridge import LeanBatchCandidate, LeanBatchVerificationResult, LeanBridge


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


def main() -> int:
    bridge = LeanBridge()
    if not bridge.available():
        print("Lean/Lake is unavailable.")
        return 2

    frontier = generate_number_theory_frontier()
    result = verify_number_theory_frontier(bridge)

    print("Gareen number-theory frontier")
    print("=============================")
    print("Vocabulary concepts:", len(NUMBER_THEORY_VOCABULARY))
    print("General probes:", len(frontier))
    print("Lean-verified probes:", result.verified_count)

    by_name = {item.theorem_name: item for item in result.results}
    for item in frontier:
        outcome = by_name[item.name]
        print(
            f"  - {item.name}: verified={outcome.verified} "
            f"tactic={outcome.tactic or '-'} role={item.role}"
        )

    core_names = {
        item.name
        for item in frontier
        if item.role == "core-vocabulary"
    }
    core_ok = all(by_name[name].verified for name in core_names)
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
