"""Focused regressions for child-promotion ownership and manager interactions."""

import random
import tkinter as tk

from main import FightEmpireApp


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    random.seed(90210)
    root = tk.Tk()
    root.withdraw()
    try:
        app = FightEmpireApp(root)
        app.new_game()
        app.cash = 3_000_000
        launch_ok, child = app.launch_ai_child_promotion(1_000_000, "Balanced", 25, "Interaction Child")
        require(launch_ok and child.roster, "child launch did not create an opening roster")

        # Ordinary company takeover must not detach a child from its parent.
        old_name = app.player_company_name
        require(app.take_control_of_company(child.name) is False, "ordinary takeover accepted a child promotion")
        require(app.player_company_name == old_name and child in app.promotions, "blocked takeover mutated ownership")

        # Empty markets must not consume capital or leave an unusable child behind.
        original_free_agents = app.free_agents
        original_cash = app.cash
        app.free_agents = []
        empty_ok, _empty_note = app.launch_ai_child_promotion(1_000_000, "Balanced", 0, "Empty Interaction Child")
        require(not empty_ok and app.cash == original_cash, "empty launch did not roll back parent capital")
        require(not any(item.name == "Empty Interaction Child" for item in app.promotions), "empty launch left a child promotion behind")
        app.free_agents = original_free_agents

        # A champion cannot carry an occupied parent belt into a loan.
        champion = next(fighter for fighter in app.roster if not fighter.retirement_pending and not fighter.injured)
        champion.champion = True
        belt_key = app.belt_key(champion.gender, champion.weight)
        app.belts[belt_key] = champion.name
        loan_ok, _loan_note = app.loan_fighter_to_child_promotion(child.name, champion.fighter_id)
        require(loan_ok, "champion could not be loaned")
        require(not champion.champion and app.belts.get(belt_key) != champion.name, "parent belt remained occupied after champion loan")
        recall_ok, _recall_note = app.recall_fighter_from_child_promotion(child.name, champion.fighter_id)
        require(recall_ok, "champion loan could not be recalled")

        # Closed parent divisions reject AI-signed child transfers.
        signed = next(fighter for fighter in child.roster if not app.child_promotion_loaned(child, fighter) and not fighter.retired)
        closed_key = app.belt_key(signed.gender, signed.weight)
        app.closed_divisions.add(closed_key)
        closed_ok, _closed_note = app.take_fighter_from_child_promotion(child.name, signed.fighter_id)
        require(not closed_ok and signed in child.roster, "transfer entered a closed parent division")
        app.closed_divisions.discard(closed_key)

        # Paid transfers write a parent expense and a child receipt.
        app.cash += 2_000_000
        before = sum(int(row.get("costs", 0) or 0) for row in app.finance.get("week_transactions", []))
        fee = app.child_promotion_transfer_fee(signed)
        transfer_ok, _transfer_note = app.take_fighter_from_child_promotion(child.name, signed.fighter_id)
        require(transfer_ok, "open child transfer failed")
        after = sum(int(row.get("costs", 0) or 0) for row in app.finance.get("week_transactions", []))
        require(after - before == fee, "parent transfer fee was not recorded in the parent ledger")
        require(int((child.finance or {}).get("transfer_fees_received", 0) or 0) == fee, "child transfer receipt was not recorded")

        # Retired and orphaned loan markers are repaired and cannot be acted on.
        orphan = next(fighter for fighter in app.roster if fighter is not champion and not fighter.retired)
        orphan.loaned_from_company = app.player_company_name
        orphan.loaned_to_promotion = "Missing Child"
        app.repair_child_promotion_state()
        require(not orphan.loaned_to_promotion and not orphan.loaned_from_company, "orphaned loan marker survived repair")
        retired = next(fighter for fighter in child.roster if not app.child_promotion_loaned(child, fighter))
        retired.retired = True
        retired.loaned_to_promotion = child.name
        retired.loaned_from_company = app.player_company_name
        app.repair_child_promotion_state()
        require(not retired.loaned_to_promotion and not retired.loaned_from_company, "retired loan marker survived repair")

        print("Child promotion interaction regressions passed")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
