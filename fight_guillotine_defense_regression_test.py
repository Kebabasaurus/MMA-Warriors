"""Stopped choke pressure is distinct from neck-grip retention and shoulder angle."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import fight_von_flue_setup_regression_test as setup_fixture
from analysis.generate_move_coverage_report import guillotine_defense_observation


class GuillotineDefenseTests(unittest.TestCase):
    setUp = setup_fixture.VonFlueSetupTests.setUp

    def resolve(self, slot='a', margin=-20, grip_edge=10, angle_edge=0,
                position='half guard', name='guillotine choke', choke=True,
                action='bottom_submission', valid_roles=True, clearing_edge=0, bundle_edge=0):
        actor, defender = (self.a, self.b) if slot == 'a' else (self.b, self.a)
        other = 'b' if slot == 'a' else 'a'
        for fighter in (actor, defender):
            fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 50)
        # Each changed skill occurs in precisely one of the two proposed edges.
        actor.detailed_skills['strength'] = 50 + 3 * grip_edge
        defender.detailed_skills['top_control'] = 50 + 3 * angle_edge
        defender.detailed_skills['hand_speed'] = 50 + 3 * clearing_edge
        state = deepcopy(self.initial)
        state.update(position=position, top=other, bottom=slot, round=1, tick=3)
        if not valid_roles:
            state['top'], state['bottom'] = slot, other
        stats = {key: {'impact': 0, 'danger': 0, 'control': 0} for key in ('a', 'b')}
        before = self.engine.fight_trace_snapshot(self.a, self.b, state)
        prior = deepcopy(stats)
        with patch.object(self.engine, 'skill_bundle', side_effect=lambda fighter, key:
                          55 + (bundle_edge if fighter is actor and key == 'submission_game' else 0)), \
             patch.object(self.engine, 'action_attack_value', return_value=margin), \
             patch.object(self.engine, 'action_defence_value', return_value=0), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.randint.return_value = 0
            rng.return_value.choice.return_value = (name, choke)
            rng.return_value.random.return_value = 0
            text = self.engine.resolve_exchange(actor, defender, action, state, stats)
            draws = (rng.return_value.randint.call_count, rng.return_value.choice.call_count,
                     rng.return_value.random.call_count)
        return actor, defender, state, stats, before, prior, text, draws

    def test_three_aftermaths_boundaries_and_preserved_control_both_slots(self):
        for slot in ('a', 'b'):
            for grip, angle, retained, positioned in ((1, 0, False, False),
                    (2, -1, True, False), (2, 0, True, True), (2, 1, True, True)):
                with self.subTest(slot=slot, grip=grip, angle=angle):
                    _, _, state, stats, before, _, _, draws = self.resolve(slot, grip_edge=grip, angle_edge=angle)
                    other = 'b' if slot == 'a' else 'a'
                    fact = state.get('last_guillotine_defense')
                    self.assertIsNotNone(fact, 'Strong denial needs explicit grip/angle evidence')
                    self.assertEqual(fact, dict(top=other, bottom=slot, position='half guard',
                        round=1, tick=3, adjusted_margin=-20, retention_margin=grip - 1,
                        shoulder_margin=angle, pressure_stopped=True, neck_wrap_retained=retained,
                        shoulder_angle_established=positioned, top_control_consolidated=True))
                    self.assertEqual(bool(state.get('von_flue_setup')), positioned)
                    if positioned:
                        self.assertEqual(state['von_flue_setup'], dict(top=other, bottom=slot,
                            position='half guard', round=1, created_tick=3))
                    self.assertEqual((state['position'], state['top'], state['bottom']), ('half guard', other, slot))
                    self.assertEqual(stats[other], {'impact': 0, 'danger': 0, 'control': 2})
                    self.assertEqual(stats[slot], {'impact': 0, 'danger': 0, 'control': 0})
                    self.assertEqual(state['stats'][slot]['sub_att'], 1)
                    for key in ('gas', 'damage'):
                        self.assertEqual(state[key], before[key])
                    self.assertEqual(state['danger'], self.initial['danger'])
                    self.assertEqual(draws, (1, 1, 0))

    def test_severity_and_clearing_skill_monotonicity(self):
        for slot in ('a', 'b'):
            scores = []
            for margin in (-11, -20, -30, -50):
                state = self.resolve(slot, margin=margin, grip_edge=2)[2]
                fact = state.get('last_guillotine_defense')
                self.assertIsNotNone(fact)
                scores.append(fact['retention_margin'])
            self.assertEqual(scores, sorted(scores, reverse=True))
            self.assertGreater(scores[0], 0)
            self.assertLess(scores[-1], 0)
            scores = [self.resolve(slot, grip_edge=3, clearing_edge=edge)[2].get('last_guillotine_defense', {}).get('retention_margin')
                      for edge in (0, 1, 2, 3)]
            self.assertEqual(scores, [2, 1, 0, -1])

    def test_adjusted_contest_not_raw_margin_drives_assessment(self):
        state = self.resolve(margin=-9, bundle_edge=-25, grip_edge=2)[2]
        fact = state.get('last_guillotine_defense')
        self.assertIsNotNone(fact)
        self.assertEqual(fact['adjusted_margin'], -12)
        self.assertAlmostEqual(fact['retention_margin'], 1.8)
        # The inverse adjustment leaves the strong-denial branch entirely.
        state = self.resolve(margin=-12, bundle_edge=25, grip_edge=2)[2]
        self.assertFalse('last_guillotine_defense' in state)

    def test_only_actual_plain_bottom_half_strong_nonfinish_is_assessed(self):
        for kwargs in ({'margin': -10}, {'margin': 30}, {'position': 'guard'},
                       {'position': 'side control'}, {'action': 'submission'},
                       {'valid_roles': False}, {'name': 'arm-in guillotine'},
                       {'name': 'high-elbow guillotine'}, {'name': 'front headlock choke'},
                       {'name': 'kimura', 'choke': False}, {'choke': False}):
            with self.subTest(kwargs=kwargs):
                state = self.resolve(**kwargs)[2]
                self.assertFalse('last_guillotine_defense' in state)
        self.engine._experimental_specialist_entries = False
        state = self.resolve()[2]
        self.assertFalse('last_guillotine_defense' in state)
        self.assertFalse('von_flue_setup' in state)
        self.assertEqual(state['last_submission_escape']['consequence'], 'top control consolidated')

    def test_actual_trace_rendering_and_single_use_provenance(self):
        for slot in ('a', 'b'):
            for grip, angle, phrase in ((0, 0, 'clears'), (2, -1, 'no shoulder'), (2, 0, 'shoulder')):
                with self.subTest(slot=slot, grip=grip, angle=angle):
                    actor, defender, state, stats, before, prior, text, _ = self.resolve(slot, grip_edge=grip, angle_edge=angle)
                    event = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender,
                        'bottom_submission', text, before, prior, state, stats)
                    self.assertTrue('guillotine_defense' in event, 'Trace omitted the resolved grip assessment')
                    self.assertEqual(event['guillotine_defense'], state['last_guillotine_defense'])
                    self.assertEqual(event['guillotine_defense']['bottom'], event['actor'])
                    self.assertEqual(event['guillotine_defense']['top'], event['top_before'])
                    self.assertEqual(guillotine_defense_observation(event),
                                     'grip_cleared' if grip <= 1 else
                                     'wrap_retained' if angle < 0 else 'von_flue_ready')
                    for technical in (False, True):
                        line = self.engine.render_exchange_trace_event(event, technical=technical).lower()
                        self.assertIn('guillotine', line)
                        self.assertIn(phrase, line)
                        self.assertIn('top', line)
                        reset = dict(event, referee_ground_action={'type': 'standup', 'text': 'Referee reset.'})
                        self.assertEqual(self.engine.render_exchange_trace_event(reset, technical=technical), 'Referee reset.')
                    state['tick'] = 4
                    tickets = self.engine.submission_technique_tickets(defender, 'submission', state)
                    self.assertEqual(('Von Flue choke', True) in tickets, grip > 1 and angle >= 0)
                    with patch.object(self.engine, '_resolve_exchange_action', return_value='Reset grips.'):
                        self.engine.resolve_exchange(actor, defender, 'survive', state, stats)
                    self.assertFalse('last_guillotine_defense' in state)
                    self.assertFalse('von_flue_setup' in state)

    def test_horn_clears_transient_assessment(self):
        rounds = []
        def choose(actor, defender, state, round_no, tick):
            if tick == 1:
                self.assertFalse('last_guillotine_defense' in state)
                rounds.append(round_no)
            state['last_guillotine_defense'] = {'pressure_stopped': True}
            return 'survive'
        # Keep the marker alive across exchanges to test the horn itself.
        with patch.object(self.engine, 'choose_action', side_effect=choose), \
             patch.object(self.engine, 'resolve_exchange', return_value='Waiting.'):
            self.engine.simulate_fight(self.a, self.b, {})
        self.assertEqual(rounds, [1, 2, 3])


if __name__ == '__main__':
    unittest.main()
