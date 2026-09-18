"""Regression coverage for the shared feature foundation contracts."""

import unittest
import random
import inspect
from types import SimpleNamespace

from admin import AdminMixin
from events import EventMixin
from feature_foundation import FoundationMixin
from models import Promotion
from persistence import PersistenceMixin
from views import ViewMixin
from world import WorldMixin


class FoundationHarness(FoundationMixin):
    def __init__(self):
        self.promotions = [Promotion("Alpha", "USA", 2, 100_000, [])]
        self.scheduled_events = [
            {"name": "Legacy Card", "fights": []},
            {"name": "Existing Card", "event_id": "combat-sport-event:Boxing:1:1:1", "fights": []},
        ]
        self.player_combat_divisions = {}
        self.combat_sport_worlds = {}
        self.booked = []
        self.ensure_foundation_state()


class WorldMembershipHarness(FoundationMixin, WorldMixin):
    """Small headless host for transition hooks that do not need a full app."""

    def __init__(self):
        self.promotions = [Promotion("Alpha", "USA", 2, 100_000, [])]
        self.player_company_name = "Player FC"
        self.roster = []
        self.month = 2030
        self.week = 2
        self.story_threads = []
        self.narrative_tracking_enabled = True
        self.ensure_foundation_state()

    def resolve_feeder_pathway_departure(self, *_args):
        return None

    def resolve_crossroads_departure(self, *_args):
        return None


class LineageMigrationHarness(FoundationMixin, AdminMixin, WorldMixin):
    """Minimal load-boundary host for malformed title-history migration."""

    def __init__(self):
        self.player_company_name = "Alpha"
        self.rules = {"lineal_belt_history_version": 0}
        self.promotions = []
        self.free_agents = []
        self.retired_fighters = []
        winner = SimpleNamespace(fighter_id="f-winner", name="Winner", gender="Male", weight="Lightweight")
        loser = SimpleNamespace(fighter_id="f-loser", name="Loser", gender="Male", weight="Lightweight")
        self.roster = [winner, loser]
        self.result_index = [{
            "company": "Alpha", "date": "Month 1 Week 1",
            "bout_results": [{
                "a": "Winner", "b": "Loser", "a_id": "f-winner", "b_id": "f-loser",
                "weight": "Lightweight", "divisional_title": True,
                "result": "Winner def. Loser by Decision",
            }],
        }]
        self.belt_history = {
            "Male Lightweight": [
                "malformed legacy title row",
                {"action": "Vacated", "fighter": "Former Holder", "date": "Month 2 Week 1"},
            ],
        }


class FoundationRegressionTests(unittest.TestCase):
    def test_missing_ids_are_stable_and_existing_ids_are_preserved(self):
        app = FoundationHarness()
        assigned = app.ensure_foundation_ids()
        self.assertEqual(assigned, {"promotion": 1, "event": 1})
        promotion_id = app.promotions[0].promotion_id
        event_id = app.scheduled_events[0]["event_id"]
        self.assertEqual(promotion_id, "promo-000001")
        self.assertEqual(event_id, "event-000001")
        self.assertEqual(app.scheduled_events[1]["event_id"], "combat-sport-event:Boxing:1:1:1")
        self.assertEqual(app.ensure_foundation_ids(), {"promotion": 0, "event": 0})
        self.assertEqual(app.promotions[0].promotion_id, promotion_id)
        self.assertEqual(app.scheduled_events[0]["event_id"], event_id)

    def test_idempotent_commit_and_atomic_restore(self):
        app = FoundationHarness()
        state = {"cash": 100}
        quote = app.foundation_quote("media", "buy", "offer-1", amount=25)
        receipt = app.foundation_commit(
            "media:offer-1", domain="media", action="buy", target_id="offer-1", quote=quote,
            validate=lambda: state["cash"] >= 25,
            snapshot=lambda: dict(state),
            restore=lambda old: state.update(old),
            apply=lambda: state.__setitem__("cash", state["cash"] - 25),
        )
        self.assertEqual(receipt["status"], "committed")
        self.assertEqual(state["cash"], 75)
        retry = app.foundation_commit(
            "media:offer-1", domain="media", action="buy", target_id="offer-1",
            apply=lambda: state.__setitem__("cash", 0),
        )
        self.assertEqual(retry["operation_id"], receipt["operation_id"])
        self.assertEqual(state["cash"], 75)

        failed = app.foundation_commit(
            "media:offer-2", domain="media", action="buy", target_id="offer-2",
            snapshot=lambda: dict(state),
            restore=lambda old: state.update(old),
            apply=lambda: (_ for _ in ()).throw(RuntimeError("gateway unavailable")),
        )
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(state["cash"], 75)

    def test_partial_rows_resume_only_unattempted_rows(self):
        app = FoundationHarness()
        attempts = []

        def apply(row, _index):
            attempts.append(row["id"])
            if row["id"] == "b" and attempts.count("b") == 1:
                raise RuntimeError("temporary")
            return row["id"]

        rows = [{"id": "a"}, {"id": "b"}]
        first = app.foundation_commit_rows("staff:batch", rows, domain="staff", action="assign", row_id=lambda row, _i: row["id"], apply=apply)
        self.assertEqual([item["status"] for item in first], ["committed", "failed"])
        second = app.foundation_commit_rows("staff:batch", rows, domain="staff", action="assign", row_id=lambda row, _i: row["id"], apply=apply)
        self.assertEqual([item["status"] for item in second], ["committed", "committed"])
        self.assertEqual(attempts, ["a", "b", "b"])

    def test_historical_archive_is_bounded_and_paged(self):
        app = FoundationHarness()
        for index in range(5):
            app.foundation_append_historical("rankings", {"round": index}, max_items=3)
        self.assertEqual(app.foundation_historical_page("rankings", offset=0, limit=10), [{"round": 2}, {"round": 3}, {"round": 4}])

    def test_work_cards_normalize_status_and_are_observational(self):
        app = FoundationHarness()
        app.foundation_record_work(
            "staff:brief-1", domain="staff", action="review", target_id="event-1",
            status="committed", quote={"amount": 250},
            result={"evidence_key": "evidence-1", "spend": 400},
        )
        app.foundation_record_work(
            "media:brief-2", domain="media", action="review", target_id="event-2",
            status="rejected", error="Target departed", quote={"amount": 500},
        )
        before = repr(app._foundation_state)
        cards = app.foundation_work_cards(domain="staff")
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["status_label"], "Completed")
        self.assertEqual(cards[0]["evidence_key"], "evidence-1")
        self.assertEqual(cards[0]["actual_spend"], 400)
        self.assertEqual(cards[0]["amount_state"], "Recorded")
        self.assertEqual(cards[0]["actual_spend_state"], "Recorded")
        self.assertEqual(app.foundation_work_summary()["counts"]["rejected"], 1)
        cards[0]["status_label"] = "changed"
        self.assertEqual(repr(app._foundation_state), before)

    def test_work_card_unknown_status_and_status_filter_remain_explicit(self):
        app = FoundationHarness()
        app.foundation_record_work("x", domain="staff", action="review", status="needs_attention")
        card = app.foundation_work_cards(statuses=("needs_attention",))[0]
        self.assertEqual(card["status_label"], "Needs Attention")
        self.assertEqual(app.foundation_work_cards(statuses=("committed",)), [])

    def test_malformed_work_receipt_remains_readable_without_normalising_state(self):
        app = FoundationHarness()
        app._foundation_state["operations"] = {
            "op-malformed": {
                "operation_id": "op-malformed", "domain": "staff",
                "action": "review", "status": "committed", "attempt": "bad",
                "quote": {"amount": "bad"}, "result": {"spend": "bad"},
            }
        }
        before = repr(app._foundation_state)
        cards = app.foundation_work_cards()
        self.assertEqual(cards[0]["attempt"], 0)
        self.assertEqual(cards[0]["amount"], 0)
        self.assertEqual(cards[0]["actual_spend"], 0)
        self.assertEqual(cards[0]["amount_state"], "Unknown")
        self.assertEqual(cards[0]["actual_spend_state"], "Unknown")
        self.assertIn("quoted amount is malformed", cards[0]["diagnostics"])
        self.assertIn("actual spend is malformed", cards[0]["diagnostics"])
        self.assertEqual(repr(app._foundation_state), before)

    def test_booking_ids_are_event_scoped_stable_and_rng_free(self):
        app = FoundationHarness()
        app.scheduled_events[0]["fights"] = [{"fighters": ["A", "B"]}, {"fighters": ["C", "D"]}]
        app.booked = [{"fighters": ["E", "F"]}]
        before_rng = random.getstate()
        self.assertEqual(app.ensure_foundation_ids(), {"promotion": 1, "event": 1})
        after_rng = random.getstate()
        self.assertEqual(before_rng, after_rng)
        first = [fight["booking_id"] for fight in app.scheduled_events[0]["fights"]]
        draft = app.booked[0]["booking_id"]
        self.assertEqual(first, ["booking:event-000001:1", "booking:event-000001:2"])
        self.assertEqual(draft, "booking:draft:1")
        self.assertEqual(app.ensure_booking_ids(), 0)
        self.assertEqual([fight["booking_id"] for fight in app.scheduled_events[0]["fights"]], first)
        self.assertEqual(app.booked[0]["booking_id"], draft)

    def test_duplicate_booking_ids_are_repaired_without_touching_event_identity(self):
        app = FoundationHarness()
        app.scheduled_events[0]["fights"] = [{"booking_id": "same"}, {"booking_id": "same"}]
        app.ensure_foundation_ids()
        ids = [fight["booking_id"] for fight in app.scheduled_events[0]["fights"]]
        self.assertEqual(ids, ["same", "booking:event-000001:2"])
        self.assertEqual(app.scheduled_events[0]["event_id"], "event-000001")

    def test_membership_events_are_id_linked_deduplicated_and_rng_free(self):
        app = FoundationHarness()
        app.player_company_name = "Player FC"
        fighter = SimpleNamespace(fighter_id="f-1", name="Fighter One")
        app.ensure_foundation_ids()
        before_rng = random.getstate()
        before_counters = dict(app.ensure_foundation_state()["counters"])

        first = app.record_membership_event(
            fighter, "join", company_name="Alpha", effective_month=2030,
            effective_week=2, reason="Contract signing",
            source_transaction="contract-signing:f-1:Alpha:2030:2",
        )
        self.assertEqual(random.getstate(), before_rng)
        self.assertEqual(first["fighter_id"], "f-1")
        self.assertEqual(first["fighter_name"], "Fighter One")
        self.assertEqual(first["action"], "join")
        self.assertEqual(first["promotion_id"], "promo-000001")
        self.assertEqual(first["effective_month"], 2030)
        self.assertEqual(first["effective_week"], 2)
        self.assertEqual(dict(app.ensure_foundation_state()["counters"]), before_counters)

        retry = app.record_membership_event(
            fighter, "join", company_name="Alpha", effective_month=2030,
            effective_week=2, reason="A changed display reason must not rewrite history",
            source_transaction="contract-signing:f-1:Alpha:2030:2",
        )
        self.assertEqual(retry, first)
        self.assertEqual(len(app.foundation_membership_events()), 1)

        leave = app.record_membership_event(
            fighter, "leave", company_name="Player FC", effective_month=2031,
            effective_week=9, precision="month", reason="Retired",
            source_transaction="retirement:f-1:Player FC:2031:1",
        )
        self.assertEqual(leave["promotion_id"], "promo-000002")
        self.assertEqual(leave["effective_week"], 4)
        self.assertEqual(leave["date_precision"], "month")
        self.assertEqual(len(app.foundation_membership_events(fighter_id="f-1", action="leave")), 1)
        self.assertEqual(len(app.foundation_membership_events(promotion_id="promo-000001")), 1)

    def test_membership_event_reads_are_paged_defensive_and_preserve_unknown_fields(self):
        app = FoundationHarness()
        fighter = SimpleNamespace(fighter_id="f-2", name="Fighter Two")
        app.record_membership_event(fighter, "join", company_name="Alpha", source_transaction="one")
        app.record_membership_event(fighter, "leave", company_name="Alpha", source_transaction="two")
        app.ensure_foundation_state()["historical"]["collections"]["membership"][0]["future_field"] = {"kept": True}

        page = app.foundation_membership_events(fighter_id="f-2", offset=1, limit=1)
        self.assertEqual(len(page), 1)
        self.assertEqual(page[0]["action"], "leave")
        page[0]["action"] = "changed"
        self.assertEqual(app.foundation_membership_events(fighter_id="f-2", offset=0, limit=1)[0]["action"], "join")
        app.ensure_foundation_state()
        self.assertEqual(
            app.ensure_foundation_state()["historical"]["collections"]["membership"][0]["future_field"],
            {"kept": True},
        )

    def test_contract_transition_hooks_capture_membership_before_story_work(self):
        app = WorldMembershipHarness()
        fighter = SimpleNamespace(
            fighter_id="f-3", name="Fighter Three", champion=False,
            interim_champion=False, popularity=0, overall=0,
        )
        app.record_contract_signing(fighter, "Alpha", source="New contract")
        app.record_contract_exit(fighter, "Alpha", reason="Contract expiry")
        rows = app.foundation_membership_events(fighter_id="f-3")
        self.assertEqual([row["action"] for row in rows], ["join", "leave"])
        self.assertTrue(all(row["promotion_id"] == "promo-000001" for row in rows))
        self.assertTrue(all(row["source_transaction"] for row in rows))

    def test_current_roster_migration_marks_presence_without_inventing_join_date(self):
        app = FoundationHarness()
        app.player_company_name = "Player FC"
        app.roster = [SimpleNamespace(fighter_id="f-player", name="Player Fighter")]
        app.promotions[0].roster = [SimpleNamespace(fighter_id="f-alpha", name="Alpha Fighter")]
        before_rng = random.getstate()
        captured = app.migrate_current_membership_presence()
        self.assertEqual(captured, 2)
        self.assertEqual(random.getstate(), before_rng)
        rows = app.foundation_membership_events()
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["action"] == "join" for row in rows))
        self.assertTrue(all(row["date_precision"] == "migration" for row in rows))
        self.assertTrue(all(row["effective_month"] is None and row["effective_week"] is None for row in rows))
        self.assertTrue(all("Known present at migration" in row["reason"] for row in rows))
        self.assertEqual(app.migrate_current_membership_presence(), 0)
        self.assertEqual(len(app.foundation_membership_events()), 2)

    def test_membership_intervals_are_a_read_only_as_of_projection(self):
        app = FoundationHarness()
        fighter = SimpleNamespace(fighter_id="f-4", name="Fighter Four")
        app.record_membership_event(
            fighter, "join", company_name="Alpha", effective_month=4,
            effective_week=1, source_transaction="join-4-1",
        )
        app.record_membership_event(
            fighter, "leave", company_name="Alpha", effective_month=6,
            effective_week=2, source_transaction="leave-6-2",
        )
        app.record_membership_event(
            fighter, "join", company_name="Alpha", effective_month=8,
            effective_week=1, source_transaction="return-8-1",
        )
        before = repr(app._foundation_state)
        intervals = app.foundation_membership_intervals(fighter_id="f-4")
        self.assertEqual(len(intervals), 2)
        self.assertEqual((intervals[0]["start_month"], intervals[0]["end_month"]), (4, 6))
        self.assertEqual(intervals[0]["coverage"], "complete")
        self.assertTrue(intervals[0]["start_membership_id"].startswith("membership-"))
        self.assertTrue(intervals[0]["end_membership_id"].startswith("membership-"))
        self.assertIsNone(intervals[1]["end_month"])
        self.assertEqual(len(app.foundation_membership_intervals(fighter_id="f-4", as_of_month=5, as_of_week=1)), 1)
        self.assertEqual(repr(app._foundation_state), before)

    def test_membership_intervals_keep_same_week_boundaries_without_merging(self):
        app = FoundationHarness()
        fighter = SimpleNamespace(fighter_id="f-same-week", name="Same Week")
        app.record_membership_event(
            fighter, "join", company_name="Alpha", effective_month=7,
            effective_week=2, source_transaction="same-week-join-1",
        )
        app.record_membership_event(
            fighter, "leave", company_name="Alpha", effective_month=7,
            effective_week=2, source_transaction="same-week-leave-1",
        )
        app.record_membership_event(
            fighter, "return", company_name="Alpha", effective_month=7,
            effective_week=2, source_transaction="same-week-return-1",
        )
        before = repr(app._foundation_state)
        intervals = app.foundation_membership_intervals(fighter_id=fighter.fighter_id)
        self.assertEqual(len(intervals), 2)
        self.assertEqual(
            [(row["start_month"], row["start_week"], row["end_month"], row["end_week"])
             for row in intervals],
            [(7, 2, 7, 2), (7, 2, None, None)],
        )
        self.assertEqual(intervals[0]["temporal_order"], "ordered")
        self.assertEqual(
            len(app.foundation_membership_intervals(
                fighter_id=fighter.fighter_id, as_of_month=7, as_of_week=2,
            )),
            1,
        )
        self.assertEqual(repr(app._foundation_state), before)

    def test_membership_intervals_label_out_of_order_or_malformed_dates(self):
        app = FoundationHarness()
        fighter = SimpleNamespace(fighter_id="f-conflict", name="Conflict")
        app._foundation_state["historical"]["collections"]["membership"] = [
            {"membership_id": "m-join", "promotion_id": "promo-1", "promotion_name": "Alpha",
             "fighter_id": fighter.fighter_id, "fighter_name": fighter.name, "action": "join",
             "effective_month": 10, "effective_week": 1, "date_precision": "week",
             "source_transaction": "join-late"},
            {"membership_id": "m-leave", "promotion_id": "promo-1", "promotion_name": "Alpha",
             "fighter_id": fighter.fighter_id, "fighter_name": fighter.name, "action": "leave",
             "effective_month": 5, "effective_week": 4, "date_precision": "week",
             "source_transaction": "leave-early"},
        ]
        before = repr(app._foundation_state)
        conflict = app.foundation_membership_intervals(fighter_id=fighter.fighter_id)
        self.assertEqual(conflict[0]["temporal_order"], "conflict")
        self.assertEqual(conflict[0]["coverage"], "incomplete")
        self.assertIn("precedes", conflict[0]["coverage_note"])
        self.assertEqual(len(app.foundation_membership_intervals(
            fighter_id=fighter.fighter_id, as_of_month=1, as_of_week=1,
        )), 1)
        app._foundation_state["historical"]["collections"]["membership"][1]["effective_month"] = "unknown"
        before_malformed = repr(app._foundation_state)
        malformed = app.foundation_membership_intervals(fighter_id=fighter.fighter_id)
        self.assertEqual(malformed[0]["temporal_order"], "unknown")
        self.assertEqual(malformed[0]["coverage"], "incomplete")
        self.assertEqual(repr(app._foundation_state), before_malformed)
        self.assertNotEqual(before, before_malformed)

    def test_membership_intervals_reject_boolean_float_and_bad_week_dates(self):
        app = FoundationHarness()
        fighter = SimpleNamespace(fighter_id="f-date-types", name="Date Types")
        app._foundation_state["historical"]["collections"]["membership"] = [
            {"membership_id": "m-bool", "promotion_id": "promo-1", "promotion_name": "Alpha",
             "fighter_id": fighter.fighter_id, "fighter_name": fighter.name, "action": "join",
             "effective_month": True, "effective_week": 1, "date_precision": "week"},
            {"membership_id": "m-float", "promotion_id": "promo-1", "promotion_name": "Alpha",
             "fighter_id": fighter.fighter_id, "fighter_name": fighter.name, "action": "leave",
             "effective_month": 4.5, "effective_week": "late", "date_precision": "week"},
        ]
        before = repr(app._foundation_state)
        rows = app.foundation_membership_intervals(fighter_id=fighter.fighter_id)
        self.assertEqual(rows[0]["coverage"], "incomplete")
        self.assertEqual(rows[0]["temporal_order"], "unknown")
        self.assertIn("malformed", rows[0]["coverage_note"])
        self.assertEqual(repr(app._foundation_state), before)

    def test_membership_retention_summary_reports_gaps_without_normalising(self):
        app = FoundationHarness()
        app.record_membership_event(
            SimpleNamespace(fighter_id="f-retained", name="Retained"), "join",
            company_name="Alpha", effective_month=10, effective_week=2,
            source_transaction="retained-join",
        )
        app.record_membership_event(
            SimpleNamespace(fighter_id="f-retained", name="Retained"), "leave",
            company_name="Alpha", precision="migration",
            source_transaction="retained-leave-unknown",
        )
        before = repr(app._foundation_state)
        summary = app.foundation_membership_retention_summary()
        self.assertEqual(summary["retained_rows"], 2)
        self.assertEqual(summary["known_date_rows"], 1)
        self.assertEqual(summary["unknown_date_rows"], 1)
        self.assertEqual(summary["fighter_count"], 1)
        self.assertEqual(summary["duplicate_membership_ids"], 0)
        self.assertTrue(summary["within_limit"])
        self.assertEqual(repr(app._foundation_state), before)

    def test_membership_reader_does_not_normalise_malformed_history(self):
        app = FoundationHarness()
        app._foundation_state = {
            "schema_version": "legacy", "historical": {"collections": "not-a-dictionary"},
            "operations": [],
        }
        before = repr(app._foundation_state)
        self.assertEqual(app.foundation_membership_events(), [])
        self.assertEqual(app.foundation_membership_intervals(fighter_id="missing"), [])
        summary = app.foundation_membership_retention_summary()
        self.assertFalse(summary["available"])
        self.assertEqual(summary["coverage"], "unavailable")
        self.assertIn("unavailable", summary["threshold_notice"].lower())
        self.assertEqual(repr(app._foundation_state), before)

    def test_membership_readers_fail_closed_for_malformed_paging_and_as_of_inputs(self):
        app = FoundationHarness()
        fighter = SimpleNamespace(fighter_id="f-reader-inputs", name="Reader Inputs")
        app.record_membership_event(
            fighter, "join", company_name="Alpha", effective_month=3,
            effective_week=2, source_transaction="reader-inputs",
        )
        before = repr(app._foundation_state)
        self.assertEqual(
            len(app.foundation_membership_events(fighter_id=fighter.fighter_id, offset="bad", limit=float("nan"))),
            1,
        )
        self.assertEqual(
            len(app.foundation_membership_intervals(
                fighter_id=fighter.fighter_id, as_of_month="bad", as_of_week=float("inf"), limit="bad",
            )),
            0,
        )
        self.assertEqual(repr(app._foundation_state), before)

    def test_membership_retention_summary_marks_malformed_collection_unavailable(self):
        app = FoundationHarness()
        app._foundation_state = {
            "schema_version": 1,
            "historical": {"collections": {"membership": {"legacy": "rows"}}},
            "operations": [],
        }
        before = repr(app._foundation_state)
        summary = app.foundation_membership_retention_summary()
        self.assertFalse(summary["available"])
        self.assertEqual(summary["coverage"], "unavailable")
        self.assertEqual(summary["retained_rows"], 0)
        self.assertIn("load/migration", summary["threshold_notice"])
        self.assertEqual(repr(app._foundation_state), before)

    def test_membership_retention_summary_marks_malformed_historical_envelope_unavailable(self):
        app = FoundationHarness()
        app._foundation_state = {
            "schema_version": 1, "historical": ["not", "an", "envelope"],
            "operations": [],
        }
        before = repr(app._foundation_state)
        summary = app.foundation_membership_retention_summary()
        self.assertFalse(summary["available"])
        self.assertEqual(summary["coverage"], "unavailable")
        self.assertIn("malformed", summary["threshold_notice"].lower())
        self.assertEqual(repr(app._foundation_state), before)

    def test_membership_retention_summary_does_not_count_blank_legacy_ids_as_duplicates(self):
        app = FoundationHarness()
        app._foundation_state["historical"]["collections"]["membership"] = [
            {"membership_id": "", "fighter_id": "legacy-1", "action": "join"},
            {"membership_id": "", "fighter_id": "legacy-2", "action": "join"},
            {"membership_id": "m-1", "fighter_id": "f-1", "action": "join"},
            {"membership_id": "m-1", "fighter_id": "f-2", "action": "join"},
        ]
        summary = app.foundation_membership_retention_summary()
        self.assertEqual(summary["retained_rows"], 4)
        self.assertEqual(summary["unique_membership_ids"], 1)
        self.assertEqual(summary["duplicate_membership_ids"], 1)
        self.assertEqual(summary["idless_rows"], 2)

    def test_membership_retention_summary_marks_malformed_month_as_unknown_date(self):
        app = FoundationHarness()
        app._foundation_state["historical"]["collections"]["membership"] = [
            {"membership_id": "m-valid", "fighter_id": "f-1", "action": "join", "effective_month": "8"},
            {"membership_id": "m-bad", "fighter_id": "f-1", "action": "leave", "effective_month": "unknown"},
            {"membership_id": "m-none", "fighter_id": "f-1", "action": "return", "effective_month": None},
        ]
        summary = app.foundation_membership_retention_summary()
        self.assertEqual(summary["known_date_rows"], 1)
        self.assertEqual(summary["unknown_date_rows"], 2)
        self.assertEqual(summary["oldest_known_month"], 8)
        self.assertEqual(summary["newest_known_month"], 8)

    def test_membership_retention_summary_counts_malformed_rows_without_repairing(self):
        app = FoundationHarness()
        app._foundation_state["historical"]["collections"]["membership"] = [
            {"membership_id": "m-valid", "fighter_id": "f-1", "action": "join", "effective_month": 8},
            "legacy malformed membership row",
            None,
        ]
        before = repr(app._foundation_state)
        summary = app.foundation_membership_retention_summary()
        self.assertEqual(summary["retained_rows"], 3)
        self.assertEqual(summary["valid_rows"], 1)
        self.assertEqual(summary["malformed_rows"], 2)
        self.assertEqual(len(app.foundation_membership_events()), 1)
        self.assertEqual(repr(app._foundation_state), before)

    def test_membership_history_never_silently_discards_rows_over_review_threshold(self):
        app = FoundationHarness()
        target = SimpleNamespace(fighter_id="f-over-limit", name="Long Career")
        for index in range(10001):
            app.record_membership_event(
                target, "join" if index == 0 else "leave",
                company_name="Alpha", effective_month=index + 1,
                effective_week=1, source_transaction=f"over-limit-{index}",
            )

        rows = app.foundation_membership_events(fighter_id=target.fighter_id, offset=10000, limit=1)
        summary = app.foundation_membership_retention_summary()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_transaction"], "over-limit-10000")
        self.assertEqual(summary["retained_rows"], 10001)
        self.assertFalse(summary["within_limit"])
        self.assertIn("all membership facts are retained", summary["threshold_notice"])
        self.assertEqual(len(app.foundation_membership_intervals(fighter_id=target.fighter_id, limit=20000)), 10000)

    def test_membership_event_count_walks_all_pages_without_mutating_history(self):
        app = FoundationHarness()
        target = SimpleNamespace(fighter_id="f-count", name="Long Career")
        for index in range(1001):
            app.record_membership_event(
                target, "join" if index == 0 else "leave",
                company_name="Alpha", effective_month=index + 1,
                effective_week=1, source_transaction=f"count-{index}",
            )
        before = repr(app._foundation_state)
        self.assertEqual(app.foundation_membership_event_count(fighter_id=target.fighter_id), 1001)
        self.assertEqual(repr(app._foundation_state), before)

    def test_lineal_title_migration_preserves_malformed_legacy_rows(self):
        app = LineageMigrationHarness()
        result = app.migrate_lineal_belt_histories()
        self.assertEqual(result["updated"], 1)
        rows = app.belt_history["Male Lightweight"]
        self.assertIn("malformed legacy title row", rows)
        self.assertTrue(any(
            isinstance(row, dict) and row.get("action") == "Inaugural Champion"
            and row.get("fighter") == "Winner"
            for row in rows
        ))
        self.assertEqual(app.rules["lineal_belt_history_version"], 1)

    def test_lineal_title_rebuild_keeps_winner_identity_for_same_names(self):
        app = LineageMigrationHarness()
        target = SimpleNamespace(fighter_id="f-target", name="Same Name", gender="Male", weight="Lightweight")
        namesake = SimpleNamespace(fighter_id="f-namesake", name="Same Name", gender="Male", weight="Lightweight")
        opponent = SimpleNamespace(fighter_id="f-opponent", name="Opponent", gender="Male", weight="Lightweight")
        app.roster = [target, namesake, opponent]
        app.result_index = [{
            "company": "Alpha", "date": "Month 3 Week 1",
            "bout_results": [{
                "a": target.name, "b": opponent.name,
                "a_id": target.fighter_id, "b_id": opponent.fighter_id,
                "winner": target.name, "winner_id": target.fighter_id,
                "weight": "Lightweight", "divisional_title": True,
                "result": f"{target.name} def. {opponent.name} by Decision",
            }],
        }]

        rebuilt = app.rebuild_lineal_belt_histories_from_results()
        row = rebuilt["Alpha"]["Male Lightweight"][0]
        self.assertEqual(row["fighter"], target.name)
        self.assertEqual(row["fighter_id"], target.fighter_id)
        self.assertEqual(row["opponent_id"], opponent.fighter_id)

    def test_lineal_title_rebuild_skips_ambiguous_legacy_winner_names(self):
        app = LineageMigrationHarness()
        app.roster = [
            SimpleNamespace(fighter_id="f-a", name="Same Name", gender="Male", weight="Lightweight"),
            SimpleNamespace(fighter_id="f-b", name="Same Name", gender="Male", weight="Lightweight"),
            SimpleNamespace(fighter_id="f-opponent", name="Opponent", gender="Male", weight="Lightweight"),
        ]
        app.result_index = [{
            "company": "Alpha", "date": "Month 3 Week 1",
            "bout_results": [{
                "a": "Same Name", "b": "Opponent",
                "weight": "Lightweight", "divisional_title": True,
                "result": "Same Name def. Opponent by Decision",
            }],
        }]

        rebuilt = app.rebuild_lineal_belt_histories_from_results()
        self.assertEqual(rebuilt, {})

    def test_lineal_title_migration_keeps_same_text_rows_with_distinct_ids(self):
        app = LineageMigrationHarness()
        app.belt_history["Male Lightweight"] = [
            "malformed legacy title row",
            {"action": "Vacated", "fighter": "Former Holder", "fighter_id": "f-former-a",
             "date": "Month 2 Week 1", "note": "same retained note"},
            {"action": "Vacated", "fighter": "Former Holder", "fighter_id": "f-former-b",
             "date": "Month 2 Week 1", "note": "same retained note"},
        ]

        result = app.migrate_lineal_belt_histories()

        self.assertEqual(result["updated"], 1)
        vacated = [
            row for row in app.belt_history["Male Lightweight"]
            if isinstance(row, dict) and row.get("action") == "Vacated"
        ]
        self.assertEqual({row.get("fighter_id") for row in vacated}, {"f-former-a", "f-former-b"})

    def test_membership_hooks_cover_real_departure_and_transfer_paths(self):
        paths = (
            (WorldMixin, "retire_after_final_fight_if_due"),
            (WorldMixin, "update_ai_contracts"),
            (WorldMixin, "review_ai_roster_cuts"),
            (WorldMixin, "distressed_promotion_buyout"),
            (WorldMixin, "review_ai_upgrade_replacements"),
            (WorldMixin, "move_regional_fighter_to_free_agency"),
            (WorldMixin, "exercise_academy_matching_right"),
            (ViewMixin, "remove_fighter_from_active_database"),
            (ViewMixin, "commit_player_transfer_deal"),
            (ViewMixin, "close_selected_division"),
            (EventMixin, "open_contract_negotiation"),
            (PersistenceMixin, "reconcile_closed_player_division_roster"),
            (PersistenceMixin, "reconcile_closed_ai_division_rosters"),
            (PersistenceMixin, "repair_player_scheduled_fighter_references"),
        )
        for owner, method in paths:
            with self.subTest(path=f"{owner.__name__}.{method}"):
                source = inspect.getsource(getattr(owner, method))
                self.assertTrue(
                    "record_membership_event" in source
                    or "record_contract_exit" in source,
                    f"{owner.__name__}.{method} must emit a membership departure fact",
                )
                if method in {
                    "close_selected_division",
                    "reconcile_closed_player_division_roster",
                    "reconcile_closed_ai_division_rosters",
                }:
                    self.assertIn("vacate_fighter_belts", source)
                    roster_mutation = "self.roster = [fighter for fighter in self.roster if fighter not in released]" if "player_division" in method else (
                        "self.roster = [fighter for fighter in self.roster if fighter not in fighters]" if method == "close_selected_division" else
                        "promo.roster = [fighter for fighter in promo.roster if fighter not in released]"
                    )
                    self.assertLess(source.index("vacate_fighter_belts"), source.index(roster_mutation))

    def test_membership_hooks_capture_both_sides_of_child_and_market_transfers(self):
        loan = inspect.getsource(WorldMixin.loan_fighter_to_child_promotion)
        recall = inspect.getsource(WorldMixin.recall_fighter_from_child_promotion)
        transfer = inspect.getsource(WorldMixin.take_fighter_from_child_promotion)
        market = inspect.getsource(EventMixin.sign_fighter)
        automatic_tba = inspect.getsource(EventMixin.find_tba_replacement)
        replacement = inspect.getsource(EventMixin.commit_last_minute_replacement)
        swap = inspect.getsource(ViewMixin.commit_player_transfer_deal)
        contract_window = inspect.getsource(EventMixin.open_contract_negotiation)
        self.assertIn('membership(fighter, "loan"', loan)
        self.assertIn('membership(fighter, "join"', loan)
        self.assertIn('membership(fighter, "leave"', recall)
        self.assertIn('membership(fighter, "return"', recall)
        self.assertIn('membership(fighter, "leave"', transfer)
        self.assertIn('membership(fighter, "join"', transfer)
        self.assertIn("record_contract_signing", market)
        self.assertIn("record_contract_signing", automatic_tba)
        self.assertIn("record_contract_signing", replacement)
        self.assertIn('target, "join"', swap)
        self.assertIn("proposal_update", contract_window)
        self.assertLess(
            market.index('membership = getattr(self, "record_membership_event", None)'),
            market.index("self.free_agents.remove(fighter)"),
        )
        self.assertLess(
            automatic_tba.index('membership = getattr(self, "record_membership_event", None)'),
            automatic_tba.index("self.free_agents.remove(replacement)"),
        )
        self.assertLess(
            replacement.index('membership = getattr(self, "record_membership_event", None)'),
            replacement.index("self.free_agents.remove(candidate)"),
        )
        self.assertLess(
            contract_window.index('membership = getattr(self, "record_membership_event", None)'),
            contract_window.index("source_promotion.roster.remove(fighter)"),
        )
        self.assertIn("comeback-signing", contract_window)
        self.assertLess(
            contract_window.index('source_transaction=f"comeback-signing'),
            contract_window.index("self.retired_fighters.remove(fighter)"),
        )
        restore = inspect.getsource(PersistenceMixin.repair_player_scheduled_fighter_references)
        self.assertLess(
            restore.index('membership = getattr(self, "record_membership_event", None)'),
            restore.index("self.free_agents.remove(fighter)"),
        )

    def test_membership_hooks_cover_intake_and_recruitment_boundaries(self):
        checks = (
            (WorldMixin, "graduate_rival_academy_prospect", "promo.roster.append(fighter)"),
            (WorldMixin, "seed_child_promotion_roster", "self.free_agents.remove(fighter)"),
            (WorldMixin, "seed_opening_ai_division_depth", "self.free_agents.remove(fighter)"),
            (WorldMixin, "_promote_academy_prospect_to_sport", "self.roster.append(fighter)"),
            (WorldMixin, "simulate_ai_promotion_month", "promo.roster.append(prospect)"),
            (WorldMixin, "spawn_annual_regional_wonderkid", "promo.roster.append(fighter)"),
            (WorldMixin, "move_regional_fighter_to_free_agency", "promo.roster.remove(fighter)"),
        )
        for owner, method, mutation in checks:
            with self.subTest(path=f"{owner.__name__}.{method}"):
                source = inspect.getsource(getattr(owner, method))
                self.assertIn('membership = getattr(self, "record_membership_event", None)', source)
                self.assertLess(
                    source.index('membership = getattr(self, "record_membership_event", None)'),
                    source.index(mutation),
                )

    def test_ai_upgrade_rollback_records_return_before_restoring_incumbent(self):
        source = inspect.getsource(WorldMixin.review_ai_upgrade_replacements)
        self.assertIn('source_transaction=f"ai-upgrade-rollback:', source)
        rollback = source.split("if not signed:", 1)[1].split("free_agents.remove(incoming)", 1)[0]
        self.assertIn('incumbent, "return"', rollback)
        self.assertLess(
            rollback.index('incumbent, "return"'),
            rollback.index("promo.roster.append(incumbent)"),
        )

    def test_ai_free_agent_signing_records_company_join_before_roster_move(self):
        app = WorldMembershipHarness()
        promo = app.promotions[0]
        promo.promotion_id = "promo-ai"
        promo.cash = 2_000_000
        promo.roster = []
        fighter = SimpleNamespace(
            fighter_id="f-ai-join", name="AI Signer", gender="Male", weight="Lightweight",
            retired=False, retirement_pending=False, injured=False, purse=20_000,
            contract_months=0, exclusive=False, contract_type="Free Agent",
            free_agent_months=2, champion=False, interim_champion=False, morale=60,
            ai_offer_company="", ai_offer_purse=0, ai_offer_months=0,
            ai_offer_signing_bonus=0, ai_offer_deadline_month=0,
        )
        app.free_agents = [fighter]
        app.news = []
        app.promotion_division_open = lambda *_args: True
        app.ai_roster_cap = lambda *_args: 100
        app.ai_financial_roster_target = lambda *_args: 50
        app.ai_division_target = lambda *_args: 20
        app.ai_contract_reserve = lambda *_args: 0
        app.record_promotion_finance_transaction = lambda *_args, **_kwargs: None
        app.record_world_story = lambda *_args, **_kwargs: None
        app.record_promotion_era_story = lambda *_args, **_kwargs: None
        app.record_contract_signing = lambda *_args, **_kwargs: None
        observed = []
        original_membership = app.record_membership_event

        def observe_membership(*args, **kwargs):
            observed.append((fighter in app.free_agents, fighter in promo.roster))
            return original_membership(*args, **kwargs)

        app.record_membership_event = observe_membership
        ok, message = app.complete_ai_free_agent_signing(
            fighter, promo, purse=22_000, months=12, signing_bonus=30_000,
        )
        self.assertTrue(ok, message)
        self.assertEqual(observed, [(True, False)])
        self.assertNotIn(fighter, app.free_agents)
        self.assertIn(fighter, promo.roster)
        rows = app.foundation_membership_events(fighter_id=fighter.fighter_id, action="join")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["promotion_id"], promo.promotion_id)
        self.assertIn("ai-signing", rows[0]["source_transaction"])

    def test_company_proposals_are_identity_linked_append_only_and_retry_safe(self):
        app = FoundationHarness()
        app.player_company_name = "Player FC"
        app.month = 2030
        app.week = 2
        source = app.promotions[0]
        outgoing = SimpleNamespace(fighter_id="f-out", name="Outgoing", gender="Male", weight="Lightweight")
        incoming = SimpleNamespace(fighter_id="f-in", name="Incoming", gender="Male", weight="Lightweight")
        before_rng = random.getstate()
        before_counters = dict(app.ensure_foundation_state()["counters"])
        kwargs = dict(
            source_company=app.player_company_name, source_company_id="player-1",
            target_company=source.name, target_company_id=source.promotion_id,
            fighters=[{"fighter_id": outgoing.fighter_id, "fighter_name": outgoing.name, "role": "outgoing"},
                      {"fighter_id": incoming.fighter_id, "fighter_name": incoming.name, "role": "incoming"}],
            costs={"cash": 25000, "currency": "USD"},
            expiry={"month": 2031, "week": 1, "label": "Next boundary"},
            warnings=["Remain unbooked"],
            terms={"transfer_type": "swap"},
        )
        first = app.create_company_proposal("fighter_swap", **kwargs)
        retry = app.create_company_proposal("fighter_swap", **kwargs)
        self.assertEqual(first["proposal_id"], retry["proposal_id"])
        self.assertEqual(len(app.foundation_historical_page("company_proposals", limit=10)), 1)
        self.assertEqual(random.getstate(), before_rng)
        self.assertEqual(dict(app.ensure_foundation_state()["counters"]), before_counters)

        countered = app.update_company_proposal(first["proposal_id"], "countered", outcome="Board requested more cash.", terms={"last_counter_cash": 40000})
        self.assertEqual(countered["status"], "countered")
        committed = app.update_company_proposal(first["proposal_id"], "committed", outcome="Accepted once.", terms={"commit_cash": 40000})
        duplicate = app.update_company_proposal(first["proposal_id"], "committed", outcome="Accepted once.", terms={"commit_cash": 40000})
        self.assertEqual(duplicate["proposal_revision"], committed["proposal_revision"])
        altered_retry = app.update_company_proposal(
            first["proposal_id"], "committed", outcome="A different final message.",
            terms={"new_field": "must not overwrite terminal evidence"},
        )
        self.assertEqual(altered_retry, committed)
        cards = app.company_proposal_read_model()
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["status_label"], "Completed")
        self.assertEqual(cards[0]["fighters"][0]["fighter_id"], "f-out")
        cards[0]["terms"]["changed"] = True
        self.assertNotIn("changed", app.company_proposal_read_model()[0]["terms"])

    def test_company_proposal_reader_does_not_normalise_malformed_history(self):
        app = FoundationHarness()
        app._foundation_state = {
            "schema_version": "legacy",
            "historical": {"collections": {"company_proposals": "not-a-list"}},
            "operations": [],
        }
        before = repr(app._foundation_state)
        self.assertEqual(app.company_proposal_read_model(), [])
        self.assertEqual(app.company_proposal_read_model(proposal_id="missing"), [])
        self.assertEqual(repr(app._foundation_state), before)

    def test_child_company_proposal_snapshots_parent_and_child_without_mechanics(self):
        app = WorldMembershipHarness()
        child = Promotion("Alpha Development", "USA", 1, 50_000, [])
        app.promotions.append(child)
        app.ensure_foundation_ids()
        fighter = SimpleNamespace(
            fighter_id="f-child", name="Child Prospect", gender="Female", weight="Strawweight",
            champion=False, interim_champion=False, retired=False, injured=False,
            retirement_pending=False, purse=5000, popularity=20,
        )
        before_rng = random.getstate()
        proposal = app.prepare_child_company_proposal("development_loan", child, fighter)
        self.assertEqual(proposal["kind"], "development_loan")
        self.assertEqual((proposal["source_company"], proposal["target_company"]), ("Player FC", "Alpha Development"))
        self.assertEqual(proposal["fighters"][0]["fighter_id"], "f-child")
        self.assertEqual(proposal["costs"]["cash"], 0)
        self.assertIn("Open until the parent recalls the loan", proposal["expiry"]["label"])
        self.assertEqual(random.getstate(), before_rng)
        self.assertEqual(fighter.name, "Child Prospect")


if __name__ == "__main__":
    unittest.main()
