"""Actual-action branching, ownership and observed sequence depth."""
import random
import unittest
from unittest.mock import patch
from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import MOVE_REGISTRY


class SequenceTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.a = synthetic_fighter("Chain A", 88, "Boxer", "Pressure", 1)
        self.b = synthetic_fighter("Chain B", 88, "Wrestler", "Pressure", 2)
        self.state = {"fighter_keys": {id(self.a): "a", id(self.b): "b"}, "round": 1, "tick": 2,
                      "plans": self.engine.fight_plan_state(self.a, self.b, {})}

    def select_only(self, move_id, position="range", ownership=None):
        definition = MOVE_REGISTRY[move_id]
        with patch("fight_engine.legal_moves", return_value=(definition,)):
            return self.engine.select_exchange_move(self.a, self.b, definition.parent_action,
                position, next(iter(definition.targets), ""), self.state, ownership_before=ownership)

    def root(self):
        event = {"actor": "a", "round": 1, "tick": 1, "move_id": "single_jab", "outcome": "landed",
                 "position_after": "range", "defense": {"tags": ["evasion"]},
                 "move": {"follow_up_ids": ["one_two", "jab_to_shot"]}}
        self.engine.update_move_sequence(self.state, event)
        return event

    def test_actual_action_can_select_alternate_and_preserves_occurrence(self):
        root = self.root()
        self.assertEqual(self.state["move_chains"]["a"]["next_move_id"], "jab_to_shot")
        before = random.getstate()
        move = self.select_only("one_two")
        self.assertEqual(random.getstate(), before)
        self.assertEqual(move["sequence_source_id"], "single_jab")
        self.assertEqual(move["sequence_step"], 2)
        event = {"actor": "a", "round": 1, "tick": 2, "move_id": "one_two", "outcome": "landed",
                 "position_after": "range", "move": move}
        self.engine.update_move_sequence(self.state, event)
        self.assertEqual((root["chain_depth"], event["chain_depth"]), (1, 2))
        self.assertEqual(root["sequence_occurrence_id"], event["sequence_occurrence_id"])
        self.state["tick"] = 3
        third = self.select_only("lead_hook_cross")
        self.assertEqual(third["sequence_step"], 3)

    def test_expiry_horn_and_unrelated_selection_do_not_inherit_chain(self):
        for tick, round_no in ((4, 1), (2, 2)):
            self.root()
            self.state.update(tick=tick, round=round_no)
            self.assertEqual(self.select_only("one_two")["sequence_source_id"], "")
        self.state.update(tick=2, round=1)
        self.root()
        self.assertEqual(self.select_only("body_round_kick")["sequence_step"], 0)

    def test_successful_same_position_sweep_seeds_only_top_successors(self):
        event = {"actor": "a", "round": 1, "tick": 1, "move_id": "butterfly_sweep", "outcome": "control",
                 "position_after": "guard", "top_before": "b", "top_after": "a", "bottom_after": "b",
                 "move": {"follow_up_ids": ["guard_submission_chain", "chest_to_chest_pin"]}}
        self.engine.update_move_sequence(self.state, event)
        self.assertEqual(self.state["move_chains"]["a"]["branch_options"], ["chest_to_chest_pin"])
        self.assertEqual(event["outcome"], "control")
        event["referee_ground_action"] = {"type": "standup"}
        self.engine.update_move_sequence(self.state, event)
        self.assertEqual(self.state["move_chains"]["a"], {})

    def test_selection_uses_pre_exchange_ownership_not_sweep_result(self):
        self.state.update(top="a", bottom="b", move_chains={"a": {
            "round": 1, "tick": 1, "actor_role": "bottom", "source_move_id": "kimura_guard",
            "step": 1, "branch_options": ["butterfly_sweep"], "next_move_id": "butterfly_sweep"}})
        self.assertEqual(self.select_only("butterfly_sweep", "guard")["sequence_step"], 0)
        selected = self.select_only("butterfly_sweep", "guard", {"top": "b", "bottom": "a"})
        self.assertEqual(selected["sequence_step"], 2)

    def test_continuations_do_not_bypass_skill_or_style_eligibility(self):
        for move_id in ("lead_hook_cross", next(m.move_id for m in MOVE_REGISTRY.values()
                        if "style-combination" in m.tags and m.preferred_styles != ("Boxer",))):
            self.state["move_chains"] = {"a": {"round": 1, "tick": 1, "source_move_id": "single_jab",
                "step": 1, "branch_options": [move_id], "next_move_id": move_id}}
            if move_id == "lead_hook_cross":
                self.a.detailed_skills = dict.fromkeys(self.a.detailed_skills, 10)
            selected = self.select_only(move_id)
            self.assertTrue(selected["generic"])
            self.assertEqual(selected["sequence_step"], 0)

    def test_target_restriction_survives_live_continuation(self):
        self.state["move_chains"] = {"a": {"round": 1, "tick": 1, "source_move_id": "single_jab",
            "step": 1, "branch_options": ["head_round_kick"], "next_move_id": "head_round_kick"}}
        selected = self.engine.select_exchange_move(self.a, self.b, "kick", "range", "body", self.state)
        self.assertNotEqual(selected["move_id"], "head_round_kick")
        self.assertEqual(selected["sequence_step"], 0)

    def test_specialist_roles_match_the_action_resolver(self):
        from fight_moves.chains import sequence_actor_role, sequence_role_allows
        for position, top_actions, bottom_actions in (
            ("turtle", ("take_back", "ground_strikes", "turtle_ride"),
             ("turtle_escape", "recover_guard", "stand_up")),
            ("front headlock", ("front_headlock_submission", "take_back", "turtle_ride"),
             ("front_headlock_escape", "recover_guard")),
            ("leg entanglement", ("leg_attack", "leg_control", "disengage_leg"),
             ("leg_escape", "counter_leg_lock")),
        ):
            for actor, expected, allowed, denied in (
                ("a", "top", top_actions, bottom_actions),
                ("b", "bottom", bottom_actions, top_actions),
            ):
                with self.subTest(position=position, actor=actor):
                    self.assertEqual(sequence_actor_role(position, actor, "a", "b"), expected)
                    self.assertTrue(all(sequence_role_allows(action, position, actor, "a", "b")
                                        for action in allowed))
                    self.assertFalse(any(sequence_role_allows(action, position, actor, "a", "b")
                                         for action in denied))


if __name__ == "__main__":
    unittest.main()
