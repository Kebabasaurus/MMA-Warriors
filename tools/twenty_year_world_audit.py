"""Run a deterministic-shape, non-save-mutating long-world simulation audit."""
import argparse
import importlib.util
import random
import sys
import statistics
import tkinter as tk
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent  # game root (scripts live in tools/)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from constants import WEIGHTS


def load_game_module():
    spec = importlib.util.spec_from_file_location("mma_warriors", ROOT / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, default=20)
    parser.add_argument("--seed", type=int, default=2042)
    args = parser.parse_args()
    years = max(1, min(250, args.years))
    out = ROOT / "audits" / f"{years}_year_world_audit_seed_{args.seed}.txt"
    random.seed(args.seed)
    game = load_game_module()
    root = tk.Tk()
    root.withdraw()
    phase = "startup"
    try:
        app = game.FightEmpireApp(root)
        # This is an isolated in-memory test. Disable only presentation work,
        # not world, fight, finance, development, or retirement logic.
        app.refresh_all = lambda: None
        app.write_log = lambda: None
        app.prompt_due_event = lambda: False
        app.open_awards_window = lambda *_args, **_kwargs: None
        app.show_event_summary = lambda *_args, **_kwargs: None
        app.enter_spectator_mode()

        start_active = len(app.all_fighter_objects())
        start_promos = len(app.promotions)
        method_totals = Counter()
        original_record = app.record_season_result
        def record_with_audit(winner, loser, method, round_no, fight, excitement, company):
            method_totals[method] += 1
            return original_record(winner, loser, method, round_no, fight, excitement, company)
        app.record_season_result = record_with_audit
        showcase_totals = {"cards": 0, "bouts": 0}
        original_showcase = app.simulate_free_agent_showcases
        def showcase_with_audit():
            before = app.independent_showcase_counter
            result = original_showcase()
            if app.independent_showcase_counter > before:
                showcase_totals["cards"] += 1
                package = next((item for item in app.ai_event_archive
                                if item.get("company") == "Independent Circuit"), {})
                showcase_totals["bouts"] += package.get("fight_count", 0)
            return result
        app.simulate_free_agent_showcases = showcase_with_audit
        # Final cash is a poor balance metric: a company can recover before the
        # report is written. Keep a lightweight, in-memory financial timeline
        # so long-world audits reveal real pressure as it happens.
        financial = {}
        def watch_finances():
            for promo in app.promotions:
                if getattr(promo, "is_regional_feeder", False):
                    continue
                row = financial.setdefault(promo.name, {
                    "low_cash": promo.cash,
                    "negative_weekly_checks": 0,
                    "below_reserve_weekly_checks": 0,
                    "recovery_weekly_checks": 0,
                    "budget_blocked_booking_checks": 0,
                    "rescued": False,
                    "closed": False,
                })
                row["low_cash"] = min(row["low_cash"], promo.cash)
                reserve = max(120_000, promo.size * 6_500)
                row["negative_weekly_checks"] += int(promo.cash < 0)
                row["below_reserve_weekly_checks"] += int(promo.cash < reserve)
                strategy = getattr(promo, "strategy", {}) or {}
                row["recovery_weekly_checks"] += int(strategy.get("current_mode") == "Financial Recovery")
                executive = getattr(promo, "executive", {}) or {}
                row["rescued"] = row["rescued"] or bool(executive.get("rescue_capital_used"))

        original_ai_should_run_show = app.ai_should_run_show
        def ai_should_run_show_with_audit(promo):
            allowed = original_ai_should_run_show(promo)
            if not allowed and not getattr(promo, "is_regional_feeder", False):
                reserve = max(120_000, promo.size * 6_500)
                if promo.cash < reserve:
                    financial.setdefault(promo.name, {
                        "low_cash": promo.cash, "negative_weekly_checks": 0,
                        "below_reserve_weekly_checks": 0, "recovery_weekly_checks": 0,
                        "budget_blocked_booking_checks": 0, "rescued": False, "closed": False,
                    })["budget_blocked_booking_checks"] += 1
            return allowed
        app.ai_should_run_show = ai_should_run_show_with_audit

        watch_finances()
        annual = []
        last_showcase_cards = 0
        last_showcase_bouts = 0
        print(f"{years}-year weekly world audit started", flush=True)
        for tick in range(years * 12):
            phase = f"month loop {tick + 1}/{years * 12}"
            # Use the game's actual weekly path: this includes AI cards,
            # free-agent showcases, recovery, staff churn, and fight results.
            for week in range(1, 5):
                app.week = week
                app.process_world_week()
                watch_finances()
            old_year = app.current_year()
            app.month += 1
            app.week = 1
            app.process_world_month(player_ran_show=False)
            watch_finances()
            if app.current_year() != old_year:
                app.run_end_of_year_awards(old_year)
                app.age_world_one_year()
            if app.month % 12 == 1:
                active_now = [fighter for fighter in app.all_fighter_objects() if not fighter.retired]
                non_feeders = [promo for promo in app.promotions if not promo.is_regional_feeder]
                cash_values = [promo.cash for promo in non_feeders]
                annual.append({
                    "year": app.current_year() - 1,
                    "active": len(active_now),
                    "free_agents": len([fighter for fighter in app.free_agents if not fighter.retired]),
                    "avg_age": statistics.mean(f.age for f in active_now),
                    "median_cash": statistics.median(cash_values),
                    "max_cash": max(cash_values),
                    "capped": sum(1 for promo in non_feeders if promo.reputation_score >= 99),
                    "turnovers": sum(len(getattr(promo, "era_history", []) or []) for promo in non_feeders),
                    "showcase_cards": showcase_totals["cards"] - last_showcase_cards,
                    "showcase_bouts": showcase_totals["bouts"] - last_showcase_bouts,
                })
                last_showcase_cards = showcase_totals["cards"]
                last_showcase_bouts = showcase_totals["bouts"]
                print(f"Completed {app.month // 12} simulated year(s)", flush=True)

        phase = "building report"
        active = [fighter for fighter in app.all_fighter_objects() if not fighter.retired]
        companies = list(app.promotions)
        retired = list(app.retired_fighters)
        active_names = [fighter.name for fighter in active]
        age_bands = {
            "Under 25": sum(1 for fighter in active if fighter.age < 25),
            "25-34": sum(1 for fighter in active if 25 <= fighter.age <= 34),
            "35-39": sum(1 for fighter in active if 35 <= fighter.age <= 39),
            "40+": sum(1 for fighter in active if fighter.age >= 40),
        }
        non_feeders = [promo for promo in companies if not promo.is_regional_feeder]
        active_names_by_company = {promo.name for promo in non_feeders}
        for name, row in financial.items():
            row["closed"] = name not in active_names_by_company
        championship_promotions = list(non_feeders)
        division_counts = [len([fighter for fighter in promo.roster if fighter.gender == gender and fighter.weight == weight and not fighter.retired]) for promo in championship_promotions for gender in ("Male", "Female") for weight in WEIGHTS]
        titleholders = [fighter for promo in championship_promotions for fighter in promo.roster if fighter.champion]
        title_defenders = [fighter for fighter in retired + titleholders if getattr(fighter, "title_defenses", 0) > 0]
        total_cash = sum(max(0, promo.cash) for promo in non_feeders)
        top_cash = max((promo.cash for promo in non_feeders), default=0)
        company_rows = []
        for promo in companies:
            company_rows.append({
                "name": promo.name,
                "cash": promo.cash,
                "stability": promo.stability,
                "rep": promo.reputation_score,
                "size": promo.size,
                "roster": len([fighter for fighter in promo.roster if not fighter.retired]),
                "events": max(0, promo.event_counter - 1),
                "executive": (promo.executive or {}).get("name", "Player"),
                "security": (promo.executive or {}).get("job_security", 100),
                "legacy": getattr(promo, "legacy_score", 0),
            })
        company_rows.sort(key=lambda row: row["rep"], reverse=True)
        champions = sum(1 for promo in companies for fighter in promo.roster if fighter.champion)
        hof = [fighter for fighter in app.hall_of_famers()]
        rows = [
            f"MMA WARRIORS - {years} YEAR WORLD AUDIT",
            f"Simulation: {years * 12} months / {years * 48} full weekly cycles in Spectator Mode; seed {args.seed}; BAMMA was AI-managed and no save changed.",
            "",
            "WORLD HEALTH",
            f"Starting active fighters: {start_active}",
            f"Ending active fighters: {len(active)}", 
            f"Retirements: {len(retired)} | Retired-fighter draws: {sum(fighter.record_d for fighter in retired)} | Hall of Fame inductions: {len(hof)}",
            f"Promotions: start {start_promos}, end {len(app.promotions)} | Defunct: {len(getattr(app, 'defunct_promotions', []))} | Active champions: {champions}",
            f"Awards years recorded: {len(app.awards_history)} | Chronicle entries retained: {len(app.world_chronicle)}",
            f"Average active age: {statistics.mean(f.age for f in active):.1f}",
            f"Average active overall: {statistics.mean(f.overall for f in active):.1f}",
            f"Age bands: under 25 {age_bands['Under 25']} | 25-34 {age_bands['25-34']} | 35-39 {age_bands['35-39']} | 40+ {age_bands['40+']}",
            f"Women in active pool: {sum(1 for fighter in active if fighter.gender == 'Female')} ({sum(1 for fighter in active if fighter.gender == 'Female') / max(1, len(active)) * 100:.1f}%)",
            f"Free agents: {len(app.free_agents)} | Duplicate active names: {len(active_names) - len(set(active_names))}",
            f"Independent circuit: {showcase_totals['cards']} showcase cards | {showcase_totals['bouts']} bouts | {showcase_totals['bouts'] / max(1, showcase_totals['cards']):.1f} bouts per card | Average annual free agents: {statistics.mean(row['free_agents'] for row in annual):.1f}",
            f"Division depth: min {min(division_counts)} | median {statistics.median(division_counts):.0f} | buckets below 3 fighters {sum(1 for count in division_counts if count < 3)}",
            f"Champion coverage: {len(titleholders)}/{len(championship_promotions) * len(WEIGHTS) * 2} across {len(championship_promotions)} competitive promotions; {len(companies) - len(championship_promotions)} feeder circuits carry no belts | Fighters with a defense: {len(title_defenders)} | Average defenses among them: {statistics.mean(f.title_defenses for f in title_defenders):.1f}" if title_defenders else "Champion coverage: no title defenses recorded.",
            f"AI financial concentration: largest company holds {top_cash / max(1, total_cash) * 100:.1f}% of non-feeder cash | companies below $0: {sum(1 for promo in non_feeders if promo.cash < 0)}",
            "",
            "COMPANY OUTCOMES",
            "Company                              Rep Size Stability       Cash Roster Events Executive                    Security Legacy",
            "-" * 120,
        ]
        for row in company_rows:
            rows.append(f"{row['name'][:34]:34} {row['rep']:>3} {row['size']:>4} {row['stability']:>9} ${row['cash']:>10,} {row['roster']:>6} {row['events']:>6} {row['executive'][:27]:27} {row['security']:>8} {row['legacy']:>6}")
        rows += ["", "FINANCIAL PRESSURE (weekly checks across the full run)", "Company                              Lowest Cash  Neg Weeks  Below Reserve  Recovery Mode  Budget Blocks  Rescue  Closed", "-" * 120]
        for name, row in sorted(financial.items(), key=lambda item: (item[1]["low_cash"], item[0])):
            rows.append(
                f"{name[:34]:34} ${row['low_cash']:>11,} {row['negative_weekly_checks']:>10} "
                f"{row['below_reserve_weekly_checks']:>14} {row['recovery_weekly_checks']:>14} "
                f"{row['budget_blocked_booking_checks']:>14} {'Yes' if row['rescued'] else 'No':>7} {'Yes' if row['closed'] else 'No':>7}"
            )
        rows += ["", "RETIRED LEGENDS", "Fighter                          W   L   D Legacy Titles/Def Awards"]
        for fighter in sorted(retired, key=lambda item: item.legacy_score, reverse=True)[:25]:
            rows.append(f"{fighter.name[:30]:30} {fighter.record_w:>3} {fighter.record_l:>3} {fighter.record_d:>3} {fighter.legacy_score:>6} {fighter.title_wins:>2}/{fighter.title_defenses:<3} {fighter.award_count:>3}")
        rows += ["", "FIGHT METHODS - FULL AUDIT RUN"]
        total_methods = sum(method_totals.values())
        for method, count in method_totals.most_common():
            rows.append(f"{method:24} {count:>7}  {count / max(1, total_methods) * 100:>6.2f}%")
        rows += ["", "ANNUAL WORLD HEALTH (every simulated year)", "Year Active Free Agents Avg Age Showcase Cards/Bouts Median AI Cash     Max AI Cash        Companies 99+ Rep Executive Era Notes"]
        for row in annual:
            rows.append(f"{row['year']} {row['active']:>6} {row['free_agents']:>11} {row['avg_age']:>7.1f} {row['showcase_cards']:>8}/{row['showcase_bouts']:<5} ${row['median_cash']:>14,.0f} ${row['max_cash']:>16,.0f} {row['capped']:>17} {row['turnovers']:>19}")
        rows += ["", "EXECUTIVE / ERA NOTES"]
        for promo in sorted(app.promotions, key=lambda item: item.reputation_score, reverse=True):
            eras = getattr(promo, "era_history", []) or []
            if eras:
                rows.append(f"{promo.name}: {eras[0].get('year', '')} - {eras[0].get('note', '')}")
        out.write_text("\n".join(rows) + "\n", encoding="utf-8")
        print(f"{years}-YEAR AUDIT PASSED: {out}")
        print(f"Active {len(active)} | Retired {len(retired)} | HOF {len(hof)} | Awards {len(app.awards_history)}")
    except Exception as exc:
        out.write_text(f"MMA WARRIORS WORLD AUDIT FAILED\nPhase: {phase}\n{type(exc).__name__}: {exc}\n", encoding="utf-8")
        raise
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
