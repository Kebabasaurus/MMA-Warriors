"""Regression coverage for bounded parent/child development-loan returns."""

import random
import tkinter as tk

from main import FightEmpireApp


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    random.seed(73104)
    root = tk.Tk()
    root.withdraw()
    try:
        app = FightEmpireApp(root)
        app.new_game()
        app.cash = 3_000_000
        ok, child = app.launch_ai_child_promotion(1_000_000, "Balanced", 20, "Return Boundary Child")
        require(ok and child.roster, "child launch failed")
        app.promotions = [child]

        fighter = next(item for item in app.roster if not item.injured and not item.retirement_pending)
        target_month, target_week = app.month, min(4, app.week + 1)
        if (target_month, target_week) == (app.month, app.week):
            target_month, target_week = app.month + 1, 1
        loan_ok, _note = app.loan_fighter_to_child_promotion(
            child.name, fighter.fighter_id,
            return_month=target_month, return_week=target_week,
        )
        require(loan_ok, "bounded development loan could not be committed")
        require((fighter.loan_return_month, fighter.loan_return_week) == (target_month, target_week),
                "agreed return boundary was not stored on the loan")
        saved = app.serialize_world()
        app.apply_world_data(saved)
        child = app.child_promotion_by_name("Return Boundary Child")
        fighter = next(item for item in child.roster if item.fighter_id == fighter.fighter_id)
        require(app.child_loan_return_label(fighter) == app.format_game_date(target_month, target_week),
                "agreed return boundary did not survive save/load")

        # The return is evaluated at a weekly boundary, not immediately when
        # the term is signed or while the calendar is still before the date.
        while app.calendar_week_index() < app.calendar_week_index(target_month, target_week):
            app.advance_month()
        require(fighter in child.roster and fighter.loaned_to_promotion == child.name,
                "loan returned before the agreed boundary")
        rng_before = random.getstate()
        app.process_child_promotion_loan_returns()
        require(random.getstate() == rng_before, "loan return processing consumed simulation RNG")
        require(fighter in app.roster and not fighter.loaned_to_promotion,
                "bounded loan did not return at the agreed safe boundary")
        require(fighter.loan_return_month == 0 and fighter.loan_return_week == 0,
                "completed loan left a stale return date")
        require(any("Development loan term completed" in str(row.get("reason", ""))
                    for row in app.foundation_membership_events(fighter_id=fighter.fighter_id)
                    if isinstance(row, dict)),
                "completed loan did not retain an attributed membership reason")
        require(any(thread.get("phase") == "loan_completed" for thread in app.story_threads),
                "completed loan did not advance its feeder story")
        app.process_child_promotion_loan_returns()
        require(fighter in app.roster and not fighter.loaned_to_promotion,
                "re-running a completed loan return was not idempotent")

        # A committed child card after the agreed date delays the return until
        # the first boundary after that card, with an explicit player-facing
        # notice and no roster mutation during the delay.
        second = next(item for item in app.roster if not item.injured and not item.retirement_pending)
        delayed_month, delayed_week = app.month, min(4, app.week + 1)
        if (delayed_month, delayed_week) == (app.month, app.week):
            delayed_month, delayed_week = app.month + 1, 1
        loan_ok, _note = app.loan_fighter_to_child_promotion(
            child.name, second.fighter_id,
            return_month=delayed_month, return_week=delayed_week,
        )
        require(loan_ok, "second bounded loan could not be committed")
        child.scheduled_events = [{
            "event_id": "return-boundary-card", "month": delayed_month,
            "week": delayed_week, "fights": [{"fighters": [second.name, "Committed Opponent"]}],
        }]
        while app.calendar_week_index() < app.calendar_week_index(delayed_month, delayed_week):
            app.advance_month()
        app.process_child_promotion_loan_returns()
        require(second in child.roster and second.loaned_to_promotion == child.name,
                "committed child bout did not hold a due loan")
        delay_rows = [row for row in app.inbox if isinstance(row, dict) and "holds the return until" in str(row.get("body", ""))]
        require(delay_rows,
                "loan return delay was not surfaced to the player")
        app.process_child_promotion_loan_returns()
        require(len([row for row in app.inbox if isinstance(row, dict) and "holds the return until" in str(row.get("body", ""))]) == len(delay_rows),
                "rechecking a delayed loan duplicated its notice")
        app.advance_month()
        app.advance_month()
        require(second in app.roster and not second.loaned_to_promotion,
                "delayed loan did not return after its committed bout boundary")
    finally:
        root.destroy()
    print("CHILD PROMOTION LOAN RETURN REGRESSION TEST PASSED")


if __name__ == "__main__":
    main()
