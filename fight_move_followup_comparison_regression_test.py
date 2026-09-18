"""The paired follow-up gate must reject mechanical drift and restore runtime globals."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import fight_engine
from analysis import compare_followup_diversity as comparison
from analysis.generate_move_coverage_report import summarize_variety


class FollowupComparisonTests(unittest.TestCase):
    def test_mechanical_drift_or_non_improvement_is_rejected(self):
        before = {"mechanical_signatures": ["a", "b"], "chained_selection_pct": 12}
        after = {"mechanical_signatures": ["a", "b"], "chained_selection_pct": 15}
        self.assertEqual(comparison.compare_reports(before, after), [])
        self.assertTrue(comparison.compare_reports(before, before))
        changed = deepcopy(after)
        changed["mechanical_signatures"].reverse()
        self.assertTrue(comparison.compare_reports(before, changed))

    def test_unapproved_metadata_rejected_before_simulation(self):
        with (patch.object(comparison, "compare_followup_update", return_value=["name changed"]),
              patch.object(comparison, "build_report") as report, self.assertRaises(ValueError)):
            comparison.compare_diversity({}, {})
        report.assert_not_called()

    def test_globals_restored_after_either_arm_fails(self):
        root = Path(__file__).resolve().parent / "analysis"
        reference = json.loads((root / "move_registry_followup_diversity.json").read_text(encoding="utf-8"))
        manifest = json.loads((root / "move_followup_continuity_manifest.json").read_text(encoding="utf-8"))
        registry, lookup = fight_engine.MOVE_REGISTRY, fight_engine.legal_moves
        report = {**summarize_variety({}, [], 0), "mechanical_signatures": []}
        for responses in ([RuntimeError("before")], [report, RuntimeError("after")]):
            with (patch.object(comparison, "build_report", side_effect=responses),
                  self.assertRaises(RuntimeError)):
                comparison.compare_diversity(reference, manifest)
            self.assertIs(fight_engine.MOVE_REGISTRY, registry)
            self.assertIs(fight_engine.legal_moves, lookup)


if __name__ == "__main__":
    unittest.main()
