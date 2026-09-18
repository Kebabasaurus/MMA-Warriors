"""Regression coverage for ID-safe recruitment decision packs."""

import unittest
from copy import deepcopy

from models import Fighter
from world import WorldMixin


class PackHarness(WorldMixin):
    def __init__(self):
        self.month, self.week = 4, 2
        self.player_company_name = "Pack FC"
        self.player_region = "USA"
        self.rules = {"scouting_mode": True}
        self.roster = []
        self.free_agents = []
        self.retired_fighters = []
        self.promotions = []
        self.scouting_reports = {}
        self.scouting_shortlist = []
        self.scouting_watchlists = []
        self.scouting_decision_packs = []
        self._scouting_state_migrated = False

    def scouting_target_company_for(self, fighter):
        return "Free Agent" if fighter in self.free_agents else "Independent"


def fighter(name, fighter_id):
    return Fighter(name, "Lightweight", 27, 8, 2, 70, 64, 60, 68, 66, 42, 2, 72, 12000, fighter_id=fighter_id)


class RecruitmentDecisionPackTests(unittest.TestCase):
    def setUp(self):
        self.app = PackHarness()
        self.a = fighter("Alex North", "FTR-A")
        self.b = fighter("Blair South", "FTR-B")
        self.c = fighter("Casey East", "FTR-C")
        self.app.free_agents = [self.a, self.b, self.c]
        self.app.scouting_reports[self.a.fighter_id] = {
            "fighter_id": self.a.fighter_id, "fighter_name": self.a.name, "kind": "full", "status": "Complete",
            "completed_week": 15, "confidence": 82, "reveal": 82, "estimates": {
                "overall": {"low": 67, "mid": 70, "high": 73}, "potential": {"low": 78, "mid": 82, "high": 87}
            }, "notes": ["Strong striking base"],
        }

    def test_pack_requires_two_to_four_ids_and_captures_evidence_once(self):
        before = deepcopy(self.app.scouting_reports)
        self.assertFalse(self.app.create_scouting_decision_pack("Too Small", "", [self.a.fighter_id])[0])
        ok, pack = self.app.create_scouting_decision_pack(
            "Headliner shortlist", "Who fits the next lightweight main event?",
            [self.a.fighter_id, self.b.fighter_id], "WATCH-main",
        )
        self.assertTrue(ok)
        self.assertEqual(pack["decision_state"], "Considering")
        self.assertEqual(pack["candidate_ids"], ["FTR-A", "FTR-B"])
        self.assertEqual(pack["candidate_snapshots"]["FTR-A"]["report"]["status"], "Complete")
        # The first operation may run the existing scouting migration, which
        # appends neutral schema bookkeeping. Evidence and estimates must stay
        # byte-for-byte equivalent.
        self.assertEqual(self.app.scouting_reports["FTR-A"]["estimates"], before["FTR-A"]["estimates"])
        self.assertEqual(self.app.scouting_reports["FTR-A"]["notes"], before["FTR-A"]["notes"])

    def test_state_and_notes_are_explicit_and_read_model_is_safe(self):
        ok, pack = self.app.create_scouting_decision_pack("Roster opening", "", ["FTR-A", "FTR-B"])
        self.assertTrue(ok)
        ok, updated = self.app.update_scouting_decision_pack(pack["pack_id"], state="Ready for negotiation", notes={"FTR-A": "Ask about availability."})
        self.assertTrue(ok)
        self.assertEqual(updated["decision_state"], "Ready for negotiation")
        model = self.app.scouting_decision_pack_read_model(updated)
        self.assertEqual(model["decision_state"], "Ready for negotiation")
        self.assertEqual(model["candidates"][0]["player_note"], "Ask about availability.")
        self.assertFalse(self.app.update_scouting_decision_pack(pack["pack_id"], state="Automatic signing")[0])

    def test_idless_pack_ids_are_position_independent_and_duplicate_safe(self):
        rows = [
            {
                "name": "Lightweight options", "purpose": "Main event",
                "watchlist_id": "WATCH-main", "candidate_ids": ["FTR-A", "FTR-B"],
                "created_week": 12,
            },
            {
                "name": "Welterweight options", "purpose": "Backup list",
                "watchlist_id": "WATCH-main", "candidate_ids": ["FTR-B", "FTR-C"],
                "created_week": 13,
            },
            {
                "name": "Lightweight options", "purpose": "Main event",
                "watchlist_id": "WATCH-main", "candidate_ids": ["FTR-A", "FTR-B"],
                "created_week": 12,
            },
        ]
        self.app.scouting_decision_packs = [dict(row) for row in rows]
        first = self.app.ensure_scouting_decision_packs()
        first_by_key = {
            (row["name"], row["created_week"]): row["pack_id"]
            for row in first if row["created_week"] == 13
        }
        duplicate_ids = [row["pack_id"] for row in first if row["created_week"] == 12]
        self.app.scouting_decision_packs = [dict(rows[2]), dict(rows[0]), dict(rows[1])]
        reordered = self.app.ensure_scouting_decision_packs()
        reordered_backup = next(row for row in reordered if row["created_week"] == 13)
        self.assertEqual(reordered_backup["pack_id"], first_by_key[("Welterweight options", 13)])
        self.assertEqual(
            {row["pack_id"] for row in reordered if row["created_week"] == 12},
            set(duplicate_ids),
        )
        self.assertEqual(len({row["pack_id"] for row in first}), 3)
        self.assertTrue(any(row["pack_id"].endswith("#2") for row in first))

    def test_departed_candidate_remains_as_historical_snapshot(self):
        ok, pack = self.app.create_scouting_decision_pack("Alternatives", "", ["FTR-A", "FTR-B"])
        self.assertTrue(ok)
        self.app.free_agents = [self.b]
        model = self.app.scouting_decision_pack_read_model(pack)
        departed = next(row for row in model["candidates"] if row["fighter_id"] == "FTR-A")
        self.assertFalse(departed["available"])
        self.assertEqual(departed["warning"], "Retired or unavailable")
        self.assertEqual(departed["name"], "Alex North")
        self.assertEqual(departed["captured_report"]["status"], "Complete")


if __name__ == "__main__":
    unittest.main(verbosity=2)
