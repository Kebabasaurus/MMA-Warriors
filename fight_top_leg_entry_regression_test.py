"""Top-guard ankle isolation is a two-beat experimental entry, not a finish."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import MOVE_REGISTRY, MoveIndex
from analysis.generate_move_coverage_report import top_leg_entry_observation


class TopLegEntryTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.engine._experimental_specialist_entries = True
        self.a = synthetic_fighter('Red', 75, 'BJJ', 'Control', 0)
        self.b = synthetic_fighter('Blue', 75, 'Wrestler', 'Control', 1)
        for fighter in (self.a, self.b):
            fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 75)
        self.addCleanup(random.setstate, random.getstate())
        class Ready(Exception):
            pass
        captured = []
        def capture(actor, defender, state, round_no, tick):
            captured.append(state)
            raise Ready()
        with patch.object(self.engine, 'choose_action', side_effect=capture):
            with self.assertRaises(Ready):
                self.engine.simulate_fight(self.a, self.b, {})
        self.initial = captured[0]

    def resolve(self, slot='a', margin=9, edge=0, position='guard', top=True,
                action='submission', technique='straight ankle lock', live=False):
        actor, defender = (self.a, self.b) if slot == 'a' else (self.b, self.a)
        other = 'b' if slot == 'a' else 'a'
        state = deepcopy(self.initial)
        state.update(position=position, top=slot if top else other, bottom=other if top else slot)
        stats = {k: {'impact': 0, 'danger': 0, 'control': 0} for k in ('a', 'b')}
        before = self.engine.fight_trace_snapshot(self.a, self.b, state)
        prior = deepcopy(stats)
        with patch.object(self.engine, 'ds_avg', side_effect=lambda fighter, keys, fallback: 75 + (edge if fighter is actor else 0)), \
             patch.object(self.engine, 'action_attack_value', return_value=margin), \
             patch.object(self.engine, 'action_defence_value', return_value=0), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.randint.return_value = 0
            rng.return_value.random.return_value = 1
            rng.return_value.choice.side_effect = lambda options: next(row for row in options if row[0] == technique)
            if live:
                text = self.engine.resolve_exchange(actor, defender, action, state, stats)
                rng.return_value.choice.assert_called_once()
                rng.return_value.randint.assert_called_once()
            else:
                with patch.object(self.engine, 'submission_technique', return_value={'name': technique, 'choke': False}):
                    text = self.engine.resolve_submission(actor, defender, action, margin, state, stats)
            draws = rng.return_value.random.call_count
        return actor, defender, state, stats, before, prior, text, draws

    def test_entry_threshold_and_skill_edge_both_slots_without_finish_credit(self):
        for slot in ('a', 'b'):
            for margin, edge, success in ((8, 0, False), (8.001, 0, True), (6, 10, False), (6.001, 10, True), (10, -10, False)):
                _, _, state, stats, before, _, _, draws = self.resolve(slot, margin, edge)
                self.assertEqual(state['last_top_leg_entry']['success'], success)
                self.assertEqual(state['position'], 'leg entanglement' if success else 'guard')
                self.assertEqual((state['top'], state['bottom']), (slot, 'b' if slot == 'a' else 'a'))
                self.assertEqual(state['stats'][slot]['sub_att'] - before['stats'][slot]['sub_att'], 1)
                self.assertEqual(state['stats'][slot]['td'], before['stats'][slot]['td'])
                self.assertEqual(state['danger'], self.initial['danger'])
                self.assertEqual(state['gas'], before['gas'])
                self.assertEqual(stats, {k: {'impact': 0, 'danger': 0, 'control': 0} for k in ('a', 'b')})
                self.assertNotIn('submission_finish', state)
                self.assertEqual(draws, 0)

    def test_pool_one_ticket_only_top_guard_above_62(self):
        for slot in ('a', 'b'):
            actor = self.a if slot == 'a' else self.b
            other = 'b' if slot == 'a' else 'a'
            for skill in (62, 63):
                actor.detailed_skills['leg_locks'] = skill
                for position in ('guard', 'half guard'):
                    state = dict(self.initial, position=position, top=slot, bottom=other)
                    pool = self.engine.submission_technique_tickets(actor, 'submission', state)
                    self.assertEqual(pool.count(('straight ankle lock', False)), int(skill > 62 and position == 'guard'))

    def test_unrelated_submission_routes_and_default_off_do_not_enter(self):
        for kwargs in ({'position': 'half guard'}, {'top': False, 'action': 'bottom_submission'},
                       {'technique': 'heel hook'}, {'technique': 'armbar'}):
            result = self.resolve(margin=-1, **kwargs)
            self.assertNotIn('last_top_leg_entry', result[2])
        self.engine._experimental_specialist_entries = False
        self.assertNotIn('last_top_leg_entry', self.resolve()[2])

    def test_real_trace_truthful_identity_and_success_denial_rendering(self):
        move = MOVE_REGISTRY['guard_top_ankle_lock']
        for slot in ('a', 'b'):
            for margin in (8, 9):
                actor, defender, state, stats, before, prior, text, draws = self.resolve(slot, margin, live=True)
                with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves):
                    event = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender,
                        'submission', text, before, prior, state, stats)
                self.assertEqual(event['move_id'], move.move_id)
                self.assertEqual(event['outcome'], 'position_change' if margin > 8 else 'defended')
                self.assertEqual(top_leg_entry_observation(event), 'entered' if margin > 8 else 'denied')
                self.assertEqual(draws, 0)
                for technical in (False, True):
                    rendered = self.engine.render_exchange_trace_event(event, technical=technical)
                    self.assertIn('straight ankle lock', rendered)
                    self.assertIn('finishing grip is not yet set' if margin > 8 else 'remains on top in guard', rendered)
                    self.assertNotIn('sweep', rendered)

    def test_existing_next_action_menus_and_entry_fact_cleared_next_exchange(self):
        for slot in ('a', 'b'):
            actor, defender, state, stats, *_ = self.resolve(slot, live=True)
            with patch.object(self.engine, 'weighted_choice', side_effect=lambda weights: set(weights)):
                self.assertEqual(self.engine.choose_action(actor, defender, state, 1, 2),
                                 {'leg_attack', 'leg_control', 'disengage_leg'})
                self.assertEqual(self.engine.choose_action(defender, actor, state, 1, 2),
                                 {'leg_escape', 'counter_leg_lock'})
            with patch.object(self.engine, '_resolve_exchange_action', return_value='Defense.'):
                self.engine.resolve_exchange(defender, actor, 'survive', state, stats)
            self.assertNotIn('last_top_leg_entry', state)

    def test_round_horn_resets_real_entry_position_and_fact(self):
        rounds = []
        def choose(actor, defender, state, round_no, tick):
            if tick == 1:
                self.assertEqual((state['position'], state['top'], state['bottom']), ('range', None, None))
                self.assertNotIn('last_top_leg_entry', state)
                rounds.append(round_no)
            self.engine.set_fight_position(state, 'guard',
                top=self.engine.fight_state_key(actor, state), bottom=self.engine.fight_state_key(defender, state))
            return 'submission'
        def entry(actor, defender, action, state, stats):
            # Arrange a legal top-guard contest each beat; the actual resolver
            # enters and the actual round loop must clear it at the next horn.
            return self.engine.resolve_submission(actor, defender, action, 100, state, stats)
        with patch.object(self.engine, 'choose_action', side_effect=choose), \
             patch.object(self.engine, '_resolve_exchange_action', side_effect=entry), \
             patch.object(self.engine, 'submission_technique', return_value={'name': 'straight ankle lock', 'choke': False}):
            self.engine.simulate_fight(self.a, self.b, {})
        self.assertEqual(rounds, [1, 2, 3])


if __name__ == '__main__':
    unittest.main()
