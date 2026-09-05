# Handoff prompt — fighter portrait system

Copy everything below the line into the other AI's first message.

---

You are implementing the fighter portrait system for **MMA Warriors**, a Python/Tkinter fight-promotion
management game at `D:\CodexFILES\MMA Warriors` (branch `dev`).

## Read first

1. `docs/FIGHTER_PORTRAIT_IMPLEMENTATION_SPEC.md` — **this is the authority.** It contains the full
   data model, all trait tables, region rules, rendering routes, integration points, tests and
   acceptance criteria. Follow it.
2. `analysis/portraits/portrait_comic_reference.py` — a working numpy prototype that proves the
   model. **Reference only, do not ship it** (see §14 of the spec for its defects and §9 for why it
   cannot be the runtime renderer).
3. `docs/FIGHTER_PORTRAIT_SYSTEM_DESIGN.md` — background and rationale. Read only if you need the
   *why* behind a decision.

## The task

Replace the current initials-badge portrait with per-fighter comic-style portraits that are unique,
deterministic across launches, region-appropriate, reflect age and career damage, and support
hand-authored appearances for named real fighters.

Today, **70.7% of the game's 4,856 fighters share a pixel-identical portrait**, because per-fighter
variation is two colours from 9 palettes plus two initials.

## Hard constraints — violating any of these is a defect

1. **Runtime must be standard library only.** No numpy, no PIL, no new dependency. numpy is listed
   in `requirements.txt` but is *optional* and used only by the audio path — the game must run
   without it. numpy is allowed in build-time and dev-only scripts.
2. **Hash `fighter_id`, never `name`.** Names change. Use one independent hash draw per trait
   (`blake2b(f"{fighter_id}|{trait}")`) so adding a trait later does not reshuffle existing fighters.
3. **No appearance trait may influence any rating, ability, popularity or simulation value.** Purely
   cosmetic. Add a test that enforces this.
4. **Never rename or remove a trait key or style id once shipped** — they are persisted in saves.
   Adding is fine.
5. **Appearance is region-conditioned, not uniformly random.** The hash selects *within* a
   distribution derived from `birth_country → nationality → region`. Distributions must be wide and
   anatomical only. Read §7 of the spec, including the guardrails, before writing these tables.
6. **Do not break existing tests.** In particular `smoke_test.py:1486` asserts the retired portrait
   seal is `#315a70` with "RTD" text.

## Build order

Follow §13 of the spec. Steps 1–2 are pure model work with no rendering, fully testable without
drawing a pixel — land those first:

1. `styles.py`, `regions.py`, `identity.py` and their tests. No rendering yet.
2. Persistence fields (`portrait_version`, `portrait_identity`), backfill at `persistence.py:1860`,
   save round-trip test.
3. The stdlib rasteriser and its cache (spec §9 Route A).
4. Replace the four hand-rolled draw sites (`views.py:2898`, `views.py:1035`, `events.py:3123`,
   `events.py:2245`) with a single `render_portrait(canvas, fighter, size, ratings_visible)`.
   Confirm the injured and retired seals now appear on fight-night intros, where they are currently
   missing.
5. State layers: greying, hairline recession, cauliflower ear, scar tissue, swelling.
6. `PORTRAIT_OVERRIDES` tier 1 (~50 named fighters) plus a contact-sheet dev tool that renders 100
   portraits to a PNG so output can be eyeballed in bulk.

## Verification

Run after each step, from the repo root:

```bash
py -3 smoke_test.py
py -3 fighter_profile_regression_test.py
py -3 run_regression_suite.py
```

Portraits are cosmetic, so they must not move the fight-engine calibration. If you touch anything
outside the portrait modules and the four draw sites, also run:

```bash
py -3 analysis/generate_fight_engine_baseline.py --verify analysis/fight_engine_baseline.json
```

That must exit 0 with `"failures": []`.

## Things that will waste your time if you rediscover them yourself

- `birth_region` is **absent from all 1,534 shipped fighters**. `birth_country`, `nationality`,
  `region` and `hometown` are present on 100%. Resolve in that order.
- The facial-hair mask must be a **jaw band only** (`t > 0.735` in head-profile coordinates, minus
  the mouth ellipse). Starting it higher covers the entire face.
- Build the head from a **vertical width profile** (crown → temple → cheekbone → jaw → chin), not a
  union of ellipses. Ellipse unions produce lozenge heads. Cel shadows must follow the surface
  normal of that profile, not an offset ellipse.
- Cornrows and braids run front-to-back, so head-on they read as **vertical colour bands**. That is
  what makes multi-colour dye jobs work.
- If you ever move to baked PNG layers, Tk `subsample` is nearest-neighbour and shatters ink line
  art (2 strokes became 99 fragments at /4). Bake every size offline with area-averaging.

## Deliverable

Working code plus tests, committed in reviewable steps — one commit per build-order step, each with
its tests passing. Do not squash the whole feature into one commit.

Report honestly: if the rendered output does not look good, say so and show it rather than declaring
success. The prototype's own face construction does not read convincingly, and improving that is
part of the job — the spec's trait tables and identity model are sound, the drawing is the open
problem.
