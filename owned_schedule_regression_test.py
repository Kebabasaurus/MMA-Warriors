"""Regression coverage for the read-only owned-company calendar index."""

import unittest
from types import SimpleNamespace

from world import WorldMixin


class CalendarHarness(WorldMixin):
    def __init__(self):
        self.month, self.week = 2, 2
        self.player_company_name = "Player FC"
        self.scheduled_events = [
            {"event_id": "event-main", "name": "Main Card", "month": 3, "week": 1, "venue": "Arena", "fights": [{"fighters": ["Anchor", "Contender"], "fighter_ids": ["f-anchor", "f-contender"]}]},
            {"name": "Legacy Card", "month": 1, "week": 1, "venue": "Old Hall", "fights": []},
        ]
        self.promotions = [SimpleNamespace(
            name="Player Child", promotion_id="promo-child", is_child_promotion=True,
            parent_company="Player FC", scheduled_events=[
                {"event_id": "event-child", "name": "Child Showcase", "month": 2, "week": 2, "bouts": [{"a_id": "c", "b_id": "d"}]},
            ],
        ), SimpleNamespace(
            name="Rival Child", is_child_promotion=True, parent_company="Other FC", scheduled_events=[
                {"event_id": "event-rival", "name": "Rival Card", "month": 2, "week": 3, "fights": []},
            ],
        )]
        self.player_combat_divisions = {"BJJ": {
            "promotion_name": "Player FC BJJ", "scheduled_events": [
                {"event_id": "event-bjj", "name": "BJJ Open", "month": 4, "week": 1, "fights": [{"a_id": "e", "b_id": "f"}]},
            ],
        }}


class OwnedScheduleTests(unittest.TestCase):
    def test_index_combines_only_owned_sources_and_preserves_event_identity(self):
        app = CalendarHarness()
        before = repr(app.scheduled_events)
        rows = app.owned_schedule_index()
        self.assertEqual([row["event_id"] for row in rows], ["legacy:MMA:Player FC:2:Legacy Card", "event-child", "event-main", "event-bjj"])
        self.assertEqual({row["owner"] for row in rows}, {"Player FC", "Player Child", "Player FC BJJ"})
        self.assertNotIn("Rival Card", {row["name"] for row in rows})
        self.assertEqual(rows[0]["identity_status"], "Legacy reference")
        self.assertEqual(rows[1]["status"], "Due")
        self.assertEqual(rows[2]["bout_count"], 1)
        self.assertEqual(rows[2]["participants"], [
            {"name": "Anchor", "fighter_id": "f-anchor", "reference": "f-anchor"},
            {"name": "Contender", "fighter_id": "f-contender", "reference": "f-contender"},
        ])
        self.assertEqual(rows[2]["reservation_count"], 0)
        self.assertEqual(repr(app.scheduled_events), before)

    def test_status_and_limit_are_deterministic(self):
        app = CalendarHarness()
        rows = app.owned_schedule_index(limit=2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "Legacy Card")
        self.assertEqual(rows[1]["status"], "Due")

    def test_diagnostics_report_malformed_source_rows_without_mutating_schedule(self):
        app = CalendarHarness()
        app.scheduled_events.append("malformed MMA event")
        app.promotions[0].scheduled_events.append(None)
        before = repr((app.scheduled_events, app.promotions[0].scheduled_events))
        result = app.owned_schedule_index(include_diagnostics=True)
        self.assertEqual(result["coverage"], "partial")
        self.assertEqual(result["malformed_count"], 2)
        self.assertEqual(result["indexed_count"], 4)
        self.assertEqual(before, repr((app.scheduled_events, app.promotions[0].scheduled_events)))

    def test_malformed_event_dates_are_bounded_and_reported_without_rewriting_schedule(self):
        app = CalendarHarness()
        app.month = "legacy month"
        app.week = float("inf")
        app.scheduled_events[0].update({"month": float("inf"), "week": "unknown"})
        before = repr((app.month, app.week, app.scheduled_events))
        result = app.owned_schedule_index(include_diagnostics=True)
        self.assertEqual(result["coverage"], "partial")
        self.assertEqual(result["malformed_count"], 1)
        self.assertEqual(result["indexed_count"], 4)
        self.assertEqual(repr((app.month, app.week, app.scheduled_events)), before)
        bounded = next(row for row in result["rows"] if row["event_id"] == "event-main")
        self.assertEqual((bounded["month"], bounded["week"]), (1, 1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
