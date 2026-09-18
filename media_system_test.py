"""Focused regression tests for the persistent media market.

This intentionally uses the real ``FightEmpireApp`` with a withdrawn Tk root.
It exercises player and AI media state through the same methods used by the UI
and event simulation, then verifies a full save-data round trip.
"""

from copy import deepcopy
import random
import tkinter as tk
from tkinter import messagebox

from constants import REGIONS
from main import FightEmpireApp


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def silence_messageboxes():
    messagebox.showinfo = lambda *args, **kwargs: None
    messagebox.showwarning = lambda *args, **kwargs: None
    messagebox.showerror = lambda *args, **kwargs: None
    messagebox.askyesno = lambda *args, **kwargs: False
    messagebox.askyesnocancel = lambda *args, **kwargs: False


def supported_region(app, contract, fallback):
    outlet = app._outlet_for(contract.get("outlet_id"))
    markets = list((outlet or {}).get("markets", []))
    return next((region for region in markets if region in REGIONS), fallback)


def event_package(name):
    return {
        "event_name": name,
        "fight_count": 8,
        "average_excitement": 92,
        "average_build": 90,
        "finance": {"build_score": 90, "excitement_score": 92},
    }


def run_player_media_checks(app):
    app.ensure_media_system()
    check(len(app.media_companies) >= 8, "The default media market must contain at least eight outlets")
    outlet_ids = [outlet.get("id") for outlet in app.media_companies]
    check(len(outlet_ids) == len(set(outlet_ids)), "Media outlet IDs must be unique")

    random.seed(1101)
    offers = app.generate_media_offers(force=True, count=4)
    check(len(offers) >= 2, "A new player company must receive default media offers")
    check(all(offer.get("events_remaining", 0) > 0 for offer in offers), "Every media offer needs a positive event commitment")

    assessed = app.media_offer_assessment(offers[0])
    check(0 <= assessed["score"] <= 100 and assessed["gross"] > 0,
          "Media offer assessment did not expose a bounded value and gross package")
    counter_offer = offers[-1]
    old_reach = counter_offer["reach"]
    accepted_counter, _message = app.counter_player_media_offer(counter_offer["id"], "Wider Reach", roll=1)
    check(accepted_counter and counter_offer["reach"] == min(99, old_reach + 5),
          "Successful wider-reach negotiation did not improve the selected offer")
    check(not app.counter_player_media_offer(counter_offer["id"], "Wider Reach", roll=1)[0],
          "A media outlet answered more than one counteroffer")

    market_offer = next(
        (
            offer for offer in offers
            if app.player_region in (app._outlet_for(offer["outlet_id"]) or {}).get("markets", [])
            or "Worldwide" in (app._outlet_for(offer["outlet_id"]) or {}).get("markets", [])
        ),
        offers[0],
    )
    accepted, message = app.accept_player_media_offer(market_offer["id"])
    check(accepted, f"Player media offer was not accepted: {message}")
    contract = app.active_media_contract()
    check(contract is not None, "Accepted media offer did not create an active contract")
    check(app.finance["media_rights"] is contract, "Legacy media_rights alias is not synced to the active contract")
    check(contract["fee"] == contract["guarantee_per_event"], "Legacy fee and guarantee aliases disagree")

    fighter_a, fighter_b = app.roster[:2]
    event = {
        "name": "Media Regression Night",
        "region": supported_region(app, contract, app.player_region),
        "broadcaster": "Regional Webcast",
        "fights": [{"fighters": [fighter_a.name, fighter_b.name]}],
    }
    no_coverage = dict(event)
    no_coverage["broadcaster"] = "No Coverage"
    eligible, reason = app.media_contract_eligibility(contract, no_coverage)
    check(not eligible and "No event production" in reason, "No Coverage event incorrectly qualified for a rights contract")
    no_coverage_outcome = app.calculate_event_media_outcome(no_coverage, event_package(event["name"]))
    check(not no_coverage_outcome["eligible"], "No Coverage event produced contracted rights income")

    events_before = contract["events_remaining"]
    audience_before = len(app.finance["media_audience_history"])
    random.seed(1102)
    outcome = app.calculate_event_media_outcome(event, event_package(event["name"]), contract=contract)
    check(outcome["eligible"], f"Covered event was rejected: {outcome['reason']}")
    check(5 <= outcome["rating"] <= 99, "Covered event produced an invalid audience rating")
    check(outcome["viewers"] > 0, "Covered event did not produce a viewer estimate")
    check(outcome["rights_income"] >= contract["fee"], "Covered event did not include its contracted guarantee")
    row = app.record_media_event_outcome(event, outcome, featured_fighters=[fighter_a, fighter_b])
    check(contract["events_remaining"] == events_before - 1, "Covered event did not decrement the contract event commitment")
    check(len(app.finance["media_audience_history"]) == audience_before + 1, "Covered event was not stored in audience history")
    check(row["event"] == event["name"] and row["rating"] == outcome["rating"], "Audience-history row does not match the event outcome")

    capacity = app.media_action_capacity()
    check(capacity >= 2, "Player media capacity must allow at least two weekly actions")
    marketing_lead = next((member for member in app.staff if member.get("role") == "Marketing"), None)
    if marketing_lead:
        original_specialty = marketing_lead.get("specialty")
        marketing_lead["specialty"] = "Regional campaigns"
        ordinary_spec = app._media_action_spec("Press Tour", fighter_a)
        marketing_lead["specialty"] = "Campaign Coordinator"
        coordinated_spec = app._media_action_spec("Press Tour", fighter_a)
        check(coordinated_spec["staff_cost_saving"] > 0 and coordinated_spec["cost"] < ordinary_spec["cost"],
              "Campaign Coordinator did not reduce the quoted paid-media cost")
        check(coordinated_spec["base_cost"] == ordinary_spec["cost"],
              "Campaign Coordinator changed the underlying campaign price basis")
        foreign_spec = app._media_action_spec("Press Tour", fighter_a, promotion=object())
        check(foreign_spec["staff_cost_saving"] == 0 and foreign_spec["cost"] == foreign_spec["base_cost"],
              "Player Campaign Coordinator leaked into another promotion's media quote")
        marketing_lead["specialty"] = original_specialty
    history_before = len(app.finance["media_campaign_history"])
    campaign_fighters = app.roster[: capacity + 1]
    random.seed(1103)
    ok, text, _row = app.resolve_media_campaign("Interview", campaign_fighters[0])
    check(ok, f"First weekly interview failed: {text}")
    repeat_ok, repeat_text, _row = app.resolve_media_campaign("Interview", campaign_fighters[0])
    check(not repeat_ok and "already completed" in repeat_text, "Same fighter bypassed the weekly media cooldown")
    for fighter in campaign_fighters[1:capacity]:
        ok, text, _row = app.resolve_media_campaign("Interview", fighter)
        check(ok, f"A media action failed before weekly capacity was reached: {text}")
    check(app.media_actions_remaining() == 0, "Weekly media capacity was not consumed correctly")
    extra_ok, extra_text, _row = app.resolve_media_campaign("Interview", campaign_fighters[capacity])
    check(not extra_ok and "0 media action" in extra_text, "Media campaign exceeded weekly action capacity")
    check(len(app.finance["media_campaign_history"]) == history_before + capacity, "Successful campaigns were not all stored in history")

    app.week += 1
    check(app.media_actions_remaining() == capacity, "Media action capacity did not reset in a new week")
    random.seed(1104)
    ok, text, _row = app.resolve_media_campaign("Interview", campaign_fighters[0])
    check(ok, f"Fighter remained incorrectly locked in the next week: {text}")

    return contract, event


def run_sponsor_management_checks(app):
    finance = app.ensure_player_media_state()
    finance["sponsor_offers"] = [{
        "id": "test-sponsor", "name": "Test Hydration", "category": "Hydration",
        "fee": 10_000, "months": 12, "fit": 80, "relationship": 50,
        "activation_requirement": "Maintain company stability above 45",
        "conduct_threshold": 35, "expires_month": app.month + 1,
    }]
    finance_before_preview = deepcopy(finance)
    rng_before_preview = random.getstate()
    assessment = app.sponsor_offer_assessment(finance["sponsor_offers"][0])
    check(finance == finance_before_preview and random.getstate() == rng_before_preview,
          "Sponsor offer valuation preview changed state or consumed RNG")
    check(assessment["annual"] == 120_000 and 0 <= assessment["score"] <= 100
          and assessment["verdict"] in ("STRONG FIT", "WORKABLE", "LOW VALUE"),
          "Sponsor comparison did not value fee, fit and term correctly")
    check(assessment["max_per_event"] == 10_000 and assessment["estimated_per_event"] == 10_000
          and assessment["term_months"] == 12 and assessment["activation_ready"],
          "Sponsor comparison did not separate contracted maximum from current estimate")
    accepted, _message = app.counter_sponsor_offer("test-sponsor", roll=1)
    check(accepted and finance["sponsor_offers"][0]["fee"] == 11_200,
          "Successful sponsor counter did not raise the event fee by 12 percent")
    check(not app.counter_sponsor_offer("test-sponsor", roll=1)[0],
          "A sponsor answered more than one counteroffer")

    deal = finance["sponsor_offers"][0]
    old_stability = app.company_stability
    app.company_stability = 45
    ready, reason = app.sponsor_activation_status(deal)
    check(not ready and "stability" in reason, "Sponsor stability requirement was only descriptive")
    at_risk = app.sponsor_offer_assessment(deal)
    check(not at_risk["activation_ready"] and at_risk["estimated_per_event"] == round(deal["fee"] * .5)
          and "stability" in at_risk["activation_reason"],
          "Sponsor preview did not disclose its activation-adjusted estimate")
    delivery_deal = {**deal, "activation_requirement": "Deliver at least one event each month"}
    finance["media_audience_history"] = []
    check(not app.sponsor_activation_status(delivery_deal)[0]
          and app.sponsor_activation_status(delivery_deal, event={"month": app.month, "week": app.week})[0],
          "Monthly event-delivery sponsor requirement was not enforced at settlement")
    check(app.sponsor_event_fee(deal) == deal["fee"] // 2,
          "An at-risk sponsor did not reduce its event payment")
    app.company_stability = max(46, old_stability)
    check(app.sponsor_activation_status(deal)[0], "A satisfied sponsor requirement stayed at risk")

    featured = app.roster[0]
    old_champion, old_rank = featured.champion, featured.ranking_position
    featured.champion = True
    ranked_deal = {**deal, "activation_requirement": "Feature a ranked fighter in campaign media"}
    finance["media_campaign_history"] = []
    check(not app.sponsor_activation_status(ranked_deal)[0],
          "Ranked-fighter activation passed without current-month campaign work")
    finance["media_campaign_history"] = [{"month": app.month, "subject": featured.name}]
    check(app.sponsor_activation_status(ranked_deal)[0],
          "Current-month champion media did not activate its sponsor")
    featured.champion, featured.ranking_position = old_champion, old_rank
    app.company_stability = old_stability


def run_legacy_migration_check(app):
    current_finance = app.finance
    try:
        legacy_finance = app.seed_finance()
        legacy_finance.pop("media_contracts", None)
        legacy_finance["media_rights"] = {
            "name": "Legacy Active Network",
            "months": 7,
            "fee": 31_000,
            "reach": 33,
        }
        app.finance = legacy_finance
        app.ensure_player_media_state()
        legacy = app.active_media_contract()
        check(legacy is not None, "Old active media-rights package was not migrated into a contract")
        check(legacy["events_remaining"] > 0, "Old active rights package migrated with no event commitment")
        check(legacy["guarantee_per_event"] == 31_000, "Old rights fee did not migrate to guarantee_per_event")
        check(app.finance["media_rights"] is legacy, "Migrated legacy deal did not sync its compatibility alias")
    finally:
        app.finance = current_finance
        app.ensure_player_media_state()


def run_ai_media_checks(app):
    promo = next(promotion for promotion in app.promotions if not promotion.is_regional_feeder and promotion.roster)
    promo.finance = {}
    app.ensure_ai_media_state(promo)
    random.seed(2201)
    offers = app.generate_media_offers(promo, force=True, count=4)
    check(len(offers) >= 2, f"{promo.name} did not receive AI media offers")
    random.seed(2202)
    contract = app.review_ai_media_deals(promo)
    check(contract is not None, f"{promo.name} did not select an AI media contract")
    check(promo.finance["media_rights"] is contract, "AI promotion legacy media-rights alias is not synced")

    fighter_a, fighter_b = promo.roster[:2]
    event = {
        "name": f"{promo.name} Media Regression",
        "region": supported_region(app, contract, promo.region),
        "broadcaster": "AI Event Production",
        "fights": [{"fighters": [fighter_a.name, fighter_b.name]}],
    }
    before_events = contract["events_remaining"]
    before_history = len(promo.finance["media_audience_history"])
    random.seed(2203)
    outcome = app.calculate_event_media_outcome(event, event_package(event["name"]), promotion=promo, contract=contract)
    check(outcome["eligible"], f"AI event was not eligible for its signed contract: {outcome['reason']}")
    check(outcome["rating"] > 0 and outcome["viewers"] > 0, "AI event did not produce a valid audience outcome")
    app.record_media_event_outcome(event, outcome, promotion=promo, featured_fighters=[fighter_a, fighter_b])
    check(contract["events_remaining"] == before_events - 1, "AI event did not decrement its media contract")
    check(len(promo.finance["media_audience_history"]) == before_history + 1, "AI audience outcome was not stored")
    return promo, contract, event


def run_round_trip_check(app, player_contract, player_event, ai_promo, ai_contract, ai_event):
    snapshot = app.serialize_world()
    check(len(snapshot.get("media_companies", [])) >= 8, "Serialized world omitted the media-company database")
    check(snapshot.get("media_market_history") is not None, "Serialized world omitted media-market history")
    check(snapshot["finance"].get("media_contracts"), "Serialized player finance omitted media contracts")
    check(snapshot["finance"].get("media_campaign_history"), "Serialized player finance omitted campaign history")
    check(snapshot["finance"].get("media_audience_history"), "Serialized player finance omitted audience history")

    root = tk.Tk()
    root.withdraw()
    try:
        restored = FightEmpireApp(root)
        restored.apply_world_data(deepcopy(snapshot))
        restored_player_contract = restored.active_media_contract()
        check(restored_player_contract is not None, "Round trip lost the player media contract")
        check(restored_player_contract["id"] == player_contract["id"], "Round trip restored the wrong player media contract")
        check(any(row.get("event") == player_event["name"] for row in restored.finance["media_audience_history"]), "Round trip lost player audience history")
        check(restored.finance["media_campaign_history"], "Round trip lost player campaign history")
        restored_ai = next((promotion for promotion in restored.promotions if promotion.name == ai_promo.name), None)
        check(restored_ai is not None, "Round trip lost the tested AI promotion")
        restored_ai_contract = restored.active_media_contract(restored_ai)
        check(restored_ai_contract is not None, "Round trip lost the AI media contract")
        check(restored_ai_contract["id"] == ai_contract["id"], "Round trip restored the wrong AI media contract")
        check(any(row.get("event") == ai_event["name"] for row in restored_ai.finance["media_audience_history"]), "Round trip lost AI audience history")
    finally:
        root.destroy()


def main():
    silence_messageboxes()
    random.seed(1000)
    root = tk.Tk()
    root.withdraw()
    try:
        app = FightEmpireApp(root)
        run_sponsor_management_checks(app)
        player_contract, player_event = run_player_media_checks(app)
        run_legacy_migration_check(app)
        ai_promo, ai_contract, ai_event = run_ai_media_checks(app)
        run_round_trip_check(app, player_contract, player_event, ai_promo, ai_contract, ai_event)
        print("MEDIA SYSTEM TEST PASSED")
        print(f"Outlets: {len(app.media_companies)}")
        print(f"Player contract: {player_contract['name']} ({player_contract['events_remaining']} events remaining)")
        print(f"Player campaigns stored: {len(app.finance['media_campaign_history'])}")
        print(f"Player audience reports stored: {len(app.finance['media_audience_history'])}")
        print(f"AI contract: {ai_promo.name} / {ai_contract['name']} ({ai_contract['events_remaining']} events remaining)")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
