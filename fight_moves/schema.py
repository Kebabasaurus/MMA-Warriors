"""Immutable technique schema and explicit authoring vocabularies."""
from dataclasses import dataclass

REGISTRY_SCHEMA_VERSION = 2

ALL_POSITIONS = frozenset({
    "range", "pocket", "clinch", "cage", "failed shot", "standing back control",
    "guard", "half guard", "side control", "mount", "back control", "turtle",
    "front headlock", "leg entanglement",
})

STANDING_POSITIONS = frozenset({"range", "pocket"})

CLINCH_POSITIONS = frozenset({"clinch", "cage", "standing back control"})

GROUND_POSITIONS = frozenset({
    "guard", "half guard", "side control", "mount", "back control", "turtle",
    "front headlock", "leg entanglement",
})

@dataclass(frozen=True)
class MoveDefinition:
    move_id: str
    name: str
    parent_action: str
    positions: frozenset
    targets: frozenset = frozenset()
    attack_skills: tuple = ()
    defense_skills: tuple = ()
    preferred_styles: tuple = ()
    minimum_skill: int = 0
    energy: float = 1.0
    miss_risk: float = 1.0
    counter_risk: float = 1.0
    follow_ups: tuple = ()
    tags: tuple = ()
    side: str = ""
    range_band: str = ""
    defense_families: tuple = ()
    entry_family: str = ""
    finish_positions: tuple = ()
    attack_path: str = ""
    failure_outcomes: tuple = ()
    components: tuple = ()
    deprecated: bool = False

@dataclass(frozen=True)
class DefenseDefinition:
    defense_id: str
    name: str
    families: tuple
    positions: frozenset
    skills: tuple
    tags: tuple = ()

def defense(defense_id, name, families, positions, skills, tags=()):
    return DefenseDefinition(defense_id, name, tuple(families), frozenset(positions), tuple(skills), tuple(tags))

def move(move_id, name, action, positions, **kwargs):
    return MoveDefinition(move_id, name, action, frozenset(positions), **kwargs)

MOVE_TAGS = frozenset({
    "back-control",
    "back-take",
    "body",
    "body-head",
    "cage",
    "chain",
    "choke",
    "clinch",
    "combination",
    "control",
    "counter",
    "creative",
    "defense",
    "elbow",
    "entry",
    "escape",
    "feint",
    "finisher",
    "flying",
    "footwork",
    "frame",
    "front-headlock",
    "ground",
    "guard",
    "half-guard",
    "head",
    "high-risk",
    "intercept",
    "joint",
    "joint-lock",
    "kick",
    "knee",
    "leg",
    "leg-entanglement",
    "leg-lock",
    "level-change",
    "low-kick",
    "mat-return",
    "mixed-combination",
    "mount",
    "movement",
    "pass",
    "power",
    "pressure",
    "pummel",
    "punch",
    "recovery",
    "ride",
    "scramble",
    "setup",
    "shell",
    "smother",
    "spinning",
    "stance-shift",
    "strike",
    "style-combination",
    "style-finisher",
    "submission",
    "sweep",
    "takedown",
    "throw",
    "transition",
    "trip",
    "turtle",
    "underhook",
    "underhooks",
    "whizzer",
    "wrestling",
    "wrist-control",
})

DEFENSE_TAGS = frozenset({
    "body",
    "punch",
    "block",
    "cage",
    "catch",
    "check",
    "clinch",
    "control",
    "escape",
    "evasion",
    "frame",
    "grip-defense",
    "ground",
    "kick",
    "leg-lock",
    "parry",
    "scramble",
    "sprawl",
    "strike",
    "submission",
    "underhook",
    "whizzer",
    "wrestling",
})

DEFENSE_FAMILIES = frozenset({
    "back step",
    "back take",
    "balance",
    "base",
    "block",
    "block-check",
    "cage escape",
    "catch",
    "check",
    "duck",
    "evade",
    "fence post",
    "frame",
    "guard frame",
    "hand fight",
    "hip block",
    "hip pressure",
    "hip turn",
    "hop",
    "jam",
    "leg escape",
    "limp leg",
    "parry",
    "parry-check",
    "pullback",
    "scramble",
    "shell",
    "sidestep",
    "slip-block",
    "sprawl",
    "stack",
    "stance switch",
    "submission defense",
    "underhook",
    "wall walk",
    "whizzer",
    "wide base",
})

ENTRY_FAMILIES = frozenset({
    "body lock",
    "double leg",
    "high crotch",
    "over-under",
    "rear body lock",
    "single leg",
    "underhook",
})

ATTACK_PATHS = frozenset({
    "arm isolation",
    "arm-in front-headlock roll",
    "arm-in neck thread",
    "back-control leg triangle",
    "back-control neck exposure",
    "bent-arm isolation",
    "cradle-and-neck isolation",
    "figure-four foot isolation",
    "figure-four shoulder isolation",
    "front-headlock neck wrap",
    "guard arm isolation",
    "guard head-and-arm trap",
    "guard isolation",
    "head-and-arm compression from top",
    "head-and-arm isolation",
    "heel exposure from entanglement",
    "knee-line isolation",
    "leg-over shoulder isolation",
    "outside ashi heel exposure",
    "position-to-isolation",
    "rolling knee-line isolation",
    "scarf-hold arm isolation",
    "straight-leg entanglement",
    "triangle lock chained to arm extension",
})

HIGH_RISK_TAG = "high-risk"
FINISHER_TAG = "finisher"
STYLE_COMBINATION_TAG = "style-combination"
STYLE_FINISHER_TAG = "style-finisher"
COUNTER_TAG = "counter"
BEHAVIOURAL_TAGS = frozenset({HIGH_RISK_TAG, FINISHER_TAG, STYLE_COMBINATION_TAG, STYLE_FINISHER_TAG, COUNTER_TAG})
