"""Head-on hair silhouettes. Pure geometry, shared by every portrait size."""

from math import sin, sqrt

from .styles import HAIR_STYLES
from .expansion import NEW_HAIR, control_value


def hair_mask(size, identity, cx, top, bottom, hw, eye_y, hairline):
    style = identity["hair_style"]
    if style >= 148:
        return authored_hair_mask(size, identity, cx, top, bottom, hw, hairline)
    if style >= 48:
        return expanded_hair_mask(size, identity, cx, top, bottom, hw, hairline)
    name, volume, side, texture_offset, texture = HAIR_STYLES[style]
    if style == 0:
        return set()
    volume *= .80 + control_value(identity["hair_volume"]) * .045
    part = (control_value(identity["hair_part"]) - 4.5) / 4.5
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


def authored_hair_mask(size, identity, cx, top, bottom, hw, hairline):
    """Loose waves and a close-sided mullet, without changing shipped shapes.

    The mullet's narrow nape locks start below the temples; they never form
    full-height curtains beside the eyes. All controls remain bounded.
    """
    style = identity["hair_style"]
    volume = control_value(identity["hair_volume"])
    part = (control_value(identity["hair_part"]) - 4.5) / 4.5
    mullet = style == 149
    shoulder = style in (150, 152, 154)
    icehawk = style == 151
    topknot = style == 153
    swept_fade = style == 156
    radius = hw * (.40 if icehawk else .90 if swept_fade else 1.03 if mullet else 1.10)
    crown_top = top - size * (.105 if icehawk else .040 if swept_fade else .018 + volume * .004)
    depth = max(size * .08, hairline - crown_top)
    mask = set()

    def ellipse(xc, yc, rx, ry):
        for y in range(max(0, round(yc - ry)), min(size, round(yc + ry) + 1)):
            extent = rx * sqrt(max(0, 1 - ((y - yc) / max(1, ry)) ** 2))
            for x in range(max(0, round(xc - extent)), min(size, round(xc + extent) + 1)):
                mask.add((x, y))

    for y in range(max(0, round(crown_top)), min(size, round(hairline + size * .07))):
        t = (y - crown_top) / depth
        width = radius * sqrt(max(0, 1 - (min(1, t) - 1) ** 2))
        for x in range(max(0, round(cx - width)), min(size, round(cx + width) + 1)):
            u = (x - cx) / max(1, radius)
            edge = hairline + size * (.017 + .033 * u * part + .006 * sin(u * 9))
            if swept_fade:
                # A compact asymmetric top with shaved sides, rather than the
                # generic horizontal cap used by regular short fades.
                edge = hairline + size * (-.045 + .040 * ((u + 1) / 2) + .004 * sin(u * 11))
            if y <= edge:
                mask.add((x, y))
    if icehawk:
        # A true crest has an elevated, broken top edge rather than a narrow
        # triangular fringe. Small uneven points keep it readable at 72px.
        for spike in range(5):
            u = (spike - 2) / 2
            tip = top - size * (.105 - .026 * abs(u))
            base_x = cx + u * hw * .24
            for y in range(max(0, round(tip)), round(hairline + size * .012)):
                taper = (y - tip) / max(1, hairline - tip)
                half = size * (.008 + .020 * min(1, taper))
                for x in range(round(base_x - half), round(base_x + half) + 1):
                    if 0 <= x < size:
                        mask.add((x, y))
    if style in (148, 149, 150, 152, 154):
        start = hairline + size * .125 if mullet else hairline - size * .025
        end = bottom + size * (.14 if shoulder else .055 if mullet else .01)
        for direction in (-1, 1):
            for y in range(max(0, round(start)), min(size, round(end))):
                t = (y - start) / max(1, end - start)
                wave = .035 * sin(t * 11 + direction)
                outer = hw * ((1.025 + .025 * t) if mullet else (1.11 + .14 * t + wave))
                inner = hw * ((.97 - .05 * t) if mullet else (.90 + .10 * t))
                if t > .8:
                    inner += (outer - inner) * (t - .8) / .2
                for d in range(round(inner), round(outer) + 1):
                    x = round(cx + direction * d)
                    if 0 <= x < size:
                        mask.add((x, y))
    if topknot:
        ellipse(cx + part * hw * .16, crown_top - size * .020, hw * .34, size * .060)
    if style == 154:
        # Two tapered plaits leave the cheeks visible and read at roster size.
        for direction in (-1, 1):
            for y in range(round(hairline), min(size, round(bottom + size * .13))):
                t = (y - hairline) / max(1, bottom - hairline)
                x = cx + direction * hw * (1.03 + .20 * t + .025 * sin(t * 25))
                ellipse(x, y, max(1, hw * (.075 - .035 * min(1, t))), 1)
    return mask


def expanded_hair_mask(size, identity, cx, top, bottom, hw, hairline):
    """Authored crown/fringe/side/tie profiles for the 100 appended styles."""
    name, texture, volume, reach, width, fringe, tail, variant = NEW_HAIR[identity["hair_style"]-48]
    volume *= .80 + control_value(identity["hair_volume"])*.045
    part = (control_value(identity["hair_part"])-4.5)/4.5
    crown_top = top-size*volume
    crown_depth = max(size*.09, hairline-crown_top)
    radius = hw*width
    mask = set()

    def span(y, left, right):
        if 0 <= y < size:
            mask.update((x, y) for x in range(max(0, round(left)), min(size, round(right)+1)))

    def ellipse(xc, yc, rx, ry):
        for y in range(max(0, round(yc-ry)), min(size, round(yc+ry)+1)):
            extent = rx*sqrt(max(0, 1-((y-yc)/max(1, ry))**2))
            span(y, xc-extent, xc+extent)

    for y in range(max(0, round(crown_top)), min(size, round(hairline+size*.085))):
        q = (y-crown_top)/crown_depth
        extent = radius*sqrt(max(0, 1-(min(1, q)-1)**2))
        crown_shift = hw*(.16 if variant == 1 else -.12 if variant == 3 else 0)*(1-min(1,q))
        for x in range(max(0, round(cx+crown_shift-extent)), min(size, round(cx+crown_shift+extent)+1)):
            u = (x-cx)/max(1, radius)
            edge = hairline + size*(fringe + .017*u*part)
            if texture in ("sweep", "tail"):
                edge += size*(.032*u*(1 if variant % 2 else -1) - .012*abs(u-part*.3))
            elif texture in ("bob", "shag"):
                edge += size*(.019*(1-abs(u))+.006*sin(u*(17+variant*3)))
            elif texture in ("coil", "curl"):
                edge += size*.014*sin(u*(15+variant*3))
            elif texture == "flat":
                edge -= size*(.015+variant*.005)*abs(u)**2
            elif texture == "spike":
                edge -= size*.025*abs(u)
            if variant == 2 and texture not in ("coil", "curl", "spike"):
                edge += size*(.048*abs(u-part*.18)-.028)
            if variant == 4 and texture in ("bob", "shag", "sweep"):
                edge += size*.024*u
            if y <= edge:
                mask.add((x, y))

    # Loose sides taper independently of the crown, never cover the face.
    if not tail:
        for direction in (-1, 1):
            end = bottom + size*reach + direction*size*.006*(variant-2)
            for y in range(round(hairline), min(size, round(end))):
                t = (y-hairline)/max(1, end-hairline)
                wave = .065*sin(t*(10+variant)+direction) if texture in ("curl", "shag") else 0
                inner = hw*(.91+.09*t)
                outer = max(inner, radius*(1+.13*t+wave))
                outer = inner+(outer-inner)*min(1, (1-t)*7)
                span(y, cx+direction*inner if direction > 0 else cx-outer,
                     cx+outer if direction > 0 else cx-inner)
    if tail in ("single", "double", "locks"):
        directions = (-1, 1) if tail != "single" else ((-1,) if variant % 2 else (1,))
        for direction in directions:
            for lock in range(3+variant//2 if tail == "locks" else 1):
                end = min(size*.94, bottom+size*(.09+variant*.020-lock*.018))
                for y in range(round(top+size*.12), round(end)):
                    t = (y-top)/max(1, end-top)
                    x = cx+direction*hw*(1.02+lock*.18+.24*t)+size*.008*sin(t*(32 if tail == "double" else 12)+lock)
                    rx = hw*((.065 if tail == "locks" else .18+variant*.012)*(1-.55*t))
                    span(y, x-rx, x+rx)
    if tail == "bun":
        placements = ((1.02, .20, .34), (-.80, .025, .40), (0., -.015, .48),
                      (0., -.038, .39), (.72, -.005, .53))
        bx, by, br = placements[variant]
        ellipse(cx+hw*bx, crown_top+size*by, hw*br, size*(.040+variant*.005))
    if tail == "puffs":
        for direction in (-1, 1):
            ellipse(cx+direction*hw*(.83+variant*.045), top+size*(.025+variant*.007),
                    hw*(.31+variant*.035), size*(.055+variant*.004))
    if texture in ("curl", "coil", "shag"):
        count = 9+variant*2
        for tuft in range(count):
            u = 2*tuft/(count-1)-1
            y = crown_top+crown_depth*(1-sqrt(max(0, 1-u*u)))
            ellipse(cx+u*radius*.94, y+size*.012, size*(.012 if texture == "coil" else .019), size*.018)
    return mask
