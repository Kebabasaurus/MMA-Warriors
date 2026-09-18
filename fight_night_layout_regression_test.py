"""Real Tk geometry and observational telemetry for the Fight Night layout."""
from copy import deepcopy
import random
import tkinter as tk
from tkinter import ttk
import unittest

from fight_night_layout import build_fight_night_layout
from events import EventMixin
from ui import UIMixin


class LayoutHost(UIMixin):
    def __init__(self, root, theme):
        self.root = root
        self.theme_name = theme
        self.configure_style()

    def _sort_unregistered_treeview_heading(self, _event):
        pass


class LiveLayoutHost(LayoutHost, EventMixin):
    def __init__(self, root, theme):
        super().__init__(root, theme)
        self.rules = {'fight_commentary_mode': 'Detailed', 'round_length': 5}

    def ensure_audio_defaults(self):
        pass

    def fight_night_audio_volume(self):
        return 0

    def set_fight_night_audio_volume(self, value):
        return 0

    def start_fight_night_audio_session(self):
        pass

    def stop_fight_night_audio_session(self):
        pass

    @staticmethod
    def display_fighter_names_in_text(value, _log):
        return value

    @staticmethod
    def display_fighter_name_value(value):
        return value

    @staticmethod
    def result_fighter(*_args):
        return None

    @staticmethod
    def fight_night_local_crowd_profile(*_args):
        return {'gain': 1.0}

    @staticmethod
    def play_fight_night_sound(*_args):
        pass

    @staticmethod
    def fight_night_decision_reaction(_cards):
        return 'decision'


class FightNightLayoutTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.windows = []
        self.callback_errors = []
        self.root.report_callback_exception = lambda *error: self.callback_errors.append(error)

    def tearDown(self):
        self.root.destroy()

    def layout(self, width, height, theme='Fight Night'):
        host = LayoutHost(self.root, theme)
        window = tk.Toplevel(self.root)
        self.windows.append(window)
        window.geometry(f'{width}x{height}+0+0')
        window.configure(bg=host.colors['chrome'])
        widgets = build_fight_night_layout(host, window, width, height)
        # The builder reserves these rows; populate representative actual controls
        # so the geometry assertion includes playback and expanded settings.
        for title in ('Play Fight', 'Pause', 'Next Round', 'Skip Fight'):
            ttk.Button(widgets.controls, text=title).pack(side='left', padx=4)
        ttk.Label(widgets.controls2, text='Slower   Faster   Beat pace (ms)   1600').pack(side='left')
        ttk.Label(widgets.reading_controls, text='Text -   Text +   Follow live   Commentary   Detailed').pack(side='left')
        ttk.Label(widgets.audio_controls, text='Broadcast audio   50%').pack(side='left')
        self.root.update()
        return host, window, widgets

    def test_compact_and_large_palettes_have_reading_space(self):
        for theme in ('Fight Night', 'Light Office', 'UFC', 'Muay Thai'):
            for width, height, portrait in ((820, 540, 104), (1360, 900, 136)):
                with self.subTest(theme=theme, size=(width, height)):
                    host, window, widgets = self.layout(width, height, theme)
                    self.assertEqual(widgets.left_portrait.cget('width'), str(portrait))
                    self.assertGreaterEqual(widgets.left_portrait.winfo_width(), portrait)
                    self.assertGreaterEqual(widgets.right_portrait.winfo_height(), portrait)
                    self.assertGreaterEqual(widgets.text.winfo_height(), 150)
                    self.assertGreaterEqual(widgets.text.winfo_width(), 330)
                    self.assertFalse(widgets.controls2.winfo_ismapped())
                    widgets.settings_button.invoke()
                    self.root.update()
                    self.assertTrue(widgets.controls2.winfo_ismapped())
                    self.assertGreaterEqual(widgets.text.winfo_height(), 150)
                    self.assertLessEqual(widgets.audio_controls.winfo_rooty() + widgets.audio_controls.winfo_height(),
                                         window.winfo_rooty() + window.winfo_height())
                    widgets.settings_button.invoke()
                    self.root.update()
                    self.assertFalse(widgets.controls2.winfo_ismapped())
                    window.destroy()
        self.assertEqual(self.callback_errors, [])

    def test_long_names_are_complete_and_wrap(self):
        _host, window, widgets = self.layout(820, 540)
        name = 'Alexandre Maximiliano de Albuquerque'
        for label in (widgets.left_name, widgets.right_name):
            label.configure(text=name)
        self.root.update()
        for label in (widgets.left_name, widgets.right_name):
            self.assertEqual(label.cget('text'), name)
            self.assertGreater(int(label.cget('wraplength')), 0)
            self.assertLessEqual(int(label.cget('wraplength')), label.winfo_width())
            self.assertGreater(label.winfo_height(), 24)
            self.assertGreaterEqual(label.winfo_height(), label.winfo_reqheight())
        self.assertGreaterEqual(widgets.text.winfo_height(), 150)
        self.assertEqual(self.callback_errors, [])

    def test_live_theme_switch_updates_semantic_tree_tags(self):
        host, window, _widgets = self.layout(820, 540, "Fight Night")
        tree = ttk.Treeview(window, columns=("status",), show="headings")
        tree.heading("status", text="Status")
        tree.tag_configure("win", foreground="#9de6a0")
        tree.tag_configure("eligible", background="#173d2b", foreground="#a8f0bd")
        tree.pack(fill="x", padx=8, pady=4)
        text = tk.Text(window)
        text.tag_configure("urgent", foreground="#ff9b9b")
        text.pack(fill="x", padx=8, pady=4)
        host.colors = host.themes["Light Office"]
        host.retheme_plain_widgets(self.root)
        self.assertEqual(str(tree.tag_configure("win", "foreground")), "#176b3a")
        eligible_fg = str(tree.tag_configure("eligible", "foreground"))
        eligible_bg = str(tree.tag_configure("eligible", "background"))
        self.assertGreaterEqual(host.wcag_contrast_ratio(eligible_fg, eligible_bg), 4.5)
        self.assertEqual(str(text.tag_cget("urgent", "foreground")), "#9f1f2d")
        self.assertEqual(self.callback_errors, [])

    def test_round_read_only_renders_supplied_telemetry(self):
        _host, window, widgets = self.layout(820, 540)
        values = {'a': {'impact': 12, 'control': 8, 'danger': 0},
                  'b': {'impact': 6, 'control': 2, 'danger': 0}}
        before = deepcopy(values)
        rng = random.getstate()
        widgets.update_round_read(values, ('Red name', 'Blue name'))
        widgets.sidebar.select(1)
        self.root.update()
        strings = [widgets.round_bars.itemcget(item, 'text') for item in widgets.round_bars.find_all()
                   if widgets.round_bars.type(item) == 'text']
        self.assertEqual(len(strings), 3)
        self.assertTrue(any('12' in value and '6' in value for value in strings))
        self.assertFalse(any('judge' in value.lower() or 'winner' in value.lower() for value in strings))
        self.assertEqual(values, before)
        self.assertEqual(random.getstate(), rng)
        self.assertEqual(self.callback_errors, [])

    def test_round_and_bout_readers_scroll_from_hovered_content(self):
        _host, window, widgets = self.layout(820, 540)
        # Make both canvas-backed readers genuinely taller than their viewport.
        widgets.round_read_label.configure(text="Round detail\n" * 120)
        widgets.current_moment_label.configure(text="Bout desk note\n" * 120)
        self.root.update()

        for tab_index, label_widget in ((1, widgets.round_read_label), (2, widgets.current_moment_label)):
            widgets.sidebar.select(tab_index)
            self.root.update()
            page = self.root.nametowidget(widgets.sidebar.tabs()[tab_index])
            canvas = next(child for child in page.winfo_children() if isinstance(child, tk.Canvas))
            before = canvas.yview()
            label_widget.event_generate('<MouseWheel>', delta=-120)
            self.root.update()
            self.assertNotEqual(canvas.yview(), before)
        self.assertEqual(self.callback_errors, [])

    def test_full_live_window_initialization_and_settings(self):
        host = LiveLayoutHost(self.root, 'Fight Night')
        package = {'log': [], 'fight_logs': [{'heading': 'BOUT 1: Red vs Blue',
            'a': 'Red', 'b': 'Blue', 'lines': ['Round 1: Start', 'Result: Red wins'],
            'round_analysis': []}]}
        original = deepcopy(package)
        rng = random.getstate()
        window = host.open_live_fight_window({'name': 'Layout fixture'}, package, apply_results=False)
        self.root.update()
        widgets = window._fight_night_widgets
        widgets['settings_button'].invoke()
        self.root.update()
        self.assertTrue(widgets['reading_controls'].winfo_ismapped())
        widgets['settings_button'].invoke()
        self.root.update()
        self.assertFalse(widgets['reading_controls'].winfo_ismapped())
        self.assertEqual(package, original)
        self.assertEqual(random.getstate(), rng)
        self.assertEqual(self.callback_errors, [])
        window.destroy()

    def test_prerecorded_playback_seals_scores_and_density_frontier(self):
        host = LiveLayoutHost(self.root, 'Fight Night')
        lines = ['Round 1: Fighters meet at centre.',
            '  [4:52] Red lands the single jab.',
            'Round 1 summary: Broadcast read - Red leads. Metrics - Red: impact 12, control 8, danger 2; Blue: impact 6, control 2, danger 0. Gas: Red 80, Blue 75. Momentum: Red.',
            'Official scorecards:', 'Judge 1 [Measured]: 30-27 Red',
            'Result: Red def. Blue by Decision R3']
        package = {'log': [], 'fight_logs': [{'heading': 'BOUT 1: Red vs Blue',
            'a': 'Red', 'b': 'Blue', 'lines': lines,
            'result': 'Red def. Blue by Decision R3', 'round_analysis': []}]}
        original = deepcopy(package)
        rng = random.getstate()
        window = host.open_live_fight_window({'name': 'Playback fixture'}, package, apply_results=False)
        window.geometry('820x540')
        self.root.update()
        widgets = window._fight_night_widgets
        state = window._fight_night_state
        def button(title):
            found = [item for item in widgets['controls'].winfo_children()
                     if isinstance(item, ttk.Button) and item.cget('text') == title]
            self.assertEqual(len(found), 1, title)
            return found[0]
        def step():
            button('Play Fight').invoke()
            if state['running']:
                button('Pause').invoke()
            self.root.update()
            self.assertEqual(self.callback_errors, [])
        button('Next Fight').invoke()
        self.root.update()
        self.assertEqual(self.callback_errors, [])
        compact_reader_height = widgets['text'].winfo_height()
        self.assertGreaterEqual(widgets['text'].winfo_width(), 330)
        self.assertEqual(state.get('round_values'), {})
        step()
        step()
        self.assertIn('Red lands the single jab.', widgets['text'].get('1.0', 'end'))
        self.assertEqual(state.get('round_values'), {})
        mode_box = next(item for item in widgets['reading_controls'].winfo_children()
                        if isinstance(item, ttk.Combobox))
        for mode in ('Broadcast', 'Detailed'):
            mode_box.set(mode)
            mode_box.event_generate('<<ComboboxSelected>>')
            self.root.update()
            self.assertNotIn('Result: Red', widgets['text'].get('1.0', 'end'))
            self.assertNotIn('30-27', widgets['text'].get('1.0', 'end'))
            self.assertEqual(state.get('round_values'), {})
        step()
        self.assertEqual(state['round_values']['a']['impact'], 12)
        self.assertEqual(state['round_values']['b']['control'], 2)
        self.assertTrue(widgets['round_bars'].find_all())
        step()
        step()
        self.assertNotIn('30-27', widgets['text'].get('1.0', 'end'))
        self.assertTrue(state['holding_scorecards'])
        step()
        rendered = widgets['text'].get('1.0', 'end')
        self.assertIn('Result: Red def. Blue', rendered)
        self.assertIn('30-27 Red', rendered)
        self.assertFalse(state['holding_scorecards'])
        self.assertLess(rendered.index('Result: Red def.'), rendered.index('30-27 Red'))
        self.assertEqual(package, original)
        self.assertEqual(random.getstate(), rng)
        self.assertEqual(self.callback_errors, [])
        self.assertGreaterEqual(compact_reader_height, 150)
        window.destroy()


if __name__ == '__main__':
    unittest.main()
