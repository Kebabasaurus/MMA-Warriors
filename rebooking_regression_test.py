"""Regression coverage for identity-safe, title-preserving bout rebooking."""

import unittest

from events import EventMixin
from models import Fighter
from world import WorldMixin


def fighter(name, fighter_id, *, champion=False):
    return Fighter(
        name=name, fighter_id=fighter_id, weight="Lightweight", gender="Male",
        age=28, record_w=8, record_l=2, striking=70, wrestling=68,
        grappling=69, cardio=72, chin=70, popularity=45, momentum=0,
        morale=70, purse=12_500, champion=champion, injured=0,
    )


class RebookingHarness(EventMixin, WorldMixin):
    def __init__(self):
        self.month, self.week = 3, 2
        self.roster = [fighter("Champion", "f-champ", champion=True), fighter("Challenger", "f-challenger")]
        self.free_agents = []
        self.retired_fighters = []
        self.pending_rebookings = []
        self.inbox = []
        self.news = []
        self.scheduled_events = [{
            "event_id": "event-future", "name": "Future Card", "month": 4,
            "week": 2, "fights": [],
        }]
        self.player_company_name = "Test FC"
        self._camp_calls = []

    def resolve_fighter(self, reference):
        key = str(reference or "")
        return next((row for row in self.roster if row.fighter_id == key), None)

    def get_fighter(self, reference):
        key = str(reference or "")
        return next((row for row in self.roster if row.fighter_id == key or row.name == key), None)

    def normalize_card_order(self, fights=None):
        return fights

    def assign_event_camps(self, event):
        self._camp_calls.append(event)


class RebookingRegressionTests(unittest.TestCase):
    def test_title_terms_and_ids_survive_rebooking(self):
        app = RebookingHarness()
        event = {"event_id": "event-source", "name": "Scale Card"}
        fight = {
            "fighters": ["Champion", "Challenger"],
            "fighter_ids": ["f-champ", "f-challenger"],
            "fight_id": "bout-source",
            "title": True, "divisional_title": True, "interim": False,
            "special_belt": "", "main": True, "tier": "Main Event",
            "fight_plans": {"f-champ": "Pressure", "f-challenger": "Counter"},
            "title_miss_decision_state": {
                "status": "rebooked", "action": "rebook", "reason": "missed weight",
            },
        }

        note = app.queue_cancelled_bout_rebooking(event, fight, fight["fighters"])

        self.assertIn("Championship terms were preserved", note)
        scheduled = app.scheduled_events[0]["fights"]
        self.assertEqual(len(scheduled), 1)
        moved = scheduled[0]
        self.assertEqual(moved["fighter_ids"], ["f-champ", "f-challenger"])
        self.assertEqual(moved["fighters"], ["Champion", "Challenger"])
        self.assertTrue(moved["title"])
        self.assertTrue(moved["divisional_title"])
        self.assertTrue(moved["main"])
        self.assertEqual(moved["tier"], "Main Event")
        self.assertEqual(moved["fight_plans"]["f-champ"], "Pressure")
        self.assertEqual(moved["rebooked_from_event_id"], "event-source")
        self.assertTrue(moved["rebooked_from"].startswith("rebook:"))
        self.assertEqual(moved.get("title_miss_decision_state"), None)
        self.assertEqual(fight["title_miss_decision_state"]["action"], "rebook")

    def test_name_only_duplicate_career_fails_closed(self):
        app = RebookingHarness()
        app.roster.append(fighter("Twin", "f-twin-1"))
        app.roster.append(fighter("Twin", "f-twin-2"))
        event = {"event_id": "event-legacy", "name": "Legacy Card"}
        fight = {"fighters": ["Twin", "Challenger"], "tier": "Prelims"}

        app.queue_cancelled_bout_rebooking(event, fight, fight["fighters"])

        self.assertEqual(app.scheduled_events[0]["fights"], [])
        self.assertEqual(len(app.pending_rebookings), 1)
        self.assertEqual(app.pending_rebookings[0]["status"], "needs_review")
        self.assertTrue(app.pending_rebookings[0]["review_required"])
        self.assertTrue(any("awaiting rebooking review" in message.lower() for message in app.news))

    def test_unavailable_future_card_is_retained_and_retry_is_quiet(self):
        app = RebookingHarness()
        app.scheduled_events = []
        event = {"event_id": "event-full", "name": "Full Card"}
        fight = {
            "fighters": ["Champion", "Challenger"],
            "fighter_ids": ["f-champ", "f-challenger"],
            "fight_id": "bout-full", "title": True, "divisional_title": True,
        }

        first = app.queue_cancelled_bout_rebooking(event, fight, fight["fighters"])
        self.assertIn("awaiting rebooking review", first.lower())
        self.assertEqual(len(app.pending_rebookings), 1)
        inbox_count = len(app.inbox)
        news_count = len(app.news)

        # Re-running the worker without a calendar change must not discard the
        # request or create another notification.
        self.assertEqual(app.process_pending_rebookings(), [])
        self.assertEqual(len(app.pending_rebookings), 1)
        self.assertEqual(len(app.inbox), inbox_count)
        self.assertEqual(len(app.news), news_count)

        app.scheduled_events = [{
            "event_id": "event-later", "name": "Later Card", "month": 5,
            "week": 1, "fights": [],
        }]
        moved = app.process_pending_rebookings()
        self.assertEqual(len(moved), 1)
        self.assertEqual(app.pending_rebookings, [])
        self.assertEqual(app.scheduled_events[0]["fights"][0]["fighter_ids"], ["f-champ", "f-challenger"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
