"""Slice 5 lead-hand depth; no additional strike or mechanics draw."""
from ..presets import punch


JAB_DEVELOPMENT = (
    punch("step_in_jab", "step-in jab", action="jab", styles=("Well-Rounded", "Dutch Kickboxer"),
          tags=("setup", "pressure"), range_band="boxing",
          attack_skills=("punch_technique", "footwork", "hand_speed"),
          follow_ups=("one_two", "collar_tie_entry")),
    punch("pawing_jab", "pawing jab", action="jab", styles=("Freestyle Wrestler", "Grappler"),
          tags=("setup", "entry"), range_band="boxing",
          attack_skills=("hand_speed", "feints", "punch_technique"),
          follow_ups=("double_leg_entry", "body_lock_entry")),
    punch("retreating_jab", "retreating jab", action="jab", styles=("Karate", "Taekwondo", "Well-Rounded"),
          tags=("setup", "footwork"), range_band="boxing",
          attack_skills=("footwork", "hand_speed", "punch_technique"),
          follow_ups=("one_two",)),
    punch("spearing_body_jab", "spearing body jab", action="jab", styles=("Karate", "Well-Rounded"),
          tags=("body", "level-change", "setup"), range_band="boxing", targets=frozenset({"body"}),
          attack_skills=("body_punching", "footwork", "punch_technique"),
          follow_ups=("single_jab", "double_leg_entry")),
    punch("chest_jab", "jab to the chest", action="jab", styles=("Boxer", "Dutch Kickboxer"),
          tags=("body", "setup"), range_band="boxing", targets=frozenset({"body"}),
          attack_skills=("punch_technique", "body_punching", "hand_speed"),
          follow_ups=("one_two", "collar_tie_entry")),
    punch("outside_step_jab", "outside-step jab", action="jab", styles=("Sanda", "Well-Rounded"),
          tags=("setup", "footwork"), range_band="boxing",
          attack_skills=("footwork", "punch_technique", "feints"),
          follow_ups=("one_two", "body_lock_entry")),
)
