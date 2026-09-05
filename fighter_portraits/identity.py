"""Persistable portrait identity vectors; no rendering or game mechanics."""

import hashlib

from .regions import GENDER_HAIR_STYLE_WEIGHTS, HAIR_WEIGHTS, REGION_APPEARANCE, appearance_region
from .styles import (
    BACKGROUND, BROW_STYLES, CHEEK_SHAPES, CHIN_SHAPES, EAR_SHAPES, EYE_SHAPES,
    EYE_SIZES, EYE_SPACINGS, FACIAL_HAIR, FACE_LENGTHS, HAIR, HAIR_STYLES,
    IDENTITY_TRAITS, JAW_SHAPES, MOUTH_SHAPES, NOSE_SHAPES, SKIN,
)

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
    gender = str(getattr(fighter, "gender", "") or "")
    hair_style_weights = GENDER_HAIR_STYLE_WEIGHTS.get(gender, GENDER_HAIR_STYLE_WEIGHTS["default"])
    return {
        "skin": _weighted_trait(fighter_id, "skin", skin_choices, skin_weights),
        "hair_colour": _weighted_trait(fighter_id, "hair_colour", hair_choices, hair_weights),
        "hair_style": _weighted_trait(fighter_id, "hair_style", tuple(range(len(HAIR_STYLES))), hair_style_weights),
        "facial_hair": trait_hash(fighter_id, "facial_hair", len(FACIAL_HAIR)),
        "dye": "", "brow": trait_hash(fighter_id, "brow", len(BROW_STYLES)),
        "eye_shape": trait_hash(fighter_id, "eye_shape", len(EYE_SHAPES)), "eye_spacing": trait_hash(fighter_id, "eye_spacing", len(EYE_SPACINGS)),
        "eye_size": trait_hash(fighter_id, "eye_size", len(EYE_SIZES)), "nose": trait_hash(fighter_id, "nose", len(NOSE_SHAPES)),
        "mouth": trait_hash(fighter_id, "mouth", len(MOUTH_SHAPES)), "jaw": trait_hash(fighter_id, "jaw", len(JAW_SHAPES)),
        "chin": trait_hash(fighter_id, "chin", len(CHIN_SHAPES)), "cheek": trait_hash(fighter_id, "cheek", len(CHEEK_SHAPES)),
        "face_length": trait_hash(fighter_id, "face_length", len(FACE_LENGTHS)), "ear": trait_hash(fighter_id, "ear", len(EAR_SHAPES)),
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
