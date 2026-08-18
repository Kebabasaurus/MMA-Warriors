"""Run a real ten-year calendar simulation and audit every promotion ledger.

This is intentionally a play-level audit rather than a unit test. It keeps the
full seeded AI world, launches one child promotion, advances 480 real calendar
weeks, and checks weekly cash reconciliation for the player and every
non-feeder promotion.
"""

import argparse
import random
import tkinter as tk
from tkinter import messagebox

from main import FightEmpireApp


def silence_dialogs():
    messagebox.showinfo = lambda *args, **kwargs: None
    messagebox.showwarning = lambda *args, **kwargs: None
    messagebox.showerror = lambda *args, **kwargs: None
    messagebox.askyesno = lambda *args, **kwargs: False
    messagebox.askyesnocancel = lambda *args, **kwargs: False


def check_finance(app, failures):
    player = app.finance_reconciliation_status(app.finance, app.cash)
    if not player["balanced"]:
        failures.append(f"player ledger off by ${player['difference']:,} at Month {app.month} Week {app.week}")
    for promo in app.promotions:
        if getattr(promo, "is_regional_feeder", False):
            continue
        report = app.finance_reconciliation_status(getattr(promo, "finance", {}) or {}, promo.cash)
        if not report["balanced"]:
            failures.append(f"{promo.name} ledger off by ${report['difference']:,} at Month {app.month} Week {app.week}")


def run(seed):
    random.seed(seed)
    silence_dialogs()
    root = tk.Tk()
    root.withdraw()
    callback_errors = []
    root.report_callback_exception = lambda exc, value, tb: callback_errors.append(str(value))
    try:
        app = FightEmpireApp(root)
        # The shipped player start is below the minimum child-promotion launch
        # budget. Fund this audit scenario explicitly so the child ledger is
        # exercised without changing the shipped starting economy.
        app.cash = max(app.cash, 2_000_000)
        audit_starting_cash = app.cash
        launch_ok, child = app.launch_ai_child_promotion(1_000_000, "Balanced", 25, "Ten Year Development")
        if not launch_ok:
            raise AssertionError(f"child promotion launch failed: {child}")
        initial_cash = app.cash
        initial_promo_count = len([promo for promo in app.promotions if not getattr(promo, "is_regional_feeder", False)])
        failures = []
        yearly = []
        for week_number in range(1, 481):
            app.advance_month()
            check_finance(app, failures)
            if week_number % 48 == 0:
                active_promos = [promo for promo in app.promotions if not getattr(promo, "is_regional_feeder", False)]
                yearly.append({
                    "year": week_number // 48,
                    "month": app.month,
                    "player_cash": app.cash,
                    "child_cash": child.cash if child in app.promotions else None,
                    "promotions": len(active_promos),
                    "negative_promotions": sum(1 for promo in active_promos if promo.cash < 0),
                    "free_agents": len([fighter for fighter in app.free_agents if not fighter.retired]),
                    "player_transactions": len(app.finance.get("week_transactions", [])),
                })
        active_promos = [promo for promo in app.promotions if not getattr(promo, "is_regional_feeder", False)]
        all_transactions = list(app.finance.get("week_transactions", []))
        for promo in active_promos:
            all_transactions.extend(getattr(promo, "finance", {}).get("week_transactions", []) or [])
        repairs = [row for row in all_transactions if row.get("category") == "Reconciliation"]
        rescues = [row for row in all_transactions if row.get("category") == "Rescue"]
        summary = {
            "seed": seed,
            "weeks": 480,
            "final_date": (app.month, app.week),
            "initial_player_cash": initial_cash,
            "audit_scenario_starting_cash": audit_starting_cash,
            "final_player_cash": app.cash,
            "player_cash_change": app.cash - initial_cash,
            "initial_non_feeder_promotions": initial_promo_count,
            "final_non_feeder_promotions": len(active_promos),
            "child_final_cash": child.cash if child in app.promotions else None,
            "child_events": len([row for row in app.result_records if row.get("company") == child.name]),
            "player_transactions_retained": len(app.finance.get("week_transactions", [])),
            "promotion_transactions_retained": len(all_transactions),
            "reconciliation_repairs": len(repairs),
            "rescue_transactions": len(rescues),
            "negative_promotions": sum(1 for promo in active_promos if promo.cash < 0),
            "min_promotion_cash": min((promo.cash for promo in active_promos), default=0),
            "max_promotion_cash": max((promo.cash for promo in active_promos), default=0),
            "free_agents": len([fighter for fighter in app.free_agents if not fighter.retired]),
            "retired_fighters": len(app.retired_fighters),
            "yearly": yearly,
            "failures": failures[:20],
            "callback_errors": callback_errors[:5],
        }
        return summary
    finally:
        root.destroy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=90210)
    args = parser.parse_args()
    summary = run(args.seed)
    print("TEN-YEAR FINANCE AUDIT")
    for key in (
        "seed", "weeks", "final_date", "audit_scenario_starting_cash", "initial_player_cash", "final_player_cash", "player_cash_change",
        "initial_non_feeder_promotions", "final_non_feeder_promotions", "child_final_cash", "child_events",
        "player_transactions_retained", "promotion_transactions_retained", "reconciliation_repairs",
        "rescue_transactions", "negative_promotions", "min_promotion_cash", "max_promotion_cash",
        "free_agents", "retired_fighters",
    ):
        print(f"{key}: {summary[key]}")
    print("YEARLY SNAPSHOTS")
    for row in summary["yearly"]:
        print(row)
    if summary["callback_errors"]:
        raise AssertionError("Tk callback errors: " + "; ".join(summary["callback_errors"]))
    if summary["failures"]:
        raise AssertionError("Finance reconciliation failures: " + "; ".join(summary["failures"]))
    print("TEN-YEAR FINANCE AUDIT PASSED")


if __name__ == "__main__":
    main()
