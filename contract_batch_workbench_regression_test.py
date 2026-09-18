"""Regression coverage for the J3 contract batch review/commit slice."""

import json
import random
import unittest
from types import SimpleNamespace

from contract_batch_workbench import ContractBatchWorkbenchMixin
from feature_foundation import FoundationMixin


def fighter(fid, name, *, months=1, purse=10_000, popularity=40, champion=False, retired=False):
    return SimpleNamespace(
        fighter_id=fid, name=name, age=29, purse=purse, popularity=popularity,
        momentum=0, champion=champion, exclusive=True, contract_months=months,
        guaranteed_fights=3, contract_fights_completed=0, retired=retired,
        retirement_pending=False, morale=70, relationship_trust=70,
        champions_clause=champion, title_shot_clause=False,
        main_event_promise=False, top_opponent_promise=False,
    )


class Harness(ContractBatchWorkbenchMixin, FoundationMixin):
    def __init__(self):
        self.month, self.week = 4, 2
        self.cash = 500_000
        self.roster = [
            fighter("f-1", "Champion", months=1, champion=True, popularity=70),
            fighter("f-2", "Contender", months=3, popularity=45),
            fighter("f-3", "Secure", months=12, popularity=20),
        ]
        self.ensure_contract_batch_state()
        self.ensure_foundation_state()

    def fighter_identity_key(self, value):
        return value.fighter_id

    def resolve_fighter(self, reference):
        return next((row for row in self.roster if row.fighter_id == str(reference)), None)

    def player_monthly_office_cost(self):
        return 5000

    def strategic_investment_upkeep(self):
        return 1000


class ContractBatchWorkbenchTests(unittest.TestCase):
    def test_quote_is_explicit_pure_identity_deduplicated_and_explains_exposure(self):
        app = Harness()
        before = random.getstate()
        ok, _note, batch = app.create_contract_batch([app.roster[1], app.roster[1], "f-2", app.roster[0], "f-3"])
        self.assertTrue(ok)
        self.assertEqual(before, random.getstate())
        self.assertEqual([row["fighter_id"] for row in batch["rows"]], ["f-1", "f-2", "f-3"])
        self.assertGreater(batch["total_required_cash"], 0)
        self.assertGreater(batch["total_guaranteed_exposure"], batch["total_required_cash"])
        self.assertTrue(any("optional" in caution.lower() for caution in batch["rows"][2]["cautions"]))

    def test_malformed_retained_contract_facts_fail_closed_in_quote(self):
        app = Harness()
        app.roster[0].purse = float("inf")
        app.roster[0].popularity = "not-a-number"
        app.roster[0].momentum = float("nan")
        app.roster[0].contract_months = float("inf")
        before = random.getstate()
        ok, _note, batch = app.create_contract_batch([app.roster[0]])
        self.assertTrue(ok)
        self.assertEqual(random.getstate(), before)
        row = batch["rows"][0]
        self.assertEqual(row["quoted_status"], "Expired")
        self.assertGreaterEqual(row["required_cash"], 0)
        self.assertGreaterEqual(row["guaranteed_exposure"], 0)

    def test_review_preserves_saved_quote_when_identity_changes(self):
        app = Harness()
        _ok, _note, batch = app.create_contract_batch(["f-1", "f-2"])
        original = json.loads(json.dumps(batch["rows"]))
        app.roster[1].contract_months = 0
        review = app.review_contract_batch(batch["batch_id"])
        row = next(item for item in review["review_rows"] if item["fighter_id"] == "f-2")
        self.assertEqual(row["current_status"], "Eligible")
        self.assertIn("changed", row["current_reason"])
        self.assertEqual(app.contract_batch_snapshot(batch["batch_id"])["rows"], original)

    def test_partial_commit_seals_each_row_and_repeat_does_not_rerun(self):
        app = Harness()
        calls = []

        def execute(fighter_obj, _row):
            calls.append(fighter_obj.fighter_id)
            if fighter_obj.fighter_id == "f-1":
                return {"renewed": 1, "failed": 0, "results": [{"name": fighter_obj.name, "status": "renewed", "months": 18, "purse": 20_000}]}
            return {"renewed": 0, "failed": 1, "results": [{"name": fighter_obj.name, "status": "failed", "reason": "camp rejected package"}]}

        app.contract_batch_executor = execute
        _ok, _note, batch = app.create_contract_batch(["f-1", "f-2"])
        ok, note, sealed = app.commit_contract_batch(batch["batch_id"])
        self.assertTrue(ok)
        self.assertIn("1 renewed", note)
        self.assertEqual(sealed["status"], "Partial")
        self.assertEqual(calls, ["f-1", "f-2"])
        first_receipts = [row["receipt_id"] for row in sealed["results"]]
        ok, repeat_note, repeated = app.commit_contract_batch(batch["batch_id"])
        self.assertTrue(ok)
        self.assertIn("already sealed", repeat_note)
        self.assertEqual(calls, ["f-1", "f-2"])
        self.assertEqual(first_receipts, [row["receipt_id"] for row in repeated["results"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
