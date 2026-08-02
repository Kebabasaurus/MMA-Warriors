"""Focused regressions for player contracts, booking identity, and event pay."""

from dataclasses import asdict

from events import EventMixin
from models import Fighter


class ContractEventProbe(EventMixin):
    def __init__(self):
        self.promotions = []
        self.roster = []
        self.finance = {"tax_rate": 0.10}
        self.inbox = []

    def get_fighter(self, reference):
        return next(
            (fighter for fighter in self.roster
             if fighter.fighter_id == reference or fighter.name == reference),
            None,
        )


def fighter(name, purse=10_000):
    return Fighter(name, "Lightweight", 28, 8, 2, 70, 70, 70, 70, 70, 45, 1, 70, purse)


def assert_contract_validation(probe):
    safe = probe.validated_contract_terms(10_000, 120, 3, 5_000, 20, 4_000, 2)
    assert safe["months"] == 60
    assert probe.validated_contract_terms(10_000, -12, 3)["months"] == 1
    for field, values in {
        "purse": (-1, 12, 3, 0, 0, 0, 0),
        "guaranteed fights": (10_000, 12, -1, 0, 0, 0, 0),
        "signing bonus": (10_000, 12, 3, -1, 0, 0, 0),
        "finish bonus": (10_000, 12, 3, 0, -1, 0, 0),
        "win bonus": (10_000, 12, 3, 0, 0, -1, 0),
        "PPV points": (10_000, 12, 3, 0, 0, 0, -1),
    }.items():
        try:
            probe.validated_contract_terms(*values)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Negative {field} was accepted")
    upfront = safe["purse"] * 2 + safe["signing_bonus"]
    assert upfront == 25_000 and upfront >= 0


def assert_booking_identity(probe):
    first = fighter("Same Name")
    second = fighter("Same Name")
    probe.roster = [first, second]
    distinct = [
        {"fighters": [first.name, "Opponent A"], "fighter_ids": [first.fighter_id, "opponent-a"]},
        {"fighters": [second.name, "Opponent B"], "fighter_ids": [second.fighter_id, "opponent-b"]},
    ]
    assert probe.duplicate_event_participant_references(distinct) == set()
    repeated = distinct + [{"fighters": [first.name, "Opponent C"], "fighter_ids": [first.fighter_id, "opponent-c"]}]
    assert probe.duplicate_event_participant_references(repeated) == {first.fighter_id}


def assert_finance_and_guarantees(probe):
    winner = fighter("Winner", 10_000)
    loser = fighter("Loser", 8_000)
    winner.win_bonus = 2_000
    winner.finish_bonus_pct = 20
    winner.ppv_points = 2
    loser.ppv_points = 1
    probe.roster = [winner, loser]
    result = [(winner, loser, {"fighters": [winner.name, loser.name]}, "TKO")]
    finance = {
        "ticket_revenue": 100_000,
        "broadcast_income": 50_000,
        "total_revenue": 150_000,
        "bonuses": 10_000,
        "tax": 5_000,
        "total_expense": 50_000,
    }
    awards = [{"award": "Fight of the Night", "fighters": [winner.name, loser.name], "bonus": 500}]
    probe.finalize_event_fight_pay(finance, result, awards)
    assert finance["bonuses"] == 1_000
    assert finance["win_bonuses"] == 2_000
    assert finance["finish_bonuses"] == 2_000
    assert finance["ppv_points_payout"] == 4_500
    assert finance["contract_clauses"] == 8_500
    assert finance["total_expense"] == 55_050
    assert finance["profit"] == 94_950

    cancelled = {
        "ticket_revenue": 100_000, "broadcast_income": 50_000,
        "total_revenue": 150_000, "bonuses": 10_000,
        "tax": 5_000, "total_expense": 50_000,
    }
    probe.finalize_event_fight_pay(cancelled, [], [])
    assert cancelled["bonuses"] == 0
    assert cancelled["contract_clauses"] == 0
    assert cancelled["profit"] == 103_500

    winner.guaranteed_fights = 2
    winner.contract_fights_completed = 0
    assert probe.record_standard_guaranteed_fight(winner) == 1
    assert probe.record_standard_guaranteed_fight(winner) == 0
    assert winner.contract_fights_completed == 2
    assert winner.relationship_trust == 61
    assert any("Guarantee Fulfilled" in row["subject"] for row in probe.inbox)


def main():
    probe = ContractEventProbe()
    assert_contract_validation(probe)
    assert probe.contract_rival_candidate() is None
    assert_booking_identity(probe)
    assert_finance_and_guarantees(probe)
    round_trip = Fighter(**asdict(probe.roster[0]))
    assert round_trip.finish_bonus_pct == probe.roster[0].finish_bonus_pct
    assert probe.player_bout_purse_cost({"tier": "Early Prelims"}, *probe.roster) == 18_000
    print("Contracts and event finance regression tests passed.")


if __name__ == "__main__":
    main()
