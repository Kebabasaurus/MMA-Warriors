"""ID-linked rematches must balance closeness, cooldown and series fatigue."""
import unittest
from world import WorldMixin
from persistence_regression_test import fighter


class CardTests(unittest.TestCase):
    def setUp(self):
        self.host = WorldMixin()
        self.host.month = 12
        self.host.matchup_history_summary = lambda *args: (2, 8)
        self.host.mutual_rivalry_between = lambda *args: True
        self.a = fighter(name="Alpha", fighter_id="alpha")
        self.b = fighter(name="Beta", fighter_id="beta")

    def history(self, cards, results=("W", "W"), month=8):
        self.a.bout_rating_history = [
            {"opponent_id": "beta", "result": result, "date": f"Month {month-i} Week 1", "scorecard": cards}
            for i, result in enumerate(results)]

    def test_sweeps_blocked_despite_title_and_heat(self):
        self.history("30-27 / 30-27 / 30-27")
        self.a.rivalry_rematch_due = True
        self.a.rivalry_heat = self.b.rivalry_heat = 100
        self.assertTrue(self.host.ai_matchup_is_stale(self.a, self.b, title=True))

    def test_close_decisions_qualify(self):
        for cards in ("29-28 / 28-29 / 29-28", "29-28 / 29-28 / 30-27"):
            self.history(cards)
            self.assertFalse(self.host.ai_matchup_is_stale(self.a, self.b))

    def test_draw_cooldown_and_repeat_limit(self):
        self.history("-", ("D",), 11)
        self.assertTrue(self.host.ai_matchup_is_stale(self.a, self.b))
        self.history("-", ("D",), 8)
        self.assertFalse(self.host.ai_matchup_is_stale(self.a, self.b))
        self.history("-", ("D", "D", "D"), 8)
        self.assertTrue(self.host.ai_matchup_is_stale(self.a, self.b))

    def test_unknown_scores_and_duplicate_names(self):
        self.history("-")
        self.assertFalse(self.host.ai_rematch_evidence(self.a, self.b)["close"])
        self.assertIsNone(self.host.ai_rematch_evidence(self.a, fighter(name="Beta", fighter_id="other")))

    def test_title_merit_and_comeback(self):
        for wins, losses, streak, eligible in ((1, 5, 1, False), (0, 0, 0, False),
                                               (5, 3, 1, True), (3, 4, 0, False),
                                               (4, 5, 3, True)):
            with self.subTest(record=(wins, losses, streak)):
                self.a.record_w, self.a.record_l = wins, losses
                self.a.career_win_streak = streak
                self.a.owed_title_shot = True
                self.assertEqual(eligible, self.host.ai_title_challenger_is_eligible(self.a))

    def test_close_series_needs_a_break_after_three_meetings(self):
        self.history("29-28 / 28-29 / 29-28", ("W", "L", "W"), 8)
        self.assertTrue(self.host.ai_matchup_is_stale(self.a, self.b, title=True))
        self.host.month = 20
        self.assertFalse(self.host.ai_matchup_is_stale(self.a, self.b, title=True))


if __name__ == "__main__":
    unittest.main()
