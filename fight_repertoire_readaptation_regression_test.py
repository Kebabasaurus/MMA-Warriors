"""Earlier independent repetition must retain eligibility, live chains and purity."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
import random
import unittest
from unittest.mock import patch

from analysis.repertoire_readaptation_candidate import repertoire_readaptation_trial
from analysis.fight_candidate_context import candidate_context
from analysis import evaluate_joint_fight_candidate as evaluator
from fight_engine_audit import FightAuditHarness, run_audited_fight
from fight_moves import MOVE_REGISTRY
import fight_move_adaptability_regression_test as fixture


class RepertoireReadaptationTests(unittest.TestCase):
    setUp = fixture.MoveAdaptabilityTests.setUp
    score = fixture.MoveAdaptabilityTests.score

    def test_earlier_exposure_retains_existing_curve_and_cap(self):
        with repertoire_readaptation_trial(True):
            for skill in (30, 65, 90):
                unit = 2.6 + max(0, skill - 65) / 55
                self.assertEqual(self.score(skill, 0), (0, ()))
                for repeats in (1, 2, 3, 100):
                    score, reasons = self.score(skill, repeats)
                    self.assertAlmostEqual(score, -min(14, repeats * unit))
                    if repeats == 1:
                        self.assertIn('earlier-repertoire-readaptation', reasons)
                    if repeats == 100:
                        self.assertNotIn('earlier-repertoire-readaptation', reasons)

    def test_live_followup_keeps_original_penalty_and_bonus(self):
        self.engine._experimental_chain_action_weighting = True
        context = deepcopy(self.context)
        context['actor_reads']['moves'][self.move.move_id] = 3
        args = (self.a, self.b, self.move, self.state, 'a', ('Boxer',), False,
                {'source_move_id': 'root'}, {self.move.move_id})
        before, rng = deepcopy(context), random.getstate()
        baseline = self.engine._move_contextual_score(*args, context=context)
        with repertoire_readaptation_trial(True):
            self.assertEqual(self.engine._move_contextual_score(*args, context=context), baseline)
        self.assertEqual(context, before)
        self.assertEqual(random.getstate(), rng)

    def test_nested_errors_restore_method_rng_and_do_not_stack(self):
        original, rng = FightAuditHarness._move_contextual_score, random.getstate()
        with repertoire_readaptation_trial(True):
            once = self.score(90, 2)
            with self.assertRaisesRegex(RuntimeError, 'trial failure'):
                with repertoire_readaptation_trial(True):
                    self.assertEqual(self.score(90, 2), once)
                    random.random()
                    raise RuntimeError('trial failure')
            self.assertEqual(self.score(90, 2), once)
        self.assertIs(FightAuditHarness._move_contextual_score, original)
        self.assertEqual(random.getstate(), rng)
        with self.assertRaisesRegex(ValueError, 'requires chain mechanics'):
            with candidate_context(repertoire_readaptation=True):
                self.fail('Accepted without chain mechanics')

    def test_normal_play_complete_bout_parity_with_trial_enabled(self):
        self.engine._experimental_chain_action_weighting = False
        actual = run_audited_fight(self.engine, self.a, self.b, 913007, {'rounds': 3})
        rng = random.getstate()
        with repertoire_readaptation_trial(True):
            trial = run_audited_fight(self.engine, self.a, self.b, 913007, {'rounds': 3})
            self.assertEqual(random.getstate(), rng)
        self.assertEqual(trial, actual)

    def test_cli_keeps_full_calibration_and_failures(self):
        with patch('sys.argv', ['candidate', '--repertoire-readaptation', '--fights', '1']), \
             patch.object(evaluator, 'calibration_trial', return_value={'failures': ['failed']}) as full, \
             patch.object(evaluator, 'coverage_trial') as coverage, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(evaluator.main(), 1)
        full.assert_called_once_with(repertoire_readaptation=True)
        coverage.assert_not_called()
        self.assertTrue(json.loads(output.getvalue())['repertoire_readaptation_trial'])

    def test_jab_filter_changes_only_jabs_and_retains_cap(self):
        for move in MOVE_REGISTRY.values():
            self.move = move
            for repeats in (0, 1, 3, 100):
                baseline = self.score(90, repeats)
                with repertoire_readaptation_trial(True, actions={'jab'}):
                    actual = self.score(90, repeats)
                if move.parent_action != 'jab' or repeats in (0, 100):
                    self.assertEqual(actual, baseline, move.move_id)
                else:
                    unit = 2.6 + 25 / 55
                    self.assertAlmostEqual(actual[0] - baseline[0], -unit, msg=move.move_id)

    def test_filtered_live_chains_and_normal_play_unchanged(self):
        with repertoire_readaptation_trial(True, actions={'jab'}):
            self.engine._experimental_chain_action_weighting = True
            context = deepcopy(self.context)
            context['actor_reads']['moves'][self.move.move_id] = 3
            args = (self.a, self.b, self.move, self.state, 'a', ('Boxer',), False,
                    {'source_move_id': 'root'}, {self.move.move_id})
            original = self.engine._move_contextual_score(*args, context=context)
        self.assertEqual(self.engine._move_contextual_score(*args, context=context), original)
        self.engine._experimental_chain_action_weighting = False
        baseline = run_audited_fight(self.engine, self.a, self.b, 913007, {'rounds': 3})
        with repertoire_readaptation_trial(True, actions={'jab'}):
            self.assertEqual(run_audited_fight(self.engine, self.a, self.b, 913007, {'rounds': 3}), baseline)

    def test_filtered_nested_scope_and_conflicts_restore(self):
        original, rng = FightAuditHarness._move_contextual_score, random.getstate()
        with repertoire_readaptation_trial(True, actions={'jab'}):
            once = self.score(90, 2)
            with repertoire_readaptation_trial(True, actions=['jab']):
                self.assertEqual(self.score(90, 2), once)
            with self.assertRaisesRegex(ValueError, 'Conflicting nested'):
                with repertoire_readaptation_trial(True):
                    self.fail('Accepted conflicting filter')
            self.assertEqual(self.score(90, 2), once)
        self.assertIs(FightAuditHarness._move_contextual_score, original)
        self.assertEqual(random.getstate(), rng)
        for kwargs in ({'jab_readaptation': True},
                       {'chains': True, 'jab_readaptation': True, 'repertoire_readaptation': True}):
            with self.assertRaisesRegex(ValueError, 'Jab readaptation requires'):
                with candidate_context(**kwargs):
                    self.fail('Accepted invalid candidate')

    def test_jab_cli_keeps_mount_base_full_calibration_and_failures(self):
        with patch('sys.argv', ['candidate', '--jab-readaptation', '--gift-wrap-mount', '--fights', '1']), \
             patch.object(evaluator, 'calibration_trial', return_value={'failures': ['failed']}) as full, \
             patch.object(evaluator, 'coverage_trial') as coverage, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(evaluator.main(), 1)
        full.assert_called_once_with(jab_readaptation=True, gift_wrap_mount=True)
        coverage.assert_not_called()
        self.assertTrue(json.loads(output.getvalue())['jab_readaptation_trial'])


if __name__ == '__main__':
    unittest.main()
