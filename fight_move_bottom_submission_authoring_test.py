"""Common guard attack authoring contracts, independent of registry integration."""
import unittest
from fight_moves import MOVE_DEFINITIONS, MoveIndex
from fight_moves.catalogue.bottom_submission_development import BOTTOM_SUBMISSION_DEVELOPMENT
from fight_moves.validation import validate_move_registry


class BottomSubmissionAuthoringTests(unittest.TestCase):
    def test_eight_valid_neutral_attacks(self):
        additions = BOTTOM_SUBMISSION_DEVELOPMENT
        ids = {m.move_id for m in MOVE_DEFINITIONS}
        combined = (*MOVE_DEFINITIONS, *(m for m in additions if m.move_id not in ids))
        self.assertEqual(len(additions), 8)
        self.assertEqual(validate_move_registry(combined), [])
        self.assertEqual(len({m.name for m in combined}), len(combined))
        for definition in additions:
            self.assertEqual(definition.parent_action, "bottom_submission")
            self.assertTrue(definition.positions <= {"guard", "half guard"})
            self.assertEqual((definition.energy, definition.miss_risk, definition.counter_risk), (1, 1, 1))
            self.assertTrue(1 <= len(definition.follow_ups) <= 3)
            self.assertTrue(definition.attack_path and definition.failure_outcomes)

    def test_legal_only_in_owned_guard_contexts(self):
        index = MoveIndex(BOTTOM_SUBMISSION_DEVELOPMENT)
        self.assertEqual(len(index.legal_moves("bottom_submission", "guard")), 7)
        self.assertEqual(len(index.legal_moves("bottom_submission", "half guard")), 2)
        for position in ("range", "clinch", "mount", "back control", "leg entanglement"):
            self.assertEqual(index.legal_moves("bottom_submission", position), ())
        self.assertEqual(index.legal_moves("submission", "guard"), ())


if __name__ == "__main__":
    unittest.main()
