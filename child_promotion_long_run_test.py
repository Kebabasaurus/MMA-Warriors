"""Deterministic long-run regression for player-funded MMA child promotions.

The test uses a fresh in-memory career and keeps only the child promotion in
the simulated AI world.  That preserves the real calendar/world pipeline while
making the 48-week regression fast enough for repeatable release checks.
"""

import random
import tkinter as tk

from main import FightEmpireApp


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    random.seed(4511)
    root = tk.Tk()
    root.withdraw()
    callback_errors = []
    root.report_callback_exception = lambda exc, value, tb: callback_errors.append(value)
    try:
        app = FightEmpireApp(root)
        app.pending_custom_promotion_config = {
            "name": "Long Run Parent",
            "region": "Canada",
            "size": 38,
            "cash": 2_500_000,
            "stability": 64,
            "reputation": "Regional",
            "personality": "Seasonal",
            "roster_depth": 8,
            "genders": ["Male", "Female"],
            "weights": ["Featherweight", "Lightweight"],
            "theme": "UFC",
        }
        app.start_company_choice.set("Create New Promotion...")
        app.new_game()

        launch_ok, child = app.launch_ai_child_promotion(
            1_000_000, "Youth Prospects", 35, "Long Run Child"
        )
        require(launch_ok and child.is_child_promotion,
                "Long-run child promotion could not be launched")
        require(child.parent_company == app.player_company_name,
                "Child promotion lost its parent-company identity")
        require(child.parent_profit_share == 35 and child.roster,
                "Child promotion did not retain its configured share and opening roster")

        loan_candidate = next(
            fighter for fighter in app.roster
            if not fighter.retirement_pending and not fighter.injured
        )
        loan_ok, _loan_note = app.loan_fighter_to_child_promotion(
            child.name, loan_candidate.fighter_id
        )
        require(loan_ok, "A parent fighter could not be loaned before the long run")

        # Other promotions are intentionally removed from this in-memory audit
        # world.  The child still runs through calendar_week_steps(), including
        # market, contracts, AI booking, finance, media, and persistence paths.
        app.promotions = [child]
        for _ in range(48):
            app.advance_month()

        child = app.promotions[0]
        child_records = [
            record for record in app.result_records
            if record.get("company") == child.name
        ]
        active_roster = [fighter for fighter in child.roster if not fighter.retired]
        require((app.month, app.week) == (13, 1),
                "The long-run probe did not cross the expected annual boundary")
        require(len(active_roster) >= 12,
                "Child promotion lost viable roster depth during the long run")
        require(len(child.show_history or []) >= 1 and child_records,
                "Child promotion did not produce an archived AI event")
        require(child.strategy.get("last_event_finance"),
                "Child promotion did not retain event-finance telemetry")
        require(int((child.finance or {}).get("parent_distributions", 0) or 0) > 0,
                "Positive child-event profit never reached the parent ledger")
        require(any(
            "Child promotion profit share: Long Run Child" in row.get("label", "")
            for row in app.finance.get("week_transactions", [])
        ), "Child profit sharing was not recorded in the parent finance ledger")
        require(any(fighter.champion for fighter in active_roster),
                "Child promotion did not retain champion state after the long run")
        require(any(int(getattr(fighter, "contract_months", 0) or 0) <= 2
                    for fighter in active_roster),
                "Long-run contract countdown was not exercised")
        require(loan_candidate.fighter_id in (child.loaned_fighter_ids or []),
                "Loan index lost the protected parent fighter")
        require(any(fighter.fighter_id == loan_candidate.fighter_id
                    for fighter in child.roster),
                "Child AI removed a protected loaned fighter")

        saved = app.serialize_world()
        app.apply_world_data(saved)
        restored = next(
            promotion for promotion in app.promotions
            if promotion.name == "Long Run Child"
        )
        require(restored.is_child_promotion and restored.parent_profit_share == 35,
                "Long-run child identity did not survive save/load")
        require(loan_candidate.fighter_id in (restored.loaned_fighter_ids or []),
                "Long-run loan state did not survive save/load")
        require(any(record.get("company") == restored.name
                    for record in app.result_records),
                "Long-run child results did not survive save/load")
        require(not callback_errors,
                f"UI callback error during long-run child test: {callback_errors[0] if callback_errors else ''}")
    finally:
        root.destroy()

    print("CHILD PROMOTION LONG-RUN TEST PASSED")
    print("Reached Month 13 Week 1 through 48 calendar weeks with child events, finance, loans, contracts, and save/load intact.")


if __name__ == "__main__":
    main()
