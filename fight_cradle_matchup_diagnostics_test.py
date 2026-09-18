"""Schedule and observation invariants for supplementary natural matchups."""
import unittest
from unittest.mock import patch

from analysis.cradle_matchup_diagnostics import ARMS, fixture_schedule, observations, build_report


class CradleMatchupTests(unittest.TestCase):
    def test_fixed_full_schedule(self):
        schedule = fixture_schedule()
        self.assertEqual(len(schedule), 240)
        self.assertEqual(len({row['seed'] for row in schedule}), 240)
        self.assertEqual(len({row['spec_id'] for row in schedule}), 12)
        self.assertEqual({row['level'] for row in schedule}, {55, 70, 85})
        self.assertTrue(all(row['a_style'] == 'Catch Wrestler' and row['a_behaviour'] == 'Control'
                            and row['fight'] == dict(title=False, main=False) for row in schedule))
        self.assertEqual(schedule, fixture_schedule())

    def test_default_observation_does_not_call_candidate_validator(self):
        with patch('analysis.cradle_matchup_diagnostics.validate_cradle_setups', side_effect=AssertionError('default validator')):
            counts, examples = observations(dict(trace=[]), False)
        self.assertEqual(counts, dict(roots=0, used=0, named=0, invalid=0))
        self.assertEqual(examples, [])
        with self.assertRaises(AssertionError):
            observations(dict(trace=[dict(move_id='catch_cradle_neck_crank_finisher')]), False)

    def test_reconciliation_rejects_missing_and_invalid_provenance(self):
        with self.assertRaises(AssertionError):
            observations(dict(trace=[dict(type='exchange', move_id='catch_cradle_neck_crank_finisher')]), True)
        with patch('analysis.cradle_matchup_diagnostics.validate_cradle_setups',
                   return_value=dict(roots=0, used=1, named=0, invalid=0)):
            with self.assertRaises(AssertionError):
                observations(dict(trace=[]), True)

    def test_real_default_and_enabled_prefix_reconcile(self):
        report = build_report(fights=1)
        self.assertIn('not canonical', report['scope'])
        self.assertEqual(report['fights_per_arm'], 1)
        for arm in ARMS:
            row = report['arms'][arm]
            self.assertEqual(sum(row['methods'].values()), 1)
            self.assertEqual(len(row['bouts']), 1)
            self.assertEqual(row['counts'], row['bouts'][0]['counts'])
            self.assertEqual(row['counts']['invalid'], 0)
        self.assertEqual(report['arms'][ARMS[0]]['bouts'][0]['input_sha256'],
                         report['arms'][ARMS[1]]['bouts'][0]['input_sha256'])


if __name__ == '__main__':
    unittest.main()
