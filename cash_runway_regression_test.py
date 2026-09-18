"""Regression coverage for the read-only promotion cash runway."""

import random
import unittest
from types import SimpleNamespace

from world import WorldMixin


class RunwayHarness(WorldMixin):
    def __init__(self, with_events=True):
        self.month, self.week = 1, 4
        self.cash = 100_000
        self.player_company_name = "Player FC"
        self.player_region = "USA"
        self.company_pop = 56
        self.company_stability = 70
        self.rules = {"drug_testing": "Standard"}
        self.staff = [{"name": "Bookkeeper", "role": "Finance", "salary": 5_000}]
        self.academy = {"owned": True, "weekly_cost": 4_500}
        self.finance = {
            "ticket_price": 55, "sponsor_income": 12_000, "merch_rate": 0.12,
            "monthly_office": 12_000, "staff_payroll": 5_000, "marketing_budget": 18_000,
            "production_base": 24_000, "medical_base": 9_000, "drug_test_cost": 2_500,
            "tax_rate": 0.18, "media_rights": {"fee": 8_000, "events_remaining": 4},
            "sponsor_deals": [], "strategic_investments": {},
            "week_transactions": [{"month": 1, "week": 4, "costs": 1_250, "revenue": 0}],
        }
        red = SimpleNamespace(name="Red", purse=7_500, popularity=60)
        blue = SimpleNamespace(name="Blue", purse=6_500, popularity=58)
        self._fighters = (red, blue)
        self.scheduled_events = [
            {"event_id": "event-one", "name": "Spring Card", "month": 2, "week": 1,
             "venue": "Regional Arena", "fights": [{"red": red, "blue": blue}]},
            {"event_id": "event-two", "name": "Second Card", "month": 2, "week": 2,
             "venue": "Regional Arena", "fights": [{"red": red, "blue": blue}]},
            {"event_id": "cancelled", "name": "Cancelled Card", "month": 2, "week": 3,
             "cancelled": True, "fights": [{"red": red, "blue": blue}]},
        ] if with_events else []

    def event_fight_fighters(self, fight):
        return [fighter for fighter in (fight.get("red"), fight.get("blue")) if fighter]

    def fight_hype(self, _a, _b, _fight):
        return 80

    def regional_market_score(self, _region):
        return 1.0

    def event_fair_ticket_price(self, _hype, _pull, _venue):
        return 55

    def ticket_price_demand_factor(self, _price, _fair):
        return 1.0

    def marketing_demand_factor(self, _budget):
        return 1.0

    def venue_capacity_for(self, _venue):
        return 1_000

    def resolve_event_production_tier(self, _event):
        return "Standard", {"cost": 1.0, "atmosphere": 0.0}

    def event_grudge_gate_bonus(self, _event):
        return 0.0


class CashRunwayTests(unittest.TestCase):
    def test_runway_is_state_and_rng_stable_with_split_scenarios(self):
        app = RunwayHarness()
        before = (repr(app.finance), repr(app.scheduled_events), app.cash, random.getstate())
        forecast = app.player_cash_runway_forecast(4)
        after = (repr(app.finance), repr(app.scheduled_events), app.cash, random.getstate())
        self.assertEqual(before, after)
        self.assertEqual(len(forecast["rows"]), 4)
        self.assertEqual(forecast["already_paid"], 1_250)
        self.assertEqual([item["event_id"] for item in forecast["events"]], ["event-one", "event-two"])
        first, second = forecast["rows"][0], forecast["rows"][1]
        self.assertGreater(first["fixed_bills"], 0)  # month rollover bill + academy
        self.assertGreater(second["event_commitments"], 0)
        self.assertGreater(first["closing"]["strong"], first["closing"]["baseline"])
        self.assertLess(first["closing"]["conservative"], first["closing"]["baseline"])
        self.assertGreater(forecast["conditional_basis"]["rights"], 0)
        self.assertIn("child-promotion", " ".join(forecast["unknowns"]))

    def test_malformed_staff_salary_is_excluded_without_rewriting_the_roster(self):
        app = RunwayHarness(with_events=False)
        app.staff = [
            {"staff_id": "STF-bad-pay", "name": "Unknown Payroll", "salary": "not recorded"},
            "legacy staff row",
        ]
        before_staff = repr(app.staff)
        forecast = app.player_cash_runway_forecast(2)
        self.assertEqual(repr(app.staff), before_staff)
        self.assertEqual(forecast["recurring"]["monthly_fixed"], app.player_monthly_office_cost() + 0 + 0)

    def test_malformed_finance_container_keeps_runway_readable_without_repair(self):
        app = RunwayHarness(with_events=False)
        app.finance = "legacy finance unavailable"
        before = (repr(app.finance), app.cash, random.getstate())
        forecast = app.player_cash_runway_forecast(2)
        self.assertEqual((repr(app.finance), app.cash, random.getstate()), before)
        self.assertEqual(forecast["recurring"]["monthly_fixed"], app.player_monthly_office_cost() + 5_000 + 0)
        self.assertEqual(forecast["conditional_basis"]["rights"], 0)

    def test_empty_runway_still_shows_bills_and_no_events(self):
        app = RunwayHarness(with_events=False)
        forecast = app.player_cash_runway_forecast(2)
        self.assertEqual(forecast["events"], [])
        self.assertTrue(all(not row["events"] and row["event_commitments"] == 0 for row in forecast["rows"]))
        self.assertGreater(forecast["rows"][0]["fixed_bills"], 0)
        self.assertEqual(forecast["lowest_baseline"]["date"], forecast["rows"][-1]["date"])

    def test_finite_rights_are_allocated_once_in_date_order(self):
        app = RunwayHarness()
        app.finance["media_rights"]["events_remaining"] = 1
        forecast = app.player_cash_runway_forecast(4)
        self.assertEqual(forecast["conditional_basis"]["rights"], 8_000)
        due_rows = [row for row in forecast["rows"] if row["events"]]
        self.assertEqual(due_rows[0]["conditional_receipts"], 20_000)
        self.assertEqual(due_rows[1]["conditional_receipts"], 12_000)

    def test_runway_separates_sponsor_maximum_from_activation_estimate(self):
        app = RunwayHarness()
        app.finance["sponsor_deals"] = [
            {"name": "Stable Brand", "fee": 10_000, "activation_requirement": "Maintain company stability above 45"},
            {"name": "Ranked Brand", "fee": 8_000, "activation_requirement": "Feature a ranked fighter in campaign media"},
        ]
        app.sponsor_activation_preview = lambda deal, event=None: (
            deal.get("name") == "Stable Brand",
            "activation ready" if deal.get("name") == "Stable Brand" else "run media this month with a champion or top-10 fighter",
        )
        forecast = app.player_cash_runway_forecast(2)
        first = next(row for row in forecast["events"] if row["event_id"] == "event-one")
        # The base sponsor income is 12,000 and the signed deals add 18,000
        # maximum. Only the second deal is currently at half-fee readiness.
        self.assertEqual(first["conditional_sponsors"], 30_000)
        self.assertEqual(first["conditional_sponsor_estimate"], 26_000)
        self.assertEqual(forecast["conditional_basis"]["sponsors"], 60_000)
        self.assertEqual(forecast["conditional_basis"]["sponsor_estimate"], 52_000)
        self.assertTrue(any("Ranked Brand" in item for item in first["sponsor_activation_reasons"]))

    def test_saved_scenario_records_inputs_forecast_and_is_retry_idempotent(self):
        app = RunwayHarness()
        before_events = repr(app.scheduled_events)
        before_cash = app.cash
        before_rng = random.getstate()
        ok, message, first = app.save_cash_runway_scenario(
            "Conservative spring plan", horizon_weeks=4,
            assumptions={"attendance_multipliers": {"conservative": 0.5, "baseline": 0.9, "strong": 1.4}},
            edits=[{"event_id": "event-one", "field": "ticket_price", "from": 55, "to": 50}],
        )
        self.assertTrue(ok, message)
        self.assertEqual(first["status"], "Draft")
        self.assertEqual(first["assumptions"]["attendance_multipliers"]["conservative"], 0.5)
        self.assertEqual(first["forecast"]["assumptions"]["attendance_multipliers"]["baseline"], 0.9)
        self.assertEqual(before_events, repr(app.scheduled_events))
        self.assertEqual(before_cash, app.cash)
        self.assertEqual(before_rng, random.getstate())
        ok, retry_message, second = app.save_cash_runway_scenario(
            "Conservative spring plan", horizon_weeks=4,
            assumptions={"attendance_multipliers": {"conservative": 0.5, "baseline": 0.9, "strong": 1.4}},
            edits=[{"event_id": "event-one", "field": "ticket_price", "from": 55, "to": 50}],
        )
        self.assertTrue(ok)
        self.assertIn("already exists", retry_message)
        self.assertEqual(first["scenario_id"], second["scenario_id"])
        self.assertEqual(len(app.finance["cash_runway_scenarios"]), 1)

    def test_saved_scenario_reader_marks_changed_inputs_stale_without_rewriting_snapshot(self):
        app = RunwayHarness()
        _ok, _message, saved = app.save_cash_runway_scenario("Baseline")
        current = app.cash_runway_scenario_by_id(saved["scenario_id"])
        self.assertEqual(current["freshness"], "Current")
        app.scheduled_events[0]["ticket_price"] = 70
        stale = app.cash_runway_scenario_by_id(saved["scenario_id"])
        self.assertEqual(stale["freshness"], "Stale inputs")
        self.assertEqual(stale["forecast"]["events"][0]["event_id"], "event-one")

    def test_saved_scenario_reader_marks_cash_staff_and_card_inputs_stale(self):
        app = RunwayHarness()
        _ok, _message, saved = app.save_cash_runway_scenario("Input identity")
        self.assertEqual(app.cash_runway_scenario_by_id(saved["scenario_id"])["freshness"], "Current")
        app.cash += 1
        self.assertEqual(app.cash_runway_scenario_by_id(saved["scenario_id"])["freshness"], "Stale inputs")
        app.cash -= 1
        app.staff[0]["salary"] += 100
        self.assertEqual(app.cash_runway_scenario_by_id(saved["scenario_id"])["freshness"], "Stale inputs")
        app.staff[0]["salary"] -= 100
        app.scheduled_events[0]["fights"][0]["red"] = SimpleNamespace(name="Changed Red", purse=7_500, popularity=60)
        self.assertEqual(app.cash_runway_scenario_by_id(saved["scenario_id"])["freshness"], "Stale inputs")

    def test_scenario_revision_handles_malformed_event_dates_without_repairing_schedule(self):
        app = RunwayHarness()
        app.scheduled_events[0]["month"] = "unknown"
        app.scheduled_events[0]["week"] = "late"
        before_events = repr(app.scheduled_events)
        revision = app._cash_runway_source_revision()
        self.assertEqual(revision["diagnostics"]["malformed_event_date_rows"], 1)
        self.assertEqual(repr(app.scheduled_events), before_events)
        ok, _message, saved = app.save_cash_runway_scenario("Malformed-date snapshot")
        self.assertTrue(ok)
        self.assertEqual(saved["source_revision"]["diagnostics"]["malformed_event_date_rows"], 1)
        self.assertEqual(repr(app.scheduled_events), before_events)

    def test_custom_sensitivity_is_bounded_and_changes_the_projection(self):
        app = RunwayHarness()
        default = app.player_cash_runway_forecast(2)
        custom = app.player_cash_runway_forecast(
            2, attendance_multipliers={"conservative": -1, "baseline": 0.5, "strong": 2.5},
        )
        assumptions = custom["assumptions"]["attendance_multipliers"]
        self.assertEqual(assumptions, {"conservative": 0.0, "baseline": 0.5, "strong": 2.0})
        self.assertNotEqual(custom["rows"][0]["receipts"]["baseline"], default["rows"][0]["receipts"]["baseline"])

    def test_break_even_is_reported_only_when_gate_and_merch_can_cover_capacity(self):
        app = RunwayHarness()
        forecast = app.player_cash_runway_forecast(2)
        constrained = forecast["events"][0]
        self.assertFalse(constrained["break_even_achievable"])
        self.assertIsNone(constrained["break_even_attendance"])
        app.venue_capacity_for = lambda _venue: 100_000
        expanded = app.player_cash_runway_forecast(2)["events"][0]
        self.assertTrue(expanded["break_even_achievable"])
        self.assertGreater(expanded["break_even_attendance"], 0)
        self.assertLessEqual(expanded["break_even_attendance"], expanded["capacity"])
        self.assertIn("conditional rights/sponsors excluded", expanded["break_even_basis"])

    def test_malformed_transactions_are_reported_without_repairing_the_finance_shelf(self):
        app = RunwayHarness()
        app.finance["week_transactions"] = [
            {"month": 1, "week": 4, "costs": 1_250, "revenue": 0},
            {"month": "unknown", "week": 4, "costs": 9_999},
            {"month": 1, "week": 4, "costs": "not-a-number"},
            "legacy transaction row",
        ]
        before = (repr(app.finance), repr(app.scheduled_events), random.getstate())
        forecast = app.player_cash_runway_forecast(2)
        after = (repr(app.finance), repr(app.scheduled_events), random.getstate())
        self.assertEqual(before, after)
        self.assertEqual(forecast["already_paid"], 1_250)
        self.assertTrue(any("3 retained finance transaction row" in item for item in forecast["unknowns"]))

    def test_malformed_transaction_shelf_is_reported_as_unavailable(self):
        app = RunwayHarness()
        app.finance["week_transactions"] = {"legacy": "not a list"}
        before = repr(app.finance)

        forecast = app.player_cash_runway_forecast(2)

        self.assertEqual(repr(app.finance), before)
        self.assertEqual(forecast["already_paid"], 0)
        self.assertTrue(any("1 retained finance transaction row" in item for item in forecast["unknowns"]))

    def test_malformed_scenario_collection_is_an_explicit_unavailable_reader_state(self):
        app = RunwayHarness()
        app.finance["cash_runway_scenarios"] = {"legacy": "not a list"}
        before = repr(app.finance)

        rows = app.cash_runway_scenarios()

        self.assertEqual(repr(app.finance), before)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["_read_status"], "Unavailable")
        self.assertIn("load/migration", rows[0]["note"])

    def test_malformed_finance_scalars_keep_forecast_readable_without_repair(self):
        app = RunwayHarness()
        app.finance.update({
            "sponsor_income": {"legacy": True},
            "production_base": "not recorded",
            "medical_base": [],
            "drug_test_cost": "unknown",
            "monthly_office": float("inf"),
            "merch_rate": float("nan"),
            "tax_rate": float("inf"),
            "media_rights": {"fee": float("inf"), "events_remaining": "ongoing"},
            "sponsor_deals": [{"name": "Legacy deal", "fee": "unavailable"}],
        })
        before = (repr(app.finance), repr(app.scheduled_events), app.cash, random.getstate())
        forecast = app.player_cash_runway_forecast(2)
        after = (repr(app.finance), repr(app.scheduled_events), app.cash, random.getstate())
        self.assertEqual(before, after)
        self.assertEqual(len(forecast["rows"]), 2)
        self.assertTrue(all(isinstance(row["closing"]["baseline"], int) for row in forecast["rows"]))
        self.assertEqual(forecast["conditional_basis"]["rights"], 0)

    def test_revenue_mix_reader_skips_malformed_history_without_repair(self):
        app = RunwayHarness(with_events=False)
        app.player_event_archive = [
            "legacy archive row",
            {"month": "unknown", "event_name": "Broken Card", "finance": {"ticket_revenue": "n/a"}},
            {"month": 1, "event_name": "Valid Card", "finance": {"ticket_revenue": 125}},
        ]
        app.finance = {
            "weekly_history": [
                "legacy week row",
                {"month": "bad", "transactions": [{"revenue": 999}]},
                {"month": 1, "transactions": ["legacy transaction", {"id": "hist-1", "revenue": "250", "category": "Transfer"}]},
            ],
            "week_transactions": ["legacy open row", {"month": 1, "revenue": "n/a"}, {"id": "open-1", "month": 1, "revenue": 75, "category": "Transfer"}],
        }
        before = (repr(app.finance), repr(app.player_event_archive))
        mix = app.player_revenue_mix(12)
        self.assertEqual(mix, {"Ticket sales": 125, "Broadcast": 0, "Sponsorship": 0, "Merchandise": 0, "Other": 325})
        self.assertEqual((repr(app.finance), repr(app.player_event_archive)), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
