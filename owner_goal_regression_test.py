"""Regression coverage for durable owner-goal semantics."""

import unittest
from copy import deepcopy

from world import WorldMixin
from views import ViewMixin


class GoalHarness(ViewMixin):
    def __init__(self):
        self.month = 5
        self.cash = 120_000
        self.company_pop = 42
        self.result_history = ["show-1"]


class BoundaryGoalHarness(WorldMixin, ViewMixin):
    """Small non-Tk host for the completed-calendar owner-goal worker."""

    def __init__(self):
        self.month = 5
        self.week = 4
        self.cash = 120_000
        self.company_pop = 42
        self.result_history = ["show-1"]
        self.player_company_name = "Test Promotion"
        self.owner_goals = []
        self.rules = {}
        self.inbox = []
        self.news = []
        self.spectator_mode = False

    def format_game_date(self, month=None, week=None, include_week=True, day=None):
        return f"Month {month} Week {week}" if include_week else f"Month {month}"

    def company_event_count(self):
        return len(self.result_history)


class OwnerGoalTests(unittest.TestCase):
    def test_legacy_goal_is_achieve_once_and_terminal_outcome_stays_sealed(self):
        app = GoalHarness()
        goal = {"goal": "Cash", "metric": "cash", "target": 100000, "deadline": 8, "status": "Active"}
        status, _progress, _reason = app.owner_goal_evaluate(goal, current=120000, month=5)
        self.assertEqual(status, "Complete")
        goal["status"] = status
        status, _progress, reason = app.owner_goal_evaluate(goal, current=10, month=6)
        self.assertEqual(status, "Complete")
        self.assertIn("sealed", reason)

    def test_missed_deadline_cannot_be_recovered_later(self):
        app = GoalHarness()
        goal = {"goal": "Shows", "metric": "shows", "target": 4, "deadline": 3, "status": "Active"}
        status, _progress, _reason = app.owner_goal_evaluate(goal, current=2, month=4)
        self.assertEqual(status, "Failed")
        goal["status"] = status
        status, _progress, _reason = app.owner_goal_evaluate(goal, current=9, month=5)
        self.assertEqual(status, "Failed")

    def test_maintain_and_improve_semantics_have_explicit_evidence(self):
        app = GoalHarness()
        maintain = {"goal": "Hold popularity", "metric": "popularity", "target": 40, "deadline": 8, "goal_type": "maintain", "maintain_months": 2, "status": "Active"}
        status, _progress, _reason = app.owner_goal_evaluate(maintain, current=45, month=5)
        self.assertEqual(status, "Active")
        self.assertEqual(maintain["maintain_started_month"], 5)
        status, _progress, _reason = app.owner_goal_evaluate(maintain, current=45, month=6)
        self.assertEqual(status, "Complete")
        improve = {"goal": "Grow popularity", "metric": "popularity", "target": 5, "deadline": 8, "goal_type": "improve", "status": "Active"}
        status, progress, _reason = app.owner_goal_evaluate(improve, current=42, month=5)
        self.assertEqual(status, "Active")
        self.assertEqual(improve["baseline_value"], 42)
        status, progress, _reason = app.owner_goal_evaluate(improve, current=47, month=6)
        self.assertEqual(status, "Complete")
        self.assertIn("baseline 42", progress)

    def test_preview_is_pure_for_maintain_and_improve_goals(self):
        app = GoalHarness()
        maintain = {
            "goal": "Hold popularity", "metric": "popularity", "target": 40,
            "deadline": 8, "goal_type": "maintain", "maintain_months": 2,
            "status": "Active",
        }
        improve = {
            "goal": "Grow popularity", "metric": "popularity", "target": 5,
            "deadline": 8, "goal_type": "improve", "status": "Active",
        }
        app.owner_goal_evaluate(maintain, current=45, month=5, record=False, seal=False)
        app.owner_goal_evaluate(improve, current=42, month=5, record=False, seal=False)
        self.assertNotIn("maintain_started_month", maintain)
        self.assertNotIn("baseline_value", improve)
        self.assertNotIn("baseline_month", improve)

    def test_legacy_goal_ids_are_position_independent_and_duplicate_safe(self):
        rows = [
            {"goal": "Build cash", "metric": "cash", "target": 100_000, "deadline": 8},
            {"goal": "Run shows", "metric": "shows", "target": 3, "deadline": 9},
            {"goal": "Build cash", "metric": "cash", "target": 100_000, "deadline": 8},
        ]
        first = GoalHarness()
        first.player_company_name = "Test Promotion"
        first.owner_goals = deepcopy(rows)
        first.ensure_owner_goal_records()
        first_ids = {(row["goal"], row["target"], index): row["goal_id"] for index, row in enumerate(first.owner_goals)}

        reordered = GoalHarness()
        reordered.player_company_name = "Test Promotion"
        reordered.owner_goals = [deepcopy(rows[1]), deepcopy(rows[2]), deepcopy(rows[0])]
        reordered.ensure_owner_goal_records()
        reordered_by_content = {}
        for row in reordered.owner_goals:
            key = (row["goal"], row["target"])
            reordered_by_content.setdefault(key, []).append(row["goal_id"])

        self.assertEqual(first_ids[("Build cash", 100_000, 0)], reordered_by_content[("Build cash", 100_000)][0])
        self.assertEqual(first_ids[("Run shows", 3, 1)], reordered_by_content[("Run shows", 3)][0])
        self.assertEqual(len({row["goal_id"] for row in first.owner_goals}), 3)
        self.assertTrue(first.owner_goals[2]["goal_id"].endswith("#2"))

    def test_completed_boundary_records_observation_and_seals_once(self):
        app = BoundaryGoalHarness()
        app.owner_goals = [{
            "goal": "Build cash reserves", "metric": "cash", "target": 100_000,
            "deadline": 5, "status": "Active",
        }]
        outcomes = app.process_owner_goals_boundary(5, 4)
        goal = app.owner_goals[0]
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(goal["status"], "Complete")
        self.assertEqual(goal["outcome_month"], 5)
        self.assertEqual(goal["outcome_week"], 4)
        self.assertEqual(len(goal["observations"]), 1)
        self.assertEqual(app.rules["owner_goals_last_boundary"], "5:4")
        self.assertEqual(len(app.inbox), 1)
        sealed = deepcopy(goal)
        inbox = list(app.inbox)
        self.assertEqual(app.process_owner_goals_boundary(5, 4), [])
        self.assertEqual(goal, sealed)
        self.assertEqual(app.inbox, inbox)

    def test_boundary_failure_is_recorded_at_the_late_boundary(self):
        app = BoundaryGoalHarness()
        app.owner_goals = [{
            "goal": "Reach cash reserve", "metric": "cash", "target": 200_000,
            "deadline": 5, "status": "Active",
        }]
        outcomes = app.process_owner_goals_boundary(6, 1)
        goal = app.owner_goals[0]
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(goal["status"], "Failed")
        self.assertEqual(goal["outcome_month"], 6)
        self.assertEqual(goal["outcome_week"], 1)
        self.assertIn("deadline", goal["outcome_reason"].lower())
        self.assertEqual(len(goal["observations"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
