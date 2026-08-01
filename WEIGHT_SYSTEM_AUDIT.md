# MMA Warriors — Weight System: Current Logic & Root Cause

Audited against `dist/MMA Warriors/Saves/Game` (month 68, 6,080 active fighters).

---

## TL;DR

**Walk weight is decided before the fighter's division is decided, and never recalculated.**

`create_generated_fighter()` rolls a **uniform random division** (`random.choice(WEIGHTS)`),
computes walk weight from *that* division, and returns. The regional-feeder seeding loops
then **overwrite `.weight`** with the division they actually wanted — leaving the walk weight
belonging to a completely unrelated class.

```python
# seeding.py:2814  (and world.py:10822 — the monthly youth intake)
fighter = self.create_regional_feeder_fighter(region, global_names, gender, feeder_name=name)
fighter.weight = weight          # <-- division overwritten, walk_weight NOT recomputed
```

A fighter born Heavyweight (walk 295) and reassigned to Flyweight stays at **295 lb walking
into a 125 lb division**. That is the 227 lb Featherweight in your screenshot.

---

## Evidence from the `Game` save

**13.0% of all active fighters (793) walk more than 25 lb over their division limit.
792 of those 793 have never moved division** — so this is birth, not movement.

| Division | Limit | n | Median walk | Min | Max | >25 lb over | Under limit |
|---|---|---|---|---|---|---|---|
| Flyweight | 125 | 838 | 133 | 130 | **295** | 205 | 0 |
| Bantamweight | 135 | 807 | 143 | 130 | **295** | 166 | 20 |
| Featherweight | 145 | 772 | 156 | 130 | **295** | 123 | 47 |
| Lightweight | 155 | 807 | 166 | 130 | **295** | 121 | 38 |
| Welterweight | 170 | 763 | 181 | 130 | **295** | 92 | 52 |
| Middleweight | 185 | 724 | 201 | 131 | **295** | 62 | 33 |
| Light Heavyweight | 205 | 659 | 221 | 132 | **295** | 24 | 19 |
| Heavyweight | 265 | 710 | 291 | **132** | 295 | 357 | 26 |

The **medians are all correct** — the generator works. But every division's range is
**130–295**, i.e. the full span of all eight classes, because ~1 in 8 fighters was born in
each class regardless of where they ended up.

### It is concentrated exactly where the buggy code path runs

| Population | n | >25 lb over | Rate |
|---|---|---|---|
| Regional feeders | 1,541 | 669 | **43.4%** |
| Major promotions | 4,238 | 407 | 9.6% |
| `feeder_origin` set | 2,074 | 890 | **42.9%** |
| `feeder_origin` empty | 4,006 | 260 | 6.5% |

Majors are mostly seeded from the real-fighter database (correct hand-authored walk weights),
so they only inherit the bug via free-agent churn and youth intake.

### Reproduced live

Calling `create_regional_feeder_fighter()` 400× then overwriting `.weight` exactly as
`seeding.py:2814` does:

```
252 of 400 (63%) end up >25 lb away from their assigned limit

     born as        walk    reassigned to    over
Light Heavyweight    221     Bantamweight     +86
      Heavyweight    295     Welterweight    +125
     Middleweight    198        Flyweight     +73
      Heavyweight    295  Light Heavyweight    +90
```

### What it does at a weigh-in

```
Gerardo Peña     Flyweight   walk 295 -> limit 126 | cut 169 lb | misses by 109.4 | penalty 22/22
Xavier Gardner   Flyweight   walk 295 -> limit 126 | cut 169 lb | misses by 110.8 | penalty 22/22
```

Penalty is clamped at 22, so these fighters sit permanently pinned at maximum weight-miss
penalty every single time they compete.

---

## The pipeline, step by step

### 1. Walk weight is born — `default_walk_weight()` · `persistence.py:1775`

```python
limit  = WEIGHT_LIMITS[fighter.weight]              # 125/135/145/155/170/185/205/265
spread = 10 if limit <= 135 else 15 if limit <= 170 else 22 if limit <= 205 else 35
if female: spread = max(8, spread - 4)

size_adjust = round((natural_size - 50) / 8)        # ~ -6 .. +6
walk = min(295, limit + max(4, randint(max(5, spread//2), spread) + size_adjust))
```

Correct in isolation — always `limit + 4` or more, capped at 295.
**The problem is what `fighter.weight` is at the moment this runs.**

Called from:
- `seeding.py:1592` — inside `create_generated_fighter`, **before** callers fix the division
- `persistence.py:1367`, `persistence.py:1592` — load-time backfill (only if missing/zero)

### 2. Division is assigned — `create_generated_fighter()` · `seeding.py:2345`

```python
weight = self.game_weight_class(weight) if weight else random.choice(WEIGHTS)   # line ~2386
...
fighter.walk_weight = self.default_walk_weight(fighter)                          # line 1592
```

The function **accepts** a `weight=` argument. Callers that pass it are fine
(`events.py:3618` does). **The feeder path does not pass it:**

```python
# seeding.py:2600
fighter = self.create_generated_fighter(2, 22, 40, 70, gender=gender, region=region, ...)
#                                        ^ no weight= argument
```

**Broken call sites (division set after the fact, walk weight left stale):**

| Site | What it does |
|---|---|
| `seeding.py:2814` | Initial regional-feeder roster build — `fighter.weight = weight` |
| `world.py:10822` | Monthly regional youth intake — `fighter.weight = intake_weight` |
| `seeding.py:833` | `reassign_bamma_closed_division_fighters` → `fighter.weight = "Welterweight"` |

### 3. The weigh-in / cut model — `perform_weigh_in()` · `events.py:3297`
(identical maths duplicated at `world.py:6403` for combat sports)

```python
limit       = WEIGHT_LIMITS[fighter.weight] + (0 if title_fight else 1)
cut_amount  = max(0, walk_weight - limit)

preparation = min(9.0, camp_weeks * 0.82)
            + camp_boost * 0.7
            + camp_quality * 0.025
            + (3.0 if camp_focus == "Weight Management" else 0)

sustainable_cut = 8
                + weight_cutting * 0.15
                + conditioning   * 0.045
                + preparation
                - max(0, natural_size - 55) * 0.1     # big frames cut less

miss_by  = max(0, (cut_amount - sustainable_cut + uniform(-3.0, 2.2)) * 0.75)
penalty  = clamp(0..22,  max(0, cut_amount - sustainable_cut + 5) * 0.7
                       + miss_by * 3
                       + max(0, 3 - camp_weeks) * 0.8)
```

Realistic `sustainable_cut` is ~18–25 lb; theoretical max ~49 lb with elite everything.
A 169 lb cut is ~7× beyond the ceiling, hence the pinned 22/22.

Note the penalty starts accruing at `cut_amount > sustainable_cut - 5`, i.e. cutting within
5 lb of your ceiling already costs you.

### 4. Division-fit "undersized" penalty — `events.py:3051–3086`

```python
def natural_walk_weight_for(fighter, weight):        # events.py:3051
    limit = WEIGHT_LIMITS[weight]
    if weight == "Heavyweight": return limit - 25    # 240 — nobody cuts to 265
    spread = 10 if limit <= 135 else 15 if limit <= 170 else 22
    if female: spread = max(8, spread - 4)
    return limit + max(4, spread // 3)

def division_size_penalty_for(fighter, target_weight):   # events.py:3073
    expected_walk = natural_walk_weight_for(fighter, target_weight)
    size_gap  = max(0, expected_walk - walk_weight)      # how far UNDER the class
    frame_gap = max(0, 55 - natural_size)                # small-framed athlete
    return clamp(0..14, round(size_gap / 4.5 + frame_gap / 16))
```

| Division | Limit | `natural_walk_weight_for` |
|---|---|---|
| Flyweight | 125 | 129 |
| Bantamweight | 135 | 139 |
| Featherweight | 145 | 150 |
| Lightweight | 155 | 160 |
| Welterweight | 170 | 175 |
| Middleweight | 185 | 192 |
| Light Heavyweight | 205 | 212 |
| Heavyweight | 265 | 240 |

### 5. Division-move rules — `weight_class_move_assessment()` · `events.py:3025`

```python
if target_limit < current_limit:                 # MOVING DOWN
    required_cut    = max(0, walk - target_limit)
    sustainable_cut = 9 + cut_skill*0.16 + conditioning*0.04 - max(0, natural_size-55)*0.12
    if required_cut > sustainable_cut + 2:
        return False, "Unsafe cut: ..."          # <-- gated
    return True, "manageable/demanding cut"

else:                                            # MOVING UP
    penalty = division_size_penalty_for(fighter, target_weight)
    if penalty <= 1:
        return True, "Natural move up: ..."
    return True, "Undersized move accepted: {walk} lb walk weight is light for {target}..."
                                                 # <-- NO cut check at all
```

Then `career_weight_move_target()` (`world.py:8060`) decides AI moves; `complete_weight_class_move()`
(`events.py:3249`) applies them — and **never touches `walk_weight`**.

### 6. Growing into a division — `acclimatize_division_fit()` · `events.py:3088`

Runs monthly. If `division_size_penalty > 0`, rolls a chance
(`0.16 + max(0, 30-age)*0.012`, ×0.45 if age ≥ 34) to add **2–5 lb** to walk weight, capped at
`natural_walk_weight_for(division)`, and eases the penalty by ≥1. This part works correctly.
It only ever grows a fighter **up**, never trims one down.

---

## Defects

### 🔴 D1 — Walk weight computed before division is known *(root cause)*
`create_generated_fighter` rolls a random division, derives walk weight from it, and callers
then overwrite `.weight`. **43% of feeder fighters are affected; 13% of the whole world.**

Sites: `seeding.py:2814`, `world.py:10822`, `seeding.py:833`.

### 🔴 D2 — Nothing ever validates or repairs walk weight afterwards
`persistence.py:1592` only fills it in when *missing*. There is no sanity clamp at load, at
signing, or at fight time. The only thing that ever lowers walk weight is the player buying a
nutrition programme (`world.py:830`), which shaves **2 lb**.

### 🟠 D3 — Move-**up** path never checks the fighter can make the target weight
A 227 lb Featherweight moving to Lightweight (155) is waved through as an "undersized move"
because the up-branch only measures *frame fit*, never *required cut*. Moving **down** is
correctly gated; moving up is not. Both directions need the cut check — moving up from 145 to
155 does not help a 227 lb athlete.

### 🟠 D4 — "Undersized" message blames the wrong variable
`division_size_penalty_for` sums two independent terms, but the UI text hardcodes the
walk-weight explanation:

> "Undersized move accepted: **227 lb walk weight is light for Lightweight**."

For that fighter (Atabek Soslanbekov, `natural_size` 29):
- `size_gap  = max(0, 160 - 227) = 0`  ← weight contributed **nothing**
- `frame_gap = max(0, 55 - 29) = 26` → `26/16 = 1.6` → **penalty 2/14**

The entire penalty came from `natural_size`. The message is factually inverted.

**305 fighters in this save are simultaneously >20 lb over their limit and carrying an
"Undersized for X" note.**

### 🟡 D5 — `complete_weight_class_move` leaves walk weight untouched
A genuine move keeps the old walk weight. Fine for a move up (acclimatisation handles it),
but a move down permanently inflates the required cut with no re-validation.

### 🟡 D6 — Weigh-in maths duplicated
`events.py:3309` and `world.py:6428` carry byte-identical `sustainable_cut` formulas. They
will drift. (`natural_walk_weight_for` exists precisely because the size model already drifted
~25 lb once — same trap.)

---

## Fix planning notes

**The one-line class of fix for D1** — pass the division in rather than patching after:

```python
# seeding.py:2598 — thread `weight` through
def create_regional_feeder_fighter(self, region, used_names, gender, feeder_name="", weight=None):
    fighter = self.create_generated_fighter(2, 22, 40, 70, weight=weight, gender=gender, ...)
```
…then have `seeding.py:2814` and `world.py:10822` pass `weight=` instead of assigning `.weight`.

**Suggested belt-and-braces**, since save data is already corrupted:

1. A single `set_fighter_division(fighter, weight, *, recompute_walk=True)` helper that is the
   *only* way `.weight` is ever written — makes D1/D5 structurally impossible to reintroduce.
2. A load-time repair pass: any fighter whose walk weight is outside a plausible band for their
   division gets it regenerated. This save needs it for 793 fighters.
3. Extend the cut check to the move-up branch (D3).
4. Make `division_size_penalty_for` return *which* term dominated, so the message can say
   "small frame for the division" vs "light for the division" (D4).
5. Collapse the two weigh-in copies into one shared function (D6).

**Reproduction script:** `scratchpad/confirm_source.py`
**Full audit script:** `scratchpad/weight_audit.py`
