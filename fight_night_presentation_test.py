"""Presentation cannot rewrite recorded commentary or invent event evidence."""
import random
import tkinter as tk
import unittest

from fight_night_presentation import (
    TIMELINE_TAGS, classify_fight_line, configure_fight_timeline,
    insert_fight_timeline_line,
)


class TimelineTest(unittest.TestCase):
    def test_source_categories(self):
        cases = {"ROUND 2 — 5:00": "round", "[02:39] Ada steps forward.": "action",
                 "Corner read: settle down.": "analysis", "Result: Ada by decision": "result",
                 "FIGHT METRICS": "metrics", "A quiet moment.": "narrative", "----": "separator",
                 "Round 1 summary: All original metrics remain here.": "analysis"}
        for source, expected in cases.items():
            self.assertEqual(classify_fight_line(source), expected)
            self.assertIn(expected, TIMELINE_TAGS)

    def test_incidental_words_are_not_events(self):
        for source in ("Ada is not hurt.", "No cut opens.", "Ben avoids being knocked down.",
                       "The referee does not stop the fight.", "Ada drops her hands.",
                       "Ben threatens a submission but cannot get the tap.",
                       "No official result is available yet."):
            self.assertEqual(classify_fight_line(source), "narrative")
        self.assertEqual(classify_fight_line('[2:30] Red scores a knockdown.'), 'knockdown')
        self.assertEqual(classify_fight_line('[2:30] Red lands a clean elbow.'), 'impact')
        self.assertEqual(classify_fight_line('[2:04] That exchange adds visible bruising to Blue.'), 'cut')
        self.assertEqual(classify_fight_line('[2:04] No visible bruising develops on Blue.'), 'action')
        self.assertEqual(classify_fight_line('[2:30] The referee stops the fight.'), 'finish')
        self.assertEqual(classify_fight_line('[2:30] The referee has seen enough and stops the contest.'), 'finish')
        self.assertEqual(classify_fight_line('[2:30] Blue has to tap.'), 'finish')
        self.assertEqual(classify_fight_line('[2:30] Blue goes unconscious.'), 'finish')
        self.assertEqual(classify_fight_line('[2:30] Blue catches the body jab on an elbow and pivots away.'), 'action')
        self.assertEqual(classify_fight_line('[2:30] Red looks for an elbow but Blue removes the lane.'), 'action')
        self.assertEqual(classify_fight_line('[2:30] Red is not hurt; no knockdown.'), 'action')
        self.assertEqual(classify_fight_line('[2:30] Red never gets the tap.'), 'action')

    def test_text_preservation_state_and_rng(self):
        root = tk.Tk()
        root.withdraw()
        try:
            widget = tk.Text(root, state="disabled")
            colors = {"panel": "#171e26", "text": "#fafafa", "muted": "#101010", "gold": "#d6b665"}
            original = colors.copy()
            before_rng = random.getstate()
            configure_fight_timeline(widget, colors)
            sources = ["  [02:39]  Ada: no cut.  ", "\nROUND 2\n", "Result: Ada by decision\n", "",
                       "Round 1 summary: Metrics - Ada: impact 21, control 12, danger 6."]
            for source in sources:
                insert_fight_timeline_line(widget, source)
            expected = "".join(source + ("" if source.endswith("\n") else "\n") for source in sources)
            self.assertEqual(widget.get("1.0", "end-1c"), expected)
            self.assertEqual(str(widget.cget("state")), "disabled")
            self.assertTrue(widget.tag_ranges("clock"))
            insert_fight_timeline_line(widget, "[2:10] Red lands a clean elbow.")
            insert_fight_timeline_line(widget, "[1:02] The referee stops the fight.")
            expected += "[2:10] Red lands a clean elbow.\n[1:02] The referee stops the fight.\n"
            self.assertTrue(widget.tag_ranges("impact"))
            self.assertTrue(widget.tag_ranges("finish"))
            self.assertNotEqual(widget.tag_cget("impact", "background"), str(widget.cget("background")))
            self.assertNotEqual(widget.tag_cget("finish", "background"), str(widget.cget("background")))
            self.assertGreater(int(widget.tag_cget("finish", "spacing1")), 0)
            configure_fight_timeline(widget, dict(colors, panel="#eeeeee", text="#eeeeee"), 13)
            self.assertEqual(widget.get("1.0", "end-1c"), expected)
            self.assertEqual(colors, original)
            self.assertEqual(random.getstate(), before_rng)
            with self.assertRaises(ValueError):
                insert_fight_timeline_line(widget, "Keep this out", tag="invented")
            self.assertEqual(widget.get("1.0", "end-1c"), expected)
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
