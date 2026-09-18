"""Boundary expiry is audit-scoped and leaves current-round counters intact."""
from copy import deepcopy
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from analysis import round_counter_expiry as trial
from analysis.fight_candidate_context import candidate_context
from fight_engine_audit import run_audited_fight, synthetic_fighter


class RoundCounterExpiryTests(unittest.TestCase):
    def test_boundary_before_both_calls_and_narrow_scope(self):
        engine = trial.FightAuditHarness()
        seen = []
        def delegate(self, a, b, state):
            seen.append(deepcopy(state))
            return 123
        with patch.object(trial.FightAuditHarness, 'initiative', delegate), trial.round_counter_trial(True):
            for entries, chains, tick, created, current, expires in (
                    (True, True, 1, 1, 2, True),
                    (True, True, 1, 2, 2, False),
                    (True, True, 2, 1, 2, False),
                    (True, True, 1, 3, 2, False),
                    (True, True, 1, None, 2, False),
                    (True, True, 1, True, 2, False),
                    (True, True, 1, 0, 2, False),
                    (False, True, 1, 1, 2, False),
                    (True, False, 1, 1, 2, False)):
                engine._experimental_specialist_entries = entries
                engine._experimental_chain_action_weighting = chains
                state = dict(round=current, tick=tick, counter_window=dict(created_round=created,
                             created_tick=1, fighter='Blue'), position='range', unrelated={'x': 1})
                expected = deepcopy(state)
                if expires:
                    expected['counter_window'] = None
                for a, b in (('Red', 'Blue'), ('Blue', 'Red')):
                    self.assertEqual(engine.initiative(a, b, state), 123)
                    self.assertEqual(seen[-1], expected)
                    self.assertEqual(state, expected)
        self.assertEqual(len(seen), 18)

    def test_nested_exception_restores_binding_and_rng(self):
        original, rng = trial.FightAuditHarness.initiative, random.getstate()
        with self.assertRaisesRegex(RuntimeError, 'test'):
            with trial.round_counter_trial(True):
                outer = trial.FightAuditHarness.initiative
                with trial.round_counter_trial(True), trial.round_counter_trial(False):
                    self.assertIs(trial.FightAuditHarness.initiative, outer)
                    random.random()
                    raise RuntimeError('test')
        self.assertIs(trial.FightAuditHarness.initiative, original)
        self.assertEqual(random.getstate(), rng)

    def test_complete_bout_default_off_and_normal_parity(self):
        rng = random.getstate()
        self.addCleanup(random.setstate, rng)
        a = synthetic_fighter('Red', 75, 'Boxer', 'Sprawl And Brawl', 0)
        b = synthetic_fighter('Blue', 75, 'Wrestler', 'Control', 1)
        engine = trial.FightAuditHarness()
        for enabled in (False, True):
            with candidate_context(entries=enabled, chains=enabled, draft_content=enabled):
                control = run_audited_fight(engine, a, b, 81231, {})
                with trial.round_counter_trial(False):
                    self.assertEqual(run_audited_fight(engine, a, b, 81231, {}), control)
                if not enabled:
                    with trial.round_counter_trial(True):
                        self.assertEqual(run_audited_fight(engine, a, b, 81231, {}), control)

    def test_real_resolver_previous_round_windows_reach_neither_initiative_score(self):
        rng = random.getstate()
        self.addCleanup(random.setstate, rng)
        a = synthetic_fighter('Red', 75, 'Boxer', 'Sprawl And Brawl', 0)
        b = synthetic_fighter('Blue', 75, 'Wrestler', 'Control', 1)
        original = trial.FightAuditHarness.initiative
        counts = {}
        for enabled in (False, True):
            observed = []
            def observe(engine, fighter, opponent, state):
                window = state.get('counter_window') or {}
                if window:
                    observed.append((window['created_round'], state['round']))
                return original(engine, fighter, opponent, state)
            with candidate_context(entries=True, chains=True, draft_content=True), \
                 patch.object(trial.FightAuditHarness, 'initiative', observe), trial.round_counter_trial(enabled):
                for seed in range(81231, 81251):
                    run_audited_fight(trial.FightAuditHarness(), a, b, seed, {})
            counts[enabled] = observed
        self.assertTrue(any(created < current for created, current in counts[False]))
        self.assertTrue(counts[True])
        self.assertTrue(all(created == current for created, current in counts[True]))

    def test_artifact_groups_failures_source_guards_and_exclusive_output(self):
        reference = hashlib.sha256((trial.ROOT / 'analysis/fight_engine_baseline.json').read_bytes()).hexdigest()
        expected = dict(overall={'total': 3840}, groups={'Overall': {'total': 3840}},
                        failures=['locked counts fail'], reference_sha256=reference)
        with patch.object(trial.evaluator, 'calibration_trial', return_value=deepcopy(expected)):
            result = trial.build_report()
        for key, value in expected.items():
            self.assertEqual(result[key], value)
        self.assertIn('analysis/round_counter_expiry.py', result['source_sha256'])
        self.assertEqual(len(result['input_schedule_sha256']), 64)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'trial.json'
            with patch.object(trial, 'build_report', return_value=result) as build, redirect_stdout(io.StringIO()):
                self.assertEqual(trial.main(['--output', str(output)]), 1)
                with self.assertRaises(FileExistsError):
                    trial.main(['--output', str(output)])
                build.assert_called_once_with(False)
            self.assertEqual(json.loads(output.read_text()), result)
        original, reads = Path.read_bytes, 0
        def changed(path):
            nonlocal reads
            data = original(path)
            if path == trial.ROOT / 'fight_engine.py':
                reads += 1
                if reads > 1:
                    return data + b'changed'
            return data
        with patch.object(trial.evaluator, 'calibration_trial', return_value=expected), \
             patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(RuntimeError, 'Source changed'):
                trial.build_report()

    def test_coverage_failures_are_reported_and_return_failure(self):
        result = {'arms': {'combined': {'content_gate_failures': ['missing move'],
                   'chain_gate_failures': ['short chains'], 'measured_final_target_failures': ['variety']}}}
        self.assertEqual(trial.report_failures(result),
                         ['combined: missing move', 'combined: short chains', 'combined: variety'])
        with tempfile.TemporaryDirectory() as directory:
            stream = io.StringIO()
            with patch.object(trial, 'build_report', return_value=result) as build, redirect_stdout(stream):
                self.assertEqual(trial.main(['--coverage', '--output', str(Path(directory) / 'coverage.json')]), 1)
                build.assert_called_once_with(True)
            self.assertIn('combined: variety', stream.getvalue())


if __name__ == '__main__':
    unittest.main()
