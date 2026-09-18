"""Retired move IDs remain loadable but cannot be selected or newly learned."""
from dataclasses import replace
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import MOVE_DEFINITIONS, MOVE_REGISTRY, MoveDefinition, MoveIndex
from fight_moves.registry import normalize_move_mastery, normalize_signature_moves
from fight_moves.validation import validate_move_registry
from seeding import SeedMixin
from world import WorldMixin
from fight_release import ReleaseFightEngineMixin


class DevelopmentHarness(SeedMixin, WorldMixin, FightAuditHarness):
    pass


class ReleaseDevelopmentHarness(SeedMixin, WorldMixin, ReleaseFightEngineMixin, FightAuditHarness):
    pass


class DeprecationTests(unittest.TestCase):
    def setUp(self):
        self.engine = DevelopmentHarness()
        self.fighter = synthetic_fighter("Retirement compatibility", 80, "Boxer", "Pressure", 0)
        self.fighter.signature_moves = []
        self.fighter.move_mastery = {}

    def retired(self):
        return replace(MOVE_REGISTRY["single_jab"], deprecated=True)

    def test_default_is_false_and_only_real_booleans_are_valid(self):
        self.assertIs(MoveDefinition.__dataclass_fields__["deprecated"].default, False)
        self.assertTrue(all(m.deprecated is False for m in MOVE_DEFINITIONS))
        for value in ("false", 0, None):
            definitions = (replace(MOVE_DEFINITIONS[0], deprecated=value), *MOVE_DEFINITIONS[1:])
            self.assertTrue(any("deprecated" in error for error in validate_move_registry(definitions)))

    def test_retired_move_is_absent_from_every_active_index(self):
        retired = self.retired()
        index = MoveIndex((retired,))
        self.assertEqual(index.by_action(retired.parent_action), ())
        for position in retired.positions:
            for target in ("", "head", "body", "unknown", None):
                self.assertEqual(index.legal_moves(retired.parent_action, position, target), ())
        for style in retired.preferred_styles:
            self.assertEqual(index.by_style(style), ())
        for tag in retired.tags:
            self.assertEqual(index.by_tag(tag), frozenset())

    def test_stored_signatures_and_mastery_retain_the_permanent_id(self):
        retired = self.retired()
        with patch("fight_moves.registry.MOVE_REGISTRY", {retired.move_id: retired}):
            self.assertEqual(normalize_signature_moves([retired.move_id]), [retired.move_id])
            self.assertEqual(normalize_move_mastery({retired.move_id: 81}), {retired.move_id: 81})
        self.fighter.signature_moves = [retired.move_id]
        with patch("seeding.MOVE_DEFINITIONS", (retired,)):
            self.assertEqual(self.engine.assign_fighter_signature_moves(self.fighter), [retired.move_id])

    def test_new_generated_signatures_cannot_acquire_a_retired_move(self):
        with patch("seeding.MOVE_DEFINITIONS", (self.retired(),)):
            self.assertEqual(self.engine.assign_fighter_signature_moves(self.fighter), [])

    def test_retired_successor_does_not_seed_an_impossible_live_chain(self):
        retired = self.retired()
        event = {"actor": "a", "round": 1, "tick": 1, "move_id": "double_jab",
                 "position_after": "range", "outcome": "landed",
                 "move": {"follow_up_ids": [retired.move_id]}}
        state = {}
        with patch("fight_engine.MOVE_REGISTRY", {retired.move_id: retired}):
            self.engine.update_move_sequence(state, event)
        self.assertEqual(state["move_chains"]["a"], {})
        self.assertFalse(event["move_sequence"]["continuation_available"])

    def test_camps_do_not_develop_or_promote_retired_mastery(self):
        retired = self.retired()
        for host in (DevelopmentHarness, ReleaseDevelopmentHarness):
            engine = host()
            # Development now reads the host's explicit profile. Patching a
            # disconnected world-module alias would not actually retire a move.
            with patch.object(host, "_fight_move_registry", {retired.move_id: retired}):
                for stored_mastery in ({}, {retired.move_id: 80}):
                    self.fighter.signature_moves = []
                    self.fighter.move_mastery = stored_mastery.copy()
                    engine.develop_fighter_move_mastery(self.fighter, weeks=12, focus="Boxing")
                    self.assertNotIn(retired.move_id, self.fighter.signature_moves)
                    self.assertEqual(self.fighter.move_mastery.get(retired.move_id), stored_mastery.get(retired.move_id))
                self.fighter.signature_moves = [retired.move_id]
                self.fighter.move_mastery = {retired.move_id: 40}
                engine.develop_fighter_move_mastery(self.fighter, weeks=12)
                self.assertEqual(self.fighter.signature_moves, [retired.move_id])
                self.assertEqual(self.fighter.move_mastery[retired.move_id], 40)


if __name__ == "__main__":
    unittest.main()
