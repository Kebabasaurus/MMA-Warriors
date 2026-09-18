"""Regression coverage for truthful comparison cohort context."""

import inspect
import random
import unittest
from types import SimpleNamespace

from views import ViewMixin


def fighter(fid, name, *, gender="Male", weight="Lightweight"):
    return SimpleNamespace(fighter_id=fid, name=name, gender=gender, weight=weight, retired=False)


class ComparisonHarness(ViewMixin):
    def __init__(self):
        self.month, self.week = 6, 2
        self.rules = {"scouting_mode": False}
        self.left = fighter("f-1", "Left")
        self.right = fighter("f-2", "Right")
        self.hidden = fighter("f-3", "Hidden")
        self.rows = [("Player", self.left), ("Rival", self.right), ("Rival", self.hidden), ("Rival", self.hidden)]

    def format_game_date(self):
        return "Month 6 Week 2"

    def fighter_display_division(self, value):
        return value.weight

    def fighter_identity_key(self, value):
        return value.fighter_id

    def all_database_fighters_with_companies(self):
        return list(self.rows)

    def world_fighter_search_stat_visible(self, _fighter, company):
        return company == "Player" or _fighter is self.right


class ComparisonContextTests(unittest.TestCase):
    def test_complete_context_counts_identity_deduplicated_visible_cohort(self):
        app = ComparisonHarness()
        app.rows = [("Player", app.left), ("Rival", app.right)]
        before = random.getstate()
        context = app.fighter_comparison_cohort_context(("Player", app.left), ("Rival", app.right))
        self.assertEqual(random.getstate(), before)
        self.assertEqual(context["as_of"], "Month 6 Week 2")
        self.assertEqual(context["visible_count"], 2)
        self.assertEqual(context["total_count"], 2)
        self.assertEqual(context["coverage"], "complete")
        self.assertIn("Complete visible cohort", context["label"])

    def test_partial_context_labels_known_sample_without_hidden_values_or_percentile(self):
        app = ComparisonHarness()
        before = [(company, row.fighter_id) for company, row in app.rows]
        context = app.fighter_comparison_cohort_context(("Player", app.left), ("Rival", app.right))
        self.assertEqual(context["visible_count"], 2)
        self.assertEqual(context["total_count"], 3)
        self.assertEqual(context["coverage"], "partial")
        self.assertIn("Known sample (2 of 3)", context["label"])
        self.assertNotIn("percentile", context["label"].lower())
        self.assertEqual([(company, row.fighter_id) for company, row in app.rows], before)

    def test_comparison_window_exposes_context_without_percentiles(self):
        source = inspect.getsource(ViewMixin.open_compare_fighters_window)
        self.assertIn("COHORT CONTEXT", source)
        self.assertIn("No percentile is inferred", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
