"""Audit real promotion finances and a generated age-16 fighter cohort to retirement."""
import argparse
import importlib.util
import random
import statistics
import tkinter as tk
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent  # game root (scripts live in tools/)


def load_game_module():
    spec = importlib.util.spec_from_file_location("mma_warriors", ROOT / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def percentile(values, fraction):
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, default=45)
    parser.add_argument("--cohort-size", type=int, default=40)
    args = parser.parse_args()
    years = max(35, min(60, args.years))
    cohort_size = max(20, min(2_000, args.cohort_size))
    out = ROOT / "audits" / "career_cohort_finance_audit_latest.txt"

    random.seed(314159)
    game = load_game_module()
    root = tk.Tk()
    root.withdraw()
    try:
        app = game.FightEmpireApp(root)
        app.refresh_all = lambda: None
        app.write_log = lambda: None
        app.prompt_due_event = lambda: False
        app.open_awards_window = lambda *_args, **_kwargs: None
        app.show_event_summary = lambda *_args, **_kwargs: None
        app.enter_spectator_mode()

        feeders = [promo for promo in app.promotions if promo.is_regional_feeder]
        cohort = []
        used_names = app.active_fighter_names()
        for index in range(cohort_size):
            promo = feeders[index % len(feeders)]
            gender = "Female" if index % 4 == 3 else "Male"
            fighter = app.create_regional_feeder_fighter(promo.region, used_names, gender)
            fighter.age = 16
            fighter.record_w = fighter.record_l = fighter.record_d = 0
            fighter.feeder_origin = promo.name
            fighter.camp = promo.name
            fighter.contract_type = "Developmental"
            fighter.weight = random.choice(app.weight_classes)
            promo.roster.append(fighter)
            cohort.append(fighter)
            used_names.add(fighter.name)

        finance = defaultdict(lambda: {"events": 0, "revenue": 0, "expenses": 0, "profit": 0})
        original_simulate = app.simulate_ai_promotion_month

        def simulate_with_finance_audit(promo, *call_args, **call_kwargs):
            before = app.ai_event_archive[0] if app.ai_event_archive else None
            result = original_simulate(promo, *call_args, **call_kwargs)
            package = app.ai_event_archive[0] if app.ai_event_archive else None
            if package and package is not before and package.get("company") == promo.name:
                stats = finance[promo.name]
                event_finance = package.get("finance", {})
                stats["events"] += 1
                stats["revenue"] += event_finance.get("total_revenue", 0)
                stats["expenses"] += event_finance.get("total_expense", 0)
                stats["profit"] += package.get("profit", 0)
            return result

        app.simulate_ai_promotion_month = simulate_with_finance_audit
        print(f"{years}-year cohort and finance audit started ({cohort_size} generated 16-year-olds)", flush=True)
        for _tick in range(years * 12):
            # A real game month contains four weekly booking cycles. Omitting
            # them starves AI cards and makes career lengths meaningless.
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

        cohort_bouts = [fighter.record_w + fighter.record_l + fighter.record_d for fighter in cohort]
        retired = [fighter for fighter in cohort if fighter.retired]
        active = [fighter for fighter in cohort if not fighter.retired]
        finance_rows = sorted(finance.items(), key=lambda item: item[1]["profit"], reverse=True)
        total_revenue = sum(row["revenue"] for row in finance.values())
        total_expenses = sum(row["expenses"] for row in finance.values())
        total_profit = sum(row["profit"] for row in finance.values())

        rows = [
            "MMA WARRIORS - CAREER COHORT AND FINANCE AUDIT",
            f"Simulation: {years} accelerated years with four weekly booking cycles per month in Spectator Mode; {cohort_size} generated 16-year-olds were inserted into regional feeders. No save changed.",
            "",
            "AGE-16 COHORT TO RETIREMENT",
            f"Cohort: {len(cohort)} | Retired: {len(retired)} | Still active: {len(active)}",
            f"Career bouts: mean {statistics.mean(cohort_bouts):.1f} | median {statistics.median(cohort_bouts):.0f} | P10 {percentile(cohort_bouts, .10)} | P90 {percentile(cohort_bouts, .90)} | min {min(cohort_bouts)} | max {max(cohort_bouts)}",
            f"Career draws: {sum(fighter.record_d for fighter in cohort)} | Fighters with a draw: {sum(1 for fighter in cohort if fighter.record_d)}",
            f"Retirement age: mean {statistics.mean([fighter.age for fighter in retired]):.1f}" if retired else "Retirement age: no cohort retirements recorded.",
            "",
            "COHORT RESULTS",
            "Fighter                         Sex  Age Status    W   L   D Bouts  OVR  Potential",
            "-" * 86,
        ]
        for fighter in sorted(cohort, key=lambda item: (not item.retired, -(item.record_w + item.record_l + item.record_d), item.name)):
            bouts = fighter.record_w + fighter.record_l + fighter.record_d
            rows.append(f"{fighter.name[:30]:30} {fighter.gender[0]:>3} {fighter.age:>4} {'Retired' if fighter.retired else 'Active':8} {fighter.record_w:>3} {fighter.record_l:>3} {fighter.record_d:>3} {bouts:>5} {fighter.overall:>4} {fighter.potential:>10}")
        rows += [
            "",
            "AI EVENT FINANCE",
            f"All audited AI events: {sum(row['events'] for row in finance.values())} | Revenue ${total_revenue:,.0f} | Event expenses ${total_expenses:,.0f} | Event profit ${total_profit:,.0f}",
            f"Event profit margin: {total_profit / max(1, total_revenue) * 100:.1f}%",
            "Company                              Events       Revenue       Expenses         Profit Margin",
            "-" * 96,
        ]
        for name, stats in finance_rows:
            margin = stats["profit"] / max(1, stats["revenue"]) * 100
            rows.append(f"{name[:34]:34} {stats['events']:>6} ${stats['revenue']:>12,.0f} ${stats['expenses']:>12,.0f} ${stats['profit']:>14,.0f} {margin:>5.1f}%")
        rows += [
            "",
            "INTERPRETATION",
            "Event revenue and event expenses are recorded directly from completed AI cards. Monthly operating costs are not included in the event-profit column.",
            "Cohort results are generated through the same feeder, contract, camp, fight, retirement, and free-agent systems used by the world simulation.",
        ]
        out.write_text("\n".join(rows), encoding="utf-8")
        print(f"COHORT/FINANCE AUDIT PASSED: {out}", flush=True)
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
