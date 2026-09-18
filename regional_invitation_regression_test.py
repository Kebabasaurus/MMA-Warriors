"""Regression coverage for the deterministic J9.b regional host invitation."""

import copy
import random
import unittest
from types import SimpleNamespace

from world import WorldMixin


def fighter(name, fighter_id, region="USA"):
    return SimpleNamespace(
        name=name, fighter_id=fighter_id, region=region, gender="Male",
        weight="Lightweight", retired=False, retirement_pending=False,
        injured=0, fatigue=0, available_week=0, available_day=0,
        champion=False, ranking_position=8, purse=2_000,
    )


class RegionalInvitationHarness(WorldMixin):
    def __init__(self):
        self.month, self.week = 1, 1
        self.player_region = "USA"
        self.player_company_name = "Player FC"
        self.company_pop = 38
        self.company_stability = 60
        self.spectator_mode = False
        self.finance = {"production_base": 24_000}
        self.regions = {
            "USA": {"economy": "stable", "legality": "Legal", "mma_love": 70,
                     "drug_accuracy": 90, "promo_benefit": {"gate": 1.0, "media": 1.0},
                     "areas": ["Nevada"]},
            "UK": {"economy": "stable", "legality": "Legal", "mma_love": 50,
                   "drug_accuracy": 80, "promo_benefit": {"gate": 1.0, "media": 1.0},
                   "areas": ["England"]},
        }
        self.roster = [fighter("Local One", "f-1"), fighter("Local Two", "f-2"), fighter("Visitor", "f-3", "UK")]
        self.free_agents = []
        self.scheduled_events = []
        self.regional_invitations = []
        self.regional_invitation_history = []
        self.news = []
        self.inbox = []
        self.cash = 100_000
        self.finance.setdefault("week_transactions", [])
        self.finance.setdefault("ledger", [])
        self.change_journal = []

    def format_game_date(self, month, week, **_kwargs):
        return f"Month {int(month)} Week {int(week)}"

    def record_change(self, *args, **kwargs):
        self.change_journal.append((args, kwargs))

    def venue_region(self, venue):
        return "USA" if venue in {"Local Gym", "Regional Arena", "Casino Ballroom", "National Sports Hall"} else ""

    def ensure_finance_defaults(self):
        self.finance.setdefault("week_transactions", [])
        self.finance.setdefault("ledger", [])


class RegionalInvitationTests(unittest.TestCase):
    def test_generation_is_deterministic_quarter_limited_and_eight_weeks_out(self):
        app = RegionalInvitationHarness()
        before = random.getstate()
        offer = app.generate_regional_invitation()
        self.assertIsNotNone(offer)
        self.assertEqual(offer["region"], "USA")
        self.assertEqual((offer["event_month"], offer["event_week"]), (3, 1))
        self.assertEqual(offer["expires_week"], 5)
        self.assertEqual(offer["guarantee"], min(25_000, round(offer["fixed_component_quote"] * 0.10)))
        self.assertEqual(random.getstate(), before)
        self.assertIsNone(app.generate_regional_invitation())
        accepted, _note = app.accept_regional_invitation(offer["invitation_id"])
        self.assertTrue(accepted)
        self.assertIsNone(app.generate_regional_invitation(force=True))

    def test_binding_and_paid_settlement_use_one_entitlement(self):
        app = RegionalInvitationHarness()
        offer = app.generate_regional_invitation(force=True)
        self.assertTrue(app.accept_regional_invitation(offer["invitation_id"])[0])
        event = {
            "event_id": "event-regional", "region": offer["region"], "venue": offer["venue"],
            "month": offer["event_month"], "week": offer["event_week"],
        }
        self.assertIs(app.bind_regional_invitation_to_event(event), offer)
        self.assertEqual(event["regional_invitation_entitlement_key"], offer["entitlement_key"])
        package = {
            "event_name": "Regional Card", "profit": 500,
            "finance": {"total_revenue": 1_000, "profit": 500},
            "results": [(app.roster[0], app.roster[2], {}, "Decision"),
                        (app.roster[1], app.roster[2], {}, "Decision")],
        }
        before_cash = app.cash
        closed = app.settle_regional_invitation(event, package)
        self.assertEqual(closed["status"], "Paid")
        self.assertEqual(closed["guarantee_paid"], offer["guarantee"])
        self.assertEqual(app.cash, before_cash + offer["guarantee"])
        self.assertEqual(package["regional_host_guarantee"], offer["guarantee"])
        self.assertEqual(package["finance"]["total_revenue"], 1_000 + offer["guarantee"])
        self.assertIsNone(app.settle_regional_invitation(event, package))
        self.assertEqual(app.cash, before_cash + offer["guarantee"])

    def test_unfulfilled_and_cancelled_invites_pay_zero(self):
        app = RegionalInvitationHarness()
        offer = app.generate_regional_invitation(force=True)
        self.assertTrue(app.accept_regional_invitation(offer["invitation_id"])[0])
        event = {"event_id": "event-empty", "region": offer["region"], "venue": offer["venue"],
                 "month": offer["event_month"], "week": offer["event_week"]}
        app.bind_regional_invitation_to_event(event)
        package = {"event_name": "Empty Card", "profit": 0, "finance": {}, "results": [(app.roster[2], app.roster[2], {}, "Decision")]}
        before_cash = app.cash
        closed = app.settle_regional_invitation(event, package)
        self.assertEqual(closed["status"], "Unfulfilled")
        self.assertEqual(closed["guarantee_paid"], 0)
        self.assertEqual(app.cash, before_cash)

        app2 = RegionalInvitationHarness()
        offer2 = app2.generate_regional_invitation(force=True)
        self.assertTrue(app2.accept_regional_invitation(offer2["invitation_id"])[0])
        event2 = {"event_id": "event-cancel", "regional_invitation_id": offer2["invitation_id"]}
        closed2 = app2.cancel_regional_invitation_for_event(event2, "Player cancelled")
        self.assertEqual(closed2["status"], "Cancelled")
        self.assertEqual(closed2["guarantee_paid"], 0)

    def test_expiry_is_terminal_without_penalty_and_malformed_quote_blocks_offer(self):
        app = RegionalInvitationHarness()
        offer = app.generate_regional_invitation(force=True)
        app.month, app.week = 2, 2  # absolute week 6, one week beyond expiry
        before_cash = app.cash
        expired = app.expire_regional_invitations()
        self.assertEqual(expired[0]["status"], "Expired")
        self.assertEqual(app.cash, before_cash)
        self.assertEqual(app.regional_invitation_history[0]["invitation_id"], offer["invitation_id"])

        blocked = RegionalInvitationHarness()
        blocked.finance["production_base"] = "unknown"
        self.assertIsNone(blocked.generate_regional_invitation(force=True))
        self.assertEqual(blocked.regional_invitations, [])

    def test_expiry_holds_malformed_saved_boundary_for_review(self):
        app = RegionalInvitationHarness()
        malformed = {
            "invitation_id": "RI-malformed-expiry", "status": "Offered",
            "region": "USA", "venue": "Regional Arena", "expires_week": "unknown",
        }
        app.regional_invitations = [malformed]
        closed = app.expire_regional_invitations()
        self.assertEqual(closed, [])
        self.assertIs(app.regional_invitations[0], malformed)
        self.assertTrue(malformed["invitation_review_required"])
        self.assertIn("expiry", malformed["invitation_review_reason"])

    def test_binding_holds_malformed_guarantee_without_mutating_event(self):
        app = RegionalInvitationHarness()
        malformed = {
            "invitation_id": "RI-malformed-bind", "status": "Accepted",
            "region": "USA", "venue": "Regional Arena", "event_month": 3,
            "event_week": 1, "guarantee": "unknown", "minimum_local_completers": 2,
        }
        app.regional_invitations = [malformed]
        event = {"event_id": "event-malformed-bind", "region": "USA", "venue": "Regional Arena", "month": 3, "week": 1}
        before = copy.deepcopy(event)
        self.assertIsNone(app.bind_regional_invitation_to_event(event))
        self.assertEqual(event, before)
        self.assertTrue(malformed["invitation_review_required"])

    def test_settlement_holds_malformed_results_without_payout(self):
        app = RegionalInvitationHarness()
        malformed = {
            "invitation_id": "RI-malformed-settle", "status": "Scheduled",
            "region": "USA", "venue": "Regional Arena", "guarantee": 10_000,
            "minimum_local_completers": 2,
        }
        app.regional_invitations = [malformed]
        package = {"event_name": "Broken Card", "results": "not-a-result-list", "finance": {}}
        before_cash = app.cash
        self.assertIsNone(app.settle_regional_invitation({"regional_invitation_id": malformed["invitation_id"]}, package))
        self.assertEqual(app.cash, before_cash)
        self.assertTrue(malformed["invitation_review_required"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
