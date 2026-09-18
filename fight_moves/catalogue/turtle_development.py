"""Ten unregistered Phase 34 turtle identities with existing resolver outcomes.

Back takes, strikes and rides belong to top; escapes and recovery to bottom.
No definition changes the underlying attack, damage, escape or finish rules.
"""
from ..schema import move

TURTLE = frozenset({"turtle"})


def _turtle(move_id, name, action, skills, defenses, styles, followups, tags):
    return move(move_id, name, action, TURTLE, attack_skills=skills,
                defense_skills=defenses, preferred_styles=styles, minimum_skill=50,
                follow_ups=followups, tags=("ground", "turtle", *tags))


TURTLE_DEVELOPMENT = (
    _turtle("turtle_seatbelt_hook_entry", "seatbelt-and-hook entry from turtle", "take_back",
            ("back_control", "transitions", "positional_ability"), ("scrambles", "submission_defence_detail"),
            ("BJJ", "Grappler", "Well-Rounded"),
            ("rear_naked_choke", "body_triangle_back_control", "turtle_wrist_ride_strikes"),
            ("transition", "back-take")),
    _turtle("turtle_far_hip_back_take", "far-hip back take from turtle", "take_back",
            ("ride_control", "back_control", "strength"), ("scrambles", "get_ups"),
            ("Wrestler", "Freestyle Wrestler", "Sambo"),
            ("back_control_short_punches", "body_triangle_back_control", "turtle_breakdown"),
            ("wrestling", "transition", "back-take")),
    _turtle("turtle_arm_drag_back_take", "near-arm drag to the back from turtle", "take_back",
            ("transitions", "clinch_control", "mobility"), ("scrambles", "strength"),
            ("Luta Livre", "Grappler", "Freestyle Wrestler"),
            ("rear_naked_choke", "back_control_short_punches", "ride_wrist_punches"),
            ("transition", "back-take", "wrist-control")),
    _turtle("turtle_far_side_head_punches", "far-side head punches around the turtle shell", "ground_strikes",
            ("ground_striking", "hand_speed", "ride_control"), ("guard_defence", "scrambles"),
            ("Wrestler", "Boxer", "Well-Rounded"),
            ("turtle_breakdown", "turtle_wrist_ride_strikes"),
            ("strike", "punch", "head")),
    _turtle("turtle_short_side_hammerfists", "short hammerfists to the side of the turtle shell", "ground_strikes",
            ("ground_striking", "punch_power", "top_control"), ("guard_defence", "get_ups"),
            ("Sambo", "Catch Wrestler", "MMA Generalist"),
            ("turtle_breakdown", "ride_wrist_punches"),
            ("strike", "punch", "head")),
    _turtle("turtle_far_ankle_ride", "far-ankle turtle ride", "turtle_ride",
            ("ride_control", "top_control", "strength"), ("get_ups", "scrambles"),
            ("Freestyle Wrestler", "Wrestler", "Grappler"),
            ("turtle_wrist_ride_strikes", "turtle_breakdown"),
            ("wrestling", "control", "ride")),
    _turtle("turtle_cross_wrist_ride", "cross-wrist turtle ride", "turtle_ride",
            ("ride_control", "clinch_control", "positional_ability"), ("scrambles", "strength"),
            ("Catch Wrestler", "Well-Rounded", "Grappler"),
            ("ride_wrist_punches", "turtle_wrist_ride_strikes"),
            ("wrestling", "control", "ride", "wrist-control")),
    _turtle("turtle_shoulder_roll_escape", "shoulder-roll escape from turtle", "turtle_escape",
            ("scrambles", "mobility", "guard_work"), ("ride_control", "back_control"),
            ("Freestyle Wrestler", "BJJ", "Grappler"),
            ("single_jab", "closed_guard_retention", "technical_standup"),
            ("escape", "scramble")),
    _turtle("turtle_hand_peel_turnout", "hand-peel turnout from turtle", "turtle_escape",
            ("get_ups", "scrambles", "strength"), ("ride_control", "clinch_control"),
            ("Wrestler", "Sambo", "Well-Rounded"),
            ("single_jab", "closed_guard_retention", "post_and_build_getup"),
            ("escape", "scramble", "wrist-control")),
    _turtle("turtle_elbow_knee_guard_recovery", "elbow-knee guard recovery from turtle", "recover_guard",
            ("guard_work", "flexibility", "bottom_control"), ("ride_control", "top_control"),
            ("BJJ", "Luta Livre", "Well-Rounded"),
            ("closed_guard_retention", "butterfly_sweep", "sit_out_reversal"),
            ("escape", "recovery", "guard")),
)
