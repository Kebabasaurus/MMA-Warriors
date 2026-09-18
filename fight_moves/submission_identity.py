"""Conservative, explicit identity evidence for experimental submission selection.

Positions/actions/styles/skills remain the selector's responsibility. These IDs
only establish technique compatibility; they never manufacture a submission roll.
An unlisted mechanical name has no compatible identity. Broad submission-chain
IDs and unproved delivery variants (rolling, belly-down ankle, scarf-hold armbar,
overhook shoulder lock, ten-finger guillotine) are intentionally not inferred.
The basic rear-naked choke identity is also true of its explicitly named variants.
"""
from .submission_transition import transition_identity

SUBMISSION_PARENT_ACTIONS = frozenset({
    "submission", "bottom_submission", "front_headlock_submission", "leg_attack",
})

COMPATIBLE_SUBMISSION_IDS = {
    "cradle neck crank": ("catch_cradle_neck_crank_finisher",),
    "shoulder-pressure choke": ("half_guard_shoulder_choke",),
    "can-opener neck crank": ("guard_can_opener",),
    "punch choke": ("guard_top_punch_choke",),
    "gogoplata": ("guard_gogoplata",),
    "reverse armbar": ("guard_reverse_armbar",),
    "overhook shoulder lock": ("guard_overhook_shoulder_lock",),
    "inverted triangle": ("guard_inverted_triangle",),
    "ten-finger guillotine": ("front_ten_finger_guillotine",),
    "belly-down ankle lock": ("entangled_belly_down_ankle_lock",),
    "figure-four toe hold": ("entangled_figure_four_toe_hold",),
    "rolling kneebar": ("entangled_rolling_kneebar", "sambo_rolling_kneebar_finisher"),
    "triangle-to-armbar finish": ("bjj_triangle_armbar_finisher",),
    "rear-triangle choke": ("submission_grappler_rear_triangle_finisher",),
    "rear-naked choke": ("rear_naked_choke",),
    "short choke": (),
    "body-triangle rear-naked choke": ("rear_naked_choke",),
    "face-crank rear-naked choke": ("rear_naked_choke",),
    "bow-and-arrow choke": (),
    "back-control armbar": ("top_armbar",),
    "twister": (),
    "neck crank": (),
    "arm-triangle choke": ("arm_triangle", "half_guard_arm_triangle", "guard_top_head_arm"),
    "mounted arm-triangle": ("arm_triangle", "grappler_arm_triangle_finisher"),
    "americana": ("americana", "half_guard_americana"),
    "kimura": ("kimura_guard", "half_guard_kimura"),
    "straight armbar": ("top_armbar", "guard_armbar", "half_guard_straight_arm_lock"),
    "mounted triangle": ("triangle_choke",),
    "paper-cutter choke": (),
    "north-south choke": ("north_south_choke",),
    "von flue choke": ("half_guard_von_flue",),
    "scarf-hold choke": (),
    "scarf-hold straight armbar": ("scarf_hold_straight_armbar", "judo_kesa_armbar_finisher"),
    "keylock": ("americana", "half_guard_americana"),
    "shoulder lock": (),
    "guillotine choke": ("guillotine_choke", "guard_top_guillotine"),
    "high-elbow guillotine": ("guard_high_elbow_guillotine", "front_high_elbow_guillotine"),
    "arm-in guillotine": ("guard_arm_in_guillotine", "front_arm_in_guillotine"),
    "triangle choke": ("triangle_choke",),
    "reverse triangle": (),
    "buggy choke": (),
    "armbar": ("top_armbar", "guard_armbar", "half_guard_straight_arm_lock"),
    "belly-down armbar": ("top_armbar", "guard_armbar"),
    "omoplata": ("omoplata",),
    "d'arce choke": ("darce_choke", "half_guard_darce"),
    "brabo choke": ("half_guard_brabo",),
    "anaconda choke": ("anaconda_choke",),
    "ninja choke": (),
    "peruvian necktie": (),
    "japanese necktie": (),
    "padlock choke": (),
    "ezekiel choke": ("guard_top_ezekiel",),
    "heel hook": ("heel_hook",),
    "inside heel hook": ("entangled_inside_heel_hook",),
    "outside heel hook": ("entangled_outside_heel_hook", "luta_outside_heel_hook_finisher"),
    "kneebar": ("kneebar",),
    "straight ankle lock": ("straight_ankle_lock", "guard_top_ankle_lock"),
    "toe hold": (),
    "calf slicer": (),
    "knee slicer": (),
    "texas cloverleaf": (),
    "front headlock choke": (),
    "wrist lock": ("guard_top_wrist_lock", "guard_wrist_lock"),
}


def compatible_submission_ids(resolved_technique):
    """Unknown/malformed evidence is deliberately not an alias for a named move."""
    if not isinstance(resolved_technique, dict):
        return ()
    name = resolved_technique.get("name")
    if not isinstance(name, str):
        return ()
    ids = COMPATIBLE_SUBMISSION_IDS.get(name.strip().casefold(), ())
    chain = transition_identity(resolved_technique)
    return ids + (chain,) if chain else ids
