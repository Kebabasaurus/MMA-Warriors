"""Regression coverage for super-event terms and terminal closeout paths."""

import unittest
from types import SimpleNamespace

from awards import AwardsMixin


class Value:
    def __init__(self, value=""):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class SuperEventHarness(AwardsMixin):
    def __init__(self):
        self.month, self.week = 1, 1
        self.cash = 50_000
        self.player_company_name = "Player FC"
        self.company_pop = 70
        self.company_stability = 70
        self.company_safety = 70
        self.finance_transactions = []
        self.news = []
        self.super_event_offers = []
        self.super_event_history = []
        self.super_event_project = None
        self.event_name, self.venue = Value(), Value()
        self.event_region, self.event_city = Value(), Value()

    def record_finance_transaction(self, label, revenue=0, costs=0, **_kwargs):
        self.finance_transactions.append({"label": label, "revenue": revenue, "costs": costs})

    def set_booking_date(self, month, week):
        self.booking_date = (month, week)

    def format_game_date(self, month, week):
        return f"W{week} M{month}"


class SuperEventCloseoutTests(unittest.TestCase):
    def test_super_event_readers_use_saved_fighter_ids_and_fail_closed_for_duplicate_names(self):
        app = SuperEventHarness()
        first = SimpleNamespace(fighter_id="fighter-a", name="Same Name", popularity=80, star_quality=75)
        second = SimpleNamespace(fighter_id="fighter-b", name="Same Name", popularity=20, star_quality=20)
        app.resolve_fighter = lambda reference: {
            "fighter-a": first,
            "fighter-b": second,
        }.get(str(reference))
        app.booked = [{
            "fighters": ["Same Name", "Same Name"],
            "fighter_ids": ["fighter-a", "fighter-b"],
            "title": False,
        }]
        offer = {"reserve": 1, "min_fights": 1, "min_titles": 0, "min_stars": 1, "venue": "Arena"}
        app.available_event_venues = lambda: ["Arena"]
        readiness = app.super_event_readiness(offer)
        self.assertEqual(readiness["stars"], 1)
        app.booked = [{"fighters": ["Same Name", "Same Name"], "fighter_ids": [], "title": False}]
        self.assertEqual(app.super_event_readiness(offer)["stars"], 0)
        self.assertIn("1 recognisable stars", app.validate_super_event_card(offer, app.booked))

    def test_offer_ui_identity_uses_saved_id_and_deterministic_legacy_suffixes(self):
        saved = {"id": "SE-1", "name": "Grand Prix"}
        duplicate = {"id": "SE-1", "name": "Grand Prix (copy)"}
        legacy = {
            "name": "Legacy Showcase", "kind": "Record", "venue": "Arena",
            "deadline_month": 8, "issued_month": 1, "status": "Offered",
        }
        used = set()
        first = AwardsMixin.super_event_offer_ui_identity(saved, used_ids=used)
        second = AwardsMixin.super_event_offer_ui_identity(duplicate, used_ids=used)
        legacy_first = AwardsMixin.super_event_offer_ui_identity(legacy, used_ids=set())
        legacy_again = AwardsMixin.super_event_offer_ui_identity(legacy, used_ids=set())
        self.assertEqual(first, "super-event:SE-1")
        self.assertEqual(second, "super-event:SE-1#2")
        self.assertEqual(legacy_first, legacy_again)
        self.assertEqual(saved, {"id": "SE-1", "name": "Grand Prix"})

    def test_record_book_identity_does_not_depend_on_sorted_row_position(self):
        used = set()
        world = AwardsMixin.historical_record_ui_identity("World", "Most Career Wins", used_ids=used)
        promotion = AwardsMixin.historical_record_ui_identity("Promotion", "Most Career Wins", used_ids=used)
        duplicate = AwardsMixin.historical_record_ui_identity("World", "Most Career Wins", used_ids=used)
        self.assertEqual(world, "record:world:Most Career Wins")
        self.assertEqual(promotion, "record:promotion:Most Career Wins")
        self.assertEqual(duplicate, "record:world:Most Career Wins#2")

    def test_achievement_identity_preserves_duplicate_target_rows(self):
        used = set()
        entry = {"id": "title-win", "target": "Champion", "scope": "Fighter"}
        duplicate = dict(entry)
        first = AwardsMixin.achievement_ui_identity(entry, used_ids=used)
        second = AwardsMixin.achievement_ui_identity(duplicate, used_ids=used)
        self.assertEqual(first, "achievement:title-win:Champion")
        self.assertEqual(second, "achievement:title-win:Champion#2")

    def test_transition_matrix_keeps_approval_and_scheduling_boundaries(self):
        allowed = AwardsMixin.super_event_transition_allowed
        self.assertTrue(allowed("Offered", "Planning"))
        self.assertTrue(allowed("Planning", "Scheduled"))
        self.assertTrue(allowed("Scheduled", "Success"))
        self.assertTrue(allowed("Scheduled", "Failed"))
        self.assertFalse(allowed("Offered", "Scheduled"))
        self.assertFalse(allowed("Planning", "Completed"))
        self.assertFalse(allowed("Completed", "Cancelled"))

    def test_new_acceptance_maps_terms_once_and_keeps_template_evidence(self):
        app = SuperEventHarness()
        offer = {
            "id": "SE-1", "name": "Grand Prix", "kind": "Special Format", "status": "Offered",
            "deposit": 1_000, "setup": 4_000, "security": 2_000, "revenue": 1.25,
            "reserve": 20_000, "earliest_month": 3, "deadline_month": 8,
            "venue": "Regional Arena", "region": "USA", "city": "Las Vegas",
        }
        app.super_event_offers = [offer]
        ok, message = app.accept_super_event_offer(offer)
        self.assertTrue(ok, message)
        self.assertEqual(app.cash, 49_000)
        self.assertEqual(offer["status"], "Planning")
        self.assertEqual(offer["security_cost"], 2_000)
        self.assertEqual(offer["revenue_multiplier"], 1.25)
        self.assertEqual(offer["remaining_setup_cost"], 4_000)
        self.assertEqual(offer["accepted_terms"]["template"]["security"], 2_000)
        self.assertEqual(offer["accepted_terms"]["canonical"]["security_cost"], 2_000)
        self.assertTrue(offer["deposit_payment_reference"].startswith("super-event-approval:SE-1:"))
        commitment = app.super_event_commitment_snapshot(offer)
        self.assertEqual(commitment["paid_total"], 1_000)
        self.assertEqual(commitment["sunk_total"], 1_000)
        self.assertEqual(commitment["unpaid_total"], 6_000)
        self.assertEqual(commitment["refundable_total"], 0)
        self.assertEqual(len(app.finance_transactions), 1)

    def test_planning_expiry_is_terminal_and_idempotent(self):
        app = SuperEventHarness()
        offer = {
            "id": "SE-2", "name": "Record Attempt", "kind": "Record", "status": "Planning",
            "deadline_month": 4, "accepted_month": 1, "deposit": 5_000, "terms_version": 2,
        }
        app.month = 5
        app.super_event_offers = [offer]
        app.super_event_project = offer
        app.expire_super_event_offers()
        self.assertEqual(app.super_event_history[0]["outcome"], "Expired")
        self.assertEqual(app.super_event_project, None)
        self.assertEqual(app.super_event_offers, [])
        app.expire_super_event_offers()
        self.assertEqual(len(app.super_event_history), 1)

    def test_expiry_revision_conflict_keeps_live_offer_for_review(self):
        app = SuperEventHarness()
        app.month = 5
        offer = {
            "id": "SE-stale-expiry", "name": "Stale Planning Card", "status": "Planning",
            "deadline_month": 4, "accepted_month": 1, "project_revision": 1,
            "deposit": 2_000,
        }
        live_project = dict(offer, project_revision=2)
        app.super_event_offers = [offer]
        app.super_event_project = live_project
        app.expire_super_event_offers()
        self.assertEqual(app.super_event_history, [])
        self.assertEqual(len(app.super_event_offers), 1)
        self.assertIs(app.super_event_offers[0], offer)
        self.assertEqual(offer["status"], "Planning")
        self.assertIn("revision", offer.get("closeout_review", "").lower())
        self.assertIs(app.super_event_project, live_project)

    def test_offered_expiry_records_zero_commitment_terminal_once(self):
        app = SuperEventHarness()
        app.month = 5
        offer = {
            "id": "SE-offered-expiry", "name": "Missed Invitation", "status": "Offered",
            "deadline_month": 4, "issued_month": 1, "deposit": 3_000,
        }
        app.super_event_offers = [offer]
        app.expire_super_event_offers()
        self.assertEqual(len(app.super_event_history), 1)
        self.assertEqual(app.super_event_history[0]["outcome"], "Expired")
        self.assertEqual(app.super_event_history[0]["deposit_paid"], 0)
        self.assertEqual(app.super_event_history[0]["commitment"]["paid_total"], 0)
        self.assertEqual(app.super_event_offers, [])
        safety_after_first = app.company_safety
        app.expire_super_event_offers()
        self.assertEqual(len(app.super_event_history), 1)
        self.assertEqual(app.company_safety, safety_after_first)

    def test_scheduled_cancellation_closes_only_matching_project(self):
        app = SuperEventHarness()
        offer = {"id": "SE-3", "name": "Historic Night", "status": "Scheduled", "accepted_month": 1, "deposit": 8_000}
        app.super_event_offers = [offer]
        first = app.close_super_event_project(offer, outcome="Cancelled", reason="Card cancelled.", event_name="Historic Night")
        second = app.close_super_event_project(offer, outcome="Cancelled", reason="Clicked twice.", event_name="Historic Night")
        self.assertEqual(first, second)
        self.assertEqual(first["reason"], "Card cancelled.")
        self.assertEqual(first["deposit_paid"], 8_000)
        self.assertEqual(first["state"], "Cancelled")
        self.assertEqual(first["settlement_key"], "super-event:SE-3:terminal")
        self.assertEqual(first["commitment"]["paid_total"], 8_000)
        self.assertEqual(first["commitment"]["unpaid_total"], 0)
        self.assertEqual(first["commitment"]["refundable_total"], 0)
        self.assertEqual(len(app.super_event_history), 1)
        self.assertEqual(app.super_event_offers, [])

    def test_legacy_closeout_keeps_manual_refund_review_and_is_idempotent(self):
        app = SuperEventHarness()
        legacy = {
            "name": "Legacy Showcase", "status": "Planning", "accepted_month": 1,
            "deposit": 2_000, "setup": 5_000, "security": 1_000,
        }
        first = app.close_super_event_project(legacy, outcome="Expired", reason="Legacy deadline")
        second = app.close_super_event_project(legacy, outcome="Expired", reason="Retry")
        self.assertEqual(first, second)
        self.assertTrue(first["id"].startswith("legacy-super-event:Legacy Showcase:1"))
        self.assertIn("Manual review", first["commitment"]["refund_status"])
        self.assertEqual(first["settlement_key"], f"super-event:{first['id']}:terminal")

    def test_stale_terminal_offer_cannot_apply_a_second_closeout(self):
        app = SuperEventHarness()
        offer = {
            "id": "SE-terminal", "name": "Already Closed", "status": "Cancelled",
            "accepted_month": 1, "deposit": 8_000,
        }
        before = (app.cash, list(app.super_event_history), list(app.super_event_offers))
        result = app.close_super_event_project(offer, outcome="Expired", reason="stale retry")
        self.assertTrue(result["already_terminal"])
        self.assertEqual(result["outcome"], "Cancelled")
        self.assertEqual((app.cash, app.super_event_history, app.super_event_offers), before)

    def test_completion_rejects_non_scheduled_event_without_effects(self):
        app = SuperEventHarness()
        event = {"super_event": {"id": "SE-cancelled", "name": "Cancelled Card", "status": "Cancelled"}}
        package = {
            "event_name": "Cancelled Card", "profit": 100_000, "average_excitement": 90,
            "finance": {"attendance": 10_000, "venue_capacity": 10_000},
        }
        before = (app.company_pop, app.company_stability, app.company_safety, list(app.super_event_history))
        self.assertIsNone(app.complete_super_event(event, package))
        self.assertEqual((app.company_pop, app.company_stability, app.company_safety, app.super_event_history), before)

    def test_successful_completion_uses_completed_state_and_is_idempotent(self):
        app = SuperEventHarness()
        app.record_world_story = lambda *_args, **_kwargs: None
        offer = {
            "id": "SE-success", "name": "Successful Card", "kind": "Special Format",
            "status": "Scheduled", "reward": 4, "accepted_month": 1,
            "deposit": 1_000, "setup": 2_000, "security_cost": 500,
            "terms_version": 2, "project_revision": 2,
        }
        event = {"super_event": offer}
        package = {
            "event_name": "Successful Card", "profit": 100_000,
            "average_excitement": 90,
            "finance": {"attendance": 10_000, "venue_capacity": 10_000},
        }
        first = app.complete_super_event(event, package)
        self.assertEqual(first["outcome"], "Success")
        self.assertEqual(first["state"], "Completed")
        before = (app.company_pop, app.company_stability, app.company_safety, len(app.super_event_history))
        second = app.complete_super_event(event, package)
        self.assertEqual(second, first)
        self.assertEqual((app.company_pop, app.company_stability, app.company_safety, len(app.super_event_history)), before)

    def test_completion_closeout_review_blocks_derived_effects(self):
        app = SuperEventHarness()
        offer = {
            "id": "SE-review", "name": "Review Required", "kind": "Special Format",
            "status": "Scheduled", "reward": 4, "project_revision": 2,
        }
        event = {"super_event": offer}
        package = {
            "event_name": "Review Card", "profit": 100_000,
            "average_excitement": 90,
            "finance": {"attendance": 10_000, "venue_capacity": 10_000},
        }
        before = (app.company_pop, app.company_stability, app.company_safety,
                  list(app.news), list(app.super_event_history))
        app.close_super_event_project = lambda *_args, **_kwargs: {
            "id": "SE-review", "outcome": "Needs review", "state": "Needs review",
            "needs_review": True, "reason": "stale completion copy",
        }
        result = app.complete_super_event(event, package)
        self.assertTrue(result["needs_review"])
        self.assertEqual(
            (app.company_pop, app.company_stability, app.company_safety,
             app.news, app.super_event_history),
            before,
        )

    def test_revision_mismatch_fails_closed_without_clearing_the_live_offer(self):
        app = SuperEventHarness()
        app.super_event_offers = [{
            "id": "SE-revision", "name": "Changed Card", "status": "Scheduled",
            "project_revision": 3, "deposit": 1_000,
        }]
        stale = {
            "id": "SE-revision", "name": "Changed Card", "status": "Scheduled",
            "project_revision": 2, "deposit": 1_000,
        }
        before = (list(app.super_event_offers), list(app.super_event_history), app.cash)
        result = app.close_super_event_project(stale, outcome="Cancelled")
        self.assertTrue(result["needs_review"])
        self.assertIn("revision", result["reason"].lower())
        self.assertEqual((app.super_event_offers, app.super_event_history, app.cash), before)

    def test_status_mismatch_fails_closed_even_when_revision_matches(self):
        app = SuperEventHarness()
        app.super_event_offers = [{
            "id": "SE-status", "name": "Rescheduled Card", "status": "Cancelled",
            "project_revision": 4, "deposit": 1_000,
        }]
        stale = {
            "id": "SE-status", "name": "Rescheduled Card", "status": "Scheduled",
            "project_revision": 4, "deposit": 1_000,
        }
        before = (list(app.super_event_offers), list(app.super_event_history))
        result = app.close_super_event_project(stale, outcome="Cancelled")
        self.assertTrue(result["needs_review"])
        self.assertIn("state", result["reason"].lower())
        self.assertEqual((app.super_event_offers, app.super_event_history), before)

    def test_malformed_legacy_terms_close_without_crashing_or_inventing_money(self):
        app = SuperEventHarness()
        offer = {
            "id": "SE-malformed-terms", "name": "Legacy Terms", "status": "Planning",
            "accepted_month": 1, "deposit": "unknown", "setup": "unknown",
            "security": "unknown", "terms_version": "old-format",
        }
        app.super_event_offers = [offer]
        result = app.close_super_event_project(offer, outcome="Cancelled", reason="Review legacy terms")
        self.assertEqual(result["outcome"], "Cancelled")
        self.assertEqual(result["deposit_paid"], 0)
        self.assertEqual(result["terms_version"], 1)
        self.assertEqual(result["commitment"]["planned_components"]["approval_deposit"], 0)
        self.assertEqual(len(app.super_event_history), 1)

    def test_malformed_settlement_evidence_fails_closed_before_project_effects(self):
        app = SuperEventHarness()
        offer = {
            "id": "SE-malformed-package", "name": "Malformed Result", "status": "Scheduled",
            "project_revision": 1, "reward": 4,
        }
        event = {"super_event": offer}
        package = {
            "event_name": "Malformed Result", "profit": "unknown",
            "average_excitement": 90,
            "finance": {"attendance": "unknown", "venue_capacity": 10_000},
        }
        before = (app.company_pop, app.company_stability, app.company_safety,
                  list(app.news), list(app.super_event_history))
        result = app.complete_super_event(event, package)
        self.assertTrue(result["needs_review"])
        self.assertIn("malformed", result["reason"].lower())
        self.assertEqual(
            (app.company_pop, app.company_stability, app.company_safety,
             app.news, app.super_event_history),
            before,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
