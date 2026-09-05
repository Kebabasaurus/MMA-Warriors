"""Comic fighter portrait - REFERENCE PROTOTYPE, not runtime code.

Uses numpy, which the game runtime must not. This exists to prove the identity
model and to serve as the build-time baker described in
docs/FIGHTER_PORTRAIT_IMPLEMENTATION_SPEC.md.

Known issues, documented rather than hidden: render() is a single ~200-line
function, coordinates are bare float literals throughout, the hair silhouette is
blocky with notch artifacts at the temples, and the face construction does not
read convincingly. The identity vector, region tables, HAIR_STYLES, DYE palettes
and head width-profile are the parts worth reusing.

Comic fighter portrait, v2.

Rebuilt from the v1 failure. The three changes that matter:
  1. the head is a vertical width profile (crown -> temple -> cheekbone -> jaw ->
     chin), not a union of ellipses, so skulls have real construction;
  2. cel shadows follow the surface normal of that profile instead of being cut
     by an offset ellipse, so shading wraps the form;
  3. hair is a scaled, offset copy of the head profile with real mass above the
     skull, carved by a hairline curve.
"""
import hashlib
import struct
import zlib
from pathlib import Path

import numpy as np

S = 460
INK = (12, 10, 14)

SKIN = [
    ((0xF7, 0xD8, 0xC0), (0xDB, 0xAC, 0x9C), (0xBE, 0x8B, 0x82)),
    ((0xEC, 0xC0, 0x9E), (0xC9, 0x95, 0x83), (0xA8, 0x74, 0x69)),
    ((0xD8, 0xA1, 0x76), (0xB0, 0x77, 0x64), (0x8E, 0x59, 0x51)),
    ((0xB8, 0x7C, 0x51), (0x8F, 0x57, 0x4C), (0x6E, 0x3F, 0x3B)),
    ((0x8F, 0x59, 0x39), (0x6A, 0x3D, 0x39), (0x4E, 0x2A, 0x2C)),
    ((0x68, 0x3E, 0x28), (0x4A, 0x2A, 0x2C), (0x33, 0x1C, 0x21)),
    ((0x48, 0x2A, 0x1C), (0x31, 0x1D, 0x21), (0x21, 0x13, 0x18)),
]
HAIR = [
    ((0x1C, 0x18, 0x1E), (0x0E, 0x0C, 0x13)), ((0x35, 0x26, 0x20), (0x1F, 0x16, 0x17)),
    ((0x56, 0x39, 0x24), (0x37, 0x22, 0x1C)), ((0x7C, 0x54, 0x2E), (0x52, 0x34, 0x23)),
    ((0xAA, 0x7C, 0x40), (0x76, 0x50, 0x30)), ((0xD4, 0xAA, 0x5E), (0x98, 0x73, 0x44)),
    ((0xB2, 0x4C, 0x26), (0x7A, 0x30, 0x20)), ((0xCB, 0xC6, 0xBE), (0x94, 0x90, 0x90)),
]
# Dye palettes for multi-colour hair. Real fighters use these constantly -
# O'Malley has fought in rainbow since UFC 250 and dyes per opponent
# (Ecuadorian flag vs Vera; pink/orange/yellow at UFC 280).
DYE = {
    "rainbow": [(0xE8, 0x3B, 0x50), (0xF0, 0x8A, 0x24), (0xF2, 0xD0, 0x36),
                (0x4A, 0xC0, 0x62), (0x36, 0x8E, 0xE0), (0x8B, 0x4F, 0xD0)],
    "sunset": [(0xF0, 0x3C, 0x78), (0xF5, 0x7A, 0x2E), (0xF7, 0xC9, 0x3A)],
    "ecuador": [(0xF7, 0xC9, 0x2E), (0x2E, 0x54, 0xC8), (0xD8, 0x2B, 0x2B)],
    "ice": [(0xBF, 0xE6, 0xF5), (0x6C, 0xB8, 0xE0), (0xE8, 0xF4, 0xFA)],
    "toxic": [(0x9B, 0xE8, 0x22), (0x24, 0xC0, 0x8A)],
    "bleach": [(0xF2, 0xE6, 0xC8), (0xD8, 0xC4, 0x96)],
    "red": [(0xD8, 0x2A, 0x32), (0x92, 0x18, 0x22)],
    "blue": [(0x2E, 0x6C, 0xE0), (0x1A, 0x3E, 0x92)],
}

BG = [
    ((0x26, 0x32, 0x42), (0x17, 0x1F, 0x2C)), ((0x1C, 0x2E, 0x60), (0x12, 0x1C, 0x3F)),
    ((0x56, 0x16, 0x1A), (0x36, 0x0D, 0x12)), ((0x1F, 0x4E, 0x3B), (0x12, 0x31, 0x26)),
    ((0x3A, 0x1A, 0x6D), (0x23, 0x0F, 0x47)), ((0x4C, 0x3A, 0x20), (0x2F, 0x23, 0x14)),
    ((0x2C, 0x30, 0x38), (0x19, 0x1C, 0x22)), ((0x5C, 0x24, 0x2C), (0x39, 0x15, 0x1C)),
    ((0x14, 0x3A, 0x4C), (0x0C, 0x23, 0x31)), ((0x40, 0x20, 0x3C), (0x28, 0x13, 0x26)),
]

# name, crown volume, side coverage, hairline offset, texture
#   side: 0 tight to skull, 1 covers the ear, 2 past the jaw
#   tex : "flat" | "curl" | "braid" | "dread" | "spike"
HAIR_STYLES = [
    ("shaved",        0.000, 0, 0.00, "flat"),
    ("buzz",          0.006, 0, 0.00, "flat"),
    ("crop",          0.016, 0, 0.00, "flat"),
    ("short_fade",    0.020, 0, -0.02, "flat"),
    ("side_part",     0.026, 0, 0.00, "flat"),
    ("slick_back",    0.024, 0, -0.03, "flat"),
    ("high_top",      0.062, 0, -0.01, "curl"),
    ("afro",          0.070, 1, 0.00, "curl"),
    ("curly_mop",     0.048, 1, 0.02, "curl"),
    ("top_knot",      0.030, 0, 0.00, "knot"),
    ("man_bun",       0.026, 1, 0.00, "knot"),
    ("ponytail",      0.022, 1, 0.00, "tail"),
    ("cornrows",      0.014, 1, -0.01, "braid"),
    ("braided_back",  0.020, 1, -0.02, "braid"),
    ("dreads",        0.040, 2, 0.00, "dread"),
    ("mohawk",        0.055, 0, -0.02, "spike"),
    ("undercut",      0.034, 0, -0.02, "flat"),
    ("long_loose",    0.032, 2, 0.01, "flat"),
    ("shoulder_wave", 0.030, 2, 0.02, "curl"),
]

YY, XX = np.mgrid[0:S, 0:S]
PX, PY = XX / S, YY / S


def hh(fid, trait, mod):
    d = hashlib.blake2b(f"{fid}|{trait}".encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(d, "big") % mod


def dilate(mask, r):
    out = mask.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                out |= np.roll(np.roll(mask, dy, 0), dx, 1)
    return out


def outline(mask, w):
    return dilate(mask, w) & ~mask


def ell(cx, cy, rx, ry):
    return (((PX - cx) / rx) ** 2 + ((PY - cy) / ry) ** 2) <= 1.0


def paint(img, mask, colour):
    img[mask] = colour


# --------------------------------------------------------------- head profile
def head_masks(top, bot, hw, cheek, jaw, chin):
    """Half-width as a function of height: a skull, not an ellipse.

    Returns (mask, t, halfwidth) where t is 0 at the crown and 1 at the chin.
    """
    t = (PY - top) / (bot - top)
    ts = [0.00, 0.08, 0.18, 0.32, 0.46, 0.60, 0.72, 0.84, 0.93, 1.00]
    ws = [0.62, 0.86, 0.97, 1.00, 0.99 * cheek, 0.94 * cheek,
          0.87 * jaw, 0.74 * jaw, 0.56 * chin, 0.34 * chin]
    half = np.interp(np.clip(t, 0, 1), ts, ws) * hw
    mask = (np.abs(PX - 0.5) <= half) & (t >= 0) & (t <= 1)
    return mask, t, half


def render(f):
    fid = f["fighter_id"]
    ov = f.get("_override", {})

    def trait(name, mod):
        return ov[name] if name in ov else hh(fid, name, mod)

    age = int(f.get("age", 27))
    bouts = int(f.get("record_w", 0)) + int(f.get("record_l", 0))
    grey = max(0.0, min(1.0, (age - 34) / 18.0))
    recede = max(0.0, min(1.0, (age - 29) / 20.0))
    cauli = max(0.0, min(1.0, bouts / 26.0))
    scar = max(0.0, min(1.0, bouts / 32.0))

    skin, skin_sh, skin_dp = SKIN[trait("skin", len(SKIN))]
    if "hair_rgb" in ov:
        hair, hair_sh = ov["hair_rgb"]
    else:
        hair, hair_sh = HAIR[7] if grey > 0.8 else HAIR[trait("hair_colour", 7)]
        if 0.25 < grey <= 0.8:
            g = grey * 0.65
            hair = tuple(hair[i] * (1 - g) + HAIR[7][0][i] * g for i in range(3))
            hair_sh = tuple(hair_sh[i] * (1 - g) + HAIR[7][1][i] * g for i in range(3))
    bg, bg_sh = BG[trait("bg", len(BG))]

    style = trait("hair_style", len(HAIR_STYLES))
    sty = HAIR_STYLES[style]
    jaw = 0.86 + trait("jaw", 4) * 0.075
    chin = 0.82 + trait("chin", 3) * 0.14
    cheek = 0.94 + trait("cheek", 3) * 0.055
    brow_i = trait("brow", 3)
    nose_i = trait("nose", 3)
    beard = trait("beard", 5)
    hw = 0.178 * (0.94 + trait("head_w", 100) / 100 * 0.16)

    top, bot = 0.195, 0.700
    head, t, half = head_masks(top, bot, hw, cheek, jaw, chin)
    eye_y = top + (bot - top) * 0.50
    nose_y = top + (bot - top) * 0.655
    mouth_y = top + (bot - top) * 0.795

    img = np.zeros((S, S, 3), dtype=np.float64)
    img[:] = bg
    paint(img, ell(0.5, 0.26, 1.05, 0.40), bg_sh)

    # ---- neck and traps: fighters are thick through here
    neck = ell(0.5, bot + 0.055, hw * 0.60, 0.105) & (PY > bot - 0.075)
    traps = ell(0.5, 1.08, 0.62, 0.33)
    paint(img, traps, skin_sh)
    paint(img, traps & ~ell(0.40, 1.02, 0.60, 0.33), skin_dp)
    paint(img, neck, skin_sh)
    paint(img, neck & (PX > 0.5 + hw * 0.22), skin_dp)

    # ---- ears, behind the head
    ear_y = eye_y + 0.020
    ear_r = 0.028 + 0.013 * cauli
    ears = (ell(0.5 - hw * 0.99, ear_y, ear_r * 0.75, ear_r * 1.15)
            | ell(0.5 + hw * 0.99, ear_y, ear_r * 0.75, ear_r * 1.15))
    paint(img, ears, skin_sh)
    paint(img, outline(ears, 2) & ~head, INK)

    # ---- face
    paint(img, head, skin)

    # form shading: nx is the horizontal surface normal across the profile
    with np.errstate(divide="ignore", invalid="ignore"):
        nx = np.where(half > 1e-6, (PX - 0.5) / np.maximum(half, 1e-6), 0.0)
    lit = head & (nx < 0.52)
    paint(img, head & ~lit, skin_sh)                       # light from upper left
    paint(img, head & (nx > 0.86), skin_dp)                # core shadow at the edge
    # cheekbone shelf
    paint(img, head & (t > 0.545) & (t < 0.635) & (np.abs(nx) > 0.42), skin_sh)
    # under the jaw / chin
    paint(img, head & (t > 0.90), skin_sh)
    # brow shelf casts down onto the eye sockets
    paint(img, head & (PY > eye_y - 0.040) & (PY < eye_y - 0.014) & (np.abs(nx) < 0.72), skin_sh)

    # ---- hair with real mass above the skull
    hair_m = np.zeros_like(head)
    if style:
        vol, side, hl_off, tex = sty[1], sty[2], sty[3], sty[4]
        hairline = top + (bot - top) * (0.255 + recede * 0.10) + hl_off
        cap = head_masks(top - vol, bot, hw * (1.0 + vol * 1.4), cheek, jaw, chin)[0]
        cap = cap & (PY < hairline + 0.34)
        # carve the face opening
        face_open = head_masks(hairline, bot + 0.05, hw * 1.02, cheek, jaw, chin)[0]
        cap = cap & ~face_open
        if side:                                              # sides cover the ear or longer
            reach = ear_y + 0.06 if side == 1 else bot + 0.03
            flank = head_masks(top, bot + 0.10, hw * (1.06 + 0.06 * side), cheek, jaw, chin)[0]
            cap |= flank & (PY > hairline) & (PY < reach) & (np.abs(PX - 0.5) > hw * 0.72)
        if tex == "knot":
            cap |= ell(0.5, top - vol - 0.020, hw * 0.32, 0.040)
        if tex == "tail":
            cap |= ell(0.5, top + 0.055, hw * 0.30, 0.055) & (PX > 0.5 - hw * 0.30)
        if tex == "spike":                                    # mohawk: strip only
            cap &= (np.abs(PX - 0.5) < hw * 0.34) | (PY < hairline + 0.02)
            cap |= ell(0.5, top - vol - 0.010, hw * 0.30, vol + 0.030)
        if tex == "dread":
            for k in range(-3, 4):
                cap |= ell(0.5 + k * hw * 0.30, bot - 0.02, hw * 0.11, 0.10) & (PY > hairline)
        if recede > 0.25:
            cap &= ~((np.abs(PX - 0.5) > hw * (0.80 - 0.34 * recede))
                     & (PY < hairline + 0.055 + 0.045 * recede))
        hair_m = cap
        dye = ov.get("dye")
        if dye:
            # Cornrows run front-to-back, so from the front they read as vertical
            # colour bands. Solid dye jobs band the same way, just wider.
            cols = DYE[dye] if isinstance(dye, str) else dye
            n = len(cols)
            band = np.clip(((PX - (0.5 - hw)) / (2 * hw) * n).astype(int), 0, n - 1)
            for i, col in enumerate(cols):
                sel = hair_m & (band == i)
                paint(img, sel, col)
                paint(img, sel & (nx > 0.55), tuple(c * 0.72 for c in col))
        else:
            paint(img, hair_m, hair)
            paint(img, hair_m & (nx > 0.48), hair_sh)
        # texture: braid / dread separations and curl breakup
        if tex in ("braid", "dread"):
            step = hw * (0.30 if tex == "braid" else 0.30)
            for k in range(-6, 7):
                line = np.abs(PX - (0.5 + k * step)) < (0.0022 if tex == "braid" else 0.004)
                paint(img, hair_m & line, INK)
        elif tex == "curl":
            for k in range(-4, 5):
                for j in range(0, 5):
                    c = ell(0.5 + k * hw * 0.34, top - vol + 0.030 + j * 0.038,
                            hw * 0.15, 0.022)
                    paint(img, hair_m & outline(c, 1), tuple(c2 * 0.75 for c2 in
                          (hair if not dye else (0x40, 0x30, 0x30))))
        paint(img, hair_m & (PY > hairline - 0.010) & (PY < hairline + 0.016) & ~head,
              tuple(c * 0.80 for c in hair) if not dye else INK)

    # ---- brows: angled, heavy
    for sx in (-1, 1):
        bx = 0.5 + sx * hw * 0.46
        by = eye_y - 0.042 - brow_i * 0.004
        brow = ell(bx, by, hw * 0.34, 0.016 + brow_i * 0.003)
        brow &= ~ell(bx + sx * hw * 0.30, by - 0.030, hw * 0.30, 0.026)   # angle the inner end
        paint(img, brow & head, hair_sh if style else skin_dp)

    # ---- eyes: almond, set in the socket
    for sx in (-1, 1):
        ex = 0.5 + sx * hw * 0.46
        upper = ell(ex, eye_y + 0.012, hw * 0.26, 0.030)
        lower = ell(ex, eye_y - 0.016, hw * 0.26, 0.030)
        eye = upper & lower & head
        paint(img, eye, (0xF2, 0xEE, 0xE7))
        paint(img, eye & ell(ex, eye_y, hw * 0.105, 0.014), hair_sh)
        paint(img, eye & ell(ex, eye_y, hw * 0.045, 0.007), INK)
        paint(img, ell(ex - hw * 0.045, eye_y - 0.008, hw * 0.030, 0.005) & eye, (255, 255, 255))
        paint(img, outline(eye, 1) & head, INK)

    # ---- nose: one shadow plane down the side, nostril, no outline box
    nw = hw * (0.16 + nose_i * 0.025)
    bridge = (np.abs(PX - (0.5 + nw * 0.42)) < nw * 0.30) & (PY > eye_y - 0.010) & (PY < nose_y)
    paint(img, bridge & head, skin_sh)
    ball = ell(0.5, nose_y, nw * 0.85, 0.020)
    paint(img, ball & head & (PX > 0.5 + nw * 0.05), skin_sh)
    paint(img, ell(0.5 - nw * 0.60, nose_y + 0.004, nw * 0.20, 0.008) & head, skin_dp)
    paint(img, ell(0.5 + nw * 0.60, nose_y + 0.004, nw * 0.20, 0.008) & head, skin_dp)

    # ---- mouth
    paint(img, ell(0.5, mouth_y, hw * 0.34, 0.009) & head, INK)
    paint(img, ell(0.5, mouth_y + 0.020, hw * 0.22, 0.010) & head, skin_sh)

    # ---- facial hair, jaw band only
    if beard:
        band = head & (t > 0.735) & ~ell(0.5, mouth_y, hw * 0.32, 0.017)
        if beard == 1:
            paint(img, band, skin_sh)
        elif beard == 2:
            paint(img, head & (t > 0.855) & (np.abs(PX - 0.5) < hw * 0.38), hair)
        elif beard == 3:
            paint(img, ell(0.5, mouth_y - 0.024, hw * 0.34, 0.013) & head, hair)
        else:
            paint(img, band, hair)
            paint(img, band & (nx > 0.48), hair_sh)
            paint(img, ell(0.5, mouth_y - 0.024, hw * 0.34, 0.013) & head, hair)
            paint(img, ell(0.5, mouth_y, hw * 0.30, 0.008) & head, INK)

    # ---- damage
    if scar > 0.4:
        sx = -1 if hh(fid, "scar_side", 2) else 1
        cut = ell(0.5 + sx * hw * 0.60, eye_y - 0.062, 0.006, 0.020)
        paint(img, cut & head, (0xEB, 0xC8, 0xBE))
        paint(img, outline(cut, 1) & head, INK)

    # ---- ink pass
    if style:
        paint(img, outline(hair_m, 2) & ~head, INK)
        paint(img, outline(hair_m, 2) & head, INK)
    paint(img, outline(neck, 2) & ~head & ~traps, INK)
    paint(img, outline(traps, 2) & (PY < 0.995) & ~head & ~neck, INK)
    paint(img, outline(head, 3) & ~hair_m, INK)
    return np.clip(img, 0, 255).astype(np.uint8)


def write_png(path, arr):
    hgt, wid, _ = arr.shape
    raw = b"".join(b"\x00" + arr[y].tobytes() for y in range(hgt))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    Path(path).write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", wid, hgt, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
