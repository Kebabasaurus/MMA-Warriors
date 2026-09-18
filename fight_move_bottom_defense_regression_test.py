"""Phase 30/33 authoring coverage before and after runtime integration."""
from collections import Counter
import unittest

from fight_moves import MOVE_DEFINITIONS, DEFENSE_DEFINITIONS, GROUND_POSITIONS, MoveIndex
from fight_moves.catalogue.bottom_development import PHASE_30
from fight_moves.defense_expansion import PHASE_33_DEFENSES
from fight_moves.validation import validate_move_registry, validate_defense_registry


class BottomDefenseExpansionTests(unittest.TestCase):
    def test_named_defenses_respect_weapon_and_target(self):
        from fight_engine_audit import FightAuditHarness, synthetic_fighter
        engine = FightAuditHarness()
        fighter = synthetic_fighter("Defense probe", 85, "Boxer", "Counter", 1)
        fighter.move_mastery = {"defense:elbow_in_body_block": 100, "defense:shoulder_roll": 100}
        for tick in range(1, 50):
            payload = {"parent_action": "kick", "tags": ("strike", "kick"), "target": "head", "defense_families": ("block",)}
            selected = engine.select_exchange_defense(fighter, payload, "range", {"round": 1, "tick": tick})
            self.assertNotIn(selected["defense_id"], {"elbow_in_body_block", "shoulder_roll"})

    def test_restricted_defenses_are_selectable_in_valid_attack_contexts(self):
        from fight_engine_audit import FightAuditHarness, synthetic_fighter
        engine = FightAuditHarness()
        fighter = synthetic_fighter("Positive defense probe", 85, "Boxer", "Counter", 1)
        fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 85)
        for defense_id, target in (("elbow_in_body_block", "body"), ("shoulder_roll", "head")):
            fighter.move_mastery = {f"defense:{defense_id}": 100}
            payload = {"parent_action": "power_punch", "tags": ("strike", "punch"),
                       "target": target, "defense_families": ("block",)}
            selected = engine.select_exchange_defense(fighter, payload, "range", {"round": 1, "tick": 1})
            self.assertEqual(selected["defense_id"], defense_id)

    def test_shoulder_roll_rejects_nonboxing_power_actions(self):
        from fight_engine_audit import FightAuditHarness, synthetic_fighter
        engine = FightAuditHarness()
        fighter = synthetic_fighter("Weapon defense probe", 85, "Boxer", "Counter", 1)
        fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 85)
        fighter.move_mastery = {"defense:shoulder_roll": 100}
        for weapon in ("knee", "elbow", "kick"):
            for action in ("power_punch", "dirty_boxing"):
                with self.subTest(weapon=weapon, action=action):
                    payload = {"parent_action": action, "tags": ("strike", weapon),
                               "target": "head", "defense_families": ("block",)}
                    selected = engine.select_exchange_defense(
                        fighter, payload, "range", {"round": 1, "tick": 1})
                    self.assertNotEqual(selected["defense_id"], "shoulder_roll")

    def test_exact_action_budget_and_followups(self):
        self.assertEqual(Counter(m.parent_action for m in PHASE_30), {
            "recover_guard": 10, "sweep": 8, "stand_up": 6, "cling": 5, "survive": 4})
        self.assertTrue(all(1 <= len(m.follow_ups) <= 3 for m in PHASE_30))
        ids = {m.move_id for m in MOVE_DEFINITIONS}
        combined = (*MOVE_DEFINITIONS, *(m for m in PHASE_30 if m.move_id not in ids))
        self.assertEqual(validate_move_registry(combined), [])

    def test_every_ground_position_has_four_recoveries(self):
        ids = {m.move_id for m in MOVE_DEFINITIONS}
        index = MoveIndex((*MOVE_DEFINITIONS, *(m for m in PHASE_30 if m.move_id not in ids)))
        for position in GROUND_POSITIONS:
            with self.subTest(position=position):
                self.assertGreaterEqual(len(index.legal_moves("recover_guard", position)), 4)

    def test_defense_families_have_two_concrete_answers(self):
        self.assertEqual(len(PHASE_33_DEFENSES), 22)
        ids = {d.defense_id for d in DEFENSE_DEFINITIONS}
        combined = (*DEFENSE_DEFINITIONS, *(d for d in PHASE_33_DEFENSES if d.defense_id not in ids))
        self.assertEqual(validate_defense_registry(combined), [])
        for family in {f for m in MOVE_DEFINITIONS for f in m.defense_families}:
            with self.subTest(family=family):
                self.assertGreaterEqual(sum(family in d.families for d in combined), 2)


if __name__ == "__main__":
    unittest.main()
