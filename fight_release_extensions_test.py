"""Native submission extensions reproduce the retained disposable candidate."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

import fight_engine
from analysis.fight_candidate_context import candidate_context
from analysis.generate_variety_opportunity_report import TerminalRngHarness
from analysis.cradle_setup_candidate import validate_cradle_setups
from analysis.submission_chain_candidate import validate_hold_transitions
from fight_engine_audit import run_audited_fight, synthetic_fighter
from fight_moves.submission_identity import COMPATIBLE_SUBMISSION_IDS
from fight_release_extensions import ReleaseCradleMixin, ReleaseSubmissionChainMixin, KEY, FACT, HOLD, MOVE_ID
import fight_scarf_hold_setup_regression_test as scarf_tests
import fight_submission_chain_candidate_test as chain_tests


class NativeHarness(ReleaseCradleMixin, ReleaseSubmissionChainMixin, TerminalRngHarness):
    @property
    def _fight_move_registry(self):
        return fight_engine.MOVE_REGISTRY


RECIPE = dict(entries=True, chains=True, draft_content=True, gift_wrap_mount=True,
              heel_hook_identity=True, standing_head_damage=True, kick_power=True,
              survival_expansion=True)


class NativeExtensionTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(random.setstate, random.getstate())

    def test_actual_complete_bout_and_terminal_rng_parity(self):
        for seed, style_a, style_b in ((9330000, 'Catch Wrestler', 'BJJ'),
                                      (9600002, 'Judo', 'Catch Wrestler'),
                                      (9410906, 'Boxer', 'Wrestler'),
                                      (9412207, 'Muay Thai', 'BJJ'),
                                      (9320004, 'Submission Grappler', 'Catch Wrestler'),
                                      (9330012, 'Catch Wrestler', 'Catch Wrestler')):
            a = synthetic_fighter('Native A', 85, style_a, 'Control', 0)
            b = synthetic_fighter('Native B', 80, style_b, 'Control', 1)
            with candidate_context(**RECIPE, hold_transitions=True, cradle_setup=True):
                old = TerminalRngHarness()
                expected = run_audited_fight(old, a, b, seed)
                rng = old.terminal_rng_states
            with candidate_context(**RECIPE), patch.dict(COMPATIBLE_SUBMISSION_IDS, {HOLD[0]: (MOVE_ID,)}):
                native = NativeHarness()
                actual = run_audited_fight(native, a, b, seed)
                self.assertEqual(actual, expected, (seed, style_a, style_b))
                self.assertEqual(native.terminal_rng_states, rng)

    def test_real_cradle_threshold_ticket_consumption_and_horn(self):
        scarf_tests.ScarfHoldSetupTests.setUp(self)
        self.engine.__class__ = NativeHarness
        self.a.style = self.b.style = 'Catch Wrestler'
        self.a.secondary_style = self.b.secondary_style = ''
        with candidate_context(**RECIPE):
            for slot in ('a', 'b'):
                for margin, edge, created in ((8, 0, False), (8.01, 0, True), (6, 10, False), (6.01, 10, True)):
                    actor, defender, state, stats, before, prior, text = scarf_tests.ScarfHoldSetupTests.create(self, slot, margin, edge)
                    self.assertEqual(KEY in state, created)
                    self.assertEqual(stats[slot], dict(control=3, impact=0, danger=0))
                    event = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender,
                                                                   'ground_control', text, before, prior, state, stats)
                    self.assertEqual(event['move_id'], 'generic_ground_control')
                    self.assertEqual(validate_cradle_setups([event])['invalid'], 0)
                    if not created:
                        continue
                    state['tick'] += 1
                    tickets = self.engine.submission_technique_tickets(actor, 'submission', state)
                    self.assertEqual(tickets.count(HOLD), 1)
                    for chosen, status in ((HOLD, 'used'), (tickets[0], 'consumed')):
                        trial = deepcopy(state)
                        with patch.object(self.engine, 'fight_mechanics_rng') as rng:
                            rng.return_value.choice.return_value = chosen
                            self.engine.submission_technique(actor, 'submission', trial)
                            rng.return_value.choice.assert_called_once()
                        self.assertNotIn(KEY, trial)
                        self.assertEqual(trial[FACT]['status'], status)
                    self.engine.recover_between_rounds(self.a, self.b, state)
                    self.assertNotIn(KEY, state)

    def test_real_top_and_guard_transition_provenance(self):
        chain_tests.SubmissionChainTests.setUp(self)
        self.engine.__class__ = NativeHarness
        with candidate_context(**RECIPE):
            for action, position, first, second, identity in (
                    ('submission', 'mount', 'americana', 'straight armbar', 'top_submission_chain'),
                    ('bottom_submission', 'guard', 'triangle choke', 'armbar', 'guard_submission_chain')):
                self.state.update(position=position, top='a' if action == 'submission' else 'b',
                                  bottom='b' if action == 'submission' else 'a', tick=1)
                self.state.pop('_hold_transition_root', None)
                self.a.signature_moves = [identity]
                self.a.move_mastery = {identity: 100}
                root = chain_tests.SubmissionChainTests.exchange(self, first, action)
                self.state['tick'] = 2
                follow = chain_tests.SubmissionChainTests.exchange(self, second, action)
                self.assertEqual(follow['move_id'], identity)
                self.assertEqual(validate_hold_transitions([root, follow]),
                                 dict(roots=2, transitions=1, named=1, invalid=0))
                self.engine.set_fight_position(self.state, 'range')
                self.assertNotIn('_hold_transition_root', self.state)


if __name__ == '__main__':
    unittest.main()
