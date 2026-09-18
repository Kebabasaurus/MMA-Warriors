from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from analysis.fight_candidate_context import candidate_context
from analysis.submission_chain_candidate import submission_chain_trial, validate_hold_transitions, PENDING
from analysis.generate_variety_opportunity_report import TerminalRngHarness
from fight_engine_audit import FightAuditHarness, synthetic_fighter, run_audited_fight


class SubmissionChainTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(random.setstate, random.getstate())
        self.a = synthetic_fighter('Chain A', 90, 'BJJ', 'Control', 0)
        self.b = synthetic_fighter('Chain B', 90, 'Wrestler', 'Control', 1)
        self.engine = FightAuditHarness()
        captured = []
        class Ready(Exception):
            pass
        def capture(actor, defender, state, round_no, tick):
            captured.append(deepcopy(state))
            raise Ready()
        with patch.object(self.engine, 'choose_action', side_effect=capture):
            with self.assertRaises(Ready):
                self.engine.simulate_fight(self.a, self.b, {})
        self.state = captured[0]
        self.state.update(position='mount', top='a', bottom='b', counter_window={})
        self.stats = {key: dict(impact=0, danger=0, control=0) for key in ('a', 'b')}

    def exchange(self, hold, action='submission', margin=25):
        state = self.state
        state['last_move_payload'] = None
        before = self.engine.fight_trace_snapshot(self.a, self.b, state)
        prior = deepcopy(self.stats)
        with patch.object(self.engine, 'action_attack_value', return_value=margin), \
             patch.object(self.engine, 'action_defence_value', return_value=0), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.randint.return_value = 0
            rng.return_value.random.return_value = 1
            rng.return_value.choice.side_effect = lambda tickets: next(t for t in tickets if t[0].casefold() == hold)
            text = self.engine.resolve_exchange(self.a, self.b, action, state, self.stats)
            self.assertEqual(rng.return_value.choice.call_count, 1)
        return self.engine.record_fight_trace_exchange(self.a, self.b, self.a, self.b, action,
                                                      text, before, prior, state, self.stats)

    def test_real_top_and_guard_hold_transitions(self):
        with candidate_context(entries=True, chains=True, draft_content=True), submission_chain_trial(True):
            for action, position, first, second, identity in (
                    ('submission', 'mount', 'americana', 'straight armbar', 'top_submission_chain'),
                    ('bottom_submission', 'guard', 'triangle choke', 'armbar', 'guard_submission_chain')):
                self.state.update(position=position, top='a' if action=='submission' else 'b',
                                  bottom='b' if action=='submission' else 'a', tick=1)
                self.state.pop(PENDING, None)
                self.a.signature_moves = [identity]
                self.a.move_mastery = {identity: 100}
                root = self.exchange(first, action)
                self.assertNotEqual(root['move_id'], identity)
                self.state['tick'] = 2
                follow = self.exchange(second, action)
                self.assertEqual(follow['move_id'], identity)
                self.assertEqual(follow['move']['name'], f'{first} to {second}')
                self.assertEqual(validate_hold_transitions([root, follow]), dict(roots=2, transitions=1, named=1, invalid=0))
                self.assertGreater(validate_hold_transitions([follow])['invalid'], 0)
                broken = deepcopy(follow)
                broken.pop('hold_transition')
                self.assertGreater(validate_hold_transitions([root, broken])['invalid'], 0)
                for field, value in (('action', 'ground_control'), ('position_after', 'range'),
                                     ('top_after', 'b' if follow['top_after'] == 'a' else 'a'),
                                     ('top_before', None), ('bottom_before', None)):
                    broken = deepcopy(follow)
                    broken[field] = value
                    self.assertGreater(validate_hold_transitions([root, broken])['invalid'], 0)
                broken = deepcopy(follow)
                broken['submission_technique']['transition']['root_tick'] = 0
                self.assertGreater(validate_hold_transitions([root, broken])['invalid'], 0)
                from fight_moves.submission_transition import transition_identity
                for key in ('tick', 'root_tick', 'round'):
                    for value in (True, 0, -1):
                        corrupt = deepcopy(follow['submission_technique'])
                        corrupt['transition'][key] = value
                        self.assertIsNone(transition_identity(corrupt))

    def test_expiry_repetition_safe_defense_and_other_actor_do_not_chain(self):
        with candidate_context(entries=True, chains=True, draft_content=True), submission_chain_trial(True):
            for variant in ('expired', 'round', 'same_hold', 'safe', 'safe_second', 'other_actor', 'position'):
                self.state.update(position='mount', top='a', bottom='b', tick=1, round=1)
                self.state.pop(PENDING, None)
                self.exchange('americana', margin=-50 if variant == 'safe' else 25)
                self.state['tick'] = 3 if variant == 'expired' else 2
                if variant == 'round':
                    self.state['round'] = 2
                if variant == 'other_actor':
                    self.state[PENDING]['actor'] = 'b'
                if variant == 'position':
                    self.engine.set_fight_position(self.state, 'guard', top='a', bottom='b')
                    self.assertNotIn(PENDING, self.state)
                event = self.exchange('kimura' if variant == 'position' else
                                      'americana' if variant == 'same_hold' else 'straight armbar',
                                      margin=-50 if variant == 'safe_second' else 25)
                self.assertNotIn('hold_transition', event)

    def test_nested_restore_and_disabled_bout_parity(self):
        original = FightAuditHarness.resolve_exchange
        with self.assertRaisesRegex(RuntimeError, 'stop'):
            with submission_chain_trial(True):
                wrapped = FightAuditHarness.resolve_exchange
                with submission_chain_trial(True):
                    self.assertIs(FightAuditHarness.resolve_exchange, wrapped)
                with self.assertRaises(ValueError):
                    with submission_chain_trial(False):
                        pass
                raise RuntimeError('stop')
        self.assertIs(FightAuditHarness.resolve_exchange, original)
        engine = TerminalRngHarness()
        expected = run_audited_fight(engine, self.a, self.b, 8451, {})
        with submission_chain_trial(False):
            other = TerminalRngHarness()
            self.assertEqual(run_audited_fight(other, self.a, self.b, 8451, {}), expected)
            self.assertEqual(engine.terminal_rng_states, other.terminal_rng_states)


if __name__ == '__main__':
    unittest.main()
