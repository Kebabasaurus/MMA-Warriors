"""Bounded action commitment stays audit-only and conserves actual draws."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from analysis.continuation_commitment_candidate import committed_bonuses, continuation_commitment_trial
from analysis.fight_candidate_context import candidate_context
from analysis.generate_variety_opportunity_report import TerminalRngHarness
from fight_engine_audit import FightAuditHarness, run_audited_fight
import fight_chain_action_weighting_regression_test as fixture


class CommitmentTests(unittest.TestCase):
    setUp = fixture.ChainActionWeightingTests.setUp

    def test_bounded_probability_mixture(self):
        for strength in (0.1, 0.5, 1, 2):
            weights = {'jab': 100, 'kick': 100, 'shoot': 100}
            result = committed_bonuses(weights, {'jab': strength})
            old_share = (100 + 100 * strength) / (300 + 100 * strength)
            new_share = (100 + 100 * result['jab']) / (300 + 100 * result['jab'])
            self.assertAlmostEqual(new_share, old_share + (1 - old_share) * strength / 4)
            self.assertEqual(set(result), {'jab'})
        self.assertEqual(committed_bonuses(weights, {}), {})
        self.assertEqual(committed_bonuses(weights, {'jab': 2}, False), {'jab': 2})

    def test_actual_budget_order_and_nonstacking_restoration(self):
        self.state.update(gas={'a': 100}, hurt={'a': 0})
        args = (self.a, self.b, self.state, self.weights, 1, 2)
        before, rng = deepcopy(self.state), random.getstate()
        original = FightAuditHarness._chain_action_weights
        baseline = self.engine._chain_action_weights(*args)
        with self.assertRaisesRegex(RuntimeError, 'stop'):
            with continuation_commitment_trial(True):
                observed = self.engine._chain_action_weights(*args)
                with continuation_commitment_trial(True):
                    self.assertEqual(observed, self.engine._chain_action_weights(*args))
                self.assertGreater(observed['jab'], baseline['jab'])
                self.assertEqual(sum(observed.values()), sum(self.weights.values()))
                self.assertEqual(list(observed), list(self.weights))
                self.assertTrue(all(v >= 1 for v in observed.values()))
                raise RuntimeError('stop')
        self.assertIs(FightAuditHarness._chain_action_weights, original)
        self.assertNotIn('_chain_action_bonuses', self.engine.__dict__)
        self.assertEqual((self.state, random.getstate()), (before, rng))

    def test_tired_hurt_expired_and_initiative_unchanged(self):
        args = (self.a, self.b, self.state, self.weights, 1, 2)
        for gas, hurt in ((41, 0), (100, self.a.toughness)):
            self.state.update(gas={'a': gas}, hurt={'a': hurt})
            baseline = self.engine._chain_action_weights(*args)
            with continuation_commitment_trial(True):
                self.assertEqual(baseline, self.engine._chain_action_weights(*args))
        self.state.update(gas={'a': 100}, hurt={'a': 0})
        preview = self.engine._chain_action_bonuses(*args)
        with continuation_commitment_trial(True):
            self.assertEqual(preview, self.engine._chain_action_bonuses(*args))
        self.state['move_chains']['a']['tick'] = -1
        with continuation_commitment_trial(True):
            self.assertEqual(self.engine._chain_action_weights(*args), self.weights)

    def test_prepared_only_intent_is_not_scaled(self):
        self.state.update(gas={'a': 100}, hurt={'a': 0})
        args = (self.a, self.b, self.state, {'submission': 100, 'jab': 100}, 1, 2)
        with patch.object(self.engine, '_chain_action_bonuses', side_effect=lambda *args: {}), \
                patch.object(self.engine, '_prepared_submission_opportunity', return_value={'readiness': 1}):
            baseline = self.engine._chain_action_weights(*args)
            with continuation_commitment_trial(True):
                self.assertEqual(self.engine._chain_action_weights(*args), baseline)

    def test_default_off_full_bout_parity_and_context_guards(self):
        a, b = self.a, self.b
        engine = TerminalRngHarness()
        baseline = run_audited_fight(engine, a, b, 9330000, {})
        rng = engine.terminal_rng_states
        with continuation_commitment_trial(True):
            self.assertEqual(run_audited_fight(engine, a, b, 9330000, {}), baseline)
            self.assertEqual(engine.terminal_rng_states, rng)
        for options in ({'chains': False}, {'chains': True, 'stronger_continuation': True}):
            with self.assertRaises(ValueError):
                with candidate_context(continuation_commitment=True, **options):
                    pass


if __name__ == '__main__':
    unittest.main()
