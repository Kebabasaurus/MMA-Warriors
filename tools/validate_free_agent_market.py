import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stability_test import destroy_root, new_app, silence_dialogs


def snapshot(app):
    free_agents = [fighter for fighter in app.free_agents if not fighter.retired]
    majors = [promo for promo in app.promotions if not promo.is_regional_feeder]
    contracted = [fighter for promo in majors for fighter in promo.roster if not fighter.retired]
    bands = Counter(
        "<50" if fighter.overall < 50 else
        "50-59" if fighter.overall < 60 else
        "60-69" if fighter.overall < 70 else
        "70-79" if fighter.overall < 80 else "80+"
        for fighter in free_agents
    )
    genders = Counter(fighter.gender for fighter in free_agents)
    opening = sum(fighter.universe_entry_month == 0 for fighter in free_agents)
    return {
        "month": app.month,
        "week": app.week,
        "free_agents": len(free_agents),
        "opening_free_agents": opening,
        "male": genders["Male"],
        "female": genders["Female"],
        "major_rosters": len(contracted),
        "major_mean_ovr": round(sum(fighter.overall for fighter in contracted) / max(1, len(contracted)), 1),
        "bands": dict(bands),
    }


def main():
    parser = argparse.ArgumentParser(description="Run a save-backed free-agent market regression.")
    parser.add_argument("save", type=Path)
    parser.add_argument("--months", type=int, default=48)
    parser.add_argument("--seed", type=int, default=90617)
    parser.add_argument("--fast-fights", action="store_true")
    parser.add_argument("--market-only", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    silence_dialogs()
    random.seed(args.seed)
    root, app, callback_errors = new_app(args.seed)
    try:
        with args.save.open("r", encoding="utf-8") as handle:
            app.apply_world_data(json.load(handle))
        app.spectator_mode = True
        app.rules["autosave_enabled"] = False
        app.suppress_autosaves = True
        if args.fast_fights or args.market_only:
            def quick_fight(a, b, _fight):
                winner, loser = (a, b) if random.random() < 0.5 else (b, a)
                return winner, loser, "Decision", 3, [f"{winner.name} wins a market-validation decision."]
            app.simulate_fight = quick_fight
        start_month = app.month
        rows = [snapshot(app)]
        flows = Counter()

        def track(label, task):
            before = {fighter.fighter_id for fighter in app.free_agents if not fighter.retired}
            task()
            after = {fighter.fighter_id for fighter in app.free_agents if not fighter.retired}
            flows[f"{label} added"] += len(after - before)
            flows[f"{label} removed"] += len(before - after)
        target_month = start_month + args.months
        while app.month < target_month:
            if args.market_only:
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
                        track("regional cards", lambda promo=promo: app.simulate_regional_feeder_month(promo))
                app.advance_free_agent_market()
                track("roster reviews", app.review_ai_roster_cuts)
                track("upgrade reviews", app.review_ai_upgrade_replacements)
                track("contract market", app.market_churn)
                track("contract expiries", app.update_ai_contracts)
                track("retirements", app.process_retirements)
            else:
                steps, _month_changed = app.calendar_week_steps(include_autosave=False)
                for _label, task in steps:
                    task()
            if app.week == 1 and ((app.month - start_month) % 12 == 0 or app.month == target_month):
                row = snapshot(app)
                rows.append(row)
                print(
                    f"Progress {app.month - start_month}/{args.months} months: "
                    f"free agents {row['free_agents']}, opening-origin {row['opening_free_agents']}, "
                    f"major roster {row['major_rosters']}",
                    flush=True,
                )
        if callback_errors:
            raise AssertionError(f"Tk callback failure: {callback_errors[0][1]}")

        peak = max(row["free_agents"] for row in rows)
        final = rows[-1]
        opening_growth = final["opening_free_agents"] - rows[0]["opening_free_agents"]
        passed = peak <= 450 and final["free_agents"] <= 350 and opening_growth <= 180
        lines = [
            "MMA WARRIORS - FREE AGENT MARKET VALIDATION",
            f"Source: {args.save}",
            f"Seed: {args.seed} | Simulated months: {args.months}",
            "",
            "Month | Free | Opening-origin | M/F | Major roster | Major mean OVR | OVR bands",
        ]
        for row in rows:
            lines.append(
                f"{row['month']:>5} | {row['free_agents']:>4} | {row['opening_free_agents']:>14} | "
                f"{row['male']}/{row['female']} | {row['major_rosters']:>12} | {row['major_mean_ovr']:>14.1f} | {row['bands']}"
            )
        lines.extend([
            "",
            f"Peak free agents: {peak}",
            f"Opening-origin free-agent growth: {opening_growth:+d}",
            "Market flows: " + " | ".join(f"{key} {value}" for key, value in sorted(flows.items())),
            f"RESULT: {'PASS' if passed else 'FAIL'}",
        ])
        report = "\n".join(lines) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(report, encoding="utf-8")
        print(report)
        if not passed:
            raise SystemExit(1)
    finally:
        destroy_root(root)


if __name__ == "__main__":
    main()
