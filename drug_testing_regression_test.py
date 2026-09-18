"""Regression coverage for the first durable drug-testing case boundary."""

import random
import unittest
from copy import deepcopy
from unittest.mock import patch

from models import Fighter
from views import ViewMixin


class DrugTestingHarness(ViewMixin):
    def __init__(self):
        self.month, self.week = 7, 3
        self.player_company_name = "Compliance FC"
        self.cash = 100_000
        self.rules = {"drug_testing": "Standard"}
        self.roster = [
            Fighter(
                name="Sample Fighter", weight="Lightweight", age=28,
                record_w=5, record_l=1, striking=70, wrestling=68,
                grappling=66, cardio=72, chin=70, popularity=40,
                momentum=0, morale=70, purse=10_000,
                fighter_id="fighter-sample", injured=0,
            ),
        ]
        self.finance = {"drug_test_cost": 2_500, "ledger": []}
        self.inbox = []
        self.transactions = []
        self.refreshes = 0
        self.drug_testing_state = self._default_drug_testing_state()

    def staff_effect(self, _role, _default=0):
        return 0

    def record_finance_transaction(self, label, **kwargs):
        self.transactions.append((label, kwargs))

    def refresh_all(self):
        self.refreshes += 1


class DrugTestingRegressionTests(unittest.TestCase):
    def test_preliminary_positive_is_durable_and_never_becomes_injury(self):
        app = DrugTestingHarness()
        before = (app.cash, app.roster[0].injured)
        with patch("views.random.sample", return_value=list(app.roster)), patch(
            "views.random.random", return_value=0.0,
        ):
            cases = app.run_drug_tests()

        self.assertEqual(len(cases), 1)
        case = cases[0]
        self.assertEqual(case["preliminary_result"], "preliminary_positive")
        self.assertEqual(case["status"], "Preliminary review")
        self.assertFalse(case["injury_effect_applied"])
        self.assertEqual(case["provider_snapshot"]["provider_id"], "legacy-promotion-testing")
        self.assertEqual(case["policy_snapshot"]["policy_id"], "Standard")
        self.assertEqual(case["sample_count"], 1)
        self.assertEqual(case["quote_snapshot"]["actual_total"], 2_500)
        self.assertEqual((app.cash, app.roster[0].injured), (97_500, before[1]))
        self.assertIn("not a proven violation", app.inbox[-1]["body"])
        self.assertEqual(len(app.drug_testing_case_rows()), 1)

    def test_case_identity_is_idempotent_and_readers_are_defensive(self):
        app = DrugTestingHarness()
        first = app.record_drug_testing_case(
            app.roster[0], test_id="drug-test-0007-03-000001",
            result="negative", policy="Standard",
        )
        second = app.record_drug_testing_case(
            app.roster[0], test_id="drug-test-0007-03-000001",
            result="positive", policy="Strict",
        )
        self.assertEqual(first, second)
        rows = app.drug_testing_case_rows()
        rows[0]["fighter"] = "mutated"
        rows[0]["future_field"] = "local only"
        rows[0]["provider_snapshot"]["name"] = "mutated"
        self.assertEqual(app.drug_testing_case_details(first["case_id"])["fighter"], "Sample Fighter")
        self.assertNotIn("future_field", app.drug_testing_case_details(first["case_id"]))
        self.assertEqual(app.drug_testing_case_details(first["case_id"])["provider_snapshot"]["name"], "Promotion Testing Desk")
        self.assertEqual(app.drug_testing_summary()["closed_negative"], 1)

    def test_idless_duplicate_fighters_get_distinct_durable_case_references(self):
        app = DrugTestingHarness()
        first = app.roster[0]
        second = deepcopy(first)
        first.fighter_id = ""
        second.fighter_id = ""
        app.roster.append(second)

        first_case = app.record_drug_testing_case(
            first, test_id="drug-test-legacy-0001", result="negative", policy="Standard",
        )
        second_case = app.record_drug_testing_case(
            second, test_id="drug-test-legacy-0001", result="negative", policy="Standard",
        )

        self.assertNotEqual(first_case["case_id"], second_case["case_id"])
        self.assertNotEqual(first_case["fighter_reference"], second_case["fighter_reference"])
        self.assertEqual(first_case["fighter_id"], "")
        self.assertEqual(second_case["fighter_id"], "")
        self.assertTrue(first_case["fighter_reference"].startswith("legacy:"))
        self.assertTrue(second_case["fighter_reference"].endswith("#2"))
        self.assertEqual(
            len(app.drug_testing_case_rows(fighter_id=second_case["fighter_reference"])), 1
        )
        self.assertEqual(
            app.record_drug_testing_case(
                first, test_id="drug-test-legacy-0001", result="positive", policy="Strict",
            ),
            first_case,
        )
        self.assertEqual(len(app.drug_testing_case_rows()), 2)

    def test_none_policy_does_not_sample_charge_or_change_cases(self):
        app = DrugTestingHarness()
        app.rules["drug_testing"] = "None"
        rng_before = random.getstate()
        with patch("views.random.sample", side_effect=AssertionError("disabled testing sampled")), patch(
            "views.random.random", side_effect=AssertionError("disabled testing rolled"),
        ):
            result = app.run_drug_tests()
        self.assertEqual(result, [])
        self.assertEqual(app.cash, 100_000)
        self.assertEqual(app.drug_testing_case_rows(), [])
        self.assertEqual(random.getstate(), rng_before)
        self.assertIn("no random test roll", app.inbox[-1]["body"])

    def test_explicit_policy_cycle_recovers_unknown_saved_label(self):
        app = DrugTestingHarness()
        app.rules["drug_testing"] = "retired-policy"
        app.cycle_drug_testing()
        self.assertEqual(app.rules["drug_testing"], "Standard")
        self.assertIn("unavailable", app.inbox[-1]["body"].lower())
        self.assertEqual(app.refreshes, 1)

    def test_explicit_policy_cycle_recovers_malformed_rules_envelope(self):
        app = DrugTestingHarness()
        app.rules = ["malformed"]
        app.cycle_drug_testing()
        self.assertEqual(app.rules, {"drug_testing": "Standard"})
        self.assertIn("unavailable", app.inbox[-1]["body"].lower())
        self.assertEqual(app.refreshes, 1)

    def test_unfunded_manual_run_fails_before_sampling_or_case_identity(self):
        app = DrugTestingHarness()
        app.cash = 1_000
        before_state = repr(app.drug_testing_state)
        before_rng = random.getstate()
        with patch("views.random.sample", side_effect=AssertionError("unfunded testing sampled")), patch(
            "views.random.random", side_effect=AssertionError("unfunded testing rolled"),
        ):
            result = app.run_drug_tests()
        self.assertEqual(result, [])
        self.assertEqual(app.cash, 1_000)
        self.assertEqual(repr(app.drug_testing_state), before_state)
        self.assertEqual(random.getstate(), before_rng)
        self.assertIn("no samples", app.inbox[-1]["body"].lower())

    def test_malformed_finance_fails_closed_before_sampling_or_case_identity(self):
        app = DrugTestingHarness()
        app.finance = ["malformed"]
        before_cash = app.cash
        before_state = repr(app.drug_testing_state)
        before_rng = random.getstate()
        with patch("views.random.sample", side_effect=AssertionError("malformed finance sampled")), patch(
            "views.random.random", side_effect=AssertionError("malformed finance rolled"),
        ):
            result = app.run_drug_tests()
        self.assertEqual(result, [])
        self.assertEqual(app.cash, before_cash)
        self.assertEqual(repr(app.drug_testing_state), before_state)
        self.assertEqual(random.getstate(), before_rng)
        self.assertIn("retained testing-cost record is unavailable", app.inbox[-1]["body"])

    def test_unavailable_saved_testing_contract_fails_before_charge_or_rng(self):
        for field, value, expected in (
            ("policy", "retired-policy", "policy"),
            ("provider", "retired-provider", "provider"),
            ("rules", ["malformed"], "rules"),
            ("cases", [{"case_id": "retained"}, "malformed"], "case evidence"),
        ):
            app = DrugTestingHarness()
            if field == "policy":
                app.rules["drug_testing"] = value
            elif field == "provider":
                app.drug_testing_state["provider_id"] = value
            elif field == "cases":
                app.drug_testing_state["cases"] = value
            else:
                app.rules = value
            before_cash = app.cash
            before_state = repr(app.drug_testing_state)
            before_rng = random.getstate()
            with patch("views.random.sample", side_effect=AssertionError("unavailable contract sampled")), patch(
                "views.random.random", side_effect=AssertionError("unavailable contract rolled"),
            ):
                result = app.run_drug_tests()
            self.assertEqual(result, [])
            self.assertEqual(app.cash, before_cash)
            self.assertEqual(repr(app.drug_testing_state), before_state)
            self.assertEqual(random.getstate(), before_rng)
            self.assertIn(expected, app.inbox[-1]["body"].lower())

    def test_nonfinite_cash_fails_closed_before_sampling_or_case_identity(self):
        app = DrugTestingHarness()
        app.cash = float("inf")
        before_state = repr(app.drug_testing_state)
        before_rng = random.getstate()
        with patch("views.random.sample", side_effect=AssertionError("nonfinite cash sampled")), patch(
            "views.random.random", side_effect=AssertionError("nonfinite cash rolled"),
        ):
            result = app.run_drug_tests()
        self.assertEqual(result, [])
        self.assertEqual(app.cash, float("inf"))
        self.assertEqual(repr(app.drug_testing_state), before_state)
        self.assertEqual(random.getstate(), before_rng)
        self.assertIn("no samples", app.inbox[-1]["body"].lower())

    def test_staff_discount_and_policy_are_frozen_on_each_case(self):
        app = DrugTestingHarness()
        app.rules["drug_testing"] = "Olympic"
        app.staff_effect = lambda _role, _default=0: 18
        with patch("views.random.sample", return_value=list(app.roster)), patch(
            "views.random.random", return_value=0.99,
        ):
            app.run_drug_tests()
        self.assertEqual(app.cash, 97_750)  # 2,500 × (1 − 18/180)
        case = app.drug_testing_case_rows()[0]
        self.assertEqual(case["policy"], "Olympic")
        self.assertEqual(case["provider_id"], "legacy-promotion-testing")
        self.assertEqual(case["policy_snapshot"]["policy_id"], "Olympic")
        self.assertEqual(case["sample_count"], 1)
        self.assertEqual(case["quote_snapshot"]["actual_total"], 2_250)
        self.assertEqual(case["quote_snapshot"]["staff_discount"], 0.1)
        self.assertEqual(case["sanction_status"].split(" — ")[0], "None")

    def test_manual_commission_uses_saved_provider_and_sample_selection(self):
        app = DrugTestingHarness()
        # The provider window is an explicit planning/selection boundary.  A
        # later manual commission must use the same provider and sample count
        # that the player reviewed, rather than silently reverting to the
        # legacy six-sample provider.
        ok, _message, _config = app.set_drug_testing_provider_selection(
            "national-compliance-network", 1,
        )
        self.assertTrue(ok)
        with patch("views.random.sample", return_value=list(app.roster)), patch(
            "views.random.random", return_value=0.99,
        ):
            cases = app.run_drug_tests()

        self.assertEqual(len(cases), 1)
        case = cases[0]
        self.assertEqual(case["provider_id"], "national-compliance-network")
        self.assertEqual(case["provider_snapshot"]["provider_id"], "national-compliance-network")
        self.assertEqual(case["sample_count"], 1)
        self.assertEqual(case["quote_snapshot"]["amount"], 3_750)
        self.assertEqual(case["quote_snapshot"]["actual_total"], 3_750)
        self.assertEqual(case["quote_snapshot"]["staff_discount"], 0.0)
        self.assertEqual(app.cash, 96_250)
        self.assertIn("National Compliance Network", app.inbox[-1]["body"])

    def test_manual_commission_bounds_saved_sample_count_to_roster(self):
        app = DrugTestingHarness()
        ok, _message, _config = app.set_drug_testing_provider_selection(
            "regional-integrity-labs", 100,
        )
        self.assertTrue(ok)
        with patch("views.random.sample", return_value=list(app.roster)) as sample, patch(
            "views.random.random", return_value=0.99,
        ):
            cases = app.run_drug_tests()

        self.assertEqual(len(cases), 1)
        sample.assert_called_once_with(app.roster, k=1)
        self.assertEqual(cases[0]["sample_count"], 1)
        self.assertEqual(cases[0]["quote_snapshot"]["amount"], 3_125)


if __name__ == "__main__":
    unittest.main(verbosity=2)
