"""Reproducible source-only layout previews using synthetic, illustrative fighters."""
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import ImageGrab
from ui import UIMixin
from models import Fighter
from fighter_portraits import render_portrait
from fight_night_layout import build_fight_night_layout
from fight_night_presentation import configure_fight_timeline, insert_fight_timeline_line
from fight_night_layout_regression_test import LiveLayoutHost


class PreviewApp(UIMixin):
    def __init__(self, root, theme):
        self.root = root
        self.theme_name = theme
        self._treeview_sort_binding = True
        self.configure_style()


def preview(theme, width, height, output):
    root = tk.Tk()
    root.title('Fight Night — illustrative source preview')
    root.geometry(f'{width}x{height}+0+0')
    app = PreviewApp(root, theme)
    root.configure(bg=app.colors['chrome'])
    layout = build_fight_night_layout(app, root, width, height)
    fighters = [Fighter(name=name, weight='Lightweight', age=age, record_w=wins,
                        record_l=losses, striking=80, wrestling=76, grappling=79,
                        cardio=84, chin=78, popularity=73, momentum=2, morale=80,
                        purse=50000) for name, age, wins, losses in
                [('Alex Morgan', 29, 18, 3), ('Daniel Ferreira', 31, 22, 5)]]
    for side, fighter, gas, status in zip(('left', 'right'), fighters, (81, 73), ('CHAMPION', '#1 CONTENDER')):
        fighter.fighter_id = 'illustrative-preview-' + side
        portrait = getattr(layout, side + '_portrait')
        render_portrait(portrait, fighter, size=104 if height < 700 else 136)
        getattr(layout, side + '_name').configure(text=fighter.name)
        getattr(layout, side + '_ovr').configure(text=f'OVR {fighter.overall} • {fighter.record}')
        getattr(layout, side + '_title_status').configure(text=status)
        getattr(layout, side + '_condition').configure(text=f'Gas {gas}/100 • No medical concern')
        getattr(layout, side + '_gas').configure(value=gas)
    layout.phase_label.configure(text='ROUND 2')
    layout.clock_label.configure(text='03:42')
    layout.label_chip.configure(text='TITLE BOUT')
    for title in ('1  Morgan vs Ferreira — LIVE', '2  Torres vs Bennett', '3  Laurent vs Evans', '4  Park vs Silva'):
        layout.fight_list.insert('end', title)
    layout.fight_list.selection_set(0)
    layout.sidebar.select(1)
    layout.fight_read_label.configure(text='ROUND READ\nMorgan leads the impact exchanges. Ferreira has the greater control total.')
    layout.round_read_label.configure(text='Round 1\nMorgan: 14 impact • 8 control\nFerreira: 11 impact • 15 control\n\nTelemetry is not a judge score.')
    layout.score_label.configure(text='OFFICIAL JUDGES\nSealed until the result')
    layout.momentum_text.configure(text='Momentum: slight red-corner edge')
    layout.update_round_read({'a': {'impact': 21, 'control': 12, 'danger': 6}, 'b': {'impact': 15, 'control': 19, 'danger': 3}}, tuple(f.name for f in fighters))
    for i, fighter in enumerate(fighters):
        layout.live_stats.insert('', 'end', values=(fighter.name, 21-i*6, 12+i*7, 6-i*3, 81-i*8, '+2' if i == 0 else '−2'))
    configure_fight_timeline(layout.text, app.colors)
    for source in ('MAIN EVENT • LIGHTWEIGHT TITLE', 'Illustrative preview — synthetic fighters and sample commentary.',
                   'ROUND 2 — 5:00', '[05:00] Both fighters return to the centre of the cage.',
                   '[04:48] Morgan works behind a jab. Ferreira keeps his guard in place.',
                   '[04:31] Ferreira closes the distance and presses Morgan against the fence.',
                   'Corner read: Morgan’s corner asks for a turn off the fence.',
                   '[04:06] Morgan circles away. The fighters return to striking range.',
                   '[03:42] Ferreira checks the low kick and resets his stance.'):
        insert_fight_timeline_line(layout.text, source)
    for title in ('Start Next Fight', 'Play Fight', 'Pause', 'Next Round', 'Skip Fight'):
        ttk.Button(layout.controls, text=title).pack(side='left', padx=4)
    for title in ('Skip Event', 'Review Selected Bout'):
        ttk.Button(layout.controls3, text=title).pack(side='left', padx=4)
    ttk.Button(layout.controls3, text='Close').pack(side='right', padx=4)
    root.update()
    root.attributes('-topmost', True)
    root.lift()
    root.after(200, root.quit)
    root.mainloop()
    root.update()
    bounds = (root.winfo_rootx(), root.winfo_rooty(), root.winfo_rootx()+root.winfo_width(), root.winfo_rooty()+root.winfo_height())
    output.parent.mkdir(parents=True, exist_ok=True)
    ImageGrab.grab(bbox=bounds).save(output)
    print(theme, width, height, 'timeline height', layout.text.winfo_height(), 'portrait', layout.left_portrait.winfo_width(), output)
    root.destroy()


def integrated_preview(width, height, output):
    """Exercise the actual live window callbacks against a disposable package."""
    root = tk.Tk()
    root.withdraw()
    errors = []
    root.report_callback_exception = lambda *args: errors.append(args)

    class IntegratedHost(LiveLayoutHost):
        def result_fighter(self, name, *_args):
            return next((fighter for fighter in self.fighters if fighter.name == name), None)

        @staticmethod
        def fighter_display_name(fighter):
            return fighter.name

        @staticmethod
        def matchup_odds(*_args):
            return 'Even'

    host = IntegratedHost(root, 'Dark Mode')
    host.fighters = [Fighter(name=name, weight='Lightweight', age=29, record_w=18,
        record_l=3, striking=80, wrestling=76, grappling=79, cardio=84, chin=78,
        popularity=73, momentum=2, morale=80, purse=50000,
        fighter_id='illustrative-live-' + str(index)) for index, name in enumerate(('Alex Morgan', 'Daniel Ferreira'))]
    lines = ['Round 1: Fighters meet at centre.',
        '[04:48] Morgan lands a clean right hand through Ferreira\'s guard.',
        '[04:20] The latest exchange leaves visible reddening across Ferreira\'s face.',
        'Round 1 summary: Broadcast read - Morgan leads the impact exchanges. Metrics - Alex Morgan: impact 21, control 12, danger 6; Daniel Ferreira: impact 15, control 19, danger 3. Gas: Alex Morgan 81, Daniel Ferreira 73. Momentum: Alex Morgan.',
        'ROUND 2 — 5:00', '[04:31] Ferreira closes the distance.',
        'Result: Alex Morgan def. Daniel Ferreira by Decision R3']
    package = {'log': [], 'fight_logs': [{'heading': 'TITLE BOUT: Morgan vs Ferreira',
        'a': host.fighters[0].name, 'b': host.fighters[1].name,
        'a_record': '18-3-0', 'b_record': '22-5-0', 'a_rating': {'overall':79},
        'b_rating': {'overall':79}, 'a_title_status':'CHAMPION', 'b_title_status':'CONTENDER',
        'label':'TITLE BOUT', 'title':True, 'lines':lines, 'round_analysis':[]}]}
    window = host.open_live_fight_window({'name':'Illustrative Preview'}, package, apply_results=True)
    window.geometry(f'{width}x{height}+0+0')
    root.update()
    widgets = window._fight_night_widgets

    def button(title):
        return next(item for item in widgets['controls'].winfo_children()
                    if isinstance(item, ttk.Button) and item.cget('text') == title)

    button('Start Next Fight').invoke()
    for _ in range(4):
        button('Play Fight').invoke()
        button('Pause').invoke()
        root.update()
    assert not errors, errors
    assert not window._fight_night_state['result_shown']
    widgets['sidebar'].select(1)
    widgets['text'].see('end')
    window.attributes('-topmost', True)
    window.lift()
    root.update()
    root.after(200, root.quit)
    root.mainloop()
    bounds = (window.winfo_rootx(), window.winfo_rooty(), window.winfo_rootx()+window.winfo_width(), window.winfo_rooty()+window.winfo_height())
    ImageGrab.grab(bbox=bounds).save(output)
    print('Integrated', width, height, 'timeline', widgets['text'].winfo_height(), 'portrait', widgets['left_portrait'].winfo_width(), output)
    window.destroy()
    root.destroy()


if __name__ == '__main__':
    output_dir = Path(__file__).resolve().parent / 'ui_previews'
    for theme in ('Dark Mode', 'Light Office', 'UFC', 'Matrix'):
        for size in ((1360, 900), (820, 540)):
            suffix = '' if theme == 'Dark Mode' and size[0] == 1360 else '_' + theme.lower().replace(' ', '_') + ('_compact' if size[0] == 820 else '')
            preview(theme, *size, output_dir / ('fight_night_overhaul' + suffix + '.png'))
    for width, height in ((1360, 900), (820, 540)):
        integrated_preview(width, height, output_dir / ('fight_night_live_preview' + ('_compact' if width == 820 else '') + '.png'))
