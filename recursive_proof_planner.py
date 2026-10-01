"""Phase 18 orchestration for Lean-native recursive backward search.

Memory is a ranking hint, never evidence. Every result is rebuilt and audited by
Lean. Reports keep unsuccessful branches as well as the accepted proof path.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from lean_proof_planner import LeanProofPlanner, PlannedProofResult, PlannerAttempt, _safe_identifier

_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*$")
_AXIOMS = re.compile(r"depends on axioms:\s*\[([^]]*)\]", re.S)


def validate_statement(statement: str) -> str:
    """Native proposition input is not an arbitrary Lean source-file interface."""
    s = statement.strip()
    if not s or any(x in s for x in ('\n', '\r', ':=', ';', '--', '/-', '-/', '#', '"')):
        raise ValueError('Expected one Lean proposition, not declarations or commands')
    if re.search(r'\b(by|sorry|admit|axiom|theorem|def|namespace|end|import|set_option|where)\b', s):
        raise ValueError('Declarations and proof terms are not accepted as goal input')
    return s


def parse_events(output: str) -> tuple[dict, ...]:
    events = []
    for line in output.splitlines():
        if 'GAREEN_EVENT ' in line:
            try:
                item = json.loads(line.split('GAREEN_EVENT ', 1)[1])
                if isinstance(item, dict) and {'id', 'parent', 'goal', 'rule', 'status'} <= item.keys():
                    events.append(item)
            except (ValueError, TypeError):
                pass
    return tuple(events)


def audited(output: str, returncode: int) -> bool:
    matches = _AXIOMS.findall(output)
    if 'does not depend on any axioms' in output:
        matches.append('')
    if returncode != 0 or len(matches) != 1 or 'declaration uses' in output:
        return False
    axioms = {a.strip() for a in matches[0].split(',') if a.strip()}
    return axioms <= {'propext', 'Classical.choice', 'Quot.sound'}


@dataclass(frozen=True)
class RecursiveResult(PlannedProofResult):
    proof_graph: tuple[dict, ...] = ()
    expanded_nodes: int = 0
    status: str = 'unproved-in-budget'
    memory_hints: tuple[str, ...] = ()


class RecursiveProofPlanner(LeanProofPlanner):
    def __init__(self, repo_root=None, *, max_depth=6, max_nodes=1200,
                 max_candidates=48, memory_path=None, **kwargs):
        super().__init__(repo_root, **kwargs)
        if not (0 <= max_depth <= 32 and 1 <= max_nodes <= 100000 and 1 <= max_candidates <= 512):
            raise ValueError('Invalid recursive search bounds')
        self.max_depth, self.max_nodes, self.max_candidates = max_depth, max_nodes, max_candidates
        self.memory_path = Path(memory_path) if memory_path else self.repo_root / '.gareen/proof-memory.json'

    def _hints(self):
        try:
            data = json.loads(self.memory_path.read_text(encoding='utf-8'))
            scores = data.get('lemmas', {})
            return tuple(k for k, v in sorted(scores.items(), key=lambda p: (-p[1], p[0]))
                         if _NAME.fullmatch(k) and isinstance(v, int))[:64]
        except (OSError, ValueError, TypeError, AttributeError):
            return ()

    def _remember(self, result):
        # Learning only from accepted branches of a fully audited theorem.
        try:
            old = json.loads(self.memory_path.read_text(encoding='utf-8'))
            if not isinstance(old, dict): old = {}
        except (OSError, ValueError):
            old = {}
        raw_scores = old.get('lemmas', {})
        if not isinstance(raw_scores, dict): raw_scores = {}
        scores = {k: v for k, v in raw_scores.items()
                  if isinstance(k, str) and _NAME.fullmatch(k) and isinstance(v, int)}
        for name in result.retrieved_constants:
            if '.' in name:
                scores[name] = scores.get(name, 0) + 1
        proofs = old.get('proofs', {})
        if not isinstance(proofs, dict): proofs = {}
        key = hashlib.sha256(result.statement.encode()).hexdigest()
        proofs[key] = {'statement': result.statement, 'source_path': result.attempts[0].source_path,
                       'constants': list(result.retrieved_constants)}
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.memory_path.with_suffix('.tmp')
        tmp.write_text(json.dumps({'version': 1, 'lemmas': scores, 'proofs': proofs}, indent=2), encoding='utf-8')
        tmp.replace(self.memory_path)

    def prove(self, statement, *, theorem_name='gareen_recursive_goal',
              wall_clock_budget_seconds=120.0, per_attempt_timeout_seconds=None):
        name = _safe_identifier(theorem_name)
        statement = validate_statement(statement)
        hints = self._hints()
        empty = dict(theorem_name=name, statement=statement, verified=False,
                     winning_strategy=None, attempts=(), memory_hints=hints)
        if wall_clock_budget_seconds <= 0:
            return RecursiveResult(**empty, status='not-attempted')
        if not self.available():
            return RecursiveResult(**empty, status='backend-unavailable')
        start = time.monotonic()
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256((name + statement).encode()).hexdigest()[:12]
        path = self.generated_dir / f'{name}_{key}_recursive.lean'
        preferred = ' [' + ', '.join(hints) + ']' if hints else ''
        source = (f'import Gareen.RecursivePlanner\nset_option maxHeartbeats 2000000\n'
                  f'namespace Gareen.GeneratedRecursive\n'
                  f'theorem {name} : {statement} := by\n'
                  f'  gareen_search {self.max_depth} {self.max_nodes} {self.max_candidates}{preferred}\n'
                  f'end Gareen.GeneratedRecursive\n#print axioms Gareen.GeneratedRecursive.{name}\n')
        path.write_text(source, encoding='utf-8')
        timeout = min(wall_clock_budget_seconds, per_attempt_timeout_seconds or self.timeout_seconds)
        try:
            proc = subprocess.run(['lake', 'env', 'lean', str(path)], cwd=self.repo_root,
                                  capture_output=True, text=True, timeout=timeout, check=False)
            rc, out, err, timed_out = proc.returncode, proc.stdout, proc.stderr, False
        except subprocess.TimeoutExpired as exc:
            def text(x): return x.decode(errors='replace') if isinstance(x, bytes) else (x or '')
            rc, out, err, timed_out = 124, text(exc.stdout), text(exc.stderr), True
        elapsed = time.monotonic() - start
        verified = audited(out + '\n' + err, rc)
        graph = parse_events(out)
        constants = tuple(dict.fromkeys(e['rule'] for e in graph
                          if e['status'] == 'accepted' and '.' in e['rule'])) if verified else ()
        counts = re.findall(r'GAREEN_NODES (\d+)', out)
        attempt = PlannerAttempt('recursive_library_search', verified, rc, round(elapsed, 3),
                                 timed_out, str(path), (), constants, out, err)
        result = RecursiveResult(name, statement, verified,
                                 'recursive_library_search' if verified else None, (attempt,),
                                 graph, int(counts[-1]) if counts else 0,
                                 'verified' if verified else ('timeout' if timed_out else 'unproved-in-budget'), hints)
        path.with_suffix('.json').write_text(json.dumps(asdict(result), indent=2), encoding='utf-8')
        if verified:
            self._remember(result)
        return result


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--statement', default='∀ a b : Nat, Nat.gcd a b ∣ a + b')
    p.add_argument('--seconds', type=float, default=120)
    args = p.parse_args()
    result = RecursiveProofPlanner().prove(args.statement, wall_clock_budget_seconds=args.seconds)
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    return 0 if result.verified else 1


if __name__ == '__main__':
    raise SystemExit(main())
