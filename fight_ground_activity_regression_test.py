"""Specialist attempts are activity; stationary rides still trigger stand-ups."""
from collections import defaultdict
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter


class GroundActivityTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.a = synthetic_fighter("Activity A", 75, "BJJ", "Control", 0)
        self.b = synthetic_fighter("Activity B", 75, "Wrestler", "Control", 1)
        self.addCleanup(random.setstate, random.getstate())

    def state(self, position, top="a"):
        return {
            "position": position, "top": top, "bottom": "b" if top == "a" else "a",
            "clinch_controller": None, "ground_inactivity": 3, "ground_warning": True,
            "fighter_keys": {id(self.a): "a", id(self.b): "b"},
            "stats": {key: defaultdict(int) for key in ("a", "b")},
            "gas": {"a": 80, "b": 80}, "danger": {"a": 0, "b": 0},
        }

    def test_resolved_specialist_attempts_reset_warning_for_both_owners(self):
        cases = (
            ("front_headlock_submission", "front headlock", True, -30),
            ("leg_attack", "leg entanglement", True, -30),
            ("take_back", "turtle", True, -30),
            ("front_headlock_escape", "front headlock", False, 0),
            ("turtle_escape", "turtle", False, -30),
            ("leg_escape", "leg entanglement", False, -30),
            ("counter_leg_lock", "leg entanglement", False, -30),
            ("counter_leg_lock", "leg entanglement", False, 30),
        )
        for top in ("a", "b"):
            for action, position, actor_on_top, margin in cases:
                with self.subTest(top=top, action=action, margin=margin):
                    state = self.state(position, top)
                    actor_key = top if actor_on_top else state["bottom"]
                    actor, defender = (self.a, self.b) if actor_key == "a" else (self.b, self.a)
                    stats = {key: defaultdict(int) for key in ("a", "b")}
                    # Fix only the exchange contest, leaving real specialist
                    # resolution and its failed-attempt consequences in place.
                    with patch.object(self.engine, "action_attack_value", return_value=margin), \
                         patch.object(self.engine, "action_defence_value", return_value=0), \
                         patch.object(self.engine, "fight_mechanics_rng") as rng:
                        rng.return_value.randint.return_value = 0
                        rng.return_value.choice.side_effect = lambda options: options[0]
                        self.engine._resolve_exchange_action(actor, defender, action, state, stats)
                    self.engine.validate_fight_transition(position, state["position"], state)
                    position_after = state["position"]
                    ownership = (state["top"], state["bottom"])
                    if action in ("leg_attack", "front_headlock_submission"):
                        self.assertEqual(state["stats"][actor_key]["sub_att"], 1)
                    self.assertEqual(self.engine.update_ground_inactivity(state, action), "")
                    self.assertEqual(state["ground_inactivity"], 0)
                    self.assertFalse(state["ground_warning"])
                    self.assertIsNone(state["last_referee_ground_action"])
                    self.assertEqual(state["position"], position_after)
                    self.assertEqual((state["top"], state["bottom"]), ownership)

    def test_static_holds_warn_then_stand_up_at_referee_threshold(self):
        for top in ("a", "b"):
            for action, position in (("turtle_ride", "turtle"), ("leg_control", "leg entanglement"),
                                     ("ground_control", "guard"), ("cling", "guard"), ("survive", "turtle")):
                for threshold in (4, 6):
                    with self.subTest(top=top, action=action, threshold=threshold):
                        state = self.state(position, top)
                        state.update(ground_inactivity=0, ground_warning=False)
                        with patch.object(self.engine, "referee_profile", return_value={"standup_threshold": threshold}):
                            for beat in range(1, threshold + 1):
                                self.engine.update_ground_inactivity(state, action)
                                if beat < threshold:
                                    self.assertEqual(state["position"], position)
                                if beat == 3:
                                    self.assertEqual(state["last_referee_ground_action"]["type"], "warning")
                        self.assertEqual(state["position"], "range")
                        self.assertEqual(state["last_referee_ground_action"]["type"], "standup")
                        self.assertIsNone(state["top"])
                        self.assertIsNone(state["bottom"])
                        self.assertIsNone(state["clinch_controller"])

    def test_common_attempt_semantics_and_standing_reset_unchanged(self):
        for action in ("ground_strikes", "advance_position", "recover_guard", "submission",
                       "bottom_submission", "sweep", "stand_up"):
            state = self.state("guard")
            before = random.getstate()
            self.assertEqual(self.engine.update_ground_inactivity(state, action), "")
            self.assertEqual(random.getstate(), before)
            self.assertEqual(state["ground_inactivity"], 0)
            self.assertFalse(state["ground_warning"])
        for position in ("range", "pocket", "clinch", "cage", "failed shot", "standing back control"):
            state = self.state(position)
            self.engine.update_ground_inactivity(state, "survive")
            self.assertEqual(state["ground_inactivity"], 0)
            self.assertFalse(state["ground_warning"])


if __name__ == "__main__":
    unittest.main()
