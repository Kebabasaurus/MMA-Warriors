"""Opt-in opportunity weighting must not force techniques or add RNG draws."""
from copy import deepcopy
from dataclasses import replace
import random
import unittest
from unittest.mock import patch

import fight_engine
from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import MOVE_REGISTRY


class ChainActionWeightingTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.engine._experimental_chain_action_weighting = True
        self.a = synthetic_fighter('Same Name', 80, 'Boxer', 'Control', 0)
        self.b = synthetic_fighter('Same Name', 80, 'BJJ', 'Control', 1)
        self.a.detailed_skills = dict.fromkeys(self.a.detailed_skills, 80)
        self.state = {'position': 'range', 'round': 1, 'tick': 2,
                      'fighter_keys': {id(self.a): 'a', id(self.b): 'b'},
                      'top': None, 'bottom': None, 'counter_window': None,
                      'move_chains': {'a': {'round': 1, 'tick': 1, 'actor_role': '',
                                            'branch_options': ['single_jab']}}}
        self.weights = {'jab': 100, 'power_punch': 100, 'kick': 100}

    def adjust(self, **updates):
        self.state.update(updates)
        return self.engine._chain_action_weights(self.a, self.b, self.state, self.weights, 1, 2)

    def branches(self, *ids):
        self.state['move_chains']['a']['branch_options'] = list(ids)

    def test_opt_in_order_total_state_and_rng_purity(self):
        self.engine._experimental_chain_action_weighting = False
        self.assertIs(self.adjust(), self.weights)
        self.engine._experimental_chain_action_weighting = True
        before, rng = deepcopy(self.state), random.getstate()
        with patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('extra RNG')):
            result = self.adjust()
        self.assertEqual(list(result), list(self.weights))
        self.assertEqual(sum(result.values()), 300)
        self.assertGreater(result['jab'], 100)
        self.assertTrue(all(value >= 1 for value in result.values()))
        self.assertEqual(self.state, before)
        self.assertEqual(random.getstate(), rng)

    def test_commitment_tracks_coordination_and_gas_without_forcing_action(self):
        self.branches('single_jab')
        samples = []
        for skill, gas in ((40, 100), (90, 100), (90, 15)):
            with patch.dict(self.a.detailed_skills, dict.fromkeys(
                    ('combination_punching', 'adaptability', 'discipline'), skill)):
                self.state['gas'] = {'a': gas}
                samples.append(self.adjust())
        self.assertGreater(samples[1]['jab'], samples[0]['jab'])
        self.assertGreater(samples[1]['jab'], samples[2]['jab'])
        for result in samples:
            self.assertEqual(sum(result.values()), sum(self.weights.values()))
            self.assertTrue(all(result[key] >= 1 for key in self.weights))
            self.assertLess(result['jab'], sum(result.values()))

    def test_commitment_uses_action_specific_skills_and_has_fixed_bounds(self):
        for skill, expected in ((0, .25), (100, 2.0)):
            with patch.object(self.engine, 'ds_avg', return_value=skill):
                self.assertEqual(self.engine._chain_commitment(self.a, 'jab', {}, 'a'), expected)
        for action, technical in (('jab', 'combination_punching'), ('takedown', 'chain_wrestling'),
                                   ('leg_attack', 'leg_locks'), ('submission', 'submission_attack'),
                                   ('stand_up', 'scrambles'), ('ground_strikes', 'ground_striking')):
            with patch.object(self.engine, 'ds_avg', return_value=75) as skills:
                self.engine._chain_commitment(self.a, action, {}, 'a')
                self.assertEqual(skills.call_args.args[1], (technical, 'adaptability', 'discipline'))

    def test_commitment_gas_boundaries_use_only_the_acting_fighter(self):
        with patch.object(self.engine, 'ds_avg', return_value=100):
            for actor, other in (('a', 'b'), ('b', 'a')):
                for gas, expected in ((0, .5), (15, .5), (60, 2), (150, 2)):
                    state = {'gas': {actor: gas, other: 0}}
                    self.assertEqual(self.engine._chain_commitment(self.a, 'jab', state, actor), expected)

    def test_expiry_role_position_and_missing_actions(self):
        for changes in ({'round': 2}, {'tick': -1}, {'tick': 2}, {'actor_role': 'bottom'}):
            with self.subTest(changes=changes):
                old = dict(self.state['move_chains']['a'])
                self.state['move_chains']['a'].update(changes)
                self.assertIs(self.adjust(), self.weights)
                self.state['move_chains']['a'] = old
        for branch in ('unknown', 'guard_armbar', 'double_leg_entry'):
            self.branches(branch)
            self.assertIs(self.adjust(), self.weights)

    def test_style_skill_rarity_and_deprecation_are_not_bypassed(self):
        self.branches('boxer_double_jab_pivot_cross_hook')
        with patch.object(self.engine, 'fighter_styles', return_value=('BJJ',)), \
             patch.object(self.engine, 'punch_target_shares', return_value={'head': 1, 'body': 0}):
            self.assertIs(self.adjust(), self.weights)
        self.branches('lead_front_snap_kick')
        with patch.object(self.engine, 'ds', return_value=1):
            self.assertIs(self.adjust(), self.weights)
        self.branches('single_jab')
        with patch.object(self.engine, '_move_rarity_gate', return_value=False):
            self.assertIs(self.adjust(), self.weights)
        with patch.dict(fight_engine.MOVE_REGISTRY, {'single_jab': replace(MOVE_REGISTRY['single_jab'], deprecated=True)}):
            self.assertIs(self.adjust(), self.weights)

    def test_current_counter_window_not_stale_previous_exchange(self):
        self.branches('pull_counter')
        self.assertIs(self.adjust(last_exchange_counter=True, counter_window=None), self.weights)
        result = self.adjust(last_exchange_counter=False, counter_window={'fighter': 'a'})
        self.assertGreater(result['power_punch'], 100)
        self.assertIs(self.adjust(counter_window={'fighter': 'b'}), self.weights)

    def test_counter_precedence_requires_an_eligible_counter_alternative(self):
        self.state['counter_window'] = {'fighter': 'a'}
        self.branches('one_two')
        with patch.object(self.engine, 'punch_target_shares', return_value={'head': 1, 'body': 0}):
            self.assertIs(self.adjust(), self.weights)
            original = self.engine._move_rarity_gate
            def reject_counters(actor, tags, *args):
                return 'counter' not in tags and original(actor, tags, *args)
            with patch.object(self.engine, '_move_rarity_gate', side_effect=reject_counters):
                self.assertGreater(self.adjust()['power_punch'], self.weights['power_punch'])
            original_static = self.engine._move_static_score
            def unskilled_counters(actor, move, *args):
                return None if 'counter' in move.tags else original_static(actor, move, *args)
            with patch.object(self.engine, '_move_static_score', side_effect=unskilled_counters):
                self.assertGreater(self.adjust()['power_punch'], self.weights['power_punch'])
            self.branches('single_jab')
            self.assertGreater(self.adjust()['jab'], self.weights['jab'])

    def test_actual_rarity_fingerprint_admits_and_rejects_high_risk_move(self):
        self.branches('wheel_kick')
        admitted, rejected = 0, 0
        with patch.object(self.engine, 'kick_target_shares', return_value={'high': 1, 'body': 0, 'teep': 0, 'leg': 0}):
            for tick in range(2, 22):
                self.state['tick'] = tick
                self.state['move_chains']['a']['tick'] = tick - 1
                result = self.engine._chain_action_weights(self.a, self.b, self.state, self.weights, 1, tick)
                admitted += result is not self.weights
                rejected += result is self.weights
        self.assertGreater(admitted, 0)
        self.assertGreater(rejected, 0)

    def test_target_lanes_and_duplicate_action_branches(self):
        self.branches('lead_front_snap_kick')
        with patch.object(self.engine, 'kick_target_shares', return_value={'high': 0, 'body': .5, 'teep': .5, 'leg': 0}):
            self.assertIs(self.adjust(), self.weights)
        with patch.object(self.engine, 'kick_target_shares', return_value={'high': .25, 'body': .25, 'teep': .25, 'leg': .25}):
            partial = self.adjust()
        with patch.object(self.engine, 'kick_target_shares', return_value={'high': 1, 'body': 0, 'teep': 0, 'leg': 0}):
            full = self.adjust()
        self.assertGreater(partial['kick'], 100)
        self.assertGreater(full['kick'], partial['kick'])
        self.branches('single_jab')
        one = self.adjust()
        self.branches('single_jab', 'double_jab')
        self.assertEqual(self.adjust(), one)
        self.branches('rear_check_hook')
        self.state['counter_window'] = {'fighter': 'a'}
        with patch.object(self.engine, 'punch_target_shares', return_value={'head': 0, 'body': 1}):
            self.assertIs(self.adjust(), self.weights)

    def test_survival_overrides_do_not_call_weighting(self):
        self.state.update(gas={'a': 1}, hurt={'a': 0})
        with patch.object(self.engine, 'fight_mechanics_rng') as rng, \
             patch.object(self.engine, '_chain_action_weights', side_effect=AssertionError('survival overridden')):
            rng.return_value.random.return_value = 0
            self.assertEqual(self.engine.choose_action(self.a, self.b, self.state, 1, 2), 'survive')
            rng.return_value.random.assert_called_once()

    def test_existing_weighted_choice_retains_single_draw_and_range(self):
        adjusted = self.adjust()
        with patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.randint.return_value = 1
            self.assertEqual(self.engine.weighted_choice(adjusted), 'jab')
            rng.return_value.randint.assert_called_once_with(1, 300)
        self.weights = {'jab': -5, 'power_punch': 1.9, 'kick': 0}
        self.assertEqual(self.adjust(), {'jab': 1, 'power_punch': 1, 'kick': 1})

    def test_submission_preview_uses_live_pool_not_impossible_setup_or_stale_hold(self):
        self.engine._experimental_specialist_entries = True
        self.state.update(position='half guard', top='a', bottom='b')
        self.state['move_chains']['a']['actor_role'] = 'top'
        self.weights = {'submission': 100, 'ground_control': 100, 'ground_strikes': 100}
        self.branches('half_guard_von_flue')
        self.state['last_submission_technique'] = {'name': 'Von Flue choke'}
        before = deepcopy(self.state)
        with patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('preview draw')):
            self.assertIs(self.adjust(), self.weights)
            self.assertEqual(self.state, before)
        self.branches('half_guard_americana')
        first = self.adjust()
        self.assertGreater(first['submission'], 100)
        self.state['last_submission_technique'] = {'name': 'heel hook'}
        self.assertEqual(self.adjust(), first)
        self.engine._experimental_specialist_entries = False
        self.branches('half_guard_von_flue')
        self.assertGreater(self.adjust()['submission'], 100)  # Old experimental-chain-only semantics.

    def test_submission_probability_counts_union_of_tickets_not_branch_count(self):
        self.engine._experimental_specialist_entries = True
        self.state.update(position='half guard', top='a', bottom='b')
        self.state['move_chains']['a']['actor_role'] = 'top'
        self.weights = {'submission': 100, 'ground_control': 100, 'ground_strikes': 100}
        tickets = [('arm-triangle choke', True)] * 2 + [('kimura', False)] * 2
        self.branches('half_guard_arm_triangle')
        with patch.object(self.engine, 'submission_technique_tickets', return_value=tickets), \
             patch.object(self.engine, '_chain_commitment', return_value=2):
            one = self.adjust()
            self.assertEqual(one, {'submission': 150, 'ground_control': 75, 'ground_strikes': 75})
            self.branches('half_guard_arm_triangle', 'guard_top_head_arm')
            self.assertEqual(self.adjust(), one)
            self.branches('half_guard_arm_triangle', 'half_guard_kimura')
            self.assertGreater(self.adjust()['submission'], one['submission'])
            with patch.object(self.engine, '_move_rarity_gate', return_value=False):
                self.assertIs(self.adjust(), self.weights)


if __name__ == '__main__':
    unittest.main()
