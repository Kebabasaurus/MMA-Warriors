"""Longitudinal audit for the five non-MMA combat-sport circuits.

This script creates fresh in-memory worlds, exercises the production monthly
circuit processing and annual aging paths, and never saves a game.  It tracks
the original roster and every generated prospect through development, bouts,
crossovers, and retirement.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
import tkinter as tk
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import main as game  # noqa: E402


SPORTS = (
    "Boxing",
    "Kickboxing",
    "Muay Thai",
    "Wrestling",
    "Brazilian Jiu-Jitsu",
)


def percentile(values, fraction):
    values = sorted(values)
    if not values:
        return None
    index = (len(values) - 1) * fraction
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return values[low]
    return values[low] + (values[high] - values[low]) * (index - low)


def distribution(values, digits=2):
    values = [value for value in values if value is not None]
    if not values:
        return {"n": 0, "mean": None, "median": None, "sd": None, "min": None, "p10": None, "p90": None, "max": None}
    return {
        "n": len(values),
        "mean": round(statistics.fmean(values), digits),
        "median": round(statistics.median(values), digits),
        "sd": round(statistics.pstdev(values), digits),
        "min": round(min(values), digits),
        "p10": round(percentile(values, 0.10), digits),
        "p90": round(percentile(values, 0.90), digits),
        "max": round(max(values), digits),
    }


def total_bouts(fighter):
    return fighter.record_w + fighter.record_l + fighter.record_d


def sport_rating(app, fighter, sport):
    """Use the player-facing normalized native-sport rating for every metric."""
    return app.combat_sport_display_rating(fighter, sport)


def register_fighter(app, sport, fighter, entrant, elapsed_month, trackers):
    rating = sport_rating(app, fighter, sport)
    trackers[sport][fighter.name] = {
        "fighter": fighter,
        "entrant": entrant,
        "entry_month": elapsed_month,
        "entry_age": fighter.age,
        "entry_rating": rating,
        "entry_bouts": total_bouts(fighter),
        "peak_rating": rating,
        "peak_age": fighter.age,
        "peak_month": elapsed_month,
        "retirement_age": fighter.age if fighter.retired else None,
        "retirement_month": elapsed_month if fighter.retired else None,
        "crossover_month": None,
        "rating_at_3y": None,
        "rating_at_5y": None,
        "rating_at_10y": None,
    }


def update_trackers(app, elapsed_month, trackers):
    for sport in SPORTS:
        world = app.combat_sport_worlds[sport]
        roster_names = {fighter.name for fighter in world.get("roster", [])}
        for fighter in world.get("roster", []):
            if fighter.name not in trackers[sport]:
                register_fighter(app, sport, fighter, "prospect", elapsed_month, trackers)
        for name, row in trackers[sport].items():
            fighter = row["fighter"]
            rating = sport_rating(app, fighter, sport)
            if rating > row["peak_rating"]:
                row["peak_rating"] = rating
                row["peak_age"] = fighter.age
                row["peak_month"] = elapsed_month
            tenure = elapsed_month - row["entry_month"]
            for years in (3, 5, 10):
                key = f"rating_at_{years}y"
                if row[key] is None and tenure >= years * 12:
                    row[key] = rating
            if fighter.retired and row["retirement_age"] is None:
                row["retirement_age"] = fighter.age
                row["retirement_month"] = elapsed_month
            if name not in roster_names and row["crossover_month"] is None and not fighter.retired:
                row["crossover_month"] = elapsed_month


def checkpoint_for_sport(app, sport, elapsed_years, trackers):
    world = app.combat_sport_worlds[sport]
    promotion = world.get("promotion", "")
    rows = list(trackers[sport].values())
    initial = [row for row in rows if row["entrant"] == "initial"]
    prospects = [row for row in rows if row["entrant"] == "prospect"]
    roster_names = {fighter.name for fighter in world.get("roster", [])}

    def in_circuit(row):
        fighter = row["fighter"]
        return fighter.name in roster_names and not fighter.retired and fighter.sport_employer == promotion

    active = [row for row in rows if in_circuit(row)]
    active_initial = [row for row in initial if in_circuit(row)]
    active_prospects = [row for row in prospects if in_circuit(row)]
    initial_changes = [sport_rating(app, row["fighter"], sport) - row["entry_rating"] for row in initial]
    active_initial_changes = [sport_rating(app, row["fighter"], sport) - row["entry_rating"] for row in active_initial]
    initial_activity = [total_bouts(row["fighter"]) - row["entry_bouts"] for row in initial]
    active_ratings = [sport_rating(app, row["fighter"], sport) for row in active]
    active_initial_ratings = [sport_rating(app, row["fighter"], sport) for row in active_initial]
    active_prospect_ratings = [sport_rating(app, row["fighter"], sport) for row in active_prospects]
    prospect_changes = [sport_rating(app, row["fighter"], sport) - row["entry_rating"] for row in prospects]
    prospect_entry_ratings = [row["entry_rating"] for row in prospects]
    active_ages = [row["fighter"].age for row in active]
    initial_age_bands = {}
    for label, lower, upper in (("young", 0, 25), ("prime", 26, 32), ("veteran", 33, 200)):
        band = [row for row in initial if lower <= row["entry_age"] <= upper]
        initial_age_bands[label] = {
            "count": len(band),
            "rating_change": distribution(sport_rating(app, row["fighter"], sport) - row["entry_rating"] for row in band),
            "bouts": distribution(total_bouts(row["fighter"]) - row["entry_bouts"] for row in band),
            "retired": sum(row["retirement_age"] is not None for row in band),
        }
    return {
        "year": elapsed_years,
        "active_roster": len(active),
        "active_initial": len(active_initial),
        "active_prospects": len(active_prospects),
        "generated_prospects": len(prospects),
        "retired": sum(row["retirement_age"] is not None for row in rows),
        "retirement_pending": sum(row["fighter"].retirement_pending and not row["fighter"].retired for row in rows),
        "crossovers": sum(row["crossover_month"] is not None for row in rows),
        "initial_rating_change": distribution(initial_changes),
        "active_initial_rating_change": distribution(active_initial_changes),
        "prospect_rating_change": distribution(prospect_changes),
        "prospect_entry_rating": distribution(prospect_entry_ratings),
        "initial_bouts": distribution(initial_activity),
        "initial_bouts_per_year_mean": round(statistics.fmean(initial_activity) / elapsed_years, 3) if initial_activity else None,
        "initial_zero_activity_pct": round(100 * sum(value == 0 for value in initial_activity) / len(initial_activity), 2) if initial_activity else None,
        "active_rating": distribution(active_ratings),
        "active_initial_rating": distribution(active_initial_ratings),
        "active_prospect_rating": distribution(active_prospect_ratings),
        "active_age": distribution(active_ages),
        "initial_age_bands": initial_age_bands,
    }


def run_seed(seed, years, checkpoints):
    random.seed(seed)
    root = tk.Tk()
    root.withdraw()
    try:
        app = game.FightEmpireApp(root)
        app.suppress_autosaves = True
        app.suppress_award_popups = True
        trackers = {sport: {} for sport in SPORTS}
        starts = {}
        for sport in SPORTS:
            world = app.combat_sport_worlds[sport]
            for fighter in world.get("roster", []):
                register_fighter(app, sport, fighter, "initial", 0, trackers)
            starts[sport] = {
                "roster_size": len(world.get("roster", [])),
                "rating": distribution(sport_rating(app, fighter, sport) for fighter in world.get("roster", [])),
                "age": distribution(fighter.age for fighter in world.get("roster", [])),
            }

        snapshots = defaultdict(dict)
        for elapsed_month in range(1, years * 12 + 1):
            completed_month = app.month
            app.month += 1
            app.week = 1
            app.process_combat_sport_worlds()
            if completed_month % 12 == 0:
                app.age_world_one_year()
            update_trackers(app, elapsed_month, trackers)
            if elapsed_month % 12 == 0:
                elapsed_year = elapsed_month // 12
                if elapsed_year in checkpoints:
                    for sport in SPORTS:
                        snapshots[sport][str(elapsed_year)] = checkpoint_for_sport(app, sport, elapsed_year, trackers)
                print(f"seed {seed}: completed year {elapsed_year}/{years}", file=sys.stderr, flush=True)

        final = {}
        for sport in SPORTS:
            rows = list(trackers[sport].values())
            prospect_rows = [row for row in rows if row["entrant"] == "prospect"]
            final[sport] = {
                "tracked_fighters": len(rows),
                "initial_fighters": sum(row["entrant"] == "initial" for row in rows),
                "generated_prospects": sum(row["entrant"] == "prospect" for row in rows),
                "peak_rating": distribution(row["peak_rating"] for row in rows),
                "peak_age": distribution(row["peak_age"] for row in rows),
                "rating_gain_to_peak": distribution(row["peak_rating"] - row["entry_rating"] for row in rows),
                "initial_peak_rating": distribution(row["peak_rating"] for row in rows if row["entrant"] == "initial"),
                "initial_peak_age": distribution(row["peak_age"] for row in rows if row["entrant"] == "initial"),
                "initial_rating_gain_to_peak": distribution(row["peak_rating"] - row["entry_rating"] for row in rows if row["entrant"] == "initial"),
                "prospect_entry_rating": distribution(row["entry_rating"] for row in rows if row["entrant"] == "prospect"),
                "prospect_peak_rating": distribution(row["peak_rating"] for row in rows if row["entrant"] == "prospect"),
                "prospect_peak_age": distribution(row["peak_age"] for row in rows if row["entrant"] == "prospect"),
                "prospect_rating_gain_to_peak": distribution(row["peak_rating"] - row["entry_rating"] for row in rows if row["entrant"] == "prospect"),
                "prospect_rating_change_3y": distribution(row["rating_at_3y"] - row["entry_rating"] for row in prospect_rows if row["rating_at_3y"] is not None),
                "prospect_rating_change_5y": distribution(row["rating_at_5y"] - row["entry_rating"] for row in prospect_rows if row["rating_at_5y"] is not None),
                "prospect_rating_change_10y": distribution(row["rating_at_10y"] - row["entry_rating"] for row in prospect_rows if row["rating_at_10y"] is not None),
                "retirement_age": distribution(row["retirement_age"] for row in rows if row["retirement_age"] is not None),
                "initial_retirement_age": distribution(row["retirement_age"] for row in rows if row["entrant"] == "initial" and row["retirement_age"] is not None),
                "prospect_retirement_age": distribution(row["retirement_age"] for row in rows if row["entrant"] == "prospect" and row["retirement_age"] is not None),
                "retirements": sum(row["retirement_age"] is not None for row in rows),
                "crossovers": sum(row["crossover_month"] is not None for row in rows),
                "career_bouts_since_entry": distribution(total_bouts(row["fighter"]) - row["entry_bouts"] for row in rows),
            }
        return {"seed": seed, "starts": starts, "snapshots": dict(snapshots), "final": final}
    finally:
        root.destroy()


def pool_distribution(seed_runs, sport, getter):
    values = []
    for run in seed_runs:
        values.extend(getter(run, sport))
    return distribution(values)


def aggregate_runs(seed_runs, checkpoints):
    aggregate = {}
    for sport in SPORTS:
        sport_data = {
            "starting_roster_size": distribution(run["starts"][sport]["roster_size"] for run in seed_runs),
            "starting_rating_seed_means": distribution(run["starts"][sport]["rating"]["mean"] for run in seed_runs),
            "starting_rating_pooled": {
                key: round(statistics.fmean(run["starts"][sport]["rating"][key] for run in seed_runs), 2)
                for key in ("mean", "median", "sd", "min", "p10", "p90", "max")
            },
            "checkpoints": {},
        }
        for year in checkpoints:
            rows = [run["snapshots"][sport][str(year)] for run in seed_runs]
            sport_data["checkpoints"][str(year)] = {
                "active_roster": distribution(row["active_roster"] for row in rows),
                "active_initial": distribution(row["active_initial"] for row in rows),
                "active_prospects": distribution(row["active_prospects"] for row in rows),
                "generated_prospects": distribution(row["generated_prospects"] for row in rows),
                "retired": distribution(row["retired"] for row in rows),
                "retirement_pending": distribution(row["retirement_pending"] for row in rows),
                "crossovers": distribution(row["crossovers"] for row in rows),
                "initial_rating_change_seed_means": distribution(row["initial_rating_change"]["mean"] for row in rows),
                "active_initial_rating_change_seed_means": distribution(row["active_initial_rating_change"]["mean"] for row in rows),
                "prospect_rating_change_seed_means": distribution(row["prospect_rating_change"]["mean"] for row in rows if row["prospect_rating_change"]["mean"] is not None),
                "prospect_entry_rating_seed_means": distribution(row["prospect_entry_rating"]["mean"] for row in rows),
                "initial_bouts_seed_means": distribution(row["initial_bouts"]["mean"] for row in rows),
                "initial_bouts_per_year": distribution(row["initial_bouts_per_year_mean"] for row in rows),
                "initial_zero_activity_pct": distribution(row["initial_zero_activity_pct"] for row in rows),
                "active_rating_seed_means": distribution(row["active_rating"]["mean"] for row in rows),
                "active_initial_rating_seed_means": distribution(row["active_initial_rating"]["mean"] for row in rows),
                "active_prospect_rating_seed_means": distribution(row["active_prospect_rating"]["mean"] for row in rows),
                "initial_age_bands": {
                    band: {
                        "count": distribution(row["initial_age_bands"][band]["count"] for row in rows),
                        "rating_change_seed_means": distribution(row["initial_age_bands"][band]["rating_change"]["mean"] for row in rows),
                        "bouts_seed_means": distribution(row["initial_age_bands"][band]["bouts"]["mean"] for row in rows),
                        "retired": distribution(row["initial_age_bands"][band]["retired"] for row in rows),
                    }
                    for band in ("young", "prime", "veteran")
                },
            }
        finals = [run["final"][sport] for run in seed_runs]
        sport_data["final"] = {
            "tracked_fighters": distribution(row["tracked_fighters"] for row in finals),
            "generated_prospects": distribution(row["generated_prospects"] for row in finals),
            "retirements": distribution(row["retirements"] for row in finals),
            "crossovers": distribution(row["crossovers"] for row in finals),
            "peak_rating_seed_means": distribution(row["peak_rating"]["mean"] for row in finals),
            "peak_age_seed_means": distribution(row["peak_age"]["mean"] for row in finals),
            "rating_gain_to_peak_seed_means": distribution(row["rating_gain_to_peak"]["mean"] for row in finals),
            "initial_peak_rating_seed_means": distribution(row["initial_peak_rating"]["mean"] for row in finals),
            "initial_peak_age_seed_means": distribution(row["initial_peak_age"]["mean"] for row in finals),
            "initial_rating_gain_to_peak_seed_means": distribution(row["initial_rating_gain_to_peak"]["mean"] for row in finals),
            "prospect_entry_rating_seed_means": distribution(row["prospect_entry_rating"]["mean"] for row in finals),
            "prospect_peak_rating_seed_means": distribution(row["prospect_peak_rating"]["mean"] for row in finals),
            "prospect_peak_age_seed_means": distribution(row["prospect_peak_age"]["mean"] for row in finals),
            "prospect_rating_gain_to_peak_seed_means": distribution(row["prospect_rating_gain_to_peak"]["mean"] for row in finals),
            "prospect_rating_change_3y_seed_means": distribution(row["prospect_rating_change_3y"]["mean"] for row in finals),
            "prospect_rating_change_5y_seed_means": distribution(row["prospect_rating_change_5y"]["mean"] for row in finals),
            "prospect_rating_change_10y_seed_means": distribution(row["prospect_rating_change_10y"]["mean"] for row in finals),
            "retirement_age_seed_means": distribution(row["retirement_age"]["mean"] for row in finals if row["retirement_age"]["mean"] is not None),
            "retirement_age_seed_medians": distribution(row["retirement_age"]["median"] for row in finals if row["retirement_age"]["median"] is not None),
            "career_bouts_seed_means": distribution(row["career_bouts_since_entry"]["mean"] for row in finals),
        }
        aggregate[sport] = sport_data
    return aggregate


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="101,202,303,404", help="Comma-separated integer seeds")
    parser.add_argument("--years", type=int, default=15, help="Longest career horizon")
    parser.add_argument("--checkpoints", default="3,5,10,15", help="Comma-separated year checkpoints")
    parser.add_argument("--json", type=Path, help="Optional JSON output path; stdout is always available")
    return parser.parse_args()


def main():
    args = parse_args()
    seeds = [int(value.strip()) for value in args.seeds.split(",") if value.strip()]
    checkpoints = sorted({int(value.strip()) for value in args.checkpoints.split(",") if value.strip()})
    if not seeds or not checkpoints or args.years < max(checkpoints):
        raise SystemExit("Provide at least one seed and checkpoints no longer than --years")
    runs = [run_seed(seed, args.years, checkpoints) for seed in seeds]
    report = {
        "config": {"seeds": seeds, "years": args.years, "checkpoints": checkpoints, "sports": list(SPORTS)},
        "aggregate": aggregate_runs(runs, checkpoints),
        "seed_runs": runs,
    }
    encoded = json.dumps(report, indent=2)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(encoded, encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
