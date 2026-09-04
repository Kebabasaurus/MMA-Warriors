# Fight Engine — Move Expansion Plan (Phases 29–34)

Continues `FIGHT_ENGINE_MOVES_AND_SKILLS_PLAN.md`, whose Phases 0–28 are complete. Phase
numbering resumes at 29; Phases 16 (fight-plan evolution) and 17 (analysis UI) remain open there
and are untouched by this plan.

Baseline for every measurement below: registry at **200 moves / 18 defenses** after commit
`4a73923`, measured over 300 simulated fights (11,342 move selections).

---

## The Balance Contract Governs Everything Here

From the parent plan, and confirmed the hard way during `4a73923`:

> total finishes **60.39%**, KO **16.48%**, TKO **19.04%**, preserved to two decimal places
> against the 3,840-bout corpus in `analysis/fight_engine_baseline.json`.

**Every phase must be classified before work starts:**

| Class | Definition | Calibration cost |
|---|---|---|
| **A — Presentation** | New move *names*, labels, commentary. No damage, position, or RNG effect. | Free. Verify anyway. |
| **B — Selection** | Changes which existing technique is chosen. No new mechanical consequence. | Free if it consumes no mechanics RNG. Verify. |
| **C — Mechanical** | New damage channel, position transition, gas cost, or stoppage path. | **Requires deliberate recalibration and sign-off.** |

The lesson from `4a73923`: adding body-punch damage plus a gas drain looked like a small,
obviously-correct change. It moved the corpus from 60.39% to **66.43%** finishes, almost entirely
by making the `body > 24` injury stoppage reachable for the first time. It was reverted to
targeting-only and the corpus returned to an exact match. **A Class C change is never a side
effect of a Class A or B one.**

Verification command, required in every phase's acceptance criteria:

```bash
py -3 analysis/generate_fight_engine_baseline.py --verify analysis/fight_engine_baseline.json
```

Exit 0 with `"failures": []` is the gate.

---

## Where The Gaps Actually Are

Measured, not assumed.

### Legal-pool depth by position (the real problem)

Pools of two or fewer techniques in the positions the engine actually occupies:

| Position | Share of beats | Thin pools |
|---|---|---|
| range | 34.7% | `cage_control` (1) |
| half guard | 17.5% | **`submission` (1)**, `recover_guard` (2), `leg_attack` (2) |
| guard | 13.9% | **`submission` (1)**, `recover_guard` (1), `leg_attack` (2) |
| clinch | 12.5% | `force_cage` (1) |
| cage | 8.8% | `force_cage` (1) |
| side control | 8.4% | `recover_guard` (2) |
| mount | 2.9% | `recover_guard` (2) |
| back control | 1.4% | `recover_guard` (2) |

**`top_submission_chain` is the only legal submission in guard and half guard** — together 31.4%
of all beats — which is why it carries **70% of every submission beat in the game**. This is the
single largest remaining concentration and Phase 29 exists for it alone.

### Style coverage is lopsided

```
Wrestler            60      Sanda                21
BJJ                 52      Submission Grappler  21
Sambo               34      MMA Generalist       19
Boxer               32      Karate               18
Muay Thai           30      Judo                 18
Catch Wrestler      25      Dutch Kickboxer      17
Kickboxer           24      Freestyle Wrestler   17
Luta Livre          22      Taekwondo            12
                            Well-Rounded          3
                            Grappler              2
```

`Grappler` and `Well-Rounded` are playable styles with almost no authored identity.

### The chain system is mostly unused

**49 of 200 moves declare `follow_ups`.** `select_exchange_move` awards a **+10 bonus** for
continuing a live chain — the largest contextual term in the function — and three quarters of the
catalogue can never trigger it.

### Positions the engine cannot enter

`pocket`, `turtle`, `standing back control`, `leg entanglement` are never reached; `front
headlock` and `failed shot` fire once or twice per 300 fights. **30 moves remain unselectable.**
This is Class C work and is deliberately last in this plan.

---

# Phase 29 — Guard and half-guard submissions

**Class B** (new moves in already-reachable positions; no new mechanical paths).

The highest-value phase in this plan. One technique currently serves 31.4% of the fight.

### Work

Author 10–12 submissions legal from top in `guard` / `half guard`, replacing the single
`top_submission_chain` catch-all as the default:

| Technique | Position | Owning styles |
|---|---|---|
| kimura from half guard | half guard | Catch Wrestler, Sambo |
| d'arce choke | half guard | BJJ, Luta Livre |
| brabo / arm-triangle from half guard | half guard | BJJ, Submission Grappler |
| guillotine from top | guard | BJJ, Luta Livre |
| north-south choke | half guard | Catch Wrestler |
| von flue choke | half guard | Catch Wrestler, Wrestler |
| americana from half guard | half guard | BJJ, Judo |
| head-and-arm from guard | guard | Judo, Sambo |
| can-opener neck crank | guard | Catch Wrestler |
| straight ankle from top guard | guard | Sambo, Luta Livre |

Retain `top_submission_chain` as the fallback for fighters who clear no specialist gate.

### Constraints

`validate_move_registry` requires every `submission`-tagged move to declare `attack_path` and
`failure_outcomes`. Reuse the existing failure vocabulary so `resolve_submission` needs no change.

### Acceptance criteria

- `submission` top-move share falls from **70%** to **≤ 25%**.
- Guard and half-guard submission pools hold ≥ 6 legal techniques each.
- Calibration verify passes with zero failures.
- Submission finish rate stays within the accepted corpus tolerance — this phase adds *names*,
  not new finish probability. If submission rate moves at all, the phase has leaked into Class C.

---

# Phase 30 — Escapes, reversals and guard recovery

**Class B.**

`recover_guard` has one or two techniques in every ground position, and the bottom fighter's
vocabulary is almost entirely failure (audited in the companion guide's Part 5, Fix 28).

### Work

- 8–10 `recover_guard` techniques: knee-shield recovery, hip-heist, elbow-frame recovery,
  granby roll, shin-to-shin retention, half-guard underhook recovery, bridge-and-shrimp.
- 4–6 `sweep` additions weighted toward the bottom fighter winning: hip bump, flower sweep,
  butterfly hook sweep, John Wayne sweep, electric chair.
- 3–4 `stand_up` techniques beyond `technical_standup`: wall walk, kick-away and stand, shin-post
  escape.

### Acceptance criteria

- Every ground position offers ≥ 4 legal `recover_guard` techniques.
- Bottom-position technique variety per fight rises measurably (report distinct bottom-side moves
  per fighter, before and after).
- Calibration verify passes. Sweep and stand-up **success rates must not change** — these are new
  names on existing resolution maths.

---

# Phase 31 — Follow-up chains across the catalogue

**Class B**, and the highest ratio of impact to new content in this plan: it adds almost no moves,
it wires up the ones that exist.

### Work

Raise `follow_ups` coverage from **49/200 to ≥ 150/200**. Every move should name 1–3 plausible
successors, so the +10 `sequence-follow-up` bonus can actually fire:

- Strikes chain into strikes and entries (jab → cross → level change).
- Entries chain into finishes (double-leg entry → double-leg finish → ride).
- Passes chain into submissions and back-takes (knee slice → side control → arm triangle).
- Escapes chain into scrambles and stand-ups.

Add a `chain_depth` counter to the trace so multi-step sequences can be reported and tested.

### Acceptance criteria

- ≥ 150 moves declare follow-ups; validator confirms every id resolves.
- Measured share of selections carrying a non-empty `sequence_source_id` rises from its current
  near-zero level to **≥ 12%**.
- Median observed chain length ≥ 2 in fights that reach round 2.
- Calibration verify passes.

---

# Phase 32 — Style identity for thin styles

**Class B.**

### Work

Bring `Grappler` (2 moves), `Well-Rounded` (3) and `Taekwondo` (12) up to at least 18 authored
moves each, and add one `style-combination` plus one `style-finisher` for any style still missing
them.

- **Grappler** — a generalist grappling identity distinct from BJJ and Wrestler: chain wrestling
  into front headlock, scramble-heavy back exposure, no-gi pressure passing.
- **Well-Rounded** — the "no holes" identity: level-change feints off punches, strike-to-clinch,
  clinch-to-strike exits.
- **Taekwondo** — the existing 12 are kick-heavy; add distance management, the back-leg side kick
  as a range tool, and the spin-off-the-check counter.

### Acceptance criteria

- No playable style holds fewer than 18 authored moves.
- Every style owns ≥ 1 `style-combination` and ≥ 1 `style-finisher`.
- Style-vs-style finish rates stay within the corpus subgroup tolerances — this phase must not
  make any style stronger, only more legible.

---

# Phase 33 — Named defenses

**Class B.**

18 defenses serve 200 moves, so defensive commentary repeats heavily and
`select_exchange_defense` has little to choose from.

### Work

Expand `DEFENSE_DEFINITIONS` from 18 to ~40, covering the families the move registry already
references but under-serves: shoulder roll, long guard, cross-guard catch, elbow-in body block,
underhook recovery, hip-to-hip escape, wrist-fight break, grip strip, posture-and-frame,
leg-lock rotation defense.

### Acceptance criteria

- Every `defense_families` value referenced by a move resolves to ≥ 2 concrete defenses.
- Defensive-clause repetition in rendered commentary falls below 10 uses per line per 300 fights.
- Calibration verify passes. Defenses here are labels over existing resolution maths.

---

# Phase 34 — Unreachable positions (Class C — calibrated)

**Class C. Do not start until Phases 29–33 are landed and verified.**

This is the phase that unlocks the 30 currently unselectable moves — including the guillotine
family, the entire leg-lock game, the turtle and the front headlock. It is real engine surgery on
position state and **will** move the corpus.

### Work

Add entry and exit transitions in `set_fight_position` for:

| Position | Entered from | Unlocks |
|---|---|---|
| `failed shot` | a stuffed `shoot` | `chained_reshot`, `whizzer_recovery`, `snapdown_front_headlock` |
| `front headlock` | stuffed shot capitalised on; snapdown from clinch | `guillotine_choke`, `anaconda_choke`, `darce_choke`, `front_headlock_go_behind` |
| `turtle` | bottom fighter turning away instead of recovering guard | `turtle_breakdown`, `turtle_wrist_ride_strikes`, `sit_out_reversal` |
| `standing back control` | clinch reversal, caught back in a scramble | `rear_waist_ride`, `lift_mat_return`, `limp_leg_escape` |
| `leg entanglement` | `bottom_submission` or `sweep` by a fighter with `leg_locks` | `heel_hook`, `toe_hold`, `straight_ankle_lock` |
| `pocket` | pressure won at range; reach disadvantage forcing the shorter fighter inside | punch-range differentiation |

Each transition needs an exit path, an inactivity/stalemate escape, and `validate_fight_transition`
coverage so no fight can strand in a new position.

### Sequencing within the phase

1. `failed shot` and `front headlock` first — smallest state surface, biggest content unlock.
2. `turtle` and `standing back control` next; they share the scramble vocabulary.
3. `leg entanglement` after, since it interacts with the submission model.
4. `pocket` last — it changes standing distance for every fight and carries the widest blast
   radius.

**Recalibrate after each sub-step, not once at the end.** Expect submissions to rise (the
guillotine is one of the sport's most common finishes and is currently impossible) and expect to
need offsetting tuning elsewhere to hold 60.39%. That trade is a deliberate, signed-off decision —
record the new accepted numbers in the parent plan's balance contract if they change.

### Acceptance criteria

- All 14 registry positions reachable; `pocket` occupancy ≥ 8% of standing beats.
- Moves never selected falls from **30** to **≤ 5**.
- Guillotine-family and leg-lock submissions appear in normal play.
- Corpus either matches 60.39/16.48/19.04 exactly, **or** a new calibration is explicitly accepted
  and written into the parent plan.

---

## Targets Across The Whole Plan

| Metric | Now (`4a73923`) | After 29–33 | After 34 |
|---|---|---|---|
| Registry size | 200 | ~270 | ~275 |
| Defenses | 18 | ~40 | ~40 |
| Moves never selected | 30 (15.0%) | ~28 | **≤ 5** |
| Distinct moves per fighter per fight | 13.2 | 17–19 | **20–24** |
| Top 10 moves' share | 34.3% | ≤ 28% | ≤ 25% |
| `submission` top-move share | 70% | **≤ 25%** | ≤ 20% |
| Moves declaring follow-ups | 49 | **≥ 150** | ≥ 200 |
| Chained selections | ~0% | **≥ 12%** | ≥ 15% |
| Styles below 18 authored moves | 3 | **0** | 0 |
| Positions never reached | 4 (+2 near-zero) | 4 | **0** |
| Finish rate | 60.39% | 60.39% (unchanged) | re-accepted |

---

## Working Rules

1. **Classify the phase before writing code.** A/B phases must leave the corpus untouched; if the
   verify moves, something leaked into Class C and must be found, not absorbed.
2. **Never consume the mechanics RNG for naming or selection.** Use a bout-local deterministic
   fingerprint, as `select_exchange_move` and `punch_target_shares` do.
3. **Run the validator early.** `validate_move_registry` enforces per-tag contracts — kicks need
   target/side/range/defense families, takedowns need entry and finish positions, submissions need
   attack path and failure outcomes, finishers must be skill-gated standing strikes.
4. **Preserve authored content from dilution.** Style combinations, style finishers and signature
   moves bypass the variety draw by design; new authored content must be tagged so it inherits
   that protection.
5. **Guard the invariants the tests encode.** A live counter window must resolve into a counter
   technique; accumulated exertion must reduce high-energy selection; every rendered call must
   name its recorded move. All three were broken and repaired during `4a73923`.
6. **Report variety with the same harness every time** so numbers stay comparable across phases.

## Suggested Delivery Slices

| Slice | Phases | Rationale |
|---|---|---|
| 1 | 29 | Biggest single concentration in the game, self-contained |
| 2 | 31 | Wires up existing content; no new authoring |
| 3 | 30 + 33 | Bottom-position and defensive vocabulary together |
| 4 | 32 | Style parity pass |
| 5 | 34 | Class C surgery, sub-stepped and recalibrated throughout |
