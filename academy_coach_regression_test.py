"""J6 Academy Coach role and bounded assignment mechanics."""

import unittest
from types import SimpleNamespace

from world import WorldMixin
from events import EventMixin
from seeding import SeedMixin


class AcademyCoachHarness(WorldMixin):
    def __init__(self):
        self.month, self.week = 3, 2
        self.player_region = "USA"
        self.player_company_name = "Test FC"
        self.cash = 500_000
        self.news, self.inbox = [], []
        self.finance = {}
        self.staff = [{
            "staff_id": "STF-COACH-1", "name": "Coach One", "role": "Academy Coach",
            "skill": 85, "morale": 80, "salary": 7000, "contract_months": 12,
        }]
        self.academy = self.academy_defaults()
        self.academy.update({
            "owned": True, "level": 2, "capacity": 8, "weekly_cost": 4500,
            "prospects": [
                {"prospect_id": "P-1", "name": "Prospect One", "age": 19, "rating": 48, "potential": 80},
                {"prospect_id": "P-2", "name": "Prospect Two", "age": 20, "rating": 48, "potential": 80},
            ],
        })


class AcademyCandidateHarness(SeedMixin):
    def __init__(self):
        self.retired_fighters = [SimpleNamespace(
            fighter_id="F-RET-1", name="Retired One", retired=True,
            record="18-6-0", gender="Male", weight="Welterweight",
            retirement_reason="Age",
        )]
        self.staff = []
        self.staff_candidates = []


class AcademyCoachTests(unittest.TestCase):
    def test_legacy_fallback_is_unchanged_without_assignment(self):
        app = AcademyCoachHarness()
        prospect = app.academy["prospects"][0]
        quality, snapshot = app.academy_training_quality(prospect)
        self.assertEqual(quality, 45.0)
        self.assertIsNone(snapshot)

    def test_assignment_applies_one_bounded_quality_adjustment(self):
        app = AcademyCoachHarness()
        ok, _ = app.start_academy_development_plan(app.academy["prospects"][0], coach_staff_id="STF-COACH-1")
        self.assertTrue(ok)
        plan = app.academy["prospects"][0]["development_plan"]
        self.assertEqual(plan["coach_staff_id"], "STF-COACH-1")
        self.assertGreaterEqual(plan["coach_adjustment"], -2.0)
        self.assertLessEqual(plan["coach_adjustment"], 2.0)
        self.assertGreater(plan["coach_quality"], 45.0)

    def test_one_coach_cannot_take_a_second_active_cohort(self):
        app = AcademyCoachHarness()
        first, _ = app.start_academy_development_plan(app.academy["prospects"][0], coach_staff_id="STF-COACH-1")
        second, message = app.start_academy_development_plan(app.academy["prospects"][1], coach_staff_id="STF-COACH-1")
        self.assertTrue(first)
        self.assertFalse(second)
        self.assertIn("already supervising", message)

    def test_expiry_clears_assignment_and_requires_review(self):
        app = AcademyCoachHarness()
        app.start_academy_development_plan(app.academy["prospects"][0], coach_staff_id="STF-COACH-1")
        app.staff[0]["contract_months"] = 1
        app.update_staff_contracts()
        self.assertEqual(app.staff, [])
        self.assertEqual(app.academy["coach_assignment"], {})
        self.assertIn("Review the active block", app.academy["coach_assignment_review"])
        self.assertTrue(app.academy["prospects"][0]["development_plan"])

    def test_retired_fighter_coach_link_is_separate_and_uses_baseline_skill(self):
        app = AcademyCandidateHarness()
        row = app._link_retired_fighter_academy_candidate({
            "name": "Market Coach", "role": "Academy Coach", "skill": 88,
            "salary": 12000, "specialty": "Development blocks",
        })
        self.assertEqual(row["origin_fighter_id"], "F-RET-1")
        self.assertEqual(row["origin_fighter_record"], "18-6-0")
        self.assertEqual(row["skill"], 45)
        self.assertTrue(row["staff_id"].startswith("STF-ACADEMY-"))
        self.assertEqual(app.retired_fighters[0].record, "18-6-0")
        self.assertNotEqual(row.get("staff_id"), row["origin_fighter_id"])

    def test_retired_fighter_is_not_offered_as_a_second_coach_identity(self):
        app = AcademyCandidateHarness()
        first = app._link_retired_fighter_academy_candidate({
            "name": "Market Coach", "role": "Academy Coach", "skill": 45,
            "salary": 5600, "specialty": "Development blocks",
        })
        app.staff_candidates = [first]
        second = app._link_retired_fighter_academy_candidate({
            "name": "Another Coach", "role": "Academy Coach", "skill": 45,
            "salary": 5600, "specialty": "Development blocks",
        })
        self.assertNotIn("origin_fighter_id", second)

    def test_completed_block_allows_explicit_coach_reassignment(self):
        app = AcademyCoachHarness()
        first, _ = app.start_academy_development_plan(app.academy["prospects"][0], coach_staff_id="STF-COACH-1")
        self.assertTrue(first)
        app.academy["prospects"][0]["development_plan"]["weeks_remaining"] = 0
        second, message = app.start_academy_development_plan(app.academy["prospects"][1], coach_staff_id="STF-COACH-1")
        self.assertTrue(second, message)
        self.assertEqual(app.academy["coach_assignment"]["prospect_id"], "P-2")

    def test_comeback_is_blocked_while_linked_coach_has_active_assignment(self):
        app = AcademyCoachHarness()
        fighter = SimpleNamespace(fighter_id="F-RET-1", name="Retired One", retired=True)
        app.retired_fighters = [fighter]
        app.staff[0]["origin_fighter_id"] = "F-RET-1"
        app.academy["coach_assignment"] = {"staff_id": "STF-COACH-1", "prospect_id": "P-1"}
        allowed, message = EventMixin.contract_negotiation_target_is_current(app, fighter, comeback=True)
        self.assertFalse(allowed)
        self.assertIn("End that coaching assignment", message)


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    if not result.result.wasSuccessful():
        raise SystemExit(1)
