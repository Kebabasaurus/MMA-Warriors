"""Coverage gates distinguish sample evidence, legality, skills and style ownership."""
from dataclasses import replace
import json
from pathlib import Path
import unittest

from fight_moves import MOVE_DEFINITIONS, MOVE_REGISTRY, KNOWN_PARENT_ACTIONS
from fight_moves.coverage import unreachable_moves, coverage_report
from fight_moves.presets import punch, kick, takedown, submission, recovery
from fight_moves.validation import validate_move_registry
from analysis.generate_move_coverage_report import (
    compare_coverage, summarize_positions, pocket_residence, submission_identity_observation,
    contradictory_submission_defense,
    top_leg_entry_observation,
    von_flue_setup_counts,
    scarf_hold_setup_counts,
    guillotine_defense_observation,
    setup_followthrough_counts,
    control_award_observation,
    DefenseRepetitionWindow,
)

ROOT = Path(__file__).resolve().parent
COMMON_POSITIONS = {"range", "clinch", "cage", "guard", "half guard", "side control", "mount", "back control"}
HISTORICAL_COMMON_POSITION_GAPS = {
    "chained_reshot", "whizzer_recovery", "lift_mat_return", "rear_waist_ride", "limp_leg_escape",
    "snapdown_front_headlock", "front_headlock_go_behind", "turtle_wrist_ride_strikes",
    "turtle_breakdown", "sit_out_reversal", "guillotine_choke", "anaconda_choke", "darce_choke",
    "heel_hook", "toe_hold", "front_headlock_posture_out",
}


class CoverageTests(unittest.TestCase):
    def test_defense_repetition_keeps_exact_300_bout_window_and_cross_boundary_peaks(self):
        window = DefenseRepetitionWindow()
        window.observe({'block': 9})
        for _ in range(299):
            window.observe({})
        self.assertEqual(window.maximum, 9)
        self.assertEqual(window.counts['block'], 9)
        window.observe({'block': 9})
        self.assertEqual(window.maximum, 9)  # 18 over301 bouts is not18 within300.
        self.assertEqual(window.counts['block'], 9)
        window.observe({'block': 1})
        self.assertEqual(window.maximum, 10)  # Same unchanged failure threshold.
        for _ in range(300):
            window.observe({})
        self.assertEqual(window.counts, {})
        self.assertEqual(window.maximum, 10)  # Do not forget an earlier failed window.
        crossing = DefenseRepetitionWindow()
        for _ in range(299):
            crossing.observe({})
        crossing.observe({'parry': 5})
        crossing.observe({'parry': 5})
        self.assertEqual(crossing.maximum, 10)  # Fixed disjoint blocks would hide this.

    def test_control_award_distinguishes_physical_control_from_knee_line_and_reset(self):
        self.assertIsNone(control_award_observation({}))
        for top, bottom in (("a", "b"), ("b", "a")):
            for position in ("front headlock", "turtle", "guard", "leg entanglement"):
                owner = top if position != "leg entanglement" else None
                fact = dict(position=position, top=top, bottom=bottom, clinch_controller=None, controller=owner)
                event = dict(type="exchange", position_after=position, top_after=top, bottom_after=bottom,
                             clinch_after=None, control_award=fact, control_delta={top: int(owner == top), bottom: 0})
                expected = position if owner else "uncontrolled"
                self.assertEqual(control_award_observation(event), expected)
                reset = dict(event, position_after="range", top_after=None, bottom_after=None,
                             referee_ground_action={"type": "standup"})
                self.assertEqual(control_award_observation(reset), expected)
                for changes in (dict(control_delta={top: 2, bottom: 0}), dict(control_delta={top: 0, bottom: 1}),
                                dict(top_after=bottom), dict(control_award=dict(fact, controller=bottom))):
                    self.assertEqual(control_award_observation(dict(event, **changes)), "invalid")
            for position in ("range", "pocket", "clinch", "cage", "failed shot", "standing back control"):
                owner = None if position in ("range", "pocket") else top
                fact = dict(position=position, top=None, bottom=None, clinch_controller=owner, controller=owner)
                event = dict(type="exchange", position_after=position, top_after=None, bottom_after=None,
                             clinch_after=owner, control_award=fact, control_delta={top: int(owner == top), bottom: 0})
                self.assertEqual(control_award_observation(event), position if owner else "uncontrolled")
        self.assertEqual(control_award_observation({"type": "exchange", "control_award": {}}), "invalid")

    def test_setup_followthrough_counts_all_losses_and_never_calls_cancelled_a_root(self):
        for field in ("von_flue_setup", "scarf_hold_setup"):
            fact = dict(status="created", top="a", bottom="b", round=1, created_tick=2, position="half guard")
            created = dict(type="exchange", **{field: fact})
            follow = dict(type="exchange", actor="a", action="submission", round=1, tick=3,
                          position_before="half guard", top_before="a", bottom_before="b")
            for change, label in (({field: dict(fact, status="used")}, "used"),
                                  ({}, "top_other_submission"), ({"actor": "b"}, "opponent_intervened"),
                                  ({"action": "ground_control"}, "top_other_action"),
                                  ({"position_before": "guard"}, "context_changed"),
                                  ({"type": "round_end"}, "non_exchange_boundary")):
                self.assertEqual(setup_followthrough_counts([created, dict(follow, **change)], field), {label: 1})
            self.assertEqual(setup_followthrough_counts([created], field), {"unobserved": 1})
            self.assertEqual(setup_followthrough_counts([{field: dict(fact, status="cancelled"), "type": "exchange"}], field), {})

    def test_guillotine_defense_assessment_requires_true_grip_angle_and_setup_facts(self):
        self.assertIsNone(guillotine_defense_observation({}))
        for top, bottom in (("a", "b"), ("b", "a")):
            for grip, angle, expected in ((0, 5, "grip_cleared"), (-1, 0, "grip_cleared"),
                                           (1, -0.01, "wrap_retained"), (1, 0, "von_flue_ready")):
                fact = dict(top=top, bottom=bottom, position="half guard", round=1, tick=2,
                            adjusted_margin=-20, retention_margin=grip, shoulder_margin=angle,
                            pressure_stopped=True, top_control_consolidated=True,
                            neck_wrap_retained=grip > 0, shoulder_angle_established=grip > 0 and angle >= 0)
                event = dict(type="exchange", action="bottom_submission", actor=bottom, round=1, tick=2,
                             top_before=top, top_after=top, bottom_before=bottom, bottom_after=bottom,
                             position_before="half guard", position_after="half guard",
                             submission_technique={"name": "guillotine choke", "choke": True},
                             guillotine_defense=fact)
                if expected == "von_flue_ready":
                    event["von_flue_setup"] = dict(top=top, bottom=bottom, position="half guard",
                                                   round=1, created_tick=2, status="created")
                self.assertEqual(guillotine_defense_observation(event), expected)
                for change in (dict(actor=top), dict(position_after="range"), dict(top_after=bottom),
                               dict(submission_technique={"name": "arm-in guillotine", "choke": True})):
                    self.assertEqual(guillotine_defense_observation(dict(event, **change)), "invalid")
                for change in (dict(adjusted_margin=-10), dict(retention_margin=float("nan")),
                               dict(shoulder_margin="0"), dict(pressure_stopped=False),
                               dict(neck_wrap_retained=not fact["neck_wrap_retained"]), dict(tick=3)):
                    self.assertEqual(guillotine_defense_observation(
                        dict(event, guillotine_defense=dict(fact, **change))), "invalid")
                if expected == "von_flue_ready":
                    self.assertEqual(guillotine_defense_observation(dict(event, von_flue_setup=None)), "invalid")
                else:
                    self.assertEqual(guillotine_defense_observation(
                        dict(event, von_flue_setup={"status": "created"})), "invalid")

    def test_scarf_setup_requires_mechanical_control_not_named_reverse_scarf(self):
        for top, bottom in (("a", "b"), ("b", "a")):
            fact = dict(top=top, bottom=bottom, position="side control", round=1, created_tick=2)
            created = dict(type="exchange", action="ground_control", actor=top, round=1, tick=2,
                           top_before=top, top_after=top, bottom_before=bottom, bottom_after=bottom,
                           position_before="side control", position_after="side control",
                           move={"generic": True, "signature": False},
                           scarf_hold_setup=dict(fact, status="created"))
            used = dict(created, action="submission", tick=3,
                        submission_technique={"name": "scarf-hold straight armbar", "choke": False},
                        scarf_hold_setup=dict(fact, status="used"))
            self.assertEqual(scarf_hold_setup_counts([created, used]), {"created": 1, "used": 1})
            self.assertEqual(scarf_hold_setup_counts([used]), {"invalid": 1})
            for move in ({"generic": False, "move_id": "reverse_scarf_hold_control"},
                         {"generic": True, "signature": True}):
                self.assertEqual(scarf_hold_setup_counts([dict(created, move=move), used]), {"invalid": 2})
            for middle in ({"type": "round_end"}, {"type": "exchange", "action": "survive"}):
                self.assertEqual(scarf_hold_setup_counts([created, middle, used]), {"created": 1, "invalid": 1})
            self.assertEqual(scarf_hold_setup_counts([dict(created, actor=bottom), used]), {"invalid": 2})
            for change in (dict(signature=True), dict(move_mastery=100),
                           dict(sequence_source_id="unproved_control"),
                           dict(move={"generic": True, "sequence_source_id": "unproved_control"})):
                self.assertEqual(scarf_hold_setup_counts([dict(created, **change)]), {"invalid": 1})
            cancelled = dict(created, position_after="range", top_after=None, bottom_after=None,
                             referee_ground_action={"type": "standup"},
                             scarf_hold_setup=dict(fact, status="cancelled", reason="referee_standup"))
            self.assertEqual(scarf_hold_setup_counts([cancelled, used]), {"cancelled": 1, "invalid": 1})
            for change in (dict(referee_ground_action=None), dict(top_after=top),
                           dict(position_after="side control"), dict(move={"generic": False})):
                self.assertEqual(scarf_hold_setup_counts([dict(cancelled, **change)]), {"invalid": 1})

    def test_von_flue_requires_immediate_created_wrap_and_matching_roles(self):
        for top, bottom in (("a", "b"), ("b", "a")):
            fact = dict(top=top, bottom=bottom, position="half guard", round=1, created_tick=2)
            created = dict(type="exchange", action="bottom_submission", actor=bottom, round=1, tick=2,
                           top_before=top, top_after=top, bottom_before=bottom, bottom_after=bottom,
                           position_before="half guard", position_after="half guard",
                           submission_technique={"name": "guillotine choke", "choke": True},
                           von_flue_setup=dict(fact, status="created"))
            used = dict(created, action="submission", actor=top, tick=3,
                        submission_technique={"name": "Von Flue choke", "choke": True},
                        von_flue_setup=dict(fact, status="used"))
            self.assertEqual(von_flue_setup_counts([created, used]), {"created": 1, "used": 1})
            self.assertEqual(von_flue_setup_counts([used]), {"invalid": 1})
            for middle in ({"type": "finish"}, {"type": "exchange", "action": "survive"}):
                self.assertEqual(von_flue_setup_counts([created, middle, used]), {"created": 1, "invalid": 1})
            for change in (dict(actor=bottom), dict(tick=4), dict(round=2), dict(top_before=bottom),
                           dict(von_flue_setup=None)):
                self.assertEqual(von_flue_setup_counts([created, dict(used, **change)]), {"created": 1, "invalid": 1})
            wrong = dict(created, submission_technique={"name": "arm-in guillotine", "choke": True})
            self.assertEqual(von_flue_setup_counts([wrong, used]), {"invalid": 2})

    def test_top_leg_entry_counts_require_true_position_and_owner_evidence(self):
        self.assertIsNone(top_leg_entry_observation({}))
        for actor, other in (("a", "b"), ("b", "a")):
            for success in (False, True):
                after = "leg entanglement" if success else "guard"
                event = dict(type="exchange", action="submission", actor=actor,
                             top_before=actor, top_after=actor, bottom_before=other, bottom_after=other,
                             position_before="guard", position_after=after,
                             outcome="position_change" if success else "defended",
                             submission_technique={"name": "straight ankle lock"},
                             top_leg_entry=dict(success=success, position_before="guard", position_after=after,
                                                controller=actor if success else None, technique="straight ankle lock"))
                self.assertEqual(top_leg_entry_observation(event), "entered" if success else "denied")
                for change in (dict(top_after=other), dict(position_after="range"), dict(action="leg_attack"),
                               dict(submission_technique={"name": "kimura"}), dict(top_leg_entry={"success": 1})):
                    self.assertEqual(top_leg_entry_observation(dict(event, **change)), "invalid")

    def test_submission_defense_gate_uses_actual_hold_not_move_label(self):
        event = {"type": "exchange", "action": "bottom_submission",
                 "move": {"generic": True, "tags": ("leg-lock",)},
                 "submission_technique": {"name": "kimura", "choke": False},
                 "defense": {"tags": ("leg-lock", "escape")}}
        self.assertTrue(contradictory_submission_defense(event))
        for name in ("heel hook", "kneebar", "straight ankle lock", "toe hold", "calf slicer"):
            self.assertFalse(contradictory_submission_defense(dict(event, submission_technique={"name": name})))
        self.assertFalse(contradictory_submission_defense(dict(event, action="counter_leg_lock")))
        self.assertFalse(contradictory_submission_defense(dict(event, defense={"tags": ("grip-defense",)})))
        for evidence in (None, {}, {"name": ""}, {"name": 3}):
            self.assertFalse(contradictory_submission_defense(dict(event, submission_technique=evidence)))

    def test_submission_identity_counts_distinguish_named_generic_and_contradiction(self):
        event = {"type": "exchange", "action": "leg_attack", "position_before": "leg entanglement",
                 "submission_technique": {"name": "kneebar"}, "move_id": "kneebar", "move": {}}
        self.assertEqual(submission_identity_observation(event)[-1], "named")
        event["move_id"] = "entangled_inside_heel_hook"
        self.assertEqual(submission_identity_observation(event)[-1], "incompatible")
        event["move_id"] = "generic_leg_attack"
        self.assertEqual(submission_identity_observation(event)[-1], "generic")
        event["submission_technique"] = None
        self.assertEqual(submission_identity_observation(event)[2:], ("unknown", "missing"))
        event["action"] = "jab"
        self.assertIsNone(submission_identity_observation(event))

    @staticmethod
    def distance_event(before, after, round_no=1):
        return {"type": "exchange", "round": round_no, "position_before": before, "position_after": after}

    def test_pocket_residence_counts_preselection_beats_and_exit_exchange(self):
        event = self.distance_event
        report = pocket_residence([event("range", "pocket"), event("pocket", "pocket"),
                                   event("pocket", "clinch"), event("clinch", "range")])
        self.assertEqual(report, {"entries": 1, "lengths": [2], "exits": {"clinch": 1}})

    def test_horn_and_finish_keep_zero_beat_pocket_entries(self):
        event = self.distance_event
        report = pocket_residence([event("range", "pocket"), {"type": "round_end", "round": 1},
                                   event("range", "pocket", 2), {"type": "finish", "round": 2}])
        self.assertEqual(report, {"entries": 2, "lengths": [0, 0],
                                  "exits": {"round_boundary": 1, "fight_end": 1}})

    def test_partial_trace_and_missing_exit_are_explicit(self):
        event = self.distance_event
        self.assertEqual(pocket_residence([]), {"entries": 0, "lengths": [], "exits": {}})
        report = pocket_residence([event("pocket", "pocket"), event("range", "range")])
        self.assertEqual(report, {"entries": 0, "lengths": [1], "exits": {"unobserved_exit": 1}})

    def test_pocket_occupancy_counts_actual_standing_exchanges(self):
        report = summarize_positions({"range": 92, "pocket": 8, "guard": 900})
        self.assertEqual(report["standing_exchange_count"], 100)
        self.assertEqual(report["pocket_exchange_share_pct"], 8)
        self.assertEqual(report["exchange_position_counts"]["guard"], 900)
        self.assertEqual(summarize_positions({"guard": 10})["pocket_exchange_share_pct"], 0)

    def test_original_sixteen_common_position_gaps_are_explicit(self):
        rows = unreachable_moves(COMMON_POSITIONS, KNOWN_PARENT_ACTIONS, None)
        self.assertEqual(set(rows), HISTORICAL_COMMON_POSITION_GAPS)
        self.assertTrue(all(reasons == ["position-never-entered"] for reasons in rows.values()))

    def test_new_position_orphan_is_not_allowlisted(self):
        new = replace(MOVE_REGISTRY["single_jab"], move_id="new_dead_move", positions=frozenset({"pocket"}))
        rows = unreachable_moves(COMMON_POSITIONS, KNOWN_PARENT_ACTIONS, None,
                                 definitions=(*MOVE_DEFINITIONS, new))
        self.assertEqual(set(rows) - HISTORICAL_COMMON_POSITION_GAPS, {"new_dead_move"})

    def test_requested_target_and_action_position_pair_matter(self):
        move = MOVE_REGISTRY["body_jab"]
        rows = unreachable_moves({"range"}, {"jab"}, None, definitions=(move,),
                                 reachable_contexts={("jab", "range", "head")})
        self.assertEqual(rows[move.move_id], ["target-never-requested"])
        rows = unreachable_moves({"range", "guard"}, {"jab"}, None, definitions=(move,),
                                 reachable_contexts={("jab", "guard", "body")})
        self.assertEqual(rows[move.move_id], ["no-parent-action"])

    def test_style_gate_and_skill_median_have_separate_reasons(self):
        move = replace(MOVE_REGISTRY["single_jab"], tags=("style-combination",),
                       preferred_styles=("Boxer",), minimum_skill=80)
        rows = unreachable_moves({"range"}, {"jab"}, {}, definitions=(move,), available_styles=("BJJ",))
        self.assertEqual(rows[move.move_id], ["style-gate-unsatisfiable", "skill-gate-above-roster"])
        ordinary = replace(move, tags=("punch",))
        self.assertNotIn("style-gate-unsatisfiable", unreachable_moves(
            {"range"}, {"jab"}, {}, definitions=(ordinary,), available_styles=("BJJ",))[move.move_id])

    def test_checked_in_allowlist_cannot_expand_silently(self):
        reference = json.loads((ROOT / "analysis" / "move_coverage_reference.json").read_text(encoding="utf-8"))
        contexts = {tuple(c) for c in reference["contexts"]}
        actual = {"coverage": coverage_report(contexts), "eligibility_warnings": unreachable_moves(
            {p for _, p, _ in contexts}, {a for a, _, _ in contexts}, None, reachable_contexts=contexts)}
        self.assertEqual(compare_coverage(actual, reference), [])
        actual["eligibility_warnings"] = dict(actual["eligibility_warnings"], new_dead_move=["position-never-entered"])
        self.assertTrue(compare_coverage(actual, reference))

    def test_pool_and_style_allowances_cannot_get_worse(self):
        reference = {"eligibility_warnings": {}, "coverage": {
            "pools": [{"action": "jab", "position": "range", "depth": 3}],
            "style_counts": {"Boxer": 17}}}
        actual = {"eligibility_warnings": {}, "coverage": {
            "pools": [{"action": "jab", "position": "range", "depth": 2, "minimum": 4}],
            "style_counts": {"Boxer": 16}}}
        self.assertEqual(len(compare_coverage(actual, reference)), 2)


class VarietyMetricTests(unittest.TestCase):
    def test_chain_median_waiver_preserves_measurement_and_other_gates(self):
        from analysis.generate_move_coverage_report import phase_31_failures, phase_31_advisories
        report = {"chained_selection_pct": 12,
                  "median_completed_chain_length_round2_fights": 2,
                  "median_attempted_chain_length_round2_fights": 1}
        self.assertEqual(phase_31_failures(report), [])
        self.assertTrue(phase_31_advisories(report))
        report["median_attempted_chain_length_round2_fights"] = 2
        self.assertEqual(phase_31_failures(report), [])
        self.assertEqual(phase_31_advisories(report), [])
        report["chained_selection_pct"] = 11.99
        self.assertIn("Phase 31 chained selection share below 12%", phase_31_failures(report))
        self.assertTrue(phase_31_failures({}))

    def test_variety_denominators_include_both_fighters_and_all_exchanges(self):
        from analysis.generate_move_coverage_report import summarize_variety
        result = summarize_variety({str(i): 2 for i in range(20)}, [0, 12, 20, 8], 6)
        self.assertEqual(result, {"total_move_selections": 40,
                                 "mean_distinct_moves_per_fighter": 10,
                                 "top_ten_move_share_pct": 50,
                                 "chained_selection_pct": 15})
        self.assertTrue(all(value == 0 for value in summarize_variety({}, [], 0).values()))


class PresetTests(unittest.TestCase):
    def test_one_line_punch_and_explicit_specialist_helpers_validate(self):
        additions = (
            punch("test_punch", "lead uppercut", styles=("Boxer",), tags=("power",)),
            kick("test_kick", "rear low kick", target="leg", side="rear"),
            takedown("test_trip", "body-lock trip", entry_family="body lock", finish_positions=("guard",)),
            submission("test_sub", "guard arm lock", positions={"guard"}, attack_path="guard arm isolation",
                       failure_outcomes=("retain guard",)),
            recovery("test_recovery", "hip escape", positions={"guard"}),
        )
        self.assertEqual(validate_move_registry((*MOVE_DEFINITIONS, *additions)), [])
        self.assertEqual(additions[0].tags, ("strike", "punch", "power"))
        self.assertEqual(additions[1].attack_skills, ("low_kick_technique", "low_kick_speed"))

    def test_override_changes_only_the_requested_default(self):
        move = punch("test", "test", energy=1.2, follow_ups=("single_jab",), tags=("strike",))
        self.assertEqual(move.energy, 1.2)
        self.assertEqual(move.tags, ("strike", "punch"))
        self.assertEqual(move.follow_ups, ("single_jab",))

    def test_takedown_cannot_author_an_unknown_finish_state(self):
        move = takedown("test_bad", "bad throw", entry_family="body lock", finish_positions=("unknown",))
        self.assertTrue(any("unknown takedown finish positions" in issue
                            for issue in validate_move_registry((*MOVE_DEFINITIONS, move))))


if __name__ == "__main__":
    unittest.main()
