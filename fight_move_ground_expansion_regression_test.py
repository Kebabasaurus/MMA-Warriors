"""Registration, appearance and style floors after the common-ground expansion."""
from dataclasses import replace
import unittest
from constants import STYLES
from fight_moves import MOVE_DEFINITIONS
from fight_moves.legacy_ids import EXPANSION_MOVE_IDS
from fight_moves.coverage import coverage_report
from fight_moves.followup_diversity import ACTION_DIVERSE_FOLLOWUP_UPDATES
from fight_moves.followup_continuity import CONTINUITY_FOLLOWUP_UPDATES
from analysis.compare_ground_move_expansion import SLICE_6
from analysis.generate_move_coverage_report import slice_6_failures


APPLIED_FOLLOWUP_UPDATES = {**ACTION_DIVERSE_FOLLOWUP_UPDATES, **CONTINUITY_FOLLOWUP_UPDATES}


class GroundExpansionTests(unittest.TestCase):
    def test_registered_and_permanently_protected(self):
        self.assertEqual(len(SLICE_6), 44)
        registry = {m.move_id: m for m in MOVE_DEFINITIONS}
        for definition in SLICE_6:
            expected = replace(definition, follow_ups=APPLIED_FOLLOWUP_UPDATES.get(
                definition.move_id, definition.follow_ups))
            self.assertEqual(registry[definition.move_id], expected)
            self.assertIn(definition.move_id, EXPANSION_MOVE_IDS)

    def test_missing_ordinary_appearance_is_rejected(self):
        ids = [m.move_id for m in SLICE_6]
        self.assertEqual(slice_6_failures({"observed_move_ids": ids}), [])
        self.assertEqual(slice_6_failures({"observed_move_ids": ids[1:]}),
                         [f"Slice 6 move absent: {ids[0]}"])

    def test_every_style_has_eighteen_moves_combination_and_finisher(self):
        counts = coverage_report([])["style_counts"]
        self.assertEqual(set(counts), set(STYLES))
        for style in STYLES:
            with self.subTest(style=style):
                self.assertGreaterEqual(counts[style], 18)
                for tag in ("style-combination", "style-finisher"):
                    self.assertTrue(any(m.preferred_styles == (style,) and tag in m.tags
                                        for m in MOVE_DEFINITIONS), (style, tag))


if __name__ == "__main__":
    unittest.main()
