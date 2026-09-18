"""A scoped escape preference cannot bypass ordinary action or chain resolution."""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from analysis import failed_shot_escape_intent as trial
from analysis.fight_candidate_context import candidate_context
from fight_engine_audit import run_audited_fight, synthetic_fighter


class FailedShotEscapeIntentTests(unittest.TestCase):
    def test_menu_scope_order_no_mutation_and_single_delegate(self):
        engine = trial.FightAuditHarness()
        a, b = SimpleNamespace(name='a', behaviour='Sprawl And Brawl'), SimpleNamespace(name='b')
        original, rng = trial.FightAuditHarness._chain_action_weights, random.getstate()
        calls = []
        def delegate(self, fighter, opponent, state, weights, round_no, tick):
            calls.append((fighter, opponent, state, weights, round_no, tick))
            return weights
        with patch.object(trial.FightAuditHarness, '_chain_action_weights', delegate), trial.escape_intent_trial(True):
            for enabled, position, controller, behaviour, disengage, expected in (
                    (True, 'failed shot', 'a', 'Sprawl And Brawl', True, True),
                    (False, 'failed shot', 'a', 'Sprawl And Brawl', True, False),
                    (True, 'range', 'a', 'Sprawl And Brawl', True, False),
                    (True, 'failed shot', 'b', 'Sprawl And Brawl', True, False),
                    (True, 'failed shot', None, 'Sprawl And Brawl', True, False),
                    (True, 'failed shot', 'a', 'Pressure', True, False),
                    (True, 'failed shot', 'a', 'Sprawl And Brawl', False, False)):
                engine._experimental_specialist_entries = enabled
                a.behaviour = behaviour
                state = dict(position=position, clinch_controller=controller)
                weights = dict(front_headlock=70, force_cage=60)
                if disengage:
                    weights['disengage'] = 50
                before = deepcopy((state, weights))
                result = engine._chain_action_weights(a, b, state, weights, 1, 2)
                self.assertEqual(list(result), list(weights))
                if expected:
                    self.assertGreater(result['disengage'], weights['disengage'])
                    self.assertEqual(sum(result.values()), sum(weights.values()))
                    self.assertTrue(all(type(value) is int and value >= 1 for value in result.values()))
                else:
                    self.assertEqual(result, weights)
                self.assertEqual((state, weights), before)
                self.assertEqual(calls[-1], (a, b, state, result, 1, 2))
                if not expected:
                    self.assertIs(result, weights)
            self.assertEqual(len(calls), 7)
        self.assertIs(trial.FightAuditHarness._chain_action_weights, original)
        self.assertEqual(random.getstate(), rng)

    def test_nested_trial_never_stacks_and_error_restores_method_rng(self):
        engine = trial.FightAuditHarness()
        engine._experimental_specialist_entries = True
        a, b = SimpleNamespace(name='a', behaviour='Sprawl And Brawl'), SimpleNamespace(name='b')
        state = dict(position='failed shot', clinch_controller='a')
        original, rng = trial.FightAuditHarness._chain_action_weights, random.getstate()
        seen = []
        def delegate(self, fighter, opponent, state, weights, round_no, tick):
            seen.append(weights['disengage'])
            random.random()
            if round_no == 2:
                raise RuntimeError('chain failure')
            return weights
        with patch.object(trial.FightAuditHarness, '_chain_action_weights', delegate):
            with trial.escape_intent_trial():
                self.assertIs(trial.FightAuditHarness._chain_action_weights, delegate)
            with trial.escape_intent_trial(True):
                outer = trial.FightAuditHarness._chain_action_weights
                with trial.escape_intent_trial(True), trial.escape_intent_trial(False):
                    self.assertIs(trial.FightAuditHarness._chain_action_weights, outer)
                    result = engine._chain_action_weights(a, b, state, {'front_headlock': 50, 'disengage': 50}, 1, 2)
                    self.assertEqual(result, {'front_headlock': 39, 'disengage': 61})
                with self.assertRaisesRegex(RuntimeError, 'chain failure'):
                    with trial.escape_intent_trial(True):
                        engine._chain_action_weights(a, b, state, {'front_headlock': 50, 'disengage': 50}, 2, 2)
                self.assertIs(trial.FightAuditHarness._chain_action_weights, outer)
            self.assertIs(trial.FightAuditHarness._chain_action_weights, delegate)
        self.assertEqual(seen, [61, 61])
        self.assertIs(trial.FightAuditHarness._chain_action_weights, original)
        self.assertEqual(random.getstate(), rng)

    def test_apportionment_keeps_cleaned_budget_positive_ordered_alternatives(self):
        for weights in ({'front_headlock': 0.1, 'force_cage': -4, 'disengage': 1},
                        {'front_headlock': 70.9, 'force_cage': 60.2, 'disengage': 50.8},
                        {'front_headlock': 1, 'force_cage': 1, 'disengage': 99},
                        {'disengage': 1}, {'disengage': 50}):
            before = dict(weights)
            result = trial.escape_tickets(weights)
            self.assertEqual(list(result), list(weights))
            self.assertEqual(sum(result.values()), sum(max(1, int(value)) for value in weights.values()))
            self.assertTrue(all(type(value) is int and value >= 1 for value in result.values()))
            self.assertEqual(weights, before)

    def test_default_off_complete_bout_parity_and_survival_bypass(self):
        rng = random.getstate()
        self.addCleanup(random.setstate, rng)
        a = synthetic_fighter('Red', 75, 'Boxer', 'Sprawl And Brawl', 0)
        b = synthetic_fighter('Blue', 75, 'Wrestler', 'Control', 1)
        engine = trial.FightAuditHarness()
        for enabled in (False, True):
            with candidate_context(entries=enabled, chains=enabled, draft_content=enabled):
                control = run_audited_fight(engine, a, b, 81231, {})
                with trial.escape_intent_trial(False):
                    self.assertEqual(run_audited_fight(engine, a, b, 81231, {}), control)
                if not enabled:
                    with trial.escape_intent_trial(True):
                        self.assertEqual(run_audited_fight(engine, a, b, 81231, {}), control)
        state = dict(position='failed shot', clinch_controller='Red', gas={'Red': 3}, hurt={'Red': 0})
        engine._experimental_specialist_entries = True
        with patch.object(engine, 'fight_mechanics_rng') as mechanics, \
             patch.object(trial.FightAuditHarness, '_chain_action_weights') as delegate, trial.escape_intent_trial(True):
            mechanics.return_value.random.return_value = 0
            self.assertEqual(engine.choose_action(a, b, state, 1, 2), 'survive')
            delegate.assert_not_called()

    def test_full_calibration_provenance_failure_retention_and_exclusive_output(self):
        reference_hash = hashlib.sha256((trial.ROOT / 'analysis/fight_engine_baseline.json').read_bytes()).hexdigest()
        expected = dict(experimental_only=True, fights=3840, overall={'total': 3840},
                        groups={'Overall': {'total': 3840}, 'Tier': {'total': 120}},
                        failures=['locked counts fail'], registry_sha256='registry', reference_sha256=reference_hash)
        rng = random.getstate()
        with patch.object(trial.evaluator, 'calibration_trial', return_value=deepcopy(expected)) as build:
            result = trial.build_report()
            build.assert_called_once_with()
        for field, value in expected.items():
            self.assertEqual(result[field], value)
        self.assertIn('fight_moves/submission_pool.py', result['source_sha256'])
        self.assertIn('analysis/failed_shot_escape_intent.py', result['source_sha256'])
        self.assertEqual(len(result['input_schedule_sha256']), 64)
        self.assertEqual(random.getstate(), rng)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'calibration.json'
            with patch.object(trial, 'build_report', return_value=result) as build, redirect_stdout(io.StringIO()):
                self.assertEqual(trial.main(['--output', str(output)]), 1)
                with self.assertRaises(FileExistsError):
                    trial.main(['--output', str(output)])
                build.assert_called_once_with()
            self.assertEqual(json.loads(output.read_text()), result)
        with patch.object(trial.evaluator, 'calibration_trial', return_value=dict(expected, reference_sha256='changed')):
            with self.assertRaisesRegex(RuntimeError, 'reference changed'):
                trial.build_report()


if __name__ == '__main__':
    unittest.main()
