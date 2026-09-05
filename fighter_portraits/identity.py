"""Persistable portrait identity vectors; no rendering or game mechanics."""

import hashlib

from .regions import HAIR_WEIGHTS, REGION_APPEARANCE, appearance_region
from .styles import BACKGROUND, FACIAL_HAIR, HAIR, HAIR_STYLES, IDENTITY_TRAITS, SKIN

CURRENT_PORTRAIT_VERSION = 1


def trait_hash(fighter_id, trait, mod):
    """Return an independent stable hash draw for one immutable trait."""
    if mod <= 0:
        raise ValueError("portrait trait modulus must be positive")
    digest = hashlib.blake2b(f"{fighter_id}|{trait}".encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % mod


def _weighted_trait(fighter_id, trait, choices, weights):
    total = sum(weights)
    draw = trait_hash(fighter_id, trait, total)
    upto = 0
    for choice, weight in zip(choices, weights):
        upto += weight
        if draw < upto:
            return choice
    return choices[-1]


def derived_portrait_identity(fighter):
    """Create a new vector from the stable fighter id and origin only."""
    fighter_id = str(getattr(fighter, "fighter_id", "") or "")
    if not fighter_id:
        raise ValueError("portrait identity requires a stable fighter_id")
    region = appearance_region(fighter)
    skin_choices, skin_weights = REGION_APPEARANCE.get(region, REGION_APPEARANCE["default"])
    hair_choices, hair_weights = HAIR_WEIGHTS.get(region, HAIR_WEIGHTS["default"])
    return {
        "skin": _weighted_trait(fighter_id, "skin", skin_choices, skin_weights),
        "hair_colour": _weighted_trait(fighter_id, "hair_colour", hair_choices, hair_weights),
        "hair_style": trait_hash(fighter_id, "hair_style", len(HAIR_STYLES)),
        "facial_hair": trait_hash(fighter_id, "facial_hair", len(FACIAL_HAIR)),
        "dye": "", "brow": trait_hash(fighter_id, "brow", 5),
        "eye_shape": trait_hash(fighter_id, "eye_shape", 6), "eye_spacing": trait_hash(fighter_id, "eye_spacing", 3),
        "eye_size": trait_hash(fighter_id, "eye_size", 3), "nose": trait_hash(fighter_id, "nose", 6),
        "mouth": trait_hash(fighter_id, "mouth", 5), "jaw": trait_hash(fighter_id, "jaw", 5),
        "chin": trait_hash(fighter_id, "chin", 4), "cheek": trait_hash(fighter_id, "cheek", 4),
        "face_length": trait_hash(fighter_id, "face_length", 3), "ear": trait_hash(fighter_id, "ear", 4),
        "head_w": trait_hash(fighter_id, "head_w", 100), "bg": trait_hash(fighter_id, "bg", len(BACKGROUND)),
    }


def _overrides_for(fighter):
    from .overrides import PORTRAIT_OVERRIDES
    return PORTRAIT_OVERRIDES.get(str(getattr(fighter, "name", "") or ""), {})


def portrait_identity(fighter):
    """Return the stored identity (or a non-mutating derived preview) with overrides."""
    stored = getattr(fighter, "portrait_identity", None)
    # New keys can be added in future without disturbing any persisted trait:
    # derive only the missing independent draws, then let saved values win.
    identity = derived_portrait_identity(fighter)
    if isinstance(stored, dict) and stored:
        identity.update(stored)
    identity.update(_overrides_for(fighter))
    return identity


def ensure_portrait_identity(fighter):
    """Backfill once; never restyle a saved vector after generator changes."""
    current = getattr(fighter, "portrait_identity", None)
    if not isinstance(current, dict) or not current:
        fighter.portrait_identity = derived_portrait_identity(fighter)
        fighter.portrait_version = CURRENT_PORTRAIT_VERSION
    elif not hasattr(fighter, "portrait_version"):
        fighter.portrait_version = 0
    return portrait_identity(fighter)


def identity_keys_are_stable():
    """Small explicit hook for regression tests guarding the save contract."""
    return tuple(IDENTITY_TRAITS)
