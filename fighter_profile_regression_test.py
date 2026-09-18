"""Focused headless regressions for fighter Profile identity and action safety."""

import copy
import inspect
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from admin import AdminMixin
from constants import DETAILED_SKILL_GROUPS
from events import EventMixin
from models import Fighter
from seeding import SeedMixin
from views import ViewMixin
from world import WorldMixin
from fighter_profile_overview import bounded_profile_metric, build_overview, compare_fighter_row_identity


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


class MembershipTimelineHarness(ViewMixin):
    def foundation_membership_intervals(self, *, fighter_id="", limit=8, **_kwargs):
        return [{
            "promotion_name": "Alpha", "promotion_id": "promo-1",
            "start_month": None, "start_week": None, "start_precision": "migration",
            "end_month": 12, "end_week": 2, "end_precision": "week",
            "coverage": "incomplete", "start_source": "migration:known-present:v1:player:f-1",
            "end_source": "contract-exit:f-1:Alpha:12:2",
        }]

    def format_game_date(self, month, week, include_week=True):
        return f"Month {month} Week {week}" if include_week else f"Month {month}"


class FighterProfileRegressionTests(unittest.TestCase):
    def test_profile_rating_grades_keep_visual_bands_stable(self):
        self.assertEqual("WEAK", ViewMixin.profile_rating_grade(49))
        self.assertEqual("DEVELOPING", ViewMixin.profile_rating_grade(50))
        self.assertEqual("GOOD", ViewMixin.profile_rating_grade(65))
        self.assertEqual("EXCELLENT", ViewMixin.profile_rating_grade(78))
        self.assertEqual("ELITE", ViewMixin.profile_rating_grade(88))

    def test_profile_technical_pages_use_dashboard_cards(self):
        source = inspect.getsource(ViewMixin.open_fighter_profile_window)
        self.assertEqual(2, source.count("self.build_profile_skill_page("))
        self.assertIn('"Contract & business"', source)

    def test_remaining_profile_tabs_share_dashboard_language(self):
        source = inspect.getsource(ViewMixin.open_fighter_profile_window)
        self.assertIn('"Official dossier", "Identity & career"', source)
        self.assertIn('"Career trajectory", "Development"', source)
        self.assertIn('"Official ledger", "Fight history"', source)
        self.assertIn('"COMPANY TIMELINE"', source)
        self.assertIn('fighter_membership_timeline_rows(fighter)', source)
        self.assertIn('style="Profile.Treeview"', source)
        self.assertIn('"Corner briefing", "Overview"', inspect.getsource(build_overview))

    def test_overview_uses_visual_career_pulse_and_skill_assessment(self):
        source = inspect.getsource(build_overview)
        self.assertIn('"Momentum"', source)
        self.assertIn('"Readiness"', source)
        self.assertIn('"RECENT FORM • LAST FIVE"', source)
        self.assertIn('"BEST → DEVELOPMENT FOCUS"', source)
        self.assertIn("profile_rating_color", source)

    def test_overview_projects_malformed_pulse_values_without_mutation(self):
        self.assertEqual(50, bounded_profile_metric(float("nan"), default=50))
        self.assertEqual(0, bounded_profile_metric(float("inf")))
        self.assertEqual(0, bounded_profile_metric("not-a-number"))
        self.assertEqual(10, bounded_profile_metric(999, low=-10, high=10))
        source = inspect.getsource(build_overview)
        for marker in ("momentum_value", "morale_value", "fatigue_value", "bounded_profile_metric", "activity_value"):
            self.assertIn(marker, source)

    def test_compare_picker_binds_rows_to_stable_fighter_identity(self):
        first = fighter("Same Name", "FTR-compare-1")
        second = fighter("Same Name", "FTR-compare-2")
        self.assertNotEqual(compare_fighter_row_identity(first), compare_fighter_row_identity(second))
        legacy_a = fighter("Legacy", "", nationality="USA")
        legacy_b = fighter("Legacy", "", nationality="CAN")
        self.assertNotEqual(compare_fighter_row_identity(legacy_a), compare_fighter_row_identity(legacy_b))
        source = inspect.getsource(__import__("fighter_profile_overview").compare_picker)
        self.assertIn("compare_fighter_row_identity", source)
        self.assertIn("used_row_ids", source)
        self.assertIn("previous_row_id", source)
        self.assertNotIn('key = str(len(visible))', source)

    def test_development_reader_projects_malformed_evidence_without_mutation(self):
        app = ProfileHarness()
        target = fighter("Development Target", "FTR-development")
        target.potential = 86
        target.development_log = [{"after": float("nan"), "reason": "retained"}, "broken history row"]
        target.camp_history = ["broken camp row"]
        before = copy.deepcopy(target.__dict__)
        app.fighter_development_explanation = lambda _fighter: {"score": float("inf"), "outlook": None}
        app.fighter_development_factors = lambda _fighter: [("Gym quality", 4), ("Malformed", float("nan")), "broken factor"]
        projection = app.development_reader_projection(target)
        self.assertEqual(projection["score"], 0.0)
        self.assertEqual(projection["overall"], float(target.overall))
        self.assertEqual(projection["potential"], 86.0)
        self.assertEqual(projection["factors"][1][1], 0.0)
        self.assertEqual(projection["factors"][2][0], "Unavailable factor")
        self.assertIn(projection["score_band"], {"Strong tailwind", "Stable", "Limited", "Declining"})
        self.assertGreaterEqual(projection["potential_gap"], 0.0)
        self.assertIn("not a guaranteed", projection["score_note"])
        self.assertTrue(projection["recent_changes"])
        self.assertTrue(projection["history"][1]["_read_status"])
        self.assertTrue(projection["camp_history"][0]["_read_status"])
        self.assertEqual(before, target.__dict__)
        source = inspect.getsource(ViewMixin.development_reader_projection)
        self.assertIn("never write the fighter", source)
        self.assertIn("Unavailable retained", source)

    def test_development_tab_explains_outlook_and_recent_changes(self):
        source = inspect.getsource(ViewMixin.open_fighter_profile_window)
        for marker in ("Monthly outlook", "Ceiling gap", "score_note", "Recent recorded changes", "Signed drivers"):
            self.assertIn(marker, source)

    def test_pre_bout_history_freezes_company_and_world_ranks_for_both_fighters(self):
        app = ProfileHarness()
        first = fighter("First", "FTR-first", record_w=14, record_l=1, striking=84)
        second = fighter("Second", "FTR-second", record_w=10, record_l=3, striking=76)
        third = fighter("Third", "FTR-third", record_w=4, record_l=5, striking=62)
        app.roster = [first, second, third]

        app.record_bout_rating_history(first, second, "W", "L", {})

        first_entry = first.bout_rating_history[0]
        second_entry = second.bout_rating_history[0]
        self.assertEqual(app.player_company_name, first_entry["self_company"])
        self.assertTrue(first_entry["self_company_rank"].startswith("#"))
        self.assertTrue(first_entry["self_world_rank"].startswith("#"))
        self.assertEqual(first_entry["self_company_rank"], second_entry["opponent_company_rank"])
        self.assertEqual(second_entry["self_world_rank"], first_entry["opponent_world_rank"])

    def test_history_column_registry_includes_rank_and_extensible_views(self):
        source = inspect.getsource(ViewMixin.open_fighter_profile_window)
        for column in ("fighter_company_rank", "fighter_world_rank", "opponent_company_rank", "opponent_world_rank"):
            self.assertIn(f'(\"{column}\",', source)
        self.assertIn('history_tree.configure(displaycolumns=selected)', source)
        self.assertIn('self.rules["ui_fighter_history_columns"]', source)
        self.assertIn('self.rules["ui_fighter_history_column_layout"]', source)
        self.assertIn('history_column_widths', source)
        self.assertIn('"Move Up"', source)
        self.assertIn('"Move Down"', source)
        self.assertIn('"Selected width"', source)
        self.assertIn('persist_history_layout_from_tree', source)
        self.assertIn('identify_region(event.x, event.y) == "heading"', source)
        self.assertIn('"Choose Columns"', source)
        self.assertIn('"Open full history"', source)
        history_source = inspect.getsource(ViewMixin.open_fighter_membership_history_window)
        self.assertIn('json.dumps(row, sort_keys=True', history_source)
        self.assertNotIn('return f"legacy-history:{index + 1}"', history_source)
        self.assertIn('"Export JSON"', history_source)
        self.assertIn('as_of_month=target_month', history_source)

    def test_membership_timeline_labels_unknown_migration_coverage(self):
        rows = MembershipTimelineHarness().fighter_membership_timeline_rows(
            SimpleNamespace(fighter_id="f-1"), limit=1,
        )
        self.assertEqual(rows[0]["company"], "Alpha")
        self.assertEqual(rows[0]["from"], "Known present at migration")
        self.assertEqual(rows[0]["coverage"], "Coverage incomplete")

    def test_membership_timeline_keeps_authoritative_source_identity(self):
        class IdentityTimelineHarness(MembershipTimelineHarness):
            def foundation_membership_intervals(self, **_kwargs):
                return [{
                    "promotion_name": "Alpha", "promotion_id": "promo-1",
                    "start_month": 2, "start_week": 1, "start_precision": "week",
                    "end_month": None, "end_week": None, "end_precision": "open",
                    "coverage": "complete", "start_source": "join-source",
                    "end_source": "", "start_membership_id": "membership-start",
                    "start_event_id": "event-start", "end_membership_id": "",
                    "end_event_id": "",
                }]

        row = IdentityTimelineHarness().fighter_membership_timeline_rows(
            SimpleNamespace(fighter_id="f-1"), limit=1,
        )[0]
        self.assertEqual(row["membership_id"], "membership-start")
        self.assertEqual(row["event_id"], "event-start")

    def test_membership_timeline_fails_closed_for_malformed_reader_rows(self):
        class MalformedTimelineHarness(MembershipTimelineHarness):
            def foundation_membership_intervals(self, **_kwargs):
                return [None, {"promotion_name": "Alpha", "coverage": "complete",
                               "start_month": 2, "start_week": 1,
                               "end_month": None, "end_week": None}, "legacy row"]

        app = MalformedTimelineHarness()
        before = copy.deepcopy(app.__dict__)
        rows = app.fighter_membership_timeline_rows(SimpleNamespace(fighter_id="f-1"), limit=8)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["company"], "Alpha")
        self.assertEqual(before, app.__dict__)

        class MalformedEnvelopeHarness(MembershipTimelineHarness):
            def foundation_membership_intervals(self, **_kwargs):
                return {"legacy": "envelope"}

        self.assertEqual(
            MalformedEnvelopeHarness().fighter_membership_timeline_rows(
                SimpleNamespace(fighter_id="f-1"), limit=8,
            ),
            [],
        )

    def test_title_history_projection_uses_stable_fighter_identity(self):
        app = ProfileHarness()
        target = fighter("Alex Smith", "FTR-title-target")
        rival = fighter("Alex Smith", "FTR-title-rival")
        app.roster = [target, rival]
        app.belt_history = {
            "Male Lightweight": [
                {"date": "Month 6 Week 1", "action": "Champion Crowned", "fighter": target.name,
                 "fighter_id": target.fighter_id, "note": "Won the title."},
                {"date": "Month 5 Week 1", "action": "Champion Crowned", "fighter": rival.name,
                 "fighter_id": rival.fighter_id, "note": "Other title event."},
            ]
        }
        rows = app.fighter_title_history_rows(target)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["fighter_id"], target.fighter_id)
        self.assertEqual(rows[0]["coverage"], "Recorded ID")

    def test_title_history_projection_preserves_archived_opponent_identity(self):
        app = ProfileHarness()
        target = fighter("Target", "FTR-title-target")
        opponent = fighter("Opponent", "FTR-title-opponent")
        app.roster = [target, opponent]
        app.belt_history = {
            "Male Lightweight": [{
                "date": "Month 6 Week 1", "action": "Title Defense",
                "fighter": target.name, "fighter_id": target.fighter_id,
                "opponent": opponent.name, "opponent_id": opponent.fighter_id,
                "note": "Defeated Opponent by Decision.",
            }]
        }

        row = app.fighter_title_history_rows(target)[0]

        self.assertEqual(row["opponent"], opponent.name)
        self.assertEqual(row["opponent_id"], opponent.fighter_id)

    def test_title_history_reader_fails_closed_for_malformed_containers_and_limit(self):
        app = ProfileHarness()
        target = fighter("Target", "FTR-title-reader")
        app.roster = [target]
        app.belt_history = {
            "Male Lightweight": "malformed history entries",
            "Male Welterweight": {"legacy": "not a list"},
        }
        before = repr(app.belt_history)

        rows = app.fighter_title_history_rows(target, limit=float("nan"))

        self.assertEqual(rows, [])
        self.assertEqual(before, repr(app.belt_history))

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

    def test_missing_historical_opponent_record_does_not_use_today_record(self):
        app = ProfileHarness()
        target = fighter("Target", "FTR-target", record_w=4, record_l=2)
        opponent = fighter("Opponent", "FTR-opponent", record_w=30, record_l=0)
        app.roster = [target, opponent]
        context = app.fighter_history_card_context(
            target, "Month 3 Week 2: Target def. Opponent by Decision", opponent,
        )
        self.assertEqual(context["opponent_name"], "Opponent")
        self.assertEqual(context["opponent_record"], "Not recorded")

    def test_archived_opponent_record_still_wins_over_current_record(self):
        app = ProfileHarness()
        target = fighter("Target", "FTR-target")
        opponent = fighter("Opponent", "FTR-opponent", record_w=30, record_l=0)
        app.roster = [target, opponent]
        target.bout_rating_history = [{
            "date": "Month 3 Week 2", "opponent_id": opponent.fighter_id,
            "opponent_name": opponent.name, "opponent_record": "8-4-0",
        }]
        context = app.fighter_history_card_context(
            target, "Month 3 Week 2: Target def. Opponent by Decision", opponent,
        )
        self.assertEqual(context["opponent_record"], "8-4-0")

    def test_history_context_preserves_title_settlement_evidence(self):
        app = ProfileHarness()
        target = fighter("Target", "FTR-target")
        opponent = fighter("Opponent", "FTR-opponent")
        app.roster = [target, opponent]
        app.result_records = [{
            "date": "Month 3 Week 2", "event": "BAMMA 9", "record_id": "card-title",
            "fight_logs": [{
                "a": target.name, "b": opponent.name,
                "a_id": target.fighter_id, "b_id": opponent.fighter_id,
                "winner_id": target.fighter_id,
                "result": "Target def. Opponent by Decision", "weight": target.weight,
                "title": True,
                "title_miss_decision_state": {"action": "keep_belt"},
                "title_sanction_snapshot": {
                    "settlement": {
                        "outcome": "retained", "method": "Decision",
                        "reason": "The official winner retained the recorded title.",
                    },
                },
            }],
        }]

        context = app.fighter_history_card_context(
            target, "Month 3 Week 2: Target def. Opponent by Decision at BAMMA 9", opponent.name,
        )

        self.assertEqual(context["title_decision"], "keep_belt")
        self.assertEqual(context["title_settlement"]["outcome"], "retained")

    def test_replay_without_archived_record_does_not_take_unrelated_same_date_snapshot(self):
        app = ProfileHarness()
        target = fighter("Target", "FTR-target")
        opponent = fighter("Opponent", "FTR-opponent", record_w=30, record_l=0)
        app.roster = [target, opponent]
        app.result_records = [{
            "date": "Month 3 Week 2", "event": "BAMMA 9", "record_id": "card-one",
            "fight_logs": [{
                "a": target.name, "b": opponent.name,
                "result": "Target def. Opponent by Decision",
            }],
        }]
        target.bout_rating_history = [{
            "date": "Month 3 Week 2", "opponent_id": "FTR-other",
            "opponent_name": "Other", "opponent_record": "12-2-0",
        }]
        context = app.fighter_history_card_context(
            target, "Month 3 Week 2: Target def. Opponent by Decision at BAMMA 9",
        )
        self.assertEqual(context["opponent_name"], "Opponent")
        self.assertEqual(context["opponent_record"], "Not recorded")

    def test_unidentified_legacy_row_does_not_take_first_same_date_snapshot(self):
        app = ProfileHarness()
        target = fighter("Target", "FTR-target")
        target.bout_rating_history = [{
            "date": "Month 3 Week 2", "opponent_id": "FTR-other",
            "opponent_name": "Other", "opponent_record": "12-2-0",
        }]
        app.roster = [target]
        context = app.fighter_history_card_context(
            target, "Month 3 Week 2: Target def. Opponent by Decision",
        )
        self.assertEqual(context["opponent_name"], "-")
        self.assertEqual(context["opponent_record"], "-")
        self.assertEqual(context["source"], "Legacy history entry; card replay unavailable")

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

    def test_duplicate_name_departure_only_vacates_the_actual_holder(self):
        app = ProfileHarness()
        champion = fighter("Alex Smith", "FTR-champion", champion=True)
        non_holder = fighter("Alex Smith", "FTR-non-holder")
        app.roster = [champion, non_holder]
        key = app.belt_key(champion.gender, champion.weight)
        app.belts[key] = champion.name

        app.belts, app.interim_belts, app.belt_history = app.vacate_fighter_belts(
            non_holder, app.roster, app.belts, app.interim_belts, app.belt_history,
            "Left without holding the title.",
        )
        self.assertEqual(app.belts[key], champion.name)
        self.assertFalse(any(row.get("fighter_id") == non_holder.fighter_id for row in app.belt_history[key]))

        app.belts, app.interim_belts, app.belt_history = app.vacate_fighter_belts(
            champion, app.roster, app.belts, app.interim_belts, app.belt_history,
            "Champion departed.",
        )
        self.assertEqual(app.belts[key], "")
        vacancy = next(row for row in app.belt_history[key] if row.get("action") == "Vacated")
        self.assertEqual(vacancy.get("fighter_id"), champion.fighter_id)

    def test_duplicate_name_interim_clear_uses_marked_holder_identity(self):
        app = ProfileHarness()
        interim_holder = fighter("Alex Smith", "FTR-interim", interim_champion=True)
        same_name = fighter("Alex Smith", "FTR-other", interim_champion=False)
        app.roster = [interim_holder, same_name]
        key = app.belt_key(interim_holder.gender, interim_holder.weight)
        app.interim_belts[key] = interim_holder.name

        app.interim_belts, app.belt_history = app.clear_interim_belt(
            app.roster, app.interim_belts, app.belt_history, key, "Unified with the primary title.",
        )
        self.assertEqual(app.interim_belts[key], "")
        self.assertFalse(interim_holder.interim_champion)
        self.assertFalse(same_name.interim_champion)
        cleared = next(row for row in app.belt_history[key] if row.get("action") == "Interim Belt Cleared")
        self.assertEqual(cleared.get("fighter_id"), interim_holder.fighter_id)

        # If a legacy duplicate-name map has no marked holder, do not guess.
        first = fighter("Jordan Lee", "FTR-jordan-1", interim_champion=False)
        second = fighter("Jordan Lee", "FTR-jordan-2", interim_champion=False)
        app.roster = [first, second]
        other_key = app.belt_key(first.gender, first.weight)
        app.interim_belts[other_key] = first.name
        history_before = copy.deepcopy(app.belt_history[other_key])
        app.interim_belts, app.belt_history = app.clear_interim_belt(
            app.roster, app.interim_belts, app.belt_history, other_key, "Ambiguous legacy holder.",
        )
        self.assertEqual(app.interim_belts[other_key], first.name)
        self.assertEqual(app.belt_history[other_key], history_before)

    def test_reconciliation_records_name_only_vacancy_for_missing_holder(self):
        app = ProfileHarness()
        key = app.belt_key("Male", "Lightweight")
        app.belts[key] = "Gone Champion"
        app.belt_history[key] = [{
            "action": "Champion Crowned", "fighter": "Gone Champion",
            "fighter_id": "FTR-gone", "date": "Month 1 Week 1",
        }]

        app.belts, app.interim_belts, app.belt_history = app.ensure_company_champions(
            [], app.belts, app.player_company_name, "USA", 50,
            player_owned=True, min_per_division=0,
            interim_belts=app.interim_belts, belt_history=app.belt_history,
        )

        self.assertEqual(app.belts[key], "")
        vacancy = next(row for row in app.belt_history[key] if row.get("action") == "Vacated")
        self.assertEqual(vacancy.get("fighter"), "Gone Champion")
        self.assertEqual(vacancy.get("fighter_id"), "")
        self.assertIn("name-only vacancy", vacancy.get("note", ""))

        # Reconciliation is idempotent after the map has been cleared.
        history_after = copy.deepcopy(app.belt_history[key])
        app.belts, app.interim_belts, app.belt_history = app.ensure_company_champions(
            [], app.belts, app.player_company_name, "USA", 50,
            player_owned=True, min_per_division=0,
            interim_belts=app.interim_belts, belt_history=app.belt_history,
        )
        self.assertEqual(app.belt_history[key], history_after)

    def test_reconciliation_fails_closed_for_ambiguous_primary_holder(self):
        app = ProfileHarness()
        first = fighter("Alex Smith", "FTR-alex-1")
        second = fighter("Alex Smith", "FTR-alex-2")
        app.roster = [first, second]
        key = app.belt_key(first.gender, first.weight)
        app.belts[key] = first.name
        history_before = copy.deepcopy(app.belt_history[key])

        app.belts, app.interim_belts, app.belt_history = app.ensure_company_champions(
            app.roster, app.belts, app.player_company_name, "USA", 50,
            player_owned=True, min_per_division=0,
            interim_belts=app.interim_belts, belt_history=app.belt_history,
        )

        self.assertEqual(app.belts[key], "Alex Smith")
        self.assertEqual(app.belt_history[key], history_before)
        self.assertFalse(first.champion)
        self.assertFalse(second.champion)

    def test_reconciliation_uses_explicit_champion_marker_for_duplicate_name(self):
        app = ProfileHarness()
        marked = fighter("Alex Smith", "FTR-alex-marked", champion=True)
        other = fighter("Alex Smith", "FTR-alex-other", champion=False)
        app.roster = [marked, other]
        key = app.belt_key(marked.gender, marked.weight)
        app.belts[key] = marked.name

        app.belts, app.interim_belts, app.belt_history = app.ensure_company_champions(
            app.roster, app.belts, app.player_company_name, "USA", 50,
            player_owned=True, min_per_division=0,
            interim_belts=app.interim_belts, belt_history=app.belt_history,
        )

        self.assertEqual(app.belts[key], marked.name)
        self.assertTrue(marked.champion)
        self.assertFalse(other.champion)

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

    def test_amateur_history_reader_bounds_malformed_dates(self):
        source = inspect.getsource(ViewMixin.open_fighter_profile_window)
        self.assertIn('entries = getattr(fighter, "fight_history", None)', source)
        self.assertIn('if not isinstance(entries, (list, tuple))', source)
        self.assertIn('if not isinstance(amateur_history, (list, tuple))', source)
        self.assertIn('def safe_history_int(value, fallback=0):', source)
        self.assertIn('if not math.isfinite(numeric):', source)
        self.assertIn('except (TypeError, ValueError, OverflowError):', source)
        self.assertIn('week = max(1, min(4, safe_history_int', source)

    def test_detailed_skill_readers_are_deterministic_and_non_mutating(self):
        app = ProfileHarness()
        target = fighter(
            "Legacy Skills", "FTR-legacy-skills", striking=81, wrestling=63,
            grappling=74, cardio=70, chin=68, fight_iq=77, morale=61,
            detailed_skills={},
        )
        before = copy.deepcopy(vars(target))
        import random
        random_state = random.getstate()
        projected = app.detailed_skills_read_model(target)
        self.assertTrue(all(key in projected for keys in DETAILED_SKILL_GROUPS.values() for key in keys))
        self.assertEqual(81, projected["footwork"])
        self.assertEqual(74, projected["guard_work"])
        self.assertEqual(before, vars(target))
        self.assertEqual(random_state, random.getstate())
        # The text and popup readers must consume the same projection rather
        # than silently invoking the RNG-backed repair owner.
        self.assertIn("Detailed Skills", inspect.getsource(ViewMixin.open_detailed_skills))
        self.assertNotIn("ensure_detailed_skills(fighter)", inspect.getsource(ViewMixin.open_detailed_skills))
        self.assertNotIn("ensure_detailed_skills(fighter)", inspect.getsource(ViewMixin.fighter_stats_text))

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
