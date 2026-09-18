"""Regression coverage for the J2 event-preparation read model."""

import copy
import random
import unittest

from events import EventMixin


class PreparationHarness(EventMixin):
    def __init__(self):
        self.finance = {
            "media_primary_plan": {
                "plan_id": "media-plan-7",
                "target_id": "event-7",
                "objective": "Sell the regional rivalry",
                "action_receipts": [
                    {"action": "press_push", "evidence_key": "media-action:event-7:press"},
                    {"action": "fan_poll", "evidence_key": "media-action:event-7:poll"},
                ],
            }
        }


class EventPreparationTimelineTests(unittest.TestCase):
    def event(self):
        return {
            "event_id": "event-7",
            "name": "Regional Collision",
            "fights": [
                {"fighters": ["Asha Vale", "TBA"], "fighter_ids": ["f-1", ""]},
                {"fighters": ["Asha Vale", "Mina Kaur"], "fighter_ids": ["f-1", "f-2"]},
                {"fighters": ["Mina Kaur", "Asha Vale"], "fighter_ids": ["f-2", "f-1"]},
            ],
        }

    def test_timeline_is_identity_linked_ordered_and_does_not_mutate_inputs(self):
        app = PreparationHarness()
        event = self.event()
        before = copy.deepcopy(event)
        press = ["PRESS CONFERENCE & FACE-OFFS", "Asha Vale works the microphone hard."]
        weigh = ["WEIGH-INS", "Asha Vale made Featherweight at 145 lb."]
        cancelled = [event["fights"][0]]
        rng_before = random.getstate()

        timeline = app.event_preparation_timeline(event, press_log=press, weigh_log=weigh, cancelled_fights=cancelled)

        self.assertEqual(event, before)
        self.assertEqual(random.getstate(), rng_before)
        self.assertEqual(timeline["event_id"], "event-7")
        self.assertEqual(timeline["fighter_ids"], ["f-1", "f-2"])
        self.assertEqual(timeline["press_outcomes"], press)
        self.assertEqual(timeline["weigh_in_outcomes"], weigh)
        self.assertEqual(timeline["cancelled_bout_count"], 1)
        self.assertEqual(timeline["final_readiness"], "Ready with 1 cancelled bout(s)")
        self.assertEqual(timeline["completion_keys"], {
            "campaign": "event-preparation:event-7:campaign:r1",
            "press": "event-preparation:event-7:press:r1",
            "weigh_in": "event-preparation:event-7:weigh_in:r1",
            "readiness": "event-preparation:event-7:readiness:r1",
        })
        self.assertEqual([row["stage_id"] for row in timeline["stage_states"]], ["campaign", "press", "weigh_in", "readiness"])
        self.assertEqual([row["evidence_key"] for row in timeline["campaign_evidence"]], [
            "media-action:event-7:press", "media-action:event-7:poll",
        ])

    def test_missing_outcomes_are_explicit_and_unlinked_campaign_is_not_fabricated(self):
        app = PreparationHarness()
        event = self.event()
        app.finance["media_primary_plan"]["target_id"] = "different-event"
        timeline = app.event_preparation_timeline(event)
        statuses = {row["stage_id"]: row["status"] for row in timeline["stage_states"]}
        self.assertEqual(statuses["campaign"], "No linked campaign evidence")
        self.assertEqual(statuses["press"], "No recorded outcome")
        self.assertEqual(statuses["weigh_in"], "No recorded outcome")
        self.assertEqual(statuses["readiness"], "No weigh-in outcome recorded")
        self.assertEqual(timeline["campaign_evidence"], [])
        self.assertEqual(timeline["completion_keys"], {})
        self.assertEqual(timeline["fighter_ids"], ["f-1", "f-2"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
