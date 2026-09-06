"""Append-only v3 art controls. No game state, random stream or dependencies.

The fifty intermediate anatomical presets are bounded within the original art
ranges. They are not fifty different anatomical types: at small sizes neighbouring
presets can look alike. Hair and beard families have separate silhouette controls.
Never reorder these records or change their interpretation after release.
"""

from math import lcm


def feature_value(values, index):
    """Retain every old value exactly; append fifty bounded intermediate steps."""
    if index < len(values):
        return values[index]
    step = index - len(values)
    if not 0 <= step < 50:
        raise ValueError("Unknown portrait feature ID")
    return min(values) + (max(values) - min(values)) * (step + .5) / 50


def control_value(index):
    return feature_value(tuple(range(10)), index)


def feature_names(prefix):
    return tuple(f"{prefix}_intermediate_{i:02d}" for i in range(50))


def tint(hex_colour, offset):
    channels = tuple(int(hex_colour[i:i+2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(max(0, min(255, c+d)) for c, d in zip(channels, offset))


# Twelve original families; warm/cool/olive/rosy undertones do not change the
# country prior's family mass. Indices 12..61 correspond to these parent IDs.
PALETTE_PARENTS = tuple(i % 12 for i in range(50))
_UNDERTONES = ((8, 2, -6), (-8, -1, 6), (2, 6, -7), (5, -6, 1), (-5, 3, 8))


def extend_ramps(ramps):
    return ramps + tuple(tuple(tint(colour, _UNDERTONES[i // 12]) for colour in ramps[parent])
                         for i, parent in enumerate(PALETTE_PARENTS))


def expand_distribution(weights):
    """Split each old family's probability equally over it and its new shades."""
    parents = tuple(range(12)) + PALETTE_PARENTS
    sizes = tuple(parents.count(i) for i in range(12))
    scale = lcm(*sizes)
    return tuple(range(62)), tuple(weights[p] * (scale // sizes[p]) for p in parents)


# (family, texture, volume, side length relative to chin, width, fringe, tail)
# Five variants per family vary crown, fringe, side taper and part together.
MALE_HAIR_FAMILIES = (
    ("temple_fade", "flat", .012, -.20, .99, -.020, ""),
    ("textured_crop", "shag", .023, -.22, 1.03, .025, ""),
    ("swept_quiff", "sweep", .047, -.21, 1.06, .005, ""),
    ("coiled_taper", "coil", .036, -.18, 1.04, -.005, ""),
    ("curled_crown", "curl", .049, -.12, 1.10, .012, ""),
    ("separated_locs", "dread", .034, .04, 1.12, -.016, "locks"),
    ("row_braids", "braid", .018, -.19, 1.02, -.014, ""),
    ("layered_shag", "shag", .037, .045, 1.13, .034, ""),
    ("ridge_hawk", "spike", .067, -.22, .50, -.015, ""),
    ("tied_back", "tail", .026, -.17, 1.01, -.016, "single"),
)
FEMALE_HAIR_FAMILIES = (
    ("sculpted_bob", "bob", .029, .005, 1.16, .036, ""),
    ("layered_lob", "shag", .039, .10, 1.20, .025, ""),
    ("swept_pixie", "sweep", .033, -.19, 1.04, .022, ""),
    ("loose_waves", "curl", .042, .17, 1.22, -.015, ""),
    ("curl_halo", "curl", .062, .015, 1.26, .010, ""),
    ("paired_braids", "braid", .023, -.18, 1.02, -.012, "double"),
    ("long_locs", "dread", .043, .13, 1.20, -.010, "locks"),
    ("gathered_bun", "knot", .025, -.21, 1.02, -.018, "bun"),
    ("swept_ponytail", "tail", .027, -.19, 1.06, .008, "single"),
    ("paired_puffs", "coil", .036, -.19, 1.04, -.009, "puffs"),
)
VARIANT_NAMES = ("compact", "offset", "rounded", "high", "flowing")


def _hair_records(families):
    return tuple((f"{family}_{VARIANT_NAMES[v]}", texture, volume + v*.006,
                  reach + v*.012, width + v*.018, fringe + (v-2)*.008,
                  tail, v) for family, texture, volume, reach, width, fringe, tail in families
                 for v in range(5))


NEW_HAIR = _hair_records(MALE_HAIR_FAMILIES) + _hair_records(FEMALE_HAIR_FAMILIES)
NEW_HAIR_STYLES = tuple((name, volume, 2 if reach >= 0 else 0, -.01, texture)
                       for name, texture, volume, reach, width, fringe, tail, v in NEW_HAIR)

# (name, lower jaw start, centre width, edge-only threshold, chin extension,
# moustache width, moustache droop, fill opacity)
BEARD_FAMILIES = (
    ("graduated_stubble", .75, 1., 0., 0., 0., 0., .32),
    ("boxed_beard", .77, 1., 0., .025, .85, .0, 1.),
    ("pointed_beard", .80, .62, 0., .065, .70, .01, 1.),
    ("jawline_beard", .75, 1., .72, .0, .0, .0, 1.),
    ("chin_goatee", .82, .38, 0., .035, .0, .0, 1.),
    ("anchor_beard", .84, .52, 0., .018, .64, .0, 1.),
    ("side_whiskers", .74, 1., .66, .0, .0, .0, 1.),
    ("chevron_moustache", 1., 0., 0., .0, .72, .0, 1.),
    ("drooping_moustache", 1., 0., 0., .0, .83, .034, 1.),
    ("chin_curtain", .80, 1., 0., .046, .0, .0, 1.),
)
NEW_BEARDS = tuple((f"{name}_{VARIANT_NAMES[v]}", start + v*.010,
                    width - v*.035, edge + v*.022 if edge else 0.,
                    length + v*.009 if length else 0., moustache + v*.075 if moustache else 0.,
                    droop + v*.010 if droop else 0., min(1., opacity + v*.12), v)
                   for name, start, width, edge, length, moustache, droop, opacity in BEARD_FAMILIES
                   for v in range(5))

# Cosmetic freckle/mole patterns: centre x/y, spread x/y, count, radius.
COMPLEXION_FAMILIES = (
    (-.48, .01, .12, .026, 1, .003), (.48, .01, .12, .026, 1, .003),
    (0., .01, .65, .025, 10, .002), (0., .045, .60, .022, 8, .002),
    (0., -.015, .55, .014, 9, .002), (0., .01, .20, .018, 6, .002),
    (-.65, -.01, .12, .035, 4, .002), (.65, -.01, .12, .035, 4, .002),
    (-.40, .05, .25, .02, 3, .003), (.40, .05, .25, .02, 3, .003),
)
NEW_COMPLEXIONS = tuple((x+(v-2)*.018, y+v*.003, sx, sy, count+v*2, radius+v*.0002)
                       for x, y, sx, sy, count, radius in COMPLEXION_FAMILIES for v in range(5))
