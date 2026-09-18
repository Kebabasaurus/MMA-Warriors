"""Retained wraps require a separate, contested positioning beat before attack."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import MOVE_REGISTRY, MoveIndex
from analysis.von_flue_angle_provenance import validate_von_flue_angles
from analysis.generate_move_coverage_report import von_flue_setup_counts


class VonFlueAngleTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.engine._experimental_specialist_entries = True
        self.a = synthetic_fighter('A', 80, 'BJJ', 'Control', 0)
        self.b = synthetic_fighter('B', 80, 'Judo', 'Control', 1)
        for fighter in (self.a, self.b):
            fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 80)
        self.addCleanup(random.setstate, random.getstate())
        captured = []
        class Ready(Exception):
            pass
        def capture(*args):
            captured.append(args[2])
            raise Ready()
        with patch.object(self.engine, 'choose_action', side_effect=capture):
            with self.assertRaises(Ready):
                self.engine.simulate_fight(self.a, self.b, {})
        self.initial = captured[0]

    def pending(self, slot='a', name='guillotine choke', margin=-20, shoulder=-20, retained=True):
        bottom, top = (self.a, self.b) if slot == 'a' else (self.b, self.a)
        state = deepcopy(self.initial)
        state.update(position='half guard', bottom=slot, top='b' if slot == 'a' else 'a', round=1, tick=3)
        stats = {k: {'control': 0, 'impact': 0, 'danger': 0} for k in ('a', 'b')}
        before, prior = self.engine.fight_trace_snapshot(self.a, self.b, state), deepcopy(stats)
        def avg(fighter, keys, fallback):
            if keys == ('guard_work', 'strength', 'submission_attack'):
                return 80 if retained else 40
            if keys == ('submission_defence_detail', 'hand_speed', 'composure'):
                return 60
            return 60 + shoulder if fighter is top else 60
        with patch.object(self.engine, 'action_attack_value', return_value=margin), \
             patch.object(self.engine, 'action_defence_value', return_value=0), \
             patch.object(self.engine, 'skill_bundle', return_value=55), \
             patch.object(self.engine, 'ds', return_value=50), \
             patch.object(self.engine, 'ds_avg', side_effect=avg), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.randint.return_value = 0
            rng.return_value.choice.side_effect = lambda pool: next(row for row in pool if row == (name, True))
            text = self.engine.resolve_exchange(bottom, top, 'bottom_submission', state, stats)
            rng.return_value.random.assert_not_called()
            rng.return_value.choice.assert_called_once()
        event = self.engine.record_fight_trace_exchange(self.a, self.b, bottom, top,
            'bottom_submission', text, before, prior, state, stats)
        return bottom, top, state, stats, event

    def angle(self, bottom, top, state, stats, margin=9, edge=0):
        state['tick'] = 4
        before, prior = self.engine.fight_trace_snapshot(self.a, self.b, state), deepcopy(stats)
        with patch.object(self.engine, 'action_attack_value', return_value=margin), \
             patch.object(self.engine, 'action_defence_value', return_value=0), \
             patch.object(self.engine, 'ds_avg', side_effect=lambda fighter, keys, fallback: 60 + (edge if fighter is top else 0)), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.randint.return_value = 0
            text = self.engine.resolve_exchange(top, bottom, 'ground_control', state, stats)
            rng.return_value.randint.assert_called_once()
            rng.return_value.random.assert_not_called()
            rng.return_value.choice.assert_not_called()
        return before, prior, text

    def test_pending_only_from_actual_strong_retained_plain_guillotine_without_angle(self):
        for slot in ('a', 'b'):
            _, top, state, _, event = self.pending(slot)
            self.assertEqual(event['von_flue_angle']['status'], 'pending')
            self.assertNotIn('von_flue_setup', state)
            state['tick'] = 4
            self.assertNotIn(('Von Flue choke', True), self.engine.submission_technique_tickets(top, 'submission', state))
        for kwargs in ({'name': 'arm-in guillotine'}, {'margin': -5}, {'shoulder': 0}, {'retained': False}):
            self.assertNotIn('von_flue_pending_wrap', self.pending(**kwargs)[2])
        self.engine._experimental_specialist_entries = False
        self.assertNotIn('von_flue_pending_wrap', self.pending()[2])

    def test_thresholds_preserve_existing_control_only_and_never_refresh_pending(self):
        for slot in ('a', 'b'):
            for margin, edge, ready in ((8, 0, False), (8.001, 0, True), (6, 10, False), (6.001, 10, True), (10, -10, False)):
                bottom, top, state, stats, _ = self.pending(slot)
                before, prior, _ = self.angle(bottom, top, state, stats, margin, edge)
                self.assertEqual(state['last_von_flue_angle']['status'], 'ready' if ready else 'cleared')
                self.assertNotIn('von_flue_pending_wrap', state)
                self.assertEqual(state['stats'], before['stats'])
                self.assertEqual(state['gas'], before['gas'])
                self.assertEqual(state['damage'], before['damage'])
                self.assertEqual(state['danger'], self.initial['danger'])
                self.assertEqual(stats[state['top']]['control'] - prior[state['top']]['control'], 3)
                self.assertEqual(stats[state['top']]['danger'], 0)
                self.assertEqual((state['position'], state['top'], state['bottom']),
                                 (before['position'], before['top'], before['bottom']))
                self.assertEqual('von_flue_setup' in state, ready)
                if ready:
                    self.assertEqual(state['von_flue_setup']['created_tick'], 4)
                    self.assertEqual(state['von_flue_setup']['origin_tick'], 3)
                    state['tick'] = 6
                    self.assertNotIn(('Von Flue choke', True), self.engine.submission_technique_tickets(top, 'submission', state))

    def test_three_real_beats_and_truthful_generic_control(self):
        for slot in ('a', 'b'):
            bottom, top, state, stats, pending = self.pending(slot)
            before, prior, text = self.angle(bottom, top, state, stats)
            move = next(m for m in MOVE_REGISTRY.values() if m.parent_action == 'ground_control' and 'half guard' in m.positions)
            top.signature_moves = [move.move_id, 'generic_ground_control']
            top.move_mastery = {move.move_id: 100, 'generic_ground_control': 100}
            with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves):
                ready = self.engine.record_fight_trace_exchange(self.a, self.b, top, bottom,
                    'ground_control', text, before, prior, state, stats)
            self.assertEqual(ready['move_id'], 'generic_ground_control')
            self.assertFalse(ready['signature'])
            self.assertEqual(ready['move_mastery'], 0)
            self.assertEqual(ready['sequence_source_id'], '')
            self.assertIn('has not yet been applied', self.engine.render_exchange_trace_event(ready))
            state['tick'] = 5
            before, prior = self.engine.fight_trace_snapshot(self.a, self.b, state), deepcopy(stats)
            with patch.object(self.engine, 'action_attack_value', return_value=30), \
                 patch.object(self.engine, 'action_defence_value', return_value=0), \
                 patch.object(self.engine, 'fight_mechanics_rng') as rng:
                rng.return_value.randint.return_value = 0
                rng.return_value.random.return_value = 1
                rng.return_value.choice.side_effect = lambda pool: next(row for row in pool if row[0] == 'Von Flue choke')
                text = self.engine.resolve_exchange(top, bottom, 'submission', state, stats)
                rng.return_value.choice.assert_called_once()
                rng.return_value.random.assert_called_once()
            used = self.engine.record_fight_trace_exchange(self.a, self.b, top, bottom,
                'submission', text, before, prior, state, stats)
            self.assertEqual(used['von_flue_setup']['status'], 'used')
            self.assertEqual(used['submission_technique']['name'], 'Von Flue choke')
            self.assertNotIn('von_flue_setup', state)
            proof = validate_von_flue_angles([pending, ready, used])
            self.assertEqual(proof['counts'], {'pending': 1, 'ready': 1})
            self.assertEqual(von_flue_setup_counts([pending, ready, used]), {'created': 1, 'used': 1})
            for field, value in (('origin_tick', 2), ('source', 'unproved')):
                corrupted = deepcopy(used)
                corrupted['von_flue_setup'][field] = value
                self.assertEqual(von_flue_setup_counts([pending, ready, corrupted]), {'created': 1, 'invalid': 1})

    def test_invalid_context_other_action_or_opponent_cancels(self):
        for change in ({'tick': 5}, {'round': 2}, {'position': 'guard'}, {'top': 'a', 'bottom': 'b'}):
            bottom, top, state, stats, _ = self.pending()
            state.update(tick=4, **{k: v for k, v in change.items() if k != 'tick'})
            if 'tick' in change:
                state['tick'] = change['tick']
            self.assertFalse(self.engine._valid_von_flue_pending(top, 'ground_control', state))
        for use_bottom, action in ((True, 'survive'), (False, 'submission'), (False, 'advance_position')):
            bottom, top, state, stats, _ = self.pending()
            state['tick'] = 4
            with patch.object(self.engine, '_resolve_exchange_action', return_value='Action.'):
                self.engine.resolve_exchange(bottom if use_bottom else top, top if use_bottom else bottom, action, state, stats)
            self.assertNotIn('von_flue_pending_wrap', state)
            self.assertEqual(state['last_von_flue_angle']['status'], 'cancelled')
        _, _, state, _, _ = self.pending()
        self.engine.set_fight_position(state, 'guard', top=state['top'], bottom=state['bottom'])
        self.assertNotIn('von_flue_pending_wrap', state)

    def test_referee_overrides_new_ready_setup_and_keeps_generic_credit(self):
        bottom, top, state, stats, pending = self.pending()
        before, prior, text = self.angle(bottom, top, state, stats)
        state.update(ground_warning=True, ground_inactivity=5)
        with patch.object(self.engine, 'referee_profile', return_value={'standup_threshold': 4}):
            self.engine.update_ground_inactivity(state, 'ground_control')
        self.assertNotIn('von_flue_setup', state)
        self.assertEqual(state['last_von_flue_angle']['status'], 'cancelled')
        self.assertEqual(state['last_von_flue_setup_event']['status'], 'cancelled')
        event = self.engine.record_fight_trace_exchange(self.a, self.b, top, bottom,
            'ground_control', text, before, prior, state, stats)
        self.assertEqual(event['move_id'], 'generic_ground_control')
        self.assertEqual(self.engine.render_exchange_trace_event(event), state['last_referee_ground_action']['text'])
        self.assertEqual(validate_von_flue_angles([pending, event])['counts'], {'pending': 1, 'cancelled': 1})
        self.assertEqual(von_flue_setup_counts([pending, event]), {'cancelled': 1})

    def test_horn_and_finish_clear_pending_without_waiting_for_another_action(self):
        bottom, top, state, _, _ = self.pending()
        state['instant_finish'] = (state['top'], state['bottom'], 'KO', 'Strike.')
        self.engine.check_fight_stoppage(top, bottom, state)
        self.assertNotIn('von_flue_pending_wrap', state)
        self.assertEqual(state['last_von_flue_angle']['reason'], 'fight_finished')
        rounds = []
        def choose(actor, defender, state, round_no, tick):
            if tick == 1:
                self.assertNotIn('von_flue_pending_wrap', state)
                self.assertNotIn('last_von_flue_angle', state)
                rounds.append(round_no)
            self.engine.set_fight_position(state, 'half guard',
                top=self.engine.fight_state_key(defender, state), bottom=self.engine.fight_state_key(actor, state))
            return 'bottom_submission'
        def avg(fighter, keys, fallback):
            return 80 if keys == ('guard_work', 'strength', 'submission_attack') else 40 if keys == ('top_control', 'positional_ability', 'strength') else 60
        with patch.object(self.engine, 'choose_action', side_effect=choose), \
             patch.object(self.engine, 'action_attack_value', return_value=-100), \
             patch.object(self.engine, 'action_defence_value', return_value=0), \
             patch.object(self.engine, 'skill_bundle', return_value=55), \
             patch.object(self.engine, 'ds', return_value=50), \
             patch.object(self.engine, 'ds_avg', side_effect=avg), \
             patch.object(self.engine, 'submission_technique', return_value={'name': 'guillotine choke', 'choke': True}):
            self.engine.simulate_fight(self.a, self.b, {})
        self.assertEqual(rounds, [1, 2, 3])


if __name__ == '__main__':
    unittest.main()
