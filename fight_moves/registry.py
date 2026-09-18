"""Construct the validated public registries once per import."""
from .catalogue import MOVE_DEFINITIONS
from .defenses import DEFENSE_DEFINITIONS, DEFENSE_REGISTRY, legal_defenses
from .validation import validate_move_registry, validate_defense_registry
from .index import MoveIndex
from .chains import MoveChainGraph

MOVE_REGISTRY = {definition.move_id: definition for definition in MOVE_DEFINITIONS}
KNOWN_PARENT_ACTIONS = frozenset(definition.parent_action for definition in MOVE_DEFINITIONS)

MOVE_REGISTRY_ERRORS = tuple(validate_move_registry())
if MOVE_REGISTRY_ERRORS:
    raise ValueError("Invalid MMA move registry: " + "; ".join(MOVE_REGISTRY_ERRORS))

DEFENSE_REGISTRY_ERRORS = tuple(validate_defense_registry())
if DEFENSE_REGISTRY_ERRORS:
    raise ValueError("Invalid MMA defense registry: " + "; ".join(DEFENSE_REGISTRY_ERRORS))

MOVE_INDEX = MoveIndex(MOVE_DEFINITIONS)
CHAIN_GRAPH = MoveChainGraph(MOVE_DEFINITIONS)
chain_depth = CHAIN_GRAPH.chain_depth
legal_moves = MOVE_INDEX.legal_moves

def normalize_signature_moves(values, limit=3, *, registry=None):
    """Return unique, stable registry IDs while ignoring unknown future moves."""
    registry = MOVE_REGISTRY if registry is None else registry
    if not isinstance(values, (list, tuple)):
        return []
    result = []
    for value in values:
        move_id = str(value or "").strip()
        if move_id in registry and move_id not in result:
            result.append(move_id)
        if len(result) >= max(0, int(limit)):
            break
    return result

def normalize_move_mastery(values, *, registry=None):
    """Normalize save-compatible offensive and defensive mastery ratings."""
    registry = MOVE_REGISTRY if registry is None else registry
    if not isinstance(values, dict):
        return {}
    result = {}
    for raw_key, raw_value in values.items():
        key = str(raw_key or "")
        known = key in registry or (key.startswith("defense:") and key[8:] in DEFENSE_REGISTRY)
        if not known:
            continue
        try:
            value = int(round(float(raw_value)))
        except (TypeError, ValueError):
            continue
        result[key] = max(0, min(100, value))
    return result
