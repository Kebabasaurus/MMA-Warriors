"""Read-only event archive with shared Fight Night transcript presentation."""
import tkinter as tk
from tkinter import ttk

from constants import FIGHT_COMMENTARY_MODES
from fight_night_presentation import configure_fight_timeline, insert_fight_timeline_line


def build_event_archive(app, title, package):
    window = app.create_managed_window()
    window.title(title)
    colors = app.colors
    window.configure(bg=colors['chrome'])
    screen_w, screen_h = window.winfo_screenwidth(), window.winfo_screenheight()
    width, height = min(1160, max(320, screen_w - 60)), min(790, max(320, screen_h - 100))
    window.geometry(f'{width}x{height}+{max(0, (screen_w-width)//2)}+{max(0, (screen_h-height)//2)}')
    window.minsize(min(720, width), min(480, height))
    window.rowconfigure(2, weight=1)
    window.columnconfigure(0, weight=1)
    logs = app.fight_night_log_order(package.get('fight_logs', []))

    header = tk.Frame(window, bg=colors['panel_dark'], padx=16, pady=12)
    header.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 6))
    header.columnconfigure(0, weight=1)
    tk.Label(header, text='FIGHT NIGHT  /  ARCHIVE', bg=colors['panel_dark'],
             fg=colors['gold'], font=('Tahoma', 9, 'bold')).grid(sticky='w')
    title_label = tk.Label(header, text=title, bg=colors['panel_dark'], fg=colors['text'],
                          font=('Tahoma', 17, 'bold'), anchor='w', justify='left')
    title_label.grid(sticky='ew', pady=(4, 0))
    tk.Label(header, text=f'{len(logs)} bouts  •  Select a bout, then explore its rounds',
             bg=colors['panel_dark'], fg=colors['muted'], font=('Tahoma', 10)).grid(sticky='w', pady=(4, 0))
    header.bind('<Configure>', lambda event: title_label.configure(wraplength=max(180, event.width - 36)))

    controls = tk.Frame(window, bg=colors['chrome'])
    controls.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 6))
    tk.Label(controls, text='Commentary', bg=colors['chrome'], fg=colors['text'],
             font=('Tahoma', 10)).pack(side='left', padx=(4, 8))
    initial = str(app.rules.get('fight_commentary_mode', 'Broadcast'))
    mode = tk.StringVar(master=window, value=initial if initial in FIGHT_COMMENTARY_MODES else 'Broadcast')
    mode_box = ttk.Combobox(controls, state='readonly', values=FIGHT_COMMENTARY_MODES,
                           textvariable=mode, width=12)
    mode_box.pack(side='left')
    ttk.Button(controls, text='Close', command=window.destroy).pack(side='right')

    body = tk.PanedWindow(window, orient='horizontal', bg=colors['line'], bd=0,
                          sashwidth=7, sashrelief='raised')
    body.grid(row=2, column=0, sticky='nsew', padx=10, pady=(0, 8))
    sidebar = ttk.Notebook(body)
    body.add(sidebar, minsize=170, width=270, stretch='never')

    def archive_list(label):
        frame = tk.Frame(sidebar, bg=colors['tree'])
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        listing = tk.Listbox(frame, font=('Tahoma', 10), width=20, borderwidth=0,
            bg=colors['tree'], fg=colors['text'], selectbackground=colors['red'],
            selectforeground='#ffffff', exportselection=False, activestyle='none')
        listing.grid(row=0, column=0, sticky='nsew')
        vertical = ttk.Scrollbar(frame, orient='vertical', command=listing.yview)
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal = ttk.Scrollbar(frame, orient='horizontal', command=listing.xview)
        horizontal.grid(row=1, column=0, sticky='ew')
        listing.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        sidebar.add(frame, text=label)
        return listing

    fight_list = archive_list('Fight card')
    round_list = archive_list('Rounds')
    preparation_list = archive_list('Preparation')
    reading = tk.Frame(body, bg=colors['tree'])
    reading.rowconfigure(1, weight=1)
    reading.columnconfigure(0, weight=1)
    body.add(reading, minsize=350, stretch='always')
    selected_heading = tk.Label(reading, text='Event report', font=('Tahoma', 12, 'bold'),
        bg=colors['panel_dark'], fg=colors['text'], anchor='w', justify='left', padx=12, pady=10)
    selected_heading.grid(row=0, column=0, columnspan=2, sticky='ew')
    reading.bind('<Configure>', lambda event: selected_heading.configure(wraplength=max(180, event.width - 28)))
    text = tk.Text(reading, wrap='word', bg=colors['cream'], fg=colors['text'],
                   font=('Tahoma', 11), padx=14, pady=10, borderwidth=0, state='disabled')
    text.grid(row=1, column=0, sticky='nsew')
    scrollbar = ttk.Scrollbar(reading, orient='vertical', command=text.yview)
    scrollbar.grid(row=1, column=1, sticky='ns')
    text.configure(yscrollcommand=scrollbar.set)
    configure_fight_timeline(text, colors)

    footer = tk.Frame(window, bg=colors['chrome'])
    footer.grid(row=3, column=0, sticky='ew', padx=10, pady=(0, 10))
    tk.Label(footer, text='Detailed keeps the complete stored commentary.', bg=colors['chrome'],
             fg=colors['muted'], font=('Tahoma', 9)).pack(side='left')
    if package.get('tournament_brackets'):
        ttk.Button(footer, text='View Tournament Bracket',
            command=lambda: app.open_event_tournament_bracket(package, window)).pack(side='right')

    def clean(line, log=None):
        value = str(line)
        for item in ([log] if log is not None else logs):
            value = app.display_fighter_names_in_text(value, item)
        return value

    def render(lines):
        text.configure(state='normal')
        text.delete('1.0', 'end')
        try:
            for line in lines:
                insert_fight_timeline_line(text, str(line))
        finally:
            text.configure(state='disabled')
        text.yview_moveto(0)

    def show_selected(_event=None):
        selected = fight_list.curselection()
        round_list.delete(0, 'end')
        if selected and selected[0] < len(logs):
            log = logs[selected[0]]
            selected_heading.configure(text=clean(log.get('heading', log.get('fight', 'Bout')), log))
            lines = app.fight_night_commentary_lines(log.get('detailed_lines', log.get('lines', [])), mode.get())
            render(clean(line, log) for line in lines)
            for row in log.get('round_analysis', []):
                round_list.insert('end', f"Round {row.get('round', '?')} analysis")
        else:
            selected_heading.configure(text='Event report')
            render(clean(line) for line in package.get('log', []))

    def show_round(_event=None):
        selected, chosen = fight_list.curselection(), round_list.curselection()
        if not selected or not chosen:
            return
        log = logs[selected[0]]
        rows = log.get('round_analysis', [])
        if chosen[0] >= len(rows):
            return
        row = rows[chosen[0]]
        heading = clean(log.get('heading', log.get('fight', 'Bout')), log)
        selected_heading.configure(text=f"{heading}  •  Round {row.get('round', '?')} analysis")
        render(app.format_round_analysis(row, log).splitlines())

    def show_preparation(_event=None):
        timeline = package.get('preparation_timeline', {})
        states = timeline.get('stage_states', []) if isinstance(timeline, dict) else []
        selected = preparation_list.curselection()
        if not selected or selected[0] >= len(states):
            selected_heading.configure(text='Event preparation')
            render([
                'Preparation evidence is not available for this legacy archive.'
                if not states else
                'Select a preparation stage to inspect its recorded outcome.'
            ])
            return
        state = states[selected[0]]
        selected_heading.configure(text=f"Preparation  •  {state.get('label', 'Stage')}")
        lines = [
            str(state.get('label', 'Preparation stage')).upper(),
            str(state.get('status', 'Not recorded')),
            str(state.get('detail', '')),
        ]
        if state.get('stage_id') == 'press':
            lines.extend(str(value) for value in timeline.get('press_outcomes', []))
        elif state.get('stage_id') == 'weigh_in':
            lines.extend(str(value) for value in timeline.get('weigh_in_outcomes', []))
        elif state.get('stage_id') == 'campaign':
            evidence = timeline.get('campaign_evidence', [])
            lines.extend(
                f"{item.get('action', 'Action')}: {item.get('evidence_key', '')}"
                for item in evidence if isinstance(item, dict)
            )
        render(lines)

    for index, log in enumerate(logs, 1):
        fight_list.insert('end', f"{index}. {clean(log.get('heading', log.get('fight', f'Bout {index}')), log)}")
    timeline = package.get('preparation_timeline', {})
    preparation_states = timeline.get('stage_states', []) if isinstance(timeline, dict) else []
    for state in preparation_states:
        if isinstance(state, dict):
            preparation_list.insert('end', f"{state.get('label', 'Stage')}: {state.get('status', 'Not recorded')}")
    if not preparation_states:
        # Legacy packages are still valid, but the archive must not imply that
        # a missing timeline was an empty or successful preparation run.  Keep
        # an explicit selectable row so the reader can see the coverage gap.
        preparation_list.insert('end', 'Unavailable: no preparation timeline retained')
        preparation_list.itemconfig(0, foreground=colors['muted'])
    fight_list.bind('<<ListboxSelect>>', show_selected)
    round_list.bind('<<ListboxSelect>>', show_round)
    preparation_list.bind('<<ListboxSelect>>', show_preparation)
    mode_box.bind('<<ComboboxSelected>>', show_selected)
    ttk.Button(controls, text='Full bout', command=show_selected).pack(side='left', padx=8)
    window._fight_archive_widgets = dict(fight_list=fight_list, round_list=round_list,
        preparation_list=preparation_list,
        text=text, heading=selected_heading, sidebar=sidebar, mode=mode, mode_box=mode_box,
        show_selected=show_selected, show_round=show_round, show_preparation=show_preparation,
        scrollbar=scrollbar)
    show_selected()
    return window
