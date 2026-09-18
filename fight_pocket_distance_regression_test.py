"""Opt-in persistent punch distance without invented strike/transition credit."""
from collections import defaultdict
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, run_audited_fight, synthetic_fighter


class PocketDistanceTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.a = synthetic_fighter("Pocket A", 75, "Boxer", "Pressure", 0)
        self.b = synthetic_fighter("Pocket B", 75, "Boxer", "Control", 1)
        for fighter in (self.a, self.b):
            fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 75)
        self.addCleanup(random.setstate, random.getstate())
        self.template = {}
        class Captured(Exception):
            pass
        def capture(_actor, _defender, state, *_args):
            self.template.update(deepcopy(state))
            raise Captured()
        with patch.object(self.engine, "choose_action", side_effect=capture):
            with self.assertRaises(Captured):
                self.engine.simulate_fight(self.a, self.b, {})
        self.engine._experimental_specialist_entries = True

    def state(self, position="range"):
        state = deepcopy(self.template)
        state.update(position=position, top=None, bottom=None, clinch_controller=None)
        return state

    def resolve(self, actor, defender, action, state, margin):
        stats = {key: defaultdict(int) for key in ("a", "b")}
        with patch.object(self.engine, "action_attack_value", return_value=margin), \
             patch.object(self.engine, "action_defence_value", return_value=0), \
             patch.object(self.engine, "fight_mechanics_rng") as rng:
            rng.return_value.randint.return_value = 0
            rng.return_value.random.return_value = 1.0
            rng.return_value.choice.side_effect = lambda options: options[0]
            result = self.engine.resolve_exchange(actor, defender, action, state, stats)
            calls = list(rng.mock_calls)
        return result, stats, calls

    def test_contested_entry_boundaries_reach_and_movement_both_orientations(self):
        for actor, defender, key in ((self.a, self.b, "a"), (self.b, self.a, "b")):
            for margin, expected in ((5, "range"), (10, "range"), (20, "pocket")):
                state = self.state()
                self.resolve(actor, defender, "power_punch", state, margin)
                self.assertEqual(state["position"], expected)
                if expected == "pocket":
                    self.assertEqual(state["last_distance_transition"],
                                     {"from": "range", "to": "pocket", "fighter": key, "reason": "pressure_entry"})
                self.engine.validate_fight_transition("range", expected, state)
            with patch.dict(actor.detailed_skills, {"reach": 55}):
                state = self.state()
                self.resolve(actor, defender, "power_punch", state, 10)
                self.assertEqual(state["position"], "pocket")
            with patch.dict(defender.detailed_skills, {"footwork": 95, "mobility": 95, "head_movement": 95}):
                state = self.state()
                self.resolve(actor, defender, "power_punch", state, 20)
                self.assertEqual(state["position"], "range")
            state = self.state("pocket")
            state["hurt"][key] = 10
            state["unanswered"][key] = 3
            self.resolve(actor, defender, "power_punch", state, -30)
            self.assertEqual(state["last_distance_transition"],
                             {"from": "pocket", "to": "range", "fighter": "b" if key == "a" else "a",
                              "reason": "defender_pivot"})
            self.assertEqual(state["hurt"][key], 10)
            self.assertEqual(state["unanswered"][key], 3)

    def test_distance_has_no_extra_damage_gas_rng_or_recovery_credit(self):
        for position, margin in (("range", 20), ("pocket", -30)):
            states, rounds, calls = [], [], []
            for enabled in (False, True):
                self.engine._experimental_specialist_entries = enabled
                state = self.state(position)
                state["hurt"]["a"] = 10
                state["unanswered"]["a"] = 3
                state["unanswered"]["b"] = 2
                _, stats, draws = self.resolve(self.a, self.b, "power_punch", state, margin)
                self.engine.apply_exchange_fatigue(self.a, self.b, "power_punch", state)
                states.append(state); rounds.append(stats); calls.append(draws)
            for channel in ("damage", "head", "body", "leg", "gas", "cuts", "knockdowns", "unanswered", "hurt", "stats"):
                self.assertEqual(states[0][channel], states[1][channel], channel)
            self.assertEqual(rounds[0], rounds[1])
            self.assertEqual(calls[0], calls[1])
            self.assertNotIn("last_distance_transition", states[0])
            if margin < 0:
                self.assertEqual(states[1]["last_distance_transition"]["fighter"], "b")
                self.assertEqual(states[1]["hurt"]["a"], 10)
                self.assertEqual(states[1]["unanswered"]["a"], 3)

    def test_persistent_next_menu_and_deliberate_jab_exit(self):
        state = self.state()
        self.resolve(self.a, self.b, "power_punch", state, 20)
        self.resolve(self.a, self.b, "power_punch", state, 0)
        self.assertEqual(state["position"], "pocket")
        self.assertNotIn("last_distance_transition", state)
        menus = {}
        for position in ("range", "pocket"):
            state["position"] = position
            with patch.object(self.engine, "weighted_choice", side_effect=lambda weights: dict(weights)):
                menus[position] = self.engine.choose_action(self.a, self.b, state, 1, 2)
        self.assertEqual(set(menus["range"]), set(menus["pocket"]))
        for action, factor in (("power_punch", 1.10), ("kick", .85), ("clinch", 1.05), ("jab", 1), ("shoot", 1)):
            self.assertAlmostEqual(menus["pocket"][action], menus["range"][action] * factor)
        self.engine._experimental_pocket_action_bias = False
        with patch.object(self.engine, "weighted_choice", side_effect=lambda weights: dict(weights)):
            unbiased = self.engine.choose_action(self.a, self.b, state, 1, 2)
        self.assertEqual(unbiased, menus["range"])
        with patch.dict(self.a.detailed_skills, {"reach": 95}):
            self.resolve(self.a, self.b, "jab", state, 30)
        self.assertEqual(state["position"], "range")
        self.assertEqual(state["last_distance_transition"]["reason"], "jab_exit")

    def test_knockdowns_finishes_and_existing_position_changes_are_protected(self):
        for effect in ("knockdown", "instant_finish", "submission_finish", "position"):
            state = self.state()
            def strike(_actor, _defender, _action, _margin, state, _stats):
                state["stats"]["a"]["sig"] += 1
                if effect == "knockdown":
                    state["knockdowns"]["a"] += 1
                elif effect == "position":
                    self.engine.set_fight_position(state, "guard", top="b", bottom="a")
                else:
                    state[effect] = ("a", "b", "finish")
                return "resolved strike"
            with patch.object(self.engine, "resolve_strike", side_effect=strike), \
                 patch.object(self.engine, "_update_punch_distance", side_effect=AssertionError("Overwrote resolved outcome")):
                self.resolve(self.a, self.b, "power_punch", state, 30)
            self.assertNotIn("last_distance_transition", state)
        with patch.object(self.engine, "_update_punch_distance", side_effect=AssertionError("Kick retagged")):
            self.resolve(self.a, self.b, "kick", self.state(), -30)

    def test_inactive_disengagement_is_neutral_and_default_off_retains_pocket(self):
        for enabled in (False, True):
            self.engine._experimental_specialist_entries = enabled
            state = self.state("pocket")
            state["unanswered"]["a"] = 3
            for _ in range(3):
                self.resolve(self.a, self.b, "survive", state, 0)
            self.assertEqual(state["position"], "range" if enabled else "pocket")
            self.assertEqual(state["unanswered"]["a"], 3)
            if enabled:
                event = {"neutral_scramble_reset": state["last_neutral_scramble_reset"],
                         "distance_transition": state["last_distance_transition"]}
                self.assertEqual(self.engine.exchange_commentary_kind(event), "neutral_reset")
                self.assertIn("Both fighters", self.engine.render_exchange_trace_event(event))
                self.assertIsNone(event["distance_transition"]["fighter"])

    def test_real_trace_renders_strike_and_correct_distance_actor_and_horn(self):
        seen, later_rounds = set(), 0
        for seed in range(68300, 68324):
            audit = run_audited_fight(self.engine, self.a, self.b, seed, {})
            prior_round = None
            for event in audit["trace"]:
                if event.get("type") != "exchange":
                    continue
                if event["round"] != prior_round:
                    self.assertEqual(event["position_before"], "range")
                    later_rounds += event["round"] > 1
                    prior_round = event["round"]
                fact = event.get("distance_transition")
                if not fact:
                    continue
                seen.add(fact["reason"])
                self.assertEqual((event["position_before"], event["position_after"]), (fact["from"], fact["to"]))
                self.assertEqual(event["td_delta"], 0)
                call = self.engine.render_exchange_trace_event(event)
                if fact["reason"] == "defender_pivot":
                    self.assertEqual(event["outcome"], "defended")
                    self.assertEqual(fact["fighter"], event["defender"])
                    self.assertIn(event["defender_name"] + " pivots away", call)
                elif fact["reason"] in {"pressure_entry", "jab_exit"}:
                    self.assertEqual(event["outcome"], "landed")
                    self.assertEqual(fact["fighter"], event["actor"])
                    self.assertGreater(event["sig_delta"], 0)
                self.assertNotEqual(self.engine.exchange_commentary_kind(event), "transitioned")
                self.assertTrue(all(value == 0 for value in event["control_delta"].values()))
        self.assertTrue({"pressure_entry", "defender_pivot"} <= seen, seen)
        self.assertGreater(later_rounds, 0)


if __name__ == "__main__":
    unittest.main()
