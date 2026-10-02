"""Fixed 50-goal ladder. Difficulty labels are workload groups, not novelty claims.

Both planners receive identical goals and per-goal wall-clock limits. Negative
controls are separate from success-rate denominators. A failed search is never
reported as a disproof. Memory is isolated between benchmark planners/runs.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lean_proof_planner import LeanProofPlanner
from portfolio_proof_planner import PortfolioProofPlanner

GROUPS = {
 'routine': [
  '∀ n : Nat, n = n', '∀ n : Nat, n + 0 = n', '∀ n : Nat, 0 + n = n',
  '∀ n : Nat, n * 1 = n', '∀ n : Nat, 1 * n = n', '∀ n : Nat, n * 0 = 0',
  '∀ n : Nat, 1 ∣ n', '∀ n : Nat, n ∣ n', '∀ n : Nat, n / 1 = n', 'Nat.Prime 2'],
 'library': [
  '∀ a b : Nat, Nat.gcd a b ∣ a', '∀ a b : Nat, Nat.gcd a b ∣ b',
  '∀ a b : Nat, Nat.gcd a b = Nat.gcd b a',
  '∀ a b : Nat, Nat.Coprime a b → Nat.Coprime b a',
  '∀ a b : Nat, a ∣ Nat.lcm a b', '∀ a b : Nat, b ∣ Nat.lcm a b',
  '∀ a b c : Nat, a ∣ b → b ∣ c → a ∣ c',
  '∀ d a b : Nat, d ∣ a → d ∣ b → d ∣ a + b',
  '∀ a b : Nat, a + b = b + a', '∀ a b : Nat, a * b = b * a'],
 'composition': [
  '∀ a b : Nat, Nat.gcd a b ∣ a + b',
  '∀ a b : Nat, Nat.gcd a b ∣ b + a',
  '∀ a b : Nat, Nat.gcd a b ∣ a + (a + b)',
  '∀ a b : Nat, Nat.gcd a b ∣ (a + b) + b',
  '∀ a b : Nat, Nat.gcd a b ∣ (a + b) + (b + a)',
  '∀ a b c : Nat, Nat.gcd a b ∣ a * c',
  '∀ a b c : Nat, Nat.gcd a b ∣ b * c',
  '∀ a b c : Nat, Nat.gcd a b ∣ a * c + b',
  '∀ a b c : Nat, Nat.gcd a b ∣ a + b * c',
  '∀ a b m n : Nat, Nat.gcd a b ∣ a * m + b * n'],
 'logic_and_branching': [
  '∀ P Q : Prop, P → Q → P ∧ Q',
  '∀ P Q : Prop, P ∧ Q → Q ∧ P',
  '∀ P Q R : Prop, (P → Q) → (Q → R) → P → R',
  '∀ P Q : Prop, P → P ∨ Q', '∀ P Q : Prop, Q → P ∨ Q',
  '∀ P Q R : Prop, P → Q → R → P ∧ (Q ∧ R)',
  '∀ a b : Nat, Nat.gcd a b ∣ a ∧ Nat.gcd a b ∣ b',
  '∀ a b : Nat, Nat.gcd a b ∣ a + b ∧ Nat.gcd a b ∣ b + a',
  '∀ d a b c : Nat, d ∣ a → d ∣ b → d ∣ c → d ∣ a + (b + c)',
  '∀ d a b c : Nat, d ∣ a → d ∣ b → d ∣ c → d ∣ (a + b) + c'],
 'challenge': [
  '∀ a b : Nat, Nat.gcd a b ∣ (a + b) * (a + b)',
  '∀ a b : Nat, Nat.gcd a b ∣ a * a + b * b',
  '∀ a b : Nat, Nat.gcd a b ∣ (a + b) + ((a + b) + (a + b))',
  '∀ d a b m n : Nat, d ∣ a → d ∣ b → d ∣ a * m + b * n',
  '∀ a b c : Nat, a ∣ b → b ∣ c → a ∣ b + c',
  '∀ a b c : Nat, a ∣ b → b ∣ c → a ∣ c + b',
  '∀ p a b : Nat, Nat.Prime p → p ∣ a * b → p ∣ a ∨ p ∣ b',
  '∀ a b : Nat, Nat.Coprime a b → Nat.gcd a b = 1',
  '∀ n d : Nat, n % d + d * (n / d) = n',
  '∀ a b c : Nat, Nat.gcd a b ∣ a * c + b * c']}

FALSE_CONTROLS = ['∀ a b : Nat, Nat.gcd a b ∣ 1',
                  '∀ n : Nat, n + 1 = n', '∀ P Q : Prop, P → Q']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seconds', type=float, default=900)
    p.add_argument('--per-goal', type=float, default=25)
    p.add_argument('--limit', type=int, default=50)
    p.add_argument('--baseline-limit', type=int, default=10)
    p.add_argument('--out', type=Path, default=ROOT / '.gareen/phase18-benchmark.json')
    args = p.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Phase 18.5 official benchmark uses the two-engine cascade.
    # Engine A is the current advanced recursive planner; Engine B is the
    # frozen legacy Phase 18 planner. The legacy engine runs only when A does
    # not verify the theorem.
    portfolio = PortfolioProofPlanner(
        advanced_timeout=args.per_goal,
        legacy_timeout=args.per_goal,
        advanced_nodes=1200,
        legacy_nodes=1200,
    )
    # False controls use smaller node budgets but the same two-engine trust
    # boundary. More wall-clock headroom is allowed because startup/elaboration
    # can dominate tiny false goals; no false theorem may verify.
    control_portfolio = PortfolioProofPlanner(
        advanced_timeout=max(args.per_goal, 35),
        legacy_timeout=max(args.per_goal, 35),
        advanced_nodes=400,
        legacy_nodes=400,
    )
    old = LeanProofPlanner(timeout_seconds=30)
    if not portfolio.advanced.available():
        print('Lean unavailable: benchmark NOT executed')
        return 2
    # Interleave groups so a global time limit does not test only easy goals.
    goals = [(group, f'{group}_{i:02}', GROUPS[group][i])
             for i in range(10) for group in GROUPS][:args.limit]
    started = time.monotonic()
    rows, controls = [], []
    payload = {'version': 1, 'baseline': 'Phase 17', 'rows': rows, 'controls': controls}
    def save():
        payload['elapsed_seconds'] = round(time.monotonic() - started, 3)
        args.out.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    def budget(): return max(0, min(args.per_goal, args.seconds - (time.monotonic() - started)))
    # Controls first, so exhaustion cannot skip the soundness checks unnoticed.
    for i, statement in enumerate(FALSE_CONTROLS):
        if budget() <= 0:
            break
        r = control_portfolio.prove(statement, theorem_name=f'false_{i}')
        controls.append(asdict(r)); save()
    for index, (group, name, statement) in enumerate(goals):
        if budget() <= 0:
            break
        r = portfolio.prove(statement, theorem_name=name)
        advanced = r.advanced
        legacy = r.legacy
        combined_nodes = advanced['expanded_nodes'] + (legacy['expanded_nodes'] if legacy else 0)
        row = {
            'group': group,
            'name': name,
            'statement': statement,
            'portfolio': asdict(r),
            # Backward-compatible summary field for existing evidence readers.
            'recursive': {
                'verified': r.verified,
                'status': 'verified' if r.verified else 'unproved-in-portfolio',
                'expanded_nodes': combined_nodes,
                'winning_engine': r.winning_engine,
            },
        }
        # Comparison cases are identical, with a fresh, independent proof process.
        if index < args.baseline_limit and budget() > 0:
            before = old.prove(statement, theorem_name=name + '_phase17',
                               wall_clock_budget_seconds=budget(), per_attempt_timeout_seconds=args.per_goal)
            row['phase17'] = asdict(before)
        rows.append(row); save()
        print(
            f"{name}: {'verified' if r.verified else 'unproved'}, "
            f"winner={r.winning_engine}, nodes={combined_nodes}",
            flush=True,
        )
    paired = [r for r in rows if 'phase17' in r]
    controls_sound = (
        len(controls) == len(FALSE_CONTROLS)
        and all(not r['verified'] for r in controls)
    )
    # In portfolio mode a false control is considered cleanly terminated when
    # neither engine verifies it and at least one attempted engine returns a
    # bounded non-timeout unproved result. A timeout in one engine is allowed
    # only if the complementary engine terminates cleanly.
    def clean_control(r):
        engines = [r.get('advanced')] + ([r.get('legacy')] if r.get('legacy') else [])
        return (not r['verified']) and any(
            e and e.get('status') == 'unproved-in-budget' for e in engines
        )
    controls_terminated = (
        len(controls) == len(FALSE_CONTROLS)
        and all(clean_control(r) for r in controls)
    )
    payload['summary'] = {
        'total': len(rows),
        'verified': sum(r['recursive']['verified'] for r in rows),
        'attempted': len(rows),
        'advanced_wins': sum(r['portfolio']['winning_engine'] == 'advanced' for r in rows),
        'legacy_recoveries': sum(r['portfolio']['winning_engine'] == 'legacy' for r in rows),
        'controls_sound': controls_sound,
        'controls_terminated': controls_terminated,
        'controls_ok': controls_sound and controls_terminated,
        'paired': len(paired),
        'phase17_verified': sum(r['phase17']['verified'] for r in paired),
        'phase18_paired_verified': sum(r['recursive']['verified'] for r in paired)}
    save()
    summary = payload['summary']
    lines = ['# Phase 18.5 portfolio benchmark', '', json.dumps(summary, indent=2), '',
             '| Goal | Group | Phase 17 | Portfolio | Winner | Nodes |',
             '|---|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['name']} | {r['group']} | {r.get('phase17', {}).get('verified', 'not run')} | {r['recursive']['status']} | {r['recursive'].get('winning_engine', '-')} | {r['recursive']['expanded_nodes']} |")
    args.out.with_suffix('.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    return 0 if (
        summary['controls_ok']
        and summary['attempted'] == len(goals)
        and summary['verified'] == len(goals)
    ) else 1

if __name__ == '__main__':
    raise SystemExit(main())
