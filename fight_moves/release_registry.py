"""Explicit, immutable 440-move production profile.

The historical public registry remains unchanged for frozen audit fixtures. Runtime
consumers opt into this profile; importing it never patches another module. Keep
construction independent of analysis helpers so packaged play needs no audit code.
"""
from dataclasses import replace
from types import MappingProxyType

from .catalogue import MOVE_DEFINITIONS as _LEGACY_DEFINITIONS
from .catalogue.specialist_entry_development import SPECIALIST_ENTRY_DEVELOPMENT
from .catalogue.front_headlock_development import FRONT_HEADLOCK_DEVELOPMENT
from .catalogue.turtle_development import TURTLE_DEVELOPMENT
from .catalogue.failed_shot_development import FAILED_SHOT_DEVELOPMENT
from .catalogue.standing_back_development import STANDING_BACK_DEVELOPMENT
from .catalogue.leg_entanglement_development import LEG_ENTANGLEMENT_DEVELOPMENT
from .catalogue.survival_development import SURVIVAL_DEVELOPMENT
from .index import MoveIndex
from .chains import MoveChainGraph
from .validation import validate_move_registry
from .registry import normalize_signature_moves, normalize_move_mastery


def _build_release_definitions():
    """Retain the accepted candidate's definition and successor ordering exactly."""
    legacy = {move.move_id: move for move in _LEGACY_DEFINITIONS}
    if len(legacy) != 346:
        raise ValueError("Historical 346-move registry changed; review the release profile")
    gift_wrap = legacy["gift_wrap_transition"]
    if gift_wrap.follow_ups != (
            "mounted_hammerfist_flurry", "rear_naked_choke", "body_triangle_back_control"):
        raise ValueError("Historical gift-wrap successors changed")
    if legacy["high_mount_arm_pinch"].positions != frozenset({"mount"}):
        raise ValueError("Mount-only arm-control geometry changed")
    heel = legacy["heel_hook"]
    if (heel.positions != frozenset({"leg entanglement"})
            or heel.parent_action != "counter_leg_lock"):
        raise ValueError("Historical heel-hook geometry changed")
    corrections = {
        "fence_drive": replace(legacy["fence_drive"], positions=frozenset({"failed shot"})),
        "gift_wrap_transition": replace(gift_wrap, follow_ups=(
            "high_mount_arm_pinch", "rear_naked_choke", "body_triangle_back_control")),
        "heel_hook": replace(heel, parent_action="leg_attack",
                             tags=tuple(tag for tag in heel.tags if tag != "counter")),
    }
    definitions = tuple(corrections.get(move.move_id, move) for move in _LEGACY_DEFINITIONS)
    definitions += (SPECIALIST_ENTRY_DEVELOPMENT + FRONT_HEADLOCK_DEVELOPMENT
                    + TURTLE_DEVELOPMENT + FAILED_SHOT_DEVELOPMENT
                    + STANDING_BACK_DEVELOPMENT + LEG_ENTANGLEMENT_DEVELOPMENT
                    + SURVIVAL_DEVELOPMENT)
    errors = validate_move_registry(definitions)
    if errors:
        raise ValueError("Invalid production move registry: " + "; ".join(errors))
    if len(definitions) != 440:
        raise ValueError("Production profile must contain exactly 440 moves")
    return definitions


RELEASE_MOVE_DEFINITIONS = _build_release_definitions()
RELEASE_MOVE_REGISTRY = MappingProxyType({move.move_id: move for move in RELEASE_MOVE_DEFINITIONS})
RELEASE_MOVE_INDEX = MoveIndex(RELEASE_MOVE_DEFINITIONS)
RELEASE_CHAIN_GRAPH = MoveChainGraph(RELEASE_MOVE_DEFINITIONS)


def normalize_release_signature_moves(values, limit=3):
    """Preserve production IDs through saves without widening legacy audit input."""
    return normalize_signature_moves(values, limit, registry=RELEASE_MOVE_REGISTRY)


def normalize_release_move_mastery(values):
    """Apply existing mastery sanitation against the complete production profile."""
    return normalize_move_mastery(values, registry=RELEASE_MOVE_REGISTRY)
