"""Unregistered final 15: five leg attacks plus ten entanglement identities.

In this position ``top`` is the knee-line controller, not physical top control.
Counter-lock actions only reverse that ownership; they are not submission rolls.
All moves retain neutral tuning and use the existing action resolvers.
"""
from ..presets import submission
from ..schema import move

LEGS = frozenset({"leg entanglement"})
_FAILURES = ("retain entanglement", "opponent recovers guard", "opponent reverses to top guard")


LEG_ATTACK_DEVELOPMENT = (
    submission("entangled_inside_heel_hook", "inside heel hook from entanglement", positions=LEGS,
               action="leg_attack", attack_path="heel exposure from entanglement", failure_outcomes=_FAILURES,
               styles=("BJJ", "Luta Livre", "Submission Grappler"), tags=("leg-lock", "joint"),
               attack_skills=("leg_locks", "submission_attack", "positional_ability"), minimum_skill=60,
               follow_ups=("kneebar", "straight_ankle_lock")),
    submission("entangled_outside_heel_hook", "outside heel hook from entanglement", positions=LEGS,
               action="leg_attack", attack_path="outside ashi heel exposure", failure_outcomes=_FAILURES,
               styles=("Luta Livre", "Catch Wrestler", "Grappler"), tags=("leg-lock", "joint"),
               attack_skills=("leg_locks", "submission_attack", "transitions"), minimum_skill=58,
               follow_ups=("straight_ankle_lock", "kneebar")),
    submission("entangled_belly_down_ankle_lock", "belly-down ankle lock from entanglement", positions=LEGS,
               action="leg_attack", attack_path="straight-leg entanglement", failure_outcomes=_FAILURES,
               styles=("Sambo", "BJJ", "Well-Rounded"), tags=("leg-lock", "joint"),
               attack_skills=("leg_locks", "strength", "submission_attack"), minimum_skill=54,
               follow_ups=("kneebar",)),
    submission("entangled_figure_four_toe_hold", "figure-four toe hold from entanglement", positions=LEGS,
               action="leg_attack", attack_path="figure-four foot isolation", failure_outcomes=_FAILURES,
               styles=("Sambo", "Catch Wrestler", "Grappler"), tags=("leg-lock", "joint"),
               attack_skills=("leg_locks", "submission_attack", "strength"), minimum_skill=56,
               follow_ups=("straight_ankle_lock",)),
    submission("entangled_rolling_kneebar", "rolling kneebar from entanglement", positions=LEGS,
               action="leg_attack", attack_path="rolling knee-line isolation", failure_outcomes=_FAILURES,
               styles=("Sambo", "Luta Livre", "Submission Grappler"), tags=("leg-lock", "joint"),
               attack_skills=("leg_locks", "transitions", "flexibility"), minimum_skill=58,
               follow_ups=("straight_ankle_lock",)),
)


def _position(move_id, name, action, skills, defenses, styles, followups, tags):
    return move(move_id, name, action, LEGS, attack_skills=skills, defense_skills=defenses,
                preferred_styles=styles, minimum_skill=50, follow_ups=followups,
                tags=("ground", "leg-entanglement", *tags))


LEG_POSITION_DEVELOPMENT = (
    _position("inside_ashi_knee_pin", "inside-ashi knee-line pin", "leg_control",
              ("leg_locks", "positional_ability", "strength"), ("scrambles", "submission_defence_detail"),
              ("BJJ", "Grappler", "Well-Rounded"),
              ("entangled_inside_heel_hook", "straight_ankle_lock"), ("control", "leg-lock")),
    _position("saddle_secondary_leg_control", "secondary-leg control from the saddle", "leg_control",
              ("leg_locks", "transitions", "clinch_control"), ("scrambles", "flexibility"),
              ("Submission Grappler", "Luta Livre", "Sambo"),
              ("entangled_inside_heel_hook", "entangled_rolling_kneebar"), ("control", "leg-lock")),
    _position("outside_ashi_hip_clamp", "outside-ashi hip clamp", "leg_control",
              ("leg_locks", "strength", "positional_ability"), ("submission_defence_detail", "mobility"),
              ("Catch Wrestler", "Sambo", "Grappler"),
              ("entangled_outside_heel_hook", "entangled_belly_down_ankle_lock"), ("control", "leg-lock")),
    _position("boot_and_heel_clearance", "boot-and-heel clearance", "leg_escape",
              ("submission_defence_detail", "leg_locks", "scrambles"), ("leg_locks", "strength"),
              ("Sambo", "BJJ", "Well-Rounded"),
              ("single_jab", "closed_guard_retention", "inside_leg_pummel_counter"), ("escape", "leg-lock")),
    _position("knee_line_hip_heist_escape", "knee-line hip-heist escape", "leg_escape",
              ("scrambles", "get_ups", "mobility"), ("leg_locks", "positional_ability"),
              ("Freestyle Wrestler", "Grappler", "Well-Rounded"),
              ("single_jab", "closed_guard_retention", "inside_leg_pummel_counter"), ("escape", "scramble")),
    _position("two_hand_ankle_retraction", "two-hand ankle retraction", "leg_escape",
              ("submission_defence_detail", "strength", "flexibility"), ("leg_locks", "clinch_control"),
              ("Wrestler", "Catch Wrestler", "Well-Rounded"),
              ("single_jab", "closed_guard_retention", "heel_hide_counter_grip"), ("escape", "wrist-control")),
    _position("inside_leg_pummel_counter", "inside-leg pummel to counter control", "counter_leg_lock",
              ("leg_locks", "scrambles", "transitions"), ("leg_locks", "positional_ability"),
              ("BJJ", "Luta Livre", "Grappler"),
              ("inside_ashi_knee_pin", "entangled_inside_heel_hook"), ("transition", "scramble", "leg-lock")),
    _position("heel_hide_counter_grip", "heel-hide counter-grip reversal", "counter_leg_lock",
              ("leg_locks", "submission_defence_detail", "strength"), ("leg_locks", "scrambles"),
              ("Sambo", "Catch Wrestler", "Submission Grappler"),
              ("outside_ashi_hip_clamp", "entangled_figure_four_toe_hold"), ("transition", "scramble", "leg-lock")),
    _position("cross_ankle_grip_release", "cross-ankle grip release and disengagement", "disengage_leg",
              ("leg_locks", "discipline", "get_ups"), ("scrambles", "leg_locks"),
              ("Well-Rounded", "MMA Generalist", "Grappler"),
              ("single_jab", "double_leg_entry"), ("escape", "recovery")),
    _position("knee_line_backstep_release", "knee-line backstep disengagement", "disengage_leg",
              ("mobility", "scrambles", "discipline"), ("leg_locks", "clinch_control"),
              ("Freestyle Wrestler", "Wrestler", "Well-Rounded"),
              ("single_jab", "double_leg_entry"), ("escape", "recovery")),
)

LEG_ENTANGLEMENT_DEVELOPMENT = LEG_ATTACK_DEVELOPMENT + LEG_POSITION_DEVELOPMENT
