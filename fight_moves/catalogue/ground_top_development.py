"""Slice 6 common-position top work; no new positions or mechanical rolls.

Guard passing entries may settle in half guard. Follow-ups describe legal next
choices, not free actions. Strike components contain impacts only: controls and
posture changes must never be counted as attempted or landed strikes.
"""
from ..schema import move


def _pass(move_id, name, position, styles, follow_ups, skills, tags=()):
    return move(move_id, name, "advance_position", frozenset({position}),
                attack_skills=skills, defense_skills=("guard_work", "scrambles", "bottom_control"),
                preferred_styles=styles, minimum_skill=51, follow_ups=follow_ups,
                tags=("ground", "transition", *tags))


def _control(move_id, name, position, styles, follow_ups, skills, tags=()):
    return move(move_id, name, "ground_control", frozenset({position}),
                attack_skills=skills, defense_skills=("bottom_control", "scrambles"),
                preferred_styles=styles, minimum_skill=49, follow_ups=follow_ups,
                tags=("ground", "control", *tags))


def _strikes(move_id, name, position, styles, follow_ups, skills, weapon, components):
    return move(move_id, name, "ground_strikes", frozenset({position}),
                attack_skills=skills, defense_skills=("bottom_control", "guard_work", "composure"),
                preferred_styles=styles, minimum_skill=51, follow_ups=follow_ups,
                tags=("ground", "strike", weapon, "combination"), components=components)


GROUND_TOP_DEVELOPMENT = (
    _pass("standing_guard_opening_pass", "standing guard-opening pass", "guard",
          ("BJJ", "Well-Rounded"), ("half_guard_crossface_control",),
          ("transitions", "positional_ability", "footwork"), ("pass", "guard")),
    _pass("knee_wedge_guard_pass", "knee-wedge guard-opening pass", "guard",
          ("Grappler", "Submission Grappler"), ("half_guard_crossface_strikes",),
          ("transitions", "top_control", "positional_ability"), ("pass", "guard")),
    _pass("hip_pin_guard_pass", "hip-pin guard-passing entry", "guard",
          ("Freestyle Wrestler", "Well-Rounded"), ("underhook_half_guard_pass",),
          ("transitions", "top_control", "strength"), ("pass", "pressure")),
    _pass("reverse_half_guard_pass", "reverse half-guard pass", "half guard",
          ("BJJ", "Sambo"), ("crucifix_elbows", "mount_transition"),
          ("transitions", "positional_ability", "top_control"), ("pass", "half-guard")),
    _pass("tripod_half_guard_pass", "tripod half-guard pass", "half guard",
          ("Wrestler", "Freestyle Wrestler"), ("chest_to_chest_pin", "mount_transition"),
          ("transitions", "top_control", "strength"), ("pass", "pressure")),
    _pass("leg_weave_half_guard_pass", "leg-weave half-guard pass", "half guard",
          ("BJJ", "Grappler"), ("knee_on_belly_pressure",),
          ("transitions", "positional_ability", "top_control"), ("pass", "half-guard")),
    _pass("hip_switch_mount_entry", "hip-switch mount entry", "side control",
          ("Judo", "Well-Rounded"), ("mount_grapevine_control", "body_triangle_back_control"),
          ("transitions", "mount_control", "mobility"), ("mount",)),
    _pass("chair_sit_back_take", "chair-sit back take", "mount",
          ("BJJ", "Submission Grappler", "Grappler"), ("rear_naked_choke", "body_triangle_back_control"),
          ("transitions", "back_control", "positional_ability"), ("back-take",)),
    _control("biceps_pin_top_control", "top-guard biceps-pin control", "guard",
             ("Wrestler", "Well-Rounded"), ("guard_posture_elbows",),
             ("top_control", "strength", "positional_ability"), ("wrist-control",)),
    _control("staggered_base_guard_control", "staggered-base top-guard control", "guard",
             ("Freestyle Wrestler", "MMA Generalist"), ("headquarters_pass",),
             ("top_control", "ride_control", "discipline"), ("guard",)),
    _control("far_wrist_half_guard_control", "far-wrist half-guard control", "half guard",
             ("Freestyle Wrestler", "Catch Wrestler"), ("ride_wrist_punches",),
             ("top_control", "ride_control", "strength"), ("wrist-control", "half-guard")),
    _control("reverse_scarf_hold_control", "reverse scarf-hold control", "side control",
             ("Judo", "Sambo", "Grappler"), ("mount_transition",),
             ("top_control", "positional_ability", "strength"), ("pressure",)),
    _control("near_side_cradle_control", "near-side cradle control", "side control",
             ("Freestyle Wrestler", "Catch Wrestler"), ("crucifix_elbows",),
             ("ride_control", "top_control", "strength"), ("ride",)),
    _control("high_mount_arm_pinch", "high-mount arm-pinch control", "mount",
             ("BJJ", "Grappler", "Submission Grappler"), ("top_armbar", "arm_triangle"),
             ("mount_control", "top_control", "positional_ability"), ("mount",)),
    _control("double_hook_seatbelt_control", "double-hook seatbelt control", "back control",
             ("BJJ", "Luta Livre", "Well-Rounded"), ("rear_naked_choke",),
             ("back_control", "ride_control", "conditioning"), ("back-control",)),
    _strikes("guard_hammerfist_chain", "hammerfist chain from top guard", "guard",
             ("Sambo", "Grappler", "Well-Rounded"), ("headquarters_pass",),
             ("ground_striking", "top_control", "punch_power"), "punch",
             ("short hammerfist", "hammerfist around the guard")),
    _strikes("guard_alternating_straights", "alternating straight punches from guard", "guard",
             ("Wrestler", "Boxer", "MMA Generalist"), ("body_lock_pass",),
             ("ground_striking", "hand_speed", "top_control"), "punch",
             ("left straight punch", "right straight punch")),
    _strikes("half_guard_diagonal_elbows", "diagonal elbows from half guard", "half guard",
             ("Muay Thai", "BJJ", "Well-Rounded"), ("underhook_half_guard_pass",),
             ("ground_striking", "elbows", "top_control"), "elbow",
             ("diagonal elbow", "short slicing elbow")),
    _strikes("half_guard_free_hand_hammerfists", "free-hand hammerfists from half guard", "half guard",
             ("Freestyle Wrestler", "Catch Wrestler"), ("half_guard_pass",),
             ("ground_striking", "ride_control", "punch_power"), "punch",
             ("free-hand hammerfist", "short hammerfist")),
    _strikes("side_control_short_hooks", "short hooks from side control", "side control",
             ("Boxer", "Judo", "Grappler"), ("mount_transition",),
             ("ground_striking", "punch_technique", "top_control"), "punch",
             ("short hook", "hook around the guard")),
    _strikes("side_control_frame_elbows", "frame-and-elbow striking from side control", "side control",
             ("Muay Thai", "Sambo", "MMA Generalist"), ("knee_on_belly_climb",),
             ("ground_striking", "elbows", "positional_ability"), "elbow",
             ("short elbow", "diagonal elbow")),
    _strikes("mounted_straight_punch_chain", "straight-punch chain from mount", "mount",
             ("Wrestler", "Freestyle Wrestler", "Well-Rounded"), ("arm_triangle", "top_armbar"),
             ("ground_striking", "mount_control", "hand_speed"), "punch",
             ("straight punch", "postured straight punch")),
    _strikes("back_control_cross_wrist_punches", "cross-wrist punches from back control", "back control",
             ("Catch Wrestler", "Freestyle Wrestler", "Luta Livre"), ("rear_naked_choke",),
             ("ground_striking", "ride_control", "back_control"), "punch",
             ("short punch around the guard", "free-hand hook")),
)
