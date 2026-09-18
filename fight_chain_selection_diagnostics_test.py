"""Actual-call instrumentation must not alter the bout it explains."""
import unittest
import tempfile
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch

from analysis.chain_selection_diagnostics import build_report, classify, inspect_decisions
from fight_chain_opportunity_regression_test import event


class ChainSelectionTests(unittest.TestCase):
    def test_mount_refinement_observer_keeps_bout_parity_and_explicit_scope(self):
        report = build_report(2, gift_wrap_mount=True)
        self.assertTrue(report['gift_wrap_mount'])
        self.assertTrue(report['all_bout_parity'])
        self.assertIn('analysis/gift_wrap_mount_candidate.py', report['source_sha256'])
        self.assertEqual(report['attempted_roots'], sum(report['stages'].values()))

    def test_complete_bout_parity_and_nonempty_observations(self):
        report = build_report(2)
        self.assertTrue(report['all_bout_parity'])
        self.assertEqual(report['attempted_roots'], sum(report['stages'].values()))
        self.assertGreater(report['details'].get('positive_preview_but_other_action_chosen', 0), 0)
        self.assertEqual(len(report['bouts']), 2)

    def test_classifier_stages(self):
        row = dict(selector_chain=dict(occurrence_id='root', branch_options=['follow']),
                   context_candidate_ids=['follow'], chain_candidates=['follow'],
                   eligible_ids=['follow'], pool=['follow'], selected_move='follow', pool_kind='chain')
        self.assertEqual(classify(row, 'root'), 'successor_selected_without_recorded_completion')
        cases = [({'selected_move': 'other'}, 'successor_in_pool_but_other_move_selected'),
                 ({'pool': ['other'], 'pool_kind': 'authored'}, 'eligible_successors_excluded_by_authored'),
                 ({'eligible_ids': []}, 'successors_rejected_before_final_pool'),
                 ({'chain_candidates': []}, 'context_successors_absent_from_live_chain_pool'),
                 ({'static_rejected_ids': ['follow']}, 'all_context_successors_static_rejected'),
                 ({'rarity_rejected_ids': ['follow']}, 'all_context_successors_static_or_rarity_rejected'),
                 ({'chosen_action': 'submission', 'resolved_technique': {'name': 'Unmapped diagnostic hold'}},
                  'resolved_hold_incompatible_with_successors'),
                 ({'context_candidate_ids': []}, 'no_context_compatible_successor'),
                 ({'selector_chain': {}}, 'root_changed_or_cleared_before_named_selection')]
        for updates, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(classify(dict(row, **updates), 'root'), expected)
        self.assertEqual(classify(dict(row, chosen_action='jab', resolved_technique={}), 'root'),
                         'successor_selected_without_recorded_completion')

    def test_missing_observations_fail_and_trace_is_not_mutated(self):
        root = event(1, 'single_jab', occurrence='root')
        root['move'] = {'follow_up_ids': ['double_jab']}
        following = event(2, 'kick', continuation=False)
        trace = [root, following, event(1, round_no=2, continuation=False)]
        before = deepcopy(trace)
        with self.assertRaisesRegex(ValueError, 'Missing'):
            inspect_decisions(trace, {})
        self.assertEqual(trace, before)

    def test_source_change_rejected(self):
        from analysis.chain_selection_diagnostics import fingerprints
        original = fingerprints()
        with patch('analysis.chain_selection_diagnostics.fingerprints', side_effect=[original, {}]):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                build_report(1)

    def test_invalid_count_rejected(self):
        for count in (0, -1, True):
            with self.assertRaises(ValueError):
                build_report(count)

    def test_existing_output_is_never_replaced(self):
        from analysis.chain_selection_diagnostics import main
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'existing.json'
            target.touch()
            with patch('sys.argv', ['diagnostic', '--output', str(target)]), \
                    patch('analysis.chain_selection_diagnostics.build_report') as collect:
                with self.assertRaises(FileExistsError):
                    main()
                collect.assert_not_called()
            self.assertEqual(target.read_bytes(), b'')


if __name__ == '__main__':
    unittest.main()
