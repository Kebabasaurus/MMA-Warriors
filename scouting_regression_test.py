"""Focused headless regressions for the scouting assignment lifecycle."""

import random
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from models import Fighter
from views import ViewMixin
from world import WorldMixin


def fighter(name="Scouting Target", fighter_id="FTR-scout-target", **updates):
    values = dict(
        name=name,
        fighter_id=fighter_id,
        weight="Lightweight",
        age=24,
        record_w=6,
        record_l=1,
        striking=70,
        wrestling=68,
        grappling=69,
        cardio=72,
        chin=70,
        popularity=42,
        momentum=0,
        morale=70,
        purse=8_000,
        region="USA",
        potential=84,
        star_quality=55,
        media_presence=50,
        professionalism=72,
    )
    values.update(updates)
    return Fighter(**values)


def completed_report(target, kind="basic", completed_week=1):
    estimates = {
        "overall": {"low": target.overall - 4, "mid": target.overall, "high": target.overall + 4},
        "potential": {"low": target.potential - 5, "mid": target.potential, "high": target.potential + 5},
        "popularity": {"low": 38, "mid": 42, "high": 46},
        "star_quality": {"low": 50, "mid": 55, "high": 60},
        "media_presence": {"low": 46, "mid": 50, "high": 54},
        "professionalism": {"low": 68, "mid": 72, "high": 76},
    }
    return {
        "schema_version": 2,
        "fighter_id": target.fighter_id,
        "fighter_name": target.name,
        "kind": kind,
        "status": "Complete",
        "started_week": completed_week - 2,
        "completed_week": completed_week,
        "weeks_remaining": 0,
        "confidence": 72,
        "reveal": 100 if kind == "full" else 72,
        "scout": "Test Scout",
        "region": target.region,
        "notes": ["Prior usable report."],
        "estimates": estimates,
        "recommendation": "MONITOR",
        "recommendation_reason": "Prior recommendation.",
    }


class Var:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class SelectionTree:
    def __init__(self, selected):
        self.selected = (selected,)

    def selection(self):
        return self.selected


class RecordTree(SelectionTree):
    def __init__(self):
        super().__init__("")
        self.rows = {}

    def delete(self, *items):
        if items:
            for item in items:
                self.rows.pop(item, None)
        else:
            self.rows.clear()

    def get_children(self):
        return tuple(self.rows)

    def insert(self, _parent, _where, iid=None, values=(), **_kwargs):
        self.rows[iid] = values


class ScoutingHarness(ViewMixin, WorldMixin):
    def __init__(self):
        self.month = 1
        self.week = 1
        self.player_region = "USA"
        self.player_company_name = "Regression FC"
        self.cash = 1_000_000
        self.roster = []
        self.free_agents = []
        self.retired_fighters = []
        self.promotions = []
        self.staff = [{
            "name": "Test Scout",
            "staff_id": "STAFF-test-scout",
            "role": "Scout",
            "skill": 72,
            "fighter_judging": 74,
            "potential_judging": 73,
            "efficiency": 70,
            "regional_knowledge": 70,
            "networking": 70,
            "reliability": 75,
            "professionalism": 72,
        }]
        self.scouting = []
        self.scouting_reports = {}
        self.scouting_searches = []
        self.scouting_shortlist = []
        self.scouting_watchlists = []
        self.scouting_history = []
        self.scouting_knowledge = {}
        self.scouting_alert_state = {}
        self._scouting_state_migrated = True
        self.rules = {"auto_assign_idle_scouts": False, "scouting_mode": True}
        self.inbox = []
        self.news = []
        self.finance = {"staff_payroll": 0}
        self.closed_divisions = set()
        self.academy = {}

    def record_finance_transaction(self, *_args, **_kwargs):
        pass

    def refresh_scouting_center(self):
        pass

    def refresh_scouting_targets(self):
        pass

    def show_selected_scouting_assignment(self):
        pass

    def scout_signing_recommendation(self, _fighter, report):
        return ("MONITOR", "Regression recommendation.") if report.get("status") == "Complete" else ("PENDING", "Pending.")


class ScoutingRegressionTests(unittest.TestCase):
    def test_ambiguous_legacy_name_report_is_not_shared_by_duplicate_fighters(self):
        first = fighter("Alex Smith", "FTR-alex-one")
        second = fighter("Alex Smith", "FTR-alex-two")
        app = ScoutingHarness()
        app.free_agents = [first, second]
        app.scouting_reports = {"Alex Smith": completed_report(first)}
        app.scouting_reports["Alex Smith"].pop("fighter_id", None)
        app._scouting_state_migrated = False

        app.migrate_scouting_state()

        self.assertFalse(app.scouting_report_for(first))
        self.assertFalse(app.scouting_report_for(second))

    def test_scouting_migration_does_not_advance_global_rng(self):
        target = fighter()
        app = ScoutingHarness()
        app.free_agents = [target]
        report = completed_report(target)
        report.pop("estimates")
        app.scouting_reports = {target.fighter_id: report}
        app._scouting_state_migrated = False
        random.seed(918273)
        before = random.getstate()

        app.migrate_scouting_state()

        self.assertEqual(before, random.getstate())

    def test_null_scouting_collections_normalize_to_empty(self):
        app = ScoutingHarness()
        app.scouting = None
        app.scouting_reports = None
        app.scouting_searches = None
        app.scouting_shortlist = None
        app.scouting_watchlists = None
        app.scouting_history = None
        app.scouting_knowledge = None
        app.scouting_alert_state = None
        app._scouting_state_migrated = False

        app.migrate_scouting_state()

        self.assertEqual([], app.scouting)
        self.assertEqual({}, app.scouting_reports)
        self.assertEqual([], app.scouting_searches)
        self.assertEqual([], app.scouting_shortlist)
        self.assertEqual("WATCH-main", app.scouting_watchlists[0]["watchlist_id"])
        self.assertEqual([], app.scouting_history)
        self.assertEqual({}, app.scouting_knowledge)
        self.assertEqual({}, app.scouting_alert_state)

    def test_prior_report_remains_usable_during_upgrade_and_after_cancel(self):
        target = fighter()
        app = ScoutingHarness()
        app.free_agents = [target]
        prior = completed_report(target)
        app.scouting_reports[target.fighter_id] = prior

        with patch("views.messagebox.showinfo"):
            self.assertTrue(app.start_scout_report_for_fighter(target, "full", scout_name="STAFF-test-scout"))
        self.assertEqual(prior["estimates"]["overall"], app.scouting_estimate(target, "overall"))

        row_id = f"report:{target.fighter_id}"
        app.scouting_assignment_tree = SelectionTree(row_id)
        app.scouting_assignment_rows = {
            row_id: {"type": "report", "fighter": target, "report": app.scouting_reports[target.fighter_id]}
        }
        app.scouting_status_var = Var()
        app.cancel_selected_scouting_assignment()

        restored = app.scouting_report_for(target)
        self.assertEqual("Complete", restored.get("status"))
        self.assertEqual(prior["estimates"]["overall"], app.scouting_estimate(target, "overall"))

    def test_observation_expiry_restores_prior_completed_report(self):
        target = fighter()
        app = ScoutingHarness()
        app.free_agents = [target]
        prior = completed_report(target)
        app.scouting_reports[target.fighter_id] = prior
        with patch("views.messagebox.showinfo"):
            self.assertTrue(app.start_scout_report_for_fighter(target, "observation", scout_name="STAFF-test-scout"))
        app.scouting_reports[target.fighter_id]["weeks_remaining"] = 1

        app.process_scouting_reports()
        app.week = 2
        app.process_scouting_reports()

        restored = app.scouting_report_for(target)
        self.assertEqual("Complete", restored.get("status"))
        self.assertEqual(prior["estimates"]["overall"], app.scouting_estimate(target, "overall"))

    def test_observation_can_complete_during_its_final_week(self):
        target = fighter()
        app = ScoutingHarness()
        app.free_agents = [target]
        app.scouting_reports[target.fighter_id] = {
            "schema_version": 2,
            "fighter_id": target.fighter_id,
            "fighter_name": target.name,
            "kind": "observation",
            "status": "In progress",
            "weeks_remaining": 1,
            "confidence": 55,
            "reveal": 0,
            "scout": "Test Scout",
            "notes": [],
        }

        app.process_scouting_reports()
        self.assertEqual("In progress", app.scouting_reports[target.fighter_id]["status"])
        app.complete_fight_observation(target)
        self.assertEqual("Complete", app.scouting_reports[target.fighter_id]["status"])

    def test_cancelled_expired_and_stale_reports_are_rediscoverable(self):
        for status, completed_week in (("Cancelled", 1), ("Expired", 1), ("Complete", 1)):
            with self.subTest(status=status):
                target = fighter(fighter_id=f"FTR-{status.lower()}")
                app = ScoutingHarness()
                app.month = 20 if status == "Complete" else 1
                app.free_agents = [target]
                old = completed_report(target, completed_week=completed_week)
                old["status"] = status
                app.scouting_reports[target.fighter_id] = old
                app.scouting_searches = [{
                    "assignment_id": f"SEARCH-{status}",
                    "type": "Talent Search",
                    "scout": "Test Scout",
                    "region": "USA",
                    "gender": "All",
                    "weight": "All",
                    "focus": "Free Agent Pool",
                    "status": "In progress",
                    "weeks_remaining": 1,
                    "started_week": 1,
                    "cost": 0,
                }]
                with patch.object(app, "create_generated_fighter", create=True, side_effect=AssertionError("usable candidate was replaced by an emergency fighter")):
                    app.process_talent_searches()

                self.assertEqual("Complete", app.scouting_searches[0]["status"])
                self.assertEqual(target.fighter_id, app.scouting_searches[0].get("result_fighter_id"))
                self.assertEqual("Complete", app.scouting_reports[target.fighter_id]["status"])

    def test_stale_basic_and_observation_ranges_widen_over_time(self):
        target = fighter()
        for kind in ("basic", "observation"):
            with self.subTest(kind=kind):
                app = ScoutingHarness()
                app.free_agents = [target]
                app.scouting_reports[target.fighter_id] = completed_report(target, kind=kind, completed_week=1)
                app.month, app.week = 1, 1
                fresh = app.scouting_estimate(target, "overall")
                app.month, app.week = 28, 2
                stale = app.scouting_estimate(target, "overall")
                fresh_width = fresh["high"] - fresh["low"]
                stale_width = stale["high"] - stale["low"]
                self.assertGreater(stale_width, fresh_width)

    def test_completed_week_label_uses_stored_week_not_today(self):
        app = ScoutingHarness()
        app.month, app.week = 20, 4

        label = app.scouting_week_label(10)

        self.assertEqual(app.format_game_date(3, 2, include_week=False), label)
        self.assertNotEqual(app.format_game_date(app.month, app.week, include_week=False), label)

    def test_completed_search_resolves_headline_and_all_result_fighters_by_id(self):
        headline = fighter("Headline", "FTR-headline")
        secondary = fighter("Secondary", "FTR-secondary")
        app = ScoutingHarness()
        app.free_agents = [headline, secondary]
        app.scouting_searches = [{
            "type": "Talent Search",
            "status": "Complete",
            "scout": "Test Scout",
            "region": "USA",
            "gender": "All",
            "weight": "All",
            "focus": "Free Agent Pool",
            "weeks_remaining": 0,
            "result_fighter_id": headline.fighter_id,
            "result_fighter_ids": [headline.fighter_id, secondary.fighter_id],
            "result_name": headline.name,
            "result_names": [headline.name, secondary.name],
            "cost": 5_000,
        }]
        app.scouting_assignment_tree = RecordTree()
        app.scouting_scout_box = SimpleNamespace(configure=lambda **_kwargs: None)
        app.scouting_scout_var = Var("Auto Assign")
        app.scouting_status_var = Var()

        ViewMixin.refresh_scouting_center(app)

        row = app.scouting_assignment_rows["search:0"]
        self.assertIs(headline, row["fighter"])
        self.assertEqual([headline, secondary], row["fighters"])

    def test_duplicate_name_scouts_keep_independent_capacity_and_workload(self):
        first = {
            "name": "Sam Lee", "staff_id": "STF-scout-aaa111", "role": "Scout",
            "skill": 55, "efficiency": 50,
        }
        second = {
            "name": "Sam Lee", "staff_id": "STF-scout-bbb222", "role": "Scout",
            "skill": 90, "efficiency": 90,
        }
        app = ScoutingHarness()
        app.staff = [first, second]
        app.scouting_reports = {
            "FTR-first": {
                "status": "In progress", "scout": "Sam Lee", "scout_id": first["staff_id"],
            },
            "FTR-second": {
                "status": "In progress", "scout": "Sam Lee", "scout_id": second["staff_id"],
            },
        }
        app.scouting_searches = [{
            "status": "In progress", "scout": "Sam Lee", "scout_id": second["staff_id"],
        }]

        self.assertEqual(1, app.scout_capacity(first))
        self.assertEqual(3, app.scout_capacity(second))
        self.assertEqual(1, app.scout_workload(first))
        self.assertEqual(2, app.scout_workload(second))
        self.assertIs(first, app.scout_for_assignment(app.scouting_reports["FTR-first"]))
        self.assertIs(second, app.scout_for_assignment(app.scouting_reports["FTR-second"]))
        self.assertFalse(app.scout_for_assignment({"scout": "Sam Lee"}, default=None))

    def test_duplicate_name_scout_selection_labels_map_to_durable_ids(self):
        scouts = [
            {"name": "Sam Lee", "staff_id": "STF-scout-aaa111", "role": "Scout"},
            {"name": "Sam Lee", "staff_id": "STF-scout-bbb222", "role": "Scout"},
        ]
        app = ScoutingHarness()
        app.staff = scouts

        labels, identities = app.scout_selection_options(scouts)

        self.assertEqual(2, len(labels))
        self.assertEqual(2, len(set(labels)))
        self.assertTrue(all(label.startswith("Sam Lee [") for label in labels))
        self.assertEqual({scout["staff_id"] for scout in scouts}, set(identities.values()))
        self.assertEqual(scouts[0]["staff_id"], identities[labels[0]])
        self.assertEqual(scouts[1]["staff_id"], identities[labels[1]])

    def test_scouting_layout_reflows_and_assignment_history_scrolls(self):
        source = (Path(__file__).parent / "ui.py").read_text(encoding="utf-8")
        scouting_ui = source.split("    def build_scouting_tab", 1)[1].split("\n    def ", 1)[0]

        for frame_name in ("target_search_row", "target_filter_row", "report_action_row", "target_action_row",
                           "scout_brief_row", "scout_filter_row", "scout_action_row", "assignment_tree_frame"):
            self.assertIn(frame_name, scouting_ui)
        self.assertIn('orient="vertical", command=self.scouting_assignment_tree.yview', scouting_ui)
        self.assertIn('orient="horizontal", command=self.scouting_assignment_tree.xview', scouting_ui)
        self.assertIn('"Cancelled", "Expired"', scouting_ui)

    def test_pending_report_hides_conclusions_and_charges_department(self):
        target = fighter()
        app = ScoutingHarness()
        app.free_agents = [target]
        before = app.cash

        with patch("views.messagebox.showinfo"):
            self.assertTrue(app.start_scout_report_for_fighter(target, "basic", scout_name="STAFF-test-scout"))

        report = app.scouting_reports[target.fighter_id]
        self.assertEqual([], report["notes"])
        self.assertEqual({}, report["estimates"])
        self.assertEqual(before - 2_500, app.cash)
        self.assertEqual("Assignment Started", app.scouting_history[-1]["type"])

    def test_automatic_scouting_is_paid_and_capped_at_one_dossier_per_week(self):
        app = ScoutingHarness()
        app.rules["auto_assign_idle_scouts"] = True
        app.free_agents = [fighter("First", "FTR-auto-one"), fighter("Second", "FTR-auto-two")]
        before = app.cash

        app.auto_assign_idle_scouts()
        app.auto_assign_idle_scouts()

        active = [row for row in app.scouting_reports.values() if row.get("status") == "In progress"]
        self.assertEqual(1, len(active))
        self.assertEqual(before - 1_000, app.cash)

    def test_fight_observation_records_structured_performance_evidence(self):
        target = fighter()
        opponent = fighter("Opponent", "FTR-observation-opponent")
        app = ScoutingHarness()
        app.free_agents = [target, opponent]
        app.scouting_reports[target.fighter_id] = {
            "fighter_id": target.fighter_id, "fighter_name": target.name, "kind": "observation",
            "status": "In progress", "weeks_remaining": 4, "confidence": 55, "scout": "Test Scout",
            "scout_id": "STAFF-test-scout", "history": [], "look_number": 1,
        }
        target.last_fight_stats = {
            "sig": 42, "sig_att": 70, "td": 2, "td_att": 4, "sub_att": 1,
            "control_secs": 155, "knockdowns": 1, "rounds": 3, "damage_taken": 29,
        }

        app.complete_fight_observation(target, opponent, "Win", "Decision", {"title": True})

        evidence = app.scouting_reports[target.fighter_id]["evidence"]
        self.assertEqual(opponent.fighter_id, evidence["opponent_id"])
        self.assertEqual(60, evidence["sig_accuracy"])
        self.assertEqual(155, evidence["control_secs"])
        self.assertTrue(evidence["title_fight"])

    def test_empty_search_does_not_create_a_fighter(self):
        app = ScoutingHarness()
        app.scouting_searches = [{
            "assignment_id": "SEARCH-empty", "status": "In progress", "weeks_remaining": 1,
            "scout": "Test Scout", "scout_id": "STAFF-test-scout", "region": "USA",
            "gender": "Female", "weight": "Heavyweight", "focus": "Free Agent Pool",
            "priority": "Balanced", "cost": 5_000,
        }]

        with patch.object(app, "create_generated_fighter", create=True, side_effect=AssertionError("search created supply")):
            app.process_talent_searches()

        self.assertEqual("No suitable lead", app.scouting_searches[0]["result_name"])
        self.assertEqual([], app.free_agents)

    def test_full_certainty_requires_a_repeated_high_confidence_look(self):
        target = fighter()
        app = ScoutingHarness()
        scout = app.staff[0]

        first = app.build_scouting_estimates(target, scout, "full", 90, rng=random.Random(7), look_count=1)
        repeated = app.build_scouting_estimates(target, scout, "full", 90, rng=random.Random(7), look_count=2)

        self.assertGreater(first["overall"]["high"] - first["overall"]["low"], 0)
        self.assertEqual(target.overall, repeated["overall"]["mid"])
        self.assertEqual(repeated["overall"]["low"], repeated["overall"]["high"])

    def test_search_priority_changes_candidate_ranking(self):
        app = ScoutingHarness()
        veteran = fighter("Veteran", "FTR-veteran", age=32, striking=82, wrestling=80, grappling=80, cardio=80, chin=80, potential=82)
        prospect = fighter("Prospect", "FTR-prospect", age=20, striking=63, wrestling=62, grappling=62, cardio=64, chin=64, potential=96)
        scout = app.staff[0]

        with patch("world.random.uniform", return_value=0):
            immediate = {row.fighter_id: app.scouting_search_score(row, scout, "Any Market", "Free Agent", "Immediate Ability") for row in (veteran, prospect)}
            future = {row.fighter_id: app.scouting_search_score(row, scout, "Any Market", "Free Agent", "High Potential") for row in (veteran, prospect)}

        self.assertGreater(immediate[veteran.fighter_id], immediate[prospect.fighter_id])
        self.assertGreater(future[prospect.fighter_id], future[veteran.fighter_id])

    def test_thin_search_returns_labelled_near_matches_without_creating_supply(self):
        exact = fighter("Exact", "FTR-exact", age=22, style="Wrestler")
        near = fighter("Near", "FTR-near", age=27, style="Kickboxer")
        app = ScoutingHarness()
        app.free_agents = [exact, near]
        app.scouting_searches = [{
            "assignment_id": "SEARCH-near", "status": "In progress", "weeks_remaining": 1,
            "scout": "Test Scout", "scout_id": "STAFF-test-scout", "region": "USA",
            "gender": "Male", "weight": "Lightweight", "focus": "Free Agent Pool",
            "priority": "Balanced", "age_band": "Under 23", "style": "Wrestler",
            "level": "Standard", "cost": 5_000,
        }]

        app.process_talent_searches()

        self.assertEqual(["Exact Match", "Near Match"], app.scouting_searches[0]["result_match_quality"])
        self.assertEqual(2, len(app.free_agents))

    def test_ongoing_search_retains_slot_and_schedules_quarterly_refresh(self):
        target = fighter()
        app = ScoutingHarness()
        app.free_agents = [target]
        app.scouting_searches = [{
            "assignment_id": "SEARCH-ongoing", "status": "In progress", "weeks_remaining": 1,
            "scout": "Test Scout", "scout_id": "STAFF-test-scout", "region": "USA",
            "gender": "All", "weight": "All", "focus": "Free Agent Pool",
            "priority": "Balanced", "age_band": "Any Age", "style": "All",
            "level": "Ongoing", "cost": 5_000,
        }]

        app.process_talent_searches()

        self.assertEqual("Monitoring", app.scouting_searches[0]["status"])
        self.assertEqual(13, app.scouting_searches[0]["weeks_remaining"])
        self.assertEqual(1, app.scout_workload(app.staff[0]))

    def test_watchlist_alert_is_emitted_once_per_material_state_change(self):
        target = fighter()
        app = ScoutingHarness()
        app.free_agents = [target]
        app.scouting_shortlist = [target.fighter_id]
        app.process_scouting_watchlist_alerts()  # observational baseline
        target.record_w += 1
        target.ai_offer_company = "Rival FC"

        app.process_scouting_watchlist_alerts()
        count = len([row for row in app.inbox if row.get("subject", "").startswith("Watchlist Update")])
        app.process_scouting_watchlist_alerts()

        self.assertEqual(1, count)
        self.assertEqual(count, len([row for row in app.inbox if row.get("subject", "").startswith("Watchlist Update")]))

    def test_expired_scout_closes_established_academy_network(self):
        app = ScoutingHarness()
        app.staff[0]["contract_months"] = 1
        app.staff[0]["salary"] = 5_000
        app.academy = app.academy_defaults()
        app.academy.update({
            "owned": True, "network_active": True, "network_weeks": 0,
            "network_region": "USA", "network_scout": "Test Scout",
            "network_scout_id": "STAFF-test-scout", "talent_pool": [{"name": "Lead"}],
        })

        app.update_staff_contracts()

        self.assertEqual([], app.staff)
        self.assertFalse(app.academy["network_active"])
        self.assertEqual([], app.academy["talent_pool"])
        self.assertFalse(any(row["subject"].startswith("Staff Deal Extended") for row in app.inbox))


if __name__ == "__main__":
    unittest.main(verbosity=2)
