"""Audit Gareen's mathematical research-value filter without invoking Lean."""

from __future__ import annotations

from collections import Counter

from artificial_mathematician import generate_research_conjectures
from math_world import build_initial_knowledge
from research_value import rank_research_conjectures


def _reason_class(reason: str) -> str:
    if "ground numerical" in reason:
        return "ground-example"
    if "primitive arithmetic rewrites" in reason:
        return "primitive-rewrite"
    if "too close to existing verified knowledge" in reason:
        return "short-known-consequence"
    if "threshold" in reason:
        return "low-score"
    return "accepted"


def main() -> int:
    state = build_initial_knowledge()
    conjectures = generate_research_conjectures(state)
    ranked = rank_research_conjectures(
        conjectures,
        state,
        min_reasoning_steps=3,
        min_score=14,
    )

    accepted = [item for item in ranked if item.assessment.accepted]
    filtered = [item for item in ranked if not item.assessment.accepted]
    reasons = Counter(_reason_class(item.assessment.reason) for item in ranked)

    print("Gareen Phase 16 research-value audit")
    print("====================================")
    print("Generated conjectures:", len(conjectures))
    print("Research-worthy:", len(accepted))
    print("Filtered low-value:", len(filtered))
    print("Reason counts:", dict(reasons))

    print("\nTop research-worthy candidates:")
    for item in accepted[:10]:
        print(
            "  -",
            item.conjecture.statement,
            f"[value={item.assessment.score}, "
            f"reuse={item.assessment.reuse_potential}, "
            f"distance={item.assessment.known_derivation_distance}]",
        )

    print("\nExamples filtered as routine:")
    for item in filtered[:10]:
        print(
            "  -",
            item.conjecture.statement,
            f"[{item.assessment.reason}]",
        )

    return 0 if conjectures else 1


if __name__ == "__main__":
    raise SystemExit(main())
