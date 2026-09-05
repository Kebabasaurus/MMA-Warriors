"""Derived cosmetic state. These values are recomputed and never persisted."""


def _clamp(value):
    return max(0.0, min(1.0, float(value)))


def portrait_state(fighter):
    bouts = max(0, int(getattr(fighter, "record_w", 0) or 0) + int(getattr(fighter, "record_l", 0) or 0) + int(getattr(fighter, "record_d", 0) or 0))
    age = max(0, int(getattr(fighter, "age", 0) or 0))
    return {
        "grey": _clamp((age - 34) / 18), "recede": _clamp((age - 29) / 20),
        "cauli": _clamp(bouts / 26), "scar": _clamp(bouts / 32),
        "swell": 1.0 if (getattr(fighter, "injured", 0) or getattr(fighter, "serious_injury", "")) else 0.0,
    }
