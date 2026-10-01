"""Time-boxed autonomous Gareen research campaign.

This experiment is intentionally not a claim of novel mathematics.
It measures how many target-free conjectures Gareen can generate and send
through Lean verification within a fixed wall-clock budget.

Pipeline:
  symbolic grammar
    -> finite observations
    -> equivalence-pattern conjectures
    -> Lean proof attempts
    -> verified/rejected research records

The campaign includes a few deliberately false controls to confirm that
the verification path rejects invalid statements.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Iterable

from lean_bridge import LeanBridge
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


def generate_expressions(
    *,
    max_size: int,
    per_size_cap: int,
) -> tuple[Expr, ...]:
    """Enumerate a bounded unary arithmetic grammar without theorem targets."""

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

    variable_expressions: list[Expr] = []
    seen: set[Expr] = set()
    for size in sorted(by_size):
        for expr in by_size[size]:
            if X not in free_vars_expr(expr):
                continue
            if expr in seen:
                continue
            seen.add(expr)
            variable_expressions.append(expr)

    return tuple(variable_expressions)


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

    # Spread candidate generation across pattern classes instead of allowing
    # one giant trivial class to dominate the experiment.
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

    # Deterministic but varied ordering: simple candidates are not the only
    # things tested first. The digest keeps runs reproducible.
    candidates.sort(
        key=lambda item: (
            sha256(str(item.statement).encode("utf-8")).hexdigest()[:8],
            -item.score,
        )
    )
    return tuple(candidates)


@dataclass
class CampaignRecord:
    index: int
    statement: str
    verified: bool
    tactic: str | None
    attempts: int
    score: int
    elapsed_seconds: float
    error: str


def false_controls() -> tuple[tuple[str, ForAll], ...]:
    return (
        (
            "false_successor_identity",
            ForAll(X, Eq(Add(X, ONE), X)),
        ),
        (
            "false_zero_mul_one",
            ForAll(X, Eq(Mul(X, ZERO), ONE)),
        ),
    )


def run_campaign(
    *,
    seconds: int,
    max_size: int,
    per_size_cap: int,
    sample_count: int,
    max_candidates: int,
    pairs_per_class: int,
    json_out: Path,
    markdown_out: Path,
) -> int:
    start = time.monotonic()
    deadline = start + seconds

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

    bridge = LeanBridge(timeout_seconds=5)
    tactic_portfolio = ("simp", "omega", "ring")

    print("Gareen autonomous campaign")
    print("==========================")
    print("Budget seconds:", seconds)
    print("Generated expressions:", len(expressions))
    print("Generated pattern candidates:", len(candidates))
    print("Sample count:", sample_count)

    control_results: list[dict] = []
    for name, statement in false_controls():
        if time.monotonic() >= deadline:
            break
        result = bridge.verify_formula(
            statement,
            theorem_name=name,
            tactics=tactic_portfolio,
        )
        control_results.append(
            {
                "name": name,
                "statement": result.statement,
                "verified": result.verified,
                "tactic": result.tactic,
                "attempts": len(result.attempts),
                "error": result.error,
            }
        )
        print(
            f"Control {name}: verified={result.verified} "
            f"(expected False)"
        )

    records: list[CampaignRecord] = []
    tactic_counts: Counter[str] = Counter()
    verified = 0
    rejected = 0

    for index, candidate in enumerate(candidates, start=1):
        if time.monotonic() >= deadline:
            break

        name = f"campaign_{index:05d}"
        result = bridge.verify_formula(
            candidate.statement,
            theorem_name=name,
            tactics=tactic_portfolio,
        )

        if result.verified:
            verified += 1
            tactic_counts[result.tactic or "unknown"] += 1
        else:
            rejected += 1

        records.append(
            CampaignRecord(
                index=index,
                statement=result.statement,
                verified=result.verified,
                tactic=result.tactic,
                attempts=len(result.attempts),
                score=candidate.score,
                elapsed_seconds=round(time.monotonic() - start, 3),
                error=result.error,
            )
        )

        if index % 25 == 0:
            print(
                f"progress attempted={len(records)} "
                f"verified={verified} rejected={rejected} "
                f"elapsed={time.monotonic() - start:.1f}s"
            )

    elapsed = time.monotonic() - start
    controls_ok = bool(control_results) and all(
        not item["verified"] for item in control_results
    )

    result_payload = {
        "budget_seconds": seconds,
        "elapsed_seconds": round(elapsed, 3),
        "generated_expressions": len(expressions),
        "generated_candidates": len(candidates),
        "attempted_candidates": len(records),
        "verified_candidates": verified,
        "rejected_candidates": rejected,
        "verification_rate": (
            round(verified / len(records), 4) if records else 0.0
        ),
        "false_controls_rejected": controls_ok,
        "false_controls": control_results,
        "tactic_counts": dict(tactic_counts),
        "sample_count": sample_count,
        "max_expression_size": max_size,
        "per_size_cap": per_size_cap,
        "pairs_per_pattern_class": pairs_per_class,
        "records": [asdict(record) for record in records],
    }

    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(result_payload, indent=2),
        encoding="utf-8",
    )

    first_verified = [record for record in records if record.verified][:20]
    first_rejected = [record for record in records if not record.verified][:10]

    markdown_lines = [
        "# Gareen 15-minute autonomous campaign",
        "",
        f"- Budget: {seconds} seconds",
        f"- Actual elapsed: {elapsed:.1f} seconds",
        f"- Generated expressions: {len(expressions)}",
        f"- Generated pattern candidates: {len(candidates)}",
        f"- Attempted candidates: {len(records)}",
        f"- Lean-verified candidates: {verified}",
        f"- Rejected candidates: {rejected}",
        f"- False controls rejected correctly: {controls_ok}",
        f"- Tactics used: {dict(tactic_counts)}",
        "",
        "## First verified candidates",
        "",
    ]
    markdown_lines.extend(
        f"- `{record.statement}` — tactic: `{record.tactic}`"
        for record in first_verified
    )
    markdown_lines.extend(
        [
            "",
            "## First rejected candidates",
            "",
        ]
    )
    markdown_lines.extend(
        f"- `{record.statement}`"
        for record in first_rejected
    )
    markdown_out.write_text(
        "\n".join(markdown_lines) + "\n",
        encoding="utf-8",
    )

    print("")
    print("Campaign summary")
    print("----------------")
    print("Elapsed seconds:", round(elapsed, 3))
    print("Attempted candidates:", len(records))
    print("Lean-verified candidates:", verified)
    print("Rejected candidates:", rejected)
    print("False controls rejected correctly:", controls_ok)
    print("Tactic counts:", dict(tactic_counts))
    print("JSON:", json_out)
    print("Markdown:", markdown_out)

    # A verification campaign should fail loudly if the invalid controls pass.
    return 0 if controls_ok and records else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=900)
    parser.add_argument("--max-size", type=int, default=9)
    parser.add_argument("--per-size-cap", type=int, default=260)
    parser.add_argument("--samples", type=int, default=6)
    parser.add_argument("--max-candidates", type=int, default=20000)
    parser.add_argument("--pairs-per-class", type=int, default=80)
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path(".gareen/campaign-15m.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(".gareen/campaign-15m.md"),
    )
    args = parser.parse_args()

    return run_campaign(
        seconds=max(1, args.seconds),
        max_size=max(2, args.max_size),
        per_size_cap=max(10, args.per_size_cap),
        sample_count=max(2, args.samples),
        max_candidates=max(1, args.max_candidates),
        pairs_per_class=max(1, args.pairs_per_class),
        json_out=args.json_out,
        markdown_out=args.markdown_out,
    )


if __name__ == "__main__":
    raise SystemExit(main())
