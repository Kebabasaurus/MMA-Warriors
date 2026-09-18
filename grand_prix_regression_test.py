"""Regression coverage for multi-event Grand Prix scheduling rules."""

import copy
import json
import random
import unittest
from types import SimpleNamespace

from events import EventMixin
from fight_engine_audit import FightAuditHarness, synthetic_fighter
from grand_prix import GrandPrixMixin


class GrandPrixHarness(GrandPrixMixin):
    def __init__(self, fighters):
        self.month = 1
        self.week = 1
        self.roster = list(fighters)
        self.free_agents = []
        self.booked = []
        self.scheduled_events = []
        self.grand_prix_series = []
        self.news = []
        self.inbox = []
        self.drug_testing_state = {"cases": []}
        self._id_counter = 0

    def _resolve_event_fighter(self, reference):
        token = str(reference or "")
        by_id = [fighter for fighter in self.roster + self.free_agents if fighter.fighter_id == token]
        if by_id:
            return by_id[0]
        by_name = [fighter for fighter in self.roster + self.free_agents if fighter.name == token]
        return by_name[0] if len(by_name) == 1 else None

    resolve_fighter = _resolve_event_fighter

    def event_fight_participant_references(self, fight):
        return list(fight.get("fighter_ids", fight.get("fighters", [])))

    def calendar_day_index(self, month=None, week=None, day=None):
        return ((int(month or self.month) - 1) * 4 + (int(week or self.week) - 1)) * 7 + int(day or 1)

    def day_index_parts(self, value):
        zero = max(0, int(value) - 1)
        week_index, day = divmod(zero, 7)
        month, week = divmod(week_index, 4)
        return month + 1, week + 1, day + 1

    def fighter_available_for_date(self, fighter, month=None, week=None, day=None):
        return not fighter.injured

    def fighter_booking_status(self, fighter, month=None, week=None):
        return "Ready" if self.fighter_available_for_date(fighter, month, week) and fighter.fatigue < 62 else "Unavailable"

    def event_date_label(self, event):
        return f"M{event.get('month')}/W{event.get('week')}"

    def assign_event_camps(self, _event):
        return None

    def _foundation_next_id(self, _kind):
        self._id_counter += 1
        return f"{_kind}-{self._id_counter}"


class SettlementGrandPrixHarness(EventMixin, GrandPrixHarness):
    """Exercise Grand Prix progression through the real atomic event owner."""

    def __init__(self, fighters):
        GrandPrixHarness.__init__(self, fighters)
        self.result_index = []
        self.result_records = []
        self.settlement_payments = []
        self.fail_after_progression = False
        self.failure_random_value = None

    def _finish_event_unchecked(self, event, package):
        if event in self.scheduled_events:
            self.scheduled_events.remove(event)
        package["grand_prix_next_events"] = [
            dict(next_event) for next_event in self.advance_grand_prix_after_event(event, package)
        ]
        self.settlement_payments.append(package["record_id"])
        self.failure_random_value = random.random()
        if self.fail_after_progression:
            raise RuntimeError("injected failure after Grand Prix progression")
        self.result_records.append({"record_id": package["record_id"]})
        return package

    def assign_event_camps(self, _event):
        return None

    def refresh_all(self):
        return None

    def write_log(self):
        return None

    def show_event_summary(self, _package):
        return None


def fighter(index, *, injured=0, overall=60):
    return SimpleNamespace(
        fighter_id=f"fighter-{index}", name=f"Fighter {index}", gender="Male", weight="Lightweight",
        injured=injured, fatigue=10, retired=False, retirement_pending=False, primary_discipline="MMA",
        available_week=0, available_day=0, overall=overall, elo_rating=1500 + overall,
        fight_iq=overall, cardio=overall,
    )


class GrandPrixRegressionTests(unittest.TestCase):
    def test_field_sizes_and_stage_distribution(self):
        self.assertEqual(GrandPrixMixin.grand_prix_event_count_options(4), (1, 2))
        self.assertEqual(GrandPrixMixin.grand_prix_event_count_options(8), (1, 2, 3))
        self.assertEqual(GrandPrixMixin.grand_prix_event_count_options(16), (1, 2, 3, 4))
        self.assertEqual(GrandPrixMixin.grand_prix_stage_distribution(16, 4), (1, 1, 1, 1))
        self.assertEqual(GrandPrixMixin.grand_prix_stage_distribution(16, 2), (2, 2))
        self.assertEqual(GrandPrixMixin.grand_prix_stage_distribution(8, 2), (2, 1))

    def test_registration_keeps_identity_and_only_first_stage_on_first_event(self):
        fighters = [fighter(index) for index in range(16)]
        app = GrandPrixHarness(fighters)
        event = {"event_id": "event-1", "month": 2, "week": 1, "day": 2, "fights": [{
            "tournament": True, "tournament_size": 16, "grand_prix_event_count": 4,
            "tournament_entrants": [item.name for item in fighters], "fighter_ids": [item.fighter_id for item in fighters],
            "fighters": [fighters[0].name, fighters[-1].name], "tournament_weight": "Lightweight", "tournament_gender": "Male",
            "tournament_name": "Spring Grand Prix", "title": False,
        }]}
        rows = app.register_grand_prix_series_for_event(event)
        self.assertEqual(len(rows), 1)
        series = rows[0]
        self.assertEqual(series["original_entrant_ids"], [item.fighter_id for item in fighters])
        self.assertEqual(series["stage_distribution"], [1, 1, 1, 1])
        self.assertEqual(event["fights"][0]["grand_prix_stage_end"], 1)
        app.scheduled_events.append(event)
        series["next_event_index"] = 1
        series["advancing_ids"] = [item.fighter_id for item in fighters[:8]]
        next_event = app._grand_prix_stage_event(series, source_event=event)
        self.assertEqual(next_event["fights"][0]["grand_prix_stage_start"], 1)
        self.assertEqual(next_event["fights"][0]["grand_prix_stage_end"], 2)
        self.assertEqual(len(next_event["fights"][0]["fighter_ids"]), 8)

    def test_four_card_lifecycle_survives_reload_and_completes_once(self):
        fighters = [fighter(index) for index in range(16)]
        app = SettlementGrandPrixHarness(fighters)
        event = {"event_id": "event-opening", "name": "Lifecycle Grand Prix — Stage 1/4",
                 "venue": "Regional Arena", "region": "Europe", "city": "London",
                 "month": 2, "week": 1, "day": 2, "fights": [{
                     "tournament": True, "tournament_size": 16, "grand_prix_event_count": 4,
                     "tournament_entrants": [item.name for item in fighters],
                     "fighter_ids": [item.fighter_id for item in fighters],
                     "fighters": [fighters[0].name, fighters[-1].name],
                     "tournament_weight": "Lightweight", "tournament_gender": "Male",
                     "tournament_name": "Lifecycle Grand Prix", "title": False,
                 }]}
        series = app.register_grand_prix_series_for_event(event)[0]
        app.scheduled_events.append(event)
        expected = [item.fighter_id for item in fighters]
        settled_event_ids = []

        for event_index in range(4):
            settled_event_ids.append(event["event_id"])
            expected = expected[:len(expected) // 2]
            completed = event_index == 3
            bracket = {
                "series_id": series["series_id"], "event_index": event_index,
                "stage_end": event_index + 1, "advancing_ids": list(expected),
                "completed": completed,
                "champion_id": expected[0] if completed else "",
                "champion": fighters[0].name if completed else "",
            }
            package = {"record_id": f"settlement-{event_index}", "tournament_brackets": [bracket], "results": []}
            app.finish_event(event, package)
            series = app.grand_prix_series_by_id(bracket["series_id"])
            self.assertEqual(series["advancing_ids"], expected)
            self.assertEqual(series["completed_event_count"], event_index + 1)
            self.assertEqual(len(series["history"]), event_index + 1)
            if completed:
                self.assertEqual(series["status"], "Completed")
                self.assertEqual(series["champion_id"], fighters[0].fighter_id)
                self.assertFalse(app.scheduled_events)
                continue
            self.assertEqual(len(app.scheduled_events), 1)
            event = app.scheduled_events[0]
            self.assertEqual(event["grand_prix_event_index"], event_index + 1)
            self.assertEqual(event["fights"][0]["fighter_ids"], expected)

            if event_index == 0:
                persisted = json.loads(json.dumps({
                    "grand_prix_series": app.grand_prix_series,
                    "scheduled_events": app.scheduled_events,
                }))
                reloaded = SettlementGrandPrixHarness(fighters)
                reloaded.grand_prix_series = persisted["grand_prix_series"]
                reloaded.scheduled_events = persisted["scheduled_events"]
                reloaded._id_counter = app._id_counter
                app = reloaded
                event = app.scheduled_events[0]
                series = app.grand_prix_series_by_id(series["series_id"])
                self.assertEqual(series["event_ids"][-1], event["event_id"])
                self.assertEqual(len(app.scheduled_events), 1)

        self.assertEqual(len(set(settled_event_ids)), 4)
        self.assertEqual(len(series["event_ids"]), 4)
        self.assertEqual(len(set(series["event_ids"])), 4)
        self.assertEqual(app.settlement_payments, ["settlement-1", "settlement-2", "settlement-3"])

    def test_committed_retry_and_failed_progression_are_idempotent_and_atomic(self):
        fighters = [fighter(index) for index in range(4)]
        app = SettlementGrandPrixHarness(fighters)
        event = {"event_id": "event-atomic", "name": "Atomic Grand Prix", "venue": "Regional Arena",
                 "region": "Europe", "month": 2, "week": 1, "day": 2, "fights": [{
                     "tournament": True, "tournament_size": 4, "grand_prix_event_count": 2,
                     "tournament_entrants": [item.name for item in fighters],
                     "fighter_ids": [item.fighter_id for item in fighters],
                     "fighters": [fighters[0].name, fighters[-1].name],
                     "tournament_weight": "Lightweight", "tournament_gender": "Male",
                     "tournament_name": "Atomic Grand Prix", "title": False,
                 }]}
        series = app.register_grand_prix_series_for_event(event)[0]
        app.scheduled_events.append(event)
        package = {"record_id": "settlement-atomic", "results": [], "tournament_brackets": [{
            "series_id": series["series_id"], "event_index": 0, "stage_end": 1,
            "advancing_ids": [fighters[0].fighter_id, fighters[1].fighter_id], "completed": False,
        }]}
        before_state = random.getstate()
        app.fail_after_progression = True
        with self.assertRaisesRegex(RuntimeError, "injected failure"):
            app.finish_event(event, package)
        self.assertEqual(random.getstate(), before_state)
        self.assertEqual(len(app.grand_prix_series[0]["history"]), 0)
        self.assertEqual(app.scheduled_events, [event])
        self.assertEqual(app.settlement_payments, [])
        self.assertNotIn("_settlement_committed", package)

        app.fail_after_progression = False
        app.finish_event(event, package)
        next_ids = [row["event_id"] for row in app.scheduled_events]
        history = copy.deepcopy(app.grand_prix_series[0]["history"])
        payments = list(app.settlement_payments)
        app.finish_event(event, package)
        self.assertEqual([row["event_id"] for row in app.scheduled_events], next_ids)
        self.assertEqual(app.grand_prix_series[0]["history"], history)
        self.assertEqual(app.settlement_payments, payments)
        self.assertEqual(len(app.result_records), 1)

    def test_injury_uses_eligible_replacement_or_moves_whole_tournament(self):
        fighters = [fighter(index) for index in range(4)]
        alternate = fighter(99, overall=55)
        app = GrandPrixHarness(fighters)
        app.free_agents = [alternate]
        event = {"event_id": "event-2", "name": "Medical Grand Prix", "month": 2, "week": 1, "day": 2, "fights": [{
            "tournament": True, "tournament_size": 4, "grand_prix_event_count": 2,
            "tournament_entrants": [item.name for item in fighters], "fighter_ids": [item.fighter_id for item in fighters],
            "fighters": [fighters[0].name, fighters[-1].name], "tournament_weight": "Lightweight", "tournament_gender": "Male",
            "tournament_name": "Medical Grand Prix", "title": False,
        }]}
        app.register_grand_prix_series_for_event(event)
        fighters[0].injured = 2
        result = app.prepare_grand_prix_event(event)
        self.assertFalse(result["postponed"])
        self.assertEqual(event["fights"][0]["fighter_ids"][0], alternate.fighter_id)

        app.free_agents = []
        fighters[1].injured = 2
        before = copy.deepcopy(event)
        result = app.prepare_grand_prix_event(event)
        self.assertTrue(result["postponed"])
        self.assertGreater(event["month"] * 4 + event["week"], before["month"] * 4 + before["week"])

    def test_preliminary_positive_does_not_trigger_confirmed_failure_policy(self):
        fighters = [fighter(index) for index in range(4)]
        app = GrandPrixHarness(fighters)
        app.drug_testing_state["cases"] = [{
            "fighter_id": fighters[0].fighter_id, "preliminary_result": "preliminary_positive",
            "confirmation": {"status": "not_enabled"}, "final_resolution": {"status": "gated"},
            "sanction": {"status": "not_enabled"},
        }]
        self.assertFalse(app.grand_prix_confirmed_drug_failure(fighters[0]))
        app.drug_testing_state["cases"][0]["confirmation"]["status"] = "confirmed_positive"
        self.assertTrue(app.grand_prix_confirmed_drug_failure(fighters[0]))

    def test_decider_is_scoped_and_uses_fifteen_minutes(self):
        engine = FightAuditHarness()
        a, b = synthetic_fighter("Decider A", 62), synthetic_fighter("Decider B", 62)
        _winner, _loser, method, _round, _lines = engine.simulate_fight(a, b, {"tournament": True, "tournament_decider": True})
        self.assertNotEqual(method, "Draw")
        self.assertEqual(engine._last_fight_result.rules["round_length"], 15)
        _winner, _loser, _method, _round, _lines = engine.simulate_fight(a, b, {})
        self.assertEqual(engine._last_fight_result.rules["round_length"], 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
