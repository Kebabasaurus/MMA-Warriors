"""Ordinary failed-shot/front-headlock entries and bounded legal exits."""
from collections import defaultdict
from contextlib import redirect_stdout
import io
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, run_audited_fight, synthetic_fighter


class SpecialistEntryTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.engine._experimental_specialist_entries = True
        self.a = synthetic_fighter("Same Name", 75, "Wrestler", "Control", 0)
        self.b = synthetic_fighter("Same Name", 75, "BJJ", "Submission Hunter", 1)
        for fighter in (self.a, self.b):
            fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 75)
        self.addCleanup(random.setstate, random.getstate())

    def state(self, position="range", controller=None):
        state = {"position": position, "top": None, "bottom": None,
                 "clinch_controller": controller, "round": 1, "tick": 1,
                 "fighter_keys": {id(self.a): "a", id(self.b): "b"},
                 "stats": {key: defaultdict(int) for key in ("a", "b")},
                 "ground_warning": False, "ground_inactivity": 0}
        for channel in ("gas", "gas_cap"):
            state[channel] = {"a": 80, "b": 80}
        for channel in ("unanswered", "hurt", "head", "danger"):
            state[channel] = {"a": 0, "b": 0}
        return state

    def test_normal_play_does_not_enable_candidate(self):
        engine = FightAuditHarness()
        self.assertFalse(getattr(engine, "_experimental_specialist_entries", False))
        with patch.object(engine, "weighted_choice", side_effect=lambda weights: weights):
            choices = engine.choose_action(self.a, self.b, self.state("clinch"), 1, 1)
        self.assertNotIn("front_headlock", choices)
        state = self.state()
        with patch.object(engine, "ds", return_value=75):
            engine.resolve_takedown(self.a, self.b, -30, state, self.stats())
        self.assertEqual(state["position"], "range")

    def test_candidate_evaluator_is_scoped_read_only_and_rejects_failure(self):
        from analysis import evaluate_specialist_entry_candidate as evaluator

        def candidate_result(_seeds):
            self.assertTrue(FightAuditHarness._experimental_specialist_entries)
            return {"fight_count": 3840, "groups": {"Overall": {}}}

        output = io.StringIO()
        with patch.object(evaluator, "build_baseline", side_effect=candidate_result), \
             patch.object(evaluator, "compare_to_baseline", return_value=[]), \
             patch.object(evaluator, "compare_to_accepted_calibration", return_value=["rejected"]), \
             patch.object(evaluator.Path, "write_text", side_effect=AssertionError("reference write")), \
             patch.object(evaluator.Path, "write_bytes", side_effect=AssertionError("reference write")), \
             redirect_stdout(output):
            self.assertEqual(evaluator.main(), 1)
        self.assertIn('"rejected"', output.getvalue())
        self.assertFalse(getattr(FightAuditHarness, "_experimental_specialist_entries", False))

    def stats(self):
        return {key: defaultdict(int) for key in ("a", "b")}

    def resolve(self, actor, defender, action, state, margin):
        with patch.object(self.engine, "action_attack_value", return_value=margin), \
             patch.object(self.engine, "action_defence_value", return_value=0), \
             patch.object(self.engine, "fight_mechanics_rng") as rng:
            rng.return_value.randint.return_value = 0
            result = self.engine.resolve_exchange(actor, defender, action, state, self.stats())
            self.assertEqual(rng.return_value.randint.call_count, 1)
            rng.return_value.random.assert_not_called()
        return result

    def test_matched_stuffed_entry_and_skill_sensitive_clean_reset_without_rng(self):
        for actor, defender, defender_key in ((self.a, self.b, "b"), (self.b, self.a, "a")):
            for margin, expected in ((-30, "failed shot"), (-18, "range"), (-9, "range"), (0, "cage")):
                with self.subTest(defender=defender_key, margin=margin):
                    state = self.state()
                    with patch.object(self.engine, "ds", return_value=75), \
                         patch.object(self.engine, "fight_mechanics_rng") as rng:
                        self.engine.resolve_takedown(actor, defender, margin, state, self.stats())
                        rng.assert_not_called()
                    self.assertEqual(state["position"], expected)
                    self.engine.validate_fight_transition("range", expected, state)
                    if expected == "failed shot":
                        self.assertEqual(state["clinch_controller"], defender_key)
            state = self.state()
            with patch.dict(actor.detailed_skills, {"scrambles": 90, "get_ups": 90}):
                self.engine.resolve_takedown(actor, defender, -30, state, self.stats())
            self.assertEqual(state["position"], "range")

    def test_clinch_snapdown_is_contested_and_not_an_open_range_or_cage_action(self):
        for actor, defender, actor_key in ((self.a, self.b, "a"), (self.b, self.a, "b")):
            for position in ("range", "clinch", "cage"):
                with patch.object(self.engine, "weighted_choice", side_effect=lambda weights: weights):
                    weights = self.engine.choose_action(actor, defender, self.state(position), 1, 1)
                self.assertEqual("front_headlock" in weights, position == "clinch")
            for margin, expected in ((0, "front headlock"), (-5, "range")):
                state = self.state("clinch", actor_key)
                text = self.resolve(actor, defender, "front_headlock", state, margin)
                self.assertEqual(state["position"], expected)
                self.engine.validate_fight_transition("clinch", expected, state)
                if expected == "front headlock":
                    self.assertEqual(state["top"], actor_key)
                    self.assertIn("snaps", text)
                    self.assertNotIn("sprawls", text)

    def test_next_action_roles_and_failed_shot_exits(self):
        for controller in ("a", "b"):
            state = self.state("failed shot", controller)
            for fighter, opponent, key in ((self.a, self.b, "a"), (self.b, self.a, "b")):
                with patch.object(self.engine, "weighted_choice", side_effect=lambda weights: weights):
                    choices = self.engine.choose_action(fighter, opponent, state, 1, 1)
                self.assertEqual(set(choices), {"front_headlock", "force_cage", "disengage"}
                                 if key == controller else {"re_shot", "recover_shot"})
            actor, defender = (self.a, self.b) if controller == "a" else (self.b, self.a)
            for action, margin, expected in (("front_headlock", 0, "front headlock"),
                                              ("disengage", 0, "range"), ("force_cage", 0, "cage")):
                state = self.state("failed shot", controller)
                self.resolve(actor, defender, action, state, margin)
                self.assertEqual(state["position"], expected)
                self.engine.validate_fight_transition("failed shot", expected, state)
            state = self.state("failed shot", controller)
            for beat in range(3):
                self.resolve(actor, defender, "survive", state, 0)
                self.assertEqual(state["position"], "range" if beat == 2 else "failed shot")
            self.assertIsNone(state["clinch_controller"])
            self.assertEqual(state["failed_shot_stall_ticks"], 0)

    def test_front_headlock_escape_and_inactivity_exit(self):
        for top in ("a", "b"):
            state = self.state("front headlock")
            state.update(top=top, bottom="b" if top == "a" else "a")
            for fighter, opponent, key in ((self.a, self.b, "a"), (self.b, self.a, "b")):
                with patch.object(self.engine, "weighted_choice", side_effect=lambda weights: weights):
                    choices = self.engine.choose_action(fighter, opponent, state, 1, 1)
                self.assertEqual(set(choices), {"front_headlock_submission", "take_back", "turtle_ride"}
                                 if key == top else {"front_headlock_escape", "recover_guard"})
            actor, defender = (self.b, self.a) if top == "a" else (self.a, self.b)
            self.resolve(actor, defender, "front_headlock_escape", state, 6)
            self.assertEqual(state["position"], "guard")
            self.assertEqual(state["top"], top)
            state.update(position="front headlock")
            with patch.object(self.engine, "referee_profile", return_value={"standup_threshold": 4}):
                for _ in range(4):
                    self.engine.update_ground_inactivity(state, "survive")
            self.assertEqual(state["position"], "range")
            self.assertIsNone(state["top"])
            self.assertIsNone(state["bottom"])

    def test_neutral_stall_reset_has_structured_non_referee_commentary(self):
        for controller in ("a", "b"):
            for actor, defender in ((self.a, self.b), (self.b, self.a)):
                with self.subTest(controller=controller, actor=id(actor)):
                    state = self.state("failed shot", controller)
                    for beat in range(3):
                        self.resolve(actor, defender, "survive", state, 0)
                        if beat < 2:
                            self.assertNotIn("last_neutral_scramble_reset", state)
                    fact = state["last_neutral_scramble_reset"]
                    self.assertEqual(fact, {
                        "reason": "stalled_failed_shot", "position_before": "failed shot",
                        "position_after": "range", "controller_before": controller})
                    event = {"action": "survive", "outcome": "position_change",
                             "move_id": "composed_survival", "move": {"name": "composed survival"},
                             "position_before": "failed shot", "position_after": "range",
                             "neutral_scramble_reset": dict(fact),
                             "result": "UNTRUSTED OLD RESOLVER PROSE"}
                    self.assertEqual(self.engine.exchange_commentary_kind(event), "neutral_reset")
                    for technical in (False, True):
                        text = self.engine.render_exchange_trace_event(event, technical=technical)
                        self.assertIn("both fighters release the grips", text)
                        self.assertIn("reset at range", text)
                        self.assertNotIn("referee", text.lower())
                        self.assertNotIn("UNTRUSTED", text)
                    self.resolve(actor, defender, "survive", state, 0)
                    self.assertNotIn("last_neutral_scramble_reset", state)

    def test_complete_matched_bouts_reach_settled_specialists_and_reset_at_horn(self):
        observed, rounds = set(), 0
        for seed in range(48100, 48148):
            audit = run_audited_fight(self.engine, self.a, self.b, seed, {})
            events = [event for event in audit["trace"] if event.get("type") == "exchange"]
            observed.update(event["position_before"] for event in events)
            for index, event in enumerate(events):
                if index == 0 or event["round"] != events[index - 1]["round"]:
                    self.assertEqual(event["position_before"], "range")
                    self.assertIsNone(event.get("top_before"))
                    self.assertIsNone(event.get("bottom_before"))
                    rounds += event["round"] >= 2
        self.assertTrue({"failed shot", "front headlock"} <= observed, observed)
        self.assertGreater(rounds, 0)


if __name__ == "__main__":
    unittest.main()
