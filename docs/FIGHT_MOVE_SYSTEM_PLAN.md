# Fight Move System Plan — Architecture and Expansion

How to grow the fight engine's technique catalogue from **200 moves** to **800+** — the code
structure that has to change first, then the content phases that fill it.

Continues `FIGHT_ENGINE_MOVES_AND_SKILLS_PLAN.md`, whose Phases 0–28 are complete. Phase numbering
resumes at 29; Phases 16 (fight-plan evolution) and 17 (analysis UI) remain open there and are
untouched by this plan.

Every measurement below is against commit `4a73923`: **200 moves / 18 defenses**, profiled over
60 fights and sampled over 300 fights (10,684 move selections). Registry facts are deterministic;
sampled figures vary run to run because rosters are generated unseeded.

**Read Part 1 before doing anything.** It contains the constraints that decide whether a change is
free or expensive, and one of them has already been violated once.

---

# Part 1 — Constraints

## 1.1 The balance contract governs everything

From the parent plan:

> total finishes **60.39%**, KO **16.48%**, TKO **19.04%**, preserved to two decimal places
> against the 3,840-bout corpus in `analysis/fight_engine_baseline.json`.

**Every change must be classified before work starts:**

| Class | Definition | Calibration cost |
|---|---|---|
| **A — Presentation** | New move *names*, labels, commentary. No damage, position, or RNG effect. | Free. Verify anyway. |
| **B — Selection** | Changes which existing technique is chosen. No new mechanical consequence. | Free if it consumes no mechanics RNG. Verify. |
| **C — Mechanical** | New damage channel, position transition, gas cost, or stoppage path. | **Requires deliberate recalibration and sign-off.** |

The lesson from `4a73923`: adding body-punch damage plus a gas drain looked like a small,
obviously-correct change. It moved the corpus from 60.39% to **66.43%** finishes, almost entirely
by making the `body > 24` injury stoppage reachable for the first time. It was reverted to
targeting-only and the corpus returned to an exact match.

> **A Class C change is never a side effect of a Class A or B one.**

Note that the `fight_engine_regression_test` suite checks **determinism only** — its own comment
says the full generator enforces the distribution. Passing tests is not evidence of calibration.
The gate is exit 0 with `"failures": []` from:

```bash
py -3 analysis/generate_fight_engine_baseline.py --verify analysis/fight_engine_baseline.json
```

## 1.2 Move IDs are a save-compatibility contract

Fighters persist `signature_moves`, `move_mastery` and `career_signature_stats` **keyed by
`move_id`**, and `database_editor.py` exposes move IDs directly to the user
(*"Stable move ID from fight_moves.py"*).

> **A `move_id` may be added. It may never be renamed or removed.**

Retiring a technique means marking it `deprecated=True` and excluding it from selection while it
stays in the registry so old saves still resolve.

## 1.3 Selection is already 10% of simulation time

Profile over 60 fights (5.14s total):

```
select_exchange_move    2,198 calls    0.539 s    10% of total sim time
  candidates scored per call    mean 6.3, max 33
  total candidate scorings      13,869
  distinct (action, position) keys       65        (~34 calls each)
```

`legal_moves()` is a **linear scan of the whole tuple on every call** — 7.4 µs at 200 moves. Two
things scale badly: the scan itself, and candidates scored per call (mean 6.3 today, ~25 at 800
moves). At 800 moves with no changes, selection becomes roughly **a third of simulation time**.
World advancement already has performance regression coverage, so this is a hard constraint.

**But the workload is almost perfectly cacheable:** only **65 distinct `(action, position)` keys**
are ever used, each hit ~34 times per 60 fights.

## 1.4 Tags are unvalidated strings

`tags`, `defense_families`, `entry_family` and `attack_path` are free-form strings compared against
literals scattered through `fight_engine.py`. A typo — `"style_finisher"` for `"style-finisher"` —
silently disables the rarity gate and the anti-dilution bypass with no error. At 200 moves that is
a lurking bug; at 800 authored by hand it is a certainty.

## 1.5 Invariants the tests encode

All four were broken and repaired during `4a73923`. Any change to selection must preserve them:

1. a live counter window always resolves into a counter technique;
2. accumulated exertion reduces high-energy technique selection;
3. authored style content is never diluted by the variety draw;
4. selection consumes **no** mechanics RNG — use a bout-local deterministic fingerprint, as
   `select_exchange_move` and `punch_target_shares` do.

---

# Part 2 — Where The Gaps Are

Measured, not assumed.

## 2.1 Legal-pool depth by position

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
of all beats — which is why it carries **67% of every submission beat in the game**. This is the
single largest remaining concentration.

## 2.2 Style coverage is lopsided

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

## 2.3 The chain system is mostly unused

**49 of 200 moves declare `follow_ups`.** `select_exchange_move` awards a **+10 bonus** for
continuing a live chain — the largest contextual term in the function — and three quarters of the
catalogue can never trigger it.

## 2.4 Positions the engine cannot enter

`pocket`, `turtle`, `standing back control` and `leg entanglement` are never reached; `front
headlock` and `failed shot` fire once or twice per 300 fights and not at all in a 60-fight sample.

**16 moves exist only in positions the engine can never enter** — a deterministic property of the
registry, listed in Phase 34. A further handful go unselected in any given sample for softer
reasons (skill and style gates, rarity), so a 300-fight run typically reports 27-34 unused of 200.
The 16 are the structural floor and the ones worth fixing.

The orphan list includes `front_headlock_posture_out`, authored in commit `4a73923` **into a
position the engine cannot reach** - the exact mistake Step 6 exists to catch, made while fixing
this very system.

---

# Part 3 — Architecture

`fight_moves.py` is one 1,127-line module holding a single `MOVE_DEFINITIONS` tuple. At 800 moves
that is ~4,500 lines in one literal — unreviewable diffs and constant merge conflicts.

## 3.1 Target structure

Replace it with a package that keeps the **exact same import surface**:

```
fight_moves/
    __init__.py          # public API only - re-exports, nothing else
    schema.py            # MoveDefinition, DefenseDefinition, builders, TAG vocabulary
    index.py             # MoveIndex: precomputed lookup tables
    validation.py        # registry validation, reachability, coverage reports
    chains.py            # follow-up graph: cycle detection, depth, orphan detection
    defenses.py          # DEFENSE_DEFINITIONS
    catalogue/
        __init__.py      # ordered concatenation of every module below
        punches.py
        kicks.py
        clinch.py
        takedowns.py
        ground_control.py
        passes.py
        submissions.py
        escapes.py
        scrambles.py
        style_signatures.py
```

`fight_moves/__init__.py` must continue to export exactly what the codebase imports today:

```python
MOVE_REGISTRY, MOVE_DEFINITIONS, MOVE_REGISTRY_ERRORS,
DEFENSE_REGISTRY, DEFENSE_REGISTRY_ERRORS,
legal_moves, legal_defenses,
normalize_signature_moves, normalize_move_mastery
```

Eleven modules import from it and none should need to change: `fight_engine.py`, `world.py`,
`events.py`, `seeding.py`, `persistence.py`, `database_editor.py`, `universe_validation.py`,
`fight_engine_audit.py`, `fight_engine_regression_test.py`, `smoke_test.py`, and
`analysis/expand_authored_signatures.py`.

**Ordering is load-bearing.** `catalogue/__init__.py` must concatenate modules in a fixed, explicit
order, and `MOVE_DEFINITIONS` must preserve today's exact sequence for existing moves. Selection
tie-breaks on `move_id` and the generic fallback depend on candidate order; a reshuffle would move
the corpus.

## Step 0 — Parity harness (do this first)

Before any restructuring, build the tool that proves restructuring changed nothing.

```
tools/move_registry_parity.py
```

- Dumps every move as a normalized, sorted record — all fields, fully expanded.
- Dumps `legal_moves(action, position, target)` for **every** combination in the cross product of
  known actions × 14 positions × {"", "head", "body", "leg"} — ids **in order**.
- Writes a single hash plus the full dump to `analysis/move_registry_parity.json`.

Capture it on `4a73923`. After every structural step, regenerate and diff. A byte-identical dump
plus a clean corpus verify is the only acceptable evidence that a refactor is behaviour-preserving.

**Acceptance:** parity dump committed; a deliberately reordered definition is proven to fail it.

## Step 1 — Schema and tag vocabulary

`fight_moves/schema.py` holds `MoveDefinition`, `DefenseDefinition`, the `move()` / `defense()`
builders, and — new — a closed vocabulary:

```python
MOVE_TAGS = frozenset({
    "strike", "punch", "kick", "knee", "elbow", "body", "head", "leg",
    "combination", "mixed-combination", "counter", "setup", "feint",
    "power", "high-risk", "spinning", "creative",
    "finisher", "style-combination", "style-finisher",
    "wrestling", "entry", "takedown", "trip", "clinch", "cage", "control",
    "ride", "pressure", "underhook", "whizzer",
    "ground", "guard", "pass", "transition", "scramble", "mount",
    "back-control", "front-headlock", "turtle",
    "submission", "choke", "joint-lock", "leg-lock",
    "escape", "defense", "recovery", "shell", "movement", "smother",
})

BEHAVIOURAL_TAGS = frozenset({
    "high-risk", "finisher", "style-combination", "style-finisher", "counter",
})
```

`BEHAVIOURAL_TAGS` is the set the engine branches on. Reference it from `fight_engine.py` rather
than repeating string literals, so a rename is a one-line change instead of a silent behaviour loss.

Validation additions:

- every tag ∈ `MOVE_TAGS`, every defense family ∈ a matching `DEFENSE_FAMILIES` set;
- `attack_path` and `entry_family` drawn from closed vocabularies;
- **no duplicate `move_id`, and no `move_id` removed relative to the parity dump** — §1.2 enforced
  mechanically.

**Acceptance:** a move tagged `"style_finisher"` fails validation at import with a clear message.

## Step 2 — MoveIndex

`fight_moves/index.py`. Build every lookup once at import; make `legal_moves` a dict hit.

```python
class MoveIndex:
    """Precomputed move lookups. Built once at import, immutable thereafter."""

    def __init__(self, definitions):
        self._by_key = {}            # (action, position, target) -> tuple[MoveDefinition]
        self._by_action = {}         # action -> tuple
        self._by_style = {}          # style  -> tuple
        self._by_tag = {}            # tag    -> frozenset[move_id]
        ...
```

`legal_moves(action, position, target)` becomes a single dict lookup returning a pre-built tuple,
in definition order, with the existing target semantics preserved exactly:

- a move with `targets` and a matching `target` is legal;
- a move with `targets` and **no** `target` is excluded;
- a move with no `targets` is always legal.

The key space is bounded — actions × 14 positions × 4 targets, and only ~65 keys are ever hit — so
full precomputation is cheap.

**Expected effect:** `legal_moves` goes from 7.4 µs and linear-in-catalogue to sub-microsecond and
constant. This is what makes 800 moves cost the same as 200 at lookup time.

**Acceptance:** parity dump byte-identical; `legal_moves` timing flat between a 200-move and an
800-move registry; corpus verify exact.

## Step 3 — Decompose `select_exchange_move`

Today it is a single ~260-line function that filters, scores, draws, and builds a 25-key payload
inline. Split it inside `fight_engine.py` — the engine keeps owning selection, only the *data*
lives in the package:

| New method | Responsibility |
|---|---|
| `_move_candidates(actor, action, position, target, state)` | Index lookup, then style / counter / finisher-eligibility filtering |
| `_move_static_score(actor, definition)` | Proficiency, style bonus, signature, mastery — **no state**, therefore cacheable |
| `_move_contextual_score(...)` | Existing `contextual_score`, lifted out |
| `_move_rarity_gate(actor, definition, fingerprint)` | The high-risk / finisher authored-rarity gates |
| `_select_from_pool(eligible, ...)` | Deterministic weighted draw, authored-content bypass, counter-window guard |
| `_move_payload(definition, ...)` | The payload dict, built once |

All four invariants in §1.5 must survive the split; each already has a test.

**Acceptance:** pure refactor — parity dump identical, corpus verify exact, all six fight suites
pass, with no behavioural edit in the same commit.

## Step 4 — Per-fight score caching

`_move_static_score` depends only on `(fighter, move_id)` — attack-skill means, style bonus,
signature membership and mastery do not change mid-fight. This is the cost that scales with
catalogue depth.

Follow the existing precedent (`_fight_skill_bundle_cache`, established in `simulate_fight`):

```python
self._fight_move_score_cache = {}      # (id(fighter), move_id) -> float
```

Created and torn down in the same place as the bundle cache, so it can never leak between fights.
With ~34 calls per `(action, position)` key and 6–25 candidates each, hit rate should be high after
round 1. Combined with Step 2 this keeps selection near its current 10% cost at four times the
catalogue size.

**Acceptance:** parity dump identical; profile shows `select_exchange_move` ≤ 15% of sim time with
an 800-move registry; `simulation_performance_regression_test` passes.

## Step 5 — Chain graph

`fight_moves/chains.py`. Phase 31 takes `follow_ups` coverage from 49/200 to 150+; at that density
the relationships need to be a validated graph, not scattered tuples.

- Build a directed graph of `move_id -> follow_ups` at import.
- **Reject cycles** — a chain that loops would let the +10 sequence bonus feed itself.
- Report unreachable chain targets and max chain depth.
- Expose `chain_depth(move_id)` so the trace can record how deep a sequence ran.

**Acceptance:** a deliberately introduced cycle fails validation; chain depth appears in the trace.

## Step 6 — Reachability and coverage tests

The step that prevents the failure that made 30 moves dead content, and the most valuable long-term
addition here.

`fight_moves/validation.py` gains report builders; a new `fight_move_coverage_regression_test.py`
asserts on them.

**Reachability.** For every move, is there any `(action, position, target)` the engine can actually
produce where the move is legal, with a plausible fighter clearing its `minimum_skill` and style
gates? Checked against positions the engine can *enter*, not positions declared in the registry —
that distinction is exactly what was missed, and it is still being missed: `4a73923` added a
seventeenth orphan while fixing move variety.

```python
def unreachable_moves(reachable_positions, reachable_actions, roster_skill_p50):
    """Moves that no fight can ever select, with the reason why."""
```

Reasons must be distinguished, because the fixes differ entirely:
`position-never-entered` / `target-never-requested` / `skill-gate-above-roster` /
`style-gate-unsatisfiable` / `no-parent-action`.

**Coverage floors.** Assert minimum pool depth for every `(action, reachable position)` pair, and
minimum authored moves per playable style. Both are currently violated (§2.1, §2.2), so land these
as **warnings with a documented allow-list**, then convert to hard failures as the phases close each
gap.

**Acceptance:** the report reproduces today's 16 position-orphaned moves with correct reasons; the
allow-list shrinks to empty as phases land; a new move authored into an unreachable position fails
CI.

## Step 7 — Authoring ergonomics

At 800 moves, hand-writing 12-field constructors is the bottleneck.

**Presets.** Style-and-family defaults so a new technique declares only what is distinctive:

```python
punch("lead_uppercut", "lead uppercut", styles=("Boxer",), tags=("power",))
# expands to the standard punch skill set, positions, defense families and range band
```

**A schema reference doc** — `docs/FIGHT_MOVE_SCHEMA.md` — documenting every field, the closed tag
vocabulary, the per-tag validator contracts (kicks need target/side/range/defense-families;
takedowns need entry and finish positions; submissions need attack path and failure outcomes;
finishers must be skill-gated standing strikes), and the move-ID save contract.

**Acceptance:** a new ordinary punch is one line; presets proven not to alter any existing
definition via the parity dump.

## 3.2 Decision: keep moves as Python, not JSON

Worth stating explicitly because it will come up.

Moves stay Python literals in versioned modules. **Do not** move them to JSON/TOML data files, and
do not make them editable in the Database Editor beyond the existing per-fighter move ID selection.

- Validation runs at import and hard-fails; a data file needs a parallel loader plus error surfacing
  in the app.
- `MoveDefinition` is a frozen dataclass with tuple fields — cheap to construct once, immutable,
  directly indexable. JSON adds a deserialization layer with no benefit.
- The balance contract means user-editable techniques would let a save drift off calibration with no
  way to detect it.
- Python literals diff and review well once split into catalogue modules, which Step 1 does.

Revisit only if user-authored moves become an explicit product goal. That is a different feature
with its own contract, not a refactor.

---

# Part 4 — Content Phases

## Phase 29 — Guard and half-guard submissions

**Class B.** The highest-value phase here: one technique currently serves 31.4% of the fight.

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
`validate_move_registry` requires every `submission`-tagged move to declare `attack_path` and
`failure_outcomes`; reuse the existing failure vocabulary so `resolve_submission` needs no change.

**Acceptance:** `submission` top-move share falls from **67%** to **≤ 25%**; guard and half-guard
pools hold ≥ 6 legal techniques each; corpus verify exact. If submission *rate* moves at all, the
phase has leaked into Class C.

## Phase 30 — Escapes, reversals and guard recovery

**Class B.** `recover_guard` has one or two techniques in every ground position, and the bottom
fighter's vocabulary is almost entirely failure.

- 8–10 `recover_guard` techniques: knee-shield recovery, hip-heist, elbow-frame recovery, granby
  roll, shin-to-shin retention, half-guard underhook recovery, bridge-and-shrimp.
- 4–6 `sweep` additions weighted toward the bottom fighter winning: hip bump, flower sweep,
  butterfly hook sweep, John Wayne sweep, electric chair.
- 3–4 `stand_up` techniques beyond `technical_standup`: wall walk, kick-away and stand, shin-post
  escape.

**Acceptance:** every ground position offers ≥ 4 legal `recover_guard` techniques; distinct
bottom-side moves per fighter rises measurably; sweep and stand-up **success rates unchanged** —
these are new names on existing resolution maths.

## Phase 31 — Follow-up chains across the catalogue

**Class B**, and the highest impact-per-effort in this plan: it adds almost no moves, it wires up
the ones that exist.

Raise `follow_ups` coverage from **49/200 to ≥ 150/200**. Every move should name 1–3 plausible
successors so the +10 sequence bonus can fire:

- strikes chain into strikes and entries (jab → cross → level change);
- entries chain into finishes (double-leg entry → double-leg finish → ride);
- passes chain into submissions and back-takes (knee slice → side control → arm triangle);
- escapes chain into scrambles and stand-ups.

Add a `chain_depth` counter to the trace (Step 5) so sequences can be reported and tested.

**Acceptance:** ≥ 150 moves declare follow-ups, validator confirms every id resolves; share of
selections carrying a non-empty `sequence_source_id` rises from near-zero to **≥ 12%**; median chain
length ≥ 2 in fights reaching round 2; corpus verify exact.

## Phase 32 — Style identity for thin styles

**Class B.** Bring `Grappler` (2 moves), `Well-Rounded` (3) and `Taekwondo` (12) to ≥ 18 authored
moves each, and add one `style-combination` plus one `style-finisher` for any style missing them.

- **Grappler** — a generalist grappling identity distinct from BJJ and Wrestler: chain wrestling
  into front headlock, scramble-heavy back exposure, no-gi pressure passing.
- **Well-Rounded** — the "no holes" identity: level-change feints off punches, strike-to-clinch,
  clinch-to-strike exits.
- **Taekwondo** — the existing 12 are kick-heavy; add distance management, the back-leg side kick
  as a range tool, and the spin-off-the-check counter.

**Acceptance:** no playable style below 18 authored moves; every style owns ≥ 1 style-combination
and ≥ 1 style-finisher; style-vs-style finish rates stay within corpus subgroup tolerances — this
phase makes styles more legible, not stronger.

## Phase 33 — Named defenses

**Class B.** 18 defenses serve 200 moves, so defensive commentary repeats heavily and
`select_exchange_defense` has little to choose from.

Expand `DEFENSE_DEFINITIONS` from 18 to ~40, covering families the move registry already references
but under-serves: shoulder roll, long guard, cross-guard catch, elbow-in body block, underhook
recovery, hip-to-hip escape, wrist-fight break, grip strip, posture-and-frame, leg-lock rotation
defense.

**Acceptance:** every `defense_families` value referenced by a move resolves to ≥ 2 concrete
defenses; defensive-clause repetition falls below 10 uses per line per 300 fights; corpus verify
exact.

## Phase 34 — Unreachable positions

**Class C. Do not start until Phases 29–33 are landed and verified.**

The phase that unlocks the 16 position-orphaned moves — the guillotine family (`guillotine_choke`,
`anaconda_choke`, `darce_choke`), the leg-lock game (`heel_hook`, `toe_hold`), the turtle
(`turtle_breakdown`, `sit_out_reversal`, `turtle_wrist_ride_strikes`), standing back control
(`rear_waist_ride`, `lift_mat_return`, `limp_leg_escape`) and the failed-shot scrambles
(`chained_reshot`, `whizzer_recovery`, `snapdown_front_headlock`). Real engine surgery on position state, and it
**will** move the corpus.

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

**Sequencing within the phase:**

1. `failed shot` and `front headlock` — smallest state surface, biggest content unlock.
2. `turtle` and `standing back control` — they share the scramble vocabulary.
3. `leg entanglement` — interacts with the submission model.
4. `pocket` last — it changes standing distance for every fight and carries the widest blast radius.

**Recalibrate after each sub-step, not once at the end.** Expect submissions to rise (the guillotine
is one of the sport's most common finishes and is currently impossible) and expect to need
offsetting tuning to hold 60.39%. That trade is a deliberate, signed-off decision — record any new
accepted numbers in the parent plan's balance contract.

**Acceptance:** all 14 registry positions reachable, `pocket` occupancy ≥ 8% of standing beats;
position-orphaned moves falls from **16** to **0**; guillotine-family and leg-lock submissions appear
in normal play; corpus either matches 60.39/16.48/19.04 exactly, **or** a new calibration is
explicitly accepted and written into the parent plan.

---

# Part 5 — Sequencing

## 5.1 Architecture steps

| Step | Class | Depends on | Behaviour change |
|---|---|---|---|
| 0 — Parity harness | tooling | — | none |
| 1 — Schema + tag vocabulary | refactor | 0 | none |
| 2 — MoveIndex | refactor | 0, 1 | none |
| 3 — Decompose selection | refactor | 0 | none |
| 4 — Score caching | performance | 3 | none |
| 5 — Chain graph | structure | 1 | trace field added |
| 6 — Reachability + coverage tests | tooling | 1, 2 | none |
| 7 — Authoring presets | ergonomics | 1 | none |

**Steps 0–4 and 6–7 are all behaviour-preserving.** Each must end with a byte-identical parity dump
and an exact corpus verify. If either moves, the step is wrong — find the cause, do not absorb it.

## 5.2 Combined delivery order

| Slice | Contents | Rationale |
|---|---|---|
| **1** | Steps 0, 1, 2 | Parity harness, schema, index. Removes the scaling wall before any bulk authoring. |
| **2** | Step 6 | Reachability tests. Would have caught the 16 orphans the day they were written; needed before adding 600 more. |
| **3** | Phase 29 | Biggest single concentration in the game, self-contained, immediately visible. |
| **4** | Steps 3, 4, 7 | Decompose, cache, presets. Do once the index is proven and before the largest authoring phases. |
| **5** | Step 5 + Phase 31 | Chain graph and the follow-up wiring it validates — same work, land together. |
| **6** | Phases 30, 33 | Bottom-position and defensive vocabulary. |
| **7** | Phase 32 | Style parity pass. |
| **8** | Phase 34 | Class C surgery, sub-stepped and recalibrated throughout. |

Slices 1–2 pay for themselves immediately and should land before anything else.

## 5.3 Working rules

1. **Classify before writing code.** A/B work must leave the corpus untouched; if the verify moves,
   something leaked into Class C — find it.
2. **Never consume the mechanics RNG** for naming or selection.
3. **Run the validator early.** Per-tag contracts are enforced at import.
4. **Preserve authored content from dilution.** New style combinations, style finishers and
   signature moves must be tagged so they inherit the anti-dilution bypass.
5. **Guard the §1.5 invariants.**
6. **Report variety with the same harness every time** so numbers stay comparable across phases.

---

# Part 6 — Targets

## Content

| Metric | Now (`4a73923`) | After 29–33 | After 34 |
|---|---|---|---|
| Registry size | 200 | ~270 | ~275 |
| Defenses | 18 | ~40 | ~40 |
| Moves orphaned by unreachable position | **16** | 16 | **0** |
| Moves unused in a 300-fight sample | 27–34 | ~25 | **≤ 8** |
| Distinct moves per fighter per fight | 12.6 | 17–19 | **20–24** |
| Top 10 moves' share | 34.0% | ≤ 28% | ≤ 25% |
| `submission` top-move share | 67% | **≤ 25%** | ≤ 20% |
| Moves declaring follow-ups | 49 | **≥ 150** | ≥ 200 |
| Chained selections | ~0% | **≥ 12%** | ≥ 15% |
| Styles below 18 authored moves | 3 | **0** | 0 |
| Positions never reached | 4 (+2 near-zero) | 4 | **0** |
| Finish rate | 60.39% | 60.39% (unchanged) | re-accepted |

## Architecture

| Metric | Now | After |
|---|---|---|
| Largest single catalogue file | 1,127 lines | ≤ 400 lines |
| `legal_moves` cost | 7.4 µs, linear in catalogue | sub-µs, constant |
| `select_exchange_move` share of sim time | 10% @ 200 moves | ≤ 15% @ 800 moves |
| Tag typos detectable | no | at import |
| Unreachable moves detectable | no | in CI, with reasons |
| Chain cycles detectable | no | at import |
| Adding an ordinary move | 12-field constructor | one preset line |
| Move-ID save contract | convention | enforced |
| Catalogue headroom | ~200 | 800+ |
