"""Common top-position authoring and factual strike-volume contracts."""
from collections import Counter
from dataclasses import replace
import random
import unittest
from unittest.mock import patch

from fight_moves import ALL_POSITIONS, MOVE_DEFINITIONS, MoveIndex
from fight_moves.catalogue.ground_top_development import GROUND_TOP_DEVELOPMENT
from fight_moves.followup_continuity import CONTINUITY_FOLLOWUP_UPDATES
from fight_moves.validation import validate_move_registry

COMMON = {"guard", "half guard", "side control", "mount", "back control"}
DESTINATIONS = {"guard": {"half guard"}, "half guard": {"side control"},
                "side control": {"mount", "back control"}, "mount": {"back control"}}


class GroundTopAuthoringTests(unittest.TestCase):
    def combined(self):
        additions = {move.move_id: replace(move, follow_ups=CONTINUITY_FOLLOWUP_UPDATES.get(
            move.move_id, move.follow_ups)) for move in GROUND_TOP_DEVELOPMENT}
        for move in MOVE_DEFINITIONS:
            if move.move_id in additions:
                self.assertEqual(move, additions[move.move_id])
        return (*[move for move in MOVE_DEFINITIONS if move.move_id not in additions], *additions.values())

    def test_budget_validation_and_unique_names(self):
        self.assertEqual(Counter(move.parent_action for move in GROUND_TOP_DEVELOPMENT),
                         {"advance_position": 8, "ground_control": 7, "ground_strikes": 8})
        self.assertEqual(validate_move_registry(self.combined()), [])
        self.assertEqual(len({move.name for move in self.combined()}), len(self.combined()))

    def test_only_common_emitted_top_contexts(self):
        index = MoveIndex(self.combined())
        for move in GROUND_TOP_DEVELOPMENT:
            move = replace(move, follow_ups=CONTINUITY_FOLLOWUP_UPDATES.get(move.move_id, move.follow_ups))
            with self.subTest(move=move.move_id):
                self.assertTrue(move.positions <= COMMON)
                self.assertEqual(move.targets, frozenset())
                for position in ALL_POSITIONS:
                    self.assertEqual(move in index.legal_moves(move.parent_action, position),
                                     position in move.positions)
                self.assertNotIn("fence", move.name)
                if move.parent_action == "advance_position":
                    self.assertTrue(move.positions <= DESTINATIONS.keys())

    def test_neutral_metadata_and_reachable_followups(self):
        existing = {move.move_id: move for move in MOVE_DEFINITIONS}
        new_ids = {move.move_id for move in GROUND_TOP_DEVELOPMENT}
        for move in GROUND_TOP_DEVELOPMENT:
            with self.subTest(move=move.move_id):
                self.assertEqual((move.energy, move.miss_risk, move.counter_risk), (1, 1, 1))
                self.assertTrue(1 <= len(move.follow_ups) <= 3)
                next_positions = (set().union(*(DESTINATIONS[position] for position in move.positions))
                                  if move.parent_action == "advance_position" else move.positions)
                for followup in move.follow_ups:
                    self.assertIn(followup, existing)
                    self.assertNotIn(followup, new_ids)
                    self.assertTrue(existing[followup].positions & next_positions)

    def test_components_reconcile_every_ground_volume_without_rng(self):
        import fight_engine
        registry = {move.move_id: move for move in self.combined()}
        before_rng = random.getstate()
        with patch.object(fight_engine, "MOVE_REGISTRY", registry):
            for move in GROUND_TOP_DEVELOPMENT:
                if move.parent_action != "ground_strikes":
                    continue
                with self.subTest(move=move.move_id):
                    self.assertEqual(len(set(move.tags) & {"punch", "elbow"}), 1)
                    self.assertTrue(2 <= len(move.components) <= 3)
                    for component in move.components:
                        self.assertTrue(any(weapon in component for weapon in ("punch", "elbow", "hook", "hammerfist")))
                        self.assertNotIn("body", component)
                        self.assertEqual("elbow" in component, "elbow" in move.tags)
                    for attempts in range(10, 27):
                        for landed in (0, attempts // 2, attempts):
                            components = fight_engine.FightEngineMixin.exchange_combination_components(
                                "ground_strikes", attempts, landed, "head", move.move_id)
                            self.assertEqual(len(components), attempts)
                            self.assertEqual(sum(item["landed"] for item in components), landed)
                            self.assertTrue(all(item["weapon"] in move.components for item in components))
        self.assertEqual(random.getstate(), before_rng)


if __name__ == "__main__":
    unittest.main()
