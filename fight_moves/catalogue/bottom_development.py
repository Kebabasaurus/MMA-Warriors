"""Phase 30 bottom-position vocabulary; integrated after Phase 29 calibration."""
from ..presets import recovery
from ..schema import move, GROUND_POSITIONS, STANDING_POSITIONS, CLINCH_POSITIONS

RECOVERIES = (
    recovery("knee_shield_recovery", "knee-shield recovery", positions={"guard", "half guard", "side control"},
             styles=("BJJ", "Submission Grappler"), tags=("frame",), follow_ups=("butterfly_sweep",)),
    recovery("hip_heist_recovery", "hip-heist recovery", positions=GROUND_POSITIONS,
             styles=("Wrestler", "Grappler"), tags=("scramble",), follow_ups=("technical_standup",)),
    recovery("elbow_frame_recovery", "elbow-frame recovery", positions=GROUND_POSITIONS,
             styles=("BJJ", "Well-Rounded"), tags=("frame",), follow_ups=("guard_submission_chain",)),
    recovery("bridge_shrimp_recovery", "bridge-and-shrimp recovery", positions=GROUND_POSITIONS,
             styles=("Judo", "Sambo"), tags=("transition",), follow_ups=("technical_standup",)),
    recovery("granby_guard_recovery", "Granby-roll guard recovery", positions={"half guard", "side control", "back control"},
             styles=("Freestyle Wrestler", "Grappler"), tags=("scramble",), minimum_skill=52,
             follow_ups=("technical_standup",)),
    recovery("shin_to_shin_retention", "shin-to-shin guard retention", positions={"guard", "half guard"},
             styles=("BJJ", "Luta Livre"), tags=("guard",), follow_ups=("butterfly_sweep",)),
    recovery("half_guard_underhook_recovery", "half-guard underhook recovery", positions={"half guard", "side control"},
             styles=("Wrestler", "Luta Livre"), tags=("underhook",), follow_ups=("butterfly_sweep",)),
    recovery("butterfly_hook_recovery", "butterfly-hook recovery", positions={"guard", "half guard"},
             styles=("BJJ", "Judo"), tags=("guard",), follow_ups=("butterfly_sweep",)),
    recovery("shoulder_walk_recovery", "shoulder-walk guard recovery", positions={"mount", "side control", "back control"},
             styles=("Submission Grappler", "Well-Rounded"), tags=("frame",), follow_ups=("guard_submission_chain",)),
    recovery("inside_knee_reinsertion", "inside-knee reinsertion", positions={"guard", "half guard", "side control", "mount"},
             styles=("BJJ", "Sambo"), tags=("guard",), follow_ups=("hip_bump_sweep",)),
)


def _sweep(move_id, name, positions, styles, skills):
    return move(move_id, name, "sweep", frozenset(positions), preferred_styles=styles,
                attack_skills=skills, defense_skills=("top_control", "strength"),
                minimum_skill=48, tags=("ground", "sweep", "transition"),
                follow_ups=("chest_to_chest_pin", "top_submission_chain"))


SWEEPS = (
    _sweep("pendulum_sweep", "pendulum sweep", {"guard"}, ("BJJ", "Judo"), ("guard_work", "transitions", "flexibility")),
    _sweep("elevator_sweep", "elevator sweep", {"guard", "half guard"}, ("Grappler", "BJJ"), ("guard_work", "scrambles", "strength")),
    _sweep("john_wayne_sweep", "John Wayne sweep", {"half guard"}, ("BJJ", "Luta Livre"), ("guard_work", "transitions", "reflexes")),
    _sweep("electric_chair_sweep", "electric-chair sweep", {"half guard"}, ("Luta Livre", "Catch Wrestler"), ("guard_work", "flexibility", "strength")),
    _sweep("old_school_sweep", "old-school half-guard sweep", {"half guard"}, ("Wrestler", "Grappler"), ("guard_work", "chain_wrestling", "scrambles")),
    _sweep("plan_b_sweep", "Plan B half-guard sweep", {"half guard"}, ("BJJ", "Sambo"), ("guard_work", "transitions", "strength")),
    _sweep("open_guard_tripod_sweep", "open-guard tripod sweep", {"guard"}, ("BJJ", "Sambo"), ("guard_work", "transitions", "reflexes")),
    _sweep("sickle_sweep", "sickle sweep", {"guard"}, ("Judo", "Luta Livre"), ("guard_work", "transitions", "mobility")),
)


def _standup(move_id, name, positions, styles, skills):
    return move(move_id, name, "stand_up", frozenset(positions), preferred_styles=styles,
                attack_skills=skills, defense_skills=("ride_control", "top_control"),
                tags=("ground", "escape", "scramble"), follow_ups=("single_jab", "double_jab"))


STANDUPS = (
    _standup("wall_walk_standup", "wall-walk stand-up", {"guard", "half guard"}, ("Wrestler", "MMA Generalist"), ("get_ups", "cage_wrestling", "strength")),
    _standup("kick_away_standup", "kick-away stand-up", {"guard"}, ("Kickboxer", "Taekwondo"), ("get_ups", "mobility", "kick_defence")),
    _standup("shin_post_standup", "shin-post stand-up", {"guard", "half guard"}, ("BJJ", "Sanda"), ("get_ups", "guard_work", "mobility")),
    _standup("elbow_post_standup", "elbow-post stand-up", {"guard", "half guard"}, ("Wrestler", "Boxer"), ("get_ups", "strength", "scrambles")),
    _standup("situp_underhook_standup", "sit-up underhook stand-up", {"guard", "half guard"}, ("Grappler", "Freestyle Wrestler"), ("get_ups", "scrambles", "clinch_control")),
    _standup("hip_scoot_standup", "hip-scoot stand-up", {"guard", "half guard"}, ("Karate", "Well-Rounded"), ("get_ups", "mobility", "footwork")),
)


CLINGS = (
    move("biceps_tie_cling", "biceps-tie control from bottom", "cling", GROUND_POSITIONS,
         attack_skills=("bottom_control", "guard_work", "strength"), defense_skills=("ground_striking", "top_control"),
         preferred_styles=("BJJ", "Grappler"), tags=("ground", "defense", "control"), follow_ups=("guard_recovery",)),
    move("overhook_clamp_cling", "overhook clamp from guard", "cling", {"guard", "half guard"},
         attack_skills=("bottom_control", "guard_work", "strength"), defense_skills=("ground_striking", "top_control"),
         preferred_styles=("Judo", "Luta Livre"), tags=("ground", "guard", "control"), follow_ups=("kimura_guard",)),
    move("wrist_elbow_cling", "wrist-and-elbow tie from bottom", "cling", GROUND_POSITIONS,
         attack_skills=("bottom_control", "scrambles", "composure"), defense_skills=("ground_striking", "top_control"),
         preferred_styles=("Catch Wrestler", "Wrestler"), tags=("ground", "defense", "control"), follow_ups=("guard_recovery",)),
    move("ankle_cross_cling", "ankle-cross guard clamp", "cling", {"guard"},
         attack_skills=("guard_work", "flexibility", "bottom_control"), defense_skills=("top_control", "strength"),
         preferred_styles=("BJJ", "Submission Grappler"), tags=("ground", "guard", "control"), follow_ups=("guard_submission_chain",)),
    move("shoulder_pinch_cling", "shoulder-pinch control from bottom", "cling", GROUND_POSITIONS,
         attack_skills=("bottom_control", "strength", "composure"), defense_skills=("ground_striking", "top_control"),
         preferred_styles=("Sambo", "Grappler"), tags=("ground", "defense", "control"), follow_ups=("guard_recovery",)),
)

SURVIVALS = (
    move("forearm_shell_survival", "forearm-shell recovery", "survive", STANDING_POSITIONS,
         attack_skills=("guard_defence", "composure", "conditioning"), defense_skills=("punch_power", "killer_instinct"),
         preferred_styles=("Boxer", "Dutch Kickboxer"), tags=("defense", "shell", "recovery"), follow_ups=("single_jab",)),
    move("long_guard_breather", "long-guard breather", "survive", STANDING_POSITIONS,
         attack_skills=("guard_defence", "footwork", "composure"), defense_skills=("punch_power", "cage_pressure"),
         preferred_styles=("Muay Thai", "Taekwondo"), tags=("defense", "frame", "recovery"), follow_ups=("double_jab",)),
    move("clinch_wrist_tie_breather", "clinch wrist-tie breather", "survive", CLINCH_POSITIONS,
         attack_skills=("clinch_defence", "composure", "conditioning"), defense_skills=("clinch_control", "dirty_boxing"),
         preferred_styles=("Judo", "Sambo"), tags=("defense", "clinch", "recovery"), follow_ups=("frame_exit",)),
    move("hip_frame_ground_breather", "hip-frame breather from bottom", "survive", GROUND_POSITIONS,
         attack_skills=("bottom_control", "guard_work", "composure"), defense_skills=("ground_striking", "top_control"),
         preferred_styles=("BJJ", "Well-Rounded"), tags=("ground", "defense", "recovery"), follow_ups=("guard_recovery",)),
)

PHASE_30 = RECOVERIES + SWEEPS + STANDUPS + CLINGS + SURVIVALS
