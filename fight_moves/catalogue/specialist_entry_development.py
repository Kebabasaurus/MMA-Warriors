"""Phase 34 entry identities; registration requires the mechanical slice gate.

Failed-shot drives belong to the defender controlling the stuffed entry. They
bring the opponent upright against the fence, not directly onto the mat.
"""
from ..schema import move


SPECIALIST_ENTRY_DEVELOPMENT = (
    move("clinch_snapdown_front_headlock", "collar-tie clinch snapdown", "front_headlock", {"clinch"},
         attack_skills=("clinch_control", "sprawl", "submission_attack"),
         defense_skills=("clinch_defence", "strength", "scrambles"),
         preferred_styles=("Wrestler", "Catch Wrestler", "Grappler"), minimum_skill=50,
         follow_ups=("guillotine_choke", "darce_choke", "front_headlock_go_behind"),
         tags=("clinch", "wrestling", "front-headlock", "transition")),
    move("collar_tie_fence_drive", "collar-tie drive to the fence", "force_cage", {"failed shot"},
         attack_skills=("clinch_control", "cage_wrestling", "strength"),
         defense_skills=("clinch_defence", "footwork"),
         preferred_styles=("Wrestler", "Well-Rounded", "MMA Generalist"), minimum_skill=45,
         follow_ups=("fence_pressure", "short_clinch_boxing", "knee_tap"),
         tags=("wrestling", "clinch", "cage", "control")),
    move("overhook_shoulder_fence_drive", "overhook-and-shoulder fence drive", "force_cage", {"failed shot"},
         attack_skills=("clinch_control", "mobility", "cage_pressure"),
         defense_skills=("scrambles", "clinch_defence"),
         preferred_styles=("Judo", "Sambo", "Well-Rounded"), minimum_skill=48,
         follow_ups=("shoulder_pressure", "knee_tap"),
         tags=("wrestling", "clinch", "cage", "control", "whizzer")),
    move("crossface_arm_fence_drive", "crossface-and-arm fence drive", "force_cage", {"failed shot"},
         attack_skills=("sprawl", "strength", "cage_wrestling"),
         defense_skills=("clinch_defence", "get_ups"),
         preferred_styles=("Catch Wrestler", "Wrestler", "Grappler"), minimum_skill=48,
         follow_ups=("head_position_pin", "inside_uppercut"),
         tags=("wrestling", "clinch", "cage", "control", "pressure")),
    move("wrist_underhook_fence_drive", "wrist-and-underhook fence drive", "force_cage", {"failed shot"},
         attack_skills=("clinch_control", "footwork", "cage_wrestling"),
         defense_skills=("scrambles", "strength"),
         preferred_styles=("Freestyle Wrestler", "Grappler", "Well-Rounded"), minimum_skill=48,
         follow_ups=("pummel_to_underhook", "short_clinch_boxing", "knee_tap"),
         tags=("wrestling", "clinch", "cage", "control", "wrist-control", "underhook")),
)
