"""Clinch Slice 5 authoring contracts, independent of registration timing."""
from collections import Counter
from dataclasses import replace
import unittest

from fight_moves import MOVE_DEFINITIONS, MoveIndex, STANDING_POSITIONS
from fight_moves.catalogue.clinch_development import CLINCH_DEVELOPMENT
from fight_moves.followup_diversity import ACTION_DIVERSE_FOLLOWUP_UPDATES
from fight_moves.followup_continuity import CONTINUITY_FOLLOWUP_UPDATES
from fight_moves.validation import validate_move_registry

APPLIED_FOLLOWUP_UPDATES = {**ACTION_DIVERSE_FOLLOWUP_UPDATES, **CONTINUITY_FOLLOWUP_UPDATES}


class ClinchAuthoringTests(unittest.TestCase):
    def combined(self):
        additions = {m.move_id: replace(m, follow_ups=APPLIED_FOLLOWUP_UPDATES.get(m.move_id, m.follow_ups))
                     for m in CLINCH_DEVELOPMENT}
        # Work before integration and continue protecting the registered objects afterward.
        for definition in MOVE_DEFINITIONS:
            if definition.move_id in additions:
                self.assertEqual(definition, additions[definition.move_id])
        return (*[m for m in MOVE_DEFINITIONS if m.move_id not in additions], *additions.values())

    def test_budget_and_metadata(self):
        self.assertEqual(len(CLINCH_DEVELOPMENT), 27)
        self.assertEqual(Counter(m.parent_action for m in CLINCH_DEVELOPMENT), {
            "dirty_boxing": 8, "clinch": 7, "cage_control": 7, "break_clinch": 5})
        self.assertEqual(validate_move_registry(self.combined()), [])
        self.assertEqual(len({m.name for m in self.combined()}), len(self.combined()))

    def test_followups_are_existing_and_position_compatible(self):
        existing = {m.move_id: m for m in MOVE_DEFINITIONS}
        for definition in CLINCH_DEVELOPMENT:
            with self.subTest(move=definition.move_id):
                self.assertTrue(1 <= len(definition.follow_ups) <= 3)
                self.assertEqual((definition.energy, definition.miss_risk, definition.counter_risk), (1, 1, 1))
                expected_positions = STANDING_POSITIONS if definition.parent_action == "break_clinch" else {"clinch", "cage"}
                for followup in definition.follow_ups:
                    self.assertIn(followup, existing)
                    self.assertTrue(existing[followup].positions & expected_positions)

    def test_only_common_emitted_contexts_are_legal(self):
        index = MoveIndex(self.combined())
        for definition in CLINCH_DEVELOPMENT:
            definition = replace(definition, follow_ups=APPLIED_FOLLOWUP_UPDATES.get(
                definition.move_id, definition.follow_ups))
            with self.subTest(move=definition.move_id):
                positions = STANDING_POSITIONS if definition.parent_action == "clinch" else {"clinch", "cage"}
                self.assertTrue(definition.positions <= positions)
                for position in definition.positions:
                    for target in definition.targets or {""}:
                        self.assertIn(definition, index.legal_moves(definition.parent_action, position, target))
                self.assertNotIn(definition, index.legal_moves(definition.parent_action, "failed shot", "head"))
                self.assertNotIn(definition, index.legal_moves(definition.parent_action, "guard", "body"))
                if "fence" in definition.name:
                    self.assertEqual(definition.positions, {"cage"})

    def test_strike_target_and_weapon_contracts(self):
        for definition in CLINCH_DEVELOPMENT:
            if definition.parent_action != "dirty_boxing":
                continue
            with self.subTest(move=definition.move_id):
                self.assertEqual(len(set(definition.tags) & {"punch", "knee", "elbow"}), 1)
                self.assertEqual(len(definition.targets), 1)
                if "knee" in definition.tags:
                    self.assertEqual(definition.targets, {"body"})
                if "elbow" in definition.tags:
                    self.assertEqual(definition.targets, {"head"})


if __name__ == "__main__":
    unittest.main()
