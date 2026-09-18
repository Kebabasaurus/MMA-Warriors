"""Import-time registry contracts and stable-ID protection."""
from constants import STYLES, DETAILED_SKILL_GROUPS
from .schema import (ALL_POSITIONS, STANDING_POSITIONS, MOVE_TAGS, DEFENSE_TAGS,
                     DEFENSE_FAMILIES, ENTRY_FAMILIES, ATTACK_PATHS)
from .legacy_ids import LEGACY_MOVE_IDS, EXPANSION_MOVE_IDS, PERSISTENT_DEFENSE_IDS
from .coverage import unreachable_moves, coverage_report
from .chains import validate_chain_graph

KNOWN_SKILLS = frozenset(key for group in DETAILED_SKILL_GROUPS.values() for key in group)

def validate_move_registry(definitions=None):
    from .catalogue import MOVE_DEFINITIONS as defaults
    MOVE_DEFINITIONS = tuple(defaults if definitions is None else definitions)
    MOVE_REGISTRY = {d.move_id: d for d in MOVE_DEFINITIONS}
    issues = []
    if len(MOVE_REGISTRY) != len(MOVE_DEFINITIONS):
        issues.append("Move IDs must be unique")
    missing = (LEGACY_MOVE_IDS | EXPANSION_MOVE_IDS) - MOVE_REGISTRY.keys()
    if missing:
        issues.append('Removed stable move IDs: ' + ', '.join(sorted(missing)))
    for definition in MOVE_DEFINITIONS:
        if type(definition.deprecated) is not bool:
            issues.append(f"{definition.move_id}: deprecated must be a boolean")
        for field, allowed in (("tags", MOVE_TAGS), ("defense_families", DEFENSE_FAMILIES)):
            unknown = set(getattr(definition, field)) - allowed
            if unknown:
                issues.append(f'{definition.move_id}: unknown {field}: {sorted(unknown)}')
        for field, allowed in (("entry_family", ENTRY_FAMILIES), ("attack_path", ATTACK_PATHS)):
            value = getattr(definition, field)
            if value and value not in allowed:
                issues.append(f'{definition.move_id}: unknown {field}: {value}')
        if not definition.positions or not definition.positions <= ALL_POSITIONS:
            issues.append(f"{definition.move_id}: contains no positions or an unknown position")
        unknown_skills = set(definition.attack_skills + definition.defense_skills) - KNOWN_SKILLS
        if unknown_skills:
            issues.append(f"{definition.move_id}: unknown skills {', '.join(sorted(unknown_skills))}")
        unknown_styles = set(definition.preferred_styles) - set(STYLES)
        if unknown_styles:
            issues.append(f"{definition.move_id}: unknown styles {', '.join(sorted(unknown_styles))}")
        unknown_followups = set(definition.follow_ups) - set(MOVE_REGISTRY)
        if unknown_followups:
            issues.append(f"{definition.move_id}: unknown follow-ups {', '.join(sorted(unknown_followups))}")
        if definition.minimum_skill < 0 or definition.minimum_skill > 99:
            issues.append(f"{definition.move_id}: minimum skill must be 0-99")
        if min(definition.energy, definition.miss_risk, definition.counter_risk) <= 0:
            issues.append(f"{definition.move_id}: risk and energy values must be positive")
        if "kick" in definition.tags:
            if not definition.targets or not definition.side or not definition.range_band or not definition.defense_families:
                issues.append(f"{definition.move_id}: kick moves require target, side, range, and defense families")
        if "takedown" in definition.tags:
            if not definition.entry_family or not definition.finish_positions or not definition.defense_families:
                issues.append(f"{definition.move_id}: takedowns require entry, finish positions, and defense families")
            if set(definition.finish_positions) - ALL_POSITIONS:
                issues.append(f"{definition.move_id}: unknown takedown finish positions")
        if "submission" in definition.tags:
            if not definition.attack_path or not definition.failure_outcomes:
                issues.append(f"{definition.move_id}: submissions require an attack path and explicit failure outcomes")
        if "finisher" in definition.tags:
            if not set(definition.positions) <= STANDING_POSITIONS or "strike" not in definition.tags:
                issues.append(f"{definition.move_id}: authored finishers must be standing strikes")
            if definition.minimum_skill < 60 or definition.energy <= 1 or definition.counter_risk <= 1:
                issues.append(f"{definition.move_id}: authored finishers must be skill-gated and carry explicit risk")
        if "style-combination" in definition.tags:
            if len(definition.preferred_styles) != 1:
                issues.append(f"{definition.move_id}: style combinations require exactly one owning style")
            if len(definition.components) < 3:
                issues.append(f"{definition.move_id}: style combinations require at least three ordered components")
        if "style-finisher" in definition.tags:
            if len(definition.preferred_styles) != 1:
                issues.append(f"{definition.move_id}: style finishers require exactly one owning style")
            if not set(definition.tags).intersection({"strike", "submission"}):
                issues.append(f"{definition.move_id}: style finishers must be a strike or submission")
    issues.extend(validate_chain_graph(MOVE_DEFINITIONS))
    return issues

def validate_defense_registry(definitions=None):
    from .defenses import DEFENSE_DEFINITIONS as defaults
    DEFENSE_DEFINITIONS = tuple(defaults if definitions is None else definitions)
    DEFENSE_REGISTRY = {d.defense_id: d for d in DEFENSE_DEFINITIONS}
    issues = []
    known_skills = {key for group in DETAILED_SKILL_GROUPS.values() for key in group}
    if len(DEFENSE_REGISTRY) != len(DEFENSE_DEFINITIONS):
        issues.append("Defense IDs must be unique")
    missing = PERSISTENT_DEFENSE_IDS - DEFENSE_REGISTRY.keys()
    if missing:
        issues.append("Removed stable defense IDs: " + ", ".join(sorted(missing)))
    for definition in DEFENSE_DEFINITIONS:
        for field, allowed in (("tags", DEFENSE_TAGS), ("families", DEFENSE_FAMILIES)):
            unknown = set(getattr(definition, field)) - allowed
            if unknown:
                issues.append(f'{definition.defense_id}: unknown {field}: {sorted(unknown)}')
        if not definition.families:
            issues.append(f"{definition.defense_id}: requires a defense family")
        if not definition.positions or not definition.positions <= ALL_POSITIONS:
            issues.append(f"{definition.defense_id}: contains an unknown position")
        unknown = set(definition.skills) - known_skills
        if unknown:
            issues.append(f"{definition.defense_id}: unknown skills {', '.join(sorted(unknown))}")
    return issues
