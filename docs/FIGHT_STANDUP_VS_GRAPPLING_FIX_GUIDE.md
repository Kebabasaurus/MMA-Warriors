# Fight Engine — Stand-Up, Grappling Balance & Commentary Fix Guide

Audited against `fight_engine.py` @ `eb6bc87` (3.0.8) using instrumented headless simulations:
400 fights for action/position distribution, 400 for segment analysis, 300 for striking output,
250 for per-beat impact and volume spread, 200 for intra-round drift, 150 for per-category
commentary repetition. All fights were same-division roster pairs from a fresh `FightEmpireApp`
world, with the engine monkeypatched rather than modified.

Companion document: `docs/FIGHT_DAMAGE_AND_CLINCH_AUDIT.md` describes the *intended* behaviour.
This guide records where the implementation diverges from it and how to correct it.

> ⚠️ **Version drift.** Parts 1–6 were measured against 3.0.8 (`eb6bc87`, 3,238 lines). The main
> checkout now holds an uncommitted engine rewrite of **7,287 lines** on top of `dev`
> (`f76037c`, 3.0.9) that adds a full named-move system. **Part 7 audits that current working
> copy; Parts 1–6 need re-verification against it before their fixes are applied.** Several of
> them — old Fixes 11, 18, 19 and 23 — are already addressed by the rewrite. Others, including
> the Part 1 position ratchet and the dead `pocket` range, measurably survive it.

---

## TL;DR

Five separate problems, all real:

1. **The round is a one-way ratchet toward the mat.** Entering the clinch or the ground is
   cheap, leaving is nearly impossible, and nothing but the round horn resets position. A round
   starts 100% standing and decays to ~18% standing by its midpoint. *(Part 1)*
2. **A third of all play-by-play text comes from hardcoded three-line lists, not the phrase
   banks** — and those lists cover exactly the stalling actions the ratchet makes most frequent.
   The `fight_phrase` banks themselves are mostly fine. *(Part 2)*
3. **The stand-up that remains is thin.** Strikes land 74.6% of the time because the miss gate
   sits below the margin distribution; punches have no anatomy while kicks do; there is no
   counter game, no pocket range, and a knockdown does not produce a downed fighter. *(Part 3)*
4. **The commentary is flavourless because selection ignores the simulation.** Standing, the
   engine computes a 12-fold spread in impact and a 7-fold spread in strikes-per-beat, then
   draws its line with a flat `random.choice` that knows none of it *(Part 4)*. On the ground it
   is worse: 46 distinct named submissions are simulated and **7.5%** of attempts show the name,
   while every sustained-position category is position-blind *(Part 5)*.

5. **Two fights in three end early.** The finish rate is 67.9% against a real-world 47–52%, with
   submissions at nearly double their real share — while Doctor Stoppage, Injury Stoppage and
   round 4–5 finishes are all mathematically unreachable. *(Part 6)*

Part 1 makes the fight stay standing. Part 3 makes that worth watching. Parts 4 and 5 make it
read that way. Part 6 decides how it ends. Do them in that order, but read Part 3 first — some
of it changes what Part 1 should be tuned against, and **do not tune Part 6's balance numbers
until Parts 1 and 3 have landed**, because both change every input those formulas read.

Note that Part 2 and Parts 4–5 fix *different* commentary defects. Part 2 is repetition: the
same sentence appearing 99 times. Parts 4 and 5 are flatness: every sentence describing the same
imaginary event no matter what the engine simulated. Fixing one does not fix the other.

Two of the flatness fixes are also **correctness** fixes — the text currently contradicts the
simulation. Ground-strike lines name a position the fighters may not be in (Fix 25), and
submission lines say "attacks the neck" about heel hooks and kneebars (Fix 23).

```
Position share by tick within a round (18 ticks/round, 200 fights):

tick  1: standing 100.0%   clinch  0.0%   ground  0.0%
tick  4: standing  38.3%   clinch 28.8%   ground 32.8%
tick  8: standing  27.0%   clinch 22.4%   ground 50.5%
tick 13: standing  18.4%   clinch 17.4%   ground 64.2%
tick 18: standing  23.6%   clinch 19.2%   ground 57.2%
```

---

# Part 1 — Position Balance

## Measured Baseline

### Time allocation (12,778 decision ticks, 400 fights)

| Phase | Engine | Real-sport target |
|---|---|---|
| Standing at range | **33.9%** | 62–70% |
| Clinch / cage | 19.6% | 8–12% |
| Ground | **46.5%** | 18–25% |

The 33.9% standing figure is inflated by the forced `state["position"] = "range"` at every round
start (`fight_engine.py:139`). Excluding tick 1, true standing time is ~29%.

### Action selection (share of all decisions)

```
survive            17.5%     ground_control      5.9%
submission          8.4%     dirty_boxing        5.4%
jab                 8.0%     shoot               5.2%
advance_position    7.1%     power_punch         5.2%
clinch              6.5%     cling               4.8%
ground_strikes      4.3%     takedown            3.5%
cage_control        3.3%     kick                3.1%
break_clinch        3.1%     stand_up            2.6%
recover_guard       2.1%     sweep               2.0%
bottom_submission   2.0%

Grouped:  ground 39.3% | clinch 21.7% | survive 17.5% | striking 16.3% | shots 5.2%
```

### Actions chosen while standing at range

```
jab          24.0%
clinch       19.3%   <- grappling entry
survive      17.0%
shoot        15.7%   <- grappling entry
power_punch  14.6%
kick          9.4%
```

**35% of standing decisions are attempts to stop striking.**

### Segment durations

| Metric | Value |
|---|---|
| Shot/takedown yields position (ground or fence control) | **82.8%** |
| — completed takedown | 62.3% |
| — failed, but shooter gets cage control | 20.5% |
| — stuffed back to range | 17.2% |
| Average completed ground segment | **11.6 ticks ≈ 3:05 of unbroken mat time** |
| Ground segments ended by the bottom fighter standing up | 64.1% |
| Ground segments ended by referee stand-up | 35.9% |
| Referee stand-ups per fight | **0.23** |
| Average clinch segment | 2.7 ticks |
| Clinch segments ending in a takedown attempt | 46.6% |

Per-tick escape probability from the ground is **~2.8%**, giving an expected ground segment of
~36 ticks (~9.5 minutes). Only the round horn prevents that from playing out.

---

## Root Causes And Fixes

Ordered by measured impact. Apply 1–4 first; they move position share on their own. Re-measure
before touching 5–6.

### Fix 1 — Takedowns are too cheap (highest impact)

**Site:** `resolve_takedown`, `fight_engine.py:2787`

```python
if margin > 8:                       # completes the takedown
    ...
if margin > -8:                      # <-- FAILED shot still awards fence control
    state["position"] = "cage"
    state["clinch_controller"] = actor.name
    round_stats[actor.name]["control"] += 2
    return self.fight_phrase("takedown_cage", actor, defender)
```

A 16-point margin band converts stuffed shots into cage control *for the shooter*. Combined with
the low completion bar, a shot yields position 82.8% of the time.

**Change:**

- Raise the completion bar: `margin > 8` → `margin > 18`.
- Narrow the consolation band: `margin > -8` → `margin > -2`, and award the clinch only when the
  shooter genuinely has a grip — gate it on `self.ds(actor, "chain_wrestling", actor.wrestling)`
  beating the defender's `sprawl`. Otherwise fall through to the stuff branch.
- Give the stuff branch a cost: bank `impact` for the sprawling fighter and drain gas from the
  shooter, so a failed shot is a real risk rather than a free reposition.

**Target:** takedown completion 35–42%; shot-yields-position ≤ 55%.

---

### Fix 2 — The top fighter can never disengage

**Site:** `choose_action`, top-position branch, `fight_engine.py:1013-1023`

```python
weights = {
    "ground_control": ...,
    "ground_strikes": ...,
    "advance_position": ...,
    "submission": ...,
}
```

All four options keep the fight on the mat. There is no equivalent of a striker standing back
up or waving the opponent up.

**Change:** add a fifth option —

```python
"disengage": self.ds_avg(fighter, ("striking", "mobility", "fight_iq", "conditioning"),
                         fighter.striking) * 0.55,
```

Weight it up hard for striking styles and behaviours (`Sprawl And Brawl`, `Boxer`, `Kickboxer`,
`Karate`, `Taekwondo`, `Muay Thai`, `Dutch Kickboxer`) and down for `Control`,
`Submission Hunter`, and the wrestling/BJJ styles via `STYLE_BIAS["top"]`
(`fight_engine.py:872`). Resolve it in `resolve_exchange` by returning both fighters to `range`
with no control credit, and add a `disengage` phrase category.

---

### Fix 3 — There is no scramble

**Sites:** `resolve_exchange` `stand_up` branch (`fight_engine.py:2231`), `sweep` branch
(`fight_engine.py:2222`)

```python
if action == "stand_up":
    if margin > 5:
        state["position"] = "range"
        ...
    round_stats[defender.name]["control"] += 2
    return self.fight_phrase("mat_return", actor, defender)   # binary: up, or pinned
```

`stand_up` is binary and a won `sweep` never returns to the feet — it only flips who is on top.
Real fights resolve most ground exchanges through scrambles that end standing.

**Change:**

- `stand_up`: add a middle band. `margin > 5` stands up cleanly; `-6 < margin <= 5` produces a
  scramble that *also* ends at `range` but awards the defender a control tick and costs the
  actor gas; only `margin <= -6` is a mat return.
- `sweep`: on a high margin (`margin > 22`), route to `range` as a scramble-to-the-feet instead
  of a top-position flip, weighted by the actor's `scrambles` skill.

**Target:** ground escape probability ≥ 8% per tick; average ground segment ≤ 5 ticks (~80s).

---

### Fix 4 — The referee stand-up never fires

**Site:** `update_ground_inactivity`, `fight_engine.py:417`

```python
active = {"ground_strikes", "advance_position", "recover_guard", "submission",
          "bottom_submission", "sweep", "stand_up"}
```

This set contains the actions chosen *most* of the time, so the inactivity counter resets almost
every tick and the 4–7 tick threshold is effectively unreachable. Result: **0.23 stand-ups per
fight**, while 35.9% of ground exits depend on this path.

**Change:** count *productive* work, not *attempted* work.

- Remove `recover_guard` and `bottom_submission` from `active` — both are commonly stalling.
- Make `submission`, `sweep`, and `advance_position` reset the clock **only on success**: set a
  `state["ground_progress"] = True` flag inside the successful branches of
  `resolve_position_move`, `resolve_submission`, and the `sweep` handler, and read that here
  instead of the raw action name.
- Keep `ground_strikes` resetting the clock only when the strike lands.

**Target:** 0.8–1.5 referee stand-ups per fight.

---

### Fix 5 — The clinch has no referee separation (`clinch_ticks` is dead state)

**Sites:** written at `fight_engine.py:2200`; reset at `:2173`, `:2181`, `:2191`, `:2210`,
`:2216`; initialised at `:69` — **never read anywhere in the file.**

There is no cage-stalling timeout at all, and 46.6% of clinch segments feed straight into a
takedown attempt.

**Change:** mirror the ground logic. Add `update_clinch_inactivity` (or extend
`update_ground_inactivity`): when the position is `clinch`/`cage` and `clinch_ticks` exceeds a
referee-dependent threshold (4 cautious → 7 late) with no landed strike, completed takedown, or
reversal, break to `range`, clear `clinch_controller`, and emit a new `ref_separation` line.
Reset `clinch_ticks` on any of those productive events.

Note that `dynamic_flavor_line` already promises this behaviour in text —
*"The referee watches the clinch closely, ready to break it if it stalls."*
(`fight_engine.py:815`) — while the engine never does it.

---

### Fix 6 — Range weights and style bias skew toward entries

**Sites:** `choose_action` range branch (`fight_engine.py:923`), `STYLE_BIAS`
(`fight_engine.py:832`)

`shoot` and `clinch` sit in the same weight pool as three striking options with comparable base
values, and `STYLE_BIAS["range"]` has ten grappling styles boosting `shoot` up to ×1.68 against
roughly seven striking styles damping it to ×0.62–0.85 — an asymmetric net push toward the mat
across the whole roster.

**Change:**

- Apply a flat ×0.78–0.82 to base `shoot` and `clinch` in the range pool.
- Cap grappling-style `shoot` multipliers at ~×1.35 (currently up to ×1.68 for
  `Freestyle Wrestler`).
- Strengthen the counter-signal at `fight_engine.py:975`: when `opponent.takedown_defence`
  clearly beats the actor's wrestling and the actor has fight IQ, damp `shoot` — currently only
  `kick` is damped in the mirror case.
- Make repeated failed shots self-limiting: track `state["failed_shots"][name]` and decay the
  `shoot` weight after two stuffs in a round.

---

## Position Targets

| Metric | Now | Target |
|---|---|---|
| Standing at range | 33.9% | 60–68% |
| Clinch / cage | 19.6% | 10–14% |
| Ground | 46.5% | 20–26% |
| Standing at tick 13 of a round | 18.4% | ≥ 50% |
| Takedown completion rate | 62.3% | 35–42% |
| Shot yields position | 82.8% | ≤ 55% |
| Average ground segment | 11.6 ticks | ≤ 5 ticks |
| Referee stand-ups per fight | 0.23 | 0.8–1.5 |
| Striking share of decisions | 16.3% | 32–40% |

Watch the method mix while tuning — see Part 6 for the full finish audit and its targets.
Submissions and ground TKOs should fall as mat time falls. Note that the current finish rate is
**67.9%** against a real-world 47–52%, so a drop in total finishes here is a *correction*, not a
regression; do not compensate for it in the position model.

---

# Part 2 — Duplicate And Repeated Exchanges

## The short answer

**No, the phrase banks are not the main problem — the hardcoded lists are.**

Across 150 fights: 6,142 play-by-play lines, 1,368 distinct, **22.3% uniqueness**.

| Source | Share of lines | Distinct lines | Uses per line |
|---|---|---|---|
| `fight_phrase` banks | 64.6% | 1,174 | **3.4** |
| Hardcoded `random.choice([...])` lists | **35.4%** | 194 | **11.2** |

The banks (57 base categories + 62 expansion categories) are broadly healthy: `jab_land` has 96
variants, `pass` 89, `round_start` 76, `power_land` 72. The inline lists scattered through
`fight_engine.py` have three to five variants each and fire constantly, because they cover
exactly the stalling actions Part 1 makes over-frequent.

Every one of the top 20 repeated lines comes from a hardcoded list:

```
99x  X shrugs off the submission attempt and settles back on top.
61x  X's corner wants the leg kick set up behind the hands.
56x  X's cornerman calls for more feints before committing.
56x  X buries their head on the chest in the clinch and catches a breath.
55x  You can hear X's corner between beats: "Hands up, back behind the jab!"
54x  X ties up the hands from underneath and slows the exchange down.
54x  X closes space from bottom, controls the wrists, and waits for a chance to improve.
53x  X's coach is barking for the body-head combination.
53x  X clings on in the clinch, slowing everything down to recover.
51x  X stays heavy on top and steadies the pace for a moment.
50x  X rides the position, catching a breather while staying busy enough to hold it.
49x  X leans into the clinch and uses the tie-up to recover.
48x  X pins the tie-up against the fence to steal a moment of rest.
47x  X walks X to the fence, settles head position, and locks the hands.
47x  X settles their weight and takes a breath without giving up top position.
47x  "Circle out, don't sit on the fence!" comes the shout from X's corner.
46x  X keeps a tight guard from the bottom and rides out the pressure.
45x  X stays defensively responsible and keeps talking to the referee.
43x  "Double the jab, then move!" - X's coach is dialed in.
41x  X postures just enough to keep control while recovering.
```

There are **23** `random.choice([...])` sites in `fight_engine.py`.

---

## Fix 7 — Promote the hardcoded lists into phrase categories

Highest-value first. Each of these should become a `fight_phrase` category with entries in both
`fight_phrase` and `mma_striking_commentary_expansion`.

| Site | Current | Uses /150 fights | New category | Target size |
|---|---|---|---|---|
| `resolve_submission` bottom-sub reversal, `:2880` | **1 line** | **99** | `submission_reversed` | 18 |
| `resolve_exchange` ground `survive`, top, `:2254` | 4 lines | ~150 | `survive_ground_top` | 15 |
| `resolve_exchange` ground `survive`, bottom, `:2260` | 4 lines | ~150 | `survive_ground_bottom` | 15 |
| `resolve_exchange` clinch `survive`, `:2267` | 4 lines | ~210 | `survive_clinch` | 15 |
| `resolve_exchange` repeat cage control, `:2203` | 3 lines | ~100 | `cage_control_hold` | 15 |
| `fighter_presence_line` hurt / gassed / ground / neutral, `:697-718` | 3 lines each | ~300 total | four `presence_*` categories | 12 each |
| `dynamic_flavor_line` corner-shout pool, `:790` | 6 lines | ~330 | `corner_shout` | 24 |
| `dynamic_flavor_line` range pool, `:798` | 9 lines | ~200 | `range_flavor` | 22 |
| `dynamic_flavor_line` clinch pool, `:810` | 6 lines | ~120 | `clinch_flavor` | 18 |
| `update_ground_inactivity` warning / stand-up, `:433`, `:448` | 5 / 4 lines | ~90 | `ref_activity_warning`, `ref_standup` | 10 each |
| `resolve_strike` clinch detail lists, `:2708-2736` | 3–4 lines each | ~130 | fold into `dirty_boxing_land` | +12 |

The corner-shout pool needs special attention beyond size: it is gated on
`actor.professionalism > 68 or discipline > 66` (`fight_engine.py:789`), so the same
high-discipline fighters trigger it every fight. Add a per-fight or per-round cooldown in
`dynamic_flavor_line` so no single flavour category repeats within ~4 ticks.

---

## Fix 8 — Widen the genuinely thin bank categories

Measured over 150 fights. Anything above ~4 uses per line reads as repetitive in a watched
fight.

| Category | Uses | Bank | Uses/line | Target bank |
|---|---|---|---|---|
| `cling` | 261 | 31 | 8.4 | 55 |
| `break_clinch` | 145 | 25 | 5.8 | 40 |
| `survive` | 294 | 52 | 5.7 | 85 |
| `submission_defended` | 219 | 44 | 5.0 | 65 |
| `stand_up` | 74 | 15 | 4.9 | 35 |
| `clinch_entry` | 284 | 58 | 4.9 | 75 |
| `top_control` | 298 | 64 | 4.7 | 95 |
| `takedown_cage` | 102 | 23 | 4.4 | 35 |
| `recover_guard` | 61 | 14 | 4.4 | 30 |
| `round_start` | 327 | 76 | 4.3 | 95 |
| `ref_intervention` | 60 | 15 | 4.0 | 25 |
| `takedown_denied` | 61 | 18 | 3.4 | 30 |
| `sweep` | 53 | 16 | 3.3 | 30 |
| `pass_denied` | 31 | 11 | 2.8 | 25 |
| `hold_position` | 52 | 20 | 2.6 | 30 |

Adequate already, no work needed: `pass` (89), `jab_land` (96), `power_land` (72),
`takedown_complete` (64), `ground_strikes_land` (63), `knockdown` (66), `submission_danger` (54),
`decision` (45), `mat_return` (31), `slam_takedown` (26), `high_kick_land` (26), `sweep_denied`
(25), `body_kick_land` (24), `jab_miss` (22).

**Miss and defence lines are the thinnest striking gap.** `teep_miss` has 2 variants,
`kick_miss` 4, `power_miss` 7, `ground_strikes_miss` 8, `high_kick_checked` 3,
`low_kick_checked` 5, `body_kick_checked` 5. These fire rarely today only because striking
itself is rare — after the Part 1 fixes triple standing time, they will be very visible. Take
each to 15–18 before shipping the position changes.

**Ordering note:** the Part 1 fixes cut ground and clinch action frequency by roughly half, which
halves the pressure on `cling`, `top_control`, `survive`, and the clinch categories. Do Part 1
first, re-measure, and the required additions in the table above will shrink. The striking miss
and check categories move the other way — they get *more* exposure, so widen those regardless.

---

## Fix 9 — Structural anti-repetition

Independent of bank size, and cheap:

- `fight_phrase` currently picks with an unguarded `random.choice`. Add a per-fight recent-use
  memory in `state` (last 3–5 picks per category) and re-roll against it. This alone lifts
  perceived variety more than doubling a bank does, because back-to-back repeats are what the
  player notices.
- `add_fight_line` in `simulate_fight` (`fight_engine.py:119`) deliberately keeps every generated
  call, including exact duplicates. Keep that policy for the log, but suppress a line that is
  byte-identical to the immediately preceding one.
- `fighter_presence_line` fires on `actor_streak >= 3` at 32% — during a long ground segment
  that is the same three lines over and over. Gate it on position change or damage change, not
  just streak.

**Commentary targets:** uniqueness ≥ 55% (from 22.3%); no single template above ~10 uses per 150
fights (from 99); hardcoded lines below 10% of play-by-play (from 35.4%).

---

# Part 3 — Improving The Stand-Up Itself

Part 1 makes the fight *stay* standing. This part is about whether the standing game is worth
watching once it does. Measured over 300 fights / 659 rounds.

## The headline problem: strikes never miss

| Metric | Engine | Real MMA (UFC avg) |
|---|---|---|
| Significant strikes **landed** per fighter per round | 24.0 | ~20 |
| Significant strikes **attempted** per fighter per round | **32.2** | ~45–50 |
| **Significant strike accuracy** | **74.6%** | **~45%** |
| Beat-level miss/check rate | **8.4%** | 50%+ |

Landed volume is roughly right. Everything else is wrong, and it all comes from one place.

**Site:** `resolve_strike`, `fight_engine.py:2687`

```python
if margin < -12:
    miss_category = {...}.get(action, "power_miss")
    return self.fight_phrase(miss_category, actor, defender)
```

A strike only misses when `margin < -12`, but the margin distribution is centred *above* zero.
Working the average case through `action_attack_value` (`:2276`) and `action_defence_value`
(`:2358`) for two 50-rated fighters:

```
jab          attack = boxing*0.85 + reach*0.18 + iq*0.18            ~= 60.5
power_punch  attack = power_boxing*0.65 + power*0.55 + killer*0.16  ~= 68.0
strike       defence = mental*0.10 + recovery*0.08
                     + strike_defence*0.48 + chin*0.22 + tough*0.24 ~= 56.0

margin = attack - defence + randint(-18, 18)
  jab:          mean +4.5   ->  P(miss) ~= 4%
  power_punch:  mean +12.0  ->  P(miss) ~= 0%
```

Measured, per 300 fights: `jab_miss` 47 against `jab_land` 714; **`power_miss` 16 against
`power_land` 447**. A power punch essentially cannot miss.

**Fix 10 — Rebalance the strike margin and widen the miss band.**

- Raise the striking defence coefficients so the mean margin sits near zero: `strike_defence`
  ×0.48 → ×0.62, and add the currently-unused standing defensive skills (below) as real terms.
- Move the miss gate from `margin < -12` to `margin < 2`, and add a *partial* band
  (`2 <= margin < 10`) that lands with reduced impact — a grazing shot, a blocked hook — so the
  outcome is not binary.
- Recalibrate `strike_volume` accuracy (`:2570`) once the margin is centred: the current
  `0.46 + margin/52` floor of 46% is applied on top of a beat that already nearly always lands,
  double-counting success. Target end-to-end accuracy 42–50%.
- Raise base sequence sizes ~40% to bring attempts to ~45/round while landed volume holds.

This single fix does more for how the stand-up *feels* than anything else in this document.
Whiffs, blocks and resets are what make the landed shots read as earned.

---

## Fix 11 — Punches have no anatomy; kicks do

Kicks are modelled properly: four types (`teep` / `high` / `body` / `leg`) at `:2578-2616`, each
with its own power, speed, technique, defence lookup, damage channel, and commentary category.

Punches are two undifferentiated buckets. `jab` and `power_punch` resolve through one formula
(`:2691`):

```python
impact = max(1, round((margin + actor.power * 0.34 + 2.3) / 8.5 * ...))
```

There is no hook, uppercut, cross, overhand, check hook, or spinning attack — and
`damage_zone` is hardcoded `"head"` for every punch (`:2745`), so **standing body punching does
not exist in the engine.** The `body` damage channel is reachable only via kicks and clinch
knees, which means the body-work → gas-drain → fatigue-TKO chain is closed off to boxers.

**Change:** mirror the kick treatment inside `power_punch`. Pick a punch type weighted by
`creative_punches`, `punch_technique`, `hand_speed`, and style, then vary the outcome:

| Type | Distinguishing behaviour |
|---|---|
| Cross / straight | Baseline; highest `flush_knockout_chance` scaling |
| Hook | Higher knockdown roll, lower accuracy |
| Uppercut | Bonus versus a defender with high `head_movement`; strong from the pocket |
| Overhand | Bonus versus a shorter-reach or southpaw-mismatched defender |
| Body hook | Routes damage to `state["body"]`, drains gas — opens the fatigue path for boxers |
| Spinning back fist | Rare, gated on `creative_punches`, high miss rate, high KO payoff |

Give each its own `*_land` / `*_miss` phrase categories. This also feeds Part 2: `power_land`
currently carries 447 uses through one category.

**Also missing standing:** knees and elbows exist only inside `dirty_boxing`
(`:2701-2740`). A flying/standing knee at range, and elbows on the break, are absent. The
`elbows` and `knees` detailed skills are consequently dead outside the clinch.

---

## Fix 12 — There is no defensive or counter game

`Counter Specialist` is a trait, `Counter` is a behaviour, and `head_movement`, `footwork`,
`feints`, and `guard_defence` are all editable `STANDING_SKILLS` (`constants.py:1071`). Usage
count in the entire 3,238-line engine:

```
feints          1 reference
guard_defence   1 reference
head_movement   2 references
punch_technique 2 references
footwork        5 references
```

A missed strike costs the attacker gas and nothing else. There is no counter window, so
`Counter Specialist` is implemented as *"jab weight ×1.18, power ×0.92"* (`:938`) — a volume
tweak, not a counter-striker.

**Change:**

- On a clear miss (`margin < -10` after Fix 10), give the defender an immediate free counter
  resolution at a bonus margin, weighted by `reflexes`, `head_movement`, and `counter_striking`.
  This is the mechanic that makes range striking dangerous in both directions and gives patient
  fighters a reason to exist.
- Make the defence roll pick a *mode* — slip, block, check, roll, step off — from
  `head_movement` / `guard_defence` / `footwork`, and select the miss commentary category from
  the mode rather than from the strike type alone.
- Give `feints` a real job: a small pre-exchange roll that reduces the defender's effective
  defence on the following tick, so setup fighters land cleaner.
- Rewrite the `Counter Specialist` and `Counter` bias in terms of the new counter window
  instead of jab weighting.

---

## Fix 13 — The `pocket` range is dead code

`"pocket"` appears in five conditionals (`:136`, `:139`, `:735`, `:798`, `:923`) and is
**never assigned anywhere in the engine.** Standing is therefore a single undifferentiated
distance: a rangy kickboxer and a short pressure boxer fight at exactly the same range.

**Change:** make `pocket` real. Enter it when the aggressor wins an exchange while pressing
forward or when `reach` disadvantage forces the shorter fighter inside; exit on footwork,
lateral movement, or a clinch entry. In the pocket: hooks, uppercuts and dirty boxing gain
weight; `jab`, `kick` and `teep` lose it; `reach` advantage flips from an asset to a liability.
This is where the reach and stance context edges (`stance_matchup_edge`, `:520`) finally get to
matter, and it gives pressure fighters a distinct, visible identity.

---

## Fix 14 — Knockdowns do not create a knockdown

`:2757-2772` handles a knockdown by adding damage, incrementing `state["knockdowns"]`, and
returning a line. Position is untouched. The fight continues as though both fighters are
standing and composed — no downed opponent, no follow-up scramble, no referee proximity, no
survival window.

Measured: 97 knockdowns per 300 fights (0.32/fight, which is a reasonable rate) — but each one
resolves as a flavour line and some damage.

**Change:** set a short-lived `state["downed"] = defender.name` for one or two ticks. While it
is set: the aggressor chooses between `finish_flurry` (ground strikes on a downed opponent),
`follow_to_ground` (jump into guard), or `wave_up` (stay standing, feeding Fix 2); the downed
fighter chooses `recover`, `turtle`, `grab_a_leg`, or `pop_back_up`. This is the single most
dramatic moment in a real fight and the engine currently skips straight past it.

---

## Fix 15 — Kick share is too low, and leg damage never pays off

Landed standing strikes across 300 fights:

```
jab           714      punches  1,161  (81.5%)
power_punch   447
high kick      92      kicks      263  (18.5%)
body kick      88
low kick       51
teep           32
```

Real MMA sits nearer 25–30% kicks. More importantly the *consequences* almost never arrive:
`leg_kick_hurt` fired **once** in 300 fights and `body_kick_hurt` 8 times, because those
categories need `state["leg"] >= 10` / `state["body"] >= 10` and kicks are too rare to
accumulate. The whole calf-kick-cripples-a-fighter storyline is implemented and effectively
unreachable.

**Change:** with Part 1 tripling standing time this partly self-corrects, but also lower the
`kick` fatigue cost (currently 4, equal to `power_punch`, `:2390`), lift the base `kick` weight
in the range pool, and drop the `leg`/`body` hurt thresholds to ~7 so the accumulation
storyline can actually surface within a three-round fight.

---

## Fix 16 — Two dead commentary paths in the striking code

Found while measuring; both belong with Part 2 but are striking-specific.

- **`dirty_boxing_land` is unreachable.** `resolve_strike` builds `clinch_detail` from three
  hardcoded lists (`:2708`, `:2715`, `:2727`, `:2736`) and returns it early at `:2786`
  (`if clinch_detail: return clinch_detail`). Measured: `dirty_boxing_land` **0 uses** in 300
  fights while `dirty_boxing_miss` fired 40 times. The 12-line bank across both phrase tables is
  dead weight, and all clinch striking runs through ~18 hardcoded lines.
- **`kick_checked` is unreachable.** The `defended_category` map at `:2626` covers all four kick
  types explicitly, so the `.get(kick_type, "kick_checked")` fallback can never fire.

---

## Stand-Up Targets

| Metric | Now | Target |
|---|---|---|
| Significant strike accuracy | 74.6% | 42–50% |
| Strikes attempted per fighter per round | 32.2 | 44–50 |
| Strikes landed per fighter per round | 24.0 | 18–22 |
| Beat-level miss/check rate | 8.4% | 45–55% |
| Power punch miss rate | ~3% | 45–55% |
| Kick share of landed standing strikes | 18.5% | 25–30% |
| Distinct standing techniques | 6 | 14+ |
| Standing distances | 1 (`range`) | 2 (`range` + `pocket`) |
| Counter-strike mechanic | none | implemented |
| Knockdown follow-up states | none | implemented |
| Unused `STANDING_SKILLS` | `feints`, `guard_defence`, `head_movement` (barely) | all consumed |

---

# Part 4 — Why The Stand-Up Commentary Feels Flavourless

**The lines are not the problem. The selection is.**

This needs stating up front because it contradicts the obvious fix. `jab_land` has 96 distinct
templates at 3.6 uses per line; `power_land` has 72. Those are healthy banks, and the writing in
them is good:

```
{A} slips outside and fires a clean cross down the middle.
{A} digs a hook to the body before bringing the next punch upstairs.
{A} uses the jab to hide an overhand that lands behind the ear.
{A} times the weight transfer and kicks through {B}'s lead thigh.
```

Adding another hundred lines to a randomly-drawn pool will not fix the flatness. The engine
computes a detailed, highly variable striking beat and then throws almost all of that detail
away before it reaches the text.

---

## The core defect: the engine knows, the commentary doesn't

`fight_phrase` ends at `fight_engine.py:1449`:

```python
template = random.choice(templates.get(category, ["{A} continues to work against {B}."]))
return template.format(A=display_name(actor), B=display_name(defender), **context)
```

A flat `random.choice`. Nothing about what actually happened influences which line is drawn.
Measured over 250 fights, here is what the engine computed and discarded:

| Per-beat quantity | Range | Mean |
|---|---|---|
| `jab` impact | **1 – 12** | 4.1 |
| `power_punch` impact | **1 – 15** | 7.3 |
| `kick` impact | 1 – 11 | 5.3 |
| Jabs landed in one beat | **5 – 36** | 16.0 |
| Power punches landed in one beat | 3 – 24 | 11.4 |
| Kicks landed in one beat | 2 – 17 | 8.7 |

A beat where **36 jabs land for 12 impact** draws its line from exactly the same 96-template pool,
with exactly the same probability, as a beat where **5 jabs land for 1 impact**. A twelve-fold
difference in what happened produces zero difference in how it is described.

That is the whole feeling. Every exchange reads as the same medium-sized event, because to the
commentary layer it *is* the same event.

---

## Fix 17 — Tier the strike categories by intensity

Split each landed-strike category into three tiers and select by the impact the engine already
calculated:

| Tier | Impact | Character of the line |
|---|---|---|
| `*_land_light` | 1–3 | Touching, scoring, range-finding. *"{A} touches the jab off {B}'s guard and resets."* |
| `*_land` | 4–7 | The current bank — clean, meaningful. |
| `*_land_heavy` | 8+ | Visible hurt, crowd reaction, momentum. *"{A} rips the cross through and {B}'s legs stiffen for a beat."* |

Implementation: `resolve_strike` already has `impact` in scope at every return
(`:2691`, `:2646`). Pass it through and pick the category tier from it. Roughly a third of the
existing lines in each bank already read as light or heavy and can be sorted into the new tiers
rather than written from scratch — this is mostly a re-filing job, not a writing job.

The same applies to `strike_volume`'s landed count: a beat of 20+ landed strikes should route to
a flurry-flavoured tier regardless of impact.

---

## Fix 18 — The technique label is computed and thrown away

The kick branch picks a genuinely specific technique name (`:2597`, `:2604`, `:2612`, `:2615`):

```python
label = random.choice(["a high kick", "a fast head kick", "a question-mark kick", "a high round kick"])
label = random.choice(["a lead teep", "a rear teep", "a stabbing push kick", "a teep to the hip"])
label = random.choice(["a hard body kick", "a digging round kick to the ribs", ...])
label = random.choice(["a chopping low kick", "a calf kick", "an inside leg kick", ...])
```

Then discards it:

- `high_kick_land` and `teep_land` are called **without** `technique` at all (`:2675`, `:2677`).
- `low_kick_land`, `body_kick_land`, `body_kick_hurt` and `leg_kick_hurt` **are** passed
  `technique=label` — but **not one template in those categories contains `{technique}`.**

Verified across the whole file: `{technique}` appears in only two categories' templates —
`knockdown` (11) and `signature_ko` (5). Every non-knockdown kick in the game computes its exact
technique and says nothing about it.

**Change:** pass `technique` on all four kick returns, and rewrite ~40% of the templates in each
kick category to consume it — *"{A} snaps {technique} into the lead leg and {B} shifts stance"*.
Keep the rest label-free so the phrasing does not become formulaic.

---

## Fix 19 — Exotic techniques only exist when they end the fight

`signature_technique` (`:2483`) holds the entire highlight-reel vocabulary:

```
a spinning backfist, a superman punch, a leaping left hook,
a spinning back kick, a flying knee, a wheel kick, a jumping switch kick,
a spinning elbow, an upward elbow on the break
```

Its only caller is `deliver_flush_knockout` (`:2510`). A creative fighter can therefore *only*
throw a spinning back kick as a fight-ending knockout — never as a strike that lands, never as
one that misses, never as one that gets caught.

**Change:** roll `signature_technique` as a low-probability variant inside the normal
`resolve_strike` path, gated on `creative_punches` / `creative_kicks` exactly as it is now, and
route the outcome to new `exotic_land` / `exotic_miss` categories. A spinning attack that misses
badly and gets punished is one of the most characterful things in the sport, and it is currently
impossible. This also gives `creative_punches` and `creative_kicks` a visible identity outside
the KO roll.

---

## Fix 20 — No beat knows what the last beat did

Each line is generated in isolation. The state needed for continuity is already tracked and
already unused by the striking text:

| Available in `state` | Currently used for |
|---|---|
| `actor_streak` | Only `fighter_presence_line` and the initiative comeback roll |
| `unanswered` | Only the TKO stoppage check (`:3066`) |
| `damage`, `head`, `body`, `leg` | Damage model; never referenced by a strike line |
| `knockdowns`, `cuts` | Stoppage checks and one `cut` category |
| `round`, `gas` | Round summaries only |

So there is never a *"there it is again"*, a *"that's the third time the calf kick has
landed"*, or a *"{B} has not answered in a minute"*. The engine tracks all three facts.

**Change:** add a lightweight `strike_memory` to `state` — last technique, consecutive lands,
per-target counts — and add a `follow_up` template set consulted when the same technique lands
twice in a row, plus a `sustained_pressure` set gated on `unanswered >= 3`.

The grappling side has the same defect in a different form; see Part 5.

---

## Fix 21 — Damage state never colours a standing line

The whole striking bank is written for a fresh fighter. There is no variant for landing a jab on
a badly cut opponent, on someone whose legs are compromised (`state["leg"] >= 10`), or in the
championship rounds with both fighters gassed. `leg_kick_hurt` and `body_kick_hurt` are the only
two damage-aware standing categories in the engine — and Part 3 measured them firing **once**
and 8 times per 300 fights respectively.

**Change:** gate a `*_land_hurt` variant for each strike type on the defender's accumulated
`head` / `body` / `leg` / `cuts` and gas, and lower the hurt thresholds as recommended in
Fix 15 so the variants are reachable. A round-5 jab landing on an exhausted, cut opponent should
never read the same as a round-1 jab.

---

## Fix 22 — Volume is invisible

`strike_volume` (`:2546`) resolves each beat into an explicit sequence — its own docstring says
so: *"Each commentary beat represents a small, explicit strike sequence, not one invisible
strike."* It produces 5–36 landed strikes per beat. The commentary never once implies a count.

**Change:** where the landed count is high, select from a flurry-tier template that reads as a
sequence rather than a single blow — *"{A} opens up with a long combination and most of it gets
through"* — and where it is low, one that reads as a single scoring shot. No numbers in the
text; just phrasing that matches the scale of what was simulated.

---

## Why This Is The Highest-Value Commentary Work

Part 2 (Fixes 7–9) fixes *repetition* — the same sentence appearing 99 times. Part 4 fixes
*flatness* — every sentence describing the same imaginary event regardless of what the engine
simulated. They are different defects and Part 4 is the one that makes the stand-up feel alive,
because it costs comparatively little new writing: Fixes 17, 18 and 22 are almost entirely
plumbing and re-filing of lines that already exist.

## Stand-Up Commentary Targets

| Metric | Now | Target |
|---|---|---|
| Strike-line selection inputs | 1 (action type) | 5 (action, impact tier, technique, volume, defender damage) |
| Landed-strike categories per strike type | 1 | 3–4 (light / clean / heavy / hurt) |
| `{technique}` reaching non-knockdown text | never | ~40% of kick and punch lines |
| Exotic techniques outside KOs | impossible | reachable on land and miss |
| Beats aware of the previous beat | 0 | follow-up and pressure sets |
| Damage-aware standing categories | 2 (both near-unreachable) | one per strike type, reachable |

---

# Part 5 — Why The Ground Commentary Feels Flavourless

Same root cause as Part 4, worse expression. The ground code contains the single most detailed
piece of domain modelling in the entire engine — and the commentary layer discards it on
**92.5%** of the occasions it is computed.

As with the stand-up, the writing is not the problem. `pass` has 89 templates,
`ground_strikes_land` 63, `submission_defended` 44, and the prose is specific and competent.
The defect is that the ground text is **position-blind and technique-blind** everywhere except
at the exact instant a position changes.

---

## Fix 23 — The named submission is computed on every attempt and shown on almost none

`submission_technique` (`fight_engine.py:2883`) is excellent work: a weighted, position-aware
table of **60+ real techniques**, gated so that leg-lock specialists unlock heel hooks, kneebars,
calf slicers and Texas cloverleafs, and so that back control yields rear-naked chokes,
bow-and-arrows and twisters while guard yields triangles, omoplatas and D'Arce chokes.

It is called unconditionally at the top of `resolve_submission` (`:2844`):

```python
technique = self.submission_technique(actor, action, state)
```

and then reaches the player through exactly one path — `submission_finish_text`, on the finish
branch at `:2870`. **All four non-finish returns discard it:**

```python
return self.fight_phrase("submission_danger",   actor, defender)   # :2872  no technique
return self.fight_phrase("submission_threat",   actor, defender)   # :2876  no technique
return f"{defender.name} shrugs off the submission attempt..."     # :2880  hardcoded
return self.fight_phrase("submission_defended", actor, defender)   # :2882  no technique
```

Measured over 400 fights:

| | Count | Share |
|---|---|---|
| Submission attempts | 1,335 | — |
| Attempts that **name the technique** (finishes only) | 100 | **7.5%** |
| Attempts that **discard the technique** | 1,235 | **92.5%** |
| Distinct techniques rolled across the sample | **46** | — |

Forty-six distinct submissions were simulated and the player saw a name for seven percent of
them. The rest render as *"{A} attacks the neck and forces {B} into emergency defence."*

**This is also a correctness bug, not only a flavour one.** The generic lines assert a body part.
`submission_danger` says *"attacks the neck"* and `submission_threat` says *"isolates a limb"* —
but the technique actually rolled may have been a heel hook, a kneebar, or a calf slicer. The
commentary contradicts the simulation.

**Change:** pass `technique=technique["name"]` on all four returns and rewrite the majority of
templates in `submission_danger`, `submission_threat` and `submission_defended` to consume
`{technique}`:

```
{A} climbs into a body-triangle rear-naked choke and {B} has to fight the hands immediately.
{B} clears the grip before the {technique} can lock in.
{A} switches from the {technique} to the trapped arm as {B} defends.
```

Use the `technique["choke"]` boolean the table already returns to pick choke-flavoured versus
joint-flavoured phrasing, so no line ever says "attacks the neck" about a leg lock. This is the
highest-value single change in the whole commentary section: it costs one argument on four call
sites plus a template rewrite, and it exposes 46 techniques that are already being simulated.

---

## Fix 24 — `{position}` reaches only the moment of transition

Across the entire file, `{position}` appears in the templates of exactly **three** categories:
`takedown_complete`, `slam_takedown`, and `pass` — and it is passed at only three call sites
(`:2805`, `:2806`, `:2827`). All three are *transitions*.

Every sustained-ground category is position-blind. Measured usage over 400 fights, with the
positions those uses were actually spread across:

| Category | Uses | Position spread |
|---|---|---|
| `top_control` | 714 | half guard 40% · guard 26% · side control 20% · mount 10% · back 5% |
| `cling` | 611 | half guard 47% · guard 25% · side control 16% · mount 8% · back 3% |
| `submission_defended` | 544 | half guard 36% · guard 35% · side control 17% · mount 9% · back 3% |
| `submission_danger` | 430 | half guard 38% · side control 23% · guard 16% · mount 14% · back 10% |
| `ground_strikes_land` | 418 | half guard 44% · side control 20% · guard 20% · mount 12% · back 4% |
| `hold_position` | 166 | half guard 46% · guard 23% · side control 19% · mount 10% · back 2% |
| `recover_guard` | 115 | half guard 43% · guard 36% · side control 10% · mount 8% · back 3% |

`top_control` draws from nine position-blind templates — *"{A} keeps heavy top pressure and
limits {B}'s options"* — for all five positions. **Mount and back control, the two most
dangerous places in the sport, read exactly like being stuck in closed guard.**

Part 1 measured the average ground segment at 11.6 ticks. So the position is named once, on the
takedown, and then never again for roughly three minutes of fight time.

**Change:**

- Pass `position=self.position_label(state["position"])` at every ground `fight_phrase` call.
- Split `top_control` into `control_guard` / `control_half` / `control_side` / `control_mount` /
  `control_back`. These are genuinely different activities and deserve different vocabulary —
  posting and posturing in guard, the crossface and shoulder pressure in side control, hooks and
  seat-belt in back control. Twelve lines each replaces nine lines for everything.
- Do the same for `cling` and `hold_position` from the bottom fighter's perspective: surviving
  in guard is a different sentence from surviving under mount.

---

## Fix 25 — Ground-strike lines assert positions the engine may not be in

`ground_strikes_land` contains lines that state a position outright:

```
{A} pins the wrist and lands a clean right from half guard.
{A} traps {B} against the fence and lands measured ground strikes.
{A} keeps the knee heavy across the thigh and lands from top.
```

Because the category is position-blind, *"from half guard"* fires while the engine has the
fighters in mount 12% of the time, and *"against the fence"* fires with no cage state tracked at
all. Same class of defect as Fix 23 — the text contradicts the simulation.

**Change:** after the Fix 24 split, move each position-asserting line into the category whose
position it actually describes, and rewrite the fence-referencing lines as position-neutral
until a ground cage-position flag exists.

**Also:** ground strikes have no weapon typing. `action_attack_value` (`:2295`) already reads
`ground_striking`, `top_control`, `elbows` and `punch_power` for the attack roll, but the outcome
never distinguishes a hammerfist from an elbow from a posture-up right hand. The kick branch
demonstrates the pattern (four typed variants with their own labels); ground strikes should pick
a weapon from `elbows` / `punch_power` / position and pass it as `{technique}`, exactly as
Fix 18 prescribes for kicks.

---

## Fix 26 — `submission_threat` is effectively unreachable

Measured: **2 uses across 400 fights**, against 11 templates written for it.

The gate is ordering, at `:2856` and `:2874`:

```python
if margin + danger_bonus > 8:        # danger branch
    ...
if margin > 0:                       # threat branch
    ...
```

`danger_bonus` is `5 + (sub_attack - 55) * 0.24` in guard/half guard and `9` or more in the
dominant positions, so virtually any attempt with `margin > 0` already satisfies
`margin + danger_bonus > 8` and is absorbed by the branch above. The threat tier — the ordinary
"he's threatening something, she's defending calmly" beat that should be the *most common*
submission outcome — almost never fires.

**Change:** re-band the outcomes so all three tiers are reachable, e.g. danger at
`margin + danger_bonus > 14`, threat at `margin + danger_bonus > 4`, defended below that. This is
a commentary fix and a pacing fix at once: it converts a share of the current all-or-nothing
"deep submission threat" beats into lower-key attacks, which is both more accurate to the sport
and less repetitive.

---

## Fix 27 — No ground beat knows the beat before it, or the damage so far

Identical to Fix 20, and the state is equally available and equally unused:

| Tracked in `state` | Used by ground commentary |
|---|---|
| `stats[name]["control_ticks"]` | No — round summary only |
| `ground_inactivity`, `ground_warning` | No — only the referee stand-up text |
| `sub_att` | No — final metrics only |
| `damage`, `head`, `body`, `cuts` | No |
| `position` history | Not tracked at all |

So there is never *"{A} has been in mount for two minutes"*, *"that's the third submission
attempt of the round"*, *"the ground-and-pound is starting to open the cut"*, or *"{B} still
hasn't improved position since the takedown"*. The referee is the only actor in the engine that
notices a stalemate, and even that fires 0.23 times per fight (Fix 4).

**Change:** add `ground_memory` to `state` — ticks in the current position, submission attempts
this round, last technique attempted — and gate three new template sets on it:
`prolonged_control` (position held 4+ ticks), `repeat_submission` (same limb or same technique
attacked twice), and `accumulating_damage` (defender's head damage rising under ground strikes).
This is the difference between a list of independent events and a round with a story.

---

## Fix 28 — The bottom fighter has no voice

Of the sustained ground categories, only `cling`, `recover_guard`, `sweep_denied` and the
bottom half of `survive` describe the fight from underneath, and all are framed as failure to
escape. There is no vocabulary for active guard — no vocabulary for threatening from the bottom,
for making the top fighter carry weight, or for a defensive guard that is *winning* the
exchange. Combined with Part 1's finding that the bottom fighter cannot get up, the player reads
a long stretch of text in which one fighter does things and the other one endures them.

**Change:** add `active_guard` and `bottom_threat` categories consulted when the bottom fighter
wins a resolution or when `bottom_submission` produces a threat, and rewrite the bottom-side
`survive` variants (promoted out of the hardcoded list by Fix 7) so that competence and danger
from the bottom are describable, not only survival.

---

## Ground Commentary Targets

| Metric | Now | Target |
|---|---|---|
| Submission attempts naming the technique | **7.5%** | 90%+ |
| Distinct techniques visible to the player | 46 rolled, ~4 seen | 46 |
| Categories using `{position}` | 3 (all transitions) | all sustained ground categories |
| Top-control categories | 1 for 5 positions | 5 |
| `submission_threat` uses per 400 fights | **2** | 250+ |
| Lines asserting a possibly-wrong position | present in `ground_strikes_land` | none |
| Ground-strike weapon typing | none | elbow / hammerfist / posture punch |
| Beats aware of prior beats or damage | 0 | 3 new gated sets |
| Bottom-fighter categories that are not failure | 0 | 2 |

---

# Part 6 — Finish Audit

Measured over **1,000 fights** (one in five booked as a five-round main/title bout) against
`fight_engine.py` @ `eb6bc87`.

## Method mix

| Method | Engine | Real UFC |
|---|---|---|
| Decision | **32.0%** | 48–50% |
| TKO | 24.2% | — |
| Submission | **26.5%** | — |
| KO | 15.1% | — |
| Technical Submission | 1.5% | — |
| Corner Stoppage | 0.6% | ~1% |
| Draw | 0.1% | ~0.4% |
| Doctor Stoppage | **0.0%** | ~1.5% |
| Injury Stoppage | **0.0%** | ~0.5% |
| **Finish rate** | **67.9%** | **47–52%** |
| KO + TKO combined | 39.3% | ~33% |
| Submission combined | **28.0%** | **~16%** |

**Two fights in three end early, and submissions are nearly double their real-world share.**

## Where finishes come from

```
submission                          37.7%
damage accumulation / unanswered    34.6%
instant (flush KO / head kick)      18.3%
flush KO (puncher's chance)          8.5%
corner stoppage                      0.8%
doctor / injury                      0.0%
```

## Round of finish

```
round 1: 48.7%     round 4: 0.9%
round 2: 33.4%     round 5: 0.3%
round 3: 16.6%
```

R1–R3 shape is close to the real sport (~44/30/22). Rounds 4 and 5 are the problem: **1.2%
combined.** Championship rounds effectively cannot produce a finish.

---

## Fix 29 — The finish rate is 16–20 points too high

Decisions are the single most common result in real MMA and the third most common here. This is
partly downstream of Part 1 (excess ground time manufactures submissions) and partly independent:
`ko_chance` in `check_fight_stoppage` (`:3072`) has a **0.108 base** applied *per fighter, per
tick*, on top of every other multiplier.

**Change:** treat the base rates as the primary tuning dial once Parts 1 and 3 land — do not
tune them before, because both change the input distribution substantially. Drop the `ko_chance`
base from 0.108 toward ~0.075 and re-measure. Target: finish rate 48–54%, decisions 42–48%.

**Order matters:** Part 1 cuts ground time roughly in half, which cuts submission opportunities;
Part 3's miss band cuts striking damage throughput. Both push the finish rate *down* on their
own. Measure after those before touching anything here, or you will over-correct twice.

---

## Fix 30 — Submissions are nearly double their real share

28.0% versus ~16%. Part 1 measured **1,335 submission attempts per 400 fights** (3.3 per fight),
and `resolve_submission` (`:2863`) rolls a finish on every attempt that clears the danger gate:

```python
finish_chance = ((0.085 + max(0, margin + danger_bonus) / 240) * ...)
if random.random() < min(0.56, finish_chance):
```

A 0.085 floor and a 0.56 ceiling, multiplied across 3.3 attempts a fight, is the whole story.
Fix 26 compounds it: because the threat tier is unreachable, nearly every attempt lands in the
danger branch that carries the finish roll.

**Change:** Fixes 1–4 and Fix 26 will do most of this by reducing attempt volume and diverting
attempts into the threat tier. If submissions are still above ~19% afterwards, lower the 0.085
floor to ~0.06 and the 0.56 cap to ~0.40 rather than reducing attempt frequency further —
submission *attempts* are good drama, submission *conversions* are what is inflated.

---

## Fix 31 — Injury Stoppage is mathematically unreachable

`check_fight_stoppage` (`:3100`, `:3104`):

```python
if body > 24 and random.random() < ...:      # Injury Stoppage
if leg  > 29 and random.random() < ...:      # Injury Stoppage
```

Peak values observed across 1,000 fights:

| Channel | Peak reached | Threshold | Fired |
|---|---|---|---|
| `body` | **24** | `> 24` | **0 times** |
| `leg` | **23** | `> 29` | **0 times** |
| `cuts` | 5 | `>= 3` | see Fix 32 |

The body threshold sits *exactly* on the observed ceiling; the leg threshold is six points above
anything the engine can generate. `check_corner_stoppage` (`:602`) carries the same dead clauses
— `body > 30` and `leg > 28` — so only its damage and gas conditions can ever fire.

**Change:** lower to `body > 17` and `leg > 15`, matching the Fix 15 recommendation to drop the
`*_hurt` commentary thresholds to ~7. Then apply the same correction in `check_corner_stoppage`.
This is what makes a sustained body-kick or calf-kick campaign a real win condition instead of a
decorative damage channel.

**Related mislabel:** the kick knockdown branch (`:2665`) sets

```python
state["finish_category"] = "head_kick_ko" if kick_type == "high" else "injury_stoppage"
```

so a body or leg kick knockdown tags itself `injury_stoppage`, which `finish_strike_text`
(`:3115`) then silently remaps back to `ko_finish`. Measured: 6 occurrences per 1,000 fights, all
rendering as a generic KO line. Give body and leg knockdowns their own finish category rather
than routing them through a label that is thrown away.

---

## Fix 32 — Doctor Stoppage cannot realistically fire

**Zero in 1,000 fights.** The gate at `:3096`:

```python
doctor_window = state.get("tick", 0) >= state.get("ticks_per_round", 0)
if doctor_window and cuts >= 3 and random.random() < max(0.008, min(0.16, doctor_chance)):
```

`doctor_window` is true only on the **single final tick of a round** — 1 tick in 18. Measured at
tick level: `cuts >= 3` occurred 116 times, but coincided with the doctor window only **7 times**,
and each of those then had to pass a ≤0.16 roll. Effective rate is roughly one fight in a
thousand.

The comment above the block explains the intent correctly — doctors assess *between rounds* —
but the implementation checks a mid-action tick rather than the between-rounds break.

**Change:** move the doctor check out of `check_fight_stoppage` and into the between-rounds path
alongside `check_corner_stoppage` (`simulate_fight:229`), where it belongs conceptually. Evaluate
it once per round break instead of once per tick, and relax to `cuts >= 2` with the per-break
probability re-tuned. Target ~1.5% of fights.

---

## Fix 33 — Championship rounds cannot produce a finish

Rounds 4 and 5 account for **1.2%** of all finishes. Three separate dampers stack in
`check_fight_stoppage` (`:3056-3070`):

```python
if state.get("championship_pacing"):    ko_threshold += 10.0 + composure / 30
if championship_late:                   ko_threshold += 18.0 + composure / 16
pacing_mod = (-0.08 if championship_pacing) + (-0.145 if championship_late)
unanswered_chance: (-0.06 if championship_pacing) + (-0.115 if championship_late)
```

A round-4 fighter with 60 composure needs roughly **32 extra damage** to reach the KO threshold
*and* takes a 0.225 absolute reduction in `ko_chance`. The intent — championship fighters are
tougher and referees give them longer — is sound; the magnitude is not. Late finishes in title
fights are one of the sport's signature moments and are currently near-impossible.

**Change:** roughly halve both — `championship_pacing` to `+5.0`, `championship_late` to `+9.0`,
and the pacing modifiers to `-0.04` / `-0.07`. Target: rounds 4–5 producing 6–9% of finishes in
five-round bouts.

---

## Fix 34 — Dead finish code and dead finish commentary

**Dead code.** `finish_chance` (`:3221`) and `finish_method` (`:3235`) are never called anywhere
in the codebase — 20 lines of unused finish logic, including trait handling for `Big Finisher`,
`Fight Finisher` and `Fragile` that exists nowhere else. Either wire the trait effects into
`check_fight_stoppage` or delete both methods; leaving them invites future edits to the wrong
function.

**Dead commentary banks**, measured per 1,000 fights:

| Category | Templates | Uses | Cause |
|---|---|---|---|
| `submission_finish` | 3 | **0** | `submission_finish_text` (`:2930`) builds its text from hardcoded lists and never calls `fight_phrase` |
| `doctor` | 13 | **0** | Fix 32 |
| `injury_stoppage` | 13 | **0** | Fix 31 |
| `draw` | 7 | 0 | draws are 0.1% |
| `walkoff_ko` | 17 | 3 | gated on `impact > 9` **and** `random() < 0.25` |

That is 46 written templates the player will essentially never see, and 280 submission finishes
per 1,000 fights all rendering from the hardcoded lists at `:2933` and `:2976`. Fixes 31 and 32
revive two of these banks for free; `submission_finish` needs the same promotion treatment as
Fix 7, and `walkoff_ko`'s gate should be loosened to roughly `impact > 7` and `random() < 0.4`.

---

## Fix 35 — Method classification is inconsistent across the codebase

`commit_career_stats` (`:404`) counts `career_knockouts` for `("KO", "TKO")` only, while
`world.py:1971` groups `("KO", "TKO", "Doctor Stoppage", "Corner Stoppage")` together. A fighter
who wins by doctor stoppage therefore gains a career finish but not a career knockout, and is
counted as a knockout winner by the other system.

**Change:** define the method groupings once — in `constants.py` — as `FINISH_METHODS`,
`KO_METHODS`, `SUBMISSION_METHODS`, and import them in `fight_engine.py`, `world.py` and
`awards.py`. Low urgency while Doctor and Corner stoppages are rare, but Fixes 31 and 32 will
make both materially more common, at which point the divergence starts showing up in career
records and awards.

---

## Finish Targets

| Metric | Now | Target |
|---|---|---|
| Finish rate | 67.9% | 48–54% |
| Decision | 32.0% | 42–48% |
| KO + TKO | 39.3% | 30–35% |
| Submission (incl. technical) | 28.0% | 15–19% |
| Doctor Stoppage | 0.0% | ~1.5% |
| Injury Stoppage | 0.0% | 0.5–1% |
| Corner Stoppage | 0.6% | 1–2% |
| Finishes in rounds 4–5 (five-round bouts) | 1.2% | 6–9% |
| Dead finish commentary templates | 46 | 0 |
| Uncalled finish helper methods | 2 | 0 |

**Do not tune any of this before Parts 1 and 3 land.** Both change the inputs to every formula
in this section: less ground time means fewer submission attempts, and a real miss rate means
less striking damage. Fixes 31, 32, 34 and 35 are safe to do at any time — they are reachability
and consistency repairs, not balance changes.

---

# Part 7 — Move Variety Audit (current engine, post-rewrite)

> **Version note.** Parts 1–6 audit `fight_engine.py` @ `eb6bc87` (3.0.8, 3,238 lines). The
> working copy in the main checkout is now **7,287 lines** — an uncommitted rewrite sitting on
> top of `dev` @ `f76037c` (3.0.9). **Parts 1–6 should be re-verified against it before any of
> their fixes are applied.** This part audits the current working copy.

## What the rewrite added

A genuine move system, and it is good work:

- **`fight_moves.py`** — a registry of **176 named techniques** and **18 named defenses**, each
  with positions, targets, attack/defense skills, preferred styles, energy, miss risk, counter
  risk, follow-ups, tags, side, range band and failure outcomes.
- `select_exchange_move` with style preferences across 18 styles, signature moves, move mastery,
  stance-matchup lanes, plan preferences, opponent reads, and a pattern-repetition penalty.
- Move chains (`update_move_sequence`), reads (`update_move_reads`), mechanics tracking, dynamic
  stance, AI fight plans with in-fight adaptation, and an evidence-driven commentary layer.

This directly addresses old Fixes 11, 18, 19 and 23 — punch anatomy, technique naming, exotic
techniques and named submissions all now exist as first-class data. The findings below are about
**reachability**, not authoring.

## Measured variety (300 fights, 10,093 move selections)

| Metric | Value |
|---|---|
| Moves in registry | 176 |
| Distinct moves ever selected | 140 |
| **Never selected** | **36 (20.5% of catalogue)** |
| Distinct moves per fight | mean **17.2** (min 1, max 44) |
| Distinct moves per fighter per fight | mean **9.9** |
| Top 10 moves' share of all selections | **52.1%** |
| Top 20 moves' share | 63.9% |
| Consecutive identical move, same fighter | **21.2%** |
| Generic fallback (no legal move matched) | 2.85% |

Single most-selected move: **`composed_survival` at 21.7% of every move selection in the game.**

Top-1 concentration inside each action:

```
survive          100.0%  composed_survival        (1 move in pool)
cling            100.0%  defensive_cling          (1 move in pool)
ground_control    77.4%  ride_control             (4 moves)
jab               71.1%  single_jab               (3 moves, 2 usable)
submission        66.5%  top_submission_chain     (9 moves)
dirty_boxing      63.2%  clinch_knee              (2 moves)
break_clinch      59.5%  frame_exit               (2 moves)
stand_up          36.8%  technical_standup        (3 moves)
kick              15.2%  head_round_kick          (28 moves)  <- healthy
advance_position  16.2%  knee_slice_pass          (12 moves)  <- healthy
```

Where the catalogue is deep, variety is genuinely good. Where it is shallow — and those are the
highest-frequency actions — one move carries everything.

---

## Fix 36 — Four positions are never reached; a fifth is reached once

Position occupancy at move-selection time, against moves authored for each:

| Position | Beats (300 fights) | Moves defined | |
|---|---|---|---|
| range | 3,774 (34.7%) | 85 | |
| half guard | 1,897 (17.5%) | 35 | |
| guard | 1,508 (13.9%) | 34 | |
| clinch | 1,355 (12.5%) | 17 | |
| cage | 951 (8.8%) | 17 | |
| side control | 907 (8.4%) | 24 | |
| mount | 315 (2.9%) | 20 | |
| back control | 151 (1.4%) | 14 | |
| `failed shot` | **3** | 4 | effectively dead |
| `front headlock` | **1** | 13 | effectively dead |
| `pocket` | **0** | 85 | **never reached** |
| `turtle` | **0** | 20 | **never reached** |
| `standing back control` | **0** | 20 | **never reached** |
| `leg entanglement` | **0** | 13 | **never reached** |

**15 move definitions exist only in positions the engine can never enter:**

```
guillotine_choke      anaconda_choke        darce_choke
heel_hook             toe_hold              turtle_breakdown
sit_out_reversal      rear_waist_ride       lift_mat_return
limp_leg_escape       whizzer_recovery      chained_reshot
snapdown_front_headlock  front_headlock_go_behind  turtle_wrist_ride_strikes
```

**The guillotine — one of the most common submissions in the sport — cannot occur. The entire
leg-lock game cannot occur. The turtle and the front headlock, the two positions where most
real scrambles resolve, do not exist.**

`pocket` is the exception that orphans nothing: all 85 of its moves are shared with `range`
(`STANDING_POSITIONS` covers both), so no move is lost. But it confirms the old Part 3 / Fix 13
finding survived the rewrite — `pocket` is still declared and still never assigned, so standing
remains one undifferentiated distance.

**Change:** these positions need entry and exit transitions in `set_fight_position`, driven from
the resolutions that should produce them:

| Position | Should be entered from |
|---|---|
| `failed shot` | a stuffed `shoot` — currently routed straight to `range` or `cage` |
| `front headlock` | a stuffed shot the defender capitalises on; a snapdown from clinch |
| `turtle` | a bottom fighter who turns away rather than recovering guard |
| `standing back control` | a clinch reversal or a caught back in a scramble |
| `leg entanglement` | a `bottom_submission` or `sweep` by a fighter with `leg_locks` |
| `pocket` | pressure won at range; reach disadvantage forcing the shorter fighter inside |

Six transitions unlock 15 orphaned moves plus the specialist set below. This is the single
highest-value change in this part — the content is already written.

---

## Fix 37 — 13 of the 17 specialist moves live in unreachable positions

`REPRESENTATIVE_SPECIALIST_MOVES` (`fight_engine.py:37`) exists precisely to surface signature
techniques — `select_exchange_move` gives them a **+24 style bonus**, by far the largest single
term in the scoring function. That bonus can never fire for thirteen of them:

| Move | Position | Beats available |
|---|---|---|
| `heel_hook`, `toe_hold` | leg entanglement | **0** |
| `turtle_breakdown` | turtle | **0** |
| `rear_waist_ride`, `lift_mat_return`, `limp_leg_escape` | standing back control | **0** |
| `guillotine_choke`, `anaconda_choke`, `darce_choke`, `front_headlock_go_behind` | front headlock | **1** |
| `sit_out_reversal` | front headlock / turtle | **1** |
| `chained_reshot`, `whizzer_recovery`, `snapdown_front_headlock` | failed shot | **3** |
| `body_jab` | range / pocket | 3,774 — but see Fix 38 |
| `kneebar`, `straight_ankle_lock` | guard / half guard | 3,405 — reachable |

Only two of seventeen are genuinely reachable and used. Fix 36 resolves this outright; no change
is needed here beyond it.

---

## Fix 38 — `body_jab` is stranded by head-only target plumbing

`resolve_strike` (`:6334`) sets the target unconditionally:

```python
state["last_strike_target"] = "head"
```

and only the `kick` branch ever overrides it. So every punch action asks for `target="head"`:

```
legal_moves("jab", "range", "head")  ->  ['single_jab', 'double_jab']
legal_moves("jab", "range", "body")  ->  ['single_jab', 'double_jab', 'body_jab']
```

`body_jab` is the only move stranded this way — `power_punch`'s body moves are also legal at
head, so they still appear. But the jab is head-only, which is why `single_jab` carries 71.1% of
all jab beats out of a three-move pool.

**Change:** derive a punch target the way `kick_target_shares` already derives a kick target,
weighted by `body_punching`. This also revives the body-damage → gas-drain path for boxers that
old Fix 11 flagged, and it costs one small function.

---

## Fix 39 — Authored-rarity gates suppress nearly all signature content

Three gates in `select_exchange_move` reject moves outright on a hash roll:

```python
if "high-risk" in definition.tags and fingerprint % 100 >= 14:        return -10_000
authored_frequency = 18 if "style-finisher" in tags else 12
if crc32(finisher_material) % 100 >= authored_frequency:              return -10_000
```

Measured share of all 11,120 selections:

| Tag | Uses | Share | Moves ever seen |
|---|---|---|---|
| `style-combination` | 207 | 1.86% | 14/18 |
| `creative` | 40 | 0.36% | 1/1 |
| `finisher` | 28 | 0.25% | 10/15 |
| `style-finisher` | 28 | 0.25% | 10/18 |
| `counter` | 25 | 0.22% | 6/8 |
| `high-risk` | 11 | **0.10%** | 5/6 |
| `spinning` | 4 | **0.04%** | 3/6 |
| Signature moves (any) | 384 | 3.45% | — |

**Spinning attacks appear four times in 300 fights.** Eighteen style-finishers were authored —
one per style, the moment that most defines a fighting style — and eight of them never appear at
all. The rarity gating is stacked on top of an already-narrow eligibility path (the finisher must
also survive `signature_finisher_ids` filtering and beat every other candidate on score).

**Change:** raise `authored_frequency` to ~35 for `style-finisher` and ~28 for `finisher`, and
the `high-risk` gate from 14 to ~30. Then gate on *fighter attributes* rather than a flat hash —
scale the threshold by `creative_kicks` / `creative_punches` / `killer_instinct` so a flashy
fighter throws flashy techniques and a grinder does not. Rarity should be a property of the
fighter, not a global constant.

---

## Fix 40 — Deterministic argmax with a 9-point variety band

`select_exchange_move` picks by:

```python
definition = max(eligible, key=lambda row: (row[0], row[1].move_id))[1]
...
variety = fingerprint % 901 / 100          # 0.00 - 9.00
return proficiency + style_bonus + signature_bonus + mastery_bonus + context_bonus + variety
```

There is no weighted draw — the top score always wins, and the only spread is a 0–9 hash term
keyed on `(identity, round, tick, action, position, target, move_id)`. Whenever a fighter's
proficiency spread across the candidate pool exceeds ~9 points, **the same move wins every time**
in that context. That is the mechanism behind the 21.2% consecutive-repeat rate and the top-1
concentrations above.

Note this is a deliberate design choice — the docstring says *"without consuming any RNG
stream"*, preserving replay determinism — so the fix must not reach for `random`.

**Change:** keep determinism, widen the draw. Convert the argmax into a deterministic weighted
selection over the top *k* candidates: take the top 4–6 by score, weight them by
`softmax(score / temperature)`, and index with the existing `fingerprint`. Same reproducibility,
far more variety. Raise the pattern-repetition penalty's ceiling as well — at `min(7.0, ...)` it
cannot outweigh a 20-point proficiency gap.

---

## Fix 41 — A quarter of all selections draw from a one-move pool

Moves defined per parent action, against how often that action fires:

| Action | Share of beats | Moves in pool | Usable |
|---|---|---|---|
| `survive` | **21.7%** | **1** | 1 |
| `cling` | **4.3%** | **1** | 1 |
| `jab` | 7.9% | 3 | 2 |
| `dirty_boxing` | 4.7% | 2 | 2 |
| `break_clinch` | 3.3% | 2 | 2 |
| `ground_control` | 5.5% | 4 | 4 |
| `cage_control` | 2.7% | 3 | 3 |
| `stand_up` | 2.9% | 3 | 3 |
| `power_punch` | 4.7% | 33 | 31 |
| `kick` | 3.2% | 28 | 22 |

**`survive` and `cling` together are 26% of every move selection in the game and have one move
each.** The catalogue is inverted: the deepest pools sit on the least frequent actions.

**Change:** author 8–12 moves each for `survive`, `cling`, `ground_control`, `break_clinch` and
`dirty_boxing`, and expand `jab` beyond three. These are the shallowest pools on the busiest
actions, so the variety return per line written is the highest in the catalogue.

Also worth noting: `force_cage` and `front_headlock_escape` are chosen as actions but have **zero
moves in the registry**, so they fall to the generic fallback every time.

---

## Fix 42 — Skill gates are *not* the problem (do not "fix" them)

Recording this to prevent a plausible wrong move. 138 of 176 moves carry a `minimum_skill` gate
between 52 and 72, which looks restrictive against a nominal 50 baseline. It is not:

```
roster detailed-skill values: n=14,000  mean 69.1  median 70  p90 84
gate >= 55: 119 moves;  87.9% of roster skill values clear it
gate >= 60:  60 moves;  80.7% clear it
gate >= 65:  26 moves;  69.4% clear it
gate >= 70:   5 moves;  53.6% clear it
```

The gates are well calibrated to the actual roster. **Leave them alone** — the dead catalogue is
caused by unreachable positions (Fix 36) and rarity gating (Fix 39), not by skill thresholds.

---

## Move Variety Targets

| Metric | Now | Target |
|---|---|---|
| Moves never selected | 36 (20.5%) | ≤ 5 |
| Positions never reached | 4 (+2 near-zero) | 0 |
| Orphaned move definitions | 15 | 0 |
| Specialist moves reachable | 2 / 17 | 17 / 17 |
| Distinct moves per fighter per fight | 9.9 | 16–20 |
| Top 10 moves' share of selections | 52.1% | ≤ 30% |
| Consecutive identical move | 21.2% | ≤ 8% |
| Single largest move share | 21.7% (`composed_survival`) | ≤ 6% |
| Style-finisher share of selections | 0.25% | 1.5–2.5% |
| Spinning-attack uses per 300 fights | 4 | 60–120 |
| Actions with a one-move pool | 2 (26% of beats) | 0 |
| Generic fallbacks | 2.85% | < 0.5% |

## One carry-over from Part 1

Position occupancy at move-selection time in the current engine: **range 34.7%, clinch/cage
21.3%, ground 44.1%.** That is essentially unchanged from the 3.0.8 measurement (33.9 / 19.6 /
46.5), so **Part 1's position-ratchet findings appear to survive the rewrite** and are worth
re-verifying directly. The dominance of `composed_survival` and `defensive_cling` in the move
data is the same stalling problem seen from a different angle.

---

# Verification Harness

Save as `tools/standup_balance_probe.py`. It monkeypatches the engine rather than modifying it,
so it can be run against any revision for before/after comparison.

```python
import collections, importlib.util, random, re, sys, tkinter as tk
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("mma_warriors", ROOT / "main.py")
game = importlib.util.module_from_spec(spec)
spec.loader.exec_module(game)

root = tk.Tk(); root.withdraw()
app = game.FightEmpireApp(root)

GROUND = {"guard", "half guard", "side control", "mount", "back control"}
CLINCH = {"clinch", "cage"}
actions = collections.Counter()
tick_pos = collections.defaultdict(collections.Counter)
td_out = collections.Counter()
cat_uses = collections.Counter()
cat_bank = collections.defaultdict(set)
seen = collections.Counter()

orig_choose = app.choose_action
def choose(fighter, opponent, state, round_no, tick):
    pos = state["position"]
    tick_pos[tick]["ground" if pos in GROUND else "clinch" if pos in CLINCH else "standing"] += 1
    action = orig_choose(fighter, opponent, state, round_no, tick)
    actions[action] += 1
    return action
app.choose_action = choose

orig_resolve = app.resolve_exchange
def resolve(actor, defender, action, state, round_stats):
    result = orig_resolve(actor, defender, action, state, round_stats)
    if action in ("shoot", "takedown"):
        after = state["position"]
        td_out["takedown" if after in GROUND
               else "cage/clinch" if after in CLINCH else "stuffed"] += 1
    return result
app.resolve_exchange = resolve

orig_phrase = app.fight_phrase
def phrase(category, actor, defender, **context):
    line = orig_phrase(category, actor, defender, **context)
    cat_uses[category] += 1
    cat_bank[category].add(line.replace(actor.name, "X").replace(defender.name, "X"))
    return line
app.fight_phrase = phrase

random.seed(7)
roster = [game.Fighter(**asdict(f)) for f in app.roster]
divisions = collections.defaultdict(list)
for fighter in roster:
    divisions[(fighter.gender, fighter.weight)].append(fighter)
pool = [d for d in divisions.values() if len(d) >= 2]

FIGHTS = 400
sig = att = rounds = 0
for _ in range(FIGHTS):
    a, b = random.sample(random.choice(pool), 2)
    fa, fb = game.Fighter(**asdict(a)), game.Fighter(**asdict(b))
    *_, last_round, lines = app.simulate_fight(fa, fb, {"main": False, "title": False})
    rounds += last_round
    for fighter in (fa, fb):
        stats = fighter.last_fight_stats or {}
        sig += stats.get("sig", 0)
        att += stats.get("sig_att", 0)
    for line in lines:
        if line.startswith("  ["):
            text = re.sub(r"^\s*\[[^\]]+\]\s*", "", line)
            seen[text.replace(a.name, "X").replace(b.name, "X")] += 1

total = sum(actions.values())
STAND = {"jab", "power_punch", "kick"}
GROUND_ACTIONS = {"ground_control", "ground_strikes", "advance_position", "submission",
                  "recover_guard", "sweep", "bottom_submission", "cling", "stand_up"}
print(f"decisions: {total}")
print(f"  striking {100 * sum(actions[k] for k in STAND) / total:.1f}%"
      f"  ground {100 * sum(actions[k] for k in GROUND_ACTIONS) / total:.1f}%")
for tick in sorted(tick_pos):
    c = tick_pos[tick]; t = sum(c.values())
    print(f"  tick {tick:2d}: standing {100 * c['standing'] / t:5.1f}%"
          f"  clinch {100 * c['clinch'] / t:5.1f}%  ground {100 * c['ground'] / t:5.1f}%")
td_total = sum(td_out.values()) or 1
for key, value in td_out.most_common():
    print(f"  {key:14s} {100 * value / td_total:5.1f}%")

print(f"\nsig landed/round {sig / (2 * rounds):.1f}   attempted/round {att / (2 * rounds):.1f}"
      f"   accuracy {100 * sig / max(1, att):.1f}%")
landed = sum(v for k, v in cat_uses.items() if k.endswith("_land"))
missed = sum(v for k, v in cat_uses.items() if k.endswith(("_miss", "_checked")))
print(f"beat-level miss/check rate {100 * missed / max(1, landed + missed):.1f}%")

lines_total = sum(seen.values())
print(f"\ncommentary: {lines_total} lines, {len(seen)} distinct "
      f"({100 * len(seen) / lines_total:.1f}% unique)")
for text, count in seen.most_common(20):
    print(f"  {count:4d}  {text[:96]}")
print("\ncategory pressure (uses per distinct line):")
rows = sorted(((cat_uses[k] / max(1, len(v)), k, cat_uses[k], len(v))
               for k, v in cat_bank.items()), reverse=True)
for ratio, key, uses, bank in rows[:25]:
    print(f"  {key:26s} {uses:6d} uses  {bank:4d} lines  {ratio:5.1f}")
```

---

# Rollout Order

**Stage A — position balance (Part 1)**

1. **Fixes 1 + 4** (takedown economy + referee stand-up). Re-run the probe. Expect standing share
   to move to roughly 45–50%.
2. **Fixes 2 + 3** (disengage + scramble). Expect standing share to reach the 60% band and average
   ground segments to fall below 5 ticks.
3. **Fix 5** (clinch separation). Small, but removes the fence-stall tail.
4. **Re-measure.** Only apply **Fix 6** if standing share is still under 58% — the first four may
   be sufficient, and over-damping the range weights will make wrestlers feel inert.

**Stage B — stand-up depth (Part 3)**

5. **Fix 10** (margin rebalance and miss band) alone, then re-measure. It changes striking
   accuracy, damage throughput, and therefore KO rate and finish mix — settle it before layering
   anything else on top. Expect KO/TKO to *fall* as strikes start missing. Part 6 measures
   KO+TKO at 39.3% against a real ~33%, so let it fall and check it against that target before
   compensating; if it overshoots downward, correct with `flush_knockout_chance` and impact
   scaling rather than by narrowing the miss band again.
6. **Fixes 11 + 15** (punch anatomy, kick share and hurt thresholds), then **Fix 12** (counters
   and defensive modes). Fix 12 depends on Fix 10 — there is no counter window until strikes
   miss.
7. **Fixes 13 + 14** (pocket range, knockdown states) last in this stage; both add new positions
   and action branches, so land them once the striking numbers are stable.

**Stage C — commentary (Parts 2, 4 and 5)**

8. **Fixes 23 + 18 + 16** — the pure-plumbing wins, in that order. Fix 23 exposes 46 already-
   simulated submissions by passing one argument at four call sites; Fix 18 makes the
   already-computed kick technique reach the text; Fix 16 revives 12 dead lines with a two-line
   change. These change how the fight reads for almost no new writing, and Fix 23 is the single
   highest-value item in the entire commentary section.
9. **Fixes 24 + 25** (position plumbing and the `top_control` split). Fix 25's misplaced lines
   can only be re-filed once Fix 24's categories exist, so do them together.
10. **Fixes 26 + 9** — `submission_threat` re-banding and structural anti-repetition. Both change
    how much of Fix 8 is needed, so run the probe again after them.
11. **Fixes 17 + 22** (impact and volume tiering). Mostly re-filing existing lines into
    light / clean / heavy / flurry tiers rather than writing new ones. This is the single
    biggest change to how the stand-up *feels*.
12. **Fixes 20 + 27 + 21 + 28** (beat-to-beat memory standing and on the ground, damage-aware
    variants, bottom-fighter vocabulary). Fix 21 depends on the lowered hurt thresholds from
    Fix 15; Fix 28 reads best after Part 1 has given the bottom fighter a real chance to escape.
13. **Fix 19** (exotic techniques outside KOs) — depends on Fix 10's miss band existing, so a
    spinning attack can whiff and be punished.
14. **Fix 7**, then **Fix 8**, last. Every new category from Fixes 2, 3, 5, 11, 13, 14, 17, 19,
    21, 24, 28 and 31 (`disengage`, `scramble_up`, `ref_separation`, the punch-type categories,
    pocket lines, knockdown-state lines, the tier splits, `exotic_*`, the `*_hurt` variants, the
    five `control_*` categories, `active_guard`/`bottom_threat`, the body/leg knockdown finish
    categories) must exist before the bank-widening pass, and the post-fix usage counts determine
    the real target sizes.

**Stage D — finishes (Part 6)**

15. **Fixes 31, 32, 34 and 35** can be done at any point, including first — they are
    reachability and consistency repairs, not balance changes. They revive the `doctor` and
    `injury_stoppage` banks (26 templates), delete two uncalled methods, and unify the method
    groupings.
16. **Fixes 29, 30 and 33** (finish-rate base, submission conversion, championship-round dampers)
    **only after Stages A and B are settled.** Part 1 halves ground time and Part 3 introduces a
    real miss rate; both push the finish rate down on their own. Measure first, then tune the
    bases — tuning before will over-correct twice.

After each step run `Run Smoke Tests.bat` (`smoke_test.py` exercises `simulate_fight` for verbose
commentary, stoppage handling, and per-fighter `last_fight_stats`) plus `stability_test.py`. Per
`AGENTS.md`, engine changes also require the CHANGELOG / README / AGENTS change package and a
rebuilt exe.
