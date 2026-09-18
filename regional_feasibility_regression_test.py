"""Regression coverage for the read-only regional feasibility brief (J9.a)."""

import copy
import random
import unittest
from types import SimpleNamespace

from world import WorldMixin


def fighter(name, *, region="USA", gender="Male", weight="Welterweight",
            ranking_position=0, champion=False, purse=1000, injured=0,
            fatigue=0, fighter_id=None):
    """Build only the live fields the feasibility read model is allowed to read."""
    return SimpleNamespace(
        name=name,
        fighter_id=fighter_id or f"id-{name.lower().replace(' ', '-')}",
        region=region,
        gender=gender,
        weight=weight,
        ranking_position=ranking_position,
        champion=champion,
        purse=purse,
        injured=injured,
        retired=False,
        retirement_pending=False,
        fatigue=fatigue,
        available_week=0,
        available_day=0,
    )


class RegionalFeasibilityHarness(WorldMixin):
    def __init__(self):
        self.month = 5
        self.week = 2
        self.player_region = "USA"
        self.player_company_name = "Player FC"
        self.regions = {
            "USA": {
                "economy": "strong",
                "legality": "Legal",
                "mma_love": 75,
                "drug_accuracy": 90,
                "promo_benefit": {"gate": 1.0, "media": 1.0},
            },
            "UK": {
                "economy": "stable",
                "legality": "Legal",
                "mma_love": 55,
                "drug_accuracy": 80,
                "promo_benefit": {"gate": 1.0, "media": 1.0},
            },
        }
        self.roster = [
            fighter("Local Champion", ranking_position=2, champion=True, purse=3000),
            fighter("Local Contender", ranking_position=8, purse=2000),
            fighter("Travelling Contender", region="UK", ranking_position=15, purse=1500),
        ]
        self.free_agents = [
            fighter("Known Free Agent", region="USA", fighter_id="fa-known"),
            fighter("Unknown Free Agent", region="USA", fighter_id="fa-hidden"),
            fighter("UK Free Agent", region="UK", fighter_id="fa-uk"),
        ]
        self.scheduled_events = [
            {"event_id": "event-usa-1", "name": "Home Card", "venue": "Regional Arena", "month": 5, "week": 3},
            {"event_id": "event-uk-1", "name": "UK Card", "venue": "National Sports Hall", "month": 5, "week": 4},
        ]

    def fighter_profile_stats_visible(self, fighter_obj, company=""):
        return getattr(fighter_obj, "fighter_id", "") != "fa-hidden"

    def venue_region(self, venue):
        return {
            "Local Gym": "USA",
            "Regional Arena": "USA",
            "Casino Ballroom": "USA",
            "National Sports Hall": "UK",
        }.get(venue, "USA")


class RegionalFeasibilityTests(unittest.TestCase):
    def test_snapshot_is_public_read_only_and_scouting_aware(self):
        app = RegionalFeasibilityHarness()
        before = copy.deepcopy({
            "roster": app.roster,
            "free_agents": app.free_agents,
            "scheduled_events": app.scheduled_events,
            "month": app.month,
            "week": app.week,
        })
        rng_state = random.getstate()

        snapshot = app.regional_feasibility_snapshot("USA", month=5, week=3)

        self.assertEqual(snapshot["region"], "USA")
        self.assertEqual(snapshot["as_of"], {"month": 5, "week": 3})
        self.assertEqual(snapshot["roster"]["active"], 3)
        self.assertEqual(snapshot["roster"]["local"], 2)
        self.assertEqual(snapshot["roster"]["ready"], 3)
        self.assertEqual(snapshot["roster"]["bookable_pairings"], 3)
        self.assertEqual(snapshot["roster"]["eligible_challenger_depth"], 2)
        self.assertEqual(snapshot["roster"]["per_bout_local_purse_exposure"], 5000)
        self.assertEqual(snapshot["recruitment"], {
            "regional_free_agents": 2,
            "known_or_scouted": 1,
            "unscouted_or_unknown": 1,
        })
        self.assertEqual(snapshot["venues"]["available"], ["Local Gym", "Regional Arena", "Casino Ballroom"])
        self.assertEqual([row["event_id"] for row in snapshot["scheduled_events"]], ["event-usa-1"])
        self.assertTrue(any("unscouted" in blocker for blocker in snapshot["blockers"]))
        self.assertEqual(random.getstate(), rng_state)
        self.assertEqual(app.roster, before["roster"])
        self.assertEqual(app.free_agents, before["free_agents"])
        self.assertEqual(app.scheduled_events, before["scheduled_events"])
        self.assertEqual((app.month, app.week), (before["month"], before["week"]))

    def test_thin_division_reports_blocker_without_waiving_title_merit(self):
        app = RegionalFeasibilityHarness()
        app.roster = [fighter("Unranked Local")]
        app.free_agents = []

        snapshot = app.regional_feasibility_snapshot("USA")

        self.assertEqual(snapshot["roster"]["bookable_pairings"], 0)
        self.assertEqual(snapshot["roster"]["eligible_challenger_depth"], 0)
        self.assertTrue(any("merit is not waived" in blocker for blocker in snapshot["blockers"]))
        self.assertTrue(any("No same-division" in blocker for blocker in snapshot["blockers"]))
        self.assertTrue(any("free-agent" in blocker for blocker in snapshot["blockers"]))

    def test_snapshot_reuses_booking_conflict_read_model_for_pairings(self):
        app = RegionalFeasibilityHarness()
        app._booking_hard_reasons = lambda fighter_obj, *_args, **_kwargs: (
            ["already has a future or draft booking"]
            if fighter_obj.name == "Travelling Contender" else []
        )

        snapshot = app.regional_feasibility_snapshot("USA", month=5, week=3)

        self.assertEqual(snapshot["roster"]["ready"], 3)
        self.assertEqual(snapshot["roster"]["bookable_ready"], 2)
        self.assertEqual(snapshot["roster"]["booking_blocked"], 1)
        self.assertEqual(snapshot["roster"]["bookable_pairings"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
