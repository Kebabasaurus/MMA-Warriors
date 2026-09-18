"""Regression coverage for the bounded M1 managed-campaign plan slice."""

import unittest
from copy import deepcopy

from feature_foundation import FoundationMixin
from media import MediaMixin
from models import Fighter
from world import WorldMixin


def make_fighter(name, fighter_id):
    return Fighter(
        name=name, weight="Lightweight", age=27, record_w=8, record_l=2,
        striking=70, wrestling=65, grappling=68, cardio=72, chin=70,
        popularity=45, momentum=0, morale=70, purse=10_000,
        fighter_id=fighter_id,
    )


class MediaPlanHarness(MediaMixin, FoundationMixin):
    def __init__(self):
        self.month, self.week = 4, 2
        self.player_company_name = "Plan FC"
        self.player_region = "USA"
        self.company_pop = 45
        self.company_stability = 60
        self.cash = 100_000
        self.roster = [make_fighter("Prospect One", "fighter-1")]
        self.free_agents = []
        self.scheduled_events = [{"event_id": "event-1", "name": "Spring Card", "month": 4, "week": 4}]
        self.promotions = []
        self.player_combat_divisions = {}
        self.combat_sport_worlds = {}
        self.media_companies = []
        self.news = []
        self.fanbase = {"casual_reach": 30}
        self.finance = {"ledger": []}
        self.ensure_foundation_state()
        self.ensure_media_system()

    def staff_skill(self, _role):
        return 55

    def record_finance_transaction(self, *_args, **_kwargs):
        return None


class MalformedMediaUniverseHarness(MediaPlanHarness):
    def universe_section(self, _name, _default):
        return {"rights_packages": [{
            "id": "custom-malformed", "name": "Legacy Broadcaster",
            "reach": "not-a-number", "markets": "USA", "prestige": object(),
            "budget": None, "selectivity": "bad", "min_production": object(),
            "base_fee": "unknown", "volatility": "invalid",
        }]}


class ReceiptTreeStub:
    """Small Treeview stand-in for read-model identity regression tests."""

    def __init__(self):
        self.rows = {}
        self.selected = ()

    def selection(self):
        return self.selected

    def selection_set(self, row_id):
        self.selected = (row_id,)

    def delete(self, *row_ids):
        if row_ids:
            for row_id in row_ids:
                self.rows.pop(row_id, None)
        else:
            self.rows.clear()

    def get_children(self):
        return tuple(self.rows)

    def insert(self, _parent, _where, iid, **kwargs):
        self.rows[iid] = kwargs


class DetailStub:
    def __init__(self):
        self.text = ""

    def config(self, **kwargs):
        self.text = kwargs.get("text", self.text)


class ChoiceStub:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class ComboStub:
    def __init__(self):
        self.values = ()

    def configure(self, **kwargs):
        self.values = tuple(kwargs.get("values", self.values))


class MediaPlanTests(unittest.TestCase):
    def test_create_retarget_cancel_preserves_plan_and_no_effect(self):
        app = MediaPlanHarness()
        before = (app.cash, app.roster[0].popularity, app.roster[0].media_heat)
        ok, _text, plan = app.create_media_campaign_plan("Event Promotion", "event-1", action_ids=["Interview"], spend_ceiling=15_000)
        self.assertTrue(ok)
        self.assertEqual(plan["status"], "Draft")
        self.assertEqual((app.cash, app.roster[0].popularity, app.roster[0].media_heat), before)
        ok, _text, _plan = app.retarget_media_campaign_plan("event-1")
        self.assertTrue(ok)
        ok, _text, plan = app.cancel_media_campaign_plan()
        self.assertTrue(ok)
        self.assertEqual(plan["status"], "Cancelled")

    def test_quote_is_observational_when_week_marker_is_stale(self):
        app = MediaPlanHarness()
        app.finance["media_action_week"] = -1
        app.finance["media_actions_used"] = 2
        before = dict(app.finance)
        quote = app.media_plan_quote("Event Promotion", "event-1", "Interview", app.roster[0])
        self.assertEqual(quote["details"]["remaining_points"], app.media_action_capacity())
        self.assertEqual(app.finance, before)

    def test_media_dashboard_capacity_read_is_pure_on_stale_week_marker(self):
        app = MediaPlanHarness()
        app.finance["media_action_week"] = -1
        app.finance["media_actions_used"] = 2
        before = dict(app.finance)
        self.assertEqual(app.media_actions_remaining_readonly(), app.media_action_capacity())
        self.assertEqual(app.finance, before)

    def test_media_dashboard_capacity_read_does_not_seed_malformed_envelope(self):
        app = MediaPlanHarness()
        app.finance = "legacy media payload"
        self.assertEqual(app.media_actions_remaining_readonly(), app.media_action_capacity())
        self.assertEqual(app.finance, "legacy media payload")

    def test_media_readonly_envelope_does_not_seed_legacy_defaults(self):
        app = MediaPlanHarness()
        app.finance = {"media_action_week": -1, "media_actions_used": 1}
        self.assertEqual(app._media_finance_readonly(), app.finance)
        self.assertNotIn("media_primary_plan", app.finance)
        # Target reads explicitly opt out of foundation migration.  Saving a
        # plan remains the explicit boundary that may assign missing IDs.
        foundation_before = repr(app._foundation_state)
        app.media_plan_target_options("Event Promotion", migrate=False)
        self.assertEqual(foundation_before, repr(app._foundation_state))

    def test_active_contract_lookup_does_not_seed_missing_finance(self):
        app = MediaPlanHarness()
        app.finance = None
        self.assertIsNone(app.active_media_contract())
        self.assertIsNone(app.finance)

    def test_active_ai_contract_lookup_does_not_seed_missing_promotion_finance(self):
        app = MediaPlanHarness()
        class PromotionStub:
            finance = None
        promo = PromotionStub()
        self.assertIsNone(app.active_media_contract(promo))
        self.assertIsNone(promo.finance)

    def test_execute_attaches_one_evidence_receipt_and_retry_is_read_only(self):
        app = MediaPlanHarness()
        ok, _text, _plan = app.create_media_campaign_plan("Prospect Exposure", "fighter-1", action_ids=["Interview"], spend_ceiling=20_000)
        self.assertTrue(ok)
        fighter = app.roster[0]
        ok, text, result = app.execute_media_campaign_plan("Interview", fighter)
        self.assertTrue(ok, text)
        self.assertIn("evidence_key", result)
        self.assertEqual(len(app.finance["media_primary_plan"]["action_receipts"]), 1)
        state = (app.cash, fighter.popularity, fighter.media_heat, len(app.finance["media_campaign_history"]))
        ok, _text, _result = app.execute_media_campaign_plan("Interview", fighter)
        self.assertTrue(ok)
        self.assertEqual(state, (app.cash, fighter.popularity, fighter.media_heat, len(app.finance["media_campaign_history"])))
        self.assertEqual(len(app.ensure_foundation_state()["operations"]), 1)

    def test_plan_spend_ceiling_counts_nested_receipts_across_weeks(self):
        app = MediaPlanHarness()
        action = "Highlight Package"
        cost = app.media_plan_quote("Prospect Exposure", "fighter-1", action, app.roster[0])["amount"]
        app.create_media_campaign_plan("Prospect Exposure", "fighter-1", action_ids=[action], spend_ceiling=cost)
        before = app.cash
        ok, text, _result = app.execute_media_campaign_plan(action, app.roster[0])
        self.assertTrue(ok, text)
        app.week += 1
        state = (app.cash, app.finance.get("media_actions_used"), len(app.finance["media_campaign_history"]))
        ok, text, _result = app.execute_media_campaign_plan(action, app.roster[0])
        self.assertFalse(ok)
        self.assertIn("spend ceiling", text)
        self.assertEqual(before - app.cash, cost)
        self.assertEqual(state, (app.cash, app.finance.get("media_actions_used"), len(app.finance["media_campaign_history"])))

    def test_plan_spend_ceiling_fails_closed_for_unknown_prior_cost(self):
        app = MediaPlanHarness()
        action = "Highlight Package"
        cost = app.media_plan_quote("Prospect Exposure", "fighter-1", action, app.roster[0])["amount"]
        app.create_media_campaign_plan("Prospect Exposure", "fighter-1", action_ids=[action], spend_ceiling=cost * 2)
        plan = app.finance["media_primary_plan"]
        plan["action_receipts"] = [{"evidence_key": "legacy", "action": action, "cost": cost}]
        before = (app.cash, deepcopy(app.finance.get("media_campaign_history", [])))
        ok, text, _result = app.execute_media_campaign_plan(action, app.roster[0])
        self.assertFalse(ok)
        self.assertIn("incomplete", text.lower())
        self.assertEqual(before, (app.cash, app.finance.get("media_campaign_history", [])))

    def test_duplicate_plan_targets_route_by_display_label_and_source_id(self):
        app = MediaPlanHarness()
        app.scheduled_events = [
            {"event_id": "event-1", "name": "Shared Name", "month": 5, "week": 1},
            {"event_id": "event-2", "name": "Shared Name", "month": 6, "week": 1},
        ]
        app.media_plan_target_combo = ComboStub()
        app.media_plan_target_choice = ChoiceStub("")
        app.media_plan_objective_choice = ChoiceStub("Event Promotion")
        app.refresh_media_plan_summary = lambda: None
        app.refresh_media_plan_targets()
        self.assertEqual(len(set(app.media_plan_target_combo.values)), 2)
        second_label = next(label for label, source_id in app._media_plan_target_map.items() if source_id == "event-2")
        app.media_plan_target_choice.set(second_label)
        self.assertEqual(app._selected_media_plan_target_id(), "event-2")
        app.scheduled_events.reverse()
        app.refresh_media_plan_targets()
        self.assertEqual(app._selected_media_plan_target_id(), "event-2")
        app.scheduled_events = [row for row in app.scheduled_events if row["event_id"] == "event-1"]
        app.refresh_media_plan_targets()
        self.assertEqual(app._selected_media_plan_target_id(), "")
        self.assertEqual(app.media_plan_target_choice.get(), "")

    def test_duplicate_fighter_and_sponsor_targets_remain_distinct(self):
        app = MediaPlanHarness()
        app.roster.append(make_fighter("Prospect One", "fighter-2"))
        fighter_rows = app.media_plan_target_options("Prospect Exposure", migrate=False)
        self.assertEqual(len({row["display_label"] for row in fighter_rows}), 2)
        self.assertEqual({row["id"] for row in fighter_rows}, {"fighter-1", "fighter-2"})
        app.finance["sponsor_deals"] = [
            {"id": "sponsor-1", "name": "Shared Sponsor", "category": "Hydration"},
            {"id": "sponsor-2", "name": "Shared Sponsor", "category": "Apparel"},
        ]
        sponsor_rows = app.media_plan_target_options("Sponsor Duty", migrate=False)
        self.assertEqual(len({row["display_label"] for row in sponsor_rows}), 2)
        self.assertEqual({row["id"] for row in sponsor_rows}, {"sponsor-1", "sponsor-2"})

    def test_duplicate_source_identity_fails_closed_during_plan_refresh(self):
        app = MediaPlanHarness()
        app.scheduled_events = [
            {"event_id": "event-1", "name": "One", "month": 5, "week": 1},
            {"event_id": "event-1", "name": "Two", "month": 6, "week": 1},
        ]
        app.media_plan_target_combo = ComboStub()
        app.media_plan_target_choice = ChoiceStub("")
        app.media_plan_objective_choice = ChoiceStub("Event Promotion")
        app.refresh_media_plan_summary = lambda: None
        foundation_before = deepcopy(app._foundation_state)
        app.refresh_media_plan_targets()
        self.assertEqual(app._media_plan_target_map, {})
        self.assertEqual(app._selected_media_plan_target_id(), "")
        self.assertTrue(all("duplicate identity" in label for label in app.media_plan_target_combo.values))
        self.assertEqual(app._foundation_state, foundation_before)

    def test_invalid_target_and_action_fail_without_mutation(self):
        app = MediaPlanHarness()
        ok, _text, _plan = app.create_media_campaign_plan("Event Promotion", "event-1", action_ids=["Crisis Response"])
        self.assertTrue(ok)
        self.assertEqual(app.finance["media_primary_plan"]["allowed_action_ids"], ["Press Tour"])
        before = dict(app.finance["media_primary_plan"])
        self.assertFalse(app.retarget_media_campaign_plan("missing")[0])
        self.assertEqual(app.finance["media_primary_plan"]["target_id"], before["target_id"])

    def test_rights_terms_expose_alias_conflict_without_rewriting_it(self):
        app = MediaPlanHarness()
        legacy = {"fee": 12000, "guarantee_per_event": 9000, "months": 6, "events_remaining": 4, "min_production": 55}
        terms = app.media_contract_terms(legacy)
        self.assertTrue(terms["alias_conflict"])
        self.assertEqual(terms["canonical_fee"], 12000)
        self.assertEqual(terms["guarantee_per_event"], 9000)
        self.assertIn("Legacy fee aliases disagree", terms["warning"])
        self.assertEqual(legacy["fee"], 12000)

    def test_rights_terms_fail_closed_for_malformed_legacy_numbers(self):
        app = MediaPlanHarness()
        legacy = {"fee": "not-a-number", "guarantee_per_event": None, "months": "unknown", "events_remaining": object(), "min_production": "bad"}
        before = repr(legacy)
        terms = app.media_contract_terms(legacy)
        self.assertEqual(terms["canonical_fee"], 0)
        self.assertEqual(terms["months"], 0)
        self.assertEqual(terms["events_remaining"], 0)
        self.assertEqual(terms["minimum_production"], 45)
        self.assertEqual(repr(legacy), before)

    def test_rights_readers_fail_closed_for_nonfinite_legacy_numbers(self):
        app = MediaPlanHarness()
        legacy = {
            "id": "rights-nonfinite-history", "status": "Active", "fee": float("inf"),
            "guarantee_per_event": float("nan"), "months": float("inf"),
            "events_remaining": float("nan"), "events_total": float("inf"),
            "breach_strikes": float("inf"), "min_production": float("nan"),
        }
        app.finance["media_contracts"] = [legacy]
        before = deepcopy(legacy)
        terms = app.media_contract_terms(legacy)
        history = app.media_contract_history_readonly(limit=float("inf"))
        self.assertEqual(terms["canonical_fee"], 0)
        self.assertEqual(terms["guarantee_per_event"], 0)
        self.assertEqual(terms["months"], 0)
        self.assertEqual(terms["events_remaining"], 0)
        self.assertEqual(history[0]["lifecycle_status"], "Needs review")
        self.assertEqual(history[0]["fee"], 0)
        self.assertEqual(legacy, before)

    def test_plan_summary_projects_malformed_quote_without_mutating_plan(self):
        app = MediaPlanHarness()
        app.media_plan_summary = DetailStub()
        app.media_plan_action_choice = ChoiceStub("Interview")
        app.finance["media_primary_plan"] = {
            "status": "Active", "objective": "Event Promotion", "target_id": "event-1",
            "target_label": "Spring Card", "action_receipts": "legacy-not-a-list",
            "revision": float("inf"),
        }
        before = deepcopy(app.finance)
        app.media_plan_quote = lambda *_args, **_kwargs: {"amount": float("inf"), "details": "legacy-not-a-mapping"}
        app.refresh_media_plan_summary()
        self.assertIn("Action Interview ($0, 0 AP)", app.media_plan_summary.text)
        self.assertIn("Completed 0", app.media_plan_summary.text)
        self.assertIn("Revision 1", app.media_plan_summary.text)
        self.assertEqual(app.finance, before)

    def test_readonly_media_capacity_fails_closed_for_nonfinite_usage(self):
        app = MediaPlanHarness()
        marker = (app.month - 1) * 4 + app.week
        app.finance.update({
            "media_action_week": marker,
            "media_actions_used": float("inf"),
        })
        self.assertEqual(app.media_actions_remaining_readonly(), app.media_action_capacity())

    def test_receipt_detail_fails_closed_for_nonfinite_amounts(self):
        app = MediaPlanHarness()
        app.media_receipt_detail = DetailStub()
        app.media_receipts_tree = ReceiptTreeStub()
        receipt = {
            "event": "Legacy Card",
            "rights": {"amount": float("inf"), "outlet": "Legacy Outlet"},
            "sponsors": [{"name": "Legacy Brand", "amount": float("nan")}],
            "sponsor_total": float("inf"), "relationship_delta": float("nan"),
        }
        app._media_receipt_rows = {"receipt:legacy": receipt}
        app.media_receipts_tree.selection_set("receipt:legacy")

        app.show_selected_media_receipt()

        self.assertIn("Rights: Legacy Outlet $0", app.media_receipt_detail.text)
        self.assertIn("Sponsor total $0", app.media_receipt_detail.text)

    def test_contract_eligibility_fails_closed_for_malformed_saved_terms(self):
        app = MediaPlanHarness()
        event = {"event_id": "event-malformed-eligibility", "broadcaster": "Coverage", "region": "USA"}
        for field, value in (("months", "unknown"), ("events_remaining", object())):
            contract = {"status": "Active", "months": 3, "events_remaining": 2,
                        "outlet_id": "local_fight_stream", field: value}
            ok, reason = app.media_contract_eligibility(contract, event)
            self.assertFalse(ok)
            self.assertIn("inactive", reason.lower())

    def test_media_outcome_handles_malformed_contract_metrics_without_overwriting_them(self):
        app = MediaPlanHarness()
        contract = {
            "id": "rights-malformed-metrics", "outlet_id": "local_fight_stream",
            "name": "Legacy Outlet", "status": "Active", "fee": 20_000,
            "guarantee_per_event": 20_000, "months": 4, "events_total": 4,
            "events_remaining": 4, "relationship": "unknown", "breach_strikes": object(),
            "minimum_rating": 0, "min_card_quality": 0, "min_production": 0,
        }
        app.finance["media_contracts"] = [contract]
        app.sync_legacy_media_rights()
        event = {"event_id": "event-malformed-metrics", "name": "Legacy Card",
                 "broadcaster": "Coverage", "region": "USA", "fights": []}
        before_relationship = contract["relationship"]
        before_breaches = contract["breach_strikes"]
        row = app.record_media_event_outcome(event, {
            "eligible": True, "delivered": False, "rights_income": 20_000,
            "outlet": "Legacy Outlet", "relationship_delta": 2,
        })
        self.assertEqual(row["settlement_status"], "Needs review")
        self.assertIn("relationship is malformed", row["settlement_review"])
        self.assertIn("breach_strikes is malformed", row["settlement_review"])
        self.assertIs(contract["relationship"], before_relationship)
        self.assertIs(contract["breach_strikes"], before_breaches)

    def test_media_outcome_quotes_malformed_package_and_contract_numbers_safely(self):
        app = MediaPlanHarness()
        contract = {
            "id": "rights-malformed-quote", "outlet_id": "local_fight_stream",
            "name": "Legacy Outlet", "status": "Active", "fee": "bad",
            "guarantee_per_event": "bad", "months": 4, "events_remaining": 4,
            "minimum_rating": "unknown", "min_card_quality": object(),
            "min_production": "invalid", "reach": "not-a-number",
        }
        event = {"event_id": "event-malformed-quote", "name": "Legacy Card",
                 "broadcaster": "Coverage", "region": "USA", "fights": "bad"}
        result = app.calculate_event_media_outcome(event, {
            "fight_count": "bad", "average_excitement": object(),
            "finance": {"build_score": "invalid"},
        }, contract=contract)
        self.assertIsInstance(result["rating"], int)
        self.assertEqual(result["rights_income"], 0)
        self.assertEqual(result["required_production"], 0)

    def test_media_outcome_fails_closed_for_nonfinite_package_and_contract_numbers(self):
        app = MediaPlanHarness()
        contract = {
            "id": "rights-nonfinite-quote", "outlet_id": "local_fight_stream",
            "name": "Legacy Outlet", "status": "Active", "fee": float("inf"),
            "guarantee_per_event": float("nan"), "months": 4, "events_remaining": 4,
            "minimum_rating": float("inf"), "min_card_quality": float("nan"),
            "min_production": float("inf"), "reach": float("nan"),
        }
        event = {"event_id": "event-nonfinite-quote", "name": "Legacy Card",
                 "broadcaster": "Coverage", "region": "USA", "fights": []}
        package = {"fight_count": float("inf"), "average_excitement": float("nan"),
                   "finance": {"build_score": float("inf")}}
        before = deepcopy(contract)
        result = app.calculate_event_media_outcome(event, package, contract=contract)
        self.assertIsInstance(result["rating"], int)
        self.assertEqual(result["rights_income"], 0)
        self.assertEqual(result["required_production"], 0)
        self.assertEqual(contract, before)

    def test_sponsor_event_fee_handles_malformed_saved_fee(self):
        app = MediaPlanHarness()
        deal = {"name": "Legacy Brand", "fee": "unknown", "conduct_threshold": 0}
        self.assertEqual(app.sponsor_event_fee(deal), 0)

    def test_media_month_holds_malformed_expiry_terms_for_review(self):
        app = MediaPlanHarness()
        app.finance["media_contracts"] = [{
            "id": "rights-expiry-review", "name": "Legacy Outlet", "status": "Active",
            "fee": 20_000, "months": "unknown", "events_remaining": 2,
        }]
        app.finance["media_rights"] = {}
        app.spectator_mode = True
        app.update_media_market = lambda: None
        app.process_media_month()
        contract = app.finance["media_contracts"][0]
        self.assertEqual(contract["months"], "unknown")
        self.assertTrue(contract["contract_review_required"])
        self.assertIn("held", contract["contract_review_reason"])

    def test_media_month_does_not_activate_successor_with_malformed_entitlements(self):
        app = MediaPlanHarness()
        app.finance["media_contracts"] = [{
            "id": "rights-complete", "name": "Prior Outlet", "status": "Fulfilled",
            "fee": 20_000, "months": 0, "events_remaining": 0,
        }]
        app.finance["media_successor_contract"] = {
            "id": "renewal:bad-entitlement", "predecessor_id": "rights-complete",
            "name": "Next Outlet", "status": "Pending", "events_total": "unknown",
        }
        app.spectator_mode = True
        app.update_media_market = lambda: None
        app.process_media_month()
        pending = app.finance["media_successor_contract"]
        self.assertEqual(pending["status"], "Needs review")
        self.assertIn("entitlement", pending["needs_review_reason"])
        self.assertEqual(len(app.finance["media_contracts"]), 1)

    def test_media_state_boundary_handles_malformed_contract_collections(self):
        app = MediaPlanHarness()
        app.finance = {
            "media_rights": {"name": "Legacy Outlet", "months": "unknown", "fee": "bad"},
            "media_contracts": "not-a-list", "media_offers": {"offer": "bad"},
        }
        app.ensure_player_media_state()
        self.assertEqual(app.finance["media_contracts"], [])
        self.assertEqual(app.finance["media_offers"], [])
        self.assertIsNone(app.active_media_contract())

    def test_malformed_custom_media_package_does_not_abort_system_initialisation(self):
        app = MalformedMediaUniverseHarness()
        outlet = next(row for row in app.media_companies if row.get("id") == "custom-malformed")
        self.assertEqual(outlet["reach"], 25)
        self.assertEqual(outlet["markets"], ["USA"])
        self.assertEqual(outlet["base_fee"], 10_000)
        self.assertEqual(outlet["volatility"], 15)

    def test_sponsor_settlement_activation_fails_closed_for_malformed_legacy_evidence(self):
        app = MediaPlanHarness()
        app.finance["media_public_trust"] = "unknown"
        app.finance["media_campaign_history"] = ["legacy campaign"]
        deal = {
            "name": "Legacy Brand", "fee": "bad", "conduct_threshold": "not-a-number",
            "activation_requirement": "Feature a ranked fighter in campaign media",
        }
        ready, reason = app.sponsor_activation_status(deal)
        self.assertFalse(ready)
        self.assertIn("run media", reason)

    def test_commercial_receipt_is_one_per_event_and_reopen_is_read_only(self):
        app = MediaPlanHarness()
        app.finance["sponsor_deals"] = [{"id": "s-1", "name": "Brand", "fee": 5000, "activation_requirement": "Event brand placement", "conduct_threshold": 0}]
        event = {"event_id": "event-1", "name": "Spring Card", "month": 4, "week": 4}
        outcome = {"outlet": "World Fight Pass", "rights_income": 22000, "delivered": True, "reason": "Delivered"}
        first = app.record_media_event_outcome(event, outcome)
        second = app.record_media_event_outcome(event, outcome)
        self.assertEqual(first["event_id"], "event-1")
        self.assertEqual(second["event_id"], "event-1")
        self.assertEqual(len(app.finance["media_commercial_receipts"]), 1)
        self.assertEqual(len(app.finance["media_audience_history"]), 1)
        receipt = app.finance["media_commercial_receipts"][0]
        self.assertEqual(receipt["rights"]["amount"], 22000)
        self.assertEqual(receipt["sponsors"][0]["status"], "Met")

    def test_commercial_receipt_detail_is_structured_and_observational(self):
        app = MediaPlanHarness()
        event = {"event_id": "event-detail", "name": "Detail Card", "month": 4, "week": 4}
        outcome = {
            "outlet": "World Fight Pass", "rights_income": 18_000, "delivered": False,
            "reason": "Production below the contracted standard", "rating": 61,
            "viewers": 120_000, "exposure_delta": -1, "campaign_lift": 2.5,
            "production_tier": "Standard", "production_quality": 45, "required_production": 65,
        }
        app.record_media_event_outcome(event, outcome)
        before = repr(app.finance)
        detail = app.media_commercial_receipt_details(event_id="event-detail")
        self.assertEqual(detail["receipt"]["rights"]["production_quality"], 45)
        self.assertEqual(detail["receipt"]["rights"]["required_production"], 65)
        self.assertEqual(detail["audience"]["viewers"], 120_000)
        self.assertEqual(detail["receipt"]["rights"]["delivered"], False)
        self.assertEqual(repr(app.finance), before)
        self.assertIsNone(app.media_commercial_receipt_details(receipt_id="missing"))

    def test_commercial_receipt_detail_prefers_saved_contract_identity(self):
        app = MediaPlanHarness()
        receipt = {
            "receipt_id": "commercial-receipt:shared-event", "event_id": "shared-event",
            "rights": {"contract_id": "contract-good", "outlet_id": "outlet-good"},
        }
        app.finance["media_commercial_receipts"] = [receipt]
        app.finance["media_audience_history"] = [
            {"event_id": "shared-event", "contract_id": "contract-wrong", "outlet_id": "outlet-wrong", "rating": 10},
            {"event_id": "shared-event", "contract_id": "contract-good", "outlet_id": "outlet-good", "rating": 99},
        ]
        before = deepcopy(app.finance)
        detail = app.media_commercial_receipt_details(receipt_id=receipt["receipt_id"])
        self.assertEqual(detail["audience"]["rating"], 99)
        self.assertEqual(app.finance, before)

    def test_commercial_receipt_reader_retains_selection_by_saved_identity(self):
        app = MediaPlanHarness()
        app.format_game_date_text = lambda value: str(value)
        app.media_receipts_tree = ReceiptTreeStub()
        app.media_receipt_detail = type("Label", (), {"config": lambda self, **_kwargs: None})()
        first = {"receipt_id": "commercial-receipt:event-a", "event_id": "event-a", "date": "M4 W1", "event": "Alpha", "rights": {"delivered": True}}
        second = {"receipt_id": "commercial-receipt:event-b", "event_id": "event-b", "date": "M4 W2", "event": "Bravo", "rights": {"delivered": False}}
        app.finance["media_commercial_receipts"] = [first, second]
        app.refresh_media_receipts()
        app.media_receipts_tree.selection_set("receipt:commercial-receipt:event-b")
        inserted = {"receipt_id": "commercial-receipt:event-new", "event_id": "event-new", "date": "M4 W3", "event": "New", "rights": {"delivered": True}}
        app.finance["media_commercial_receipts"] = [inserted, first, second]
        app.refresh_media_receipts()
        self.assertEqual(app.media_receipts_tree.selection(), ("receipt:commercial-receipt:event-b",))
        self.assertIs(app._selected_media_receipt(), second)

    def test_legacy_commercial_receipt_view_id_is_content_bound(self):
        legacy = {"date": "M1 W1", "event": "Old Card"}
        identity = MediaPlanHarness._media_receipt_identity_key(legacy)
        self.assertTrue(identity.startswith("legacy-receipt:"))
        self.assertEqual(MediaPlanHarness._media_receipt_view_id(legacy, 4), identity)
        self.assertEqual(MediaPlanHarness._media_receipt_view_id(legacy, 99), identity)

    def test_receipt_reader_handles_malformed_numeric_legacy_fields(self):
        app = MediaPlanHarness()
        app.format_game_date_text = lambda value: str(value)
        app.media_receipts_tree = ReceiptTreeStub()
        app.media_receipt_detail = type("Label", (), {"config": lambda self, **_kwargs: None})()
        app.finance["media_commercial_receipts"] = [{
            "receipt_id": "receipt-malformed", "event_id": "event-malformed",
            "date": "M4 W3", "event": "Legacy Card",
            "rights": {"delivered": True, "amount": "unknown", "production_quality": "bad"},
            "sponsor_total": "not-a-number", "relationship_delta": object(),
            "sponsors": [{"name": "Brand", "amount": "bad"}],
        }]
        app.refresh_media_receipts()
        self.assertIn("receipt:receipt-malformed", app.media_receipts_tree.get_children())

    def test_receipt_reader_surfaces_settlement_review_without_hiding_delivery_row(self):
        app = MediaPlanHarness()
        app.format_game_date_text = lambda value: str(value)
        app.media_receipts_tree = ReceiptTreeStub()
        app.media_receipt_detail = type("Label", (), {"config": lambda self, **_kwargs: None})()
        app.finance["media_commercial_receipts"] = [{
            "receipt_id": "receipt-review", "event_id": "event-review",
            "date": "M4 W4", "event": "Review Card",
            "rights": {"delivered": True, "amount": 20_000},
            "settlement_status": "Needs review",
            "settlement_review": "relationship is malformed",
        }]
        app.refresh_media_receipts()
        row = app.media_receipts_tree.rows["receipt:receipt-review"]
        self.assertEqual(row["tags"], ("review",))
        self.assertEqual(row["values"][-1], "REVIEW")

    def test_renewal_is_queued_without_overlapping_the_current_contract(self):
        app = MediaPlanHarness()
        app.finance["media_contracts"] = [{
            "id": "rights-1", "name": "Local Fight Stream", "status": "Active",
            "fee": 18000, "guarantee_per_event": 18000, "months": 4,
            "events_total": 4, "events_remaining": 4, "reach": 16,
        }]
        app.sync_legacy_media_rights()
        ok, _text, offer = app.prepare_media_renewal_offer()
        self.assertTrue(ok)
        self.assertEqual(offer["predecessor_id"], "rights-1")
        cash = app.cash
        ok, _text, _result = app.accept_media_renewal_offer()
        self.assertTrue(ok)
        self.assertEqual(app.cash, cash)
        self.assertEqual(app.finance["media_successor_contract"]["status"], "Pending")
        ok, _text, _result = app.accept_media_renewal_offer()
        self.assertTrue(ok)
        self.assertEqual(len(app.finance["media_contracts"]), 1)
        # The predecessor has fulfilled its quota; the successor starts at
        # the next calendar boundary without overlapping entitlement payment.
        app.finance["media_contracts"][0]["months"] = 1
        app.finance["media_contracts"][0]["events_remaining"] = 0
        app.spectator_mode = True
        app.update_media_market = lambda: None
        app.process_media_month()
        self.assertIsNone(app.finance["media_successor_contract"])
        self.assertEqual(app.active_media_contract()["status"], "Active")

    def test_rights_term_expiry_with_events_owed_is_explicit_shortfall(self):
        app = MediaPlanHarness()
        app.finance["media_contracts"] = [{
            "id": "rights-expire", "name": "Outlet", "status": "Active",
            "fee": 18_000, "guarantee_per_event": 18_000, "months": 1,
            "events_total": 4, "events_remaining": 4, "reach": 22,
        }]
        app.sync_legacy_media_rights()
        app.spectator_mode = True
        app.update_media_market = lambda: None
        app.process_media_month()
        self.assertEqual(app.finance["media_contracts"][0]["status"], "Expired with shortfall")
        self.assertIsNone(app.active_media_contract())

    def test_contract_history_does_not_label_malformed_evidence_as_fulfilled(self):
        app = MediaPlanHarness()
        app.finance["media_contracts"] = [{
            "id": "rights-history-review", "name": "Legacy Outlet", "status": "Completed",
            "months": 0, "events_remaining": "unknown", "events_total": 4,
            "breach_strikes": 0, "fee": 10_000,
        }]
        rows = app.media_contract_history_readonly()
        self.assertEqual(rows[0]["lifecycle_status"], "Needs review")

    def test_renewal_offer_opens_at_the_two_month_boundary_without_rng_or_spend(self):
        app = MediaPlanHarness()
        app.finance["media_contracts"] = [{
            "id": "rights-due", "name": "Outlet", "status": "Active",
            "fee": 18_000, "guarantee_per_event": 18_000, "months": 3,
            "events_total": 4, "events_remaining": 4, "reach": 22,
        }]
        app.sync_legacy_media_rights()
        app.spectator_mode = True
        app.update_media_market = lambda: None
        cash = app.cash
        app.process_media_month()
        offer = app.finance["media_successor_offer"]
        self.assertEqual(offer["status"], "Offer")
        self.assertEqual(offer["predecessor_id"], "rights-due")
        self.assertEqual(app.cash, cash)

    def test_rejected_renewal_is_retained_in_offer_history(self):
        app = MediaPlanHarness()
        app.finance["media_contracts"] = [{
            "id": "rights-reject", "name": "Outlet", "status": "Active",
            "fee": 18_000, "guarantee_per_event": 18_000, "months": 4,
            "events_total": 4, "events_remaining": 4, "reach": 22,
        }]
        app.sync_legacy_media_rights()
        ok, _text, _offer = app.prepare_media_renewal_offer()
        self.assertTrue(ok)
        ok, _text, rejected = app.reject_media_renewal_offer()
        self.assertTrue(ok)
        self.assertEqual(rejected["status"], "Rejected")
        self.assertEqual(app.finance["media_offer_history"][0]["decision"], "Renewal rejected")
        self.assertIsNone(app.finance["media_successor_offer"])

    def test_breach_termination_marks_pending_successor_needs_review(self):
        app = MediaPlanHarness()
        app.finance["media_contracts"] = [{
            "id": "rights-breach", "outlet_id": "outlet-1", "name": "Outlet", "status": "Active",
            "fee": 18_000, "guarantee_per_event": 18_000, "months": 4,
            "events_total": 4, "events_remaining": 4, "reach": 22, "breach_strikes": 2,
            "relationship": 50,
        }]
        app.finance["media_successor_contract"] = {
            "id": "renewal:rights-breach:4", "predecessor_id": "rights-breach",
            "name": "Outlet", "status": "Pending", "events_total": 4,
        }
        app.sync_legacy_media_rights()
        app.record_media_event_outcome(
            {"event_id": "event-breach", "name": "Breach Card"},
            {"eligible": True, "delivered": False, "rights_income": 18_000, "outlet": "Outlet"},
        )
        self.assertEqual(app.finance["media_contracts"][0]["status"], "Terminated")
        pending = app.finance["media_successor_contract"]
        self.assertEqual(pending["status"], "Needs review")
        self.assertIn("delivery failures", pending["needs_review_reason"])

    def test_media_outcome_and_receipt_keep_outlet_and_contract_identity(self):
        app = MediaPlanHarness()
        contract = {
            "id": "rights-identity", "outlet_id": "outlet-identity", "name": "Shared Name",
            "status": "Active", "fee": 20_000, "guarantee_per_event": 20_000,
            "months": 4, "events_total": 4, "events_remaining": 4,
            "minimum_rating": 0, "min_card_quality": 0, "min_production": 0,
        }
        event = {"event_id": "event-identity", "name": "Identity Card", "broadcaster": "Coverage", "region": "USA", "fights": []}
        outcome = app.calculate_event_media_outcome(event, {"fight_count": 1, "average_excitement": 70, "average_build": 70}, contract=contract)
        self.assertEqual(outcome["outlet_id"], "outlet-identity")
        self.assertEqual(outcome["contract_id"], "rights-identity")
        app.finance["media_contracts"] = [contract]
        app.sync_legacy_media_rights()
        app.record_media_event_outcome(event, outcome)
        receipt = app.finance["media_commercial_receipts"][0]
        self.assertEqual(receipt["rights"]["outlet_id"], "outlet-identity")
        self.assertEqual(receipt["rights"]["contract_id"], "rights-identity")

    def test_manual_legacy_outcome_is_enriched_from_active_contract_identity(self):
        app = MediaPlanHarness()
        app.finance["media_contracts"] = [{
            "id": "rights-manual", "outlet_id": "outlet-manual", "name": "Shared Name",
            "status": "Active", "fee": 20_000, "guarantee_per_event": 20_000,
            "months": 4, "events_total": 4, "events_remaining": 4,
        }]
        app.sync_legacy_media_rights()
        app.record_media_event_outcome(
            {"event_id": "event-manual", "name": "Manual Card"},
            {"eligible": True, "delivered": True, "rights_income": 20_000, "outlet": "Shared Name"},
        )
        rights = app.finance["media_commercial_receipts"][0]["rights"]
        self.assertEqual(rights["outlet_id"], "outlet-manual")
        self.assertEqual(rights["contract_id"], "rights-manual")

    def test_contract_history_read_model_keeps_terminal_statuses_without_mutation(self):
        app = MediaPlanHarness()
        app.finance["media_contracts"] = [
            {"id": "rights-old", "outlet_id": "outlet-old", "name": "Old Deal", "status": "Completed",
             "months": 0, "events_total": 4, "events_remaining": 0, "breach_strikes": 0, "fee": 10_000},
            {"id": "rights-short", "outlet_id": "outlet-short", "name": "Short Deal", "status": "Completed",
             "months": 0, "events_total": 4, "events_remaining": 2, "breach_strikes": 1, "fee": 12_000},
            {"id": "rights-term", "outlet_id": "outlet-term", "name": "Terminated Deal", "status": "Terminated",
             "months": 3, "events_total": 4, "events_remaining": 2, "breach_strikes": 3, "fee": 14_000},
        ]
        before = repr(app.finance)
        rows = app.media_contract_history_readonly()
        self.assertEqual([row["lifecycle_status"] for row in rows], ["Fulfilled", "Expired with shortfall", "Terminated"])
        self.assertEqual([row["contract_id"] for row in rows], ["rights-old", "rights-short", "rights-term"])
        self.assertEqual(repr(app.finance), before)

    def test_contract_delivery_history_excludes_predecessor_and_unscoped_rows(self):
        app = MediaPlanHarness()
        active = {"id": "new", "contract_id": "new", "outlet_id": "outlet-a", "name": "Outlet A"}
        history = [
            {"contract_id": "old", "outlet_id": "outlet-a", "delivered": False, "event": "Old deal"},
            {"contract_id": "new", "outlet_id": "outlet-a", "delivered": True, "event": "New deal"},
            {"outlet_id": "outlet-a", "delivered": False, "event": "Legacy unscoped"},
            {"contract_id": "new", "outlet_id": "outlet-b", "delivered": True, "event": "Saved contract wins"},
        ]
        before = deepcopy(history)
        rows, unscoped = app.media_contract_delivery_history(active, history)
        self.assertEqual([row["event"] for row in rows], ["New deal", "Saved contract wins"])
        self.assertEqual(unscoped, 1)
        self.assertEqual(history, before)

    def test_legacy_contract_delivery_history_uses_bounded_identity_fallback(self):
        app = MediaPlanHarness()
        history = [
            {"outlet_id": "outlet-a", "outlet": "Shared", "delivered": True},
            {"outlet_id": "outlet-b", "outlet": "Shared", "delivered": False},
            {"contract_id": "known-term", "outlet_id": "outlet-a", "outlet": "Shared", "delivered": False},
        ]
        rows, unscoped = app.media_contract_delivery_history({"outlet_id": "outlet-a", "name": "Shared"}, history)
        self.assertEqual(rows, [history[0]])
        self.assertEqual(unscoped, 0)

    def test_media_account_review_is_scoped_to_active_contract(self):
        app = MediaPlanHarness()
        active = {
            "id": "new", "contract_id": "new", "outlet_id": "outlet-a", "name": "Outlet A",
            "status": "Active", "months": 6, "events_total": 4, "events_remaining": 4,
            "fee": 10_000, "reach": 10,
        }
        app.finance["media_contracts"] = [active]
        app.finance["media_audience_history"] = [
            {"contract_id": "old", "outlet_id": "outlet-a", "delivered": False,
             "event": "Old deal event", "reason": "Old shortfall"},
            {"contract_id": "new", "outlet_id": "outlet-a", "delivered": True,
             "event": "New deal event"},
            {"outlet_id": "outlet-a", "delivered": False, "event": "Legacy event"},
        ]
        app.media_kpi_summary = DetailStub()
        app.media_action_summary = DetailStub()
        app.media_rights_summary = DetailStub()
        app.media_account_review = DetailStub()
        app.media_offers_tree = ReceiptTreeStub()
        app.media_campaign_history_tree = ReceiptTreeStub()
        app.media_desk_fighter = lambda: app.roster[0]
        app.show_selected_media_offer = lambda: None
        app.show_selected_media_campaign = lambda: None
        app.refresh_media_receipts = lambda: None
        app.refresh_media_plan_summary = lambda: None
        app.format_game_date = lambda month, week, include_week=False: f"M{month}"
        app.format_game_date_text = lambda value: str(value)
        before = deepcopy(app.finance)
        app.refresh_media_dashboard()
        self.assertIn("1 delivered / 1 recorded", app.media_account_review.text)
        self.assertIn("1 legacy unscoped row(s) excluded", app.media_account_review.text)
        self.assertNotIn("Old shortfall", app.media_account_review.text)
        self.assertEqual(app.finance, before)

    def test_rights_delivery_uses_disclosed_production_threshold_without_withholding_guarantee(self):
        app = MediaPlanHarness()
        contract = {"id": "rights-2", "name": "Premium Outlet", "status": "Active", "fee": 25_000,
                    "guarantee_per_event": 25_000, "months": 4, "events_remaining": 4,
                    "minimum_rating": 0, "min_card_quality": 0, "min_production": 65}
        event = {"event_id": "event-prod", "name": "Lean Card", "broadcaster": "Coverage", "region": "USA",
                 "production_tier": "Lean", "fights": []}
        outcome = app.calculate_event_media_outcome(event, {"fight_count": 1, "average_excitement": 80, "average_build": 80}, contract=contract)
        self.assertEqual(outcome["production_quality"], 20)
        self.assertFalse(outcome["production_ok"])
        self.assertFalse(outcome["delivered"])
        self.assertIn("below the contracted 65", outcome["reason"])
        self.assertEqual(outcome["rights_income"], 25_000)

    def test_renewal_allows_one_retry_safe_counter_before_acceptance(self):
        app = MediaPlanHarness()
        app.finance["media_contracts"] = [{"id": "rights-counter", "name": "Outlet", "status": "Active", "fee": 18000,
                                            "guarantee_per_event": 18000, "months": 5, "events_total": 5, "events_remaining": 5,
                                            "reach": 22, "relationship": 70}]
        app.sync_legacy_media_rights()
        ok, _text, offer = app.prepare_media_renewal_offer()
        self.assertTrue(ok)
        before = offer["fee"]
        ok, text, result = app.counter_media_renewal_offer(stance="Higher Guarantee", roll=1)
        self.assertTrue(ok, text)
        self.assertEqual(result["status"], "Accepted")
        updated = app.finance["media_successor_offer"]
        self.assertGreater(updated["fee"], before)
        self.assertEqual(updated["fee"], updated["guarantee_per_event"])
        ok, _text, _result = app.counter_media_renewal_offer(stance="Higher Guarantee", roll=1)
        self.assertTrue(ok)

    def test_versioned_sponsor_duty_stays_pending_then_closes_from_evidence(self):
        app = MediaPlanHarness()
        deal = {"agreement_id": "sponsor-1", "name": "Brand", "fee": 5000,
                "activation_requirement": "Event brand placement", "conduct_threshold": 0,
                "duty": {"duty_id": "duty:sponsor-1", "type": "Event brand placement",
                         "period_start": 4, "period_end": 4, "status": "Pending", "evidence": []}}
        app.finance["sponsor_deals"] = [deal]
        event = {"event_id": "event-duty", "name": "Duty Card", "month": 4, "week": 4}
        app.record_media_event_outcome(event, {"outlet": "No rights partner", "rights_income": 0, "delivered": False})
        self.assertEqual(deal["duty"]["status"], "Pending")
        self.assertEqual(len(deal["duty"]["evidence"]), 1)
        app.month = 5
        closed = app.review_sponsor_duties()
        self.assertEqual(len(closed), 1)
        self.assertEqual(deal["duty"]["status"], "Met")
        self.assertEqual(len(app.finance["sponsor_duty_history"]), 1)

    def test_sponsor_preview_fails_closed_for_malformed_legacy_inputs(self):
        app = MediaPlanHarness()
        app.finance["media_public_trust"] = "not-a-number"
        app.finance["sponsor_deals"] = None
        app.finance["media_campaign_history"] = None
        offer = {
            "id": "legacy-sponsor", "name": "Legacy Brand", "category": "Hydration",
            "fee": "unknown", "months": "bad", "fit": None,
            "activation_requirement": "Feature a ranked fighter in campaign media",
            "conduct_threshold": "bad",
        }
        before = deepcopy(app.finance)
        ready, reason = app.sponsor_activation_preview(offer)
        assessment = app.sponsor_offer_assessment(offer)
        self.assertFalse(ready)
        self.assertIn("fighter", reason)
        self.assertEqual(assessment["max_per_event"], 0)
        self.assertEqual(assessment["term_months"], 0)
        self.assertEqual(app.finance, before)

    def test_sponsor_preview_fails_closed_for_nonfinite_legacy_inputs(self):
        app = MediaPlanHarness()
        app.finance["media_public_trust"] = float("nan")
        app.finance["sponsor_deals"] = [{"name": "Existing", "category": "Hydration"}]
        app.company_stability = float("nan")
        offer = {
            "id": "nonfinite-sponsor", "name": "Legacy Brand", "category": "Hydration",
            "fee": float("inf"), "months": float("nan"), "fit": float("inf"),
            "activation_requirement": "Maintain company stability above 45",
            "conduct_threshold": float("inf"),
        }
        before = deepcopy(app.finance)
        ready, _reason = app.sponsor_activation_preview(offer)
        assessment = app.sponsor_offer_assessment(offer)
        self.assertFalse(ready)
        self.assertEqual(assessment["max_per_event"], 0)
        self.assertEqual(assessment["term_months"], 0)
        self.assertEqual(assessment["estimated_per_event"], 0)
        self.assertEqual(app.finance, before)

    def test_ai_media_review_preserves_malformed_saved_offer_and_uses_valid_sibling(self):
        app = MediaPlanHarness()
        promo = type("PromotionStub", (), {})()
        promo.name = "AI Plan FC"
        promo.region = "USA"
        promo.size = 45
        promo.cash = 100_000
        promo.roster = [make_fighter("AI Prospect", "ai-fighter-1")]
        promo.reputation_score = 50
        promo.stability = 55
        promo.strategy = {"current_mode": "Balanced"}
        malformed = {
            "id": "legacy-malformed-offer", "outlet_id": "local_fight_stream",
            "name": "Legacy Outlet", "fee": "unknown", "reach": "bad",
            "min_card_quality": object(), "months": 12, "events_total": 8,
        }
        valid = {
            "id": "valid-offer", "outlet_id": "local_fight_stream",
            "name": "Local Fight Stream", "type": "Streaming", "reach": 16,
            "fee": 12_000, "guarantee_per_event": 12_000, "months": 12,
            "events_total": 8, "events_remaining": 8, "minimum_rating": 36,
            "min_card_quality": 36, "min_production": 20, "exclusivity": "Regional",
            "relationship": 50, "breach_strikes": 0, "performance_bonus": 1_000,
            "termination_fee": 5_000, "status": "Offer",
        }
        promo.finance = {"media_offers": [malformed, valid], "media_last_offer_month": app.month}
        contract = app.review_ai_media_deals(promo)
        self.assertIsNotNone(contract)
        self.assertEqual(contract["id"], "valid-offer")
        self.assertEqual([row["id"] for row in promo.finance["media_offers"]], ["legacy-malformed-offer"])
        self.assertTrue(promo.finance["media_offer_review_required"])
        self.assertIn("legacy-malformed-offer", promo.finance["media_offer_review_ids"])

    def test_media_market_refresh_keeps_malformed_outlet_fields_for_review(self):
        app = MediaPlanHarness()
        malformed_fee = object()
        legacy = {
            "id": "legacy-outlet", "name": "Legacy Broadcaster", "active": True,
            "volatility": "unknown", "budget": "bad", "base_fee": malformed_fee,
        }
        app.media_companies = [legacy]
        app.media_market_last_month = 0
        app.update_media_market()
        self.assertEqual(legacy["volatility"], "unknown")
        self.assertEqual(legacy["budget"], "bad")
        self.assertIs(legacy["base_fee"], malformed_fee)
        self.assertTrue(legacy["market_review_required"])
        self.assertIn("budget", legacy["market_review_reason"])
        self.assertEqual(app.media_market_history[0]["active_outlets"], 1)
        self.assertEqual(app.media_market_history[0]["average_budget"], 0)

    def test_media_offer_expiry_retains_non_dict_and_unknown_expiry_evidence(self):
        app = MediaPlanHarness()
        unknown = {"id": "legacy-unknown-expiry", "name": "Legacy", "expires_month": "unknown"}
        app.finance["media_offers"] = ["legacy raw offer", unknown]
        app.expire_media_offers()
        self.assertEqual(app.finance["media_offers"][0], "legacy raw offer")
        self.assertIs(app.finance["media_offers"][1], unknown)
        self.assertTrue(app.finance["media_offer_review_required"])
        self.assertIn("malformed", app.finance["media_offer_review_reason"])

    def test_accept_media_offer_fails_closed_on_malformed_terms_without_spend(self):
        app = MediaPlanHarness()
        malformed = {
            "id": "malformed-signing", "outlet_id": "local_fight_stream",
            "name": "Legacy Outlet", "fee": "unknown", "reach": 20,
            "months": 12, "events_total": 8,
        }
        app.finance["media_offers"] = [malformed]
        before = repr(app.finance)
        cash = app.cash
        ok, message = app.accept_player_media_offer("malformed-signing")
        self.assertFalse(ok)
        self.assertIn("malformed", message)
        self.assertEqual(app.cash, cash)
        self.assertEqual(app.finance["media_offers"][0], malformed)
        self.assertTrue(app.finance["media_offer_review_required"])
        self.assertNotEqual(repr(app.finance), before)  # review marker is the explicit action evidence

    def test_sponsor_counter_fails_closed_on_malformed_offer_terms(self):
        app = MediaPlanHarness()
        malformed = {"id": "malformed-sponsor", "name": "Legacy Brand", "fee": "bad", "fit": "unknown"}
        app.finance["sponsor_offers"] = [malformed]
        ok, message = app.counter_sponsor_offer("malformed-sponsor", roll=1)
        self.assertFalse(ok)
        self.assertIn("malformed", message)
        self.assertNotIn("negotiated", malformed)
        self.assertIs(app.finance["sponsor_offers"][0], malformed)
        self.assertTrue(malformed["offer_review_required"])

    def test_media_counter_fails_closed_on_malformed_offer_terms(self):
        app = MediaPlanHarness()
        malformed = {
            "id": "malformed-media-counter", "outlet_id": "local_fight_stream",
            "name": "Legacy Outlet", "fee": "bad", "reach": 20,
            "minimum_rating": 40, "min_card_quality": 40, "months": 12,
            "events_total": 8, "relationship": 50, "market_score": 40,
        }
        app.finance["media_offers"] = [malformed]
        ok, message = app.counter_player_media_offer("malformed-media-counter", "Higher Guarantee", roll=1)
        self.assertFalse(ok)
        self.assertIn("malformed", message)
        self.assertNotIn("negotiated", malformed)
        self.assertIs(app.finance["media_offers"][0], malformed)
        self.assertTrue(malformed["offer_review_required"])

    def test_sponsor_deal_envelope_retains_malformed_container_before_repair(self):
        app = MediaPlanHarness()
        app.finance["sponsor_deals"] = {"legacy": "raw"}
        app.ensure_player_media_state()
        self.assertEqual(app.finance["sponsor_deals"], [])
        self.assertEqual(app.finance["sponsor_deals_legacy_raw"], {"legacy": "raw"})

    def test_selected_sponsor_offer_ignores_non_dict_row(self):
        app = MediaPlanHarness()
        app.finance["sponsor_offers"] = ["legacy row"]
        app.sponsor_market_tree = type("Tree", (), {"selection": lambda self: ("legacy row",)})()
        app._sponsor_market_rows = {}
        self.assertIsNone(app.selected_sponsor_offer())

    def test_media_system_keeps_malformed_market_container_as_legacy_evidence(self):
        app = MediaPlanHarness()
        app.media_companies = {"legacy": "raw"}
        app.media_market_last_month = "not-a-month"
        app.ensure_media_system()
        self.assertEqual(app.media_companies_legacy_raw, {"legacy": "raw"})
        self.assertEqual(app.media_market_last_month, 0)
        self.assertTrue(app.media_market_review_required)
        self.assertGreaterEqual(len(app.media_companies), 8)

    def test_media_action_capacity_and_marker_bound_malformed_promotion_values(self):
        app = MediaPlanHarness()
        promo = type("PromotionStub", (), {
            "size": "unknown", "strategy": {"commercial_strength": "bad"},
            "finance": {}, "name": "AI FC", "region": "USA", "reputation_score": 40,
            "stability": 50, "cash": 100_000, "roster": [],
        })()
        self.assertEqual(app.media_action_capacity(promo), 2)
        app.finance["media_action_week"] = "bad"
        app.finance["media_actions_used"] = "unknown"
        self.assertEqual(app.media_actions_remaining(), app.media_action_capacity())

    def test_monthly_sponsor_tick_holds_malformed_terms_and_expires_valid_deals(self):
        app = MediaPlanHarness()
        app.ensure_finance_defaults = lambda: None
        malformed = {"id": "bad-deal", "name": "Legacy Brand", "months": "unknown", "fee": "bad"}
        valid = {"id": "valid-deal", "name": "Current Brand", "months": 1, "fee": 5_000}
        app.finance = {
            "sponsor_deals": [malformed, valid], "media_contracts": [],
            "media_rights": {"name": "No rights package", "months": 0, "fee": 0, "reach": 0},
            "ledger": [],
        }
        WorldMixin.tick_business_deals(app)
        self.assertEqual(app.finance["sponsor_deals"], [malformed])
        self.assertEqual(malformed["months"], "unknown")
        self.assertTrue(malformed["deal_review_required"])
        self.assertIn("expired", app.finance["ledger"][0].lower())

    def test_monthly_media_rights_tick_holds_malformed_legacy_term(self):
        app = MediaPlanHarness()
        app.ensure_finance_defaults = lambda: None
        rights = {"name": "Legacy Outlet", "months": "unknown", "fee": 8_000}
        app.finance = {"sponsor_deals": [], "media_contracts": [], "media_rights": rights, "ledger": []}
        WorldMixin.tick_business_deals(app)
        self.assertIs(app.finance["media_rights"], rights)
        self.assertTrue(rights["contract_review_required"])
        self.assertEqual(rights["months"], "unknown")


if __name__ == "__main__":
    unittest.main()
