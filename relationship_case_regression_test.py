"""Regression coverage for evidence-linked Talent Relations cases."""

import unittest
from types import SimpleNamespace

from models import Fighter
from world import WorldMixin


class RelationshipHarness(WorldMixin):
    def __init__(self):
        self.month, self.week = 5, 2
        self.player_company_name = "Case FC"
        self.player_region = "USA"
        self.cash = 100_000
        self.rules = {}
        self.roster = []
        self.free_agents = []
        self.retired_fighters = []
        self.promotions = []
        self.story_threads = []
        self._story_thread_index = {}
        self.relationship_cases = []
        self.finance = {"other": 0}

    def fighter_company_name(self, fighter):
        return "Case FC" if fighter in self.roster else "Rival FC" if any(fighter in getattr(promo, "roster", []) for promo in self.promotions) else "Independent"


def fighter(name, fighter_id):
    return Fighter(name, "Lightweight", 29, 12, 3, 70, 64, 62, 68, 66, 45, 1, 78, 15000, fighter_id=fighter_id)


class RelationshipCaseTests(unittest.TestCase):
    def setUp(self):
        self.app = RelationshipHarness()
        self.alex = fighter("Alex North", "FTR-A")
        self.blair = fighter("Blair North", "FTR-B")
        self.alex.main_event_promise = True
        self.alex.top_opponent_promise = True
        self.alex.promise_deadline_month = 9
        self.app.roster = [self.alex, self.blair]

    def test_open_is_source_backed_and_repeated_open_does_not_duplicate(self):
        ok, case = self.app.open_relationship_case(self.alex)
        self.assertTrue(ok)
        self.assertEqual(case["source_kind"], "Contract Promise")
        self.assertEqual(case["original_obligations"], ["main-event", "top-opponent"])
        ok, same = self.app.open_relationship_case(self.alex)
        self.assertTrue(ok)
        self.assertEqual(same["case_id"], case["case_id"])
        self.assertEqual(len(self.app.relationship_cases), 1)

    def test_partial_delivery_and_explicit_action_have_no_benefit(self):
        ok, case = self.app.open_relationship_case(self.alex)
        self.assertTrue(ok)
        before = (self.alex.morale, self.alex.relationship_trust, self.app.cash)
        self.alex.main_event_promise = False
        model = self.app.relationship_case_read_model(case)
        self.assertEqual(model["status"], "Partially delivered")
        self.assertEqual(model["delivered_obligations"], ["main-event"])
        self.assertTrue(self.app.acknowledge_relationship_case(case["case_id"])[0])
        self.assertTrue(self.app.acknowledge_relationship_case(case["case_id"])[0])
        self.assertTrue(self.app.select_relationship_case_action(case["case_id"], "review_contract")[0])
        self.assertEqual((self.alex.morale, self.alex.relationship_trust, self.app.cash), before)

    def test_departure_closes_case_without_losing_duplicate_name_identity(self):
        ok, case = self.app.open_relationship_case(self.alex)
        self.assertTrue(ok)
        self.app.roster = [self.blair]
        self.app.retired_fighters = [self.alex]
        self.alex.retired = True
        ok, model = self.app.review_relationship_case(case["case_id"])
        self.assertTrue(ok)
        self.assertEqual(model["status"], "Closed - departed")
        self.assertEqual(model["fighter_id"], "FTR-A")
        self.assertEqual(model["fighter_name"], "Alex North")
        self.assertEqual(self.app.relationship_cases[0]["resolution"], model["resolution"])

    def test_transfer_is_visible_without_rewriting_the_original_case(self):
        ok, case = self.app.open_relationship_case(self.alex)
        self.assertTrue(ok)
        self.app.roster = [self.blair]
        self.app.promotions = [SimpleNamespace(name="Rival FC", roster=[self.alex])]
        model = self.app.relationship_case_read_model(case)
        self.assertEqual(model["status"], "Transferred")
        self.assertIn("Case FC", model["resolution"])
        self.assertIn("Rival FC", model["resolution"])

    def test_case_reader_does_not_normalise_malformed_saved_rows(self):
        self.app.relationship_cases = [{
            "case_id": "legacy-case", "fighter_id": "FTR-A",
            "status": "Unknown status", "review_month": float("inf"),
            "created_week": float("nan"), "updated_week": "bad",
            "history": "not-a-list", "evidence_refs": "not-a-list",
            "original_obligations": "not-a-list",
        }, "not-a-case"]
        before = repr(self.app.relationship_cases)
        rows = self.app.relationship_case_rows()
        retained = self.app.relationship_cases_read_model()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "Open")
        self.assertEqual(rows[0]["review_month"], 0)
        self.assertEqual(retained[0]["evidence_refs"], [])
        self.assertEqual(retained[0]["original_obligations"], [])
        direct = self.app.relationship_case_read_model(self.app.relationship_cases[0])
        self.assertEqual(direct["review_month"], 0)
        self.assertEqual(direct["delivered_obligations"], [])
        self.assertEqual(repr(self.app.relationship_cases), before)

    def test_idless_case_ids_are_position_independent_and_duplicate_safe(self):
        rows = [
            {
                "fighter_id": "FTR-A", "fighter_name": "Alex North",
                "company_at_open": "Case FC", "source_kind": "Contract Promise",
                "source_ref": "promise:FTR-A", "review_month": 9,
                "created_week": 14, "original_obligations": ["main-event"],
            },
            {
                "fighter_id": "FTR-B", "fighter_name": "Blair North",
                "company_at_open": "Case FC", "source_kind": "Career Journey",
                "source_ref": "arc:FTR-B", "review_month": 10,
                "created_week": 15, "original_obligations": ["Title Path"],
            },
            {
                "fighter_id": "FTR-A", "fighter_name": "Alex North",
                "company_at_open": "Case FC", "source_kind": "Contract Promise",
                "source_ref": "promise:FTR-A", "review_month": 9,
                "created_week": 14, "original_obligations": ["main-event"],
            },
        ]
        self.app.relationship_cases = [dict(row) for row in rows]
        first = self.app.relationship_cases_read_model()
        first_by_key = {(row["fighter_id"], row["source_kind"], index): row["case_id"] for index, row in enumerate(first)}

        self.app.relationship_cases = [dict(rows[1]), dict(rows[2]), dict(rows[0])]
        reordered = self.app.relationship_cases_read_model()
        reordered_ids = {}
        for row in reordered:
            key = (row["fighter_id"], row["source_kind"])
            reordered_ids.setdefault(key, []).append(row["case_id"])

        self.assertEqual(first_by_key[("FTR-B", "Career Journey", 1)], reordered_ids[("FTR-B", "Career Journey")][0])
        self.assertEqual(first_by_key[("FTR-A", "Contract Promise", 0)], reordered_ids[("FTR-A", "Contract Promise")][0])
        self.assertEqual(len({row["case_id"] for row in first}), 3)
        self.assertTrue(first[2]["case_id"].endswith("#2"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
