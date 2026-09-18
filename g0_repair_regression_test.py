"""Focused checks for the first G0 correctness/presentation repair slice."""

import tkinter as tk
import unittest
from unittest.mock import patch

from main import FightEmpireApp


class G0RepairTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = FightEmpireApp(self.root)

    def tearDown(self):
        self.root.destroy()

    def test_media_preview_calls_exposure_a_score_not_probability(self):
        preview = self.app.media_action_preview("Press Tour", self.app.roster[0])
        self.assertIn("Exposure", preview)
        self.assertNotIn("risk", preview.lower())
        self.assertNotIn("%", preview)

    def test_media_preview_reprices_popularity_dependent_action(self):
        fighter = self.app.roster[0]
        fighter.popularity = 40
        low = self.app.media_action_preview("Press Tour", fighter)
        fighter.popularity = 90
        high = self.app.media_action_preview("Press Tour", fighter)
        self.assertIn("$12,000", low)
        self.assertIn("$22,000", high)

    def test_sponsor_capacity_does_not_discard_existing_deal(self):
        finance = self.app.ensure_player_media_state()
        finance["sponsor_deals"] = [{"name": f"Existing {index}", "category": f"Category {index}", "fee": 1000} for index in range(8)]
        offer = {"id": "capacity-offer", "name": "New Brand", "category": "New Category", "fee": 2000, "months": 12}
        finance["sponsor_offers"] = [offer]
        with patch.object(self.app, "selected_sponsor_offer", return_value=offer), \
             patch.object(self.app, "refresh_finance"), \
             patch.object(self.app, "refresh_all"):
            accepted = self.app.accept_sponsor_offer()
        self.assertFalse(accepted[0])
        self.assertEqual(len(finance["sponsor_deals"]), 8)
        self.assertEqual(finance["sponsor_deals"][0]["name"], "Existing 0")

    def test_stacked_matchmaking_keeps_fighter_rows_reachable(self):
        self.root.deiconify()
        self.root.geometry("1280x760")
        self.app.ensure_screen_built("booking")
        self.app.tabs.select(self.app.tab_pages["booking"])
        self.root.update()
        self.root.after(1500, self.root.quit)
        self.root.mainloop()
        self.root.update()
        self.assertEqual(self.app.booking_horizontal_split.cget("orient"), "vertical")
        # Four 20px-ish Treeview rows should remain visible after the card
        # summary and filter/action controls have been laid out.
        self.assertGreaterEqual(self.app.available_tree.winfo_height(), 60)


if __name__ == "__main__":
    unittest.main()
