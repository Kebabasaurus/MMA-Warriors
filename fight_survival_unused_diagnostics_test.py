"""Observation/restoration contracts for the current-440 frequency wrapper."""
import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch

from analysis import survival_unused_diagnostics as diagnostic


class SurvivalUnusedDiagnosticsTests(unittest.TestCase):
    def test_real_bout_inventory_hash_and_parity(self):
        context = diagnostic.observer.candidate_context
        select = diagnostic.observer.RepertoireHarness.select_exchange_move
        report = diagnostic.build_report(1)
        with context(entries=True, chains=True, draft_content=True, gift_wrap_mount=True,
                     standing_head_damage=True, kick_power=True, heel_hook_identity=True,
                     hold_transitions=True, cradle_setup=True, survival_expansion=True) as definitions:
            active = {move.move_id for move in definitions if not move.deprecated}
        self.assertEqual(len(active), 440)
        self.assertTrue(active.issubset({row['move_id'] for row in report['move_counts']}))
        self.assertTrue(report['all_bout_parity'])
        self.assertEqual(len(report['bouts']), 1)
        expected = diagnostic.hashlib.sha256(Path(diagnostic.__file__).read_bytes()).hexdigest()
        self.assertEqual(report['source_sha256']['analysis/survival_unused_diagnostics.py'], expected)
        self.assertIs(diagnostic.observer.candidate_context, context)
        self.assertIs(diagnostic.observer.RepertoireHarness.select_exchange_move, select)

    def test_existing_output_is_rejected_before_simulation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'existing.json'
            output.write_text('historical', encoding='utf-8')
            with patch.object(diagnostic.sys, 'argv', ['diagnostic', '--output', str(output)]), \
                    patch.object(diagnostic, 'build_report') as build:
                with self.assertRaises(FileExistsError):
                    diagnostic.main()
                build.assert_not_called()
            self.assertEqual(output.read_text(encoding='utf-8'), 'historical')

    def test_observes_explicit_hold_without_reselecting(self):
        original_context = diagnostic.observer.candidate_context
        calls = []
        sentinel = object()

        def select(*args, **kwargs):
            calls.append(kwargs)
            return sentinel

        def collect(fights, retained_damage):
            self.assertEqual((fights, retained_damage), (300, True))
            engine = diagnostic.observer.RepertoireHarness()
            engine.fighter_styles = lambda actor: ('BJJ',)
            result = engine.select_exchange_move(None, None, 'bottom_submission', 'guard',
                                                  'body', {}, resolved_technique={'name': 'armbar'})
            self.assertIs(result, sentinel)
            return dict(source_sha256={}, scope='test', observations=[], bouts=[],
                        move_counts=[], all_bout_parity=True)

        with patch.object(diagnostic.observer.RepertoireHarness, 'select_exchange_move', select), \
                patch.object(diagnostic.observer, 'build_report', collect):
            report = diagnostic.build_report()
            self.assertIs(diagnostic.observer.RepertoireHarness.select_exchange_move, select)
        self.assertIs(diagnostic.observer.candidate_context, original_context)
        self.assertEqual(len(calls), 1)
        self.assertEqual(report['resolved_hold_contexts'][0]['hold'], 'armbar')
        self.assertIn('analysis/survival_unused_diagnostics.py', report['source_sha256'])

    def test_restores_observer_after_collection_error(self):
        context = diagnostic.observer.candidate_context
        select = diagnostic.observer.RepertoireHarness.select_exchange_move
        with patch.object(diagnostic.observer, 'build_report', side_effect=RuntimeError('test')):
            with self.assertRaisesRegex(RuntimeError, 'test'):
                diagnostic.build_report()
        self.assertIs(diagnostic.observer.candidate_context, context)
        self.assertIs(diagnostic.observer.RepertoireHarness.select_exchange_move, select)


if __name__ == '__main__':
    unittest.main()
