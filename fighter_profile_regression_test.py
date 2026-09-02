"""Focused headless regressions for fighter Profile identity and action safety."""

import copy
import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from admin import AdminMixin
from events import EventMixin
from models import Fighter
from seeding import SeedMixin
from views import ViewMixin
from world import WorldMixin


def fighter(name="Profile Fighter", fighter_id="FTR-profile", **updates):
    values = dict(
        name=name, fighter_id=fighter_id, weight="Lightweight", age=27,
        record_w=8, record_l=2, striking=72, wrestling=68, grappling=70,
        cardio=73, chin=71, popularity=45, momentum=1, morale=70,
        purse=12_000, region="USA", potential=82,
    )
    values.update(updates)
    return Fighter(**values)


class ProfileHarness(AdminMixin, SeedMixin, ViewMixin, EventMixin, WorldMixin):
    def __init__(self):
        self.player_company_name = "BAMMA"
        self.roster = []
        self.free_agents = []
        self.retired_fighters = []
        self.promotions = []
        self.combat_sport_worlds = {}
        self.player_combat_divisions = {}
        self.belts = self.blank_belts()
        self.interim_belts = self.blank_belts()
        self.belt_history = self.blank_belt_history()
        self.special_belts = {}
        self.rules = {"scouting_mode": True}
        self.scouting_reports = {}
        self.scouting_searches = []
        self.month = 1
        self.week = 1
        self.spectator_mode = False
        self.result_records = []
        self.ai_event_archive = []


class FighterProfileRegressionTests(unittest.TestCase):
    def test_duplicate_name_employer_does_not_leak_private_ratings(self):
        app = ProfileHarness()
        owned = fighter("Alex Smith", "FTR-owned", striking=80, wrestling=80, grappling=80)
        rival = fighter("Alex Smith", "FTR-rival", striking=64, wrestling=64, grappling=64)
        promotion = SimpleNamespace(name="Rival FC", roster=[rival], belts={}, interim_belts={}, belt_history={})
        app.roster = [owned]
        app.promotions = [promotion]

        company = app.fighter_company_for_profile(rival)
        self.assertEqual("Rival FC", company)
        self.assertFalse(app.fighter_profile_stats_visible(rival, company))
        badge = app.portrait_badge_text(rival, ratings_visible=False)
        self.assertIn("SCOUT", badge)
        self.assertNotIn(str(rival.overall), badge)

    def test_same_name_history_uses_fighter_ids(self):
        app = ProfileHarness()
        winner = fighter("Alex Smith", "FTR-winner")
        loser = fighter("Alex Smith", "FTR-loser")
        app.roster = [winner, loser]
        log = {
            "a": winner.name, "b": loser.name,
            "a_id": winner.fighter_id, "b_id": loser.fighter_id,
            "winner": winner.name, "winner_id": winner.fighter_id,
            "draw": False, "result": "Alex Smith - Decision R3",
        }

        self.assertEqual("W", app.fighter_profile_outcome(winner, log))
        self.assertEqual("L", app.fighter_profile_outcome(loser, log))
        self.assertIs(loser, app.fighter_profile_history_opponent(winner, {"opponent_id": loser.fighter_id}))
        self.assertIs(winner, app.fighter_profile_history_opponent(loser, {"opponent_id": winner.fighter_id}))

    def test_distinct_same_label_archives_remain_searchable(self):
        app = ProfileHarness()
        target = fighter("Target", "FTR-target")
        opponent = fighter("Opponent", "FTR-opponent")
        app.roster = [target, opponent]
        common = {"date": "Month 3 Week 2", "company": "BAMMA", "event": "BAMMA 9"}
        app.result_records = [
            {**common, "record_id": "card-one", "fight_logs": [{"a": "Other A", "b": "Other B", "a_id": "FTR-a", "b_id": "FTR-b", "result": "Other A def. Other B by Decision"}]},
            {**common, "record_id": "card-two", "fight_logs": [{
                "a": target.name, "b": opponent.name, "a_id": target.fighter_id, "b_id": opponent.fighter_id,
                "winner_id": target.fighter_id, "result": "Target def. Opponent by Decision", "weight": target.weight,
            }]},
        ]
        context = app.fighter_history_card_context(target, "Month 3 Week 2: Target def. Opponent by Decision at BAMMA 9", opponent.name)
        self.assertEqual("card-two", context["record"]["record_id"])
        self.assertEqual("W", context["result_code"])

    def test_duplicate_name_does_not_inherit_another_owners_title(self):
        app = ProfileHarness()
        champion = fighter("Alex Smith", "FTR-champion", champion=True)
        rival = fighter("Alex Smith", "FTR-rival")
        app.roster = [champion]
        app.belts[app.belt_key(champion.gender, champion.weight)] = champion.name
        promotion = SimpleNamespace(name="Rival FC", roster=[rival], belts={}, interim_belts={}, belt_history={})
        app.promotions = [promotion]

        self.assertTrue(app.fighter_current_championships(champion))
        self.assertEqual([], app.fighter_current_championships(rival))

    def test_combat_sport_profile_queries_are_observational(self):
        app = ProfileHarness()
        boxer = fighter(
            "Boxer", "FTR-boxer", primary_discipline="Boxing",
            sport_employer="World Boxing", sport_weight_class="Lightweight",
        )
        world = {
            "promotion": "World Boxing", "roster": [boxer],
            "rankings_by_division": {"Male Lightweight": [boxer.name]},
            "titles": {"Male Lightweight": boxer.name},
        }
        app.combat_sport_worlds = {"Boxing": world}
        before = copy.deepcopy({key: value for key, value in world.items() if key != "roster"})
        fighter_before = copy.deepcopy(vars(boxer))
        with patch.object(app, "ensure_combat_sport_circuit_state", side_effect=AssertionError("Profile query invoked migration")):
            app.rank_label_for_fighter(boxer, "World Boxing")
            app.fighter_current_championships(boxer)
        self.assertEqual(before, {key: value for key, value in world.items() if key != "roster"})
        self.assertEqual(fighter_before, vars(boxer))

    def test_profile_geometry_never_exceeds_screen(self):
        for screen_width, screen_height in ((1024, 720), (800, 600), (600, 480)):
            with self.subTest(screen=(screen_width, screen_height)):
                width, height, min_width, min_height = ProfileHarness.fighter_profile_geometry(screen_width, screen_height)
                self.assertLessEqual(width, screen_width)
                self.assertLessEqual(height, screen_height)
                self.assertLessEqual(min_width, width)
                self.assertLessEqual(min_height, height)

    def test_profile_builder_does_not_run_load_repairs(self):
        source = inspect.getsource(ViewMixin.open_fighter_profile_window)
        for forbidden in (
            "ensure_detailed_skills(fighter)",
            "ensure_fighter_business_stats(fighter)",
            "migrate_academy_amateur_history(fighter)",
            "ensure_fighter_history_baseline(fighter)",
            "ensure_combat_sport_circuit_state(",
        ):
            self.assertNotIn(forbidden, source)

    def test_stale_weight_move_requires_current_player_ownership(self):
        app = ProfileHarness()
        target = fighter()
        with patch("events.messagebox.showwarning"), patch.object(app, "complete_weight_class_move") as complete:
            self.assertFalse(app.move_fighter_weight_class(target, "Welterweight"))
        complete.assert_not_called()

    def test_contract_target_guard_rejects_spectator_and_stale_owner(self):
        app = ProfileHarness()
        target = fighter()
        app.free_agents = [target]
        app.spectator_mode = True
        self.assertFalse(app.contract_negotiation_target_is_current(target)[0])

        app.spectator_mode = False
        app.free_agents = []
        app.promotions = [SimpleNamespace(name="Rival FC", roster=[target])]
        self.assertFalse(app.contract_negotiation_target_is_current(target)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
