"""Mechanical submission identity must win over incompatible authored credit."""
from copy import deepcopy
from dataclasses import replace
import random
import unittest
from unittest.mock import patch

import fight_engine
from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import MOVE_REGISTRY, MoveIndex
from fight_moves.catalogue.leg_entanglement_development import LEG_ATTACK_DEVELOPMENT
from fight_moves.submission_identity import COMPATIBLE_SUBMISSION_IDS, compatible_submission_ids
from analysis.fight_candidate_context import DRAFT_MOVE_DEFINITIONS


class SubmissionIdentityTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.engine._experimental_specialist_entries = True
        self.a = synthetic_fighter('Leg A', 80, 'Grappler', 'Control', 0)
        self.b = synthetic_fighter('Leg B', 80, 'Wrestler', 'Control', 1)
        self.registry = dict(MOVE_REGISTRY, **{m.move_id: m for m in DRAFT_MOVE_DEFINITIONS})
        self.addCleanup(random.setstate, random.getstate())

    def state(self):
        return {'position': 'leg entanglement', 'top': 'a', 'bottom': 'b', 'clinch_controller': None,
                'round': 1, 'tick': 2, 'fighter_keys': {id(self.a): 'a', id(self.b): 'b'}}

    def select(self, move, evidence, state=None):
        with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves):
            return self.engine.select_exchange_move(self.a, self.b, move.parent_action,
                                                   next(iter(move.positions)), '', state or self.state(),
                                                   resolved_technique=evidence)

    def test_mapping_resolves_without_unsupported_deliveries(self):
        for ids in COMPATIBLE_SUBMISSION_IDS.values():
            self.assertTrue(set(ids) <= self.registry.keys())
        for name, forbidden in (('kneebar', 'entangled_rolling_kneebar'),
                                ('straight ankle lock', 'entangled_belly_down_ankle_lock'),
                                ('guillotine choke', 'front_ten_finger_guillotine')):
            self.assertNotIn(forbidden, compatible_submission_ids({'name': name}))
        for evidence in ({'name': 'unknown lock'}, {}, {'name': None}, 'heel hook'):
            self.assertEqual(compatible_submission_ids(evidence), ())

    def test_all_submission_parents_filter_before_signature_exclusions(self):
        cases = (('guard_armbar', 'armbar'), ('arm_triangle', 'arm-triangle choke'),
                 ('guillotine_choke', 'guillotine choke'), ('entangled_inside_heel_hook', 'inside heel hook'))
        self.assertEqual({self.registry[key].parent_action for key, _ in cases},
                         {'bottom_submission', 'submission', 'front_headlock_submission', 'leg_attack'})
        for key, name in cases:
            move = self.registry[key]
            self.a.signature_moves = [key]
            self.a.move_mastery = {key: 95}
            before = random.getstate()
            self.assertEqual(self.select(move, {'name': name})['move_id'], key)
            payload = self.select(move, {'name': 'unknown lock'})
            self.assertTrue(payload['generic'])
            self.assertFalse(payload['signature'])
            self.assertEqual(payload['follow_up_ids'], ())
            self.assertEqual(random.getstate(), before)

    def test_default_off_and_isolated_authoring_do_not_infer_stale_evidence(self):
        move = self.registry['entangled_rolling_kneebar']
        state = self.state()
        state['last_submission_technique'] = {'name': 'heel hook'}
        self.assertEqual(self.select(move, None, state)['move_id'], move.move_id)
        self.assertTrue(self.select(move, {'name': 'heel hook'}, state)['generic'])
        self.engine._experimental_specialist_entries = False
        self.assertEqual(self.select(move, {'name': 'heel hook'}, state)['move_id'], move.move_id)
        self.engine._experimental_specialist_entries = True
        jab = self.registry['single_jab']
        self.assertEqual(self.select(jab, {'name': 'heel hook'})['move_id'], jab.move_id)

    def test_incompatible_signature_finisher_cannot_exclude_compatible_identity(self):
        matching = replace(self.registry['entangled_outside_heel_hook'],
                           tags=('submission', 'leg-lock', 'style-finisher'), preferred_styles=('Grappler',))
        wrong = replace(matching, move_id='sambo_rolling_kneebar_finisher')
        self.a.signature_moves = [wrong.move_id]
        with patch('fight_engine.legal_moves', side_effect=MoveIndex((matching, wrong)).legal_moves), \
             patch.object(self.engine, '_move_rarity_gate', return_value=True):
            payload = self.engine.select_exchange_move(self.a, self.b, 'leg_attack', 'leg entanglement', '',
                                                       self.state(), resolved_technique={'name': 'outside heel hook'})
        self.assertEqual(payload['move_id'], matching.move_id)
        self.assertFalse(payload['signature'])

    def test_pre_action_preview_ignores_stale_resolved_technique(self):
        self.engine._experimental_chain_action_weighting = True
        state = self.state()
        state['move_chains'] = {'a': {'round': 1, 'tick': 1, 'actor_role': 'top',
                                    'branch_options': ['entangled_inside_heel_hook']}}
        move = self.registry['entangled_inside_heel_hook']
        weights = {'leg_attack': 100, 'leg_control': 100, 'disengage_leg': 100}
        with patch('fight_engine.MOVE_REGISTRY', self.registry), \
             patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves):
            first = self.engine._chain_action_weights(self.a, self.b, state, weights, 1, 2)
            state['last_submission_technique'] = {'name': 'armbar'}
            self.assertEqual(self.engine._chain_action_weights(self.a, self.b, state, weights, 1, 2), first)
        self.assertGreater(first['leg_attack'], weights['leg_attack'])

    def test_real_resolution_trace_and_finish_summary_do_not_credit_wrong_signature(self):
        class Ready(Exception):
            pass
        captured = []
        def capture(actor, defender, state, round_no, tick):
            captured.append(state)
            raise Ready()
        with patch.object(self.engine, 'choose_action', side_effect=capture):
            with self.assertRaises(Ready):
                self.engine.simulate_fight(self.a, self.b, {})
        for move_id, actual_name, expected in (
                ('entangled_rolling_kneebar', 'heel hook', 'generic_leg_attack'),
                ('entangled_rolling_kneebar', 'kneebar', 'generic_leg_attack'),
                ('entangled_belly_down_ankle_lock', 'straight ankle lock', 'generic_leg_attack'),
                ('entangled_inside_heel_hook', 'inside heel hook', 'entangled_inside_heel_hook')):
            self.a.signature_moves = [move_id, 'generic_leg_attack']
            self.a.move_mastery = {move_id: 95, 'generic_leg_attack': 100}
            move = self.registry[move_id]
            state = deepcopy(captured[0])
            state.update(position='leg entanglement', top='a', bottom='b', clinch_controller=None)
            before = self.engine.fight_trace_snapshot(self.a, self.b, state)
            stats = {key: {'impact': 0, 'danger': 0, 'control': 0} for key in ('a', 'b')}
            prior = deepcopy(stats)
            with patch.object(self.engine, 'action_attack_value', return_value=30), \
                 patch.object(self.engine, 'action_defence_value', return_value=0), \
                 patch.object(self.engine, 'fight_mechanics_rng') as rng:
                rng.return_value.randint.return_value = 0
                rng.return_value.choice.side_effect = lambda options: next(row for row in options if row[0] == actual_name)
                rng.return_value.random.return_value = 0  # Real finish branch, no second roll for joints.
                text = self.engine.resolve_exchange(self.a, self.b, 'leg_attack', state, stats)
                rng.return_value.choice.assert_called_once()
                rng.return_value.random.assert_called_once()
            with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves), \
                 patch('fight_engine.MOVE_REGISTRY', self.registry):
                event = self.engine.record_fight_trace_exchange(self.a, self.b, self.a, self.b,
                                                              'leg_attack', text, before, prior, state, stats)
            self.assertEqual(event['submission_technique']['name'], actual_name)
            self.assertEqual(event['move_id'], expected)
            rendered = self.engine.render_exchange_trace_event(event, technical=True)
            self.assertIn(actual_name, rendered)
            if expected.startswith('generic'):
                self.assertFalse(event['signature'])
                self.assertEqual(event['move_mastery'], 0)
                self.assertNotIn('signature', rendered.lower())
            else:
                self.assertTrue(event['signature'])
                self.assertEqual(event['move_mastery'], 95)
            self.engine.finalize_fight_result(self.a, self.b, self.a, self.b, 'Submission', 1, [], state)
            summary = self.engine._last_fight_result.metrics['signature_moves']['a']
            self.assertNotIn('generic_leg_attack', summary)
            if expected.startswith('generic'):
                self.assertNotIn(move_id, summary)
            else:
                self.assertEqual(summary[move_id]['finishes'], 1)


if __name__ == '__main__':
    unittest.main()
