"""Broad, region-conditioned anatomical colour distributions.

These are intentionally ranges, not a cultural classification: they only select
skin and natural-hair ramps. Country aliases take precedence over nationality,
which takes precedence over a simulation market region.
"""

from constants import COUNTRY_TO_REGION

# (values, weights). Each profile has at least three possible values.
REGION_APPEARANCE = {
    "USA": ((0, 1, 2, 3, 4, 5, 6), (13, 15, 15, 15, 15, 14, 13)),
    "Canada": ((0, 1, 2, 3, 4, 5, 6), (16, 16, 15, 15, 14, 13, 11)),
    "Brazil": ((0, 1, 2, 3, 4, 5, 6), (8, 13, 18, 20, 18, 14, 9)),
    "Mexico": ((0, 1, 2, 3, 4, 5, 6), (7, 15, 22, 23, 17, 11, 5)),
    "UK": ((0, 1, 2, 3, 4, 5, 6), (17, 17, 16, 15, 14, 12, 9)),
    "Europe": ((0, 1, 2, 3, 4, 5, 6), (16, 17, 17, 16, 14, 11, 9)),
    "Russia": ((0, 1, 2, 3, 4, 5, 6), (18, 19, 18, 16, 12, 10, 7)),
    "Japan": ((0, 1, 2, 3, 4, 5, 6), (8, 16, 25, 24, 15, 8, 4)),
    "South Korea": ((0, 1, 2, 3, 4, 5, 6), (7, 15, 25, 25, 16, 8, 4)),
    "Australia": ((0, 1, 2, 3, 4, 5, 6), (16, 17, 17, 16, 14, 11, 9)),
    "Asia": ((0, 1, 2, 3, 4, 5, 6), (9, 15, 21, 22, 17, 10, 6)),
    "Middle East": ((0, 1, 2, 3, 4, 5, 6), (7, 14, 21, 23, 19, 11, 5)),
    "Africa": ((0, 1, 2, 3, 4, 5, 6), (3, 6, 10, 15, 20, 23, 23)),
    "default": ((0, 1, 2, 3, 4, 5, 6), (14, 15, 15, 15, 15, 14, 12)),
}

# Hair is separately broad so no skin profile maps to a single hair colour.
HAIR_WEIGHTS = {
    "default": ((0, 1, 2, 3, 4, 5, 6, 7), (27, 21, 16, 11, 8, 6, 6, 5)),
    "Africa": ((0, 1, 2, 3, 4, 5, 6, 7), (45, 25, 12, 7, 4, 2, 2, 3)),
    "Asia": ((0, 1, 2, 3, 4, 5, 6, 7), (42, 25, 13, 7, 4, 2, 3, 4)),
    "Japan": ((0, 1, 2, 3, 4, 5, 6, 7), (50, 22, 10, 5, 3, 2, 3, 5)),
    "South Korea": ((0, 1, 2, 3, 4, 5, 6, 7), (49, 22, 10, 5, 3, 2, 3, 6)),
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
