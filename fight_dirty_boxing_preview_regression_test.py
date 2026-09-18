"""Clinch body continuations use actual landed-knee probability, not full credit."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter, run_audited_fight


class DirtyBoxingPreviewTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(random.setstate, random.getstate())
        self.engine = FightAuditHarness()
        self.engine._experimental_chain_action_weighting = True
        self.a = synthetic_fighter('Red', 80, 'Muay Thai', 'Control', 0)
        self.b = synthetic_fighter('Blue', 80, 'Boxer', 'Control', 1)
        for fighter in (self.a, self.b):
            fighter.trait = 'Clutch'
            fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 80)
        class Ready(Exception):
            pass
        captured = []
        def capture(actor, defender, state, round_no, tick):
            captured.append(state)
            raise Ready()
        with patch.object(self.engine, 'choose_action', side_effect=capture):
            with self.assertRaises(Ready):
                self.engine.simulate_fight(self.a, self.b, {})
        self.state = captured[0]
        self.state.update(position='clinch', top=None, bottom=None, round=1, tick=2,
                          clinch_controller='a', counter_window=None)
        self.state['move_chains'] = {'a': {'round': 1, 'tick': 1, 'actor_role': '',
                                        'branch_options': ['inside_body_hook']}, 'b': {}}
        self.weights = {'dirty_boxing': 100, 'takedown': 100, 'cage_control': 100, 'break_clinch': 100}

    def test_exact_contest_and_cleaned_weapon_tickets(self):
        for trait in ('Clutch', 'Erratic'):
            self.a.trait = trait
            offsets = range(-7, 8) if trait == 'Erratic' else (0,)
            for base in (-31, -30.001, -30, -12.001, -12, 5.999, 6, 7):
                def attack(actor, action, state, *, erratic_roll=None):
                    self.assertIsNotNone(erratic_roll)
                    return base + erratic_roll
                with patch.object(self.engine, 'action_attack_value', side_effect=attack), \
                     patch.object(self.engine, 'action_defence_value', return_value=0), \
                     patch.object(self.engine, '_dirty_boxing_weapon_weights',
                                  return_value={'elbow': -3, 'knee': 2.9, 'punch': 0}), \
                     patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('preview RNG')):
                    shares = self.engine.dirty_boxing_target_shares(self.a, self.b, self.state)
                expected = sum(base + offset + roll >= -12 for offset in offsets
                               for roll in range(-18, 19)) / (37 * len(offsets)) * .5
                self.assertAlmostEqual(shares['body'], expected)
                self.assertAlmostEqual(sum(shares.values()), 1)

    def test_real_attack_explicit_erratic_preserves_default_draw_arithmetic(self):
        self.a.trait = 'Erratic'
        before = deepcopy({key: value for key, value in self.state.items() if key != 'fighters'})
        for offset in (-7, 0, 7):
            with patch.object(self.engine, 'fight_mechanics_rng') as rng:
                rng.return_value.randint.return_value = offset
                ordinary = self.engine.action_attack_value(self.a, 'dirty_boxing', self.state)
                rng.return_value.randint.assert_called_once_with(-7, 7)
            with patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('preview RNG')):
                preview = self.engine.action_attack_value(self.a, 'dirty_boxing', self.state,
                                                        erratic_roll=offset)
                self.engine.dirty_boxing_target_shares(self.a, self.b, self.state)
            self.assertEqual(ordinary, preview)
        self.assertEqual({key: value for key, value in self.state.items() if key != 'fighters'}, before)

    def test_body_successor_probability_union_gates_and_ticket_conservation(self):
        before = deepcopy({key: value for key, value in self.state.items() if key != 'fighters'})
        with patch.object(self.engine, 'dirty_boxing_target_shares', return_value={'head': .75, 'body': .25}), \
             patch.object(self.engine, '_chain_commitment', return_value=2), \
             patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('preview RNG')):
            bonuses = self.engine._chain_action_bonuses(self.a, self.b, self.state, self.weights, 1, 2)
            self.assertEqual(bonuses, {'dirty_boxing': .5})
            adjusted = self.engine._chain_action_weights(self.a, self.b, self.state, self.weights, 1, 2)
            self.assertGreater(adjusted['dirty_boxing'], 100)
            self.assertEqual(sum(adjusted.values()), 400)
            self.assertEqual(list(adjusted), list(self.weights))
            self.assertTrue(all(value >= 1 for value in adjusted.values()))
            self.state['move_chains']['a']['branch_options'].append('short_rib_knee')
            self.assertEqual(self.engine._chain_action_bonuses(
                self.a, self.b, self.state, self.weights, 1, 2), bonuses)
            self.state['move_chains']['a']['branch_options'].pop()
            with patch.object(self.engine, '_move_rarity_gate', return_value=False):
                self.assertEqual(self.engine._chain_action_bonuses(
                    self.a, self.b, self.state, self.weights, 1, 2), {})
            self.engine._experimental_chain_action_weighting = False
            self.assertIs(self.engine._chain_action_weights(
                self.a, self.b, self.state, self.weights, 1, 2), self.weights)
        self.assertEqual({key: value for key, value in self.state.items() if key != 'fighters'}, before)

    def test_actual_resolver_target_boundary_and_both_fighter_slots(self):
        for actor, defender, slot in ((self.a, self.b, 'a'), (self.b, self.a, 'b')):
            for margin in (-12.001, -12, 0):
                for weapon in ('elbow', 'knee', 'punch'):
                    state = deepcopy(self.state)
                    stats = {key: {'impact': 0, 'danger': 0, 'control': 0} for key in ('a', 'b')}
                    with patch.object(self.engine, 'action_attack_value', return_value=margin), \
                         patch.object(self.engine, 'action_defence_value', return_value=0), \
                         patch.object(self.engine, 'weighted_choice', return_value=weapon) as choice, \
                         patch.object(self.engine, 'fight_mechanics_rng') as rng:
                        rng.return_value.randint.return_value = 0
                        rng.return_value.random.return_value = 1
                        self.engine.resolve_exchange(actor, defender, 'dirty_boxing', state, stats)
                    self.assertEqual(state['last_strike_target'],
                                     'body' if margin >= -12 and weapon == 'knee' else 'head')
                    self.assertEqual(choice.call_count, int(margin >= -12))
                    if choice.called:
                        self.assertEqual(choice.call_args.args[0], self.engine._dirty_boxing_weapon_weights(actor))

    def test_default_off_complete_bout_never_calls_preview(self):
        self.engine._experimental_chain_action_weighting = False
        self.a.trait = 'Erratic'
        expected = run_audited_fight(self.engine, deepcopy(self.a), deepcopy(self.b), 7614, {})
        rng_before = random.getstate()
        with patch.object(self.engine, 'dirty_boxing_target_shares', side_effect=AssertionError('default preview')):
            actual = run_audited_fight(self.engine, deepcopy(self.a), deepcopy(self.b), 7614, {})
        self.assertEqual(actual, expected)
        self.assertEqual(random.getstate(), rng_before)


if __name__ == '__main__':
    unittest.main()
