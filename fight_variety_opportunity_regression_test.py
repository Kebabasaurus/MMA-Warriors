"""Fixed-pool bounds are exact, observational and retain both corner slots."""
from copy import deepcopy
from contextlib import redirect_stdout
import io
import itertools
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import fight_engine
import fight_moves
from analysis import generate_variety_opportunity_report as diagnostic
from analysis.fight_candidate_context import candidate_context
from analysis.compare_candidate_striking import fixture_schedule
from analysis.generate_variety_opportunity_report import (
    final_selection_pool, maximum_distinct_matching, inspect_bout, build_report,
    TerminalRngHarness, VarietyOpportunityHarness,
)
from fight_engine_audit import synthetic_fighter, run_audited_fight, FightAuditHarness


class VarietyOpportunityTests(unittest.TestCase):
    def test_source_changes_and_existing_outputs_are_rejected(self):
        with patch.object(diagnostic, 'source_fingerprints', side_effect=[{'source': 'old'}, {'source': 'new'}]):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                build_report(1)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'report.json'
            with patch.object(diagnostic, 'build_report', return_value={'evidence': True}) as build:
                with patch('sys.argv', ['diagnostic', '--output', str(output)]), redirect_stdout(io.StringIO()):
                    diagnostic.main()
                original = output.read_bytes()
                with patch('sys.argv', ['diagnostic', '--output', str(output)]):
                    with self.assertRaises(FileExistsError):
                        diagnostic.main()
                self.assertEqual(build.call_count, 1)
                self.assertEqual(output.read_bytes(), original)

    def test_matching_agrees_with_exhaustive_assignments(self):
        cases = ([], [[], []], [['a'], ['a']], [['a', 'b'], ['a'], ['b', 'c']],
                 [['a'], ['a'], ['b', 'c'], ['c', 'd']], [['a', 'b'], ['a', 'b']])
        for pools in cases:
            before = deepcopy(pools)
            alternatives = [pool or [None] for pool in pools]
            expected = max((len(set(choice) - {None}) for choice in itertools.product(*alternatives)), default=0)
            self.assertEqual(maximum_distinct_matching(pools), expected)
            self.assertEqual(pools, before)
        # Union size is three, but only two actual exchanges can expose IDs.
        self.assertEqual(maximum_distinct_matching([['a', 'b'], ['b', 'c']]), 2)

    def test_pool_counter_authored_top5_and_chain_priority(self):
        registry = fight_moves.MOVE_REGISTRY
        names = ('one_two', 'lead_hook_cross', 'rear_uppercut', 'corkscrew_cross', 'spinning_backfist', 'slip_cross')
        rows = [(100 - i, registry[name]) for i, name in enumerate(names)]
        before = list(rows)
        pool, kind = final_selection_pool(rows, False, set(), set(), {})
        self.assertEqual(pool, names[:5])
        self.assertEqual(kind, 'ordinary')
        self.assertEqual(final_selection_pool(rows, True, set(), set(), {}), (('slip_cross',), 'ordinary'))
        self.assertEqual(final_selection_pool(rows, False, {'one_two'}, {'rear_uppercut'}, {}),
                         (('one_two',), 'authored'))
        self.assertEqual(final_selection_pool(rows, False, set(), {'lead_hook_cross', 'rear_uppercut'},
                                               {'next_move_id': 'rear_uppercut'}), (('rear_uppercut',), 'chain'))
        self.assertEqual(final_selection_pool(rows, False, set(), {'slip_cross'}, {}), (names[:5], 'ordinary'))
        self.assertEqual(rows, before)
        engine = FightAuditHarness()
        # Match actual selector outcomes without changing its deterministic draw.
        for counter in (False, True):
            for target in ('head', 'body'):
                pool, _ = final_selection_pool(rows, counter, set(), set(), {})
                for tick in range(1, 12):
                    selected = engine._select_from_pool(list(rows), counter, set(), set(), {},
                                                         'test-identity', 'power_punch', 'range', target,
                                                         {'round': 1, 'tick': tick})
                    self.assertIn(selected.move_id, pool)

    def test_zero_fighters_unwrapped_singletons_and_bad_observations(self):
        identities = {'a': 'A', 'b': 'B'}
        empty = inspect_bout([], {}, identities)
        self.assertEqual(len(empty['fighters']), 2)
        self.assertTrue(all(row['selections'] == row['observed_pool_max_distinct'] == 0 for row in empty['fighters']))
        trace = [dict(type='exchange', actor='a', round=1, tick=1, move_id='generic_survive')]
        before = deepcopy(trace)
        report = inspect_bout(trace, {}, identities)
        self.assertEqual(report['unwrapped_singletons'], 1)
        self.assertEqual(report['singleton_move_counts'], {'generic_survive': 1})
        self.assertEqual(report['fighters'][1]['selections'], 0)
        self.assertEqual(trace, before)
        for pools in ({(1, 1, 'A'): ('invented',)}, {(1, 2, 'A'): ('generic_survive',)}):
            with self.assertRaises(ValueError):
                inspect_bout(trace, pools, identities)
        with self.assertRaises(ValueError):
            inspect_bout(trace + trace, {}, identities)

    def test_three_real_bouts_exact_audit_four_rngs_inputs_and_bindings(self):
        rng = random.getstate()
        registry = fight_moves.MOVE_REGISTRY
        engine_registry = fight_engine.MOVE_REGISTRY
        schedule = fixture_schedule(44)
        with candidate_context(entries=True, chains=True, draft_content=True):
            for index in (0, 20, 40):
                fixture = schedule[index]
                spec = fixture['spec']
                a = synthetic_fighter(fixture['a_name'], spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
                b = synthetic_fighter(fixture['b_name'], spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
                a.stance, b.stance = spec.get('a_stance', a.stance), spec.get('b_stance', b.stance)
                before = deepcopy((vars(a), vars(b), fixture))
                plain, probe = TerminalRngHarness(), VarietyOpportunityHarness()
                expected = run_audited_fight(plain, a, b, fixture['seed'], spec['fight'])
                actual = run_audited_fight(probe, a, b, fixture['seed'], spec['fight'])
                self.assertEqual(actual, expected)
                self.assertEqual(probe.terminal_rng_states, plain.terminal_rng_states)
                self.assertEqual((vars(a), vars(b), fixture), before)
                self.assertEqual(random.getstate(), rng)
                self.assertTrue(probe.observed_pools)
                report = inspect_bout(actual['trace'], probe.observed_pools,
                                      {'a': str(a.fighter_id), 'b': str(b.fighter_id)})
                self.assertEqual(len(report['fighters']), 2)
                # Per-bout observer reset, with identical replay evidence.
                again = run_audited_fight(probe, a, b, fixture['seed'], spec['fight'])
                self.assertEqual(again, actual)
        self.assertIs(fight_moves.MOVE_REGISTRY, registry)
        self.assertIs(fight_engine.MOVE_REGISTRY, engine_registry)
        self.assertEqual(random.getstate(), rng)

    def test_report_invalid_counts_and_exception_restore(self):
        for count in (None, 0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                build_report(count)
        rng, registry = random.getstate(), fight_moves.MOVE_REGISTRY
        def failure(*args, **kwargs):
            random.random()
            raise RuntimeError('injected')
        with patch('analysis.generate_variety_opportunity_report.run_audited_fight', side_effect=failure):
            with self.assertRaisesRegex(RuntimeError, 'injected'):
                build_report(1)
        self.assertEqual(random.getstate(), rng)
        self.assertIs(fight_moves.MOVE_REGISTRY, registry)

    def test_report_provenance_and_runtime_input_guard(self):
        report = build_report(1)
        self.assertEqual(report['fighter_count'], 2)
        self.assertFalse(report['acceptance_gate'])
        self.assertIn('NOT a universal', report['scope'])
        for source in ('constants.py', 'models.py', 'fight_moves/chains.py', 'fight_moves/index.py'):
            self.assertIn(source, report['source_sha256'])
        self.assertEqual(len(report['bouts']), 1)
        bout = report['bouts'][0]
        self.assertTrue(bout['inputs_unchanged'])
        self.assertEqual(len(bout['input_sha256']), 64)
        self.assertEqual(len(bout['trace_sha256']), 64)
        def mutate(engine, a, b, *args):
            a.momentum += 1
            return {'trace': []}
        with patch('analysis.generate_variety_opportunity_report.run_audited_fight', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'input mutated'):
                build_report(1)


if __name__ == '__main__':
    unittest.main()
