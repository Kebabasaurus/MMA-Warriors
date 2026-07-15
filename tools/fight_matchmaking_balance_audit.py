"""Reproducible fight-engine and world-matchmaking balance audit.

The controlled portion clones database fighters and never applies career results.  The
optional world portion creates a fresh in-memory spectator world and never saves it.
Only the text report in ``audits/`` is written.
"""

from __future__ import annotations

import argparse
import importlib.util
import random
import re
import statistics
import sys
import tkinter as tk
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "audits" / "fight_matchmaking_balance_audit_latest.txt"
SEED = 20260714
FINISH_METHODS = {
    "KO", "TKO", "Submission", "Technical Submission", "Doctor Stoppage",
    "Corner Stoppage", "Injury Stoppage",
}
TIER_RULES = {
    "Low (<68)": lambda rating: rating < 68,
    "Mid (68-79)": lambda rating: 68 <= rating < 80,
    "High (80+)": lambda rating: rating >= 80,
}


def load_game_module():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("mma_warriors_balance_audit", ROOT / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tier_name(rating):
    if rating < 68:
        return "Low (<68)"
    if rating < 80:
        return "Mid (68-79)"
    return "High (80+)"


def gap_band(gap):
    if gap == 0:
        return "0 (even)"
    if gap <= 2:
        return "1-2"
    if gap <= 4:
        return "3-4"
    if gap <= 6:
        return "5-6"
    if gap <= 9:
        return "7-9"
    if gap <= 14:
        return "10-14"
    return "15+"


def new_stats():
    return {
        "fights": 0,
        "methods": Counter(),
        "rounds": Counter(),
        "gaps": Counter(),
        "gap_bands": defaultdict(Counter),
        "rating_gap_total": 0,
        "anomalies": Counter(),
    }


def merge_stats(rows):
    merged = new_stats()
    for stats in rows:
        merged["fights"] += stats["fights"]
        merged["methods"].update(stats["methods"])
        merged["rounds"].update(stats["rounds"])
        merged["gaps"].update(stats["gaps"])
        merged["rating_gap_total"] += stats["rating_gap_total"]
        merged["anomalies"].update(stats["anomalies"])
        for band, values in stats["gap_bands"].items():
            merged["gap_bands"][band].update(values)
    return merged


def record_result(stats, a, b, winner, method, round_no, lines=None, max_rounds=None):
    gap = abs(a.overall - b.overall)
    band = gap_band(gap)
    stats["fights"] += 1
    stats["methods"][method] += 1
    stats["rounds"][round_no] += 1
    stats["gaps"][gap] += 1
    stats["rating_gap_total"] += gap
    row = stats["gap_bands"][band]
    row["fights"] += 1
    if method == "Draw":
        row["draws"] += 1
    elif gap:
        row["rated_results"] += 1
        favourite = a if a.overall > b.overall else b
        if winner is not favourite:
            row["upsets"] += 1
    if method in FINISH_METHODS:
        row["finishes"] += 1

    if lines is None:
        return
    anomalies = stats["anomalies"]
    if max_rounds is not None:
        if not 1 <= round_no <= max_rounds:
            anomalies["round_out_of_bounds"] += 1
        if method in ("Decision", "Draw") and round_no != max_rounds:
            anomalies["early_decision_or_draw"] += 1
    for fighter in (a, b):
        last = fighter.last_fight_stats or {}
        if last.get("rounds") != round_no:
            anomalies["stats_round_mismatch"] += 1
        if last.get("sig", 0) > last.get("sig_att", 0):
            anomalies["landed_strikes_exceed_attempts"] += 1
        if last.get("td", 0) > last.get("td_att", 0):
            anomalies["takedowns_exceed_attempts"] += 1

    text = "\n".join(lines)
    if any(token in text for token in ("\ufffd", "\u00e2\u20ac", "Ã")):
        anomalies["mojibake_or_replacement_character"] += 1
    if method in FINISH_METHODS:
        official = [line for line in lines if "Official result:" in line or "The official time is" in line]
        if len(official) != 1:
            anomalies["missing_or_multiple_official_finish"] += 1
        elif winner.name not in official[0] or method not in official[0]:
            anomalies["official_finish_result_mismatch"] += 1
        if "Official scorecards:" in text:
            anomalies["scorecards_after_finish"] += 1
    elif method == "Decision":
        if "Official scorecards:" not in text:
            anomalies["decision_without_scorecards"] += 1
        decision_lines = [
            line for line in lines
            if "wins by decision" in line or "takes the decision" in line or "The judges prefer" in line
        ]
        if not decision_lines or not any(winner.name in line for line in decision_lines):
            anomalies["decision_winner_text_mismatch"] += 1
    elif method == "Draw":
        if "Official scorecards:" not in text:
            anomalies["draw_without_scorecards"] += 1
        draw_lines = [line for line in lines if "declared a draw" in line or "fight to a draw" in line or "officially a draw" in line]
        if not draw_lines:
            anomalies["draw_without_draw_announcement"] += 1
        if re.search(r"wins by (?:KO|TKO|Submission|decision)", text, re.I):
            anomalies["draw_contains_winner_announcement"] += 1


def valid_groups(fighters, tier=None):
    groups = defaultdict(list)
    predicate = TIER_RULES.get(tier, lambda _rating: True)
    for fighter in fighters:
        if not fighter.retired and predicate(fighter.overall):
            groups[(fighter.gender, fighter.weight)].append(fighter)
    usable = {}
    for key, pool in groups.items():
        candidates = [
            fighter for fighter in pool
            if any(other.name != fighter.name and abs(other.overall - fighter.overall) <= 6 for other in pool)
        ]
        if len(candidates) >= 2:
            usable[key] = candidates
    return usable


def choose_pair(groups, rng):
    key = rng.choice(list(groups))
    pool = groups[key]
    a = rng.choice(pool)
    opponents = [other for other in pool if other.name != a.name and abs(other.overall - a.overall) <= 6]
    return a, rng.choice(opponents)


def run_controlled(app, per_tier, mixed_runs, seed):
    rng = random.Random(seed)
    # The engine itself uses the module-level generator.  Pair selection uses a
    # separate stream so a longer commentary log cannot alter the sampled pool.
    random.seed(seed + 1)
    fighters = list(app.all_database_fighters())
    groups_by_tier = {name: valid_groups(fighters, name) for name in TIER_RULES}
    stats_by_cohort = {}

    def simulate(cohort, original_a, original_b, main=False, title=False):
        a = app.clone_fighter_for_sim(original_a)
        b = app.clone_fighter_for_sim(original_b)
        # Symmetric, plausible camps isolate the rating/tier question without
        # granting either corner an audit-only advantage.
        camp_weeks = rng.randint(6, 10)
        app.prepare_sim_fighter(a, camp_weeks, title_fight=title)
        app.prepare_sim_fighter(b, camp_weeks, title_fight=title)
        fight = {"main": main, "title": title, "tier": "Main Card" if main else "Prelims"}
        winner, _loser, method, round_no, lines = app.simulate_fight(a, b, fight)
        max_rounds = app.rules["title_rounds"] if (main or title) else app.rules["rounds"]
        record_result(stats_by_cohort[cohort], a, b, winner, method, round_no, lines, max_rounds)

    for tier_index, (tier, groups) in enumerate(groups_by_tier.items()):
        # Give each cohort an independent deterministic stream. Changing a mid-
        # tier finish path must not shift every subsequent high-tier pairing.
        rng.seed(seed + tier_index * 1_000)
        random.seed(seed + tier_index * 1_000 + 1)
        stats_by_cohort[tier] = new_stats()
        for _ in range(per_tier):
            a, b = choose_pair(groups, rng)
            simulate(tier, a, b)

    stats_by_cohort["Realistic mixed cards"] = new_stats()
    rng.seed(seed + 10_000)
    random.seed(seed + 10_001)
    weights = [("Low (<68)", 25), ("Mid (68-79)", 55), ("High (80+)", 20)]
    weighted_tiers = [name for name, weight in weights for _ in range(weight)]
    for index in range(mixed_runs):
        selected = rng.choice(weighted_tiers)
        a, b = choose_pair(groups_by_tier[selected], rng)
        card_slot = index % 10
        main = card_slot == 0
        title = main and rng.random() < 0.35
        simulate("Realistic mixed cards", a, b, main=main, title=title)
    return stats_by_cohort


def run_world(app, years, seed):
    random.seed(seed)
    app.refresh_all = lambda: None
    app.write_log = lambda *_args, **_kwargs: None
    app.prompt_due_event = lambda: False
    app.open_awards_window = lambda *_args, **_kwargs: None
    app.show_event_summary = lambda *_args, **_kwargs: None
    app.suppress_award_popups = True
    app.suppress_autosaves = True
    app.enter_spectator_mode()

    overall = new_stats()
    by_source = defaultdict(new_stats)
    by_tier = defaultdict(new_stats)
    pending = None
    real_simulate = app.simulate_fight
    real_record = app.record_season_result
    real_build_ai_card = app.build_ai_card
    matchmaking = Counter()

    def capture_ai_card(promo, ready, target):
        card = real_build_ai_card(promo, ready, target)
        for entry in card:
            reason = entry.get("booking_reason", "")
            if reason.startswith(("Adjacent-ranked divisional matchup", "Activity-restoring matchup")):
                gap = abs(entry["a"].overall - entry["b"].overall)
                matchmaking["ordinary"] += 1
                matchmaking["ordinary_gap_total"] += gap
                matchmaking["ordinary_within_6"] += int(gap <= 6)
                matchmaking["ordinary_forced_mismatch"] += int(gap > 6)
            else:
                matchmaking["exceptions"] += 1
        return card

    def capture_simulate(a, b, fight):
        nonlocal pending
        a_rating, b_rating = a.overall, b.overall
        result = real_simulate(a, b, fight)
        winner, _loser, method, round_no, lines = result
        pending = {
            "a": a, "b": b, "a_rating": a_rating, "b_rating": b_rating,
            "winner": winner, "method": method, "round": round_no,
            "lines": lines, "fight": fight,
        }
        return result

    def capture_record(winner, loser, method, round_no, fight, excitement, company):
        nonlocal pending
        if pending and pending["method"] == method and {pending["a"].name, pending["b"].name} == {winner.name, loser.name}:
            a, b = pending["a"], pending["b"]
            # Results are recorded immediately after simulation, before any
            # post-fight development can change the calculated overall property.
            source = "Independent Circuit" if company == "Independent Circuit" else (
                "Regional feeders" if any(p.name == company and p.is_regional_feeder for p in app.promotions)
                else "Major promotions"
            )
            rating_tier = tier_name((a.overall + b.overall) / 2)
            record_result(overall, a, b, pending["winner"], method, round_no)
            record_result(by_source[source], a, b, pending["winner"], method, round_no)
            record_result(by_tier[rating_tier], a, b, pending["winner"], method, round_no)
        else:
            overall["anomalies"]["unmatched_record_hook"] += 1
        pending = None
        return real_record(winner, loser, method, round_no, fight, excitement, company)

    app.simulate_fight = capture_simulate
    app.record_season_result = capture_record
    app.build_ai_card = capture_ai_card
    for month_index in range(years * 12):
        for week in range(1, 5):
            app.week = week
            app.process_world_week()
        old_year = app.current_year()
        app.month += 1
        app.week = 1
        app.process_world_month(player_ran_show=False)
        if app.current_year() != old_year:
            app.run_end_of_year_awards(old_year)
            app.age_world_one_year()
        if (month_index + 1) % 12 == 0:
            print(f"World audit: completed {(month_index + 1) // 12}/{years} years", flush=True)
    overall["matchmaking"] = matchmaking
    return overall, dict(by_source), dict(by_tier)


def pct(value, total):
    return value / max(1, total) * 100


def append_stats(lines, heading, stats, include_anomalies=False):
    total = stats["fights"]
    finishes = sum(stats["methods"][method] for method in FINISH_METHODS)
    decisions = stats["methods"]["Decision"]
    draws = stats["methods"]["Draw"]
    avg_gap = stats["rating_gap_total"] / max(1, total)
    avg_round = sum(round_no * count for round_no, count in stats["rounds"].items()) / max(1, total)
    lines.extend([
        heading,
        "-" * 104,
        f"Fights {total:,} | Finishes {finishes:,} ({pct(finishes, total):.2f}%) | "
        f"Decisions {decisions:,} ({pct(decisions, total):.2f}%) | Draws {draws:,} ({pct(draws, total):.2f}%)",
        f"Average pre-fight OVR gap {avg_gap:.2f} | Average ending round {avg_round:.2f}",
        "Methods: " + " | ".join(
            f"{method} {count} ({pct(count, total):.2f}%)"
            for method, count in stats["methods"].most_common()
        ),
        "Ending rounds: " + " | ".join(f"R{round_no} {count} ({pct(count, total):.2f}%)" for round_no, count in sorted(stats["rounds"].items())),
        "Gap band       Fights  Share    Finish rate   Rated results  Upsets   Upset rate",
    ])
    band_order = ("0 (even)", "1-2", "3-4", "5-6", "7-9", "10-14", "15+")
    for band in band_order:
        row = stats["gap_bands"].get(band)
        if not row:
            continue
        rated = row["rated_results"]
        lines.append(
            f"{band:<14}{row['fights']:>6}  {pct(row['fights'], total):>6.2f}%  "
            f"{pct(row['finishes'], row['fights']):>10.2f}%  {rated:>14}  {row['upsets']:>6}  "
            f"{pct(row['upsets'], rated):>9.2f}%"
        )
    if include_anomalies:
        lines.append("Consistency checks: " + (
            "none detected" if not stats["anomalies"]
            else " | ".join(f"{name}={count}" for name, count in sorted(stats["anomalies"].items()))
        ))
    lines.append("")


def make_conclusion(controlled, world_overall, world_sources, historical_total=4751, historical_finishes=2906):
    mixed = controlled["Realistic mixed cards"]
    mixed_finishes = sum(mixed["methods"][method] for method in FINISH_METHODS)
    low = controlled["Low (<68)"]
    mid = controlled["Mid (68-79)"]
    high = controlled["High (80+)"]
    tier_rates = {
        "low": pct(sum(low["methods"][m] for m in FINISH_METHODS), low["fights"]),
        "mid": pct(sum(mid["methods"][m] for m in FINISH_METHODS), mid["fights"]),
        "high": pct(sum(high["methods"][m] for m in FINISH_METHODS), high["fights"]),
    }
    result = [
        "INTERPRETATION",
        "=" * 104,
        f"Historical five-year report: {historical_finishes:,}/{historical_total:,} finishes ({pct(historical_finishes, historical_total):.2f}%).",
        f"Controlled realistic mixed cards (all gaps <=6): {mixed_finishes:,}/{mixed['fights']:,} finishes ({pct(mixed_finishes, mixed['fights']):.2f}%).",
        f"Controlled same-tier finish rates: low {tier_rates['low']:.2f}%, mid {tier_rates['mid']:.2f}%, high {tier_rates['high']:.2f}%.",
    ]
    if world_overall:
        world_finishes = sum(world_overall["methods"][method] for method in FINISH_METHODS)
        wide = sum(row["fights"] for band, row in world_overall["gap_bands"].items() if band in ("7-9", "10-14", "15+"))
        wide_finishes = sum(row["finishes"] for band, row in world_overall["gap_bands"].items() if band in ("7-9", "10-14", "15+"))
        close = world_overall["fights"] - wide
        close_finishes = world_finishes - wide_finishes
        result.extend([
            f"Fresh five-year world replay: {world_finishes:,}/{world_overall['fights']:,} finishes ({pct(world_finishes, world_overall['fights']):.2f}%).",
            f"World bouts at gap <=6: {close:,} ({pct(close, world_overall['fights']):.2f}%), finish rate {pct(close_finishes, close):.2f}%.",
            f"World bouts at gap >=7: {wide:,} ({pct(wide, world_overall['fights']):.2f}%), finish rate {pct(wide_finishes, wide):.2f}%.",
        ])
        independent = world_sources.get("Independent Circuit")
        feeders = world_sources.get("Regional feeders")
        if independent:
            ind_fin = sum(independent["methods"][m] for m in FINISH_METHODS)
            result.append(f"Independent circuit finish rate: {pct(ind_fin, independent['fights']):.2f}% across {independent['fights']:,} bouts.")
        if feeders:
            feed_fin = sum(feeders["methods"][m] for m in FINISH_METHODS)
            result.append(f"Regional feeder finish rate: {pct(feed_fin, feeders['fights']):.2f}% across {feeders['fights']:,} bouts.")

    in_target = 50 <= tier_rates["low"] <= 56 and 38 <= tier_rates["mid"] <= 44 and 40 <= tier_rates["high"] <= 46
    if in_target:
        recommendation = "All three controlled tiers are inside the documented calibration bands; engine tuning is not warranted."
    else:
        outliers = []
        if not 50 <= tier_rates["low"] <= 56:
            outliers.append("low")
        if not 38 <= tier_rates["mid"] <= 44:
            outliers.append("mid")
        if not 40 <= tier_rates["high"] <= 46:
            outliers.append("high")
        recommendation = (
            "Controlled tier calibration is outside the documented band for " + ", ".join(outliers) +
            "; only a targeted mechanics review for those tiers is supported, not an aggregate finish-rate nerf."
        )
    result.extend([recommendation, "The world aggregate should not be used as a direct engine calibration target.", ""])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-tier", type=int, default=400)
    parser.add_argument("--mixed", type=int, default=1000)
    parser.add_argument("--world-years", type=int, default=5)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--seeds", default="", help="Comma-separated controlled-audit seeds to pool.")
    args = parser.parse_args()
    game = load_game_module()
    controlled_seeds = [int(item.strip()) for item in args.seeds.split(",") if item.strip()] or [args.seed]
    controlled_runs = []
    for controlled_seed in controlled_seeds:
        root = tk.Tk()
        root.withdraw()
        try:
            app = game.FightEmpireApp(root)
            app.refresh_all = lambda: None
            print(f"Controlled audit seed {controlled_seed}: {args.per_tier} fights per tier + {args.mixed} mixed-card fights", flush=True)
            controlled_runs.append(run_controlled(app, max(1, args.per_tier), max(1, args.mixed), controlled_seed))
        finally:
            root.destroy()
    controlled = {
        name: merge_stats([run[name] for run in controlled_runs])
        for name in ("Low (<68)", "Mid (68-79)", "High (80+)", "Realistic mixed cards")
    }

    world_overall = None
    world_sources = {}
    world_tiers = {}
    if args.world_years > 0:
        world_root = tk.Tk()
        world_root.withdraw()
        try:
            world_app = game.FightEmpireApp(world_root)
            world_overall, world_sources, world_tiers = run_world(world_app, args.world_years, args.seed)
        finally:
            world_root.destroy()

    lines = [
        "MMA WARRIORS - FIGHT / MATCHMAKING BALANCE AUDIT",
        "=" * 104,
        f"Controlled seeds {', '.join(map(str, controlled_seeds))}. World seed {args.seed}. Cloned/in-memory fighters only; no save changed.",
        f"Controlled pooled sample: {args.per_tier * len(controlled_seeds):,} each low/mid/high plus {args.mixed * len(controlled_seeds):,} realistic mixed-card bouts.",
        "Controlled matchmaking: same gender/division and pre-fight OVR gap <=6; mixed cards are 25% low, 55% mid, 20% high with one five-round main event per 10 bouts.",
        "Upset = lower pre-fight OVR fighter wins; draws and equal-OVR bouts are excluded from the upset denominator.",
        "",
        "CONTROLLED ENGINE CALIBRATION",
        "=" * 104,
    ]
    if len(controlled_runs) > 1:
        lines.extend(["PER-SEED FINISH RATES", "-" * 104])
        for controlled_seed, run in zip(controlled_seeds, controlled_runs):
            rates = []
            for name in ("Low (<68)", "Mid (68-79)", "High (80+)", "Realistic mixed cards"):
                stats = run[name]
                finishes = sum(stats["methods"][method] for method in FINISH_METHODS)
                rates.append(f"{name.split()[0]} {pct(finishes, stats['fights']):.2f}%")
            lines.append(f"{controlled_seed}: " + " | ".join(rates))
        lines.append("")
    for name in ("Low (<68)", "Mid (68-79)", "High (80+)", "Realistic mixed cards"):
        append_stats(lines, name, controlled[name], include_anomalies=True)

    if world_overall:
        lines.extend(["FRESH WORLD MATCHMAKING REPLAY", "=" * 104])
        append_stats(lines, f"All recorded MMA fights ({args.world_years} years)", world_overall, include_anomalies=True)
        lines.extend(["WORLD RESULTS BY SOURCE", "-" * 104])
        for name in ("Major promotions", "Regional feeders", "Independent Circuit"):
            if name in world_sources:
                append_stats(lines, name, world_sources[name])
        lines.extend(["WORLD RESULTS BY AVERAGE BOUT TIER", "-" * 104])
        for name in ("Low (<68)", "Mid (68-79)", "High (80+)"):
            if name in world_tiers:
                append_stats(lines, name, world_tiers[name])
        matchmaking = world_overall.get("matchmaking", {})
        ordinary = matchmaking.get("ordinary", 0)
        lines.extend([
            "MAJOR-PROMOTION ORDINARY MATCHMAKING",
            "-" * 104,
            f"Ordinary bouts {ordinary:,} | OVR gap <=6: {matchmaking.get('ordinary_within_6', 0):,} "
            f"({pct(matchmaking.get('ordinary_within_6', 0), ordinary):.2f}%) | "
            f"Forced division-depth mismatches: {matchmaking.get('ordinary_forced_mismatch', 0):,}",
            f"Average ordinary OVR gap: {matchmaking.get('ordinary_gap_total', 0) / max(1, ordinary):.2f} | "
            f"Preserved title/grudge/retirement/prospect exceptions: {matchmaking.get('exceptions', 0):,}",
            "",
        ])

    lines.extend(make_conclusion(controlled, world_overall, world_sources))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT}", flush=True)


if __name__ == "__main__":
    main()
