"""Focused regressions for player-owned combat-sport promotion operations."""

import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from feature_foundation import FoundationMixin
from models import Fighter
from world import WorldMixin


def fighter(name, fighter_id, employer, purse=4_000, months=12, popularity=50):
    return Fighter(
        name=name, fighter_id=fighter_id, weight="Lightweight", age=25,
        record_w=5, record_l=1, striking=72, wrestling=65, grappling=64,
        cardio=73, chin=70, popularity=popularity, momentum=0, morale=70,
        purse=purse, potential=82, primary_discipline="Boxing",
        sport_employer=employer, sport_weight_class="Lightweight",
        contract_months=months,
    )


class CombatSportsHarness(WorldMixin):
    def __init__(self):
        self.player_company_name = "Player Co"
        self.cash = 1_000_000
        self.company_pop = 50
        self.month = 8
        self.week = 2
        self.news = []
        self.inbox = []
        self.finance_rows = []
        self.result_records = []
        self.player_combat_divisions = {}
        self.combat_sport_worlds = {}

    def record_finance_transaction(self, label, **kwargs):
        self.finance_rows.append({"label": label, **kwargs})

    def refresh_combat_sport_rankings(self, sport, world, employer=None, division=None):
        return self.combat_sport_roster(sport, employer)

    def combat_sport_competition_class(self, sport, fighter):
        return fighter.sport_weight_class or fighter.weight

    def ds(self, fighter, key, fallback=50):
        return (fighter.detailed_skills or {}).get(key, fallback)

    def starting_fight_gas(self, fighter):
        return max(20, 100 - fighter.fatigue)

    def gym_quality(self, _camp):
        return 50

    def combat_sport_weight_ladder(self, _sport, _gender):
        return [("Lightweight", 155)]

    def combat_sport_mma_equivalent(self, _sport, label, _gender):
        return label

    def assign_combat_sport_weight(self, _sport, fighter, label="", reset_walk_weight=False):
        fighter.sport_weight_class = label or fighter.sport_weight_class or fighter.weight
        return fighter.sport_weight_class

    def archive_result_record(self, row):
        self.result_records.append(row)

    def record_world_story(self, *_args, **_kwargs):
        return None

    def record_combat_sport_story(self, *_args, **_kwargs):
        return None

    def refresh_promotion_rankings(self):
        return None

    def apply_combat_sport_result(self, sport, world, a, b, **kwargs):
        return {
            "a": a.name, "b": b.name, "a_id": a.fighter_id, "b_id": b.fighter_id,
            "a_record": a.record, "b_record": b.record, "a_rating": {}, "b_rating": {},
            "start_stamina": {a.name: 100, b.name: 100},
            "condition": {a.name: {}, b.name: {}}, "readiness": {}, "weight": a.weight,
            "winner": a.name, "method": "Decision", "round": 3, "score": "30-27",
            "result": f"{a.name} def. {b.name} by Decision", "log": [],
            "title": bool(kwargs.get("title")), "title_key": kwargs.get("title_key", ""),
        }

    def ensure_combat_sport_circuit_state(self, sport, world, employer=None, player_owned=False):
        return self.player_combat_divisions[sport] if player_owned else world

    def combat_sport_card_strategy(self, *_args, **_kwargs):
        return "Balanced"


class CombatSportsMembershipHarness(CombatSportsHarness, FoundationMixin):
    """The same world stubs with the authoritative membership ledger enabled."""

    def __init__(self):
        super().__init__()
        self.promotions = []
        self.roster = []
        self.ensure_foundation_state()

    def rank_value(self, fighter):
        return float(getattr(fighter, "overall", 0) or 0)


class CombatSportsOperationsTest(unittest.TestCase):
    def setUp(self):
        self.app = CombatSportsHarness()
        self.flagship = "World Boxing"
        self.a = fighter("Shared Name", "box-a", self.app.player_company_name, purse=7_500)
        self.b = fighter("Shared Name", "box-b", self.app.player_company_name, purse=9_000)
        self.market = fighter("Market Star", "box-market", self.flagship, months=0)
        self.world = {
            "promotion": self.flagship, "roster": [self.a, self.b, self.market],
            "events": 4, "event_history": ["Flagship history"], "media": [],
        }
        self.division = {
            "sport": "Boxing", "promotion_name": "Player Co Boxing", "roster": ["Shared Name"],
            "roster_ids": [self.a.fighter_id, self.b.fighter_id], "booked_bouts": [],
            "events": [], "titles": {}, "rankings_by_division": {}, "finance_history": [],
            "revenue_total": 0, "cost_total": 0, "profit_total": 0,
            "reputation": 50, "stability": 60, "last_card_month": 0,
        }
        self.app.combat_sport_worlds["Boxing"] = self.world
        self.app.player_combat_divisions["Boxing"] = self.division

    def test_duplicate_names_remain_distinct_in_roster_and_bookings(self):
        self.division["booked_bouts"] = [{
            "a_id": self.a.fighter_id, "b_id": self.b.fighter_id,
            "a": self.a.name, "b": self.b.name,
        }]
        repaired = self.app.ensure_player_combat_division_identity("Boxing", self.world)
        self.assertEqual(repaired["roster_ids"], ["box-a", "box-b"])
        self.assertEqual(repaired["booked_bouts"][0]["a_id"], "box-a")
        self.assertEqual(repaired["booked_bouts"][0]["b_id"], "box-b")

    def test_circuit_reader_projects_legacy_state_without_repairing_saved_world(self):
        before_world = deepcopy(self.world)
        before_fighters = {
            fighter.fighter_id: (fighter.sport_weight_class, fighter.weight, fighter.champion)
            for fighter in self.world["roster"]
        }
        state = WorldMixin.ensure_combat_sport_circuit_state(
            self.app, "Boxing", self.world, self.flagship, False, repair=False,
        )
        self.assertIn("rankings_by_division", state)
        self.assertIn("titles", state)
        self.assertEqual(self.world.keys(), before_world.keys())
        self.assertEqual(self.world.get("titles"), before_world.get("titles"))
        self.assertEqual(self.world.get("rankings_by_division"), before_world.get("rankings_by_division"))
        for fighter in self.world["roster"]:
            self.assertEqual(
                (fighter.sport_weight_class, fighter.weight, fighter.champion),
                before_fighters[fighter.fighter_id],
            )

    def test_contract_reader_projects_membership_without_repairing_saved_division(self):
        self.division["roster_ids"] = []
        self.division["roster"] = [self.a.name]
        before = deepcopy(self.division)
        rows = self.app.player_combat_contract_rows(repair=False)
        self.assertEqual({row["fighter"].fighter_id for row in rows}, {self.a.fighter_id, self.b.fighter_id})
        self.assertEqual(self.division, before)

    def test_contract_reader_fails_closed_for_malformed_containers(self):
        before_divisions = self.app.player_combat_divisions
        self.app.player_combat_divisions = "malformed"
        self.assertEqual(self.app.player_combat_contract_rows(repair=False), [])
        self.app.player_combat_divisions = before_divisions
        self.app.combat_sport_worlds["Boxing"] = {"roster": ["malformed", self.a]}
        self.assertEqual(
            {row["fighter"].fighter_id for row in self.app.player_combat_contract_rows(repair=False)},
            {self.a.fighter_id},
        )
        self.app.combat_sport_worlds["Boxing"] = "malformed"
        self.assertEqual(self.app.player_combat_contract_rows(repair=False), [])

    def test_duplicate_name_bout_telemetry_keeps_both_corners(self):
        result = self.app.simulate_combat_sport_bout("Boxing", self.a, self.b)
        self.assertEqual(set(result["condition"]), {"box-a", "box-b"})
        self.assertEqual(set(result["start_stamina"]), {"box-a", "box-b"})
        self.assertEqual(set(result["readiness"]), {"box-a", "box-b"})

    def test_boxing_and_muay_thai_use_distinct_professional_formats(self):
        self.assertEqual(self.app.combat_sport_bout_rules("Boxing", a=self.a, b=self.b)["rounds"], 6)
        self.assertEqual(self.app.combat_sport_bout_rules("Boxing", title=True, a=self.a, b=self.b)["rounds"], 12)
        self.assertEqual(self.app.combat_sport_bout_rules("Muay Thai", a=self.a, b=self.b)["rounds"], 3)
        self.assertEqual(self.app.combat_sport_bout_rules("Muay Thai", title=True, a=self.a, b=self.b)["rounds"], 5)
        lethwei = fighter("Lethwei Athlete", "lethwei-1", self.app.player_company_name)
        lethwei.primary_discipline = "Lethwei"
        lethwei_rules = self.app.combat_sport_bout_rules("Muay Thai", a=lethwei, b=self.b)
        self.assertEqual(lethwei_rules["rounds"], 5)
        self.assertTrue(lethwei_rules["lethwei"])

    def test_native_judging_rewards_boxing_knockdowns_and_thai_weapons(self):
        blank = {"landed": 0, "effective": 0.0, "knockdowns": 0, "punches": 0, "kicks": 0, "knees_elbows": 0, "clinch_balance": 0}
        boxing = {self.a: dict(blank, landed=3, effective=3.0, punches=3, knockdowns=1), self.b: dict(blank, landed=5, effective=3.3, punches=5)}
        with patch("world.random.uniform", return_value=0):
            self.assertEqual(self.app.combat_sport_round_scorecards("Boxing", self.a, self.b, -2, boxing), [(10, 8)] * 3)
        thai = {self.a: dict(blank, landed=4, effective=5.0, kicks=2, knees_elbows=1, clinch_balance=1), self.b: dict(blank, landed=7, effective=3.0, punches=7)}
        with patch("world.random.uniform", return_value=0):
            self.assertEqual(self.app.combat_sport_round_scorecards("Muay Thai", self.a, self.b, -1, thai), [(10, 9)] * 3)

    def test_boxing_result_exposes_three_official_cards_and_round_evidence(self):
        with patch("world.random.random", return_value=0.99):
            result = self.app.simulate_combat_sport_bout("Boxing", self.a, self.b, title=True)
        self.assertEqual(len(result["scorecards"]), 3)
        self.assertEqual(len(result["round_metrics"]), 12)
        self.assertTrue(self.app.combat_sport_is_decision(result["method"]))
        self.assertIn("J1", result["score"])

    def test_same_name_title_belongs_to_one_fighter_id(self):
        key = self.app.combat_sport_division_key(self.b, "Boxing")
        self.division.update({
            "titles_initialized": True,
            "titles": {key: self.b.name},
            "title_ids": {key: self.b.fighter_id},
        })
        state = WorldMixin.ensure_combat_sport_circuit_state(
            self.app, "Boxing", self.world, self.app.player_company_name, True,
        )
        self.assertFalse(self.a.champion)
        self.assertTrue(self.b.champion)
        ok, _note = self.app.release_player_combat_athlete("Boxing", self.a)
        self.assertTrue(ok)
        self.assertEqual(state["title_ids"][key], self.b.fighter_id)
        self.assertEqual(state["titles"][key], self.b.name)

    def test_independent_guest_is_not_persisted_in_season_awards_state(self):
        guest = fighter("One Night Guest", "guest-1", "Independent Boxing Circuit")
        guest.contract_type = "One-Fight Independent"
        state = {"season_stats": {}, "records": {}}
        self.app.record_combat_sport_season_result(state, self.a, guest, self.a, "Decision")
        self.assertEqual(set(state["season_stats"]), {self.a.fighter_id})
        self.assertEqual(set(state["records"]), {self.a.fighter_id})

    def test_flagship_buyout_creates_a_real_contract(self):
        terms = self.app.combat_sport_contract_terms("Boxing", self.market)
        ok, _note, signed = self.app.sign_player_combat_flagship(
            "Boxing", self.market.fighter_id, terms["purse"], terms["months"],
        )
        self.assertTrue(ok)
        self.assertIs(signed, self.market)
        self.assertEqual(signed.contract_months, terms["months"])
        self.assertEqual(signed.purse, terms["purse"])
        self.assertTrue(signed.exclusive)
        self.assertIn(signed.fighter_id, self.division["roster_ids"])
        self.assertEqual(self.app.finance_rows[-1]["source"], "Flagship buyout")

    def test_flagship_buyout_records_leave_and_child_join(self):
        app, athlete, world, division = self.membership_setup()
        athlete.sport_employer = world["promotion"]
        terms = app.combat_sport_contract_terms("Boxing", athlete)
        ok, _note, signed = app.sign_player_combat_flagship(
            "Boxing", athlete.fighter_id, terms["purse"], terms["months"],
        )
        self.assertTrue(ok)
        self.assertIs(signed, athlete)
        rows = app.foundation_membership_events(fighter_id=athlete.fighter_id)
        self.assertEqual([row["action"] for row in rows], ["leave", "join"])
        self.assertEqual(rows[0]["promotion_name"], world["promotion"])
        self.assertEqual(rows[1]["promotion_name"], division["promotion_name"])
        self.assertEqual(rows[0]["source_transaction"], rows[1]["source_transaction"])

    def test_private_market_signing_records_child_join(self):
        app, _athlete, world, division = self.membership_setup()
        recruit = fighter("Youth Recruit", "box-youth", "")
        recruit.age = 18
        division["signable_youth"] = [recruit]
        terms = app.combat_sport_contract_terms("Boxing", recruit)
        ok, _note, signed = app.sign_player_combat_youth(
            "Boxing", recruit.fighter_id, terms["purse"], terms["months"],
        )
        self.assertTrue(ok)
        self.assertEqual(signed.fighter_id, recruit.fighter_id)
        self.assertIn(signed, world["roster"])
        rows = app.foundation_membership_events(fighter_id=recruit.fighter_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["action"], "join")
        self.assertEqual(rows[0]["promotion_name"], division["promotion_name"])

    def test_academy_graduation_into_child_division_records_join(self):
        app = CombatSportsMembershipHarness()
        app.player_region = "North America"
        app.academy = {}
        graduate = fighter("Academy Graduate", "box-academy", "")
        world = {"promotion": "World Boxing", "roster": []}
        division = {
            "sport": "Boxing", "promotion_name": "Player Co Boxing",
            "roster": [], "roster_ids": [], "booked_bouts": [],
        }
        app.combat_sport_worlds["Boxing"] = world
        app.player_combat_divisions["Boxing"] = division
        prospect = {"prospect_id": "academy-prospect-1", "name": graduate.name, "region": app.player_region}
        with patch.object(app, "academy_prospect_to_fighter", return_value=graduate), \
             patch.object(app, "open_player_combat_division", return_value=(True, division)), \
             patch.object(app, "add_player_combat_member"), \
             patch.object(app, "fulfill_academy_promise"), \
             patch.object(app, "record_academy_graduate"):
            ok, _note, signed = app._promote_academy_prospect_to_sport(prospect, "Boxing")
        self.assertTrue(ok)
        self.assertIs(signed, graduate)
        rows = app.foundation_membership_events(fighter_id=graduate.fighter_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["action"], "join")
        self.assertEqual(rows[0]["promotion_name"], division["promotion_name"])

    def test_expired_contract_leaves_after_grace_month(self):
        self.a.contract_months = 0
        self.app.tick_player_combat_contracts()
        self.assertEqual(self.a.sport_employer, self.flagship)
        self.assertNotIn(self.a.fighter_id, self.division["roster_ids"])
        self.assertTrue(any("Departure" in row["subject"] for row in self.app.inbox))

    def test_card_pays_purses_and_does_not_touch_flagship_counter(self):
        cash_before = self.app.cash
        card = self.app.run_combat_sport_card(
            "Boxing", self.world, self.app.player_company_name, player_owned=True,
            bouts=[{"a": self.a, "b": self.b, "title": False, "title_key": ""}],
            event_name="Identity Night",
        )
        self.assertIsNotNone(card)
        self.assertEqual(card["finance"]["fighter_payroll"], 16_500)
        self.assertEqual(self.world["events"], 4)
        self.assertEqual(self.world["event_history"], ["Flagship history"])
        self.assertEqual(self.division["event_counter"], 1)
        self.assertEqual(self.app.finance_rows[-1]["event"], "Identity Night")
        self.assertIn(":1:", self.app.finance_rows[-1]["reference"])
        self.assertEqual(self.app.cash, max(0, cash_before + card["finance"]["profit"]))
        self.assertIsNone(self.app.run_combat_sport_card(
            "Boxing", self.world, self.app.player_company_name, player_owned=True,
            bouts=[{"a": self.a, "b": self.b}], event_name="Too Soon",
        ))

    def test_future_card_persists_forecast_and_runs_only_when_due(self):
        planned = [{
            "a_id": self.a.fighter_id, "b_id": self.b.fighter_id,
            "a": self.a.name, "b": self.b.name, "title": False,
        }]
        ok, _note, event = self.app.schedule_player_combat_event(
            "Boxing", planned, self.app.month, 3, "Future Fight Night",
            production="Arena", marketing=25_000,
        )
        self.assertTrue(ok)
        self.assertEqual(event["production"], "Arena")
        self.assertEqual(event["marketing"], 25_000)
        self.assertEqual(event["forecast"]["fighter_payroll"], 16_500)
        self.assertEqual(self.app.process_due_player_combat_events(), [])
        self.assertEqual(len(self.division["scheduled_events"]), 1)
        self.app.week = 3
        completed = self.app.process_due_player_combat_events()
        self.assertEqual(len(completed), 1)
        self.assertFalse(self.division["scheduled_events"])
        self.assertEqual(completed[0]["event_plan"]["production"], "Arena")
        self.assertEqual(completed[0]["finance"], event["forecast"])

    def test_scheduled_card_can_be_cancelled_and_blocks_same_month_duplicate(self):
        planned = [{"a_id": self.a.fighter_id, "b_id": self.b.fighter_id, "a": self.a.name, "b": self.b.name}]
        ok, _note, event = self.app.schedule_player_combat_event("Boxing", planned, 9, 1, "First Booking")
        self.assertTrue(ok)
        duplicate, note, _ = self.app.schedule_player_combat_event("Boxing", planned, 9, 4, "Duplicate")
        self.assertFalse(duplicate)
        self.assertIn("already", note)
        cancelled, _note = self.app.cancel_player_combat_event("Boxing", event["event_id"])
        self.assertTrue(cancelled)
        self.assertFalse(self.division["scheduled_events"])

    def test_manager_exposes_scheduling_and_event_plan_controls(self):
        source = (Path(__file__).resolve().parent / "views.py").read_text(encoding="utf-8")
        self.assertIn('text="Schedule Show"', source)
        self.assertIn('"UPCOMING SCHEDULED CARDS"', source)
        self.assertIn('text="Production"', source)
        self.assertIn('text="Marketing $"', source)

    @staticmethod
    def membership_setup():
        app = CombatSportsMembershipHarness()
        athlete = fighter("Crossover Athlete", "box-membership", app.player_company_name)
        world = {
            "promotion": "World Boxing", "roster": [athlete], "prospects": [],
            "titles": {}, "events": [],
        }
        division = {
            "sport": "Boxing", "promotion_name": "Player Co Boxing",
            "roster": [athlete.name], "roster_ids": [athlete.fighter_id],
            "booked_bouts": [], "titles": {}, "title_ids": {},
            "title_history": {}, "rankings_by_division": {},
        }
        app.combat_sport_worlds["Boxing"] = world
        app.player_combat_divisions["Boxing"] = division
        return app, athlete, world, division

    def test_player_crossover_records_leave_and_join_facts_before_roster_change(self):
        app, athlete, _world, _division = self.membership_setup()
        ok, _note = app.move_player_combat_athlete_to_mma("Boxing", athlete)
        self.assertTrue(ok)
        rows = app.foundation_membership_events(fighter_id=athlete.fighter_id)
        self.assertEqual([row["action"] for row in rows], ["leave", "join"])
        self.assertEqual(rows[0]["promotion_name"], "Player Co Boxing")
        self.assertEqual(rows[1]["promotion_name"], app.player_company_name)
        self.assertEqual(rows[0]["source_transaction"], rows[1]["source_transaction"])

    def test_player_combat_release_records_both_sides_of_transition(self):
        app, athlete, _world, division = self.membership_setup()
        observed = []
        original_membership = app.record_membership_event

        def observe_membership(*args, **kwargs):
            observed.append((list(division.get("roster_ids", [])), list(division.get("roster", []))))
            return original_membership(*args, **kwargs)

        app.record_membership_event = observe_membership
        ok, _note = app.release_player_combat_athlete("Boxing", athlete)
        self.assertTrue(ok)
        self.assertEqual(
            observed,
            [([athlete.fighter_id], [athlete.name]), ([athlete.fighter_id], [athlete.name])],
        )
        rows = app.foundation_membership_events(fighter_id=athlete.fighter_id)
        self.assertEqual([row["action"] for row in rows], ["leave", "join"])
        self.assertEqual(rows[0]["promotion_name"], "Player Co Boxing")
        self.assertEqual(rows[1]["promotion_name"], "World Boxing")
        self.assertEqual(rows[0]["source_transaction"], rows[1]["source_transaction"])

    def test_ai_combat_sport_replenishment_records_the_new_membership(self):
        app = CombatSportsMembershipHarness()
        prospect = fighter("Generated Prospect", "box-generated", "World Boxing")
        world = {"promotion": "World Boxing", "roster": [], "prospects": []}
        app.combat_sport_roster = lambda _sport, _promotion=None: []
        app.combat_sport_roster_target = lambda _sport, _world: 1
        app.generate_combat_sport_prospect = lambda _sport, _world: prospect
        self.assertEqual(app.replenish_combat_sport_world("Boxing", world), 1)
        rows = app.foundation_membership_events(fighter_id=prospect.fighter_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["action"], "join")
        self.assertEqual(rows[0]["promotion_name"], "World Boxing")

    def test_combat_sport_retirement_records_departure_before_retired_flag(self):
        app, athlete, world, _division = self.membership_setup()
        athlete.retirement_pending = True
        state = {"titles": {}, "title_ids": {}, "title_history": {}}
        self.assertTrue(app.retire_combat_sport_after_final_fight("Boxing", world, athlete, state))
        rows = app.foundation_membership_events(fighter_id=athlete.fighter_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["action"], "leave")
        self.assertEqual(rows[0]["promotion_name"], app.player_company_name)
        self.assertTrue(athlete.retired)


if __name__ == "__main__":
    unittest.main()
