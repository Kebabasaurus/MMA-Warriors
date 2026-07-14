"""Broad, non-destructive application playtest for shipping stability.

This complements smoke_test.py by exercising real event completion, retirement
cleanup, UI viewers, academy/card edge cases, save round-tripping and repeated
world advancement.  It never writes a player save.
"""

import json
import random
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from main import FightEmpireApp
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


def exercise_all_main_screens(app, root):
    for name in app.tab_pages:
        app.select_tab(name)
        app.refresh_all()
        root.update_idletasks()

    fighter = app.roster[0]
    app.open_fighter_profile_window(fighter)
    app.open_regional_identity_window(fighter)

    app.company_list.selection_clear(0, "end")
    app.company_list.selection_set(0)
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


def exercise_normal_and_retirement_events(app, root):
    pair = ready_pair(app)
    require(pair, "Could not find a legal player event pairing")
    normal = event_for(app, pair, "Stability Normal Event")
    package = app.prepare_event_result(normal)
    require(package.get("fight_logs"), "Normal event produced no fight logs")
    require(any("cut penalty" in line for line in package["fight_logs"][0]["lines"]), "Event readiness line missing")
    app.open_live_fight_window(normal, package, apply_results=False)
    live_window = next(child for child in root.winfo_children() if isinstance(child, tk.Toplevel))
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
    app.process_world_week = lambda: None
    app.process_world_month = lambda player_ran_show: captured.append(player_ran_show)
    app.refresh_all = lambda: None
    app.write_log = lambda: None
    app.run_automatic_save_cycle = lambda month_changed=False: (None, None)
    app.advance_month()
    require(captured == [True], "Month rollover incorrectly treated an active player as quiet")


def exercise_academy_and_sport_edge_cases(app):
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
    require(result.get("log") and result.get("weight") == athlete.weight, "Guest sport bout did not complete with replay metadata")
    athlete.sport_employer = original_employer


def exercise_save_roundtrip(app):
    app.rules.update({"autosave_weekly_keep": 12, "autosave_monthly_keep": 24, "save_backup_keep": 60, "save_retention_version": 1})
    app.ensure_rule_defaults()
    require(
        (app.rules["autosave_weekly_keep"], app.rules["autosave_monthly_keep"], app.rules["save_backup_keep"]) == (8, 6, 12),
        "Legacy oversized save retention defaults were not migrated",
    )
    encoded = json.dumps(app.serialize_world())
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
        require(not callback_errors, f"Save roundtrip UI callback error: {callback_errors[0][1] if callback_errors else ''}")
    finally:
        root2.destroy()


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
            root.destroy()
    return summaries


def main():
    silence_dialogs()
    root, app, callback_errors = new_app(2200)
    try:
        exercise_all_main_screens(app, root)
        exercise_normal_and_retirement_events(app, root)
        exercise_academy_and_sport_edge_cases(app)
        exercise_save_roundtrip(app)
        require(not callback_errors, f"UI callback error: {callback_errors[0][1] if callback_errors else ''}")
    finally:
        root.destroy()

    root, app, callback_errors = new_app(2204)
    try:
        exercise_month_tracking(app)
        require(not callback_errors, f"Month tracking callback error: {callback_errors[0][1] if callback_errors else ''}")
    finally:
        root.destroy()

    summaries = exercise_repeated_world_loops()
    print("STABILITY PLAYTEST PASSED")
    for seed, month, results, retired in summaries:
        print(f"Seed {seed}: reached Month {month}; recorded events {results}; retired fighters {retired}")


if __name__ == "__main__":
    main()
