"""Regression coverage for the persisted spectator stop-policy seam."""

import random
import unittest
from unittest.mock import patch

from constants import GAME_VERSION
from world import WorldMixin
from views import ViewMixin


class PauseProbe(WorldMixin):
    def __init__(self):
        self.rules = {}
        self.month = 1
        self.week = 1
        self.ai_event_archive = []
        self.event_log = []


class RuleDefaultsProbe(ViewMixin):
    def __init__(self, policy):
        self.rules = {"simulation_pause_policy": policy}

    def ensure_audio_defaults(self):
        return None


class LabelProbe:
    def __init__(self):
        self.text = ""

    def config(self, **kwargs):
        self.text = str(kwargs.get("text", ""))


class SimulationPausePolicyTests(unittest.TestCase):
    def test_target_policy_is_data_and_uses_exact_calendar_boundary(self):
        probe = PauseProbe()
        policy = probe.set_spectator_pause_policy(target=(3, 2))
        self.assertTrue(policy["enabled"])
        self.assertEqual(policy["target"], [3, 2])
        probe.month, probe.week = 3, 1
        self.assertEqual(probe.evaluate_simulation_pause_policy(), "")
        probe.week = 2
        self.assertEqual(probe.evaluate_simulation_pause_policy(), "Reached target Mar W2 2026")

    def test_event_policy_uses_new_archive_rows_without_rng(self):
        probe = PauseProbe()
        probe.set_spectator_pause_policy(stop_on_event=True)
        state = random.getstate()
        self.assertEqual(probe.evaluate_simulation_pause_policy(), "")
        self.assertEqual(state, random.getstate())
        probe.ai_event_archive.append({"company": "North Star MMA", "date": "Month 1 Week 2", "event_name": "NS 1", "summary": "A card", "fight_count": 2})
        self.assertIn("New hosted event recorded", probe.evaluate_simulation_pause_policy())
        self.assertEqual(state, random.getstate())

    def test_watched_company_and_fighter_filters_are_record_bound(self):
        probe = PauseProbe()
        probe.ai_event_archive.append({
            "company": "North Star MMA", "date": "Month 1 Week 2", "event_name": "NS 1",
            "summary": "A card", "fight_count": 1,
            "fight_logs": [{"a_id": "fighter-7", "b_id": "fighter-8"}],
        })
        probe.set_spectator_pause_policy(stop_on_event=True, watched_company_names=["North Star MMA"], watched_fighter_ids=["fighter-7"])
        # Setting the cursor after the archive is intentional: the policy is
        # armed from the committed current boundary, so old rows do not fire.
        self.assertEqual(probe.evaluate_simulation_pause_policy(), "")
        probe.ai_event_archive.insert(0, {
            "company": "North Star MMA", "date": "Month 1 Week 3", "event_name": "NS 2",
            "summary": "A card", "fight_count": 1,
            "fight_logs": [{"a_id": "fighter-7", "b_id": "fighter-9"}],
        })
        self.assertIn("North Star MMA", probe.evaluate_simulation_pause_policy())

    def test_non_matching_event_does_not_pause(self):
        probe = PauseProbe()
        probe.set_spectator_pause_policy(stop_on_event=True, watched_company_names=["North Star MMA"])
        probe.ai_event_archive.append({"company": "South Coast FC", "date": "Month 1 Week 2", "event_name": "SC 1", "summary": "A card", "fight_count": 1})
        self.assertEqual(probe.evaluate_simulation_pause_policy(), "")

    def test_policy_clear_is_idempotent_and_refreshes_cursor(self):
        probe = PauseProbe()
        probe.set_spectator_pause_policy(target=(2, 1), stop_on_event=True)
        self.assertTrue(probe.clear_spectator_pause_policy())
        self.assertFalse(probe.rules["simulation_pause_policy"]["enabled"])
        self.assertTrue(probe.clear_spectator_pause_policy())

    def test_event_cursor_is_stable_across_reload_shaped_data(self):
        probe = PauseProbe()
        probe.ai_event_archive.append({"company": "North Star MMA", "date": "Month 1 Week 2", "event_name": "NS 1", "summary": "A card", "fight_count": 1})
        saved = probe.set_spectator_pause_policy(stop_on_event=True)
        reloaded = PauseProbe()
        reloaded.rules = {"simulation_pause_policy": dict(saved)}
        reloaded.ai_event_archive = list(probe.ai_event_archive)
        self.assertEqual(reloaded.evaluate_simulation_pause_policy(), "")

    def test_new_policy_records_source_revision_and_legacy_policy_remains_compatible(self):
        probe = PauseProbe()
        policy = probe.set_spectator_pause_policy(target=(2, 1))
        self.assertEqual(policy["source_revision"], str(GAME_VERSION))
        legacy = dict(policy)
        legacy.pop("source_revision")
        reloaded = PauseProbe()
        reloaded.rules = {"simulation_pause_policy": legacy}
        reloaded.month, reloaded.week = 2, 1
        self.assertIn("Reached target", reloaded.evaluate_simulation_pause_policy())

    def test_rule_default_projection_preserves_saved_source_revision(self):
        probe = RuleDefaultsProbe({"enabled": True, "target": [3, 1], "source_revision": "old-build"})
        ViewMixin.ensure_rule_defaults(probe)
        policy = probe.rules["simulation_pause_policy"]
        self.assertEqual(policy["source_revision"], "old-build")
        self.assertEqual(policy["target"], [3, 1])

    def test_legacy_rule_default_projection_adds_compatible_empty_revision(self):
        probe = RuleDefaultsProbe({"enabled": True, "target": [2, 4]})
        ViewMixin.ensure_rule_defaults(probe)
        self.assertEqual(probe.rules["simulation_pause_policy"]["source_revision"], "")

    def test_policy_status_reader_keeps_malformed_target_explicit(self):
        probe = PauseProbe()
        probe.spectator_policy_status = LabelProbe()
        probe.rules = {"simulation_pause_policy": {"enabled": True, "target": ["not-a-month", {}]}}
        probe.refresh_spectator_pause_policy_ui()
        self.assertIn("Date target unavailable", probe.spectator_policy_status.text)

    def test_policy_status_reader_surfaces_revision_mismatch_without_rewriting(self):
        probe = PauseProbe()
        probe.spectator_policy_status = LabelProbe()
        policy = {"enabled": True, "target": [3, 1], "source_revision": "old-build"}
        probe.rules = {"simulation_pause_policy": policy}
        probe.refresh_spectator_pause_policy_ui()
        self.assertIn("different game revision", probe.spectator_policy_status.text)
        self.assertEqual(probe.rules["simulation_pause_policy"], policy)

    def test_revision_mismatch_blocks_resume_and_fast_forward_without_rewriting_policy(self):
        probe = PauseProbe()
        probe.spectator_mode = True
        policy = probe.set_spectator_pause_policy(target=(3, 1))
        policy["source_revision"] = "old-build"
        probe.rules["simulation_pause_policy"] = policy
        before = dict(policy)
        with patch.object(probe, "begin_advance_sequence", side_effect=AssertionError("mismatched policy advanced")):
            self.assertFalse(probe.spectator_advance_weeks(1))
        self.assertFalse(probe.resume_spectator_simulation())
        self.assertEqual(probe.rules["simulation_pause_policy"], before)

    def test_direct_advance_entry_cannot_bypass_revision_guard(self):
        probe = PauseProbe()
        probe.spectator_mode = True
        policy = probe.set_spectator_pause_policy(target=(3, 1))
        policy["source_revision"] = "old-build"
        probe.rules["simulation_pause_policy"] = policy
        before = dict(policy)
        with patch.object(probe, "spectator_inline_notice", return_value=False) as notice:
            self.assertFalse(probe.begin_advance_sequence(1))
        notice.assert_called_once()
        self.assertEqual(probe.rules["simulation_pause_policy"], before)

    def test_spectator_precondition_notices_use_the_inline_surface(self):
        probe = PauseProbe()
        with patch("world.messagebox.showinfo", side_effect=AssertionError("routine spectator notice opened a modal")):
            self.assertFalse(probe.spectator_advance_weeks(1))
            self.assertFalse(probe.resume_spectator_simulation())
            self.assertFalse(probe.watch_latest_world_event())
            self.assertFalse(probe.spectator_watch_next_event())


if __name__ == "__main__":
    unittest.main()
