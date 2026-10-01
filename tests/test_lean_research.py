import unittest

from lean_bridge import (
    LeanBatchItemResult,
    LeanBatchVerificationResult,
    LeanVerificationResult,
)
from lean_research import (
    LeanBackedResearcher,
    report_to_json,
    select_research_conjectures,
)
from artificial_mathematician import generate_research_conjectures
from math_world import KnowledgeState


class FakeLeanBridge:
    def __init__(self, verified=True):
        self.verified = verified
        self.calls = []

    def verify_formula(self, formula, *, theorem_name):
        self.calls.append((formula, theorem_name))
        return LeanVerificationResult(
            theorem_name=theorem_name,
            statement=str(formula),
            verified=self.verified,
            tactic="simp" if self.verified else None,
            attempts=(),
            error=(
                ""
                if self.verified
                else "unproved within the current budget"
            ),
        )


class FakeBatchBridge:
    def __init__(self):
        self.batch_calls = []

    def verify_batch(self, candidates, *, batch_size):
        self.batch_calls.append((tuple(candidates), batch_size))
        results = tuple(
            LeanBatchItemResult(
                theorem_name=item.theorem_name,
                statement=str(item.formula),
                verified=True,
                tactic="aesop",
            )
            for item in candidates
        )
        return LeanBatchVerificationResult(
            results=results,
            process_invocations=2,
            elapsed_seconds=0.25,
        )


class FakeTacticAwareBatchBridge:
    def __init__(self):
        self.calls = []

    def verify_batch(self, candidates, *, tactics, batch_size):
        candidates = tuple(candidates)
        tactics = tuple(tactics)
        self.calls.append((candidates, tactics, batch_size))

        if tactics == ("simp", "norm_num"):
            results = tuple(
                LeanBatchItemResult(
                    theorem_name=item.theorem_name,
                    statement=str(item.formula),
                    verified=(index == 0),
                    tactic="simp" if index == 0 else None,
                    error="" if index == 0 else "routine gate did not solve",
                )
                for index, item in enumerate(candidates)
            )
        else:
            results = tuple(
                LeanBatchItemResult(
                    theorem_name=item.theorem_name,
                    statement=str(item.formula),
                    verified=True,
                    tactic="aesop",
                )
                for item in candidates
            )

        return LeanBatchVerificationResult(
            results=results,
            process_invocations=1,
            elapsed_seconds=0.1,
        )


class LeanBackedResearchTests(unittest.TestCase):
    def test_researcher_sends_generated_conjectures_to_lean_backend(self):
        bridge = FakeLeanBridge(verified=True)
        researcher = LeanBackedResearcher(
            bridge=bridge,
            max_attempts=2,
        )

        report = researcher.research(KnowledgeState())

        self.assertGreater(report.generated_conjectures, 0)
        self.assertEqual(report.attempted_conjectures, 2)
        self.assertEqual(report.verified_candidates, 2)
        self.assertEqual(report.routine_verified, 2)
        self.assertEqual(report.verified_discoveries, 0)
        self.assertEqual(len(bridge.calls), 2)

    def test_unproved_candidate_is_not_a_discovery(self):
        bridge = FakeLeanBridge(verified=False)
        researcher = LeanBackedResearcher(
            bridge=bridge,
            max_attempts=1,
        )

        report = researcher.research(KnowledgeState())

        self.assertEqual(report.verified_discoveries, 0)
        self.assertEqual(report.unproved_conjectures, 1)
        self.assertFalse(report.attempts[0].verified)
        self.assertEqual(
            report.attempts[0].status,
            "unproved-in-budget",
        )

    def test_researcher_prefers_batch_backend_when_available(self):
        bridge = FakeBatchBridge()
        report = LeanBackedResearcher(
            bridge=bridge,
            max_attempts=4,
            batch_size=32,
        ).research(KnowledgeState())

        self.assertEqual(len(bridge.batch_calls), 1)
        self.assertEqual(report.attempted_conjectures, 4)
        self.assertEqual(report.verified_candidates, 4)
        self.assertEqual(report.routine_verified, 0)
        self.assertEqual(report.verified_discoveries, 4)
        self.assertEqual(report.process_invocations, 2)
        self.assertEqual(report.verification_elapsed_seconds, 0.25)

    def test_routine_gate_avoids_strong_prover_for_easy_candidate(self):
        bridge = FakeTacticAwareBatchBridge()
        report = LeanBackedResearcher(
            bridge=bridge,
            max_attempts=2,
            batch_size=32,
        ).research(KnowledgeState())

        self.assertEqual(len(bridge.calls), 2)
        self.assertEqual(bridge.calls[0][1], ("simp", "norm_num"))
        self.assertEqual(bridge.calls[1][1], ("omega", "ring", "nlinarith", "aesop"))
        self.assertEqual(len(bridge.calls[1][0]), 1)
        self.assertEqual(report.verified_candidates, 2)
        self.assertEqual(report.routine_verified, 1)
        self.assertEqual(report.verified_discoveries, 1)

    def test_selection_does_not_starve_bivariate_conjectures(self):
        conjectures = generate_research_conjectures(KnowledgeState())
        selected = select_research_conjectures(
            conjectures,
            limit=4,
        )

        arities = [len(item.variables) for item in selected]
        self.assertIn(1, arities)
        self.assertIn(2, arities)

    def test_report_is_json_serializable_shape(self):
        bridge = FakeLeanBridge(verified=True)
        report = LeanBackedResearcher(
            bridge=bridge,
            max_attempts=1,
        ).research(KnowledgeState())

        payload = report_to_json(report)

        self.assertEqual(payload["attempted_conjectures"], 1)
        self.assertEqual(payload["verified_candidates"], 1)
        self.assertEqual(payload["routine_verified"], 1)
        self.assertEqual(payload["verified_discoveries"], 0)
        self.assertEqual(payload["unproved_conjectures"], 0)
        self.assertEqual(len(payload["discoveries"]), 0)


if __name__ == "__main__":
    unittest.main()
