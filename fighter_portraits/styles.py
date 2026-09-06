"""Stable portrait style identifiers and colour ramps.

Do not rename or reorder these identifiers: portrait identities are persisted in
saves. New entries may only be appended.
"""

# (name, crown_volume, side_coverage, hairline_offset, texture)
HAIR_STYLES = (
    ("shaved", 0.000, 0, 0.00, "flat"), ("buzz", 0.006, 0, 0.00, "flat"),
    ("crew_cut", 0.012, 0, 0.00, "flat"), ("crop", 0.016, 0, 0.00, "flat"),
    ("short_fade", 0.020, 0, -0.02, "flat"), ("high_fade", 0.024, 0, -0.03, "flat"),
    ("side_part", 0.026, 0, 0.00, "flat"), ("comb_over", 0.024, 0, 0.01, "flat"),
    ("slick_back", 0.024, 0, -0.03, "flat"), ("quiff", 0.040, 0, -0.01, "flat"),
    ("pompadour", 0.052, 0, -0.01, "flat"), ("high_top", 0.062, 0, -0.01, "coil"),
    ("flat_top", 0.050, 0, -0.01, "coil"), ("afro", 0.070, 1, 0.00, "coil"),
    ("curly_mop", 0.048, 1, 0.02, "curl"), ("bowl_cut", 0.030, 1, 0.02, "flat"),
    ("wavy_medium", 0.030, 1, 0.01, "curl"), ("shoulder_wave", 0.032, 2, 0.02, "curl"),
    ("long_loose", 0.034, 2, 0.01, "flat"), ("man_bun", 0.026, 1, 0.00, "knot"),
    ("top_knot", 0.030, 0, 0.00, "knot"), ("ponytail", 0.022, 1, 0.00, "tail"),
    ("half_up", 0.028, 2, 0.00, "tail"), ("cornrows", 0.014, 1, -0.01, "braid"),
    ("braided_back", 0.020, 1, -0.02, "braid"), ("box_braids", 0.034, 2, 0.00, "braid"),
    ("dreads", 0.040, 2, 0.00, "dread"), ("twists", 0.030, 1, 0.00, "twist"),
    ("mohawk", 0.055, 0, -0.02, "spike"), ("faux_hawk", 0.038, 0, -0.02, "spike"),
    ("undercut", 0.034, 0, -0.02, "flat"), ("receding_nat", 0.014, 0, 0.04, "flat"),
    ("pixie_swept", .026, 0, .00, "sweep"),
    ("chin_bob", .030, 2, .00, "bob"),
    ("angled_bob", .030, 2, -.01, "angled_bob"),
    ("long_centre_part", .034, 2, -.03, "centre"),
    ("side_swept_fringe", .036, 1, .00, "sweep"),
    ("twin_braids", .020, 2, -.02, "twin_braids"),
    ("double_buns", .025, 0, -.02, "double_buns"),
    ("high_curly_puff", .065, 0, -.03, "puff"),
    ("short_coils", .024, 0, -.01, "coil"),
    ("curly_taper", .038, 0, -.02, "curl"),
    ("locs_tied_up", .050, 0, -.02, "loc_knot"),
    ("low_bun", .022, 1, -.02, "low_bun"),
    ("braided_ponytail", .020, 1, -.02, "braid_tail"),
    ("shag_layers", .045, 2, .01, "shag"),
    ("mullet", .025, 2, -.01, "mullet"),
    ("curtain_crop", .036, 1, .01, "curtains"),
)

FACIAL_HAIR = (
    "none", "stubble_light", "stubble_heavy", "moustache", "horseshoe", "goatee",
    "van_dyke", "soul_patch", "chin_strap", "short_beard", "full_beard",
    "heavy_beard", "long_beard", "mutton_chops", "beard_no_moustache", "braided_beard",
)

# Women's generation uses its own catalogue, not a nonzero chance of every
# men's cut. Shared geometry keeps existing saved IDs stable. Explicit authored
# hair overrides may represent a real fighter with an uncommon cut.
FEMALE_HAIR_STYLES = (
    13, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27,
    32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 47,
)

# base, form shadow, deep shadow.  The ramps deliberately describe only colour.
SKIN = (
    ("#f7d8c0", "#dbac9c", "#be8b82"), ("#ecc09e", "#c99583", "#a87469"),
    ("#d8a176", "#b07764", "#8e5951"), ("#b87c51", "#8f574c", "#6e3f3b"),
    ("#8f5939", "#6a3d39", "#4e2a2c"), ("#683e28", "#4a2a2c", "#331c21"),
    ("#482a1c", "#311d21", "#211318"),
    ("#f4c9ad", "#d89a87", "#b7796f"), ("#cd8b65", "#a66458", "#7f4642"),
    ("#a86a46", "#7b483f", "#59302f"), ("#77482e", "#55302f", "#3b2025"),
    ("#58331f", "#3d2528", "#291820"),
)
HAIR = (
    ("#1c181e", "#0e0c13"), ("#352620", "#1f1617"), ("#563924", "#37221c"),
    ("#7c542e", "#523423"), ("#aa7c40", "#765030"), ("#d4aa5e", "#987344"),
    ("#b24c26", "#7a3020"), ("#cbc6be", "#949090"),
    ("#17151a", "#09080d"), ("#452d22", "#291a18"), ("#96683c", "#664327"),
    ("#e5d5ad", "#b2a37f"),
)
DYE = {
    "rainbow": ("#e83b50", "#f08a24", "#f2d036", "#4ac062", "#368ee0", "#8b4fd0"),
    "sunset": ("#f03c78", "#f57a2e", "#f7c93a"), "ecuador": ("#f7c92e", "#2e54c8", "#d82b2b"),
    "ice": ("#bfe6f5", "#6cb8e0", "#e8f4fa"), "toxic": ("#9be822", "#24c08a"),
    "bleach": ("#f2e6c8", "#d8c496"), "red": ("#d82a32", "#921822"),
    "blue": ("#2e6ce0", "#1a3e92"), "platinum": ("#f0eee5", "#c7c4ba"),
    "pink": ("#f05a9d", "#c93472"),
}
BACKGROUND = (
    ("#263242", "#171f2c"), ("#1c2e60", "#121c3f"), ("#56161a", "#360d12"),
    ("#1f4e3b", "#123126"), ("#3a1a6d", "#230f47"), ("#4c3a20", "#2f2314"),
    ("#2c3038", "#191c22"), ("#5c242c", "#39151c"), ("#143a4c", "#0c2331"),
    ("#40203c", "#281326"), ("#254b59", "#16323e"), ("#4b3032", "#2e1b20"),
)

# Existing IDs remain at the front of every tuple.  Additions are appended
# only; a saved numeric trait must always retain its visual meaning.
BROW_STYLES = (
    "flat", "arched", "angled_down", "heavy", "thin", "soft_arch", "high_arch",
    "straight_heavy", "broken", "tapered",
)
EYE_SHAPES = (
    "almond", "round", "hooded", "narrow", "downturned", "upturned", "deep_set",
    "wide_lid", "monolid", "sharp_almond",
)
EYE_SPACINGS = ("close", "normal", "wide", "very_close", "slightly_close", "soft_normal", "slightly_wide", "far_wide", "high_set", "low_set")
EYE_SIZES = ("small", "normal", "large", "very_small", "soft_small", "open", "very_large", "tall", "wide", "compact")
NOSE_SHAPES = (
    "straight", "broad", "aquiline", "snub", "broken_left", "broken_right", "roman",
    "button", "long_bridge", "wide_tip",
)
MOUTH_SHAPES = ("neutral", "wide", "thin", "full", "downturned", "bowed", "short", "long", "soft_full", "firm")
JAW_SHAPES = ("narrow", "soft", "balanced", "broad", "square", "tapered", "round", "angular", "wide", "long")
CHIN_SHAPES = ("round", "square", "cleft", "pointed", "short", "broad", "narrow", "projecting", "soft", "long")
CHEEK_SHAPES = ("flat", "subtle", "high", "pronounced", "full", "hollow", "wide", "narrow", "sharp", "soft")
FACE_LENGTHS = ("short", "normal", "long", "very_short", "soft_short", "slightly_long", "very_long", "compact", "oval", "elongated")
EAR_SHAPES = ("small", "medium", "large", "very_large", "very_small", "soft_small", "broad", "tall", "round", "angled")

IDENTITY_TRAITS = (
    "skin", "hair_colour", "hair_style", "facial_hair", "dye", "brow", "eye_shape",
    "eye_spacing", "eye_size", "nose", "mouth", "jaw", "chin", "cheek", "face_length",
    "ear", "head_w", "bg", "neck_width", "shoulder_width", "iris_colour",
    "nose_length", "lip_fullness", "hair_volume", "hair_part", "complexion",
    "feature_offset",
)

IRIS_COLOURS = ("#392820", "#65432d", "#8a6640", "#68764b", "#45667c",
                "#69858b", "#394d45", "#806742", "#525a69", "#463629")

# V3 is append-only. Old palette indices and complete saved vectors retain
# their exact meaning. Shared anatomical presets are available to both genders.
from .expansion import NEW_HAIR_STYLES, NEW_BEARDS, extend_ramps, feature_names, tint

HAIR_STYLES += NEW_HAIR_STYLES
MALE_HAIR_STYLES = tuple(range(98))
FEMALE_HAIR_STYLES += tuple(range(98, 148))
FACIAL_HAIR += tuple(record[0] for record in NEW_BEARDS)
SKIN = extend_ramps(SKIN)
HAIR = extend_ramps(HAIR)
BACKGROUND = extend_ramps(BACKGROUND)
IRIS_COLOURS += tuple(tint(IRIS_COLOURS[i % 10],
                          ((i//10-2)*8+3, (i//10-2)*5-2, (2-i//10)*6+1))
                      for i in range(50))
# Five new undertone variants of each original dye palette; empty dye remains
# the natural generated default. These are authored choices, not country rules.
_DYE_BASE = tuple(DYE.items())
for _name, _colours in _DYE_BASE:
    for _suffix, _offset in (("warm", (18, 5, -12)), ("cool", (-12, 3, 18)),
                             ("pastel", (28, 28, 28)), ("muted", (-22, -22, -22)),
                             ("rose", (15, -18, 8))):
        DYE[f"{_name}_{_suffix}"] = tuple(tint(c, _offset) for c in _colours)

BROW_STYLES += feature_names("brow")
EYE_SHAPES += feature_names("eye_shape")
EYE_SPACINGS += feature_names("eye_spacing")
EYE_SIZES += feature_names("eye_size")
NOSE_SHAPES += feature_names("nose")
MOUTH_SHAPES += feature_names("mouth")
JAW_SHAPES += feature_names("jaw")
CHIN_SHAPES += feature_names("chin")
CHEEK_SHAPES += feature_names("cheek")
FACE_LENGTHS += feature_names("face_length")
EAR_SHAPES += feature_names("ear")
FEATURE_COUNTS = dict(zip(IDENTITY_TRAITS, (
    62, 62, 148, 66, 61, 60, 60, 60, 60, 60, 60, 60, 60, 60, 60,
    60, 150, 62, 60, 60, 60, 60, 60, 60, 60, 60, 60)))


def portrait_gender(fighter):
    """Normalise imported labels without changing fighter or simulation data."""
    value = str(getattr(fighter, "gender", "") or "").strip().casefold()
    return "Female" if value in {"female", "f", "woman", "women"} else "Male" if value in {"male", "m", "man", "men"} else "default"
