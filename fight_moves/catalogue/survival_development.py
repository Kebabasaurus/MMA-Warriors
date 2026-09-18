"""Forty opt-in recovery postures using the existing survival resolution.

Names describe protective work, never an awarded escape, strike, grip win or
position change. Ownership is explicit metadata for the candidate eligibility
gate; positions alone cannot establish top, bottom or clinch control. In leg
entanglement top/bottom mean knee-line ownership, not physical top position.
This module is deliberately absent from the production catalogue imports.
"""
from types import MappingProxyType

from ..schema import move


def _recovery(move_id, name, positions, skills, tags=()):
    return move(move_id, name, "survive", positions, attack_skills=skills,
                defense_skills=("killer_instinct",),
                tags=("defense", "recovery", *tags))


STANDING_RECOVERIES = (
    _recovery("cross_arm_recovery", "cross-arm cover recovery", ("pocket",),
              ("guard_defence", "composure", "resilience"), ("shell",)),
    _recovery("shoulder_cover_recovery", "chin-behind-shoulder recovery", ("range", "pocket"),
              ("head_movement", "guard_defence", "composure"), ("shell",)),
    _recovery("compact_elbow_recovery", "tucked-elbow body-cover recovery", ("pocket",),
              ("guard_defence", "body_punching", "discipline"), ("shell", "body")),
    _recovery("rear_hand_cheek_recovery", "rear-hand cheek-cover recovery", ("range", "pocket"),
              ("guard_defence", "reflexes", "discipline"), ("shell", "head")),
    _recovery("short_step_guard_recovery", "short-step guarded recovery", ("range",),
              ("footwork", "conditioning", "discipline"), ("footwork",)),
    _recovery("split_guard_recovery", "split-guard recovery posture", ("range",),
              ("guard_defence", "reach", "composure"), ("frame",)),
    _recovery("narrow_stance_recovery", "balanced-stance breathing reset", ("range",),
              ("footwork", "mobility", "conditioning"), ("footwork",)),
    _recovery("temple_cover_recovery", "double-temple cover recovery", ("pocket",),
              ("guard_defence", "stun_recovery", "resilience"), ("shell", "head")),
)

CLINCH_RECOVERIES = (
    _recovery("inside_biceps_recovery", "inside-biceps frame recovery", ("clinch", "cage"),
              ("clinch_defence", "strength", "conditioning"), ("clinch", "frame")),
    _recovery("collarbone_frame_recovery", "collarbone-frame recovery", ("clinch", "cage"),
              ("clinch_defence", "reach", "composure"), ("clinch", "frame")),
    _recovery("overhook_brace_recovery", "overhook-brace recovery", ("clinch", "cage"),
              ("clinch_defence", "strength", "discipline"), ("clinch", "whizzer")),
    _recovery("clinch_forehead_recovery", "forehead-position recovery", ("clinch", "cage"),
              ("clinch_control", "composure", "conditioning"), ("clinch",)),
    _recovery("cage_back_brace_recovery", "fence-backed base recovery", ("cage",),
              ("cage_wrestling", "takedown_defence_detail", "conditioning"), ("clinch", "cage")),
    _recovery("clinch_elbow_seal_recovery", "elbows-inside clinch recovery", ("clinch", "cage"),
              ("clinch_defence", "guard_defence", "discipline"), ("clinch", "shell")),
)

TOP_RECOVERIES = (
    _recovery("guard_low_posture_recovery", "low-posture recovery inside guard", ("guard",),
              ("top_control", "submission_defence_detail", "composure"), ("ground", "guard")),
    _recovery("half_guard_wide_base_recovery", "wide-base top half-guard recovery", ("half guard",),
              ("top_control", "positional_ability", "conditioning"), ("ground", "half-guard")),
    _recovery("side_control_hip_sprawl_recovery", "hip-sprawl side-control recovery", ("side control",),
              ("top_control", "sprawl", "conditioning"), ("ground",)),
    _recovery("side_control_knee_post_recovery", "knee-post side-control recovery", ("side control",),
              ("top_control", "positional_ability", "discipline"), ("ground",)),
    _recovery("mount_palm_post_recovery", "palm-post mount recovery", ("mount",),
              ("mount_control", "positional_ability", "conditioning"), ("ground", "mount")),
    _recovery("back_control_chest_recovery", "chest-aligned back-control recovery", ("back control",),
              ("back_control", "ride_control", "composure"), ("ground", "back-control")),
)

BOTTOM_RECOVERIES = (
    _recovery("guard_biceps_shield_recovery", "biceps-shield recovery from guard", ("guard",),
              ("guard_work", "bottom_control", "conditioning"), ("ground", "guard", "frame")),
    _recovery("guard_head_posture_recovery", "head-posture restraint from guard", ("guard",),
              ("guard_work", "bottom_control", "strength"), ("ground", "guard")),
    _recovery("half_guard_knee_shield_recovery", "knee-shield half-guard recovery", ("half guard",),
              ("guard_work", "flexibility", "composure"), ("ground", "half-guard", "frame")),
    _recovery("half_guard_near_arm_recovery", "near-arm shell from half guard", ("half guard",),
              ("bottom_control", "guard_defence", "discipline"), ("ground", "half-guard", "shell")),
    _recovery("side_control_neck_frame_recovery", "neck-frame recovery under side control", ("side control",),
              ("bottom_control", "guard_work", "composure"), ("ground", "frame")),
    _recovery("side_control_elbow_wedge_recovery", "elbow-wedge recovery under side control", ("side control",),
              ("bottom_control", "positional_ability", "conditioning"), ("ground", "frame")),
    _recovery("mount_elbow_knee_shell_recovery", "elbow-knee shell under mount", ("mount",),
              ("guard_defence", "bottom_control", "resilience"), ("ground", "mount", "shell")),
    _recovery("back_control_two_hand_recovery", "two-hand neck protection from back control", ("back control",),
              ("submission_defence_detail", "bottom_control", "composure"), ("ground", "back-control")),
)

SPECIALIST_RECOVERIES = (
    _recovery("turtle_inside_elbow_recovery", "inside-elbow turtle shell", ("turtle",),
              ("guard_defence", "bottom_control", "discipline"), ("ground", "turtle", "shell")),
    _recovery("turtle_neck_hand_recovery", "neck-cover hand fighting in turtle", ("turtle",),
              ("submission_defence_detail", "bottom_control", "composure"), ("ground", "turtle")),
    _recovery("turtle_rider_knee_post_recovery", "knee-post recovery over turtle", ("turtle",),
              ("ride_control", "top_control", "conditioning"), ("ground", "turtle")),
    _recovery("front_headlock_neck_brace_recovery", "neck-brace front-headlock recovery", ("front headlock",),
              ("submission_defence_detail", "strength", "composure"), ("ground", "front-headlock")),
    _recovery("front_headlock_wrist_cover_recovery", "wrist-cover recovery under front headlock", ("front headlock",),
              ("submission_defence_detail", "clinch_defence", "discipline"), ("ground", "front-headlock")),
    _recovery("front_headlock_wide_knee_recovery", "wide-knee front-headlock recovery", ("front headlock",),
              ("top_control", "sprawl", "conditioning"), ("ground", "front-headlock")),
    _recovery("failed_shot_hip_brace_recovery", "hip-brace recovery over a stalled shot", ("failed shot",),
              ("sprawl", "takedown_defence_detail", "conditioning"), ("wrestling",)),
    _recovery("failed_shot_elbow_tuck_recovery", "elbow-tuck recovery under a stalled shot", ("failed shot",),
              ("submission_defence_detail", "takedowns", "composure"), ("wrestling", "shell")),
    _recovery("standing_back_base_recovery", "rear-clinch base recovery", ("standing back control",),
              ("clinch_control", "cage_wrestling", "conditioning"), ("clinch", "back-control")),
    _recovery("standing_back_grip_cover_recovery", "rear-clinch grip-cover recovery", ("standing back control",),
              ("clinch_defence", "takedown_defence_detail", "composure"), ("clinch", "back-control")),
    _recovery("knee_line_ankle_shelter_recovery", "ankle-shelter recovery with knee-line control", ("leg entanglement",),
              ("leg_locks", "submission_defence_detail", "composure"), ("leg-entanglement",)),
    _recovery("knee_line_heel_cover_recovery", "heel-cover recovery under knee-line control", ("leg entanglement",),
              ("submission_defence_detail", "leg_locks", "discipline"), ("leg-entanglement",)),
)

SURVIVAL_DEVELOPMENT = (STANDING_RECOVERIES + CLINCH_RECOVERIES + TOP_RECOVERIES
                        + BOTTOM_RECOVERIES + SPECIALIST_RECOVERIES)

SURVIVAL_ROLES = MappingProxyType({
    **{definition.move_id: "any" for definition in STANDING_RECOVERIES + CLINCH_RECOVERIES},
    **{definition.move_id: "top" for definition in TOP_RECOVERIES},
    **{definition.move_id: "bottom" for definition in BOTTOM_RECOVERIES},
    "cage_back_brace_recovery": "controlled",
    "turtle_inside_elbow_recovery": "bottom",
    "turtle_neck_hand_recovery": "bottom",
    "turtle_rider_knee_post_recovery": "top",
    "front_headlock_neck_brace_recovery": "bottom",
    "front_headlock_wrist_cover_recovery": "bottom",
    "front_headlock_wide_knee_recovery": "top",
    "failed_shot_hip_brace_recovery": "controller",
    "failed_shot_elbow_tuck_recovery": "controlled",
    "standing_back_base_recovery": "controller",
    "standing_back_grip_cover_recovery": "controlled",
    "knee_line_ankle_shelter_recovery": "top",
    "knee_line_heel_cover_recovery": "bottom",
})
