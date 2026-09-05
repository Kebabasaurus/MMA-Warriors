"""Small standard-library comic portrait rasteriser and Tk image cache.

The renderer intentionally uses ordinary Python lists and ``PhotoImage.put``.
It must remain importable in headless simulation tools: Tk is only touched by
``render_portrait`` after a canvas is supplied.
"""

from collections import OrderedDict
from math import sqrt

from .identity import portrait_identity, trait_hash
from .state import portrait_state
from .styles import BACKGROUND, DYE, FACIAL_HAIR, HAIR, HAIR_STYLES, SKIN

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


def _head_profile(size, identity):
    cx = size / 2
    face_scale = (.91, 1.0, 1.10, .84, .96, 1.04, 1.18, .88, 1.06, 1.14)[identity["face_length"]]
    top, bottom = size * 0.17, size * (0.69 + (face_scale - 1) * 0.16)
    head_width = size * 0.184 * (0.94 + identity["head_w"] / 100 * 0.16)
    # The first entries retain the pre-expansion proportions; appended IDs add
    # visibly different but still anatomical construction variants.
    cheek = (.94, .995, 1.05, 1.105, 1.13, .90, 1.16, .92, 1.14, .98)[identity["cheek"]]
    jaw = (.86, .935, 1.01, 1.085, 1.16, .80, .90, 1.12, 1.22, 1.02)[identity["jaw"]]
    chin = (.82, .96, 1.10, 1.24, .74, 1.17, .88, 1.12, .92, 1.30)[identity["chin"]]
    stops = (0.00, 0.08, 0.18, 0.32, 0.46, 0.60, 0.72, 0.84, 0.93, 1.00)
    widths = (0.62, 0.86, 0.97, 1.00, .99 * cheek, .94 * cheek, .87 * jaw, .74 * jaw, .56 * chin, .34 * chin)

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
    """Rasterise to an RGB buffer. This pure function is suitable for tests."""
    size = max(48, int(size))
    identity, state = portrait_identity(fighter), portrait_state(fighter)
    skin, skin_shadow, skin_deep = map(_rgb, SKIN[identity["skin"]])
    bg, bg_shadow = map(_rgb, BACKGROUND[identity["bg"]])
    raster = _Raster(size, bg)
    raster.polygon(((0, 0), (size, 0), (size, size * .62), (0, size * .30)), bg_shadow)
    cx, top, bottom, hw, half_width, inside = _head_profile(size, identity)
    # Broad shoulders and neck make the silhouette read as a fighter at 90px.
    raster.ellipse(cx, size * 1.06, size * .59, size * .31, skin_shadow)
    raster.ellipse(cx + size * .18, size * 1.02, size * .55, size * .29, skin_deep)
    raster.ellipse(cx, bottom + size * .055, hw * .60, size * .11, skin_shadow)
    raster.ellipse(cx + hw * .20, bottom + size * .055, hw * .41, size * .11, skin_deep)
    # Ears are behind the profile and swell only up to the documented cap.
    eye_y = top + (bottom - top) * .50
    ear_radius = size * ((.026, .038, .050, .062, .020, .032, .056, .054, .046, .050)[identity["ear"]] + .013 * state["cauli"])
    for direction in (-1, 1):
        raster.ellipse(cx + direction * hw * .98, eye_y + size * .02, ear_radius * .76, ear_radius * 1.16, skin_shadow)
        if state["cauli"] > .25:
            raster.ellipse(cx + direction * hw * 1.00, eye_y + size * .02, ear_radius * .35, ear_radius * .48, skin_deep)
    # The vertical-width profile is deliberately not a stack of ellipses.
    for y in range(int(top), int(bottom) + 1):
        half = half_width(y)
        for x in range(max(0, int(cx - half)), min(size, int(cx + half) + 1)):
            normal = (x - cx) / max(half, 1)
            colour = skin if normal < .50 else skin_shadow
            if normal > .84:
                colour = skin_deep
            t = (y - top) / max(1, bottom - top)
            if .545 < t < .635 and abs(normal) > .42:
                colour = skin_shadow
            if t > .90:
                colour = skin_shadow
            raster.put(x, y, colour)
    # Broad, low-contrast planes let the face read as a head instead of a flat
    # mask: a temple shadow, one lit cheek plane and a restrained jaw plane.
    cheek_y = top + (bottom - top) * .59
    raster.polygon(((cx - hw * .82, cheek_y), (cx - hw * .22, cheek_y - size * .018),
                    (cx - hw * .16, cheek_y + size * .070), (cx - hw * .66, cheek_y + size * .095)),
                   _mix(skin, skin_shadow, .42))
    raster.polygon(((cx + hw * .16, cheek_y + size * .006), (cx + hw * .80, cheek_y - size * .016),
                    (cx + hw * .67, cheek_y + size * .096), (cx + hw * .18, cheek_y + size * .072)),
                   _mix(skin_shadow, skin_deep, .34))
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
    hairline = top + (bottom - top) * (.255 + state["recede"] * .10 + line_offset)
    hair_mask = set()
    if style_id != 0:  # "shaved" is bare scalp, not a zero-height hair cap.
        for y in range(max(0, int(top - volume * size * 2.0)), min(size, int(hairline + size * .025))):
            # A rounded expanded profile avoids the prototype's rectangular temples.
            expansion = 1 + volume * 3.5
            half = half_width(max(top, y + volume * size * 1.15)) * expansion
            if y <= hairline + size * .018:
                for x in range(max(0, int(cx - half)), min(size, int(cx + half) + 1)):
                    hair_mask.add((x, y))
    if style_id != 0 and side:
        reach = eye_y + size * .08 if side == 1 else bottom + size * .04
        for y in range(int(hairline), min(size, int(reach))):
            half = half_width(min(bottom, y))
            for direction in (-1, 1):
                for x in range(int(cx + direction * half * .72), int(cx + direction * half * (1.10 + side * .04)), 1 if direction > 0 else -1):
                    if 0 <= x < size:
                        hair_mask.add((x, y))
    if texture == "knot":
        for y in range(max(0, int(top - size * .07)), int(top)):
            for x in range(int(cx - hw * .28), int(cx + hw * .28)):
                if ((x - cx) / max(1, hw * .28)) ** 2 + ((y - (top - size * .035)) / max(1, size * .04)) ** 2 < 1:
                    hair_mask.add((x, y))
    if texture == "tail":
        # A tail sits behind the head, with a curved, tapered fall rather than
        # an extra rectangle pasted beside the skull.
        tail_side = -1 if trait_hash(str(getattr(fighter, "fighter_id", "")), "tail_side", 2) else 1
        anchor_x = cx + tail_side * hw * .78
        for y in range(int(top + size * .09), min(size, int(bottom + size * .14))):
            progress = (y - (top + size * .09)) / max(1, bottom - top)
            tail_x = anchor_x + tail_side * hw * (.16 + progress * .35)
            radius = max(1, hw * (.15 - progress * .075))
            for x in range(round(tail_x - radius), round(tail_x + radius) + 1):
                if 0 <= x < size:
                    hair_mask.add((x, y))
    if texture == "spike":
        hair_mask = {(x, y) for x, y in hair_mask if abs(x - cx) < hw * .42 or y < hairline - size * .01}
    if texture == "dread":
        for direction in (-3, -2, -1, 1, 2, 3):
            x = cx + direction * hw * .27
            for y in range(int(hairline), min(size, int(bottom + size * .08))):
                for dx in range(-max(1, size // 90), max(2, size // 90 + 1)):
                    hair_mask.add((round(x + dx), y))
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
        raster.put(x, y, colour)
    hair_clip = lambda x, y: (x, y) in hair_mask
    # Texture pass: each class has a different directional cue at thumbnail
    # size, so styles do not collapse into the same dark cap.
    if texture in ("curl", "coil"):
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
    # Hair ink and braid band separations are drawn over fills, never tinted.
    for x, y in hair_mask:
        if (x - 1, y) not in hair_mask or (x + 1, y) not in hair_mask or (x, y - 1) not in hair_mask:
            raster.put(x, y, INK)
    if texture in ("braid", "dread", "twist"):
        step = max(3, round(hw * (.20 if texture == "braid" else .27)))
        for x in range(round(cx - hw), round(cx + hw) + 1, step):
            end_y = bottom + size * .05 if texture == "dread" else (bottom if side == 2 else eye_y + size * .06)
            raster.line(x, top - volume * size, x, end_y, max(1, size // 150), INK, hair_clip)
    # Brows and eyes are positionally distinct enough to survive the small card.
    spacing = (.38, .46, .54, .32, .42, .47, .50, .60, .44, .49)[identity["eye_spacing"]]
    eye_scale = (.78, 1.0, 1.18, .64, .88, 1.08, 1.30, 1.12, 1.15, .72)[identity["eye_size"]]
    brow_kind = identity["brow"]
    asymmetry = trait_hash(str(getattr(fighter, "fighter_id", "")), "facial_asymmetry", 5) - 2
    for direction in (-1, 1):
        ex = cx + direction * hw * spacing
        brow_height = (0, .002, .004, .010, -.002, .003, .007, .006, .001, -.004)[brow_kind]
        brow_y = eye_y - size * (.044 + brow_height)
        slope = (0, .003, .006, .002, -.002, .004, .009, -.004, .006, -.006)[brow_kind] * size * direction
        brow_width = hw * (.24, .23, .24, .28, .20, .22, .21, .30, .23, .18)[brow_kind]
        brow_ink = max(1, round(size * (.014, .014, .016, .024, .009, .013, .012, .022, .015, .010)[brow_kind]))
        raster.line(ex - brow_width, brow_y - slope, ex + brow_width, brow_y + slope, brow_ink, hair_shadow, inside)
        eye_w, eye_h = hw * .23 * eye_scale, size * .018 * eye_scale
        eye_kind = identity["eye_shape"]
        eye_h *= (1.0, 1.18, .65, .55, .82, .86, .68, 1.08, .62, .72)[eye_kind]
        eye_w *= (1.0, .92, 1.0, 1.12, .98, .98, .88, 1.15, 1.10, 1.05)[eye_kind]
        eye_y_shift = ((0, 0, .002, 0, .004, -.004, .002, -.002, .001, 0)[eye_kind] * direction
                       + asymmetry * .0015 * direction) * size
        # Socket first, then a narrow sclera, iris and lids.  Keeping the
        # socket wider than the white removes the old sticker-eye effect.
        raster.ellipse(ex, eye_y + eye_y_shift + size * .004, eye_w * 1.14, eye_h * 1.72,
                       _mix(skin_shadow, skin_deep, .48), inside)
        raster.ellipse(ex, eye_y + eye_y_shift, eye_w, eye_h, _mix(EYE_WHITE, skin, .18), inside)
        iris = _mix(hair_shadow, (83, 62, 45), .36)
        raster.ellipse(ex, eye_y + eye_y_shift, max(1, eye_h * .76), max(1, eye_h * .76), iris, inside)
        raster.ellipse(ex, eye_y + eye_y_shift, max(1, eye_h * .38), max(1, eye_h * .38), INK, inside)
        raster.line(ex - eye_w, eye_y + eye_y_shift - eye_h * .82,
                    ex + eye_w, eye_y + eye_y_shift - eye_h * .82, max(1, size // 120), INK, inside)
        raster.line(ex - eye_w * .75, eye_y + eye_y_shift + eye_h,
                    ex + eye_w * .75, eye_y + eye_y_shift + eye_h, max(1, size // 180), skin_deep, inside)
    # Nose uses shadow planes instead of a boxed outline.
    nose_y, nose_kind = top + (bottom - top) * .655, identity["nose"]
    if nose_kind < 4 and state["nose_damage"] > .60:
        nose_kind = 4 + trait_hash(str(getattr(fighter, "fighter_id", "")), "career_nose_side", 2)
    nose_width = hw * (.15, .17, .19, .21, .23, .25, .18, .13, .16, .28)[nose_kind]
    shift = (-size * .012 if nose_kind == 4 else size * .012 if nose_kind == 5 else 0)
    raster.polygon(((cx + shift, eye_y + size * .012), (cx + nose_width * .42 + shift, eye_y + size * .030),
                    (cx + nose_width * .50 + shift, nose_y), (cx + shift, nose_y + size * .012)), skin_shadow)
    raster.line(cx + nose_width * .34 + shift, eye_y + size * .005, cx + nose_width * .46 + shift, nose_y, max(1, size // 110), skin_deep, inside)
    raster.ellipse(cx + shift, nose_y, nose_width * .78, size * .019, skin_shadow, inside)
    for direction in (-1, 1):
        raster.ellipse(cx + shift + direction * nose_width * .55, nose_y + size * .005, max(1, nose_width * .18), max(1, size * .007), skin_deep, inside)
    mouth_y = top + (bottom - top) * .795
    mouth_kind = identity["mouth"]
    mouth_width = hw * (.25, .278, .306, .334, .362, .29, .20, .39, .34, .24)[mouth_kind]
    mouth_slope = (-.004, 0, .004, .008, .012, -.006, -.002, .002, -.001, .006)[mouth_kind] * size
    lip_shadow = _mix(skin_deep, (72, 38, 42), .42)
    raster.line(cx - mouth_width, mouth_y + mouth_slope, cx, mouth_y - size * .004,
                max(1, size // 105), lip_shadow, inside)
    raster.line(cx, mouth_y - size * .004, cx + mouth_width, mouth_y - mouth_slope,
                max(1, size // 105), lip_shadow, inside)
    raster.ellipse(cx, mouth_y + size * .012, mouth_width * .60, max(1, size * .008),
                   _mix(skin, (194, 93, 98), .22), inside)
    # Facial-hair masks never reach higher than the jaw band, apart from an
    # explicitly separate moustache.
    facial = identity["facial_hair"] if str(getattr(fighter, "gender", "Male")) != "Female" else 0
    beard_name = FACIAL_HAIR[facial]
    beard_base, beard_shadow = hair_base, hair_shadow
    if beard_name != "none":
        if beard_name in ("stubble_light", "stubble_heavy"):
            beard_base = _mix(skin_shadow, hair_base, .30 if beard_name == "stubble_light" else .58)
        for y in range(int(top + (bottom - top) * .735), int(bottom) + 1):
            half = half_width(y)
            for x in range(max(0, int(cx - half)), min(size, int(cx + half) + 1)):
                mouth_cut = ((x - cx) / max(1, mouth_width * 1.15)) ** 2 + ((y - mouth_y) / max(1, size * .022)) ** 2 < 1
                if not mouth_cut and (beard_name not in ("goatee", "soul_patch") or abs(x - cx) < hw * .35):
                    raster.put(x, y, beard_shadow if x > cx + half * .42 else beard_base)
        if beard_name not in ("beard_no_moustache", "stubble_light", "stubble_heavy", "soul_patch"):
            raster.ellipse(cx, mouth_y - size * .024, mouth_width * .82, max(1, size * .010), beard_base, inside)
    # Sustained career state saturates and adds a small, readable brow scar.
    if state["scar"] > .40:
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


def portrait_cache_key(fighter, size):
    state = portrait_state(fighter)
    return (str(getattr(fighter, "fighter_id", "")), int(size), tuple(sorted(portrait_identity(fighter).items())), tuple(sorted(state.items())))


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
    key = portrait_cache_key(fighter, size)
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
