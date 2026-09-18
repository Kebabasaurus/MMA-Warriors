"""Regression coverage for the deterministic J1 booking workbench slice."""

import json
import random
import unittest
from types import SimpleNamespace

from booking_workbench import BookingWorkbenchMixin
from feature_foundation import FoundationMixin


def fighter(fid, name, *, gender="Male", weight="Lightweight", overall=60,
            popularity=40, fatigue=0, injured=False, champion=False, age=28,
            record_w=8, record_l=3):
    row = SimpleNamespace(
        fighter_id=fid, name=name, gender=gender, weight=weight, overall=overall,
        popularity=popularity, fatigue=fatigue, injured=injured, champion=champion,
        interim_champion=False, retired=False, retirement_pending=False, age=age,
        record_w=record_w, record_l=record_l, record_d=0, record=f"{record_w}-{record_l}-0",
        ranking_position=0, owed_title_shot=False, title_shot_clause=False,
        available_week=0, available_day=0, momentum=0, elo_rating=overall,
    )
    return row


class Harness(BookingWorkbenchMixin, FoundationMixin):
    def __init__(self):
        self.month, self.week = 3, 2
        self.closed_divisions = set()
        self.booked = []
        self.roster = [
            fighter("f-1", "Anchor", overall=68, popularity=48),
            fighter("f-2", "Close Rival", overall=66, popularity=45),
            fighter("f-3", "Injured Rival", overall=64, popularity=35, injured=True),
            fighter("f-4", "Wrong Class", weight="Welterweight", overall=65),
            fighter("f-5", "Fresh Alternative", overall=67, popularity=43),
        ]
        self.ensure_booking_workbench_state()
        self.ensure_foundation_state()

    def resolve_fighter(self, reference):
        return next((row for row in self.roster if row.fighter_id == str(reference)), None)

    def fighter_identity_key(self, row):
        return row.fighter_id

    def fighter_available_for_date(self, row, month=None, week=None, day=None):
        return not row.injured

    def fighter_has_scheduled_fight(self, row, include_booked=False):
        return any(row.fighter_id in fight.get("fighter_ids", []) for fight in self.booked)

    def belt_key(self, gender, weight):
        return f"{gender}:{weight}"

    def player_division_rank_map(self):
        ordered = sorted(
            (row for row in self.roster if row.weight == "Lightweight" and row.gender == "Male"),
            key=lambda row: row.overall, reverse=True,
        )
        return {row.fighter_id: (0 if row.champion else index) for index, row in enumerate(ordered, 1)}

    def unfiltered_ranked_fighter_rows(self):
        return [("Player", row) for row in self.roster]

    def division_rank_maps(self, rows):
        world = {}
        for index, (_company, row) in enumerate(sorted(rows, key=lambda item: item[1].overall, reverse=True), 1):
            world[row.fighter_id] = f"#{index}"
        return {}, world

    def matchmaking_score(self, a, b, rank_map=None):
        return 80 - abs(a.overall - b.overall), "close ability gap"

    def matchmaking_fit_score(self, a, b):
        return max(1, 99 - abs(a.overall - b.overall) * 3)

    def match_build_score(self, a, b, fight, rank_map=None):
        return round((a.popularity + b.popularity) / 2)

    def assistant_pair_booking_warning(self, a, b, rank_map=None, target_month=None):
        return "wide ranking gap" if abs(a.overall - b.overall) >= 8 else ""

    def normalize_card_order(self):
        for index, fight in enumerate(self.booked):
            fight["main"] = index == 0


class BookingWorkbenchTests(unittest.TestCase):
    def test_generation_is_explicit_deterministic_and_separates_blocks(self):
        app = Harness()
        ok, _message, brief = app.save_booking_workbench_brief("f-1", emphasis="Sporting", opposition_gap=1)
        self.assertTrue(ok)
        before_rng = random.getstate()
        ok, _message, proposal = app.generate_booking_proposal("f-1", 4, 1)
        self.assertTrue(ok)
        self.assertEqual(before_rng, random.getstate())
        self.assertEqual(proposal["brief_id"], brief["brief_id"])
        rows = {row["fighter_id"]: row for row in proposal["options"]}
        self.assertEqual(rows["f-2"]["generation_status"], "Eligible")
        self.assertIn("injured", " ".join(rows["f-3"]["hard_blocks"]))
        self.assertIn("different weight class", " ".join(rows["f-4"]["hard_blocks"]))
        self.assertTrue(rows["f-2"]["cautions"], "brief range should remain an advisory caution")

    def test_review_marks_changed_option_stale_without_rewriting_snapshot(self):
        app = Harness()
        _ok, _message, proposal = app.generate_booking_proposal("f-1", 4, 1)
        original = json.loads(json.dumps(proposal["options"]))
        app.roster[1].injured = True
        review = app.review_booking_proposal(proposal["proposal_id"])
        row = next(item for item in review["options"] if item["fighter_id"] == "f-2")
        self.assertEqual(row["current_status"], "Blocked")
        self.assertEqual(proposal["options"], original)

    def test_fill_uses_one_receipt_and_repeat_returns_it(self):
        app = Harness()
        _ok, _message, proposal = app.generate_booking_proposal("f-1", 4, 1)
        option_index = next(index for index, row in enumerate(proposal["options"]) if row["fighter_id"] == "f-2")
        ok, _message, first = app.commit_booking_proposal(proposal["proposal_id"], option_index)
        self.assertTrue(ok)
        self.assertEqual(len(app.booked), 1)
        self.assertEqual(first["status"], "committed")
        ok, message, second = app.commit_booking_proposal(proposal["proposal_id"], option_index)
        self.assertTrue(ok)
        self.assertIn("already committed", message)
        self.assertEqual(first["operation_id"], second["operation_id"])
        self.assertEqual(len(app.booked), 1)

    def test_identity_commit_resolves_saved_fighter_after_option_order_changes(self):
        app = Harness()
        _ok, _message, proposal = app.generate_booking_proposal("f-1", 4, 1)
        state = app.ensure_booking_workbench_state()
        saved = next(row for row in state["proposals"] if row["proposal_id"] == proposal["proposal_id"])
        saved["options"] = list(reversed(saved["options"]))
        ok, message, receipt = app.commit_booking_proposal_for_fighter(proposal["proposal_id"], "f-2")
        self.assertTrue(ok, message)
        self.assertEqual(receipt["status"], "committed")
        self.assertEqual(app.booked[0]["fighter_ids"], ["f-1", "f-2"])

    def test_identity_commit_fails_closed_on_duplicate_saved_fighter_ids(self):
        app = Harness()
        _ok, _message, proposal = app.generate_booking_proposal("f-1", 4, 1)
        state = app.ensure_booking_workbench_state()
        saved = next(row for row in state["proposals"] if row["proposal_id"] == proposal["proposal_id"])
        saved["options"].append(dict(saved["options"][0]))
        ok, message, receipt = app.commit_booking_proposal_for_fighter(proposal["proposal_id"], saved["options"][0]["fighter_id"])
        self.assertFalse(ok)
        self.assertIn("duplicate", message)
        self.assertIsNone(receipt)
        self.assertEqual(app.booked, [])

    def test_medical_preview_is_factual_and_rng_pure(self):
        app = Harness()
        before = json.loads(json.dumps(app.booking_workbench, default=str))
        before_rng = random.getstate()
        preview = app.booking_workbench_medical_preview("f-3", 4, 1)
        self.assertEqual(preview["status"], "Medical hold")
        self.assertIn("injured", preview["medical_blocks"])
        self.assertFalse(preview["binding"])
        self.assertIn("no camp reserved", preview["camp"])
        self.assertEqual(before_rng, random.getstate())
        self.assertEqual(before, json.loads(json.dumps(app.booking_workbench, default=str)))

    def test_tentative_medical_slot_is_persisted_without_booking_or_reservation(self):
        app = Harness()
        before_roster = [(row.fighter_id, row.injured, getattr(row, "camp_weeks", None)) for row in app.roster]
        before_booked = json.loads(json.dumps(app.booked))
        before_rng = random.getstate()
        ok, message, plan = app.save_tentative_medical_slot("f-1", "f-3", 4, 1)
        self.assertTrue(ok)
        self.assertIn("not a booking", message)
        self.assertEqual(plan["status"], "Tentative")
        self.assertFalse(plan["binding"])
        self.assertEqual(len(app.booking_workbench_medical_plans()), 1)
        self.assertEqual(before_roster, [(row.fighter_id, row.injured, getattr(row, "camp_weeks", None)) for row in app.roster])
        self.assertEqual(before_booked, app.booked)
        self.assertEqual(before_rng, random.getstate())
        ok, repeat_message, repeat = app.save_tentative_medical_slot("f-1", "f-3", 4, 1)
        self.assertTrue(ok)
        self.assertIn("already exists", repeat_message)
        self.assertEqual(repeat["plan_id"], plan["plan_id"])
        self.assertEqual(len(app.booking_workbench_medical_plans()), 1)

    def test_medical_draft_review_is_current_read_model_and_expires(self):
        app = Harness()
        _ok, _message, plan = app.save_tentative_medical_slot("f-1", "f-3", 4, 1)
        app.roster[2].injured = False
        ready = app.review_tentative_medical_slot(plan["plan_id"])
        self.assertEqual(ready["current_status"], "Ready to confirm")
        app.month, app.week = 5, 1
        expired = app.review_tentative_medical_slot(plan["plan_id"])
        self.assertEqual(expired["current_status"], "Needs replacement")
        self.assertEqual(app.booking_workbench_medical_plans()[0]["status"], "Tentative")

    def test_review_readers_do_not_normalize_malformed_workbench_envelope(self):
        app = Harness()
        app.booking_workbench = {
            "schema_version": "legacy", "brief": "not-a-brief",
            "proposals": "not-a-list", "locked_slot_proposals": {"raw": True},
            "medical_plans": "not-a-list", "future_field": {"keep": 1},
        }
        before = json.loads(json.dumps(app.booking_workbench))
        self.assertIsNone(app.booking_workbench_brief_snapshot())
        self.assertEqual(app.booking_workbench_medical_plans(), [])
        self.assertIsNone(app.review_booking_proposal("missing"))
        self.assertIsNone(app.review_locked_slot_proposal("missing"))
        self.assertEqual(app.booking_workbench, before)

    def test_proposal_review_keeps_medical_snapshot_and_adds_current_preview(self):
        app = Harness()
        _ok, _message, proposal = app.generate_booking_proposal("f-1", 4, 1)
        option = next(row for row in proposal["options"] if row["fighter_id"] == "f-3")
        stored_status = option["medical_preview"]["status"]
        app.roster[2].injured = False
        review = app.review_booking_proposal(proposal["proposal_id"])
        row = next(item for item in review["options"] if item["fighter_id"] == "f-3")
        self.assertEqual(row["medical_preview"]["status"], stored_status)
        self.assertEqual(row["current_medical_preview"]["status"], "Ready to confirm")

    def test_draft_review_separates_preserved_pairings_and_unresolved_slots(self):
        app = Harness()
        app.booked = [
            {"booking_id": "bout-7", "fighter_ids": ["f-1", "f-2"], "fighters": ["Anchor", "Close Rival"], "title": True, "tier": "Main Card"},
            {"fighter_ids": ["f-1", "TBA"], "fighters": ["Anchor", "TBA"], "title": False, "tier": "Prelims"},
        ]
        before = json.loads(json.dumps(app.booked))
        snapshot = app.booking_workbench_draft_snapshot()
        self.assertEqual(snapshot["locked_existing_bout_ids"], ["bout-7"])
        self.assertEqual(len(snapshot["unresolved_slots"]), 1)
        self.assertTrue(snapshot["unresolved_slots"][0].startswith("legacy-slot:"))
        self.assertEqual(
            snapshot["unresolved_slots"][0],
            app.booking_workbench_draft_snapshot()["unresolved_slots"][0],
        )
        self.assertEqual(snapshot["rows"][0]["identity_status"], "Stable")
        self.assertEqual(snapshot["rows"][1]["identity_status"], "Legacy reference")
        self.assertEqual(snapshot["rows"][1]["status"], "Needs opponent")
        self.assertEqual(app.booked, before)
        self.assertEqual(app.booked[0]["booking_id"], before[0]["booking_id"])
        self.assertEqual(app.booked[0]["fighter_ids"], before[0]["fighter_ids"])
        self.assertEqual(app.booked[1]["fighter_ids"], before[1]["fighter_ids"])
        self.assertEqual(app.booked[1]["fighters"], before[1]["fighters"])

    def test_locked_slot_proposal_is_explicit_stable_and_preserves_card_until_commit(self):
        app = Harness()
        app.booked = [
            {"fighter_ids": ["f-1", "f-2"], "fighters": ["Anchor", "Close Rival"],
             "title": True, "tier": "Main Card", "main": True,
             "fight_plans": {"f-1": "Balanced", "f-2": "Aggressive"}},
            {"fighter_ids": ["f-3", "f-4"], "fighters": ["Injured Rival", "Wrong Class"], "tier": "Prelims"},
        ]
        before_rng = random.getstate()
        before_second = json.loads(json.dumps(app.booked[1]))
        ok, message, proposal = app.generate_locked_slot_proposal("booking:draft:1", 1, 4, 1)
        self.assertTrue(ok, message)
        self.assertEqual(proposal["proposal_kind"], "locked_slot")
        self.assertEqual(proposal["original_fighter_ids"], ["f-1", "f-2"])
        self.assertEqual(before_rng, random.getstate())
        self.assertEqual(app.booked[0]["fighter_ids"], ["f-1", "f-2"])
        self.assertEqual(app.booked[1]["fighter_ids"], before_second["fighter_ids"])
        self.assertEqual(app.booked[1]["fighters"], before_second["fighters"])
        self.assertEqual(app.booked[1]["tier"], before_second["tier"])
        option_index = next(index for index, row in enumerate(proposal["options"]) if row["fighter_id"] == "f-5")
        review = app.review_locked_slot_proposal(proposal["proposal_id"])
        self.assertEqual(review["current_status"], "Draft")
        self.assertEqual(review["options"][option_index]["current_status"], "Eligible")
        ok, message, receipt = app.commit_locked_slot_proposal(proposal["proposal_id"], option_index)
        self.assertTrue(ok, message)
        self.assertEqual(receipt["status"], "committed")
        self.assertEqual(app.booked[0]["fighter_ids"], ["f-1", "f-5"])
        self.assertEqual(app.booked[0]["fighters"], ["Anchor", "Fresh Alternative"])
        self.assertTrue(app.booked[0]["title"])
        self.assertEqual(app.booked[0]["tier"], "Main Card")
        self.assertEqual(app.booked[0]["replacement_history"][0]["removed_fighter_id"], "f-2")
        self.assertEqual(app.booked[0]["replacement_history"][0]["replacement_fighter_id"], "f-5")
        self.assertEqual(app.booked[1]["fighter_ids"], before_second["fighter_ids"])
        self.assertEqual(app.booked[1]["fighters"], before_second["fighters"])
        self.assertEqual(app.booked[1]["tier"], before_second["tier"])
        ok, _message, repeat = app.commit_locked_slot_proposal(proposal["proposal_id"], option_index)
        self.assertTrue(ok)
        self.assertEqual(receipt["operation_id"], repeat["operation_id"])

    def test_locked_slot_rejects_stale_card_without_mutation(self):
        app = Harness()
        app.booked = [{"fighter_ids": ["f-1", "f-2"], "fighters": ["Anchor", "Close Rival"], "title": False}]
        _ok, _message, proposal = app.generate_locked_slot_proposal("booking:draft:1", 0, 4, 1)
        original = json.loads(json.dumps(app.booked))
        app.booked[0]["tier"] = "Main Event"
        review = app.review_locked_slot_proposal(proposal["proposal_id"])
        self.assertEqual(review["current_status"], "Stale")
        option_index = next(index for index, row in enumerate(proposal["options"]) if row["fighter_id"] == "f-5")
        ok, message, receipt = app.commit_locked_slot_proposal(proposal["proposal_id"], option_index)
        self.assertFalse(ok)
        self.assertIn("changed", message.lower())
        self.assertIsNotNone(receipt)
        self.assertEqual(app.booked[0]["fighter_ids"], original[0]["fighter_ids"])

    def test_locked_slot_state_round_trips_unknown_evidence(self):
        app = Harness()
        app.booking_workbench["locked_slot_proposals"] = [{
            "proposal_id": "booking-locked-slot-000001", "booking_id": "booking:draft:1",
            "original_fight": {"title": True, "future_card_field": {"keep": 1}},
            "future_evidence": {"source": "next-build"}, "options": [],
        }]
        state = app.ensure_booking_workbench_state()
        saved = state["locked_slot_proposals"][0]
        self.assertEqual(saved["original_fight"]["future_card_field"], {"keep": 1})
        self.assertEqual(saved["future_evidence"], {"source": "next-build"})

    def test_malformed_saved_options_are_readable_and_fail_closed(self):
        app = Harness()
        app.booking_workbench["proposals"] = [{
            "proposal_id": "proposal-malformed-list", "anchor_id": "f-1",
            "target_month": 4, "target_week": 1, "status": "Draft",
            "options": "not-a-list", "future_evidence": {"keep": True},
        }, {
            "proposal_id": "proposal-malformed-row", "anchor_id": "f-1",
            "target_month": 4, "target_week": 1, "status": "Draft",
            "options": [{"fighter_id": "f-2"}, "not-a-row"],
        }]
        before = json.loads(json.dumps(app.booking_workbench))
        unavailable = app.review_booking_proposal("proposal-malformed-list")
        self.assertEqual(unavailable["current_status"], "Unavailable")
        self.assertIn("malformed", unavailable["current_reason"].lower())
        mixed = app.review_booking_proposal("proposal-malformed-row")
        self.assertEqual(mixed["options"][1]["current_status"], "Unavailable")
        self.assertIn("malformed", mixed["options"][1]["current_blocks"][0])
        ok, message, receipt = app.commit_booking_proposal("proposal-malformed-row", 1)
        self.assertFalse(ok)
        self.assertIn("malformed", message.lower())
        self.assertIsNone(receipt)
        self.assertEqual(app.booking_workbench, before)

    def test_rematch_cooldown_is_a_current_block_not_a_commit_bypass(self):
        app = Harness()
        app.ai_matchup_is_stale = lambda a, b, **_kwargs: b.fighter_id == "f-2"
        _ok, _message, proposal = app.generate_booking_proposal("f-1", 4, 1)
        row = next(item for item in proposal["options"] if item["fighter_id"] == "f-2")
        self.assertEqual(row["generation_status"], "Blocked")
        self.assertIn("rematch cooldown", " ".join(row["hard_blocks"]))
        option_index = next(index for index, item in enumerate(proposal["options"]) if item["fighter_id"] == "f-2")
        ok, message, receipt = app.commit_booking_proposal(proposal["proposal_id"], option_index)
        self.assertFalse(ok)
        self.assertIn("rematch cooldown", message)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.get("status"), "rejected")
        self.assertEqual(app.booked, [])

    def test_title_commit_rechecks_challenger_merit_and_holder_protection(self):
        app = Harness()
        app.roster[0].champion = True
        app.roster[1].record_w = 1
        app.roster[1].record_l = 4
        app.ai_title_challenger_is_eligible = lambda fighter: (
            fighter.record_w >= 2 and fighter.record_w >= fighter.record_l
        )
        _ok, _message, proposal = app.generate_booking_proposal("f-1", 4, 1)
        option_index = next(index for index, item in enumerate(proposal["options"]) if item["fighter_id"] == "f-2")
        ok, message, receipt = app.commit_booking_proposal(
            proposal["proposal_id"], option_index, title=True,
        )
        self.assertFalse(ok)
        self.assertIn("title-challenger merit", message)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.get("status"), "rejected")
        self.assertEqual(app.booked, [])

    def test_past_target_and_changed_selected_date_fail_closed(self):
        app = Harness()
        _ok, _message, past = app.generate_booking_proposal("f-1", 2, 4)
        past_row = next(item for item in past["options"] if item["fighter_id"] == "f-2")
        self.assertIn("already passed", " ".join(past_row["hard_blocks"]))

        _ok, _message, proposal = app.generate_booking_proposal("f-1", 4, 1)
        app.selected_booking_date = lambda reject_past=False: (5, 1)
        option_index = next(index for index, item in enumerate(proposal["options"]) if item["fighter_id"] == "f-2")
        ok, message, receipt = app.commit_booking_proposal(proposal["proposal_id"], option_index)
        self.assertFalse(ok)
        self.assertIn("booking date changed", message)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt.get("status"), "rejected")
        self.assertEqual(app.booked, [])

    def test_shallow_division_keeps_the_no_alternative_state_explicit(self):
        app = Harness()
        for row in app.roster[1:]:
            row.injured = True
        ok, message, proposal = app.generate_booking_proposal("f-1", 4, 1)
        self.assertTrue(ok)
        self.assertIn("no eligible alternative", message)
        self.assertTrue(proposal["options"])
        self.assertTrue(all(row.get("hard_blocks") for row in proposal["options"]))


if __name__ == "__main__":
    unittest.main()
