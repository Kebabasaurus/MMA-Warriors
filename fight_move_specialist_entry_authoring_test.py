"""Validate the five Phase 34 identities independently of registration."""
from collections import Counter
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import ALL_POSITIONS, MOVE_DEFINITIONS, MoveIndex
from fight_moves.catalogue.specialist_entry_development import SPECIALIST_ENTRY_DEVELOPMENT
from fight_moves.chains import MoveChainGraph, sequence_role_allows
from fight_moves.validation import validate_move_registry


class SpecialistEntryAuthoringTests(unittest.TestCase):
    def combined(self):
        additions = {move.move_id: move for move in SPECIALIST_ENTRY_DEVELOPMENT}
        for move in MOVE_DEFINITIONS:
            if move.move_id in additions:
                self.assertEqual(move, additions[move.move_id])
        return (*[move for move in MOVE_DEFINITIONS if move.move_id not in additions],
                *SPECIALIST_ENTRY_DEVELOPMENT)

    def test_five_unique_neutral_valid_definitions_and_acyclic_successors(self):
        combined = self.combined()
        self.assertEqual(len(SPECIALIST_ENTRY_DEVELOPMENT), 5)
        self.assertEqual(Counter(move.parent_action for move in SPECIALIST_ENTRY_DEVELOPMENT),
                         {"front_headlock": 1, "force_cage": 4})
        self.assertEqual(validate_move_registry(combined), [])
        self.assertEqual(len({move.name for move in combined}), len(combined))
        MoveChainGraph(combined)
        existing = {move.move_id: move for move in MOVE_DEFINITIONS}
        for move in SPECIALIST_ENTRY_DEVELOPMENT:
            self.assertEqual((move.energy, move.miss_risk, move.counter_risk), (1, 1, 1))
            self.assertLessEqual(move.minimum_skill, 50)
            self.assertTrue(1 <= len(move.follow_ups) <= 3)
            settled = "front headlock" if move.parent_action == "front_headlock" else "cage"
            for followup in move.follow_ups:
                self.assertIn(followup, existing)
                self.assertIn(settled, existing[followup].positions)
                self.assertTrue(sequence_role_allows(existing[followup].parent_action, settled,
                                                    "a", "a" if settled == "front headlock" else None,
                                                    "b" if settled == "front headlock" else None))

    def test_exact_preselection_positions_and_four_move_failed_shot_pool(self):
        index = MoveIndex(self.combined())
        self.assertGreaterEqual(len(index.legal_moves("force_cage", "failed shot")), 4)
        for move in SPECIALIST_ENTRY_DEVELOPMENT:
            expected = "clinch" if move.parent_action == "front_headlock" else "failed shot"
            self.assertEqual(move.positions, {expected})
            for position in ALL_POSITIONS:
                self.assertEqual(move in index.legal_moves(move.parent_action, position), position == expected)

    def test_each_identity_produces_legal_payload_without_rng_or_registration(self):
        engine = FightAuditHarness()
        actor = synthetic_fighter("Payload A", 75, "Well-Rounded", "Control", 0)
        defender = synthetic_fighter("Payload B", 75, "Wrestler", "Control", 1)
        original_ids = tuple(move.move_id for move in MOVE_DEFINITIONS)
        before = random.getstate()
        self.addCleanup(random.setstate, before)
        for move in SPECIALIST_ENTRY_DEVELOPMENT:
            index = MoveIndex((move,))
            position = next(iter(move.positions))
            for actor_key in ("a", "b"):
                state = {"round": 1, "tick": 2, "position": position,
                         "fighter_keys": {id(actor): actor_key, id(defender): "b" if actor_key == "a" else "a"},
                         "top": None, "bottom": None, "clinch_controller": actor_key}
                with patch("fight_engine.legal_moves", side_effect=index.legal_moves):
                    payload = engine.select_exchange_move(actor, defender, move.parent_action, position, "", state)
                self.assertEqual(payload["move_id"], move.move_id)
                self.assertFalse(payload["generic"])
        self.assertEqual(random.getstate(), before)
        self.assertEqual(tuple(move.move_id for move in MOVE_DEFINITIONS), original_ids)


if __name__ == "__main__":
    unittest.main()
