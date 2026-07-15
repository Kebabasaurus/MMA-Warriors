"""Run a deterministic-shape, non-save-mutating long-world simulation audit."""
import argparse
import importlib.util
import random
import sys
import statistics
import tkinter as tk
from collections import Counter, defaultdict
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
    parser.add_argument(
        "--no-academy-harness", action="store_true",
        help="Leave the spectator-only academy dormant instead of exercising its player-facing pipeline.",
    )
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

        # Spectator mode has no human operator, so its academy would otherwise
        # remain permanently dormant.  The audit harness runs one representative
        # level-two academy: it automatically accepts the best affordable leads
        # and releases ready graduates into the MMA free-agent market.  This is
        # deliberately audit-only and is identified as such in the report.
        academy_harness = not args.no_academy_harness
        if academy_harness:
            academy = app.academy_defaults()
            academy.update({
                "owned": True, "level": 2, "capacity": 10, "weekly_cost": 6_300,
                "network_active": True, "network_region": "Europe",
                "network_scout": "Audit Scout", "network_scout_skill": 70,
                "auto_train": True, "auto_showcases": True,
            })
            app.academy = academy

        starting_fighters = [fighter for fighter in app.all_fighter_objects() if not fighter.retired]
        start_active = len(starting_fighters)
        starting_cohort_ids = {id(fighter) for fighter in starting_fighters}
        start_promos = len(app.promotions)
        method_totals = Counter()
        original_record = app.record_season_result
        def record_with_audit(winner, loser, method, round_no, fight, excitement, company):
            method_totals[method] += 1
            if company and company != "Independent Circuit":
                company_activity[company]["bouts"] += 1
                company_activity[company]["fighters"].update((winner.name, loser.name))
            return original_record(winner, loser, method, round_no, fight, excitement, company)
        company_activity = defaultdict(lambda: {"bouts": 0, "fighters": set()})
        app.record_season_result = record_with_audit

        academy_totals = Counter()
        academy_graduate_development = []
        academy_graduate_ratings = []
        original_academy_week = app.process_academy_week
        def academy_week_with_audit():
            academy = app.academy
            before_leads = {item.get("name") for item in academy.get("talent_pool", [])}
            before_cards = academy.get("total_cards", 0)
            before_bouts = academy.get("total_bouts", 0)
            before_development = sum(item.get("development", 0) for item in academy.get("prospects", []))
            result = original_academy_week()
            after_leads = {item.get("name") for item in academy.get("talent_pool", [])}
            academy_totals["leads"] += len(after_leads - before_leads)
            academy_totals["expired_leads"] += len(before_leads - after_leads)
            academy_totals["cards"] += max(0, academy.get("total_cards", 0) - before_cards)
            academy_totals["bouts"] += max(0, academy.get("total_bouts", 0) - before_bouts)
            after_development = sum(item.get("development", 0) for item in academy.get("prospects", []))
            academy_totals["development_points"] += max(0, after_development - before_development)
            return result
        app.process_academy_week = academy_week_with_audit

        def operate_academy_harness():
            if not academy_harness:
                return
            academy = app.academy
            open_places = max(0, academy.get("capacity", 0) - len(academy.get("prospects", [])))
            candidates = sorted(
                academy.get("talent_pool", []),
                key=lambda item: (item.get("potential", 0), item.get("rating", 0), item.get("scout_confidence", 0)),
                reverse=True,
            )
            for item in candidates[:open_places]:
                academy["talent_pool"].remove(item)
                item.update({
                    "plan": "Automatic", "training_intensity": "Standard",
                    "amateur_w": 0, "amateur_l": 0, "amateur_d": 0,
                    "amateur_history": [], "weeks": 0, "development": 0,
                    "weeks_to_sign": 0, "academy_member": True,
                    "joined_month": app.month, "baseline_rating": item.get("rating", 40),
                })
                app.repair_academy_prospect(item)
                academy["prospects"].append(item)
                academy_totals["signings"] += 1
            for prospect in list(academy.get("prospects", [])):
                bouts = app.academy_amateur_fight_count(prospect)
                readiness = app.academy_graduation_readiness(prospect)
                if prospect.get("age", 0) < 18 or bouts < 4 or readiness < 68:
                    continue
                fighter = app.academy_prospect_to_fighter(prospect)
                fighter.contract_months = 0
                fighter.exclusive = False
                fighter.contract_type = "Free Agent"
                fighter.free_agent_months = 0
                app.record_academy_graduate(prospect, fighter, "MMA free-agent market (audit harness)")
                app.free_agents.append(fighter)
                academy["prospects"].remove(prospect)
                academy_totals["graduates"] += 1
                academy_graduate_development.append(prospect.get("development", 0))
                academy_graduate_ratings.append(prospect.get("rating", fighter.overall))

        combat_totals = defaultdict(Counter)
        combat_participants = defaultdict(set)
        combat_roster_samples = defaultdict(list)
        combat_roster_seen = defaultdict(set)
        for sport, world in app.combat_sport_worlds.items():
            combat_roster_seen[sport].update(fighter.name for fighter in world.get("roster", []))
        original_combat_card = app.run_combat_sport_card
        def combat_card_with_audit(sport, world, employer, player_owned=False, target_bouts=6):
            card = original_combat_card(sport, world, employer, player_owned=player_owned, target_bouts=target_bouts)
            if card and not player_owned:
                row = combat_totals[sport]
                bouts = card.get("bouts", [])
                row["cards"] += 1
                row["bouts"] += len(bouts)
                row["title_bouts"] += sum(bool(item.get("title")) for item in bouts)
                row["athlete_slots"] += len(bouts) * 2
                roster_names = {fighter.name for fighter in world.get("roster", [])}
                for item in bouts:
                    for name in (item.get("a", ""), item.get("b", "")):
                        if name in roster_names:
                            combat_participants[sport].add(name)
                        else:
                            row["guest_slots"] += 1
                finance = card.get("finance", {}) or {}
                row["revenue"] += finance.get("revenue", finance.get("total_revenue", 0))
                row["cost"] += finance.get("cost", finance.get("total_expense", 0))
                row["profit"] += finance.get("profit", 0)
            return card
        app.run_combat_sport_card = combat_card_with_audit

        original_replenish_sport = app.replenish_combat_sport_world
        def replenish_sport_with_audit(sport, world):
            additions = original_replenish_sport(sport, world)
            combat_totals[sport]["prospect_signings"] += additions or 0
            return additions
        app.replenish_combat_sport_world = replenish_sport_with_audit

        original_process_sports = app.process_combat_sport_worlds
        def process_sports_with_audit():
            before = {
                sport: {id(fighter) for fighter in world.get("roster", [])}
                for sport, world in app.combat_sport_worlds.items()
            }
            result = original_process_sports()
            free_ids = {id(fighter) for fighter in app.free_agents}
            for sport, old_ids in before.items():
                current_ids = {id(fighter) for fighter in app.combat_sport_worlds[sport].get("roster", [])}
                combat_totals[sport]["mma_crossovers"] += len((old_ids - current_ids) & free_ids)
            return result
        app.process_combat_sport_worlds = process_sports_with_audit

        original_sport_strategy = app.update_combat_sport_business_strategy
        def sport_strategy_with_audit(sport, world):
            before_cash = world.get("cash", 0)
            result = original_sport_strategy(sport, world)
            if before_cash < -1_000_000 and world.get("cash", 0) > before_cash + 2_000_000:
                combat_totals[sport]["rescues"] += 1
            return result
        app.update_combat_sport_business_strategy = sport_strategy_with_audit

        circulation = Counter()
        promotion_churn = defaultdict(Counter)
        known_ids = {id(fighter) for fighter in app.all_fighter_objects()}
        known_ids.update(
            id(fighter)
            for world in app.combat_sport_worlds.values()
            for fighter in world.get("roster", [])
        )
        previous_rosters = {promo.name: {id(fighter) for fighter in promo.roster} for promo in app.promotions}
        previous_free_agents = {id(fighter) for fighter in app.free_agents}

        def capture_circulation():
            nonlocal previous_rosters, previous_free_agents
            current_rosters = {promo.name: {id(fighter) for fighter in promo.roster} for promo in app.promotions}
            current_free_agents = {id(fighter) for fighter in app.free_agents}
            current_retired = {id(fighter) for fighter in app.retired_fighters}
            old_roster_union = set().union(*previous_rosters.values()) if previous_rosters else set()
            new_roster_union = set().union(*current_rosters.values()) if current_rosters else set()
            entered = current_free_agents - previous_free_agents
            exited = previous_free_agents - current_free_agents
            circulation["fa_inflow"] += len(entered)
            circulation["fa_outflow"] += len(exited)
            circulation["releases_to_fa"] += len(entered & old_roster_union)
            circulation["new_to_fa"] += len(entered - known_ids)
            circulation["fa_signings"] += len(exited & new_roster_union)
            circulation["fa_retirements"] += len(exited & current_retired)
            for name in set(previous_rosters) | set(current_rosters):
                old = previous_rosters.get(name, set())
                new = current_rosters.get(name, set())
                promotion_churn[name]["joined"] += len(new - old)
                promotion_churn[name]["left"] += len(old - new)
                promotion_churn[name]["from_fa"] += len((new - old) & previous_free_agents)
                promotion_churn[name]["to_fa"] += len((old - new) & current_free_agents)
            known_ids.update(current_free_agents | new_roster_union | current_retired)
            previous_rosters = current_rosters
            previous_free_agents = current_free_agents

        # Capture contract releases and signings at their actual boundary, so a
        # fighter cannot disappear from both sides of a coarse monthly snapshot.
        original_update_ai_contracts = app.update_ai_contracts
        def update_ai_contracts_with_audit():
            result = original_update_ai_contracts()
            capture_circulation()
            return result
        app.update_ai_contracts = update_ai_contracts_with_audit

        original_resolve_offers = app.resolve_ai_contract_offers
        def resolve_offers_with_audit():
            result = original_resolve_offers()
            capture_circulation()
            return result
        app.resolve_ai_contract_offers = resolve_offers_with_audit

        original_process_failures = app.process_promotion_failures
        def process_failures_with_audit():
            result = original_process_failures()
            capture_circulation()
            return result
        app.process_promotion_failures = process_failures_with_audit
        event_financial = defaultdict(Counter)
        original_simulate_ai_month = app.simulate_ai_promotion_month
        def simulate_ai_month_with_audit(promo, develop=True):
            before = promo.event_counter
            result = original_simulate_ai_month(promo, develop=develop)
            if promo.event_counter > before:
                package = next((item for item in app.ai_event_archive if item.get("company") == promo.name), {})
                finance = package.get("finance", {})
                row = event_financial[promo.name]
                row["cards"] += 1
                row["revenue"] += finance.get("total_revenue", 0)
                row["cost"] += finance.get("total_expense", 0)
                row["profit"] += finance.get("profit", 0)
                row["loss_cards"] += int(finance.get("profit", 0) < 0)
            return result
        app.simulate_ai_promotion_month = simulate_ai_month_with_audit
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
                    "low_stability": promo.stability,
                    "negative_weekly_checks": 0,
                    "below_reserve_weekly_checks": 0,
                    "distressed_weekly_checks": 0,
                    "recovery_weekly_checks": 0,
                    "budget_blocked_booking_checks": 0,
                    "rescued": False, "_rescue_active": False, "rescue_events": 0, "buyouts": 0,
                    "closed": False,
                })
                row["low_cash"] = min(row["low_cash"], promo.cash)
                row["low_stability"] = min(row["low_stability"], promo.stability)
                reserve = max(120_000, promo.size * 6_500)
                row["negative_weekly_checks"] += int(promo.cash < 0)
                row["below_reserve_weekly_checks"] += int(promo.cash < reserve)
                row["distressed_weekly_checks"] += int(promo.cash < 0 or promo.stability < 20)
                strategy = getattr(promo, "strategy", {}) or {}
                row["recovery_weekly_checks"] += int(strategy.get("current_mode") == "Financial Recovery")
                executive = getattr(promo, "executive", {}) or {}
                rescue_now = bool(executive.get("rescue_capital_used"))
                if rescue_now and not row["_rescue_active"]:
                    row["rescue_events"] += 1
                row["rescued"] = row["rescued"] or rescue_now
                row["_rescue_active"] = rescue_now
                row["buyouts"] = max(row["buyouts"], int(strategy.get("distressed_buyouts", 0)))

        original_ai_should_run_show = app.ai_should_run_show
        def ai_should_run_show_with_audit(promo):
            allowed = original_ai_should_run_show(promo)
            if not allowed and not getattr(promo, "is_regional_feeder", False):
                reserve = max(120_000, promo.size * 6_500)
                if promo.cash < reserve:
                    financial.setdefault(promo.name, {
                        "low_cash": promo.cash, "low_stability": promo.stability,
                        "negative_weekly_checks": 0, "below_reserve_weekly_checks": 0,
                        "distressed_weekly_checks": 0, "recovery_weekly_checks": 0,
                        "budget_blocked_booking_checks": 0, "rescued": False,
                        "_rescue_active": False, "rescue_events": 0, "buyouts": 0, "closed": False,
                    })["budget_blocked_booking_checks"] += 1
            return allowed
        app.ai_should_run_show = ai_should_run_show_with_audit

        watch_finances()
        annual = []
        last_showcase_cards = 0
        last_showcase_bouts = 0
        last_circulation = Counter()
        last_academy = Counter()
        last_combat_cards = 0
        last_combat_bouts = 0
        print(f"{years}-year weekly world audit started", flush=True)
        for tick in range(years * 12):
            phase = f"month loop {tick + 1}/{years * 12}"
            # Use the game's actual weekly path: this includes AI cards,
            # free-agent showcases, recovery, staff churn, and fight results.
            for week in range(1, 5):
                app.week = week
                app.process_world_week()
                operate_academy_harness()
                capture_circulation()
                watch_finances()
            old_year = app.current_year()
            app.month += 1
            app.week = 1
            app.process_world_month(player_ran_show=False)
            capture_circulation()
            watch_finances()
            for sport, world in app.combat_sport_worlds.items():
                roster = app.combat_sport_roster(sport, world.get("promotion", ""))
                combat_roster_samples[sport].append(len(roster))
                combat_roster_seen[sport].update(fighter.name for fighter in roster)
            if app.current_year() != old_year:
                app.run_end_of_year_awards(old_year)
                app.age_world_one_year()
            if app.month % 12 == 1:
                active_now = [fighter for fighter in app.all_fighter_objects() if not fighter.retired]
                non_feeders = [promo for promo in app.promotions if not promo.is_regional_feeder]
                cash_values = [promo.cash for promo in non_feeders]
                current_combat_cards = sum(row["cards"] for row in combat_totals.values())
                current_combat_bouts = sum(row["bouts"] for row in combat_totals.values())
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
                    "fa_in": circulation["fa_inflow"] - last_circulation["fa_inflow"],
                    "fa_out": circulation["fa_outflow"] - last_circulation["fa_outflow"],
                    "fa_signed": circulation["fa_signings"] - last_circulation["fa_signings"],
                    "fa_released": circulation["releases_to_fa"] - last_circulation["releases_to_fa"],
                    "academy_leads": academy_totals["leads"] - last_academy["leads"],
                    "academy_signings": academy_totals["signings"] - last_academy["signings"],
                    "academy_bouts": academy_totals["bouts"] - last_academy["bouts"],
                    "academy_graduates": academy_totals["graduates"] - last_academy["graduates"],
                    "academy_development": academy_totals["development_points"] - last_academy["development_points"],
                    "combat_cards": current_combat_cards - last_combat_cards,
                    "combat_bouts": current_combat_bouts - last_combat_bouts,
                })
                last_showcase_cards = showcase_totals["cards"]
                last_showcase_bouts = showcase_totals["bouts"]
                last_circulation = circulation.copy()
                last_academy = academy_totals.copy()
                last_combat_cards = current_combat_cards
                last_combat_bouts = current_combat_bouts
                print(f"Completed {app.month // 12} simulated year(s)", flush=True)

        phase = "building report"
        active = [fighter for fighter in app.all_fighter_objects() if not fighter.retired]
        starting_cohort_active = [fighter for fighter in active if id(fighter) in starting_cohort_ids]
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
        world_roster_buckets = Counter((fighter.gender, fighter.weight) for fighter in active)
        free_agent_buckets = Counter(
            (fighter.gender, fighter.weight) for fighter in app.free_agents if not fighter.retired
        )
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
                "joined": promotion_churn[promo.name]["joined"],
                "left": promotion_churn[promo.name]["left"],
                "used": len(company_activity[promo.name]["fighters"]),
                "bouts": company_activity[promo.name]["bouts"],
                "executive": (promo.executive or {}).get("name", "Player"),
                "security": (promo.executive or {}).get("job_security", 100),
                "legacy": getattr(promo, "legacy_score", 0),
            })
        company_rows.sort(key=lambda row: row["rep"], reverse=True)
        champions = sum(1 for promo in companies for fighter in promo.roster if fighter.champion)
        hof = [fighter for fighter in app.hall_of_famers()]
        academy_destinations = Counter()
        promotion_names_by_fighter = {
            fighter.name: promo.name for promo in companies for fighter in promo.roster
        }
        free_agent_names = {fighter.name for fighter in app.free_agents}
        retired_names = {fighter.name for fighter in retired}
        for alumnus in app.academy.get("alumni", []):
            name = alumnus.get("name", "")
            if name in promotion_names_by_fighter:
                academy_destinations["promotion roster"] += 1
            elif name in free_agent_names:
                academy_destinations["free agent"] += 1
            elif name in retired_names:
                academy_destinations["retired"] += 1
            else:
                academy_destinations["other/expired tracking"] += 1
        rows = [
            f"MMA WARRIORS - {years} YEAR WORLD AUDIT",
            f"Simulation: {years * 12} months / {years * 48} full weekly cycles in Spectator Mode; seed {args.seed}; BAMMA was AI-managed and no save changed.",
            "",
            "WORLD HEALTH",
            f"Starting active fighters: {start_active}",
            f"Ending active fighters: {len(active)}", 
            (f"Starting cohort still active: {len(starting_cohort_active)}" +
             (f" | Oldest remaining: {max(fighter.age for fighter in starting_cohort_active)}" if starting_cohort_active else "")),
            f"Retirements: {len(retired)} | Retired-fighter draws: {sum(fighter.record_d for fighter in retired)} | Hall of Fame inductions: {len(hof)}",
            f"Promotions: start {start_promos}, end {len(app.promotions)} | Defunct: {len(getattr(app, 'defunct_promotions', []))} | Active champions: {champions}",
            f"Awards years recorded: {len(app.awards_history)} | Chronicle entries retained: {len(app.world_chronicle)}",
            f"Average active age: {statistics.mean(f.age for f in active):.1f}",
            f"Average active overall: {statistics.mean(f.overall for f in active):.1f}",
            f"Age bands: under 25 {age_bands['Under 25']} | 25-34 {age_bands['25-34']} | 35-39 {age_bands['35-39']} | 40+ {age_bands['40+']}",
            f"Women in active pool: {sum(1 for fighter in active if fighter.gender == 'Female')} ({sum(1 for fighter in active if fighter.gender == 'Female') / max(1, len(active)) * 100:.1f}%)",
            f"Free agents: {len(app.free_agents)} | Duplicate active names: {len(active_names) - len(set(active_names))}",
            f"Free-agent circulation: inflow {circulation['fa_inflow']} | outflow {circulation['fa_outflow']} | promotion releases {circulation['releases_to_fa']} | negotiated signings {circulation['fa_signings']} | retirements from market {circulation['fa_retirements']} | new/generated entrants {circulation['new_to_fa']}",
            f"Independent circuit: {showcase_totals['cards']} showcase cards | {showcase_totals['bouts']} bouts | {showcase_totals['bouts'] / max(1, showcase_totals['cards']):.1f} bouts per card | Average annual free agents: {statistics.mean(row['free_agents'] for row in annual):.1f}",
            f"Division depth: min {min(division_counts)} | median {statistics.median(division_counts):.0f} | buckets below 3 fighters {sum(1 for count in division_counts if count < 3)}",
            f"Champion coverage: {len(titleholders)}/{len(championship_promotions) * len(WEIGHTS) * 2} across {len(championship_promotions)} competitive promotions; {len(companies) - len(championship_promotions)} feeder circuits carry no belts | Fighters with a defense: {len(title_defenders)} | Average defenses among them: {statistics.mean(f.title_defenses for f in title_defenders):.1f}" if title_defenders else "Champion coverage: no title defenses recorded.",
            f"AI financial concentration: largest company holds {top_cash / max(1, total_cash) * 100:.1f}% of non-feeder cash | companies below $0: {sum(1 for promo in non_feeders if promo.cash < 0)}",
            "",
            "COMPANY OUTCOMES",
            "Company                              Rep Size Stability       Cash Roster Events Joined Left Used/Bouts Executive                    Security Legacy",
            "-" * 150,
        ]
        for row in company_rows:
            rows.append(f"{row['name'][:34]:34} {row['rep']:>3} {row['size']:>4} {row['stability']:>9} ${row['cash']:>10,} {row['roster']:>6} {row['events']:>6} {row['joined']:>6} {row['left']:>4} {row['used']:>4}/{row['bouts']:<5} {row['executive'][:27]:27} {row['security']:>8} {row['legacy']:>6}")
        event_cards = sum(row["cards"] for row in event_financial.values())
        event_revenue = sum(row["revenue"] for row in event_financial.values())
        event_cost = sum(row["cost"] for row in event_financial.values())
        event_profit = sum(row["profit"] for row in event_financial.values())
        event_losses = sum(row["loss_cards"] for row in event_financial.values())
        rows += [
            "", "AI MMA EVENT ECONOMICS",
            (f"Cards {event_cards} | Revenue ${event_revenue:,} | Cost ${event_cost:,} | Profit ${event_profit:,} | "
             f"Retained margin {event_profit / max(1, event_revenue) * 100:.1f}% | Loss-making cards {event_losses}/{event_cards} ({event_losses / max(1, event_cards) * 100:.1f}%)"),
            "Company                              Cards  Margin   Loss Cards",
            "-" * 70,
        ]
        for name, row in sorted(event_financial.items(), key=lambda item: item[0]):
            rows.append(
                f"{name[:34]:34} {row['cards']:>5} {row['profit'] / max(1, row['revenue']) * 100:>6.1f}% "
                f"{row['loss_cards']:>6}/{row['cards']:<5}"
            )
        rows += ["", "FINANCIAL PRESSURE (weekly checks across the full run)", "Company                              Lowest Cash Low Stab Neg Weeks Below Reserve Distressed Recovery Budget Blocks Rescues Buyouts Closed", "-" * 140]
        for name, row in sorted(financial.items(), key=lambda item: (item[1]["low_cash"], item[0])):
            rows.append(
                f"{name[:34]:34} ${row['low_cash']:>11,} {row['low_stability']:>8} {row['negative_weekly_checks']:>9} "
                f"{row['below_reserve_weekly_checks']:>13} {row['distressed_weekly_checks']:>10} {row['recovery_weekly_checks']:>8} "
                f"{row['budget_blocked_booking_checks']:>13} {row['rescue_events']:>7} {row['buyouts']:>7} {'Yes' if row['closed'] else 'No':>6}"
            )
        academy = app.academy
        rows += [
            "", "ACADEMY PIPELINE (representative autonomous audit harness)" if academy_harness else "ACADEMY PIPELINE",
            (f"Leads {academy_totals['leads']} | Signings {academy_totals['signings']} | Expired leads {academy_totals['expired_leads']} | "
             f"Showcase cards {academy_totals['cards']} | Bouts {academy_totals['bouts']} | Graduates {academy_totals['graduates']} | "
             f"Training/bout development points {academy_totals['development_points']}") if academy_harness else "Academy harness disabled; spectator mode has no organically operated academy.",
        ]
        if academy_harness:
            rows.append(
                f"Current prospects {len(academy.get('prospects', []))}/{academy.get('capacity', 0)} | Open leads {len(academy.get('talent_pool', []))} | "
                f"Average graduate development {statistics.mean(academy_graduate_development):.1f} | Average graduation rating {statistics.mean(academy_graduate_ratings):.1f}"
                if academy_graduate_development else
                f"Current prospects {len(academy.get('prospects', []))}/{academy.get('capacity', 0)} | Open leads {len(academy.get('talent_pool', []))} | No graduates reached readiness."
            )
            rows.append("Graduate destinations now: " + (" | ".join(f"{key} {value}" for key, value in sorted(academy_destinations.items())) or "none"))

        rows += ["", "COMBAT-SPORT CIRCUIT HEALTH", "Sport                    Cards Bouts Title Prospect Crossovers Guest Roster Avg/Now Used/Ever      Revenue         Cost       Profit Rescue Cash/Stab Titles"]
        for sport, world in sorted(app.combat_sport_worlds.items()):
            row = combat_totals[sport]
            roster = app.combat_sport_roster(sport, world.get("promotion", ""))
            average_roster = statistics.mean(combat_roster_samples[sport]) if combat_roster_samples[sport] else len(roster)
            usage = len(combat_participants[sport]) / max(1, len(combat_roster_seen[sport])) * 100
            titles = world.get("titles", {}) or {}
            rows.append(
                f"{sport[:24]:24} {row['cards']:>5} {row['bouts']:>5} {row['title_bouts']:>5} {row['prospect_signings']:>8} "
                f"{row['mma_crossovers']:>10} {row['guest_slots']:>5} {average_roster:>5.1f}/{len(roster):<3} {len(combat_participants[sport]):>3}/{len(combat_roster_seen[sport]):<3} {usage:>5.1f}% "
                f"${row['revenue']:>11,} ${row['cost']:>11,} ${row['profit']:>11,} {row['rescues']:>6} "
                f"${world.get('cash', 0):>9,}/{world.get('stability', 0):<3} {sum(bool(value) for value in titles.values())}/{len(titles)}"
            )

        rows += ["", "MMA ROSTER POPULATION BY GENDER / WEIGHT", "Gender Weight                         Active  Free Agents"]
        for gender in ("Male", "Female"):
            for weight in WEIGHTS:
                rows.append(f"{gender:6} {weight:30} {world_roster_buckets[(gender, weight)]:>7} {free_agent_buckets[(gender, weight)]:>12}")
        rows += ["", "BEST ACTIVE FIGHTERS", "Fighter                        Age OVR  W   L   D Legacy Titles/Def Champion"]
        for fighter in sorted(
            active,
            key=lambda item: (item.legacy_score, item.overall, item.elo_rating, item.record_w - item.record_l),
            reverse=True,
        )[:25]:
            rows.append(
                f"{fighter.name[:30]:30} {fighter.age:>3} {fighter.overall:>3} {fighter.record_w:>3} {fighter.record_l:>3} {fighter.record_d:>3} "
                f"{fighter.legacy_score:>6} {fighter.title_wins:>2}/{fighter.title_defenses:<3} {'Yes' if fighter.champion else 'No'}"
            )
        rows += ["", "BEST ACTIVE PROSPECTS", "Fighter                        Age OVR POT Gap Record      Region"]
        for fighter in sorted(
            [item for item in active if item.age <= 25],
            key=lambda item: (item.potential, item.potential - item.overall, item.overall, item.record_w - item.record_l),
            reverse=True,
        )[:20]:
            rows.append(
                f"{fighter.name[:30]:30} {fighter.age:>3} {fighter.overall:>3} {fighter.potential:>3} "
                f"{fighter.potential - fighter.overall:>3} {fighter.record:11} {fighter.region}"
            )
        rows += ["", "RETIRED LEGENDS", "Fighter                          W   L   D Legacy Titles/Def Awards"]
        for fighter in sorted(retired, key=lambda item: item.legacy_score, reverse=True)[:25]:
            rows.append(f"{fighter.name[:30]:30} {fighter.record_w:>3} {fighter.record_l:>3} {fighter.record_d:>3} {fighter.legacy_score:>6} {fighter.title_wins:>2}/{fighter.title_defenses:<3} {fighter.award_count:>3}")
        rows += ["", "FIGHT METHODS - FULL AUDIT RUN"]
        total_methods = sum(method_totals.values())
        for method, count in method_totals.most_common():
            rows.append(f"{method:24} {count:>7}  {count / max(1, total_methods) * 100:>6.2f}%")
        rows += ["", "ANNUAL WORLD HEALTH (every simulated year)", "Year Active Free Agents AvgAge  FA In/Out Sign/Release  Showcase  Academy L/S/B/G/Dev  Combat Cards/Bouts  Median AI Cash     Max AI Cash      99+Rep Eras"]
        for row in annual:
            rows.append(
                f"{row['year']} {row['active']:>6} {row['free_agents']:>11} {row['avg_age']:>6.1f} "
                f"{row['fa_in']:>5}/{row['fa_out']:<5} {row['fa_signed']:>4}/{row['fa_released']:<7} "
                f"{row['showcase_cards']:>3}/{row['showcase_bouts']:<4} "
                f"{row['academy_leads']:>3}/{row['academy_signings']:<3}/{row['academy_bouts']:<3}/{row['academy_graduates']:<3}/{row['academy_development']:<4} "
                f"{row['combat_cards']:>5}/{row['combat_bouts']:<5} ${row['median_cash']:>14,.0f} ${row['max_cash']:>16,.0f} {row['capped']:>6} {row['turnovers']:>4}"
            )
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
