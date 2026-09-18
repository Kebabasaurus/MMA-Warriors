"""Opt-in cage-pummel rear control, identity-safe exits and static-lock resets."""
from collections import defaultdict
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, run_audited_fight, synthetic_fighter


class StandingBackEntryTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.engine._experimental_specialist_entries = True
        self.a = synthetic_fighter("Same Name", 75, "Wrestler", "Control", 0)
        self.b = synthetic_fighter("Same Name", 75, "Grappler", "Control", 1)
        for fighter in (self.a, self.b):
            fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 75)
        self.addCleanup(random.setstate, random.getstate())

    def state(self, position="cage", controller="a"):
        state = {"position": position, "top": None, "bottom": None,
                 "clinch_controller": controller, "round": 1, "tick": 1,
                 "fighter_keys": {id(self.a): "a", id(self.b): "b"},
                 "stats": {key: defaultdict(int) for key in ("a", "b")}}
        for key in ("gas", "gas_cap"):
            state[key] = {"a": 80, "b": 80}
        for key in ("head", "hurt", "unanswered", "danger"):
            state[key] = {"a": 0, "b": 0}
        return state

    def resolve(self, actor, defender, action, state, margin):
        with patch.object(self.engine, "action_attack_value", return_value=margin), \
             patch.object(self.engine, "action_defence_value", return_value=0), \
             patch.object(self.engine, "fight_mechanics_rng") as rng:
            rng.return_value.randint.return_value = 0
            result = self.engine.resolve_exchange(actor, defender, action, state,
                                                 {key: defaultdict(int) for key in ("a", "b")})
            rng.return_value.randint.assert_called_once_with(-18, 18)
            rng.return_value.random.assert_not_called()
            return result

    def test_matched_controller_and_trapped_pummels_both_id_orientations(self):
        for actor, defender, actor_key, defender_key in ((self.a, self.b, "a", "b"), (self.b, self.a, "b", "a")):
            for controller in (actor_key, defender_key):
                for margin, expected in ((7, "cage"), (17, "cage"), (18, "standing back control")):
                    with self.subTest(actor=actor_key, controller=controller, margin=margin):
                        state = self.state(controller=controller)
                        result = self.resolve(actor, defender, "cage_control", state, margin)
                        self.assertEqual(state["position"], expected)
                        self.engine.validate_fight_transition("cage", expected, state)
                        if expected == "standing back control":
                            self.assertEqual(state["clinch_controller"], actor_key)
                            self.assertIn("rear body lock", result)
                            self.assertIsNone(state["top"])
                            self.assertIsNone(state["bottom"])
                with patch.dict(defender.detailed_skills, {"clinch_defence": 95, "scrambles": 95, "strength": 95}):
                    state = self.state(controller=controller)
                    self.resolve(actor, defender, "cage_control", state, 18)
                    self.assertEqual(state["position"], "cage")
            state = self.state("clinch", actor_key)
            self.resolve(actor, defender, "cage_control", state, 30)
            self.assertEqual(state["position"], "cage")

    def test_default_off_retains_ordinary_and_legacy_extreme_paths(self):
        self.engine._experimental_specialist_entries = False
        state = self.state()
        self.resolve(self.a, self.b, "cage_control", state, 30)
        self.assertEqual(state["position"], "cage")
        with patch.dict(self.a.detailed_skills, {"back_control": 95}), \
             patch.dict(self.b.detailed_skills, {"clinch_defence": 40}):
            state = self.state()
            self.resolve(self.a, self.b, "cage_control", state, 35)
            self.assertEqual(state["position"], "standing back control")
        for _ in range(6):
            self.resolve(self.a, self.b, "standing_back_ride", state, 0)
        self.assertEqual(state["position"], "standing back control")
        self.assertNotIn("last_neutral_scramble_reset", state)

    def test_next_action_roles_mat_return_and_escape(self):
        for controller in ("a", "b"):
            state = self.state("standing back control", controller)
            for actor, defender, key in ((self.a, self.b, "a"), (self.b, self.a, "b")):
                with patch.object(self.engine, "weighted_choice", side_effect=lambda weights: weights):
                    options = self.engine.choose_action(actor, defender, state, 1, 1)
                self.assertEqual(set(options), {"mat_return", "dirty_boxing", "standing_back_ride"}
                                 if key == controller else {"standing_escape", "recover_shot"})
            top_actor, trapped = (self.a, self.b) if controller == "a" else (self.b, self.a)
            self.resolve(top_actor, trapped, "mat_return", state, 0)
            self.assertEqual(state["position"], "back control")
            self.assertEqual(state["top"], controller)
            self.assertEqual(state["stats"][controller]["td"], 1)
            self.engine.validate_fight_transition("standing back control", "back control", state)
            state = self.state("standing back control", controller)
            self.resolve(trapped, top_actor, "standing_escape", state, 3)
            self.assertEqual(state["position"], "range")
            self.assertIsNone(state["clinch_controller"])

    def test_static_ride_separation_fact_and_active_attempt_reset(self):
        for controller in ("a", "b"):
            rider, opponent = (self.a, self.b) if controller == "a" else (self.b, self.a)
            for action in ("standing_back_ride", "survive"):
                state = self.state("standing back control", controller)
                for beat in range(4):
                    text = self.resolve(rider, opponent, action, state, 0)
                    self.assertEqual(state["position"], "range" if beat == 3 else "standing back control")
                self.assertIsNone(state["clinch_controller"])
                self.assertEqual(state["stats"][controller]["td"], 0)
                fact = state["last_neutral_scramble_reset"]
                self.assertEqual(fact["controller_before"], controller)
                event = {"neutral_scramble_reset": fact}
                self.assertEqual(self.engine.exchange_commentary_kind(event), "neutral_reset")
                self.assertEqual(self.engine.render_exchange_trace_event(event), text)
                state = self.state("standing back control", controller)
                self.resolve(rider, opponent, action, state, 0)
                self.resolve(opponent, rider, "standing_escape", state, -10)
                self.assertEqual(state["standing_back_stall_ticks"], 0)
                self.assertEqual(state["clinch_controller"], controller)

    def test_complete_matched_bouts_show_rear_control_and_horn_reset(self):
        observed, later_rounds = 0, 0
        for seed in range(58200, 58248):
            audit = run_audited_fight(self.engine, self.a, self.b, seed, {})
            prior_round = None
            for event in audit["trace"]:
                if event.get("type") != "exchange":
                    continue
                observed += event["position_before"] == "standing back control"
                if event["round"] != prior_round:
                    self.assertEqual(event["position_before"], "range")
                    self.assertIsNone(event.get("top_before"))
                    self.assertIsNone(event.get("bottom_before"))
                    later_rounds += event["round"] > 1
                    prior_round = event["round"]
        self.assertGreater(observed, 0)
        self.assertGreater(later_rounds, 0)

    def test_automatic_separations_do_not_grant_survival_response_credit(self):
        for position, counter, threshold in (
                ('standing back control', 'standing_back_stall_ticks', 4),
                ('failed shot', 'failed_shot_stall_ticks', 3)):
            for actor, defender, actor_key in ((self.a, self.b, 'a'), (self.b, self.a, 'b')):
                for controller in ('a', 'b'):
                    for prior in (threshold - 2, threshold - 1):
                        with self.subTest(position=position, actor=actor_key, controller=controller, prior=prior):
                            state = self.state(position, controller)
                            state[counter] = prior
                            state['hurt'][actor_key] = 10
                            state['unanswered'][actor_key] = 4
                            self.resolve(actor, defender, 'survive', state, 0)
                            self.assertEqual(state['hurt'][actor_key], 9)
                            self.assertEqual(state['unanswered'][actor_key], 4)

    def test_neutral_trace_preserves_control_but_not_effectiveness_or_chains(self):
        # Capture a fully initialized real bout state, then drive one final
        # static beat through the real resolver and trace-recording pipeline.
        class StateReady(Exception):
            pass
        captured = []
        def capture(actor, defender, state, round_no, tick):
            captured.append(state)
            raise StateReady()
        with patch.object(self.engine, 'choose_action', side_effect=capture):
            with self.assertRaises(StateReady):
                self.engine.simulate_fight(self.a, self.b, {})
        initial = captured[0]
        for actor, defender, actor_key, other in ((self.a, self.b, 'a', 'b'), (self.b, self.a, 'b', 'a')):
            for action in ('survive', 'standing_back_ride'):
                state = deepcopy(initial)
                state.update(position='standing back control', clinch_controller=actor_key,
                             standing_back_stall_ticks=3, top=None, bottom=None)
                state['move_chains'] = {k: {'round': 1, 'tick': 0, 'branch_options': ['single_jab'],
                                          'source_move_id': 'single_jab', 'actor_role': ''} for k in ('a', 'b')}
                state['commentary_profiles'][actor_key]['trait'] = 'Fast Starter'
                state['hurt'][actor_key] = 10
                state['unanswered'][actor_key] = 4
                before = self.engine.fight_trace_snapshot(self.a, self.b, state)
                stats = {k: {'impact': 0, 'danger': 0, 'control': 0} for k in ('a', 'b')}
                round_before = deepcopy(stats)
                with patch.object(self.engine, 'action_attack_value', return_value=0), \
                     patch.object(self.engine, 'action_defence_value', return_value=0), \
                     patch.object(self.engine, 'fight_mechanics_rng') as rng:
                    rng.return_value.randint.return_value = 0
                    text = self.engine.resolve_exchange(actor, defender, action, state, stats)
                event = self.engine.record_fight_trace_exchange(
                    self.a, self.b, actor, defender, action, text, before, round_before, state, stats)
                expected_control = 3 if action == 'standing_back_ride' else 0
                self.assertAlmostEqual(state['hurt'][actor_key], 9.725 if expected_control else 9)
                self.assertEqual(state['unanswered'][actor_key], 0 if expected_control else 4)
                self.assertEqual(event['outcome'], 'neutral_reset')
                self.assertEqual(event['round_metric_delta'][actor_key]['control'], expected_control)
                self.assertEqual(state['plans'][actor_key]['effective_actions'], 0)
                evidence = self.engine.round_evidence_from_trace(state, 1)[actor_key]
                self.assertEqual(evidence['effective_actions'], 0)
                self.assertEqual(evidence['control'], expected_control)
                self.assertEqual(state['move_chains'], {'a': {}, 'b': {}})
                self.assertFalse(event['move_sequence']['continuation_available'])
                self.assertFalse(event['move_sequence']['completed_follow_up'])
                self.assertEqual(event['trait_commentary'], '')
                self.assertEqual(event['camp_commentary'], '')
                self.assertEqual(state['trait_commentary_seen'][actor_key]['count'], 0)
                self.assertEqual(state['camp_commentary_seen'][actor_key]['count'], 0)
                event.update(actor_camp='Test camp', actor_camp_specialties=['Wrestling'])
                with patch.object(self.engine, 'stable_commentary_due', return_value=True):
                    self.assertEqual(self.engine.camp_exchange_commentary(event, 'neutral_reset'), '')
                    self.assertEqual(self.engine.trait_exchange_commentary(event, 'neutral_reset'), '')

    def test_both_neutral_reasons_clear_other_actor_and_range_legal_successors(self):
        for reason in ('stalled_failed_shot', 'stalled_standing_back'):
            state = {'move_chains': {'a': {'actor_role': '', 'next_move_id': 'single_jab'},
                                    'b': {'actor_role': '', 'next_move_id': 'single_jab'}}}
            event = {'actor': 'a', 'round': 1, 'tick': 4, 'position_after': 'range',
                     'outcome': 'position_change', 'neutral_scramble_reset': {'reason': reason},
                     'move': {'follow_up_ids': ['single_jab'], 'sequence_source_id': 'single_jab',
                              'sequence_step': 2, 'sequence_occurrence_id': 'old'},
                     'sequence_source_id': 'single_jab', 'sequence_step': 2}
            self.engine.update_move_sequence(state, event)
            self.assertEqual(state['move_chains'], {'a': {}, 'b': {}})
            self.assertFalse(event['move_sequence']['continuation_available'])
            self.assertFalse(event['move_sequence']['completed_follow_up'])
            self.assertEqual(event['sequence_source_id'], '')
            self.assertEqual(event['sequence_step'], 0)


if __name__ == "__main__":
    unittest.main()
