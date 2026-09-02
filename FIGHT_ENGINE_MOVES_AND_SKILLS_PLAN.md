# Fight Engine Moves, Skills and Combinations Plan

## Purpose

This roadmap expands the MMA fight engine with a deeper vocabulary of combinations, techniques and
fighter-specific weapons. It builds on the completed realism roadmap in
`FIGHT_ENGINE_DEVELOPMENT_PLAN.md`; it does not replace or reopen that work.

The objective is to make fighters express *how* they fight more distinctly while preserving the
current result balance. New moves must emerge from skills, stance, position, style, behaviour,
traits, tactics and fatigue. They must never be selected merely to force a winner or finish.

## Non-Negotiable Balance Contract

The accepted 3,840-bout calibration is the release authority for every phase:

- total finishes: **60.39%**;
- KO: **16.48%**;
- TKO: **19.04%**; and
- the existing submission, decision, round-timing, competitive-tier, mismatch, style and behaviour
  distributions retained by `analysis/fight_engine_baseline.json`.

Every phase must run the same fixed corpus before and after the change. The release target is exact
preservation of the three headline percentages to two decimal places. Existing confidence-aware
subgroup tolerances remain diagnostic guardrails, not permission to deliberately move the headline
rates. Do not change `competitive_finish_conversion()`, overwrite final methods, or regenerate the
baseline to conceal drift.

New technique selection must use its own bout-local deterministic stream or reuse already-resolved
mechanical evidence. Adding a move name must not consume the legacy mechanics stream. A technique
that has mechanical consequences must record those consequences explicitly in the trace and pass
the calibration corpus.

## Current-State Audit

The engine already has a strong base:

- 18 supported MMA styles, eight behaviours and 11 fight plans;
- 67 detailed skills across standing, wrestling, ground, clinch, mental and physical groups;
- 18 core actions plus specialized failed-shot, cage, turtle, front-headlock, standing-back-control
  and leg-entanglement actions;
- ordered combination components, location damage, cuts, knockdowns, submissions, positional paths,
  defensive responses and counters in the native trace; and
- a 356-bout full-system test plus the frozen 3,840-bout calibration audit.

The main limitation is granularity. Broad actions such as `power_punch`, `kick`, `takedown`,
`ground_strikes` and `submission` can render several descriptions, but a named move is not yet a
first-class mechanical choice with prerequisites, target, risk, energy cost, defensive answer and
trace identity. Some detailed-skill gaps also make distinct weapons share overly broad ratings.

### Confirmed data-integrity defect

Four shipped MMA records currently contain unsupported `style` values:

| Fighter | Current style | Correct supported style | Behaviour |
| --- | --- | --- | --- |
| Jiri Prochazka | `Dynamic Attacker` | `Kickboxer` | `Dynamic Attacker` |
| Brandon Royval | `Submission Hunter` | `BJJ` | `Dynamic Attacker` |
| Lito Adiwang | `Wushu` | `Sanda` | retain or derive a supported behaviour |
| Kevin Belingon | `Wushu` | `Sanda` | retain or derive a supported behaviour |

Jiri and Royval already contain the correct supported `profile_style`, but the later authored-field
override restores the invalid `style`. Wushu is not a supported runtime style; Sanda is the closest
existing mechanical identity and avoids adding a redundant alias.

The shared universe validator currently checks style/trait/behaviour choices for child-sport
profiles but not for `fighters.all_fighters`. That gap allows all four records to pass release
validation. Normal style-specific seed biases and fight-engine weights then fall back to generic
handling.

## Architecture Direction

### Three separate concepts

Keep these concepts distinct:

1. **Style** describes a fighter's broad technical base, such as Sanda, BJJ or Wrestler.
2. **Behaviour** describes decision temperament, such as Pressure, Counter or Dynamic Attacker.
3. **Move** describes the actual technique attempted, such as a check hook, body-lock trip or
   arm-triangle.

A behaviour must never be accepted as a style. A move must not become a new style merely because one
fighter is known for it.

### Move registry

Introduce one canonical, data-driven MMA move registry. Each move definition should contain:

- stable ID and player-facing name;
- parent action and legal positions;
- target and damage family;
- stance/side requirements where relevant;
- attack skill bundle and defensive skill bundle;
- minimum proficiency or physical prerequisite;
- energy, miss, counter and positional risks;
- possible follow-ups and defensive answers;
- trace tags, commentary family and statistical category; and
- whether it can knock down, cut, submit, change position or only score/control.

The registry is code-owned tuning data, not arbitrary save data. Saves store only stable move IDs
when a fighter has an authored signature or preference. Unknown future IDs are ignored safely.

### Fighter move identity

Add a small optional `signature_moves` list and, only if the audit proves it necessary, a bounded
`move_preferences` mapping. Existing careers default to no authored moves and derive a legal move
pool from style, stance, behaviour, trait and detailed skills. Generated fighters receive a
deterministic bounded move identity during creation; loading or viewing a profile must not consume
simulation RNG or rewrite the save.

Signature status changes selection frequency and presentation identity, not raw finish chance. The
move still succeeds or fails through the relevant skills and defense.

## Phase 0 — COMPLETED — Data Integrity and Expansion Baseline

### Work

- Correct the four shipped records using the mappings above and synchronize every compatibility
  representation of those fighters.
- Validate `style`, `profile_style`, `trait` and `behaviour` for every `fighters.all_fighters` record,
  not only child-sport profiles.
- Make `apply_authored_fighter_overrides()` reject or normalize unsupported enum values rather than
  bypassing the earlier safe fallback. Preserve arbitrary authored text only for genuinely free-text
  fields.
- Add named smoke assertions for all four fighters and a malformed-universe regression proving the
  validator reports unsupported fighter values.
- Extend the full-system audit report with move/action frequency, success, damage, energy, counter,
  position and finish contribution by tier and style.
- Freeze the current action-frequency report before adding techniques.

### Acceptance criteria

- Every newly seeded MMA fighter has a supported style, trait and behaviour.
- The shipped universe passes the shared validator with the four named identities intact.
- Old saves with an unsupported style load safely using a narrow compatibility mapping without
  rewriting the source save merely because it was inspected.
- The 3,840-bout result percentages remain exactly 60.39% / 16.48% / 19.04%.

**Delivered:** the four shipped records now use Kickboxer, BJJ and Sanda as appropriate; the shared
validator covers all MMA style/trait/behaviour fields; authored and legacy-save identity values pass
through narrow compatibility normalization; and new universes assign a supported, distinct secondary
discipline to roughly 65% of fighters without consuming simulation RNG. Secondary styles contribute
a bounded 35% style influence beneath the primary compatibility/search identity and are visible in
Fight Night and profiles. `analysis/fight_engine_action_baseline.json` freezes action frequency,
effectiveness, damage, energy, counters, positions and finishing exchanges across the same 3,840
bouts. The full matrix, persistence, smoke and distribution gates pass at exactly 60.39% / 16.48% /
19.04%.

## Phase 1 — COMPLETED — Technique Registry and Trace Contract

### Work

- Add the canonical move definition and registry validation.
- Add deterministic legal-move-pool resolution from fighter and bout state.
- Add `move_id`, target, attack bundle, defense bundle and follow-up ID to each exchange trace.
- Initially map every move to its existing parent action with **no mechanical modifier**.
- Render existing commentary through the selected move name without changing action outcomes.
- Reject duplicate IDs, missing parent actions, illegal positions, unknown skills and impossible
  follow-up links at startup/test time.

### Acceptance criteria

- Every resolved core action has either a valid move or an explicit generic fallback.
- Replacing move names or commentary cannot alter winner, method, round, cards or statistics.
- Trace additions consume no legacy mechanics RNG and pass exact fixed-seed parity.
- Registry validation is covered without opening Tk.

**Delivered:** `fight_moves.py` initially defined and validated 32 named techniques with stable IDs, parent
actions, positions, targets, skill/defense bundles, style preferences, prerequisites, energy/risk
metadata, follow-ups and tags. Every native exchange now retains a deterministic move payload and
renders its recorded technique; illegal or unavailable techniques fall back explicitly to the broad
action. Selection consumes no RNG. A registry-on/off regression proves winner, method, round, cards
and statistics are identical, the full structural matrix passes, the action baseline is byte-stable,
and the accepted distribution remains 60.39% / 16.48% / 19.04%.

## Phase 2 — COMPLETED — Standing Skills and Boxing Combinations

### Skill audit

First measure whether existing skills can express each candidate. Add a detailed skill only when it
creates a mechanically distinct axis that cannot be represented by a current bundle. Initial
candidates are:

- `combination_punching` — sequencing accuracy and balance across multi-strike chains;
- `body_punching` — committed body-shot placement rather than generic punch technique;
- `counter_timing` — timing the return, distinct from defensive head movement; and
- `distance_management` — only if footwork plus feints cannot already represent it cleanly.

New skills require model defaults, generated distributions, gym development paths, database-editor
support, save/load normalization, profile display and direct mechanical coverage.

### Move families

- single jab, double jab, jab to body and stiff-arm jab;
- one-two, jab-cross-hook, double jab-cross and cross-hook-cross;
- check hook, pull counter, slip-cross and catch-and-return;
- lead/rear uppercut, overhand, shovel hook and body-head changes;
- stance-shift combinations and bounded five-strike finishing flurries; and
- defensive shell, parry, slip, pull, pivot and frame responses tied to the attempted move.

### Acceptance criteria

- Combination components reconcile exactly with aggregate attempts and landed strikes.
- Body/head targets match recorded damage and commentary.
- Counter-only techniques require a real trace `counter_window`.
- Longer combinations retain explicit energy and counter-risk metadata for audit and later tuning;
  broad action gas/damage remains the calibrated resolution boundary so global KO/TKO does not move.

### Delivered

Added `combination_punching`, `body_punching` and `counter_timing`; footwork, feints, mobility and
reach remain the non-duplicated distance-management bundle. Old saves derive the new ratings from
their own saved profile without RNG, while new fighters generate and train them through the Standing
group and the editor/profile surfaces inherit them automatically. Seven additional boxing sequences
cover double-jab-cross, cross-hook-cross, body/head changes, check hooks, pull counters and slip-cross
returns. Counter-only moves require a genuine counter window, named components reconcile with the
aggregate strike count, and skill changes alter deterministic technique choice. Move energy/risk is
retained as data but deliberately does not alter the broad resolver: the 3,840-bout corpus remains
exactly 60.39% finishes, 16.48% KO and 19.04% TKO.

## Phase 3 — COMPLETED — Kicks, Knees, Elbows and Mixed Combinations

### Skill audit

Evaluate targeted additions such as `body_kick_technique`, `calf_kicks` and `spinning_attacks` against
the existing high/low/creative kick, knees, elbows, mobility and reflexes ratings. Prefer new bundles
over duplicate skills when the existing ratings already describe the technique.

### Move families

- inside/outside low kick, calf kick and low-kick counters;
- round kick, teep, side kick, question-mark kick, wheel kick and spinning back kick;
- body kick, head kick, switch kick and stance-dependent rear/lead variants;
- jab-low kick, cross-body kick, hook-low kick and punch-to-head-kick chains;
- intercepting knee, flying knee, step-in elbow and spinning elbow; and
- caught-kick counters, checks, shin clashes, pullbacks, blocks and takedown entries.

### Acceptance criteria

- Every kick has a target, side, range and legal defensive family.
- Leg/body/head damage and movement penalties remain internally consistent.
- High-risk spinning or flying moves are uncommon, skill-gated and meaningfully counterable.
- Sanda, Taekwondo, Karate, Kickboxer and Muay Thai produce measurably different move mixes without
  breaching any calibration gate.

### Delivered

The existing kick, knee, elbow, mobility, flexibility, reflex and creativity ratings proved sufficient,
so no duplicate detailed skills were added. Fifteen new standing-strike definitions cover calf and
check-return low kicks, teeps, side/switch/question-mark/wheel/spinning kicks, four punch-kick chains,
intercepting/flying knees and step-in/spinning elbows. Every registered kick now validates a target,
lead/rear side, range band and defensive family. High-risk techniques have strict skill floors and a
deterministic rarity gate; style-mix regressions distinguish Sanda, Taekwondo, Karate, Kickboxer and
Muay Thai. The full matrix passes and calibration remains exactly 60.39% / 16.48% / 19.04%.

## Phase 4 — COMPLETED — Clinch, Cage and Wrestling Chains

### Skill audit

Audit whether `hand_fighting`, `underhooks` or `wall_walking` are genuinely missing axes. Existing
clinch control, cage pressure, cage wrestling, chain wrestling, throws, trips, slams, ride control,
get-ups and defense should be reused wherever possible.

### Move families

- collar tie, double underhooks, over-under, Thai plum and body lock;
- pummel, frame, shoulder pressure, foot sweep and outside/inside trip;
- single leg, double leg, high crotch, ankle pick and reactive shot;
- knee tap, hip toss, lateral drop, mat return and lift/slam;
- jab-to-shot, overhand-to-double, kick catch-to-takedown and chained re-shots;
- cage turn, wall walk, whizzer, sprawl, limp-leg escape and granby-style scramble; and
- front-headlock snapdown into go-behind, knee or submission threat.

### Acceptance criteria

- Every takedown records entry, defense, finish position and controller ownership.
- Failed attacks open only legal counter and scramble paths.
- Chain wrestling spends additional energy and cannot create impossible position jumps.
- Wrestling, Judo, Sambo and Sanda produce distinct legal takedown families.

### Delivered

The skill audit retained the existing clinch-control/defense, cage-pressure/wrestling, chain-wrestling,
throws, slams, ride-control, get-up and scramble ratings rather than duplicating hand fighting,
underhooks or wall walking. Twenty-three additions cover over-under/double-underhook/Thai-plum entries,
pummels, fence pressure and frame exits; ankle-pick/reactive/mixed shot entries; inside/outside trips,
high crotch, knee tap, hip toss and lateral drop; re-shots, whizzers, mat returns, standing rides,
limp-leg escapes and front-headlock go-behinds. Every takedown definition now validates entry family,
legal defenses and possible finish positions. Style-mix tests distinguish Wrestling, Judo, Sambo and
Sanda while the structural and calibration gates remain unchanged.

## Phase 5 — COMPLETED — Ground Striking, Transitions and Submission Chains

### Skill audit

Assess a dedicated `submission_chaining` rating only if transitions, positional ability, submission
attack and fight IQ cannot express it. Do not create separate ratings for every submission.

### Move families

- posture punches, short elbows, body-head ground striking and ride-based punches;
- knee slice, half-guard pass, mount transition, back take and turtle breakdown;
- technical stand-up, hip escape, butterfly sweep, sit-out, reversal and wall-assisted get-up;
- rear-naked choke, arm triangle, guillotine, anaconda and D'Arce families;
- armbar, triangle, kimura, Americana and omoplata families;
- kneebar, straight ankle lock, heel hook and toe hold from legal entanglements; and
- submission-to-sweep, submission-to-back-take and chained finish attempts.

### Acceptance criteria

- A submission is legal for its current position and available limb/neck pathway.
- Failed submissions have explicit outcomes: retain position, lose position, concede reversal,
  recover guard or return to neutral.
- Technical submissions remain evidence-driven and do not become a second finish-conversion path.
- BJJ, Luta Livre, Catch Wrestler, Submission Grappler and Sambo produce distinct technique mixes.

### Delivered

Transitions, positional ability, submission attack, leg locks, control, scrambles and fight IQ already
express chaining, so no duplicate `submission_chaining` rating was added. Twenty-four additions bring
the registry to 101 moves: body/head and ride-based ground striking; knee-slice/half-guard passes,
mounts, back takes and turtle breakdowns; hip-bump/sit-out reversals; rear-naked, arm-triangle,
guillotine, anaconda and D'Arce chokes; armbars, triangle, kimura, Americana and omoplata attacks; and
ankle locks, kneebars, heel hooks and toe holds. Each submission validates its legal position/path and
explicit failure outcomes. Style-mix, structural and unchanged calibration gates pass.

## Phase 6 — COMPLETED — Fighter Signatures and Authored Move Sets

### Work

- Add database-editor controls for supported signature move IDs with registry-backed choices.
- Author a small first cohort across different archetypes rather than filling the whole universe at
  once.
- Give generated fighters one to three deterministic signatures when their skills support them.
- Display signatures on scouted profiles and the tale of the tape subject to scouting visibility.
- Track attempted, landed and finishing signature moves in post-fight metrics and career milestones.
- Keep names and fighter IDs out of mechanical move definitions; fighter-specific preference belongs
  to fighter data.

### Acceptance criteria

- A signature move is attempted more often than comparable legal alternatives but is never
  guaranteed to land or finish.
- Duplicate-name fighters retain independent move sets through save/load and replay.
- Old saves derive legal pools without mutation, crashes or empty action choices.
- Authored moves that become unknown in a future version degrade to valid generic actions.

### Delivered

`Fighter.signature_moves` now stores up to three stable registry IDs and `career_signature_stats`
retains attempts, effective uses and finishes. The Database Editor provides three registry-backed
selectors, shared universe validation rejects malformed/unknown IDs, and save loading drops unknown
future IDs safely. Nine varied authored fighters form the first cohort; skill-supported generated
fighters receive one-to-three deterministic signatures without RNG. Legal signature candidates gain
a bounded preference but remain subject to action, position, skill and deterministic variety, so they
are neither guaranteed to appear nor guaranteed to succeed. Scouted profiles, full profiles, the tale
of the tape and post-fight/career metrics expose the data with identity-safe save/load coverage.

## Phase 7 — COMPLETED — Tactical Selection, Feints and Adaptive Chains

### Work

- Make fight plans influence move-family weights beneath the existing action weights.
- Let fighters build reads: body work opens head attacks, low kicks alter stance/mobility, feints
  improve later entries, and repeated patterns become more counterable.
- Let adaptable corners recommend move-family changes using only public trace evidence.
- Add bounded opponent-recognition memory inside one bout; do not add persistent omniscience.
- Preserve AI/player parity by routing both through the same move selector.

### Acceptance criteria

- Tactical chains are explainable from earlier trace evidence.
- A plan changes move selection, not direct finish probability.
- Counter fighters exploit repeated patterns; pressure fighters build combinations; grapplers chain
  entries without bypassing defensive skill.
- The same fixed fight with different commentary produces identical mechanics.

### Delivered

The move selector now applies bounded beneath-action preferences from the existing fight plan, signature
set and public prior trace. Bout-local counters retain only capped move/target/tag/setup counts: body
work can open head choices, low kicks can open head/entry families, established feints can support
entries, repeated techniques receive a pattern penalty, and adaptable counter fighters exploit a
genuine opponent pattern only during a counter window. Every selected move records its explainable
`selection_reasons`. Existing evidence-led corner changes automatically redirect these move-family
weights without direct result modifiers, RNG, persistent opponent omniscience or AI/player divergence.

## Phase 8 — COMPLETED — Presentation, UI and Analysis

### Work

- Show move names, targets, defensive responses and follow-ups in Fight Night without flooding the
  transcript.
- Extend round telemetry with bounded move-family summaries rather than a full raw event dump.
- Add move frequency/success panels to the Simulation Lab and fighter post-fight profile.
- Preserve sealed judging totals and avoid implying that ineffective variety scores by itself.
- Add accessibility-safe labels; never rely on colour alone for target or outcome.

### Acceptance criteria

- Commentary describes exactly the recorded move and outcome.
- Full-card skip/replay retains the same move trace without applying results twice.
- Long fights remain responsive and all structural Fight Night lines remain present.
- Presentation changes pass mechanical signature parity.

### Delivered

Fight Night renders the exact move name plus text labels for target, defensive response and meaningful
follow-up, without relying on colour. Completed-round telemetry adds only the top two move families per
corner as effective/used counts; the raw trace remains available for audits and replay. FightResult,
last-fight and persistent career telemetry reconcile family counts with the raw exchanges. Fighter
statistics show career family and signature effectiveness, and Quick Fight Simulator results expose
the top families plus techniques, sequences, signatures, risk/load, stance lanes and plan evolution.
Presentation consumes no RNG and the structural/mechanical parity
regressions remain green.

## Phase 9 — COMPLETED — Calibration, Content Expansion and Release

### Work

- Run the 356-bout structural matrix, focused fight regressions and 3,840-bout distribution audit
  after every mechanical slice, not only at the end.
- Add minimum-sample move-family reports by style, behaviour, tier and stance.
- Detect dead moves, dominant moves, impossible counters, energy exploits and techniques that never
  appear outside mismatch fights.
- Expand the authored fighter cohort only after generic/generated fighters pass distribution checks.
- Run the complete isolated regression suite and stability playtest before release.

### Release gates

- Exactly 60.39% total finishes, 16.48% KO and 19.04% TKO on the accepted fixed corpus.
- No change to `competitive_finish_conversion()`.
- No illegal position, ownership, target, move or follow-up path.
- All trace totals reconcile with final box scores and medical evidence.
- Every new detailed skill is mechanically consumed and develops through at least one supported path.
- Every supported style has a sampled, distinguishable and non-dominant move identity.
- Shipped universe validation, current save round trip and legacy-shaped load tests pass.
- Full canonical regression suite and long stability playtest pass.

### Delivered

The release audit now produces a deterministic 880-fight move report with minimum-sample breakdowns for
all 18 supported styles, every behaviour, competitive tier, both stances and open/closed/switch matchups.
It measures pairwise style identity and distinguishes moves absent
from the representative corpus from genuinely unreachable entries through a targeted all-registry probe;
all 176 moves are reachable, with no dominant same-action/position move, mismatch-only technique, illegal
counter, position or target use, or unsafe energy metadata. Turtle breakdown and sit-out reversal identity
now follows the broad actions that actually resolve those states. The expanded Standing sheet retains its
pre-expansion per-skill development exposure, and sparse legacy editor records derive missing skills safely
until Apply deliberately materializes a full sheet. The 356-bout structural matrix, exact action baseline,
3,840-bout distribution (60.39% finishes, 16.48% KO, 19.04% TKO), shipped database validation, complete
isolated regression suite and long stability playtest form the final release gates.

## Post-Roadmap Development — COMPLETED

### Phase 10 — Specialist transition coverage

Elite, rating-gated specialists can retain failed-shot/front-headlock, standing-back-control and
leg-entanglement states into the next action. A deterministic 720-complete-fight report requires each
state and its legal follow-up action families without broadening the finish converter.

### Phase 11 — Authored signatures

The shipped cohort expanded from nine to 40 authored fighters across 11 styles. Every ID is validated
against the canonical registry and remains a preference rather than a forced or illegal technique.

### Phase 12 — Mechanical move differentiation

Move energy, miss risk and counter vulnerability now create bounded, decaying pressure on later legal
technique selection. They deliberately do not alter broad gas, landing, damage or finish resolution.

### Phase 13 — Combination sequencing

An effective registry move may schedule its authored follow-up for at most two ticks in the same round.
Completed steps retain their source in the trace and still consume one ordinary broad action.

### Phase 14 — Style identities

All 18 primary styles have explicit technique-tag preferences. The release report measures pairwise
move-distribution distance and rejects indistinct sampled style pairs.

### Phase 15 — Stance and matchup interaction

Open, closed and switch stances prefer different legal lanes, while striker/grappler pairings shape
range, entry and scramble choices. Every influence is exposed as a move-selection reason.

### Phase 16 — Fight-plan evolution

Enabled corners can change plans from completed round evidence: repeated opponent moves, successful own
families, gas, urgency and visible leads. Changes retain evidence, confidence and a one-change-per-round
guard; compatibility bouts without assigned plans remain Balanced.

### Phase 17 — Analysis UI

The Simulation Lab now presents top techniques, completed sequences, signature effectiveness, average
energy/miss/counter metadata, stance-lane usage and plan evolution alongside move-family effectiveness.
All values reconcile to the completed trace and consume no presentation or mechanics RNG.

### Phase 18 — Named defensive techniques — COMPLETED

Eighteen registry-backed defenses now cover standing, wrestling, cage, ground and submission reactions.
Every exchange retains a known defensive ID; the already-resolved broad outcome remains authoritative.

### Phase 19 — Technique mastery and development — COMPLETED

Persistent move/defense mastery develops through camps and academy training, transfers on graduation,
can create earned signatures, and declines gradually for veterans beyond their prime.

### Phase 20 — Dynamic stance switching — COMPLETED

Natural switch fighters and highly adaptable movers can make cooldown-bound orthodox/southpaw changes
from plan and matchup context. Each change is traceable and consumes no additional mechanics draw.

### Phase 21 — Branching sequences — COMPLETED

Registry moves may offer multiple follow-ups. Resulting position filters legality and named defensive
frames/evasions/escapes can select an alternate branch inside the existing two-tick limit.

### Phase 22 — Per-round replay explorer — COMPLETED

Archived cards expose trace-derived round effectiveness, moves, defenses, sequence paths, stance changes
and plan changes through a second replay selector while legacy logs remain readable.

### Phase 23 — Broader authored content — COMPLETED

The shipped authored cohort now covers 114 fighters across 13 styles. Existing bespoke sets are
preserved; the second explicit cohort uses style- and behaviour-consistent registry IDs.

### Phase 24 — Representative specialist frequency — COMPLETED

The 17 legal techniques absent from the small synthetic general sample receive a stronger specialist
identity preference when their rare action/position becomes available, and the expanded authored cohort
places those skills in more ordinary universe bouts. Targeted reachability remains a release gate; broad
actions and the locked finish percentages are unchanged.

### Phase 25 — Expanded standing combinations and finishing techniques — COMPLETED

Ten registry-backed sequences add body-to-head boxing, stance-shift and pressure combinations,
double-jab/hook kick endings, and punch/elbow/knee chains. Six uncommon finishers cover the rear
uppercut, corkscrew cross, spinning backfist, axe kick, jumping front kick and switch flying knee.
Combination components reconcile against realistic aggregate volume, every addition appears in the
representative 880-fight corpus, and the causal registry technique is authoritative in KO/TKO
narration. Selection remains below the broad resolver: no added combat draw, landing modifier or
finish-conversion path, and the frozen 2,319 finishes/633 KOs/731 TKOs remain exact.

### Phase 26 — Expanded ground techniques — COMPLETED

Twenty-three registry-backed additions deepen the most common ground positions: six authored striking
chains, five passing/climbing transitions, four sweeps, five recoveries/get-ups/retentions and three control rides.
Every common-position move appears in the representative 880-fight corpus; the turtle-specific
wrist-ride chain remains legal and targeted-reachable in its rare specialist state. Ground-strike
components reconcile against realistic aggregate volume, branches remain ordinary future actions,
and causal mounted hammerfists survive TKO narration. The broad resolver remains authoritative for
damage, success, position and finishes, preserving the exact result and action baselines.

### Phase 27 — Style-specific combinations — COMPLETED

Every supported style now owns one exclusive authored chain. The striking disciplines use ordered
boxing, kick, elbow and knee components; Sanda and the wrestling styles connect strikes or feints to
their characteristic entries; judo and sambo chain grips and punches into trips; and the grappling
styles connect drags, passes, scrambles and leg entries to position or submission threats. Primary
and secondary styles can unlock their chain, while signatures and mastery cannot grant it to an
unrelated style. All 18 appear in the representative 880-fight corpus with no dominance, legality,
reachability or style-distance diagnostic. Each remains one existing broad action, preserving the
locked result and action baselines.

### Phase 28 — Style-specific finishers — COMPLETED

Every supported style now owns one exclusive causal finisher. Striking styles use distinct knockout
techniques, wrestling styles use trace-backed ground-and-pound sequences, and catch wrestling, BJJ,
Luta Livre, sambo, judo and the broader grappling styles use characteristic chokes, joint locks and
leg locks. Well-Rounded and MMA Generalist fighters receive mixed-striking finishes. Primary or
secondary style ownership is required, and signature/mastery data cannot bypass it. The deterministic
selection window only identifies a move beneath an existing KO, TKO or submission outcome. All 18
appear in the representative 880-fight corpus without dominance or legality diagnostics, while the
exact result and action baselines remain release gates.

## Recommended Delivery Slices

Keep each implementation reviewable and independently releasable:

1. unsupported-style repair and validator hardening;
2. registry plus trace-only move identity;
3. boxing skills and combinations;
4. kicks and mixed striking;
5. clinch and wrestling chains;
6. ground transitions and submissions;
7. signatures and authored fighter identity;
8. tactics and adaptation;
9. UI, analysis and final calibration.

Do not combine multiple mechanical phases into one patch. Each slice needs its own tests,
documentation updates and before/after audit evidence so any distribution drift can be traced to the
specific element that caused it.
