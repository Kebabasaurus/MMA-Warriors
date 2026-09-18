"""Prepared holds receive bounded preferences, never guaranteed actions/results."""
from copy import deepcopy
from dataclasses import replace
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import MOVE_REGISTRY, MoveIndex
from fight_moves.submission_pool import submission_ticket_family


class PreparedSubmissionTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.engine._experimental_specialist_entries = True
        self.a = synthetic_fighter('Red', 80, 'Judo', 'Control', 0)
        self.b = synthetic_fighter('Blue', 80, 'Wrestler', 'Control', 1)
        self.a.detailed_skills = dict.fromkeys(self.a.detailed_skills, 80)
        self.addCleanup(random.setstate, random.getstate())

    def state(self, kind='scarf', slot='a'):
        other = 'b' if slot == 'a' else 'a'
        key, position = ('scarf_hold_setup', 'side control') if kind == 'scarf' else ('von_flue_setup', 'half guard')
        return {'fighter_keys': {id(self.a): slot, id(self.b): other}, 'position': position,
                'top': slot, 'bottom': other, 'round': 1, 'tick': 4,
                'gas': {slot: 80, other: 80}, 'hurt': {slot: 0, other: 0},
                key: {'top': slot, 'bottom': other, 'position': position, 'round': 1, 'created_tick': 3}}

    def test_prepared_opportunity_without_chain_requires_immediate_valid_context(self):
        for kind in ('scarf', 'von'):
            for slot in ('a', 'b'):
                state = self.state(kind, slot)
                before, rng = deepcopy(state), random.getstate()
                opportunity = self.engine._prepared_submission_opportunity(self.a, 'submission', state)
                self.assertEqual(opportunity['readiness'], 1)
                self.assertEqual(state, before)
                self.assertEqual(random.getstate(), rng)
                for changes in ({'tick': 3}, {'tick': 5}, {'round': 2}, {'position': 'mount'},
                                {'top': state['bottom'], 'bottom': state['top']}, {'instant_finish': ('a', 'b')}):
                    self.assertIsNone(self.engine._prepared_submission_opportunity(self.a, 'submission', dict(state, **changes)))
                self.assertIsNone(self.engine._prepared_submission_opportunity(self.a, 'ground_control', state))

    def test_readiness_gas_and_enabled_plan_execution_are_bounded(self):
        state = self.state()
        with patch.object(self.engine, 'ds_avg', return_value=60):
            for enabled, execution, plan, expected in (
                    (False, 1, 'Submission hunt', .5), (True, 0, 'Submission hunt', .5),
                    (True, 1, 'Submission hunt', .575), (True, .5, 'Submission hunt', .5375),
                    (True, 1, 'Conserve energy', .3), (True, 1.1, 'Protect a lead', .28)):
                state['plans'] = {'a': {'enabled': enabled, 'execution': execution, 'current': plan}}
                self.assertAlmostEqual(self.engine._prepared_submission_opportunity(self.a, 'submission', state)['readiness'], expected)
            state.pop('plans')
            state['gas']['a'] = 30
            self.assertAlmostEqual(self.engine._prepared_submission_opportunity(self.a, 'submission', state)['readiness'], .25)

    def test_candidate_skill_style_rarity_and_current_counter_gates(self):
        state = self.state()
        ordinary = MOVE_REGISTRY['scarf_hold_straight_armbar']
        for move, rarity in ((replace(ordinary, minimum_skill=95), True),
                             (replace(ordinary, tags=ordinary.tags + ('counter',)), True), (ordinary, False)):
            with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves), \
                 patch.object(self.engine, '_move_rarity_gate', return_value=rarity):
                self.assertIsNone(self.engine._prepared_submission_opportunity(self.a, 'submission', state))
        finisher = MOVE_REGISTRY['judo_kesa_armbar_finisher']
        self.a.style, self.a.secondary_style = 'Boxer', ''
        with patch('fight_engine.legal_moves', side_effect=MoveIndex((finisher,)).legal_moves):
            self.assertIsNone(self.engine._prepared_submission_opportunity(self.a, 'submission', state))
        self.a.style = 'Judo'
        state['last_exchange_counter'] = True  # Stale prior actor evidence must not select a counter-only definition.
        counter = replace(ordinary, tags=ordinary.tags + ('counter',))
        with patch('fight_engine.legal_moves', side_effect=MoveIndex((counter,)).legal_moves):
            self.assertIsNone(self.engine._prepared_submission_opportunity(self.a, 'submission', state))
            state['counter_window'] = {'fighter': 'a'}
            self.assertIsNotNone(self.engine._prepared_submission_opportunity(self.a, 'submission', state))

    def test_technique_preference_preserves_length_order_firsts_and_each_ticket_family(self):
        for kind in ('scarf', 'von'):
            state = self.state(kind)
            with patch.object(self.engine, '_prepared_submission_opportunity', return_value=None):
                before = self.engine.submission_technique_tickets(self.a, 'submission', state)
            after = self.engine.submission_technique_tickets(self.a, 'submission', state)
            self.assertEqual(len(before), len(after))
            self.assertEqual(list(map(submission_ticket_family, before)), list(map(submission_ticket_family, after)))
            seen = set()
            for index, ticket in enumerate(before):
                if ticket not in seen:
                    self.assertEqual(after[index], ticket)
                    seen.add(ticket)
            prepared = ('scarf-hold straight armbar', False) if kind == 'scarf' else ('Von Flue choke', True)
            self.assertGreater(after.count(prepared), before.count(prepared))
            self.assertLessEqual(after.count(prepared) - before.count(prepared), 4)
            self.assertTrue(set(before) <= set(after))

    def test_action_preference_without_chain_preserves_budget_and_all_alternatives(self):
        state, weights = self.state(), {'submission': 100, 'ground_control': 100, 'advance_position': 100}
        self.engine._experimental_chain_action_weighting = False
        result = self.engine._chain_action_weights(self.a, self.b, state, weights, 1, 4)
        self.assertGreater(result['submission'], 100)
        self.assertEqual(sum(result.values()), 300)
        self.assertEqual(list(result), list(weights))
        self.assertTrue(all(value >= 1 for value in result.values()))
        self.engine._experimental_specialist_entries = False
        self.assertIs(self.engine._chain_action_weights(self.a, self.b, state, weights, 1, 4), weights)

    def test_existing_draw_consumes_setup_and_survival_still_wins(self):
        state = self.state()
        with patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.choice.side_effect = lambda options: next(row for row in options if row[0] == 'kimura')
            self.assertEqual(self.engine.submission_technique(self.a, 'submission', state)['name'], 'kimura')
            rng.return_value.choice.assert_called_once()
            rng.return_value.random.assert_not_called()
        self.assertNotIn('scarf_hold_setup', state)
        state = self.state()
        state['gas']['a'] = 0
        with patch.object(self.engine, '_prepared_submission_opportunity', side_effect=AssertionError('survival bypassed')), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.random.return_value = 0
            self.assertEqual(self.engine.choose_action(self.a, self.b, state, 1, 4), 'survive')

    def test_chain_and_prepared_preference_use_maximum_not_stacking(self):
        state, weights = self.state(), {'submission': 100, 'ground_control': 100, 'advance_position': 100}
        for chain_bonus, readiness in ((1.5, 1), (.25, 1), (1, 1)):
            with patch.object(self.engine, '_chain_action_bonuses', return_value={'submission': chain_bonus}), \
                 patch.object(self.engine, '_prepared_submission_opportunity', return_value={'readiness': readiness}):
                combined = self.engine._chain_action_weights(self.a, self.b, state, weights, 1, 4)
            with patch.object(self.engine, '_chain_action_bonuses', return_value={'submission': max(chain_bonus, readiness)}), \
                 patch.object(self.engine, '_prepared_submission_opportunity', return_value=None):
                strongest_alone = self.engine._chain_action_weights(self.a, self.b, state, weights, 1, 4)
            self.assertEqual(combined, strongest_alone)

    def test_zero_readiness_and_missing_duplicate_budget_do_not_manufacture_tickets(self):
        state = self.state()
        tickets = [('scarf-hold straight armbar', False), ('armbar', False), ('guillotine choke', True)]
        self.assertEqual(self.engine._prepared_submission_tickets(self.a, 'submission', state, tickets), tickets)
        with patch.object(self.engine, 'ds_avg', return_value=40):
            self.assertEqual(self.engine._prepared_submission_tickets(self.a, 'submission', state, tickets * 2), tickets * 2)

    def test_real_setup_weighted_draw_and_resolved_trace(self):
        captured = []
        class Ready(Exception):
            pass
        def capture(*args):
            captured.append(args[2])
            raise Ready()
        with patch.object(self.engine, 'choose_action', side_effect=capture):
            with self.assertRaises(Ready):
                self.engine.simulate_fight(self.a, self.b, {})
        state = captured[0]
        state.update(position='side control', top='a', bottom='b', tick=3, round=1)
        stats = {k: {'impact': 0, 'control': 0, 'danger': 0} for k in ('a', 'b')}
        before = self.engine.fight_trace_snapshot(self.a, self.b, state)
        prior = deepcopy(stats)
        with patch.object(self.engine, 'action_attack_value', return_value=100), \
             patch.object(self.engine, 'action_defence_value', return_value=0):
            text = self.engine.resolve_exchange(self.a, self.b, 'ground_control', state, stats)
        created = self.engine.record_fight_trace_exchange(self.a, self.b, self.a, self.b,
            'ground_control', text, before, prior, state, stats)
        state['tick'] = 4
        before, prior = self.engine.fight_trace_snapshot(self.a, self.b, state), deepcopy(stats)
        with patch.object(self.engine, 'action_attack_value', return_value=30), \
             patch.object(self.engine, 'action_defence_value', return_value=0), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.randint.return_value = 0
            rng.return_value.random.return_value = 1
            rng.return_value.choice.side_effect = lambda options: next(row for row in options if row[0] == 'scarf-hold straight armbar')
            text = self.engine.resolve_exchange(self.a, self.b, 'submission', state, stats)
            selected_pool = rng.return_value.choice.call_args.args[0]
            self.assertEqual(selected_pool.count(('scarf-hold straight armbar', False)), 5)
            self.assertEqual(len(selected_pool), 17)
            rng.return_value.choice.assert_called_once()
            rng.return_value.randint.assert_called_once()
            rng.return_value.random.assert_called_once()
        move = MOVE_REGISTRY['scarf_hold_straight_armbar']
        with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves):
            used = self.engine.record_fight_trace_exchange(self.a, self.b, self.a, self.b,
                'submission', text, before, prior, state, stats)
        self.assertEqual(used['move_id'], move.move_id)
        self.assertEqual(created['scarf_hold_setup']['status'], 'created')
        self.assertEqual(used['scarf_hold_setup']['status'], 'used')
        self.assertNotIn('scarf_hold_setup', state)


if __name__ == '__main__':
    unittest.main()
