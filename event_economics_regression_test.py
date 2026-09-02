"""Regressions for per-event economics and bookable grudge matches.

Ticket price, production tier and marketing spend are per-card decisions, and a
feud is worth real money at the gate.  These checks pin the tradeoffs so a later
balance change cannot silently turn a lever back into free money.
"""

import os
import sys
import tkinter as tk
from dataclasses import replace

from constants import (
    DEFAULT_EVENT_PRODUCTION_TIER,
    EVENT_PRODUCTION_TIER_ORDER,
    EVENT_TICKET_PRICE_MAX,
    EVENT_TICKET_PRICE_MIN,
)
from main import FightEmpireApp
from models import Fighter
from persistence import FIGHTER_SAVE_FIELDS, load_model_row, serialize_fighter_model


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def same_division_pair(app):
    groups = {}
    for fighter in app.roster:
        groups.setdefault((fighter.gender, fighter.weight), []).append(fighter)
    for members in groups.values():
        if len(members) >= 2:
            return members[0], members[1]
    raise AssertionError("The seeded roster has no same-division pair to match.")


def finance_for(app, fight, hype=320, **overrides):
    event = {
        "name": "Economics Test", "venue": "Regional Arena", "region": "USA",
        "city": "Las Vegas", "month": 1, "week": 1, "fights": [fight],
        "broadcaster": "No Coverage",
    }
    event.update(overrides)
    return app.calculate_event_finance(
        hype, 40_000, event, [], excitement_score=55, build_score=50, regional_pull=1.0,
    )


def main():
    root = tk.Tk()
    root.withdraw()
    callback_errors = []
    root.report_callback_exception = lambda exc, value, tb: callback_errors.append(value)
    try:
        app = FightEmpireApp(root, startup_progress=lambda _value, _text: None)
        a, b = same_division_pair(app)
        fight = {"fighters": [a.name, b.name], "main": True, "title": False, "tier": "Main Card"}

        # --- price elasticity -------------------------------------------------
        fair = app.event_fair_ticket_price(320, 1.0, "Regional Arena")
        require(fair >= EVENT_TICKET_PRICE_MIN, "Fair ticket price fell below the supported minimum.")
        cheap = finance_for(app, fight, ticket_price=max(EVENT_TICKET_PRICE_MIN, round(fair * 0.5)))
        priced = finance_for(app, fight, ticket_price=fair)
        gouged = finance_for(app, fight, ticket_price=round(fair * 3))
        require(cheap["attendance"] > gouged["attendance"],
                "Ticket price does not affect turnout; raising it is still free money.")
        require(priced["ticket_revenue"] > gouged["ticket_revenue"],
                "Tripling the ticket price must not out-earn a market-rate card.")
        require(app.ticket_price_demand_factor(fair, fair) == 1.0,
                "Charging the market rate should be demand-neutral.")
        # Demand must decay to zero. A floor made revenue climb forever past the
        # point it bound, so the optimal play was always to charge the maximum.
        require(app.ticket_price_demand_factor(EVENT_TICKET_PRICE_MAX, 20) == 0.0,
                "Extreme overpricing must empty the room, not rest on a demand floor.")
        peak_price, peak_revenue = 0, -1
        for candidate in range(EVENT_TICKET_PRICE_MIN, EVENT_TICKET_PRICE_MAX + 1, 5):
            revenue = candidate * app.ticket_price_demand_factor(candidate, fair)
            if revenue > peak_revenue:
                peak_price, peak_revenue = candidate, revenue
        require(peak_price < EVENT_TICKET_PRICE_MAX,
                "Gate revenue must peak below the price cap, not at it.")
        require(1.15 <= peak_price / fair <= 1.5,
                f"The gate optimum should sit just above the market rate, not at {peak_price / fair:.2f}x.")

        # --- production tier --------------------------------------------------
        tiers = {name: finance_for(app, fight, ticket_price=fair, production_tier=name)
                 for name in EVENT_PRODUCTION_TIER_ORDER}
        require(tiers["Spectacle"]["production"] > tiers["Lean"]["production"],
                "A richer production tier must cost more to stage.")
        require(tiers["Spectacle"]["attendance"] > tiers["Lean"]["attendance"],
                "A richer production tier must improve the room.")
        require(tiers["Lean"]["profit"] > tiers["Spectacle"]["profit"],
                "Spectacle production must not be free profit on a small untelevised card.")
        # Richer production is bought against broadcast reach. Without that link
        # every promotion past the opening weeks simply always picks Spectacle.
        app.ensure_broadcast_contract_defaults()
        app.broadcasters.append({
            "name": "Audit Wide Network", "reach": 88, "fee": 160_000, "type": "Premium TV",
            "min_popularity": 0, "term_months": 12, "contract_months": 12,
            "signing_fee": 0, "signed_month": 1, "renewal_notified": False,
        })
        app.company_pop = 70
        covered = {
            name: finance_for(app, fight, hype=650, venue="National Sports Hall",
                              broadcaster="Audit Wide Network", production_tier=name,
                              ticket_price=app.event_fair_ticket_price(650, 1.0, "National Sports Hall"))
            for name in EVENT_PRODUCTION_TIER_ORDER
        }
        require(max(covered, key=lambda name: covered[name]["profit"]) == "Spectacle",
                "Behind a wide-reach broadcast deal, the richest production must be the right call.")

        # --- marketing --------------------------------------------------------
        unmarketed = finance_for(app, fight, ticket_price=fair, marketing_budget=0)
        marketed = finance_for(app, fight, ticket_price=fair, marketing_budget=60_000)
        require(marketed["attendance"] > unmarketed["attendance"],
                "Marketing spend must buy turnout.")
        require(marketed["marketing"] > unmarketed["marketing"],
                "Marketing spend must be charged as an event cost.")

        # --- career-stage balance --------------------------------------------
        # Opening authored stars use founder-era contracts.  Generated depth
        # was already affordable and must not receive another discount.
        curated = sorted((fighter.purse for fighter in app.roster if not fighter.generated), reverse=True)
        require(curated and sum(curated[:10]) <= 650_000,
                "A credible opening star card must not carry near-$1M in base purses.")
        generated = [fighter.purse for fighter in app.roster if fighter.generated]
        require(generated and max(generated) >= 20_000,
                "Opening-contract relief must not halve already-affordable generated depth.")

        app.company_pop = 38
        early_office = app.player_monthly_office_cost()
        app.company_pop = 68
        mid_office = app.player_monthly_office_cost()
        app.company_pop = 88
        late_office = app.player_monthly_office_cost()
        require(early_office == app.finance["monthly_office"],
                "A regional company should retain the documented base office cost.")
        require(early_office < mid_office < late_office,
                "Infrastructure overhead must grow through the mid and late game.")

        app.company_pop = 70
        app.company_stability = 68
        app.result_records = []
        first_show = finance_for(app, fight, hype=600, venue="National Sports Hall", ticket_price=65)
        app.result_records.append({
            "company": app.player_company_name, "date": "Month 1 Week 1", "event": "First monthly show",
        })
        second_show = finance_for(app, fight, hype=600, venue="National Sports Hall", ticket_price=65)
        require(first_show["cadence_factor"] == 1.0 and second_show["cadence_factor"] < 0.8,
                "A second event in one month must expose its audience-cannibalization factor.")
        require(second_show["total_revenue"] < first_show["total_revenue"]
                and second_show["fighter_pay"] == first_show["fighter_pay"],
                "Same-month cards must lose reach while honoring every signed purse.")
        app.result_records = []
        app.scheduled_events = [{
            "name": "Earlier card", "month": 1, "week": 1, "day": 5, "fights": [],
        }]
        forecast_event = {"name": "Later card", "month": 1, "week": 3, "day": 5}
        require(app.player_events_in_month(1, forecast_event) == 1,
                "A future later card must forecast same-month cannibalization before settlement.")
        app.result_records = []
        app.scheduled_events = []
        app.company_pop = 38
        app.company_stability = 52

        # --- legacy and AI cards keep company defaults ------------------------
        app.ensure_finance_defaults()
        legacy = app.event_economics({"name": "Legacy card"})
        require(legacy["ticket_price"] == app.finance["ticket_price"],
                "A card saved before per-event pricing must fall back to the company price.")
        require(legacy["production_tier"] == DEFAULT_EVENT_PRODUCTION_TIER,
                "A card without a production tier must use the default tier.")
        clamped = app.event_economics({"ticket_price": 10_000, "marketing_budget": -50})
        require(clamped["ticket_price"] == EVENT_TICKET_PRICE_MAX, "Ticket price must clamp to its maximum.")
        require(clamped["marketing_budget"] == 0, "Marketing spend must never go negative.")
        require(app.event_economics({"production_tier": "Nonsense"})["production_tier"] == DEFAULT_EVENT_PRODUCTION_TIER,
                "An unknown production tier must fall back rather than crash.")

        # --- grudge matches ---------------------------------------------------
        # Seeded fighters can already carry world history.  This case owns its
        # initial state so an unrelated high-heat seed cannot make it flaky.
        for fighter in (a, b):
            fighter.rival = ""
            fighter.rival_fighter_id = ""
            fighter.rivalry_heat = 0
            fighter.rivalry_origin = ""
            fighter.rivalry_rematch_due = False
        require(not app.grudge_match_state(a, b)["grudge"], "Unrelated fighters must not read as a grudge match.")
        base_hype = app.fight_hype(a, b, fight)
        base_gate = app.event_grudge_gate_bonus({"fights": [fight]})
        require(base_gate == 0, "A card with no feud must earn no grudge gate bonus.")

        app.establish_rivalry(a, b, "Media callout", heat=45)
        state = app.grudge_match_state(a, b)
        require(state["grudge"] and state["heat"] == 45, "A media callout must create a bookable grudge match.")
        require(a.rival_fighter_id == b.fighter_id and b.rival_fighter_id == a.fighter_id,
                "New rivalries must bind both display names to stable fighter IDs.")

        saved_rival = serialize_fighter_model(a)
        require(saved_rival["rival_fighter_id"] == b.fighter_id,
                "The stable rivalry target must be included in fighter saves.")
        loaded_rival = load_model_row(saved_rival, Fighter, FIGHTER_SAVE_FIELDS, "rivalry round trip")
        require(loaded_rival.rival_fighter_id == b.fighter_id,
                "The stable rivalry target must survive a fighter save round trip.")
        legacy_rival = dict(saved_rival)
        legacy_rival.pop("rival_fighter_id")
        loaded_legacy = load_model_row(legacy_rival, Fighter, FIGHTER_SAVE_FIELDS, "legacy rivalry row")
        require(loaded_legacy.rival_fighter_id == "",
                "A legacy fighter row without a rivalry ID must retain a safe default.")

        duplicate = replace(b, fighter_id=f"{b.fighter_id}-DUPLICATE", rival="", rival_fighter_id="")
        app.roster.append(duplicate)
        require(not app.grudge_match_state(a, duplicate)["grudge"],
                "A same-name fighter must not inherit another fighter's grudge bonus.")
        a.rival_fighter_id = ""
        b.rival = ""
        b.rival_fighter_id = ""
        require(not app.grudge_match_state(a, b)["grudge"],
                "An ambiguous legacy rival name must not attach to an arbitrary fighter.")
        a.rival_fighter_id = b.fighter_id
        b.rival = a.name
        b.rival_fighter_id = a.fighter_id
        app.roster.remove(duplicate)
        require(app.fight_hype(a, b, fight) > base_hype, "A live feud must lift projected hype.")
        require(app.event_grudge_gate_bonus({"fights": [fight]}) > 0, "A live feud must lift the gate.")

        # heat accumulates so a feud can be built over several weeks
        before = app.rivalry_heat_between(a, b)
        app.build_rivalry_heat(a, b, 15, note="Escalated in the media.")
        after = app.rivalry_heat_between(a, b)
        require(after == before + 15, "Media promotion must accumulate rivalry heat.")
        require(app.fight_hype(a, b, fight) > base_hype, "Accumulated heat must keep raising hype.")

        hot_gate = app.event_grudge_gate_bonus({"fights": [fight]})
        a.rivalry_heat = b.rivalry_heat = 100
        require(app.event_grudge_gate_bonus({"fights": [fight]}) > hot_gate,
                "Hotter feuds must be worth more at the gate.")

        prelim = {"fighters": [a.name, b.name], "main": False, "title": False, "tier": "Prelims"}
        require(app.event_grudge_gate_bonus({"fights": [prelim]}) < app.event_grudge_gate_bonus({"fights": [fight]}),
                "A grudge buried on the prelims must be worth less than a headline feud.")

        # a feud must be worth real money on an otherwise identical card
        hot = finance_for(app, fight, ticket_price=fair)
        a.rival = b.rival = ""
        a.rival_fighter_id = b.rival_fighter_id = ""
        a.rivalry_heat = b.rivalry_heat = 0
        cold = finance_for(app, fight, ticket_price=fair)
        require(hot["ticket_revenue"] > cold["ticket_revenue"],
                "Settling a feud must out-earn the same card without one.")

        # building heat on fighters with no feud must be a no-op, not a crash
        require(app.build_rivalry_heat(a, b, 20) == 0, "Heat cannot be built where no feud exists.")

        # A stale or ambiguous rivalry must be rejected before a paid press
        # action changes cash, weekly capacity, or fighter state.
        app.ensure_media_system()
        app.finance["media_actions_used"] = 0
        a.rival = "Missing Rival"
        a.rival_fighter_id = "missing-fighter-id"
        before_press = (app.cash, app.finance["media_actions_used"], a.media_heat, a.popularity)
        ok, _message, _row = app.resolve_media_campaign("Press Conference", a)
        require(not ok, "A press conference must reject a stale rivalry reference.")
        require((app.cash, app.finance["media_actions_used"], a.media_heat, a.popularity) == before_press,
                "A rejected press conference must not charge cash, consume capacity, or mutate the fighter.")

        a.rival = b.name
        a.rival_fighter_id = ""
        app.roster.append(duplicate)
        before_tour = (app.cash, app.finance["media_actions_used"], a.media_heat, a.popularity)
        ok, _message, _row = app.resolve_media_campaign("Press Tour", a)
        require(not ok, "A press tour must reject an ambiguous legacy rivalry name.")
        require((app.cash, app.finance["media_actions_used"], a.media_heat, a.popularity) == before_tour,
                "A rejected press tour must not charge cash, consume capacity, or mutate the fighter.")
        app.roster.remove(duplicate)
        a.rival = ""
        a.rival_fighter_id = ""

        # An untouched card must price itself at the market rate. The old
        # company-wide default never scaled, so ignoring this lever grew steadily
        # more expensive the bigger the promotion became.
        app.ensure_screen_built("booking")
        app.booked.append({"fighters": [a.name, b.name], "main": True, "title": False, "tier": "Main Card"})
        app._event_price_user_set = False
        app.refresh_event_economics_forecast()
        require(app.event_ticket_price.get() == app.suggested_event_economics()["ticket_price"],
                "An untouched card must follow the market price.")
        app.event_ticket_price.set(199)
        app.note_manual_event_price()
        app.refresh_event_economics_forecast()
        require(app.event_ticket_price.get() == 199,
                "A manually priced card must not be overwritten by auto-pricing.")

        require(not callback_errors, f"Tk callback errors occurred: {callback_errors}")
        print("EVENT ECONOMICS AND GRUDGE MATCH REGRESSION TEST PASSED")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
