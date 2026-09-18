"""clinch catalogue; historical batches preserve selection order."""
from ..schema import move, ALL_POSITIONS, STANDING_POSITIONS, CLINCH_POSITIONS, GROUND_POSITIONS

BATCH_006 = (
    move("collar_tie_entry", "collar-tie entry", "clinch", STANDING_POSITIONS,
         attack_skills=("clinch_control", "hand_speed"), defense_skills=("clinch_defence", "footwork"),
         preferred_styles=("Muay Thai", "Wrestler"), follow_ups=("clinch_knee",), tags=("clinch", "entry")),
    move("body_lock_entry", "body-lock entry", "clinch", STANDING_POSITIONS,
         attack_skills=("clinch_control", "strength", "cage_pressure"), defense_skills=("clinch_defence", "mobility"),
         preferred_styles=("Judo", "Sambo", "Wrestler"), follow_ups=("body_lock_trip",), tags=("clinch", "entry")),
    move("over_under_entry", "over-under entry", "clinch", STANDING_POSITIONS,
         attack_skills=("clinch_control", "clinch_defence", "strength"), defense_skills=("clinch_defence", "footwork"),
         preferred_styles=("Wrestler", "Judo", "Sambo"), follow_ups=("outside_trip",), tags=("clinch", "entry")),
    move("double_underhooks", "double-underhook entry", "clinch", STANDING_POSITIONS,
         attack_skills=("clinch_control", "cage_pressure", "strength"), defense_skills=("clinch_defence", "mobility"),
         preferred_styles=("Wrestler", "Freestyle Wrestler"), minimum_skill=56, energy=1.1,
         follow_ups=("knee_tap",), tags=("clinch", "entry", "underhooks")),
    move("thai_plum_entry", "Thai-plum entry", "clinch", STANDING_POSITIONS,
         attack_skills=("thai_plum", "clinch_control", "hand_speed"), defense_skills=("clinch_defence", "strength"),
         preferred_styles=("Muay Thai",), minimum_skill=55, follow_ups=("clinch_knee",), tags=("clinch", "entry")),
    move("short_clinch_boxing", "short clinch boxing", "dirty_boxing", CLINCH_POSITIONS,
         attack_skills=("dirty_boxing", "punch_technique"), defense_skills=("clinch_defence", "guard_defence"),
         preferred_styles=("Boxer", "Catch Wrestler", "Sanda"), tags=("clinch", "strike", "punch")),
    move("clinch_knee", "knee from the clinch", "dirty_boxing", CLINCH_POSITIONS,
         attack_skills=("knees", "thai_plum", "clinch_control"), defense_skills=("clinch_defence", "strength"),
         preferred_styles=("Muay Thai", "Kickboxer"), energy=1.12, tags=("clinch", "strike", "knee")),
)

BATCH_008 = (
    move("fence_pressure", "fence pressure", "cage_control", CLINCH_POSITIONS | STANDING_POSITIONS,
         attack_skills=("cage_pressure", "cage_wrestling", "clinch_control"), defense_skills=("clinch_defence", "get_ups"),
         preferred_styles=("Wrestler", "Sambo"), tags=("clinch", "control", "cage")),
    move("pummel_to_underhook", "pummel to underhook", "cage_control", CLINCH_POSITIONS,
         attack_skills=("clinch_control", "cage_wrestling", "conditioning"), defense_skills=("clinch_defence", "strength"),
         preferred_styles=("Wrestler", "Freestyle Wrestler"), energy=1.06,
         tags=("clinch", "control", "cage", "underhooks")),
    move("shoulder_pressure", "shoulder pressure on the fence", "cage_control", CLINCH_POSITIONS,
         attack_skills=("cage_pressure", "clinch_control", "strength"), defense_skills=("clinch_defence", "conditioning"),
         preferred_styles=("Wrestler", "Sambo", "Catch Wrestler"), tags=("clinch", "control", "cage")),
)

BATCH_026 = (
    move("inside_uppercut", "short inside uppercut", "dirty_boxing", CLINCH_POSITIONS,
         attack_skills=("dirty_boxing", "punch_technique", "hand_speed"), defense_skills=("clinch_defence", "guard_defence"),
         preferred_styles=("Boxer", "Muay Thai"), tags=("strike", "punch", "clinch")),
    move("collar_tie_elbow", "collar-tie elbow", "dirty_boxing", CLINCH_POSITIONS,
         attack_skills=("elbows", "clinch_control", "punch_technique"), defense_skills=("clinch_defence", "guard_defence"),
         preferred_styles=("Muay Thai", "Sanda"), minimum_skill=55, tags=("strike", "elbow", "clinch")),
    move("inside_body_hook", "inside body hook", "dirty_boxing", CLINCH_POSITIONS, targets=frozenset({"body"}),
         attack_skills=("body_punching", "dirty_boxing", "strength"), defense_skills=("clinch_defence", "conditioning"),
         preferred_styles=("Boxer", "Catch Wrestler"), tags=("strike", "punch", "body", "clinch")),
    move("shoulder_grind", "shoulder grind on the fence", "dirty_boxing", CLINCH_POSITIONS,
         attack_skills=("cage_pressure", "strength", "dirty_boxing"), defense_skills=("clinch_defence", "composure"),
         preferred_styles=("Wrestler", "Sambo"), tags=("strike", "clinch", "cage")),
)

BATCH_028 = (
    move("fence_drive", "drive to the fence", "force_cage", CLINCH_POSITIONS,
         attack_skills=("cage_wrestling", "clinch_control", "strength"), defense_skills=("clinch_defence", "footwork"),
         preferred_styles=("Wrestler", "Sambo", "Judo"), tags=("clinch", "cage", "control")),
)
