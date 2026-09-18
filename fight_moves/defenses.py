"""Named defensive techniques, in compatibility order."""
from .schema import defense, ALL_POSITIONS, STANDING_POSITIONS, CLINCH_POSITIONS, GROUND_POSITIONS
from .defense_expansion import PHASE_33_DEFENSES

DEFENSE_DEFINITIONS = (
    defense("high_guard", "high guard", ("block", "shell", "slip-block"), STANDING_POSITIONS, ("guard_defence", "composure"), ("strike", "block")),
    defense("outside_parry", "outside parry", ("parry", "parry-check"), STANDING_POSITIONS, ("guard_defence", "reflexes"), ("strike", "parry")),
    defense("slip_exit", "slip and angle exit", ("evade", "sidestep", "pullback"), STANDING_POSITIONS, ("head_movement", "footwork"), ("strike", "evasion")),
    defense("shin_check", "shin check", ("check", "block-check"), STANDING_POSITIONS, ("kick_defence", "mobility"), ("kick", "check")),
    defense("kick_catch", "kick catch", ("catch",), STANDING_POSITIONS, ("reflexes", "takedown_defence_detail"), ("kick", "catch")),
    defense("knee_jam", "knee-and-elbow jam", ("jam",), STANDING_POSITIONS | CLINCH_POSITIONS, ("clinch_defence", "reflexes"), ("clinch", "frame")),
    defense("hip_sprawl", "hips-heavy sprawl", ("sprawl",), ALL_POSITIONS, ("sprawl", "takedown_defence_detail"), ("wrestling", "sprawl")),
    defense("whizzer_balance", "whizzer and balance", ("whizzer", "balance", "wide base", "base"), ALL_POSITIONS, ("clinch_defence", "strength"), ("wrestling", "whizzer")),
    defense("fence_post", "fence post and hip frame", ("fence post", "hip pressure"), CLINCH_POSITIONS | frozenset({"failed shot"}), ("cage_wrestling", "strength"), ("cage", "frame")),
    defense("underhook_turn", "underhook hip turn", ("underhook", "hip turn", "hip block"), CLINCH_POSITIONS, ("clinch_defence", "cage_wrestling"), ("clinch", "underhook")),
    defense("limp_leg", "limp-leg withdrawal", ("limp leg", "hop"), ALL_POSITIONS, ("scrambles", "mobility"), ("wrestling", "escape")),
    defense("hand_fight_escape", "two-on-one hand fight", ("hand fight",), CLINCH_POSITIONS | GROUND_POSITIONS, ("get_ups", "scrambles"), ("control", "escape")),
    defense("guard_frame", "guard frame and hip escape", ("frame", "guard frame"), GROUND_POSITIONS, ("guard_work", "bottom_control"), ("ground", "frame")),
    defense("submission_hand_fight", "submission hand fighting", ("submission defense",), GROUND_POSITIONS, ("submission_defence_detail", "composure"), ("submission", "grip-defense")),
    defense("stack_escape", "stack-and-turn escape", ("stack",), GROUND_POSITIONS, ("submission_defence_detail", "strength"), ("submission", "escape")),
    defense("knee_line_escape", "knee-line escape", ("leg escape",), frozenset({"guard", "half guard", "leg entanglement"}), ("submission_defence_detail", "mobility"), ("leg-lock", "escape")),
    defense("wall_walk", "wall-walk escape", ("wall walk", "cage escape"), CLINCH_POSITIONS | GROUND_POSITIONS, ("get_ups", "cage_wrestling"), ("cage", "escape")),
    defense("technical_scramble", "technical scramble", ("scramble", "back step", "back take"), ALL_POSITIONS, ("scrambles", "transitions"), ("scramble", "escape")),
)

DEFENSE_DEFINITIONS = DEFENSE_DEFINITIONS + PHASE_33_DEFENSES
DEFENSE_REGISTRY = {definition.defense_id: definition for definition in DEFENSE_DEFINITIONS}

def legal_defenses(families, position):
    families = set(families or ())
    return tuple(definition for definition in DEFENSE_DEFINITIONS
                 if position in definition.positions and families.intersection(definition.families))
