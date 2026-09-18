"""Physical-top specialist plans reuse bounded ordinary tactical preferences."""
from copy import deepcopy
import pickle
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import run_audited_fight
from fight_moves.specialist_intent import specialist_plan_weights
import fight_top_leg_entry_regression_test as fixture


class SpecialistPlanTests(unittest.TestCase):
    setUp = fixture.TopLegEntryTests.setUp

    def context(self, position="turtle", slot="a", plan="Chase a finish", execution=1):
        state = deepcopy(self.initial)
        other = "b" if slot == "a" else "a"
        state.update(position=position, top=slot, bottom=other)
        state["gas"][slot] = 100
        state["hurt"][slot] = 0
        state["plans"][slot].update(current=plan, execution=execution, enabled=True)
        actor, opponent = (self.a, self.b) if slot == "a" else (self.b, self.a)
        return state, actor, opponent

    def adjusted(self, state, actor, opponent, weights):
        return specialist_plan_weights(self.engine, actor, opponent, state, weights, 1)

    def test_chase_conserve_and_submission_hunt_both_physical_top_slots(self):
        for slot in ("a", "b"):
            for position, attack in (("turtle", "ground_strikes"),
                                     ("front headlock", "front_headlock_submission")):
                weights = {"take_back": 80, attack: 100, "turtle_ride": 60}
                for plan, attack_factor, ride_factor, advance_factor in (
                    ("Chase a finish", 1.45 if position == "turtle" else 1.38, 0.68, 1),
                    ("Conserve energy", 0.72 if position == "turtle" else 0.68, 1.42, 1),
                    ("Submission hunt", 0.78 if position == "turtle" else 1.62, 1, 1.28),
                ):
                    state, actor, opponent = self.context(position, slot, plan)
                    result = self.adjusted(state, actor, opponent, weights)
                    self.assertEqual(list(result), list(weights))
                    self.assertAlmostEqual(result[attack], 100 * attack_factor)
                    self.assertAlmostEqual(result["turtle_ride"], 60 * ride_factor)
                    self.assertAlmostEqual(result["take_back"], 80 * advance_factor)

    def test_execution_bounds_and_disabled_plan(self):
        weights = {"ground_strikes": 100, "turtle_ride": 100}
        for execution, expected in ((0.5, 122.5), (3, 145), (-1, 100),
                                    (float("nan"), 100), (float("inf"), 100),
                                    (None, 100), ("invalid", 100)):
            state, actor, opponent = self.context(execution=execution)
            self.assertAlmostEqual(self.adjusted(state, actor, opponent, weights)["ground_strikes"], expected)
        state, actor, opponent = self.context()
        state["plans"]["a"]["enabled"] = False
        self.assertEqual(self.adjusted(state, actor, opponent, weights), weights)
        del state["plans"]["a"]["enabled"]
        self.assertEqual(self.adjusted(state, actor, opponent, weights), weights)

    def test_default_off_other_positions_and_bottom_are_unchanged(self):
        weights = {"ground_strikes": 90, "front_headlock_submission": 80, "turtle_ride": 70}
        for position in ("guard", "leg entanglement", "standing back control", "range", "failed shot"):
            state, actor, opponent = self.context(position)
            self.assertIs(self.adjusted(state, actor, opponent, weights), weights)
        state, actor, opponent = self.context()
        state.update(top="b", bottom="a")
        self.assertIs(self.adjusted(state, actor, opponent, weights), weights)
        state.update(top="a", bottom="b")
        self.engine._experimental_specialist_entries = False
        self.assertIs(self.adjusted(state, actor, opponent, weights), weights)

    def test_inputs_rng_and_original_action_order_are_preserved(self):
        state, actor, opponent = self.context("front headlock", execution=7)
        weights = {"turtle_ride": 70, "unmapped_action": 13, "front_headlock_submission": 90}
        before = pickle.dumps((state, actor, opponent, weights))
        rng = random.getstate()
        result = self.adjusted(state, actor, opponent, weights)
        self.assertEqual(pickle.dumps((state, actor, opponent, weights)), before)
        self.assertEqual(random.getstate(), rng)
        self.assertEqual(list(result), list(weights))
        self.assertEqual(result["unmapped_action"], 13)
        self.assertNotIn("submission", result)
        self.assertNotIn("ground_control", result)
        self.assertAlmostEqual(result["front_headlock_submission"], 124.2)

    def test_real_menu_hook_after_survival_before_chain_weighting(self):
        state, actor, opponent = self.context()
        original = self.engine._chain_action_weights
        observed = []

        def hooked(fighter, defender, current, weights, round_no, tick):
            observed.append(dict(weights))
            return original(fighter, defender, current, weights, round_no, tick)

        with patch.object(self.engine, "_chain_action_weights", side_effect=hooked), \
             patch.object(self.engine, "weighted_choice", side_effect=lambda weights: dict(weights)):
            result = self.engine.choose_action(actor, opponent, state, 1, 1)
            self.assertAlmostEqual(result["ground_strikes"], 75 * 1.45)
            self.assertAlmostEqual(result["turtle_ride"], 75 * 0.68)
            self.assertEqual(len(observed), 1)
            state["gas"]["a"] = 3
            with patch.object(self.engine, "fight_mechanics_rng") as rng:
                rng.return_value.random.return_value = 0
                self.assertEqual(self.engine.choose_action(actor, opponent, state, 1, 1), "survive")
            self.assertEqual(len(observed), 1)

    def test_complete_bout_default_off_hook_parity(self):
        self.engine._experimental_specialist_entries = False
        baseline = run_audited_fight(self.engine, self.a, self.b, 93271, {})
        baseline_rng = random.getstate()
        original = self.engine._chain_action_weights

        def hooked(fighter, opponent, state, weights, round_no, tick):
            adjusted = specialist_plan_weights(self.engine, fighter, opponent, state, weights, round_no)
            return original(fighter, opponent, state, adjusted, round_no, tick)

        with patch.object(self.engine, "_chain_action_weights", side_effect=hooked):
            observed = run_audited_fight(self.engine, self.a, self.b, 93271, {})
        self.assertEqual(observed, baseline)
        self.assertEqual(random.getstate(), baseline_rng)

    def test_natural_bouts_with_enabled_plans_reach_specialist_policy(self):
        original = self.engine.apply_fight_plan_weights
        observed = set()
        def inspect(fighter, opponent, state, phase, weights, round_no):
            before = dict(weights)
            result = original(fighter, opponent, state, phase, weights, round_no)
            if state['position'] in {'turtle', 'front headlock'} and phase == 'top':
                self.assertEqual(list(result), list(before))
                self.assertNotEqual(result, before)
                observed.add(state['position'])
            return result
        with patch.object(self.engine, 'apply_fight_plan_weights', side_effect=inspect):
            for seed in range(93271, 93371):
                run_audited_fight(self.engine, self.a, self.b, seed,
                                 {'fight_plans': {'a': 'Chase a finish', 'b': 'Chase a finish'}})
                if len(observed) == 2:
                    break
        self.assertEqual(observed, {'turtle', 'front headlock'})


if __name__ == "__main__":
    unittest.main()
