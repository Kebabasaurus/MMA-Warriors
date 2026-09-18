"""Regression coverage for resuming a saved title weight-miss decision."""

import random
import unittest

from events import EventMixin
from admin import AdminMixin
from models import Fighter


def fighter(name, fighter_id, *, champion=False):
    return Fighter(
        name=name, weight="Lightweight", age=28, record_w=8, record_l=2,
        striking=70, wrestling=68, grappling=69, cardio=72, chin=70,
        popularity=45, momentum=0, morale=70, purse=12_500,
        fighter_id=fighter_id, champion=champion, injured=0,
    )


class TitleDecisionResumeHarness(AdminMixin, EventMixin):
    def __init__(self):
        self.month, self.week = 3, 2
        self.roster = [fighter("Champion", "f-champ", champion=True), fighter("Challenger", "f-challenger")]
        self.free_agents = []
        self.retired_fighters = []
        self.scheduled_events = []
        self.player_company_name = "Test FC"
        self.player_region = "USA"
        self.news = []
        self.belts = {"Male Lightweight": "Champion"}
        self.interim_belts = {}
        self.belt_history = {"Male Lightweight": []}
        self._weigh_calls = []
        self._rebook_calls = []

    def resolve_fighter(self, reference):
        key = str(reference or "")
        return next((row for row in self.roster if row.fighter_id == key or row.name == key), None)

    def perform_weigh_in(self, *args, **kwargs):
        self._weigh_calls.append((args, kwargs))
        raise AssertionError("A saved title decision must not roll the weigh-in again.")

    def event_fight_participant_references(self, fight):
        return EventMixin.event_fight_participant_references(self, fight)

    def queue_cancelled_bout_rebooking(self, event, fight, names):
        self._rebook_calls.append((event.get("event_id", ""), tuple(names)))
        return "Queued for the existing rescheduling review."


class ReplacementMissHarness(TitleDecisionResumeHarness):
    """Harness for a replacement that reaches the scale but misses again."""

    def __init__(self):
        super().__init__()
        self.replacement = fighter("Short Notice", "f-short-notice")
        self.free_agents = [self.replacement]
        self._replacement_calls = []

    def commit_last_minute_replacement(self, _event, fight, replacement_id, corner_index=0):
        if replacement_id != self.replacement.fighter_id:
            return False, "That fighter is no longer available for this card."
        names = list(fight["fighters"])
        ids = list(fight["fighter_ids"])
        names[corner_index] = self.replacement.name
        ids[corner_index] = self.replacement.fighter_id
        fight["fighters"], fight["fighter_ids"] = names, ids
        if self.replacement in self.free_agents:
            self.free_agents.remove(self.replacement)
            self.roster.append(self.replacement)
        self._replacement_calls.append(replacement_id)
        return True, "Short Notice is now booked on short notice."

    def perform_weigh_in(self, fighter, *args, **kwargs):
        if fighter is self.replacement:
            fighter.missed_weight = True
            fighter.scale_weight = 3
            fighter.weight_cut_penalty = 5
            return {"made": False, "miss_by": 3.0, "scale_weight": 173.0}
        return super().perform_weigh_in(fighter, *args, **kwargs)


class FreshTitleStakesHarness(TitleDecisionResumeHarness):
    """Exercise the live weigh-in decision boundary for narrow title flags."""

    def perform_weigh_in(self, fighter, *args, **kwargs):
        fighter.missed_weight = fighter.name == "Champion"
        fighter.scale_weight = 157 if fighter.missed_weight else 155
        fighter.weight_cut_penalty = 4 if fighter.missed_weight else 0
        return {
            "made": not fighter.missed_weight,
            "miss_by": 2.0 if fighter.missed_weight else 0.0,
            "scale_weight": fighter.scale_weight,
        }


class IdlessReplacementSuccessHarness(TitleDecisionResumeHarness):
    """Exercise a legacy replacement that has no fighter_id."""

    def __init__(self):
        super().__init__()
        self.replacement = fighter("Legacy Short Notice", "f-legacy-short")
        self.replacement.fighter_id = ""
        self.free_agents = [self.replacement]

    def ai_title_challenger_is_eligible(self, candidate):
        return candidate.record_w >= 2 and candidate.record_w >= candidate.record_l

    def fighter_booking_status(self, _fighter, _month=None, _week=None):
        return "Ready"

    def assign_event_camps(self, _event):
        return None

    def perform_weigh_in(self, fighter, *args, **kwargs):
        if fighter is self.replacement:
            fighter.missed_weight = False
            fighter.scale_weight = 154
            fighter.weight_cut_penalty = 0
            return {"made": True, "miss_by": 0.0, "scale_weight": 154.0}
        return super().perform_weigh_in(fighter, *args, **kwargs)


class DeferredPrepareHarness(TitleDecisionResumeHarness):
    def __init__(self):
        super().__init__()
        self._press_calls = 0

    def normalize_card_order(self, _fights):
        return None

    def refresh_scheduled_event_auto_name(self, _event):
        return None

    def event_date_label(self, event):
        return f"Month {event.get('month', 1)} Week {event.get('week', 1)}"

    def event_day(self, _event):
        return 1

    def venue_region(self, _venue):
        return "USA"

    def run_press_conference(self, _event):
        self._press_calls += 1
        return (["PRESS OUTCOME: retained for the pending card."], 7.0)


class TitleDecisionResumeTests(unittest.TestCase):
    def _pending_fight(self, app):
        event = {"event_id": "event-resume", "name": "Resume Card", "month": 3, "week": 2}
        fight = {
            "fighters": ["Champion", "Challenger"],
            "fighter_ids": ["f-champ", "f-challenger"],
            "title": True,
            "divisional_title": True,
        }
        snapshot = app.build_title_miss_decision_snapshot(event, fight, [(app.roster[0], 2.0)])
        fight["title_miss_decision_state"] = snapshot
        event["fights"] = [fight]
        return event, fight

    def test_pending_snapshot_resumes_without_a_second_scale_roll(self):
        app = TitleDecisionResumeHarness()
        event, fight = self._pending_fight(app)
        app._title_miss_decision_provider = lambda _event, _fight, misses: (
            self.assertEqual([(row.name, miss) for row, miss in misses], [("Champion", 2.0)])
            or {"action": "keep_belt"}
        )
        rng_before = random.getstate()

        lines, purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(app._weigh_calls, [])
        self.assertEqual(purse_penalty, 2_500)
        self.assertEqual(cancelled, [])
        self.assertEqual(fight["title_miss_decision_state"]["status"], "resolved")
        self.assertEqual(fight["title_miss_decision_state"]["action"], "keep_belt")
        self.assertEqual(fight["title_sanction_snapshot"]["decision"], "keep_belt")
        self.assertTrue(fight["title_sanction_snapshot"]["on_line"])
        self.assertTrue(fight["title_miss_decision_state"]["miss_fine_applied"])
        self.assertTrue(fight["title"], "Keep Belt must preserve the title sanction on the bout.")
        self.assertTrue(fight["divisional_title"], "Keep Belt must preserve the divisional-title flag.")
        self.assertFalse(fight.get("catchweight", False), "Keep Belt must not downgrade the bout to catchweight.")
        self.assertTrue(any("no new scale roll" in line.lower() for line in lines))
        self.assertEqual(random.getstate(), rng_before)

    def test_divisional_title_flag_enters_the_live_decision_flow(self):
        app = FreshTitleStakesHarness()
        event = {"event_id": "event-divisional", "name": "Divisional Card", "month": 3, "week": 2}
        fight = {
            "fighters": ["Champion", "Challenger"],
            "fighter_ids": ["f-champ", "f-challenger"],
            "title": False,
            "divisional_title": True,
        }
        event["fights"] = [fight]
        app._title_miss_decision_provider = lambda *_args: {"action": "keep_belt"}

        _lines, _purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(cancelled, [])
        self.assertEqual(fight["title_miss_decision_state"]["action"], "keep_belt")
        self.assertTrue(fight["title_sanction_snapshot"]["on_line"])
        self.assertTrue(fight["divisional_title"])
        self.assertEqual(app._weigh_calls, [])

    def test_named_special_belt_enters_the_live_decision_flow(self):
        app = FreshTitleStakesHarness()
        event = {"event_id": "event-special", "name": "Special Belt Card", "month": 3, "week": 2}
        fight = {
            "fighters": ["Champion", "Challenger"],
            "fighter_ids": ["f-champ", "f-challenger"],
            "title": False,
            "special_belt": "Grand Prix Belt",
        }
        event["fights"] = [fight]
        app._title_miss_decision_provider = lambda *_args: {"action": "keep_belt"}

        _lines, _purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(cancelled, [])
        self.assertEqual(fight["title_miss_decision_state"]["action"], "keep_belt")
        self.assertTrue(fight["title_sanction_snapshot"]["on_line"])
        self.assertEqual(fight["special_belt"], "Grand Prix Belt")

    def test_dismissed_title_decision_stays_pending_without_defaulting_to_keep_belt(self):
        app = TitleDecisionResumeHarness()
        event, fight = self._pending_fight(app)
        app._title_miss_decision_provider = lambda *_args: None
        rng_before = random.getstate()

        _lines, purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(purse_penalty, 2_500)
        self.assertEqual(cancelled, [fight])
        self.assertEqual(fight["title_miss_decision_state"]["status"], "awaiting_player")
        self.assertEqual(fight["title_miss_decision_state"]["action"], "awaiting_player")
        self.assertFalse(fight.get("_weight_miss_decision_applied"))
        self.assertFalse(fight["title_sanction_snapshot"]["on_line"])
        self.assertTrue(fight["title"], "The unresolved decision must not rewrite the booking.")
        self.assertEqual(random.getstate(), rng_before)

    def test_pending_package_cannot_open_or_settle_event(self):
        app = TitleDecisionResumeHarness()
        event, _fight = self._pending_fight(app)
        notices = []
        app._results_status_notice = lambda message, warning=False: notices.append((message, warning))
        package = {
            "preparation_pending": True,
            "pending_reason": "Choose a title-miss action first.",
        }

        self.assertIs(app.open_live_fight_window(event, package), package)
        self.assertIs(app.finish_event(event, package), package)
        self.assertNotIn("_settlement_id", event)
        self.assertTrue(any(message == package["pending_reason"] and warning for message, warning in notices))

    def test_prepare_pending_reuses_press_evidence_on_retry(self):
        app = DeferredPrepareHarness()
        event, _fight = self._pending_fight(app)
        event["venue"] = "Test Arena"
        app._title_miss_decision_provider = lambda *_args: None

        first = app.prepare_event_result(event)
        second = app.prepare_event_result(event)

        self.assertTrue(first["preparation_pending"])
        self.assertTrue(second["preparation_pending"])
        self.assertEqual(app._press_calls, 1)
        self.assertEqual(second["preparation_timeline"]["status"], "awaiting_player")
        self.assertEqual(
            second["preparation_timeline"]["final_readiness"],
            "Awaiting player title-miss decision",
        )

    def test_terminal_decision_is_not_reapplied_after_reload(self):
        app = TitleDecisionResumeHarness()
        event, fight = self._pending_fight(app)
        fight["title_miss_decision_state"].update({
            "status": "resolved", "action": "keep_belt", "reason": "Player kept the title on the line.",
        })
        fight["title_sanction_snapshot"] = {
            "schema_version": 1, "on_line": True, "decision": "keep_belt",
            "champion_miss_waived": True, "missed_corners": fight["title_miss_decision_state"]["corners"],
        }
        fight["_weight_miss_decision_applied"] = True
        app._title_miss_decision_provider = lambda *_args: self.fail("A terminal decision must not prompt again.")

        lines, purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(app._weigh_calls, [])
        self.assertEqual(purse_penalty, 0)
        self.assertEqual(cancelled, [])
        self.assertTrue(any("no new scale roll" in line.lower() for line in lines))

    def test_unresolvable_pending_corner_fails_closed_for_review(self):
        app = TitleDecisionResumeHarness()
        event, fight = self._pending_fight(app)
        fight["title_miss_decision_state"]["corners"][0]["fighter_id"] = "missing-corner"

        _lines, purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(app._weigh_calls, [])
        self.assertEqual(purse_penalty, 2_500)
        self.assertEqual(cancelled, [fight])
        self.assertEqual(fight["title_miss_decision_state"]["status"], "needs_review")
        self.assertIn("could not resolve", fight["title_miss_decision_state"]["reason"])
        _lines, _purse_penalty, second_cancelled = app.run_weigh_ins(event)
        self.assertEqual(app._weigh_calls, [])
        self.assertEqual(second_cancelled, [fight])

    def test_nonfinite_pending_miss_fails_closed_without_a_new_scale_roll(self):
        app = TitleDecisionResumeHarness()
        event, fight = self._pending_fight(app)
        fight["title_miss_decision_state"]["corners"][0]["miss_by"] = float("inf")
        fight["title_miss_decision_state"]["miss_fine_total"] = float("inf")

        _lines, purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(app._weigh_calls, [])
        self.assertEqual(purse_penalty, 0)
        self.assertEqual(cancelled, [fight])
        self.assertEqual(fight["title_miss_decision_state"]["status"], "needs_review")

    def test_unresolvable_non_missed_corner_retains_pending_fine(self):
        app = TitleDecisionResumeHarness()
        event, fight = self._pending_fight(app)
        fight["title_miss_decision_state"]["corners"][1]["fighter_id"] = "missing-corner"
        # The champion's missed identity is still valid, but the other corner
        # cannot be rebuilt, so the bout must fail closed without losing the
        # already-recorded fine evidence.
        _lines, purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(app._weigh_calls, [])
        self.assertEqual(purse_penalty, 2_500)
        self.assertEqual(cancelled, [fight])
        self.assertEqual(fight["title_miss_decision_state"]["status"], "needs_review")
        self.assertTrue(fight["title_miss_decision_state"]["miss_fine_applied"])

    def test_rebook_terminal_state_is_idempotent_after_reload(self):
        app = TitleDecisionResumeHarness()
        event, fight = self._pending_fight(app)
        app._title_miss_decision_provider = lambda *_args: {"action": "rebook"}
        rng_before = random.getstate()

        _lines, purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(app._weigh_calls, [])
        self.assertEqual(purse_penalty, 2_500)
        self.assertEqual(cancelled, [fight])
        self.assertTrue(fight.get("_weight_miss_decision_applied"))
        self.assertEqual(fight["title_miss_decision_state"]["status"], "rebooked")
        self.assertEqual(len(app._rebook_calls), 1)
        self.assertEqual(random.getstate(), rng_before)

        app._title_miss_decision_provider = lambda *_args: self.fail("A rebooked decision must not prompt again.")
        _lines, purse_penalty, second_cancelled = app.run_weigh_ins(event)

        self.assertEqual(app._weigh_calls, [])
        self.assertEqual(purse_penalty, 0)
        self.assertEqual(second_cancelled, [fight])
        self.assertEqual(len(app._rebook_calls), 1)
        self.assertEqual(random.getstate(), rng_before)

    def test_keep_belt_double_miss_skips_legacy_commission_roll(self):
        app = TitleDecisionResumeHarness()
        event = {"event_id": "event-double-miss", "name": "Double Miss", "month": 3, "week": 2}
        fight = {
            "fighters": ["Champion", "Challenger"],
            "fighter_ids": ["f-champ", "f-challenger"],
            "title": True, "divisional_title": True,
        }
        fight["title_miss_decision_state"] = app.build_title_miss_decision_snapshot(
            event, fight, [(app.roster[0], 6.0), (app.roster[1], 6.0)],
        )
        event["fights"] = [fight]
        app._title_miss_decision_provider = lambda *_args: {"action": "keep_belt"}
        rng_before = random.getstate()

        _lines, purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(app._weigh_calls, [])
        self.assertEqual(purse_penalty, 7_500)
        self.assertEqual(cancelled, [])
        self.assertTrue(fight["title"])
        self.assertFalse(fight.get("catchweight", False))
        self.assertEqual(random.getstate(), rng_before)

    def test_remove_belt_vacates_an_interim_holder(self):
        app = TitleDecisionResumeHarness()
        interim = app.roster[1]
        interim.interim_champion = True
        app.interim_belts = {"Male Lightweight": interim.name}
        event, fight = self._pending_fight(app)
        fight["fighters"] = ["Champion", "Challenger"]
        fight["fighter_ids"] = ["f-champ", "f-challenger"]
        fight["title_miss_decision_state"] = app.build_title_miss_decision_snapshot(
            event, fight, [(interim, 2.0)],
        )
        app._title_miss_decision_provider = lambda *_args: {"action": "remove_belt"}

        _lines, _purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(cancelled, [])
        self.assertFalse(interim.interim_champion)
        self.assertEqual(app.interim_belts["Male Lightweight"], "")
        self.assertTrue(fight["title_sanction_snapshot"]["on_line"])

    def test_remove_belt_challenger_only_miss_fails_closed_for_review(self):
        app = TitleDecisionResumeHarness()
        event, fight = self._pending_fight(app)
        # The challenger missed, but there is no champion to vacate.  The
        # approved policy does not define that title consequence, so the
        # decision must retain the evidence and stop rather than guessing.
        fight["title_miss_decision_state"] = app.build_title_miss_decision_snapshot(
            event, fight, [(app.roster[1], 2.0)],
        )
        app._title_miss_decision_provider = lambda *_args: {"action": "remove_belt"}

        _lines, purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(app._weigh_calls, [])
        self.assertEqual(purse_penalty, 2_500)
        self.assertEqual(cancelled, [fight])
        self.assertEqual(fight["title_miss_decision_state"]["status"], "needs_review")
        self.assertTrue(fight["title_sanction_snapshot"]["review_required"])
        self.assertFalse(fight["title_sanction_snapshot"]["on_line"])
        self.assertIn("challenger-only", fight["title_miss_decision_state"]["reason"])
        self.assertTrue(fight["title_miss_decision_state"]["miss_fine_applied"])

    def test_cancel_terminal_state_is_idempotent_after_reload(self):
        app = TitleDecisionResumeHarness()
        event, fight = self._pending_fight(app)
        app._title_miss_decision_provider = lambda *_args: {"action": "cancel"}
        rng_before = random.getstate()

        _lines, purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(app._weigh_calls, [])
        self.assertEqual(purse_penalty, 2_500)
        self.assertEqual(cancelled, [fight])
        self.assertTrue(fight.get("_weight_miss_decision_applied"))
        self.assertEqual(fight["title_miss_decision_state"]["status"], "cancelled")
        self.assertEqual(app._rebook_calls, [])
        self.assertEqual(random.getstate(), rng_before)

        app._title_miss_decision_provider = lambda *_args: self.fail("A cancelled decision must not prompt again.")
        _lines, purse_penalty, second_cancelled = app.run_weigh_ins(event)

        self.assertEqual(app._weigh_calls, [])
        self.assertEqual(purse_penalty, 0)
        self.assertEqual(second_cancelled, [fight])
        self.assertEqual(app._rebook_calls, [])
        self.assertEqual(random.getstate(), rng_before)

    def test_replacement_that_misses_again_is_held_for_review_without_catchweight(self):
        app = ReplacementMissHarness()
        event = {"event_id": "event-replacement-miss", "name": "Replacement Miss", "month": 3, "week": 2}
        fight = {
            "fighters": ["Champion", "Challenger"],
            "fighter_ids": ["f-champ", "f-challenger"],
            "title": True, "divisional_title": True,
        }
        fight["title_miss_decision_state"] = app.build_title_miss_decision_snapshot(
            event, fight, [(app.roster[0], 2.0)],
        )
        event["fights"] = [fight]
        app._title_miss_decision_provider = lambda *_args: {
            "action": "replacement", "fighter_id": "f-short-notice", "corner_index": 1,
        }

        _lines, purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(cancelled, [fight])
        self.assertEqual(purse_penalty, 6_250)
        self.assertEqual(fight["title_miss_decision_state"]["status"], "needs_review")
        self.assertTrue(fight["title_miss_decision_state"]["miss_fine_applied"])
        self.assertFalse(fight["title_sanction_snapshot"]["on_line"])
        self.assertFalse(fight.get("catchweight", False))
        self.assertIn("stopped for review", " ".join(_lines).lower())

        app._title_miss_decision_provider = lambda *_args: self.fail("A replacement review must not prompt again.")
        _lines, second_penalty, second_cancelled = app.run_weigh_ins(event)
        self.assertEqual(second_penalty, 0)
        self.assertEqual(second_cancelled, [fight])
        self.assertEqual(app._replacement_calls, ["f-short-notice"])

    def test_idless_replacement_resolves_by_unique_saved_name_after_commit(self):
        app = IdlessReplacementSuccessHarness()
        event = {"event_id": "event-idless-replacement", "name": "ID-less Replacement", "month": 3, "week": 2}
        fight = {
            "fighters": ["Champion", "Challenger"],
            "fighter_ids": ["f-champ", "f-challenger"],
            "title": True, "divisional_title": True,
        }
        fight["title_miss_decision_state"] = app.build_title_miss_decision_snapshot(
            event, fight, [(app.roster[0], 2.0)],
        )
        event["fights"] = [fight]
        candidate_key = app.last_minute_replacement_candidates(event, fight, 1)[0]["candidate_key"]
        app._title_miss_decision_provider = lambda *_args: {
            "action": "replacement", "fighter_id": candidate_key, "corner_index": 1,
        }

        _lines, _purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(cancelled, [])
        self.assertEqual(fight["fighters"][1], "Legacy Short Notice")
        self.assertEqual(fight["fighter_ids"][1], "")
        self.assertEqual(fight["title_miss_decision_state"]["status"], "resolved")
        self.assertTrue(fight["title_sanction_snapshot"]["on_line"])

    def test_invalid_replacement_selection_cancels_to_review_without_fallback(self):
        app = ReplacementMissHarness()
        event = {"event_id": "event-invalid-replacement", "name": "Invalid Replacement", "month": 3, "week": 2}
        fight = {
            "fighters": ["Champion", "Challenger"],
            "fighter_ids": ["f-champ", "f-challenger"],
            "title": True, "divisional_title": True,
        }
        fight["title_miss_decision_state"] = app.build_title_miss_decision_snapshot(
            event, fight, [(app.roster[0], 2.0)],
        )
        event["fights"] = [fight]
        app._title_miss_decision_provider = lambda *_args: {
            "action": "replacement", "fighter_id": "does-not-exist", "corner_index": 1,
        }

        _lines, purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(cancelled, [fight])
        self.assertEqual(purse_penalty, 2_500)
        self.assertEqual(fight["title_miss_decision_state"]["status"], "needs_review")
        self.assertFalse(fight.get("catchweight", False))
        self.assertEqual(app._replacement_calls, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
