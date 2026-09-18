"""Contested near-arm isolation is explicit, transient and honestly credited."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import MOVE_REGISTRY, MoveIndex
from analysis.generate_move_coverage_report import scarf_hold_setup_counts


class ScarfHoldSetupTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.engine._experimental_specialist_entries = True
        self.a = synthetic_fighter('Red', 80, 'Judo', 'Control', 0)
        self.b = synthetic_fighter('Blue', 80, 'Judo', 'Control', 1)
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

    def create(self, slot='a', margin=9, edge=0, position='side control', top=True):
        actor, defender = (self.a, self.b) if slot == 'a' else (self.b, self.a)
        other = 'b' if slot == 'a' else 'a'
        state = deepcopy(self.initial)
        state.update(position=position, top=slot if top else other, bottom=other if top else slot, round=1, tick=3)
        stats = {k: {'impact': 0, 'danger': 0, 'control': 0} for k in ('a', 'b')}
        before, prior = self.engine.fight_trace_snapshot(self.a, self.b, state), deepcopy(stats)
        with patch.object(self.engine, 'action_attack_value', return_value=margin), \
             patch.object(self.engine, 'action_defence_value', return_value=0), \
             patch.object(self.engine, 'ds_avg', side_effect=lambda fighter, keys, fallback: 60 + (edge if fighter is actor else 0)), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.randint.return_value = 0
            text = self.engine.resolve_exchange(actor, defender, 'ground_control', state, stats)
            rng.return_value.randint.assert_called_once()
            rng.return_value.random.assert_not_called()
            rng.return_value.choice.assert_not_called()
        return actor, defender, state, stats, before, prior, text

    def test_contest_thresholds_slots_and_only_existing_control_credit(self):
        for slot in ('a', 'b'):
            for margin, edge, expected in ((8, 0, False), (8.001, 0, True), (6, 10, False), (6.001, 10, True), (10, -10, False)):
                _, _, state, stats, before, *_ = self.create(slot, margin, edge)
                self.assertEqual('scarf_hold_setup' in state, expected)
                self.assertEqual((state['position'], state['top'], state['bottom']),
                                 (before['position'], before['top'], before['bottom']))
                self.assertEqual(state['stats'], before['stats'])
                self.assertEqual(state['danger'], self.initial['danger'])
                self.assertEqual(state['damage'], before['damage'])
                self.assertEqual(state['gas'], before['gas'])
                self.assertEqual(stats[slot], {'control': 3, 'impact': 0, 'danger': 0})
        for kwargs in ({'top': False}, {'position': 'half guard'}, {'position': 'mount'}):
            self.assertNotIn('scarf_hold_setup', self.create(**kwargs)[2])
        self.engine._experimental_specialist_entries = False
        self.assertNotIn('scarf_hold_setup', self.create()[2])

    def test_control_intent_neutral_ties_and_nonexclusive_skill_style_preferences(self):
        state = deepcopy(self.initial)
        cases = [('Boxer', 70, 70, 'ride_pin'), ('Judo', 70, 70, 'arm_isolation'),
                 ('Sambo', 70, 70, 'arm_isolation'), ('Wrestler', 70, 70, 'ride_pin'),
                 ('Freestyle Wrestler', 70, 70, 'ride_pin'), ('Catch Wrestler', 70, 70, 'ride_pin'),
                 ('Judo', 70, 75, 'ride_pin'), ('Wrestler', 75, 70, 'arm_isolation')]
        for style, arm, ride, expected in cases:
            self.a.style, self.a.secondary_style = style, ''
            with patch.object(self.engine, 'ds_avg', side_effect=lambda fighter, keys, fallback: arm if 'submission_attack' in keys else ride):
                self.assertEqual(self.engine._side_control_intent(self.a, state), expected)
        with patch.object(self.engine, 'fighter_styles', return_value=('Judo', 'Sambo')), \
             patch.object(self.engine, 'ds_avg', side_effect=lambda fighter, keys, fallback: 70 if 'submission_attack' in keys else 75):
            self.assertEqual(self.engine._side_control_intent(self.a, state), 'ride_pin')

    def test_control_intent_enabled_plan_execution_and_purity(self):
        self.a.style, self.a.secondary_style = 'Boxer', ''
        state = {'fighter_keys': {id(self.a): 'a', id(self.b): 'b'}, 'plans': {}}
        for plan, enabled, execution, arm, ride, expected in (
                ('Submission hunt', False, 1, 70, 70, 'ride_pin'),
                ('Submission hunt', True, 0, 70, 70, 'ride_pin'),
                ('Submission hunt', True, 0.5, 70, 72, 'ride_pin'),
                ('Submission hunt', True, 1, 70, 72, 'arm_isolation'),
                ('Protect a lead', True, 1, 72, 70, 'ride_pin'),
                ('Conserve energy', True, 1, 72, 70, 'ride_pin'),
                ('Conserve energy', False, 1, 72, 70, 'arm_isolation'),
                ('Balanced', True, 1, 70, 70, 'ride_pin')):
            state['plans']['a'] = {'current': plan, 'enabled': enabled, 'execution': execution}
            before, rng_before = deepcopy(state), random.getstate()
            with patch.object(self.engine, 'ds_avg', side_effect=lambda fighter, keys, fallback: arm if 'submission_attack' in keys else ride), \
                 patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('intent RNG')):
                self.assertEqual(self.engine._side_control_intent(self.a, state), expected)
            self.assertEqual(state, before)
            self.assertEqual(random.getstate(), rng_before)

    def test_ordinary_control_keeps_cradle_eligible_without_forcing_it(self):
        self.a.style, self.a.secondary_style = 'Freestyle Wrestler', ''
        actor, defender, state, stats, before, prior, text = self.create(margin=100)
        self.assertNotIn('scarf_hold_setup', state)
        move = MOVE_REGISTRY['near_side_cradle_control']
        # Isolated catalogue proves eligibility, not guaranteed ordinary frequency.
        with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves):
            event = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender,
                'ground_control', text, before, prior, state, stats)
        self.assertEqual(event['move_id'], move.move_id)
        self.assertNotIn('scarf_hold_setup', event)

    def test_ride_intent_does_not_evaluate_isolation_contest(self):
        state = deepcopy(self.initial)
        state.update(position='side control', top='a', bottom='b')
        stats = {k: {'impact': 0, 'danger': 0, 'control': 0} for k in ('a', 'b')}
        with patch.object(self.engine, '_side_control_intent', return_value='ride_pin'), \
             patch.object(self.engine, 'action_attack_value', return_value=100), \
             patch.object(self.engine, 'action_defence_value', return_value=0), \
             patch.object(self.engine, 'ds_avg', side_effect=AssertionError('unselected isolation contest')):
            self.engine._resolve_exchange_action(self.a, self.b, 'ground_control', state, stats)
        self.assertEqual(stats['a']['control'], 3)
        self.assertNotIn('scarf_hold_setup', state)

    def test_created_trace_suppresses_incompatible_signature_mastery_and_chain(self):
        for slot in ('a', 'b'):
            actor, defender, state, stats, before, prior, text = self.create(slot)
            move = MOVE_REGISTRY['reverse_scarf_hold_control']
            actor.signature_moves = [move.move_id, 'generic_ground_control']
            actor.move_mastery = {move.move_id: 100, 'generic_ground_control': 100}
            state['move_chains'] = {slot: {'round': 1, 'tick': 2, 'actor_role': 'top',
                                         'branch_options': [move.move_id], 'source_move_id': 'test_root', 'step': 1}}
            with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves):
                event = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender,
                    'ground_control', text, before, prior, state, stats)
            self.assertEqual(event['move_id'], 'generic_ground_control')
            self.assertFalse(event['signature'])
            self.assertEqual(event['move_mastery'], 0)
            self.assertEqual(event['sequence_source_id'], '')
            self.assertFalse(state['move_chains'][slot])
            self.assertEqual(event['scarf_hold_setup']['status'], 'created')
            for technical in (False, True):
                line = self.engine.render_exchange_trace_event(event, technical=technical)
                self.assertIn('isolates the near arm', line)
                self.assertIn('framing underneath', line)
                self.assertIn('armbar has not been applied', line)

    def test_pure_pool_and_chain_preview_require_current_setup(self):
        actor, defender, state, *_ = self.create()
        state['tick'] = 4
        before = deepcopy(state)
        before['fighters'] = state['fighters']
        rng_before = random.getstate()
        self.engine._experimental_chain_action_weighting = True
        state['move_chains'] = {'a': {'round': 1, 'tick': 3, 'actor_role': 'top',
                                    'branch_options': ['scarf_hold_straight_armbar']}}
        before['move_chains'] = deepcopy(state['move_chains'])
        weights = {'submission': 1000, 'ground_control': 1000}
        move = MOVE_REGISTRY['scarf_hold_straight_armbar']
        with patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('preview RNG')), \
             patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves), \
             patch.object(self.engine, '_move_rarity_gate', return_value=True):
            # Fresh 80-rated actor: one base ticket plus four bounded prepared tickets.
            self.assertEqual(self.engine.submission_technique_tickets(actor, 'submission', state).count(('scarf-hold straight armbar', False)), 5)
            self.assertGreater(self.engine._chain_action_weights(actor, defender, state, weights, 1, 4)['submission'], 1000)
            self.assertEqual(state, before)
            self.assertEqual(random.getstate(), rng_before)
            for changes in ({'tick': 3}, {'tick': 5}, {'round': 2}, {'position': 'mount'},
                            {'top': 'b', 'bottom': 'a'}, {'instant_finish': ('a', 'b')}, {'technical_outcome': {'method': 'No Contest'}}):
                stale = dict(state, **changes)
                self.assertNotIn(('scarf-hold straight armbar', False), self.engine.submission_technique_tickets(actor, 'submission', stale))

    def test_actual_draw_consumes_setup_even_when_other_hold_wins(self):
        for name in ('scarf-hold straight armbar', 'kimura'):
            actor, _, state, *_ = self.create()
            state['tick'] = 4
            with patch.object(self.engine, 'fight_mechanics_rng') as rng:
                rng.return_value.choice.side_effect = lambda options: next(row for row in options if row[0] == name)
                self.assertEqual(self.engine.submission_technique(actor, 'submission', state)['name'], name)
                rng.return_value.choice.assert_called_once()
                rng.return_value.random.assert_not_called()
            self.assertNotIn('scarf_hold_setup', state)
            self.assertNotIn(('scarf-hold straight armbar', False), self.engine.submission_technique_tickets(actor, 'submission', state))

    def test_identity_mapping_retains_style_and_minimum_skill_gates(self):
        move = MOVE_REGISTRY['judo_kesa_armbar_finisher']
        actor, defender, state, *_ = self.create()
        state['tick'] = 4
        actor.signature_moves = [move.move_id]
        with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves):
            for style, skill, eligible in (('Judo', 80, True), ('Boxer', 80, False), ('Judo', 63, False)):
                actor.style = style
                actor.secondary_style = ''
                actor.detailed_skills = dict.fromkeys(actor.detailed_skills, skill)
                payload = self.engine.select_exchange_move(actor, defender, 'submission', 'side control', '', state,
                    resolved_technique={'name': 'scarf-hold straight armbar', 'choke': False})
                self.assertEqual(payload['move_id'] == move.move_id, eligible)
            actor.style = 'Judo'
            actor.detailed_skills = dict.fromkeys(actor.detailed_skills, 80)
            self.assertTrue(self.engine.select_exchange_move(actor, defender, 'submission', 'side control', '', state,
                resolved_technique={'name': 'straight armbar', 'choke': False})['generic'])

    def test_other_action_transition_and_finish_clear_setup(self):
        for bottom_action in (False, True):
            actor, defender, state, stats, *_ = self.create()
            state['tick'] = 4
            with patch.object(self.engine, '_resolve_exchange_action', return_value='Defense.'):
                self.engine.resolve_exchange(defender if bottom_action else actor,
                    actor if bottom_action else defender, 'survive', state, stats)
            self.assertNotIn('scarf_hold_setup', state)
        actor, defender, state, *_ = self.create()
        self.engine.set_fight_position(state, 'mount', top='a', bottom='b')
        self.assertNotIn('scarf_hold_setup', state)
        actor, defender, state, *_ = self.create()
        state['instant_finish'] = ('a', 'b', 'KO', 'Strike.')
        self.engine.check_fight_stoppage(actor, defender, state)
        self.assertNotIn('scarf_hold_setup', state)

    def test_actual_trace_pair_uses_isolated_arm_then_shared_submission_contest(self):
        for slot in ('a', 'b'):
            actor, defender, state, stats, before, prior, text = self.create(slot)
            created = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender,
                'ground_control', text, before, prior, state, stats)
            state['tick'] = 4
            before = self.engine.fight_trace_snapshot(self.a, self.b, state)
            prior = deepcopy(stats)
            with patch.object(self.engine, 'action_attack_value', return_value=30), \
                 patch.object(self.engine, 'action_defence_value', return_value=0), \
                 patch.object(self.engine, 'fight_mechanics_rng') as rng:
                rng.return_value.randint.return_value = 0
                rng.return_value.choice.side_effect = lambda options: next(row for row in options if row[0] == 'scarf-hold straight armbar')
                rng.return_value.random.return_value = 1
                text = self.engine.resolve_exchange(actor, defender, 'submission', state, stats)
                rng.return_value.randint.assert_called_once()
                rng.return_value.choice.assert_called_once()
                rng.return_value.random.assert_called_once()
            move = MOVE_REGISTRY['scarf_hold_straight_armbar']
            with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves):
                used = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender,
                    'submission', text, before, prior, state, stats)
            self.assertEqual(used['move_id'], move.move_id)
            self.assertEqual(scarf_hold_setup_counts([created, used]), {'created': 1, 'used': 1})
            self.assertIn('isolated near arm', self.engine.render_exchange_trace_event(used))
            self.assertIn('scarf-hold straight armbar', self.engine.render_exchange_trace_event(used))

    def test_referee_standup_cancels_same_exchange_scarf_setup(self):
        for slot in ('a', 'b'):
            actor, defender, state, stats, before, prior, text = self.create(slot)
            self.assertIn('scarf_hold_setup', state)
            actor.signature_moves = ['reverse_scarf_hold_control']
            actor.move_mastery = {'reverse_scarf_hold_control': 100}
            state['move_chains'] = {slot: {'round': 1, 'tick': 2, 'actor_role': 'top',
                                         'branch_options': ['reverse_scarf_hold_control'],
                                         'source_move_id': 'test_root', 'step': 1}}
            # Match the live loop: resolve first, then referee inactivity,
            # then record/render the exchange. Isolation must not bypass the
            # existing static-control stand-up threshold.
            state['ground_inactivity'] = 3
            state['ground_warning'] = True
            with patch.object(self.engine, 'referee_profile', return_value={'standup_threshold': 4}), \
                 patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('referee RNG')):
                note = self.engine.update_ground_inactivity(state, 'ground_control')
            self.assertEqual((state['position'], state['top'], state['bottom']), ('range', None, None))
            self.assertIsNone(state['clinch_controller'])
            self.assertEqual(state['ground_inactivity'], 0)
            self.assertFalse(state['ground_warning'])
            self.assertEqual(stats[slot], {'control': 3, 'impact': 0, 'danger': 0})
            self.assertEqual(state['last_referee_ground_action']['type'], 'standup')
            self.assertTrue(note)
            with self.subTest(slot=slot, boundary='setup lifecycle'):
                self.assertFalse('scarf_hold_setup' in state, 'Stand-up retained a live scarf setup')
                self.assertEqual(state.get('last_scarf_hold_setup_event', {}).get('status'), 'cancelled')

            event = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender,
                'ground_control', text, before, prior, state, stats)
            with self.subTest(slot=slot, boundary='trace and identity'):
                self.assertEqual(event['position_after'], 'range')
                self.assertIsNone(event['top_after'])
                self.assertIsNone(event['bottom_after'])
                self.assertEqual(event.get('scarf_hold_setup', {}).get('status'), 'cancelled')
                self.assertEqual(event['move_id'], 'generic_ground_control')
                self.assertFalse(event['signature'])
                self.assertEqual(event['move_mastery'], 0)
                self.assertEqual(event['sequence_source_id'], '')
                self.assertFalse(state['move_chains'][slot])
            with self.subTest(slot=slot, boundary='coverage'):
                self.assertEqual(scarf_hold_setup_counts([event]), {'cancelled': 1})
            for technical in (False, True):
                with self.subTest(slot=slot, boundary='rendering', technical=technical):
                    rendered = self.engine.render_exchange_trace_event(event, technical=technical)
                    self.assertIn(note, rendered)
                    self.assertNotIn('framing underneath', rendered)
                    self.assertNotIn('isolates the near arm', rendered)
            state['tick'] = 4
            with self.subTest(slot=slot, boundary='no next-exchange opportunity'):
                self.assertNotIn(('scarf-hold straight armbar', False),
                                 self.engine.submission_technique_tickets(actor, 'submission', state))

    def test_horn_and_new_setup_replacement_lifecycle(self):
        rounds = []
        def choose(actor, defender, state, round_no, tick):
            if tick == 1:
                self.assertNotIn('scarf_hold_setup', state)
                self.assertNotIn('last_scarf_hold_setup_event', state)
                rounds.append(round_no)
            if state['position'] == 'range':
                self.engine.set_fight_position(state, 'guard',
                    top=self.engine.fight_state_key(actor, state), bottom=self.engine.fight_state_key(defender, state))
                self.engine.set_fight_position(state, 'half guard',
                    top=self.engine.fight_state_key(actor, state), bottom=self.engine.fight_state_key(defender, state))
            self.engine.set_fight_position(state, 'side control',
                top=self.engine.fight_state_key(actor, state), bottom=self.engine.fight_state_key(defender, state))
            return 'ground_control'
        with patch.object(self.engine, 'choose_action', side_effect=choose), \
             patch.object(self.engine, 'action_attack_value', return_value=100), \
             patch.object(self.engine, 'action_defence_value', return_value=0):
            self.engine.simulate_fight(self.a, self.b, {})
        self.assertEqual(rounds, [1, 2, 3])
        actor, defender, state, stats, *_ = self.create()
        state['tick'] = 4
        with patch.object(self.engine, 'action_attack_value', return_value=100), \
             patch.object(self.engine, 'action_defence_value', return_value=0):
            self.engine.resolve_exchange(actor, defender, 'ground_control', state, stats)
        self.assertEqual(state['scarf_hold_setup']['created_tick'], 4)


if __name__ == '__main__':
    unittest.main()
