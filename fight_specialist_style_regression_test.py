"""Specialist physical-top menus inherit existing primary/secondary style policy."""
from copy import deepcopy
import pickle
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import run_audited_fight
from fight_moves.specialist_intent import specialist_style_weights
import fight_top_leg_entry_regression_test as fixture


class SpecialistStyleTests(unittest.TestCase):
    setUp = fixture.TopLegEntryTests.setUp

    def context(self, position='turtle', slot='a', style='Wrestler', secondary=''):
        state = deepcopy(self.initial)
        state.update(position=position, top=slot, bottom='b' if slot == 'a' else 'a',
                     clinch_controller=None)
        actor = self.a if slot == 'a' else self.b
        actor.style, actor.secondary_style = style, secondary
        return state, actor

    def test_real_menu_applies_style_then_plan_before_chain_and_after_survival(self):
        state, actor = self.context()
        state['gas']['a'], state['hurt']['a'] = 100, 0
        state['plans']['a'].update(current='Chase a finish', enabled=True, execution=1)
        seen = []
        def inspect(fighter, opponent, current, menu, round_no, tick):
            seen.append(dict(menu))
            return menu
        with patch.object(self.engine, '_chain_action_weights', side_effect=inspect), \
             patch.object(self.engine, 'weighted_choice', side_effect=lambda menu: menu):
            result = self.engine.choose_action(actor, self.b, state, 1, 1)
            self.assertAlmostEqual(result['ground_strikes'], 75 * 1.4 * 1.45)
            self.assertAlmostEqual(result['turtle_ride'], 75 * 1.3 * .68)
            self.assertEqual(list(result), ['take_back', 'ground_strikes', 'turtle_ride'])
            self.assertEqual(len(seen), 1)
            state['gas']['a'] = 3
            with patch.object(self.engine, 'fight_mechanics_rng') as rng:
                rng.return_value.random.return_value = 0
                self.assertEqual(self.engine.choose_action(actor, self.b, state, 1, 1), 'survive')
            self.assertEqual(len(seen), 1)

    def test_default_off_complete_bout_parity(self):
        self.engine._experimental_specialist_entries = False
        actual = run_audited_fight(self.engine, self.a, self.b, 93271, {})
        after = random.getstate()
        with patch('fight_engine.specialist_style_weights', side_effect=lambda e, f, s, w: w):
            legacy = run_audited_fight(self.engine, self.a, self.b, 93271, {})
        self.assertEqual(actual, legacy)
        self.assertEqual(random.getstate(), after)

    def test_exact_existing_primary_factors_both_slots(self):
        for slot in ('a', 'b'):
            state, actor = self.context('turtle', slot, 'Wrestler')
            menu = {'take_back': 80, 'ground_strikes': 100, 'turtle_ride': 60}
            adjusted = specialist_style_weights(self.engine, actor, state, menu)
            self.assertEqual(adjusted, {'take_back': 80, 'ground_strikes': 140, 'turtle_ride': 78})
            state, actor = self.context('front headlock', slot, 'BJJ')
            menu = {'take_back': 80, 'front_headlock_submission': 100, 'turtle_ride': 60}
            adjusted = specialist_style_weights(self.engine, actor, state, menu)
            self.assertEqual(adjusted, {'take_back': 96, 'front_headlock_submission': 150, 'turtle_ride': 60})

    def test_secondary_style_uses_existing_point_35_influence(self):
        state, actor = self.context('front headlock', style='Wrestler', secondary='BJJ')
        menu = {'take_back': 100, 'front_headlock_submission': 100, 'turtle_ride': 100}
        adjusted = specialist_style_weights(self.engine, actor, state, menu)
        self.assertAlmostEqual(adjusted['take_back'], 100 * (1 + .2 * .35))
        self.assertAlmostEqual(adjusted['front_headlock_submission'], 100 * (1 + .5 * .35))
        self.assertAlmostEqual(adjusted['turtle_ride'], 130)

    def test_plan_enablement_does_not_gate_style_and_inputs_are_pure(self):
        state, actor = self.context('front headlock', style='BJJ')
        menu = {'turtle_ride': 17, 'unmapped_action': 19, 'front_headlock_submission': 100}
        for enabled in (False, True):
            state['plans']['a']['enabled'] = enabled
            before = pickle.dumps((state, actor, menu))
            rng = random.getstate()
            adjusted = specialist_style_weights(self.engine, actor, state, menu)
            self.assertEqual(pickle.dumps((state, actor, menu)), before)
            self.assertEqual(random.getstate(), rng)
            self.assertEqual(list(adjusted), list(menu))
            self.assertEqual(adjusted['unmapped_action'], 19)
            self.assertEqual(adjusted['front_headlock_submission'], 150)

    def test_other_roles_positions_and_default_off_return_original(self):
        menu = {'ground_strikes': 100, 'turtle_ride': 100}
        for position in ('guard', 'half guard', 'leg entanglement', 'range', 'pocket',
                         'standing back control', 'failed shot', 'cage', 'clinch'):
            state, actor = self.context(position)
            self.assertIs(specialist_style_weights(self.engine, actor, state, menu), menu)
        state, actor = self.context()
        for changes in ({'top': 'b', 'bottom': 'a'}, {'bottom': None}, {'bottom': 'a'},
                        {'clinch_controller': 'a'}):
            self.assertIs(specialist_style_weights(self.engine, actor, dict(state, **changes), menu), menu)
        self.engine._experimental_specialist_entries = False
        self.assertIs(specialist_style_weights(self.engine, actor, state, menu), menu)


if __name__ == '__main__':
    unittest.main()
