"""S4 employment safety: AI staff identities and affordability are durable."""

import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from views import ViewMixin
from world import WorldMixin


def candidate():
    return {
        "staff_id": "STF-candidate-1", "name": "Market Staff", "role": "Marketing",
        "skill": 70, "salary": 100, "morale": 70, "specialty": "Regional campaigns",
        "contract_months": 12,
    }


class AIStaffHarness(ViewMixin):
    def __init__(self, cash):
        self.staff_candidates = [candidate()]
        self.promotions = [SimpleNamespace(name="AI FC", cash=cash, staff=[])]
        self.news = []
        self.month, self.week = 4, 2
        self.transactions = []

    def create_staff_candidate(self):
        return {"staff_id": "STF-new", "name": "New Staff", "role": "Scout", "skill": 50, "salary": 1000}

    def record_promotion_finance_transaction(self, promo, title, **kwargs):
        self.transactions.append((promo.name, title, kwargs))


class AIStaffExpiryHarness(WorldMixin):
    def __init__(self):
        self.month, self.week = 8, 1
        self.news = []
        self.staff_candidates = []
        self.promotions = [SimpleNamespace(name="AI FC", is_regional_feeder=False, staff=[
            {"staff_id": "STF-ai-expiring", "name": "Expiring Staff", "role": "Marketing",
             "salary": 1200, "contract_months": 1},
        ], finance={})]


class AIStaffLedgerHarness(WorldMixin):
    def __init__(self):
        self.promotions = [
            SimpleNamespace(
                name="AI FC", promotion_id="promo-ai", is_regional_feeder=False,
                staff=[
                    {"staff_id": "STF-1", "name": "Stable Staff", "role": "Scout",
                     "specialty": "Prospect eye", "skill": 75, "morale": 62,
                     "salary": 2400, "contract_months": 8,
                     "contract_start_month": 3, "contract_expiry_month": 11},
                    {"staff_id": "STF-1", "name": "Duplicate Identity", "role": "Marketing",
                     "salary": 1800, "contract_months": 2},
                    {"name": "Legacy Staff", "role": "Doctor", "salary": "bad", "contract_months": "bad"},
                    "not-a-staff-record",
                ],
            ),
            SimpleNamespace(
                name="Feeder", promotion_id="promo-feeder", is_regional_feeder=True,
                staff=[{"staff_id": "STF-feeder", "name": "Feeder Staff", "role": "Scout"}],
            ),
        ]
        self.staff_candidates = [
            {"staff_id": "STF-market", "name": "Market Staff", "role": "Compliance",
             "salary": 3200, "contract_months": 24},
        ]


class AIStaffRunwayHarness(WorldMixin):
    def __init__(self):
        self.month = 12
        self.promotions = [SimpleNamespace(
            name="Runway FC", promotion_id="promo-runway", size=20, cash=250_000,
            roster=[SimpleNamespace(retired=False)],
            staff=[{"staff_id": "STF-existing", "role": "Scout", "salary": 6_000}],
            executive={"discipline": 60}, strategy={},
        )]


class AIStaffMarketHarness(ViewMixin):
    def __init__(self):
        self.month, self.week = 4, 2
        self.news = []
        self.promotions = []
        self.staff_candidates = [
            {"staff_id": "STF-bad-market", "name": "Unknown Salary", "role": "Marketing", "salary": "not recorded", "skill": 60},
            "legacy market row",
        ]

    def create_staff_candidate(self):
        return {"staff_id": "STF-new", "name": "New Staff", "role": "Scout", "skill": 50, "salary": 1000}


class FreshStaffMarketHarness(ViewMixin):
    def __init__(self):
        self.month, self.week = 4, 2
        self.news = []
        self.promotions = []
        self.staff = []
        self.staff_candidates = []

    def create_staff_candidate(self):
        return {
            "name": "Fresh Market Staff", "role": "Scout", "skill": 50,
            "salary": 1000, "specialty": "Prospect eye", "contract_months": 24,
        }


class StaffEmploymentTests(unittest.TestCase):
    @staticmethod
    def run_market(app):
        with patch("views.random.random", return_value=0.0), \
                patch("views.random.randrange", return_value=0), \
                patch("views.random.choice", return_value=app.promotions[0]):
            app.simulate_ai_staff_market()

    def test_unaffordable_candidate_returns_to_market(self):
        app = AIStaffHarness(cash=100)
        self.run_market(app)
        self.assertEqual(app.promotions[0].staff, [])
        self.assertTrue(any(item.get("staff_id") == "STF-candidate-1" for item in app.staff_candidates))
        self.assertEqual(app.transactions, [])

    def test_affordable_candidate_moves_with_same_identity_and_one_debit(self):
        app = AIStaffHarness(cash=10_000)
        self.run_market(app)
        self.assertEqual(len(app.promotions[0].staff), 1)
        self.assertEqual(app.promotions[0].staff[0]["staff_id"], "STF-candidate-1")
        self.assertEqual(app.promotions[0].cash, 9_800)
        self.assertEqual(len(app.transactions), 1)
        self.assertFalse(any(item.get("staff_id") == "STF-candidate-1" for item in app.staff_candidates))

    def test_ai_hire_normalises_legacy_terms_and_disambiguates_duplicate_staff_id(self):
        app = AIStaffHarness(cash=10_000)
        app.staff_candidates = [{
            "staff_id": "STF-duplicate", "name": "Legacy Hire", "role": "Marketing",
            "salary": "250", "contract_months": "unknown", "specialty": "Regional campaigns",
        }]
        app.promotions[0].staff = [{"staff_id": "STF-duplicate", "name": "Existing", "role": "Scout"}]
        self.run_market(app)
        self.assertEqual(len(app.promotions[0].staff), 2)
        hired = app.promotions[0].staff[-1]
        self.assertEqual(hired["staff_id"], "STF-duplicate#2")
        self.assertEqual(hired["salary"], 250)
        self.assertEqual(hired["contract_months"], 24)
        self.assertEqual(hired["contract_start_month"], app.month)
        self.assertEqual(hired["contract_expiry_month"], app.month + 24)

    def test_expired_ai_staff_returns_with_identity(self):
        app = AIStaffExpiryHarness()
        app.update_ai_staff_contracts()
        self.assertEqual(app.promotions[0].staff, [])
        self.assertEqual(app.staff_candidates[0]["staff_id"], "STF-ai-expiring")
        self.assertEqual(app.staff_candidates[0]["contract_months"], 24)

    def test_ai_staff_expiry_is_retry_safe_across_a_two_year_boundary_run(self):
        app = AIStaffExpiryHarness()
        promo = app.promotions[0]
        promo.staff = [
            {"staff_id": "STF-ai-one", "name": "One", "role": "Marketing", "salary": 1200, "contract_months": 1},
            {"staff_id": "STF-ai-six", "name": "Six", "role": "Scout", "salary": 1500, "contract_months": 6},
            {"staff_id": "STF-ai-year", "name": "Year", "role": "Doctor", "salary": 1800, "contract_months": 12},
        ]
        for month in range(1, 25):
            app.month = month
            app.update_ai_staff_contracts()
            active_ids = [row.get("staff_id") for row in promo.staff if isinstance(row, dict)]
            market_ids = [row.get("staff_id") for row in app.staff_candidates if isinstance(row, dict)]
            self.assertEqual(len(active_ids), len(set(active_ids)))
            self.assertEqual(len(market_ids), len(set(market_ids)))
        self.assertEqual(promo.staff, [])
        self.assertEqual(
            {row["staff_id"] for row in app.staff_candidates if isinstance(row, dict)},
            {"STF-ai-one", "STF-ai-six", "STF-ai-year"},
        )
        self.assertTrue(all(row.get("contract_months") == 24 for row in app.staff_candidates if isinstance(row, dict)))
        self.assertIn("returned to the staff market", app.news[0])

    def test_expired_legacy_ai_staff_is_retained_for_market_review(self):
        app = AIStaffExpiryHarness()
        app.promotions[0].staff = [{
            "name": "Legacy AI Staff", "role": "Operations", "salary": 900,
            "contract_months": 1,
        }]
        app.update_ai_staff_contracts()
        self.assertEqual(app.promotions[0].staff, [])
        legacy = next(row for row in app.staff_candidates if row.get("name") == "Legacy AI Staff")
        self.assertNotIn("staff_id", legacy)
        self.assertEqual(legacy["contract_months"], 24)
        ledger = app.ai_staff_employment_rows()
        market_row = next(row for row in ledger if row["name"] == "Legacy AI Staff")
        self.assertEqual(market_row["identity_quality"], "Legacy fallback")

    def test_malformed_ai_contract_term_is_held_for_review_without_loss(self):
        app = AIStaffExpiryHarness()
        malformed = {
            "staff_id": "STF-malformed", "name": "Unclear Term", "role": "Operations",
            "salary": "bad", "contract_months": "unknown",
        }
        app.promotions[0].staff = [malformed, "legacy malformed staff row"]
        before = deepcopy(app.promotions[0].staff)
        app.update_ai_staff_contracts()
        self.assertEqual(app.promotions[0].staff[0]["contract_months"], "unknown")
        self.assertTrue(app.promotions[0].staff[0]["contract_review_required"])
        self.assertEqual(app.promotions[0].staff[1], "legacy malformed staff row")
        self.assertEqual(app.staff_candidates, [])
        self.assertEqual(len([row for row in app.news if "malformed term evidence" in row]), 1)
        app.update_ai_staff_contracts()
        self.assertEqual(len([row for row in app.news if "malformed term evidence" in row]), 1)
        self.assertEqual(app.promotions[0].staff[0]["contract_months"], before[0]["contract_months"])

    def test_contract_readers_fail_closed_for_malformed_term_without_rewriting_it(self):
        app = AIStaffExpiryHarness()
        member = {"name": "Unclear Term", "role": "Academy Coach", "contract_months": "unknown"}
        before = deepcopy(member)
        self.assertEqual(app.staff_contract_remaining(member), 0)
        self.assertEqual(app.staff_contract_status(member), "EXPIRED")
        self.assertEqual(app.staff_contract_remaining(member), 0)
        self.assertEqual(member, before)

    def test_staff_table_projection_keeps_malformed_rows_visible_without_repair(self):
        malformed = {"staff_id": "STF-bad", "name": "Unknown Staff", "role": "Marketing", "skill": "?", "salary": "unknown", "morale": None}
        before = deepcopy(malformed)
        projected = ViewMixin.staff_display_fields(malformed)
        self.assertEqual(projected["name"], "Unknown Staff")
        self.assertEqual(projected["salary"], "—")
        self.assertEqual(projected["skill"], "—")
        self.assertEqual(projected["morale"], "—")
        self.assertEqual(malformed, before)
        self.assertEqual(ViewMixin.staff_display_fields("legacy row")["identity_quality"], "Malformed legacy row")

    def test_contract_offer_readers_fail_closed_for_malformed_financial_fields(self):
        app = AIStaffExpiryHarness()
        app.staff = [
            {"staff_id": "STF-valid", "role": "Marketing", "salary": 5000, "reputation": 60},
            "legacy staff row",
            {"role": "Marketing", "salary": "unknown", "reputation": "bad", "negotiation_heat": None},
        ]
        malformed = app.staff[-1]
        before = deepcopy(malformed)
        target = app.staff_contract_target(malformed)
        score = app.staff_contract_offer_score(malformed, "bad", "unknown", existing=True)
        self.assertGreaterEqual(target, 3500)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)
        self.assertEqual(malformed, before)
        self.assertEqual(app.staff_contract_target("legacy staff row"), 3500)
        self.assertGreaterEqual(app.staff_contract_offer_score("legacy staff row", None, None), 0.0)

    def test_contract_warning_reader_skips_malformed_staff_rows(self):
        app = AIStaffExpiryHarness()
        app.staff = [
            "legacy staff row",
            {"name": "Expiring", "role": "Marketing", "salary": "unknown", "contract_months": 1},
        ]
        app.inbox = []
        app.record_staff_tenure_story = lambda *args, **kwargs: None
        app.check_staff_contract_warnings()
        self.assertEqual(len(app.inbox), 1)
        self.assertIn("$0/month", app.inbox[0]["body"])

    def test_contract_tick_holds_malformed_terms_and_preserves_rows(self):
        app = AIStaffExpiryHarness()
        malformed = {"staff_id": "STF-term", "name": "Unclear", "role": "Marketing",
                     "salary": "bad", "contract_months": None}
        app.staff = [malformed, "legacy staff row"]
        app.inbox = []
        app.finance = {}
        app.player_company_name = "Player FC"
        app.record_staff_tenure_story = lambda *args, **kwargs: None
        before = deepcopy(app.staff)
        app.update_staff_contracts()
        self.assertEqual(app.staff[0]["contract_months"], before[0]["contract_months"])
        self.assertEqual(app.staff[0]["salary"], before[0]["salary"])
        self.assertEqual(app.staff[1], before[1])
        self.assertTrue(malformed["contract_review_required"])
        self.assertEqual(app.finance["staff_payroll"], 0)
        self.assertEqual(len(app.inbox), 1)
        self.assertIn("was not ticked", app.inbox[0]["body"])
        app.update_staff_contracts()
        self.assertEqual(len(app.inbox), 1)

    def test_ai_market_does_not_turn_malformed_salary_into_a_free_hire(self):
        app = AIStaffMarketHarness()
        with patch("views.random.random", return_value=0.0), patch("views.random.randrange", return_value=0):
            app.simulate_ai_staff_market()
        self.assertTrue(any(isinstance(row, dict) and row.get("staff_id") == "STF-bad-market" for row in app.staff_candidates))
        self.assertIn("legacy market row", app.staff_candidates)
        self.assertFalse(app.news)

    def test_new_market_candidate_receives_stable_identity_before_audit_boundary(self):
        app = FreshStaffMarketHarness()
        app.simulate_ai_staff_market()
        self.assertEqual(len(app.staff_candidates), 1)
        self.assertRegex(app.staff_candidates[0].get("staff_id", ""), r"^AI-STAFF-[0-9a-f]{12}$")

    def test_staff_profile_compatibility_repair_handles_bad_role_and_skill_without_rewriting_them(self):
        app = AIStaffExpiryHarness()
        malformed = {
            "staff_id": "STF-load-bad", "name": "Legacy Row", "role": ["Marketing"],
            "skill": "unknown", "salary": "bad", "contract_months": "bad",
        }
        app.staff = [malformed]
        app.staff_candidates = []
        before_role = deepcopy(malformed["role"])
        before_skill = malformed["skill"]
        app.ensure_staff_profiles()
        self.assertEqual(malformed["role"], before_role)
        self.assertEqual(malformed["skill"], before_skill)
        self.assertIn("specialty", malformed)
        self.assertIn("reputation", malformed)

    def test_idless_staff_profile_identity_is_not_bound_to_source_position(self):
        rows = [
            {"name": "Legacy Scout", "role": "Scout", "skill": 64, "salary": 3_200,
             "contract_start_month": 4},
            {"name": "Legacy Doctor", "role": "Doctor", "skill": 71, "salary": 4_100,
             "contract_start_month": 5},
        ]
        first = AIStaffExpiryHarness()
        first.staff = deepcopy(rows)
        first.staff_candidates = []
        first.ensure_staff_profiles()
        first_ids = {row["name"]: row["staff_id"] for row in first.staff}

        reordered = AIStaffExpiryHarness()
        reordered.staff = [deepcopy(rows[1]), deepcopy(rows[0])]
        reordered.staff_candidates = []
        reordered.ensure_staff_profiles()
        reordered_ids = {row["name"]: row["staff_id"] for row in reordered.staff}

        self.assertEqual(first_ids, reordered_ids)
        self.assertTrue(all(value.startswith("STF-") for value in first_ids.values()))

    def test_staff_and_scout_helpers_fail_closed_for_malformed_rows(self):
        app = AIStaffExpiryHarness()
        app.staff = [
            {"staff_id": "STF-bad", "role": "Scout", "skill": "unknown", "morale": "bad", "efficiency": None},
            "legacy staff row",
        ]
        self.assertEqual(app.staff_skill("Scout"), 45 * (0.72 + 65 / 230))
        self.assertEqual(app.staff_role_info(["Scout"])["label"], "Operations")
        self.assertEqual(app.scout_capacity(app.staff[0]), 1)
        self.assertEqual(app.scout_capacity("legacy scout"), 0)
        self.assertEqual(app.scout_for_assignment({"scout_id": "missing"}), {})
        self.assertEqual(app.scout_workload(app.staff[0]), 0)

    def test_staff_readers_fail_closed_for_nonfinite_numeric_rows(self):
        app = AIStaffExpiryHarness()
        member = {
            "staff_id": "STF-nonfinite", "role": "Scout", "skill": float("inf"),
            "morale": float("nan"), "salary": float("inf"),
            "reputation": float("nan"), "negotiation_heat": float("inf"),
            "contract_months": float("inf"),
        }
        before = deepcopy(member)
        app.staff = [member]
        self.assertEqual(app.staff_skill("Scout"), 45 * (0.72 + 65 / 230))
        self.assertEqual(app.staff_contract_remaining(member), 0)
        self.assertEqual(app.staff_contract_status(member), "EXPIRED")
        self.assertGreaterEqual(app.staff_contract_target(member), 3500)
        score = app.staff_contract_offer_score(member, float("inf"), float("nan"), existing=True)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)
        self.assertEqual(member, before)

    def test_monthly_player_payroll_skips_malformed_salary_rows(self):
        app = AIStaffExpiryHarness()
        app.staff = [
            {"staff_id": "STF-valid", "name": "Bookkeeper", "salary": 5_000},
            {"staff_id": "STF-bad", "name": "Unknown Payroll", "salary": "bad"},
            "legacy staff row",
        ]
        app.roster = []
        app.cash = 100_000
        app.company_pop = 0
        app.finance = {"monthly_office": 12_000, "ledger": []}
        app.event_log = []
        app.record_finance_transaction = lambda *_args, **_kwargs: None
        app.record_roster_cost_snapshot = lambda: None
        app.apply_player_financial_pressure = lambda: None
        app.tick_business_deals = lambda: None
        app.tick_broadcast_contracts = lambda: None
        before_staff = deepcopy(app.staff)
        payroll_task = next(task for label, task in app.monthly_player_business_steps() if label == "Office and payroll")
        payroll_task()
        self.assertEqual(app.cash, 100_000 - 17_000)
        self.assertEqual(app.staff[1], before_staff[1])
        self.assertEqual(app.staff[2], before_staff[2])

    def test_ledger_is_pure_identity_safe_and_excludes_feeders(self):
        app = AIStaffLedgerHarness()
        before = deepcopy((app.promotions, app.staff_candidates))
        rows = app.ai_staff_employment_rows()
        self.assertEqual((app.promotions, app.staff_candidates), before)
        self.assertEqual([row["source"] for row in rows], ["AI roster", "AI roster", "AI roster", "Shared market"])
        self.assertFalse(any(row["name"] == "Feeder Staff" for row in rows))
        duplicate_rows = [row for row in rows if row["staff_id"] == "STF-1"]
        self.assertEqual(len(duplicate_rows), 2)
        self.assertNotEqual(duplicate_rows[0]["row_id"], duplicate_rows[1]["row_id"])
        legacy = next(row for row in rows if row["name"] == "Legacy Staff")
        self.assertEqual(legacy["identity_quality"], "Legacy fallback")
        self.assertEqual(legacy["salary"], 0)
        market = next(row for row in rows if row["source"] == "Shared market")
        self.assertEqual(market["status"], "Available")

    def test_legacy_ai_staff_row_identity_survives_source_reordering(self):
        app = AIStaffLedgerHarness()
        first = next(row for row in app.ai_staff_employment_rows() if row["name"] == "Legacy Staff")
        app.promotions[0].staff = list(reversed(app.promotions[0].staff))
        second = next(row for row in app.ai_staff_employment_rows() if row["name"] == "Legacy Staff")
        self.assertEqual(first["row_id"], second["row_id"])
        self.assertNotIn("|2", first["row_id"])

    def test_ledger_limit_is_bounded_without_normalising(self):
        app = AIStaffLedgerHarness()
        before = deepcopy((app.promotions, app.staff_candidates))
        rows = app.ai_staff_employment_rows(limit="1")
        self.assertEqual(len(rows), 1)
        self.assertEqual((app.promotions, app.staff_candidates), before)

    def test_ledger_bounds_nonfinite_values_and_limit_without_normalising(self):
        app = AIStaffLedgerHarness()
        member = app.promotions[0].staff[0]
        member.update({
            "salary": float("inf"), "contract_months": float("nan"),
            "skill": float("inf"), "morale": float("nan"),
        })
        before = deepcopy((app.promotions, app.staff_candidates))

        rows = app.ai_staff_employment_rows(limit=float("inf"))

        row = next(item for item in rows if item["name"] == "Stable Staff")
        self.assertEqual(row["salary"], 0)
        self.assertEqual(row["contract_months"], 0)
        self.assertEqual(row["skill"], 0)
        self.assertEqual(row["morale"], 0)
        self.assertEqual((app.promotions, app.staff_candidates), before)

    def test_ledger_fails_closed_for_malformed_collections(self):
        app = AIStaffLedgerHarness()
        app.promotions = "not a promotion list"
        app.staff_candidates = {"not": "a market list"}
        before = deepcopy((app.promotions, app.staff_candidates))

        self.assertEqual(app.ai_staff_employment_rows(), [])
        self.assertEqual((app.promotions, app.staff_candidates), before)

    def test_affordability_snapshot_is_pure_and_explains_six_month_runway(self):
        app = AIStaffRunwayHarness()
        promotion = app.promotions[0]
        market_candidate = {"staff_id": "STF-market", "role": "Marketing", "salary": 8_000}
        before = deepcopy((promotion.cash, promotion.staff, promotion.strategy))
        snapshot = app.ai_staff_affordability_snapshot(promotion, market_candidate)
        self.assertEqual(snapshot["promotion_id"], "promo-runway")
        self.assertEqual(snapshot["existing_staff_payroll"], 6_000)
        self.assertEqual(snapshot["candidate_salary"], 8_000)
        self.assertEqual(snapshot["signing_cost"], 16_000)
        self.assertEqual(snapshot["six_month_runway"], snapshot["monthly_recurring_cost"] * 6)
        self.assertEqual(
            snapshot["current_runway_months"],
            round(snapshot["cash"] / snapshot["monthly_recurring_cost"], 1),
        )
        self.assertEqual(
            snapshot["post_signing_runway_months"],
            round(max(0, snapshot["post_signing_cash"]) / snapshot["monthly_recurring_cost"], 1),
        )
        self.assertEqual(snapshot["runway_basis"], "No-revenue recurring-cost stress test")
        self.assertEqual(snapshot["required_cash_after_signing"], snapshot["six_month_runway"] + 8_000)
        self.assertEqual(snapshot["post_signing_cash"], 234_000)
        self.assertFalse(snapshot["affordable"])
        self.assertIn("required after signing", snapshot["reason"])
        self.assertEqual((promotion.cash, promotion.staff, promotion.strategy), before)

    def test_affordability_snapshot_reports_role_blockers_without_mutation(self):
        app = AIStaffRunwayHarness()
        promotion = app.promotions[0]
        promotion.cash = 2_000_000
        promotion.strategy = {"ai_staff_hire_history": [{"role": "Scout", "month": 12}]}
        before = deepcopy((promotion.cash, promotion.staff, promotion.strategy))
        snapshot = app.ai_staff_affordability_snapshot(
            promotion, {"role": "Scout", "salary": 1_000},
        )
        self.assertFalse(snapshot["affordable"])
        self.assertTrue(snapshot["role_hired_this_month"])
        self.assertTrue(snapshot["role_already_occupied"])
        self.assertIn("Scout already hired this month", snapshot["reason"])
        self.assertIn("Scout role already occupied", snapshot["reason"])
        self.assertEqual((promotion.cash, promotion.staff, promotion.strategy), before)

    def test_affordability_snapshot_handles_malformed_legacy_salary_without_repair(self):
        app = AIStaffRunwayHarness()
        promotion = app.promotions[0]
        promotion.staff.append({"staff_id": "STF-legacy", "role": "Operations", "salary": "unknown"})
        before = deepcopy((promotion.cash, promotion.staff, promotion.strategy))
        snapshot = app.ai_staff_affordability_snapshot(
            promotion, {"staff_id": "STF-market", "role": "Marketing", "salary": 1_000},
        )
        self.assertEqual(snapshot["existing_staff_payroll"], 6_000)
        self.assertEqual(snapshot["monthly_recurring_cost"], app._ai_staff_recurring_cost(promotion))
        self.assertEqual((promotion.cash, promotion.staff, promotion.strategy), before)

    def test_ai_operating_costs_skip_malformed_salary_without_losing_staff_evidence(self):
        app = AIStaffRunwayHarness()
        promotion = app.promotions[0]
        promotion.is_regional_feeder = False
        promotion.size = 20
        promotion.cash = 100_000
        promotion.roster = []
        promotion.staff = [
            {"staff_id": "STF-valid", "role": "Scout", "salary": 6_000},
            {"staff_id": "STF-bad", "role": "Marketing", "salary": "unknown"},
            "legacy staff row",
        ]
        promotion.executive = {"discipline": 60}
        promotion.strategy = {"commercial_strength": 60}
        promotion.reputation_score = 60
        promotion.stability = 70
        app.record_promotion_finance_transaction = lambda *_args, **_kwargs: None
        app.promotion_strategy = lambda _promo: promotion.strategy
        app.ai_financial_runway = lambda _promo: 100_000
        app.ai_cash_ceiling = lambda _promo: 1_000_000
        before_staff = deepcopy(promotion.staff)
        app.apply_ai_operating_costs()
        self.assertEqual(promotion.staff[1], before_staff[1])
        self.assertEqual(promotion.staff[2], before_staff[2])
        self.assertEqual(promotion.cash, 100_000 - (round(31_000 * (0.88 + 25 / 170)) + 6_000))


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    if not result.result.wasSuccessful():
        raise SystemExit(1)
