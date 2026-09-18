"""Focused regressions for child-promotion ownership and manager interactions."""

from copy import deepcopy
import random
import tkinter as tk
from unittest.mock import patch

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

        # Future child cards are explicit planning records.  They appear in the
        # shared schedule without reserving a fighter or running matchmaking
        # until the committed week, and duplicate monthly plans are rejected.
        schedule_ok, schedule_note, scheduled = app.schedule_child_promotion_event(
            child.promotion_id, app.month + 2, 2, "Interaction Child Showcase",
        )
        require(schedule_ok and scheduled and scheduled["status"] == "Scheduled",
                f"future child card could not be committed: {schedule_note}")
        require(any(row.get("event_id") == scheduled["event_id"] for row in child.scheduled_events),
                "future child card was not retained on the child promotion")
        saved_boundary = (app.month, app.week)
        app.month, app.week = app.month + 2, 2
        require(app.ai_should_run_show(child), "a due child card was still gated by the probabilistic show roll")
        app.month, app.week = saved_boundary
        duplicate_ok, _duplicate_note, _duplicate = app.schedule_child_promotion_event(
            child.promotion_id, app.month + 2, 3, "Duplicate month",
        )
        require(not duplicate_ok, "child promotion accepted two future cards in one month")
        cancel_ok, _cancel_note = app.cancel_child_promotion_event(child.promotion_id, scheduled["event_id"])
        require(cancel_ok and not child.scheduled_events, "future child card could not be cancelled by stable ID")

        # Ordinary company takeover must not detach a child from its parent.
        old_name = app.player_company_name
        with patch("persistence.messagebox.showinfo"), patch("persistence.messagebox.showwarning"):
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
        feeder_key = champion.feeder_story_key
        feeder_thread = app.story_thread(feeder_key)
        require(feeder_thread and feeder_thread["type"] == "Feeder Pathway"
                and feeder_thread["phase"] == "development_loan"
                and feeder_thread["child_company"] == child.name,
                "a child loan did not begin a durable feeder pathway")
        recall_ok, _recall_note = app.recall_fighter_from_child_promotion(child.name, champion.fighter_id)
        require(recall_ok, "champion loan could not be recalled")
        require(champion.feeder_story_key == feeder_key
                and app.story_thread(feeder_key)["phase"] == "parent_recalled",
                "loan recall did not advance the same feeder pathway")

        # Closed parent divisions reject AI-signed child transfers.
        signed = next(fighter for fighter in child.roster if not app.child_promotion_loaned(child, fighter) and not fighter.retired)
        closed_key = app.belt_key(signed.gender, signed.weight)
        app.closed_divisions.add(closed_key)
        closed_ok, _closed_note = app.take_fighter_from_child_promotion(child.name, signed.fighter_id)
        require(not closed_ok and signed in child.roster, "transfer entered a closed parent division")
        require(not signed.feeder_story_key,
                "a rejected child transfer created a feeder story")
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
        transferred_story = app.story_thread(signed.feeder_story_key)
        require(transferred_story and transferred_story["phase"] == "parent_transfer"
                and transferred_story["pathway_kind"] == "transfer"
                and transferred_story["parent_company"] == app.player_company_name,
                "a paid child transfer did not begin its parent-career pathway")

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

        # A late story failure must roll the entire paid move back: cash,
        # ledgers, rosters, fighter contract state, Chronicle and story indexes.
        rollback_child = app.child_promotion_by_name(child.name)
        rollback_fighter = next(
            fighter for fighter in rollback_child.roster
            if not app.child_promotion_loaned(rollback_child, fighter)
            and not fighter.retired and not fighter.retirement_pending
        )
        app.closed_divisions.discard(app.belt_key(rollback_fighter.gender, rollback_fighter.weight))
        app.cash = max(app.cash, app.child_promotion_transfer_fee(rollback_fighter) + 100_000)
        rollback_id = rollback_fighter.fighter_id
        cash_before = app.cash
        child_cash_before = rollback_child.cash
        parent_rows_before = deepcopy(app.finance.get("week_transactions", []))
        child_finance_before = deepcopy(rollback_child.finance)
        stories_before = deepcopy(app.story_threads)
        chronicle_before = deepcopy(app.world_chronicle)
        rng_before = random.getstate()

        def fail_feeder_hook(*_args, **_kwargs):
            raise RuntimeError("forced feeder narrative failure")

        app.record_feeder_pathway_transition = fail_feeder_hook
        try:
            try:
                app.take_fighter_from_child_promotion(child.name, rollback_id)
            except RuntimeError as exc:
                require("forced feeder narrative failure" in str(exc),
                        "paid transfer surfaced the wrong forced failure")
            else:
                raise AssertionError("paid transfer swallowed the forced narrative failure")
        finally:
            del app.__dict__["record_feeder_pathway_transition"]
        restored_child = app.child_promotion_by_name(child.name)
        restored_fighter = next(
            (fighter for fighter in restored_child.roster if fighter.fighter_id == rollback_id), None
        )
        require(restored_fighter is not None
                and all(fighter.fighter_id != rollback_id for fighter in app.roster),
                "failed paid transfer did not restore child and parent rosters")
        require(app.cash == cash_before and restored_child.cash == child_cash_before,
                "failed paid transfer did not restore parent and child cash")
        require(app.finance.get("week_transactions", []) == parent_rows_before
                and restored_child.finance == child_finance_before,
                "failed paid transfer left finance-ledger mutations behind")
        require(app.story_threads == stories_before and app.world_chronicle == chronicle_before,
                "failed paid transfer left Chronicle or feeder-story state behind")
        require(random.getstate() == rng_before,
                "failed paid transfer did not restore simulation RNG")

        print("Child promotion interaction regressions passed")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
