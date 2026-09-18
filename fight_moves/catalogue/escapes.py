"""escapes catalogue; historical batches preserve selection order."""
from ..schema import move, ALL_POSITIONS, STANDING_POSITIONS, CLINCH_POSITIONS, GROUND_POSITIONS

BATCH_009 = (
    move("pivot_exit", "pivoting clinch exit", "break_clinch", CLINCH_POSITIONS,
         attack_skills=("clinch_defence", "footwork", "mobility"), defense_skills=("clinch_control", "cage_pressure"),
         preferred_styles=("Boxer", "Karate", "Taekwondo"), tags=("clinch", "escape")),
    move("frame_exit", "frame-and-circle exit", "break_clinch", CLINCH_POSITIONS,
         attack_skills=("clinch_defence", "guard_defence", "footwork"), defense_skills=("clinch_control", "cage_pressure"),
         preferred_styles=("Boxer", "Kickboxer", "Muay Thai"), tags=("clinch", "escape", "frame")),
)

BATCH_015 = (
    move("guard_recovery", "guard recovery", "recover_guard", frozenset({"half guard", "side control", "mount", "back control", "turtle", "front headlock", "leg entanglement"}),
         attack_skills=("guard_work", "bottom_control", "scrambles"), defense_skills=("top_control", "positional_ability"),
         preferred_styles=("BJJ", "Luta Livre"), tags=("ground", "escape", "transition")),
    move("closed_guard_retention", "closed-guard retention", "recover_guard", frozenset({"guard"}),
         attack_skills=("guard_work", "bottom_control", "reflexes"), defense_skills=("top_control", "positional_ability"),
         preferred_styles=("BJJ", "Luta Livre", "Submission Grappler"), minimum_skill=52,
         tags=("ground", "defense", "control", "guard")),
)

BATCH_017 = (
    move("technical_standup", "technical stand-up", "stand_up", frozenset({"guard", "half guard", "turtle"}),
         attack_skills=("get_ups", "mobility", "scrambles"), defense_skills=("ride_control", "top_control"),
         preferred_styles=("Wrestler", "Kickboxer", "Boxer"), tags=("ground", "escape")),
    move("post_and_build_getup", "post-and-build get-up", "stand_up", frozenset({"guard", "half guard", "turtle"}),
         attack_skills=("get_ups", "scrambles", "conditioning"), defense_skills=("ride_control", "top_control"),
         preferred_styles=("Wrestler", "Freestyle Wrestler", "MMA Generalist"), minimum_skill=54, energy=1.08,
         tags=("ground", "escape", "scramble")),
    move("tripod_standup", "tripod stand-up", "stand_up", frozenset({"guard", "half guard"}),
         attack_skills=("get_ups", "scrambles", "strength"), defense_skills=("ride_control", "top_control"),
         preferred_styles=("Wrestler", "Freestyle Wrestler", "Sambo"), minimum_skill=55, energy=1.1,
         tags=("ground", "escape", "scramble")),
    move("elbow_knee_guard_recovery", "elbow-knee guard recovery", "recover_guard", frozenset({"half guard", "side control", "mount"}),
         attack_skills=("guard_work", "bottom_control", "flexibility"), defense_skills=("top_control", "positional_ability"),
         preferred_styles=("BJJ", "Luta Livre", "Submission Grappler"), minimum_skill=54, energy=1.08,
         tags=("ground", "escape", "transition", "frame")),
    move("back_control_handfight_recovery", "back-control hand-fight recovery", "recover_guard", frozenset({"back control"}),
         attack_skills=("submission_defence_detail", "scrambles", "guard_work"), defense_skills=("back_control", "ride_control"),
         preferred_styles=("BJJ", "Wrestler", "Luta Livre"), minimum_skill=57, energy=1.1,
         tags=("ground", "escape", "transition", "back-control")),
)

BATCH_023 = (
    move("composed_survival", "composed survival", "survive", ALL_POSITIONS,
         attack_skills=("composure", "conditioning", "stun_recovery"), defense_skills=("killer_instinct",),
         preferred_styles=("Well-Rounded", "MMA Generalist"), tags=("defense", "recovery")),
    move("shell_and_reset", "high shell and reset", "survive", STANDING_POSITIONS | CLINCH_POSITIONS,
         attack_skills=("guard_defence", "composure", "footwork"), defense_skills=("killer_instinct", "combination_punching"),
         preferred_styles=("Boxer", "Kickboxer"), tags=("defense", "recovery", "shell")),
    move("circling_breather", "circling breather", "survive", STANDING_POSITIONS,
         attack_skills=("footwork", "mobility", "conditioning"), defense_skills=("cage_pressure", "killer_instinct"),
         preferred_styles=("Karate", "Taekwondo", "MMA Generalist"), tags=("defense", "recovery", "movement")),
    move("clinch_lean_recovery", "clinch lean recovery", "survive", CLINCH_POSITIONS,
         attack_skills=("clinch_defence", "strength", "composure"), defense_skills=("clinch_control", "dirty_boxing"),
         preferred_styles=("Muay Thai", "Judo", "Wrestler"), tags=("defense", "recovery", "clinch")),
    move("bottom_frame_survival", "framing survival from bottom", "survive", GROUND_POSITIONS,
         attack_skills=("bottom_control", "guard_work", "composure"), defense_skills=("top_control", "ground_striking"),
         preferred_styles=("BJJ", "Luta Livre"), tags=("defense", "recovery", "ground")),
    move("heavy_top_breather", "heavy top breather", "survive", GROUND_POSITIONS,
         attack_skills=("top_control", "ride_control", "conditioning"), defense_skills=("scrambles", "bottom_control"),
         preferred_styles=("Wrestler", "Catch Wrestler"), tags=("defense", "recovery", "ground", "control")),
)

BATCH_025 = (
    move("frame_and_pivot_exit", "frame and pivot exit", "break_clinch", CLINCH_POSITIONS,
         attack_skills=("clinch_defence", "footwork", "mobility"), defense_skills=("clinch_control", "cage_wrestling"),
         preferred_styles=("Karate", "Kickboxer", "Boxer"), tags=("clinch", "escape", "footwork")),
    move("post_and_push_exit", "post and push off the fence", "break_clinch", CLINCH_POSITIONS,
         attack_skills=("strength", "clinch_defence", "conditioning"), defense_skills=("cage_wrestling", "clinch_control"),
         preferred_styles=("Wrestler", "Sanda"), tags=("clinch", "escape", "cage")),
    move("swim_to_space", "swim inside and cut the angle", "break_clinch", CLINCH_POSITIONS,
         attack_skills=("clinch_defence", "scrambles", "reflexes"), defense_skills=("clinch_control", "strength"),
         preferred_styles=("MMA Generalist", "Freestyle Wrestler"), minimum_skill=54, tags=("clinch", "escape", "pummel")),
)
