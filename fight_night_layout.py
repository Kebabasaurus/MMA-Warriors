"""Presentation-only Fight Night dashboard; playback remains in EventMixin."""
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk


def build_fight_night_layout(app, window, width, height):
    colors = app.colors
    widgets = {}
    panel = colors['panel']
    readable = getattr(app, 'accessible_tab_text', lambda background, foreground: foreground)
    gold_text = readable(panel, colors['gold'])

    def label(parent, text='', size=10, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=panel, fg=colors['text'],
                        font=('Tahoma', size, 'bold' if bold else 'normal'), **kwargs)

    controls_area = ttk.Frame(window, style='Chrome.TFrame')
    controls_area.pack(side='bottom', fill='x', padx=12, pady=(0, 8))
    controls = ttk.Frame(controls_area, style='Chrome.TFrame')
    controls.pack(fill='x', pady=(3, 2))
    controls3 = ttk.Frame(controls_area, style='Chrome.TFrame')
    controls3.pack(fill='x', pady=2)
    settings = ttk.Frame(controls_area, style='Panel.TFrame')
    controls2 = ttk.Frame(settings, style='Panel.TFrame')
    controls2.pack(fill='x', padx=6, pady=(5, 2))
    reading_controls = ttk.Frame(settings, style='Panel.TFrame')
    reading_controls.pack(fill='x', padx=6, pady=2)
    audio_controls = ttk.Frame(settings, style='Panel.TFrame')
    audio_controls.pack(fill='x', padx=6, pady=(2, 5))
    settings_open = tk.BooleanVar(value=False)

    def toggle_settings():
        settings_open.set(not settings_open.get())
        if settings_open.get():
            settings.pack(fill='x', before=controls3, pady=4)
        else:
            settings.pack_forget()
        settings_button.configure(text='Hide Settings' if settings_open.get() else 'Playback Settings')

    settings_button = ttk.Button(controls3, text='Playback Settings', command=toggle_settings)
    settings_button.pack(side='left', padx=4)
    widgets.update(controls_area=controls_area, controls=controls, controls2=controls2,
                   controls3=controls3, reading_controls=reading_controls,
                   audio_controls=audio_controls, settings_button=settings_button)

    tote = tk.Frame(window, bg=colors['chrome'])
    tote.pack(fill='x', padx=12, pady=(8, 4))
    tote.columnconfigure(0, weight=1, uniform='corners')
    tote.columnconfigure(2, weight=1, uniform='corners')
    portrait_size = 104 if height < 700 else 136
    corner_inners = []
    for column, side, corner in ((0, 'left', 'RED CORNER'), (2, 'right', 'BLUE CORNER')):
        card = tk.Frame(tote, bg=panel, highlightthickness=1, highlightbackground=colors['line'])
        card.grid(row=0, column=column, sticky='nsew')
        accent = colors['red'] if side == 'left' else colors.get('blue', '#3f7bd6')
        tk.Frame(card, bg=accent, height=3).pack(fill='x')
        inner = tk.Frame(card, bg=panel)
        inner.pack(fill='both', expand=True, padx=8, pady=4 if height < 700 else 8)
        corner_inners.append(inner)
        portrait = tk.Canvas(inner, width=portrait_size, height=portrait_size,
                             bg=colors['panel_dark'], highlightthickness=0)
        portrait.pack(side='left' if side == 'left' else 'right', padx=(0, 8) if side == 'left' else (8, 0))
        info = tk.Frame(inner, bg=panel)
        info.pack(fill='both', expand=True)
        label(info, corner, 8, True, anchor='w').pack(fill='x')
        name = label(info, 'Awaiting fighter', 12, True, anchor='w', justify='left',
                     wraplength=220, cursor='hand2')
        name.pack(fill='x', pady=(3, 2))
        meta = tk.Frame(info, bg=panel)
        meta.pack(fill='x')
        ovr = label(meta, '', 9, True, anchor='w')
        ovr.configure(fg=gold_text)
        ovr.pack(side='left', padx=(0, 8))
        title = label(meta, '', 8, True, anchor='w', justify='left', wraplength=110)
        title.pack(side='left', fill='x', expand=True)
        condition = label(info, 'READY', 8, anchor='w', justify='left', wraplength=220)
        condition.pack(fill='x', pady=(4, 2))
        gas = ttk.Progressbar(info, maximum=100, value=100,
                             style=app.live_fight_condition_styles['red' if side == 'left' else 'blue'])
        gas.pack(fill='x')
        def resize_info(event, name=name, title=title, condition=condition):
            for item in (name, condition):
                item.configure(wraplength=max(70, event.width - 4))
            title.configure(wraplength=max(55, title.winfo_width()))
        info.bind('<Configure>', resize_info)
        widgets.update({f'{side}_name': name, f'{side}_ovr': ovr, f'{side}_portrait': portrait,
                        f'{side}_title_status': title, f'{side}_condition': condition, f'{side}_gas': gas})
    center = tk.Frame(tote, bg=panel, width=116)
    center.grid(row=0, column=1, sticky='ns', padx=8)
    chip = label(center, 'FIGHT NIGHT', 8, True, wraplength=110, justify='center')
    chip.pack(padx=4, pady=(10, 3))
    phase = label(center, 'CARD READY', 10, True, wraplength=110)
    phase.pack(padx=4, pady=3)
    clock = label(center, '--:--', 24, True)
    clock.configure(fg=gold_text)
    clock.pack(padx=6, pady=3)
    vs = label(center, 'VS', 10, True)
    vs.pack(pady=(0, 5))
    widgets.update(label_chip=chip, phase_label=phase, clock_label=clock, vs_label=vs)

    body = tk.PanedWindow(window, orient='horizontal', bg=colors['line'], bd=0,
                         sashwidth=7, showhandle=True)
    body.pack(fill='both', expand=True, padx=12, pady=(4, 8))
    sidebar = ttk.Notebook(body)
    card_page = ttk.Frame(sidebar, style='Panel.TFrame')
    sidebar.add(card_page, text='Card')
    fight_list = tk.Listbox(card_page, width=24, font=('Tahoma', 10), bg=colors['tree'],
                           fg=colors['text'], selectbackground=colors['red'],
                           selectforeground='#ffffff', activestyle='none', exportselection=False)
    fight_list.grid(row=0, column=0, sticky='nsew')
    card_page.rowconfigure(0, weight=1)
    card_page.columnconfigure(0, weight=1)
    ttk.Scrollbar(card_page, command=fight_list.yview).grid(row=0, column=1, sticky='ns')
    horizontal = ttk.Scrollbar(card_page, orient='horizontal', command=fight_list.xview)
    horizontal.grid(row=1, column=0, sticky='ew')
    vertical = card_page.grid_slaves(row=0, column=1)[0]
    fight_list.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

    def scrolling_page(title):
        page = ttk.Frame(sidebar, style='Panel.TFrame')
        sidebar.add(page, text=title)
        canvas = tk.Canvas(page, bg=panel, highlightthickness=0, width=250)
        scroll = ttk.Scrollbar(page, command=canvas.yview)
        scroll.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        canvas.configure(yscrollcommand=scroll.set)
        content = tk.Frame(canvas, bg=panel)
        item = canvas.create_window(0, 0, window=content, anchor='nw')
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(item, width=event.width))
        content.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
        return content

    analysis = scrolling_page('Round Read')
    brief = scrolling_page('Bout Desk')
    for key, parent, title, size in (
            ('score_label', analysis, 'Official judges remain sealed', 9),
            ('fight_read_label', analysis, 'Telemetry appears as the bout unfolds.', 10),
            ('round_read_label', analysis, 'No round summary yet.', 10),
            ('intro_label', brief, 'TALE OF THE TAPE', 11),
            ('bout_brief_label', brief, 'Select a bout to begin.', 10),
            ('current_moment_label', brief, 'Latest commentary will appear here.', 11)):
        item = label(parent, title, size, key in {'intro_label', 'current_moment_label'},
                     justify='left', anchor='w', wraplength=235, padx=10, pady=7)
        item.pack(fill='x')
        item.bind('<Configure>', lambda event, item=item: item.configure(wraplength=max(80, event.width-24)))
        widgets[key] = item
    momentum_canvas = tk.Canvas(analysis, height=22, bg=colors['panel_dark'], highlightthickness=0)
    momentum_canvas.pack(fill='x', padx=10, pady=(8, 2))
    momentum_text = label(analysis, 'Momentum: even', 9, justify='left', wraplength=230)
    momentum_text.pack(fill='x', padx=10, pady=(0, 8))
    stats_panel = ttk.Frame(analysis, style='Panel.TFrame')
    stats_panel.pack(fill='x', padx=6, pady=6)
    round_bars = tk.Canvas(analysis, height=132, bg=panel, highlightthickness=0)
    round_bars.pack(fill='x', padx=10, pady=8, before=stats_panel)
    round_snapshot = {'values': {}, 'names': ('Red', 'Blue')}

    def update_round_read(values, names):
        # Only presented telemetry is supplied by the existing playback callback.
        round_snapshot.update(values=values, names=names)
        round_bars.delete('all')
        span = max(80, round_bars.winfo_width() - 8)
        for index, (key, title) in enumerate((('impact', 'IMPACT'), ('control', 'CONTROL'), ('danger', 'THREAT'))):
            a = max(0, float(values.get('a', {}).get(key, 0) or 0))
            b = max(0, float(values.get('b', {}).get(key, 0) or 0))
            scale = max(1, a, b)
            y = index * 44
            round_bars.create_text(0, y, anchor='nw', text=f'{title}   Red {a:g}  /  Blue {b:g}',
                                   fill=colors['text'], font=('Tahoma', 9, 'bold'))
            for offset, value, color in ((18, a, colors['red']), (29, b, colors.get('blue', '#3f7bd6'))):
                round_bars.create_rectangle(0, y+offset, span, y+offset+7, fill=colors['line'], outline='')
                round_bars.create_rectangle(0, y+offset, span*value/scale, y+offset+7, fill=color, outline='')
    round_bars.bind('<Configure>', lambda event: update_round_read(round_snapshot['values'], round_snapshot['names']))
    live_stats = ttk.Treeview(stats_panel, columns=('fighter', 'impact', 'control', 'threat', 'gas', 'momentum'),
                              show='headings', height=2, selectmode='none')
    for key, title, size in (('fighter', 'Fighter', 150), ('impact', 'Impact', 60), ('control', 'Control', 60),
                             ('threat', 'Threat', 60), ('gas', 'Gas', 50), ('momentum', 'Edge', 65)):
        live_stats.heading(key, text=title)
        live_stats.column(key, width=size, minwidth=size, stretch=False)
    live_stats.pack(fill='x')
    stats_scroll = ttk.Scrollbar(stats_panel, orient='horizontal', command=live_stats.xview)
    stats_scroll.pack(fill='x')
    live_stats.configure(xscrollcommand=stats_scroll.set)
    widgets['round_read_label'].pack_forget()
    widgets['round_read_label'].pack(fill='x', pady=(4, 8))
    ribbon = tk.Frame(brief, bg=panel, highlightthickness=1, highlightbackground=colors['gold'])
    result_winner = label(ribbon, '', 13, True, justify='left', wraplength=225)
    result_winner.pack(fill='x', padx=8, pady=6)
    result_detail = label(ribbon, '', 10, justify='left', wraplength=225)
    result_detail.pack(fill='x', padx=8, pady=6)
    for item in (result_winner, result_detail):
        item.bind('<Configure>', lambda event, item=item: item.configure(wraplength=max(80, event.width-16)))

    def attach_scoped_wheel(content):
        """Route wheel input to the hovered Round Read/Bout Desk canvas.

        The main page scroller deliberately leaves native text/list/tree widgets
        alone.  These two Fight Night readers are canvas-backed, however, so
        their child labels need the same local wheel affordance without a
        global ``bind_all`` that could hijack the action timeline or another
        page.  Bind the current content tree once after construction; callers
        that add a new reader widget should call this helper for that widget.
        """
        canvas = content.master

        def wheel(event, step=None):
            if step is None:
                delta = getattr(event, 'delta', 0)
                step = -1 if delta > 0 else 1
                if getattr(event, 'num', None) == 4:
                    step = -1
                elif getattr(event, 'num', None) == 5:
                    step = 1
            try:
                canvas.yview_scroll(step * 3, 'units')
            except tk.TclError:
                return None
            return 'break'

        def bind_tree(widget):
            # Preserve native behaviour for any future Treeview/Text/Listbox
            # added to a reader page; labels and frames use the local canvas.
            if isinstance(widget, (tk.Text, tk.Listbox, ttk.Treeview)):
                return
            widget.bind('<MouseWheel>', wheel, add='+')
            widget.bind('<Button-4>', lambda event: wheel(event, -1), add='+')
            widget.bind('<Button-5>', lambda event: wheel(event, 1), add='+')
            for child in widget.winfo_children():
                bind_tree(child)

        bind_tree(content)
        return canvas

    attach_scoped_wheel(analysis)
    attach_scoped_wheel(brief)
    reader = tk.Frame(body, bg=panel, highlightthickness=1, highlightbackground=colors['line'])
    label(reader, 'ACTION TIMELINE', 10, True, anchor='w', padx=14, pady=7).pack(fill='x')
    text_scroll = ttk.Scrollbar(reader)
    text_scroll.pack(side='right', fill='y')
    text = tk.Text(reader, wrap='word', bg=colors['tree'], fg=colors['text'],
                   font=('Tahoma', 11), padx=18, pady=12, state='disabled')
    text.pack(fill='both', expand=True)
    text.configure(yscrollcommand=text_scroll.set)
    body.add(sidebar, width=260, minsize=190, stretch='never')
    body.add(reader, minsize=330, stretch='always')
    widgets.update(body=body, sidebar=sidebar, brief_page=sidebar.tabs()[2], text=text,
                   text_scroll=text_scroll, fight_list=fight_list, live_stats=live_stats,
                   momentum_canvas=momentum_canvas, momentum_text=momentum_text,
                   result_ribbon=ribbon, result_winner_label=result_winner,
                   result_detail_label=result_detail, update_round_read=update_round_read,
                   round_bars=round_bars, corner_inners=corner_inners)
    window._fight_night_widgets = widgets
    return SimpleNamespace(**widgets)
