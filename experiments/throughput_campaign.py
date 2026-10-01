"""High-throughput time-boxed Gareen research benchmark.

This is a research benchmark, not a claim of novel mathematics.

It intentionally reuses the Phase 15 workload shape from the first 15-minute
experiment while sending candidates to Lean in batches. Candidate generation
is target-free; finite sample agreement only proposes conjectures. Lean remains
the acceptance authority.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lean_bridge import LeanBatchCandidate, LeanBridge
from math_world import (
    Add,
    Eq,
    Expr,
    ForAll,
    Mul,
    ONE,
    Succ,
    Var,
    X,
    ZERO,
    free_vars_expr,
    normalize,
    substitute_expr,
)


def numeral(value: int) -> Expr:
    result: Expr = ZERO
    for _ in range(value):
        result = Succ(result)
    return result


def expr_size(expr: Expr) -> int:
    if isinstance(expr, (Var, type(ZERO))):
        return 1
    if isinstance(expr, Succ):
        return 1 + expr_size(expr.value)
    if isinstance(expr, (Add, Mul)):
        return 1 + expr_size(expr.left) + expr_size(expr.right)
    return 1


def operator_count(expr: Expr) -> int:
    if isinstance(expr, Succ):
        return 1 + operator_count(expr.value)
    if isinstance(expr, (Add, Mul)):
        return 1 + operator_count(expr.left) + operator_count(expr.right)
    return 0


def contains_mul(expr: Expr) -> bool:
    if isinstance(expr, Mul):
        return True
    if isinstance(expr, Succ):
        return contains_mul(expr.value)
    if isinstance(expr, Add):
        return contains_mul(expr.left) or contains_mul(expr.right)
    return False


def direct_rewrite_equivalent(left: Expr, right: Expr) -> bool:
    try:
        left_normal, _ = normalize(left, max_steps=500)
        right_normal, _ = normalize(right, max_steps=500)
    except RuntimeError:
        return False
    return left_normal == right_normal


def generate_expressions(
    *,
    max_size: int,
    per_size_cap: int,
) -> tuple[Expr, ...]:
    by_size: dict[int, tuple[Expr, ...]] = {
        1: (ZERO, X),
    }

    for size in range(2, max_size + 1):
        generated: set[Expr] = set()

        for child in by_size.get(size - 1, ()):
            generated.add(Succ(child))

        for left_size in range(1, size - 1):
            right_size = size - 1 - left_size
            for left in by_size.get(left_size, ()):
                for right in by_size.get(right_size, ()):
                    generated.add(Add(left, right))
                    generated.add(Mul(left, right))

        ordered = sorted(
            generated,
            key=lambda expr: (
                operator_count(expr),
                str(expr),
            ),
        )
        by_size[size] = tuple(ordered[:per_size_cap])

    expressions: list[Expr] = []
    seen: set[Expr] = set()
    for size in sorted(by_size):
        for expr in by_size[size]:
            if X not in free_vars_expr(expr) or expr in seen:
                continue
            seen.add(expr)
            expressions.append(expr)

    return tuple(expressions)


def observation_signature(
    expr: Expr,
    samples: tuple[Expr, ...],
) -> tuple[str, ...] | None:
    outputs: list[str] = []
    try:
        for sample in samples:
            grounded = substitute_expr(expr, X, sample)
            normalized, _ = normalize(grounded, max_steps=5000)
            outputs.append(str(normalized))
    except (RuntimeError, RecursionError):
        return None
    return tuple(outputs)


@dataclass(frozen=True)
class Candidate:
    left: Expr
    right: Expr
    signature: tuple[str, ...]
    score: int
    rewrite_trivial: bool

    @property
    def statement(self) -> ForAll:
        return ForAll(X, Eq(self.left, self.right))


def build_candidates(
    expressions: tuple[Expr, ...],
    *,
    samples: tuple[Expr, ...],
    max_candidates: int,
    pairs_per_class: int,
) -> tuple[Candidate, ...]:
    groups: dict[tuple[str, ...], list[Expr]] = defaultdict(list)

    for expr in expressions:
        signature = observation_signature(expr, samples)
        if signature is not None:
            groups[signature].append(expr)

    candidates: list[Candidate] = []
    seen: set[tuple[str, str]] = set()

    viable = [
        (signature, sorted(items, key=lambda item: (expr_size(item), str(item))))
        for signature, items in groups.items()
        if len(items) >= 2
    ]
    viable.sort(key=lambda item: (len(item[1]), item[0]), reverse=True)

    for signature, items in viable:
        emitted = 0
        for i, left in enumerate(items):
            for right in items[i + 1 :]:
                key = tuple(sorted((str(left), str(right))))
                if key in seen:
                    continue
                seen.add(key)

                score = (
                    operator_count(left)
                    + operator_count(right)
                    + (4 if contains_mul(left) or contains_mul(right) else 0)
                    + abs(expr_size(left) - expr_size(right))
                )
                candidates.append(
                    Candidate(
                        left=left,
                        right=right,
                        signature=signature,
                        score=score,
                        rewrite_trivial=direct_rewrite_equivalent(left, right),
                    )
                )
                emitted += 1
                if emitted >= pairs_per_class:
                    break
                if len(candidates) >= max_candidates:
                    break
            if emitted >= pairs_per_class or len(candidates) >= max_candidates:
                break
        if len(candidates) >= max_candidates:
            break

    # Phase 15 ranking: nontrivial candidates first, then structurally richer
    # ones. The hash only stabilizes ties across runs.
    candidates.sort(
        key=lambda item: (
            1 if item.rewrite_trivial else 0,
            -item.score,
            sha256(str(item.statement).encode("utf-8")).hexdigest()[:8],
        )
    )
    return tuple(candidates)


def false_controls() -> tuple[LeanBatchCandidate, ...]:
    return (
        LeanBatchCandidate(
            theorem_name="false_successor_identity",
            formula=ForAll(X, Eq(Add(X, ONE), X)),
        ),
        LeanBatchCandidate(
            theorem_name="false_zero_mul_one",
            formula=ForAll(X, Eq(Mul(X, ZERO), ONE)),
        ),
    )


@dataclass(frozen=True)
class CampaignRecord:
    index: int
    statement: str
    attempted: bool
    verified: bool
    tactic: str | None
    score: int
    rewrite_trivial: bool
    error: str


def run_campaign(
    *,
    seconds: int,
    max_size: int,
    per_size_cap: int,
    sample_count: int,
    max_candidates: int,
    pairs_per_class: int,
    batch_size: int,
    json_out: Path,
    markdown_out: Path,
) -> int:
    started = time.monotonic()

    samples = tuple(numeral(i) for i in range(sample_count))
    expressions = generate_expressions(
        max_size=max_size,
        per_size_cap=per_size_cap,
    )
    candidates = build_candidates(
        expressions,
        samples=samples,
        max_candidates=max_candidates,
        pairs_per_class=pairs_per_class,
    )

    bridge = LeanBridge(timeout_seconds=45)
    tactics = ("simp", "omega", "ring", "norm_num", "nlinarith")

    generation_elapsed = time.monotonic() - started
    remaining_budget = max(1.0, seconds - generation_elapsed)

    print("Gareen high-throughput autonomous campaign")
    print("==========================================")
    print("Budget seconds:", seconds)
    print("Generation elapsed seconds:", round(generation_elapsed, 3))
    print("Generated expressions:", len(expressions))
    print("Generated pattern candidates:", len(candidates))
    print("Sample count:", sample_count)
    print("Batch size:", batch_size)

    control_result = bridge.verify_batch(
        false_controls(),
        tactics=tactics,
        batch_size=8,
        round_timeout_seconds=15,
        wall_clock_budget_seconds=min(60.0, remaining_budget),
    )
    controls_ok = (
        control_result.attempted_count == len(false_controls())
        and control_result.verified_count == 0
    )
    print("False controls rejected correctly:", controls_ok)

    elapsed_after_controls = time.monotonic() - started
    remaining_budget = max(1.0, seconds - elapsed_after_controls)

    batch_candidates = tuple(
        LeanBatchCandidate(
            theorem_name=f"campaign_{index:05d}",
            formula=candidate.statement,
        )
        for index, candidate in enumerate(candidates, start=1)
    )
    result = bridge.verify_batch(
        batch_candidates,
        tactics=tactics,
        batch_size=batch_size,
        round_timeout_seconds=45,
        wall_clock_budget_seconds=remaining_budget,
    )

    result_by_name = {
        item.theorem_name: item
        for item in result.results
    }
    records: list[CampaignRecord] = []
    tactic_counts: Counter[str] = Counter()

    for index, candidate in enumerate(candidates, start=1):
        name = f"campaign_{index:05d}"
        item = result_by_name[name]
        if item.verified and item.tactic is not None:
            tactic_counts[item.tactic] += 1

        records.append(
            CampaignRecord(
                index=index,
                statement=item.statement,
                attempted=item.attempted,
                verified=item.verified,
                tactic=item.tactic,
                score=candidate.score,
                rewrite_trivial=candidate.rewrite_trivial,
                error=item.error,
            )
        )

    elapsed = time.monotonic() - started
    attempted_records = [item for item in records if item.attempted]
    verified_records = [item for item in attempted_records if item.verified]
    unproved_records = [
        item
        for item in attempted_records
        if not item.verified
    ]
    budget_skipped = [item for item in records if not item.attempted]

    payload = {
        "budget_seconds": seconds,
        "elapsed_seconds": round(elapsed, 3),
        "generation_elapsed_seconds": round(generation_elapsed, 3),
        "generated_expressions": len(expressions),
        "generated_candidates": len(candidates),
        "attempted_candidates": len(attempted_records),
        "verified_candidates": len(verified_records),
        "unproved_in_budget": len(unproved_records),
        "budget_skipped_candidates": len(budget_skipped),
        "verification_rate_among_attempted": (
            round(len(verified_records) / len(attempted_records), 4)
            if attempted_records
            else 0.0
        ),
        "false_controls_rejected": controls_ok,
        "process_invocations": (
            control_result.process_invocations + result.process_invocations
        ),
        "candidate_process_invocations": result.process_invocations,
        "batch_verification_elapsed_seconds": round(
            result.elapsed_seconds,
            3,
        ),
        "tactic_counts": dict(tactic_counts),
        "sample_count": sample_count,
        "max_expression_size": max_size,
        "per_size_cap": per_size_cap,
        "pairs_per_pattern_class": pairs_per_class,
        "batch_size": batch_size,
        "records": [asdict(record) for record in records],
    }

    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    first_verified = verified_records[:20]
    first_unproved = unproved_records[:10]
    markdown = [
        "# Gareen Phase 15 throughput benchmark",
        "",
        f"- Budget: {seconds} seconds",
        f"- Actual elapsed: {elapsed:.1f} seconds",
        f"- Generated expressions: {len(expressions)}",
        f"- Generated candidates: {len(candidates)}",
        f"- Attempted candidates: {len(attempted_records)}",
        f"- Lean-verified candidates: {len(verified_records)}",
        f"- Unproved in budget: {len(unproved_records)}",
        f"- Budget-skipped candidates: {len(budget_skipped)}",
        f"- Lean process invocations: {payload['process_invocations']}",
        f"- False controls rejected correctly: {controls_ok}",
        f"- Tactics used: {dict(tactic_counts)}",
        "",
        "## First verified candidates",
        "",
    ]
    markdown.extend(
        f"- `{item.statement}` — tactic: `{item.tactic}`"
        for item in first_verified
    )
    markdown.extend(
        [
            "",
            "## First unproved-in-budget candidates",
            "",
        ]
    )
    markdown.extend(
        f"- `{item.statement}`"
        for item in first_unproved
    )
    markdown_out.write_text("\n".join(markdown) + "\n", encoding="utf-8")

    print("")
    print("Campaign summary")
    print("----------------")
    print("Elapsed seconds:", round(elapsed, 3))
    print("Attempted candidates:", len(attempted_records))
    print("Lean-verified candidates:", len(verified_records))
    print("Unproved in current budget:", len(unproved_records))
    print("Budget-skipped candidates:", len(budget_skipped))
    print("Lean process invocations:", payload["process_invocations"])
    print("False controls rejected correctly:", controls_ok)
    print("Tactic counts:", dict(tactic_counts))
    print("JSON:", json_out)
    print("Markdown:", markdown_out)

    return 0 if controls_ok and attempted_records else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=900)
    parser.add_argument("--max-size", type=int, default=9)
    parser.add_argument("--per-size-cap", type=int, default=260)
    parser.add_argument("--samples", type=int, default=6)
    parser.add_argument("--max-candidates", type=int, default=20000)
    parser.add_argument("--pairs-per-class", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=96)
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path(".gareen/campaign-15m-v2.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(".gareen/campaign-15m-v2.md"),
    )
    args = parser.parse_args()

    return run_campaign(
        seconds=max(1, args.seconds),
        max_size=max(2, args.max_size),
        per_size_cap=max(10, args.per_size_cap),
        sample_count=max(2, args.samples),
        max_candidates=max(1, args.max_candidates),
        pairs_per_class=max(1, args.pairs_per_class),
        batch_size=max(1, args.batch_size),
        json_out=args.json_out,
        markdown_out=args.markdown_out,
    )


if __name__ == "__main__":
    raise SystemExit(main())
