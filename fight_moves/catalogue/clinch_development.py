"""Slice 5 clinch depth, confined to existing common-position action contexts.

These identities describe one resolved exchange, not extra attacks or transitions.
Fence-driving content belongs to the later failed-shot specialist-state slice.
"""
from ..schema import move, STANDING_POSITIONS

COMMON_CLINCH = frozenset({"clinch", "cage"})


def _inside_strike(move_id, name, weapon, skills, styles, follow_ups, target="head"):
    return move(move_id, name, "dirty_boxing", COMMON_CLINCH,
                targets=frozenset({target}), attack_skills=skills,
                defense_skills=("clinch_defence", "guard_defence"),
                preferred_styles=styles, minimum_skill=48,
                follow_ups=follow_ups, tags=("clinch", "strike", weapon, target),
                range_band="clinch", defense_families=("block", "frame"))


INSIDE_STRIKES = (
    _inside_strike("collar_tie_short_hook", "collar-tie short hook", "punch",
                   ("dirty_boxing", "punch_technique", "clinch_control"),
                   ("Boxer", "Well-Rounded"), ("inside_uppercut", "frame_exit")),
    _inside_strike("underhook_uppercut", "underhook uppercut", "punch",
                   ("dirty_boxing", "hand_speed", "clinch_control"),
                   ("Catch Wrestler", "Grappler"), ("knee_tap", "short_clinch_boxing")),
    _inside_strike("clinch_shovel_hook", "clinch shovel hook", "punch",
                   ("body_punching", "dirty_boxing", "punch_technique"),
                   ("Boxer", "Dutch Kickboxer", "Well-Rounded"),
                   ("inside_uppercut", "frame_exit"), target="body"),
    _inside_strike("diagonal_clinch_elbow", "diagonal clinch elbow", "elbow",
                   ("elbows", "clinch_control", "reflexes"),
                   ("Muay Thai", "Sanda"), ("clinch_knee", "pivot_exit")),
    _inside_strike("horizontal_clinch_elbow", "horizontal clinch elbow", "elbow",
                   ("elbows", "dirty_boxing", "hand_speed"),
                   ("Muay Thai", "MMA Generalist"), ("short_clinch_boxing", "frame_exit")),
    _inside_strike("short_rib_knee", "short knee to the ribs", "knee",
                   ("knees", "thai_plum", "strength"),
                   ("Muay Thai", "Kickboxer", "Well-Rounded"),
                   ("collar_tie_elbow", "inside_trip"), target="body"),
    _inside_strike("overhook_short_cross", "overhook short cross", "punch",
                   ("dirty_boxing", "punch_power", "clinch_control"),
                   ("Sambo", "Catch Wrestler"), ("outside_trip", "inside_body_hook")),
    _inside_strike("wrist_pin_short_punch", "wrist-pin short punch", "punch",
                   ("dirty_boxing", "hand_speed", "cage_wrestling"),
                   ("Freestyle Wrestler", "Grappler", "Well-Rounded"),
                   ("pummel_to_underhook", "knee_tap")),
)


def _entry(move_id, name, skills, styles, follow_ups, tag):
    return move(move_id, name, "clinch", STANDING_POSITIONS,
                attack_skills=skills, defense_skills=("clinch_defence", "footwork"),
                preferred_styles=styles, minimum_skill=48, follow_ups=follow_ups,
                tags=("clinch", "entry", tag), defense_families=("frame", "underhook"))


ENTRIES = (
    _entry("inside_biceps_entry", "inside-biceps tie entry",
           ("clinch_control", "hand_speed", "reflexes"),
           ("Well-Rounded", "MMA Generalist"), ("clinch_knee", "short_clinch_boxing"), "pummel"),
    _entry("elbow_control_entry", "elbow-control tie entry",
           ("clinch_control", "takedown_setup", "strength"),
           ("Freestyle Wrestler", "Grappler"), ("knee_tap", "pummel_to_underhook"), "wrestling"),
    _entry("russian_tie_entry", "two-on-one Russian-tie entry",
           ("clinch_control", "chain_wrestling", "hand_speed"),
           ("Freestyle Wrestler", "Sambo"), ("single_leg_finish", "knee_tap"), "wrist-control"),
    _entry("single_underhook_entry", "single-underhook entry",
           ("clinch_control", "cage_wrestling", "takedown_setup"),
           ("Grappler", "Wrestler", "Well-Rounded"), ("knee_tap", "body_lock_trip"), "underhook"),
    _entry("wrist_to_collar_entry", "wrist-to-collar tie entry",
           ("thai_plum", "clinch_control", "hand_speed"),
           ("Muay Thai", "Sanda"), ("clinch_knee", "collar_tie_elbow"), "wrist-control"),
    _entry("forearm_frame_entry", "forearm-frame clinch entry",
           ("guard_defence", "clinch_control", "footwork"),
           ("Well-Rounded", "Grappler", "MMA Generalist"),
           ("short_clinch_boxing", "pummel_to_underhook"), "frame"),
    _entry("shoulder_to_chest_entry", "shoulder-to-chest clinch entry",
           ("clinch_control", "cage_pressure", "strength"),
           ("Judo", "Sambo", "Grappler"), ("body_lock_trip", "shoulder_pressure"), "pressure"),
)


def _control(move_id, name, skills, styles, follow_ups, tag, positions=COMMON_CLINCH):
    return move(move_id, name, "cage_control", positions,
                attack_skills=skills, defense_skills=("clinch_defence", "strength"),
                preferred_styles=styles, minimum_skill=48, follow_ups=follow_ups,
                tags=("clinch", "control", tag), defense_families=("underhook", "frame"))


CONTROLS = (
    _control("head_position_pin", "head-position pin",
             ("clinch_control", "cage_pressure", "conditioning"),
             ("Freestyle Wrestler", "Well-Rounded"), ("knee_tap", "short_clinch_boxing"), "pressure"),
    _control("far_wrist_fence_control", "far-wrist fence control",
             ("cage_wrestling", "clinch_control", "hand_speed"),
             ("Catch Wrestler", "Grappler"), ("short_clinch_boxing", "single_leg_finish"),
             "wrist-control", positions={"cage"}),
    _control("two_on_one_clinch_control", "two-on-one clinch control",
             ("clinch_control", "chain_wrestling", "strength"),
             ("Freestyle Wrestler", "Sambo", "Grappler"),
             ("single_leg_finish", "outside_trip"), "wrist-control"),
    _control("overhook_fence_clamp", "overhook fence clamp",
             ("clinch_control", "clinch_defence", "cage_wrestling"),
             ("Judo", "Sambo", "Well-Rounded"), ("inside_trip", "short_clinch_boxing"),
             "cage", positions={"cage"}),
    _control("inside_biceps_control", "inside-biceps control",
             ("clinch_control", "hand_speed", "thai_plum"),
             ("Muay Thai", "Well-Rounded"), ("clinch_knee", "collar_tie_elbow"), "pummel"),
    _control("knee_block_fence_control", "knee-block fence control",
             ("cage_wrestling", "clinch_takedowns", "positional_ability"),
             ("Freestyle Wrestler", "Grappler"), ("knee_tap", "body_lock_trip"),
             "cage", positions={"cage"}),
    _control("hip_pin_fence_control", "hip-pin fence control",
             ("cage_pressure", "strength", "clinch_control"),
             ("Wrestler", "Grappler", "Well-Rounded"), ("double_leg_finish", "body_lock_trip"),
             "cage", positions={"cage"}),
)


def _exit(move_id, name, skills, styles, follow_ups, tag):
    return move(move_id, name, "break_clinch", COMMON_CLINCH,
                attack_skills=skills, defense_skills=("clinch_control", "cage_wrestling"),
                preferred_styles=styles, minimum_skill=48, follow_ups=follow_ups,
                tags=("clinch", "escape", tag), defense_families=("hand fight", "hip pressure"))


EXITS = (
    _exit("wrist_peel_exit", "wrist-peel clinch exit",
          ("clinch_defence", "hand_speed", "reflexes"),
          ("Well-Rounded", "Freestyle Wrestler"), ("single_jab", "double_jab"), "wrist-control"),
    _exit("elbow_pry_exit", "elbow-pry clinch exit",
          ("clinch_defence", "strength", "footwork"),
          ("Grappler", "Catch Wrestler"), ("single_jab", "body_jab"), "frame"),
    _exit("shoulder_turn_exit", "shoulder-turn clinch exit",
          ("clinch_defence", "mobility", "scrambles"),
          ("Judo", "Sanda", "Well-Rounded"), ("double_jab", "single_leg_entry"), "footwork"),
    _exit("underhook_lift_exit", "underhook-lift clinch exit",
          ("clinch_defence", "clinch_control", "strength"),
          ("Freestyle Wrestler", "Wrestler", "Grappler"),
          ("single_jab", "double_leg_entry"), "underhook"),
    _exit("collar_tie_strip_exit", "collar-tie strip exit",
          ("clinch_defence", "thai_plum", "hand_speed"),
          ("Muay Thai", "Well-Rounded", "MMA Generalist"),
          ("single_jab", "body_jab"), "pummel"),
)


CLINCH_DEVELOPMENT = (*INSIDE_STRIKES, *ENTRIES, *CONTROLS, *EXITS)
