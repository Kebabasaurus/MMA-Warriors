"""Reviewed action-diverse successors for 30 frequently interrupted chain roots.

The ordinary jab ladder remains acyclic, clinch entries can strike/control/take down,
and top work can choose a different action instead of duplicating strike options.
These are alternatives under independently resolved actions, never extra actions.

The pre-integration 300-fight experiment improved chained selections from 12.03%
to 15.53% and completed attempted roots from 1,097/5,721 to 1,323/5,338. Broad
mechanical signatures were identical; largest top-submission share was 20.39%.
The meaningful attempted-chain median remained one: this is progress, not proof
that Phase 31's median-two requirement is satisfied. No defensive-pause retention
behavior is part of this map.
"""

ACTION_DIVERSE_FOLLOWUP_UPDATES = {
    # Different jab deliveries progress toward power or a level-change entry.
    "single_jab": ("one_two", "jab_to_shot", "double_jab"),
    "double_jab": ("one_two", "up_jab", "collar_tie_entry"),
    "up_jab": ("one_two", "collar_tie_entry", "power_jab"),
    "pawing_jab": ("double_leg_entry", "body_lock_entry", "flicker_jab"),
    "flicker_jab": ("one_two", "single_jab", "collar_tie_entry"),
    "retreating_jab": ("one_two", "single_jab", "collar_tie_entry"),
    "outside_step_jab": ("one_two", "body_lock_entry", "power_jab"),
    "power_jab": ("lead_hook_cross", "double_leg_entry", "collar_tie_entry"),
    "step_in_jab": ("one_two", "collar_tie_entry", "power_jab"),
    # A secured entry can develop along three different existing action lanes.
    "inside_biceps_entry": ("clinch_knee", "pummel_to_underhook", "knee_tap"),
    "forearm_frame_entry": ("short_clinch_boxing", "pummel_to_underhook", "knee_tap"),
    "collar_tie_entry": ("clinch_knee", "pummel_to_underhook", "knee_tap"),
    "over_under_entry": ("outside_trip", "pummel_to_underhook", "short_clinch_boxing"),
    "double_underhooks": ("knee_tap", "pummel_to_underhook", "short_clinch_boxing"),
    "pummel_to_underhook": ("knee_tap", "clinch_knee", "head_position_pin"),
    "shoulder_pressure": ("short_clinch_boxing", "body_lock_trip", "head_position_pin"),
    "head_position_pin": ("knee_tap", "short_clinch_boxing", "inside_biceps_control"),
    # After an actual escape, the independently selected next action may be a jab.
    "frame_and_pivot_exit": ("side_kick", "single_jab", "one_two"),
    "collar_tie_strip_exit": ("single_jab", "one_two", "body_lock_entry"),
    "pivot_exit": ("side_kick", "single_jab", "one_two"),
    "swim_to_space": ("side_kick", "single_jab", "one_two"),
    "shoulder_turn_exit": ("double_jab", "single_leg_entry", "one_two"),
    "frame_exit": ("lead_teep", "single_jab", "one_two"),
    "post_and_push_exit": ("lead_teep", "single_jab", "one_two"),
    # Preserve legal source-position alternatives; do not manufacture top ownership.
    "ride_control": ("hip_pressure_ride", "posture_punches", "half_guard_kimura"),
    "body_head_ground_chain": ("position_pass", "guard_top_head_arm", "chest_to_chest_pin"),
    "knee_on_belly_pressure": ("crucifix_elbows", "mount_transition", "half_guard_brabo"),
    "guard_posture_elbows": ("headquarters_pass", "guard_top_head_arm", "staggered_base_guard_control"),
    "headquarters_pass": ("half_guard_crossface_strikes", "half_guard_crossface_control", "half_guard_kimura"),
    "position_pass": ("top_submission_chain", "back_take_transition", "knee_on_belly_pressure"),
}
