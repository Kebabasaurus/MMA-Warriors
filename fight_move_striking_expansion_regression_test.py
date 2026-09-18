"""Authoring and integration gates for the standing/clinch expansion slices."""
from dataclasses import replace
import unittest

from fight_moves import MOVE_DEFINITIONS, MoveIndex
from fight_moves.catalogue.power_punch_development import POWER_PUNCH_DEVELOPMENT
from fight_moves.catalogue.jab_development import JAB_DEVELOPMENT
from fight_moves.followup_diversity import ACTION_DIVERSE_FOLLOWUP_UPDATES
from fight_moves.followup_continuity import CONTINUITY_FOLLOWUP_UPDATES
from fight_moves.validation import validate_move_registry

APPLIED_FOLLOWUP_UPDATES = {**ACTION_DIVERSE_FOLLOWUP_UPDATES, **CONTINUITY_FOLLOWUP_UPDATES}


class StrikingExpansionTests(unittest.TestCase):
    def test_referee_reset_is_not_a_fighter_or_camp_achievement(self):
        from unittest.mock import patch
        from fight_engine_audit import FightAuditHarness
        engine = FightAuditHarness()
        event = {"actor_name": "Resilient fighter", "actor_commentary_profile": {"trait": "Iron Chin"},
                 "actor_damage_after": 30, "actor_camp": "Test gym", "actor_coach": "Test coach",
                 "actor_camp_specialties": ["Boxing"], "action": "power_punch",
                 "move": {"tags": ["punch"]}, "outcome": "position_change"}
        with patch.object(engine, "stable_commentary_due", return_value=True):
            self.assertTrue(engine.trait_exchange_commentary(event, "transitioned"))
            self.assertTrue(engine.camp_exchange_commentary(event, "transitioned"))
            event["referee_ground_action"] = {"type": "standup"}
            for kind in ("transitioned", "referee_standup"):
                self.assertEqual(engine.trait_exchange_commentary(event, kind), "")
                self.assertEqual(engine.camp_exchange_commentary(event, kind), "")

    def test_registration_and_ordinary_appearance_gate(self):
        from analysis.compare_striking_move_expansion import SLICE_5
        from analysis.generate_move_coverage_report import slice_5_failures
        from fight_moves.legacy_ids import EXPANSION_MOVE_IDS
        registered = {m.move_id: m for m in MOVE_DEFINITIONS}
        self.assertEqual(len(SLICE_5), 53)
        for definition in SLICE_5:
            expected = replace(definition, follow_ups=APPLIED_FOLLOWUP_UPDATES.get(
                definition.move_id, definition.follow_ups))
            self.assertEqual(registered[definition.move_id], expected)
            self.assertIn(definition.move_id, EXPANSION_MOVE_IDS)
        ids = [m.move_id for m in SLICE_5]
        self.assertEqual(slice_5_failures({"observed_move_ids": ids}), [])
        self.assertEqual(slice_5_failures({"observed_move_ids": ids[1:]}),
                         [f"Slice 5 move absent: {ids[0]}"])

    def test_jab_budget_and_followups(self):
        self.assertEqual(len(JAB_DEVELOPMENT), 6)
        existing = {m.move_id for m in MOVE_DEFINITIONS}
        definitions = (*MOVE_DEFINITIONS, *(m for m in JAB_DEVELOPMENT if m.move_id not in existing))
        self.assertEqual(validate_move_registry(definitions), [])
        for definition in JAB_DEVELOPMENT:
            self.assertEqual(definition.parent_action, "jab")
            self.assertTrue(1 <= len(definition.follow_ups) <= 3)
            self.assertEqual((definition.energy, definition.miss_risk, definition.counter_risk), (1, 1, 1))
        index = MoveIndex(JAB_DEVELOPMENT)
        self.assertEqual(len(index.legal_moves("jab", "range", "body")), 6)
        self.assertEqual(len(index.legal_moves("jab", "range", "head")), 4)

    def test_power_punch_budget_and_metadata(self):
        self.assertEqual(len(POWER_PUNCH_DEVELOPMENT), 10)
        existing = {m.move_id for m in MOVE_DEFINITIONS}
        definitions = (*MOVE_DEFINITIONS, *(m for m in POWER_PUNCH_DEVELOPMENT if m.move_id not in existing))
        self.assertEqual(validate_move_registry(definitions), [])
        self.assertEqual(len({m.move_id for m in POWER_PUNCH_DEVELOPMENT}), 10)
        self.assertEqual(sum(m.targets == frozenset({"body"}) for m in POWER_PUNCH_DEVELOPMENT), 6)
        for definition in POWER_PUNCH_DEVELOPMENT:
            with self.subTest(move=definition.move_id):
                self.assertEqual(definition.parent_action, "power_punch")
                self.assertTrue(1 <= len(definition.follow_ups) <= 3)
                self.assertIn("punch", definition.tags)
                self.assertEqual((definition.energy, definition.miss_risk, definition.counter_risk), (1, 1, 1))

    def test_power_punch_target_pools(self):
        index = MoveIndex(POWER_PUNCH_DEVELOPMENT)
        for position in ("range", "pocket"):
            for target, count in (("body", 6), ("head", 4), ("leg", 0), ("", 0)):
                with self.subTest(position=position, target=target):
                    self.assertEqual(len(index.legal_moves("power_punch", position, target)), count)
        self.assertEqual(index.legal_moves("power_punch", "guard", "head"), ())


if __name__ == "__main__":
    unittest.main()
