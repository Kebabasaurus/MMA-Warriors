"""Real Tk archive checks: readable navigation without transcript mutations."""
from copy import deepcopy
import random
import tkinter as tk
import unittest

from events import EventMixin
from fight_night_archive import build_event_archive


class ArchiveHost(EventMixin):
    def __init__(self, root):
        self.root = root
        self.rules = {'fight_commentary_mode': 'Detailed'}
        self.colors = dict(chrome='#171c24', panel_dark='#202833', tree='#171c24',
            cream='#10151b', text='#edf1f4', gold='#e7bc64', muted='#a7b2bd',
            red='#a92e36', line='#394451')

    def create_managed_window(self):
        return tk.Toplevel(self.root)

    @staticmethod
    def display_fighter_names_in_text(value, log):
        return value.replace('Red [internal]', 'Red')


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = ArchiveHost(self.root)
        self.heading = 'BOUT 1: ' + 'A very long fighter name versus another complete fighter name ' * 3
        self.lines = ['Round 1: Start', '  [4:52] Red [internal] lands a jab. [target head]',
                      'Official scorecards:', 'Judge 1 [Measured]: 30-27 Red',
                      'Result: Red wins by decision']
        self.package = {'log': ['The complete event report'], 'preparation_timeline': {
            'stage_states': [
                {'stage_id': 'press', 'label': 'Press conference', 'status': 'Recorded', 'detail': '1 stored line(s).'},
            ],
            'press_outcomes': ['PRESS CONFERENCE', 'Asha Vale stays composed.'],
            'weigh_in_outcomes': [], 'campaign_evidence': [],
        }, 'fight_logs': [{
            'heading': self.heading, 'a': 'Red', 'b': 'Blue', 'lines': ['compact'],
            'detailed_lines': self.lines, 'round_analysis': [{'round': 1, 'corners': {
                'a': {'effective': 2, 'attempts': 4, 'moves': {'jab': 2}},
                'b': {'effective': 1, 'attempts': 3}}, 'plan_changes': [], 'stance_switches': []}]}]}
        self.before = deepcopy(self.package)
        self.rng = random.getstate()
        self.window = build_event_archive(self.app, 'Saved event', self.package)
        self.widgets = self.window._fight_archive_widgets
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def select_bout(self):
        self.widgets['fight_list'].selection_set(0)
        self.widgets['show_selected']()

    def test_complete_names_readonly_scrollable_transcript_and_no_mutation(self):
        self.assertEqual(self.widgets['fight_list'].get(0), '1. ' + self.heading)
        self.select_bout()
        expected = '\n'.join(line.replace('Red [internal]', 'Red') for line in self.lines) + '\n'
        self.assertEqual(self.widgets['text'].get('1.0', 'end-1c'), expected)
        self.assertEqual(self.widgets['text'].cget('state'), 'disabled')
        self.widgets['text'].insert('end', 'unwanted edit')
        self.assertEqual(self.widgets['text'].get('1.0', 'end-1c'), expected)
        self.assertTrue(self.widgets['text'].cget('yscrollcommand'))
        self.assertTrue(self.widgets['fight_list'].cget('xscrollcommand'))
        self.assertEqual(self.package, self.before)
        self.assertEqual(random.getstate(), self.rng)

    def test_round_selection_retains_bout_and_full_analysis(self):
        self.select_bout()
        self.widgets['sidebar'].select(1)
        self.widgets['round_list'].selection_set(0)
        self.widgets['round_list'].focus_set()
        self.root.update()
        self.assertEqual(self.widgets['fight_list'].curselection(), (0,))
        self.assertFalse(self.widgets['fight_list'].cget('exportselection'))
        self.assertFalse(self.widgets['round_list'].cget('exportselection'))
        self.widgets['show_round']()
        log = self.package['fight_logs'][0]
        self.assertEqual(self.widgets['text'].get('1.0', 'end-1c'),
                         self.app.format_round_analysis(log['round_analysis'][0], log) + '\n')
        self.widgets['mode'].set('Broadcast')
        self.widgets['show_selected']()
        self.assertEqual(self.widgets['text'].cget('state'), 'disabled')
        self.assertEqual(self.package, self.before)
        self.assertEqual(random.getstate(), self.rng)

    def test_preparation_tab_reads_stored_outcome_without_mutation(self):
        self.widgets['preparation_list'].selection_set(0)
        self.widgets['show_preparation']()
        self.assertIn('PRESS CONFERENCE', self.widgets['text'].get('1.0', 'end-1c'))
        self.assertIn('Asha Vale stays composed.', self.widgets['text'].get('1.0', 'end-1c'))
        self.assertEqual(self.widgets['text'].cget('state'), 'disabled')
        self.assertEqual(self.package, self.before)
        self.assertEqual(random.getstate(), self.rng)

    def test_legacy_package_exposes_unavailable_preparation_state(self):
        legacy = {'log': ['Legacy event summary'], 'fight_logs': []}
        window = build_event_archive(self.app, 'Legacy event', legacy)
        widgets = window._fight_archive_widgets
        self.root.update()
        self.assertEqual(widgets['preparation_list'].get(0), 'Unavailable: no preparation timeline retained')
        widgets['preparation_list'].selection_set(0)
        widgets['show_preparation']()
        self.assertIn('Preparation evidence is not available for this legacy archive.',
                      widgets['text'].get('1.0', 'end-1c'))
        self.assertEqual(widgets['text'].cget('state'), 'disabled')
        window.destroy()
        self.assertEqual(legacy, {'log': ['Legacy event summary'], 'fight_logs': []})
        self.assertEqual(random.getstate(), self.rng)

    def test_compact_window_keeps_controls_and_reading_area(self):
        self.window.geometry('820x540')
        self.root.update()
        text = self.widgets['text']
        self.assertGreater(text.winfo_height(), 230)
        self.assertGreater(text.winfo_width(), 350)
        self.assertTrue(self.widgets['mode_box'].winfo_ismapped())
        self.assertLess(self.widgets['mode_box'].winfo_rootx() + self.widgets['mode_box'].winfo_width(),
                        self.window.winfo_rootx() + self.window.winfo_width())


if __name__ == '__main__':
    unittest.main()
