"""Broad, region-conditioned anatomical colour distributions.

These are intentionally ranges, not a cultural classification: they only select
skin and natural-hair ramps. Country aliases take precedence over nationality,
which takes precedence over a simulation market region.
"""

from constants import COUNTRY_TO_REGION

# (values, weights). Each profile has at least three possible values.
REGION_APPEARANCE = {
    "USA": (tuple(range(12)), (8, 9, 10, 10, 10, 9, 8, 8, 8, 8, 7, 7)),
    "Canada": (tuple(range(12)), (11, 11, 10, 9, 8, 7, 6, 7, 8, 8, 7, 8)),
    "Brazil": (tuple(range(12)), (5, 8, 12, 14, 13, 10, 6, 8, 10, 8, 4, 2)),
    "Mexico": (tuple(range(12)), (5, 10, 15, 16, 13, 8, 4, 8, 10, 7, 3, 1)),
    "UK": (tuple(range(12)), (12, 12, 11, 9, 8, 6, 5, 7, 8, 7, 6, 9)),
    "Europe": (tuple(range(12)), (11, 12, 11, 10, 8, 6, 5, 7, 8, 7, 6, 9)),
    "Russia": (tuple(range(12)), (14, 14, 12, 9, 6, 5, 3, 6, 6, 4, 3, 4)),
    "Japan": (tuple(range(12)), (6, 11, 17, 16, 10, 5, 2, 9, 12, 7, 3, 2)),
    "South Korea": (tuple(range(12)), (5, 10, 17, 17, 10, 5, 2, 9, 12, 7, 3, 3)),
    "Australia": (tuple(range(12)), (11, 12, 11, 10, 8, 6, 5, 7, 8, 7, 6, 9)),
    "Asia": (tuple(range(12)), (7, 10, 14, 15, 11, 6, 3, 9, 11, 8, 4, 2)),
    "Middle East": (tuple(range(12)), (5, 9, 14, 16, 13, 8, 3, 8, 11, 8, 4, 1)),
    "Africa": (tuple(range(12)), (2, 3, 5, 8, 12, 15, 16, 7, 9, 11, 7, 5)),
    "default": (tuple(range(12)), (9, 10, 10, 10, 9, 8, 7, 8, 8, 8, 6, 7)),
}

# Hair is separately broad so no skin profile maps to a single hair colour.
HAIR_WEIGHTS = {
    "default": (tuple(range(12)), (20, 16, 13, 9, 7, 5, 5, 4, 8, 6, 4, 3)),
    "Africa": (tuple(range(12)), (36, 21, 11, 6, 3, 2, 2, 2, 8, 4, 3, 2)),
    "Asia": (tuple(range(12)), (35, 21, 11, 6, 3, 2, 2, 3, 8, 5, 2, 2)),
    "Japan": (tuple(range(12)), (42, 19, 9, 4, 2, 2, 2, 4, 7, 4, 2, 3)),
    "South Korea": (tuple(range(12)), (41, 19, 9, 4, 2, 2, 2, 5, 7, 4, 2, 3)),
}

# Only resolution aliases; values retain the broad market distributions above.
COUNTRY_ALIASES = {
    "United States of America": "United States", "USA": "United States",
    "United Kingdom": "UK", "England": "UK", "Scotland": "UK", "Wales": "UK",
    "Northern Ireland": "UK", "Republic of Ireland": "Europe", "Czech Republic": "Europe",
    "People's Republic of China": "Asia", "New Zealand": "Australia",
}
NATIONALITY_ALIASES = {
    "American": "USA", "Canadian": "Canada", "Brazilian": "Brazil", "Mexican": "Mexico",
    "British": "UK", "English": "UK", "Scottish": "UK", "Welsh": "UK", "Irish": "Europe",
    "Russian": "Russia", "Japanese": "Japan", "South Korean": "South Korea",
    "Australian": "Australia", "Nigerian": "Africa", "South African": "Africa",
}


def appearance_region(fighter):
    """Resolve the documented origin order without using fighting-base data."""
    country = str(getattr(fighter, "birth_country", "") or "").strip()
    if country:
        return COUNTRY_ALIASES.get(country, COUNTRY_TO_REGION.get(country, country if country in REGION_APPEARANCE else "default"))
    nationality = str(getattr(fighter, "nationality", "") or "").strip()
    if nationality:
        return NATIONALITY_ALIASES.get(nationality, "default")
    region = str(getattr(fighter, "region", "") or "").strip()
    if region:
        return region if region in REGION_APPEARANCE else "default"
    birth_region = str(getattr(fighter, "birth_region", "") or "").strip()
    return birth_region if birth_region in REGION_APPEARANCE else "default"
