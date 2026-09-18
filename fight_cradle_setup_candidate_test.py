"""Real resolver and lifecycle boundaries for the audit-only cradle trial."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from analysis.cradle_setup_candidate import cradle_setup_trial, valid_cradle_setup, validate_cradle_setups, HOLD, KEY, FACT, MOVE_ID
from fight_engine_audit import FightAuditHarness
import fight_scarf_hold_setup_regression_test as scarf_fixture
from fight_moves.submission_identity import COMPATIBLE_SUBMISSION_IDS


class CradleTests(unittest.TestCase):
    setUp = scarf_fixture.ScarfHoldSetupTests.setUp
    create = scarf_fixture.ScarfHoldSetupTests.create

    def prepared(self, margin=9, edge=0, slot='a'):
        self.a.style = self.b.style = 'Catch Wrestler'
        self.a.secondary_style = self.b.secondary_style = ''
        return self.create(slot=slot, margin=margin, edge=edge)

    def test_real_control_contest_slots_threshold_and_credit(self):
        with cradle_setup_trial(True):
            for slot in ('a', 'b'):
                for margin, edge, success in ((8, 0, False), (8.01, 0, True), (6, 10, False), (6.01, 10, True)):
                    actor, defender, state, stats, before, prior, text = self.prepared(margin, edge, slot)
                    self.assertEqual(KEY in state, success)
                    self.assertEqual(stats[slot], dict(control=3, impact=0, danger=0))
                    self.assertEqual(state['stats'], before['stats'])
                    self.assertEqual(state['damage'], before['damage'])
                    event = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender, 'ground_control', text, before, prior, state, stats)
                    self.assertEqual(event['move_id'], 'generic_ground_control')
                    self.assertEqual(event[KEY]['status'], 'created' if success else 'denied')

    def test_one_ticket_after_adaptation_and_single_draw_consumption(self):
        with cradle_setup_trial(True):
            actor, _, state, *_ = self.prepared()
            state['tick'] += 1
            self.assertTrue(valid_cradle_setup(self.engine, actor, 'submission', state))
            tickets = self.engine.submission_technique_tickets(actor, 'submission', state)
            self.assertEqual(tickets.count(HOLD), 1)
            for chosen, expected in ((HOLD, 'used'), (tickets[0], 'consumed')):
                trial = deepcopy(state)
                with patch.object(self.engine, 'fight_mechanics_rng') as rng:
                    rng.return_value.choice.return_value = chosen
                    result = self.engine.submission_technique(actor, 'submission', trial)
                    rng.return_value.choice.assert_called_once()
                    rng.return_value.randint.assert_not_called()
                self.assertEqual(result, dict(name=chosen[0], choke=chosen[1]))
                self.assertNotIn(KEY, trial)
                self.assertEqual(trial[FACT]['status'], expected)
                self.assertNotIn(HOLD, self.engine.submission_technique_tickets(actor, 'submission', trial))

    def test_expiry_other_actor_action_tick_round_position_and_finish(self):
        with cradle_setup_trial(True):
            actor, defender, state, stats, *_ = self.prepared()
            state['tick'] += 1
            for changes in ({'tick': 6}, {'round': 2}, {'position': 'mount'}, {'top': 'b', 'bottom': 'a'}, {'submission_finish': True}):
                altered = dict(state, **changes)
                self.assertFalse(valid_cradle_setup(self.engine, actor, 'submission', altered))
                self.assertNotIn(HOLD, self.engine.submission_technique_tickets(actor, 'submission', altered))
            self.assertFalse(valid_cradle_setup(self.engine, defender, 'submission', state))
            self.assertFalse(valid_cradle_setup(self.engine, actor, 'ground_control', state))
            self.engine.resolve_exchange(actor, defender, 'survive', state, stats)
            self.assertNotIn(KEY, state)
            self.assertEqual(state[FACT]['status'], 'cancelled')
            _, _, state, *_ = self.prepared()
            self.engine.set_fight_position(state, 'side control', top='a', bottom='b')
            self.assertNotIn(KEY, state)
            _, _, state, *_ = self.prepared()
            self.engine.recover_between_rounds(self.a, self.b, state)
            self.assertNotIn(KEY, state)

    def test_default_off_style_and_nested_exception_restoration(self):
        original = FightAuditHarness.resolve_exchange
        mapping = dict(COMPATIBLE_SUBMISSION_IDS)
        with cradle_setup_trial(False):
            self.assertNotIn(KEY, self.prepared()[2])
        rng = random.getstate()
        with self.assertRaisesRegex(RuntimeError, 'test'):
            with cradle_setup_trial(True):
                patched = FightAuditHarness.resolve_exchange
                with cradle_setup_trial(True):
                    self.assertIs(FightAuditHarness.resolve_exchange, patched)
                with self.assertRaises(ValueError):
                    with cradle_setup_trial(False):
                        pass
                self.a.style = self.b.style = 'Judo'
                self.assertNotIn(KEY, self.create()[2])
                random.random()
                raise RuntimeError('test')
        self.assertIs(FightAuditHarness.resolve_exchange, original)
        self.assertEqual(COMPATIBLE_SUBMISSION_IDS, mapping)
        self.assertEqual(random.getstate(), rng)

    def test_identity_requires_current_draw_proof(self):
        with cradle_setup_trial(True):
            actor, defender, state, *_ = self.prepared()
            state['tick'] += 1
            rows = self.engine._move_candidates(actor, 'submission', 'side control', '', state)[0]
            self.assertNotIn(MOVE_ID, [row.move_id for row in rows])
            with patch.object(self.engine, 'fight_mechanics_rng') as rng:
                rng.return_value.choice.return_value = HOLD
                self.engine.submission_technique(actor, 'submission', state)
            rows = self.engine._move_candidates(actor, 'submission', 'side control', '', state)[0]
            self.assertIn(MOVE_ID, [row.move_id for row in rows])
            state['tick'] += 1
            rows = self.engine._move_candidates(actor, 'submission', 'side control', '', state)[0]
            self.assertNotIn(MOVE_ID, [row.move_id for row in rows])

    def test_real_submission_resolver_carries_draw_fact(self):
        with cradle_setup_trial(True):
            actor, defender, state, stats, before, prior, text = self.prepared()
            root = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender,
                'ground_control', text, before, prior, state, stats)
            state['tick'] += 1
            before = self.engine.fight_trace_snapshot(self.a, self.b, state)
            prior = deepcopy(stats)
            mechanics = self.engine.fight_mechanics_rng()
            with patch.object(mechanics, 'choice', return_value=HOLD), \
                 patch.object(self.engine, 'action_attack_value', return_value=-100), \
                 patch.object(self.engine, 'action_defence_value', return_value=100):
                text = self.engine.resolve_exchange(actor, defender, 'submission', state, stats)
            self.assertEqual(state['stats']['a']['sub_att'], before['stats']['a']['sub_att'] + 1)
            self.assertEqual(state[FACT]['status'], 'used')
            self.assertNotIn(KEY, state)
            event = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender,
                'submission', text, before, prior, state, stats)
            self.assertEqual(event[KEY]['technique'], dict(name=HOLD[0], choke=False))
            counts = validate_cradle_setups([root, event])
            self.assertEqual((counts['roots'], counts['used'], counts['invalid']), (1, 1, 0))
            for corrupt in ('missing', 'margin', 'tick', 'attempt', 'signature'):
                events = deepcopy([root, event])
                if corrupt == 'missing':
                    events[1].pop(KEY)
                elif corrupt == 'margin':
                    events[0][KEY]['raw_margin'] = float('nan')
                elif corrupt == 'tick':
                    events[1]['tick'] += 1
                elif corrupt == 'attempt':
                    events[1]['sub_att_delta'] = 0
                else:
                    events[0]['signature'] = True
                self.assertGreater(validate_cradle_setups(events)['invalid'], 0)

    def test_hold_skill_gate_and_referee_reset(self):
        with cradle_setup_trial(True):
            actor, defender, state, stats, before, prior, text = self.prepared()
            state['tick'] += 1
            for skill, expected in ((63.99, False), (64, True)):
                for key in ('submission_attack', 'ride_control', 'strength'):
                    actor.detailed_skills[key] = skill
                self.assertEqual(HOLD in self.engine.submission_technique_tickets(actor, 'submission', state), expected)
            actor.style = 'Judo'
            self.assertNotIn(HOLD, self.engine.submission_technique_tickets(actor, 'submission', state))
            actor, defender, state, stats, before, prior, text = self.prepared()
            state['ground_warning'] = True
            state['ground_inactivity'] = 100
            state['last_move_payload'] = self.engine.select_exchange_move(actor, defender, 'ground_control', 'side control', '', state)
            self.engine.update_ground_inactivity(state, 'ground_control')
            self.assertNotIn(KEY, state)
            self.assertEqual(state[FACT]['reason'], 'referee_standup')
            self.assertEqual(state['last_move_payload']['move_id'], 'generic_ground_control')
            event = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender,
                'ground_control', text, before, prior, state, stats)
            self.assertEqual(validate_cradle_setups([event])['invalid'], 0)

    def test_disabled_engine_complete_bout_parity(self):
        self.engine._experimental_specialist_entries = False
        random.seed(7483)
        expected = self.engine.simulate_fight(deepcopy(self.a), deepcopy(self.b), {})
        terminal = random.getstate()
        random.seed(7483)
        with cradle_setup_trial(True):
            actual = self.engine.simulate_fight(deepcopy(self.a), deepcopy(self.b), {})
            self.assertEqual(random.getstate(), terminal)
        self.assertEqual([vars(x) if hasattr(x, '__dict__') else x for x in actual],
                         [vars(x) if hasattr(x, '__dict__') else x for x in expected])


if __name__ == '__main__':
    unittest.main()
