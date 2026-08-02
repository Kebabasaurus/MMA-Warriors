"""Broad, non-destructive application playtest for shipping stability.

This complements smoke_test.py by exercising real event completion, retirement
cleanup, UI viewers, academy/card edge cases, save round-tripping and repeated
world advancement.  It never writes a player save.
"""

import copy
import json
import random
import tempfile
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from main import FightEmpireApp
from models import Fighter, Promotion
from persistence import atomic_write_json_gzip, read_json_text


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def silence_dialogs():
    messagebox.showinfo = lambda *args, **kwargs: None
    messagebox.showwarning = lambda *args, **kwargs: None
    messagebox.showerror = lambda *args, **kwargs: None
    messagebox.askyesno = lambda *args, **kwargs: False
    messagebox.askyesnocancel = lambda *args, **kwargs: False


def new_app(seed):
    random.seed(seed)
    root = tk.Tk()
    root.withdraw()
    app = FightEmpireApp(root)
    app.rules["autosave_enabled"] = False
    callback_errors = []
    root.report_callback_exception = lambda exc, value, tb: callback_errors.append((exc, value, tb))
    return root, app, callback_errors


def close_secondary_windows(root):
    for child in list(root.winfo_children()):
        if isinstance(child, tk.Toplevel):
            child.destroy()
    root.update_idletasks()


def destroy_root(root):
    """Drain pending ttk theme events before destroying one of several test roots."""
    try:
        root.update_idletasks()
        root.update()
    except tk.TclError:
        pass
    root.destroy()


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def ready_pair(app):
    groups = {}
    for fighter in app.roster:
        if not fighter.injured:
            fighter.fatigue = 0
            fighter.available_week = 0
            groups.setdefault((fighter.gender, fighter.weight), []).append(fighter)
    return next((fighters[:2] for fighters in groups.values() if len(fighters) >= 2), None)


def ready_group(app, size=4):
    groups = {}
    for fighter in app.roster:
        if not fighter.injured:
            fighter.fatigue = 0
            fighter.available_week = 0
            groups.setdefault((fighter.gender, fighter.weight), []).append(fighter)
    return next((fighters[:size] for fighters in groups.values() if len(fighters) >= size), None)


def event_for(app, pair, name):
    a, b = pair
    fight = {"fighters": [a.name, b.name], "main": True, "title": False, "interim": False, "tier": "Main Event"}
    event = {
        "name": name,
        "venue": "Regional Arena",
        "region": app.player_region,
        "city": "Las Vegas",
        "month": app.month,
        "week": app.week,
        "broadcaster": app.broadcasters[0]["name"],
        "fights": [fight],
    }
    app.assign_event_camps(event)
    app.scheduled_events.append(event)
    return event


def exercise_extended_title_live_watch(app, root):
    """Advance a configured seven-round title fight without losing lines."""
    pair = ready_pair(app)
    require(pair, "Could not find a legal title-fight pairing")
    a, b = pair
    previous_title_rounds = app.rules.get("title_rounds", 5)
    app.rules["title_rounds"] = 7
    fight = {"fighters": [a.name, b.name], "main": True, "title": True, "interim": False, "tier": "Main Event"}
    event = {
        "name": "Stability Extended Title Event", "venue": "Regional Arena",
        "region": app.player_region, "city": "Las Vegas", "month": app.month,
        "week": app.week, "broadcaster": app.broadcasters[0]["name"], "fights": [fight],
    }
    app.assign_event_camps(event)
    original_stoppage = app.check_fight_stoppage
    original_corner_stoppage = app.check_corner_stoppage
    try:
        # The watcher regression is about the complete extended presentation;
        # keep the fixture on the decision path so every boundary is exercised.
        app.check_fight_stoppage = lambda *args, **kwargs: None
        app.check_corner_stoppage = lambda *args, **kwargs: None
        package = app.prepare_event_result(event)
    finally:
        app.check_fight_stoppage = original_stoppage
        app.check_corner_stoppage = original_corner_stoppage
    log = package["fight_logs"][0]
    require(log.get("title") and len([line for line in log["lines"] if line.startswith("Round ") and "summary:" not in line.lower()]) == 7,
            "Extended title-fight fixture did not produce seven round introductions")
    require(sum(" summary:" in line.lower() for line in log["lines"]) == 7,
            "Extended title-fight fixture did not produce seven round summaries")

    app.open_live_fight_window(event, package, apply_results=False)
    root.update_idletasks()
    live_window = next(
        child for child in root.winfo_children()
        if isinstance(child, tk.Toplevel)
        and any(widget.winfo_class() == "TButton" and widget.cget("text") == "Next Round" for widget in descendants(child))
    )
    commentary = next(widget for widget in descendants(live_window) if widget.winfo_class() == "Text")
    next_round = next(widget for widget in descendants(live_window) if widget.winfo_class() == "TButton" and widget.cget("text") == "Next Round")
    for round_no in range(1, 8):
        next_round.invoke()
        root.update_idletasks()
        rendered = commentary.get("1.0", "end-1c")
        raw_summary = next(line for line in log["lines"] if line.startswith(f"Round {round_no} summary:"))
        expected_summary = app.display_fighter_names_in_text(raw_summary, log)
        require(f"Round {round_no}:" in rendered, f"Live title watch lost Round {round_no}")
        require(expected_summary in rendered, f"Live title watch collapsed Round {round_no} commentary")
        if round_no < 7:
            require("OFFICIAL SCORECARDS - RESULT CONFIRMED" not in rendered,
                    "Live title watch revealed scorecards before the final round")
    # The final-round control stops on the round summary; one more advance
    # carries the watcher through the horn, decision, metrics, and result.
    next_round.invoke()
    root.update_idletasks()
    rendered = commentary.get("1.0", "end-1c")
    require(rendered.count("OFFICIAL SCORECARDS - RESULT CONFIRMED") == 1,
            "Live title watch duplicated or lost the official scorecard reveal")
    require(rendered.count("Judge 1 [") == 1 and "FIGHT METRICS" in rendered and "Result:" in rendered,
            "Live title watch lost final scorecard, metrics, or result text")
    close_secondary_windows(root)
    app.rules["title_rounds"] = previous_title_rounds


def exercise_all_main_screens(app, root):
    for name in app.tab_pages:
        app.select_tab(name)
        app.refresh_all()
        root.update_idletasks()

    fighter = app.roster[0]
    app.open_fighter_profile_window(fighter)
    app.open_regional_identity_window(fighter)

    company_children = app.company_list.get_children("")
    if company_children:
        app.company_list.selection_set(company_children[0])
    app.open_selected_company_hub()

    app.region_list.selection_clear(0, "end")
    app.region_list.selection_set(0)
    app.open_selected_region_hub()

    first_gym = app.gym_tree.get_children()[0]
    app.gym_tree.selection_set(first_gym)
    app.open_selected_gym_viewer()

    app.open_combat_sports_window()
    app.open_world_chronicle()
    app.open_fanbase_window()
    app.open_awards_history_window()
    app.open_achievements_window()
    app.open_records_ledger_window()
    app.open_record_book_window()
    root.update_idletasks()
    close_secondary_windows(root)


def exercise_free_agent_viewport_and_scroll(app, root):
    """Free-agent rows fill the page and wheel input stays inside the list."""
    original_geometry = root.geometry()
    root.geometry("1366x768")
    root.deiconify()
    try:
        app.select_tab("market")
        root.update()
        page = app.tab_pages["market"]
        canvas = page._scroll_canvas
        require(app.market_tree.winfo_height() >= int(canvas.winfo_height() * 0.65), "Free-agent list did not expand to the available screen height")
        require(len(app.market_tree.get_children()) > 20, "Free-agent scroll test did not have enough rows")
        app.market_tree.yview_moveto(0)
        root.update()
        outer_before = canvas.yview()
        tree_before = app.market_tree.yview()
        page.event_generate("<Enter>")
        app.market_tree.event_generate("<MouseWheel>", delta=-120)
        root.update()
        require(app.market_tree.yview() != tree_before, "Mouse wheel did not move through the free-agent list")
        require(canvas.yview() == outer_before, "Mouse wheel moved the whole Free Agents page instead of its list")
        page.event_generate("<Leave>")
    finally:
        root.withdraw()
        root.geometry(original_geometry)


def exercise_media_story_reader(app, root):
    """News briefs retain Chronicle depth and open in a safe, scrollable reader."""
    original_news = list(app.news)
    original_chronicle = list(app.world_chronicle)
    headline = "Stability champion signs landmark media agreement."
    fighter_name = app.roster[0].name
    company_name = app.player_company_name
    long_detail = "\n\n".join(
        f"Paragraph {index}: {fighter_name} discusses preparation, divisional stakes, and the future of {company_name}."
        for index in range(1, 81)
    )
    structured = {
        "month": 19,
        "week": 3,
        "year": 2027,
        "type": "Media",
        "headline": headline,
        "detail": long_detail,
        "companies": [company_name],
        "fighters": [fighter_name],
        "importance": 4,
    }
    legacy = "A legacy string-only scouting update reached the media desk."
    try:
        app.news = [headline, legacy]
        app.world_chronicle = [structured]
        app.website_news.selection_remove(app.website_news.selection())
        app.refresh_website()
        root.update_idletasks()

        entries = app._website_news_entries
        require(len(entries) == 2, "Media Desk did not adapt every current news story")
        rich = entries[0]
        require(rich.get("detail") == long_detail, "Chronicle detail was lost when its headline entered the Media Desk")
        require((rich.get("year"), rich.get("month"), rich.get("week")) == (2027, 19, 3), "Chronicle story date was lost")
        require(rich.get("fighters") == [fighter_name] and rich.get("companies") == [company_name], "Chronicle story entities were lost")
        require(entries[1].get("headline") == legacy and entries[1].get("detail") == legacy, "Legacy news did not receive a safe reader fallback")

        rows = app.website_news.get_children()
        require(rows == ("story:0", "story:1"), "Media Desk story table did not populate in news order")
        app.website_news.selection_set("story:0")
        app.show_selected_media_story()
        preview = app.website_news_preview.get("1.0", "end-1c")
        require(headline in preview and long_detail in preview, "Selected story preview omitted the headline or full detail")
        require("Jul W3 2027" in preview, "Selected story preview omitted the Chronicle date")

        app.website_news.selection_remove(app.website_news.selection())
        require(app.selected_media_story_entry() is None, "Empty Media Desk selection returned a story")
        before_windows = set(root.winfo_children())
        app.show_selected_media_story()
        app.open_selected_news_story()
        app.open_selected_story_context()
        root.update_idletasks()
        require(set(root.winfo_children()) == before_windows, "Empty Media Desk selection opened an unexpected window")
        require("Select a headline" in app.website_news_preview.get("1.0", "end-1c"), "Empty selection did not show the safe preview prompt")

        app.website_news.selection_set("story:0")
        app.show_selected_media_story()
        world_before = json.dumps(app.serialize_world(), sort_keys=True)
        # serialize_world currently performs legacy division repairs and may
        # consume RNG; capture the UI-isolation baseline after that known work.
        rng_before = random.getstate()
        app.open_selected_news_story()
        root.update()
        reader = getattr(app, "_news_reader_window", None)
        require(isinstance(reader, tk.Toplevel) and reader.winfo_exists(), "Full news reader did not open")
        reader.update_idletasks()
        require(reader.winfo_width() <= 860 and reader.winfo_height() <= 620, "News reader exceeded its laptop-safe maximum size")
        min_width, min_height = reader.minsize()
        require(min_width <= 650 and min_height <= 470, "News reader minimum size is unsafe for a laptop display")
        reader_texts = [widget for widget in descendants(reader) if isinstance(widget, tk.Text)]
        require(len(reader_texts) == 1, "News reader did not expose one clear story body")
        body = reader_texts[0]
        require(long_detail in body.get("1.0", "end-1c"), "Full news reader omitted the Chronicle article body")
        require(body.cget("yscrollcommand"), "Full news reader body is not connected to a scrollbar")
        require(any(widget.winfo_class() == "TScrollbar" and str(widget.cget("orient")) == "vertical" for widget in descendants(reader)), "Full news reader has no vertical scrollbar")
        require(body.yview()[1] < 1.0, "Long news story did not require scrolling")
        require(random.getstate() == rng_before, "Opening a news story consumed simulation RNG")
        require(json.dumps(app.serialize_world(), sort_keys=True) == world_before, "Opening a news story mutated persisted world data")
    finally:
        reader = getattr(app, "_news_reader_window", None)
        if reader is not None:
            try:
                reader.destroy()
            except tk.TclError:
                pass
        app._news_reader_window = None
        app.news = original_news
        app.world_chronicle = original_chronicle
        app.refresh_website()
        root.update_idletasks()


def exercise_normal_and_retirement_events(app, root):
    pair = ready_pair(app)
    require(pair, "Could not find a legal player event pairing")
    normal = event_for(app, pair, "Stability Normal Event")
    package = app.prepare_event_result(normal)
    require(package.get("fight_logs"), "Normal event produced no fight logs")
    require(any("cut penalty" in line for line in package["fight_logs"][0]["lines"]), "Event readiness line missing")
    app.open_live_fight_window(normal, package, apply_results=False)
    root.update_idletasks()
    live_window = next(
        child for child in root.winfo_children()
        if isinstance(child, tk.Toplevel)
        and any(widget.winfo_class() == "TButton" and widget.cget("text") == "Skip Event" for widget in descendants(child))
    )
    require(live_window.winfo_width() <= live_window.winfo_screenwidth() and live_window.winfo_height() <= live_window.winfo_screenheight(), "Live fight viewer exceeds the laptop screen")
    live_widgets = list(descendants(live_window))
    require(sum(1 for widget in live_widgets if widget.winfo_class() == "TScrollbar") >= 2, "Live fight viewer needs visible bout-list and commentary scrollbars")
    commentary = next((widget for widget in live_widgets if widget.winfo_class() == "Text"), None)
    require(commentary is not None and "courier" not in str(commentary.cget("font")).lower(), "Fight commentary should use a readable proportional font")
    require(any(widget.winfo_class() == "TButton" and widget.cget("text") == "Text +" for widget in live_widgets), "Live fight viewer text zoom controls missing")
    require(any(widget.winfo_class() == "TButton" and widget.cget("text") == "Review Selected Bout" for widget in live_widgets), "Live fight viewer cannot reopen completed-bout commentary")
    live_checks = {widget.cget("text"): widget for widget in live_widgets if widget.winfo_class() == "TCheckbutton"}
    require("Auto-play card" in live_checks and "Follow live" in live_checks, "Live fight viewer preference controls missing")
    require(bool(int(live_checks["Auto-play card"].getvar(live_checks["Auto-play card"].cget("variable")))) == bool(app.rules.get("live_auto_play_card", False)), "Auto-play preference did not persist into the next fight-night window")
    require(bool(int(live_checks["Follow live"].getvar(live_checks["Follow live"].cget("variable")))) == bool(app.rules.get("live_follow_commentary", True)), "Follow-live preference did not persist into the next fight-night window")
    play = next((widget for widget in live_widgets if widget.winfo_class() == "TButton" and widget.cget("text") == "Play Fight"), None)
    require(play is not None, "Live fight viewer did not expose playback")
    play.invoke()
    root.update_idletasks()
    first_playback = commentary.get("1.0", "end")
    require(len(first_playback.strip().splitlines()) >= 3, "Play Fight stopped before playback began")
    play.invoke()
    root.update_idletasks()
    require(commentary.get("1.0", "end") == first_playback, "Repeated Play created a duplicate playback chain")
    skip = next((widget for widget in descendants(live_window) if widget.winfo_class() == "TButton" and widget.cget("text") == "Skip Event"), None)
    require(skip is not None, "Live fight viewer did not expose Skip Event")
    skip.invoke()
    root.update_idletasks()
    close_secondary_windows(root)
    app.finish_event(normal, package)
    require(any(record.get("event") == "Stability Normal Event" for record in app.result_records), "Normal event did not finish")

    field = ready_group(app, 4)
    require(field, "Could not find a four-fighter tournament field")
    tournament_fight = {
        "fighters": [field[0].name, field[-1].name],
        "tournament": True,
        "tournament_size": 4,
        "tournament_entrants": [fighter.name for fighter in field],
        "tournament_weight": field[0].weight,
        "tournament_gender": field[0].gender,
        "tournament_name": "Stability Grand Prix",
        "main": True, "title": False, "interim": False, "tier": "Main Event",
    }
    tournament_event = {
        "name": "Stability Tournament Event", "venue": "Regional Arena",
        "region": app.player_region, "city": "Las Vegas", "month": app.month,
        "week": app.week, "broadcaster": app.broadcasters[0]["name"],
        "fights": [tournament_fight],
    }
    app.assign_event_camps(tournament_event)
    app.scheduled_events.append(tournament_event)
    fatigue_before = {fighter.name: fighter.fatigue for fighter in field}
    career_stats_before = {fighter.name: fighter.career_stat_fights for fighter in field}
    tournament_package = app.prepare_event_result(tournament_event)
    require(len(tournament_package.get("results", [])) == 3, "Four-fighter tournament did not generate three career bouts")
    require(len(tournament_package.get("fight_logs", [])) == 3, "Tournament did not generate a live log for every bout")
    require(tournament_package.get("tournament_brackets", [{}])[0].get("champion"), "Tournament bracket has no champion")
    require(all(fighter.fatigue == fatigue_before[fighter.name] for fighter in field), "Tournament preparation leaked cumulative fatigue into the live world")
    app.open_event_tournament_bracket(tournament_package)
    bracket_window = next((child for child in root.winfo_children() if isinstance(child, tk.Toplevel) and child.title() == "Tournament Bracket"), None)
    require(bracket_window is not None, "Tournament bracket viewer did not open")
    root.update_idletasks()
    close_secondary_windows(root)
    root.deiconify()
    app.show_event_summary(tournament_package)
    root.update_idletasks()
    summary_window = next((child for child in root.winfo_children() if isinstance(child, tk.Toplevel) and child.title() == "End of Event"), None)
    require(summary_window is not None, "End-of-event card recap did not open")
    require(any(widget.winfo_class() == "Treeview" for widget in descendants(summary_window)), "End-of-event recap has no card-results table")
    close_secondary_windows(root)
    root.withdraw()
    app.finish_event(tournament_event, tournament_package)
    tournament_record = next((record for record in app.result_records if record.get("event") == "Stability Tournament Event"), None)
    require(tournament_record and tournament_record.get("tournament_brackets"), "Completed event did not retain its tournament bracket")
    require(any("Won Stability Grand Prix" in achievement for fighter in field for achievement in (fighter.career_achievements or [])), "Tournament champion achievement was not applied")
    appearances = {fighter.name: 0 for fighter in field}
    for winner, loser, _fight, _method in tournament_package["results"]:
        if winner.name in appearances:
            appearances[winner.name] += 1
        if loser.name in appearances:
            appearances[loser.name] += 1
    require(all(fighter.career_stat_fights - career_stats_before[fighter.name] == appearances[fighter.name] for fighter in field), "Tournament bout box scores were not committed once per appearance")
    champion_name = tournament_package["tournament_brackets"][0]["champion"]
    champion = next(fighter for fighter in field if fighter.name == champion_name)
    expected_opponents = {
        loser.name if winner is champion else winner.name
        for winner, loser, _fight, _method in tournament_package["results"]
        if champion in (winner, loser)
    }
    # Event completion prepends one history row per tournament appearance. A
    # fighter may also have faced the same opponent on another card that week,
    # so date/name filtering would incorrectly count that older bout as part of
    # this tournament.
    tournament_entries = list(champion.fight_history[:appearances[champion.name]])
    resolved_opponents = {
        app.fighter_history_card_context(champion, entry, app.fighter_history_opponent_name(champion, entry)).get("opponent_name")
        for entry in tournament_entries
    }
    require(
        len(tournament_entries) == 2 and resolved_opponents == expected_opponents,
        f"Same-night tournament bouts collapsed into one fighter-history row: champion={champion.name}, expected={expected_opponents}, resolved={resolved_opponents}, entries={tournament_entries}",
    )
    require(all("scorecards" in log for log in tournament_package["fight_logs"]), "Tournament history logs omitted scorecard metadata")
    close_secondary_windows(root)

    pair = ready_pair(app)
    require(pair, "Could not find retirement event pairing")
    retiree = pair[0]
    app.mark_retirement_fight_required(retiree, "Stability test")
    retirement = event_for(app, pair, "Stability Retirement Event")
    retirement_package = app.prepare_event_result(retirement)
    app.finish_event(retirement, retirement_package)
    require(retiree.retired and retiree in app.retired_fighters, "Retirement fighter was not retired after the event")
    require(retiree not in app.roster, "Retirement fighter remained on active roster")

    app.open_result_card_window(app.result_records[0])
    app.open_event_replay_window("Stability Replay", retirement_package)
    root.update_idletasks()
    close_secondary_windows(root)


def exercise_month_tracking(app):
    app.result_records.insert(0, {
        "date": f"Month {app.month} Week 2", "company": app.player_company_name,
        "event": "Month Tracking", "summary": "Recorded player event",
    })
    require(app.player_ran_show_in_month(app.month), "Recorded player show was not detected")
    captured = []
    app.week = 4
    app.world_week_steps = lambda: []
    app.world_month_steps = lambda player_ran_show: (captured.append(player_ran_show) or [])
    app.monthly_player_business_steps = lambda: []
    app.refresh_all = lambda: None
    app.write_log = lambda: None
    app.run_automatic_save_cycle = lambda month_changed=False: (None, None)
    app.advance_month()
    require(captured == [True], "Month rollover incorrectly treated an active player as quiet")


def exercise_responsive_advance(app, root):
    """The Tk queue must remain live during normal, month-end and fast-forward work."""

    def run_case(label, starter):
        start = (app.month, app.week)
        heartbeat_times = []
        interaction_seen = [False]
        heartbeat_after = [None]

        def heartbeat():
            heartbeat_after[0] = None
            if app._advance_in_progress:
                heartbeat_times.append(time.monotonic())
                heartbeat_after[0] = root.after(20, heartbeat)

        def simulated_interaction():
            if app._advance_in_progress:
                interaction_seen[0] = True

        heartbeat_after[0] = root.after(20, heartbeat)
        root.after(35, simulated_interaction)
        require(starter(), f"{label} responsive advance did not start")
        started = time.monotonic()
        while app._advance_in_progress and time.monotonic() - started < 180:
            root.update()
            time.sleep(0.001)
        require(not app._advance_in_progress, f"{label} responsive advance did not complete")
        if heartbeat_after[0]:
            root.after_cancel(heartbeat_after[0])
        require((app.month, app.week) != start, f"{label} responsive advance did not change the date")
        require(len(heartbeat_times) >= 2, f"Tk event queue was starved during {label} advance")
        require(interaction_seen[0], f"A queued UI interaction did not run during {label} advance")
        gaps = [later - earlier for earlier, later in zip(heartbeat_times, heartbeat_times[1:])]
        require(not gaps or max(gaps) < 2.0, f"{label} advance blocked Tk for {max(gaps):.2f}s")

    run_case("normal week", app.request_advance_week)
    app.week = 4
    run_case("month boundary", app.request_advance_week)
    app.spectator_mode = True
    run_case("spectator batch", lambda: app.spectator_advance_weeks(4, "Stability spectator run"))
    app.spectator_mode = False
    require(not app.advance_progress.winfo_manager(), "Advance progress remained visible after completion")
    require(str(app.advance_button.cget("state")) == "normal", "Advance button remained disabled")


def exercise_academy_and_sport_edge_cases(app):
    # Repairing old saves is also performed by read-only UI paths.  It must be
    # deterministic and must not consume randomness that belongs to the world
    # or fight simulations.
    legacy = {
        "owned": True,
        "prospects": [{"name": "Legacy Academy Prospect", "region": app.player_region}],
        "talent_pool": [],
    }
    random.seed(73191)
    rng_before = random.getstate()
    repaired = app.repair_academy(legacy)
    rng_after = random.getstate()
    first_repair = json.loads(json.dumps(repaired))
    app.repair_academy(repaired)
    require(rng_after == rng_before == random.getstate(), "Academy legacy repair consumed the simulation RNG")
    require(json.loads(json.dumps(repaired)) == first_repair, "Academy legacy repair was not deterministic or idempotent")
    require(repaired.get("schema_version") == 5, "Academy legacy repair did not migrate the schema version")
    require(repaired.get("auto_card_min_bouts") == 2, "Academy legacy repair did not add the auto-card fight threshold")
    require(repaired.get("showcase_weeks") >= 6, "Legacy academy retained the overactive two-week showcase schedule")
    require(repaired["prospects"][0].get("prospect_id"), "Academy legacy repair did not create a stable prospect ID")
    require(repaired["prospects"][0].get("amateur_bout_records") == [], "Academy legacy repair did not add structured amateur records")

    academy = app.academy_defaults()
    academy.update({"owned": True, "level": 1, "capacity": 8, "weekly_cost": 4500})
    prospect = app.create_academy_scout_prospect(70, region=app.player_region)
    prospect["gender"] = "Female"
    prospect["fatigue"] = 0
    prospect["injured"] = 0
    academy["prospects"] = [prospect]
    app.academy = academy
    results = app.run_academy_showcase_card(academy)
    require(len(results) == 1, "An isolated academy prospect still could not obtain a guest bout")
    require(app.academy_amateur_fight_count(prospect) == 1, "Academy guest bout did not update the owned prospect")
    require(academy.get("card_history") and academy["card_history"][0].get("fight_logs"), "Academy card did not retain a replay")
    require(len(academy["card_history"][0]["fight_logs"][0].get("lines", [])) >= 20, "Academy bout did not use the detailed fight engine")
    require(academy.get("total_bouts") == 1 and academy.get("total_cards") == 1, "Academy career totals were not updated")
    require(0 <= app.academy_graduation_readiness(prospect) <= 100, "Academy graduation readiness is invalid")
    lead = app.create_academy_scout_prospect(72, region=app.player_region)
    confidence = lead["scout_confidence"]
    app.refine_academy_lead(lead, academy)
    require(lead["scout_confidence"] > confidence, "Academy scout report did not improve while observed")
    require(app.academy_preferred_sport(prospect) in ("MMA", "Boxing", "Kickboxing", "Muay Thai", "Wrestling", "Brazilian Jiu-Jitsu"), "Academy pathway recommendation is invalid")

    # A full academy must put all eight healthy, rested members into bouts.  A
    # second card in the same week must not let any of them fight twice.
    full_academy = app.academy_defaults()
    full_academy.update({"owned": True, "level": 3, "capacity": 8, "weekly_cost": 8500})
    full_prospects = []
    for index in range(8):
        item = app.create_academy_scout_prospect(70, region=app.player_region)
        item.update({
            "name": f"Stability Academy Prospect {index + 1}", "age": 16,
            "gender": "Male", "weight": "Lightweight", "amateur_weight": "Youth Lightweight",
            "fatigue": 0, "injured": 0, "last_amateur_week": -99, "academy_member": True,
        })
        app.repair_academy_prospect(item)
        full_prospects.append(item)
    full_academy["prospects"] = full_prospects
    full_academy["development_events"] = [{"month": app.month, "week": app.week, "note": "Stability academy baseline"}]
    app.academy = full_academy
    full_results = app.run_academy_showcase_card(full_academy)
    require(len(full_results) == 4, "Eight-prospect academy card did not produce four bouts")
    require(all(app.academy_amateur_fight_count(item) == 1 for item in full_prospects), "Not every academy prospect fought exactly once on the full card")
    require(len({record["opponent"] for item in full_prospects for record in item["amateur_bout_records"]}) >= 4, "Academy structured records did not retain opponents")
    require(all(len(item["amateur_bout_records"]) == 1 for item in full_prospects), "Academy bout did not create exactly one structured record per participant")
    require(all(item["amateur_bout_records"][0].get("result") in ("W", "L", "D") for item in full_prospects), "Academy structured records contain an invalid W/L/D result")
    require(
        all(
            sum(item.get(key, 0) for key in ("amateur_w", "amateur_l", "amateur_d")) == len(item["amateur_bout_records"])
            for item in full_prospects
        ),
        "Academy structured W/L/D records disagree with the career totals",
    )
    totals_before_cooldown = (full_academy["total_cards"], full_academy["total_bouts"])
    require(app.run_academy_showcase_card(full_academy) == [], "Academy prospects were allowed to fight twice in the same week")
    require((full_academy["total_cards"], full_academy["total_bouts"]) == totals_before_cooldown, "A blocked same-week academy card changed career totals")
    saved_date = (app.month, app.week)
    first_card_week = app.calendar_week_index()
    app.month, app.week = (first_card_week + 5 - 1) // 4 + 1, (first_card_week + 5 - 1) % 4 + 1
    require(app.run_academy_showcase_card(full_academy) == [], "Academy prospects bypassed the six-week individual bout recovery rule")
    app.month, app.week = (first_card_week + 6 - 1) // 4 + 1, (first_card_week + 6 - 1) % 4 + 1
    require(len(app.run_academy_showcase_card(full_academy)) == 4, "Recovered academy prospects were not eligible after six weeks")
    app.month, app.week = saved_date

    # Academy decisions add player agency between cards without bypassing the
    # normal prospect ledger. The low-risk coaching choice should resolve,
    # improve the prospect, and remain in the academy story history.
    full_academy["active_challenge"] = {}
    challenge = app.create_academy_challenge(full_academy)
    require(challenge and challenge.get("prospect_id"), "Academy did not surface a development challenge")
    challenged = next(item for item in full_academy["prospects"] if item.get("prospect_id") == challenge["prospect_id"])
    confidence_before = challenged.get("confidence", 0)
    ok, challenge_note = app.resolve_academy_challenge("mentor", full_academy)
    require(ok and challenge_note and not full_academy.get("active_challenge"), "Academy challenge did not resolve through the coaching choice")
    require(challenged.get("confidence", 0) >= confidence_before, "Academy coaching decision reduced confidence unexpectedly")
    require(full_academy.get("challenge_history") and full_academy["challenge_history"][0].get("choice") == "mentor", "Academy challenge resolution was not recorded")

    # Scout quality should affect the distribution, not guarantee an elite lead
    # on each individual roll.  Fixed seeds keep this statistical check stable.
    def scouting_sample(seed, scout_score, size=96):
        random.seed(seed)
        sample = [app.create_academy_scout_prospect(scout_score, region=app.player_region) for _ in range(size)]
        return {
            "potential": sum(item["potential"] for item in sample) / size,
            "rating": sum(item["rating"] for item in sample) / size,
            "confidence": sum(item["scout_confidence"] for item in sample) / size,
        }

    low_scout = scouting_sample(48120, 35)
    elite_scout = scouting_sample(48120, 88)
    require(elite_scout["potential"] >= low_scout["potential"] + 5, "Elite scout did not materially improve the prospect-potential distribution")
    require(elite_scout["rating"] >= low_scout["rating"] + 2, "Elite scout did not improve the current-ability distribution")
    require(elite_scout["confidence"] >= low_scout["confidence"] + 25, "Elite scout reports were not materially more confident")

    # The 16-year minimum is a domain rule, not merely a disabled UI button. Once eligible,
    # conversion must preserve the identity and skill profile the player built.
    graduate = {
        "name": "Stability Academy Graduate", "age": 15, "potential": 91,
        "region": app.player_region, "gender": "Male", "weight": "Welterweight",
        "rating": 68, "style": "Pressure Wrestler", "stance": "Southpaw", "trait": "Iron Will",
        "striking": 64, "wrestling": 78, "grappling": 73, "cardio": 76,
        "chin": 69, "power": 71, "toughness": 82, "fight_iq": 79,
        "dedication": 87, "coachability": 84, "confidence": 74,
        "amateur_w": 7, "amateur_l": 2, "amateur_d": 1,
        "amateur_history": ["Stability amateur history"],
    }
    app.repair_academy_prospect(graduate)
    roster_before = len(app.roster)
    graduates_before = full_academy["total_graduates"]
    ok, _message, fighter = app.promote_academy_prospect_to_sport(graduate, "MMA")
    require(not ok and fighter is None, "Under-16 academy prospect bypassed the professional graduation guard")
    require(len(app.roster) == roster_before and full_academy["total_graduates"] == graduates_before, "Rejected under-16 graduation changed the professional world")
    graduate["age"] = 16
    ok, _message, fighter = app.promote_academy_prospect_to_sport(graduate, "MMA")
    require(ok and fighter is app.roster[-1], "Eligible academy prospect did not graduate into MMA")
    require((fighter.style, fighter.stance, fighter.trait) == (graduate["style"], graduate["stance"], graduate["trait"]), "Academy graduation lost style, stance, or trait")
    require(
        (fighter.striking, fighter.wrestling, fighter.grappling, fighter.cardio, fighter.chin, fighter.power, fighter.toughness, fighter.fight_iq)
        == tuple(graduate[key] for key in ("striking", "wrestling", "grappling", "cardio", "chin", "power", "toughness", "fight_iq")),
        "Academy graduation changed the developed core skill profile",
    )
    require(fighter.detailed_skills.get("footwork") == graduate["striking"], "Academy graduation did not map striking into detailed standing skills")
    require(fighter.detailed_skills.get("takedowns") == graduate["wrestling"], "Academy graduation did not map wrestling into detailed wrestling skills")
    require(fighter.detailed_skills.get("guard_work") == graduate["grappling"], "Academy graduation did not map grappling into detailed ground skills")
    require(fighter.detailed_skills.get("conditioning") == graduate["cardio"], "Academy graduation did not preserve detailed conditioning")
    require(fighter.detailed_skills.get("resilience") == graduate["toughness"], "Academy graduation did not preserve detailed resilience")
    require(fighter.detailed_skills.get("dedication") == graduate["dedication"], "Academy graduation did not preserve detailed dedication")
    require(full_academy["alumni"][0]["amateur_record"] == "7-2-1", "Academy graduate alumni record lost structured W/L/D totals")

    sport = "Boxing"
    world = app.combat_sport_worlds[sport]
    athlete = world["roster"][0]
    original_employer = athlete.sport_employer
    athlete.sport_employer = "Stability Child Division"
    athlete.fatigue = 0
    athlete.injured = 0
    athlete.available_week = 0
    bouts = app.build_combat_sport_card(sport, world, athlete.sport_employer, player_owned=False, target_bouts=1)
    require(len(bouts) == 1, "An isolated combat-sport athlete still could not obtain a guest bout")
    require(bouts[0]["b"].sport_employer.startswith("Independent"), "Combat-sport fallback was not an independent opponent")
    result = app.apply_combat_sport_result(sport, world, bouts[0]["a"], bouts[0]["b"])
    require(result.get("log") and result.get("weight") == app.combat_sport_competition_class(sport, athlete), "Guest sport bout did not complete with corrected division replay metadata")
    athlete.sport_employer = original_employer


def exercise_save_roundtrip(app):
    app.rules.update({"autosave_weekly_keep": 12, "autosave_monthly_keep": 24, "save_backup_keep": 60, "save_retention_version": 1})
    app.ensure_rule_defaults()
    require(
        (app.rules["autosave_weekly_keep"], app.rules["autosave_monthly_keep"], app.rules["save_backup_keep"]) == (2, 2, 2),
        "Legacy save retention was not migrated to two rolling slots",
    )
    replay_package = {
        "date": "Month 1 Week 1", "company": "Stability AI", "event_name": "Archive Link Test",
        "log": ["Full commentary line one", "Full commentary line two"],
        "fight_logs": [{"heading": "A vs B", "lines": ["Exchange", "Result"]}],
    }
    app.ai_event_archive.insert(0, replay_package)
    app.result_records.insert(0, {
        "date": replay_package["date"], "company": replay_package["company"], "event": replay_package["event_name"],
        "summary": "Archive link test", "log": replay_package["log"], "fight_logs": replay_package["fight_logs"],
    })
    serialized = app.serialize_world()
    serialized_academy = serialized.get("academy", {})
    require(serialized_academy.get("schema_version") == 5, "Academy schema version was omitted from the save payload")
    require(len(serialized_academy.get("prospects", [])) == 8, "Full academy roster was omitted from the save payload")
    require(all(item.get("prospect_id") for item in serialized_academy["prospects"]), "Academy prospect IDs were omitted from the save payload")
    require(all(item.get("amateur_bout_records") for item in serialized_academy["prospects"]), "Structured amateur records were omitted from the save payload")
    require(serialized_academy.get("development_events"), "Academy development events were omitted from the save payload")
    latest_academy_bout_week = max(
        int(item.get("last_amateur_week", -99) or -99)
        for item in serialized_academy["prospects"]
    )
    require(
        serialized_academy.get("last_showcase_week") == latest_academy_bout_week,
        "Academy showcase timing was omitted from the save payload",
    )
    expected_academy_ids = [item["prospect_id"] for item in serialized_academy["prospects"]]
    expected_academy_records = {
        item["prospect_id"]: list(item["amateur_bout_records"])
        for item in serialized_academy["prospects"]
    }
    expected_academy_totals = (serialized_academy["total_cards"], serialized_academy["total_bouts"], serialized_academy["total_graduates"])
    saved_replay = serialized["result_records"][0]
    require(saved_replay.get("_archive_ref") and "log" not in saved_replay and "fight_logs" not in saved_replay, "AI replay detail was duplicated in the save payload")
    encoded = json.dumps(serialized)
    payload = json.loads(encoded)
    with tempfile.TemporaryDirectory() as folder:
        compressed = Path(folder) / "stability_autosave.json.gz"
        atomic_write_json_gzip(compressed, payload)
        require(json.loads(read_json_text(compressed))["month"] == payload["month"], "Compressed autosave could not be read back")
        require(compressed.stat().st_size < len(encoded) * 0.5, "Compressed autosave did not materially reduce storage")
    root2, loaded, callback_errors = new_app(9917)
    try:
        loaded.apply_world_data(payload)
        loaded.refresh_all()
        require(len(loaded.roster) == len(app.roster), "Save roundtrip changed player roster size")
        require(len(loaded.promotions) == len(app.promotions), "Save roundtrip changed promotion count")
        restored_replay = loaded.result_records[0]
        require(restored_replay.get("log") == replay_package["log"] and restored_replay.get("fight_logs") == replay_package["fight_logs"], "Archived replay detail was not restored after load")
        loaded_academy = loaded.academy
        require(loaded_academy.get("schema_version") == 5, "Academy schema version did not survive save roundtrip")
        require(loaded_academy.get("challenge_history") == serialized_academy.get("challenge_history"), "Academy challenge history changed after save roundtrip")
        require([item.get("prospect_id") for item in loaded_academy.get("prospects", [])] == expected_academy_ids, "Academy prospect identity changed after save roundtrip")
        require(
            {item["prospect_id"]: item.get("amateur_bout_records", []) for item in loaded_academy["prospects"]} == expected_academy_records,
            "Structured amateur records changed after save roundtrip",
        )
        require(
            (loaded_academy.get("total_cards"), loaded_academy.get("total_bouts"), loaded_academy.get("total_graduates")) == expected_academy_totals,
            "Academy card or graduation totals changed after save roundtrip",
        )
        require(loaded_academy.get("development_events") == serialized_academy["development_events"], "Academy development events changed after save roundtrip")
        require(loaded_academy.get("last_showcase_week") == serialized_academy["last_showcase_week"], "Academy showcase cooldown changed after save roundtrip")
        require(loaded_academy.get("alumni", [{}])[0].get("amateur_record") == "7-2-1", "Academy alumni record changed after save roundtrip")
        require(not callback_errors, f"Save roundtrip UI callback error: {callback_errors[0][1] if callback_errors else ''}")
    finally:
        destroy_root(root2)


def exercise_talent_ecosystem_balance(app):
    """Protect the long-save talent distribution without scripting fight results."""
    random_state = random.getstate()
    saved_date = (app.month, app.week)
    saved_free_agents = app.free_agents
    try:
        # Pooled across several streams rather than one. Name generation runs
        # before the potential roll and consumes a variable amount of the
        # random stream, so a single fixed seed silently re-rolls this whole
        # distribution whenever the seeded name pool changes size -- which made
        # the rarest bucket drift below its floor on an unrelated data change.
        sample = []
        for seed in (77241, 4415, 90233):
            random.seed(seed)
            used_names = app.active_fighter_names()
            sample.extend(
                app.create_regional_feeder_fighter(
                    "USA", used_names, "Female" if index % 4 == 0 else "Male"
                )
                for index in range(400)
            )
        potentials = [fighter.potential for fighter in sample]
        mean_potential = sum(potentials) / len(potentials)
        require(76 <= mean_potential <= 82, "Regional intake potential distribution is too weak or inflated")
        require(24 <= sum(value >= 90 for value in potentials) <= 120, "Elite regional ceilings are missing or too common")
        require(6 <= sum(value >= 95 for value in potentials) <= 48, "Generational regional ceilings are missing or too common")
        require(all(17 <= fighter.age <= 21 and fighter.overall < fighter.potential for fighter in sample), "Regional intake age or development runway is invalid")

        # Spread the development cohort across all three intake streams and
        # decouple career outcomes from variable name-generation retries.
        cohort = sample[::7][:160]
        starting = [fighter.overall for fighter in cohort]
        random.seed(667120)
        for month in range(1, 121):
            app.month, app.week = month, 1
            app.age_and_develop_fighters(cohort)
            if month % 12 == 0:
                for fighter in cohort:
                    fighter.age += 1
        ending = [fighter.overall for fighter in cohort]
        mean_gain = sum(end - start for start, end in zip(starting, ending)) / len(cohort)
        require(12 <= mean_gain <= 23, "Ten-year regional development is stagnant or excessively fast")
        require(sum(value >= 70 for value in ending) >= len(cohort) * 0.70, "Too few regional fighters mature into credible professionals")
        require(len(cohort) * 0.08 <= sum(value >= 80 for value in ending) <= len(cohort) * 0.35, "High-level regional development is missing or overproduced")
        require(sum(value >= 90 for value in ending) <= len(cohort) * 0.05, "Elite development has become commonplace")
        require(all(fighter.overall <= fighter.potential for fighter in cohort), "Development exceeded a fighter's potential ceiling")

        retirement_probes = [copy.deepcopy(fighter) for fighter in sample[:3]]
        for fighter, age, waiting in zip(retirement_probes, (39, 40, 43), (11, 6, 3)):
            fighter.age = age
            fighter.free_agent_months = waiting
            fighter.retirement_pending = True
            fighter.injured = 0
            fighter.fatigue = 0
            fighter.ai_offer_company = ""
            fighter.available_week = 0
            fighter.showcase_last_month = -99
        app.free_agents = retirement_probes
        eligible_ids = {fighter.fighter_id for fighter in app.eligible_free_agent_retirement_card_fighters()}
        require(retirement_probes[0].fighter_id not in eligible_ids, "Under-40 retirement card bypassed its twelve-month market wait")
        require(retirement_probes[1].fighter_id in eligible_ids, "Age-40 retirement card did not use the six-month market limit")
        require(retirement_probes[2].fighter_id in eligible_ids, "Age-43 retirement card did not use the three-month market limit")
    finally:
        app.month, app.week = saved_date
        app.free_agents = saved_free_agents
        random.setstate(random_state)


def exercise_optimized_autosave_cycle(app):
    """Automatic saves occur once after each pair of completed months."""
    original_serialize = app.serialize_world
    original_write = app.write_rolling_autosave
    serialize_calls = [0]
    writes = []

    def counted_serialize():
        serialize_calls[0] += 1
        return original_serialize()

    def capture_write(kind="weekly", snapshot=None):
        require(snapshot is not None, "Autosave writer did not receive a shared snapshot")
        writes.append((kind, id(snapshot), snapshot.get("month"), snapshot.get("week")))
        return Path(f"captured_{kind}.json.gz")

    app.serialize_world = counted_serialize
    app.write_rolling_autosave = capture_write
    app.rules["autosave_enabled"] = True
    original_month = app.month
    original_week = app.week
    try:
        app.month, app.week = 1, 4
        labels, _ = app.calendar_week_steps()
        require("Creating autosave" not in [label for label, _task in labels], "Calendar scheduled an autosave after only one month")
        app.month, app.week = 2, 4
        labels, _ = app.calendar_week_steps()
        require("Creating autosave" in [label for label, _task in labels], "Calendar did not schedule the two-month autosave")
        app.month = 2
        app.run_automatic_save_cycle(month_changed=True)
        require(not writes and serialize_calls[0] == 0, "Autosave ran after only one completed month")
        app.month = 3
        app.run_automatic_save_cycle(month_changed=True)
    finally:
        app.month = original_month
        app.week = original_week
        app.serialize_world = original_serialize
        app.write_rolling_autosave = original_write
        app.rules["autosave_enabled"] = False
    require(serialize_calls[0] == 1, "Month-end autosave serialized the world more than once")
    require([item[0] for item in writes] == ["monthly"], "Two-month autosave wrote more than one rolling file")


def exercise_retirement_card_pipeline():
    """Long-waiting retirees receive limited, legal farewell cards and no renewals."""
    root, app, callback_errors = new_app(7724)
    try:
        app.month, app.week = 40, 4
        template = app.free_agents[0]
        cohort = []
        for index in range(26):
            fighter = copy.deepcopy(template)
            fighter.name = f"Retirement Card Probe {index:02d}"
            fighter.gender = "Male"
            fighter.weight = "Welterweight"
            fighter.popularity = 100 - index
            skill_shift = index % 4
            fighter.striking = max(35, min(95, fighter.striking + skill_shift))
            fighter.wrestling = max(35, min(95, fighter.wrestling + skill_shift))
            fighter.grappling = max(35, min(95, fighter.grappling + skill_shift))
            fighter.retired = False
            fighter.age = 39
            fighter.retirement_pending = True
            fighter.retirement_fight_completed = False
            fighter.retirement_requested_month = app.month - 12
            fighter.retirement_reason = "Stability retirement-card test; final fight required."
            fighter.free_agent_months = 11
            fighter.injured = 0
            fighter.fatigue = 0
            fighter.available_week = 0
            fighter.showcase_last_month = -99
            fighter.ai_offer_company = ""
            fighter.champion = False
            fighter.interim_champion = False
            cohort.append(fighter)
        app.free_agents = cohort
        app.retired_fighters = []
        app.result_records = []
        app.ai_event_archive = []

        require(app.retirement_card_weekly_limit(9) == 0, "Fewer than ten retirees enabled a retirement card")
        require(app.retirement_card_weekly_limit(10) == 1, "Normal retirement queue did not allow one weekly card")
        require(app.retirement_card_weekly_limit(47) == 1, "Normal retirement queue allowed too many weekly cards")
        require(app.retirement_card_weekly_limit(48) == 2, "Severe retirement queue did not allow a second weekly card")
        require(app.retirement_card_weekly_limit(500) == 2, "Retirement-card weekly cap exceeded two")
        require(not app.simulate_due_free_agent_retirement_cards(), "An under-40 retirement card ran before the twelve-month wait")

        for fighter in cohort[:9]:
            fighter.free_agent_months = 12
        require(not app.simulate_due_free_agent_retirement_cards(), "Nine eligible retirees triggered a retirement card")
        for fighter in cohort:
            fighter.free_agent_months = 12

        packages = app.simulate_due_free_agent_retirement_cards()
        require(len(packages) == 1, "A 26-fighter queue should create exactly one card this week")
        package = packages[0]
        require(package["fight_count"] == 12, "Retirement card exceeded or failed to fill the 12-fight cap")
        require(len(package["retired_names"]) == 24, "Retirement card did not retire both participants in every bout")
        require("Retirement Card Probe 00" in {package["fight_logs"][0]["a"], package["fight_logs"][0]["b"]}, "Most popular retiree did not appear in the main event")
        participants = [name for fight in package["fight_logs"] for name in (fight["a"], fight["b"])]
        require(len(participants) == len(set(participants)) == 24, "Retirement card reused a fighter")
        require(all(fight["weight"] == "Welterweight" for fight in package["fight_logs"]), "Retirement card crossed weight classes")
        require(all(fighter.retired and not fighter.retirement_pending and fighter.retirement_fight_completed for fighter in app.retired_fighters), "Retirement-card participant retained an invalid career state")
        require(len(app.free_agents) == 2 and all(fighter.retirement_pending for fighter in app.free_agents), "Unselected retirement candidates were not preserved")
        require(app.retirement_cards_already_run_this_week() == 1, "Retirement card was not archived once for the current week")
        require(not app.simulate_due_free_agent_retirement_cards(), "A sub-threshold remainder created another retirement card")

        # A severe backlog may create a second card, but never a third on the
        # same date even when enough eligible fighters remain.
        app.month = 41
        severe_queue = []
        for index in range(60):
            fighter = copy.deepcopy(template)
            fighter.name = f"Severe Retirement Queue Probe {index:02d}"
            fighter.gender = "Female"
            fighter.weight = "Lightweight"
            fighter.popularity = max(10, 100 - index)
            fighter.retired = False
            fighter.retirement_pending = True
            fighter.retirement_fight_completed = False
            fighter.retirement_requested_month = app.month - 30
            fighter.free_agent_months = 30
            fighter.injured = 0
            fighter.fatigue = 0
            fighter.available_week = 0
            fighter.showcase_last_month = -99
            fighter.ai_offer_company = ""
            fighter.champion = False
            fighter.interim_champion = False
            severe_queue.append(fighter)
        app.free_agents = severe_queue
        app.retired_fighters = []
        packages = app.simulate_due_free_agent_retirement_cards()
        require(len(packages) == 2 and sum(package["fight_count"] for package in packages) == 24, "Severe queue did not produce exactly two full retirement cards")
        require(app.retirement_cards_already_run_this_week() == 2, "Severe queue was not capped at two retirement cards for the week")
        require(len(app.free_agents) == 12, "Two retirement cards did not retire exactly 48 fighters")
        require(not app.simulate_due_free_agent_retirement_cards(), "A third retirement card ran in the same week")

        ai_promo = copy.deepcopy(next(promo for promo in app.promotions if not promo.is_regional_feeder))
        ai_retiree = copy.deepcopy(template)
        ai_retiree.name = "AI Contract Retirement Probe"
        ai_retiree.contract_months = 0
        ai_retiree.retirement_pending = True
        ai_retiree.champion = True
        ai_retiree.popularity = 100
        ai_promo.roster = [ai_retiree]
        app.promotions = [ai_promo]
        app.free_agents = []
        app.update_ai_contracts()
        require(ai_retiree in app.free_agents and ai_retiree not in ai_promo.roster and ai_retiree.contract_months == 0, "AI renewed a retirement-pending fighter")

        # Solvent companies below their roster plan must not dump opening depth
        # deals en masse when those short contracts first expire.
        renewal_promo = copy.deepcopy(next(promo for promo in app.promotions if promo.name == "Ultimate Fighting Championship"))
        renewal_promo.cash = 100_000_000
        renewal_promo.roster = []
        require(app.ai_division_target(renewal_promo, "Male") == 33, "UFC male division plan does not match its roster share")
        require(app.ai_division_target(renewal_promo, "Female") == 17, "UFC female division plan does not match its roster share")
        for gender, target in (("Male", 33), ("Female", 17)):
            for weight in renewal_promo.weight_classes:
                for index in range(target):
                    member = copy.deepcopy(template)
                    member.name = f"Opening Depth Renewal Probe {gender} {weight} {index}"
                    member.gender = gender
                    member.weight = weight
                    member.striking = member.wrestling = member.grappling = member.cardio = member.chin = 58
                    member.detailed_skills = None
                    member.potential = 72
                    member.popularity = 12
                    member.contract_type = "Depth Contract"
                    member.contract_months = 8
                    renewal_promo.roster.append(member)
        require(len(renewal_promo.roster) == app.ai_roster_target(renewal_promo) == 400,
                "Gender-weighted UFC division plan does not reconcile to its company roster target")
        expiring_depth = renewal_promo.roster[0]
        expiring_depth.contract_months = 0
        app.promotions = [renewal_promo]
        app.free_agents = []
        app.update_ai_contracts()
        require(expiring_depth in renewal_promo.roster and expiring_depth.contract_months > 0,
                "AI released usable male opening depth from a correctly balanced full roster")

        # Temporary divisional imbalance is corrected by recruitment and the
        # gradual roster review, not a mass expiry dump while the company has
        # hundreds of vacant jobs elsewhere.
        extra_depth = copy.deepcopy(renewal_promo.roster[:6])
        renewal_promo.roster = renewal_promo.roster[:344] + extra_depth
        for index, member in enumerate(extra_depth):
            member.name = f"Over-plan Division Renewal Probe {index}"
            member.fighter_id = f"OVER-PLAN-RENEWAL-{index}"
            member.contract_months = 8
        over_plan_depth = renewal_promo.roster[0]
        over_plan_depth.contract_months = 0
        app.update_ai_contracts()
        require(over_plan_depth in renewal_promo.roster and over_plan_depth.contract_months > 0,
                "AI released usable divisional depth while the company remained below its overall roster target")

        player_retiree = copy.deepcopy(template)
        player_retiree.name = "Player Contract Retirement Probe"
        player_retiree.contract_months = 0
        player_retiree.retirement_pending = True
        player_retiree.champion = True
        player_retiree.popularity = 100
        player_retiree.morale = 100
        app.roster = [player_retiree]
        app.free_agents = []
        app.belts, app.interim_belts, app.belt_history = app.blank_belts(), app.blank_belts(), app.blank_belt_history()
        app.update_contracts()
        require(player_retiree in app.roster and player_retiree not in app.free_agents
                and player_retiree.contract_months == 0 and player_retiree.retirement_pending,
                "Player expiry logic changed a retirement-pending fighter's final-fight state")
        require(not callback_errors, f"Retirement-card Tk callback error: {callback_errors[0][1] if callback_errors else ''}")
    finally:
        destroy_root(root)


def exercise_repeated_world_loops():
    summaries = []
    for seed in (2201, 2202, 2203):
        root, app, callback_errors = new_app(seed)
        try:
            app.spectator_mode = True
            start_month = app.month
            for _ in range(12):
                app.advance_month()
            require(app.month >= start_month + 3, "Repeated world loop did not advance three months")
            require(not callback_errors, f"World-loop Tk callback error: {callback_errors[0][1] if callback_errors else ''}")
            summaries.append((seed, app.month, len(app.result_records), len(app.retired_fighters)))
        finally:
            destroy_root(root)
    return summaries


def exercise_sim_lab_population_tool(app):
    before = len(app.free_agents)
    created = app.create_sim_lab_free_agents(
        12,
        age=21,
        ability=74,
        gender="Female",
        weight="Flyweight",
    )
    require(len(created) == 12 and len(app.free_agents) == before + 12,
            "Sim Lab population tool did not add the requested number of free agents")
    require(len({fighter.fighter_id for fighter in created}) == 12,
            "Sim Lab population tool created duplicate fighter IDs")
    require(len({fighter.name for fighter in created}) == 12,
            "Sim Lab population tool created duplicate fighter names")
    require(all(fighter.age == 21 and fighter.overall == 74 for fighter in created),
            "Sim Lab population tool did not honor fixed age and ability")
    require(all(fighter.gender == "Female" and fighter.weight == "Flyweight" for fighter in created),
            "Sim Lab population tool did not honor fixed gender and division")
    require(all(fighter.record == "0-0-0" and fighter.contract_months == 0
                and fighter.contract_type == "Free Agent" and not fighter.exclusive for fighter in created),
            "Sim Lab population tool created malformed free-agent careers")
    # Invalid programmatic input must clamp at the legal minimum, and spectator
    # worlds do not always carry a current_screen attribute.
    app.sim_generate_count.set(1)
    app.sim_generate_age.set("12")
    app.sim_generate_ability.set("60")
    app.sim_generate_gender.set("Male")
    app.sim_generate_weight.set("Bantamweight")
    had_screen = "current_screen" in app.__dict__
    old_screen = app.__dict__.pop("current_screen", None)
    before_invalid = len(app.free_agents)
    app.generate_sim_lab_free_agents()
    require(len(app.free_agents) == before_invalid + 1 and app.free_agents[-1].age == 16,
            "Sim Lab accepted an under-16 generated fighter")
    if had_screen:
        app.current_screen = old_screen


def exercise_free_agent_safety_floor(app):
    active = [fighter for fighter in app.free_agents if not fighter.retired]
    require(len(active) >= 160, "Test universe lacks enough free agents for the safety-floor regression")
    app.month = max(2, app.month)
    app.free_agents = active[:160]
    ids_at_floor = {fighter.fighter_id for fighter in app.free_agents}
    require(app.ensure_free_agent_depth(emergency=True) == 0,
            "Free-agent safety floor activated at 160 instead of below 160")
    require({fighter.fighter_id for fighter in app.free_agents} == ids_at_floor,
            "Free-agent safety floor changed a healthy 160-fighter market")

    app.free_agents = active[:159]
    additions = app.ensure_free_agent_depth(emergency=True)
    live = [fighter for fighter in app.free_agents if not fighter.retired]
    require(additions == 41 and len(live) == 200,
            "Free-agent safety floor did not restore a sub-160 market to 200")
    require(len({fighter.fighter_id for fighter in live}) == 200,
            "Free-agent safety floor introduced duplicate fighter IDs")
    generated = [fighter for fighter in live if fighter.fighter_id not in {item.fighter_id for item in active[:159]}]
    require(all(fighter.contract_months == 0 and not fighter.exclusive for fighter in generated),
            "Free-agent safety floor created contracted emergency entrants")


def exercise_regional_title_booking(app):
    """Regional champions must sit out unless they are defending their belt."""
    fighters = []
    for index, name in enumerate(("Regional Champ", "Regional Challenger", "Regional Third", "Regional Fourth")):
        fighter = Fighter(name, "Lightweight", 20, 6 + index, 1, 70 + index, 68, 67, 72, 70, 15, 0, 70, 1000)
        fighter.gender = "Male"
        fighter.potential = 80
        fighter.available_week = 0
        fighter.fatigue = 0
        fighters.append(fighter)
    champion = fighters[0]
    champion.champion = True
    promo = Promotion("Regional Title Regression", "UK", 30, 500000, fighters, is_regional_feeder=True)
    key = app.belt_key("Male", "Lightweight")
    promo.belts = app.blank_belts()
    promo.belts[key] = champion.name
    promo.interim_belts = app.blank_belts()
    promo.belt_history = app.normalize_belt_history({
        key: [{"date": "Month 9 Week 1", "action": "Champion Crowned", "division": key,
               "fighter": champion.name, "note": "Regression fixture."}],
    })
    promo.show_history = []
    promo.regional_division_activity = {}
    promo.closed_divisions = []
    app.promotions.append(promo)

    app.month, app.week = 10, 1
    app.simulate_regional_feeder_month(promo)
    require(not any(entry.get("opponent_name") for entry in (champion.bout_rating_history or [])),
            "Regional champion was booked in a non-title bout before a defense was due")

    for fighter in promo.roster:
        fighter.fatigue = 0
        fighter.available_week = 0
        fighter.available_day = 0
        fighter.injured = 0
    app.month, app.week = 13, 1
    app.simulate_regional_feeder_month(promo)
    title_bouts = champion.bout_rating_history or []
    require(title_bouts and title_bouts[0]["title"] and title_bouts[0]["divisional_title"],
            "Regional champion did not defend once the title cadence was due")


def exercise_fighter_tree_identity_safety(app):
    """Duplicate display names and stale UI selections must not crash core tables."""
    market_original = app.free_agents[0]
    market_duplicate = app.create_generated_fighter()
    market_duplicate.name = market_original.name
    market_duplicate.fighter_id = "stability-duplicate-market-id"
    app.free_agents.append(market_duplicate)
    app.refresh_market()
    duplicate_rows = [row_id for row_id, fighter in app.market_tree_fighters.items()
                      if fighter.name == market_original.name]
    require(len(duplicate_rows) >= 2 and len(duplicate_rows) == len(set(duplicate_rows)),
            "Free Agents still uses a fighter's display name as the Treeview key")
    market_duplicate.gender = market_original.gender
    market_duplicate.weight = market_original.weight
    _company_ranks, world_ranks = app.division_rank_maps()
    original_key = app.fighter_identity_key(market_original)
    duplicate_key = app.fighter_identity_key(market_duplicate)
    require(original_key != duplicate_key and world_ranks.get(original_key) and world_ranks.get(duplicate_key),
            "Worldwide rankings still collapse same-named fighters into one entry")
    app.free_agents.remove(market_duplicate)

    first, second = app.roster[:2]
    second_original_name = second.name
    second.name = first.name
    try:
        app.refresh_roster()
        app.refresh_contracts()
        app.refresh_available()
        require(len(app.roster_tree_fighters) == len(app.roster_tree.get_children()),
                "Roster Treeview identity mapping lost a duplicate-name fighter")
        require(len(app.contracts_tree_fighters) == len(app.contracts_tree.get_children()),
                "Contracts Treeview identity mapping lost a duplicate-name fighter")

        selected = app.roster_tree.selection()[0]
        removed = app.roster_tree_fighters[selected]
        app.roster.remove(removed)
        app.update_fighter_detail()
        require(not app.roster_tree.selection(), "Stale roster selection was not cleared")
        app.roster.append(removed)
    finally:
        second.name = second_original_name
        app.refresh_roster()
        app.refresh_contracts()
        app.refresh_available()


def main():
    silence_dialogs()
    root, app, callback_errors = new_app(2200)
    try:
        exercise_all_main_screens(app, root)
        exercise_free_agent_viewport_and_scroll(app, root)
        exercise_media_story_reader(app, root)
        exercise_extended_title_live_watch(app, root)
        exercise_normal_and_retirement_events(app, root)
        exercise_academy_and_sport_edge_cases(app)
        exercise_talent_ecosystem_balance(app)
        exercise_save_roundtrip(app)
        exercise_optimized_autosave_cycle(app)
        exercise_responsive_advance(app, root)
        exercise_sim_lab_population_tool(app)
        exercise_free_agent_safety_floor(app)
        exercise_regional_title_booking(app)
        exercise_fighter_tree_identity_safety(app)
        require(not callback_errors, f"UI callback error: {callback_errors[0][1] if callback_errors else ''}")
    finally:
        destroy_root(root)

    root, app, callback_errors = new_app(2204)
    try:
        exercise_month_tracking(app)
        require(not callback_errors, f"Month tracking callback error: {callback_errors[0][1] if callback_errors else ''}")
    finally:
        destroy_root(root)

    summaries = exercise_repeated_world_loops()
    exercise_retirement_card_pipeline()
    print("STABILITY PLAYTEST PASSED")
    for seed, month, results, retired in summaries:
        print(f"Seed {seed}: reached Month {month}; recorded events {results}; retired fighters {retired}")


if __name__ == "__main__":
    main()
