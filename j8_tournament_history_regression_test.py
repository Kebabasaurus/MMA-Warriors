"""Regression coverage for the durable one-night tournament history hub."""

import copy
import inspect
import random
import unittest
from types import SimpleNamespace

from events import EventMixin
from views import ViewMixin
from world import WorldMixin


class TournamentViewHarness(ViewMixin):
    def format_game_date_text(self, value):
        return str(value)


class TournamentIndexHarness(WorldMixin):
    def scorecard_summary_from_lines(self, _lines):
        return "recorded"


class TournamentAlternateHarness(EventMixin):
    def event_fight_participant_references(self, fight):
        return list(fight.get("fighter_ids", fight.get("fighters", [])))

    def fighter_booking_status(self, fighter, _month, _week):
        return "Ready" if not getattr(fighter, "injured", False) and getattr(fighter, "fatigue", 0) < 65 else "Unavailable"

    def fighter_company_for_profile(self, fighter):
        return getattr(fighter, "company", "Free Agent")


def sample_bracket():
    return {
        "title": "Regional Grand Prix",
        "entrant_ids": ["fighter-1", "fighter-2", "fighter-3", "fighter-4"],
        "entrants": ["Alpha", "Bravo", "Charlie", "Delta"],
        "seeds": [
            {"seed": 1, "fighter_id": "fighter-1", "name": "Alpha", "rank": 2},
            {"seed": 2, "fighter_id": "fighter-2", "name": "Bravo", "rank": 5},
            {"seed": 3, "fighter_id": "fighter-3", "name": "Charlie", "rank": 8},
            {"seed": 4, "fighter_id": "fighter-4", "name": "Delta", "rank": 11},
        ],
        "weight": "Lightweight",
        "gender": "Male",
        "series_id": "series-regional-lightweight",
        "substitutions": [{"fighter_id": "fighter-4", "replaced": "fighter-9", "reason": "Medical"}],
        "stages": [{
            "name": "SEMIFINALS",
            "matches": [{
                "a": "Alpha", "b": "Delta", "a_id": "fighter-1", "b_id": "fighter-4",
                "advancing": "Alpha", "advancing_id": "fighter-1",
                "method": "Decision", "round": 3, "summary": "Alpha def. Delta by Decision, R3",
            }],
        }],
        "champion": "Alpha",
        "champion_id": "fighter-1",
        "title_fight": True,
        "final_decisive": True,
        "result_refs": ["event-2030-04-1:bout:3"],
    }


class TournamentHistoryRegressionTests(unittest.TestCase):
    def test_compact_index_retains_draw_identity_and_future_fields(self):
        app = TournamentIndexHarness()
        record = {
            "record_id": "event-2030-04-1",
            "date": "Apr W2 2030",
            "company": "Regional FC",
            "event": "Spring Classic",
            "tournament_brackets": [sample_bracket()],
        }
        row = app.result_index_row(record)
        bracket = row["tournament_brackets"][0]
        self.assertEqual(bracket["entrant_ids"], ["fighter-1", "fighter-2", "fighter-3", "fighter-4"])
        self.assertEqual(bracket["seeds"][0]["rank"], 2)
        self.assertEqual(bracket["substitutions"][0]["fighter_id"], "fighter-4")
        self.assertEqual(bracket["result_refs"], ["event-2030-04-1:bout:3"])
        record["tournament_brackets"][0]["seeds"][0]["name"] = "Mutated"
        self.assertEqual(bracket["seeds"][0]["name"], "Alpha")

    def test_reader_is_identity_safe_filterable_and_defensive(self):
        app = TournamentViewHarness()
        bracket = sample_bracket()
        app.result_index = [{
            "record_id": "event-2030-04-1", "date": "Apr W2 2030",
            "company": "Regional FC", "event": "Spring Classic",
            "has_replay": False, "tournament_brackets": [bracket],
        }, {
            "record_id": "event-2030-05-1", "date": "May W1 2030",
            "company": "National FC", "event": "Summer Classic",
            "has_replay": True, "tournament_brackets": [{
                "title": "National Grand Prix", "entrants": ["Echo", "Foxtrot"],
                "champion": "Echo", "champion_id": "fighter-5",
            }],
        }]
        app.result_records = []
        app.player_event_archive = []
        app.ai_event_archive = []
        before = copy.deepcopy(app.result_index)
        before_rng = random.getstate()
        rows = app.tournament_edition_rows(company="Regional FC", query="alpha")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["edition_id"], "event-2030-04-1:tournament:1")
        self.assertEqual(rows[0]["entrant_ids"][0], "fighter-1")
        self.assertEqual(rows[0]["stages"][0]["matches"][0]["advancing_id"], "fighter-1")
        self.assertEqual(rows[0]["result_refs"], ["event-2030-04-1:bout:3"])
        rows[0]["seeds"][0]["name"] = "Changed in reader"
        self.assertEqual(app.result_index, before)
        self.assertEqual(random.getstate(), before_rng)
        self.assertEqual(app.tournament_edition_rows(company="National FC")[0]["has_replay"], True)
        self.assertEqual(len(app.tournament_edition_rows(query="not present")), 0)

    def test_legacy_detail_fallback_does_not_fabricate_missing_brackets(self):
        app = TournamentViewHarness()
        app.result_index = []
        app.result_records = [{
            "record_id": "event-legacy", "date": "Date unavailable",
            "company": "Legacy FC", "event": "Old Card",
            "tournament_brackets": [{"title": "Legacy Cup", "entrants": ["One"], "champion": "One"}],
        }, {
            "record_id": "event-no-tournament", "company": "Legacy FC", "event": "Ordinary Card",
        }]
        app.player_event_archive = []
        app.ai_event_archive = []
        rows = app.tournament_edition_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Legacy Cup")
        self.assertEqual(rows[0]["series_id"].startswith("series:"), True)

    def test_malformed_draw_containers_remain_readable_and_marked_for_review(self):
        app = TournamentViewHarness()
        malformed = {
            "record_id": "event-malformed", "date": "Jun W1 2030",
            "company": "Legacy FC", "event": "Unclear Cup",
            "tournament_brackets": [{
                "title": "Unclear Cup", "entrants": "not-a-list",
                "entrant_ids": {"fighter": "fighter-1"}, "seeds": "unknown",
                "stages": {"name": "FINAL"}, "substitutions": "legacy text",
                "result_refs": "legacy-ref", "champion": "TBD",
            }],
        }
        app.result_index = [malformed]
        app.result_records = []
        app.player_event_archive = []
        app.ai_event_archive = []
        before = copy.deepcopy(app.result_index)
        before_rng = random.getstate()
        rows = app.tournament_edition_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["entrants"], [])
        self.assertEqual(rows[0]["seeds"], [])
        self.assertEqual(rows[0]["stages"], [])
        self.assertEqual(rows[0]["result_refs"], ["event-malformed"])
        self.assertTrue(rows[0]["review_reasons"])
        self.assertEqual(rows[0]["display_status"], "Review required")
        self.assertEqual(app.result_index, before)
        self.assertEqual(random.getstate(), before_rng)

    def test_malformed_bracket_envelope_is_skipped_without_reader_failure(self):
        app = TournamentViewHarness()
        app.result_index = [{
            "record_id": "event-envelope", "company": "Legacy FC",
            "event": "Broken Card", "tournament_brackets": {"title": "Not a list"},
        }, {
            "record_id": "event-valid", "company": "Legacy FC",
            "event": "Valid Card", "tournament_brackets": [sample_bracket()],
        }]
        app.result_records = []
        app.player_event_archive = []
        app.ai_event_archive = []
        rows = app.tournament_edition_rows()
        self.assertEqual([row["source_id"] for row in rows], ["event-valid"])

    def test_index_writer_retains_malformed_tournament_evidence_without_crashing(self):
        app = TournamentIndexHarness()
        record = {
            "record_id": "event-writer-malformed", "date": "Jul W2 2030",
            "company": "Legacy FC", "event": "Broken Draw",
            "fight_logs": ["legacy line", {"label": "MAIN EVENT", "a": "Alpha", "b": "Bravo", "result": "Decision"}],
            "tournament_brackets": {
                "title": "Legacy Draw", "stages": {"name": "FINAL"},
            },
        }
        before = copy.deepcopy(record)
        row = app.result_index_row(record, has_replay=False)
        self.assertEqual(row["record_id"], "event-writer-malformed")
        self.assertEqual(row["bout_results"][0]["a"], "Alpha")
        self.assertEqual(row["tournament_brackets"], [])
        self.assertEqual(row["tournament_brackets_legacy_raw"]["title"], "Legacy Draw")
        self.assertEqual(record, before)

    def test_simulator_authors_identity_safe_seed_metadata(self):
        source = inspect.getsource(EventMixin.simulate_event_tournament)
        for marker in ('"entrant_ids"', '"seeds"', '"series_id"', '"weight"', '"gender"'):
            self.assertIn(marker, source)

    def test_alternate_review_is_read_only_and_ranked(self):
        make = lambda fid, name, company, elo: SimpleNamespace(
            fighter_id=fid, name=name, company=company, gender="Male", weight="Lightweight",
            elo_rating=elo, overall=60, champion=False, injured=False, fatigue=5,
            record="4-1-0",
        )
        current = make("fighter-1", "Alpha", "Player FC", 90)
        alternate = make("fighter-9", "Alternate", "Free Agent", 70)
        busy = make("fighter-10", "Busy", "Free Agent", 95)
        app = TournamentAlternateHarness()
        app.free_agents = [alternate, busy]
        app.roster = [current]
        app.promotions = []
        app.scheduled_events = [{"event_id": "other", "month": 4, "week": 2, "fights": [{"fighter_ids": ["fighter-10", "fighter-x"], "fighters": ["Busy", "Other"]}]}]
        app.booked = []
        fight = {
            "tournament": True, "tournament_weight": "Lightweight", "tournament_gender": "Male",
            "tournament_entrants": ["Alpha", "Seeded Two"], "fighter_ids": ["fighter-1", "fighter-2"],
        }
        before = copy.deepcopy(app.free_agents)
        before_rng = random.getstate()
        rows = app.tournament_alternate_candidates({"month": 4, "week": 2}, fight)
        self.assertEqual([row["fighter_id"] for row in rows], ["fighter-9"])
        self.assertEqual(rows[0]["world_rank"], "#3")
        self.assertEqual(app.free_agents, before)
        self.assertEqual(random.getstate(), before_rng)

    def test_booking_ui_exposes_tournament_field_review(self):
        source = inspect.getsource(ViewMixin.review_selected_tournament_field)
        for marker in ("TOURNAMENT FIELD REVIEW", "SEEDED FIELD", "READY ALTERNATES", "Planning evidence only", "tournament_alternate_candidates"):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
