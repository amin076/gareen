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
from recursive_proof_planner import RecursiveProofPlanner

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
    memory = args.out.with_suffix('.memory.json')
    memory.unlink(missing_ok=True)
    new = RecursiveProofPlanner(timeout_seconds=30, memory_path=memory)
    # Negative controls are a fast soundness gate, not a theorem-proving
    # workload. Give them a smaller deterministic search envelope so a known
    # false statement cannot consume an entire per-goal wall-clock slot.
    control_memory = args.out.with_suffix('.control-memory.json')
    control_memory.unlink(missing_ok=True)
    controls_planner = RecursiveProofPlanner(
        timeout_seconds=30, max_nodes=400, max_candidates=32,
        memory_path=control_memory)
    old = LeanProofPlanner(timeout_seconds=30)
    if not new.available():
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
        r = controls_planner.prove(
            statement, theorem_name=f'false_{i}',
            wall_clock_budget_seconds=budget())
        controls.append(asdict(r)); save()
    for index, (group, name, statement) in enumerate(goals):
        r = new.prove(statement, theorem_name=name, wall_clock_budget_seconds=budget())
        row = {'group': group, 'name': name, 'statement': statement, 'recursive': asdict(r)}
        # Comparison cases are identical, with a fresh, independent proof process.
        if index < args.baseline_limit and budget() > 0:
            before = old.prove(statement, theorem_name=name + '_phase17',
                               wall_clock_budget_seconds=budget(), per_attempt_timeout_seconds=args.per_goal)
            row['phase17'] = asdict(before)
        rows.append(row); save()
        print(f'{name}: {r.status}, nodes={r.expanded_nodes}', flush=True)
    paired = [r for r in rows if 'phase17' in r]
    controls_sound = all(r['attempts'] and not r['verified'] for r in controls)
    controls_terminated = all(r['status'] == 'unproved-in-budget' for r in controls)
    payload['summary'] = {
        'total': len(rows), 'verified': sum(r['recursive']['verified'] for r in rows),
        'attempted': sum(bool(r['recursive']['attempts']) for r in rows),
        'controls_sound': controls_sound,
        'controls_terminated': controls_terminated,
        'controls_ok': controls_sound and controls_terminated,
        'paired': len(paired), 'phase17_verified': sum(r['phase17']['verified'] for r in paired),
        'phase18_paired_verified': sum(r['recursive']['verified'] for r in paired)}
    save()
    summary = payload['summary']
    lines = ['# Phase 18 benchmark', '', json.dumps(summary, indent=2), '',
             '| Goal | Group | Phase 17 | Phase 18 | Nodes |', '|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['name']} | {r['group']} | {r.get('phase17', {}).get('verified', 'not run')} | {r['recursive']['status']} | {r['recursive']['expanded_nodes']} |")
    args.out.with_suffix('.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    required = {'composition_00', 'composition_02', 'logic_and_branching_00'}
    solved = {r['name'] for r in rows if r['recursive']['verified']}
    return 0 if summary['controls_ok'] and required <= solved and summary['attempted'] == len(rows) else 1

if __name__ == '__main__':
    raise SystemExit(main())
