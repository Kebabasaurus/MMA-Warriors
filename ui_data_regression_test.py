"""Focused regressions for UI/scouting/world-data QA fixes.

This suite intentionally avoids creating a Tk root so it can run in CI and on
headless packaging workers.
"""

import ast
import json
import inspect
import math
import unittest
from collections import Counter
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from models import Gym
from admin import AdminMixin
from fight_engine import FightEngineMixin
from media import MediaMixin
from events import EventMixin
from awards import AwardsMixin
from persistence import PersistenceMixin
from seeding import SeedMixin
from ui import UIMixin
from views import ViewMixin
from world import WorldMixin


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


class ListSelection:
    def __init__(self, index=0):
        self.index = index

    def curselection(self):
        return (self.index,) if self.index is not None else ()


class RegionListSelection(ListSelection):
    def __init__(self, values, index=0):
        super().__init__(index)
        self.values = list(values)

    def get(self, index):
        return self.values[index]

    def delete(self, *_args):
        self.values = []
        self.index = None

    def insert(self, _where, value):
        self.values.append(value)

    def size(self):
        return len(self.values)

    def selection_set(self, index):
        self.index = index


class Text:
    def __init__(self):
        self.value = ""

    def config(self, **_kwargs):
        pass

    def delete(self, *_args):
        self.value = ""

    def insert(self, _where, value):
        self.value += str(value)


class ViewHarness(ViewMixin, FightEngineMixin):
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


class WorldReviewHarness(WorldMixin):
    def scheduled_fighter_references(self, include_booked=False):
        return set(self.scheduled_references)

    def fighter_has_scheduled_fight(self, fighter, include_booked=False):
        return fighter.name in self.scheduled_references or fighter.fighter_id in self.scheduled_references


class FinanceReaderHarness(WorldMixin):
    """Minimal host for testing finance-only projections without Tk state."""

    def __init__(self, finance):
        self.finance = finance
        self.company_pop = 70
        self.cash = 5_000_000
        self.player_company_name = "Reader FC"


class UIDataRegressionTests(unittest.TestCase):
    def test_event_log_presentation_classifies_without_rewriting_lines(self):
        samples = [
            ("Spring Card - Venue", "=" * 60, "log_event_header"),
            ("=" * 60, "", "log_divider"),
            ("Tony def. Alex by KO (R2)", "", "log_result"),
            ("The referee has seen enough and stops the contest.", "", "log_highlight"),
            ("Month 4: overhead paid.", "", "log_system"),
            ("Signed Prospect One to a contract.", "", "log_action"),
            ("A quiet exchange was recorded.", "", "log_body"),
        ]
        for line, next_line, expected in samples:
            self.assertIn(expected, UIMixin.event_log_line_tags(line, next_line))
        source = inspect.getsource(UIMixin.render_event_log)
        self.assertIn("if isinstance(raw_entries, (list, tuple))", source)
        self.assertIn("load/migration review is required", source)

    def test_fight_night_archive_projection_keeps_replay_and_results_only_rows(self):
        harness = object.__new__(UIMixin)
        replay = {
            "record_id": "event-replay", "company": "Alpha", "event_name": "Alpha 1",
            "date": "Month 2 Week 1", "fight_logs": [{"a": "One", "b": "Two"}],
            "log": ["Alpha 1"], "future_field": {"kept": True},
        }
        duplicate_index = {
            "record_id": "event-replay", "company": "Alpha", "event": "Alpha 1",
            "date": "Month 2 Week 1", "bout_results": [{"result": "One def. Two"}],
        }
        results_only = {
            "record_id": "event-index", "company": "Beta", "event": "Beta 4",
            "date": "Month 1 Week 4", "bout_results": [{"result": "Draw"}], "has_replay": True,
        }
        harness.player_event_archive = [replay]
        harness.ai_event_archive = []
        harness.result_index = [duplicate_index, results_only]
        harness.result_records = []
        before = json.dumps(replay, sort_keys=True)

        rows = UIMixin.fight_night_archive_rows(harness)

        self.assertEqual(["event-replay", "event-index"], [row["record_id"] for row in rows])
        self.assertTrue(rows[0]["replay"])
        self.assertEqual("Replay ready", rows[0]["status"])
        self.assertFalse(rows[1]["replay"])
        self.assertEqual("Results only", rows[1]["status"])
        self.assertEqual(before, json.dumps(replay, sort_keys=True))
        self.assertIs(rows[0]["record"], replay)

    def test_scouting_target_board_exposes_named_watchlist_management(self):
        source = inspect.getsource(UIMixin.build_scouting_tab)
        for marker in ("Active watchlist", "New List", "Rename", "Archive", "scouting_watchlist_box"):
            self.assertIn(marker, source)
        for method in ("refresh_scouting_watchlists", "switch_selected_scouting_watchlist", "create_scouting_watchlist_from_ui", "rename_scouting_watchlist_from_ui", "archive_scouting_watchlist_from_ui"):
            self.assertIn(method, inspect.getsource(ViewMixin))

    def test_finance_landing_promotes_read_only_decision_cards(self):
        source = inspect.getsource(UIMixin.build_finance_tab)
        for key, label in (
            ("cash", "CASH ON HAND"),
            ("commitments", "MONTHLY COMMITMENTS"),
            ("event_income", "NEXT EVENT INCOME"),
            ("exposure", "BOOKED EXPOSURE"),
        ):
            self.assertIn(f'("{key}"', source)
            self.assertIn(label, source)
        refresh = inspect.getsource(ViewMixin.refresh_finance)
        self.assertIn("finance_kpi_cards", refresh)
        self.assertIn("event_medical_exposure", refresh)
        defaults = inspect.getsource(ViewMixin.ensure_finance_defaults)
        self.assertIn("media_rights_legacy_raw", defaults)
        self.assertIn("safe_int", defaults)
        runway = inspect.getsource(UIMixin.build_finance_tab)
        runway_refresh = inspect.getsource(ViewMixin.refresh_finance_runway)
        scenario = inspect.getsource(ViewMixin.save_cash_runway_scenario_from_ui)
        scenario_reader = inspect.getsource(ViewMixin.open_cash_runway_scenarios_window)
        self.assertIn("Save Scenario Snapshot", runway)
        self.assertIn("cash_runway_scenarios", runway_refresh)
        self.assertIn("non-binding", scenario)
        for marker in ("SNAPSHOT DETAIL", "PROPOSED EDITS (NOT APPLIED)", "freshness", "read-only evidence"):
            self.assertIn(marker, scenario_reader)
        self.assertIn("_finance_runway_sensitivity_values", runway_refresh)
        self.assertIn("_read_status", runway_refresh)
        self.assertIn("Saved planning snapshots: unavailable", runway_refresh)

    def test_contracts_landing_has_selected_read_only_brief(self):
        source = inspect.getsource(UIMixin.build_contracts_tab)
        self.assertIn("contract_selected_summary", source)
        self.assertIn("Renewal is a separate player action", inspect.getsource(ViewMixin.show_selected_contract_summary))
        self.assertIn("champions_clause", inspect.getsource(ViewMixin.show_selected_contract_summary))

    def test_combat_sport_contract_rows_keep_identity_selection_across_refresh(self):
        source = inspect.getsource(ViewMixin.refresh_sport_contracts)
        for marker in ("prior_selection", "fighter_identity_key", "sportcontract:", "restored_row_id", "selection_set"):
            self.assertIn(marker, source)
        self.assertIn("player_combat_contract_rows(repair=False)", source)

    def test_mma_contract_rows_keep_identity_selection_across_refresh(self):
        source = inspect.getsource(ViewMixin.refresh_contracts)
        for marker in ("prior_selection", "prior_identity", "fighter_identity_key", "restored_row_id", "selection_set"):
            self.assertIn(marker, source)
        self.assertIn("duplicate", source)

    def test_fighter_tree_row_keys_ignore_visible_order_and_suffix_duplicates(self):
        first = SimpleNamespace(fighter_id="fighter-7", name="Stable")
        second = SimpleNamespace(fighter_id="fighter-8", name="Moved")
        self.assertEqual(ViewMixin.fighter_tree_row_id(ViewHarness(), "roster", first, 0), "roster:fighter-7")
        self.assertEqual(ViewMixin.fighter_tree_row_id(ViewHarness(), "roster", first, 99), "roster:fighter-7")
        rows = {}
        self.assertEqual(ViewMixin.unique_fighter_tree_row_id(ViewHarness(), rows, "roster", first), "roster:fighter-7")
        rows["roster:fighter-7"] = first
        self.assertEqual(ViewMixin.unique_fighter_tree_row_id(ViewHarness(), rows, "roster", second), "roster:fighter-8")
        self.assertEqual(ViewMixin.unique_fighter_tree_row_id(ViewHarness(), rows, "roster", first), "roster:fighter-7#2")

    def test_game_menu_explains_empty_saves_and_keeps_database_controls_distinct(self):
        source = inspect.getsource(UIMixin.build_game_menu_tab)
        self.assertIn("save_library_empty_hint", source)
        self.assertIn("DATABASE / WORLD", source)
        self.assertIn("SPECTATOR WORLD SIMULATION", source)
        self.assertIn("Migrate Profiles", source)
        self.assertIn("migrate_selected_save_archetypes", source)
        refresh = inspect.getsource(PersistenceMixin.refresh_game_menu)
        self.assertIn("save_entry_identity", refresh)
        self.assertIn("database_entry_identity", refresh)
        self.assertIn("marker_path = DATA_DIR / \"active_universe.txt\"", refresh)
        self.assertIn("primary_save_paths(create=False)", refresh)
        self.assertIn("default_database = DATABASE_DIR / \"Default Universe.universe.json\"", refresh)
        self.assertNotIn("SAVE_DIR.mkdir", refresh)
        self.assertNotIn("DATABASE_DIR.mkdir", refresh)
        self.assertNotIn("self.ensure_default_universe_database()", refresh)
        self.assertNotIn("self.ensure_rule_defaults()", refresh)
        summary = inspect.getsource(PersistenceMixin.refresh_save_selection_summary)
        self.assertIn("save_slot_reader", summary)
        self.assertIn("create=False", summary)
        self.assertIn("active_path = self.active_save_path()", summary)

    def test_company_takeover_guidance_stays_with_company_reader(self):
        helper = inspect.getsource(PersistenceMixin._company_takeover_notice)
        self.assertIn("_company_status_notice", helper)
        self.assertIn("warning=True", helper)
        for method in (PersistenceMixin.take_control_selected_company, PersistenceMixin.take_control_of_company, PersistenceMixin.return_to_spectator_mode):
            source = inspect.getsource(method)
            self.assertIn("_company_takeover_notice", source)

    def test_company_editor_refresh_uses_defensive_read_models(self):
        source = inspect.getsource(ViewMixin.refresh_company_editor)
        for marker in ("belts_view", "interim_belts_view", "special_belts_view", "rules_view", "broadcasters_view"):
            self.assertIn(marker, source)
        self.assertNotIn("self.ensure_rule_defaults()", source)
        self.assertNotIn("self.ensure_broadcast_contract_defaults()", source)
        malformed = {"Male Lightweight": {"holder": "A"}, "Bad": {"defenses": "not-a-number", "history": "bad"}}
        before = json.dumps(malformed, sort_keys=True)
        projected = AdminMixin.normalize_special_belts(None, malformed)
        self.assertEqual(projected["Bad"]["defenses"], 0)
        self.assertEqual(projected["Bad"]["history"], [])
        self.assertEqual(before, json.dumps(malformed, sort_keys=True))
        self.assertEqual({}, AdminMixin.normalize_special_belts(None, "malformed"))
        for method in (ViewMixin.vacate_selected_special_belt, ViewMixin.delete_selected_special_belt):
            action_source = inspect.getsource(method)
            self.assertIn("holder_id", action_source)
            self.assertIn("_resolve_event_fighter", action_source)

    def test_game_settings_open_is_projection_only_until_apply(self):
        source = inspect.getsource(ViewMixin.open_game_settings_window)
        before_apply = source.split("        def apply():", 1)[0]
        self.assertIn("settings_rules", before_apply)
        self.assertIn("raw_rules", before_apply)
        self.assertIn("normalize_fight_night_audio_volume", before_apply)
        self.assertNotIn("self.ensure_rule_defaults()", before_apply)
        self.assertNotIn("self.ensure_audio_defaults()", before_apply)
        apply_block = source.split("        def apply():", 1)[1]
        self.assertIn("self.ensure_rule_defaults()", apply_block)

    def test_simulation_lab_exposes_explicit_100_year_audit_and_balance_evidence(self):
        source = inspect.getsource(UIMixin.build_sim_lab_tab)
        self.assertIn("Run 100-Year Audit", source)
        self.assertIn("run_100_year_play_audit", source)
        runner = inspect.getsource(__import__("admin").AdminMixin.run_play_level_audit)
        for marker in ("audit_balance_findings", "title_holders", "history_total", "blocking_balance_findings"):
            self.assertIn(marker, runner)

    def test_due_event_choice_uses_a_managed_decision_surface(self):
        source = inspect.getsource(EventMixin.prompt_due_event)
        for marker in ("decision:due-event:", "create_managed_window", "Watch Live", "Simulate Now", "Stay on This Week", "The card is due now"):
            self.assertIn(marker, source)

    def test_spectator_preconditions_write_to_the_persistent_desk(self):
        source = inspect.getsource(WorldMixin.spectator_inline_notice)
        for marker in ("spectator_sim_status", "spectator_policy_status", "config", "return False"):
            self.assertIn(marker, source)
        for method in (WorldMixin.resume_spectator_simulation, WorldMixin.spectator_advance_weeks, WorldMixin.watch_latest_world_event, WorldMixin.spectator_watch_next_event):
            self.assertIn("spectator_inline_notice", inspect.getsource(method))

    def test_staff_and_testing_case_surfaces_expose_readable_workflow(self):
        staff_source = inspect.getsource(UIMixin.build_staff_tab)
        case_source = inspect.getsource(ViewMixin.open_drug_testing_cases_window)
        self.assertIn('(\"Testing Cases\", self.open_drug_testing_cases_window)', staff_source)
        for marker in ("CASE TIMELINE", "timeline_status_vars", "total_spend", "Recorded total", "workflow"):
            self.assertIn(marker, case_source)
        for marker in ("drug_testing_case_ui_identity", "used_ids", "previous_iid", "selection_set"):
            self.assertIn(marker, case_source)
        refresh = inspect.getsource(PersistenceMixin.refresh_game_menu)
        self.assertIn("save_entry_identity", refresh)
        self.assertIn("database_entry_identity", refresh)
        self.assertIn("marker_path = DATA_DIR / \"active_universe.txt\"", refresh)

    def test_contract_show_filters_share_month_and_special_obligation_meaning(self):
        helper = ViewMixin.contract_filter_matches
        self.assertTrue(helper("Expiring (<=3 mo)", 2))
        self.assertFalse(helper("Expiring (<=3 mo)", 2, is_comeback=True))
        self.assertFalse(helper("Final month", 1, retirement_pending=True))
        self.assertTrue(helper("Non-Exclusive", 24, exclusive=False))
        self.assertFalse(helper("Non-Exclusive", 24, exclusive=True))

    def test_matchmaking_delayed_layout_callbacks_are_destroy_safe(self):
        source = inspect.getsource(UIMixin.cancel_booking_layout_callbacks)
        schedule = inspect.getsource(UIMixin.schedule_booking_layout_callback)
        layout = inspect.getsource(UIMixin.configure_booking_panel_layout)
        for marker in ("after_cancel", "_booking_sash_after_id", "_booking_scroll_after_id"):
            self.assertIn(marker, source)
        self.assertIn("winfo_exists", schedule)
        self.assertIn("schedule_booking_layout_callback", layout)

    def test_matchmaking_stacked_layout_reserves_readable_explorer_height(self):
        source = inspect.getsource(UIMixin.configure_booking_panel_layout)
        self.assertIn('resize.configure(height=720)', source)
        self.assertIn('pane.add(available, minsize=520, stretch="always")', source)
        self.assertIn('card_height = min(190, max(170, height - 530))', source)
        self.assertIn('resize.configure(height=620)', source)

    def test_region_profile_promotes_read_only_context_cards(self):
        source = inspect.getsource(UIMixin.build_regions_tab)
        refresh = inspect.getsource(ViewMixin.refresh_region_profile)
        for key, label in (("economy", "MARKET"), ("legality", "REGULATION"), ("testing", "TESTING"), ("mma_love", "LOCAL PULSE")):
            self.assertIn(f'("{key}"', source)
            self.assertIn(label, source)
            self.assertIn(f'get("{key}"', refresh)

    def test_company_profile_promotes_standings_context_cards(self):
        source = inspect.getsource(UIMixin.build_companies_tab)
        refresh = inspect.getsource(ViewMixin.refresh_company_profile)
        for key, label in (("rank", "INDUSTRY RANK"), ("power", "POWER"), ("roster", "ROSTER"), ("stability", "STABILITY")):
            self.assertIn(f'("{key}"', source)
            self.assertIn(label, source)
            self.assertIn(f'"{key}":', refresh)

    def test_company_decision_center_exposes_identity_bound_next_steps(self):
        source = inspect.getsource(UIMixin.build_companies_tab)
        refresh = inspect.getsource(ViewMixin._refresh_company_next_steps)
        action = inspect.getsource(ViewMixin.open_company_next_step)
        for marker in ("NEXT STEP", "company_next_step_primary", "company_next_step_secondary"):
            self.assertIn(marker, source)
        for marker in ("Operating pressure", "Build a Card", "_company_next_step_source", "def safe_count(value):", "def safe_int(value, fallback=0):", "math.isfinite(numeric)"):
            self.assertIn(marker, refresh)
        for marker in ("expected", "current", "open_selected_company_section"):
            self.assertIn(marker, action)

    def test_region_decision_center_exposes_identity_bound_next_steps(self):
        source = inspect.getsource(UIMixin.build_regions_tab)
        refresh = inspect.getsource(ViewMixin._refresh_region_next_steps)
        action = inspect.getsource(ViewMixin.open_region_next_step)
        for marker in ("NEXT STEP", "region_next_step_primary", "region_next_step_secondary"):
            self.assertIn(marker, source)
        for marker in ("bookable_pairings", "Feasibility Review", "scheduled show", "_region_next_step_region"):
            self.assertIn(marker, refresh)
        for marker in ("expected", "current", "open_selected_region_feasibility", "open_selected_region_hub"):
            self.assertIn(marker, action)

    def test_regional_feasibility_reader_fails_closed_for_malformed_inputs(self):
        source = inspect.getsource(ViewMixin.open_region_feasibility_window)
        for marker in (
            "def display_int",
            "if not isinstance(invitation, dict)",
            "if not isinstance(snapshot, dict)",
            "as_of = snapshot.get(\"as_of\", {}) if isinstance(snapshot.get(\"as_of\"), dict) else {}",
            "scheduled = [row for row in (snapshot.get(\"scheduled_events\", []) or []) if isinstance(row, dict)]",
        ):
            self.assertIn(marker, source)
        self.assertIn("except (TypeError, ValueError, OverflowError)", source)

    def test_combat_sports_history_reader_fails_closed_for_malformed_rows(self):
        source = inspect.getsource(ViewMixin.open_combat_sport_history_window)
        for marker in (
            "if not isinstance(worlds, dict)",
            "if not isinstance(world, dict)",
            "if not isinstance(division, dict)",
            "if not isinstance(entry, dict)",
            "except (TypeError, ValueError, OverflowError)",
        ):
            self.assertIn(marker, source)
        self.assertIn("repair=False", source)

    def test_region_profile_reader_fails_closed_for_nonfinite_rows(self):
        reader = inspect.getsource(ViewMixin.region_data_reader)
        next_steps = inspect.getsource(ViewMixin._refresh_region_next_steps)
        refresh = inspect.getsource(ViewMixin.refresh_region_profile)
        self.assertIn("except (TypeError, ValueError, OverflowError)", reader)
        self.assertIn("except (TypeError, ValueError, OverflowError)", next_steps)
        self.assertIn("isinstance(e, dict)", refresh)
        self.assertIn("region_data_reader", refresh)

    def test_company_standings_projection_bounds_nonfinite_inputs(self):
        fighter = SimpleNamespace(
            retired=False, overall=float("inf"), elo_rating=float("nan"),
            champion=False, popularity=float("nan"), star_quality=float("inf"),
        )
        components = ViewMixin.company_power_components(
            None, [fighter], float("inf"), float("nan"), float("inf"), float("nan"),
        )
        self.assertTrue(all(math.isfinite(value) for _label, value in components))
        source = inspect.getsource(ViewMixin.industry_standings_rows)
        self.assertIn("if not isinstance(worlds, dict)", source)
        self.assertIn("world = raw_world if isinstance(raw_world, dict) else {}", source)
        self.assertIn("if isinstance(division, dict)", source)

    def test_staff_decision_center_exposes_identity_bound_next_steps(self):
        source = inspect.getsource(UIMixin.build_staff_tab)
        refresh = inspect.getsource(ViewMixin._refresh_staff_next_steps)
        action = inspect.getsource(ViewMixin.open_staff_next_step)
        for marker in ("NEXT STEP", "staff_next_step_primary", "staff_next_step_secondary"):
            self.assertIn(marker, source)
        for marker in ("expiring", "Evidence Audit", "Coverage gap", "_staff_next_step_source"):
            self.assertIn(marker, refresh)
        for marker in ("expected", "_staff_next_step_source_key", "open_staff_evidence_audit_window"):
            self.assertIn(marker, action)

    def test_scouting_decision_center_exposes_identity_bound_next_steps(self):
        source = inspect.getsource(UIMixin.build_scouting_tab)
        refresh = inspect.getsource(ViewMixin._refresh_scouting_next_steps)
        action = inspect.getsource(ViewMixin.open_scouting_next_step)
        for marker in ("NEXT STEP", "scouting_next_step_primary", "scouting_next_step_secondary"):
            self.assertIn(marker, source)
        for marker in ("RECOMMEND SIGNING", "Stale", "active_assignments", "_scouting_next_step_source"):
            self.assertIn(marker, refresh)
        for marker in ("expected", "_scouting_next_step_source_key", "show_selected_recruitment_target_summary"):
            self.assertIn(marker, action)

    def test_world_hub_decision_center_exposes_identity_bound_next_steps(self):
        source = inspect.getsource(UIMixin.build_world_tab)
        refresh = inspect.getsource(ViewMixin._refresh_world_next_steps)
        action = inspect.getsource(ViewMixin.open_world_next_step)
        for marker in ("NEXT STEP", "world_next_step_primary", "world_next_step_secondary"):
            self.assertIn(marker, source)
        for marker in ("Latest story", "Open Chronicle", "_world_next_step_source"):
            self.assertIn(marker, refresh)
        for marker in ("expected", "_world_next_step_source_key", "open_selected_world_story_reader"):
            self.assertIn(marker, action)

    def test_contract_review_routes_routine_feedback_to_page_alerts(self):
        source = inspect.getsource(ViewMixin._contract_status_notice)
        sports = inspect.getsource(ViewMixin.selected_sport_contract_row)
        batch = inspect.getsource(ViewMixin.open_contract_batch_workbench)
        auto = inspect.getsource(ViewMixin.auto_negotiate_selected_contracts)
        self.assertIn("contracts_alert", source)
        self.assertIn("sport_contracts_alert", source)
        self.assertIn("_contract_status_notice", sports)
        self.assertIn("_contract_status_notice", batch)
        self.assertIn("_contract_status_notice", auto)

    def test_roster_and_card_editor_route_routine_feedback_to_surface_notices(self):
        roster_ui = inspect.getsource(UIMixin.build_roster_tab)
        roster_view = inspect.getsource(ViewMixin._roster_status_notice)
        for marker in ("roster_action_notice", "Manage Divisions"):
            self.assertIn(marker, roster_ui)
        for marker in ("roster_action_notice", "native fallback", "warning"):
            self.assertIn(marker, roster_view)
        for method in (ViewMixin.cut_player_fighter, ViewMixin.close_selected_division, ViewMixin.reopen_selected_division):
            self.assertIn("_roster_status_notice", inspect.getsource(method))
        close_source = inspect.getsource(ViewMixin.close_selected_division)
        for marker in ("fighter_ids", "fight_uses_closed_division", "event_fight_participant_references"):
            self.assertIn(marker, close_source)
        editor = inspect.getsource(EventMixin.open_scheduled_card_editor)
        for marker in ("editor_status_var", "set_editor_status", "BOOKING BLOCKED", "REPLACEMENT BLOCKED"):
            self.assertIn(marker, editor)

    def test_free_agent_market_routes_routine_feedback_to_surface_notice(self):
        market_ui = inspect.getsource(UIMixin.build_market_tab)
        market_view = inspect.getsource(ViewMixin._market_status_notice)
        negotiation = inspect.getsource(EventMixin.open_negotiation)
        signing = inspect.getsource(EventMixin.sign_fighter)
        self.assertIn("market_action_notice", market_ui)
        self.assertIn("market_action_notice", market_view)
        self.assertIn("_market_status_notice", negotiation)
        self.assertIn("_market_status_notice", signing)

    def test_matchmaking_validation_keeps_routine_feedback_in_booking_surface(self):
        source = inspect.getsource(ViewMixin.add_matchup)
        tournament = inspect.getsource(ViewMixin.add_tournament_to_card)
        tba = inspect.getsource(ViewMixin.add_tba_matchup)
        compare = inspect.getsource(ViewMixin.compare_selected_card_matchup)
        fill = inspect.getsource(ViewMixin.fill_selected_tba_matchup)
        for method in (source, tournament, tba, compare, fill):
            self.assertIn("set_matchmaking_notice", method)
        self.assertIn("_resolve_event_fighter", compare)
        card_refresh = inspect.getsource(ViewMixin.refresh_card)
        for marker in ("_resolve_event_fighter", "Identity unavailable", "Review the saved fighter"):
            self.assertIn(marker, card_refresh)
        self.assertIn("set_schedule_status", inspect.getsource(ViewMixin.selected_booking_date))
        event_source = inspect.getsource(EventMixin.schedule_event)
        self.assertIn("_resolve_event_fighter", event_source)
        self.assertNotIn("self.get_fighter(reference)", event_source)

    def test_world_chronicle_exposes_read_only_exports(self):
        source = inspect.getsource(ViewMixin.open_world_chronicle)
        for marker in ("export_chronicle", "Export JSON", "Export Report", "Nothing to export", "read-only"):
            self.assertIn(marker, source)

    def test_fighter_search_keeps_selection_feedback_on_page(self):
        source = inspect.getsource(UIMixin.build_fighter_search_tab)
        view = inspect.getsource(ViewMixin._world_search_status_notice)
        profile = inspect.getsource(ViewMixin.open_selected_world_fighter_profile)
        compare = inspect.getsource(ViewMixin.compare_selected_world_fighters)
        self.assertIn("world_fighter_action_notice", source)
        self.assertIn("world_fighter_action_notice", view)
        self.assertIn("_world_search_status_notice", profile)
        self.assertIn("_world_search_status_notice", compare)

    def test_combat_sports_overview_keeps_routine_actions_in_context(self):
        source = inspect.getsource(ViewMixin.build_combat_sports_tab)
        for marker in ("status_var", "set_status", "DIVISION UNAVAILABLE", "open_history", "Circuit Records & History"):
            self.assertIn(marker, source)

    def test_combat_sports_overview_reader_fails_closed_for_malformed_worlds(self):
        source = inspect.getsource(ViewMixin.build_combat_sports_tab)
        for marker in ("raw_world", "world = raw_world if isinstance(raw_world, dict) else {}", "safe_display_int", "repair=False"):
            self.assertIn(marker, source)
        self.assertIn("isinstance(divisions, dict)", source)

    def test_assistant_decision_detail_explains_consequence_and_destination(self):
        source = inspect.getsource(UIMixin.build_assistant_tab)
        refresh = inspect.getsource(ViewMixin.refresh_assistant_decision_detail)
        self.assertIn("assistant_decision_consequence", source)
        for marker in ("Urgent", "Next:", "Why it matters", "consequence"):
            self.assertIn(marker, refresh)

    def test_company_hub_detail_reader_keeps_malformed_finance_and_staff_rows_visible(self):
        source = inspect.getsource(ViewMixin.open_selected_company_hub)
        for marker in (
            "required_fighter_fields",
            "omitted_roster_rows",
            "Unavailable roster evidence",
            'history = data.get("show_history", [])',
            'if not isinstance(finance_data, dict)',
            'staff_rows = data.get("staff", [])',
            'Unavailable staff record — retained for audit.',
            'Unknown salary',
        ):
            self.assertIn(marker, source)

    def test_results_detail_promotes_selected_event_context_cards(self):
        source = inspect.getsource(UIMixin.build_results_tab)
        refresh = inspect.getsource(ViewMixin.show_selected_result_detail)
        for key, label in (("date", "DATE"), ("main", "MAIN EVENT"), ("fights", "BOUTS"), ("profit", "RESULT")):
            self.assertIn(f'("{key}"', source)
            self.assertIn(label, source)
            self.assertIn(f'"{key}":', refresh)

    def test_results_tab_exposes_durable_tournament_history(self):
        source = inspect.getsource(UIMixin.build_results_tab)
        reader = inspect.getsource(ViewMixin.tournament_edition_rows)
        window = inspect.getsource(ViewMixin.open_tournament_history_window)
        self.assertIn("Tournament History", source)
        for marker in ("result_index", "entrant_ids", "seeds", "result_refs", "deepcopy", "rolls RNG"):
            self.assertIn(marker, reader)
        for marker in ("TOURNAMENT HISTORY", "SEEDED FIELD", "STAGES", "Open Source Card", "edition(s) indexed"):
            self.assertIn(marker, window)

    def test_rankings_labels_matching_and_shown_rows(self):
        source = inspect.getsource(UIMixin.build_rankings_tab)
        refresh = inspect.getsource(ViewMixin.refresh_rankings)
        for key, label in (("matching", "MATCHED"), ("shown", "SHOWN")):
            self.assertIn(f'("{key}"', source)
            self.assertIn(label, source)
            self.assertIn(f'"{key}"', refresh)
        self.assertIn('[:50]', refresh)
        self.assertIn('min(75, len(division))', refresh)
        self.assertIn('Company P4P', refresh)
        self.assertIn('Company Division', refresh)
        self.assertIn('ranking_row_meta', refresh)
        detail = inspect.getsource(ViewMixin.show_ranking_detail)
        self.assertIn('No same-scope snapshot', detail)

    def test_rankings_rows_use_identity_bound_selection(self):
        refresh = inspect.getsource(ViewMixin.refresh_rankings)
        for marker in ("prior_row_key", "_ranking_row_keys", "ranking_view_identity", "restore_selection", "iid=row_id"):
            self.assertIn(marker, refresh)
        harness = ViewHarness()
        fighter = SimpleNamespace(fighter_id="ranked-1")
        self.assertEqual(
            harness.ranking_view_identity("Pound-for-Pound", "Alpha", fighter),
            harness.ranking_view_identity("Pound-for-Pound", "Alpha", fighter),
        )
        self.assertNotEqual(
            harness.ranking_view_identity("Pound-for-Pound", "Alpha", fighter),
            harness.ranking_view_identity("Division Rankings", "Alpha", fighter),
        )

    def test_company_rankings_keep_duplicate_promotion_rosters_attached(self):
        refresh = inspect.getsource(ViewMixin.refresh_rankings)
        for marker in ("entity_id", "ranking_promotion_identity", "row[\"roster\"]", "entity_id=row[\"entity_id\"]"):
            self.assertIn(marker, refresh)
        self.assertNotIn("next(p.roster for p in self.promotions if p.name == row[0])", refresh)
        harness = ViewHarness()
        self.assertNotEqual(
            harness.ranking_view_identity("Company Rankings", "Same Name", entity_id="promotion:one"),
            harness.ranking_view_identity("Company Rankings", "Same Name", entity_id="promotion:two"),
        )
        detail = inspect.getsource(ViewMixin.show_ranking_detail)
        self.assertIn('meta.get("mode") == "Company Rankings"', detail)
        self.assertIn("promotion-level ranking", detail)

    def test_ranking_scope_and_rank_maps_keep_duplicate_promotions_separate(self):
        refresh = inspect.getsource(ViewMixin.refresh_rankings)
        rows_reader = inspect.getsource(ViewMixin.ranked_fighter_rows)
        maps = inspect.getsource(ViewMixin.division_rank_maps) + inspect.getsource(ViewMixin.p4p_rank_maps)
        for marker in ("_ranking_scope_rows", "scope_labels", "selected_promo", "previous_scope_entity", "restored_scope"):
            self.assertIn(marker, refresh + rows_reader)
        self.assertIn("ranking_company_identity", maps)
        self.assertIn("ranking_promotion_identity", refresh)
        f1 = SimpleNamespace(fighter_id="same-1", gender="Male", weight="Lightweight", champion=False, interim_champion=False)
        f2 = SimpleNamespace(fighter_id="same-2", gender="Male", weight="Lightweight", champion=False, interim_champion=False)
        p1 = SimpleNamespace(name="Same Name", region="USA", promotion_id="one", roster=[f1])
        p2 = SimpleNamespace(name="Same Name", region="UK", promotion_id="two", roster=[f2])
        harness = ViewHarness()
        harness.roster = []
        harness.player_company_name = "Player FC"
        harness.promotions = [p1, p2]
        harness._ranking_scope_rows = {
            "Same Name (UK)": {"name": "Same Name", "entity_id": "promotion:two", "promo": p2},
        }
        harness.ranking_gender_filter = Var("All")
        harness.ranking_weight_filter = Var("All")
        selected = harness.ranked_fighter_rows("Same Name (UK)")
        self.assertEqual(selected, [("Same Name", f2)])
        company_ranks, _world_ranks = harness.division_rank_maps(
            [("Same Name", f1), ("Same Name", f2)], {id(f1): 70, id(f2): 60},
        )
        self.assertIn(("promotion:one", "same-1"), company_ranks)
        self.assertIn(("promotion:two", "same-2"), company_ranks)

    def test_rankings_movement_does_not_relabel_division_history_as_p4p(self):
        fighter = SimpleNamespace(champion=False, ranking_position=2, previous_ranking_position=5)
        harness = ViewHarness()
        self.assertEqual(harness.ranking_movement_label(fighter, scope="P4P"), "—")
        self.assertEqual(harness.ranking_movement_label(fighter, scope="Division"), "▲3")

    def test_rankings_do_not_expose_hidden_score_fields(self):
        source = inspect.getsource(ViewMixin.refresh_rankings)
        self.assertGreaterEqual(source.count("fighter_profile_stats_visible"), 2)
        self.assertGreaterEqual(source.count('"Hidden"'), 2)
        self.assertNotIn("self.refresh_promotion_rankings(", source)

    def test_matchmaking_available_rows_retain_selected_fighter(self):
        source = inspect.getsource(ViewMixin.refresh_available)
        for marker in ("prior_selection", "prior_identity", "available_tree_fighters", "restored_row_id", "selection_set"):
            self.assertIn(marker, source)

    def test_roster_refresh_restores_selected_fighter_by_identity(self):
        source = inspect.getsource(ViewMixin.refresh_roster)
        for marker in ("prior_selection", "prior_identity", "roster_tree_fighters", "restored_row_id", "selection_set"):
            self.assertIn(marker, source)

    def test_market_refresh_restores_selected_free_agent_by_identity(self):
        source = inspect.getsource(ViewMixin.refresh_market)
        for marker in ("prior_selection", "prior_identity", "market_tree_fighters", "restored_row_id", "selection_set"):
            self.assertIn(marker, source)

    def test_legacy_company_ledger_rows_do_not_collide_on_duplicate_names(self):
        first = SimpleNamespace(promotion_id="promo-a", name="Same FC", region="USA")
        second = SimpleNamespace(promotion_id="promo-b", name="Same FC", region="USA")
        self.assertNotEqual(ViewMixin._world_promotion_identity(first), ViewMixin._world_promotion_identity(second))
        legacy_a = SimpleNamespace(name="Legacy FC", region="UK")
        legacy_b = SimpleNamespace(name="Legacy FC", region="UK")
        self.assertEqual(ViewMixin._world_promotion_identity(legacy_a), ViewMixin._world_promotion_identity(legacy_b))
        source = inspect.getsource(ViewMixin.open_legacy_ledger)
        self.assertIn("used_company_row_ids", source)
        self.assertIn("_world_promotion_identity", source)

    def test_academy_rival_program_rows_use_promotion_identity(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        academy = source.split("    def open_academy_window", 1)[1].split("    def refresh_academy_tab", 1)[0]
        self.assertIn("used_rival_ids", academy)
        self.assertIn("base_rival_id = self._world_promotion_identity", academy)
        self.assertNotIn('iid=f"rival:{promo.name}"', academy)

    def test_matchmaking_draft_refresh_projects_card_metadata_without_reordering_saved_rows(self):
        source = inspect.getsource(ViewMixin.refresh_card)
        self.assertIn("display_fights = [dict(fight) for fight in self.booked]", source)
        self.assertIn("self.normalize_card_order(display_fights)", source)
        self.assertIn("source_fight", source)
        self.assertIn("self.default_event_name(fights=display_fights)", source)
        self.assertNotIn("self.normalize_card_order()", source)

    def test_scouting_assignment_rows_prefer_saved_search_identity(self):
        source = inspect.getsource(ViewMixin.refresh_scouting_center)
        helper = inspect.getsource(ViewMixin.scouting_search_row_id)
        for marker in ("prior_row_id", "scouting_search_row_id", "#duplicate", "selection_set"):
            self.assertIn(marker, source)
        self.assertIn("assignment_id", helper)
        self.assertIn("search:legacy:", helper)

    def test_scouting_target_board_promotes_selected_visible_context(self):
        source = inspect.getsource(UIMixin.build_scouting_tab)
        refresh = inspect.getsource(ViewMixin.show_selected_recruitment_target_summary)
        cards = inspect.getsource(ViewMixin.update_scouting_target_cards)
        target_refresh = inspect.getsource(ViewMixin.refresh_scouting_targets)
        for key, label in (("identity", "SELECTED TARGET"), ("intel", "INTEL STATUS"), ("advice", "SCOUT ADVICE"), ("market", "MARKET CONTEXT")):
            self.assertIn(f'("{key}"', source)
            self.assertIn(label, source)
            self.assertIn(f'"{key}"', cards)
        self.assertIn("update_scouting_target_cards", refresh)
        self.assertIn("No report", cards)
        self.assertIn("semantic_status_palette", cards)
        # Filtering/paging can delete the old Treeview selection without
        # emitting <<TreeviewSelect>>. The reader must clear every card in
        # that branch rather than leaving stale fighter evidence visible.
        self.assertIn("stale scouting facts cannot remain on screen", target_refresh)
        self.assertIn("self.update_scouting_target_cards()", target_refresh)

    def test_scouting_selection_readers_do_not_repair_saved_reports(self):
        """Selecting a prospect/target or opening comparison stays RNG/state neutral."""
        for reader in (
            ViewMixin.show_selected_regional_prospect,
            ViewMixin.show_selected_recruitment_target_summary,
            ViewMixin.open_compare_fighters_window,
        ):
            source = inspect.getsource(reader)
            self.assertIn("scouting_report_for", source)
            self.assertIn("migrate=False", source)

    def test_combat_sports_overview_promotes_selected_management_context(self):
        source = inspect.getsource(ViewMixin.build_combat_sports_tab)
        for key, label in (
            ("roster", "ROSTER"),
            ("next", "NEXT COMMITTED CARD"),
            ("contracts", "CONTRACT WATCH"),
            ("results", "RECENT RESULT"),
        ):
            self.assertIn(f'("{key}"', source)
            self.assertIn(label, source)
        self.assertIn("combat_sports_selected_sport", source)
        self.assertIn("scheduled_events", source)
        self.assertIn("contract_months", source)

    def test_media_rights_promotes_read_only_account_review(self):
        source = inspect.getsource(UIMixin.build_website_tab)
        refresh = inspect.getsource(MediaMixin.refresh_media_dashboard)
        self.assertIn("media_account_review", source)
        for marker in ("delivered", "shortfalls", "breach_strikes", "media_successor_contract", "historical/read-only"):
            self.assertIn(marker, refresh)

    def test_camp_plan_explains_tradeoffs_and_preserves_cancel_boundary(self):
        source = inspect.getsource(ViewMixin.open_fighter_camp_plan)
        self.assertIn('window.resizable(True, True)', source)
        self.assertIn('"EXPECTED TRADE-OFF"', source)
        self.assertIn('"MEDICAL LIMIT"', source)
        self.assertIn('window.destroy)', source)
        self.assertIn('effective_injury_tendency(fighter)', source)

    def test_scouting_search_is_debounced_and_disposed_on_navigation(self):
        source = inspect.getsource(UIMixin.build_scouting_tab)
        schedule = inspect.getsource(ViewMixin.schedule_scouting_target_refresh)
        cancel = inspect.getsource(ViewMixin.cancel_scouting_target_refresh)
        select = inspect.getsource(UIMixin.select_tab)
        self.assertIn('schedule_scouting_target_refresh()', source)
        self.assertIn('delay=200', schedule)
        self.assertIn('after(', schedule)
        self.assertIn('after_cancel', schedule)
        self.assertIn('_scouting_target_search_revision', schedule)
        self.assertIn('after_cancel', cancel)
        self.assertIn('cancel_scouting_target_refresh()', select)

    def test_fight_history_layout_preserves_visibility_order_and_width_preferences(self):
        source = inspect.getsource(ViewMixin.open_fighter_profile_window)
        for marker in (
            'ui_fighter_history_column_layout',
            'saved_history_layout.get("order", [])',
            'saved_history_layout.get("widths", {})',
            'history_column_widths',
            'history_tree.configure(displaycolumns=selected)',
            'persist_history_layout_from_tree',
            'identify_region(event.x, event.y) == "heading"',
            'Move Up',
            'Move Down',
            'Selected width',
        ):
            self.assertIn(marker, source)
        # Hidden columns retain their widths and can be restored later.
        self.assertIn('for column in history_column_ids}', source)

    def test_profile_history_rows_use_identity_bound_selection(self):
        source = inspect.getsource(ViewMixin.open_fighter_profile_window)
        for marker in ("fighter_profile_source_key", "history_base_ids", "prior_history_key", "_fighter_history_view_identity", "#duplicate", "selection_set"):
            self.assertIn(marker, source)
        self.assertIn("fighter-history-columns:{self.fighter_profile_source_key(fighter)}", source)
        membership_source = inspect.getsource(ViewMixin.open_fighter_membership_history_window)
        self.assertIn("fighter_profile_source_key", membership_source)
        legacy_profile_key = ViewMixin.fighter_profile_source_key(SimpleNamespace(
            name="Legacy Profile", gender="Male", weight="Lightweight", region="USA",
            record="8-2-0", age=28,
        ))
        self.assertTrue(legacy_profile_key.startswith("legacy-fighter:"))
        saved = ViewHarness._fighter_history_view_identity({"bout_key": "event-1:bout-2"}, index=4)
        self.assertEqual(saved, "history:event-1:bout-2")
        legacy = ViewHarness._fighter_history_view_identity({"date": "Apr W2 2030", "opponent": "Rival", "result": "W"}, index=4)
        self.assertTrue(legacy.startswith("legacy-history:"))

    def test_legacy_roster_detail_shows_live_injury_risk(self):
        source = inspect.getsource(ViewMixin.update_fighter_detail)
        self.assertIn("effective_injury_tendency(fighter)", source)
        self.assertIn("(base {fighter.injury_proneness})", source)

    def test_booking_draft_review_routes_by_booking_identity(self):
        source = inspect.getsource(ViewMixin.open_booking_draft_review_window)
        for marker in ("row_by_iid", "used_iids", "legacy-slot", "suffixes"):
            self.assertIn(marker, source)
        self.assertIn("row_by_iid.get(selected[0])", source)
        self.assertNotIn("rows[int(selected[0])]", source)

    def test_booking_workbench_options_route_by_fighter_identity(self):
        source = inspect.getsource(ViewMixin.open_booking_workbench_window)
        for marker in ("option_by_iid", "legacy-option", "used_iids", "selected_option"):
            self.assertIn(marker, source)
        self.assertIn("refresh_rows(selected[0])", source)
        self.assertIn("commit_booking_proposal_for_fighter", source)
        self.assertIn("no stable fighter identity", source)
        self.assertNotIn("iid=str(index)", source)
        self.assertNotIn("int(selected[0])", source)

    def test_locked_slot_options_route_by_fighter_identity(self):
        source = inspect.getsource(ViewMixin.open_locked_slot_workbench_window)
        for marker in ("option_by_iid", "legacy-option", "used_iids", "selected_option"):
            self.assertIn(marker, source)
        self.assertIn("refresh_rows(selected[0])", source)
        self.assertIn("commit_locked_slot_proposal_for_fighter", source)
        self.assertIn("no stable fighter identity", source)
        self.assertNotIn("iid=str(index)", source)
        self.assertNotIn("int(selected[0])", source)

    def test_workbench_legacy_keys_are_deterministic_and_position_independent(self):
        option = {
            "name": "Legacy Rival", "gender": "Male", "weight": "Lightweight",
            "record": "8-2-0", "overall": 61, "company_rank": "#4",
            "world_rank": "#18", "generation_status": "Blocked",
            "hard_blocks": ["medical return not recorded"], "cautions": [],
        }
        self.assertEqual(
            ViewMixin.workbench_option_view_id(option),
            ViewMixin.workbench_option_view_id(dict(option)),
        )
        self.assertTrue(ViewMixin.workbench_option_view_id(option).startswith("legacy-option:"))
        draft = {
            "participants": ["Legacy Rival", "TBA"], "tier": "Prelims",
            "title": False, "status": "Needs opponent", "reason": "Open corner",
            "open_slots": [1],
        }
        self.assertEqual(
            ViewMixin.workbench_draft_view_id(draft),
            ViewMixin.workbench_draft_view_id(dict(draft)),
        )
        self.assertTrue(ViewMixin.workbench_draft_view_id(draft).startswith("legacy-slot:"))

    def test_company_proposal_ledger_keeps_proposal_identity_on_refresh(self):
        source = inspect.getsource(ViewMixin.open_company_proposal_ledger_window)
        for marker in ("prior_selection", "used_ids", "legacy-proposal", "rows_by_id", "selection_set"):
            self.assertIn(marker, source)
        self.assertIn("json.dumps(row, sort_keys=True", source)
        self.assertNotIn("legacy-proposal:{index + 1}", source)

    def test_company_history_reader_uses_fact_identity_not_visible_index(self):
        source = inspect.getsource(ViewMixin.open_fighter_membership_history_window)
        for marker in ("history_row_id", "rows_by_id", "legacy-history", "used_ids", "prior_selection", "selection_set", "membership_id", "title_event_id"):
            self.assertIn(marker, source)
        for marker in ("page_size = 250", "page_index", "previous_button", "next_button", "preserve_selection=False", "limit=100000"):
            self.assertIn(marker, source)
        self.assertIn("rows_by_id.get(selected[0])", source)
        self.assertNotIn("all_rows[int(selected[0])]", source)

    def test_career_journeys_routes_actions_by_fighter_identity(self):
        source = inspect.getsource(ViewMixin.open_career_goals_window)
        for marker in ("fighter_by_iid", "used_fighter_iids", "legacy-fighter", "selected_id"):
            self.assertIn(marker, source)
        self.assertIn("fighter_by_iid.get(selected[0])", source)
        self.assertNotIn("rows[int(selected[0])", source)

    def test_finance_history_uses_week_identity_for_selection(self):
        refresh = inspect.getsource(ViewMixin.refresh_finance)
        detail = inspect.getsource(ViewMixin.show_selected_finance_week)
        for marker in ("_finance_history_rows", "finance-week:", "legacy-finance-week:", "used_finance_ids", "restored_finance_id"):
            self.assertIn(marker, refresh)
        self.assertIn("_finance_history_rows", detail)
        self.assertNotIn("history[int(selected[0])", detail)
        runway = inspect.getsource(ViewMixin.refresh_finance_runway)
        self.assertIn("legacy-runway:", runway)
        self.assertIn("json.dumps(row, sort_keys=True", runway)

    def test_owner_goal_reader_keeps_malformed_rows_explicit(self):
        refresh = inspect.getsource(ViewMixin.refresh_owner_goals)
        measure = inspect.getsource(ViewMixin.owner_goal_measure)
        for marker in ("goals = getattr(self, \"owner_goals\", [])", "if not isinstance(goals, (list, tuple))", "Unavailable owner objective", "_owner_goal_safe_int"):
            self.assertIn(marker, refresh)
        self.assertIn("goal = goal if isinstance(goal, dict) else {}", measure)

    def test_owner_goal_projection_bounds_nonfinite_metrics(self):
        class GoalProbe(ViewMixin):
            pass
        probe = GoalProbe()
        probe.cash = float("inf")
        probe.company_pop = float("nan")
        probe.month = float("nan")
        probe.result_history = []
        self.assertEqual(probe.owner_goal_measure({"metric": "cash"}), 0)
        status, progress, _reason = probe.owner_goal_evaluate(
            {"metric": "cash", "target": float("inf"), "deadline": float("nan")},
            current=float("inf"), month=float("nan"), record=False, seal=False,
        )
        self.assertEqual(status, "Complete")
        self.assertEqual(progress, "0 / 0")

    def test_testing_cases_reader_bounds_nonfinite_quote_and_sample_values(self):
        class CaseProbe(ViewMixin):
            pass
        probe = CaseProbe()
        source = {
            "case_id": "CASE-bad-numeric", "status": "Closed negative",
            "fighter": "Legacy Fighter", "quote_snapshot": {"amount": float("inf")},
            "sample_count": float("nan"), "provider_id": "national_lab", "policy": "Standard",
        }
        probe.drug_testing_state = {"cases": [source]}
        before = deepcopy(probe.drug_testing_state)
        projected = probe.drug_testing_case_read_model()
        summary = probe.drug_testing_summary()
        self.assertEqual(projected[0]["recorded_total"], 0)
        self.assertEqual(summary["samples_collected"], 0)
        self.assertEqual(summary["total_spend"], 0)
        self.assertEqual(probe.drug_testing_state, before)

    def test_matchmaking_card_routes_by_booking_identity(self):
        refresh = inspect.getsource(ViewMixin.refresh_card)
        for marker in ("card_tree_fights", "used_card_row_ids", "legacy-card:", "insert_card_row", "restored_card_row_id"):
            self.assertIn(marker, refresh)
        for method in (
            ViewMixin.review_selected_tournament_field,
            ViewMixin.remove_matchup,
            ViewMixin.compare_selected_card_matchup,
            ViewMixin.fill_selected_tba_matchup,
            ViewMixin.toggle_card_title,
            ViewMixin.move_fight_up,
            ViewMixin.move_fight_down,
        ):
            source = inspect.getsource(method)
            self.assertIn("card_tree_fights", source)
            self.assertNotIn("booked[int(selected[0])", source)
            self.assertNotIn("booked.pop(int(selected[0]))", source)
            self.assertNotIn("booked.index(", source)
        self.assertIn("self.resolve_fighter", inspect.getsource(ViewMixin.review_selected_tournament_field))
        self.assertIn("identity is unavailable or ambiguous", inspect.getsource(ViewMixin.fill_selected_tba_matchup))
        self.assertIn("identity is unavailable or ambiguous", inspect.getsource(ViewMixin.toggle_card_title))

    def test_duplicate_equal_draft_rows_resolve_by_source_identity(self):
        probe = type("CardProbe", (), {})()
        first = {"fighters": ["A", "B"], "title": False}
        second = {"fighters": ["A", "B"], "title": False}
        probe.booked = [first, second]
        probe._booked_fight_source_index = ViewMixin._booked_fight_source_index.__get__(probe)
        self.assertEqual(probe._booked_fight_source_index(first), 0)
        self.assertEqual(probe._booked_fight_source_index(second), 1)
        self.assertIsNone(probe._booked_fight_source_index(dict(first)))

        first_with_id = {"booking_id": "booking:one", "fighters": ["A", "B"]}
        second_with_id = {"booking_id": "booking:two", "fighters": ["A", "B"]}
        probe.booked = [first_with_id, second_with_id]
        detached = {"booking_id": "booking:two", "fighters": ["A", "B"]}
        self.assertEqual(probe._booked_fight_source_index(detached), 1)

    def test_inbox_and_owner_goal_readers_route_by_source_identity(self):
        inbox_refresh = inspect.getsource(ViewMixin.refresh_inbox)
        inbox_identity = inspect.getsource(ViewMixin._inbox_view_identity)
        inbox_selected = inspect.getsource(ViewMixin.selected_inbox_item)
        goals_refresh = inspect.getsource(ViewMixin.refresh_owner_goals)
        goal_identity = inspect.getsource(ViewMixin._owner_goal_view_identity)
        goal_open = inspect.getsource(ViewMixin.open_selected_owner_goal)
        for marker in ("_inbox_rows", "_inbox_view_identity", "retained_inbox_id", "inbox_reader_rows", "source_messages"):
            self.assertIn(marker, inbox_refresh)
        self.assertNotIn("normalize_inbox_messages()", inbox_refresh)
        self.assertIn("legacy-inbox:", inbox_identity)
        self.assertIn("_inbox_rows", inbox_selected)
        self.assertNotIn("inbox[int(selected[0])", inbox_selected)
        self.assertIn("OverflowError", inspect.getsource(WorldMixin.inbox_reader_rows))
        self.assertIn("OverflowError", inspect.getsource(WorldMixin.inbox_item_needs_action))
        self.assertIn("len(matches) == 1", inspect.getsource(WorldMixin.inbox_item_needs_action))
        related = inspect.getsource(ViewMixin.inbox_related_fighter)
        self.assertIn("len(matches) == 1", related)
        self.assertIn("fighter_id", related)
        visible = inspect.getsource(ViewMixin.visible_inbox_items)
        self.assertIn("_inbox_rows", visible)
        self.assertNotIn("inbox[int(iid)", visible)
        for marker in ("_owner_goal_rows", "_owner_goal_view_identity", "retained_goal_id"):
            self.assertIn(marker, goals_refresh)
        self.assertIn("legacy-owner-goal:", goal_identity)
        self.assertIn("_owner_goal_rows", goal_open)
        self.assertNotIn("owner_goals[int(self.goals_tree.selection()[0])", goal_open)

    def test_inbox_name_only_fallback_fails_closed_for_duplicate_careers(self):
        first = SimpleNamespace(name="Same Name", fighter_id="fighter-a")
        second = SimpleNamespace(name="Same Name", fighter_id="fighter-b")
        harness = object.__new__(ViewMixin)
        harness.all_scoutable_fighters = lambda: [first, second]
        harness.scouting_report_key = lambda fighter: fighter.fighter_id
        harness.all_database_fighters_with_companies = lambda: [("A", first), ("B", second)]
        self.assertIsNone(harness.inbox_related_fighter({"subject": "Same Name", "body": ""}))
        self.assertIs(harness.inbox_related_fighter({"fighter_id": "fighter-b", "subject": "Same Name", "body": ""}), second)
        first.serious_injury_pending = True
        second.serious_injury_pending = True
        world_harness = object.__new__(WorldMixin)
        world_harness.roster = [first, second]
        world_harness.free_agents = []
        world_harness.retired_fighters = []
        self.assertFalse(world_harness.inbox_item_needs_action({"action": "serious_injury", "fighter": "Same Name"}))
        self.assertTrue(world_harness.inbox_item_needs_action({"action": "serious_injury", "fighter_id": "fighter-b", "fighter": "Same Name"}))

    def test_inbox_reader_derives_legacy_defaults_without_mutating_messages(self):
        harness = type("InboxHarness", (), {"month": 8, "week": 3})()
        harness.inbox = [{"subject": "Legacy", "body": "Retained", "created_month": float("inf"), "created_week": float("nan")}, "malformed"]
        before = deepcopy(harness.inbox)
        rows = WorldMixin.inbox_reader_rows(harness)
        self.assertEqual(rows[0]["created_month"], 8)
        self.assertEqual(rows[0]["created_week"], 1)
        self.assertEqual(rows[0]["_read_status"], "Recorded")
        self.assertEqual(rows[1]["_read_status"], "Unavailable")
        self.assertEqual(harness.inbox, before)

    def test_retired_fighter_rows_route_comeback_by_identity(self):
        refresh = inspect.getsource(ViewMixin.refresh_results)
        identity = inspect.getsource(ViewMixin._retired_fighter_view_identity)
        handler = inspect.getsource(ViewMixin.unretire_selected_fighter)
        for marker in ("_retired_fighter_rows", "used_retired_ids", "retained_retired_id"):
            self.assertIn(marker, refresh)
        self.assertIn("retired-fighter:", identity)
        self.assertIn("_retired_fighter_rows", handler)
        self.assertNotIn("retired_fighters[index]", handler)

    def test_staff_actions_fail_closed_without_identity_map(self):
        hire = inspect.getsource(ViewMixin.hire_staff)
        select = inspect.getsource(ViewMixin.selected_staff_for_action)
        self.assertNotIn("staff_candidates[int(selected[0])", hire)
        self.assertNotIn("staff[int(selected[0])", select)

    def test_media_story_rows_use_story_identity_for_reader_navigation(self):
        refresh = inspect.getsource(ViewMixin.refresh_website)
        selected = inspect.getsource(ViewMixin.selected_media_story_entry)
        open_story = inspect.getsource(ViewMixin.open_selected_news_story)
        move = inspect.getsource(ViewMixin.open_story_reader)
        for marker in ("_website_news_rows", "_media_story_view_identity", "used_story_ids", "retained_story_id"):
            self.assertIn(marker, refresh)
        self.assertIn("legacy-story:", inspect.getsource(ViewMixin._media_story_view_identity))
        self.assertIn("_website_news_rows", selected)
        self.assertNotIn("entries[index]", selected)
        self.assertNotIn("split(\":\", 1)[1]", open_story)
        self.assertIn("_website_news_rows", move)
        self.assertNotIn("entries.index(entry)", move)
        self.assertIn("candidate is entry", move)
        self.assertIn("identity_field", move)
        self.assertNotIn("any(str(candidate.get(field", move)
        context = inspect.getsource(ViewMixin.open_story_entry_context)
        self.assertIn("fighter_ids", context)
        self.assertIn("select_unique_company_by_name", context)

    def test_media_story_reader_keeps_duplicate_legacy_rows_source_bound(self):
        first = {"headline": "Same", "detail": "Same", "month": 1, "week": 1}
        second = {"headline": "Same", "detail": "Same", "month": 1, "week": 1}
        entries = [first, second]
        selected_index = next((index for index, candidate in enumerate(entries) if candidate is second), None)
        self.assertEqual(selected_index, 1)
        detached = dict(second)
        detached_index = next((index for index, candidate in enumerate(entries) if candidate is detached), None)
        self.assertIsNone(detached_index)

    def test_assistant_and_staff_readers_do_not_fallback_to_visible_indexes(self):
        detail = inspect.getsource(ViewMixin.refresh_assistant_decision_detail)
        notice = inspect.getsource(ViewMixin.open_selected_assistant_notice)
        staff = inspect.getsource(ViewMixin.open_selected_staff_profile)
        self.assertNotIn("_assistant_messages[int(selected[0])", detail)
        self.assertNotIn("_assistant_messages[int(selected[0])", notice)
        self.assertNotIn("pool[int(selected[0])", staff)

    def test_assistant_readers_are_defensive_and_non_mutating(self):
        records = [{"event": "Recorded card", "fight_count": 5}, "legacy scalar"]
        original = list(records)
        projected = ViewMixin.assistant_result_reader_rows(records, limit=12)
        self.assertEqual(projected[0]["event"], "Recorded card")
        self.assertEqual(projected[0].get("_read_status"), None)
        self.assertEqual(projected[1]["_read_status"], "Unavailable")
        self.assertEqual(records, original)

        journal = [{"month": 2, "week": 1, "category": "Finance", "delta": -50}, 17]
        journal_before = list(journal)
        changes = ViewMixin.assistant_change_reader_rows(journal, month=2, week=1, limit=16)
        self.assertEqual(changes[0]["_read_status"], "Unavailable")
        self.assertEqual(changes[1]["category"], "Finance")
        self.assertEqual(journal, journal_before)

        unavailable = ViewMixin.assistant_result_reader_rows({"bad": "container"})
        self.assertEqual(unavailable[0]["_read_status"], "Unavailable")
        invalid_journal = ViewMixin.assistant_change_reader_rows({"bad": "container"})
        self.assertEqual(invalid_journal[0]["_read_status"], "Unavailable")
        refresh = inspect.getsource(ViewMixin.refresh_assistant)
        self.assertIn("assistant_result_reader_rows", refresh)
        self.assertIn("assistant_change_reader_rows", refresh)
        self.assertIn("safe_scout_int", refresh)
        self.assertIn("isinstance(report, dict)", refresh)

    def test_academy_history_and_alumni_rows_use_record_identity(self):
        source = inspect.getsource(ViewMixin.render_academy_screen)
        for marker in ("academy_row_maps", "academy_table_row_id", "used_card_ids", "used_alumni_ids", "legacy-{prefix}:"):
            self.assertIn(marker, source)
        self.assertNotIn("card:{index}", source)
        self.assertNotIn("alumnus:{index}", source)
        legacy_source = inspect.getsource(ViewMixin._open_academy_window_legacy)
        self.assertIn("used_alumni_ids", legacy_source)
        self.assertIn("academy_archive_row_view", legacy_source)
        self.assertIn("selected_legacy_item", legacy_source)
        self.assertIn("remember_legacy_selection", legacy_source)
        self.assertNotIn('iid=f"alumni:{index}"', legacy_source)
        self.assertNotIn("academy['talent_pool'][talent.curselection()[0]]", legacy_source)
        self.assertNotIn("academy['prospects'][prospects.curselection()[0]]", legacy_source)
        selected_index = source.split("def selected_index", 1)[1].split("def set_enabled", 1)[0]
        self.assertNotIn("int(selected[0])", selected_index)
        self.assertIn("academy_history_row_id", source)
        self.assertIn("used_history_ids", source)
        self.assertNotIn('iid=f"history:{index}"', source)
        record = {"event_id": "show-4", "bout_id": "bout-2", "opponent": "Rival", "result": "W"}
        self.assertEqual(ViewMixin.academy_history_row_id(record), ViewMixin.academy_history_row_id(dict(record)))
        legacy = ViewMixin.academy_history_row_id("Month 1 Week 1: Prospect def. Rival by Decision")
        self.assertTrue(legacy.startswith("academy-history:legacy:"))

    def test_academy_archive_rows_keep_malformed_history_visible_without_mutation(self):
        card = {"event_id": "show-17", "event_name": "Academy Night"}
        alumni = {"fighter_id": "fighter-9", "name": "Graduate"}
        self.assertIs(ViewMixin.academy_archive_row_view("card", card), card)
        self.assertIs(ViewMixin.academy_archive_row_view("alumnus", alumni), alumni)

        raw_card = ["legacy card payload"]
        raw_alumni = ["legacy alumnus payload"]
        card_view = ViewMixin.academy_archive_row_view("card", raw_card)
        alumni_view = ViewMixin.academy_archive_row_view("alumnus", raw_alumni)
        self.assertEqual(card_view["_read_status"], "Unavailable retained record")
        self.assertEqual(card_view["event_name"], "Unavailable retained record")
        self.assertEqual(card_view["fight_logs"], [])
        self.assertEqual(alumni_view["name"], "Unavailable retained record")
        self.assertEqual(alumni_view["status"] if "status" in alumni_view else alumni_view["active"], False)
        self.assertEqual(raw_card, ["legacy card payload"])
        self.assertEqual(raw_alumni, ["legacy alumnus payload"])

        source = inspect.getsource(ViewMixin.render_academy_screen)
        for marker in ("academy_archive_row_view", 'tags=("unavailable",)', "selected_card_id", "selected_alumnus_id"):
            self.assertIn(marker, source)

    def test_combat_sport_card_and_event_rows_use_identity_maps(self):
        source = inspect.getsource(ViewMixin.open_player_combat_division_window)
        for marker in ("booked_bout_rows", "combat_sport_row_id", "booked_bout_source_index", "used_bout_ids", "used_scheduled_ids", "used_event_ids"):
            self.assertIn(marker, source)
        self.assertNotIn('iid=f"bout:{index - 1}"', source)
        self.assertNotIn('iid=f"event:{index}"', source)
        self.assertNotIn('iid=f"scheduled:{index}"', source)
        self.assertNotIn('int(selected[0].split(":", 1)[1])', source)
        self.assertNotIn('booked_bouts"].index(bout)', source)
        self.assertIn('if candidate is target:', source)
        self.assertIn('if len(matches) == 1:', source)

    def test_combat_sport_history_profile_open_uses_saved_athlete_identity(self):
        source = inspect.getsource(ViewMixin.open_combat_sport_history_window)
        for marker in ("source_roster", "roster_by_id", "title_ids", "ranking_row_fighters"):
            self.assertIn(marker, source)
        # A ranking name is only a compatibility fallback when it is unique;
        # duplicate careers must not open whichever row happens to come first.
        self.assertIn("len(matches) == 1", source)
        self.assertIn("ranking_row_fighters.get(str(key))", source)
        self.assertNotIn("next((candidate for candidate in source_roster if candidate.name == name), None)", source)

    def test_combat_sport_history_reader_defensively_projects_malformed_rows(self):
        source = inspect.getsource(ViewMixin.open_combat_sport_history_window)
        for marker in ("raw_title_history", "raw_finance_history", "raw_events", "safe_history_date", "Unavailable retained"):
            self.assertIn(marker, source)
        self.assertIn("isinstance(entry, dict)", source)
        self.assertIn("isinstance(raw_rankings, dict)", source)

    def test_upcoming_scheduled_card_actions_use_saved_event_identity(self):
        refresh = inspect.getsource(ViewMixin.refresh_upcoming)
        for marker in ("scheduled_event_ui_identity", "upcoming_event_rows", "used_event_rows", "prior_row_id"):
            self.assertIn(marker, refresh)
        self.assertIn("scheduled_event_title_decision_status", refresh)
        self.assertIn("display_event = dict(event)", refresh)
        self.assertIn("saved_fights = event.get(\"fights\", [])", refresh)
        self.assertNotIn("self.repair_scheduled_event_names()", refresh)
        economics = inspect.getsource(EventMixin.selected_event_economics)
        forecast = inspect.getsource(ViewMixin.refresh_event_economics_forecast)
        broadcaster = inspect.getsource(ViewMixin.refresh_event_broadcaster_status)
        self.assertIn("repair=False", forecast)
        self.assertIn("if repair:", economics)
        self.assertIn("finance = getattr(self, \"finance\", {})", economics)
        self.assertIn("isinstance(finance, dict)", broadcaster)
        self.assertIn("if not isinstance(rights, dict)", broadcaster)
        self.assertIn("safe_int", broadcaster)
        self.assertIn("math.isfinite", broadcaster)
        self.assertIn("isinstance(item, dict)", broadcaster)
        for method in (
            EventMixin.selected_due_event,
            EventMixin.selected_scheduled_event_for_edit,
            EventMixin.cancel_selected_scheduled_event,
        ):
            source = inspect.getsource(method)
            self.assertIn("upcoming_event_rows", source)
            self.assertNotIn("int(selected[0])", source)

    def test_upcoming_reader_surfaces_saved_title_decision_without_resolution(self):
        event = {
            "fights": [
                {"fighters": ["Alpha", "Beta"], "title_miss_decision_state": {"status": "needs_review"}},
                {"fighters": ["Gamma", "Delta"], "title_miss_decision_state": {"status": "awaiting_player"}},
                {"fighters": ["Ignored", "Done"], "title_miss_decision_state": {"status": "resolved"}},
            ],
        }
        before = deepcopy(event)
        summary = ViewMixin.scheduled_event_title_decision_status(ViewMixin(), event)
        self.assertEqual(summary["status"], "Decision required")
        self.assertEqual(summary["pending_count"], 1)
        self.assertEqual(summary["review_count"], 1)
        self.assertEqual(summary["pending"][0]["fight_label"], "Gamma vs Delta")
        self.assertEqual(event, before)

    def test_upcoming_reader_ignores_malformed_or_terminal_decisions(self):
        event = {
            "fights": [
                None,
                {"fighters": "bad", "title_miss_decision_state": {"status": "awaiting_player"}},
                {"fighters": ["Done", "Done"], "title_miss_decision_state": {"status": "resolved"}},
            ],
        }
        summary = ViewMixin.scheduled_event_title_decision_status(ViewMixin(), event)
        self.assertEqual(summary["status"], "Decision required")
        self.assertEqual(summary["pending_count"], 1)
        self.assertEqual(summary["pending"][0]["fight_label"], "Bout 2")

    def test_upcoming_reader_surfaces_review_only_sanction_envelope(self):
        # Some interrupted/legacy rows retain the sanction envelope but not a
        # separate decision-state object. The explicit review flag is still a
        # blocked card and must remain discoverable after reload.
        event = {
            "fights": [{
                "fighters": ["Alpha", "Beta"],
                "title_sanction_snapshot": {
                    "review_required": True,
                    "decision": "awaiting_player",
                    "missed_corners": [],
                },
            }],
        }
        before = deepcopy(event)
        summary = ViewMixin.scheduled_event_title_decision_status(ViewMixin(), event)
        self.assertEqual(summary["status"], "Review required")
        self.assertEqual(summary["review_count"], 1)
        self.assertEqual(summary["review"][0]["fight_label"], "Alpha vs Beta")
        self.assertEqual(event, before)

    def test_scheduled_card_editor_bouts_use_identity_bound_rows(self):
        source = inspect.getsource(EventMixin.open_scheduled_card_editor)
        for marker in ("fight_editor_ui_identity", "card_tree_fights", "used_fight_ids", "prior_fight"):
            self.assertIn(marker, source)
        self.assertNotIn('iid=str(index)', source)
        self.assertNotIn("return int(selected[0])", source)
        self.assertIn("card_tree_fights.get(selected[0])", source)

    def test_superfight_card_rows_use_identity_bound_actions(self):
        source = inspect.getsource(ViewMixin.open_superfight_night_window)
        for marker in ("superfight_card_ui_identity", "card_tree_bouts", "used_bout_ids", "prior_bout"):
            self.assertIn(marker, source)
        self.assertNotIn('iid=str(index)', source)
        self.assertNotIn("del card[int(sel[0])]", source)
        self.assertNotIn("int(sel[0])", source)

    def test_fighter_comparison_measures_use_stable_identity(self):
        source = inspect.getsource(ViewMixin.open_compare_fighters_window)
        for marker in ("measure_rows_by_id", "measure_row_id", '"measure:"', "used_measure_ids"):
            self.assertIn(marker, source)
        self.assertIn("measure_rows_by_id.get(selected[0])", source)
        self.assertNotIn("rows[int(selected[0])]", source)
        self.assertNotIn('iid=str(index)', source)

    def test_semantic_status_palette_is_theme_aware_and_readable(self):
        source = inspect.getsource(UIMixin.semantic_status_palette)
        self.assertIn('light_surface', source)
        self.assertIn('positive', source)
        self.assertIn('negative', source)
        for background in ('#10151a', '#171a1f', '#eee9df', '#f2eee6'):
            palette = UIMixin.semantic_status_palette({'tree': background})
            for foreground in palette.values():
                self.assertGreaterEqual(UIMixin.wcag_contrast_ratio(foreground, background), 4.5)
        lazy = inspect.getsource(UIMixin.ensure_screen_built)
        self.assertIn('self.retheme_plain_widgets(self.root)', lazy)
        retheme = inspect.getsource(UIMixin.retheme_plain_widgets)
        for status in ("unread", "ready", "owned", "available", "rising", "sliding", "partial", "preserved"):
            self.assertIn(f'"{status}"', retheme)
        self.assertIn("tag_background", retheme)
        self.assertIn("_semantic_status_name", retheme)
        self.assertIn("scouting_target_legend_labels", inspect.getsource(UIMixin.build_scouting_tab))

    def test_world_hub_promotes_company_and_gym_context_cards(self):
        source = inspect.getsource(UIMixin.build_world_tab)
        refresh = inspect.getsource(ViewMixin.refresh_world)
        company = inspect.getsource(ViewMixin.show_selected_world_promotion)
        gym = inspect.getsource(ViewMixin.show_selected_world_gym)
        for key, label in (("company", "SELECTED COMPANY"), ("promotion", "PROMOTION SNAPSHOT"), ("gym", "SELECTED GYM"), ("capacity", "GYM CAPACITY")):
            self.assertIn(f'("{key}"', source)
            self.assertIn(label, source)
        self.assertIn("_world_promotion_rows", refresh)
        self.assertIn("selection_set", refresh)
        self.assertIn("world_context_vars", company)
        self.assertIn("world_context_vars", gym)

    def test_owned_calendar_exposes_read_only_event_detail(self):
        source = inspect.getsource(UIMixin.build_assistant_tab)
        refresh = inspect.getsource(ViewMixin.refresh_assistant)
        detail = inspect.getsource(ViewMixin.open_selected_owned_calendar_event)
        for marker in ("Owned Calendar", "View Event Detail", "assistant_calendar_detail", "owner_filter", "source_filter", "status_filter"):
            self.assertIn(marker, source)
        self.assertIn("_assistant_calendar_rows", refresh)
        self.assertIn("owned_schedule_index", refresh)
        self.assertIn("prior_calendar_identity", refresh)
        self.assertIn("_assistant_calendar_row_id", refresh)
        self.assertIn("Showing {len(calendar_rows)} of {len(all_calendar_rows)}", refresh)
        self.assertIn("reset_assistant_calendar_filters", source)
        self.assertIn("_selected_owned_calendar_row", detail)
        self.assertIn("reservation_count", detail)
        self.assertIn("participants", detail)
        self.assertIn("Read-only source record", detail)
        self.assertIn("does not resolve fighters", detail)

    def test_owned_calendar_row_ids_are_source_bound_and_deterministic(self):
        first = {"event_id": "event-7", "owner_ref": "promo-parent", "source": "MMA child"}
        same = dict(first)
        other_owner = dict(first, owner_ref="promo-other")
        first_id = ViewMixin._assistant_calendar_row_id(first)
        self.assertEqual(first_id, ViewMixin._assistant_calendar_row_id(same))
        self.assertNotEqual(first_id, ViewMixin._assistant_calendar_row_id(other_owner))
        self.assertEqual(ViewMixin._assistant_calendar_identity(first), "event-7|promo-parent|MMA child")
    def test_every_titleholder_departure_records_the_vacancy_first(self):
        buyout = inspect.getsource(WorldMixin.distressed_promotion_buyout)
        self.assertLess(buyout.index("vacate_fighter_belts"), buyout.index("promo.roster.remove(fighter)"))
        self.assertIn("retention_key", buyout)
        self.assertIn("fighter_id", buyout)
        self.assertNotIn("fighter.name in retained", buyout)
        contracts = inspect.getsource(WorldMixin.update_ai_contracts)
        self.assertEqual(contracts.count("vacate_fighter_belts"), 2)
        for departure in contracts.split("promo.roster.remove(fighter)")[:-1]:
            self.assertIn("vacate_fighter_belts", departure[-900:])

        removal = inspect.getsource(ViewMixin.remove_fighter_from_active_database)
        self.assertIn("self.vacate_fighter_belts", removal)
        self.assertIn("promotion.belt_history = self.vacate_fighter_belts", removal)
        editor_save = inspect.getsource(ViewMixin.save_database_editor_fighter)
        self.assertLess(editor_save.index("remove_fighter_from_active_database"),
                        editor_save.index('for key in ("name", "gender", "weight"'))

    def test_regional_prospect_ratings_use_the_row_promotion(self):
        source = inspect.getsource(ViewMixin.refresh_regional_prospects)
        self.assertNotIn('scouting_display_value(fighter, "overall", company)', source)
        self.assertIn('scouting_display_value(fighter, "overall", promo.name)', source)
        self.assertIn('scouting_display_value(fighter, "potential", promo.name)', source)

    def test_regional_prospect_rows_keep_promotion_fighter_identity_after_resort(self):
        promo = SimpleNamespace(promotion_id="regional-1", name="Regional One")
        fighter = SimpleNamespace(fighter_id="fighter-7", name="Prospect")
        first = ViewMixin.regional_prospect_row_identity(promo, fighter, fallback_index=0)
        self.assertEqual(first, ViewMixin.regional_prospect_row_identity(promo, fighter, fallback_index=99))
        self.assertNotEqual(
            first,
            ViewMixin.regional_prospect_row_identity(SimpleNamespace(promotion_id="regional-2", name="Regional Two"), fighter),
        )
        source = inspect.getsource(ViewMixin.refresh_regional_prospects)
        for marker in ("regional_prospect_row_identity", "prior_identity", "used_row_ids", "retained_row_id", "selection_set"):
            self.assertIn(marker, source)
        self.assertNotIn('row_id = f"regional:{fighter.fighter_id}:{index}"', source)

    def test_regional_prospect_refresh_uses_nonrepairing_throughput_projection(self):
        source = inspect.getsource(ViewMixin.refresh_regional_prospects)
        self.assertIn("regional_market_throughput_readonly", source)
        app = WorldReviewHarness()
        app.rules = {"regional_eligible_backlog_month": 4, "regional_eligible_backlog_count": float("inf")}
        app.month = 4
        app.promotions = "malformed promotions"
        app.free_agents = "malformed free agents"
        app.ai_roster_target = lambda _promo: 0
        before = deepcopy(app.rules)
        self.assertEqual(app.regional_market_throughput_readonly()["graduation_slots"], 6)
        self.assertEqual(app.rules, before)
        backlog = inspect.getsource(WorldMixin.regional_eligible_backlog_count)
        throughput = inspect.getsource(WorldMixin.regional_market_throughput)
        for marker in ("OverflowError", "isinstance(promotions, (list, tuple))", "isinstance(roster, (list, tuple))"):
            self.assertIn(marker, backlog)
        self.assertIn("isinstance(free_agent_rows, (list, tuple))", throughput)

    def test_duplicate_fighter_names_use_compact_display_marker(self):
        harness = ViewHarness()
        duplicate = SimpleNamespace(name="Miesha Tate BAMMA", champion=False, interim_champion=False)
        champion = SimpleNamespace(name="Miesha Tate BAMMA", champion=True, interim_champion=False)
        harness.all_database_fighters = lambda include_retired=True: [duplicate]

        self.assertEqual("Miesha Tate (D)", harness.fighter_display_name(duplicate))
        self.assertEqual("Miesha Tate (D) (C)", harness.fighter_display_name(champion))
        self.assertEqual("Miesha Tate", harness.clean_display_fighter_name("Miesha Tate BAMMA (D)"))
        self.assertEqual("Miesha Tate (D) won the belt", harness.display_fighter_text("Miesha Tate BAMMA won the belt"))

    def test_fight_night_name_rendering_does_not_duplicate_champion_tag(self):
        harness = ViewHarness()
        champion = SimpleNamespace(name="Magomed Zaynukov", champion=True, interim_champion=False)
        harness.result_fighter = lambda *_args: champion
        rendered = harness.display_fighter_names_in_text(
            "Magomed Zaynukov (C) (C) probes with the lead hand.",
            {"a": "Magomed Zaynukov", "b": "Christian Lee"},
        )

        self.assertEqual("Magomed Zaynukov (C) probes with the lead hand.", rendered)
        self.assertEqual("Magomed Zaynukov (C)", harness.fighter_display_name(SimpleNamespace(name="Magomed Zaynukov (C)", champion=True, interim_champion=False)))

    def test_ai_roster_reviews_protect_scheduled_fighters(self):
        fighters = [
            SimpleNamespace(
                name=f"Review Fighter {index}",
                fighter_id=f"review-{index}",
                retired=False,
                retirement_pending=False,
                champion=False,
                interim_champion=False,
                gender="Male",
                weight="Lightweight",
                age=28,
                potential=70,
                overall=70,
                record_w=0,
                record_l=0,
                record_d=0,
                momentum=0,
                purse=1_000,
                contract_months=12,
                prime_end=34,
                popularity=10,
            )
            for index in range(12)
        ]
        promo = SimpleNamespace(
            name="Review Test Promotion",
            roster=fighters,
            cash=10_000_000,
            size=60,
            reputation_score=60,
            stability=60,
            is_regional_feeder=False,
            belts={},
            interim_belts={},
            show_history=[],
        )
        harness = WorldReviewHarness()
        harness.promotions = [promo]
        harness.free_agents = [SimpleNamespace(
            name="Scheduled Upgrade Target",
            fighter_id="incoming-1",
            retired=False,
            retirement_pending=False,
            injured=0,
            fatigue=0,
            ai_offer_company="",
            age=29,
            potential=72,
            overall=71,
            gender="Male",
            weight="Lightweight",
        )]
        harness.scheduled_references = {fighters[0].fighter_id, fighters[0].name}
        harness.month = 3
        harness.news = []
        harness.update_ai_promotion_strategy = lambda _promo: {"financial_pressure": 0}
        harness.promotion_strategy = lambda _promo: {"last_upgrade_review_month": -99}
        harness.ai_roster_target = lambda _promo: 40
        harness.ai_financial_roster_target = lambda _promo: 40
        harness.ai_contract_reserve = lambda _promo: 0
        harness.ai_division_target = lambda _promo, _gender=None: 20
        harness.promotion_belt_holders = lambda _promo: set()
        harness.child_promotion_loaned = lambda _promo, _fighter: False

        harness.review_ai_roster_cuts()
        harness.review_ai_upgrade_replacements()

        self.assertIn(fighters[0], promo.roster)

    def test_refresh_staff_is_safe_before_staff_tab_is_built(self):
        harness = ViewHarness()
        harness.staff = []
        harness.refresh_staff()  # no lazily-created Tk widgets exist

    def test_refresh_staff_projects_malformed_collections_without_mutating_them(self):
        harness = ViewHarness()
        harness.staff = None
        harness.staff_candidates = {"unexpected": "container"}
        harness.staff_tree = Tree()
        harness.staff_candidate_tree = Tree()
        harness.staff_expiry_tree = Tree()
        harness.staff_text = Text()
        harness.post_show_bonuses = {"fight": 0, "ko": 0, "sub": 0}
        harness.scouting = []
        harness.staff_contract_remaining = lambda _member: 12
        harness.staff_contract_expiry_label = lambda _member: "Jan W1 2027"
        harness.staff_contract_status = lambda _member: "Active"
        harness.staff_effect = lambda _role: 0
        before = (harness.staff, deepcopy(harness.staff_candidates))
        harness.refresh_staff()
        self.assertEqual(harness.staff, before[0])
        self.assertEqual(harness.staff_candidates, before[1])
        self.assertEqual(harness.staff_tree.get_children(), ())
        self.assertEqual(harness.staff_candidate_tree.get_children(), ())
        self.assertEqual(harness.staff_expiry_tree.get_children(), ())
        self.assertIn("Unstaffed", harness.staff_text.value)
        refresh_source = inspect.getsource(ViewMixin.refresh_staff)
        self.assertIn("isinstance(raw_staff, (list, tuple))", refresh_source)
        self.assertIn("isinstance(raw_candidates, (list, tuple))", refresh_source)
        display = ViewMixin.staff_display_fields({
            "staff_id": "staff-overflow", "name": "Overflow", "role": "Marketing",
            "skill": float("inf"), "salary": float("nan"), "morale": float("inf"),
        })
        self.assertEqual(display["skill"], "—")
        self.assertEqual(display["salary"], "—")
        self.assertEqual(display["morale"], "—")
        bounded = ViewMixin.staff_display_fields({
            "staff_id": "staff-bounded", "name": "Bounded", "role": "Marketing",
            "skill": "999999999999999999999999", "salary": "999999999999999999999999",
            "morale": "-999999999999999999999999",
        })
        self.assertEqual(bounded["skill"], 100)
        self.assertEqual(bounded["salary_value"], 1_000_000_000)
        self.assertEqual(bounded["morale"], 0)
        self.assertIn("OverflowError", inspect.getsource(ViewMixin.staff_display_fields))
        profile_source = inspect.getsource(ViewMixin.open_selected_staff_profile)
        self.assertIn("salary_display", profile_source)
        self.assertIn("OverflowError", profile_source)

    def test_staff_action_selection_uses_stable_staff_identity_rows(self):
        harness = ViewHarness()
        current = {"staff_id": "staff-stable-2", "name": "Second Lead", "role": "Marketing"}
        harness.staff = [
            {"staff_id": "staff-stable-1", "name": "First Lead", "role": "Marketing"},
            current,
        ]
        harness.staff_tree = Tree(selected=("staff:staff-stable-2",))
        harness.staff_rows = {"staff:staff-stable-2": current}
        self.assertIs(harness.selected_staff_for_action(), current)
        self.assertEqual(ViewHarness._staff_table_row_id(current, 1), "staff:staff-stable-2")
        legacy = ViewHarness._staff_table_row_id({"name": "Legacy"}, 4)
        self.assertTrue(legacy.startswith("staff:legacy:"))
        self.assertEqual(legacy, ViewHarness._staff_table_row_id({"name": "Legacy"}, 99))
        empty = ViewHarness._staff_table_row_id({}, 4)
        self.assertTrue(empty.startswith("staff:legacy:"))
        self.assertEqual(empty, ViewHarness._staff_table_row_id({}, 99))
        duplicate = {"staff_id": "staff-stable-2", "name": "Namesake", "role": "Marketing"}
        self.assertEqual(ViewHarness._staff_table_row_id(duplicate, 5, "staff-candidate"), "staff-candidate:staff-stable-2")

    def test_staff_tab_exposes_read_only_ai_employment_ledger(self):
        ui_source = Path("ui.py").read_text(encoding="utf-8")
        view_source = Path("views.py").read_text(encoding="utf-8")
        world_source = Path("world.py").read_text(encoding="utf-8")
        self.assertIn('("AI Staff Ledger", self.open_ai_staff_employment_window)', ui_source)
        self.assertIn("def open_ai_staff_employment_window(self):", view_source)
        self.assertIn("def ai_staff_employment_rows(self, include_market=True, limit=200):", world_source)
        self.assertIn("does not refresh offers, tick contracts or run AI hiring", view_source)
        ai_ledger = view_source.split("    def open_ai_staff_employment_window", 1)[1].split("\n    def ", 1)[0]
        self.assertIn("def safe_ledger_int(value, fallback=0):", ai_ledger)
        self.assertIn("def safe_runway_label(value):", ai_ledger)
        self.assertIn("if not isinstance(snapshot, dict):", ai_ledger)
        self.assertIn("if not math.isfinite(numeric):", ai_ledger)
        self.assertIn('text="View Evidence Audit"', ui_source)
        self.assertIn("def open_staff_evidence_audit_window(self):", view_source)
        self.assertIn("normalises the save, reruns a handler, spends cash", view_source)

    def test_child_promotion_actions_resolve_by_id_and_fail_closed_for_duplicate_names(self):
        harness = WorldReviewHarness()
        harness.player_company_name = "Parent"
        first = SimpleNamespace(name="Twin Child", promotion_id="child-1", is_child_promotion=True, parent_company="Parent")
        second = SimpleNamespace(name="Twin Child", promotion_id="child-2", is_child_promotion=True, parent_company="Parent")
        unique = SimpleNamespace(name="Unique Child", promotion_id="child-3", is_child_promotion=True, parent_company="Parent")
        harness.promotions = [first, second, unique]
        self.assertIs(harness.child_promotion_by_reference("child-2"), second)
        self.assertIs(harness.child_promotion_by_name("Unique Child"), unique)
        self.assertIsNone(harness.child_promotion_by_name("Twin Child"))

    def test_child_card_planning_is_future_dated_and_identity_bound(self):
        source = Path("views.py").read_text(encoding="utf-8")
        world_source = Path("world.py").read_text(encoding="utf-8")
        manager = source.split("    def open_child_promotion_manager", 1)[1].split("    def company_selected_name", 1)[0]
        self.assertIn("FUTURE CHILD CARDS", manager)
        self.assertIn("schedule_child_promotion_event", manager)
        self.assertIn("scheduled_event_rows", manager)
        self.assertIn("cancel_child_promotion_event", manager)
        self.assertIn("def safe_schedule_int(value, fallback=1):", manager)
        self.assertIn("if not math.isfinite(numeric):", manager)
        self.assertIn("scheduled_events = getattr(promo, \"scheduled_events\", None)", manager)
        self.assertIn("event_week = max(1, min(4, safe_schedule_int", manager)
        schedule = world_source.split("    def schedule_child_promotion_event", 1)[1].split("    def simulate_ai_promotion_month", 1)[0]
        self.assertIn("calendar_week_index(target_month, target_week)", schedule)
        self.assertIn("scheduled_event_counter", schedule)
        self.assertIn('"status": "Scheduled"', schedule)
        self.assertIn("scheduled_events", world_source)
        self.assertIn("return True\n        if promo.cash", world_source)

    def test_refresh_staff_restores_selection_after_reordering(self):
        harness = ViewHarness()
        harness.staff = [
            {"staff_id": "staff-refresh-1", "name": "First", "role": "Marketing", "skill": 60, "salary": 5000, "morale": 70},
            {"staff_id": "staff-refresh-2", "name": "Second", "role": "Marketing", "skill": 65, "salary": 5200, "morale": 72},
        ]
        harness.staff_candidates = [
            {"staff_id": "candidate-refresh-1", "name": "Candidate One", "role": "Marketing", "skill": 55, "salary": 4500, "morale": 65},
            {"staff_id": "candidate-refresh-2", "name": "Candidate Two", "role": "Marketing", "skill": 58, "salary": 4600, "morale": 66},
        ]
        harness.staff_tree = Tree()
        harness.staff_candidate_tree = Tree()
        harness.staff_text = Text()
        harness.post_show_bonuses = {"fight": 0, "ko": 0, "sub": 0}
        harness.scouting = []
        harness.staff_contract_remaining = lambda _member: 12
        harness.staff_contract_expiry_label = lambda _member: "Jan W1 2027"
        harness.staff_effect = lambda _role: 0
        harness.refresh_staff()
        harness.staff_tree.selection_set("staff:staff-refresh-2")
        harness.staff_candidate_tree.selection_set("staff-candidate:candidate-refresh-2")
        harness.staff = list(reversed(harness.staff))
        harness.staff_candidates = list(reversed(harness.staff_candidates))
        harness.refresh_staff()
        self.assertEqual(harness.staff_tree.selection(), ("staff:staff-refresh-2",))
        self.assertEqual(harness.staff_candidate_tree.selection(), ("staff-candidate:candidate-refresh-2",))
        self.assertEqual(harness.staff_rows["staff:staff-refresh-2"]["name"], "Second")
        self.assertEqual(harness.staff_candidate_rows["staff-candidate:candidate-refresh-2"]["name"], "Candidate Two")

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

    def test_result_rows_use_saved_archive_identity_when_available(self):
        harness = ViewHarness()
        first = {"record_id": "event-alpha", "key": "event-alpha", "company": "Alpha", "event": "Alpha 1", "date": "Jan W1 2026"}
        second = {"record_id": "event-beta", "key": "event-beta", "company": "Beta", "event": "Beta 1", "date": "Jan W1 2026"}
        harness.result_index = [first, second]
        harness.result_records = []
        harness.result_history = []
        harness.result_search = Var("")
        harness.result_company_filter = Var("All")
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
        harness.results_tree.selection_set("result:event-beta")
        harness.result_company_filter.set("All")
        # Rebuild with a new card inserted at the front.  The selected event
        # must follow its archive identity, not the old visible position.
        inserted = {"record_id": "event-new", "key": "event-new", "company": "Gamma", "event": "Gamma 1", "date": "Jan W2 2026"}
        harness.result_index = [inserted, first, second]
        harness.refresh_results()

        self.assertEqual(("result:event-beta",), harness.results_tree.selection())
        self.assertEqual("DETAIL:Beta 1", harness.results_text.value)

    def test_assistant_notice_identity_is_stable_and_content_bound(self):
        first = ViewHarness._assistant_notice_view_id("!", "No future event is scheduled", "booking", "urgent")
        repeat = ViewHarness._assistant_notice_view_id("!", "No future event is scheduled", "booking", "urgent")
        changed = ViewHarness._assistant_notice_view_id("!", "No future event is scheduled", "contracts", "urgent")
        self.assertEqual(first, repeat)
        self.assertNotEqual(first, changed)
        self.assertTrue(first.startswith("assistant-notice:"))

    def test_story_thread_identity_prefers_saved_id_and_marks_legacy(self):
        saved = ViewHarness._story_thread_identity({"story_id": "thread-42", "status": "active"}, index=3)
        self.assertEqual(saved, "story:thread-42")
        legacy = ViewHarness._story_thread_identity({
            "type": "Rivalry", "fighter_ids": ["F2", "F1"],
            "created_month": 4, "created_week": 2,
        }, index=3)
        repeat = ViewHarness._story_thread_identity({
            "type": "Rivalry", "fighter_ids": ["F1", "F2"],
            "created_month": 4, "created_week": 2,
        }, index=99)
        self.assertTrue(legacy.startswith("legacy-story:"))
        self.assertEqual(legacy, repeat)
        self.assertEqual(
            ViewHarness._story_thread_identity({}, index=1),
            ViewHarness._story_thread_identity({}, index=999),
        )

    def test_storyline_context_links_fail_closed_for_ambiguous_company_names(self):
        source = inspect.getsource(ViewMixin.open_storylines_window)
        self.assertIn("fighter_ids", source)
        self.assertIn("select_unique_company_by_name", source)

    def test_story_and_chronicle_readers_are_defensive_and_non_mutating(self):
        harness = object.__new__(ViewHarness)
        harness.story_threads = [
            {
                "story_id": "story-safe", "story_key": "safe", "type": "Rivalry",
                "importance": "bad", "fighter_ids": "not-a-list",
                "beats": [{"ref": "b1", "month": "bad", "summary": "Recorded beat"}, "bad-beat"],
                "scoreboard": {"Alpha": "bad"}, "staff_legacy_score": "bad",
            },
            "bad-thread",
        ]
        harness.world_chronicle = [
            {"story_id": "chronicle-safe", "type": "Event", "headline": "A card", "month": "bad", "companies": "Alpha"},
            "bad-chronicle",
        ]
        before_threads = repr(harness.story_threads)
        before_chronicle = repr(harness.world_chronicle)
        stories = ViewMixin.story_thread_reader_rows(harness)
        chronicle = ViewMixin.world_chronicle_reader_rows(harness)
        self.assertEqual(len(stories), 2)
        self.assertEqual(stories[0]["_read_status"], "Needs review")
        self.assertEqual(stories[0]["fighter_ids"], [])
        self.assertEqual(stories[0]["beats"][0]["month"], 0)
        self.assertEqual(stories[1]["_read_status"], "Unavailable")
        self.assertEqual(len(chronicle), 2)
        self.assertFalse(chronicle[0]["_date_valid"])
        self.assertEqual(chronicle[0]["companies"], [])
        self.assertEqual(chronicle[1]["_read_status"], "Unavailable")
        self.assertEqual(repr(harness.story_threads), before_threads)
        self.assertEqual(repr(harness.world_chronicle), before_chronicle)

    def test_story_reader_fails_closed_for_nonfinite_numbers(self):
        harness = object.__new__(ViewHarness)
        harness.story_threads = [{
            "story_id": "story-nonfinite",
            "importance": float("inf"),
            "last_updated_month": float("nan"),
            "beats": [{"month": float("inf"), "week": float("nan"), "summary": "beat"}],
            "scoreboard": {"Alpha": float("inf")},
        }]
        before = repr(harness.story_threads)

        rows = ViewMixin.story_thread_reader_rows(harness, limit=float("inf"))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["importance"], 1)
        self.assertEqual(rows[0]["last_updated_month"], 0)
        self.assertEqual(rows[0]["beats"][0]["month"], 0)
        self.assertEqual(rows[0]["beats"][0]["week"], 1)
        self.assertEqual(rows[0]["scoreboard"], {})
        self.assertEqual(rows[0]["_read_status"], "Needs review")
        self.assertEqual(repr(harness.story_threads), before)

    def test_story_reader_fails_closed_when_fallback_date_is_nonfinite(self):
        harness = object.__new__(ViewHarness)
        harness.story_threads = [{
            "story_id": "story-fallback-nonfinite",
            "started_month": float("inf"),
            "last_updated_month": "bad",
        }]

        rows = ViewMixin.story_thread_reader_rows(harness)

        self.assertEqual(rows[0]["last_updated_month"], 0)
        self.assertEqual(rows[0]["_read_status"], "Needs review")

    def test_world_chronicle_identity_survives_reordering(self):
        first = ViewHarness._chronicle_entry_identity({"story_id": "chronicle-1", "headline": "One"}, index=0)
        second = ViewHarness._chronicle_entry_identity({"story_id": "chronicle-2", "headline": "Two"}, index=1)
        self.assertEqual(first, "chronicle:chronicle-1")
        self.assertEqual(ViewHarness._chronicle_entry_identity({"story_id": "chronicle-1"}, index=9), first)
        self.assertEqual([second, first].index(first), 1)
        self.assertEqual(
            ViewHarness._chronicle_entry_identity({}, index=0),
            ViewHarness._chronicle_entry_identity({}, index=99),
        )

    def test_world_chronicle_reader_fails_closed_for_nonfinite_dates(self):
        harness = object.__new__(ViewHarness)
        harness.world_chronicle = [{
            "story_id": "chronicle-nonfinite",
            "month": float("inf"), "week": float("nan"),
            "headline": "Retained chronology",
        }]
        before = repr(harness.world_chronicle)

        rows = ViewMixin.world_chronicle_reader_rows(harness, limit=float("inf"))

        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["_date_valid"])
        self.assertEqual(rows[0]["month"], 0)
        self.assertEqual(rows[0]["week"], 1)
        self.assertEqual(rows[0]["_read_status"], "Needs review")
        self.assertEqual(repr(harness.world_chronicle), before)

    def test_world_chronicle_reader_routes_context_by_identity(self):
        source = inspect.getsource(ViewMixin.open_world_chronicle)
        for marker in ("chronicle_rows_by_key", "selected_chronicle_entry", "chronicle_row_keys", "prior_chronicle_key"):
            self.assertIn(marker, source)
        self.assertIn("fighter_ids", source)
        self.assertIn("select_unique_company_by_name", source)
        self.assertNotIn("entry = rows[selected[0]]", source)

    def test_world_hub_news_selection_uses_source_bound_row_keys(self):
        harness = object.__new__(ViewHarness)
        first = {"story_id": "story-a", "headline": "A"}
        second = {"story_id": "story-b", "headline": "B"}
        harness.world_news_list = ListSelection(1)
        harness._world_news_row_keys = ["chronicle:story-a", "chronicle:story-b"]
        harness._world_news_rows_by_key = {
            "chronicle:story-a": first, "chronicle:story-b": second,
        }
        harness._world_news_entries = [first, second]
        self.assertIs(ViewMixin._selected_world_news_entry(harness), second)
        source = inspect.getsource(ViewMixin.refresh_world)
        self.assertIn("world_chronicle_reader_rows", source)

    def test_regions_selection_uses_source_bound_identity(self):
        harness = object.__new__(ViewHarness)
        harness.regions = {"USA": {}, "Europe": {}}
        harness.region_list = RegionListSelection(["USA", "Europe"], index=1)
        harness._region_list_keys = ["region:USA", "region:Europe"]
        harness._region_rows_by_key = {
            "region:USA": "USA", "region:Europe": "Europe",
        }
        self.assertEqual(ViewMixin.selected_region_name(harness), "Europe")
        # A refresh that reorders the source still restores Europe by its
        # saved key rather than clamping the old visible index.
        harness.regions = {"Europe": {}, "USA": {}}
        harness.refresh_region_profile = lambda: None
        ViewMixin.refresh_regions(harness)
        self.assertEqual(harness.region_list.values, ["Europe", "USA"])
        self.assertEqual(harness.region_list.curselection(), (0,))
        self.assertEqual(ViewMixin.selected_region_name(harness), "Europe")
        self.assertEqual(ViewHarness._region_ui_identity("Europe", index=99), "region:Europe")
        self.assertTrue(ViewHarness._region_ui_identity("", index=4).startswith("legacy-region:"))
        self.assertEqual(ViewHarness._region_ui_identity("", index=4), ViewHarness._region_ui_identity("", index=99))

    def test_region_profile_reader_is_defensive_and_non_mutating(self):
        harness = object.__new__(ViewHarness)
        harness.regions = {"USA": {"areas": "bad", "drug_accuracy": "unknown"}, "Broken": "legacy row"}
        before = deepcopy(harness.regions)
        projected = ViewMixin.region_data_reader(harness, "USA")
        self.assertEqual(projected["_read_status"], "Recorded")
        self.assertEqual(projected["areas"], [])
        self.assertEqual(projected["drug_accuracy"], 0)
        self.assertEqual(harness.regions, before)
        unavailable = ViewMixin.region_data_reader(harness, "Broken")
        self.assertEqual(unavailable["_read_status"], "Unavailable")
        unavailable_catalogue = ViewMixin.region_data_reader(SimpleNamespace(regions="bad"), "USA")
        self.assertEqual(unavailable_catalogue["_read_status"], "Unavailable")

    def test_region_team_reader_fails_closed_for_malformed_gym_rows(self):
        harness = object.__new__(ViewHarness)
        harness.gyms = [
            "malformed gym",
            SimpleNamespace(region="USA", name="Good Gym", reputation=float("inf"), quality="bad", facilities=3),
        ]
        before = repr(harness.gyms)
        teams = ViewMixin.region_team_names(harness, "USA", data={"teams": "bad"}, limit=float("nan"))
        self.assertEqual(teams, ["Good Gym"])
        self.assertEqual(repr(harness.gyms), before)

    def test_regional_prospect_refresh_uses_non_repairing_assessment(self):
        source = inspect.getsource(ViewMixin.regional_prospect_rows)
        self.assertIn("regional_candidate_assessment(fighter, promo, repair=False)", source)
        assessment = inspect.getsource(WorldMixin.regional_candidate_assessment)
        self.assertIn("repair=False", assessment)
        self.assertIn("saved_baseline", assessment)
        self.assertIn("except (TypeError, ValueError, OverflowError)", assessment)
        harness = object.__new__(WorldMixin)
        fighter = SimpleNamespace(
            feeder_origin="Regional", record_history_baseline_w=float("inf"),
            record_history_baseline_l=float("nan"), record_history_baseline_d="bad",
            record_w=float("inf"), record_l=float("nan"), record_d="bad", age=float("inf"), potential=float("nan"),
            momentum=float("inf"), popularity=float("nan"), injured=False, retirement_pending=False,
            retired=False,
        )
        promo = SimpleNamespace(name="Regional")
        result = WorldMixin.regional_candidate_assessment(harness, fighter, promo, repair=False)
        self.assertEqual(result["bouts"], 0)
        self.assertEqual(result["win_rate"], 0)
        self.assertEqual(result["status"], "Developing")

    def test_regions_reader_routes_actions_through_selected_identity(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        hub = source.split("    def open_selected_region_hub", 1)[1].split("    def open_region_feasibility_window", 1)[0]
        refresh = source.split("    def refresh_regions(self):", 1)[1].split("    def region_team_names", 1)[0]
        profile = source.split("    def refresh_region_profile(self):", 1)[1].split("    def open_selected_region_feasibility", 1)[0]
        feasibility = source.split("    def open_selected_region_feasibility(self):", 1)[1].split("    def open_region_feasibility_window", 1)[0]
        for block in (refresh, profile, feasibility, hub):
            self.assertIn("selected_region_name", block)
        self.assertIn("region_data_reader", hub)
        self.assertNotIn("data = self.regions[region]", hub)
        self.assertIn("_region_list_keys", refresh)
        self.assertIn("_region_rows_by_key", refresh)
        self.assertNotIn("selection_set(min(current[0]", refresh)
        self.assertNotIn("self.region_list.get(self.region_list.curselection()[0])", profile)
        self.assertNotIn("self.region_list.get(self.region_list.curselection()[0])", feasibility)

    def test_region_hub_gym_actions_use_identity_bound_rows(self):
        source = inspect.getsource(ViewMixin.open_selected_region_hub)
        for marker in ("gym_row_keys", "gym_rows_by_key", "used_gym_keys", "_world_gym_identity", "open_selected_region_gym"):
            self.assertIn(marker, source)
        self.assertNotIn("self.open_gym_viewer(gyms[gym_list.curselection()[0]])", source)
        self.assertIn("gym_rows_by_key.get(row_key)", source)
        self.assertIn('if not events:', source)

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
        harness.red_fight_plan = Var("Balanced")
        harness.blue_fight_plan = Var("Balanced")
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

    def test_world_refresh_does_not_resynchronize_gym_membership(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        refresh = source.split("    def refresh_world(self):", 1)[1].split("    def show_selected_world_promotion", 1)[0]
        self.assertNotIn("self.sync_gym_membership()", refresh)
        viewer = source.split("    def open_gym_viewer", 1)[1].split("    def ", 1)[0]
        self.assertNotIn("self.sync_gym_membership()", viewer)

    def test_eurasian_feeder_description_is_not_used_as_level(self):
        source = (Path(__file__).parent / "seeding.py").read_text(encoding="utf-8")
        self.assertIn('reputation="Regional Feeder"', source)
        self.assertIn('strategy["description"] = EURASIAN_FIGHT_CIRCUIT_DESCRIPTION', source)

    def test_sponsor_market_rows_bind_to_agreement_or_offer_identity(self):
        saved = ViewHarness._sponsor_market_row_identity({"agreement_id": "agreement-7", "name": "Brand"}, kind="deal", index=0)
        self.assertEqual(saved, "sponsor-deal:agreement-7")
        offer = ViewHarness._sponsor_market_row_identity({"id": "offer-3", "name": "Brand"}, kind="offer", index=4)
        self.assertEqual(offer, "sponsor-offer:offer-3")
        legacy = ViewHarness._sponsor_market_row_identity({"name": "Brand", "category": "Equipment", "fee": 5000}, kind="deal", index=0)
        reordered = ViewHarness._sponsor_market_row_identity({"name": "Brand", "category": "Equipment", "fee": 5000}, kind="deal", index=99)
        self.assertTrue(legacy.startswith("legacy-sponsor-deal:"))
        self.assertEqual(legacy, reordered)

    def test_sponsor_refresh_keeps_active_deals_read_only_and_separate(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        refresh = source.split("    def refresh_finance(self):", 1)[1].split("    def refresh_finance_history_outlook", 1)[0]
        media = (Path(__file__).parent / "media.py").read_text(encoding="utf-8")
        self.assertIn("self._sponsor_market_rows = {}", refresh)
        self.assertIn("kind\": kind", refresh)
        self.assertIn("selected_sponsor_deal", media)
        self.assertIn("sponsor_accept_button", media)

    def test_finance_and_media_history_readers_keep_malformed_rows_visible(self):
        views = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        media = (Path(__file__).parent / "media.py").read_text(encoding="utf-8")
        finance_refresh = views.split("    def refresh_finance(self):", 1)[1].split("    def refresh_finance_history_outlook", 1)[0]
        finance_outlook = views.split("    def refresh_finance_history_outlook(self):", 1)[1].split("    def refresh_finance_runway", 1)[0]
        for marker in ("safe_int", '"Unavailable"', "if not isinstance(row, dict)", "valid_recent"):
            self.assertIn(marker, finance_refresh + finance_outlook)
        self.assertIn("display_month = safe_int", finance_refresh)
        self.assertIn("display_week = safe_int", finance_refresh)
        dashboard = media.split("    def refresh_media_dashboard(self):", 1)[1].split("    def refresh_media_receipts", 1)[0]
        receipts = media.split("    def refresh_media_receipts(self):", 1)[1].split("    @staticmethod\n    def _media_receipt_identity_key", 1)[0]
        for marker in ("audience_history", "offers", "Malformed retained offer", "safe_int"):
            self.assertIn(marker, dashboard)
        for marker in ("Malformed retained receipt", "if not isinstance(receipt, dict)"):
            self.assertIn(marker, receipts)
        self.assertIn("_media_receipt_view_id(receipt", receipts)
        self.assertNotIn('row_id = f"legacy-receipt:{index}"', receipts)
        receipt_identity = inspect.getsource(MediaMixin._media_receipt_identity_key)
        self.assertIn("legacy-receipt:", receipt_identity)
        self.assertIn("json.dumps(payload, sort_keys=True", receipt_identity)
        selected_receipt = inspect.getsource(MediaMixin._selected_media_receipt)
        self.assertNotIn("rows[index]", selected_receipt)

    def test_finance_refresh_projects_without_repairing_saved_envelope(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        refresh = source.split("    def refresh_finance(self):", 1)[1].split("    def refresh_finance_history_outlook", 1)[0]
        outlook = source.split("    def refresh_finance_history_outlook(self):", 1)[1].split("    def refresh_finance_runway", 1)[0]
        self.assertIn("raw_finance = getattr(self, \"finance\", {})", refresh)
        self.assertIn("finance = dict(raw_finance)", refresh)
        self.assertNotIn("self.ensure_finance_defaults()", refresh)
        self.assertNotIn('self.finance["staff_payroll"]', refresh)
        self.assertNotIn('self.finance["sponsor_offers"]', refresh)
        self.assertIn("raw_finance = getattr(self, \"finance\", {})", outlook)
        self.assertNotIn("self.update_annual_finance_history()", outlook)

    def test_finance_readers_fail_closed_for_overflow_and_nonfinite_values(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        refresh = source.split("    def refresh_finance(self):", 1)[1].split("    def refresh_finance_history_outlook", 1)[0]
        outlook = source.split("    def refresh_finance_history_outlook(self):", 1)[1].split("    def refresh_finance_runway", 1)[0]
        runway = source.split("    def refresh_finance_runway(self):", 1)[1].split("    def refresh_finance_runway_row", 1)[0] if "    def refresh_finance_runway_row" in source else source.split("    def refresh_finance_runway(self):", 1)[1]
        for block in (refresh, outlook, runway):
            self.assertIn("OverflowError", block)
            self.assertIn("safe_int", block)
        self.assertIn("math.isfinite", refresh)

    def test_finance_readers_project_strategic_upkeep_without_repairing_envelope(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        refresh = source.split("    def refresh_finance(self):", 1)[1].split("    def refresh_finance_history_outlook", 1)[0]
        dashboard = source.split("    def refresh_assistant(self):", 1)[1].split("    def refresh_website", 1)[0]
        self.assertIn("strategic_investment_upkeep(repair=False)", refresh)
        self.assertIn("strategic_investment_upkeep(repair=False)", dashboard)
        world_source = (Path(__file__).parent / "world.py").read_text(encoding="utf-8")
        self.assertIn("def owned_strategic_investments(self, *, repair=True)", world_source)
        self.assertIn("return dict(owned) if isinstance(owned, dict) else {}", world_source)
        app = FinanceReaderHarness("legacy finance payload")
        before = app.finance
        self.assertEqual(app.strategic_investment_upkeep(repair=False), 0)
        self.assertIs(app.finance, before)
        app.finance = {"strategic_investments": "unavailable"}
        before = dict(app.finance)
        self.assertEqual(app.strategic_investment_upkeep(repair=False), 0)
        self.assertEqual(app.finance, before)

    def test_milestone_projection_keeps_malformed_finance_readable(self):
        source = (Path(__file__).parent / "world.py").read_text(encoding="utf-8")
        projection = source.split("    def company_milestone_projection(self, rule):", 1)[1].split("    def result_record_month", 1)[0]
        for marker in ("safe_int", "math.isfinite", "OverflowError", "isinstance(recent_value, list)", "valid_records"):
            self.assertIn(marker, projection)
        app = FinanceReaderHarness("legacy finance payload")
        app.result_records = ["legacy row", {"company": "Other", "date": "Month 1 Week 1"}]
        app.month = 3
        app.company_stability = 48
        app.company_safety = 61
        before = app.finance
        result = app.company_milestone_projection({
            "cash": 1_000_000, "months": 6, "stability": 45,
            "popularity": 0, "safety": 0, "events": 2,
        })
        self.assertEqual(set(result), {"monthly_net", "cash_gap", "event_gap", "eta_months", "blockers"})
        self.assertEqual(result["monthly_net"], 0)
        self.assertEqual(result["event_gap"], 2)
        self.assertIs(app.finance, before)
        malformed = app.company_milestone_projection({
            "cash": float("inf"), "months": float("nan"),
            "stability": "999999999999999999999999999999999999",
            "popularity": float("inf"), "safety": -float("inf"),
            "events": float("nan"),
        })
        self.assertEqual(malformed["cash_gap"], 0)
        self.assertEqual(malformed["event_gap"], 0)
        self.assertIs(app.finance, before)

    def test_media_offer_rows_use_saved_identity_and_legacy_fingerprints(self):
        stable = MediaMixin._media_offer_identity_key({"id": "offer-7", "name": "Stream"}, index=0)
        self.assertEqual(stable, "media-offer:offer-7")
        legacy = MediaMixin._media_offer_identity_key({"name": "Stream", "fee": 5000, "months": 6}, index=0)
        reordered = MediaMixin._media_offer_identity_key({"name": "Stream", "fee": 5000, "months": 6}, index=99)
        self.assertTrue(legacy.startswith("legacy-media-offer:"))
        self.assertEqual(legacy, reordered)
        source = (Path(__file__).parent / "media.py").read_text(encoding="utf-8")
        dashboard = source.split("    def refresh_media_dashboard(self):", 1)[1].split("    def refresh_media_receipts", 1)[0]
        self.assertIn("self._media_offer_rows = {}", dashboard)
        self.assertIn("_media_offer_view_id", dashboard)
        self.assertIn("retained_offer_id", dashboard)
        self.assertIn("_media_offer_rows", source.split("    def _selected_media_offer_id", 1)[1].split("    def media_accept_selected_offer", 1)[0])

    def test_media_receipt_rows_use_retained_facts_not_visible_positions(self):
        first = {"date": "M2 W1", "event": "Card A", "rights": {"amount": 1000}, "sponsor_total": 500}
        second = dict(first)
        self.assertEqual(
            MediaMixin._media_receipt_identity_key(first),
            MediaMixin._media_receipt_identity_key(second),
        )
        self.assertTrue(MediaMixin._media_receipt_view_id(first, fallback_index=0).startswith("legacy-receipt:"))
        self.assertEqual(
            MediaMixin._media_receipt_view_id(first, fallback_index=0),
            MediaMixin._media_receipt_view_id(first, fallback_index=99),
        )
        self.assertEqual(
            MediaMixin._media_receipt_view_id([], fallback_index=0),
            MediaMixin._media_receipt_view_id([], fallback_index=99),
        )

    def test_media_campaign_history_uses_content_identity_and_selected_detail(self):
        campaign = {
            "date": "M4 W2", "month": 4, "week": 2, "strategy": "Balanced",
            "action": "Interview", "subject": "Fighter One", "target": "",
            "outcome": "Strong response", "band": "Strong", "heat": 8, "cost": 0,
        }
        self.assertEqual(
            MediaMixin._media_campaign_identity_key(campaign),
            MediaMixin._media_campaign_identity_key(dict(campaign)),
        )
        self.assertNotEqual(
            MediaMixin._media_campaign_identity_key(campaign),
            MediaMixin._media_campaign_identity_key({**campaign, "outcome": "Backlash"}),
        )
        self.assertTrue(MediaMixin._media_campaign_view_id(campaign).startswith("legacy-media-campaign:"))
        source = (Path(__file__).parent / "media.py").read_text(encoding="utf-8")
        dashboard = source.split("    def refresh_media_dashboard(self):", 1)[1].split("    def refresh_media_receipts", 1)[0]
        for marker in ("_media_campaign_rows", "_media_campaign_view_id", "retained_campaign_id", "show_selected_media_campaign"):
            self.assertIn(marker, dashboard)
        self.assertIn("media_campaign_detail", (Path(__file__).parent / "ui.py").read_text(encoding="utf-8"))

    def test_media_campaign_controls_route_duplicate_fighters_by_identity(self):
        views = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        media = (Path(__file__).parent / "media.py").read_text(encoding="utf-8")
        website = views.split("    def refresh_website(self):", 1)[1].split("    def open_selected_story_context", 1)[0]
        targets = views.split("    def refresh_media_targets", 1)[1].split("    def legacy_media_desk_callout", 1)[0]
        run = media.split("    def media_run_selected_campaign", 1)[1].split("    def refresh_media_plan_targets", 1)[0]
        for marker in ("_media_fighter_rows", "used_labels", "prior_media_fighter", "media_fighter_choice.set"):
            self.assertIn(marker, website)
        for marker in ("_media_target_rows", "prior_target", "fighter_display_name", "selected_target"):
            self.assertIn(marker, targets)
        self.assertIn("_media_target_rows", run)
        self.assertNotIn("target = self.get_fighter(self.media_target_choice.get())", views + media)

    def test_media_actions_keep_routine_feedback_on_desk(self):
        ui = (Path(__file__).parent / "ui.py").read_text(encoding="utf-8")
        media = (Path(__file__).parent / "media.py").read_text(encoding="utf-8")
        website = ui.split("    def build_website_tab", 1)[1].split("    def build_finance_tab", 1)[0]
        self.assertIn("self.media_action_notice", website)
        self.assertIn("self.media_plan_notice", website)
        self.assertIn("self.media_rights_notice", website)
        for method, next_method in (
            ("media_run_selected_campaign", "refresh_media_plan_targets"),
            ("media_save_plan_from_ui", "media_retarget_plan_from_ui"),
            ("media_accept_selected_offer", "media_reject_selected_offer"),
            ("media_prepare_renewal", "media_accept_renewal"),
        ):
            block = media.split(f"    def {method}", 1)[1].split(f"    def {next_method}", 1)[0]
            self.assertIn("_media_", block)
            self.assertNotIn('messagebox.showinfo("Media Rights"', block)
        self.assertIn("_media_surface_notice", media)

    def test_secondary_readers_keep_missing_state_on_owning_surface(self):
        ui = (Path(__file__).parent / "ui.py").read_text(encoding="utf-8")
        events = (Path(__file__).parent / "events.py").read_text(encoding="utf-8")
        media = (Path(__file__).parent / "media.py").read_text(encoding="utf-8")
        receipt = media.split("    def media_open_selected_receipt", 1)[1].split("    def ", 1)[0]
        self.assertIn("_media_receipt_notice", media)
        self.assertNotIn('messagebox.showinfo("Settlement receipt"', receipt)
        staff = ui.split("    def staff_open_selected_work_receipt", 1)[1].split("    def ", 1)[0]
        self.assertIn("_staff_status_notice", staff)
        self.assertIn('messagebox.showinfo("Staff receipt"', staff)  # headless/legacy fallback only
        bracket = events.split("    def open_event_tournament_bracket", 1)[1].split("    def ", 1)[0]
        self.assertIn("_results_status_notice", bracket)
        self.assertIn("archive_detail.set", ui)

    def test_simulation_lab_keeps_routine_feedback_in_tool_surfaces(self):
        admin = (Path(__file__).parent / "admin.py").read_text(encoding="utf-8")
        for marker in ("_simulation_status_notice", "sim_result", "sim_tournament_report", "export_status_var"):
            self.assertIn(marker, admin)
        self.assertIn("Draw & Seed Field", admin)
        self.assertNotIn('messagebox.showerror("Testing desk"', (Path(__file__).parent / "views.py").read_text(encoding="utf-8"))

    def test_game_and_saves_keeps_routine_outcomes_in_context(self):
        persistence = (Path(__file__).parent / "persistence.py").read_text(encoding="utf-8")
        self.assertIn("def _save_surface_notice", persistence)
        for method, next_method in (
            ("save_game", "normalized_save_name"),
            ("use_selected_universe_database", "clone_selected_universe_database"),
            ("export_database", "career_conversion_preview"),
            ("import_quick_save_as_database", "load_selected_database"),
            ("load_selected_database", "open_create_promotion_mode"),
        ):
            block = persistence.split(f"    def {method}", 1)[1].split(f"    def {next_method}", 1)[0]
            self.assertIn("_save_surface_notice", block, method)
        section_editor = persistence.split("    def open_universe_section_editor", 1)[1].split("    def validate_universe_section", 1)[0]
        self.assertIn("section_status", section_editor)
        self.assertIn("Validation needs attention", section_editor)
        self.assertIn("Save failed", persistence)  # failures retain an actionable compatibility path
        self.assertIn("Overwrite Save Slot", persistence)  # explicit destructive approval remains modal

    def test_database_editor_keeps_routine_guidance_in_status_line(self):
        editor = (Path(__file__).parent / "database_editor.py").read_text(encoding="utf-8")
        self.assertIn("def _editor_notice", editor)
        for marker in (
            "Select a fighter first.", "Select a record first.",
            "Choose a field and leave at least one record", "Choose a universe database first.",
        ):
            self.assertIn(marker, editor)
        validation = editor.split("    def validate_database", 1)[1].split("    def preflight_database", 1)[0]
        self.assertIn("Validation complete", validation)
        self.assertNotIn('messagebox.showinfo("Database valid"', validation)

    def test_world_editor_keeps_routine_guidance_in_context(self):
        ui = (Path(__file__).parent / "ui.py").read_text(encoding="utf-8")
        views = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        self.assertIn("editor_action_notice_var", ui)
        self.assertIn("def _editor_status_notice", views)
        for method in (
            "save_database_editor_fighter",
            "open_editor_selected_profile",
            "retire_database_editor_fighter",
            "open_detailed_skill_editor",
        ):
            body = views.split(f"    def {method}", 1)[1].split("    def ", 1)[0]
            self.assertIn("_editor_status_notice", body, method)
        self.assertIn("Detailed ratings saved", views)
        self.assertIn("pending career save", views)
        self.assertIn('messagebox.showwarning("Current Career Editor"', views)  # native fallback only

    def test_awards_fighter_leaderboard_routes_profiles_by_identity(self):
        fighter = SimpleNamespace(fighter_id="record-fighter-7", name="Same Name")
        self.assertEqual("record-fighter:record-fighter-7", AwardsMixin._record_fighter_row_id("Alpha", fighter))
        legacy = SimpleNamespace(name="Same Name", gender="Male", weight="Lightweight", record="4-1-0")
        self.assertEqual(
            AwardsMixin._record_fighter_row_id("Alpha", legacy),
            AwardsMixin._record_fighter_row_id("Alpha", legacy, fallback_index=99),
        )
        source = (Path(__file__).parent / "awards.py").read_text(encoding="utf-8")
        reader = source.split("        def refresh_fighter_records", 1)[1].split("        def open_selected_record", 1)[0]
        self.assertIn("fighter_rows", reader)
        self.assertIn("iid=row_id", reader)
        self.assertNotIn('fighter_tree.item(selected[0], "values")[1]', source)

    def test_legacy_ledger_rows_do_not_use_displayed_rank_as_identity(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        reader = source.split("    def open_legacy_ledger", 1)[1].split("\n    def ", 1)[0]
        self.assertIn('base_iid = f"legacy:{key}"', reader)
        self.assertIn("used_legacy_ids", reader)
        self.assertNotIn('iid=f"legacy:{key}:{index}"', reader)

    def test_achievement_ledger_keeps_fighter_identity_and_fails_closed_for_legacy_duplicates(self):
        fighter_a = SimpleNamespace(fighter_id="fighter-a", name="Same Name")
        fighter_b = SimpleNamespace(fighter_id="fighter-b", name="Same Name")
        class Harness(AwardsMixin):
            def __init__(self):
                self.month = 1
                self.achievement_log = []
                self.player_company_name = "Alpha"
                self.news = []
                self.inbox = []

            def current_year(self):
                return 2026

        app = Harness()
        self.assertTrue(app.unlock_achievement("Fighter", fighter_a.name, "Alpha", "first", "First", "First win", fighter=fighter_a))
        self.assertFalse(app.unlock_achievement("Fighter", fighter_a.name, "Alpha", "first", "First", "First win", fighter=fighter_a))
        self.assertTrue(app.unlock_achievement("Fighter", fighter_b.name, "Alpha", "first", "First", "First win", fighter=fighter_b))
        self.assertEqual({"fighter-a", "fighter-b"}, {row.get("fighter_id") for row in app.achievement_log})
        source = (Path(__file__).parent / "awards.py").read_text(encoding="utf-8")
        self.assertIn("fighter_id", source.split("    def unlock_achievement", 1)[1].split("    def fighter_company_name", 1)[0])
        unlock = source.split("    def unlock_achievement", 1)[1].split("    def fighter_company_name", 1)[0]
        self.assertIn("resolve_award_fighter", unlock)
        self.assertNotIn("find_fighter_anywhere(target)", unlock)
        window = source.split("    def open_achievements_window", 1)[1].split("    def season_bucket", 1)[0]
        self.assertIn("resolve_award_fighter", window)
        self.assertNotIn("find_fighter_anywhere(entry[\"target\"])", window)

    def test_title_lineage_rows_preserve_division_and_fighter_identity(self):
        lineage = {"company": "Alpha", "tier": "Major", "division": "Male Lightweight"}
        entry = {"action": "Champion Crowned", "date": "Month 4 Week 1", "fighter": "Same Name", "fighter_id": "fighter-7"}
        self.assertEqual(AwardsMixin._title_lineage_row_id(lineage), AwardsMixin._title_lineage_row_id(dict(lineage)))
        self.assertTrue(AwardsMixin._title_history_entry_row_id(lineage, entry).startswith("title-entry:"))
        legacy_id = AwardsMixin._title_history_entry_row_id(lineage, {**entry, "fighter_id": ""})
        self.assertTrue(legacy_id.startswith("legacy-title-entry:"))
        source = (Path(__file__).parent / "awards.py").read_text(encoding="utf-8")
        reader = source.split("    def build_title_lineage_tab", 1)[1]
        for marker in ("_title_lineage_row_id", "_title_history_entry_row_id", 'state = {"lineage_by_row": {}, "entry_by_row": {}', "resolve_award_fighter"):
            self.assertIn(marker, reader)
        self.assertNotIn('name = detail_tree.item(selected[0], "values")[2]', reader)

    def test_name_only_profile_readers_fail_closed_for_duplicate_careers(self):
        class Harness(ViewMixin):
            def __init__(self, fighters):
                self._fighters = list(fighters)

            def all_fighter_objects(self):
                return list(self._fighters)

        first = SimpleNamespace(name="Same Name", fighter_id="a")
        second = SimpleNamespace(name="Same Name", fighter_id="b")
        unique = SimpleNamespace(name="Unique Name", fighter_id="c")
        app = Harness([first, second, unique])
        self.assertIsNone(app.resolve_unique_fighter_name("Same Name"))
        self.assertIs(unique, app.resolve_unique_fighter_name("Unique Name"))
        self.assertIsNone(app.resolve_unique_fighter_name("Missing"))
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        helper = source.split("    def resolve_unique_fighter_name", 1)[1].split("    def open_tree_fighter_profile", 1)[0]
        self.assertIn("len(matches) == 1", helper)
        self.assertIn("resolve_unique_fighter_name(fighter.rival)", source)
        self.assertNotIn("find_fighter_anywhere(self.clean_display_fighter_name(values[3]))", source)

    def test_world_hub_gym_rows_use_identity_not_sort_position(self):
        saved = ViewHarness._world_gym_identity(SimpleNamespace(gym_id="gym-7", name="Elite Room", region="USA"), index=3)
        self.assertEqual(saved, "gym:gym-7")
        legacy = ViewHarness._world_gym_identity(SimpleNamespace(name="Elite Room", region="USA"), index=3)
        reordered = ViewHarness._world_gym_identity(SimpleNamespace(name="Elite Room", region="USA"), index=99)
        self.assertTrue(legacy.startswith("legacy-gym:"))
        self.assertEqual(legacy, reordered)
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        refresh = source.split("    def refresh_world(self):", 1)[1].split("    def show_selected_world_promotion", 1)[0]
        self.assertIn("self._world_gym_rows = {}", refresh)
        self.assertIn("previous_gym_key", refresh)
        selected = inspect.getsource(ViewMixin.selected_gym_from_tree)
        self.assertIn("_world_gym_rows", selected)
        self.assertIn("len(matches) == 1", selected)
        self.assertNotIn("return self.gym_by_name(values[0])", selected)

    def test_simulation_tournament_rows_use_fighter_identity(self):
        refresh = inspect.getsource(AdminMixin.refresh_sim_fighter_choices)
        seed = inspect.getsource(AdminMixin.auto_seed_sim_tournament)
        run = inspect.getsource(AdminMixin.run_simulation_tournament)
        for marker in ("_sim_tournament_row_keys", "_sim_tournament_rows_by_key", "prior_selected_keys", "name_counts"):
            self.assertIn(marker, refresh)
        self.assertIn("_simulation_tournament_source_key", seed)
        self.assertIn("selected_keys", run)
        self.assertNotIn("selected_names = [self.sim_tournament_list.get", run)
        self.assertNotIn("find_fighter_anywhere(name)", run)
        self.assertIn("selected_sim_fighter", inspect.getsource(AdminMixin.update_sim_fighter_cards))
        self.assertIn("_sim_fighter_choice_rows", refresh)
        self.assertIn("Duplicate display names", inspect.getsource(AdminMixin.run_quick_fight_sim))

    def test_world_hub_promotion_rows_use_identity_not_sort_position(self):
        saved = ViewHarness._world_promotion_identity(SimpleNamespace(promotion_id="promo-7", name="North Star", region="USA"), index=3)
        self.assertEqual(saved, "promotion:promo-7")
        legacy = ViewHarness._world_promotion_identity(SimpleNamespace(name="North Star", region="USA"), index=3)
        reordered = ViewHarness._world_promotion_identity(SimpleNamespace(name="North Star", region="USA"), index=99)
        self.assertTrue(legacy.startswith("legacy-promotion:"))
        self.assertEqual(legacy, reordered)
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        refresh = source.split("    def refresh_world(self):", 1)[1].split("    def show_selected_world_promotion", 1)[0]
        self.assertIn("self._world_promotion_identity", refresh)
        self.assertNotIn("promo.show_history = []", refresh)

    def test_world_hub_refresh_projects_malformed_promotion_and_gym_rows(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        refresh = source.split("    def refresh_world(self):", 1)[1].split("    def show_selected_world_promotion", 1)[0]
        for marker in (
            'if not isinstance(promotions, (list, tuple))',
            'def safe_number(value, fallback=0.0)',
            'except (AttributeError, TypeError, ValueError, OverflowError):',
            'if not isinstance(gyms, (list, tuple))',
            'specialties = specialties if isinstance(specialties, (list, tuple)) else []',
        ):
            self.assertIn(marker, refresh)

    def test_profile_follow_button_reads_subscription_projection(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        profile = source.split("fighter_follow_id =", 1)[1].split("def toggle_fighter_follow", 1)[0]
        self.assertIn("story_subscriptions_read_model", profile)
        self.assertNotIn("ensure_story_subscriptions()", profile)

    def test_company_profile_follow_button_reads_subscription_projection(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        profile = source.split('if hasattr(self, "follow_story_target") and data.get("name"):', 1)[1].split("def company_power_components", 1)[0]
        self.assertIn("story_subscriptions_read_model", profile)
        self.assertIn("self.ensure_story_subscriptions()", profile)
        self.assertNotIn("self.ensure_story_subscriptions()\n            company_name", profile)

    def test_company_readers_do_not_seed_missing_promotion_strategy(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        child_manager = source.split("    def open_child_promotion_manager", 1)[1].split("    def company_selected_name", 1)[0]
        profile = source.split("    def refresh_company_profile(self):", 1)[1].split("    def _closest_rivals", 1)[0]
        selected = source.split("    def selected_company_data(self):", 1)[1].split("    def open_selected_company_section", 1)[0]
        for block in (child_manager, profile, selected):
            self.assertNotIn("self.promotion_strategy(", block)
        self.assertIn("promotion_strategy_read_model", child_manager + profile + selected)

    def test_decision_pack_refresh_is_projection_only(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        refresh = source.split("    def refresh_scouting_decision_packs(self):", 1)[1].split("    def selected_scouting_decision_pack", 1)[0]
        self.assertIn("_scouting_decision_pack_view_identity", refresh)
        self.assertIn("not isinstance(pack, dict)", refresh)
        self.assertNotIn("ensure_scouting_decision_packs()", refresh)

    def test_scouting_readers_do_not_migrate_on_refresh(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        target_refresh = source.split("    def refresh_scouting_targets(self):", 1)[1].split("    def refresh_scouting_decision_packs", 1)[0]
        center_refresh = source.split("    def refresh_scouting_center(self):", 1)[1].split("    def scouting_week_label", 1)[0]
        self.assertNotIn("migrate_scouting_state()", target_refresh)
        self.assertNotIn("migrate_scouting_state()", center_refresh)
        self.assertIn("migrate=False", target_refresh)
        self.assertIn("isinstance(report, dict)", center_refresh)

    def test_fighter_search_uses_read_only_history_baseline(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        search_record = source.split("    def world_fighter_universe_record", 1)[1].split("    def world_fighter_last_five", 1)[0]
        self.assertIn("fighter_history_baseline_for_profile", search_record)
        self.assertNotIn("ensure_fighter_history_baseline", search_record)

    def test_fighter_search_source_projection_skips_malformed_collections(self):
        harness = object.__new__(ViewHarness)
        harness.player_company_name = "Player FC"
        player = SimpleNamespace(name="Player", fighter_id="player-1")
        sport = SimpleNamespace(name="Sport", fighter_id="sport-1", sport_employer="", primary_discipline="Boxing")
        retired = SimpleNamespace(name="Retired", fighter_id="retired-1")
        harness.roster = ["bad roster row", player]
        harness.free_agents = "bad free-agent envelope"
        harness.promotions = [SimpleNamespace(name="Broken Promotion", roster="bad roster"), "bad promotion"]
        harness.combat_sport_worlds = {"Boxing": "bad world", "Kickboxing": {"roster": [sport]}}
        harness.retired_fighters = [None, retired]
        rows = ViewMixin.all_database_fighters_with_companies(harness)
        self.assertEqual([(company, fighter.name) for company, fighter in rows], [
            ("Player FC", "Player"), ("Kickboxing", "Sport"), ("Retired", "Retired"),
        ])
        malformed = SimpleNamespace(
            record_w=float("inf"), record_l=float("nan"), record_d="bad",
            record_history_baseline_w="bad", record_history_baseline_l=True,
            record_history_baseline_d=float("inf"), bout_rating_history="bad",
        )
        self.assertEqual(ViewMixin.world_fighter_universe_record(harness, malformed), "0-0-0")
        self.assertEqual(ViewMixin.world_fighter_last_five(harness, malformed), "-")

    def test_fighter_search_rows_use_source_identity_across_pages(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        identity = source.split("    def world_fighter_search_row_identity", 1)[1].split("    def world_fighter_universe_record", 1)[0]
        refresh = source.split("    def refresh_world_fighter_search", 1)[1].split("    def open_selected_world_fighter_profile", 1)[0]
        self.assertIn("fighter_id", identity)
        self.assertIn("legacy-fighter-search", identity)
        for marker in ("previous_key", "used_row_ids", "world_fighter_search_row_identity", "selection_set", "_world_fighter_search_selected_key"):
            self.assertIn(marker, refresh)
        self.assertNotIn("item_id = str(index)", refresh)
        fighter = SimpleNamespace(fighter_id="fighter-7", name="Same Name")
        self.assertEqual(
            ViewMixin.world_fighter_search_row_identity("Alpha", fighter),
            ViewMixin.world_fighter_search_row_identity("Alpha", fighter),
        )
        self.assertNotEqual(
            ViewMixin.world_fighter_search_row_identity("Alpha", fighter),
            ViewMixin.world_fighter_search_row_identity("Beta", fighter),
        )
        legacy = SimpleNamespace(name="Legacy", gender="Male", weight="Lightweight", region="USA", nationality="USA", age=27, record="4-1")
        self.assertTrue(ViewMixin.world_fighter_search_row_identity("Alpha", legacy).startswith("legacy-fighter-search:"))

    def test_results_reader_keeps_malformed_rows_visible(self):
        rows = ViewMixin.result_reader_rows(["malformed-result", {"record_id": "R-1", "event": "Recorded"}])
        self.assertEqual(rows[0]["_read_status"], "Unavailable")
        self.assertEqual(rows[0]["_read_index"], 0)
        self.assertEqual(rows[1]["record_id"], "R-1")

    def test_results_detail_reader_bounds_malformed_dates_without_dropping_card(self):
        harness = object.__new__(ViewHarness)
        harness.result_record_with_compact_bouts = lambda record: record
        harness.result_bout_lines = lambda _record: ["Month Infinity Week NaN"]
        harness.format_game_date_text = lambda _value: (_ for _ in ()).throw(OverflowError("bad date"))
        text = ViewMixin.result_card_text(harness, {"summary": "Month Infinity", "log": "bad"})
        self.assertIn("Unknown date", text)
        source = inspect.getsource(ViewMixin.refresh_results)
        self.assertIn("def safe_result_date(value)", source)

    def test_company_standings_selection_keeps_sport_scope(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        refresh = source.split("    def refresh_companies(self):", 1)[1].split("    def _write_company_profile", 1)[0]
        self.assertIn("previous = self.company_selected_identity()", refresh)
        self.assertIn("self.select_company_by_identity(previous)", refresh)
        self.assertIn("def company_selected_identity", source)
        self.assertIn("def select_company_by_identity", source)

    def test_company_standings_rows_keep_duplicate_entities_separate(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        refresh = source.split("    def refresh_companies(self):", 1)[1].split("    def _write_company_profile", 1)[0]
        standings = source.split("    def industry_standings_rows(self):", 1)[1].split("    @staticmethod\n    def standings_history_key", 1)[0]
        for marker in ("company_selected_row_identity", "entity_id", "standings_row_id", "source_ref", "used_row_ids"):
            self.assertIn(marker, source if marker in ("company_selected_row_identity", "standings_row_id") else refresh + standings)
        self.assertNotEqual(ViewMixin.standings_history_key("MMA", "Same Name", "promotion:one"),
                            ViewMixin.standings_history_key("MMA", "Same Name", "promotion:two"))
        self.assertEqual(ViewMixin.standings_row_id({"sport": "MMA", "name": "Same Name", "entity_id": "promotion:one"}),
                         "MMA|id:promotion:one")
        self.assertNotEqual(ViewMixin.standings_row_id({"sport": "MMA", "name": "Same Name", "entity_id": "promotion:one"}),
                            ViewMixin.standings_row_id({"sport": "MMA", "name": "Same Name", "entity_id": "promotion:two"}))

    def test_company_standings_reader_projects_combat_sport_state_without_repair(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        standings = source.split("    def industry_standings_rows(self):", 1)[1].split("    @staticmethod\n    def standings_history_key", 1)[0]
        selected = source.split("    def selected_company_data(self):", 1)[1].split("    def open_selected_company_section", 1)[0]
        self.assertGreaterEqual(standings.count("repair=False"), 2)
        self.assertIn("repair=False", selected)

    def test_selected_combat_company_reader_fails_closed_for_malformed_envelopes(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        selected = source.split("    def selected_company_data(self):", 1)[1].split("    def open_selected_company_section", 1)[0]
        for marker in ("raw_world", "raw_division", "read_status", "safe_int", "safe_list", "safe_mapping", "safe_fighter_list", "fighter_fields", "roster_incomplete"):
            self.assertIn(marker, selected)
        world_source = (Path(__file__).parent / "world.py").read_text(encoding="utf-8")
        roster = world_source.split("    def combat_sport_roster(self, sport, employer=None):", 1)[1].split("    def combat_sport_for_fighter", 1)[0]
        self.assertIn("isinstance(world, dict)", roster)
        harness = WorldMixin.__new__(WorldMixin)
        harness.combat_sport_worlds = {"Boxing": "malformed"}
        self.assertEqual(harness.combat_sport_roster("Boxing"), [])

    def test_company_card_archive_uses_promotion_identity_for_duplicate_names(self):
        source = (Path(__file__).parent / "views.py").read_text(encoding="utf-8")
        helper = source.split("    def _selected_company_archive_package", 1)[1].split("    def view_selected_company_card", 1)[0]
        for marker in ("promotion_id", "source_company_id", "fail closed", "same_name"):
            self.assertIn(marker, helper)
        world_source = (Path(__file__).parent / "world.py").read_text(encoding="utf-8")
        self.assertIn('"promotion_id": str(getattr(promo, "promotion_id", "") or "")', world_source)

        harness = ViewMixin.__new__(ViewMixin)
        harness._standings_rows_by_key = {
            "MMA|id:promotion:one": {"name": "Same Name", "sport": "MMA", "entity_id": "promotion:one"},
            "MMA|id:promotion:two": {"name": "Same Name", "sport": "MMA", "entity_id": "promotion:two"},
        }
        packages = [
            {"company": "Same Name", "promotion_id": "one", "event_name": "One Card"},
            {"company": "Same Name", "promotion_id": "two", "event_name": "Two Card"},
        ]
        selected = {"name": "Same Name", "sport": "MMA", "entity_id": "promotion:two"}
        self.assertEqual(
            harness._selected_company_archive_package(packages, selected)["event_name"],
            "Two Card",
        )
        self.assertIsNone(
            harness._selected_company_archive_package(
                [{"company": "Same Name", "event_name": "Legacy Card"}], selected,
            )
        )


class AcademyAndCombatSportsTabTests(unittest.TestCase):
    """Academy and Combat Sports are main notebook pages, not popups."""

    @classmethod
    def setUpClass(cls):
        root = Path(__file__).parent
        cls.ui_source = (root / "ui.py").read_text(encoding="utf-8")
        cls.views_source = (root / "views.py").read_text(encoding="utf-8")

    def test_both_screens_are_registered_as_notebook_pages(self):
        self.assertIn('("academy", "academy_tab", "Fight Academy")', self.ui_source)
        self.assertIn('("combat_sports", "combat_sports_tab", "Combat Sports")', self.ui_source)
        self.assertIn('"academy": self.build_academy_tab,', self.ui_source)
        self.assertIn('"combat_sports": self.build_combat_sports_tab,', self.ui_source)

    def test_navigation_no_longer_special_cases_the_two_screens(self):
        self.assertNotIn("self.open_combat_sports_window if tab ==", self.ui_source)
        self.assertNotIn("self.open_academy_window if tab ==", self.ui_source)

    def test_select_tab_routes_through_the_page_registry(self):
        # A hand-maintained lookup was a second place to forget a new screen.
        self.assertIn("page = self.tab_pages.get(name)", self.ui_source)

    def test_builders_exist_and_primary_workspaces_open_no_toplevel(self):
        for name in ("build_academy_tab", "render_academy_screen", "build_combat_sports_tab",
                     "refresh_academy_tab", "refresh_combat_sports_tab"):
            self.assertTrue(hasattr(ViewMixin, name), f"{name} is missing from ViewMixin")
        for opener in ("open_academy_window", "open_combat_sports_window"):
            body = self._method_source(opener)
            self.assertIn("self.select_tab(", body, f"{opener} should route to a tab")
            self.assertNotIn("tk.Toplevel", body, f"{opener} must not open a window")

    def test_primary_workspaces_build_into_their_page(self):
        # Retained detail popups (prospect profiles, replays) may still create a
        # Toplevel; what must not happen is the workspace itself being one.
        combat = self._method_source("build_combat_sports_tab")
        self.assertIn("window = self.combat_sports_tab", combat)
        self.assertNotIn("window = tk.Toplevel", combat)
        academy = self._method_source("render_academy_screen")
        self.assertIn('parent = getattr(self, "academy_tab", None)', academy)
        self.assertIn('window = ttk.Frame(parent, style="Chrome.TFrame")', academy)
        self.assertNotIn("window = tk.Toplevel", academy)
        self.assertNotIn("window.protocol(", academy, "a page has no window-close protocol")
        self.assertNotIn("window.geometry(", academy, "a page has no window geometry")

    def test_academy_empty_state_price_check_is_live(self):
        # The panel stays on screen for as long as the player has no academy,
        # so reading cash once at construction froze it (it reported $0 forever)
        # and left the build button stuck at its original enabled state.
        empty = self._method_source("build_academy_empty_state")
        self.assertIn("self._academy_empty_refresh = refresh_empty_state", empty)
        self.assertIn('build_button.state(["!disabled"] if affordable else ["disabled"])', empty)
        refresh = self._method_source("refresh_academy_tab")
        self.assertIn('getattr(self, "_academy_empty_refresh", None)', refresh)
        self.assertIn(
            'if getattr(self, "_academy_window", None) is not None or getattr(self, "_academy_empty_refresh", None) is not None:',
            self.views_source, "refresh_all must also refresh a page showing the empty state")

    def test_academy_empty_state_does_not_stretch_the_page(self):
        empty = self._method_source("build_academy_empty_state")
        self.assertIn("wraplength=660", empty)
        self.assertNotIn('.pack(fill="both", expand=True, padx=18, pady=18)', empty)

    def test_academy_rival_program_reader_does_not_seed_saved_strategy(self):
        refresh = self.views_source.split("    def render_academy_screen(self):", 1)[1].split("    def refresh_academy_tab", 1)[0]
        self.assertIn("rival_academy_program(item, repair=False)", refresh)
        promo = SimpleNamespace(
            name="Legacy Rival", size=55, reputation_score=64, region="USA", strategy={},
        )
        before = deepcopy(vars(promo))
        program = WorldMixin.rival_academy_program(WorldMixin(), promo, repair=False)
        self.assertTrue(program.get("name"))
        self.assertEqual(before, vars(promo))

    def test_refresh_routes_exist_for_both_pages(self):
        self.assertIn('"academy": (self.refresh_academy_tab,),', self.views_source)
        self.assertIn('"combat_sports": (self.refresh_combat_sports_tab,),', self.views_source)

    def test_full_refresh_does_not_construct_unopened_pages(self):
        # refresh_current_screen builds a screen on demand, so listing these two
        # in the full sweep would create their widgets for a player who has
        # never opened them.
        full_sweep = self.views_source.split("if full:", 1)[1].split("else:", 1)[0]
        self.assertNotIn('"academy"', full_sweep)
        self.assertNotIn('"combat_sports"', full_sweep)
        self.assertTrue('_academy_window", None) is not None' in self.views_source)
        self.assertTrue('if getattr(self, "_combat_sports_redraw", None) is not None:' in self.views_source)

    def _method_source(self, name):
        marker = f"    def {name}(self"
        self.assertIn(marker, self.views_source, f"{name} not found in views.py")
        body = self.views_source.split(marker, 1)[1]
        return body.split("\n    def ", 1)[0]


class NativeDialogInventoryTests(unittest.TestCase):
    """Keep routine information dialogs behind their owning page surfaces.

    A direct ``showinfo`` is intentionally still retained for headless/legacy
    callers, but the normal desktop path must first offer a page status line or
    managed reader.  This inventory makes a new routine popup an explicit
    review item instead of allowing it to slip back into the UI unnoticed.
    """

    MODULES = ("views.py", "events.py", "persistence.py", "database_editor.py", "ui.py")

    # (module, qualified function, method, title): source marker proving the
    # normal path has an owning surface (or is a deliberate headless reader
    # fallback).  Counts below preserve duplicate calls in one function.
    ROUTINE_INFO = {
        ("views.py", "open_selected_world_story_reader", "showinfo", "World News"): ("world_news_detail", 1),
        ("views.py", "open_superfight_night_window", "showinfo", "Superfight Night"): ("world_next_step_summary", 1),
        ("views.py", "open_player_combat_division_window", "showinfo", "Combat Sports"): ("combat_sports_overview_status", 1),
        ("views.py", "open_selected_gym_viewer", "showinfo", "Gym Viewer"): ("world_context_vars", 1),
        ("views.py", "open_weekly_narrative_digest", "showinfo", "Week in Stories"): ("website_news_preview", 1),
        ("views.py", "open_story_reader", "showinfo", "Media Desk"): ("website_news_preview", 1),
        ("views.py", "legacy_media_desk_callout", "showinfo", "Media Desk"): ("_media_campaign_notice", 1),
        ("views.py", "legacy_media_desk_interview", "showinfo", "Media Desk"): ("_media_campaign_notice", 1),
        ("views.py", "legacy_media_desk_press_tour", "showinfo", "Media Desk"): ("_media_campaign_notice", 1),
        ("views.py", "open_selected_staff_profile", "showinfo", "Staff Profile"): ('not hasattr(self, "root")', 1),
        ("views.py", "media_callout_selected", "showinfo", "Media Callout"): ("_media_campaign_notice", 1),
        ("views.py", "choose_camp_focus_selected", "showinfo", "Camp Plan"): ("_roster_status_notice", 1),
        ("views.py", "open_editor_selected_profile", "showinfo", "Current Career Editor"): ("_editor_status_notice", 1),
        ("views.py", "retire_database_editor_fighter", "showinfo", "Current Career Editor"): ("_editor_status_notice", 1),
        ("views.py", "open_detailed_skill_editor", "showinfo", "Detailed Skill Editor"): ("_editor_status_notice", 1),
        ("events.py", "open_contract_negotiation", "showinfo", "Contract unavailable"): ("_market_status_notice", 1),
        ("events.py", "open_negotiation", "showinfo", "Negotiations"): ("_market_status_notice", 2),
        ("events.py", "run_event", "showinfo", "No fights"): ("set_schedule_status", 1),
        ("events.py", "open_event_tournament_bracket", "showinfo", "Tournament Bracket"): ("_results_status_notice", 1),
        ("persistence.py", "save_game", "showinfo", "Saved"): ("_save_surface_notice", 1),
        ("persistence.py", "load_game", "showinfo", "No save"): ("_save_surface_notice", 1),
        ("persistence.py", "use_selected_universe_database", "showinfo", "Universe Database"): ("_save_surface_notice", 1),
        ("persistence.py", "use_selected_universe_database", "showinfo", "Universe Selected"): ("_save_surface_notice", 1),
        ("persistence.py", "clone_selected_universe_database", "showinfo", "Universe Cloned"): ("_save_surface_notice", 1),
        ("persistence.py", "reset_default_universe_database", "showinfo", "Default Universe Ready"): ("_save_surface_notice", 1),
        ("persistence.py", "open_database_folder", "showinfo", "Database Folder"): ("_save_surface_notice", 1),
        ("persistence.py", "validate_active_universe_database", "showinfo", "Universe Validation"): ("_save_surface_notice", 1),
        ("persistence.py", "save_selected_slot", "showinfo", "Save name required"): ("_save_surface_notice", 1),
        ("persistence.py", "migrate_selected_save_archetypes", "showinfo", "Career profile migration"): ("_save_surface_notice", 1),
        ("persistence.py", "migrate_selected_save_archetypes", "showinfo", "Career profiles migrated"): ("_save_surface_notice", 1),
        ("persistence.py", "load_selected_slot", "showinfo", "No save"): ("_save_surface_notice", 1),
        ("persistence.py", "delete_selected_slot", "showinfo", "No save"): ("_save_surface_notice", 1),
        ("persistence.py", "backup_selected_slot", "showinfo", "No save"): ("_save_surface_notice", 1),
        ("persistence.py", "backup_selected_slot", "showinfo", "Backup Created"): ("_save_surface_notice", 1),
        ("persistence.py", "open_saves_folder", "showinfo", "Saves Folder"): ("_save_surface_notice", 1),
        ("persistence.py", "open_save_backup_manager::restore_backup", "showinfo", "Restore Backup"): ("_save_surface_notice", 1),
        ("persistence.py", "open_save_backup_manager::restore_backup", "showinfo", "Backup Restored"): ("_save_surface_notice", 1),
        ("persistence.py", "open_pinned_checkpoint_manager::restore_selected", "showinfo", "Restore checkpoint"): ("_save_surface_notice", 1),
        ("persistence.py", "open_pinned_checkpoint_manager::restore_selected", "showinfo", "Checkpoint restored"): ("_save_surface_notice", 1),
        ("persistence.py", "open_pinned_checkpoint_manager::delete_selected", "showinfo", "Delete checkpoint"): ("_save_surface_notice", 1),
        ("persistence.py", "export_database", "showinfo", "Database Exported"): ("_save_surface_notice", 1),
        ("persistence.py", "convert_career_to_database", "showinfo", "Career database created"): ("_save_surface_notice", 1),
        ("persistence.py", "import_quick_save_as_database", "showinfo", "No quick save"): ("_save_surface_notice", 1),
        ("persistence.py", "import_quick_save_as_database", "showinfo", "Database Imported"): ("_save_surface_notice", 1),
        ("persistence.py", "load_selected_database", "showinfo", "No database"): ("_save_surface_notice", 1),
        ("persistence.py", "load_selected_database", "showinfo", "Universe Loaded"): ("_save_surface_notice", 1),
        ("persistence.py", "load_selected_database", "showinfo", "Database Loaded"): ("_save_surface_notice", 1),
        ("database_editor.py", "apply_quick_fighter_fields", "showinfo", "No fighter selected"): ("_editor_notice", 1),
        ("database_editor.py", "apply_signature_moves", "showinfo", "No fighter selected"): ("_editor_notice", 1),
        ("database_editor.py", "apply_core_ratings", "showinfo", "No fighter selected"): ("_editor_notice", 1),
        ("database_editor.py", "use_suggested_overall", "showinfo", "No fighter selected"): ("_editor_notice", 1),
        ("database_editor.py", "materialize_opening_profile", "showinfo", "No fighter selected"): ("_editor_notice", 1),
        ("database_editor.py", "apply_skill_sheet", "showinfo", "No fighter selected"): ("_editor_notice", 1),
        ("database_editor.py", "open_database_folder", "showinfo", "Database folder"): ("_editor_notice", 1),
        ("database_editor.py", "ensure_database_loaded", "showinfo", "No database selected"): ("_editor_notice", 1),
        ("database_editor.py", "apply_field", "showinfo", "No record selected"): ("_editor_notice", 1),
        ("database_editor.py", "apply_raw_record", "showinfo", "No record selected"): ("_editor_notice", 1),
        ("database_editor.py", "apply_bulk", "showinfo", "Nothing to edit"): ("_editor_notice", 1),
        ("database_editor.py", "duplicate_fighter", "showinfo", "No fighter selected"): ("_editor_notice", 1),
        ("database_editor.py", "duplicate_company", "showinfo", "No company selected"): ("_editor_notice", 1),
        ("ui.py", "staff_open_selected_work_receipt", "showinfo", "Staff receipt"): ("_staff_status_notice", 2),
    }

    @classmethod
    def _calls(cls):
        calls = []
        for module in cls.MODULES:
            source = Path(module).read_text(encoding="utf-8")
            tree = ast.parse(source, filename=module)

            class Visitor(ast.NodeVisitor):
                def __init__(self):
                    self.stack = []
                    self.function_sources = {}

                def visit_FunctionDef(self, node):
                    self.stack.append(node.name)
                    self.function_sources["::".join(self.stack)] = ast.get_source_segment(source, node) or ""
                    self.generic_visit(node)
                    self.stack.pop()

                visit_AsyncFunctionDef = visit_FunctionDef

                def visit_Call(self, node):
                    fn = node.func
                    if (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name)
                            and fn.value.id == "messagebox"):
                        title = node.args[0].value if node.args and isinstance(node.args[0], ast.Constant) else ""
                        calls.append({
                            "key": (module, "::".join(self.stack) or "<module>", fn.attr, title),
                            "source": self.function_sources.get("::".join(self.stack), ""),
                        })
                    self.generic_visit(node)

            Visitor().visit(tree)
        return calls

    def test_routine_info_dialogs_have_owned_surface_inventory(self):
        calls = self._calls()
        actual = Counter(item["key"] for item in calls if item["key"][2] == "showinfo")
        expected = Counter({key: value[1] for key, value in self.ROUTINE_INFO.items()})
        self.assertEqual(actual, expected, "A new direct information popup needs an explicit owning-surface entry")
        for key, (marker, _count) in self.ROUTINE_INFO.items():
            matching = [item for item in calls if item["key"] == key]
            self.assertTrue(matching, key)
            self.assertTrue(all(marker in item["source"] for item in matching), f"{key} lost its surface guard")

    def test_only_fight_day_keeps_a_native_three_way_choice_and_it_is_headless_guarded(self):
        calls = self._calls()
        choices = [item for item in calls if item["key"][2] == "askyesnocancel"]
        self.assertEqual(
            [item["key"] for item in choices],
            [("events.py", "prompt_due_event", "askyesnocancel", "Fight Day")],
        )
        self.assertIn('not hasattr(self, "create_managed_window")', choices[0]["source"])

    def test_status_helper_fallbacks_are_the_only_dynamic_messagebox_routes(self):
        """Dynamic info/warning selection belongs only to compatibility helpers."""
        expected = {
            ("views.py", name)
            for name in (
                "_contract_status_notice", "_roster_status_notice", "_transfer_status_notice",
                "_company_status_notice", "_staff_status_notice", "_company_editor_status_notice",
                "_results_status_notice", "_scouting_status_notice", "_market_status_notice",
                "_world_search_status_notice",
            )
        } | {("persistence.py", "_company_takeover_notice")}
        actual = set()
        helper_sources = {}
        for module in self.MODULES:
            source = Path(module).read_text(encoding="utf-8")
            tree = ast.parse(source, filename=module)
            stack = []

            class Visitor(ast.NodeVisitor):
                def visit_FunctionDef(self, node):
                    stack.append(node.name)
                    helper_sources[(module, node.name)] = ast.get_source_segment(source, node) or ""
                    self.generic_visit(node)
                    stack.pop()

                visit_AsyncFunctionDef = visit_FunctionDef

                def visit_Call(self, node):
                    fn = node.func
                    messagebox_attrs = [
                        item for item in ast.walk(fn)
                        if isinstance(item, ast.Attribute)
                        and isinstance(item.value, ast.Name)
                        and item.value.id == "messagebox"
                    ]
                    direct = (
                        isinstance(fn, ast.Attribute)
                        and isinstance(fn.value, ast.Name)
                        and fn.value.id == "messagebox"
                    )
                    if messagebox_attrs and not direct:
                        actual.add((module, stack[-1] if stack else "<module>"))
                    self.generic_visit(node)

            Visitor().visit(tree)
        self.assertEqual(actual, expected, "A new dynamic messagebox route needs an explicit compatibility review")
        for key in expected:
            self.assertIn("messagebox.showwarning if warning else messagebox.showinfo", helper_sources[key])


if __name__ == "__main__":
    unittest.main(verbosity=2)
