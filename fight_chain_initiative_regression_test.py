"""Candidate standing cadence is legal, bounded, observational and never forced."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter


class ChainInitiativeTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(random.setstate, random.getstate())
        self.engine = FightAuditHarness()
        self.a = synthetic_fighter('Cadence A', 80, 'Boxer', 'Control', 0)
        self.b = synthetic_fighter('Cadence B', 80, 'Boxer', 'Control', 1)
        for fighter in (self.a, self.b):
            fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 80)
        captured = []
        class Ready(Exception):
            pass
        def capture(a, b, state, *args):
            captured.append(state)
            raise Ready()
        with patch.object(self.engine, 'choose_action', side_effect=capture):
            with self.assertRaises(Ready):
                self.engine.simulate_fight(self.a, self.b, {})
        self.state = captured[0]
        self.state.update(position='range', round=1, tick=2, counter_window=None)
        self.state['gas'] = {'a': 100, 'b': 100}
        self.state['hurt'] = {'a': 0, 'b': 0}
        self.state['move_chains'] = {'a': dict(round=1, tick=1, actor_role='', branch_options=['single_jab'])}
        self.engine._experimental_chain_action_weighting = True

    def bonus(self):
        return self.engine._chain_initiative_bonus(self.a, self.b, self.state)

    def test_real_legal_chain_purity_skill_gas_cap_and_no_stacking(self):
        before = deepcopy(self.state, {id(self.a): self.a, id(self.b): self.b})
        fighters, rng = deepcopy((vars(self.a), vars(self.b))), random.getstate()
        with patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('new RNG')):
            full = self.bonus()
        self.assertGreater(full, 0)
        self.assertLessEqual(full, 2)
        self.assertEqual(self.state, before)
        self.assertEqual((vars(self.a), vars(self.b)), fighters)
        self.assertEqual(random.getstate(), rng)
        self.state['move_chains']['a']['branch_options'] = ['single_jab', 'double_jab']
        self.assertEqual(self.bonus(), full)
        self.state['gas']['a'] = 60
        self.assertEqual(self.bonus(), full)
        self.state['gas']['a'] = 41
        self.assertGreater(self.bonus(), 0)
        self.assertLess(self.bonus(), full)
        self.state['gas']['a'] = 100
        with patch.dict(self.a.detailed_skills, dict.fromkeys(('combination_punching', 'adaptability', 'discipline'), 45)):
            self.assertLess(self.bonus(), full)
        for gas in (0, 21, 22):
            self.state['gas']['a'] = gas
            self.assertEqual(self.bonus(), 0)

    def test_disabled_other_positions_hurt_counter_and_expiry_role(self):
        self.engine._experimental_chain_action_weighting = False
        self.assertEqual(self.bonus(), 0)
        self.engine._experimental_chain_action_weighting = True
        for position in ('clinch', 'cage', 'failed shot', 'standing back control', 'front headlock', 'turtle',
                         'leg entanglement', 'guard', 'half guard', 'side control', 'mount', 'back control'):
            self.state['position'] = position
            self.assertEqual(self.bonus(), 0)
        self.state['position'] = 'pocket'
        self.assertGreater(self.bonus(), 0)
        self.state['hurt']['a'] = self.a.toughness * .65
        self.assertGreater(self.bonus(), 0)
        self.state['hurt']['a'] += .01
        self.assertEqual(self.bonus(), 0)
        self.state['hurt']['a'] = 0
        self.state['counter_window'] = {'fighter': 'b'}
        self.assertEqual(self.bonus(), 0)
        self.state['counter_window'] = None
        self.state['last_exchange_counter'] = True
        self.assertGreater(self.bonus(), 0)
        for changes in ({'round': 2}, {'tick': -1}, {'tick': 2}, {'actor_role': 'bottom'}):
            with patch.dict(self.state['move_chains']['a'], changes):
                self.assertEqual(self.bonus(), 0)

    def test_actual_style_skill_rarity_and_unknown_successors(self):
        chain = self.state['move_chains']['a']
        for move in ('unknown', 'guard_armbar'):
            chain['branch_options'] = [move]
            self.assertEqual(self.bonus(), 0)
        chain['branch_options'] = ['boxer_double_jab_pivot_cross_hook']
        with patch.object(self.engine, 'fighter_styles', return_value=('BJJ',)):
            self.assertEqual(self.bonus(), 0)
        chain['branch_options'] = ['lead_front_snap_kick']
        with patch.dict(self.a.detailed_skills, dict.fromkeys(self.a.detailed_skills, 1)):
            self.assertEqual(self.bonus(), 0)
        chain['branch_options'] = ['wheel_kick']
        results = []
        for tick in range(2, 42):
            self.state['tick'], chain['tick'] = tick, tick - 1
            results.append(self.bonus())
        self.assertTrue(any(value > 0 for value in results))
        self.assertIn(0, results)

    def test_actor_counter_excludes_impossible_ordinary_branch_but_keeps_jab_lane(self):
        self.state['counter_window'] = {'fighter': 'a', 'created_round': 1, 'created_tick': 1}
        self.state['last_exchange_counter'] = False
        chain = self.state['move_chains']['a']
        # Keep target evidence identical in the preview and actual selector;
        # no style, skill, rarity, scoring or counter eligibility is bypassed.
        with patch.object(self.engine, 'punch_target_shares', return_value={'body': 0.0}):
            for branch, action, expected_move, cadence_available in (
                    ('one_two', 'power_punch', 'slip_cross', False),
                    ('single_jab', 'jab', 'single_jab', True)):
                with self.subTest(branch=branch):
                    chain['branch_options'] = [branch]
                    payload = self.engine.select_exchange_move(
                        self.a, self.b, action, 'range', 'head', self.state,
                    )
                    self.assertEqual(payload['move_id'], expected_move)
                    if cadence_available:
                        self.assertNotIn('counter', payload['tags'])
                        self.assertGreater(self.bonus(), 0)
                    else:
                        self.assertIn('counter', payload['tags'])
                        self.assertNotEqual(payload['move_id'], branch)
                        self.assertEqual(self.bonus(), 0,
                                         'Counter priority makes this ordinary successor unavailable')

    def test_initiative_retains_single_roll_and_either_fighter_can_win(self):
        rng = random.Random(123)
        with patch.object(self.engine, 'fight_mechanics_rng', return_value=rng):
            self.engine._experimental_chain_action_weighting = False
            start = rng.getstate()
            old = self.engine.initiative(self.a, self.b, self.state)
            after = rng.getstate()
            rng.setstate(start)
            self.engine._experimental_chain_action_weighting = True
            expected = self.bonus()
            new = self.engine.initiative(self.a, self.b, self.state)
            self.assertAlmostEqual(new - old, expected)
            self.assertEqual(rng.getstate(), after)
            self.state['move_chains'].clear()
            rng.setstate(start)
            self.assertEqual(self.engine.initiative(self.a, self.b, self.state), old)
            self.assertEqual(rng.getstate(), after)
        # The captured real-bout state has random night form/context. Establish
        # equal inputs explicitly rather than hoping a seed offsets that edge.
        for fighter in (self.a, self.b):
            fighter.behaviour = 'Control'
            fighter.fight_iq = fighter.toughness = 80
            fighter.momentum = fighter.camp_boost = 0
            fighter.weight_cut_penalty = fighter.division_size_penalty = 0
            fighter.detailed_skills = deepcopy(self.a.detailed_skills)
        self.state.update(night_form={'a': 0, 'b': 0}, counter_window=None,
                          last_exchange_counter=False, gas={'a': 100, 'b': 100},
                          hurt={'a': 0, 'b': 0}, move_chains={},
                          plans={key: {'current': 'Balanced', 'execution': 1.0} for key in ('a', 'b')})
        with patch.object(self.engine, 'context_edge', return_value=0.0):
            for seed in (3, 12, 99):
                rng = random.Random(seed)
                with patch.object(self.engine, 'fight_mechanics_rng', return_value=rng):
                    self.state['move_chains'] = {}
                    start = rng.getstate()
                    baseline_a = self.engine.initiative(self.a, self.b, self.state)
                    after_a = rng.getstate()
                    rng.setstate(start)
                    baseline_b = self.engine.initiative(self.b, self.a, self.state)
                    self.assertEqual(baseline_a, baseline_b)
                    self.assertEqual(after_a, rng.getstate())
                    for slot, fighter, opponent in (('a', self.a, self.b), ('b', self.b, self.a)):
                        with self.subTest(seed=seed, slot=slot):
                            self.state['move_chains'] = {slot: dict(
                                round=1, tick=1, actor_role='', branch_options=['single_jab'])}
                            self.assertGreater(self.engine._chain_initiative_bonus(fighter, opponent, self.state), 0)
                            rng.seed(seed)
                            outcomes = {self.engine.initiative(fighter, opponent, self.state)
                                        > self.engine.initiative(opponent, fighter, self.state)
                                        for _ in range(100)}
                            self.assertEqual(outcomes, {True, False})


if __name__ == '__main__':
    unittest.main()
