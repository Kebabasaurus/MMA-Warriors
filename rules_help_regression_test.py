"""Regression coverage for the authored Rules Help catalogue."""

import inspect
import random
import tkinter as tk
from tkinter import ttk
import unittest

from rules_help import HELP_TOPICS, help_topic, search_help_topics
from ui import UIMixin


class RulesHelpTests(unittest.TestCase):
    def test_catalogue_has_stable_complete_topics_and_unique_routes(self):
        ids = [topic.get("topic_id") for topic in HELP_TOPICS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(HELP_TOPICS), 8)
        required = ("title", "summary", "answer", "why_blocked", "action_label", "action_route", "aliases", "terms")
        for topic in HELP_TOPICS:
            for field in required:
                self.assertTrue(topic.get(field), f"missing {field}: {topic.get('topic_id')}")
            self.assertTrue(topic["action_route"])

    def test_search_is_case_insensitive_ordered_defensive_and_rng_pure(self):
        before = random.getstate()
        results = search_help_topics("OPPONENT RANKING")
        self.assertEqual(random.getstate(), before)
        self.assertEqual([topic["topic_id"] for topic in results], ["ranking-scopes"])
        results[0]["title"] = "mutated"
        self.assertEqual(help_topic("ranking-scopes")["title"], "Company rank vs world rank")
        rank_results = [topic["topic_id"] for topic in search_help_topics("rank")]
        self.assertGreaterEqual(len(rank_results), 1)
        self.assertEqual(rank_results[0], "ranking-scopes")
        self.assertEqual(search_help_topics("does-not-exist"), [])

    def test_ui_keeps_help_links_as_navigation_and_disables_stale_routes(self):
        source = inspect.getsource(UIMixin.show_help_topic)
        self.assertIn("route in getattr(self, \"tab_pages\", {})", source)
        self.assertIn("state=\"normal\" if available else \"disabled\"", source)
        refresh_source = inspect.getsource(UIMixin.refresh_help_topics)
        self.assertIn("self.rules[\"ui_help_search\"]", refresh_source)
        self.assertIn("isinstance(getattr(self, \"rules\", None), dict)", refresh_source)
        self.assertIn("search_help_topics(query)", refresh_source)

    def test_help_page_filters_and_fails_closed_when_a_route_is_missing(self):
        root = tk.Tk()
        root.withdraw()
        try:
            class Harness(UIMixin):
                pass

            app = Harness()
            app.root = root
            app.rules = {}
            app.colors = {
                "chrome": "#171c24", "panel": "#202833", "panel_dark": "#202833",
                "tree": "#171c24", "cream": "#10151b", "text": "#edf1f4",
                "gold": "#e7bc64", "muted": "#a7b2bd", "red": "#a92e36", "line": "#394451",
            }
            app.help_tab = ttk.Frame(root)
            app.tab_pages = {"rankings": ttk.Frame(root), "booking": ttk.Frame(root), "staff": ttk.Frame(root), "website": ttk.Frame(root), "contracts": ttk.Frame(root), "finance": ttk.Frame(root), "log": ttk.Frame(root)}
            app.build_help_tab()
            root.update_idletasks()
            self.assertEqual(app.help_topic_list.size(), len(HELP_TOPICS))
            app.help_search_var.set("opponent ranking")
            app.refresh_help_topics()
            self.assertEqual(app.help_topic_list.size(), 1)
            self.assertEqual(app.help_topic_rows[0]["topic_id"], "ranking-scopes")
            app.tab_pages = {}
            app.show_help_topic()
            self.assertEqual(str(app.help_action_button.cget("state")), "disabled")
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main(verbosity=2)
