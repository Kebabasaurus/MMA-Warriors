"""Candidate anti-repetition intent follows adaptability; normal play is unchanged."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, run_audited_fight, synthetic_fighter
from fight_moves import MOVE_REGISTRY


class MoveAdaptabilityTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.a = synthetic_fighter('Adaptive A', 75, 'Boxer', 'Counter', 0)
        self.b = synthetic_fighter('Adaptive B', 75, 'Kickboxer', 'Pressure', 1)
        self.move = MOVE_REGISTRY['single_jab']
        self.state = {'fighter_keys': {id(self.a): 'a', id(self.b): 'b'}}
        self.context = {
            'actor_reads': {'moves': {}, 'targets': {}},
            'plan': {'current': 'Balanced', 'execution': 0},
            'strain': 0, 'recent_misses': 0, 'defender_vulnerability': 0,
            'counter_timing': 75, 'stance_matchup': 'none',
            'actor_grappler': False, 'defender_grappler': False,
            'preferred': (), 'opponent_repeats': 0, 'adaptability': 50,
        }

    def score(self, skill, repeats, enabled=True, **updates):
        self.engine._experimental_chain_action_weighting = enabled
        context = deepcopy(self.context)
        context.update(updates)
        context['adaptability'] = skill
        context['actor_reads']['moves'][self.move.move_id] = repeats
        before, state_before, rng = deepcopy(context), deepcopy(self.state), random.getstate()
        with patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('extra draw')):
            result = self.engine._move_contextual_score(
                self.a, self.b, self.move, self.state, 'a', ('Boxer',),
                False, {}, set(), context=context)
        self.assertEqual(context, before)
        self.assertEqual(self.state, state_before)
        self.assertEqual(random.getstate(), rng)
        return result

    def test_candidate_direction_and_repeat_threshold(self):
        for repeats in (0, 1):
            for skill in (0, 30, 65, 90, 100):
                self.assertEqual(self.score(skill, repeats), (0.0, ()))
        scores = [self.score(skill, 3)[0] for skill in (0, 30, 65, 90, 100)]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertLess(scores[-1], scores[0])
        for skill in (0, 30, 65, 90, 100):
            self.assertAlmostEqual(self.score(skill, 2)[0], -(2.6 + max(0, skill - 65) / 55))

    def test_cap_and_default_legacy_equation(self):
        for skill in (0, 30, 65, 90, 100):
            for enabled in (False, True):
                self.assertEqual(self.score(skill, 100, enabled)[0], -14.0)
            for repeats in (2, 3, 5, 12):
                expected = -min(14.0, (repeats - 1) * (2.6 + max(0, 65 - skill) / 55))
                self.assertEqual(self.score(skill, repeats, False)[0], expected)

    def test_only_repetition_component_changes(self):
        updates = {'strain': 4, 'recent_misses': 3, 'stance_matchup': 'closed',
                   'preferred': ('punch',), 'plan': {'current': 'Attack the body', 'execution': .7}}
        for skill in (30, 90):
            legacy, legacy_reasons = self.score(skill, 3, False, **updates)
            candidate, candidate_reasons = self.score(skill, 3, True, **updates)
            old = 2 * (2.6 + max(0, 65 - skill) / 55)
            new = 2 * (2.6 + max(0, skill - 65) / 55)
            self.assertAlmostEqual(candidate - legacy, old - new)
            self.assertEqual(candidate_reasons, legacy_reasons)
            self.assertIn('pattern-repetition-penalty', candidate_reasons)

    def test_default_off_complete_bout_matches_independent_legacy_penalty(self):
        original = FightAuditHarness._move_contextual_score

        def legacy(engine, actor, defender, definition, state, actor_key, styles,
                   active_counter, active_chain, chain_candidates, context=None, definition_tags=None):
            context = context if context is not None else engine._move_context_inputs(
                actor, defender, state, actor_key, styles)
            repeats = context['actor_reads'].get('moves', {}).get(definition.move_id, 0)
            neutral = dict(context, actor_reads=dict(context['actor_reads'], moves={}))
            score, reasons = original(engine, actor, defender, definition, state, actor_key,
                                     styles, active_counter, active_chain, chain_candidates,
                                     context=neutral, definition_tags=definition_tags)
            if repeats >= 2:
                score -= min(14.0, (repeats - 1) * (2.6 + max(0, 65 - context['adaptability']) / 55))
                reasons = list(reasons)
                index = reasons.index('opponent-pattern-counter') if 'opponent-pattern-counter' in reasons else len(reasons)
                reasons.insert(index, 'pattern-repetition-penalty')
            return score, tuple(reasons)

        self.engine._experimental_chain_action_weighting = False
        rng = random.getstate()
        for seed in (913007, 913009):
            actual = run_audited_fight(self.engine, self.a, self.b, seed, {'rounds': 3})
            with patch.object(FightAuditHarness, '_move_contextual_score', legacy):
                expected = run_audited_fight(self.engine, self.a, self.b, seed, {'rounds': 3})
            self.assertEqual(actual, expected)
        self.assertEqual(random.getstate(), rng)


if __name__ == '__main__':
    unittest.main()
