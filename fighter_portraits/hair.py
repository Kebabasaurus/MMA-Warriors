"""Head-on hair silhouettes. Pure geometry, shared by every portrait size."""

from math import sin, sqrt

from .styles import HAIR_STYLES


def hair_mask(size, identity, cx, top, bottom, hw, eye_y, hairline):
    style = identity["hair_style"]
    name, volume, side, texture_offset, texture = HAIR_STYLES[style]
    if style == 0:
        return set()
    volume *= .80 + identity["hair_volume"] * .045
    part = (identity["hair_part"] - 4.5) / 4.5
    cap_top = top - size * volume
    radius = hw * (1.02 + volume * 1.7)
    mask = set()

    def ellipse(xc, yc, rx, ry):
        for y in range(max(0, int(yc - ry)), min(size, int(yc + ry) + 1)):
            extent = rx * sqrt(max(0, 1 - ((y - yc) / max(1, ry)) ** 2))
            for x in range(max(0, round(xc - extent)), min(size, round(xc + extent) + 1)):
                mask.add((x, y))

    # Crown starts at a point and widens smoothly; the old profile clamp made
    # every crown flat. Hairlines and fringes vary independently of that crown.
    cap_depth = max(size * .09, hairline - cap_top)
    for y in range(max(0, int(cap_top)), min(size, int(hairline + size * .09))):
        crown = sqrt(max(0, 1 - ((y - (cap_top + cap_depth)) / cap_depth) ** 2)) if y < cap_top + cap_depth else 1
        extent = radius * crown
        for x in range(max(0, round(cx - extent)), min(size, round(cx + extent) + 1)):
            u = (x - cx) / max(1, radius)
            edge = hairline
            if style in (1, 2, 4, 5, 40, 41):
                edge -= size * .025 * abs(u)
            if style == 2:
                edge += size * .012 * (1-abs(u))
            if style == 3:
                edge += size * (.018 + .004*sin(u*30))
            if style == 5:
                edge -= size * .040 * abs(u)**2
            if style == 8:
                edge -= size * .018 * (1-abs(u))
            if style in (6, 7, 9, 10, 30, 32, 36):
                edge += size * (.032 * u * (1 if part >= 0 else -1) + .012)
            if style in (15, 33, 34, 45):
                edge += size * (.055 - .027 * abs(u) + .004 * sin(u * 23))
            if style in (35, 47):
                edge += size * (.065 * abs(u - part * .24) - .025)
            if style == 31:
                edge -= size * .085 * max(0, 1 - abs(u) * 1.35)
            if texture in ("curl", "coil", "shag"):
                edge += size * .012 * sin(u * 22)
            if style in (28, 29) and abs(u) > (.22 if style == 28 else .42):
                continue
            if y <= edge:
                mask.add((x, y))

    # Loose hair falls OUTSIDE the cheek. Tapered locks avoid the old solid
    # strips across the face. Bobs stop at jaw; loose hair extends to shoulders.
    if side:
        reach = eye_y + size * .07 if side == 1 else bottom + size * .14
        if style in (33, 34):
            reach = bottom + size * .015
        for direction in (-1, 1):
            for y in range(int(hairline - size * .025), min(size, int(reach))):
                t = (y - hairline) / max(1, reach - hairline)
                wave = .04 * sin(t * 13 + direction) if texture in ("curl", "shag") else 0
                outer = radius * (1.02 + .13 * t + wave)
                inner = hw * (.86 + .10 * t)
                if side == 1:
                    outer *= 1 - .15 * max(0, t)
                if style == 34:
                    outer *= 1 + direction * .12 * t
                if t > .87:
                    inner += (outer - inner) * (t - .87) / .13
                for d in range(round(inner), round(outer) + 1):
                    x = round(cx + direction * d)
                    if 0 <= x < size:
                        mask.add((x, y))

    if texture in ("knot", "loc_knot", "puff"):
        ellipse(cx + part * hw * .18, cap_top + size * .008,
                hw * (.66 if texture == "puff" else .43), size * (.070 if texture == "puff" else .045))
    if texture == "double_buns":
        for direction in (-1, 1):
            ellipse(cx + direction * hw * .95, top + size * .025, hw * .36, size * .052)
    if texture == "low_bun":
        ellipse(cx + hw * .95, eye_y + size * .04, hw * .31, size * .045)
    if texture == "dread":
        for direction in (-1, 1):
            for lock in range(3):
                end = bottom + size * (.07 + lock * .026)
                for y in range(round(hairline),min(size,round(end))):
                    t = (y-hairline)/max(1,end-hairline)
                    x = cx + direction*hw*(.85+lock*.20+.10*sin(t*6+lock))
                    ellipse(x,y,hw*.065,1)
    if texture in ("tail", "braid_tail", "twin_braids"):
        directions = (-1, 1) if texture == "twin_braids" else ((-1,) if part < 0 else (1,))
        for direction in directions:
            for y in range(int(top + size * .10), min(size, int(bottom + size * .18))):
                t = (y - top) / max(1, bottom - top)
                x = cx + direction * hw * (1.02 + .25 * t)
                if texture in ("twin_braids", "braid_tail"):
                    x += size * .006 * sin(t * 65)
                ellipse(x, y, max(1, hw * (.20 - .10 * t)), 1)
    if texture in ("coil", "curl", "puff", "loc_knot", "shag"):
        # Irregular round tufts change the OUTLINE as well as surface texture.
        for index in range(11):
            u = (index - 5) / 5
            y = cap_top + cap_depth * (1 - sqrt(max(0, 1 - u * u)))
            ellipse(cx + u * radius * .93, y + size * .012,
                    size * (.014 if texture == "coil" else .022), size * .020)
    return mask
