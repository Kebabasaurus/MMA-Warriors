"""A Von Flue attempt requires a real, one-exchange retained guillotine wrap."""
from collections import defaultdict
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import MOVE_REGISTRY, MoveIndex
from analysis.generate_move_coverage_report import von_flue_setup_counts


class VonFlueSetupTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.engine._experimental_specialist_entries = True
        self.a = synthetic_fighter('Red', 75, 'BJJ', 'Control', 0)
        self.b = synthetic_fighter('Blue', 75, 'Wrestler', 'Control', 1)
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

    def create(self, slot='a', margin=-5, *, edge=0, position='half guard',
               name='guillotine choke', choke=True, action='bottom_submission', finish=False):
        actor, defender = (self.a, self.b) if slot == 'a' else (self.b, self.a)
        other = 'b' if slot == 'a' else 'a'
        state = deepcopy(self.initial)
        state.update(position=position, top=other, bottom=slot, round=1, tick=3)
        stats = {key: defaultdict(int) for key in ('a', 'b')}
        with patch.object(self.engine, 'skill_bundle', return_value=55), \
             patch.object(self.engine, 'ds', return_value=50), \
             patch.object(self.engine, 'ds_avg', side_effect=lambda fighter, keys, fallback: 60 + (edge if fighter is defender else 0)), \
             patch.object(self.engine, 'submission_technique', return_value={'name': name, 'choke': choke}), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.random.return_value = 0 if finish else 1
            text = self.engine.resolve_submission(actor, defender, action, margin, state, stats)
            draws = rng.return_value.random.call_count
        return actor, defender, state, stats, text, draws

    def test_creation_bounds_both_slots_and_no_added_credit(self):
        for slot in ('a', 'b'):
            for margin in (-10, -5, 0):
                actor, defender, state, stats, text, draws = self.create(slot, margin)
                other = 'b' if slot == 'a' else 'a'
                self.assertEqual(state['von_flue_setup'], {'top': other, 'bottom': slot,
                    'position': 'half guard', 'round': 1, 'created_tick': 3})
                self.assertEqual((state['position'], state['top'], state['bottom']), ('half guard', other, slot))
                self.assertEqual(state['gas'], self.initial['gas'])
                self.assertEqual(state['danger'], self.initial['danger'])
                self.assertEqual(state['stats'][slot]['sub_att'], 1)
                self.assertFalse(any(sum(row.values()) for row in stats.values()))
                self.assertEqual(draws, 0)
                self.assertIn('retains the neck wrap', text)
                self.assertEqual(state['last_submission_escape']['consequence'],
                                 'pressure relieved; guillotine neck wrap retained')

    def test_creation_rejects_variants_advantage_wrong_position_and_after_finish(self):
        for kwargs in ({'margin': -10.01}, {'margin': 0.01}, {'edge': -0.01},
                       {'name': 'arm-in guillotine'}, {'name': 'high-elbow guillotine'}, {'choke': False},
                       {'position': 'guard'}, {'action': 'submission'}, {'margin': 40, 'finish': True}):
            self.assertNotIn('von_flue_setup', self.create(**kwargs)[2])
        self.engine._experimental_specialist_entries = False
        self.assertNotIn('von_flue_setup', self.create()[2])

    def test_adjusted_not_raw_margin_controls_creation(self):
        # The create fixture holds both bundle values equal and instinct equal;
        # use a separate real call to move the adjusted margin outside the gate.
        actor, defender, state, stats, *_ = self.create()
        state.pop('von_flue_setup')
        with patch.object(self.engine, 'skill_bundle', side_effect=lambda fighter, key: 75 if fighter is actor else 55), \
             patch.object(self.engine, 'ds', return_value=50), \
             patch.object(self.engine, 'submission_technique', return_value={'name': 'guillotine choke', 'choke': True}), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.random.return_value = 1
            self.engine.resolve_submission(actor, defender, 'bottom_submission', 0, state, stats)
        self.assertNotIn('von_flue_setup', state)

    def test_pure_next_tick_pool_excludes_stale_role_position_round_and_finish(self):
        for slot in ('a', 'b'):
            bottom, top, state, *_ = self.create(slot)
            state['tick'] = 4
            before, rng_before = deepcopy(state), random.getstate()
            before['fighters'] = state['fighters']  # Fighters deliberately use identity equality.
            with patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('preview consumed RNG')):
                tickets = self.engine.submission_technique_tickets(top, 'submission', state)
                # This fixture has enough readiness for three extra prepared tickets.
                self.assertEqual(tickets.count(('Von Flue choke', True)), 4)
                self.assertNotIn(('Von Flue choke', True), self.engine.submission_technique_tickets(bottom, 'bottom_submission', state))
            self.assertEqual(state, before)
            self.assertEqual(random.getstate(), rng_before)
            for changes in ({'tick': 3}, {'tick': 5}, {'round': 2}, {'position': 'guard'},
                            {'top': state['bottom'], 'bottom': state['top']}, {'submission_finish': ('a', 'b')},
                            {'instant_finish': ('a', 'b')}, {'technical_foul_stoppage': {'injured': 'a'}},
                            {'technical_outcome': {'method': 'No Contest'}}):
                stale = dict(state, **changes)
                self.assertNotIn(('Von Flue choke', True), self.engine.submission_technique_tickets(top, 'submission', stale))

    def test_actual_draw_consumes_once_even_when_other_technique_chosen(self):
        for name in ('Von Flue choke', 'kimura'):
            _, top, state, *_ = self.create()
            state['tick'] = 4
            with patch.object(self.engine, 'fight_mechanics_rng') as rng:
                rng.return_value.choice.side_effect = lambda options: next(row for row in options if row[0] == name)
                actual = self.engine.submission_technique(top, 'submission', state)
                self.assertEqual(actual['name'], name)
                rng.return_value.choice.assert_called_once()
                rng.return_value.random.assert_not_called()
            self.assertNotIn('von_flue_setup', state)
            self.assertNotIn(('Von Flue choke', True), self.engine.submission_technique_tickets(top, 'submission', state))

    def test_chain_preview_uses_current_pool_without_consuming_setup(self):
        _, top, state, *_ = self.create()
        self.engine._experimental_chain_action_weighting = True
        state['tick'] = 4
        state['move_chains'] = {state['top']: {'round': 1, 'tick': 3, 'actor_role': 'top',
                                             'branch_options': ['half_guard_von_flue']}}
        bottom = self.a
        move = MOVE_REGISTRY['half_guard_von_flue']
        weights = {'submission': 1000, 'ground_control': 1000}
        before = deepcopy(state['von_flue_setup'])
        with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves), \
             patch.object(self.engine, '_move_rarity_gate', return_value=True), \
             patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('preview RNG')):
            current = self.engine._chain_action_weights(top, bottom, state, weights, 1, 4)
            self.assertGreater(current['submission'], weights['submission'])
            state['von_flue_setup']['created_tick'] = 1
            self.assertEqual(self.engine._chain_action_weights(top, bottom, state, weights, 1, 4), weights)
        state['von_flue_setup']['created_tick'] = 3
        self.assertEqual(state['von_flue_setup'], before)

    def test_new_bottom_setup_survives_old_setup_invalidation(self):
        bottom, top, state, stats, *_ = self.create()
        state['tick'] = 4
        with patch.object(self.engine, 'skill_bundle', return_value=55), \
             patch.object(self.engine, 'ds', return_value=50), \
             patch.object(self.engine, 'ds_avg', return_value=60), \
             patch.object(self.engine, 'action_attack_value', return_value=0), \
             patch.object(self.engine, 'action_defence_value', return_value=5), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.randint.return_value = 0
            rng.return_value.choice.side_effect = lambda options: next(row for row in options if row[0] == 'guillotine choke')
            self.engine.resolve_exchange(bottom, top, 'bottom_submission', state, stats)
            rng.return_value.choice.assert_called_once()
            rng.return_value.random.assert_not_called()
        self.assertEqual(state['von_flue_setup']['created_tick'], 4)
        self.assertEqual(state['last_von_flue_setup_event']['status'], 'created')

    def test_other_action_or_position_change_invalidates(self):
        for acting_top, action in ((False, 'survive'), (True, 'ground_control')):
            bottom, top, state, stats, *_ = self.create()
            state['tick'] = 4
            with patch.object(self.engine, '_resolve_exchange_action', return_value='Control.'):
                self.engine.resolve_exchange(top if acting_top else bottom, bottom if acting_top else top, action, state, stats)
            self.assertNotIn('von_flue_setup', state)
        _, _, state, *_ = self.create()
        self.engine.set_fight_position(state, 'guard', top=state['top'], bottom=state['bottom'])
        self.assertNotIn('von_flue_setup', state)

    def test_stoppage_clears_setup_without_waiting_for_another_action(self):
        for method in ('KO', 'Submission', 'technical'):
            bottom, top, state, *_ = self.create()
            if method == 'KO':
                state['instant_finish'] = (state['top'], state['bottom'], 'KO', 'Clean strike.')
            elif method == 'Submission':
                state['submission_finish'] = (state['top'], state['bottom'], 'Tap.', 'Submission')
            with patch.object(self.engine, 'technical_foul_outcome',
                              return_value=(top, bottom, 'No Contest', 'Foul.') if method == 'technical' else None):
                self.assertIsNotNone(self.engine.check_fight_stoppage(top, bottom, state))
            self.assertNotIn('von_flue_setup', state)

    def test_horn_clears_setup_and_transient_fact(self):
        rounds = []
        def choose(actor, defender, state, round_no, tick):
            if tick == 1:
                self.assertNotIn('von_flue_setup', state)
                self.assertNotIn('last_von_flue_setup_event', state)
                rounds.append(round_no)
            self.engine.set_fight_position(state, 'half guard',
                top=self.engine.fight_state_key(defender, state), bottom=self.engine.fight_state_key(actor, state))
            return 'bottom_submission'
        def action(actor, defender, action, state, stats):
            return self.engine.resolve_submission(actor, defender, action, -5, state, stats)
        with patch.object(self.engine, 'choose_action', side_effect=choose), \
             patch.object(self.engine, '_resolve_exchange_action', side_effect=action), \
             patch.object(self.engine, 'skill_bundle', return_value=55), \
             patch.object(self.engine, 'ds', return_value=50), \
             patch.object(self.engine, 'ds_avg', return_value=60), \
             patch.object(self.engine, 'submission_technique', return_value={'name': 'guillotine choke', 'choke': True}):
            self.engine.simulate_fight(self.a, self.b, {})
        self.assertEqual(rounds, [1, 2, 3])

    def test_real_trace_creation_then_von_flue_with_shared_contest(self):
        for slot in ('a', 'b'):
            bottom, top, state, _, text, _ = self.create(slot)
            stats = {k: {'impact': 0, 'danger': 0, 'control': 0} for k in ('a', 'b')}
            before = self.engine.fight_trace_snapshot(self.a, self.b, state)
            before['stats'][slot]['sub_att'] -= 1
            created = self.engine.record_fight_trace_exchange(self.a, self.b, bottom, top,
                'bottom_submission', text, before, deepcopy(stats), state, stats)
            rendered = self.engine.render_exchange_trace_event(created)
            self.assertIn('keeps the neck wrap', rendered)
            self.assertIn('has not been cleared', rendered)
            state['tick'] = 4
            before = self.engine.fight_trace_snapshot(self.a, self.b, state)
            prior = deepcopy(stats)
            with patch.object(self.engine, 'action_attack_value', return_value=30), \
                 patch.object(self.engine, 'action_defence_value', return_value=0), \
                 patch.object(self.engine, 'fight_mechanics_rng') as rng:
                rng.return_value.randint.return_value = 0
                rng.return_value.choice.side_effect = lambda options: next(row for row in options if row[0] == 'Von Flue choke')
                rng.return_value.random.return_value = 1
                text = self.engine.resolve_exchange(top, bottom, 'submission', state, stats)
                rng.return_value.choice.assert_called_once()
                rng.return_value.random.assert_called_once()
            move = MOVE_REGISTRY['half_guard_von_flue']
            with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves):
                used = self.engine.record_fight_trace_exchange(self.a, self.b, top, bottom,
                    'submission', text, before, prior, state, stats)
            self.assertEqual(used['move_id'], 'half_guard_von_flue')
            self.assertEqual(used['von_flue_setup']['status'], 'used')
            self.assertEqual(von_flue_setup_counts([created, used]), {'created': 1, 'used': 1})
            self.assertIn('retained guillotine wrap', self.engine.render_exchange_trace_event(used))
            self.assertIn('Von Flue choke', self.engine.render_exchange_trace_event(used))


if __name__ == '__main__':
    unittest.main()
