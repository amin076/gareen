import unittest

from autonomous_discovery import (
    AutonomousTheoremExplorer,
    generate_candidate_statements,
    generate_closed_terms,
)
from math_world import build_initial_knowledge, check_proof
from proof_search import BoundedProofSearcher


class AutonomousDiscoveryTests(unittest.TestCase):
    def test_candidate_generation_requires_no_external_goal(self):
        terms = generate_closed_terms(include_multiplication=False)
        candidates = generate_candidate_statements(terms)

        self.assertGreater(len(terms), 4)
        self.assertGreater(len(candidates), 0)
        self.assertTrue(all(candidate.statement is not None for candidate in candidates))

    def test_explorer_autonomously_accepts_verified_theorems(self):
        state = build_initial_knowledge()
        initial_names = set(state.theorems)

        explorer = AutonomousTheoremExplorer(
            max_attempts=32,
            max_discoveries=3,
            min_proof_steps=4,
            include_multiplication=False,
            searcher=BoundedProofSearcher(
                max_depth=6,
                max_terms=64,
                instantiation_rounds=1,
            ),
        )

        report = explorer.explore(state)

        self.assertGreater(report.generated_candidates, 0)
        self.assertGreater(report.attempted_candidates, 0)
        self.assertGreaterEqual(report.accepted_theorems, 1)
        self.assertEqual(report.accepted_theorems, len(report.discoveries))

        discovered_names = {record.theorem_name for record in report.discoveries}
        self.assertTrue(discovered_names.isdisjoint(initial_names))
        self.assertTrue(discovered_names.issubset(state.theorems))

    def test_every_discovery_rechecks_with_trusted_checker(self):
        state = build_initial_knowledge()
        explorer = AutonomousTheoremExplorer(
            max_attempts=32,
            max_discoveries=2,
            min_proof_steps=4,
            include_multiplication=False,
        )

        report = explorer.explore(state)
        self.assertGreaterEqual(report.accepted_theorems, 1)

        for discovery in report.discoveries:
            theorem = state.theorems[discovery.theorem_name]
            known = tuple(
                other
                for name, other in state.theorems.items()
                if name != discovery.theorem_name
            )
            check = check_proof(
                theorem.proof,
                axioms=state.world.axioms,
                known_theorems=known,
            )
            self.assertTrue(check.valid, (discovery.theorem_name, check.errors))

    def test_discovery_records_attempt_statuses(self):
        state = build_initial_knowledge()
        explorer = AutonomousTheoremExplorer(
            max_attempts=12,
            max_discoveries=1,
            min_proof_steps=4,
            include_multiplication=False,
        )

        report = explorer.explore(state)

        self.assertGreater(len(report.attempts), 0)
        statuses = {attempt.status for attempt in report.attempts}
        self.assertTrue(
            statuses.intersection(
                {"accepted", "skipped-too-direct", "unproved", "skipped-existing"}
            )
        )

    def test_high_minimum_proof_length_prevents_storage(self):
        state = build_initial_knowledge()
        initial_count = len(state.theorems)

        explorer = AutonomousTheoremExplorer(
            max_attempts=12,
            max_discoveries=2,
            min_proof_steps=10_000,
            include_multiplication=False,
        )

        report = explorer.explore(state)

        self.assertEqual(report.accepted_theorems, 0)
        self.assertEqual(len(state.theorems), initial_count)


if __name__ == "__main__":
    unittest.main()
