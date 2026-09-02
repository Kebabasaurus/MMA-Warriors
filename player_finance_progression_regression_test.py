"""Regression coverage for finance history, outlook and strategic investments."""

import tkinter as tk

from main import FightEmpireApp


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def unlock(app, milestone_id):
    app.achievement_log.append({
        "scope": "Promotion", "target": app.player_company_name,
        "company": app.player_company_name, "id": milestone_id,
    })


def main():
    root = tk.Tk()
    root.withdraw()
    try:
        app = FightEmpireApp(root, startup_progress=lambda *_: None)
        app.ensure_finance_defaults()
        require(app.finance["annual_history"] == [] and app.finance["roster_cost_history"] == [],
                "New and legacy-compatible finance state must start with empty reporting history.")
        require(app.finance["strategic_investments"] == {},
                "New and old saves must default to no owned strategic projects.")
        app.finance.update({"annual_history": None, "roster_cost_history": None, "strategic_investments": None})
        app.ensure_finance_defaults()
        require(app.finance["annual_history"] == [] and app.finance["roster_cost_history"] == []
                and app.finance["strategic_investments"] == {},
                "Null-shaped legacy finance reporting and investment fields must normalize safely.")

        app.finance["week_transactions"] = []
        app.finance["weekly_history"] = []
        opening = app.cash
        app.cash += 800_000
        app.record_finance_transaction(
            "Audit event", revenue=1_000_000, costs=200_000,
            category="Event", source="Promoted event", event="Audit event",
        )
        app.close_finance_week()
        annual = app.finance["annual_history"][-1]
        require(annual["year"] == app.current_year() and annual["revenue"] == 1_000_000
                and annual["costs"] == 200_000 and annual["net"] == 800_000,
                "Annual finance history must aggregate canonical transaction revenue and costs.")
        require(annual["ending"] == opening + 800_000,
                "Annual history must retain the real closing cash balance.")

        snapshot = app.record_roster_cost_snapshot()
        require(snapshot["roster"] == len([fighter for fighter in app.roster if not fighter.retired]),
                "Roster-cost history must count the active player roster.")
        require(snapshot["purse_pool"] >= snapshot["top_10_purses"] > 0,
                "Roster-cost history must expose total and top-ten purse commitments.")
        require(app.finance["roster_cost_history"][-1] == snapshot,
                "The monthly roster snapshot must persist in finance state.")

        app.player_event_archive = [{
            "month": app.month, "event_name": "Mix Audit",
            "finance": {"ticket_revenue": 100, "broadcast_income": 200, "sponsorship": 300, "merchandise": 400},
        }]
        app.record_finance_transaction("Non-event income", revenue=500, category="Transfer", source="Transfer fee")
        mix = app.player_revenue_mix(12)
        require(mix == {"Ticket sales": 100, "Broadcast": 200, "Sponsorship": 300, "Merchandise": 400, "Other": 500},
                "Revenue mix must separate event streams and retain non-event income.")

        first_rule = app.company_milestone_registry()[0]
        projection = app.company_milestone_projection(first_rule)
        require(set(projection) == {"monthly_net", "cash_gap", "event_gap", "eta_months", "blockers"},
                "Milestone projection must expose cash, pace, ETA and non-financial blockers.")

        app.company_pop = 75
        app.cash = 25_000_000
        unlock(app, "national_power")
        ok, message = app.purchase_strategic_investment("performance_institute")
        require(ok and "Performance Institute" in message,
                "An eligible company must be able to approve an unlocked strategic facility.")
        require(app.cash == 22_000_000 and "performance_institute" in app.owned_strategic_investments(),
                "Strategic investment approval must charge capital and persist ownership.")
        duplicate_ok, _duplicate_message = app.purchase_strategic_investment("performance_institute")
        require(not duplicate_ok, "A strategic project must never be purchased twice.")
        investment_rows = [row for row in app.finance["week_transactions"] if row.get("reference") == "investment:performance_institute"]
        require(len(investment_rows) == 1 and investment_rows[0]["category"] == "Investment",
                "Capital expenditure must use one canonical, idempotent finance reference.")

        event = {"venue": "Regional Arena", "region": app.player_region, "city": "London", "fights": [{}] * 5,
                 "broadcaster": "No Coverage", "ticket_price": 45, "marketing_budget": 18_000, "production_tier": "Standard"}
        app.finance["strategic_investments"] = {}
        baseline = app.calculate_event_finance(350, 180_000, event, [], 50, 50, 1.0)
        app.finance["strategic_investments"] = {"performance_institute": {"purchased_month": app.month}}
        improved = app.calculate_event_finance(350, 180_000, event, [], 50, 50, 1.0)
        require(improved["medical"] < baseline["medical"] and improved["fighter_pay"] == baseline["fighter_pay"],
                "A performance facility must lower its stated medical cost without touching signed purses.")

        before_upkeep = app.cash
        upkeep_task = next(task for label, task in app.monthly_player_business_steps() if label == "Strategic investment upkeep")
        upkeep_task()
        require(app.cash == before_upkeep - 90_000,
                "Owned strategic facilities must charge their stated monthly upkeep.")
        require(any(row.get("reference") == f"investment-upkeep:{app.month}" for row in app.finance["week_transactions"]),
                "Monthly strategic upkeep must be visible in the canonical ledger.")
        upkeep_task()
        require(app.cash == before_upkeep - 90_000,
                "Repeating the same month-end upkeep step must not charge a project twice.")

        unlock(app, "major_organisation")
        app.company_pop = 80
        app.cash = 20_000_000
        original_recorder = app.record_finance_transaction
        before_failure = (app.cash, dict(app.owned_strategic_investments()), list(app.finance["week_transactions"]))
        app.record_finance_transaction = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("late ledger failure"))
        try:
            app.purchase_strategic_investment("commercial_department")
        except RuntimeError:
            pass
        else:
            raise AssertionError("A simulated late strategic-investment failure did not propagate.")
        finally:
            app.record_finance_transaction = original_recorder
        require((app.cash, app.owned_strategic_investments(), app.finance["week_transactions"]) == before_failure,
                "A failed strategic purchase must restore cash, ownership and ledger state.")

        serialized = app.serialize_world()
        require("performance_institute" in serialized["finance"]["strategic_investments"],
                "Strategic project ownership must survive ordinary save serialization.")
        app.ensure_screen_built("finance")
        require(hasattr(app, "finance_annual_tree") and hasattr(app, "finance_investment_tree"),
                "The Finance screen must expose History & Outlook and Strategic Investments views.")
        app.refresh_finance()
        require(app.finance_annual_tree.get_children() and app.finance_investment_tree.get_children(),
                "Finance reporting and investment tables must populate after refresh.")
        print("PLAYER FINANCE PROGRESSION REGRESSION TEST PASSED")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
