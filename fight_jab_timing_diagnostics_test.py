"""Paired timing attribution preserves denominators, boundaries and source inputs."""
from copy import deepcopy
import random
import unittest

from analysis.jab_timing_diagnostics import timing, transitions, divergences, build_report, recheck_changed_outcomes


class JabTimingDiagnosticsTests(unittest.TestCase):
    def test_canonical_timing_boundaries_and_nonfinishes(self):
        for rounds, expected in ((3, ['Early', 'Middle', 'Late']),
                                 (5, ['Early', 'Middle', 'Middle', 'Late', 'Late'])):
            for round_no, label in enumerate(expected, 1):
                row = dict(method='KO', round=round_no, scheduled_rounds=rounds)
                self.assertEqual(timing(row), label)
                self.assertEqual(timing(dict(row, method='Decision')), 'Nonfinish')

    def test_transition_matrix_keeps_both_directions_and_new_finishes(self):
        rows = [dict(method='KO', round=i, scheduled_rounds=3) for i in (1, 2, 3)]
        rows.append(dict(method='Decision', round=3, scheduled_rounds=3))
        pairs = [dict(control=rows[a], jab=rows[b]) for a,b in ((0,1),(1,0),(3,1),(1,3),(2,1))]
        report = transitions(pairs)
        self.assertEqual(sum(r['bouts'] for r in report['timing']), 5)
        self.assertEqual(sum(r['bouts'] for r in report['methods']), 5)
        self.assertEqual(len(report['timing']), 5)

    def test_named_difference_is_not_mechanical_or_plan_difference(self):
        left = [dict(round=1, tick=1, actor='a', action='jab', move_id='single_jab',
                     plan='Balanced', outcome='landed')]
        right = [dict(left[0], move_id='pawing_jab')]
        before = deepcopy((left, right))
        result = divergences(left, right)
        self.assertEqual(set(result), {'named', 'named_window'})
        self.assertEqual((left, right), before)
        right.append(dict(right[0], tick=2))
        self.assertEqual(divergences(left, right)['trace_length'], {'control': 1, 'jab': 2})
        self.assertNotIn('mechanical_projection', divergences(left, right))

    def test_small_complete_bouts_reconcile_and_restore_rng(self):
        rng = random.getstate()
        report = build_report(coverage_fights=2)
        self.assertEqual(random.getstate(), rng)
        self.assertEqual(report['corpus'], 'coverage_diagnostic')
        for name in ('control', 'jab'):
            self.assertEqual(report['groups'][name]['Overall']['total'], 2)
        self.assertEqual(sum(r['bouts'] for r in report['all_bouts']['timing']), 2)
        self.assertEqual(len(report['paired_bouts']), 2)

    def test_trace_tails_are_not_plan_changes(self):
        row = dict(round=1, tick=1, actor='a', plan='Balanced', move_id='single_jab')
        result = divergences([row], [row, dict(row, tick=2)])
        self.assertNotIn('plan', result)
        self.assertEqual(result['trace_length'], {'control': 1, 'jab': 2})

    def test_plan_comparison_requires_same_actor_round_and_tick(self):
        a = dict(round=1, tick=1, actor='a', plan='Balanced')
        b = dict(a, actor='b', plan='Wrestle early')
        self.assertNotIn('plan', divergences([a], [b]))

    def test_projection_retains_the_triggering_fields(self):
        a = dict(round=1, tick=1, actor='a', hurt_delta={'a': 0, 'b': 0})
        b = dict(a, hurt_delta={'a': 0, 'b': 3})
        result = divergences([a], [b])['mechanical_projection']
        self.assertEqual(result['differing_fields'], ['hurt_delta'])
        self.assertEqual(result['control']['hurt_delta'], a['hurt_delta'])
        self.assertEqual(result['jab']['hurt_delta'], b['hurt_delta'])

    def test_recheck_rejects_short_parent_and_mechanical_source_changes(self):
        report = build_report(coverage_fights=2)
        with self.assertRaisesRegex(ValueError, 'complete calibration parent'):
            recheck_changed_outcomes(report)
        changed = deepcopy(report)
        changed['source_sha256']['fight_engine.py'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'mechanical sources differ'):
            recheck_changed_outcomes(changed)
        incomplete = dict(report, corpus='full_calibration', fights_per_arm=3840)
        with self.assertRaisesRegex(ValueError, 'Incomplete parent fixtures'):
            recheck_changed_outcomes(incomplete)


if __name__ == '__main__':
    unittest.main()
