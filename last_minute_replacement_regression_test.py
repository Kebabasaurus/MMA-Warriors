"""Regression tests for explicit short-notice replacement selection."""

import inspect
import unittest
from types import SimpleNamespace

from events import EventMixin
from admin import AdminMixin
from models import Fighter
from feature_foundation import FoundationMixin
from views import ViewMixin


def fighter(name, fighter_id, weight="Lightweight", fatigue=10, injured=0, wins=6, losses=2):
    return Fighter(
        name=name, weight=weight, age=28, record_w=wins, record_l=losses,
        striking=70, wrestling=68, grappling=69, cardio=72, chin=70,
        popularity=45, momentum=0, morale=70, purse=12_500,
        fighter_id=fighter_id, fatigue=fatigue, injured=injured,
    )


class ReplacementHarness(AdminMixin, EventMixin, FoundationMixin):
    def __init__(self):
        self.month, self.week = 3, 2
        self.roster = [fighter("Booked", "f-booked")]
        self.free_agents = [
            fighter("Ready Ranked", "f-ready"),
            fighter("Injured", "f-injured", injured=1),
            fighter("Wrong Class", "f-heavy", weight="Heavyweight"),
        ]
        self.retired_fighters = []
        self.scheduled_events = []
        self.booked = []
        self.news = []
        self.player_company_name = "Test FC"
        self.player_combat_divisions = {}
        self.combat_sport_worlds = {}
        self.ensure_foundation_state()

    def ai_title_challenger_is_eligible(self, fighter):
        return fighter.record_w >= 2 and (
            fighter.record_w >= fighter.record_l
            or getattr(fighter, "career_win_streak", 0) >= 3
        )

    def resolve_fighter(self, reference):
        key = str(reference or "")
        return next((f for f in self.roster + self.free_agents if f.fighter_id == key or f.name == key), None)

    def fighter_booking_status(self, fighter, month=None, week=None):
        if fighter.injured:
            return "Injured"
        if fighter.fatigue >= 65:
            return f"Fatigued {fighter.fatigue}"
        return "Ready"

    def fighter_company_for_profile(self, _fighter):
        return "Free Agent"

    def rank_label_for_fighter(self, fighter, _company, world=False):
        return "#8" if world else "#3"

    def fighter_fatigue_label(self, fighter):
        return f"{fighter.fatigue} Fresh"

    def format_game_date(self, month, week):
        return f"W{week} M{month}"

    def assign_event_camps(self, _event):
        return None

    def event_fight_participant_references(self, fight):
        return EventMixin.event_fight_participant_references(self, fight)


class SpecialHolderReplacementHarness(ReplacementHarness):
    """Exercise a named-belt holder that has no generic champion flag."""

    def __init__(self):
        super().__init__()
        self.roster = [fighter("Booked", "f-booked"), fighter("Challenger", "f-challenger")]
        self.free_agents = [fighter("Ready Ranked", "f-ready")]
        self.special_belts = {
            "Grand Prix Belt": {
                "name": "Grand Prix Belt", "holder": "Booked", "holder_id": "f-booked",
                "defenses": 0, "history": [],
            },
        }
        self.belts, self.interim_belts, self.belt_history = {}, {}, {}

    def perform_weigh_in(self, fighter, *args, **kwargs):
        fighter.missed_weight = fighter.name == "Booked"
        fighter.scale_weight = 157 if fighter.missed_weight else 155
        fighter.weight_cut_penalty = 4 if fighter.missed_weight else 0
        return {
            "made": not fighter.missed_weight,
            "miss_by": 2.0 if fighter.missed_weight else 0.0,
            "scale_weight": fighter.scale_weight,
        }


class LastMinuteReplacementTests(unittest.TestCase):
    class _SelectionStub:
        def __init__(self, row_id):
            self.row_id = row_id

        def selection(self):
            return (self.row_id,)

    def test_dropdown_adapter_is_ready_same_division_and_ranked(self):
        app = ReplacementHarness()
        event = {"month": 3, "week": 2, "fights": []}
        fight = {"fighters": ["Booked", "TBA"], "fighter_ids": ["f-booked", ""], "tba_weight": "Lightweight", "tba_gender": "Male"}
        rows = app.last_minute_replacement_candidates(event, fight, 1)
        self.assertEqual([row["name"] for row in rows], ["Ready Ranked"])
        # A free agent has no rank inside the player's promotion; only the
        # world position is shown until the replacement is signed.
        self.assertEqual(rows[0]["company_rank"], "-")
        self.assertEqual(rows[0]["world_rank"], "#8")

    def test_title_dropdown_filters_ready_but_unqualified_challengers(self):
        app = ReplacementHarness()
        app.free_agents.extend([
            fighter("Unqualified", "f-weak", wins=1, losses=5),
            fighter("Title Ready", "f-title-ready", wins=5, losses=2),
        ])
        event = {"month": 3, "week": 2, "fights": []}
        fight = {
            "fighters": ["Booked", "Ready Ranked"],
            "fighter_ids": ["f-booked", "f-ready"],
            "title": True, "tba_weight": "Lightweight", "tba_gender": "Male",
        }
        rows = app.last_minute_replacement_candidates(event, fight, 1)
        self.assertEqual([row["name"] for row in rows], ["Title Ready"])
        self.assertTrue(rows[0]["title_eligible"])

    def test_title_dropdown_fails_closed_without_merit_owner(self):
        app = ReplacementHarness()
        app.ai_title_challenger_is_eligible = None
        event = {"month": 3, "week": 2, "fights": []}
        fight = {
            "fighters": ["Booked", "Ready Ranked"],
            "fighter_ids": ["f-booked", "f-ready"],
            "title": True, "tba_weight": "Lightweight", "tba_gender": "Male",
        }
        self.assertEqual(app.last_minute_replacement_candidates(event, fight, 1), [])

    def test_divisional_title_flag_also_requires_challenger_merit(self):
        app = ReplacementHarness()
        app.free_agents.extend([
            fighter("Unqualified Divisional", "f-weak-div", wins=1, losses=5),
            fighter("Eligible Divisional", "f-good-div", wins=5, losses=2),
        ])
        event = {"month": 3, "week": 2, "fights": []}
        fight = {
            "fighters": ["Booked", "Ready Ranked"],
            "fighter_ids": ["f-booked", "f-ready"],
            "title": False,
            "divisional_title": True,
            "tba_weight": "Lightweight",
            "tba_gender": "Male",
        }
        rows = app.last_minute_replacement_candidates(event, fight, 1)
        self.assertEqual([row["name"] for row in rows], ["Eligible Divisional"])

    def test_idless_duplicate_candidates_use_deterministic_keys_without_collapsing(self):
        app = ReplacementHarness()
        legacy_one = fighter("Legacy Twin", "f-legacy-1")
        legacy_two = fighter("Legacy Twin", "f-legacy-2")
        # Simulate imported rows before the identity migration.  Their retained
        # facts are identical, so the reader must suffix the deterministic
        # fingerprint rather than use object identity or drop the second row.
        legacy_one.fighter_id = ""
        legacy_two.fighter_id = ""
        app.free_agents.extend([legacy_one, legacy_two])
        event = {"month": 3, "week": 2, "fights": []}
        fight = {
            "fighters": ["Booked", "Ready Ranked"],
            "fighter_ids": ["f-booked", "f-ready"],
            "title": False, "tba_weight": "Lightweight", "tba_gender": "Male",
        }

        first = app.last_minute_replacement_candidates(event, fight, 1)
        second = app.last_minute_replacement_candidates(event, fight, 1)

        self.assertEqual([row["name"] for row in first], ["Legacy Twin", "Legacy Twin"])
        self.assertEqual([row["candidate_key"] for row in first], [row["candidate_key"] for row in second])
        self.assertNotEqual(first[0]["candidate_key"], first[1]["candidate_key"])
        self.assertTrue(first[1]["candidate_key"].endswith("#2"))
        self.assertNotIn("fighter_id", first[0]["candidate_key"])

    def test_commit_replaces_only_selected_corner_and_retains_evidence(self):
        app = ReplacementHarness()
        event = {"month": 3, "week": 2, "fights": []}
        fight = {"fighters": ["Booked", "TBA"], "fighter_ids": ["f-booked", ""], "tba_weight": "Lightweight", "tba_gender": "Male"}
        ok, note = app.commit_last_minute_replacement(event, fight, "f-ready", 1)
        self.assertTrue(ok, note)
        self.assertEqual(fight["fighters"], ["Booked", "Ready Ranked"])
        self.assertEqual(fight["fighter_ids"], ["f-booked", "f-ready"])
        self.assertEqual(fight["replacement_history"][0]["removed_name"], "TBA")
        self.assertEqual(fight["replacement_history"][0]["world_rank"], "#8")
        ranking_snapshot = fight["replacement_history"][0]["pre_bout_rankings"]
        self.assertEqual(ranking_snapshot["replacement"]["world_rank"], "#8")
        self.assertEqual(ranking_snapshot["replacement"]["company_rank"], "-")
        self.assertEqual(ranking_snapshot["retained_opponent"]["fighter"], "Booked")
        self.assertEqual(ranking_snapshot["retained_opponent"]["world_rank"], "#8")
        self.assertNotIn("Ready Ranked", [f.name for f in app.free_agents])
        self.assertIn("Ready Ranked", [f.name for f in app.roster])
        self.assertEqual(len(app.ensure_foundation_state()["operations"]), 1)
        self.assertEqual(next(iter(app.ensure_foundation_state()["operations"].values()))["status"], "committed")

    def test_idless_commit_retains_deterministic_replacement_reference(self):
        app = ReplacementHarness()
        legacy = fighter("Legacy Ready", "f-legacy")
        legacy.fighter_id = ""
        app.free_agents.append(legacy)
        event = {"month": 3, "week": 2, "fights": []}
        fight = {"fighters": ["Booked", "TBA"], "fighter_ids": ["f-booked", ""], "tba_weight": "Lightweight", "tba_gender": "Male"}
        rows = app.last_minute_replacement_candidates(event, fight, 1)
        selected = next(row for row in rows if row["name"] == "Legacy Ready")

        ok, note = app.commit_last_minute_replacement(event, fight, selected["candidate_key"], 1)

        self.assertTrue(ok, note)
        history = fight["replacement_history"][0]
        self.assertTrue(history["replacement_reference"].startswith("legacy:"))
        self.assertEqual(history["replacement_id"], "")
        receipt = next(iter(app.ensure_foundation_state()["operations"].values()))
        self.assertIn(history["replacement_reference"], receipt["result"]["replacement_reference"])

    def test_title_decision_provider_is_injectable(self):
        app = ReplacementHarness()
        expected = {"action": "replacement", "fighter_id": "f-ready", "corner_index": 1}
        app._title_miss_decision_provider = lambda _event, _fight, _misses: expected
        decision = app.prompt_title_weight_miss_decision(
            {"month": 3, "week": 2},
            {"fighters": ["Booked", "TBA"], "fighter_ids": ["f-booked", ""], "tba_weight": "Lightweight", "tba_gender": "Male"},
            [(app.roster[0], 1.0)],
        )
        self.assertEqual(decision, expected)

    def test_title_miss_snapshot_retains_corners_choices_and_roles(self):
        app = ReplacementHarness()
        event = {"event_id": "event-1", "name": "Test Card", "month": 3, "week": 2}
        fight = {
            "fighters": ["Booked", "Ready Ranked"],
            "fighter_ids": ["f-booked", "f-ready"],
            "title": True,
            "divisional_title": True,
        }
        snapshot = app.build_title_miss_decision_snapshot(event, fight, [(app.roster[0], 2.5)])
        self.assertEqual(snapshot["schema_version"], 1)
        self.assertEqual(snapshot["status"], "awaiting_player")
        self.assertEqual(snapshot["fighter_references"], ["f-booked", "f-ready"])
        self.assertEqual(snapshot["belt_id"], "")
        self.assertEqual(snapshot["title_key"], "division:Male:Lightweight")
        self.assertEqual(snapshot["corners"][0]["miss_by"], 2.5)
        self.assertFalse(snapshot["corners"][0]["champion"])
        self.assertTrue(snapshot["corners"][0]["eligible_to_win"])
        self.assertFalse(snapshot["corners"][0]["eligible_to_retain"])
        self.assertEqual(snapshot["choices"], ["remove_belt", "rebook", "keep_belt", "cancel", "replacement"])
        EventMixin.record_title_miss_decision(fight, "keep_belt", reason="kept")
        self.assertEqual(fight["title_miss_decision_state"]["status"], "resolved")
        self.assertEqual(fight["title_miss_decision_state"]["action"], "keep_belt")

    def test_title_miss_snapshot_marks_divisional_or_special_stakes(self):
        app = ReplacementHarness()
        event = {"event_id": "event-stakes", "name": "Stakes", "month": 3, "week": 2}
        divisional = {
            "fighters": ["Booked", "Ready Ranked"],
            "fighter_ids": ["f-booked", "f-ready"],
            "title": False,
            "divisional_title": True,
        }
        special = {
            "fighters": ["Booked", "Ready Ranked"],
            "fighter_ids": ["f-booked", "f-ready"],
            "title": False,
            "special_belt": "Grand Prix Belt",
        }
        self.assertTrue(app.build_title_miss_decision_snapshot(event, divisional, [(app.roster[0], 1.0)])["title_stakes_before"])
        special_snapshot = app.build_title_miss_decision_snapshot(event, special, [(app.roster[0], 1.0)])
        self.assertTrue(special_snapshot["title_stakes_before"])
        self.assertEqual(special_snapshot["title_key"], "special:Grand Prix Belt")

        app.special_belts = {
            "Grand Prix Belt": {
                "name": "Grand Prix Belt", "holder": "Booked",
                "holder_id": "f-booked", "defenses": 0, "history": [],
            },
        }
        special_snapshot = app.build_title_miss_decision_snapshot(
            event, special, [(app.roster[0], 1.0)]
        )
        self.assertTrue(special_snapshot["corners"][0]["special_belt_holder"])
        self.assertTrue(special_snapshot["corners"][0]["eligible_to_retain"])
        self.assertTrue(special_snapshot["corners"][0]["eligible_to_win"])

    def test_title_decision_reader_preserves_explicit_corner_eligibility(self):
        app = ReplacementHarness()
        event = {
            "event_id": "event-eligibility",
            "fights": [{
                "fight_id": "fight-eligibility",
                "fighters": ["Booked", "Ready Ranked"],
                "fighter_ids": ["f-booked", "f-ready"],
                "title": True,
                "title_miss_decision_state": {
                    "status": "awaiting_player",
                    "title_stakes_before": True,
                    "corners": [
                        {
                            "corner": 0, "fighter_id": "f-booked", "fighter": "Booked",
                            "eligible_to_win": True, "eligible_to_retain": False,
                        },
                        {
                            "corner": 1, "fighter_id": "f-ready", "fighter": "Ready Ranked",
                            "eligible_to_win": True, "eligible_to_retain": True,
                        },
                    ],
                },
                "title_sanction_snapshot": {
                    "on_line": True,
                    "settlement": {
                        "outcome": "won", "method": "Decision",
                        "reason": "The official winner became the recorded title holder.",
                    },
                },
            }],
        }

        row = app.title_miss_decision_read_model(event)[0]

        self.assertEqual(
            [(item["eligible_to_win"], item["eligible_to_retain"]) for item in row["corner_eligibility"]],
            [(True, False), (True, True)],
        )
        self.assertEqual(row["settlement"]["outcome"], "won")

    def test_settlement_evidence_records_observed_title_outcome(self):
        app = ReplacementHarness()
        winner, loser = app.roster[0], app.free_agents[0]
        winner.champion = True
        fight = {
            "title": True,
            "title_sanction_snapshot": {
                "belt_id": "belt-1",
                "title_key": "division:Male:Lightweight",
                "on_line": True,
                "missed_corners": [
                    {"fighter_id": winner.fighter_id, "champion": False, "interim_champion": False},
                    {"fighter_id": loser.fighter_id, "champion": False, "interim_champion": False},
                ],
            },
        }

        evidence = app.title_sanction_settlement_evidence(fight, winner, loser, "Decision")

        self.assertEqual(evidence["outcome"], "won")
        self.assertTrue(evidence["title_on_line"])
        self.assertEqual(evidence["winner_id"], winner.fighter_id)
        self.assertIn("official winner", evidence["reason"])
        fight["title_sanction_snapshot"]["missed_corners"][0]["interim_champion"] = True
        interim_evidence = app.title_sanction_settlement_evidence(fight, winner, loser, "Decision")
        self.assertEqual(interim_evidence["outcome"], "retained")
        app.update_title_sanction_snapshot(fight, decision="keep_belt")
        self.assertEqual(fight["title_sanction_snapshot"]["belt_id"], "belt-1")
        self.assertEqual(fight["title_sanction_snapshot"]["title_key"], "division:Male:Lightweight")

    def test_special_belt_settlement_uses_saved_holder_evidence(self):
        app = SpecialHolderReplacementHarness()
        holder, challenger = app.roster
        fight = {
            "special_belt": "Grand Prix Belt",
            "title_sanction_snapshot": {
                "on_line": True,
                "missed_corners": [
                    {
                        "fighter_id": holder.fighter_id, "champion": False,
                        "interim_champion": False, "special_belt_holder": True,
                        "eligible_to_retain": True,
                    },
                    {
                        "fighter_id": challenger.fighter_id, "champion": False,
                        "interim_champion": False, "special_belt_holder": False,
                        "eligible_to_retain": False,
                    },
                ],
            },
        }

        evidence = app.title_sanction_settlement_evidence(
            fight, holder, challenger, "Decision"
        )

        self.assertEqual(evidence["outcome"], "retained")

    def test_special_belt_holder_replacement_removes_the_belt_from_the_bout(self):
        app = SpecialHolderReplacementHarness()
        event = {"event_id": "event-special-replace", "name": "Special Replacement", "month": 3, "week": 2}
        fight = {
            "fighters": ["Booked", "Challenger"],
            "fighter_ids": ["f-booked", "f-challenger"],
            "title": False,
            "special_belt": "Grand Prix Belt",
        }
        event["fights"] = [fight]
        app._title_miss_decision_provider = lambda *_args: {
            "action": "replacement", "fighter_id": "f-ready", "corner_index": 0,
        }

        _lines, _purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(cancelled, [])
        self.assertEqual(fight["special_belt"], "")
        self.assertFalse(fight["title_sanction_snapshot"]["on_line"])

    def test_remove_belt_recognises_special_holder_without_champion_flag(self):
        app = SpecialHolderReplacementHarness()
        event = {"event_id": "event-special-remove", "name": "Special Removal", "month": 3, "week": 2}
        fight = {
            "fighters": ["Booked", "Challenger"],
            "fighter_ids": ["f-booked", "f-challenger"],
            "title": False,
            "special_belt": "Grand Prix Belt",
        }
        event["fights"] = [fight]
        app._title_miss_decision_provider = lambda *_args: {"action": "remove_belt"}

        _lines, _purse_penalty, cancelled = app.run_weigh_ins(event)

        self.assertEqual(cancelled, [])
        self.assertEqual(app.special_belts["Grand Prix Belt"]["holder_id"], "")
        self.assertEqual(fight["title_decision"], "remove_belt")

    def test_special_belt_vacancy_is_scoped_to_departing_promotion(self):
        app = ReplacementHarness()
        fighter = app.roster[0]
        fighter.special_titles = ["Child Belt", "Player Belt"]
        child = SimpleNamespace(special_belts={
            "Child Belt": {
                "name": "Child Belt", "holder": fighter.name,
                "holder_id": fighter.fighter_id, "defenses": 2, "history": [],
            },
        })
        app.special_belts = {
            "Player Belt": {
                "name": "Player Belt", "holder": fighter.name,
                "holder_id": fighter.fighter_id, "defenses": 1, "history": [],
            },
        }

        app.vacate_special_belts_held_by(fighter, "Transferred to the parent.", owner=child)

        self.assertEqual(child.special_belts["Child Belt"]["holder_id"], "")
        self.assertEqual(app.special_belts["Player Belt"]["holder_id"], fighter.fighter_id)
        self.assertEqual(fighter.special_titles, ["Player Belt"])
        self.assertEqual(child.special_belts["Child Belt"]["history"][0]["action"], "Vacated")

    def test_weigh_in_persists_snapshot_before_prompt_and_sanction_after_choice(self):
        source = inspect.getsource(EventMixin.run_weigh_ins)
        self.assertLess(source.index("build_title_miss_decision_snapshot"), source.index("prompt_title_weight_miss_decision"))
        self.assertIn("title_sanction_snapshot", source)
        self.assertIn("record_title_miss_decision", source)

    def test_preparation_timeline_exposes_title_decision_without_recomputing(self):
        app = ReplacementHarness()
        event = {
            "event_id": "event-2", "name": "Scale Card", "month": 3, "week": 2,
            "fights": [{
                "fighters": ["Booked", "Ready Ranked"],
                "fighter_ids": ["f-booked", "f-ready"], "title": True,
                "title_miss_decision_state": {
                    "status": "resolved", "action": "keep_belt",
                    "reason": "Player kept the title on the line.",
                    "replacement_id": "", "corners": [],
                },
                "title_sanction_snapshot": {
                    "on_line": True, "champion_miss_waived": True,
                    "missed_corners": [],
                },
            }],
        }
        timeline = app.event_preparation_timeline(event, weigh_log=["Recorded weigh-in"])
        self.assertEqual(len(timeline["title_miss_decisions"]), 1)
        decision = timeline["title_miss_decisions"][0]
        self.assertEqual(decision["action"], "keep_belt")
        self.assertTrue(decision["on_line"])
        self.assertIn("title-miss decision(s) retained", timeline["stage_states"][2]["detail"])

    def test_title_decision_reader_centralises_choices_and_legacy_identity(self):
        app = ReplacementHarness()
        event = {
            "event_id": "event-reader",
            "fights": [
                {
                    "fight_id": "fight-reader-1",
                    "fighters": ["Booked", "Ready Ranked"],
                    "fighter_ids": ["f-booked", "f-ready"],
                    "title_miss_decision_state": {
                        "status": "awaiting_player",
                        "choices": ["keep_belt", "cancel", "bogus"],
                        "reason": "Choose a title treatment.",
                        "corners": [{"fighter_id": "f-booked", "miss_by": 1.5}],
                    },
                    "title_sanction_snapshot": {"on_line": False, "decision": "awaiting_player"},
                },
                {
                    "fighters": ["Legacy A", "Legacy B"],
                    "title_miss_decision_state": {"status": "needs_review"},
                },
            ],
        }
        before = repr(event)
        rows = app.title_miss_decision_read_model(event)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["fighter_references"], ["f-booked", "f-ready"])
        # This fixture has no retained belt scope; the reader must not infer
        # one from whatever division the fighters occupy today.
        self.assertEqual(rows[0]["title_key"], "")
        self.assertEqual(rows[0]["choices"], ["keep_belt", "cancel"])
        self.assertEqual(rows[0]["status"], "awaiting_player")
        self.assertFalse(rows[0]["scheduled_title"])
        self.assertFalse(rows[0]["legacy_reference"])
        self.assertTrue(rows[1]["legacy_reference"])
        self.assertEqual(rows[1]["choices"], list(EventMixin.TITLE_MISS_ACTIONS))
        rows[0]["missed_corners"].append({"mutated": True})
        self.assertEqual(repr(event), before)

    def test_pending_title_reader_distinguishes_scheduled_title_from_settlement(self):
        app = ReplacementHarness()
        event = {
            "event_id": "event-pending-title",
            "fights": [{
                "fight_id": "bout-pending-title",
                "fighters": ["Booked", "Ready Ranked"],
                "fighter_ids": ["f-booked", "f-ready"],
                "title": True,
                "title_miss_decision_state": {
                    "status": "awaiting_player",
                    "title_stakes_before": True,
                    "corners": [{"fighter_id": "f-booked", "miss_by": 1.0}],
                },
                "title_sanction_snapshot": {
                    "on_line": False,
                    "review_required": True,
                },
            }],
        }
        row = app.title_miss_decision_read_model(event)[0]
        self.assertTrue(row["scheduled_title"])
        self.assertFalse(row["on_line"])

    def test_upcoming_title_decision_review_is_read_only_and_headless_safe(self):
        app = ReplacementHarness()
        event = {
            "event_id": "event-review",
            "name": "Review Card",
            "month": 3,
            "week": 2,
            "fights": [{
                "fight_id": "bout-review",
                "fighters": ["Booked", "Ready Ranked"],
                "fighter_ids": ["f-booked", "f-ready"],
                "title_miss_decision_state": {
                    "status": "awaiting_player",
                    "reason": "Recorded scale miss needs a player decision.",
                    "choices": ["remove_belt", "keep_belt"],
                    "corners": [{"fighter_id": "f-booked", "fighter": "Booked", "miss_by": 1.5}],
                },
            }],
        }
        app.upcoming_tree = self._SelectionStub("event-review")
        app.upcoming_event_rows = {"event-review": event}
        before = repr(event)
        rows = app.review_selected_title_miss_decision()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "awaiting_player")
        self.assertEqual(rows[0]["choices"], ["remove_belt", "keep_belt"])
        self.assertEqual(repr(event), before)

    def test_action_consequences_are_explicit_and_presentation_only(self):
        app = ReplacementHarness()
        fight = {"title": True}
        misses = [(app.roster[0], 1.5)]
        expected = {
            "remove_belt": "vacating",
            "rebook": "no result",
            "keep_belt": "title on the line",
            "cancel": "No result",
            "replacement": "same-division candidate",
        }
        for action, phrase in expected.items():
            text = app.title_miss_action_consequence(action, fight, misses)
            self.assertIn(phrase.lower(), text.lower())
        source = inspect.getsource(EventMixin.title_miss_action_consequence)
        self.assertIn("does not", source)
        self.assertIn("RNG", source)

    def test_result_card_preparation_includes_title_decision_evidence(self):
        source = inspect.getsource(ViewMixin.open_result_card_window)
        self.assertIn("title_miss_decisions", source)
        self.assertIn("Title remained on the line", source)
        self.assertIn("Title scheduled; decision pending", source)
        self.assertIn("title_key", source)
        self.assertIn("Permitted choices", source)
        self.assertIn("Recorded miss", source)
        self.assertIn("Replacement identity", source)


if __name__ == "__main__":
    unittest.main()
