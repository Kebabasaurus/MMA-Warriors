"""Regression coverage for non-modal calendar progression summaries."""

from world import WorldMixin
from views import ViewMixin


class AdvanceNoticeProbe(WorldMixin, ViewMixin):
    def __init__(self):
        self.inbox = []
        self.news = []
        self.pending_final_month_contract_alerts = []
        self.pending_broadcast_notices = []

    def broadcast_contract_months_left(self, row):
        return row.get("months", 1)


def test_routine_notices_become_one_inbox_summary():
    probe = AdvanceNoticeProbe()
    probe.pending_final_month_contract_alerts = [{
        "name": "Alex Example", "gender": "Male", "weight": "Lightweight",
        "champion": True, "purse": 12000,
    }]
    probe.pending_broadcast_notices = [
        ("expired", {"name": "Old Network", "reach": 30}),
        ("expiring", {"name": "Current Network", "months": 1}),
    ]

    probe.show_final_month_contract_alerts()
    probe.show_pending_broadcast_notices()
    assert len(probe.inbox) == 0, "Routine notices should wait for the summary presenter"
    probe.present_advance_notice_summary()

    assert len(probe.inbox) == 1
    assert probe.inbox[0]["subject"] == "Calendar advance summary"
    assert "Final-month contracts" in probe.inbox[0]["body"]
    assert "Broadcast contracts" in probe.inbox[0]["body"]
    assert len(probe.news) == 1
    assert probe.advance_notice_queue == []


def test_summary_presenter_is_idempotent_when_empty():
    probe = AdvanceNoticeProbe()
    probe.present_advance_notice_summary()
    probe.present_advance_notice_summary()
    assert probe.inbox == []
    assert probe.news == []


if __name__ == "__main__":
    test_routine_notices_become_one_inbox_summary()
    test_summary_presenter_is_idempotent_when_empty()
    print("ADVANCE NOTIFICATION REGRESSION TEST PASSED")
