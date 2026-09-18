"""Focused regressions for Fight Night presentation state and accessibility."""

from pathlib import Path
import random
import threading
import unittest

from events import EventMixin


ROOT = Path(__file__).resolve().parent


class FakeWindow:
    def __init__(self, exists=True):
        self.exists = exists
        self.actions = []

    def winfo_exists(self):
        return self.exists

    def deiconify(self):
        self.actions.append("deiconify")

    def lift(self):
        self.actions.append("lift")

    def focus_force(self):
        self.actions.append("focus")


class FightNightStateTests(unittest.TestCase):
    def test_event_transaction_snapshot_excludes_live_audio_stop_event(self):
        probe = object.__new__(EventMixin)
        probe.persistent_value = {"settled": False}
        probe._fight_night_audio_session_stop = threading.Event()
        probe._fight_night_audio_rng = random.SystemRandom()

        snapshot = probe.capture_event_transaction_state()

        self.assertEqual(snapshot["persistent_value"], {"settled": False})
        self.assertNotIn("_fight_night_audio_session_stop", snapshot)
        self.assertNotIn("_fight_night_audio_rng", snapshot)

    def test_detailed_commentary_returns_an_unmodified_copy(self):
        lines = [
            "Round 1: Fighters meet at centre.",
            "  [4:52] Single jab — Red lands clean. [target head; defense outside parry; next counter available]",
            "Round 1 summary: Broadcast read - Red is ahead; official cards remain sealed.",
        ]

        rendered = EventMixin.fight_night_commentary_lines(lines, mode="Detailed")

        self.assertEqual(rendered, lines)
        self.assertIsNot(rendered, lines)
        self.assertEqual(
            lines[1],
            "  [4:52] Single jab — Red lands clean. [target head; defense outside parry; next counter available]",
        )

    def test_broadcast_commentary_compacts_repetition_without_losing_fight_evidence(self):
        repeated_round_one = [
            f"  [4:{50 - index:02d}] Composed survival — Red circles and both fighters reset. "
            "[target head; defense technical scramble; next follow-up pressure]"
            for index in range(8)
        ]
        repeated_round_two = [
            f"  [4:{40 - index:02d}] Composed survival — Red circles and both fighters reset. "
            "[target head; defense technical scramble; next follow-up pressure]"
            for index in range(8)
        ]
        protected_lines = [
            "  [3:44] Blue scores a knockdown with the right hand.",
            "  [3:12] Red locks a dangerous submission attempt.",
            "  [2:49] An elbow opens a cut over Blue's eye.",
            "  [2:03] The referee warns Red for a foul.",
            "  [1:18] Blue finishes the fight with unanswered strikes.",
            "Official scorecards:",
            "Judge 1 [Measured]: 50-45 Red",
            "FIGHT METRICS",
            "Result: Red def. Blue by Decision R5",
        ]
        lines = [
            "Tale of the tape: Red vs Blue.",
            "Round 1: Fighters meet at centre.",
            *repeated_round_one,
            *protected_lines[:4],
            "Round 1 summary: Broadcast read - Red is ahead; official cards remain sealed.",
            "Between rounds: Blue's corner asks for more urgency.",
            "Round 2: The fight resumes.",
            *repeated_round_two,
            protected_lines[4],
            "Round 2 summary: Broadcast read - Red stays ahead; official cards remain sealed.",
            *protected_lines[5:],
        ]

        rendered = EventMixin.fight_night_commentary_lines(lines, mode="Broadcast")

        self.assertEqual(lines[0], "Tale of the tape: Red vs Blue.")
        for structural in (
            "Tale of the tape: Red vs Blue.",
            "Round 1: Fighters meet at centre.",
            "Round 1 summary: Broadcast read - Red is ahead; official cards remain sealed.",
            "Between rounds: Blue's corner asks for more urgency.",
            "Round 2: The fight resumes.",
            "Round 2 summary: Broadcast read - Red stays ahead; official cards remain sealed.",
        ):
            self.assertEqual(rendered.count(structural), 1)
        for evidence in protected_lines:
            self.assertEqual(rendered.count(evidence), 1)

        repeated_calls = [line for line in rendered if "Composed survival" in line]
        self.assertLessEqual(len(repeated_calls), 4)
        self.assertTrue(
            any("quiet" in line.lower() and "summar" in line.lower() for line in rendered),
            "Broadcast mode did not replace suppressed low-value calls with a quiet-action summary",
        )
        self.assertLess(len(rendered), len(lines))
        self.assertEqual(lines, [
            "Tale of the tape: Red vs Blue.",
            "Round 1: Fighters meet at centre.",
            *repeated_round_one,
            *protected_lines[:4],
            "Round 1 summary: Broadcast read - Red is ahead; official cards remain sealed.",
            "Between rounds: Blue's corner asks for more urgency.",
            "Round 2: The fight resumes.",
            *repeated_round_two,
            protected_lines[4],
            "Round 2 summary: Broadcast read - Red stays ahead; official cards remain sealed.",
            *protected_lines[5:],
        ])

    def test_broadcast_compaction_preserves_completed_ground_flow(self):
        routine_standing = [
            f"  [4:{59 - index:02d}] Red probes with standing exchange number {index}."
            for index in range(20)
        ]
        completed_ground_work = [
            "  [4:38] Red completes the double leg and settles in half guard.",
            "  [4:04] The postured ground punches gets through for Red on Blue.",
            "  [3:31] Red uses the butterfly sweep to move the fight from guard to guard.",
            "  [2:58] Red uses the wall walk to escape from half guard to range.",
            "  [2:24] The knee-slice pass carries Red from guard into side control.",
        ]
        completed_standing_work = [
            "  [4:46] Red lands the single jab on Blue's head.",
            "  [3:46] The rear round kick gets through for Red on Blue's body.",
        ]
        denied = [
            f"  [1:{50 - index:02d}] Red attempts the hip-bump sweep from half guard, "
            "but Blue denies the transition."
            for index in range(5)
        ]
        passive = [
            f"  [1:{30 - index:02d}] Red uses defensive ground work to maintain control from half guard."
            for index in range(5)
        ]
        lines = [
            "Round 1: Start.",
            *routine_standing[:2], completed_standing_work[0],
            *routine_standing[2:4], completed_ground_work[0],
            *routine_standing[4:8], completed_ground_work[1],
            *routine_standing[8:10], completed_standing_work[1],
            *routine_standing[10:12], completed_ground_work[2],
            *routine_standing[12:16], completed_ground_work[3],
            *routine_standing[16:], completed_ground_work[4],
            *denied, *passive,
            "Round 1 summary: Red controlled the grappling exchanges.",
            "Result: Red def. Blue by Decision R3",
        ]

        rendered = EventMixin.fight_night_commentary_lines(lines, mode="Broadcast")

        for evidence in completed_ground_work:
            self.assertIn(evidence, rendered)
        for evidence in completed_standing_work:
            self.assertIn(evidence, rendered)
        self.assertLessEqual(sum("denies the transition" in line for line in rendered), 2)
        self.assertLessEqual(sum("maintain control from half guard" in line for line in rendered), 2)
        summaries = [line for line in rendered if "Broadcast note:" in line]
        self.assertTrue(summaries)
        self.assertTrue(any("ground-control exchange" in line for line in summaries))
        self.assertFalse(any("reset, hand-fight, and manage position" in line for line in summaries))
        self.assertLess(len(rendered), len(lines))

    def test_broadcast_commentary_removes_only_trailing_technical_suffix(self):
        technical = (
            "  [4:52] Single jab — Red lands clean. "
            "[target head; defense outside parry; next counter available]"
        )
        ordinary_brackets = "Broadcast desk [live]: both fighters look composed."

        rendered = EventMixin.fight_night_commentary_lines(
            ["Round 1: Start.", technical, ordinary_brackets, "Round 1 summary: Even round."],
            mode="Broadcast",
        )

        exchange = next(line for line in rendered if "Single jab" in line)
        self.assertTrue(exchange.startswith("  [4:52] Single jab"))
        self.assertEqual(exchange, "  [4:52] Single jab — Red lands clean.")
        self.assertIn(ordinary_brackets, rendered)

    def test_broadcast_repeat_memory_survives_interleaved_round_flavour(self):
        repeated = "Composed survival — Red circles and both fighters reset."
        flavour = [
            "Red stays patient behind the lead hand.",
            "Blue keeps edging toward the centre logo.",
            "The crowd waits for one fighter to commit.",
        ]
        lines = ["Round 1: Start."]
        for index in range(6):
            lines.append(f"  [4:{50 - index:02d}] {repeated}")
            if index < len(flavour):
                lines.append(flavour[index])
        high_value = "  [3:30] Red drops Blue with a clean right hand."
        lines.extend([high_value, "Round 1 summary: Red edges it.", "Result: Red def. Blue by Decision R3"])

        rendered = EventMixin.fight_night_commentary_lines(lines, mode="Broadcast")

        repeated_calls = [line for line in rendered if repeated in line]
        self.assertEqual(len(repeated_calls), 2)
        for line in flavour:
            self.assertIn(line, rendered)
        self.assertIn("Round 1: Start.", rendered)
        self.assertIn("Round 1 summary: Red edges it.", rendered)
        self.assertIn(high_value, rendered)
        self.assertIn("Result: Red def. Blue by Decision R3", rendered)

    def test_broadcast_repeat_limit_also_applies_to_critical_position_calls(self):
        repeated = "Red stays safe in mount while Blue rebuilds the submission attack."
        lines = ["Round 1: Start."]
        lines.extend(f"  [4:{50 - index:02d}] {repeated}" for index in range(6))
        lines.extend(["Round 1 summary: Red survived the danger.", "Result: Blue def. Red by Decision R3"])

        rendered = EventMixin.fight_night_commentary_lines(lines, mode="Broadcast")

        self.assertEqual(sum(repeated in line for line in rendered), 2)
        self.assertTrue(any("Broadcast note:" in line for line in rendered))
        self.assertIn("Round 1 summary: Red survived the danger.", rendered)

    def test_presentation_logs_do_not_mutate_archived_transcripts(self):
        raw = [{
            "heading": "MAIN EVENT: Red vs Blue",
            "lines": [
                "Round 1: Start.",
                *[f"  [4:{50 - index:02d}] Composed survival — both reset." for index in range(7)],
                "Round 1 summary: Red edges it.",
            ],
            "round_analysis": [{"round": 1}],
        }]
        original_lines = list(raw[0]["lines"])

        presented = EventMixin.fight_night_presentation_logs(raw, mode="Broadcast")

        self.assertIsNot(presented[0], raw[0])
        self.assertIsNot(presented[0]["lines"], raw[0]["lines"])
        self.assertEqual(presented[0]["detailed_lines"], original_lines)
        self.assertLess(len(presented[0]["lines"]), len(original_lines))
        self.assertEqual(raw[0]["lines"], original_lines)
        self.assertNotIn("detailed_lines", raw[0])

    def test_density_switch_maps_active_progress_without_revealing_future_lines(self):
        raw = {
            "heading": "MAIN EVENT: Red vs Blue",
            "lines": [
                "MAIN EVENT: Red vs Blue",
                "Round 1: Start.",
                "  [4:50] Composed survival — both reset. [target head; defense technical scramble]",
                "  [4:40] Composed survival — both reset. [target head; defense technical scramble]",
                "  [4:30] Composed survival — both reset. [target head; defense technical scramble]",
                "Round 1 summary: Red edges it.",
                "Official scorecards:",
                "Judge 1 [Measured]: 50-45 Red",
                "Result: Red def. Blue by Decision R5",
            ],
        }
        original = list(raw["lines"])
        broadcast = EventMixin.fight_night_presentation_logs([raw], mode="Broadcast")[0]
        summary_position = next(
            index for index, line in enumerate(broadcast["lines"])
            if line.startswith("Round 1 summary:")
        )
        active_display_count = summary_position + 1

        source_cutoff = EventMixin.fight_night_source_cutoff(broadcast, active_display_count)
        detailed, detailed_count = EventMixin.fight_night_presentation_progress(
            raw, "Detailed", source_cutoff,
        )

        self.assertEqual(detailed["lines"][:detailed_count], original[:source_cutoff])
        self.assertNotIn("Official scorecards:", detailed["lines"][:detailed_count])
        self.assertFalse(any(line.startswith("Result:") for line in detailed["lines"][:detailed_count]))
        self.assertEqual(raw["lines"], original)
        self.assertNotIn("detailed_lines", raw)

        completed, completed_count = EventMixin.fight_night_presentation_progress(
            raw, "Detailed", len(original),
        )
        self.assertEqual(completed_count, len(original))
        self.assertEqual(completed["lines"], original)

    def test_watch_reuses_matching_window_before_preparing_package(self):
        probe = object.__new__(EventMixin)
        event = {"name": "BAMMA 1", "month": 2, "week": 3}
        window = FakeWindow()
        probe._active_live_fight_window = window
        probe._active_live_fight_event_key = probe.fight_night_event_key(event)
        probe.selected_due_event = lambda: event
        prepared = []
        opened = []
        probe.prepare_event_result = lambda selected: prepared.append(selected)
        probe.open_live_fight_window = lambda selected, package: opened.append((selected, package))

        probe.watch_due_event()

        self.assertEqual(prepared, [])
        self.assertEqual(opened, [])
        self.assertEqual(window.actions, ["deiconify", "lift", "focus"])

    def test_due_prompt_guards_before_preparing_live_package(self):
        source = (ROOT / "events.py").read_text(encoding="utf-8")
        prompt = source[source.index("    def prompt_due_event"):source.index("    def evolve_trait_from_camp")]
        guard = prompt.index("if self.focus_active_live_fight_window():")
        prepare = prompt.index("package = self.prepare_event_result(event)")
        self.assertLess(guard, prepare)

    def test_bout_completion_blocks_advancing_and_future_reviews(self):
        logs = [
            {"lines": ["one", "two"]},
            {"lines": ["three"]},
        ]
        active = {"fight": 0, "line": 1, "finished": False}
        self.assertFalse(EventMixin.fight_night_bout_complete(active, logs))
        self.assertFalse(EventMixin.fight_night_can_review(active, logs, 0))
        self.assertFalse(EventMixin.fight_night_can_review(active, logs, 1))

        active["line"] = 2
        self.assertTrue(EventMixin.fight_night_bout_complete(active, logs))
        self.assertTrue(EventMixin.fight_night_can_review(active, logs, 0))
        self.assertFalse(EventMixin.fight_night_can_review(active, logs, 1))

    def test_completed_or_skipped_card_unlocks_every_bout_review(self):
        logs = [{"lines": ["one"]}, {"lines": ["two"]}]
        finished = {"fight": 0, "line": 0, "finished": True}
        self.assertTrue(EventMixin.fight_night_can_review(finished, logs, 0))
        self.assertTrue(EventMixin.fight_night_can_review(finished, logs, 1))

    def test_failed_commit_reports_error_without_claiming_success(self):
        probe = object.__new__(EventMixin)

        def fail(_event, _package):
            raise RuntimeError("archive unavailable")

        probe.finish_event = fail
        committed, error = probe.commit_live_fight_package({}, {}, apply_results=True)
        self.assertFalse(committed)
        self.assertEqual(error, "archive unavailable")
        self.assertEqual(probe.commit_live_fight_package({}, {}, apply_results=False), (True, ""))

    def test_duplicate_names_use_winner_identity_for_each_corner(self):
        probe = object.__new__(EventMixin)
        log = {
            "a": "Alex Lee", "b": "Alex Lee",
            "a_id": "red-id", "b_id": "blue-id",
            "winner": "Alex Lee", "winner_id": "blue-id",
        }
        self.assertEqual(probe.live_fight_corner_outcome(log, "a"), "loss")
        self.assertEqual(probe.live_fight_corner_outcome(log, "b"), "win")

    def test_ambiguous_legacy_winner_does_not_award_both_corners(self):
        probe = object.__new__(EventMixin)
        log = {"a": "Alex Lee", "b": "Alex Lee", "result": "Alex Lee - Decision R3"}
        self.assertEqual(probe.live_fight_corner_outcome(log, "a"), "unknown")
        self.assertEqual(probe.live_fight_corner_outcome(log, "b"), "unknown")

    def test_round_analysis_formats_recorded_moves_defenses_and_changes(self):
        row = {
            "round": 2,
            "corners": {
                "a": {"effective": 3, "attempts": 5, "moves": {"one_two": 2},
                      "defenses": {"outside_parry": 1}, "sequences": [{"source": "single_jab", "move": "one_two", "branch": "primary-continuation"}]},
                "b": {"effective": 1, "attempts": 4, "moves": {"double_leg_entry": 2},
                      "defenses": {"hip_sprawl": 1}, "sequences": []},
            },
            "stance_switches": [{"corner": "a", "from": "Orthodox", "to": "Southpaw"}],
            "plan_changes": [{"corner": "b", "plan": "Wrestle early", "reason": "entry success"}],
        }
        rendered = EventMixin.format_round_analysis(row, {"a": "Red", "b": "Blue"})
        self.assertIn("ROUND 2 ANALYSIS", rendered)
        self.assertIn("outside parry", rendered)
        self.assertIn("single jab -> one two", rendered)
        self.assertIn("Orthodox -> Southpaw", rendered)
        self.assertIn("Wrestle early", rendered)


class FightNightSourceInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "events.py").read_text(encoding="utf-8")

    def test_live_controls_have_guards_confirmation_and_shortcuts(self):
        source = self.source
        self.assertIn("Finish or skip the active bout before starting the next fight.", source)
        self.assertIn('skip_event_button.config(text="Confirm Skip Event")', source)
        self.assertIn('window.bind("<Control-n>"', source)
        self.assertIn('window.bind("<Escape>"', source)
        self.assertIn("next_fight_button.focus_set()", source)

    def test_saved_auto_play_starts_and_failed_commit_remains_retryable(self):
        source = self.source
        self.assertIn('if state["auto"]:\n            window.after_idle(start)', source)
        commit_call = source.index("committed, commit_error = self.commit_live_fight_package")
        finished_flag = source.index('state["finished"] = True', commit_call)
        self.assertLess(commit_call, finished_flag)
        self.assertIn('skip_event_button.config(text="Retry End Event")', source)

    def test_round_telemetry_no_longer_depends_on_hidden_score_totals(self):
        source = self.source
        self.assertNotIn('rf"Live score\\s+', source)
        self.assertIn('values.get("a", {})', source)
        self.assertIn('values.get("b", {})', source)

    def test_summary_is_responsive_and_scrollable(self):
        source = self.source
        self.assertIn('summary_height = min(760, max(520, screen_h - 140))', source)
        self.assertIn('summary_canvas.create_window((0, 0), window=content', source)
        self.assertIn('summary_canvas.configure(scrollregion=summary_canvas.bbox("all"))', source)

    def test_review_and_replay_clean_fighter_display_names(self):
        source = self.source
        self.assertIn('return build_event_archive(self, title, package)', source)
        archive = (ROOT / 'fight_night_archive.py').read_text(encoding='utf-8')
        self.assertIn('app.display_fighter_names_in_text', archive)
        self.assertIn('log.get("detailed_lines", log.get("lines", [])), commentary_mode_var.get()', source)
        self.assertIn("for line in review_lines", source)
        self.assertIn('left_copy = self.display_fighter_name_value(log.get("a", "Red corner"))', source)

    def test_live_density_switch_rebuilds_only_to_the_sealed_frontier(self):
        source = self.source
        self.assertIn('commentary_mode_box.bind("<<ComboboxSelected>>", switch_commentary_mode)', source)
        self.assertIn("source_cutoff = self.fight_night_source_cutoff", source)
        self.assertIn("state[\"rerendering\"] = True", source)
        self.assertIn("for line in log.get(\"lines\", [])[first_line:displayed_count]", source)
        self.assertIn('textvariable=commentary_personality_var', source)

    def test_round_and_high_impact_calls_have_distinct_live_styles(self):
        source = self.source
        self.assertIn('insert_fight_timeline_line(text, value, tag=visual_tag)', source)
        self.assertIn('configure_fight_timeline(text, self.colors)', source)
        styles = (ROOT / 'fight_night_presentation.py').read_text(encoding='utf-8')
        self.assertIn('for tag in ("heading", "round", "result")', styles)
        self.assertIn('"impact": (colors.get("gold", accent)', styles)
        self.assertIn('"knockdown": (colors.get("gold", accent)', styles)
        self.assertIn('"cut": (colors.get("red", impact)', styles)
        self.assertIn('"finish": (colors.get("red", impact)', styles)
        self.assertIn('relief="raised", borderwidth=1', styles)
        self.assertIn('"timeline_hanging"', styles)


if __name__ == "__main__":
    unittest.main(verbosity=2)
