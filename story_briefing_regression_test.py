"""Regression coverage for followed-story cursors and grouped briefings."""

import unittest

from world import WorldMixin


class BriefingHarness(WorldMixin):
    def __init__(self):
        self.month, self.week = 5, 2
        self.story_threads = [{
            "story_id": "STORY-1", "story_key": "rivalry:one", "type": "Rivalry", "status": "active",
            "phase": "active", "importance": 3, "fighter_ids": ["FTR-A"], "fighter_names": ["Alex North"],
            "companies": ["Case FC"], "stakes": "The next bout may settle the rivalry.",
            "beats": [{"month": 4, "week": 1, "kind": "origin", "ref": "beat-old", "summary": "The rivalry began."}],
            "opening_summary": "The rivalry began.",
        }]
        self._story_thread_index = {}
        self.story_subscriptions = []


class StoryBriefingTests(unittest.TestCase):
    def test_follow_and_acknowledge_are_cursor_based_and_refresh_safe(self):
        app = BriefingHarness()
        ok, sub = app.follow_story_target("thread", "STORY-1", "Rivalry")
        self.assertTrue(ok)
        app.story_threads[0]["beats"].append({"month": 5, "week": 3, "kind": "update", "ref": "beat-new", "summary": "The challenger called for a rematch."})
        before = repr(app.story_subscriptions)
        rows = app.followed_story_briefing()
        self.assertEqual(rows[0]["unread_count"], 1)
        self.assertEqual(rows[0]["beats"][0]["ref"], "beat-new")
        self.assertEqual(repr(app.story_subscriptions), before)
        ok, _ = app.acknowledge_story_subscription(sub["subscription_id"], "beat-new")
        self.assertTrue(ok)
        self.assertEqual(app.followed_story_briefing(), [])

    def test_company_subscription_and_snooze_do_not_delete_history(self):
        app = BriefingHarness()
        ok, sub = app.follow_story_target("company", target_name="Case FC")
        self.assertTrue(ok)
        app.story_threads[0]["beats"].append({"month": 5, "week": 2, "kind": "update", "ref": "beat-company", "summary": "Case FC announced a new card."})
        self.assertTrue(app.snooze_story_subscription(sub["subscription_id"], 4)[0])
        self.assertEqual(app.followed_story_briefing(), [])
        self.assertEqual(len(app.story_threads[0]["beats"]), 2)
        self.assertTrue(app.unfollow_story_subscription(sub["subscription_id"])[0])
        self.assertEqual(len(app.story_subscriptions), 1)

    def test_expired_cursor_discloses_coverage_gap(self):
        app = BriefingHarness()
        ok, sub = app.follow_story_target("thread", "STORY-1", "Rivalry")
        self.assertTrue(ok)
        app.story_subscriptions[0]["last_acknowledged_beat_ref"] = "beat-pruned"
        rows = app.followed_story_briefing()
        self.assertTrue(rows[0]["coverage_gap"])
        self.assertEqual(rows[0]["beats"][0]["ref"], "beat-old")

    def test_briefing_reader_does_not_normalise_malformed_subscriptions(self):
        app = BriefingHarness()
        app.story_subscriptions = [{
            "subscription_id": "legacy-sub", "target_type": "thread",
            "target_id": "STORY-1", "enabled": True,
            "snoozed_until_week": "not-a-week",
            "coverage_from_week": "not-a-week",
        }, "not-a-row"]
        before = repr(app.story_subscriptions)
        rows = app.followed_story_briefing()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["story_id"], "STORY-1")
        self.assertEqual(repr(app.story_subscriptions), before)
        projected = app.story_subscriptions_read_model()
        self.assertEqual(projected[0]["snoozed_until_week"], 0)
        self.assertEqual(repr(app.story_subscriptions), before)

    def test_idless_subscription_ids_are_position_independent_and_duplicate_safe(self):
        app = BriefingHarness()
        rows = [
            {
                "target_type": "thread", "target_id": "STORY-1",
                "target_name": "Rivalry", "created_week": 12,
                "coverage_from_week": 12, "enabled": True,
            },
            {
                "target_type": "company", "target_name": "Case FC",
                "created_week": 13, "coverage_from_week": 13,
                "enabled": True,
            },
            {
                "target_type": "thread", "target_id": "STORY-1",
                "target_name": "Rivalry", "created_week": 12,
                "coverage_from_week": 12, "enabled": True,
            },
        ]
        app.story_subscriptions = [dict(row) for row in rows]
        first = app.story_subscriptions_read_model()
        first_by_key = {
            (row["target_type"], row.get("target_id", ""), row.get("target_name", ""), row.get("created_week", 0)): row["subscription_id"]
            for row in first if row.get("target_type") == "company"
        }
        duplicate_ids = [row["subscription_id"] for row in first if row.get("target_type") == "thread"]

        app.story_subscriptions = [dict(rows[2]), dict(rows[0]), dict(rows[1])]
        reordered = app.story_subscriptions_read_model()
        reordered_company = next(row for row in reordered if row.get("target_type") == "company")
        self.assertEqual(
            reordered_company["subscription_id"],
            first_by_key[("company", "", "Case FC", 13)],
        )
        reordered_thread_ids = [row["subscription_id"] for row in reordered if row.get("target_type") == "thread"]
        self.assertEqual(set(reordered_thread_ids), set(duplicate_ids))
        self.assertEqual(len(set(row["subscription_id"] for row in first)), 3)
        self.assertTrue(any(row["subscription_id"].endswith("#2") for row in first))
        self.assertEqual(app.story_subscriptions, [dict(rows[2]), dict(rows[0]), dict(rows[1])])

    def test_storyline_index_reader_does_not_normalise_malformed_threads(self):
        app = BriefingHarness()
        app.story_threads = {"malformed": True}
        before = repr(app.story_threads)
        self.assertEqual(app.story_thread_index_read_model(), {})
        self.assertEqual(repr(app.story_threads), before)

    def test_briefing_reader_skips_malformed_thread_rows_without_mutation(self):
        app = BriefingHarness()
        ok, _ = app.follow_story_target("thread", "STORY-1", "Rivalry")
        self.assertTrue(ok)
        app.story_threads[0]["beats"].append({"month": 5, "week": 2, "kind": "update", "ref": "beat-new", "summary": "A new development."})
        app.story_threads = ["not-a-row", app.story_threads[0]]
        before = repr(app.story_threads)
        rows = app.followed_story_briefing()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["story_id"], "STORY-1")
        self.assertEqual(repr(app.story_threads), before)

    def test_briefing_reader_and_profile_query_fail_closed_for_nonfinite_dates(self):
        app = BriefingHarness()
        app.story_threads[0]["beats"] = [{
            "month": float("inf"), "week": float("nan"),
            "ref": "beat-nonfinite", "summary": "A malformed retained beat.",
        }]
        app.story_threads[0]["last_updated_month"] = float("inf")
        app.story_threads[0]["importance"] = float("nan")
        ok, _ = app.follow_story_target("thread", "STORY-1", "Rivalry")
        self.assertTrue(ok)
        app.story_subscriptions[0]["coverage_from_week"] = 0
        before = repr(app.story_threads)

        rows = app.followed_story_briefing()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["beats"][0]["ref"], "beat-nonfinite")
        queried = app.story_threads_for_fighter(type("FighterRef", (), {"fighter_id": "FTR-A"})())
        self.assertEqual(len(queried), 1)
        self.assertEqual(repr(app.story_threads), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
