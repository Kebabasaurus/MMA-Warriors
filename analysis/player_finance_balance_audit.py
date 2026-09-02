"""Deterministic early/mid/late player-finance balance audit.

Run from the repository root.  The audit copies the shipped universe database
to an isolated temporary runtime and never reads or writes player careers.
"""

import json
import os
import random
import shutil
import sys
import tempfile
import tkinter as tk
from pathlib import Path


def run():
    random.seed(90210)
    repo = Path(__file__).resolve().parents[1]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    runtime = Path(tempfile.mkdtemp(prefix="mma-player-finance-audit-"))
    (runtime / "Databases").mkdir()
    shutil.copy2(
        repo / "Databases" / "Default Universe.universe.json",
        runtime / "Databases" / "Default Universe.universe.json",
    )
    os.environ["MMA_WARRIORS_DATA_DIR"] = str(runtime)

    from main import FightEmpireApp

    root = tk.Tk()
    root.withdraw()
    try:
        app = FightEmpireApp(root, startup_progress=lambda *_: None)
        curated = sorted((fighter.purse for fighter in app.roster if not fighter.generated), reverse=True)
        generated = sorted((fighter.purse for fighter in app.roster if fighter.generated), reverse=True)
        opening = {
            "starting_cash": app.cash,
            "roster_size": len(app.roster),
            "curated_fighters": len(curated),
            "generated_fighters": len(generated),
            "top_10_curated_purses": sum(curated[:10]),
            "estimated_pre_balance_top_10": round(sum(curated[:10]) / 0.55),
            "highest_generated_purse": max(generated),
        }

        scenarios = (
            {"stage": "Early", "pop": 38, "stability": 52, "hype": 360, "purses": 260_000,
             "venue": "Regional Arena", "outlet": "combat_cable", "reach": 44,
             "rights_fee": 70_000, "sponsors": [18_000]},
            {"stage": "Mid", "pop": 68, "stability": 68, "hype": 600, "purses": 750_000,
             "venue": "National Stadium", "outlet": "world_fight_pass", "reach": 66,
             "rights_fee": 260_000, "sponsors": [30_000] * 4},
            {"stage": "Late", "pop": 88, "stability": 82, "hype": 780, "purses": 1_450_000,
             "venue": "Mega Stadium", "outlet": "global_sports_plus", "reach": 92,
             "rights_fee": 1_200_000, "sponsors": [45_000] * 8},
        )
        stage_rows = []
        payroll = sum(staff["salary"] for staff in app.staff)
        for scenario in scenarios:
            app.company_pop = scenario["pop"]
            app.company_stability = scenario["stability"]
            app.finance["sponsor_deals"] = [{"fee": fee} for fee in scenario["sponsors"]]
            app.finance["media_rights"] = {
                "status": "Active", "months": 12, "events_remaining": 12,
                "outlet_id": scenario["outlet"], "name": scenario["outlet"],
                "reach": scenario["reach"], "fee": scenario["rights_fee"],
            }
            event = {
                "name": "Audit", "month": 1, "week": 1, "region": app.player_region,
                "city": "London", "venue": scenario["venue"], "broadcaster": "Regional Webcast",
                "fights": [{}] * 8, "marketing_budget": 18_000, "production_tier": "Standard",
            }
            event["ticket_price"] = app.event_fair_ticket_price(
                scenario["hype"], 1.0, scenario["venue"]
            )
            app.result_records = []
            first = app.calculate_event_finance(
                scenario["hype"], scenario["purses"], event, [], 50, 50, 1.0
            )
            app.result_records = [{
                "company": app.player_company_name, "date": "Month 1 Week 1",
                "event": "First monthly show",
            }]
            second = app.calculate_event_finance(
                scenario["hype"], scenario["purses"], event, [], 50, 50, 1.0
            )
            office = app.player_monthly_office_cost()
            stage_rows.append({
                "stage": scenario["stage"], "office": office, "staff_payroll": payroll,
                "first_revenue": first["total_revenue"], "first_profit": first["profit"],
                "monthly_net_after_fixed": first["profit"] - office - payroll,
                "second_cadence_factor": second["cadence_factor"],
                "second_profit": second["profit"],
            })

        checks = {
            "opening_top_10_under_650k": opening["top_10_curated_purses"] <= 650_000,
            "early_first_card_survives": stage_rows[0]["monthly_net_after_fixed"] > -app.cash,
            "office_scales_by_stage": stage_rows[0]["office"] < stage_rows[1]["office"] < stage_rows[2]["office"],
            "second_card_is_not_free_growth": all(
                row["second_profit"] < row["first_profit"] for row in stage_rows
            ),
        }
        if not all(checks.values()):
            raise AssertionError(checks)
        return {"seed": 90210, "opening": opening, "stages": stage_rows, "checks": checks}
    finally:
        root.destroy()
        shutil.rmtree(runtime)


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
