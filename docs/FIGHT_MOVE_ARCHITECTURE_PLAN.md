# Fight Move System — Architecture Plan For Scaling The Catalogue

Companion to `docs/FIGHT_ENGINE_MOVE_EXPANSION_PLAN.md`, which says *what* moves to add. This
document says *what code has to change* so the catalogue can grow from **200** to **800+** moves
without the authoring, performance, or correctness cost growing with it.

Measured against commit `4a73923`.

---

## The Four Constraints That Shape Everything

### 1. Move IDs are a save-compatibility contract

Fighters persist `signature_moves`, `move_mastery` and `career_signature_stats` **keyed by
`move_id`**, and `database_editor.py` exposes move IDs directly to the user
(*"Stable move ID from fight_moves.py"*).

> **A `move_id` may be added. It may never be renamed or removed.**

Retiring a technique means marking it `deprecated=True` and excluding it from selection while it
stays in the registry so old saves still resolve. Every refactor below has to preserve IDs
exactly.

### 2. The balance contract

60.39% / 16.48% / 19.04% to two decimal places. Restructuring must be **provably** behaviour-
preserving: the corpus verify has to return an exact match after every structural step, not a
"close enough". This is the reason for the parity harness in Step 0.

### 3. Selection is already 11% of simulation time

Profile over 60 fights (4.51s total):

```
select_exchange_move    2,585 calls    0.493 s    11% of total sim time
  candidates scored per call    mean 6.2, max 33
  total candidate scorings      16,144
  distinct (action, position) keys       65        (~40 calls each)
```

`legal_moves()` is a **linear scan of the whole tuple on every call** — 7.4 µs at 200 moves. Two
things scale badly:

- the scan itself, linear in catalogue size;
- candidates scored per call, which rises with catalogue depth (mean 6.2 today, ~25 at 800 moves).

At 800 moves and no changes, selection becomes roughly **a third of simulation time**. World
advancement already has performance regression coverage, so this is a hard constraint, not a
nicety.

**But note the shape of the data:** only **65 distinct `(action, position)` keys** are ever used,
each hit ~40 times per 60 fights. The workload is almost perfectly cacheable.

### 4. Tags are unvalidated strings

`tags`, `defense_families`, `entry_family` and `attack_path` are free-form strings compared with
literals scattered through `fight_engine.py`. A typo — `"style_finisher"` for `"style-finisher"` —
silently disables the rarity gate and the anti-dilution bypass with no error. At 200 moves that is
a lurking bug; at 800 authored by hand it is a certainty.

---

## Target Structure

`fight_moves.py` is one 1,040-line module holding a single `MOVE_DEFINITIONS` tuple. At 800 moves
that is ~4,000 lines in one literal — unreviewable diffs and constant merge conflicts.

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

Eleven call sites across `fight_engine.py`, `models.py`, `database_editor.py`, the analysis
scripts and six regression tests import from it. None of them should need to change.

**Ordering is load-bearing.** `catalogue/__init__.py` must concatenate modules in a fixed,
explicit order, and `MOVE_DEFINITIONS` must preserve today's exact sequence for the moves that
already exist. Selection tie-breaks on `move_id` and the generic fallback depend on candidate
order; a reshuffle would move the corpus.

---

## Step 0 — Parity Harness (do this first)

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

---

## Step 1 — Schema And Tag Vocabulary

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

`BEHAVIOURAL_TAGS` is the set the engine branches on. Document it here and reference it from
`fight_engine.py` rather than repeating string literals, so a rename is a one-line change instead
of a silent behaviour loss.

Validation additions:

- every tag ∈ `MOVE_TAGS`, every defense family ∈ a matching `DEFENSE_FAMILIES` set;
- `attack_path` and `entry_family` drawn from closed vocabularies;
- **no duplicate `move_id`, and no `move_id` removed relative to the parity dump** — the save
  contract, enforced mechanically.

**Acceptance:** a move with tag `"style_finisher"` fails validation at import with a clear message.

---

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

The key space is small — actions × 14 positions × 4 targets, and only ~65 keys are ever hit — so
full precomputation is cheap and bounded.

**Expected effect:** `legal_moves` goes from 7.4 µs and linear-in-catalogue to sub-microsecond and
constant. This is what makes 800 moves cost the same as 200 at lookup time.

**Acceptance:** parity dump byte-identical; `legal_moves` timing flat between a 200-move and an
800-move registry; corpus verify exact.

---

## Step 3 — Decompose `select_exchange_move`

Today it is a single ~260-line function that filters, scores, draws, and builds a 25-key payload
inline. Split it inside `fight_engine.py` (the engine keeps owning selection — only the *data*
lives in the package):

| New method | Responsibility |
|---|---|
| `_move_candidates(actor, action, position, target, state)` | Index lookup, then style / counter / finisher-eligibility filtering |
| `_move_static_score(actor, definition)` | Proficiency, style bonus, signature, mastery — **no state**, therefore cacheable |
| `_move_contextual_score(...)` | Existing `contextual_score`, lifted out |
| `_move_rarity_gate(actor, definition, fingerprint)` | The high-risk / finisher authored-rarity gates |
| `_select_from_pool(eligible, ...)` | The deterministic weighted draw, including the authored-content bypass and counter-window guard |
| `_move_payload(definition, ...)` | The payload dict, built once |

Every existing invariant must survive the split, and each already has a test:

1. a live counter window always resolves into a counter technique;
2. accumulated exertion reduces high-energy selection;
3. authored style content is never diluted by the variety draw;
4. selection consumes **no** mechanics RNG.

**Acceptance:** pure refactor — parity dump identical, corpus verify exact, all six fight suites
pass with no behavioural edit in the same commit.

---

## Step 4 — Per-Fight Score Caching

`_move_static_score` depends only on `(fighter, move_id)` — attack-skill means, style bonus,
signature membership and mastery do not change mid-fight. This is the cost that scales with
catalogue depth.

Follow the existing precedent (`_fight_skill_bundle_cache`, established in `simulate_fight`):

```python
self._fight_move_score_cache = {}      # (id(fighter), move_id) -> float
```

Created and torn down in the same place as the bundle cache, so it can never leak between fights.

With ~40 calls per `(action, position)` key and 6–25 candidates each, the hit rate should be high
after the first round. Combined with Step 2 this is what keeps selection near its current 11% cost
at four times the catalogue size.

**Acceptance:** parity dump identical; profile shows `select_exchange_move` ≤ 15% of sim time with
an 800-move registry; `simulation_performance_regression_test` passes.

---

## Step 5 — Chain Graph

`fight_moves/chains.py`. Expansion Phase 31 takes `follow_ups` coverage from 49/200 to 150+; at
that density the chain relationships need to be a validated graph, not scattered tuples.

- Build a directed graph of `move_id -> follow_ups` at import.
- **Reject cycles** — a chain that loops would let the +10 sequence bonus feed itself.
- Report unreachable chain targets and max chain depth.
- Expose `chain_depth(move_id)` so the trace can record how deep a sequence ran.

**Acceptance:** a deliberately introduced cycle fails validation; chain depth appears in the trace;
median observed chain length ≥ 2 in fights reaching round 2.

---

## Step 6 — Reachability And Coverage Tests

This is the step that prevents the failure that made 30 moves dead content, and it is the most
valuable long-term addition in this document.

`fight_moves/validation.py` gains report builders; a new
`fight_move_coverage_regression_test.py` asserts on them:

**Reachability.** For every move, is there any `(action, position, target)` the engine can
actually produce where the move is legal, with a plausible fighter clearing its `minimum_skill`
and style gates? Reachability is checked against the set of positions the engine can *enter*, not
the positions declared in the registry — that distinction is exactly what was missed.

```python
def unreachable_moves(reachable_positions, reachable_actions, roster_skill_p50):
    """Moves that no fight can ever select, with the reason why."""
```

Reasons must be distinguished, because the fixes differ entirely:
`position-never-entered` / `target-never-requested` / `skill-gate-above-roster` /
`style-gate-unsatisfiable` / `no-parent-action`.

**Coverage floors.** Assert minimum pool depth for every `(action, reachable position)` pair, and
minimum authored moves per playable style. Both are currently violated —
`submission` in guard is 1, `Grappler` has 2 moves — so land these as **warnings with a documented
allow-list**, then convert to hard failures as the expansion phases close each gap.

**Acceptance:** the report reproduces today's 30 unreachable moves with correct reasons; the
allow-list shrinks to empty as phases land; a new move authored into an unreachable position
fails CI.

---

## Step 7 — Authoring Ergonomics

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

**Acceptance:** a new ordinary punch is one line; presets are proven not to alter any existing
definition via the parity dump.

---

## Decision: Keep Moves As Python, Not JSON

Worth stating explicitly because it will come up.

Moves stay Python literals in versioned modules. **Do not** move them to JSON/TOML data files, and
do not make them editable in the Database Editor beyond the existing per-fighter move ID
selection.

Reasons:

- Validation runs at import and hard-fails; a data file needs a parallel loader plus error
  surfacing in the app.
- `MoveDefinition` is a frozen dataclass with tuple fields — cheap to construct once, immutable,
  and directly indexable. JSON adds a deserialization layer with no benefit.
- The balance contract means user-editable techniques would let a save drift off calibration with
  no way to detect it.
- Python literals diff and review well once split into catalogue modules, which Step 1 does.

Revisit only if user-authored moves become an explicit product goal. That is a different feature
with its own contract, not a refactor.

---

## Sequencing

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

**Steps 0–4 and 6–7 are all behaviour-preserving.** Every one of them must end with a byte-identical
parity dump and an exact corpus verify. If either moves, the step is wrong — do not absorb the
drift.

Land the whole of this before the expansion phases author content in bulk. Steps 0–2 and 6 in
particular pay for themselves immediately: the index removes the scaling wall, and the
reachability test would have caught the 30 dead moves the day they were written.

---

## Success Criteria

| Metric | Now | After |
|---|---|---|
| Largest single catalogue file | 1,040 lines | ≤ 400 lines |
| `legal_moves` cost | 7.4 µs, linear in catalogue | sub-µs, constant |
| `select_exchange_move` share of sim time | 11% @ 200 moves | ≤ 15% @ 800 moves |
| Tag typos detectable | no | at import |
| Unreachable moves detectable | no | in CI, with reasons |
| Chain cycles detectable | no | at import |
| Adding an ordinary move | 12-field constructor | one preset line |
| Move-ID save contract | convention | enforced |
| Catalogue headroom | ~200 | 800+ |
