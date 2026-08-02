"""Focused regressions for UI/scouting/world-data QA fixes.

This suite intentionally avoids creating a Tk root so it can run in CI and on
headless packaging workers.
"""

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from models import Gym
from seeding import SeedMixin
from views import ViewMixin


class Var:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class Tree:
    def __init__(self, selected=()):
        self.rows = {}
        self.selected = tuple(selected)
        self.focused = ""

    def get_children(self):
        return tuple(self.rows)

    def delete(self, *items):
        for item in items:
            self.rows.pop(item, None)

    def insert(self, _parent, _where, iid=None, values=(), **_kwargs):
        self.rows[iid] = values

    def selection(self):
        return self.selected

    def selection_set(self, iid):
        self.selected = (iid,)

    def focus(self, iid):
        self.focused = iid


class Text:
    def __init__(self):
        self.value = ""

    def config(self, **_kwargs):
        pass

    def delete(self, *_args):
        self.value = ""

    def insert(self, _where, value):
        self.value += str(value)


class ViewHarness(ViewMixin):
    def event_fight_participants(self, fight):
        return list(fight.get("tournament_entrants", fight.get("fighters", [])))

    def event_fight_participant_references(self, fight):
        participants = self.event_fight_participants(fight)
        fighter_ids = list(fight.get("fighter_ids", []))
        if len(fighter_ids) == len(participants):
            return [fighter_id or name for name, fighter_id in zip(participants, fighter_ids)]
        return participants

    def scheduled_fighter_references(self, include_booked=False):
        fights = list(self.booked) if include_booked else []
        fights.extend(fight for event in self.scheduled_events for fight in event.get("fights", []))
        return {
            reference for fight in fights
            for reference in self.event_fight_participant_references(fight)
            if reference != "TBA"
        }

    def fighter_has_scheduled_fight(self, fighter, include_booked=False):
        references = self.scheduled_fighter_references(include_booked)
        return fighter.fighter_id in references or fighter.name in references


class SeedHarness(SeedMixin):
    pass


class UIDataRegressionTests(unittest.TestCase):
    def test_refresh_staff_is_safe_before_staff_tab_is_built(self):
        harness = ViewHarness()
        harness.staff = []
        harness.refresh_staff()  # no lazily-created Tk widgets exist

    def test_academy_guidance_recognizes_hired_scout(self):
        harness = ViewHarness()
        harness.staff = [{"name": "Georgia Vazirov", "role": "Scout", "skill": 71}]
        guidance = harness.academy_network_guidance()
        self.assertIn("Georgia Vazirov", guidance)
        self.assertNotIn("Hire a Scout", guidance)

    def test_result_filter_selects_and_displays_first_visible_record(self):
        harness = ViewHarness()
        first = {"company": "Alpha", "event": "Alpha 1", "date": "Jan W1 2026"}
        second = {"company": "Beta", "event": "Beta 1", "date": "Jan W1 2026"}
        harness.result_index = [first, second]
        harness.result_records = []
        harness.result_history = []
        harness.result_search = Var("")
        harness.result_company_filter = Var("Beta")
        harness.result_company_combo = SimpleNamespace(configure=lambda **_kwargs: None)
        harness.results_tree = Tree()
        harness._visible_result_records = {}
        harness.retired_tree = Tree()
        harness.retired_fighters = []
        harness.retired_search = Var("")
        harness.retired_gender_filter = Var("All")
        harness.retired_weight_filter = Var("All")
        harness.retired_legacy_filter = Var("All")
        harness.results_text = Text()
        harness.promotions = []
        harness.player_company_name = "Alpha"
        harness.result_headline = lambda record: record["event"]
        harness.format_game_date_text = lambda value: value
        harness.result_card_text = lambda record: f"DETAIL:{record['event']}"

        harness.refresh_results()

        self.assertEqual([second], list(harness._visible_result_records.values()))
        self.assertEqual("DETAIL:Beta 1", harness.results_text.value)
        self.assertEqual(("result-1",), harness.results_tree.selection())

    def test_duplicate_names_use_distinct_matchmaking_ids(self):
        harness = ViewHarness()
        a = SimpleNamespace(name="Alex Smith", fighter_id="fighter-a", weight="Lightweight", gender="Male", injured=0, fatigue=0)
        b = SimpleNamespace(name="Alex Smith", fighter_id="fighter-b", weight="Lightweight", gender="Male", injured=0, fatigue=0)
        harness.available_tree = Tree(("row-a", "row-b"))
        harness.available_tree_fighters = {"row-a": a, "row-b": b}
        harness.booked = []
        harness.scheduled_events = []
        harness.month = harness.week = 1
        harness.rules = {"allow_mixed_gender": False}
        harness.closed_divisions = set()
        harness.title_fight = Var(False)
        harness.main_event = Var(False)
        harness.card_tier = Var("Main Card")
        harness.special_belt_choice = Var("None")
        harness.set_matchmaking_notice = lambda *_args: None
        harness.belt_key = lambda gender, weight: f"{gender}:{weight}"
        harness.selected_special_belt_name = lambda: ""
        harness.special_belt_booking_error = lambda *_args: ""
        harness.divisional_title_is_interim = lambda *_args: False
        harness.selected_booking_date = lambda **_kwargs: (1, 1)
        harness.fighter_available_for_date = lambda *_args: True
        harness.normalize_card_order = lambda: None
        harness.refresh_available = lambda: None
        harness.refresh_card = lambda: None
        harness.is_event_due = lambda _event: False

        with patch("views.messagebox.showinfo"), patch("views.messagebox.showwarning"):
            harness.add_matchup()

        self.assertEqual(["Alex Smith", "Alex Smith"], harness.booked[0]["fighters"])
        self.assertEqual(["fighter-a", "fighter-b"], harness.booked[0]["fighter_ids"])
        self.assertTrue(harness.fighter_has_scheduled_fight(a, include_booked=True))
        self.assertTrue(harness.fighter_has_scheduled_fight(b, include_booked=True))

    def test_region_teams_match_seeded_gym_geography(self):
        harness = SeedHarness()
        gyms = harness.seed_gyms()
        gyms_by_name = {gym.name: gym for gym in gyms}
        for region, data in harness.seed_regions().items():
            self.assertTrue(data["teams"], region)
            for team in data["teams"]:
                self.assertIn(team, gyms_by_name)
                self.assertEqual(region, gyms_by_name[team].region, team)
        database = json.loads((Path(__file__).parent / "Databases" / "Default Universe.universe.json").read_text(encoding="utf-8"))
        for region, data in database["sections"]["regions"].items():
            for team in data["teams"]:
                self.assertEqual(region, gyms_by_name[team].region, team)

    def test_regions_listbox_uses_only_supported_theme_keys(self):
        source = (Path(__file__).parent / "ui.py").read_text(encoding="utf-8")
        regions_builder = source.split("    def build_regions_tab", 1)[1].split("    def build_results_tab", 1)[0]
        self.assertNotIn('self.colors["accent"]', regions_builder)
        self.assertNotIn("activebackground=", regions_builder)
        self.assertNotIn("activeforeground=", regions_builder)
        for key in ("cream", "text", "red", "line"):
            self.assertIn(f'self.colors["{key}"]', regions_builder)

    def test_opening_gym_capacity_is_bounded_to_135_percent_load(self):
        harness = SeedHarness()
        gym = Gym("Busy Gym", "USA", "City", 80, 80, [], "Coach", 100, 1000)
        harness.gyms = [gym]
        harness.roster = [SimpleNamespace(camp="Busy Gym", retired=False) for _ in range(300)]
        harness.free_agents = []
        harness.promotions = []
        harness.combat_sport_worlds = {}
        harness.month = harness.week = 1

        harness.sync_gym_membership()

        self.assertEqual(300, gym.member_count)
        self.assertLessEqual(gym.member_count / gym.capacity, 1.35)
        self.assertEqual(0, gym.capacity_growth, "baseline repair is not earned lifetime gym growth")

    def test_eurasian_feeder_description_is_not_used_as_level(self):
        source = (Path(__file__).parent / "seeding.py").read_text(encoding="utf-8")
        self.assertIn('reputation="Regional Feeder"', source)
        self.assertIn('strategy["description"] = EURASIAN_FIGHT_CIRCUIT_DESCRIPTION', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
