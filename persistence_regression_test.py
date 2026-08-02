"""Focused regressions for persistence, result identity, and world integrity fixes."""

import inspect
import random
import tempfile
from pathlib import Path

import persistence
import world as world_module
from models import Fighter
from persistence import PersistenceMixin, serialize_fighter_model
from world import WorldMixin


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def fighter(name="Test Fighter", fighter_id="FTR-test", **updates):
    values = dict(
        name=name, weight="Lightweight", age=28, record_w=5, record_l=2,
        striking=70, wrestling=68, grappling=69, cardio=72, chin=70,
        popularity=45, momentum=0, morale=70, purse=12_500,
        fighter_id=fighter_id,
    )
    values.update(updates)
    return Fighter(**values)


class ResultProbe(WorldMixin):
    def scorecard_summary_from_lines(self, _lines):
        return ""


class TransactionProbe(PersistenceMixin):
    def __init__(self):
        self.cash = 100
        self.roster = ["original"]
        self.marker = {"career": "original"}

    def _apply_world_data_unchecked(self, data):
        self.cash = data["cash"]
        self.roster.append("staged mutation")
        self.marker["career"] = "incoming"
        if data.get("fail"):
            raise ValueError("late migration failure")

    def set_player_event_location_default(self):
        pass


class WorldProbe(WorldMixin):
    def __init__(self):
        self.month = 1
        self.week = 1
        self.booked = []
        self.scheduled_events = []
        self.roster = []
        self.free_agents = []
        self.news = []
        self.inbox = []
        self.rules = {"auto_assign_idle_scouts": True, "drug_testing": "Standard"}
        self.belts = {}
        self.interim_belts = {}
        self.belt_history = {}
        self.special_belts = {}
        self.player_company_name = "Regression FC"
        self.player_region = "USA"
        self.company_pop = 40
        self.company_stability = 60

    def is_event_due(self, _event):
        return False

    def event_fight_participants(self, fight):
        return list(fight.get("fighters", []))

    def event_fight_participant_references(self, fight):
        names = self.event_fight_participants(fight)
        ids = list(fight.get("fighter_ids", []))
        return ids if len(ids) == len(names) and all(ids) else names

    def vacate_fighter_belts(self, _fighter, _roster, belts, interim, history, _reason):
        return belts, interim, history

    def vacate_special_belts_held_by(self, *_args):
        pass

    def resolve_title_shot_inbox(self, *_args):
        pass

    def ensure_company_champions(self, _roster, belts, _name, _region, _pop, **kwargs):
        return belts, kwargs.get("interim_belts", {}), kwargs.get("belt_history", {})

    def record_change(self, *_args):
        pass


def test_result_index_is_idempotent():
    probe = ResultProbe()
    first = {
        "date": "Month 1 Week 1", "company": "Test FC", "event": "Test FC 1",
        "summary": "Card one", "fights": 1,
        "fight_logs": [{"label": "MAIN", "a": "A", "b": "B", "a_id": "a", "b_id": "b", "result": "A - Decision", "scorecards": "29-28"}],
    }
    second = {
        **first, "summary": "A genuinely different card",
        "fight_logs": [{"label": "MAIN", "a": "C", "b": "D", "a_id": "c", "b_id": "d", "result": "D - KO", "scorecards": ""}],
    }
    probe.result_records = [first, second]
    old_row = probe.result_index_row(first, has_replay=True)
    old_row.pop("record_id", None)
    old_row["key"] = "Month 1 Week 1|Test FC|Test FC 1"
    duplicate = dict(old_row)
    duplicate["key"] += "|2"
    probe.result_index = [old_row, duplicate]
    probe.promotions = []
    probe.ensure_result_index()
    keys_after_first = [row["key"] for row in probe.result_index]
    check(len(keys_after_first) == 2, "duplicate legacy row was not collapsed or distinct card was lost")
    probe.ensure_result_index()
    check([row["key"] for row in probe.result_index] == keys_after_first, "result migration was not idempotent")


def test_transactional_apply_rolls_back():
    probe = TransactionProbe()
    original_roster = list(probe.roster)
    try:
        probe.apply_world_data({"cash": 999, "fail": True})
    except ValueError:
        pass
    else:
        raise AssertionError("deliberately late load failure did not propagate")
    check(probe.cash == 100, "failed load changed live cash")
    check(probe.roster == original_roster, "failed load mutated the live roster")
    check(probe.marker == {"career": "original"}, "failed load partially changed nested career state")


def test_serialization_and_metadata_invariants():
    source = inspect.getsource(PersistenceMixin.serialize_world)
    check("ensure_all_company_champions()" not in source, "serialization still performs champion/roster repair")
    load_source = inspect.getsource(PersistenceMixin._apply_world_data_unchecked)
    check("ensure_all_company_champions()" not in load_source, "loading still performs champion/roster repair")
    original_writer = persistence.atomic_write_json_compact
    original_logging = persistence.LOGGER.disabled
    persistence.atomic_write_json_compact = lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("sidecar unavailable"))
    persistence.LOGGER.disabled = True
    try:
        with tempfile.TemporaryDirectory() as folder:
            check(TransactionProbe().write_save_metadata_sidecar(Path(folder) / "save.json", {"slot": "Test"}) is False,
                  "metadata cache failure was not isolated from the primary save")
    finally:
        persistence.atomic_write_json_compact = original_writer
        persistence.LOGGER.disabled = original_logging


def test_finish_bonus_save_compatibility():
    current = fighter(finish_bonus_pct=17)
    row = serialize_fighter_model(current)
    check(row["finish_bonus_pct"] == 17, "current fighter serialization lost finish bonus")
    check(Fighter(**row).finish_bonus_pct == 17, "current fighter round trip lost finish bonus")
    row.pop("finish_bonus_pct")
    check(Fighter(**row).finish_bonus_pct == 0, "legacy fighter data did not receive the safe finish-bonus default")


def test_world_domain_integrity():
    probe = WorldProbe()
    expiring = fighter("Popular Champion", "FTR-expired", champion=True, popularity=90, contract_months=0)
    probe.roster = [expiring]
    probe.update_contracts()
    check(expiring not in probe.roster and expiring in probe.free_agents, "expired star received a hidden free renewal")
    check(expiring.contract_months == 0 and not expiring.exclusive, "released fighter retained an active contract")

    scheduled = fighter("Same Name", "FTR-scheduled")
    namesake = fighter("Same Name", "FTR-namesake")
    probe.scheduled_events = [{"month": 2, "week": 1, "fights": [{"fighters": [scheduled.name], "fighter_ids": [scheduled.fighter_id]}]}]
    check(probe.fighter_has_scheduled_fight(scheduled), "stable scheduled fighter ID was not recognized")
    check(not probe.fighter_has_scheduled_fight(namesake), "display-name collision incorrectly marked a namesake busy")

    probe.roster = [fighter("Debt Fighter", "FTR-debt", morale=70)]
    probe.finance = {}
    probe.cash = -10_000
    probe.apply_player_financial_pressure()
    check(probe.finance["negative_cash_months"] == 1 and probe.company_stability == 58,
          "first debt month did not persist a modest stability consequence")
    check(probe.roster[0].morale == 69, "debt pressure did not reach roster morale")
    probe.cash = 500
    probe.apply_player_financial_pressure()
    check(probe.finance["negative_cash_months"] == 0, "positive cash did not reset the debt streak")


def test_outside_draw_and_full_purse():
    probe = WorldProbe()
    contracted = fighter("Outside Fighter", "FTR-outside", exclusive=False)
    opponent = fighter("Outside Opponent", "FTR-opponent")
    probe.roster = [contracted]
    draw_calls = []
    probe.create_generated_fighter = lambda *_args: opponent
    probe.simulate_fight = lambda *_args: (contracted, opponent, "Draw", 3, [])
    probe.apply_draw_result = lambda a, b, fight: (setattr(a, "record_d", a.record_d + 1), draw_calls.append((a, b, fight)))
    rolls = iter((0.0, 1.0))
    original_random = world_module.random.random
    world_module.random.random = lambda: next(rolls)
    try:
        probe.simulate_nonexclusive_outside_fights()
    finally:
        world_module.random.random = original_random
    check(draw_calls and contracted.record_d == 1 and contracted.record_l == 2,
          "outside draw bypassed shared draw handling or became a loss")

    probe.finance = {
        "ticket_price": 50, "media_rights": {}, "sponsor_deals": [], "commentators": [],
        "broadcast_cut": 0.1, "sponsor_income": 0, "merch_rate": 0.0, "production_base": 0,
        "medical_base": 0, "marketing_budget": 0, "drug_test_cost": 0, "tax_rate": 0.0,
    }
    probe.engine_settings = {"gate_multiplier": 1.0}
    probe.broadcasters = []
    probe.post_show_bonuses = {"fight": 0, "ko": 0, "sub": 0}
    probe.venue_capacity_for = lambda _venue: 1000
    probe.event_atmosphere = lambda *_args: {"attendance_factor": 1.0, "sponsor_factor": 1.0, "merch_factor": 1.0}
    probe.ensure_finance_defaults = lambda: None
    finance = probe.calculate_event_finance(40, 15_000, {"venue": "Test", "fights": []}, [], contracted_fighter_pay=25_000)
    check(finance["fighter_pay"] == 25_000 and finance["contracted_fighter_pay"] == 25_000,
          "event finance discounted a signed purse")
    check(finance["tier_purse_savings"] == 0, "event finance still reports hidden purse savings")


def test_scout_auto_assignment_toggle():
    probe = WorldProbe()
    probe.rules["auto_assign_idle_scouts"] = False
    probe.staff = [{"name": "Scout", "role": "Scout"}]
    probe.scout_workload = lambda _name: 0
    probe.start_scout_report_for_fighter = lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("disabled automation assigned a scout"))
    probe.auto_assign_idle_scouts()


def main():
    random.seed(4401)
    test_result_index_is_idempotent()
    test_transactional_apply_rolls_back()
    test_serialization_and_metadata_invariants()
    test_finish_bonus_save_compatibility()
    test_world_domain_integrity()
    test_outside_draw_and_full_purse()
    test_scout_auto_assignment_toggle()
    print("PERSISTENCE REGRESSION TEST PASSED")


if __name__ == "__main__":
    main()
