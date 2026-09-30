import unittest

from lean_bridge import LeanVerificationResult
from lean_research import LeanBackedResearcher, report_to_json
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
            error="" if self.verified else "rejected",
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
        self.assertEqual(report.verified_discoveries, 2)
        self.assertEqual(len(bridge.calls), 2)

    def test_rejected_candidate_is_not_a_discovery(self):
        bridge = FakeLeanBridge(verified=False)
        researcher = LeanBackedResearcher(
            bridge=bridge,
            max_attempts=1,
        )

        report = researcher.research(KnowledgeState())

        self.assertEqual(report.verified_discoveries, 0)
        self.assertFalse(report.attempts[0].verified)

    def test_report_is_json_serializable_shape(self):
        bridge = FakeLeanBridge(verified=True)
        report = LeanBackedResearcher(
            bridge=bridge,
            max_attempts=1,
        ).research(KnowledgeState())

        payload = report_to_json(report)

        self.assertEqual(payload["attempted_conjectures"], 1)
        self.assertEqual(payload["verified_discoveries"], 1)
        self.assertEqual(len(payload["discoveries"]), 1)


if __name__ == "__main__":
    unittest.main()
