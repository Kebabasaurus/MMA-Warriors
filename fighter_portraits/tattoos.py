"""Named, crop-visible tattoo direction for real-fighter portrait icons."""

from .styles import TATTOO_DESIGNS

# Only marks visible in the game head/neck/upper-shoulder crop belong here.
# Body art outside that crop is intentionally omitted.  The strings are stable
# catalogue IDs rather than name-derived generated values.
FAMOUS_TATTOOS = {
    "Conor McGregor": ("crown_00", "neck"),
    "Charles Oliveira": ("prayer_hands_03", "neck"),
    "Cody Garbrandt": ("wings_04", "neck"),
}


def named_tattoo(name):
    """Return ``(design_id, placement)`` for a hand-authored icon, if any."""
    record = FAMOUS_TATTOOS.get(str(name or ""))
    if record is None:
        return None
    design, placement = record
    return TATTOO_DESIGNS.index(design), placement
