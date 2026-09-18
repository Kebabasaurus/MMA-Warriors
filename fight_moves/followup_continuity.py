"""Second reviewed action-diverse successor layer.

Thirty additional existing roots gain legal alternatives after clinch work,
control, passing, guard recovery setups and striking. No root is deleted, no
terminal move is manufactured, and no survival response is counted as a step.

Paired 300-fight evidence against the first diversity layer: chained selections
15.53% -> 17.51%; completed attempted roots 1,323/5,338 -> 1,450/5,217;
largest top-submission share 20.39% -> 19.64%, with identical broad mechanics.
The attempted-chain median is still one. This layer is not Phase 31 acceptance.
"""

CONTINUITY_FOLLOWUP_UPDATES = {
    "shoulder_pinch_cling": ("guard_recovery", "guard_submission_chain", "technical_standup"),
    "wrist_elbow_cling": ("guard_recovery", "guard_armbar", "technical_standup"),
    "biceps_tie_cling": ("guard_recovery", "kimura_guard", "technical_standup"),
    "overhook_clamp_cling": ("kimura_guard", "guard_recovery", "technical_standup"),
    "sambo_overhand_body_lock_trip": ("outside_trip", "shoulder_pressure", "clinch_knee"),
    "wrist_to_collar_entry": ("clinch_knee", "pummel_to_underhook", "knee_tap"),
    "inside_biceps_control": ("clinch_knee", "shoulder_grind", "knee_tap"),
    "clinch_knee": ("body_lock_trip", "inside_trip", "hip_pin_fence_control"),
    "gift_wrap_transition": ("mounted_hammerfist_flurry", "rear_naked_choke", "body_triangle_back_control"),
    "two_on_one_clinch_control": ("single_leg_finish", "short_clinch_boxing", "hip_pin_fence_control"),
    "half_guard_crossface_control": ("underhook_half_guard_pass", "half_guard_darce", "half_guard_diagonal_elbows"),
    "mma_generalist_cross_kick_clinch_chain": ("body_lock_entry", "lead_teep", "single_jab"),
    "thai_plum_entry": ("clinch_knee", "pummel_to_underhook", "knee_tap"),
    "body_lock_entry": ("body_lock_trip", "shoulder_grind", "short_clinch_boxing"),
    "single_underhook_entry": ("knee_tap", "shoulder_grind", "short_clinch_boxing"),
    "horizontal_clinch_elbow": ("short_clinch_boxing", "frame_exit", "hip_pin_fence_control"),
    "russian_tie_entry": ("single_leg_finish", "short_clinch_boxing", "shoulder_pressure"),
    "body_jab": ("one_two", "jab_to_shot", "single_jab"),
    "mma_generalist_elbow_knee_finisher": ("body_lock_entry", "lead_teep", "single_jab"),
    "inside_uppercut": ("clinch_knee", "knee_tap", "hip_pin_fence_control"),
    "body_lock_pass": ("half_guard_crossface_strikes", "knee_on_belly_pressure", "half_guard_arm_triangle"),
    "guard_alternating_straights": ("body_lock_pass", "guard_top_head_arm", "staggered_base_guard_control"),
    "underhook_lift_exit": ("single_jab", "double_leg_entry", "one_two"),
    "shoulder_to_chest_entry": ("body_lock_trip", "shoulder_pressure", "clinch_knee"),
    "short_rib_knee": ("collar_tie_elbow", "inside_trip", "overhook_fence_clamp"),
    "elbow_control_entry": ("knee_tap", "pummel_to_underhook", "short_clinch_boxing"),
    "staggered_base_guard_control": ("headquarters_pass", "guard_top_head_arm", "guard_hammerfist_chain"),
    "posture_punches": ("position_pass", "guard_top_head_arm", "staggered_base_guard_control"),
    "underhook_half_guard_pass": ("crucifix_elbows", "reverse_scarf_hold_control", "arm_triangle"),
    "back_take_transition": ("rear_naked_choke", "body_triangle_back_control", "back_control_short_punches"),
}
