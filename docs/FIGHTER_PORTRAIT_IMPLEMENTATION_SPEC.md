# Fighter Portrait System — Implementation Spec

**Audience: an implementer building this end to end.** This is a build spec, not a discussion
document. Design rationale lives in `docs/FIGHTER_PORTRAIT_SYSTEM_DESIGN.md`; read it only if you
need the *why*. Everything required to build is here.

Reference implementation: `analysis/portraits/portrait_comic_reference.py` (numpy prototype — proves
the model, **not** shippable, see §9).

---

## 1. What you are building

Replace the current initials-badge portrait with per-fighter comic-style portraits that are:

1. **unique** — no two fighters visually identical;
2. **deterministic** — byte-identical on every launch, machine and save;
3. **region-appropriate** — appearance conditioned on where a fighter is from;
4. **stateful** — fighters visibly age and accumulate damage across a career;
5. **overridable** — named real fighters get authored appearances.

### Current state to replace

The portrait is four Tk canvas shapes (frame, accent oval "head", fixed `#d7d7d7` polygon torso,
two initials). Per-fighter variation is two colours from **9 palettes** keyed on
`sum(ord(name)) % 9`.

Measured on a 4,856-fighter world: **70.7% of fighters share a pixel-identical portrait**; 2,630
distinct portraits total; worst collision 11 fighters.

---

## 2. Hard constraints — violating any of these is a defect

| # | Constraint | Why |
|---|---|---|
| C1 | **Runtime is stdlib only.** No numpy, no PIL. | `requirements.txt` lists numpy as *optional* (audio). The game must run without it. numpy is allowed in build-time/dev scripts only. |
| C2 | **A `move_id`-style contract applies to portrait trait ids.** Never rename or remove a trait key or a style id once shipped. | Persisted in saves. Add only. |
| C3 | **No appearance trait may touch any rating, ability, popularity or simulation value.** | Cosmetic only. Enforce with a test. |
| C4 | **Hash `fighter_id`, never `name`.** | Names change; `sum(ord)` is also order-independent (`"Jon Jones"` and `"Jones Jon"` collide). |
| C5 | **Independent hash draw per trait.** | So adding a trait later does not reshuffle existing fighters. |
| C6 | Existing test contracts must keep passing, incl. `smoke_test.py:1486` (retired seal `#315a70`, "RTD" text). | |

### Determinism source

All 1,534 shipped real fighters carry a stable id from `deterministic_source_fighter_id`
(`models.py:16`) — a UUID5 of `database_type + name + owner + placement`:

```
FTR-DU-3dccf6c6db985190a1af0328b227592b  ->  Sean O'Malley
```

Reproducible from the data, so anything hashed from it is stable forever. Generated fighters get a
random persisted `uuid4` — stable within a save, different in a new world, which is correct.

```python
def trait_hash(fighter_id: str, trait: str, mod: int) -> int:
    d = hashlib.blake2b(f"{fighter_id}|{trait}".encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(d, "big") % mod
```

---

## 3. Data model

### 3.1 Immutable identity — hashed once, persisted

| Field | Range | Notes |
|---|---|---|
| `skin` | 0–6 | index into `SKIN`, region-weighted |
| `hair_colour` | 0–7 | index into `HAIR`, region-weighted |
| `hair_style` | 0–31 | index into `HAIR_STYLES` (§4) |
| `facial_hair` | 0–15 | index into `FACIAL_HAIR` (§5) |
| `dye` | `""` or key of `DYE` | usually `""`; overrides set it |
| `brow` | 0–4 | §6 |
| `eye_shape` | 0–5 | §6 |
| `eye_spacing` | 0–2 | §6 |
| `eye_size` | 0–2 | §6 |
| `nose` | 0–5 | §6 |
| `mouth` | 0–4 | §6 |
| `jaw` | 0–4 | §6 |
| `chin` | 0–3 | §6 |
| `cheek` | 0–3 | §6 |
| `face_length` | 0–2 | §6 |
| `ear` | 0–3 | §6 |
| `head_w` | 0–99 | width multiplier 0.94–1.10 |
| `bg` | 0–11 | background palette |

**Combinatorial space: ~2.6 × 10¹² before dye and state.** Collisions are not a concern; the work
is making the variation *legible*, not large.

### 3.2 Derived state — recomputed every draw, never stored

```python
grey    = clamp((age - 34) / 18)          # hair greys
recede  = clamp((age - 29) / 20)          # hairline recedes
cauli   = clamp(total_bouts / 26)         # cauliflower ear
scar    = clamp(total_bouts / 32)         # brow scar tissue
swell   = 1.0 if fighter.injured else 0   # asymmetric swelling
```

Rule: state layers **saturate**, never stack past their cap, so a veteran does not become
grotesque.

### 3.3 Persistence

Add to `Fighter` (`models.py`):

```python
portrait_version: int = 0        # mirrors the existing career_arc_version pattern
portrait_identity: dict = field(default_factory=dict)
```

Backfill where the current palette is backfilled — `persistence.py:1860`, which fills
`portrait_bg`/`portrait_accent` only when empty. **Keep `portrait_bg`/`portrait_accent`** as the
fallback palette for legacy saves and missing assets.

**Versioning rule:** bumping the generator must not restyle existing fighters. A fighter with
`portrait_version < CURRENT` keeps their stored vector unless explicitly migrated.

---

## 4. Hair styles — 32

`(id, name, crown_volume, side_coverage, hairline_offset, texture)`
`side`: 0 tight to skull · 1 covers the ear · 2 past the jaw
`texture`: `flat` `curl` `coil` `braid` `dread` `twist` `spike` `knot` `tail`

```
 0 shaved          0.000 0  0.00 flat      16 wavy_medium     0.030 1  0.01 curl
 1 buzz            0.006 0  0.00 flat      17 shoulder_wave   0.032 2  0.02 curl
 2 crew_cut        0.012 0  0.00 flat      18 long_loose      0.034 2  0.01 flat
 3 crop            0.016 0  0.00 flat      19 man_bun         0.026 1  0.00 knot
 4 short_fade      0.020 0 -0.02 flat      20 top_knot        0.030 0  0.00 knot
 5 high_fade       0.024 0 -0.03 flat      21 ponytail        0.022 1  0.00 tail
 6 side_part       0.026 0  0.00 flat      22 half_up         0.028 2  0.00 tail
 7 comb_over       0.024 0  0.01 flat      23 cornrows        0.014 1 -0.01 braid
 8 slick_back      0.024 0 -0.03 flat      24 braided_back    0.020 1 -0.02 braid
 9 quiff           0.040 0 -0.01 flat      25 box_braids      0.034 2  0.00 braid
10 pompadour       0.052 0 -0.01 flat      26 dreads          0.040 2  0.00 dread
11 high_top        0.062 0 -0.01 coil      27 twists          0.030 1  0.00 twist
12 flat_top        0.050 0 -0.01 coil      28 mohawk          0.055 0 -0.02 spike
13 afro            0.070 1  0.00 coil      29 faux_hawk       0.038 0 -0.02 spike
14 curly_mop       0.048 1  0.02 curl      30 undercut        0.034 0 -0.02 flat
15 bowl_cut        0.030 1  0.02 flat      31 receding_nat    0.014 0  0.04 flat
```

### 4.1 Hair colour and dye

Natural `HAIR` ramp: 8 entries, each a `(base, shadow)` pair, black → dark brown → brown → light
brown → dark blond → blond → auburn → grey.

Dye palettes are **multi-colour**, and this matters — real fighters dye constantly. Sean O'Malley
has fought in rainbow at every bout since UFC 250 (2020), usually **braided**, and customises per
opponent (Ecuadorian flag colours vs Vera at UFC 252; pink/orange/yellow at UFC 280).

```python
DYE = {
  "rainbow": [red, orange, yellow, green, blue, violet],
  "sunset":  [pink, orange, yellow],
  "ecuador": [yellow, blue, red],
  "ice":     [pale_blue, mid_blue, white],
  "toxic":   [lime, teal],
  "bleach":  [cream, sand],
  "red": [...], "blue": [...], "platinum": [...], "pink": [...],
}
```

**Rendering rule that makes this work:** cornrows and braids run front-to-back, so head-on they read
as **vertical colour bands**. Band index across the hair mask:

```python
band = int((x - (cx - hw)) / (2 * hw) * len(colours))
```

Apply the same banding to non-braided dye jobs with fewer, wider bands. Braid/dread textures then
overlay thin ink separation lines along the band boundaries. This is verified working in the
reference implementation.

---

## 5. Facial hair — 16

```
 0 none              8 chin_strap
 1 stubble_light     9 short_beard
 2 stubble_heavy    10 full_beard
 3 moustache        11 heavy_beard
 4 horseshoe        12 long_beard
 5 goatee           13 mutton_chops
 6 van_dyke         14 beard_no_moustache
 7 soul_patch       15 braided_beard
```

Rules:
- gate on `gender != "Female"`;
- the beard mask is a **jaw band only** — `t > 0.735` in head-profile coordinates, minus the mouth
  ellipse. A mask that starts higher covers the whole face (this was a real bug in the prototype);
- moustache is a separate small mask so it can combine with beard styles;
- colour follows hair colour, greys with `grey`, and is **not** affected by `dye` unless the
  override sets `dye_beard: true`.

---

## 6. Facial features

All hashed independently (C5).

| Trait | Options |
|---|---|
| `brow` | flat · arched · angled_down · heavy · thin |
| `eye_shape` | almond · round · hooded · narrow · downturned · upturned |
| `eye_spacing` | close · normal · wide |
| `eye_size` | small · normal · large |
| `nose` | straight · broad · aquiline · snub · **broken_left** · **broken_right** |
| `mouth` | neutral · wide · thin · full · downturned |
| `jaw` | 5 steps, narrow → square |
| `chin` | round · square · cleft · pointed |
| `cheek` | 4 steps, flat → high cheekbones |
| `face_length` | short · normal · long |
| `ear` | 4 sizes, each with 3 cauliflower states driven by `cauli` |

`broken_left` / `broken_right` should be weighted **up** with career length — a broken nose is
characteristic of the sport and a cheap, high-value differentiator.

### Head construction

Do **not** build the head from a union of ellipses (the first prototype did; it produces lozenges).
Use a **vertical width profile** — half-width as a function of height, interpolated over control
points from crown to chin:

```
t    0.00  0.08  0.18  0.32  0.46        0.60        0.72       0.84       0.93       1.00
w    0.62  0.86  0.97  1.00  0.99*cheek  0.94*cheek  0.87*jaw   0.74*jaw   0.56*chin  0.34*chin
```

`face_length` scales the crown→chin distance. Cel shadows follow the **surface normal** of this
profile (`nx = (x - cx) / half_width(y)`), not an offset ellipse — that is what makes shading wrap
the form.

---

## 7. Region-conditioned appearance

**The hash selects *within* a region distribution, never across the global space.** A uniform hash
gives Nigerian fighters pale skin and blond hair.

### Resolution order — verified against the shipped database

`birth_region` is **absent from all 1,534 shipped fighters**. Present on 100%: `birth_country`,
`nationality`, `region`, `hometown`.

```
birth_country  ->  nationality  ->  region  ->  birth_region  ->  default
```

This matches `country_flag_path_for_fighter` (`views.py:1637`), so the two systems agree.

Each group maps to weights over the `SKIN` (7) and `HAIR` (8) ramps. See
`REGION_APPEARANCE` in the reference implementation for a working starting table covering the 13
`REGIONS` plus country and nationality aliases.

### Guardrails — non-negotiable

1. Distributions are **wide, never single-valued**. No region maps to one appearance.
2. Traits are anatomical ranges only (tone, texture, structure) — never cultural props, never
   region-specific "features".
3. No appearance trait affects any simulation value (C3).
4. Authored overrides always win, so any bad derivation is correctable.
5. `birth_country` drives appearance; `fighting_base` does not. A fighter born in Nigeria fighting
   out of the UK draws from Nigeria.

---

## 8. Authored overrides

Follow the existing pattern — `real_sport_profiles.py:200` (`PRIME_AGE_OVERRIDES`) is a name-keyed
dict of hand-authored values.

```python
PORTRAIT_OVERRIDES = {
    "Sean O'Malley": {
        "skin": 0, "hair_style": 23,        # cornrows
        "dye": "rainbow", "facial_hair": 10,
        "jaw": 1, "chin": 1, "cheek": 2, "nose": 0, "bg": 4,
    },
}
```

Merged over the derived vector — author only what matters, everything else stays hashed.

**Tiering:** ~50 icons fully authored · ~200 well-known partial (skin, hair, facial hair) ·
remaining ~1,280 fully derived.

**Key by `name`**, with a test asserting every override key resolves to a fighter in the shipped
database so a rename fails CI loudly instead of silently dropping the override.

---

## 9. Rendering — two viable routes

The reference implementation is **numpy** and therefore cannot be the runtime renderer (C1). Pick one:

### Route A — stdlib rasteriser (recommended to start)

Port the reference to pure Python producing a `tk.PhotoImage` via bulk `put`. Measured costs on
Tk 8.6.15:

```
bulk put, full 360x360     121.9 ms      -> acceptable once, cached
PhotoImage PNG export        6.6 ms
```

Portraits render 1–2 at a time (profile card, fight-night corners), so with a cache keyed on
`(fighter_id, size, state_signature)` this is fine. **No new dependency, ships immediately.**

### Route B — baked PNG layers (higher art ceiling)

Composite pre-baked layers. Measured: **0.25 ms per layer, ~2.5 ms per 10-layer portrait.**

```python
root.tk.call(base, "copy", layer, "-to", 0, 0, "-compositingrule", "overlay")
```

Constraints if you take this route:
- **Runtime scaling is impossible.** Tk `subsample` is nearest-neighbour and shatters ink: measured
  2 strokes → **42 fragments at /3, 99 at /4**. Area-averaged offline downscaling stays continuous.
  Bake every shipped size.
- Ship **180px and 90px**; author at 720.
- Every element ships as a **fill** (greyscale, tinted at bake) + an **ink** (black, never tinted).
  Composite all fills bottom-to-top, then all inks on top, or you get doubled lines at seams.
- The 90px bake needs its own **simplified ink** — light interior lines do not survive.
- Use `analysis/portraits/portrait_comic_reference.py` as the build-time baker; numpy is fine there.

### Layer order (both routes)

```
background → background wedge → traps/shoulders → neck → ears → head →
form shadow → cheekbone shelf → jaw shadow → hair → brows → eyes →
nose → mouth → facial hair → damage (scars, swelling) → ink pass
```

---

## 10. Integration points

Replace **four** hand-rolled copies with one renderer:

| Site | Current size | Notes |
|---|---|---|
| `views.py:2898` `draw_fighter_portrait` | 104px | magic coordinates |
| `views.py:1035` `draw_profile_portrait` | 180px | magic coordinates |
| `events.py:3123` (inline) | 98px | magic coordinates |
| `events.py:2245` `draw_intro_portrait` | proportional | **missing status markers** |

```python
render_portrait(canvas, fighter, size=180, ratings_visible=True)
```

This also fixes the divergence — injured/retired seals currently do not render on fight-night
intros. Use `fighter_display_name(fighter)`, not `fighter.name`, so nickname handling matches the
rest of the UI.

Suggested module layout:

```
fighter_portraits/
    __init__.py     # render_portrait, portrait_identity
    identity.py     # hashed vector, override merge
    regions.py      # appearance distributions
    styles.py       # HAIR_STYLES, FACIAL_HAIR, feature tables, DYE
    state.py        # derived state layers
    render.py       # rasteriser + cache
    overrides.py    # PORTRAIT_OVERRIDES
```

---

## 11. Tests

| Test | Asserts |
|---|---|
| Determinism | same `fighter_id` → identical vector across separate processes |
| Shipped manifest | the 1,534 real fighters produce a stable manifest hash |
| No reshuffle | adding a trait leaves every existing trait value unchanged |
| Region distribution | derived skin/hair match the region profile within tolerance |
| **Cosmetic isolation (C3)** | no appearance trait appears in any rating or simulation path |
| Collision rate | < 0.5% of a 5,000-fighter world shares an identical vector |
| Override resolution | every `PORTRAIT_OVERRIDES` key matches a shipped fighter |
| Style coverage | every `hair_style` / `facial_hair` id is reachable and renders |
| Beard containment | no facial-hair mask extends above the nose line |
| Save round-trip | `portrait_identity` survives save/load; legacy saves backfill |
| Existing contracts | `smoke_test.py:1486` retired seal still passes |
| Performance | portrait render + cache hit within budget |

---

## 12. Acceptance criteria

| Metric | Now | Target |
|---|---|---|
| Fighters sharing an identical portrait | **70.7%** | **< 0.5%** |
| Distinct portraits (4,856-fighter world) | 2,630 | > 4,830 |
| Hair styles | 7 | **32** |
| Facial hair options | 5 | **16** |
| Independent facial feature traits | 4 | **11** |
| Dye palettes | 0 | 10, multi-colour |
| Hand-rolled draw sites | 4 | 1 |
| Portraits reflecting age / damage | none | greying, recession, cauliflower, scars |
| Authored real fighters | 0 | ~50 tier 1, ~200 tier 2 |
| Runtime dependencies added | — | **0** |

---

## 13. Build order

1. `styles.py` + `regions.py` + `identity.py` + tests — **no rendering**. Land the model first;
   it is fully testable without a single pixel.
2. Persistence fields, backfill and save round-trip test.
3. `render.py` Route A, plus the cache.
4. Replace the four draw sites with `render_portrait`; verify the retired/injured seals now appear
   on fight-night intros.
5. State layers (greying, recession, cauliflower, scars, swelling).
6. `PORTRAIT_OVERRIDES` tier 1 (~50), plus a contact-sheet dev tool for eyeballing 100 at a time.
7. Only if the art ceiling demands it: Route B baked layers.

Steps 1–2 carry no visual risk and no art dependency. Do not start step 7 without re-reading §9.

---

## 14. Known problems in the reference implementation

Do not copy these:

- `render()` is a single ~200-line function; split it per §10.
- Coordinates are bare float literals throughout (253 of them); name them.
- The hair silhouette is blocky with notch artifacts at the temples — the flank mask needs a
  rounded lower edge rather than a rectangular clip.
- Face construction still does not read convincingly at any size. The identity model, region
  tables, `HAIR_STYLES`, `DYE` and the head width-profile are the parts worth reusing; the feature
  drawing is not.
