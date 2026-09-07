"""Small standard-library comic portrait rasteriser and Tk image cache.

The renderer intentionally uses ordinary Python lists and ``PhotoImage.put``.
It must remain importable in headless simulation tools: Tk is only touched by
``render_portrait`` after a canvas is supplied.
"""

from collections import OrderedDict
from math import sqrt, sin, cos

from .identity import portrait_identity, trait_hash
from .state import portrait_state
from .styles import BACKGROUND, DYE, FACIAL_HAIR, HAIR, HAIR_STYLES, SKIN, IRIS_COLOURS, portrait_gender
from .hair import hair_mask as build_hair_mask
from .expansion import feature_value, control_value, NEW_BEARDS, NEW_COMPLEXIONS

INK = (18, 15, 20)
EYE_WHITE = (242, 238, 231)
# Four portrait sizes are used in the game.  Keep enough warm entries for a
# large event card without keeping every fighter image alive for a full save.
PORTRAIT_CACHE_LIMIT = 192
_PHOTO_CACHE = OrderedDict()


def _rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def _hex(value):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(channel))) for channel in value)


def _mix(left, right, amount):
    return tuple(left[index] * (1 - amount) + right[index] * amount for index in range(3))


def _shade(value, amount):
    return tuple(channel * amount for channel in value)


class _Raster:
    def __init__(self, size, colour):
        self.size = size
        self.pixels = [colour] * (size * size)

    def put(self, x, y, colour):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.pixels[y * self.size + x] = colour

    def ellipse(self, cx, cy, rx, ry, colour, clip=None):
        left, right = max(0, int(cx - rx - 1)), min(self.size - 1, int(cx + rx + 1))
        top, bottom = max(0, int(cy - ry - 1)), min(self.size - 1, int(cy + ry + 1))
        for y in range(top, bottom + 1):
            for x in range(left, right + 1):
                if ((x - cx) / max(rx, 0.1)) ** 2 + ((y - cy) / max(ry, 0.1)) ** 2 <= 1:
                    if clip is None or clip(x, y):
                        self.put(x, y, colour)

    def line(self, x0, y0, x1, y1, width, colour, clip=None):
        steps = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) * 2))
        radius = max(0, int(width / 2))
        for step in range(steps + 1):
            ratio = step / steps
            x, y = round(x0 + (x1 - x0) * ratio), round(y0 + (y1 - y0) * ratio)
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius and (clip is None or clip(x + dx, y + dy)):
                        self.put(x + dx, y + dy, colour)

    def polygon(self, points, colour):
        ys = [point[1] for point in points]
        for y in range(max(0, int(min(ys))), min(self.size - 1, int(max(ys))) + 1):
            hits = []
            for index, first in enumerate(points):
                second = points[(index + 1) % len(points)]
                if (first[1] <= y < second[1]) or (second[1] <= y < first[1]):
                    hits.append(first[0] + (y - first[1]) * (second[0] - first[0]) / (second[1] - first[1]))
            hits.sort()
            for index in range(0, len(hits) - 1, 2):
                for x in range(max(0, round(hits[index])), min(self.size - 1, round(hits[index + 1])) + 1):
                    self.put(x, y, colour)

    def tk_rows(self):
        """Return a Tk bulk-put colour string without external image libraries."""
        rows = []
        for y in range(self.size):
            start = y * self.size
            rows.append("{" + " ".join(_hex(pixel) for pixel in self.pixels[start:start + self.size]) + "}")
        return " ".join(rows)


def _head_profile(size, identity, female=False):
    cx = size / 2
    face_scale = feature_value((.91, 1.0, 1.10, .84, .96, 1.04, 1.18, .88, 1.06, 1.14), identity["face_length"])
    top, bottom = size * 0.17, size * (0.70 + (face_scale - 1) * 0.36)
    head_width = size * 0.205 * (0.85 + feature_value(tuple(range(100)), identity["head_w"]) / 100 * 0.30)
    # The first entries retain the pre-expansion proportions; appended IDs add
    # visibly different but still anatomical construction variants.
    cheek = feature_value((.94, .995, 1.05, 1.105, 1.13, .90, 1.16, .92, 1.14, .98), identity["cheek"])
    jaw = feature_value((.86, .935, 1.01, 1.085, 1.16, .80, .90, 1.12, 1.22, 1.02), identity["jaw"])
    chin = feature_value((.82, .96, 1.10, 1.24, .74, 1.17, .88, 1.12, .92, 1.30), identity["chin"])
    stops = (0.00, 0.08, 0.18, 0.32, 0.46, 0.60, 0.72, 0.84, 0.93, 1.00)
    if female:
        jaw *= .89
        chin *= .87
    widths = (0.06, 0.65, 0.91, 1.00, .99 * cheek, .94 * cheek, .87 * jaw, .74 * jaw, .50 * chin, .20 * chin)

    def half_width(y):
        t = max(0.0, min(1.0, (y - top) / max(1, bottom - top)))
        for index in range(len(stops) - 1):
            if stops[index] <= t <= stops[index + 1]:
                blend = (t - stops[index]) / (stops[index + 1] - stops[index])
                return head_width * (widths[index] * (1 - blend) + widths[index + 1] * blend)
        return head_width * widths[-1]

    def contains(x, y):
        return top <= y <= bottom and abs(x - cx) <= half_width(y)

    return cx, top, bottom, head_width, half_width, contains


def rasterize_portrait(fighter, size=180):
    """Render small UI sizes with area averaging so ink stays continuous."""
    size = max(48, int(size))
    if size > 180:
        return _rasterize_portrait(fighter, size)
    source = _rasterize_portrait(fighter, size * 2)
    result = _Raster(size, INK)
    stride = size * 2
    for y in range(size):
        for x in range(size):
            start = y * 2 * stride + x * 2
            samples = (source.pixels[start], source.pixels[start+1],
                       source.pixels[start+stride], source.pixels[start+stride+1])
            result.pixels[y*size+x] = tuple(round(sum(p[c] for p in samples) / 4) for c in range(3))
    return result


def _rasterize_portrait(fighter, size):
    """Pure high-resolution geometry; no Tk objects or simulation access."""
    size = max(48, int(size))
    identity, state = portrait_identity(fighter), portrait_state(fighter)
    female = portrait_gender(fighter) == "Female"
    skin, skin_shadow, skin_deep = map(_rgb, SKIN[identity["skin"]])
    bg, bg_shadow = map(_rgb, BACKGROUND[identity["bg"]])
    raster = _Raster(size, bg)
    raster.polygon(((0, 0), (size, 0), (size, size * .62), (0, size * .30)), bg_shadow)
    cx, top, bottom, hw, half_width, inside = _head_profile(size, identity, female)
    # Broad shoulders and neck make the silhouette read as a fighter at 90px.
    shoulder = size * ((.40 if female else .46) + control_value(identity["shoulder_width"]) * .012)
    neck = hw * ((.36 if female else .44) + control_value(identity["neck_width"]) * .017)
    raster.ellipse(cx, size * 1.05, shoulder, size * .28, skin)
    raster.ellipse(cx + shoulder * .32, size * 1.05, shoulder * .70, size * .26, skin_shadow)
    raster.polygon(((cx-neck, bottom-size*.06), (cx+neck,bottom-size*.06),
                    (cx+neck*1.12,size*.84), (cx-neck*1.12,size*.84)), skin)
    raster.polygon(((cx+neck*.35,bottom), (cx+neck,bottom-size*.04),
                    (cx+neck*1.12,size*.84), (cx+neck*.30,size*.82)), skin_shadow)
    if female:
        # Athletic singlet gives an unambiguous women's portrait presentation
        # without relying on long hair or exaggerated facial proportions.
        kit = _mix(bg, (45, 60, 81), .50)
        raster.polygon(((cx-shoulder*.88,size), (cx-shoulder*.64,size*.81),
                        (cx-shoulder*.44,size*.80), (cx-shoulder*.32,size*.90),
                        (cx+shoulder*.32,size*.90), (cx+shoulder*.44,size*.80),
                        (cx+shoulder*.64,size*.81), (cx+shoulder*.88,size)), kit)
    # Ears are behind the profile and swell only up to the documented cap.
    eye_y = top + (bottom - top) * (.48 + control_value(identity["feature_offset"]) * .004)
    ear_radius = size * (feature_value((.026, .038, .050, .062, .020, .032, .056, .054, .046, .050), identity["ear"]) + .013 * state["cauli"])
    for direction in (-1, 1):
        raster.ellipse(cx + direction * hw * .98, eye_y + size * .02, ear_radius * .76, ear_radius * 1.16, skin_shadow)
        if state["cauli"] > .25:
            raster.ellipse(cx + direction * hw * 1.00, eye_y + size * .02, ear_radius * .35, ear_radius * .48, skin_deep)
    # The vertical-width profile is deliberately not a stack of ellipses.
    for y in range(int(top), int(bottom) + 1):
        half = half_width(y)
        for x in range(max(0, int(cx - half)), min(size, int(cx + half) + 1)):
            normal = (x - cx) / max(half, 1)
            colour = skin if normal < .64 else skin_shadow
            if normal > .84:
                colour = skin_deep
            t = (y - top) / max(1, bottom - top)
            if .545 < t < .635 and abs(normal) > .65:
                colour = _mix(skin, skin_shadow, .45)
            if t > .90:
                colour = skin_shadow
            raster.put(x, y, colour)
    # Broad, low-contrast planes let the face read as a head instead of a flat
    # mask: a temple shadow, one lit cheek plane and a restrained jaw plane.
    cheek_y = top + (bottom - top) * .59
    raster.polygon(((cx - hw * .82, cheek_y), (cx - hw * .22, cheek_y - size * .018),
                    (cx - hw * .16, cheek_y + size * .070), (cx - hw * .66, cheek_y + size * .095)),
                   _mix(skin, skin_shadow, .16 if female else .26))
    raster.polygon(((cx + hw * .16, cheek_y + size * .006), (cx + hw * .80, cheek_y - size * .016),
                    (cx + hw * .67, cheek_y + size * .096), (cx + hw * .18, cheek_y + size * .072)),
                   _mix(skin, skin_shadow, .32 if female else .55))
    # Ink the actual profile boundary, giving a reliable skull silhouette.
    for y in range(int(top), int(bottom) + 1):
        half = half_width(y)
        for direction in (-1, 1):
            x = round(cx + direction * half)
            raster.line(x, y, x, y + 1, max(1, size // 80), INK)
    hair_base, hair_shadow = map(_rgb, HAIR[identity["hair_colour"]])
    if state["grey"]:
        hair_base, hair_shadow = _mix(hair_base, _rgb(HAIR[7][0]), state["grey"] * .72), _mix(hair_shadow, _rgb(HAIR[7][1]), state["grey"] * .72)
    style_id = identity["hair_style"]
    _, volume, side, line_offset, texture = HAIR_STYLES[style_id]
    hairline = top + (bottom - top) * (.255 + state["recede"] * (.025 if female else .10) + line_offset)
    hair_mask = build_hair_mask(size, identity, cx, top, bottom, hw, eye_y, hairline)
    fringe_base = hairline + size * .055
    dye = identity.get("dye", "")
    dye_colours = tuple(map(_rgb, DYE[dye])) if dye in DYE else ()
    for x, y in hair_mask:
        if not (0 <= x < size and 0 <= y < size):
            continue
        if dye_colours:
            band = min(len(dye_colours) - 1, max(0, int((x - (cx - hw)) / max(1, 2 * hw) * len(dye_colours))))
            colour = dye_colours[band]
        else:
            colour = hair_shadow if x > cx + hw * .45 else hair_base
            if style_id == 1:
                colour = _mix(skin, colour, .38)
            elif style_id in (4,5,41) and abs(x-cx) > hw*.70:
                colour = _mix(skin_shadow, colour, .52)
        raster.put(x, y, colour)
    hair_clip = lambda x, y: (x, y) in hair_mask
    # Texture pass: each class has a different directional cue at thumbnail
    # size, so styles do not collapse into the same dark cap.
    if style_id >= 148:
        # Loose directional strands, not coil dots or straight curtain grain.
        grain = _mix(dye_colours[0], INK, .30) if dye_colours else _mix(hair_base, hair_shadow, .65)
        part = (control_value(identity["hair_part"])-4.5)/4.5
        for strand in range(9):
            x0 = cx-hw*1.13+strand*hw*.28
            points = [(x0 + size*.018*sin(t*8+strand*.45) + part*size*.08*(1-t),
                       top-size*volume+t*size*.72) for t in (i/30 for i in range(31))]
            for a, b in zip(points, points[1:]):
                raster.line(*a, *b, max(1, size//220), grain, hair_clip)
    elif style_id >= 48:
        _expanded_hair_texture(raster, size, cx, top, hw, hairline, volume, texture,
                               style_id, hair_base, hair_shadow, hair_clip)
    elif texture in ("curl", "coil", "puff", "shag", "loc_knot"):
        step_x = max(3, round(hw * (.23 if texture == "coil" else .31)))
        step_y = max(3, round(size * .040))
        for y in range(max(0, int(top - volume * size)), int(hairline + size * .015), step_y):
            offset = (step_x // 2) if ((y // step_y) % 2) else 0
            for x in range(round(cx - hw) + offset, round(cx + hw), step_x):
                radius = max(1, round(size * (.012 if texture == "coil" else .017)))
                raster.ellipse(x, y, radius, radius, hair_shadow, hair_clip)
                if texture == "coil":
                    raster.ellipse(x - radius * .22, y - radius * .18, max(1, radius * .34), max(1, radius * .34), hair_base, hair_clip)
    elif texture == "twist":
        for x in range(round(cx - hw * .84), round(cx + hw * .85), max(3, round(hw * .22))):
            raster.line(x - size * .010, top, x + size * .010, hairline + size * .025,
                        max(1, size // 125), hair_shadow, hair_clip)
    elif texture == "flat" and style_id in (4, 5, 30):
        # Fade/undercut sides need a visible taper boundary.
        for direction in (-1, 1):
            raster.line(cx + direction * hw * .76, top + size * .08,
                        cx + direction * hw * .83, eye_y + size * .015,
                        max(1, size // 145), _mix(hair_shadow, skin_shadow, .58), hair_clip)
    elif style_id in (15, 32, 33, 34, 35, 36, 43, 45, 46, 47):
        # Fine vertical grain breaks the wide blond fringe into hair rather
        # than a single flat colour plate.
        for x in range(round(cx - hw * .72), round(cx + hw * .73), max(2, round(size * .024))):
            raster.line(x, top + size * .015, x - size * .006, fringe_base - size * .018,
                        max(1, size // 180), _mix(hair_base, hair_shadow, .42), hair_clip)
    # Hair ink and braid band separations are drawn over fills, never tinted.
    for x, y in hair_mask:
        if (x - 1, y) not in hair_mask or (x + 1, y) not in hair_mask or (x, y - 1) not in hair_mask:
            raster.put(x, y, INK)
    if texture in ("braid", "dread", "twist", "twin_braids", "braid_tail"):
        step = max(3, round(hw * (.20 if texture == "braid" else .27)))
        for x in range(round(cx - hw), round(cx + hw) + 1, step):
            end_y = bottom + size * .05 if texture == "dread" else (bottom if side == 2 else eye_y + size * .06)
            raster.line(x, top - volume * size, x, end_y, max(1, size // 150), INK, hair_clip)
    # Brows and eyes are positionally distinct enough to survive the small card.
    spacing = feature_value((.38, .46, .54, .32, .42, .47, .50, .60, .44, .49), identity["eye_spacing"])
    eye_scale = feature_value((.78, 1.0, 1.18, .64, .88, 1.08, 1.30, 1.12, 1.15, .72), identity["eye_size"])
    brow_kind = identity["brow"]
    asymmetry = trait_hash(str(getattr(fighter, "fighter_id", "")), "facial_asymmetry", 5) - 2
    for direction in (-1, 1):
        ex = cx + direction * hw * spacing
        brow_height = feature_value((0, .002, .004, .010, -.002, .003, .007, .006, .001, -.004), brow_kind)
        brow_y = eye_y - size * (.044 + brow_height)
        slope = feature_value((0, .003, .006, .002, -.002, .004, .009, -.004, .006, -.006), brow_kind) * size * direction
        brow_width = hw * feature_value((.24, .23, .24, .28, .20, .22, .21, .30, .23, .18), brow_kind)
        brow_ink = max(1, round(size * feature_value((.014, .014, .016, .024, .009, .013, .012, .022, .015, .010), brow_kind)))
        if female:
            brow_ink = max(1, round(brow_ink * .62))
        raster.line(ex - brow_width, brow_y - slope, ex + brow_width, brow_y + slope, brow_ink, hair_shadow, inside)
        eye_w, eye_h = hw * .23 * eye_scale, size * .018 * eye_scale
        eye_kind = identity["eye_shape"]
        eye_h *= feature_value((1.0, 1.18, .65, .55, .82, .86, .68, 1.08, .62, .72), eye_kind)
        eye_w *= feature_value((1.0, .92, 1.0, 1.12, .98, .98, .88, 1.15, 1.10, 1.05), eye_kind)
        eye_y_shift = (feature_value((0, 0, .002, 0, .004, -.004, .002, -.002, .001, 0), eye_kind) * direction
                       + asymmetry * .0015 * direction) * size
        # Socket first, then a narrow sclera, iris and lids.  Keeping the
        # socket wider than the white removes the old sticker-eye effect.
        raster.ellipse(ex, eye_y + eye_y_shift + size * .004, eye_w * 1.14, eye_h * 1.72,
                       _mix(skin, skin_shadow, .52 if female else .78), inside)
        raster.ellipse(ex, eye_y + eye_y_shift, eye_w, eye_h, _mix(EYE_WHITE, skin, .18), inside)
        iris = _rgb(IRIS_COLOURS[identity["iris_colour"]])
        raster.ellipse(ex, eye_y + eye_y_shift, max(1, eye_h * .76), max(1, eye_h * .76), iris, inside)
        raster.ellipse(ex, eye_y + eye_y_shift, max(1, eye_h * .38), max(1, eye_h * .38), INK, inside)
        raster.line(ex - eye_w, eye_y + eye_y_shift - eye_h * .82,
                    ex + eye_w, eye_y + eye_y_shift - eye_h * .82, max(1, size // 120), INK, inside)
        raster.line(ex - eye_w * .75, eye_y + eye_y_shift + eye_h,
                    ex + eye_w * .75, eye_y + eye_y_shift + eye_h, max(1, size // 180), skin_deep, inside)
    # Nose uses shadow planes instead of a boxed outline.
    nose_y, nose_kind = top + (bottom - top) * (.62 + control_value(identity["nose_length"]) * .008), identity["nose"]
    wear_eligible = nose_kind < 4 or (nose_kind >= 10 and (nose_kind-10) % 5 < 2)
    if wear_eligible and state["nose_damage"] > .60 and trait_hash(str(getattr(fighter, "fighter_id", "")), "nose_wear", 4) == 0:
        nose_kind = 4 + trait_hash(str(getattr(fighter, "fighter_id", "")), "career_nose_side", 2)
    nose_width = hw * feature_value((.15, .17, .19, .21, .23, .25, .18, .13, .16, .28), nose_kind)
    if female:
        nose_width *= .88
    shift = (-size * .012 if nose_kind == 4 else size * .012 if nose_kind == 5 else 0)
    raster.polygon(((cx + shift, eye_y + size * .012), (cx + nose_width * .42 + shift, eye_y + size * .030),
                    (cx + nose_width * .50 + shift, nose_y), (cx + shift, nose_y + size * .012)), skin_shadow)
    raster.line(cx + nose_width * .34 + shift, eye_y + size * .005, cx + nose_width * .46 + shift, nose_y, max(1, size // 110), skin_deep, inside)
    raster.ellipse(cx + shift, nose_y, nose_width * .78, size * .019, skin_shadow, inside)
    for direction in (-1, 1):
        raster.ellipse(cx + shift + direction * nose_width * .55, nose_y + size * .005, max(1, nose_width * .18), max(1, size * .007), skin_deep, inside)
    mouth_y = top + (bottom - top) * .795
    mouth_kind = identity["mouth"]
    mouth_width = hw * feature_value((.25, .278, .306, .334, .362, .29, .20, .39, .34, .24), mouth_kind)
    mouth_slope = feature_value((-.004, 0, .004, .008, .012, -.006, -.002, .002, -.001, .006), mouth_kind) * size
    lip_shadow = _mix(skin_deep, (72, 38, 42), .42)
    raster.line(cx - mouth_width, mouth_y + mouth_slope, cx, mouth_y - size * .004,
                max(1, size // 105), lip_shadow, inside)
    raster.line(cx, mouth_y - size * .004, cx + mouth_width, mouth_y - mouth_slope,
                max(1, size // 105), lip_shadow, inside)
    fullness = size * (.005 + control_value(identity["lip_fullness"]) * .0012)
    raster.ellipse(cx, mouth_y + fullness, mouth_width * .68, max(1, fullness),
                   _mix(skin, (156, 74, 72), .30 if female else .18), inside)
    # Facial-hair masks never reach higher than the jaw band, apart from an
    # explicitly separate moustache.
    facial = identity["facial_hair"] if not female else 0
    beard_name = FACIAL_HAIR[facial]
    # Optional authored colour; absence preserves historical pixels exactly.
    # This extra override key is save-compatible and must remain stable.
    beard_base, beard_shadow = hair_base, hair_shadow
    if "beard_colour" in identity:
        beard_base, beard_shadow = map(_rgb, HAIR[identity["beard_colour"]])
        if state["grey"]:
            beard_base = _mix(beard_base, _rgb(HAIR[7][0]), state["grey"] * .72)
            beard_shadow = _mix(beard_shadow, _rgb(HAIR[7][1]), state["grey"] * .72)
    if facial >= 16:
        _expanded_beard(raster, NEW_BEARDS[facial-16], size, cx, top, bottom, hw,
                        half_width, inside, mouth_y, mouth_width, skin, skin_shadow,
                        beard_base, beard_shadow)
    elif beard_name != "none":
        if beard_name in ("stubble_light", "stubble_heavy"):
            beard_base = _mix(skin_shadow, beard_base, .30 if beard_name == "stubble_light" else .58)
            beard_shadow = _mix(skin_deep, beard_shadow, .30 if beard_name == "stubble_light" else .58)
        for y in range(int(top + (bottom - top) * .735), int(bottom) + 1):
            half = half_width(y)
            for x in range(max(0, int(cx - half)), min(size, int(cx + half) + 1)):
                mouth_cut = ((x - cx) / max(1, mouth_width * 1.15)) ** 2 + ((y - mouth_y) / max(1, size * .022)) ** 2 < 1
                distance = abs(x-cx) / max(1, half)
                band = beard_name not in ("moustache", "horseshoe")
                if beard_name in ("goatee", "van_dyke", "soul_patch"):
                    band = distance < (.19 if beard_name == "soul_patch" else .38)
                elif beard_name == "mutton_chops":
                    band = distance > .68
                elif beard_name == "chin_strap":
                    band = distance > .80 or y > bottom-size*.025
                elif beard_name == "short_beard":
                    band = y > top+(bottom-top)*.78 or distance > .75
                if not mouth_cut and band:
                    raster.put(x, y, beard_shadow if x > cx + half * .42 else beard_base)
        if beard_name not in ("beard_no_moustache", "stubble_light", "stubble_heavy", "soul_patch", "goatee"):
            raster.ellipse(cx, mouth_y - size * .024, mouth_width * .82, max(1, size * .010), beard_base, inside)
        if beard_name == "horseshoe":
            for direction in (-1, 1):
                raster.line(cx+direction*mouth_width*.8, mouth_y-size*.024,
                            cx+direction*mouth_width*.85, mouth_y+size*.045,
                            max(1, size//65), beard_base, inside)
        if beard_name == "heavy_beard":
            raster.polygon(((cx-hw*.42,bottom-size*.04), (cx+hw*.42,bottom-size*.04),
                            (cx+hw*.25,bottom+size*.025), (cx-hw*.25,bottom+size*.025)), beard_base)
        if beard_name in ("long_beard", "braided_beard"):
            raster.polygon(((cx-hw*.40,bottom-size*.05), (cx+hw*.40,bottom-size*.05),
                            (cx+hw*.16,bottom+size*.07), (cx-hw*.16,bottom+size*.07)), beard_base)
            if beard_name == "braided_beard":
                for y in range(round(bottom),round(bottom+size*.07),max(2,size//60)):
                    raster.line(cx-hw*.12,y,cx+hw*.12,y+size*.008,1,beard_shadow)
    complexion = identity["complexion"]
    if complexion >= 10:
        _expanded_complexion(raster, NEW_COMPLEXIONS[complexion-10], fighter, size,
                             cx, hw, cheek_y, skin, skin_deep, inside)
    elif complexion:
        # Ten real options: clear; light/dense freckles; left/right mole;
        # low/high cheek freckles; paired moles; nose freckles; temple freckles.
        count = (0, 12, 24, 1, 1, 8, 9, 2, 6, 7)[complexion]
        for dot in range(count):
            fid = str(getattr(fighter, "fighter_id", ""))
            dx = (trait_hash(fid, f"freckle_x_{dot}", 101)-50)*hw*.014
            dy = trait_hash(fid, f"freckle_y_{dot}", 20)*size*.0018
            if complexion in (3, 4, 7):
                dx = hw*.48*(-1 if complexion == 3 or (complexion == 7 and dot == 0) else 1)
                dy = size*.035
            elif complexion == 5:
                dy += size*.035
            elif complexion == 6:
                dy -= size*.018
            elif complexion == 8:
                dx *= .24
            elif complexion == 9:
                dx = (hw*.72+abs(dx)*.15)*(-1 if dot % 2 else 1)
                dy -= size*.025
            x, y = cx+dx, cheek_y+dy
            raster.ellipse(x,y,max(.55,size*.002),max(.55,size*.002),_mix(skin,skin_deep,.45),inside)
    # Sustained career state saturates and adds a small, readable brow scar.
    if state["scar"] > .40 and trait_hash(str(getattr(fighter, "fighter_id", "")), "scar_visible", 3) == 0:
        direction = -1 if trait_hash(str(getattr(fighter, "fighter_id", "")), "scar_side", 2) else 1
        scar_x = cx + direction * hw * .57
        raster.line(scar_x, eye_y - size * .070, scar_x - direction * size * .010, eye_y - size * .022, max(1, size // 110), (235, 200, 190), inside)
    if state["recent_cut"]:
        direction = -1 if trait_hash(str(getattr(fighter, "fighter_id", "")), "cut_side", 2) else 1
        location = state["recent_cut_location"].lower()
        if "brow" in location or "eye" in location:
            start_x, start_y = cx + direction * hw * .48, eye_y - size * .060
            end_x, end_y = start_x - direction * size * .020, eye_y - size * .010
        elif "nose" in location:
            start_x, start_y = cx + direction * size * .006, nose_y - size * .022
            end_x, end_y = cx - direction * size * .010, nose_y + size * .012
        else:
            start_x, start_y = cx + direction * hw * .40, cheek_y + size * .005
            end_x, end_y = start_x - direction * size * .024, cheek_y + size * .047
        raster.line(start_x, start_y, end_x, end_y, max(1, round(size * .006 * state["recent_cut"])),
                    _mix((124, 34, 38), skin_deep, .30), inside)
    if state["swell"]:
        direction = -1 if trait_hash(str(getattr(fighter, "fighter_id", "")), "swell_side", 2) else 1
        raster.ellipse(cx + direction * hw * .47, eye_y + size * .035, hw * .22, size * .045,
                       _mix(skin_shadow, (150, 52, 56), .35 * state["swell"]), inside)
    return raster


def _expanded_hair_texture(raster, size, cx, top, hw, hairline, volume, texture,
                           style_id, base, shadow, clip):
    variant = (style_id-48) % 5
    if texture in ("curl", "coil", "shag"):
        radius = size*(.010 if texture == "coil" else .016)
        step = max(3, round(radius*2.8))
        # Broken curved strands, not filled polka dots. Stagger rows and vary
        # the arc phase deterministically without drawing simulation RNG.
        for row, y in enumerate(range(max(0, round(top-volume*size)), round(hairline+size*.035), step)):
            for col, x in enumerate(range(round(cx-hw)+(row%2)*step//2, round(cx+hw), step)):
                phase = (col*1.3+row*.7+variant*.4)
                points = [(x+radius*cos(phase+i*.45), y+radius*.8*sin(phase+i*.45)) for i in range(7)]
                for a, b in zip(points, points[1:]):
                    raster.line(*a,*b,max(1,size//240),_mix(base,shadow,.70),clip)
    else:
        # Grain follows swept/tied styles; braids receive a woven cross cue
        # under the existing vertical ink separators and multi-colour bands.
        for x in range(round(cx-hw*1.4),round(cx+hw*1.4),max(3,round(size*.024))):
            lean = size*(.025 if variant%2 else -.018) if texture in ("sweep","tail","knot") else 0
            raster.line(x,top-size*volume,x+lean,size*.89,max(1,size//220),_mix(base,shadow,.43),clip)
            if texture in ("braid","dread"):
                for y in range(round(top),round(size*.88),max(3,round(size*.028))):
                    raster.line(x-size*.005,y,x+size*.006,y+size*.009,1,shadow,clip)


def _expanded_beard(raster, record, size, cx, top, bottom, hw, half_width, inside,
                    mouth_y, mouth_width, skin, skin_shadow, hair_base, hair_shadow):
    name, start, width, edge, extension, moustache, droop, opacity, variant = record
    base = _mix(skin, hair_base, opacity)
    shadow = _mix(skin_shadow, hair_shadow, opacity)
    for y in range(round(top+(bottom-top)*max(.735, start)), int(bottom)+1):
        half = half_width(y)
        for x in range(max(0, round(cx-half)), min(size, round(cx+half)+1)):
            distance = abs(x-cx)/max(1, half)
            mouth_cut = ((x-cx)/max(1, mouth_width*1.15))**2 + ((y-mouth_y)/max(1, size*.022))**2 < 1
            if not mouth_cut and edge <= distance <= width:
                raster.put(x, y, shadow if x > cx+half*.42 else base)
    if extension:
        upper = hw*min(.48, width*.58)
        lower = upper*(.22+variant*.09 if "pointed" in name else .60+variant*.06)
        raster.polygon(((cx-upper,bottom-size*.028), (cx+upper,bottom-size*.028),
                        (cx+lower,bottom+size*extension), (cx-lower,bottom+size*extension)), base)
        raster.line(cx+lower*.65,bottom,cx+lower*.4,bottom+size*extension, max(1,size//150), shadow)
    if moustache:
        rx = mouth_width*moustache
        for direction in (-1, 1):
            raster.line(cx+direction*size*.003, mouth_y-size*.025,
                        cx+direction*rx, mouth_y-size*(.022-variant*.0015),
                        max(1, round(size*(.007+variant*.003))), base, inside)
            if droop:
                raster.line(cx+direction*rx,mouth_y-size*.022,
                            cx+direction*rx*.93,mouth_y+size*droop,
                            max(1, round(size*(.008+variant*.002))), base, inside)


def _expanded_complexion(raster, record, fighter, size, cx, hw, cheek_y, skin, deep, inside):
    px, py, sx, sy, count, radius = record
    fid = str(getattr(fighter, "fighter_id", ""))
    for dot in range(count):
        dx = (trait_hash(fid, f"freckle_x_{dot}", 101)-50)/50
        dy = (trait_hash(fid, f"freckle_y_{dot}", 101)-50)/50
        raster.ellipse(cx+hw*(px+dx*sx), cheek_y+size*(py+dy*sy),
                       max(.55,size*radius), max(.55,size*radius), _mix(skin,deep,.45), inside)


def portrait_cache_key(fighter, size):
    state = portrait_state(fighter)
    return (str(getattr(fighter, "fighter_id", "")), portrait_gender(fighter), int(size), tuple(sorted(portrait_identity(fighter).items())), tuple(sorted(state.items())))


def clear_portrait_cache():
    _PHOTO_CACHE.clear()


def portrait_cache_info():
    """Expose cache bounds for lightweight UI/performance regression checks."""
    return {"size": len(_PHOTO_CACHE), "limit": PORTRAIT_CACHE_LIMIT}


def _cache_get(key):
    photo = _PHOTO_CACHE.get(key)
    if photo is not None:
        _PHOTO_CACHE.move_to_end(key)
    return photo


def _cache_store(key, photo):
    _PHOTO_CACHE[key] = photo
    _PHOTO_CACHE.move_to_end(key)
    while len(_PHOTO_CACHE) > PORTRAIT_CACHE_LIMIT:
        _PHOTO_CACHE.popitem(last=False)
    return photo


def render_portrait(canvas, fighter, size=None, ratings_visible=True, **_options):
    """Render a cached image and the durable injury/retirement state seals."""
    import tkinter as tk

    if size is None:
        size = min(int(canvas.cget("width")), int(canvas.cget("height")))
    size = max(48, int(size))
    key = (id(canvas.tk), portrait_cache_key(fighter, size))
    photo = _cache_get(key)
    if photo is None:
        raster = rasterize_portrait(fighter, size)
        photo = tk.PhotoImage(master=canvas, width=size, height=size)
        photo.put(raster.tk_rows(), to=(0, 0, size, size))
        _cache_store(key, photo)
    canvas.delete("all")
    canvas.configure(bg=_hex(_rgb(BACKGROUND[portrait_identity(fighter)["bg"]][0])))
    canvas.create_image(int(canvas.cget("width")) // 2, int(canvas.cget("height")) // 2, image=photo)
    # Canvas items do not keep a Python PhotoImage reference.  The LRU may
    # evict this key while it is still on screen, so retain its current image
    # on the canvas itself until the next portrait replaces it.
    canvas._portrait_photo = photo
    _draw_status_markers(canvas, fighter, size)
    return photo


def _draw_status_markers(canvas, fighter, size):
    marker = max(15, round(size * .155))
    right, top = int(canvas.cget("width")) - max(6, round(size * .065)), max(5, round(size * .065))
    injured = bool(getattr(fighter, "injured", 0) or getattr(fighter, "serious_injury", ""))
    if injured:
        cx, cy = right - marker // 2, top + marker // 2
        canvas.create_oval(cx - marker // 2, cy - marker // 2, cx + marker // 2, cy + marker // 2, fill="#8d2029", outline="#ffd2d7", width=1)
        cross, arm = max(2, marker // 6), max(5, marker // 3)
        canvas.create_rectangle(cx - cross, cy - arm, cx + cross, cy + arm, fill="#ffffff", outline="")
        canvas.create_rectangle(cx - arm, cy - cross, cx + arm, cy + cross, fill="#ffffff", outline="")
    if getattr(fighter, "retired", False):
        cx, cy = right - marker // 2, top + (marker + 4 if injured else 0) + marker // 2
        canvas.create_oval(cx - marker // 2, cy - marker // 2, cx + marker // 2, cy + marker // 2, fill="#315a70", outline="#bfe6f2", width=1)
        canvas.create_text(cx, cy + 1, text="RTD", fill="#ffffff", font=("Impact", max(7, marker - 17)))
    elif getattr(fighter, "retirement_pending", False):
        cx, cy = right - marker // 2, top + (marker + 4 if injured else 0) + marker // 2
        canvas.create_oval(cx - marker // 2, cy - marker // 2, cx + marker // 2, cy + marker // 2, fill="#b88717", outline="#fff0bd", width=1)
        canvas.create_text(cx, cy + 1, text="R", fill="#1b1710", font=("Impact", max(11, marker - 8)))
