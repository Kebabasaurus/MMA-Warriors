"""Experimental nonfinishing leg-lock retention; original finish logic stays first."""
from collections import defaultdict
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter


class LegEntryTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.engine._experimental_specialist_entries = True
        self.a = synthetic_fighter('Same Name', 75, 'BJJ', 'Control', 0)
        self.b = synthetic_fighter('Same Name', 75, 'Wrestler', 'Control', 1)
        for fighter in (self.a, self.b):
            fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 75)
            fighter.trait = 'Pressure Fighter'
        self.addCleanup(random.setstate, random.getstate())

    def state(self, actor_key='a', position='guard', action='bottom_submission'):
        other = 'b' if actor_key == 'a' else 'a'
        return {'position': position, 'top': other if action == 'bottom_submission' else actor_key,
                'bottom': actor_key if action == 'bottom_submission' else other, 'clinch_controller': None,
                'fighter_keys': {id(self.a): actor_key, id(self.b): other},
                'stats': {key: defaultdict(int) for key in ('a', 'b')},
                'gas': {'a': 80, 'b': 80}, 'danger': {'a': 0, 'b': 0}}

    def resolve(self, state, *, action='bottom_submission', margin=20, technique='heel hook', finish=False):
        stats = {key: defaultdict(int) for key in ('a', 'b')}
        with patch.object(self.engine, 'submission_technique', return_value={'name': technique, 'choke': False}), \
             patch.object(self.engine, 'competitive_finish_conversion', return_value=1), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.random.return_value = 0 if finish else 1
            text = self.engine.resolve_submission(self.a, self.b, action, margin, state, stats)
            rng.return_value.randint.assert_not_called()
            rng.return_value.choice.assert_not_called()
            self.assertEqual(rng.return_value.random.call_count, 1 if margin >= 0 else 0)
        return text, stats

    def test_matched_nonfinishing_leg_entries_keep_technique_credit_and_knee_line_roles(self):
        for actor_key in ('a', 'b'):
            other = 'b' if actor_key == 'a' else 'a'
            for position in ('guard', 'half guard'):
                state = self.state(actor_key, position)
                text, stats = self.resolve(state)
                self.assertEqual(state['position'], 'leg entanglement')
                self.assertEqual((state['top'], state['bottom']), (actor_key, other))
                self.assertEqual(state['last_submission_technique']['name'], 'heel hook')
                self.assertIn('heel hook', text)
                self.assertEqual(state['stats'][actor_key]['sub_att'], 1)
                self.assertEqual(state['gas'][other], 70)
                self.assertEqual(state['danger'][actor_key], 14)
                self.assertEqual(stats[actor_key]['danger'], 14)
                self.engine.validate_fight_transition(position, state['position'], state)

    def test_nonleg_nontop_level_action_and_position_prerequisites(self):
        for action, position, technique in (('bottom_submission', 'guard', 'armbar'),
                                            ('submission', 'guard', 'heel hook'),
                                            ('bottom_submission', 'side control', 'heel hook'),
                                            ('bottom_submission', 'turtle', 'heel hook')):
            state = self.state(position=position, action=action)
            self.resolve(state, action=action, technique=technique)
            self.assertEqual(state['position'], position)

    def test_minimum_leg_skill_and_defensive_advantage(self):
        self.a.detailed_skills['leg_locks'] = 64
        state = self.state()
        self.resolve(state)
        self.assertEqual(state['position'], 'guard')
        self.a.detailed_skills['leg_locks'] = 65
        state = self.state()
        self.resolve(state)
        self.assertEqual(state['position'], 'leg entanglement')
        for key in ('submission_defence_detail', 'scrambles', 'get_ups'):
            self.b.detailed_skills[key] = 95
        state = self.state()
        self.resolve(state)
        self.assertEqual(state['position'], 'guard')

    def test_adjusted_margin_threshold_is_inclusive_without_another_draw(self):
        # Skill bundles55, guard work55, instinct/composure50 give danger5 and
        # no margin adjustment; margin15 gives20*0.25, exactly cancelling -5.
        def skill(fighter, key, fallback=50):
            return 65 if key == 'leg_locks' else 55 if key == 'guard_work' else 50
        with patch.object(self.engine, 'skill_bundle', return_value=55), \
             patch.object(self.engine, 'ds', side_effect=skill), \
             patch.object(self.engine, 'ds_avg', side_effect=lambda fighter, keys, fallback: 75 if fighter is self.a else 80):
            for margin, expected in ((14.99, 'guard'), (15, 'leg entanglement')):
                state = self.state()
                self.resolve(state, margin=margin)
                self.assertEqual(state['position'], expected)

    def test_finish_and_nondangerous_attempt_do_not_evaluate_retention(self):
        for finish, margin in ((True, 20), (False, -20)):
            state = self.state()
            with patch.object(self.engine, 'ds_avg', side_effect=AssertionError('retention should not run')):
                self.resolve(state, finish=finish, margin=margin)
            self.assertEqual(state['position'], 'guard')
            self.assertEqual('submission_finish' in state, finish)

    def test_exact_danger_boundary_does_not_roll_finish_or_retain(self):
        def skill(fighter, key, fallback=50):
            return 65 if key == 'leg_locks' else 55 if key == 'guard_work' else 50
        state = self.state()
        with patch.object(self.engine, 'skill_bundle', return_value=55), \
             patch.object(self.engine, 'ds', side_effect=skill), \
             patch.object(self.engine, 'submission_technique', return_value={'name': 'heel hook', 'choke': False}), \
             patch.object(self.engine, 'ds_avg', side_effect=AssertionError('retention at danger boundary')), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            self.engine.resolve_submission(self.a, self.b, 'bottom_submission', 3, state,
                                           {key: defaultdict(int) for key in ('a', 'b')})
            rng.assert_not_called()
        self.assertEqual(state['position'], 'guard')
        self.assertEqual(state['gas']['b'], 80)

    def test_default_off_preserves_elite_trait_predicate(self):
        self.engine._experimental_specialist_entries = False
        state = self.state()
        self.resolve(state)
        self.assertEqual(state['position'], 'guard')
        self.a.trait = 'Submission Ace'
        self.a.detailed_skills['leg_locks'] = 95
        self.b.detailed_skills['submission_defence_detail'] = 40
        state = self.state()
        self.resolve(state, margin=40)
        self.assertEqual(state['position'], 'leg entanglement')
        self.a.trait = 'Pressure Fighter'
        state = self.state()
        self.resolve(state, margin=40)
        self.assertEqual(state['position'], 'guard')

    def test_actual_mechanical_technique_draw_is_retained_not_replaced(self):
        state = self.state()
        with patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.choice.side_effect = lambda options: next(row for row in options if row[0] == 'straight ankle lock')
            rng.return_value.random.return_value = 1
            text = self.engine.resolve_submission(self.a, self.b, 'bottom_submission', 20, state,
                                                 {key: defaultdict(int) for key in ('a', 'b')})
            rng.return_value.choice.assert_called_once()
            rng.return_value.random.assert_called_once()
        self.assertEqual(state['position'], 'leg entanglement')
        self.assertEqual(state['last_submission_technique']['name'], 'straight ankle lock')
        self.assertIn('straight ankle lock', text)


if __name__ == '__main__':
    unittest.main()
