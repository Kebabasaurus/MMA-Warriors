# Fighter Portrait System — Design Working Document

**Status: working draft, Phase 0 spike complete.** Open questions are marked ❓. Resolved ones are
marked ✅ with the measurement that settled them.

Goal: replace the current abstract initials-badge with portraits that (a) look like *people*,
(b) are unique per fighter, and (c) are byte-identical on every launch, with hand-authored
appearances for real fighters.

---

## 1. Where we are

The current portrait is four Tk canvas shapes — a frame, an accent oval "head", a fixed
`#d7d7d7` polygon torso, and two initials. Per-fighter variation is **two colours and two
initials**, drawn from 9 palettes keyed on `sum(ord(name)) % 9`.

Measured across a full generated world of 4,856 fighters:

| | |
|---|---|
| Distinct visual portraits | 2,630 |
| Fighters sharing a pixel-identical portrait | **3,435 (70.7%)** |
| Worst collision | 11 fighters |

Four separate hand-rolled copies of the drawing code exist (`views.py:2898`, `views.py:1035`,
`events.py:3123`, `events.py:2245`) at 104px, 180px, 98px and proportional. Only the last scales;
the first three use magic coordinates. They have already diverged — injured and retired seals do
not render on fight-night intros.

---

## 2. The three requirements, and which are actually hard

| Requirement | Difficulty | Why |
|---|---|---|
| Deterministic across launches | **Already solved** | see §3 |
| Unique per fighter | **Easy** | a feature vector with ~10 traits gives ~10⁷ combinations |
| Looks like a fighter | **The whole problem** | everything below §4 is about this |

Uniqueness is trivial and we should not congratulate ourselves for it. Randomised trait soup
produces 4,856 unique portraits that all look equally like nobody. **The design goal is
recognisability, not entropy.**

---

## 3. Determinism is free — use `fighter_id`, not `name`

All 1,534 real fighters in the shipped database already carry a stable identity:

```
FTR-DU-19bd9f3592ef562c814d37fa7f467707  ->  Tony Ferguson
```

`deterministic_source_fighter_id` (`models.py:16`) builds it as **UUID5 of
database_type + name + owner + placement**. It is reproducible from the data, not random, so
anything derived from it is identical on every launch, machine and new save.

Generated fighters get a random `uuid4` that is persisted — stable within a save, different in a
new world, which is the behaviour we want.

**Decision: hash `fighter_id`.** The current `name` key is wrong on two counts — renames shift a
portrait, and `sum(ord)` is order-independent so `"Jon Jones"` and `"Jones Jon"` collide (verified).

Use a stable hash with good avalanche — `zlib.crc32` or `hashlib.blake2b` over
`f"{fighter_id}|{trait_name}"`, one independent draw per trait, so adding a trait later does not
reshuffle existing ones. This matters: a naive "one hash, consume bits sequentially" scheme
restyles every fighter the moment a trait is inserted.

---

## 4. Identity vector vs state layers

The single most important structural idea in this document.

**A fighter's appearance splits into two halves that behave completely differently:**

| | Immutable identity | Derived state |
|---|---|---|
| Examples | skin tone, bone structure, eye shape, nose, ear shape, base hair colour | greying, hairline recession, scar tissue, cauliflower ear, weight/puffiness, cuts, black eye |
| Source | hashed from `fighter_id`, conditioned by region (§5) | computed at render time from `age`, `career damage`, `record`, `injured`, weight class |
| Storage | **persisted once** on the Fighter | **never stored** — recomputed every draw |
| Changes over a career | never | continuously |

This gives us something no palette system can: **a fighter visibly ages and accumulates damage
across a 15-year career** while remaining recognisably the same person. A 22-year-old debutant
and the same fighter at 38 with 40 bouts share bone structure and colouring but differ in
greying, scar tissue, cauliflower and hairline.

That is the feature that makes this worth building rather than just widening the palette list.

❓ **Open:** should state layers be capped so a veteran does not become grotesque? Proposal: each
state layer has a max intensity and they saturate rather than stack linearly.

---

## 5. Appearance must be region-conditioned, not uniformly random

A pure hash produces Nigerian fighters with pale skin and blond hair. That is both visually wrong
and a representation problem we should not ship.

The game already models this well: `REGIONS` (13), `REGION_IDENTITY_PROFILES` mapping each region
to countries and nationalities, plus per-fighter `birth_region`, `nationality`, `hometown`,
`fighting_base`.

**Design: the hash selects *within* a region-conditioned distribution, not across the global
space.**

```
appearance_profile(region, nationality) -> weighted distributions over
    skin_tone       (8 steps)
    hair_colour     (8)
    hair_texture    (5)
    eye_colour      (5)
    facial_structure(5)
```

Then `trait = weighted_pick(distribution, hash(fighter_id, trait_name))`.

### Guardrails — deliberate, and non-negotiable

1. **Distributions are wide, never single-valued.** Every region gets a broad range. No region
   maps to one appearance; real populations are diverse and the game's rosters are international.
2. **Nationality refines, never overrides.** A Brazilian fighter draws from Brazil's distribution,
   which is itself broad.
3. **No appearance trait ever touches ability, rating, popularity or any simulation value.** Purely
   cosmetic, and enforced by a test.
4. **No caricature.** Traits are anatomical ranges (tone, texture, structure), never cultural props,
   and never region-specific "features".
5. **Authored overrides always win** over derived values, so any bad derivation is correctable.
6. **Migration/diaspora is normal.** `birth_region` drives appearance; `fighting_base` does not.
   A fighter born in Nigeria fighting out of the UK draws from Nigeria.

### ✅ Resolved by inspecting the shipped database

`birth_region` is **absent from all 1,534 shipped fighters**. What they actually carry, on 100% of
records, is `birth_country`, `nationality`, `region` and `hometown`.

**Resolution order: `birth_country` → `nationality` → `region`.** This is both more specific than
region and matches the order `country_flag_path_for_fighter` (`views.py:1637`) already uses, so
the two systems agree. `birth_region` stays as a last-resort fallback for generated fighters.

---

## 6. Art pipeline — the real fork

I tested this rather than assuming. **Tk 8.6.15 supports alpha layer compositing with no PIL:**

```python
root.tk.call(base, 'copy', layer, '-to', 0, 0, '-compositingrule', 'overlay')
```

PNG load, per-pixel `put`, and `transparency_get` all work. So authored raster art is on the table
without adding a dependency.

| | Vector (Tk canvas shapes) | **PNG layer compositing** |
|---|---|---|
| Art ceiling | low — ovals and polygons | **high — real illustration** |
| Scaling | any size, free | **integer subsample only** |
| Assets | none | ~100–160 PNGs |
| Build | nothing | bundle a folder (precedent: `country_flags` already bundled in both specs) |
| Where logic lives | all in code | thin code, art in assets |
| Iteration | code change | drop in a PNG |

**Recommendation: PNG layers.** "Fighter-like" is the actual request, and Tk canvas primitives
will never get there — we would be building a worse version of the thing we already have.

### The constraint that follows

`PhotoImage` scales by **integer factors only** (`zoom` / `subsample`). Current portrait sizes are
98, 104 and 180 px — none are integer-related.

**Decision: standardise portrait sizes.** Author at **360px**, ship at 360 → subsample 2 → 180,
3 → 120, 4 → 90. Adopt **180 / 120 / 90** as the three UI sizes. This means changing three call
sites' canvas dimensions, which we want to do anyway when unifying them (§8).

❓ **Open:** is 360px master the right authoring size, or do we need a 720 master for a future
high-DPI/large profile view? Cheap to decide now, expensive later.

### Asset count is additive, not multiplicative

Layers compose, so the asset count is the *sum* of options per layer, not the product:

| Layer | Options | ×2 for gender? |
|---|---|---|
| Base head + skin tone | 8 | yes |
| Facial structure | 5 | yes |
| Eyes / brow | 5 | shared |
| Nose | 4 | shared |
| Mouth / jaw | 4 | shared |
| Ears (incl. cauliflower states) | 3 × 3 | shared |
| Hair style × colour | 12 + 8 tint | yes |
| Facial hair | 6 | male only |
| Body / neck build | 4 | yes |
| Scars, cuts, marks | 8 | shared |
| Kit / background | 24 tints | shared |

Roughly **110–160 PNGs** for full coverage. Colour variants are tints applied at composite time
rather than separate files where possible.

### ✅ Phase 0 spike — resolved

Measured on Tk 8.6.15:

```
overlay composite, one layer      0.25 ms   ->  10-layer portrait = 2.5 ms   viable
bulk put, full 360x360          121.9 ms   ->  runtime tinting NOT viable
per-pixel get, full 360x360       0.2 s    ->  runtime masking  NOT viable
PNG export (PhotoImage.write)     6.6 ms   ->  works
```

**Runtime tinting and runtime masking are both dead.** Compositing pre-coloured layers is fast
enough to be free (2.5 ms per portrait).

**But PNG export works, which resolves the asset budget favourably:** colour variants are *baked
at build time* from greyscale masters by a script, not hand-authored. numpy is already an optional
dependency used by the audio path and pyinstaller is already build-only, so a build-time baking
script may use numpy freely — the runtime renderer stays stdlib-only.

Revised budget: **~30–40 hand-drawn greyscale masters**, expanded by the baking script to the
~110–160 shipped PNGs. That is a tractable commission.

---

## 6b. Procedural prototype — built, measured, and it does not clear the bar

A full working prototype is committed at `analysis/portraits/portrait_prototype.py`, with output at
`analysis/portraits/procedural_prototype_contact_sheet.png` (48 real fighters from the shipped
database, rendered at 200px).

**What it proves works:**

- the identity-vector pipeline end to end — hash `fighter_id`, condition by region, compose layers;
- **skin tone and hair colour distributions read correctly** and vary convincingly across the roster;
- state layers work — greying, hairline recession, cauliflower and scar tissue all respond to age
  and career length;
- determinism — same `fighter_id` renders identically every run;
- collisions are gone at the vector level.

**What it proves does not work:** procedural ellipse-stacking does not produce faces that read as
people. After two iterations the hair still renders as a band or cap rather than hair, features sit
in an uncanny middle ground, and the portraits read as *generic avatars* rather than *fighters*.
That is not a tuning problem — it is the ceiling of composing primitives without an artist.

### ✅ This resolves open question 3: skip the interim procedural art

Do **not** ship a procedural-vector Phase 2 as an interim step. It cannot meet the stated bar
("should look like people"), and the effort does not transfer to the layer pipeline. Keep the
prototype as a harness for the identity model and go straight to authored layers.

**What does transfer, and should be kept verbatim:** the identity vector, the region-conditioned
distributions, the immutable/state split, the per-trait independent hashing, and the contact-sheet
tooling — all of which are art-independent and already working.

Follow the existing pattern — `real_sport_profiles.py:200` already does exactly this shape with
`PRIME_AGE_OVERRIDES`, a name-keyed dict of hand-authored values.

```python
PORTRAIT_OVERRIDES = {
    "Jon Jones":       {"skin": 4, "hair": "short_fade", "facial_hair": "none",
                        "build": "tall_rangy", "ears": "cauliflower_light"},
    "Conor McGregor":  {"skin": 1, "hair": "swept_back", "facial_hair": "full_beard",
                        "tattoo": "chest"},
}
```

Merged over the derived vector, so an author writes only what matters and the rest stays hashed.

### Tiering — 1,534 real fighters cannot all be authored

| Tier | Count | Treatment |
|---|---|---|
| 1 — Icons | ~50 | fully authored, every layer specified |
| 2 — Well known | ~200 | partial: skin, hair, facial hair, build |
| 3 — Everyone else | ~1,280 | fully derived |

❓ **Open:** key overrides by `name` (matches `PRIME_AGE_OVERRIDES`, readable, breaks on rename) or
by `fighter_id` (stable, unreadable)? Proposal: **name**, with a test asserting every override key
resolves to a real fighter in the shipped database, so a rename fails CI loudly instead of
silently dropping the override.

---

## 8. Code structure

One module, one renderer, replacing four hand-rolled copies.

```
fighter_portraits/
    __init__.py        # public API: portrait_vector(fighter), render_portrait(canvas, fighter, size)
    identity.py        # hashed immutable vector, region-conditioned
    state.py           # derived state layers from age / damage / record
    regions.py         # appearance distributions per region and nationality
    overrides.py       # PORTRAIT_OVERRIDES for real fighters
    render.py          # layer composition, caching, vector fallback
    validation.py      # asset completeness, override resolution, determinism
assets/portraits/      # authored PNG layers, bundled like country_flags
```

Replace all four draw sites with:

```python
render_portrait(canvas, fighter, size=180, ratings_visible=True)
```

This also fixes the divergence: status markers (injured / retired seals) render everywhere,
including fight-night intros where they are currently missing.

**Use `fighter_display_name(fighter)`**, not `fighter.name`, so nickname handling matches the rest
of the UI.

### Caching

Composited images should be cached by `(fighter_id, size, state_signature)` where
`state_signature` is a short hash of the state-affecting attributes. Portraits render 1–2 at a
time in the profile card and fight-night corners, so cost is low — but the Database Editor and any
future roster grid could ask for many at once.

❓ **Open:** does anything want a portrait *per table row*? Today all list views are ttk Treeviews
with no images. If a future roster grid wants 50 portraits, caching strategy matters much more.

---

## 9. Storage and migration

Persist the **identity vector only** (state is always recomputed), plus a generator version:

```python
portrait_version: int = 0        # mirrors the existing career_arc_version pattern
portrait_identity: dict = {}     # {"skin": 4, "hair": "short_fade", ...}
```

Backfill in the same place the current palette is backfilled — `persistence.py:1860`, which
already fills `portrait_bg` / `portrait_accent` only when empty.

**Versioning rule:** bumping the generator must not restyle existing fighters. A fighter with
`portrait_version < CURRENT` keeps their stored vector unless explicitly migrated. Otherwise every
art change silently rewrites everyone's roster, which players will notice and dislike.

Keep `portrait_bg` / `portrait_accent` as the vector-fallback palette so old saves and missing
assets still render something.

---

## 10. Testing

| Test | Asserts |
|---|---|
| Determinism | same `fighter_id` → identical vector, across separate processes |
| Determinism, real fighters | the 1,534 shipped fighters produce a stable manifest hash |
| No reshuffle | adding a trait does not change any existing trait's value |
| Region distribution | derived skin/hair distributions match the region profile within tolerance |
| Cosmetic isolation | no appearance trait appears in any rating, ability or simulation path |
| Collision rate | < 0.5% of a 5,000-fighter world shares an identical vector |
| Override resolution | every `PORTRAIT_OVERRIDES` key matches a fighter in the shipped database |
| Asset completeness | every layer id referenced by code or overrides exists as a file |
| Fallback | missing assets fall back to vector rendering without raising |
| Existing contracts | `smoke_test.py:1486` retired seal `#315a70` + "RTD" still passes |

---

## 11. Phasing

| Phase | Work | Ships | Status |
|---|---|---|---|
| **0** | Spike: Tk compositing, tinting, PNG export | asset budget settled | ✅ **done** |
| **0b** | Procedural prototype + contact sheet | proved the identity model, ruled out procedural art | ✅ **done** |
| **1** | Unify the four draw sites behind `render_portrait`, keep current art | no visual change, removes duplication, fixes missing seals | ready |
| **2** | Identity vector + region profiles + persistence + tests — **no new art** | model landed and tested, still drawn with the current badge | ready |
| **3** | Art commission: ~30–40 greyscale masters + build-time baking script | the asset set | **blocked on an artist** |
| **4** | PNG layer renderer + size standardisation to 180/120/90 | **portraits look like people** | after 3 |
| **5** | State layers wired to the renderer — ageing, scars, cauliflower | fighters visibly age across a career | after 4 |
| **6** | `PORTRAIT_OVERRIDES` tier 1 and 2 + contact-sheet preview tool | real fighters recognisable | after 4 |

Phases 1 and 2 are pure engineering, carry no art dependency, and can start now. **Phase 3 is the
critical path and it is a commission, not a code task.**

---

## 12. Honest limits

- These will be **stylised avatars, not likenesses.** Real fighters will be identifiable by
  silhouette, colouring, build and authored details — not by looking like photographs.
- **Art is the bottleneck, not code — now demonstrated rather than asserted.** The prototype in
  `analysis/portraits/` implements the entire model in ~300 lines and still does not look like
  people. The engineering is maybe a week; a coherent layer set is the long pole and needs someone
  who can draw.
- **Tk is not an image library.** No rotation, no free scaling, no blend modes beyond overlay. The
  art must be authored to composite cleanly at fixed sizes with no transforms.
- We should not ship real fighters' likenesses even if we could — stylised, clearly-illustrated
  avatars are the right call for a game shipping real names.

---

## 13. Decisions still needed

Resolved by the Phase 0 spike and the prototype: the asset budget (§6), the region keying (§5), and
whether to ship interim procedural art (§6b — no).

Still open:

1. **Who is producing the art, and at what cadence?** This sets the whole timeline. Nothing in
   Phases 3–6 can start without it, and no amount of engineering substitutes for it.
2. Master authoring size — 360 or 720? Cheap now, expensive later. (§6)
3. Override key — name or `fighter_id`? (§7)
4. Does anything need portraits per table row? Changes the caching strategy materially. (§8)
5. Art direction: what *style*? Flat vector illustration, semi-realistic painted, or comic/cel?
   This should be settled with the artist before masters are drawn, because the layer decomposition
   depends on it.
