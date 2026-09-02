"""Focused regressions for calendar simulation performance invariants."""

import random
import tkinter as tk
from tkinter import messagebox

from main import FightEmpireApp
import test_support


def require(condition, message):
    if not condition:
        raise AssertionError(test_support.contextual_message(message, subsystem=test_support.caller_name()))


def silence_dialogs():
    messagebox.showinfo = lambda *args, **kwargs: None
    messagebox.showwarning = lambda *args, **kwargs: None
    messagebox.showerror = lambda *args, **kwargs: None
    messagebox.askyesno = lambda *args, **kwargs: False
    messagebox.askyesnocancel = lambda *args, **kwargs: False


def test_card_day_is_cached_per_promotion(app):
    promo = next(item for item in app.promotions if not getattr(item, "is_regional_feeder", False))
    originals = {
        name: getattr(app, name)
        for name in (
            "ai_card_day", "ai_fatigue_limit", "update_ai_promotion_strategy",
            "ai_min_ready_fighters", "ai_show_chance", "fighter_available_for_date",
        )
    }
    calls = []
    try:
        app.ai_card_day = lambda _promo: calls.append(_promo.name) or 6
        app.ai_fatigue_limit = lambda _promo: 100
        app.update_ai_promotion_strategy = lambda _promo: {"current_mode": "Balanced"}
        app.ai_min_ready_fighters = lambda _promo: 1
        app.ai_show_chance = lambda _promo: 0.5
        app.fighter_available_for_date = lambda _fighter, **_kwargs: True
        promo.cash = max(promo.cash, 100_000_000)
        app.ai_should_run_show(promo)
        require(calls == [promo.name], "AI show readiness recalculated the promotion card day per fighter")

        feeder = next(item for item in app.promotions if getattr(item, "is_regional_feeder", False))
        calls.clear()
        original_recruit = app.regional_recruit_fighter
        app.fighter_available_for_date = lambda _fighter, **_kwargs: False
        app.regional_recruit_fighter = lambda *_args, **_kwargs: None
        try:
            app.simulate_regional_feeder_month(feeder)
        finally:
            app.regional_recruit_fighter = original_recruit
        require(calls == [feeder.name], "Regional readiness recalculated the circuit card day per fighter")
    finally:
        for name, value in originals.items():
            setattr(app, name, value)


def test_precomputed_head_to_head_is_reused(app):
    a, b = app.roster[:2]
    original = app.commentary_head_to_head
    calls = []
    app.commentary_head_to_head = lambda *_args: calls.append(True) or {
        "meetings": 0, "a_wins": 0, "b_wins": 0, "last_result": "",
    }
    try:
        supplied = {"meetings": 1, "a_wins": 1, "b_wins": 0, "last_result": "Month 1"}
        app.commentary_opening_context(a, b, {}, {"context": {}, "head_to_head": supplied})
        require(not calls, "Opening commentary repeated a head-to-head lookup already stored in fight state")
        app.commentary_opening_context(a, b, {}, {"context": {}})
        require(len(calls) == 1, "Opening commentary did not perform exactly one fallback history lookup")
    finally:
        app.commentary_head_to_head = original


def test_regional_recruitment_reuses_name_set(app):
    promo = next(
        item for item in app.promotions
        if getattr(item, "is_regional_feeder", False) and item.name != "Eurasian Fight Circuit"
    )
    original_roster = list(promo.roster)
    original_free_agents = app.free_agents
    original_names = app.active_fighter_names
    original_throughput = app.regional_market_throughput
    reserved = original_names()
    calls = []
    try:
        app.free_agents = []
        app.active_fighter_names = lambda: calls.append(True) or set(reserved)
        app.regional_market_throughput = lambda: {
            "deficit": 500, "target": 500, "available_free_agents": 0,
        }
        app.regional_recruit_fighter(promo, slots=3)
        recruits = promo.roster[len(original_roster):]
        require(len(calls) == 1, "Regional recruitment rebuilt the complete world-name set within one batch")
        require(len(recruits) == 3, "Regional recruitment performance fixture did not fill all requested slots")
        require(len({app.fighter_name_key(fighter.name) for fighter in recruits}) == 3,
                "Batched regional name reuse allowed a generated-name collision")
    finally:
        promo.roster = original_roster
        app.free_agents = original_free_agents
        app.active_fighter_names = original_names
        app.regional_market_throughput = original_throughput


def test_regional_cards_are_evenly_staggered(app):
    feeders = sorted(
        (promo for promo in app.promotions if getattr(promo, "is_regional_feeder", False)),
        key=lambda promo: promo.name,
    )
    original_week = app.week
    original_simulate = app.simulate_regional_feeder_month
    original_develop = app.age_and_develop_fighters
    completed = []
    weekly_counts = []
    total_review_counts = []
    monthly_review_labels = []
    try:
        app.simulate_regional_feeder_month = lambda promo: completed.append((app.week, promo.name))
        app.age_and_develop_fighters = lambda _roster, **_kwargs: None
        for week in range(1, 5):
            app.week = week
            steps = app.world_week_steps()
            regional_steps = [task for label, task in steps if label.endswith(" regional circuit")]
            monthly_review_labels.extend(
                label for label, _task in steps if label.endswith(" monthly review")
            )
            weekly_counts.append(len(regional_steps))
            total_review_counts.append(
                len(regional_steps) + sum(label.endswith(" monthly review") for label, _task in steps)
            )
            for task in regional_steps:
                task()
            require(not any(
                label == f"{promo.name} booking"
                for promo in feeders for label, _task in steps
            ), "A regional feeder remained in the generic weekly AI booking path")

        require(len(completed) == len(feeders), "Regional staggering changed the number of monthly circuit cards")
        require({name for _week, name in completed} == {promo.name for promo in feeders},
                "Regional staggering omitted or duplicated a circuit")
        require(max(weekly_counts) - min(weekly_counts) <= 1,
                "Regional circuit cards were not distributed evenly across the four weeks")
        require(max(total_review_counts) - min(total_review_counts) <= 1,
                "Promotion monthly reviews were not distributed evenly across the four weeks")
        require(len(monthly_review_labels) + len(completed) == len(app.promotions),
                "Weekly staggering scheduled a duplicate promotion monthly review")
        reviewed_promotions = {
            label.removesuffix(" monthly review") for label in monthly_review_labels
        } | {name for _week, name in completed}
        require(reviewed_promotions == {promo.name for promo in app.promotions},
                "Weekly staggering omitted or duplicated a promotion monthly review")

        monthly_steps = app.world_month_steps(False)
        feeder_labels = {f"{promo.name} monthly review" for promo in feeders}
        for label, task in monthly_steps:
            if label in feeder_labels:
                task()
        require(len(completed) == len(feeders), "Month-boundary reviews ran duplicate regional cards")
    finally:
        app.week = original_week
        app.simulate_regional_feeder_month = original_simulate
        app.age_and_develop_fighters = original_develop


def main():
    silence_dialogs()
    random.seed(448_901)
    root = tk.Tk()
    root.withdraw()
    try:
        app = FightEmpireApp(root, startup_progress=lambda *_args: None)
        app.rules["autosave_enabled"] = False
        test_card_day_is_cached_per_promotion(app)
        test_precomputed_head_to_head_is_reused(app)
        test_regional_recruitment_reuses_name_set(app)
        test_regional_cards_are_evenly_staggered(app)
        print("SIMULATION PERFORMANCE REGRESSION PASSED")
    finally:
        root.destroy()


if __name__ == "__main__":
    test_support.run_suite("simulation_performance_regression_test.py", main)
