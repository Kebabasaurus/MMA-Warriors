"""Broad, region-conditioned anatomical colour distributions.

These are intentionally ranges, not a cultural classification: they only select
skin and natural-hair ramps. Country aliases take precedence over nationality,
which takes precedence over a simulation market region.
"""

from constants import COUNTRY_NATIONALITIES, COUNTRY_TO_REGION


# Hair is separately broad so no skin profile maps to a single hair colour.
HAIR_WEIGHTS = {
    "default": (tuple(range(12)), (20, 16, 13, 9, 7, 5, 5, 4, 8, 6, 4, 3)),
    "Africa": (tuple(range(12)), (36, 21, 11, 6, 3, 2, 2, 2, 8, 4, 3, 2)),
    "Asia": (tuple(range(12)), (35, 21, 11, 6, 3, 2, 2, 3, 8, 5, 2, 2)),
    "Japan": (tuple(range(12)), (42, 19, 9, 4, 2, 2, 2, 4, 7, 4, 2, 3)),
    "South Korea": (tuple(range(12)), (41, 19, 9, 4, 2, 2, 2, 5, 7, 4, 2, 3)),
}

# Silhouette is not a regional attribute.  These deliberately broad cosmetic
# distributions make new generated portraits read more intentionally across
# the game's recorded genders, while every shipped style remains possible for
# every group.  Persisted vectors always win, so this only affects newly
# generated identities.
GENDER_HAIR_STYLE_WEIGHTS = {
    "default": (1,) * 48,
    "Male": (
        13, 12, 11, 10, 10, 10, 9, 9, 8, 8, 8, 8, 7, 7, 7, 7,
        5, 5, 5, 5, 6, 6, 6, 6, 6, 5, 5, 5, 5, 4, 4, 4,
        3, 2, 2, 3, 8, 3, 1, 4, 12, 12, 5, 3, 4, 6, 8, 10,
    ),
    "Female": (
        1, 1, 1, 1, 2, 2, 3, 2, 3, 2, 2, 3, 2, 8, 8, 4,
        12, 14, 14, 10, 12, 24, 14, 16, 22, 16, 10, 10, 2, 2, 3, 1,
        12, 18, 14, 22, 14, 26, 10, 16, 5, 5, 10, 22, 24, 10, 2, 7,
    ),
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


# Art-direction priors, not demographic estimates or classifications of an
# individual. Palette IDs are NOT ordered by lightness (7 is light, 8 medium).
# All profiles retain multiple tones; mixed-population profiles stay broad.
TONE_PROFILES = {
    "light": (30, 30, 10, 2, 1, 1, 1, 22, 2, 1, 1, 1),
    "light_medium": (12, 27, 28, 8, 2, 1, 1, 14, 10, 4, 1, 1),
    "medium": (2, 10, 27, 22, 7, 2, 1, 5, 18, 10, 2, 1),
    "medium_deep": (1, 2, 9, 19, 22, 10, 5, 1, 10, 17, 9, 5),
    "deep": (1, 1, 2, 4, 21, 21, 12, 1, 3, 10, 14, 10),
    "mixed": (12, 20, 17, 10, 8, 7, 4, 9, 5, 4, 3, 3),
}
REGION_TONE_PROFILES = {
    "USA": "mixed", "Canada": "mixed", "UK": "light", "Europe": "light_medium",
    "Russia": "light_medium", "Japan": "light_medium", "South Korea": "light_medium",
    "Australia": "mixed", "Brazil": "mixed", "Mexico": "medium",
    "Asia": "medium", "Middle East": "medium", "Africa": "deep",
}
REGION_APPEARANCE = {
    region: (tuple(range(12)), TONE_PROFILES[profile])
    for region, profile in REGION_TONE_PROFILES.items()
} | {"default": (tuple(range(12)), TONE_PROFILES["mixed"])}

COUNTRY_TONE_PROFILES = {
    **dict.fromkeys(("Nigeria", "Ghana", "Senegal", "Cameroon", "Kenya", "Uganda",
                     "Democratic Republic of the Congo", "Angola"), "deep"),
    **dict.fromkeys(("Morocco", "Algeria", "Tunisia", "Egypt", "Iran", "Iraq",
                     "Thailand", "Philippines", "Indonesia", "Vietnam", "Mexico"), "medium"),
    **dict.fromkeys(("India", "Pakistan", "Bangladesh", "Sri Lanka"), "medium_deep"),
    **dict.fromkeys(("Japan", "South Korea", "China", "Taiwan", "Mongolia",
                     "Russia", "Turkey", "Georgia", "Armenia", "Kazakhstan"), "light_medium"),
    **dict.fromkeys(("Ireland", "UK", "Poland", "Sweden", "Norway", "Finland",
                     "Denmark", "Germany", "Ukraine", "Iceland", "Netherlands"), "light"),
    **dict.fromkeys(("United States", "Canada", "Brazil", "South Africa", "Australia",
                     "New Zealand", "France"), "mixed"),
}
_COUNTRY_NAMES = {
    "usa": "United States", "united states of america": "United States",
    "united kingdom": "UK", "england": "UK", "scotland": "UK", "wales": "UK",
    "northern ireland": "UK", "republic of ireland": "Ireland",
    "people's republic of china": "China",
}
_KNOWN_COUNTRIES = {name.casefold(): name for name in
                    (*COUNTRY_TO_REGION, *COUNTRY_TONE_PROFILES, *REGION_APPEARANCE)}
_NATIONALITY_COUNTRIES = {adjective.casefold(): country
                          for country, adjective in COUNTRY_NATIONALITIES.items()}


def canonical_country(value):
    value = str(value or "").strip()
    value = _NATIONALITY_COUNTRIES.get(value.casefold(), value)
    return _COUNTRY_NAMES.get(value.casefold(), _KNOWN_COUNTRIES.get(value.casefold(), value))


def _resolve_region(value):
    country = canonical_country(value)
    region = COUNTRY_TO_REGION.get(country, country)
    return region if region in REGION_APPEARANCE else None


def appearance_region(fighter):
    """Resolve the documented origin order without using fighting-base data."""
    country = str(getattr(fighter, "birth_country", "") or "").strip()
    if _resolve_region(country):
        return _resolve_region(country)
    nationality = str(getattr(fighter, "nationality", "") or "").strip()
    if nationality:
        resolved = _resolve_region(nationality) or NATIONALITY_ALIASES.get(nationality.title())
        if resolved:
            return resolved
    region = str(getattr(fighter, "region", "") or "").strip()
    if _resolve_region(region):
        return _resolve_region(region)
    birth_region = str(getattr(fighter, "birth_region", "") or "").strip()
    return birth_region if birth_region in REGION_APPEARANCE else "default"


def skin_distribution(fighter):
    for field in ("birth_country", "nationality"):
        country = canonical_country(getattr(fighter, field, ""))
        if country in COUNTRY_TONE_PROFILES:
            return tuple(range(12)), TONE_PROFILES[COUNTRY_TONE_PROFILES[country]]
        region = _resolve_region(country) or NATIONALITY_ALIASES.get(country.title())
        if region:
            return REGION_APPEARANCE[region]
    return REGION_APPEARANCE[appearance_region(fighter)]


def hair_distribution(fighter):
    region = appearance_region(fighter)
    if region in {"Africa", "Asia", "Japan", "South Korea", "Middle East", "Mexico", "Brazil"}:
        return tuple(range(12)), (48, 26, 9, 2, 1, 1, 1, 1, 18, 7, 1, 1)
    return HAIR_WEIGHTS.get(region, HAIR_WEIGHTS["default"])
