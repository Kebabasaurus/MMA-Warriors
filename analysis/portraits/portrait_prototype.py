"""Prototype stylised fighter portrait rasteriser.

Dev tool only: uses numpy for speed. Proves the identity-vector -> layered
portrait pipeline and produces a contact sheet so the art direction can be
judged before any assets are commissioned.
"""
import hashlib
import json
import struct
import zlib
from pathlib import Path

import numpy as np

S = 200  # render size


# ---------------------------------------------------------------- hashing
def h(fid, trait, mod):
    """Independent stable draw per trait so adding traits never reshuffles."""
    digest = hashlib.blake2b(f"{fid}|{trait}".encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % mod


def hf(fid, trait):
    return h(fid, trait, 100000) / 100000.0


# ---------------------------------------------------------------- palettes
# Skin ramp, light -> deep. Deliberately broad; every region draws a wide range.
SKIN = [
    (0xF3, 0xD5, 0xC0), (0xE9, 0xC3, 0xA6), (0xDA, 0xAB, 0x88), (0xC5, 0x90, 0x6A),
    (0xAA, 0x76, 0x53), (0x8B, 0x5C, 0x3E), (0x6C, 0x45, 0x2D), (0x4F, 0x32, 0x20),
]
HAIR = [
    (0x14, 0x10, 0x0E), (0x2C, 0x20, 0x1A), (0x48, 0x32, 0x23), (0x69, 0x48, 0x2D),
    (0x8B, 0x69, 0x41), (0xB4, 0x8D, 0x54), (0xD7, 0xBF, 0x89), (0xA7, 0x4A, 0x27),
]
BG = [
    (0x1F, 0x29, 0x37), (0x17, 0x25, 0x54), (0x3B, 0x0A, 0x0A), (0x1B, 0x43, 0x32),
    (0x2E, 0x10, 0x65), (0x3F, 0x2F, 0x1D), (0x11, 0x18, 0x27), (0x4A, 0x1D, 0x1F),
    (0x0F, 0x17, 0x2A), (0x28, 0x30, 0x20), (0x30, 0x1A, 0x2A), (0x1A, 0x2E, 0x3A),
]

# Region-conditioned appearance. Each entry is a weighting over the SKIN and
# HAIR ramps. Every distribution is intentionally WIDE - no region maps to a
# single look, and these are anatomical ranges only.
REGION_APPEARANCE = {
    "USA":          {"skin": [8, 10, 11, 9, 7, 7, 8, 6], "hair": [16, 14, 12, 9, 7, 5, 3, 2]},
    "Canada":       {"skin": [11, 12, 11, 8, 5, 4, 4, 3], "hair": [15, 14, 13, 10, 8, 6, 4, 2]},
    "Brazil":       {"skin": [7, 10, 13, 13, 11, 9, 7, 5], "hair": [20, 17, 12, 7, 4, 2, 1, 1]},
    "Mexico":       {"skin": [5, 9, 14, 15, 12, 8, 5, 3], "hair": [24, 18, 10, 4, 2, 1, 1, 1]},
    "UK":           {"skin": [13, 13, 11, 7, 5, 5, 5, 4], "hair": [13, 13, 13, 12, 10, 7, 5, 4]},
    "Europe":       {"skin": [13, 13, 12, 8, 5, 4, 3, 2], "hair": [14, 14, 13, 11, 9, 7, 5, 2]},
    "Russia":       {"skin": [14, 14, 12, 7, 4, 3, 2, 1], "hair": [15, 15, 14, 11, 8, 6, 4, 2]},
    "Japan":        {"skin": [9, 14, 15, 10, 5, 3, 2, 1], "hair": [34, 20, 7, 3, 1, 1, 1, 1]},
    "South Korea":  {"skin": [10, 15, 15, 9, 4, 2, 2, 1], "hair": [35, 20, 6, 2, 1, 1, 1, 1]},
    "Australia":    {"skin": [12, 13, 11, 8, 6, 5, 4, 3], "hair": [14, 14, 13, 11, 9, 7, 5, 3]},
    "Asia":         {"skin": [7, 11, 14, 13, 9, 6, 4, 3], "hair": [30, 19, 8, 4, 2, 1, 1, 1]},
    "Middle East":  {"skin": [6, 10, 14, 14, 11, 8, 5, 3], "hair": [28, 19, 10, 5, 2, 1, 1, 1]},
    "Africa":       {"skin": [1, 2, 4, 7, 12, 17, 21, 19], "hair": [40, 22, 8, 3, 1, 1, 1, 1]},
}
DEFAULT_APPEARANCE = {"skin": [1] * 8, "hair": [1] * 8}


NATIONALITY_GROUP = {
    "american": "USA", "canadian": "Canada", "brazilian": "Brazil", "mexican": "Mexico",
    "british": "UK", "english": "UK", "scottish": "UK", "welsh": "UK", "irish": "Europe",
    "european": "Europe", "french": "Europe", "german": "Europe", "polish": "Europe",
    "spanish": "Europe", "dutch": "Europe", "italian": "Europe", "swedish": "Europe",
    "russian": "Russia", "russia": "Russia", "ukrainian": "Russia", "georgian": "Russia",
    "dagestani": "Russia", "kazakh": "Asia", "japanese": "Japan", "south korean": "South Korea",
    "korean": "South Korea", "chinese": "Asia", "asian": "Asia", "thai": "Asia",
    "filipino": "Asia", "indian": "Asia", "australian": "Australia", "new zealander": "Australia",
    "nigerian": "Africa", "cameroonian": "Africa", "south african": "Africa", "african": "Africa",
    "ghanaian": "Africa", "congolese": "Africa", "angolan": "Africa",
    "iranian": "Middle East", "iraqi": "Middle East", "jordanian": "Middle East",
    "emirati": "Middle East", "turkish": "Middle East", "moroccan": "Middle East",
    "egyptian": "Middle East", "tunisian": "Middle East", "algerian": "Middle East",
    "argentine": "Brazil", "chilean": "Brazil", "ecuadorian": "Brazil", "peruvian": "Brazil",
}
COUNTRY_GROUP = {
    "nigeria": "Africa", "cameroon": "Africa", "south africa": "Africa", "ghana": "Africa",
    "congo": "Africa", "angola": "Africa", "senegal": "Africa", "kenya": "Africa",
    "japan": "Japan", "south korea": "South Korea", "china": "Asia", "thailand": "Asia",
    "philippines": "Asia", "india": "Asia", "brazil": "Brazil", "mexico": "Mexico",
    "united states": "USA", "canada": "Canada", "australia": "Australia",
    "russia": "Russia", "ukraine": "Russia", "georgia": "Russia", "kazakhstan": "Asia",
    "iran": "Middle East", "turkiye": "Middle East", "turkey": "Middle East",
    "morocco": "Middle East", "egypt": "Middle East",
}


def appearance_profile(fighter):
    """birth_country is most specific, then nationality, then broad region."""
    country = str(fighter.get("birth_country") or "").strip().casefold()
    if country in COUNTRY_GROUP:
        return REGION_APPEARANCE[COUNTRY_GROUP[country]]
    nat = str(fighter.get("nationality") or "").strip().casefold()
    if nat in NATIONALITY_GROUP:
        return REGION_APPEARANCE[NATIONALITY_GROUP[nat]]
    region = str(fighter.get("region") or fighter.get("birth_region") or "").strip()
    return REGION_APPEARANCE.get(region, DEFAULT_APPEARANCE)


def weighted(weights, roll):
    total = sum(weights)
    cursor = 0
    target = roll * total
    for index, weight in enumerate(weights):
        cursor += weight
        if target < cursor:
            return index
    return len(weights) - 1


# ---------------------------------------------------------------- identity
def identity_vector(fighter):
    fid = fighter["fighter_id"]
    profile = appearance_profile(fighter)
    female = fighter.get("gender", "Male") == "Female"
    return {
        "skin": weighted(profile["skin"], hf(fid, "skin")),
        "hair_colour": weighted(profile["hair"], hf(fid, "hair_colour")),
        "hair_style": h(fid, "hair_style", 8 if not female else 6),
        "jaw": h(fid, "jaw", 5),
        "head_w": 0.86 + h(fid, "head_w", 100) / 100 * 0.28,
        "brow": h(fid, "brow", 4),
        "eye": h(fid, "eye", 4),
        "nose": h(fid, "nose", 4),
        "mouth": h(fid, "mouth", 3),
        "ear": h(fid, "ear", 3),
        "beard": 0 if female else h(fid, "beard", 6),
        "bg": h(fid, "bg", len(BG)),
        "female": female,
    }


def state_layers(fighter):
    """Recomputed every draw - never stored."""
    age = int(fighter.get("age", 27))
    fights = int(fighter.get("record_w", 0)) + int(fighter.get("record_l", 0))
    return {
        "grey": max(0.0, min(1.0, (age - 34) / 18.0)),
        "recede": max(0.0, min(1.0, (age - 27) / 18.0)),
        "cauli": max(0.0, min(1.0, fights / 28.0)),
        "scar": max(0.0, min(1.0, fights / 34.0)),
    }


# ---------------------------------------------------------------- raster helpers
YY, XX = np.mgrid[0:S, 0:S]
PX = XX / S
PY = YY / S


def ellipse(cx, cy, rx, ry, soft=0.006):
    d = np.sqrt(((PX - cx) / rx) ** 2 + ((PY - cy) / ry) ** 2)
    return np.clip((1.0 - d) / soft, 0, 1)


def blend(dst, mask, colour):
    m = mask[..., None]
    return dst * (1 - m) + np.array(colour, dtype=np.float64) * m


def shade(colour, factor):
    return tuple(max(0, min(255, c * factor)) for c in colour)


# ---------------------------------------------------------------- renderer
def render(fighter):
    v = identity_vector(fighter)
    st = state_layers(fighter)
    skin = SKIN[v["skin"]]
    hair_base = HAIR[v["hair_colour"]]
    grey_mix = st["grey"] * 0.55
    hair = tuple(hair_base[i] * (1 - grey_mix) + 0xC8 * grey_mix for i in range(3))

    img = np.zeros((S, S, 3), dtype=np.float64)
    bg = BG[v["bg"]]
    img[:] = bg
    # vignette so the head reads against the panel
    img = blend(img, ellipse(0.5, 0.62, 0.62, 0.66, 0.5) * 0.30, shade(bg, 1.7))

    hw = 0.175 * v["head_w"]
    cy = 0.44

    # shoulders / neck
    img = blend(img, ellipse(0.5, 1.22, 0.52, 0.42, 0.02), shade(skin, 0.55))
    img = blend(img, ellipse(0.5, 0.80, 0.085, 0.13, 0.02), shade(skin, 0.82))

    # ears (cauliflower thickens and reddens them)
    ear_r = 0.022 + 0.009 * st["cauli"] + v["ear"] * 0.003
    ear_col = tuple(skin[i] * (1 - 0.35 * st["cauli"]) + (0xB0, 0x6A, 0x60)[i] * (0.35 * st["cauli"]) for i in range(3))
    img = blend(img, ellipse(0.5 - hw + 0.004, cy + 0.045, ear_r, ear_r * 1.35, 0.02), ear_col)
    img = blend(img, ellipse(0.5 + hw - 0.004, cy + 0.045, ear_r, ear_r * 1.35, 0.02), ear_col)

    # skull + jaw (jaw index widens/squares the lower face)
    jaw_w = hw * (0.80 + v["jaw"] * 0.06)
    img = blend(img, ellipse(0.5, cy, hw, 0.215, 0.012), skin)
    img = blend(img, ellipse(0.5, cy + 0.115, jaw_w, 0.135, 0.014), skin)
    # cheek/jaw shadow gives the flat fill some form
    img = blend(img, ellipse(0.5, cy + 0.20, jaw_w * 0.92, 0.075, 0.05) * 0.30, shade(skin, 0.80))
    img = blend(img, ellipse(0.5, cy - 0.13, hw * 0.94, 0.10, 0.06) * 0.18, shade(skin, 1.10))

    # hair: an opaque cap over the skull, cut by a hairline curve
    style = v["hair_style"]
    if style != 0:  # 0 = shaved
        recede = st["recede"]
        # hairline sits lower for thick styles, higher as it recedes
        line = cy - 0.150 + recede * 0.055 + (0.012 if style in (3, 6) else 0.0)
        skull = ellipse(0.5, cy - 0.012, hw * 1.045, 0.222, 0.010)
        cap = skull * (PY < line + 0.30)
        # carve the face out from the hairline down, with a curved edge
        face_cut = ellipse(0.5, line + 0.235, hw * 1.02, 0.235, 0.012)
        cap = np.clip(cap - face_cut, 0, 1)
        if style in (3, 6):  # longer: sides come down past the ears
            sides = ellipse(0.5, cy + 0.055, hw * 1.10, 0.215, 0.014)
            sides = sides * (PY > line + 0.02) * (np.abs(PX - 0.5) > hw * 0.72)
            cap = np.clip(cap + sides, 0, 1)
        if style == 5:  # volume on top
            cap = np.clip(cap + ellipse(0.5, cy - 0.205, hw * 0.62, 0.055, 0.014), 0, 1)
        if style == 7:  # widow's peak
            peak = ellipse(0.5, line + 0.030, hw * 0.30, 0.055, 0.02)
            cap = np.clip(cap + peak * skull, 0, 1)
        if recede > 0.25:  # temples recede first
            temples = ((np.abs(PX - 0.5) > hw * (0.76 - 0.30 * recede))
                       & (PY < line + 0.075 + 0.045 * recede))
            cap = cap * ~temples
        img = blend(img, cap, hair)
        # a touch of sheen so it is not a flat slab
        img = blend(img, ellipse(0.5 - hw * 0.35, cy - 0.135, hw * 0.30, 0.045, 0.06) * cap * 0.22,
                    shade(hair, 1.55))

    # brows
    bw = hw * (0.42 + v["brow"] * 0.04)
    by = cy - 0.045 - v["brow"] * 0.004
    for sx in (-1, 1):
        img = blend(img, ellipse(0.5 + sx * hw * 0.42, by, bw * 0.55, 0.016 + v["brow"] * 0.002, 0.02),
                    shade(hair, 0.85))

    # eyes
    ew = hw * 0.235
    ey = cy + 0.012
    for sx in (-1, 1):
        img = blend(img, ellipse(0.5 + sx * hw * 0.42, ey, ew, 0.020 + v["eye"] * 0.002, 0.02), (0xEE, 0xEA, 0xE4))
        img = blend(img, ellipse(0.5 + sx * hw * 0.42, ey, ew * 0.46, 0.016, 0.02), shade(hair_base, 0.85))
        img = blend(img, ellipse(0.5 + sx * hw * 0.42 - 0.006, ey - 0.005, ew * 0.16, 0.006, 0.04), (0xFF, 0xFF, 0xFF))
        # upper lid
        img = blend(img, ellipse(0.5 + sx * hw * 0.42, ey - 0.026, ew * 1.10, 0.020, 0.03) * 0.95, skin)

    # nose
    nl = 0.055 + v["nose"] * 0.010
    img = blend(img, ellipse(0.5, cy + nl, hw * (0.17 + v["nose"] * 0.02), 0.030, 0.05) * 0.42,
                shade(skin, 0.78))
    img = blend(img, ellipse(0.5, cy + nl + 0.012, hw * 0.10, 0.012, 0.06) * 0.30, shade(skin, 0.66))

    # mouth
    my = cy + 0.132
    img = blend(img, ellipse(0.5, my, hw * (0.30 + v["mouth"] * 0.04), 0.014, 0.03) * 0.75,
                shade(skin, 0.60))

    # facial hair
    if v["beard"]:
        b = v["beard"]
        lower = ellipse(0.5, cy + 0.135, jaw_w * 1.02, 0.155, 0.02) * (PY > cy + 0.055)
        if b == 1:   # stubble
            img = blend(img, lower * 0.32, shade(hair, 0.9))
        elif b == 2:  # goatee
            goat = ellipse(0.5, cy + 0.155, hw * 0.34, 0.075, 0.03)
            img = blend(img, goat * 0.92, hair)
        elif b == 3:  # moustache
            img = blend(img, ellipse(0.5, my - 0.030, hw * 0.36, 0.020, 0.03) * 0.95, hair)
        elif b == 4:  # full beard
            img = blend(img, lower * 0.95, hair)
            img = blend(img, ellipse(0.5, my - 0.028, hw * 0.36, 0.019, 0.03) * 0.95, hair)
        else:        # heavy beard
            heavy = ellipse(0.5, cy + 0.155, jaw_w * 1.08, 0.185, 0.02) * (PY > cy + 0.035)
            img = blend(img, heavy * 0.97, hair)
            img = blend(img, ellipse(0.5, my - 0.028, hw * 0.38, 0.021, 0.03) * 0.97, hair)
        # mouth line re-asserted over the beard
        img = blend(img, ellipse(0.5, my, hw * 0.26, 0.009, 0.03) * 0.55, shade(skin, 0.45))

    # scar tissue over the brow, accumulating with career length
    if st["scar"] > 0.35:
        sx = -1 if h(fighter["fighter_id"], "scar_side", 2) else 1
        img = blend(img, ellipse(0.5 + sx * hw * 0.46, cy - 0.075, 0.010, 0.026, 0.04) * (0.35 * st["scar"]),
                    (0xC9, 0x8B, 0x82))

    return np.clip(img, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- png out
def write_png(path, arr):
    height, width, _ = arr.shape
    raw = b"".join(b"\x00" + arr[y].tobytes() for y in range(height))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))
    Path(path).write_bytes(png)


# ---------------------------------------------------------------- contact sheet
def main():
    universe = json.loads(Path("Databases/Default Universe.universe.json").read_text(encoding="utf-8"))
    rows = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("fighter_id") and o.get("name"):
                rows.append(o)
            for value in o.values():
                walk(value)
        elif isinstance(o, list):
            for value in o:
                walk(value)

    walk(universe)
    seen, picks = set(), []
    for row in rows:
        if row["name"] in seen:
            continue
        seen.add(row["name"])
        picks.append(row)
    picks = picks[:48]

    cols, gap = 8, 6
    rows_n = (len(picks) + cols - 1) // cols
    sheet = np.zeros((rows_n * (S + gap) + gap, cols * (S + gap) + gap, 3), dtype=np.uint8)
    sheet[:] = 18
    for i, f in enumerate(picks):
        r, c = divmod(i, cols)
        y, x = gap + r * (S + gap), gap + c * (S + gap)
        sheet[y:y + S, x:x + S] = render(f)
    write_png("portrait_contact_sheet.png", sheet)

    print(f"rendered {len(picks)} portraits -> portrait_contact_sheet.png")
    for i, f in enumerate(picks):
        if i % cols == 0:
            print()
        print(f"  r{i // cols + 1}c{i % cols + 1} {f['name'][:24]:<24} "
              f"{str(f.get('birth_region') or '?')[:12]:<12} age {f.get('age', '?')}", end="\n" if False else "\n")


if __name__ == "__main__":
    main()
