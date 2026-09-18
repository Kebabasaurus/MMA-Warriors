"""Player-facing profile overview, using existing management workflows."""
import hashlib
import math
import tkinter as tk
from tkinter import ttk
from fighter_trait_ui import build_trait_card


def bounded_profile_metric(value, *, low=0, high=100, default=0):
    """Project a retained profile metric to a finite display-safe integer.

    Profile pages are readers.  A legacy save can contain a malformed or
    non-finite value, and that must not turn an overview repaint into a crash
    (or a misleading ``nan``/``inf`` meter).  The raw fighter field remains
    untouched; callers choose the range appropriate to the metric.
    """
    try:
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError
        return max(int(low), min(int(high), int(round(numeric))))
    except (TypeError, ValueError, OverflowError):
        return max(int(low), min(int(high), int(default)))


def compare_fighter_row_identity(fighter):
    """Return a stable source-bound key for a comparison-picker row.

    The picker is rebuilt whenever its query changes, so a visible row index
    cannot safely identify the fighter behind an action.  Saved fighter IDs
    are preferred; imported legacy objects without one receive a deterministic
    fingerprint of retained identity fields.  Duplicate source keys are
    disambiguated by the renderer without changing the underlying fighter.
    """
    fighter_id = str(getattr(fighter, "fighter_id", "") or "").strip()
    if fighter_id:
        return f"compare-fighter:{fighter_id}"
    payload = "|".join(str(getattr(fighter, field, "") or "") for field in (
        "name", "gender", "weight", "region", "nationality", "age", "record_w",
        "record_l", "record_d",
    ))
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:20]
    return f"legacy-compare-fighter:{digest}"


def vertical_scroller(app, parent):
    """One width-constrained vertical viewport, with no horizontal scrollbar."""
    shell = ttk.Frame(parent, style="Chrome.TFrame")
    canvas = tk.Canvas(shell, bg=app.colors["chrome"], highlightthickness=0)
    scrollbar = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    content = ttk.Frame(canvas, style="Chrome.TFrame")
    item = canvas.create_window(0, 0, window=content, anchor="nw")
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(item, width=max(1, event.width)))
    content.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))

    def wheel(event):
        bounds = canvas.bbox("all")
        if bounds and bounds[3] > canvas.winfo_height():
            delta = getattr(event, "delta", 0)
            step = (-1 if delta > 0 else 1) if delta else (1 if event.num == 5 else -1)
            canvas.yview_scroll(step * 3, "units")
        return "break"

    bound = set()

    def attach(_event=None):
        pending = [canvas, content]
        while pending:
            widget = pending.pop()
            pending.extend(widget.winfo_children())
            if str(widget) not in bound:
                if isinstance(widget, (tk.Text, tk.Listbox, ttk.Treeview, ttk.Combobox, ttk.Spinbox)):
                    continue
                widget.bind("<MouseWheel>", wheel, add="+")
                widget.bind("<Button-4>", wheel, add="+")
                widget.bind("<Button-5>", wheel, add="+")
                bound.add(str(widget))

    shell.bind("<Map>", attach, add="+")
    return shell, content


def compare_picker(app, fighter):
    window = app.create_managed_window()
    window.title("Choose a fighter to compare")
    window.geometry(f"{min(980, window.winfo_screenwidth() - 80)}x{min(600, window.winfo_screenheight() - 100)}")
    window.configure(bg=app.colors["chrome"])
    query = tk.StringVar()
    ttk.Label(window, text="COMPARE WITH", style="ScreenTitle.TLabel").pack(anchor="w", padx=12, pady=8)
    ttk.Label(window, text="Search fighter name. Same-division fighters appear first; ability respects scouting knowledge.",
              style="Chrome.TLabel", wraplength=650).pack(anchor="w", padx=12, pady=(0, 4))
    entry = ttk.Entry(window, textvariable=query)
    entry.pack(fill="x", padx=12, pady=4)
    footer = ttk.Frame(window, style="Chrome.TFrame")
    footer.pack(side="bottom", fill="x", padx=12, pady=8)
    count_label = ttk.Label(footer, style="Chrome.TLabel")
    count_label.pack(side="left")
    table = ttk.Frame(window, style="Chrome.TFrame")
    table.pack(fill="both", expand=True, padx=12, pady=8)
    tree = ttk.Treeview(table, columns=("name", "division", "record", "age", "ability", "company"), show="headings", selectmode="browse")
    for key, title in (("name", "Fighter"), ("division", "Division"), ("record", "Record"), ("age", "Age"), ("ability", "Ability / estimate"), ("company", "Company")):
        tree.heading(key, text=title)
        tree.column(key, width=60 if key == "age" else 95 if key == "record" else 165, minwidth=40)
    scroll = ttk.Scrollbar(table, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)
    fighters = [other for other in app.all_fighter_objects()
                if other.fighter_id != fighter.fighter_id]
    fighters.sort(key=lambda other: (other.gender != fighter.gender or other.weight != fighter.weight, other.name.casefold()))
    visible = {}

    def render(*_):
        previous_selection = tree.selection()
        previous_row_id = previous_selection[0] if previous_selection else ""
        tree.delete(*tree.get_children())
        visible.clear()
        used_row_ids = set()
        needle = query.get().strip().casefold()
        for other in fighters:
            if needle and needle not in other.name.casefold():
                continue
            base_key = compare_fighter_row_identity(other)
            key = base_key
            duplicate = 2
            while key in used_row_ids:
                key = f"{base_key}#{duplicate}"
                duplicate += 1
            used_row_ids.add(key)
            visible[key] = other
            tree.insert("", "end", iid=key, values=(app.fighter_display_name(other),
                        f"{other.gender} {app.fighter_display_division(other)}", other.record, other.age,
                        app.scouting_display_value(other, "overall", app.fighter_company_for_profile(other)),
                        app.fighter_company_for_profile(other)))
            if len(visible) >= 150:
                break
        count_label.configure(text=f"{len(visible)} shown" + (" | First 150 matches; narrow your search" if len(visible) == 150 else ""))
        # Reapply selection by source identity, not by the row's old position.
        # Filtering/paging can remove the selected fighter without emitting a
        # Tk selection event; explicitly clear the selection in that case.
        if previous_row_id and previous_row_id in visible:
            tree.selection_set(previous_row_id)
            tree.focus(previous_row_id)
        elif previous_row_id:
            tree.selection_remove(tree.selection())

    def choose(_event=None):
        selected = tree.selection()
        other = visible.get(selected[0]) if selected else None
        if other:
            app.open_compare_fighters_window((app.fighter_company_for_profile(fighter), fighter),
                                            (app.fighter_company_for_profile(other), other))
            window.destroy()

    ttk.Button(footer, text="Compare Selected", command=choose, style="Accent.TButton").pack(side="right")
    tree.bind("<Double-1>", choose)
    tree.bind("<Return>", choose)
    query.trace_add("write", render)
    window.bind("<Escape>", lambda _event: window.destroy())
    render()
    entry.focus_set()


def build_overview(app, parent, fighter, company, stats_visible, report, profile_window):
    shell, content = vertical_scroller(app, parent)
    shell.pack(fill="both", expand=True)
    owned = app.player_owns_fighter(fighter)
    observer = getattr(app, "spectator_mode", False)
    retired = getattr(fighter, "retired", False)
    sport = bool(getattr(fighter, "sport_employer", ""))
    # Keep every visual meter finite and bounded without writing back into the
    # fighter.  This matters for legacy profiles as well as malformed imported
    # rows, especially when scouting mode hides the native ratings.
    momentum_value = bounded_profile_metric(getattr(fighter, "momentum", 0), low=-10, high=10)
    morale_value = bounded_profile_metric(getattr(fighter, "morale", 0))
    fatigue_value = bounded_profile_metric(getattr(fighter, "fatigue", 0))
    camp_weeks_value = bounded_profile_metric(getattr(fighter, "camp_weeks", 0), high=520)

    def activity_value():
        try:
            return bounded_profile_metric(app.fighter_activity_rating(fighter))
        except (AttributeError, TypeError, ValueError, OverflowError):
            # Activity is a public rhythm indicator.  If a legacy field is
            # malformed, keep the card readable without repairing the fighter.
            return 0

    layout_items = []
    layout_state = {"wide": None, "count": -1}

    def reflow(event=None):
        wide = content.winfo_width() >= 920
        if layout_state == {"wide": wide, "count": len(layout_items)}:
            return
        layout_state.update(wide=wide, count=len(layout_items))
        content.columnconfigure(0, weight=1, uniform="overview")
        content.columnconfigure(1, weight=1 if wide else 0, uniform="overview" if wide else "")
        for index, widget in enumerate(layout_items):
            row, column = (index, 0) if not wide or index < 2 else (2 + (index - 2) // 2, (index - 2) % 2)
            widget.grid(row=row, column=column, columnspan=2 if wide and index < 2 else 1,
                        sticky="nsew", padx=8, pady=6)

    content.bind("<Configure>", reflow, add="+")

    def section(title, text):
        panel = ttk.Frame(content, style="Panel.TFrame")
        layout_items.append(panel)
        heading = tk.Frame(panel, bg=app.colors["panel"])
        heading.pack(fill="x", padx=16, pady=(14, 8))
        tk.Frame(heading, bg=app.colors["gold"], width=3, height=17).pack(side="left", padx=(0, 9))
        tk.Label(heading, text=title, bg=app.colors["panel"], fg=app.colors["text"],
                 font=("Tahoma", 11, "bold"), anchor="w").pack(side="left")
        label = tk.Label(panel, text=text, bg=app.colors["panel"], fg=app.colors["text"],
                         font=("Tahoma", 11), justify="left", anchor="w", wraplength=660)
        label.pack(fill="x", padx=16, pady=(0, 16))
        panel.bind("<Configure>", lambda event: label.configure(wraplength=max(160, min(780, event.width - 40))))
        return panel

    if retired:
        status = "RETIRED | Historical career profile"
    elif owned and not sport:
        status = app.fighter_matchmaking_status(fighter, app.month, app.week)
    else:
        status = str(fighter.status)
    last = bounded_profile_metric(getattr(fighter, "last_fight_month", 0), high=999999)
    idle = f"{max(0, app.month - last)} month(s) since last recorded fight" if last else "No dated last fight recorded"
    readiness = idle
    if not retired and owned and not sport:
        if fighter.injured or getattr(fighter, "serious_injury", ""):
            readiness += f"\nMedical return: {app.fighter_recovery_date_label(fighter)}"
        if app.fighter_has_scheduled_fight(fighter, include_booked=True):
            readiness += "\nA fight is already booked. Review its date and opponent in Booking."
        if stats_visible:
            readiness += (f"\nFatigue {fatigue_value}/100 | Camp: {camp_weeks_value} week(s), quality {fighter.camp_quality}"
                          if camp_weeks_value else f"\nFatigue {fatigue_value}/100 | No fight camp completed yet")
    if getattr(fighter, "serious_injury_pending", False):
        readiness += "\nMedical decision required: review the injury message in Inbox."
    if getattr(fighter, "retirement_pending", False):
        readiness += "\nFinal-fight request: " + str(getattr(fighter, "retirement_reason", "") or "Farewell bout pending")
    hero = ttk.Frame(content, style="Chrome.TFrame")
    layout_items.append(hero)
    if stats_visible:
        hero_metrics = (("Status", status), ("Overall", bounded_profile_metric(getattr(fighter, "overall", 0))),
                        ("Activity", f"{activity_value()}/100"))
    else:
        hero_metrics = (("Status", status), ("Intel", f"{app.scouting_effective_confidence(report)}%"),
                        ("Company", company))
    app.profile_dashboard_header(
        hero, "Corner briefing", "Overview",
        "The immediate management read: availability, recent form, strengths and the next useful decision.",
        hero_metrics,
    )

    def meter_card(parent_widget, title, value, subtitle, color=None):
        value = bounded_profile_metric(value)
        card = tk.Frame(parent_widget, bg=app.colors["panel"], highlightthickness=1,
                        highlightbackground=app.colors["line"], padx=10, pady=8)
        tk.Label(card, text=title.upper(), bg=app.colors["panel"], fg=app.colors["muted"],
                 font=("Tahoma", 7, "bold"), anchor="w").pack(fill="x")
        headline = tk.Frame(card, bg=app.colors["panel"])
        headline.pack(fill="x", pady=(2, 5))
        tk.Label(headline, text=str(value), bg=app.colors["panel"], fg=color or app.profile_rating_color(value),
                 font=("Impact", 21), anchor="w").pack(side="left")
        tk.Label(headline, text=subtitle, bg=app.colors["panel"], fg=app.colors["text"],
                 font=("Tahoma", 8), anchor="e").pack(side="right")
        bar = tk.Canvas(card, height=7, bg=app.colors["panel"], highlightthickness=0)
        bar.pack(fill="x")
        def draw(event=None):
            width = max(10, event.width if event else bar.winfo_width())
            bar.delete("all")
            bar.create_rectangle(0, 0, width, 7, fill=app.colors["tree"], outline="")
            bar.create_rectangle(0, 0, max(2, width * value / 100), 7,
                                 fill=color or app.profile_rating_color(value), outline="")
        bar.bind("<Configure>", draw, add="+")
        return card

    pulse = tk.Frame(content, bg=app.colors["chrome"])
    layout_items.append(pulse)
    pulse_values = (
        ("Momentum", max(0, min(100, 50 + momentum_value * 10)),
         f"{momentum_value:+d} form"),
        ("Morale", morale_value, "mindset"),
        ("Readiness", 100 - fatigue_value, f"fatigue {fatigue_value}"),
        ("Activity", activity_value(), "fight rhythm"),
    ) if stats_visible else (
        ("Intel", app.scouting_effective_confidence(report), "confidence"),
        ("Activity", app.fighter_activity_rating(fighter), "fight rhythm"),
    )
    for index, values in enumerate(pulse_values):
        card = meter_card(pulse, *values)
        card.grid(row=0, column=index, sticky="nsew", padx=3, pady=3)
        pulse.grid_columnconfigure(index, weight=1, uniform="overview-pulse")
    readiness_panel = section("READINESS & ACTIVITY", readiness)
    readiness_heading = readiness_panel.winfo_children()[0]
    ready_now = str(status).strip().casefold() == "ready"
    badge_bg = "#224d3e" if ready_now else app.colors["panel_dark"]
    badge_fg = "#b5efcb" if ready_now else app.colors["gold"]
    tk.Label(readiness_heading, text=str(status).upper(), bg=badge_bg, fg=badge_fg,
             font=("Tahoma", 10, "bold"), padx=12, pady=4).pack(side="right", padx=(12, 0))

    actions = ttk.Frame(content, style="Chrome.TFrame")
    layout_items.append(actions)

    def navigate(tab):
        app.select_tab(tab)
        profile_window.destroy()

    def booking():
        app.select_tab("booking")
        for attr, value in (("available_weight_filter", fighter.weight), ("available_gender_filter", fighter.gender),
                            ("available_status_filter", "All"), ("available_search", "")):
            variable = getattr(app, attr, None)
            if variable is not None:
                variable.set(value)
        app.refresh_available()
        for row, other in app.available_tree_fighters.items():
            if other.fighter_id == fighter.fighter_id:
                app.available_tree.selection_set(row)
                app.available_tree.see(row)
                break
        profile_window.destroy()

    buttons = []
    if owned and not observer and not retired and not sport:
        if getattr(fighter, "serious_injury_pending", False):
            buttons.append(("Review Medical Decision", lambda: navigate("inbox")))
        elif app.fighter_in_closed_player_division(fighter):
            buttons.append(("Move To Active Division", lambda: app.open_weight_class_move_dialog(fighter, profile_window)))
        else:
            buttons.append(("Review Booking" if app.fighter_has_scheduled_fight(fighter, include_booked=True) else "Plan Next Fight", booking))
        buttons.append(("Training Plan", lambda: app.open_fighter_camp_plan(fighter)))
        if not getattr(fighter, "retirement_pending", False):
            buttons.append(("Renew Contract", lambda: app.open_contract_negotiation(fighter, existing=True)))
    buttons.append(("Compare", lambda: compare_picker(app, fighter)))
    action_style = ttk.Style(parent)
    action_style.configure("ProfileAction.TButton", font=("Tahoma", 10, "bold"), padding=(12, 9))
    action_style.configure("ProfilePrimary.TButton", font=("Tahoma", 10, "bold"), padding=(12, 9),
                           background=app.colors["gold"], foreground="#161616")
    action_style.map("ProfilePrimary.TButton", background=[("active", "#f0ca77")], foreground=[("active", "#161616")])
    for index, (title, callback) in enumerate(buttons):
        ttk.Button(actions, text=title, command=callback,
                   style="ProfilePrimary.TButton" if index == 0 else "ProfileAction.TButton").grid(
                       row=index // 2, column=index % 2, sticky="ew", padx=3, pady=3)
    actions.columnconfigure(0, weight=1)
    actions.columnconfigure(1, weight=1)

    section("RECENT FORM • LAST FIVE", "Loading retained fight history...")
    # The owning profile already parses its history once; it fills this label later.
    form_panel = content.winfo_children()[-1]
    form_label = form_panel.winfo_children()[-1]

    if stats_visible and not sport:
        ratings = [("Striking", bounded_profile_metric(getattr(fighter, "striking", 0))),
                   ("Wrestling", bounded_profile_metric(getattr(fighter, "wrestling", 0))),
                   ("Grappling", bounded_profile_metric(getattr(fighter, "grappling", 0))),
                   ("Cardio", bounded_profile_metric(getattr(fighter, "cardio", 0))),
                   ("Chin", bounded_profile_metric(getattr(fighter, "chin", 0))),
                   ("Takedown defence", bounded_profile_metric(getattr(fighter, "takedown_defence", 0))),
                   ("Submission defence", bounded_profile_metric(getattr(fighter, "submission_defence", 0))),
                   ("Fight IQ", bounded_profile_metric(getattr(fighter, "fight_iq", 0)))]
        ordered = sorted(ratings, key=lambda row: row[1], reverse=True)
        assessment = ttk.Frame(content, style="Panel.TFrame")
        layout_items.append(assessment)
        heading = tk.Frame(assessment, bg=app.colors["panel"])
        heading.pack(fill="x", padx=16, pady=(14, 8))
        tk.Frame(heading, bg=app.colors["gold"], width=3, height=17).pack(side="left", padx=(0, 9))
        tk.Label(heading, text="FIGHTER ASSESSMENT", bg=app.colors["panel"], fg=app.colors["text"],
                 font=("Tahoma", 11, "bold"), anchor="w").pack(side="left")
        tk.Label(heading, text="BEST → DEVELOPMENT FOCUS", bg=app.colors["panel"], fg=app.colors["muted"],
                 font=("Tahoma", 7, "bold"), anchor="e").pack(side="right")
        chart = tk.Frame(assessment, bg=app.colors["panel"])
        chart.pack(fill="x", padx=16, pady=(0, 12))
        for index, (name, value) in enumerate(ordered):
            tk.Label(chart, text=name.upper(), bg=app.colors["panel"], fg=app.colors["muted"],
                     font=("Tahoma", 7, "bold"), anchor="w", width=19).grid(row=index, column=0, sticky="w", pady=2)
            canvas = tk.Canvas(chart, height=14, bg=app.colors["panel"], highlightthickness=0)
            canvas.grid(row=index, column=1, sticky="ew", padx=8, pady=2)
            def draw_skill(event, widget=canvas, rating=value):
                width = max(20, event.width)
                widget.delete("all")
                widget.create_rectangle(0, 2, width, 12, fill=app.colors["tree"], outline="")
                widget.create_rectangle(0, 2, width * rating / 100, 12,
                                        fill=app.profile_rating_color(rating), outline="")
            canvas.bind("<Configure>", draw_skill, add="+")
            tk.Label(chart, text=f"{value}  {app.profile_rating_grade(value)}", bg=app.colors["panel"],
                     fg=app.profile_rating_color(value), font=("Tahoma", 8, "bold"), anchor="e", width=15).grid(
                         row=index, column=2, sticky="e", pady=2)
        chart.grid_columnconfigure(1, weight=1)
    else:
        section("ABILITY & INFORMATION", app.scouting_uncertainty_text(report) if not stats_visible else
                "Use the sport-specific ratings and career stage; MMA skill comparisons are not a substitute.")

    layout_items.append(build_trait_card(app, content, fighter, stats_visible))

    threads = app.story_threads_for_fighter(fighter, include_resolved=False)
    threads.sort(key=lambda row: (int(row.get("importance", 1)), int(row.get("last_updated_month", 0)),
                                  int(row.get("last_updated_week", 0))), reverse=True)
    if threads:
        thread = threads[0]
        beats = thread.get("beats", []) or []
        latest = beats[-1].get("summary", "") if beats else ""
        section("CURRENT CHAPTER", f"{thread.get('type', 'Career')} | {str(thread.get('phase', '')).replace('_', ' ')}\n"
                f"{latest}\nStill at stake: {thread.get('stakes') or 'No further stakes recorded.'}")
    else:
        goal = str(getattr(fighter, "career_goal", "") or "").strip() if owned else ""
        section("CURRENT CHAPTER", (f"Current goal: {goal}\n\n" if goal else "") +
                "A new chapter starts here. Results and career decisions in this save will build the timeline.")
    if owned and not retired:
        section("MANAGEMENT SNAPSHOT", f"Contract: {fighter.contract_months} month(s) | ${fighter.purse:,} per fight\n"
                f"Morale {fighter.morale}/100 | Motivation {fighter.motivation}/100\n"
                f"Career goal: {fighter.career_goal or 'Undeclared'}")
    reflow()
    return form_label
