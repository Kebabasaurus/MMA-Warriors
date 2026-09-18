"""Seven unregistered failed-shot identities for the Phase 34 candidate.

The shooter reattacks or rebuilds stance; the defending controller disengages.
These moves describe existing resolver outcomes, not extra shots or mechanics.
"""
from ..schema import move


FAILED_SHOT_DEVELOPMENT = (
    move("knee_slide_double_leg_reshot", "knee-slide double-leg re-shot", "re_shot", {"failed shot"},
         attack_skills=("chain_wrestling", "takedown_speed", "strength"),
         defense_skills=("sprawl", "scrambles"),
         preferred_styles=("Wrestler", "Freestyle Wrestler"), minimum_skill=50,
         follow_ups=("staggered_base_guard_control", "short_clinch_boxing", "two_on_one_chinstrap_clear"),
         tags=("wrestling", "entry", "chain")),
    move("corner_turn_single_leg_reshot", "corner-turn single-leg re-shot", "re_shot", {"failed shot"},
         attack_skills=("chain_wrestling", "takedown_setup", "mobility"),
         defense_skills=("sprawl", "strength"),
         preferred_styles=("Freestyle Wrestler", "Sambo", "Well-Rounded"), minimum_skill=50,
         follow_ups=("ride_control", "knee_tap", "two_on_one_chinstrap_clear"),
         tags=("wrestling", "entry", "chain")),
    move("high_crotch_recollect_reshot", "high-crotch grip recollection", "re_shot", {"failed shot"},
         attack_skills=("takedowns", "chain_wrestling", "strength"),
         defense_skills=("sprawl", "clinch_defence"),
         preferred_styles=("Wrestler", "Freestyle Wrestler", "Grappler"), minimum_skill=52,
         follow_ups=("chest_to_chest_pin", "head_position_pin", "elbow_frame_head_clearance"),
         tags=("wrestling", "entry", "chain")),
    move("tripod_head_withdrawal", "tripod-and-head withdrawal", "recover_shot", {"failed shot"},
         attack_skills=("get_ups", "scrambles", "clinch_defence"),
         defense_skills=("sprawl", "clinch_control"),
         preferred_styles=("Wrestler", "MMA Generalist", "Well-Rounded"), minimum_skill=45,
         follow_ups=("single_jab", "frame_exit"),
         tags=("wrestling", "escape", "recovery")),
    move("inside_elbow_post_shot_recovery", "inside-elbow post to standing", "recover_shot", {"failed shot"},
         attack_skills=("get_ups", "strength", "scrambles"),
         defense_skills=("clinch_control", "cage_wrestling"),
         preferred_styles=("Sambo", "Grappler", "Well-Rounded"), minimum_skill=45,
         follow_ups=("double_jab", "pummel_to_underhook"),
         tags=("wrestling", "escape", "recovery", "frame")),
    move("crossface_pushaway_disengagement", "crossface push-away disengagement", "disengage", {"failed shot"},
         attack_skills=("sprawl", "footwork", "discipline"),
         defense_skills=("chain_wrestling", "takedown_speed"),
         preferred_styles=("Wrestler", "Boxer", "Well-Rounded"), minimum_skill=45,
         follow_ups=("single_jab", "outside_low_kick"),
         tags=("wrestling", "defense", "escape", "frame")),
    move("wrist_release_circle_out", "wrist-release circle-out", "disengage", {"failed shot"},
         attack_skills=("clinch_control", "footwork", "mobility"),
         defense_skills=("chain_wrestling", "strength"),
         preferred_styles=("Freestyle Wrestler", "Karate", "MMA Generalist"), minimum_skill=45,
         follow_ups=("double_jab", "lead_front_snap_kick"),
         tags=("wrestling", "defense", "escape", "wrist-control")),
)
