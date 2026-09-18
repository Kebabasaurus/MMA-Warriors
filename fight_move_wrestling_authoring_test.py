"""Slice 6 wrestling authoring and common resolver-position contracts."""
from collections import Counter
import unittest

from fight_moves import MOVE_DEFINITIONS, MoveIndex, STANDING_POSITIONS
from fight_moves.catalogue.wrestling_development import WRESTLING_DEVELOPMENT
from fight_moves.validation import validate_move_registry


class WrestlingAuthoringTests(unittest.TestCase):
    def combined(self):
        additions = {m.move_id: m for m in WRESTLING_DEVELOPMENT}
        for definition in MOVE_DEFINITIONS:
            if definition.move_id in additions:
                self.assertEqual(definition, additions[definition.move_id])
        return (*[m for m in MOVE_DEFINITIONS if m.move_id not in additions], *WRESTLING_DEVELOPMENT)

    def test_budget_and_closed_metadata(self):
        self.assertEqual(len(WRESTLING_DEVELOPMENT), 13)
        self.assertEqual(Counter(m.parent_action for m in WRESTLING_DEVELOPMENT), {"shoot": 6, "takedown": 7})
        self.assertEqual(validate_move_registry(self.combined()), [])
        self.assertEqual(len({m.name for m in self.combined()}), len(self.combined()))
        for definition in WRESTLING_DEVELOPMENT:
            self.assertEqual((definition.energy, definition.miss_risk, definition.counter_risk), (1, 1, 1))

    def test_chooser_contexts_and_resolver_finishes(self):
        index = MoveIndex(self.combined())
        for definition in WRESTLING_DEVELOPMENT:
            with self.subTest(move=definition.move_id):
                positions = STANDING_POSITIONS if definition.parent_action == "shoot" else {"clinch", "cage"}
                self.assertTrue(definition.positions <= positions)
                self.assertTrue(definition.entry_family)
                self.assertTrue(definition.defense_families)
                for position in definition.positions:
                    self.assertIn(definition, index.legal_moves(definition.parent_action, position))
                for position in {"guard", "failed shot", "standing back control"}:
                    self.assertNotIn(definition, index.legal_moves(definition.parent_action, position))
                if definition.parent_action == "takedown":
                    self.assertEqual(set(definition.finish_positions), {"guard", "half guard"})

    def test_existing_followups_cover_successful_top_arrival(self):
        existing = {m.move_id: m for m in MOVE_DEFINITIONS}
        for definition in WRESTLING_DEVELOPMENT:
            with self.subTest(move=definition.move_id):
                self.assertTrue(1 <= len(definition.follow_ups) <= 3)
                for followup in definition.follow_ups:
                    self.assertIn(followup, existing)
                    self.assertTrue(existing[followup].positions & {"guard", "half guard", "cage"})
                for position in {"guard", "half guard"}:
                    self.assertTrue(any(position in existing[key].positions for key in definition.follow_ups))


if __name__ == "__main__":
    unittest.main()
