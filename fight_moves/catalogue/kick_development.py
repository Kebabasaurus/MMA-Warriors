"""Slice 5: ordinary kick identities within the calibrated kick action.

Lead/rear and delivery distinctions are deliberate: an unswitched lead round kick
is not the existing switch kick, and a snapping front kick is not a pushing teep.
These definitions add selection vocabulary, not impact or extra strike rolls.
"""
from ..presets import kick


SLICE_5_KICKS = (
    kick("rear_teep", "rear teep", target="body", side="rear",
         styles=("Muay Thai", "Well-Rounded"), tags=("body", "intercept"),
         attack_skills=("creative_kicks", "low_kick_technique", "footwork"),
         minimum_skill=48, range_band="long", defense_families=("parry", "catch", "sidestep"),
         follow_ups=("single_jab", "outside_low_kick")),
    kick("lead_front_snap_kick", "lead front snap kick to the chin", target="head", side="lead",
         styles=("Karate", "Taekwondo"), tags=("head", "creative"),
         minimum_skill=56, defense_families=("block", "evade", "sidestep"),
         follow_ups=("one_two",)),
    kick("lead_hook_kick", "lead hook kick", target="head", side="lead",
         styles=("Taekwondo", "Karate"), tags=("head", "creative"),
         attack_skills=("high_kick_technique", "high_kick_speed", "flexibility"),
         minimum_skill=59, defense_families=("block", "evade", "jam"),
         follow_ups=("side_kick", "single_jab")),
    kick("rear_side_kick", "rear side kick to the ribs", target="body", side="rear",
         styles=("Taekwondo", "Sanda"), tags=("body",),
         attack_skills=("creative_kicks", "high_kick_technique", "mobility"),
         minimum_skill=54, range_band="long", defense_families=("sidestep", "catch", "pullback"),
         follow_ups=("single_jab",)),
    kick("intercepting_cut_kick", "intercepting cut kick to the body", target="body", side="lead",
         styles=("Taekwondo", "Well-Rounded"), tags=("body", "intercept"),
         attack_skills=("high_kick_technique", "footwork", "counter_timing"),
         minimum_skill=53, range_band="long", defense_families=("parry", "sidestep", "catch"),
         follow_ups=("head_round_kick", "one_two")),
    kick("step_out_low_kick", "step-out low kick", target="leg", side="rear",
         styles=("Dutch Kickboxer", "Kickboxer", "Well-Rounded"), tags=("leg", "footwork"),
         attack_skills=("low_kick_technique", "low_kick_speed", "footwork"),
         minimum_skill=49, defense_families=("check", "pullback", "stance switch"),
         follow_ups=("one_two", "body_round_kick")),
    kick("inside_calf_kick", "lead inside calf kick", target="leg", side="lead",
         styles=("Dutch Kickboxer", "MMA Generalist", "Well-Rounded"), tags=("leg",),
         minimum_skill=50, defense_families=("check", "pullback", "stance switch"),
         follow_ups=("one_two", "outside_low_kick")),
    kick("oblique_thigh_kick", "oblique kick to the thigh", target="leg", side="lead",
         styles=("Karate", "Well-Rounded", "MMA Generalist"), tags=("leg", "intercept"),
         attack_skills=("low_kick_technique", "creative_kicks", "footwork"),
         minimum_skill=50, range_band="long", defense_families=("pullback", "sidestep", "stance switch"),
         follow_ups=("single_jab", "head_round_kick")),
    kick("lead_body_round_kick", "unswitched lead round kick to the body", target="body", side="lead",
         styles=("Dutch Kickboxer", "Kickboxer", "Taekwondo"), tags=("body",),
         minimum_skill=48, defense_families=("block", "catch", "evade"),
         follow_ups=("one_two", "outside_low_kick")),
    kick("outside_crescent_kick", "outside crescent kick", target="head", side="lead",
         styles=("Taekwondo", "Karate"), tags=("head", "creative"),
         attack_skills=("creative_kicks", "high_kick_technique", "flexibility"),
         minimum_skill=58, defense_families=("block", "evade", "jam"),
         follow_ups=("side_kick", "single_jab")),
)
