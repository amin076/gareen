"""Prepared 30-minute Gareen GCD proof trial.

This experiment tests the CURRENT Gareen/Lean proving setup on one elementary
but genuinely multi-step number-theory target:

    forall a b : Nat, Nat.gcd a b ∣ a + b

The trial deliberately gives no hand-written lemma hints for the primary goal.
It records every tactic attempt, elapsed time, return code, stdout/stderr, and
whether Lean accepted the proof.

A known-easy positive control and a false control are included so the run tells
us whether the verification pipeline is functioning and conservative.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
import time

from lean_bridge import render_theorem_source


PRIMARY_NAME = "gareen_gcd_divides_sum"
PRIMARY_STATEMENT = "∀ a b : Nat, Nat.gcd a b ∣ a + b"

POSITIVE_CONTROL_NAME = "control_gcd_divides_left"
POSITIVE_CONTROL_STATEMENT = "∀ a b : Nat, Nat.gcd a b ∣ a"

FALSE_CONTROL_NAME = "control_false_gcd_divides_one"
FALSE_CONTROL_STATEMENT = "∀ a b : Nat, Nat.gcd a b ∣ 1"

TACTICS = (
    "simp",
    "norm_num",
    "omega",
    "ring",
    "nlinarith",
    "aesop",
    "simp_ring",
    "simp_nlinarith",
)


@dataclass
class AttemptLog:
    theorem_name: str
    statement: str
    tactic: str
    started_after_seconds: float
    elapsed_seconds: float
    returncode: int
    timed_out: bool
    stdout: str
    stderr: str
    verified: bool


@dataclass
class TrialResult:
    name: str
    statement: str
    verified: bool
    winning_tactic: str | None
    status: str
    attempts: list[AttemptLog]


def _run_one(
    *,
    repo_root: Path,
    theorem_name: str,
    statement: str,
    tactics: tuple[str, ...],
    trial_started: float,
    deadline: float,
    per_tactic_timeout: int,
) -> TrialResult:
    attempts: list[AttemptLog] = []
    generated = repo_root / ".gareen" / "gcd_trial"
    generated.mkdir(parents=True, exist_ok=True)

    for tactic in tactics:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break

        source = render_theorem_source(
            statement,
            theorem_name=theorem_name,
            tactic=tactic,
        )
        path = generated / f"{theorem_name}_{tactic}.lean"
        path.write_text(source, encoding="utf-8")
        rel = path.relative_to(repo_root)

        started = time.monotonic()
        timeout = max(1.0, min(float(per_tactic_timeout), remaining))
        timed_out = False
        try:
            completed = subprocess.run(
                ["lake", "env", "lean", str(rel)],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            rc = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            rc = 124
            stdout = exc.stdout or ""
            stderr = (exc.stderr or "") + "\nLean attempt timed out."

        elapsed = time.monotonic() - started
        verified = rc == 0
        attempts.append(
            AttemptLog(
                theorem_name=theorem_name,
                statement=statement,
                tactic=tactic,
                started_after_seconds=round(started - trial_started, 3),
                elapsed_seconds=round(elapsed, 3),
                returncode=rc,
                timed_out=timed_out,
                stdout=stdout,
                stderr=stderr,
                verified=verified,
            )
        )

        if verified:
            return TrialResult(
                name=theorem_name,
                statement=statement,
                verified=True,
                winning_tactic=tactic,
                status="lean-verified",
                attempts=attempts,
            )

    budget_exhausted = time.monotonic() >= deadline
    return TrialResult(
        name=theorem_name,
        statement=statement,
        verified=False,
        winning_tactic=None,
        status=(
            "unproved-budget-exhausted"
            if budget_exhausted
            else "unproved-strategies-exhausted"
        ),
        attempts=attempts,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=1800)
    parser.add_argument("--per-tactic-timeout", type=int, default=180)
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path(".gareen/gcd-proof-trial.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(".gareen/gcd-proof-trial.md"),
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    started = time.monotonic()
    deadline = started + max(60, args.seconds)

    # Small controls use only a subset and a short timeout so the research
    # budget remains focused on the primary target.
    positive = _run_one(
        repo_root=repo_root,
        theorem_name=POSITIVE_CONTROL_NAME,
        statement=POSITIVE_CONTROL_STATEMENT,
        tactics=("simp", "aesop"),
        trial_started=started,
        deadline=min(deadline, time.monotonic() + 90),
        per_tactic_timeout=45,
    )
    false_control = _run_one(
        repo_root=repo_root,
        theorem_name=FALSE_CONTROL_NAME,
        statement=FALSE_CONTROL_STATEMENT,
        tactics=("simp", "omega", "aesop"),
        trial_started=started,
        deadline=min(deadline, time.monotonic() + 90),
        per_tactic_timeout=30,
    )

    primary = _run_one(
        repo_root=repo_root,
        theorem_name=PRIMARY_NAME,
        statement=PRIMARY_STATEMENT,
        tactics=TACTICS,
        trial_started=started,
        deadline=deadline,
        per_tactic_timeout=max(10, args.per_tactic_timeout),
    )

    elapsed = time.monotonic() - started
    controls_ok = positive.verified and not false_control.verified

    payload = {
        "budget_seconds": args.seconds,
        "elapsed_seconds": round(elapsed, 3),
        "primary_target": PRIMARY_STATEMENT,
        "controls_ok": controls_ok,
        "positive_control": asdict(positive),
        "false_control": asdict(false_control),
        "primary": asdict(primary),
    }

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Gareen GCD proof trial",
        "",
        f"- Budget: {args.seconds} seconds",
        f"- Actual elapsed: {elapsed:.1f} seconds",
        f"- Controls healthy: {controls_ok}",
        f"- Positive control: {positive.status}",
        f"- False control: {false_control.status}",
        f"- Primary target: `{PRIMARY_STATEMENT}`",
        f"- Primary status: {primary.status}",
        f"- Winning tactic: {primary.winning_tactic or '-'}",
        f"- Primary attempts: {len(primary.attempts)}",
        "",
        "## Primary attempt log",
        "",
    ]
    for attempt in primary.attempts:
        lines.append(
            f"- `{attempt.tactic}`: rc={attempt.returncode}, "
            f"elapsed={attempt.elapsed_seconds}s, "
            f"timeout={attempt.timed_out}, verified={attempt.verified}"
        )
    args.markdown_out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    print(f"JSON log: {args.json_out}")
    print(f"Markdown log: {args.markdown_out}")

    # The experiment itself is considered operationally healthy if controls
    # behaved correctly, even if the primary theorem remains unproved.
    return 0 if controls_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
