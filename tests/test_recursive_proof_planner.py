import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from recursive_proof_planner import RecursiveProofPlanner, audited, parse_events, validate_statement
from experiments.recursive_benchmark import GROUPS, FALSE_CONTROLS

AUDIT = "'Gareen.GeneratedRecursive.goal' depends on axioms: [propext, Classical.choice, Quot.sound]"
EVENTS = '\n'.join('GAREEN_EVENT ' + json.dumps(e) for e in [
    dict(id=1, parent=0, goal='P', rule='Nat.foo', status='try'),
    dict(id=2, parent=1, goal='P', rule='Nat.foo', status='backtrack'),
    dict(id=3, parent=0, goal='P', rule='dvd_add.mp', declaration='dvd_add', status='accepted')])

class RecursivePlannerTests(unittest.TestCase):
    def test_admission_or_custom_axiom_never_passes(self):
        self.assertTrue(audited(AUDIT, 0))
        self.assertTrue(audited("goal does not depend on any axioms", 0))
        self.assertFalse(audited(AUDIT, 1))
        self.assertFalse(audited('', 0))
        self.assertFalse(audited(AUDIT.replace('propext', 'sorryAx'), 0))
        self.assertFalse(audited(AUDIT.replace('propext', 'myFakeAxiom'), 0))
        self.assertFalse(audited(AUDIT + '\n' + AUDIT, 0))

    def test_goal_cannot_inject_a_declaration_or_proof(self):
        for bad in ['True := by trivial', 'True\naxiom evil : False', 'by sorry',
                    'True -- comment', 'True; end', 'True /- comment -/']:
            with self.assertRaises(ValueError): validate_statement(bad)
        self.assertEqual(validate_statement('∀ a b : Nat, a ∣ b → a ∣ b'),
                         '∀ a b : Nat, a ∣ b → a ∣ b')

    def test_graph_retains_failed_branches(self):
        events = parse_events(EVENTS)
        self.assertEqual([e['status'] for e in events], ['try', 'backtrack', 'accepted'])
        self.assertEqual(events[1]['parent'], 1)

    def test_verified_proof_updates_only_successful_lemmas(self):
        with tempfile.TemporaryDirectory() as d:
            p = RecursiveProofPlanner(d)
            with patch.object(p, 'available', return_value=True), patch('subprocess.run', return_value=
                    subprocess.CompletedProcess([], 0, EVENTS + '\nGAREEN_NODES 7\n' + AUDIT, '')):
                r = p.prove('True', theorem_name='goal')
            self.assertTrue(r.verified)
            self.assertEqual(r.retrieved_constants, ('dvd_add',))
            self.assertEqual(r.expanded_nodes, 7)
            self.assertEqual(p._hints(), ('dvd_add',))
            self.assertTrue(Path(r.attempts[0].source_path).with_suffix('.json').exists())

    def test_timeout_bytes_preserved_without_learning(self):
        with tempfile.TemporaryDirectory() as d:
            p = RecursiveProofPlanner(d)
            with patch.object(p, 'available', return_value=True), patch('subprocess.run', side_effect=
                    subprocess.TimeoutExpired('lean', 1, output=b'partial', stderr=b'timed')):
                r = p.prove('False', wall_clock_budget_seconds=0.01)
            self.assertEqual(r.status, 'timeout')
            self.assertEqual(r.attempts[0].stdout, 'partial')
            self.assertFalse(p.memory_path.exists())

    def test_zero_budget_never_invokes_lean(self):
        with tempfile.TemporaryDirectory() as d, patch('subprocess.run') as run:
            r = RecursiveProofPlanner(d).prove('True', wall_clock_budget_seconds=0)
            self.assertEqual(r.status, 'not-attempted')
            run.assert_not_called()

    def test_failed_audit_never_teaches_memory(self):
        with tempfile.TemporaryDirectory() as d:
            p = RecursiveProofPlanner(d)
            with patch.object(p, 'available', return_value=True), patch('subprocess.run', return_value=
                    subprocess.CompletedProcess([], 0, EVENTS + '\n' + AUDIT.replace('propext', 'sorryAx'), '')):
                r = p.prove('False')
            self.assertFalse(r.verified)
            self.assertFalse(p.memory_path.exists())

    def test_corrupt_memory_is_only_a_hint(self):
        with tempfile.TemporaryDirectory() as d:
            p = RecursiveProofPlanner(d)
            p.memory_path.parent.mkdir()
            for text in ['not json', '[]', '{"lemmas": {"by sorry": 100}}']:
                p.memory_path.write_text(text)
                self.assertEqual(p._hints(), ())

    def test_benchmark_is_fixed_and_controls_are_separate(self):
        goals = [g for group in GROUPS.values() for g in group]
        self.assertEqual(len(goals), 50)
        self.assertEqual(len(set(goals)), 50)
        self.assertFalse(set(goals) & set(FALSE_CONTROLS))
        for g in goals + FALSE_CONTROLS: validate_statement(g)

if __name__ == '__main__': unittest.main()
