"""Regression coverage for canonical player and promotion finance ledgers."""

from models import Promotion
from world import WorldMixin


class FinanceProbe(WorldMixin):
    def __init__(self):
        self.month = 4
        self.week = 2
        self.cash = 10_000
        self.player_company_name = "Probe FC"
        self.finance = {
            "ledger": [], "week_transactions": [], "weekly_history": [],
        }
        self.promotions = []
        self.change_journal = []

    def ensure_finance_defaults(self):
        self.finance.setdefault("ledger", [])
        self.finance.setdefault("week_transactions", [])
        self.finance.setdefault("weekly_history", [])

    def record_change(self, *_args):
        return None


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    probe = FinanceProbe()
    probe.cash += 2_000
    probe.record_finance_transaction(
        "Test event receipt", revenue=2_000, category="Event", source="Gate",
        counterparty="Test venue", event="Test Card", reference="event:test-card",
    )
    row = probe.finance["week_transactions"][-1]
    require(
        all(row.get(key) for key in ("id", "category", "source", "counterparty", "event", "reference")),
        "canonical player transaction metadata is incomplete",
    )
    # Simulate a legacy/direct cash mutation. Weekly close must make the
    # adjustment explicit and leave the balance mathematically reconciled.
    probe.finance["weekly_history"].append({"month": 4, "week": 1, "opening": 10_000, "revenue": 0, "costs": 0, "ending": 10_000})
    probe.cash -= 125
    probe.close_finance_week()
    latest = probe.finance["weekly_history"][-1]
    require(latest["opening"] + latest["revenue"] - latest["costs"] == latest["ending"], "player weekly ledger does not reconcile to cash")
    repair = next(row for row in latest["transactions"] if row.get("category") == "Reconciliation")
    require(repair["costs"] == 125 and repair["reference"].startswith("reconcile:player:"), "direct player cash mutation was not repaired canonically")
    transaction_count = len(probe.finance["week_transactions"])
    probe.close_finance_week()
    require(len(probe.finance["week_transactions"]) == transaction_count, "repeated player finance close created duplicate repair transactions")

    child = Promotion("Probe Development", "USA", 30, 50_000, [], is_child_promotion=True, parent_company="Probe FC")
    probe.promotions = [child]
    child.cash += 8_000
    probe.record_promotion_finance_transaction(
        child, "Child event receipt", revenue=8_000, category="Event", source="Gate",
        counterparty=child.name, event="Child Card", reference="child-event:test-card",
    )
    child.finance["weekly_history"].append({"month": 4, "week": 1, "opening": 50_000, "revenue": 0, "costs": 0, "ending": 50_000})
    child.cash -= 300
    probe.close_promotion_finance_week(child)
    child_row = child.finance["weekly_history"][-1]
    require(child_row["opening"] + child_row["revenue"] - child_row["costs"] == child_row["ending"], "child weekly ledger does not reconcile to cash")
    require(probe.finance_reconciliation_status(child.finance, child.cash)["balanced"], "child finance status reports an unbalanced ledger")
    require(any(row.get("category") == "Reconciliation" for row in child_row["transactions"]), "direct child cash mutation was not recorded")
    child_transaction_count = len(child.finance["week_transactions"])
    probe.close_promotion_finance_week(child)
    require(len(child.finance["week_transactions"]) == child_transaction_count, "repeated child finance close created duplicate repair transactions")
    print("Finance audit regression tests passed.")


if __name__ == "__main__":
    main()
