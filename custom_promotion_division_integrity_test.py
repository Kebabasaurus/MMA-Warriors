"""Regression for AI custom promotions preserving closed divisions."""

import random
import tkinter as tk

from main import FightEmpireApp


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    random.seed(4401)
    root = tk.Tk()
    root.withdraw()
    callback_errors = []
    root.report_callback_exception = lambda exc, value, tb: callback_errors.append(value)
    try:
        app = FightEmpireApp(root)
        app.pending_custom_promotion_config = {
            "name": "Audit Four Division League",
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
        app.enter_spectator_mode()

        promotion = next(
            item for item in app.promotions
            if item.name == "Audit Four Division League"
        )
        allowed = {
            app.belt_key(gender, weight)
            for gender in ("Male", "Female")
            for weight in ("Featherweight", "Lightweight")
        }

        # Keep the calendar and child-independent AI paths real while avoiding
        # unrelated promotions making this focused annual-movement check slow.
        app.promotions = [promotion]
        for _ in range(48):
            app.advance_month()

        violations = [
            f"{fighter.gender}/{fighter.weight}/{fighter.name}"
            for fighter in promotion.roster
            if not fighter.retired
            and app.belt_key(fighter.gender, fighter.weight) not in allowed
        ]
        require((app.month, app.week) == (13, 1),
                "The progression probe did not cross the annual movement boundary")
        require(not violations,
                "AI custom promotion roster entered closed divisions: " + ", ".join(violations))
        require(not callback_errors,
                f"UI callback error during division-integrity test: {callback_errors[0] if callback_errors else ''}")
    finally:
        root.destroy()

    print("CUSTOM PROMOTION DIVISION INTEGRITY TEST PASSED")
    print("No active AI-roster fighter entered a closed division after 48 calendar weeks.")


if __name__ == "__main__":
    main()
