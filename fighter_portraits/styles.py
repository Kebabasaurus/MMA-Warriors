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
)

FACIAL_HAIR = (
    "none", "stubble_light", "stubble_heavy", "moustache", "horseshoe", "goatee",
    "van_dyke", "soul_patch", "chin_strap", "short_beard", "full_beard",
    "heavy_beard", "long_beard", "mutton_chops", "beard_no_moustache", "braided_beard",
)

# base, form shadow, deep shadow.  The ramps deliberately describe only colour.
SKIN = (
    ("#f7d8c0", "#dbac9c", "#be8b82"), ("#ecc09e", "#c99583", "#a87469"),
    ("#d8a176", "#b07764", "#8e5951"), ("#b87c51", "#8f574c", "#6e3f3b"),
    ("#8f5939", "#6a3d39", "#4e2a2c"), ("#683e28", "#4a2a2c", "#331c21"),
    ("#482a1c", "#311d21", "#211318"),
)
HAIR = (
    ("#1c181e", "#0e0c13"), ("#352620", "#1f1617"), ("#563924", "#37221c"),
    ("#7c542e", "#523423"), ("#aa7c40", "#765030"), ("#d4aa5e", "#987344"),
    ("#b24c26", "#7a3020"), ("#cbc6be", "#949090"),
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

IDENTITY_TRAITS = (
    "skin", "hair_colour", "hair_style", "facial_hair", "dye", "brow", "eye_shape",
    "eye_spacing", "eye_size", "nose", "mouth", "jaw", "chin", "cheek", "face_length",
    "ear", "head_w", "bg",
)
