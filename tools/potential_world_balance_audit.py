"""Fast long-horizon audit for MMA rating and potential population balance."""
import argparse
import random
import statistics
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stability_test import destroy_root, new_app, silence_dialogs


def rating_band(value):
    if value < 50:
        return "<50"
    if value < 60:
        return "50-59"
    if value < 65:
        return "60-64"
    if value <= 75:
        return "65-75"
    if value < 82:
        return "76-81"
    if value < 90:
        return "82-89"
    return "90+"


def summarize(app, year):
    majors = [promo for promo in app.promotions if not promo.is_regional_feeder]
    regionals = [promo for promo in app.promotions if promo.is_regional_feeder]
    major_fighters = [fighter for promo in majors for fighter in promo.roster if not fighter.retired]
    regional_fighters = [fighter for promo in regionals for fighter in promo.roster if not fighter.retired]
    free_agents = [fighter for fighter in app.free_agents if not fighter.retired]
    all_active = major_fighters + regional_fighters + free_agents + [fighter for fighter in app.roster if not fighter.retired]
    ceilings = sum(fighter.overall >= fighter.potential for fighter in major_fighters)
    return {
        "year": year,
        "major_count": len(major_fighters),
        "major_mean": statistics.mean(f.overall for f in major_fighters) if major_fighters else 0,
        "major_potential": statistics.mean(f.potential for f in major_fighters) if major_fighters else 0,
        "major_bands": Counter(rating_band(f.overall) for f in major_fighters),
        "regional_count": len(regional_fighters),
        "regional_mean": statistics.mean(f.overall for f in regional_fighters) if regional_fighters else 0,
        "free_count": len(free_agents),
        "free_mean": statistics.mean(f.overall for f in free_agents) if free_agents else 0,
        "active_count": len(all_active),
        "active_mean": statistics.mean(f.overall for f in all_active) if all_active else 0,
        "at_ceiling": ceilings,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260717)
    args = parser.parse_args()
    years = max(1, min(100, args.years))
    random.seed(args.seed)
    silence_dialogs()
    root, app, callback_errors = new_app(args.seed)
    try:
        app.enter_spectator_mode()
        app.rules["autosave_enabled"] = False
        app.suppress_autosaves = True

        def quick_fight(a, b, _fight):
            # Ratings still influence the result, with broad fight-night form.
            chance_a = max(0.18, min(0.82, 0.5 + (a.overall - b.overall) * 0.018 + random.uniform(-0.12, 0.12)))
            winner, loser = (a, b) if random.random() < chance_a else (b, a)
            return winner, loser, random.choice(("Decision", "Decision", "TKO", "Submission")), random.randint(1, 3), []

        app.simulate_fight = quick_fight
        rows = [summarize(app, app.current_year())]
        for _ in range(years * 12):
            previous_year = app.current_year()
            app.month += 1
            app.week = 1
            if app.current_year() != previous_year:
                app.age_world_one_year()
            app.age_and_develop_fighters(app.roster, player_roster=True)
            app.age_and_develop_fighters(app.free_agents)
            for promo in app.promotions:
                app.age_and_develop_fighters(promo.roster)
                if promo.is_regional_feeder:
                    app.simulate_regional_feeder_month(promo)
            app.advance_free_agent_market()
            app.review_ai_roster_cuts()
            app.review_ai_upgrade_replacements()
            app.market_churn()
            app.update_ai_contracts()
            app.process_retirements()
            if (app.month - 1) % 12 == 0:
                row = summarize(app, app.current_year())
                rows.append(row)
                print(f"Year {row['year']}: major mean {row['major_mean']:.1f}; active mean {row['active_mean']:.1f}", flush=True)

        if callback_errors:
            raise AssertionError(f"Tk callback failure: {callback_errors[0][1]}")
        lines = [
            "MMA WARRIORS - POTENTIAL / WORLD BALANCE AUDIT",
            f"Seed {args.seed}; {years} years; fast neutral fight rendering; full development and market systems.",
            "",
            "Year | Major count/mean/potential | Regional count/mean | Free count/mean | All active count/mean | Major at ceiling",
        ]
        for row in rows:
            lines.append(
                f"{row['year']} | {row['major_count']}/{row['major_mean']:.1f}/{row['major_potential']:.1f} | "
                f"{row['regional_count']}/{row['regional_mean']:.1f} | {row['free_count']}/{row['free_mean']:.1f} | "
                f"{row['active_count']}/{row['active_mean']:.1f} | {row['at_ceiling']} ({row['at_ceiling'] / max(1, row['major_count']) * 100:.1f}%)"
            )
        final = rows[-1]
        lines.extend(["", "FINAL MAJOR RATING BANDS"])
        for band in ("<50", "50-59", "60-64", "65-75", "76-81", "82-89", "90+"):
            count = final["major_bands"][band]
            lines.append(f"{band:>5}: {count:>5} ({count / max(1, final['major_count']) * 100:5.1f}%)")
        output = ROOT / "audits" / "potential_world_balance_audit_latest.txt"
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {output}")
    finally:
        destroy_root(root)


if __name__ == "__main__":
    main()
