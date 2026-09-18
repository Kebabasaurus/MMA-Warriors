"""Nine draft Phase 34 front-headlock identities, pending candidate integration.

Submission, breakdown and go-behind actions belong to the head controller (top);
escapes and guard recovery belong to the trapped fighter (bottom). Follow-ups
describe existing settled outcomes, not new transitions or guaranteed finishes.
"""
from ..presets import submission, recovery
from ..schema import move

FRONT = frozenset({"front headlock"})

FRONT_HEADLOCK_DEVELOPMENT = (
    submission("front_high_elbow_guillotine", "high-elbow guillotine from front headlock",
               positions=FRONT, action="front_headlock_submission",
               attack_path="front-headlock neck wrap",
               failure_outcomes=("retain front headlock", "opponent recovers guard", "opponent reverses to top guard"),
               styles=("BJJ", "Luta Livre", "Grappler"), tags=("front-headlock", "choke"),
               attack_skills=("submission_attack", "clinch_control", "flexibility"), minimum_skill=54,
               follow_ups=("front_arm_in_guillotine", "front_headlock_go_behind", "guard_top_guillotine")),
    submission("front_arm_in_guillotine", "arm-in guillotine from front headlock",
               positions=FRONT, action="front_headlock_submission",
               attack_path="front-headlock neck wrap",
               failure_outcomes=("retain front headlock", "opponent recovers guard", "opponent reverses to top guard"),
               styles=("Catch Wrestler", "Submission Grappler", "Well-Rounded"), tags=("front-headlock", "choke"),
               attack_skills=("submission_attack", "strength", "positional_ability"), minimum_skill=52,
               follow_ups=("front_headlock_go_behind", "guard_top_guillotine")),
    submission("front_ten_finger_guillotine", "ten-finger guillotine from front headlock",
               positions=FRONT, action="front_headlock_submission",
               attack_path="front-headlock neck wrap",
               failure_outcomes=("retain front headlock", "opponent recovers guard", "opponent reverses to top guard"),
               styles=("Catch Wrestler", "Wrestler", "Luta Livre"), tags=("front-headlock", "choke"),
               attack_skills=("submission_attack", "clinch_control", "strength"), minimum_skill=54,
               follow_ups=("front_high_elbow_guillotine", "front_headlock_go_behind", "guard_top_guillotine")),
    move("chinstrap_wrist_breakdown", "chinstrap-and-wrist breakdown", "turtle_ride", FRONT,
         attack_skills=("clinch_control", "ride_control", "strength"),
         defense_skills=("scrambles", "get_ups"),
         preferred_styles=("Wrestler", "Freestyle Wrestler", "Grappler"), minimum_skill=48,
         follow_ups=("turtle_wrist_ride_strikes", "turtle_breakdown"),
         tags=("ground", "front-headlock", "transition", "ride", "wrist-control")),
    move("near_arm_spiral_breakdown", "near-arm spiral breakdown from front headlock", "turtle_ride", FRONT,
         attack_skills=("ride_control", "transitions", "top_control"),
         defense_skills=("scrambles", "strength"),
         preferred_styles=("Catch Wrestler", "Freestyle Wrestler", "Well-Rounded"), minimum_skill=50,
         follow_ups=("turtle_breakdown", "ride_wrist_punches"),
         tags=("ground", "front-headlock", "transition", "ride")),
    move("two_on_one_chinstrap_clear", "two-on-one chinstrap clearance", "front_headlock_escape", FRONT,
         attack_skills=("submission_defence_detail", "scrambles", "strength"),
         defense_skills=("clinch_control", "ride_control"),
         preferred_styles=("Wrestler", "Freestyle Wrestler", "Well-Rounded"), minimum_skill=48,
         follow_ups=("closed_guard_retention", "sit_out_reversal"),
         tags=("ground", "front-headlock", "escape", "wrist-control")),
    move("elbow_frame_head_clearance", "elbow-frame head clearance", "front_headlock_escape", FRONT,
         attack_skills=("submission_defence_detail", "guard_work", "mobility"),
         defense_skills=("top_control", "clinch_control"),
         preferred_styles=("BJJ", "Grappler", "Well-Rounded"), minimum_skill=48,
         follow_ups=("closed_guard_retention", "technical_standup"),
         tags=("ground", "front-headlock", "escape", "frame")),
    recovery("front_headlock_knee_insert_recovery", "knee-insertion guard recovery from front headlock",
             positions=FRONT, styles=("BJJ", "Luta Livre", "Grappler"), tags=("front-headlock", "guard"),
             attack_skills=("guard_work", "flexibility", "scrambles"), minimum_skill=48,
             follow_ups=("closed_guard_retention", "butterfly_sweep")),
    move("front_elbow_shuck_go_behind", "elbow-shuck go-behind", "take_back", FRONT,
         attack_skills=("transitions", "back_control", "mobility"),
         defense_skills=("scrambles", "ride_control"),
         preferred_styles=("Freestyle Wrestler", "Wrestler", "Grappler"), minimum_skill=50,
         follow_ups=("rear_naked_choke", "body_triangle_back_control", "turtle_wrist_ride_strikes"),
         tags=("ground", "front-headlock", "transition", "back-take")),
)
