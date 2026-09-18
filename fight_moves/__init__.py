"""Public compatibility API for MMA technique definitions."""
from .schema import (MoveDefinition, DefenseDefinition, move, defense, ALL_POSITIONS, REGISTRY_SCHEMA_VERSION,
                     STANDING_POSITIONS, CLINCH_POSITIONS, GROUND_POSITIONS,
                     MOVE_TAGS, DEFENSE_TAGS, DEFENSE_FAMILIES, ENTRY_FAMILIES,
                     ATTACK_PATHS, BEHAVIOURAL_TAGS)
from .validation import validate_move_registry, validate_defense_registry, KNOWN_SKILLS
from .index import MoveIndex
from .chains import MoveChainGraph, validate_chain_graph
from .registry import (MOVE_DEFINITIONS, MOVE_REGISTRY, MOVE_REGISTRY_ERRORS,
                       KNOWN_PARENT_ACTIONS, DEFENSE_DEFINITIONS, DEFENSE_REGISTRY,
                       DEFENSE_REGISTRY_ERRORS, legal_moves, legal_defenses,
                       normalize_signature_moves, normalize_move_mastery, MOVE_INDEX,
                       CHAIN_GRAPH, chain_depth)
