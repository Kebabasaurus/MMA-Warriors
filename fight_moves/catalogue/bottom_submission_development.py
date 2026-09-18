"""Slice 6 attacks from established guard positions, not new transition paths."""
from ..presets import submission


def _guard_attack(move_id, name, positions, path, styles, skills, tag, follow_ups):
    return submission(move_id, name, action="bottom_submission", positions=positions,
                      attack_path=path, failure_outcomes=("retain guard", "concede pass", "return neutral"),
                      styles=styles, attack_skills=skills,
                      defense_skills=("submission_defence_detail", "top_control"),
                      minimum_skill=52, tags=("guard", tag), follow_ups=follow_ups,
                      defense_families=("submission defense", "stack"))


BOTTOM_SUBMISSION_DEVELOPMENT = (
    _guard_attack("guard_high_elbow_guillotine", "high-elbow guillotine from guard", {"guard"},
                  "front-headlock neck wrap", ("BJJ", "Luta Livre", "Grappler"),
                  ("submission_attack", "guard_work", "strength"), "choke",
                  ("hip_bump_sweep", "guard_armbar")),
    _guard_attack("guard_arm_in_guillotine", "arm-in guillotine from guard", {"guard", "half guard"},
                  "arm-in neck thread", ("Submission Grappler", "Luta Livre", "Well-Rounded"),
                  ("submission_attack", "guard_work", "positional_ability"), "choke",
                  ("butterfly_sweep", "kimura_guard")),
    _guard_attack("guard_gogoplata", "gogoplata from guard", {"guard"},
                  "guard head-and-arm trap", ("BJJ", "Submission Grappler"),
                  ("submission_attack", "guard_work", "flexibility"), "choke",
                  ("omoplata", "triangle_choke")),
    _guard_attack("guard_reverse_armbar", "reverse armbar from guard", {"guard"},
                  "guard arm isolation", ("BJJ", "Judo", "Grappler"),
                  ("submission_attack", "guard_work", "positional_ability"), "joint-lock",
                  ("kimura_guard", "hip_bump_sweep")),
    _guard_attack("guard_wrist_lock", "wrist lock from guard", {"guard"},
                  "guard arm isolation", ("Catch Wrestler", "BJJ", "Well-Rounded"),
                  ("submission_attack", "guard_work", "hand_speed"), "joint-lock",
                  ("guard_armbar", "kimura_guard")),
    _guard_attack("half_guard_straight_arm_lock", "straight-arm lock from half guard", {"half guard"},
                  "arm isolation", ("Judo", "Catch Wrestler", "Grappler"),
                  ("submission_attack", "bottom_control", "positional_ability"), "joint-lock",
                  ("kimura_guard", "half_guard_underhook_recovery")),
    _guard_attack("guard_overhook_shoulder_lock", "overhook shoulder lock from guard", {"guard"},
                  "bent-arm isolation", ("Judo", "Catch Wrestler", "Grappler"),
                  ("submission_attack", "guard_work", "strength"), "joint-lock",
                  ("guard_armbar", "hip_bump_sweep")),
    _guard_attack("guard_inverted_triangle", "inverted triangle from guard", {"guard"},
                  "guard head-and-arm trap", ("BJJ", "Submission Grappler"),
                  ("submission_attack", "guard_work", "flexibility"), "choke",
                  ("guard_armbar", "technical_standup")),
)
