"""Fast finance and roster forecast for MMA Warriors.

This deliberately omits fight resolution, camps, injuries, development, and UI
refresh work. It retains promotion targets, cash reserves, operating costs,
card-level revenue risk, contract turnover, and recruitment so long-horizon
roster/economy health can be inspected quickly. It never writes to a save.
"""

import csv
import json
import random
import tkinter as tk
from collections import defaultdict
from pathlib import Path

from main import FightEmpireApp


ROOT = Path(__file__).resolve().parent
SAVE_PATH = ROOT / "dist" / "MMA Warriors" / "Saves" / "Game 1.json"
AUDIT_DIR = ROOT / "Audits"
MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
CHECKPOINT_MONTHS = {7: "July", 12: "December"}


def active_members(promo):
    return [fighter for fighter in promo.roster if not fighter.retired]


def calendar_parts(month):
    return 2026 + (month - 1) // 12, (month - 1) % 12 + 1


def light_show_probability(promo):
    return {
        "Super Shows": 0.52,
        "Seasonal": 0.56,
        "Big Names": 0.58,
        "Prospect Builder": 0.68,
        "Star Builder": 0.60,
        "Frequent Small Cards": 0.78,
    }.get(promo.show_personality, 0.60)


def simulate_light_card(app, promo):
    roster = active_members(promo)
    if len(roster) < 12 or random.random() > light_show_probability(promo):
        return None
    strategy = app.promotion_strategy(promo)
    commercial = strategy.get("commercial_strength", promo.reputation_score)
    runway = app.ai_financial_runway(promo)
    if promo.cash < max(runway * 0.30, 350_000):
        return None

    fight_count = min(len(roster) // 2, random.randint(7, 10))
    selected = random.sample(roster, min(len(roster), fight_count * 2))
    average_purse = sum(fighter.purse for fighter in selected) / max(1, len(selected))
    average_quality = sum(fighter.overall + fighter.popularity * 0.9 for fighter in selected) / max(1, len(selected))
    roster_health = min(1.05, len(roster) / max(1, app.ai_roster_target(promo)))
    regional_pull = app.regional_market_score(promo.region)
    revenue_factor = 0.48 + commercial / 150 + strategy.get("market_momentum", 0) / 150
    revenue = average_quality * fight_count * promo.size * regional_pull * random.uniform(52, 94) * max(0.35, revenue_factor)
    revenue *= 0.72 + roster_health * 0.36
    projected_cost = average_purse * fight_count * 2 + promo.size * 9_500 + fight_count * 22_000
    downside_chance = max(0.08, min(0.18, 0.23 - commercial / 850))
    roll = random.random()
    if roll < downside_chance:
        revenue *= random.uniform(0.52, 0.74)
        projected_cost *= random.uniform(1.04, 1.16)
    elif roll > 0.93:
        revenue *= random.uniform(1.15, 1.35)
    reinvestment = max(0, revenue - projected_cost) * min(0.28, 0.12 + promo.size / 1_200)
    profit = round(revenue - projected_cost - reinvestment)
    promo.cash += profit
    margin = profit / max(1, projected_cost)
    if margin >= 0.25:
        promo.stability = min(100, promo.stability + 1)
    elif margin < -0.22:
        promo.stability = max(1, promo.stability - 2)
    elif margin < 0:
        promo.stability = max(1, promo.stability - 1)
    return profit


def process_light_turnover(app, promo, december=False):
    target = app.ai_financial_roster_target(promo)
    roster = active_members(promo)
    roster_count = len(roster)
    division_target = app.ai_division_target(promo)
    division_counts = defaultdict(int)
    for fighter in roster:
        division_counts[(fighter.gender, fighter.weight)] += 1
    for fighter in list(roster):
        fighter.contract_months = max(0, fighter.contract_months - 1)
        if december:
            fighter.age += 1
        retirement_risk = 0.0
        if fighter.age >= 42:
            retirement_risk = 0.38 + min(0.45, (fighter.age - 42) * 0.10)
        elif fighter.age >= 39:
            retirement_risk = 0.06 + (fighter.age - 39) * 0.07
        if retirement_risk and random.random() < retirement_risk:
            promo.roster.remove(fighter)
            roster_count -= 1
            division_counts[(fighter.gender, fighter.weight)] -= 1
            fighter.retired = True
            app.retired_fighters.append(fighter)
            continue
        if fighter.contract_months > 0:
            continue
        valuable = fighter.champion or fighter.overall >= 76 or fighter.potential >= 84 or fighter.popularity >= 48
        needed = roster_count <= target or division_counts[(fighter.gender, fighter.weight)] < division_target
        if (valuable or needed) and promo.cash > app.ai_contract_reserve(promo):
            fighter.contract_months = random.randint(12, 24)
            fighter.purse = round(fighter.purse * random.uniform(1.03, 1.13) / 500) * 500
        else:
            promo.roster.remove(fighter)
            roster_count -= 1
            division_counts[(fighter.gender, fighter.weight)] -= 1
            fighter.contract_type = "Free Agent"
            fighter.exclusive = False
            fighter.free_agent_months = 0
            app.free_agents.append(fighter)


def replenish_light_market(app):
    while len([fighter for fighter in app.free_agents if not fighter.retired]) < 420:
        fighter = app.create_generated_fighter(4, 38, 43, 82, region=random.choice(list(app.regions)))
        app.avoid_name_collision(fighter, app.active_fighter_names())
        fighter.contract_months = 0
        fighter.contract_type = "Free Agent"
        fighter.exclusive = False
        app.free_agents.append(fighter)


def recruit_lightly(app, promo):
    target = app.ai_financial_roster_target(promo)
    roster = active_members(promo)
    deficit = max(0, target - len(roster))
    if not deficit or promo.cash <= app.ai_contract_reserve(promo):
        return 0
    max_signings = min(7, max(1, round(deficit / 16)))
    signed = 0
    division_target = app.ai_division_target(promo)
    division_counts = defaultdict(int)
    for fighter in roster:
        division_counts[(fighter.gender, fighter.weight)] += 1
    for _ in range(max_signings):
        roster = active_members(promo)
        if len(roster) >= target:
            break
        candidates = [fighter for fighter in app.free_agents if not fighter.retired and fighter.age >= 18]
        if not candidates:
            break
        sample = random.sample(candidates, min(180, len(candidates)))
        sample.sort(
            key=lambda fighter: (
                max(-2, division_target - division_counts[(fighter.gender, fighter.weight)]) * 22
                + max(0, 4 - division_counts[(fighter.gender, fighter.weight)]) * 18
                + fighter.overall * 0.55
                + max(0, fighter.potential - fighter.overall) * 1.1
                + fighter.popularity * 0.25
                - fighter.purse / max(2_000, promo.size * 30)
            ),
            reverse=True,
        )
        fighter = sample[0]
        signing_bonus = max(1_500, round(fighter.purse * random.uniform(0.45, 0.80) / 500) * 500)
        if promo.cash - signing_bonus < app.ai_contract_reserve(promo):
            break
        app.free_agents.remove(fighter)
        promo.roster.append(fighter)
        promo.cash -= signing_bonus
        fighter.contract_months = random.randint(12, 24)
        fighter.contract_type = "Exclusive"
        fighter.exclusive = True
        division_counts[(fighter.gender, fighter.weight)] += 1
        signed += 1
    return signed


def snapshot_rows(app, label, report_month):
    rows = []
    year, month_in_year = calendar_parts(report_month)
    free_agents = len([fighter for fighter in app.free_agents if not fighter.retired])
    contracted = sum(len(active_members(promo)) for promo in app.promotions if not promo.is_regional_feeder)
    for promo in sorted((promo for promo in app.promotions if not promo.is_regional_feeder), key=lambda item: item.name):
        rows.append({
            "year": year,
            "checkpoint": label,
            "calendar_month": MONTH_NAMES[month_in_year - 1],
            "simulation_month": report_month,
            "promotion": promo.name,
            "roster": len(active_members(promo)),
            "target": app.ai_roster_target(promo),
            "cap": app.ai_roster_cap(promo),
            "cash": promo.cash,
            "runway": app.ai_financial_runway(promo),
            "stability": promo.stability,
            "free_agents": free_agents,
            "world_contracted": contracted,
        })
    return rows


def main():
    if not SAVE_PATH.exists():
        raise FileNotFoundError(f"Expected current save at {SAVE_PATH}")
    random.seed(100_726)
    root = tk.Tk()
    root.withdraw()
    try:
        app = FightEmpireApp(root)
        app.apply_world_data(json.loads(SAVE_PATH.read_text(encoding="utf-8")))
        app.suppress_autosaves = True
        audit_start = app.month
        rows = []
        card_profits = defaultdict(list)
        for _ in range(100 * 12):
            app.month += 1
            app.week = 4
            _year, month_in_year = calendar_parts(app.month)
            december = month_in_year == 12
            for promo in [item for item in app.promotions if not item.is_regional_feeder]:
                process_light_turnover(app, promo, december=december)
                profit = simulate_light_card(app, promo)
                if profit is not None:
                    card_profits[promo.name].append(profit)
            app.apply_ai_operating_costs()
            replenish_light_market(app)
            for promo in [item for item in app.promotions if not item.is_regional_feeder]:
                recruit_lightly(app, promo)
            if month_in_year in CHECKPOINT_MONTHS:
                rows.extend(snapshot_rows(app, CHECKPOINT_MONTHS[month_in_year], app.month))

        AUDIT_DIR.mkdir(exist_ok=True)
        csv_path = AUDIT_DIR / "finance_roster_light_100y_audit.csv"
        text_path = AUDIT_DIR / "finance_roster_light_100y_audit.txt"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        latest = rows[-len([promo for promo in app.promotions if not promo.is_regional_feeder]):]
        with text_path.open("w", encoding="utf-8") as handle:
            handle.write("MMA WARRIORS - LIGHT FINANCE AND ROSTER FORECAST\n")
            handle.write("No saves were written. Fight simulation, development, injuries, camps, and UI work were intentionally skipped.\n")
            handle.write("It retains target depth, card-level economic risk, operating costs, contract turnover, retirement pressure, and recruitment reserves.\n\n")
            handle.write(f"Start: Month {audit_start} | End: Month {app.month} | Checkpoints: July and December for 100 years\n\n")
            handle.write("FINAL CHECKPOINT\n")
            for row in latest:
                handle.write(f"{row['promotion']}: roster {row['roster']}/{row['target']} (cap {row['cap']}) | cash ${row['cash']:,} | runway ${row['runway']:,} | stability {row['stability']}\n")
            handle.write("\nCARD PROFIT SAMPLE (mean across light cards)\n")
            for name in sorted(card_profits):
                profits = card_profits[name]
                handle.write(f"{name}: {len(profits)} cards | mean ${round(sum(profits) / max(1, len(profits))):,} | low ${min(profits):,} | high ${max(profits):,}\n")
            handle.write(f"\nDetailed checkpoint data: {csv_path.name}\n")
        print(f"Audit complete: {text_path}")
        print(f"Detailed checkpoints: {csv_path}")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
