"""Derived cosmetic state. These values are recomputed and never persisted."""

from .identity import trait_hash
from .styles import SCALP_FINISHES


def _clamp(value):
    return max(0.0, min(1.0, float(value)))


def portrait_state(fighter):
    bouts = max(0, int(getattr(fighter, "record_w", 0) or 0) + int(getattr(fighter, "record_l", 0) or 0) + int(getattr(fighter, "record_d", 0) or 0))
    age = max(0, int(getattr(fighter, "age", 0) or 0))
    recent = getattr(fighter, "last_fight_stats", None) or {}
    recent = recent if isinstance(recent, dict) else {}
    cut_details = recent.get("cut_details", [])
    cut_details = [row for row in cut_details if isinstance(row, dict)] if isinstance(cut_details, list) else []
    head_damage = max(0, int(recent.get("head_damage", 0) or 0))
    cut_severity = max((max(0, int(row.get("severity", 0) or 0)) for row in cut_details), default=0)
    cut_location = str(max(cut_details, key=lambda row: int(row.get("severity", 0) or 0)).get("location", "") or "") if cut_details else ""
    fighter_id = str(getattr(fighter, "fighter_id", "") or "")
    # The finish is not a persisted identity trait: it is a cosmetic, age-led
    # scalp detail.  A young reference portrait remains untouched, while a
    # mature shaved/buzzed fighter receives one stable treatment per id.
    scalp_finish = trait_hash(fighter_id, "scalp_finish", len(SCALP_FINISHES)) if age >= 30 else None
    return {
        "grey": _clamp((age - 34) / 18), "recede": _clamp((age - 29) / 20),
        "cauli": _clamp(bouts / 26), "scar": _clamp(bouts / 32),
        # This supplements, rather than replaces, the immutable nose shape.
        # Long careers increasingly get the small broken-nose silhouette.
        "nose_damage": _clamp(bouts / 45),
        # Recent structured bout facts are cosmetic presentation only. They
        # never feed a rating or simulation path and disappear on the next
        # recorded bout rather than becoming invented permanent scars.
        "recent_head_damage": _clamp(head_damage / 40),
        "recent_cut": _clamp(cut_severity / 6),
        "recent_cut_location": cut_location,
        "swell": max(_clamp(head_damage / 34), 1.0 if (getattr(fighter, "injured", 0) or getattr(fighter, "serious_injury", "")) else 0.0),
        "scalp_finish": scalp_finish,
    }
