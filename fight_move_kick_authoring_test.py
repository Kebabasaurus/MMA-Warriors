"""Slice 5 kick contracts, runnable before and after registry integration."""
import unittest

from fight_moves import MOVE_DEFINITIONS, MoveIndex, STANDING_POSITIONS, ALL_POSITIONS
from fight_moves.catalogue.kick_development import SLICE_5_KICKS
from fight_moves.validation import validate_move_registry


def combined_definitions():
    current_ids = {move.move_id for move in MOVE_DEFINITIONS}
    return (*MOVE_DEFINITIONS, *(move for move in SLICE_5_KICKS if move.move_id not in current_ids))


class KickAuthoringTests(unittest.TestCase):
    def test_ten_unique_valid_kick_definitions(self):
        self.assertEqual(len(SLICE_5_KICKS), 10)
        self.assertEqual(len({move.move_id for move in SLICE_5_KICKS}), 10)
        self.assertEqual(validate_move_registry(combined_definitions()), [])
        names = [move.name.casefold() for move in combined_definitions()]
        self.assertEqual(len(names), len(set(names)))

    def test_target_and_position_match_the_standing_kick_lane(self):
        index = MoveIndex(combined_definitions())
        for move in SLICE_5_KICKS:
            with self.subTest(move=move.move_id):
                self.assertEqual(move.parent_action, "kick")
                self.assertEqual(move.positions, STANDING_POSITIONS)
                self.assertEqual(len(move.targets), 1)
                self.assertTrue(move.targets <= {"head", "body", "leg"})
                for position in ALL_POSITIONS:
                    for target in ("head", "body", "leg", ""):
                        self.assertEqual(move in index.legal_moves("kick", position, target),
                                         position in STANDING_POSITIONS and target in move.targets)

    def test_followups_resolve_and_metadata_stays_neutral(self):
        definitions = {move.move_id: move for move in combined_definitions()}
        new_ids = {move.move_id for move in SLICE_5_KICKS}
        for move in SLICE_5_KICKS:
            with self.subTest(move=move.move_id):
                self.assertEqual((move.energy, move.miss_risk, move.counter_risk), (1, 1, 1))
                self.assertFalse(set(move.tags) & {"high-risk", "flying", "spinning", "finisher"})
                self.assertTrue(1 <= len(move.follow_ups) <= 3)
                for followup in move.follow_ups:
                    self.assertIn(followup, definitions)
                    self.assertNotIn(followup, new_ids)
                    self.assertTrue(definitions[followup].positions & move.positions)
                self.assertTrue(move.defense_families)

    def test_thin_styles_gain_meaningful_kick_choices(self):
        for style, minimum in (("Taekwondo", 5), ("Well-Rounded", 4), ("Dutch Kickboxer", 3)):
            with self.subTest(style=style):
                self.assertGreaterEqual(sum(style in move.preferred_styles for move in SLICE_5_KICKS), minimum)


if __name__ == "__main__":
    unittest.main()
