"""Stronger audit intent preserves legality, cadence, draw budgets and restoration."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
import random
import unittest
from unittest.mock import patch

import fight_moves

from analysis.continuation_strength_candidate import continuation_strength_trial
from analysis.fight_candidate_context import candidate_context
from analysis import evaluate_joint_fight_candidate as evaluator
from fight_engine_audit import FightAuditHarness, run_audited_fight
import fight_chain_action_weighting_regression_test as fixture
import fight_top_leg_entry_regression_test as full_fixture


class ContinuationStrengthTests(unittest.TestCase):
    setUp = fixture.ChainActionWeightingTests.setUp

    def test_combined_context_restores_registry_and_trial_on_error(self):
        registry = fight_moves.MOVE_REGISTRY
        method = FightAuditHarness._chain_action_weights
        rng = random.getstate()
        with self.assertRaisesRegex(RuntimeError, 'combined failure'):
            with candidate_context(entries=True, chains=True, draft_content=True,
                                   stronger_continuation=True):
                self.assertEqual(len(fight_moves.MOVE_REGISTRY), 400)
                self.assertTrue(getattr(FightAuditHarness._chain_action_weights,
                                        '_stronger_continuation_trial', False))
                random.random()
                raise RuntimeError('combined failure')
        self.assertIs(fight_moves.MOVE_REGISTRY, registry)
        self.assertIs(FightAuditHarness._chain_action_weights, method)
        self.assertEqual(random.getstate(), rng)

    def test_prepared_preference_is_not_doubled_or_stacked(self):
        args = (self.a, self.b, self.state, {'submission': 100, 'jab': 100}, 1, 2)
        with patch.object(self.engine, '_prepared_submission_opportunity', return_value={'readiness': 1}), \
             patch.object(self.engine, '_chain_action_bonuses', return_value={}) as preview:
            baseline = self.engine._chain_action_weights(*args)
            preview.return_value = {'submission': .4}
            with continuation_strength_trial(True):
                self.assertEqual(self.engine._chain_action_weights(*args), baseline)

    def test_survival_bypasses_the_trial_apportioner(self):
        full_fixture.TopLegEntryTests.setUp(self)
        self.engine._experimental_chain_action_weighting = True
        self.initial['gas']['a'] = 3
        self.initial['hurt']['a'] = 0
        with continuation_strength_trial(True), \
             patch.object(self.engine, '_chain_action_weights', wraps=self.engine._chain_action_weights) as apportion, \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.random.return_value = 0
            self.assertEqual(self.engine.choose_action(self.a, self.b, self.initial, 1, 1), 'survive')
            apportion.assert_not_called()

    def test_real_apportionment_preserves_budget_options_rng_and_initiative(self):
        self.weights_menu = self.weights
        self.state.update(gas={'a': 100, 'b': 100}, hurt={'a': 0, 'b': 0})
        before = deepcopy(self.state)
        rng = random.getstate()
        args = (self.a, self.b, self.state, self.weights_menu, 1, 2)
        baseline = self.engine._chain_action_weights(*args)
        cadence = self.engine._chain_initiative_bonus(self.a, self.b, self.state)
        with continuation_strength_trial(True):
            result = self.engine._chain_action_weights(*args)
            self.assertGreater(result['jab'], baseline['jab'])
            self.assertEqual(sum(result.values()), sum(baseline.values()))
            self.assertEqual(list(result), list(self.weights_menu))
            self.assertTrue(all(value >= 1 for value in result.values()))
            self.assertEqual(self.engine._chain_initiative_bonus(self.a, self.b, self.state), cadence)
        self.assertEqual(self.state, before)
        self.assertEqual(random.getstate(), rng)
        self.assertNotIn('_chain_action_bonuses', self.engine.__dict__)

    def test_strength_retains_skill_and_fatigue_bounds(self):
        def observe(engine, *args):
            return engine._chain_action_bonuses(*args)
        with patch.object(FightAuditHarness, '_chain_action_weights', observe):
            with continuation_strength_trial(True):
                for skill, gas, expected in ((90, 100, 4), (90, 15, 1), (40, 100, .5)):
                    self.a.detailed_skills.update(dict.fromkeys(
                        ('combination_punching', 'adaptability', 'discipline'), skill))
                    self.state['gas'] = {'a': gas}
                    bonuses = self.engine._chain_action_weights(self.a, self.b, self.state, self.weights, 1, 2)
                    self.assertEqual(bonuses['jab'], expected)

    def test_nested_exception_restores_instance_class_and_rng_without_stacking(self):
        original = FightAuditHarness._chain_action_weights
        override = lambda *args: {'jab': 2}
        self.engine._chain_action_bonuses = override
        rng = random.getstate()
        args = (self.a, self.b, self.state, self.weights, 1, 2)
        with continuation_strength_trial(True):
            once = self.engine._chain_action_weights(*args)
            with self.assertRaisesRegex(RuntimeError, 'nested failure'):
                with continuation_strength_trial(True):
                    self.assertEqual(self.engine._chain_action_weights(*args), once)
                    random.random()
                    raise RuntimeError('nested failure')
            self.assertIs(self.engine._chain_action_bonuses, override)
            with patch.object(self.engine, '_prepared_submission_opportunity', side_effect=ValueError('menu failure')):
                with self.assertRaisesRegex(ValueError, 'menu failure'):
                    self.engine._chain_action_weights(self.a, self.b, self.state, {'submission': 10}, 1, 2)
            self.assertIs(self.engine._chain_action_bonuses, override)
        self.assertIs(FightAuditHarness._chain_action_weights, original)
        self.assertEqual(random.getstate(), rng)

    def test_no_live_opportunity_or_disabled_flag_retains_original_weights(self):
        args = (self.a, self.b, self.state, self.weights, 1, 2)
        with continuation_strength_trial(True):
            self.state['move_chains'] = {}
            self.assertIs(self.engine._chain_action_weights(*args), self.weights)
            self.engine._experimental_chain_action_weighting = False
            self.assertIs(self.engine._chain_action_weights(*args), self.weights)
        with self.assertRaisesRegex(ValueError, 'requires chain mechanics'):
            with candidate_context(stronger_continuation=True):
                self.fail('Accepted stronger intent without chains')

    def test_disabled_trial_complete_bout_parity(self):
        baseline = run_audited_fight(self.engine, self.a, self.b, 93271, {})
        rng = random.getstate()
        with continuation_strength_trial(False):
            result = run_audited_fight(self.engine, self.a, self.b, 93271, {})
            self.assertEqual(random.getstate(), rng)
        self.assertEqual(result, baseline)

    def test_cli_keeps_full_calibration_and_failure(self):
        with patch('sys.argv', ['candidate', '--stronger-continuation', '--fights', '1']), \
             patch.object(evaluator, 'calibration_trial', return_value={'failures': ['balance failure']}) as full, \
             patch.object(evaluator, 'coverage_trial') as coverage, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(evaluator.main(), 1)
        full.assert_called_once_with(stronger_continuation=True)
        coverage.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())['continuation_bonus_multiplier'], 2)


if __name__ == '__main__':
    unittest.main()
