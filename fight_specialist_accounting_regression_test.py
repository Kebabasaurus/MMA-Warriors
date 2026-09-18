"""Specialist skills and physical control use explicit supported ownership."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from constants import DETAILED_SKILL_GROUPS
from fight_engine_audit import run_audited_fight
from analysis.generate_move_coverage_report import control_award_observation
import fight_scarf_hold_setup_regression_test as fixture


class SpecialistAccountingTests(unittest.TestCase):
    setUp = fixture.ScarfHoldSetupTests.setUp

    def state(self, position, top='a'):
        state = deepcopy(self.initial)
        ground = position in self.engine.GROUND_POSITIONS
        state.update(position=position, top=top if ground else None,
                     bottom=('b' if top == 'a' else 'a') if ground else None,
                     clinch_controller=top if position in {'clinch', 'cage', 'failed shot', 'standing back control'} else None)
        return state

    def test_actual_specialist_menus_attack_and_defense_use_supported_keys(self):
        supported = {key for group in DETAILED_SKILL_GROUPS.values() for key in group}
        original_avg, original_ds = self.engine.ds_avg, self.engine.ds
        def avg(fighter, keys, fallback=50):
            self.assertFalse(set(keys) - supported, f'Unsupported average keys: {set(keys) - supported}')
            return original_avg(fighter, keys, fallback)
        def ds(fighter, key, fallback=50):
            self.assertIn(key, supported)
            return original_ds(fighter, key, fallback)
        with patch.object(self.engine, 'ds_avg', side_effect=avg), \
             patch.object(self.engine, 'ds', side_effect=ds), \
             patch.object(self.engine, 'weighted_choice', side_effect=lambda weights: weights):
            for position in ('failed shot', 'standing back control', 'front headlock', 'turtle', 'leg entanglement'):
                for actor in (self.a, self.b):
                    with self.subTest(position=position, actor=actor.name):
                        other = self.b if actor is self.a else self.a
                        state = self.state(position)
                        menu = self.engine.choose_action(actor, other, state, 1, 1)
                        for action in menu:
                            self.engine.action_attack_value(actor, action, state)
                            self.engine.action_defence_value(other, action, state)

    def test_replacement_skills_change_intended_attack_and_menu_without_rng(self):
        for fighter in (self.a, self.b):
            fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 50)
        cases = (('force_cage', 'failed shot', 'cage_wrestling'),
                 ('force_cage', 'failed shot', 'cage_pressure'),
                 ('standing_back_ride', 'standing back control', 'back_control'),
                 ('turtle_ride', 'turtle', 'top_control'),
                 ('turtle_ride', 'turtle', 'positional_ability'),
                 ('front_headlock_submission', 'front headlock', 'positional_ability'))
        before = random.getstate()
        for action, position, skill in cases:
            with self.subTest(action=action, skill=skill):
                state = self.state(position)
                low = self.engine.action_attack_value(self.a, action, state)
                self.a.detailed_skills[skill] = 90
                high = self.engine.action_attack_value(self.a, action, state)
                self.a.detailed_skills[skill] = 50
                self.assertGreater(high, low)
        with patch.object(self.engine, 'weighted_choice', side_effect=lambda weights: weights):
            for position, action, skill, top in (
                    ('standing back control', 'standing_escape', 'mobility', 'b'),
                    ('front headlock', 'front_headlock_submission', 'positional_ability', 'a')):
                state = self.state(position, top)
                low = self.engine.choose_action(self.a, self.b, state, 1, 1)[action]
                self.a.detailed_skills[skill] = 90
                high = self.engine.choose_action(self.a, self.b, state, 1, 1)[action]
                self.a.detailed_skills[skill] = 50
                self.assertGreater(high, low)
        self.assertEqual(random.getstate(), before)

    def test_disengage_preserves_broad_iq_rounding_and_default_off_skill_path(self):
        self.a.detailed_skills['discipline'] = 41
        self.a.detailed_skills['footwork'] = 62
        self.a.fight_iq = 76
        state = self.state('failed shot')
        with patch.object(self.engine, 'weighted_choice', side_effect=lambda weights: weights):
            for enabled in (False, True):
                self.engine._experimental_specialist_entries = enabled
                self.assertEqual(self.engine.choose_action(self.a, self.b, state, 1, 1)['disengage'],
                                 round((41 + 62 + 76) / 3))
        self.engine._experimental_specialist_entries = False
        original = self.engine.action_attack_value(self.a, 'force_cage', state)
        self.a.detailed_skills['cage_pressure'] = 1
        self.assertEqual(self.engine.action_attack_value(self.a, 'force_cage', state), original)

    def test_control_owner_matrix_and_purity(self):
        self.assertTrue(callable(getattr(self.engine, '_fight_control_owner', None)),
                        'Missing shared physical-control attribution helper')
        physical = {'guard', 'half guard', 'side control', 'mount', 'back control', 'front headlock', 'turtle'}
        standing = {'clinch', 'cage', 'failed shot', 'standing back control'}
        for enabled in (False, True):
            self.engine._experimental_specialist_entries = enabled
            for position in physical | standing | {'range', 'pocket', 'leg entanglement'}:
                for slot in ('a', 'b'):
                    with self.subTest(enabled=enabled, position=position, slot=slot):
                        state = self.state(position, slot)
                        owners = (state['position'], state['top'], state['bottom'], state['clinch_controller'])
                        expected = slot if position in standing | (physical if enabled else physical - {'front headlock', 'turtle'}) else None
                        self.assertEqual(self.engine._fight_control_owner(state), expected)
                        self.assertEqual((state['position'], state['top'], state['bottom'], state['clinch_controller']), owners)

    def test_actual_bouts_settled_control_escape_reversal_neutral_and_horn(self):
        scenarios = (('front headlock', 'survive', False), ('front headlock', 'turtle_ride', False),
                     ('turtle', 'turtle_ride', False), ('turtle', 'turtle_escape', True),
                     ('leg entanglement', 'counter_leg_lock', True), ('failed shot', 'force_cage', False),
                     ('standing back control', 'standing_escape', True),
                     ('standing back control', 'standing_back_ride', False), ('failed shot', 're_shot', True))
        rounds, final_state = [], []
        def choose(actor, defender, state, round_no, tick):
            if tick == 1:
                self.assertFalse('last_control_award' in state)
                rounds.append(round_no)
            position, action, bottom = scenarios[(tick - 1) % len(scenarios)]
            actor_key, defender_key = self.engine.fight_state_key(actor, state), self.engine.fight_state_key(defender, state)
            top_key = defender_key if bottom else actor_key
            state.update(position=position, top=top_key if position in self.engine.GROUND_POSITIONS else None,
                         bottom=(actor_key if bottom else defender_key) if position in self.engine.GROUND_POSITIONS else None,
                         clinch_controller=top_key if position not in self.engine.GROUND_POSITIONS else None,
                         standing_back_stall_ticks=3 if action == 'standing_back_ride' else 0)
            if action == 'survive':
                # Existing award timing is before this later referee reset.
                state['ground_warning'] = True
                state['ground_inactivity'] = max(3, self.engine.referee_profile(state)['standup_threshold'] - 1)
            final_state[:] = [state]
            return action
        with patch.object(self.engine, 'choose_action', side_effect=choose), \
             patch.object(self.engine, 'action_attack_value', side_effect=lambda actor, action, state: -100 if action == 're_shot' else 100), \
             patch.object(self.engine, 'action_defence_value', return_value=0):
            audit = run_audited_fight(self.engine, self.a, self.b, 731840, {})
        exchanges = [event for event in audit['trace'] if event.get('type') == 'exchange']
        total = {'a': 0, 'b': 0}
        observed = []
        for event in exchanges:
            award = event.get('control_award')
            self.assertIsNotNone(award, 'Missing actual credit-point ownership evidence')
            self.assertEqual(set(award), {'position', 'top', 'bottom', 'clinch_controller', 'controller'})
            expected = (award['top'] if award['position'] in {'guard', 'half guard', 'side control', 'mount', 'back control', 'front headlock', 'turtle'}
                        else award['clinch_controller'] if award['position'] in {'clinch', 'cage', 'failed shot', 'standing back control'} else None)
            self.assertEqual(award['controller'], expected)
            self.assertEqual(event['control_delta'], {key: int(key == expected) for key in ('a', 'b')})
            observed.append(control_award_observation(event))
            self.assertNotEqual(observed[-1], 'invalid')
            if event['action'] == 'counter_leg_lock':
                self.assertEqual(event['top_after'], event['actor'])
                self.assertIsNone(expected)
                self.assertEqual(observed[-1], 'uncontrolled')
            if event['action'] == 'survive':
                self.assertEqual(award['position'], 'front headlock')
                self.assertEqual(expected, event['actor'])
                self.assertEqual(event['position_after'], 'range')
                self.assertEqual(event['referee_ground_action']['type'], 'standup')
            if event['action'] == 'standing_escape' or event.get('neutral_scramble_reset'):
                self.assertIsNone(expected)
            if event['action'] == 're_shot':
                self.assertEqual(event['position_after'], 'front headlock')
                self.assertEqual(expected, event['defender'])
            for key in total:
                total[key] += event['control_delta'][key]
        self.assertEqual(rounds, [1, 2, 3])
        self.assertIn('front headlock', observed)
        self.assertIn('turtle', observed)
        self.assertEqual({event['actor'] for event in exchanges}, {'a', 'b'})
        for key in total:
            self.assertEqual(final_state[0]['stats'][key]['control_ticks'], total[key])
            seconds_per_tick = self.engine.rules.get('round_length', 5) * 60 / final_state[0]['ticks_per_round']
            self.assertEqual(audit['stats'][key]['control_secs'], round(total[key] * seconds_per_tick))
            self.assertGreater(total[key], 0)


if __name__ == '__main__':
    unittest.main()
