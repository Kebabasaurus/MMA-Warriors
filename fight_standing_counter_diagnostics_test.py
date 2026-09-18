"""Counter-age observation preserves complete bouts and counts calls honestly."""
from collections import Counter
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from analysis import standing_counter_diagnostics as diagnostic


class StandingCounterDiagnosticsTests(unittest.TestCase):
    def test_age_owner_readiness_boundaries_and_partition(self):
        engine = diagnostic.paired.FightAuditHarness()
        engine._experimental_chain_action_weighting = True
        a, b = SimpleNamespace(name='a', toughness=100), SimpleNamespace(name='b', toughness=100)
        state = dict(position='range', round=2, tick=5, gas={'a': 60}, hurt={'a': 0})
        counts = Counter()
        for window, expected in ((None, ('no_window', 'no_window')),
                ({'fighter': 'a', 'created_round': 2, 'created_tick': 3}, ('own', 'same_round_age_0_to_2')),
                ({'fighter': 'b', 'created_round': 2, 'created_tick': 2}, ('opponent', 'same_round_age_gt_2')),
                ({'fighter': 'b', 'created_round': 1, 'created_tick': 20}, ('opponent', 'previous_round')),
                ({'fighter': 'b', 'created_round': 3, 'created_tick': 1}, ('opponent', 'future_metadata')),
                ({'fighter': 'b', 'created_round': 2, 'created_tick': 6}, ('opponent', 'future_metadata')),
                ({'fighter': 'b', 'created_round': 2}, ('opponent', 'unknown')),
                ({'fighter': 'b', 'created_round': True, 'created_tick': 1}, ('opponent', 'unknown')),
                ({'fighter': 'missing', 'created_round': 2, 'created_tick': 2}, ('unknown', 'same_round_age_gt_2'))):
            state['counter_window'] = window
            before, rng = deepcopy(state), random.getstate()
            result = diagnostic.classify_call(engine, a, b, state)
            self.assertEqual(result[1:3], expected)
            self.assertEqual(state, before)
            self.assertEqual(random.getstate(), rng)
            counts[result] += 1
        summary = diagnostic.summarize(counts)
        self.assertEqual(summary['initiative_calls'], 9)
        self.assertEqual(sum(row['initiative_calls'] for row in summary['observations']), 9)
        self.assertEqual(summary['stale_opponent_guard_calls'], 2)
        self.assertEqual(summary['otherwise_ready_stale_guard_calls'], 2)
        state['counter_window'] = dict(fighter='b', created_round=2, created_tick=2)
        for position, enabled, gas, hurt, guard, ready in (
                ('pocket', True, 22, 0, True, False), ('range', True, 22.01, 65, True, True),
                ('range', True, 60, 65.01, True, False), ('range', True, None, 0, True, False),
                ('range', False, 60, 0, False, False), ('cage', True, 60, 0, False, False)):
            state.update(position=position, gas={'a': gas}, hurt={'a': hurt})
            engine._experimental_chain_action_weighting = enabled
            self.assertEqual(diagnostic.classify_call(engine, a, b, state)[3:], (guard, ready))

    def test_wrapper_single_call_nested_error_and_instance_rng_restoration(self):
        engine = diagnostic.paired.FightAuditHarness()
        a, b = SimpleNamespace(name='a', toughness=100), SimpleNamespace(name='b', toughness=100)
        state = dict(position='range', round=1, tick=1)
        original, rng = engine.initiative, random.getstate()
        calls = []
        def resolve(*args):
            calls.append(args)
            random.random()
            raise RuntimeError('initiative failed')
        with patch.object(engine, 'initiative', resolve):
            outer_counts, inner_counts = Counter(), Counter()
            with diagnostic.observe_initiative(engine, outer_counts):
                outer = engine.initiative
                with self.assertRaisesRegex(RuntimeError, 'initiative failed'):
                    with diagnostic.observe_initiative(engine, inner_counts):
                        engine.initiative(a, b, state)
                self.assertIs(engine.initiative, outer)
            self.assertIs(engine.initiative, resolve)
        self.assertEqual(engine.initiative, original)
        self.assertNotIn('initiative', vars(engine))
        self.assertEqual(len(calls), 1)
        self.assertEqual(sum(outer_counts.values()), 1)
        self.assertEqual(inner_counts, outer_counts)
        self.assertEqual(random.getstate(), rng)

    def test_complete_bout_result_trace_rng_and_registry_parity_both_arms(self):
        import fight_moves
        paired = diagnostic.paired
        rng, registry = random.getstate(), fight_moves.MOVE_DEFINITIONS
        rows = paired.fixture_schedule(2)
        report = diagnostic.build_report(2)
        for name, enabled in (('current_normal', False), ('combined_candidate', True)):
            with paired.candidate_context(entries=enabled, chains=enabled, draft_content=enabled):
                engine = paired.FightAuditHarness()
                for index, row in enumerate(rows):
                    spec = row['spec']
                    a = paired.synthetic_fighter(row['a_name'], spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
                    b = paired.synthetic_fighter(row['b_name'], spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
                    a.stance, b.stance = spec.get('a_stance', a.stance), spec.get('b_stance', b.stance)
                    before = deepcopy((vars(a), vars(b), spec))
                    audit = paired.run_audited_fight(engine, a, b, row['seed'], spec['fight'])
                    recorded = report['arms'][name]['bouts'][index]
                    self.assertEqual(recorded['audit_sha256'], paired.digest(audit))
                    self.assertEqual(recorded['trace_sha256'], paired.digest(audit['trace']))
                    exchanges = sum(event.get('type') == 'exchange' for event in audit['trace'])
                    self.assertEqual(recorded['initiative_calls'], exchanges * 2)
                    self.assertEqual(before, (vars(a), vars(b), spec))
            arm = report['arms'][name]
            self.assertEqual(arm['initiative_calls'], sum(bout['initiative_calls'] for bout in arm['bouts']))
            self.assertEqual(arm['initiative_calls'], sum(row['initiative_calls'] for row in arm['observations']))
        self.assertEqual(report, diagnostic.build_report(2))
        self.assertEqual(random.getstate(), rng)
        self.assertIs(fight_moves.MOVE_DEFINITIONS, registry)

    def test_invalid_count_source_change_and_exclusive_output(self):
        for count in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                diagnostic.build_report(count)
        rng = random.getstate()
        original, reads = Path.read_bytes, 0
        def changed(path):
            nonlocal reads
            data = original(path)
            if path == diagnostic.ROOT / 'fight_engine.py':
                reads += 1
                if reads > 1:
                    return data + b'changed'
            return data
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(RuntimeError, 'Source changed'):
                diagnostic.build_report(1)
        self.assertEqual(random.getstate(), rng)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'observations.json'
            with patch.object(diagnostic, 'build_report', return_value={'test': 1}) as build:
                with redirect_stdout(io.StringIO()):
                    diagnostic.main(['--fights', '2', '--output', str(output)])
                build.assert_called_once_with(2)
                with self.assertRaises(FileExistsError):
                    diagnostic.main(['--output', str(output)])
                build.assert_called_once()
            self.assertEqual(json.loads(output.read_text()), {'test': 1})


if __name__ == '__main__':
    unittest.main()
