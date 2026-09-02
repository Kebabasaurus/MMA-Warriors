# Fight Engine Development Plan

## Purpose

This plan evolves the MMA fight engine from a detailed but tightly coupled simulation into a
reproducible, explainable and tactically expressive system. The work should improve realism without
forcing desired winners or replacing simulation outcomes after the bout.

The existing `competitive_finish_conversion()` calculation is explicitly outside this plan. Do not
change, replace or tune it as part of these phases.

## Current Baseline

The engine already provides:

- collision-safe private state for duplicate-name fighters;
- detailed striking, clinch, wrestling, positional grappling and submission skills;
- style, stance, behaviour, trait, morale, camp, weight-cut and fight-night context;
- head, body and leg damage, cuts, fatigue, knockdowns and unanswered-offence tracking;
- three independent judge cards and structured round summaries;
- complete Fight Night commentary, official scorecards and post-fight metrics; and
- shared mechanics for player, game-AI, academy and sandbox MMA fights.

The main limitations are architectural rather than a lack of individual formulas. Combat and
presentation randomness are interleaved, judging includes factors that should only influence the
actions themselves, temporary hurt and lasting damage share state, tactical behaviour is mostly
static, and the core action resolvers lack focused regression coverage.

## Design Rules

Every phase must preserve these rules:

1. The engine models exchanges and derives the result; it never chooses a desired result first.
2. Player and game-AI fights use the same underlying mechanics.
3. Fighter identity is always object- or ID-based; display names are presentation only.
4. Commentary cannot change the mechanical result.
5. Exact official cards remain sealed until the decision is announced.
6. Existing saves remain loadable. New persistent settings require safe defaults and load repair.
7. A phase must be measurable before it is tuned.
8. Do not alter `competitive_finish_conversion()` during this roadmap.
9. Preserve the current finish-rate profile. New architecture and richer mechanics must not make
   the game more or less finish-heavy overall or within realistic matchmaking bands.

## Finish-Rate Preservation Contract

Keeping the current percentage of finishes is a release-blocking requirement for every phase in
this plan. Before Phase 1 begins, Phase 0 must capture a checked-in baseline from a fixed fighter
corpus, matchup list and seed list using the current engine.

The baseline must record:

- overall finish percentage;
- competitive low-, mid- and high-tier finish percentages;
- mismatch finish percentage, reported separately from competitive fights;
- KO, TKO, submission, technical-submission, doctor, corner and injury-stoppage shares;
- finish percentage by round and scheduled bout length;
- finish percentage for every adequately sampled style and behaviour pairing; and
- decision and draw percentages as the complement of the finish distribution.

Use paired before/after audits against exactly the same fighters, corners, rules and seed corpus.
Every implementation phase must meet all of these gates:

- Phase 1 trace-only infrastructure work retains exact winner, method, round and scorecard parity.
  Separating a legacy shared RNG stream intentionally changes individual draws, so that slice must
  instead pass the locked distribution gates below and the commentary-independence regression.
- Later intentional mechanics work: overall finish rate within 1.0 percentage point of baseline.
- KO and TKO rates: each within 1.0 percentage point of baseline.
- Competitive low-, mid- and high-tier finish rates: each within 1.5 percentage points of baseline;
  a nominal crossing is release-blocking when its 95% interval also separates from baseline.
- Competitive versus mismatch finish-rate gap: within 1.5 percentage points of baseline.
- KO/TKO and submission family shares: each within 2.0 percentage points of baseline.
- Finish timing by early, middle and late rounds: each within 2.0 percentage points of baseline.
- No adequately sampled style or behaviour group may move more than 3.0 percentage points with a
  non-overlapping 95% confidence interval without a separately approved balance change.

The tolerances are regression limits, not tuning targets. Do not adjust
`competitive_finish_conversion()` or overwrite final methods to force a passing report. If a phase
crosses a limit, correct the new exchange, damage, tactical, scoring or stoppage mechanics that
caused the drift before merging that phase. Reports must publish sample counts and confidence
intervals so a small sample cannot be mistaken for a meaningful change.

## Phase 0 — COMPLETED — Establish the Measurement Baseline

### Goal

Make the current engine measurable before changing its mechanics.

### Work

- Add `fight_engine_regression_test.py` and register it in `run_regression_suite.py`.
- Add a non-mutating fight-audit runner that accepts a seed, fighter pair and rules payload.
- Record method, round, winner, judge cards, significant strikes, takedowns, submission attempts,
  control, knockdowns, damage by location, gas and position time.
- Produce grouped reports by rating band, rating gap, style pairing, behaviour, bout length and
  title/main-event status.
- Freeze the current finish-rate and finish-method report as the preservation baseline described
  above.
- Add mirrored-corner audits: run equivalent red/blue assignments and detect meaningful bias.
- Record result predictiveness by rating gap without imposing a target winner.

### Acceptance criteria

- A fixed audit seed produces byte-stable structured output.
- The audit does not change career state, fighter records, RNG state outside its sandbox or saves.
- Results can be compared before and after every later phase.
- Reports distinguish competitive matchups from mismatches.
- The checked-in baseline contains enough paired bouts for the finish-rate preservation gates to be
  statistically meaningful.

**Delivered:** `fight_engine_audit.py` provides a UI-free, non-mutating harness, style-shaped fixed
corpus, per-exchange evidence, position-time counts, confidence intervals, distribution comparison
and detailed-attribute usage classification. `analysis/fight_engine_baseline.json` freezes 3,840
bouts and their parity signatures, while `analysis/FIGHT_ENGINE_BASELINE_REPORT.md` records the
human-readable result. `fight_engine_regression_test.py` verifies deterministic execution, input and
RNG purity, trace/stat consistency, attribute coverage and every frozen signature. The suite is
registered in `run_regression_suite.py`.

## Phase 1 — COMPLETED — Separate Mechanics from Presentation

### Goal

Ensure commentary, clocks and viewer changes can never affect a fight result.

### Work

- Give each bout independent combat, officiating and presentation RNG streams derived from the
  supplied simulation seed.
- Move flavour selection, commentary variation and irregular clock generation onto the presentation
  stream.
- Introduce a structured `FightResult` and event trace. At minimum, each event should retain:
  - round and clock;
  - actor and defender slots;
  - position before and after;
  - attempted action and outcome;
  - strike, takedown, control and submission evidence;
  - gas and damage deltas;
  - knockdown, hurt, cut or stoppage flags; and
  - the mechanical reason for a finish.
- Render commentary from the completed trace instead of consuming combat randomness inside action
  resolution.
- Keep the existing `(winner, loser, method, round, lines)` return shape through a compatibility
  adapter while callers migrate.
- Build `last_fight_stats`, round summaries and replay data from the same trace.

### Acceptance criteria

- The same combat seed produces the same winner, method, round, stats and cards when commentary is
  disabled, expanded or rendered in a different language/style bank.
- Every commentary action is backed by one trace event.
- No trace or commentary event occurs after the official finish event.
- Existing player, AI, academy and sandbox callers continue to work.
- Trace-only refactors retain exact bout parity. RNG decoupling retains the locked finish, KO, TKO,
  method-family, timing, tier and statistically meaningful subgroup distributions.

**Delivered:** `FightResult` retains immutable
commentary, native per-exchange trace events, scorecards, metrics and rules; every trace terminates in
one official-result event. `simulate_fight_result()` exposes the structured result while the existing
five-item tuple remains unchanged. This slice adds no random calls and retains all 3,840 frozen
signatures. Combat, officiating and presentation use explicit bout-local streams; foul recovery is
no longer hidden inside atmospheric commentary; clocked calls render through exchange trace events;
and a phrase-bank replacement regression locks winner, method, round, stats and cards. Trace events
retain classified outcomes, state flags, control and damage deltas, commentary calls and the final
mechanical stoppage reason. The post-separation corpus remains at 59.79% finishes, 16.25% KO and
18.98% TKO, while the smoke suite covers the shared player, game-AI, academy and sandbox interface.

## Phase 2 — COMPLETED — Rebuild Judging Around Recorded Evidence

### Goal

Make every scorecard defensible from what happened in that round.

### Work

- Remove remaining gas, home, experience and pressure bonuses from the judge's round value. Those
  factors may affect execution, but should not independently earn points.
- Apply a judging hierarchy:
  1. effective striking and grappling;
  2. effective aggression when the first category is effectively even; and
  3. control when the first two categories are effectively even.
- Derive impact, danger, aggression and control from trace events rather than coarse final counters.
- Define evidence-based 10-8 thresholds using duration and severity of dominance.
- Support rare justified 10-10 rounds.
- Add majority decisions, split decisions, majority draws and split draws as explicit result labels.
- Add a minimal foul and point-deduction model only after normal cards are stable.
- Keep judge disagreement tied to genuinely ambiguous evidence. Judge variance must not invent a
  different fight when one athlete clearly dominated the round.

### Acceptance criteria

- Removing presentation or changing fighter names cannot change a card.
- A clearly dominant round cannot be awarded to the dominated fighter through ordinary noise.
- Close rounds can split across judge profiles.
- Every 10-8 and point deduction is visible in the trace and official card.
- Scorecard totals, judge votes and final decision labels always agree.

**Delivered:** Round cards now aggregate the native exchange trace and follow the effective-offense,
effective-aggression, then control hierarchy. Non-scoring context and gas bonuses were removed;
ordinary variance is confined to ambiguous effective offense on an isolated judging substream;
dominance severity and duration gate 10-8 rounds; and evidence-free rounds can be 10-10. Official
cards retain per-round evidence and deductions. `FightResult.verdict` and the transcript expose
unanimous, split and majority decision/draw labels while canonical methods remain save-compatible.
Focused tests cover dominant rounds, name independence, close judge disagreement, 10-10s, vote/
verdict agreement and repeated-foul deductions. The 3,840-bout gate passes at 59.32% finishes,
16.25% KO and 19.24% TKO; smoke coverage also passes.

## Phase 3 — COMPLETED — Separate Lasting Damage, Hurt and Recovery

### Goal

Make physical consequences coherent during the bout and useful after it.

### Work

- Separate persistent `head_damage`, `body_damage` and `leg_damage` from transient `hurt` and
  `stun` state.
- Allow stun and composure to recover through defensive success, survival and corner work without
  erasing accumulated physical damage.
- Replace the cut count with structured cut state: location, severity, bleeding and swelling.
- Make body damage reduce sustained output and recovery.
- Make leg damage affect movement, stance stability, kick output, shots and stand-ups.
- Make repeated head trauma affect reactions, defence and stoppage risk through transient hurt plus
  lasting damage.
- Run doctor checks at legitimate breaks or severe incidents using cut visibility and function, not
  repeated generic rolls.
- Feed the final trace into post-fight medical layoff and injury logic.

### Acceptance criteria

- Resting can reduce hurt and restore some gas but cannot heal accumulated head, body or leg damage.
- Location damage has visible, mechanically appropriate consequences.
- Doctor and corner stoppages identify the evidence that caused them.
- Post-fight injuries and layoffs use the same damage record shown in Fight Night.

**Delivered:** Persistent aggregate/head/body/leg trauma is now separate from transient `hurt`.
Survival, meaningful defensive responses and corner work recover bounded hurt/gas without reducing
physical damage. Body, leg and head channels have distinct output, mobility and reaction effects.
Cut events retain deterministic location, severity, bleeding, swelling and vision risk; doctor
stoppages state that evidence. `last_fight_stats` exposes peak hurt and cut detail, and post-fight
medical layoff/injury logic consumes those same visible values. Focused tests prove recovery cannot
heal trauma, location effects are distinct, structured cuts are complete and severe visible damage
feeds the medical path. The 3,840-bout gate passes at 60.39% finishes, 16.48% KO and 19.04% TKO;
smoke coverage also passes.

## Phase 4 — COMPLETED: Add Fight Plans and Corner Adaptation

### Goal

Turn style identity into tactical behaviour and give management choices a meaningful fight-night
effect.

### Work

- Add validated pre-fight plans such as:
  - Balanced;
  - Pressure and volume;
  - Counter striking;
  - Wrestle early;
  - Cage grind;
  - Attack the body;
  - Damage the lead leg;
  - Submission hunt;
  - Conserve energy;
  - Protect a lead; and
  - Chase a finish.
- Store player-selected plans on booked bouts by fighter ID. Old cards default to Balanced.
- Give game-AI fighters plans based on style, opponent skills, camp, stakes and promotion strategy.
- Let Fight IQ, adaptability, discipline and coaching quality determine plan execution.
- At each corner break, assess only observable trace evidence and choose whether to keep or adjust the
  plan.
- Surface concise corner advice and post-fight plan effectiveness without exposing hidden ratings.
- Ensure plans alter action selection and pace rather than directly modifying the final result.

### Acceptance criteria

- Plans produce measurable differences in action mix, target selection and energy use.
- A counter-striking plan does not merely become lower volume; it creates actual counter windows.
- Adaptable fighters respond more effectively to a failing plan over large samples.
- Player and game-AI plans use the same execution model.
- Duplicate-name fighters retain independent plans through booking, replay and save/load.

**Delivered:** Matchmaking and the booked-card editor now store eleven validated corner plans by
`fighter_id`; old or malformed scheduled bouts load as Balanced, while AI-controlled fights choose
through the same style/matchup plan model. Plans alter weighted action choice, kick targets and
energy use, and Counter striking consumes an actual opportunity created by a defended attack.
Fight IQ, adaptability, discipline and coaching shape execution; between-round changes read only
the recorded trace, gas and visible trauma, then publish rating-free corner advice and a post-fight
effectiveness recap. Compatibility is explicit: bouts created without a plan retain the legacy
Balanced path without automatic tactical switching. Focused action, target, counter, adaptation,
identity and persistence tests pass, as does save/load smoke coverage. The unchanged 3,840-bout
gate reports 60.39% finishes, 16.48% KO and 19.04% TKO without changing
`competitive_finish_conversion()` or the frozen baseline.

## Phase 5 — COMPLETED: Upgrade Exchanges and Counters

### Goal

Replace isolated one-actor actions with coherent exchanges while retaining readable simulation
speed.

### Work

- Resolve each beat as an exchange:

  ```text
  initiative
    -> setup or attack
    -> defensive response
    -> counter opportunity
    -> follow-up, transition or disengagement
  ```

- Add setups such as feints, level changes, jab entries, pressure to the fence and stance traps.
- Add explicit defensive responses: block, evade, check, parry, sprawl, frame, pummel and scramble.
- Add counter events driven by timing, anticipation, reflexes and the opponent's failed action.
- Add combination templates that retain the individual attempted and landed strikes in the trace.
- Let failed attacks create position-specific consequences instead of returning immediately to a
  neutral state.
- Preserve a bounded number of mechanical beats per round for performance and replay readability.

### Acceptance criteria

- Counter fighters generate more successful counters than comparable pressure fighters.
- Missed or defended attacks can lead to mechanically valid counters.
- Combination statistics never record more landed strikes than attempts.
- Exchange chains remain deterministic for a fixed combat seed.
- Runtime remains suitable for long game-AI calendar simulations.

**Delivered:** Every trace exchange now contains a bounded setup/attack/defense/counter/follow-up
chain. Entries distinguish level changes, re-shots, jab entries, feints, stance traps, fence
pressure, hand fighting and grappling transitions; resolved defenses identify blocks, evasions,
parries, checks, sprawls, frames, pummels and scrambles from the actual action and position. Failed
offense creates a traceable counter opportunity, and a consumed window records whether the counter
was mechanically successful. Aggregate strike volume expands into ordered, capped combination
components whose landed count can never exceed attempts. Sixty mirrored fixed-seed bouts show the
Counter striking plan creates more attempted and successful counters than Pressure and volume, and
the repeated chains are deterministic. The 3,840-bout gate remains at 60.39% finishes, 16.48% KO
and 19.04% TKO with no baseline or finish-conversion change.

## Phase 6 — COMPLETED: Deepen Grappling and Cage Wrestling

### Goal

Make grappling a legal positional state machine rather than a mostly linear progression.

### Work

- Add turtle, front headlock, standing back control and failed-shot positions.
- Distinguish open-space takedowns from cage takedowns and mat returns.
- Support chained shots, re-shots, sprawls into front headlocks and wall get-ups.
- Give submission escapes explicit consequences: safe escape, guard recovery, reversal, scramble or
  worse position.
- Add leg-entanglement states only with clear entry, control, escape and submission rules.
- Make referee stand-ups depend on position, meaningful activity and warnings.
- Validate every transition against an allowed state-transition table.

### Acceptance criteria

- Illegal ownership combinations such as both fighters being on top are impossible.
- Horns clear temporary clinch and ground ownership.
- A failed submission cannot silently leave both fighters in an undefined position.
- Wrestlers, control grapplers and submission specialists produce measurably different positional
  paths.
- Every grappling commentary line matches the trace's legal position.

**Delivered:** The engine now owns an explicit allowed-transition table and validates every settled
and within-exchange position plus `top`, `bottom` and standing-controller ownership. Failed shots,
front headlocks, turtle, standing back control and leg entanglements have legal entry/escape routes;
open-space sprawls, cage chains, re-shots, mat returns, wall escapes, back takes and leg-lock pummels
use the relevant wrestling/grappling details. Brief scrambles are retained as a validated
`position_path` inside one exchange when neither fighter consolidates them, matching real MMA
without falsely carrying a momentary position into the next beat. Submission failures record safe
defense, retained position, guard recovery, reversal or consolidated top control, with specialist
traits and the actual skill relationship gating the rarer consequences. Ground inactivity includes
every legal mat state and still requires inactivity plus a warning before a referee stand-up. Tests
cover illegal ownership, illegal transitions, horn-safe state, reachable expanded paths, explicit
submission consequences and distinct wrestler/submission-specialist/striker samples. Focused and
smoke suites pass; the unchanged corpus remains 60.39% finishes, 16.48% KO and 19.04% TKO.

## Phase 7 — COMPLETED: Referee, Fouls and Fight Consequences

### Goal

Add controlled variance and long-term meaning without overwhelming ordinary fights.

### Work

- Give referees explicit tendencies for warnings, stand-ups, fence grabs, low blows, eye pokes and
  stoppage timing.
- Keep fouls uncommon and bounded. Avoid repeated random interruptions.
- Add recovery time, warnings and point deductions with correct scorecard effects.
- Support technical decisions or no contests only when the rules and completed rounds justify them.
- Use trace evidence to drive medical suspensions, confidence effects and injury recurrence.
- Add post-fight review flags for unusually early or late stoppages without rewriting the result.

### Acceptance criteria

- Fouls and deductions are visible in the replay and cards.
- Technical outcomes follow configured rules and completed-round thresholds.
- Referee tendencies affect process, not fighter ratings or desired winners.
- Long-term medical consequences agree with the displayed fight damage.

**Delivered:** Referee profiles now explicitly own the existing stoppage modifier, ground-warning
pace and stand-up threshold without reading fighter ratings or changing the calibrated values.
Fouls retain warning number, recovery allowance, accidental intent, referee and round/tick evidence;
the third incident can deduct a scorecard point and a hard three-incident cap prevents interruption
loops. Severe accidental fouls use the real three- or five-round completed-round threshold to
produce a No Contest or technical scorecard result, with all player, AI, academy and independent
settlement paths protecting records, Elo and titles after a No Contest. Post-fight review metadata
flags unusually early/late stoppage evidence without rewriting the official result. The visible
head/body/leg/cut metrics now drive the existing medical layoff plus bounded confidence and injury-
recurrence consequences. Focused, persistence and smoke tests pass; after correcting an initial
foul-selection drift, the unchanged 3,840-bout corpus is exactly 60.39% finishes, 16.48% KO and
19.04% TKO.

## Phase 8 — COMPLETED: Cleanup and Tuning Surface

### Goal

Reduce hidden coupling and leave a maintainable engine after the mechanical upgrades.

### Work

- Remove confirmed unused helpers such as `finish_chance()` and `finish_method()` after a repository-
  wide caller check.
- Move fight-only tuning values into named constants or a validated fight configuration object.
- Move unrelated business settings such as gate multipliers out of `engine_settings`.
- Replace unexplained numeric thresholds with named values and comments describing their units.
- Add a configuration version and safe defaults for existing saves.
- Keep Simulation Lab controls bounded and label which settings affect mechanics versus presentation.
- Profile realistic cards and full calendar runs before and after cleanup.

### Acceptance criteria

- No duplicate or dead fight-resolution path remains.
- Every user-facing tuning control has one documented mechanical effect.
- Old saves load with equivalent default behaviour.
- Full regression, stability, persistence and long-run performance suites pass.
- The finish-rate preservation report passes every overall, tier, matchup, method and timing gate.

**Delivered:** Repository-wide caller checks confirmed and removed the unused `finish_chance()` and
`finish_method()` resolution path. Fight tuning now has named defaults, bounds and configuration
version 2; load normalization clamps malformed values and supplies equivalent defaults. Gate
multiplier moved to a separately versioned business-simulation configuration with an old-save
migration from the legacy engine dictionary. Simulation Lab labels fight-mechanical controls and
the business-only gate control separately, and every control remains bounded to 0.5–2.0. Focused
tests cover dead-path removal, malformed-value repair and the legacy gate migration. The frozen
distribution verifier remains exact at the accepted current 60.39% finish, 16.48% KO and 19.04%
TKO rates. The canonical isolated regression suite, 48-week child/custom-promotion runs, narrative
calendar benchmark and three-seed stability playtest all pass after the cleanup.

## Phase 9 — COMPLETED: Broadcast Density and Repetition Control

### Goal

Make watched fights readable without deleting the technical record or changing outcomes.

### Delivered

- The complete engine transcript and structured trace remain the archive/debug authority.
- Fight Night defaults to a deterministic Broadcast view capped only across ordinary timestamped
  calls. It retains round structure, consequential exchanges, incidents, finishes, scorecards,
  metrics and results, and inserts one quiet-action summary for suppressed clusters.
- Detailed playback and completed-bout review expose the complete stored transcript.
- Legacy `[target; defense; next]` suffixes are removed from Broadcast prose while the Analysis
  Explorer retains the same technical evidence.

## Phase 10 — COMPLETED: Fact-Driven Exchanges and Continuous Finishes

### Goal

Ensure the visible sentence always agrees with the named technique and the final exchange.

### Delivered

- Exchange calls render from trace actor, move, target, defense, outcome and position. The older
  broad-action result string remains compatibility evidence but is no longer a prose source.
- Instant finishes are narrated only after the current move payload is available.
- KO, TKO, submission and technical-submission copy uses that move and settled position, followed
  by at most one intervention clause and one official result announcement.
- Semantic fixtures deliberately provide contradictory legacy prose and verify it cannot leak into
  the rendered call.

## Phase 11 — COMPLETED: Contextual Corners and Broadcast Voices

### Goal

Make round-to-round analysis sound responsive and let the player choose the broadcast tone.

### Delivered

- Corners cite completed public evidence such as gas, damage/effect deficit, control, repeated moves
  and successful technique families. Balanced legacy bouts receive natural observations instead of
  developer-facing text about a missing assigned plan.
- Advice memory prevents an unchanged recommendation from repeating verbatim across breaks.
- Persistent Balanced, Technical, Excitable and Concise voices change exchange and corner wording
  only. Unknown or legacy values normalize to Balanced; commentary density defaults to Broadcast.
- Same-seed personality regressions require identical winner, method, round, mechanics trace, stats
  and scorecards.

## Phase 12 — COMPLETED: Deterministic Fact-Driven Variety

### Goal

Increase broadcast variety without allowing prose generation to influence the fight.

### Delivered

- Landed, blocked, slipped, countered, transitioned and escaped outcomes select among multiple calls
  using stable presentation-only evidence.
- Every variant preserves the recorded actor, move, outcome, defense/counter evidence and settled
  position; compatibility prose cannot override the completed trace.
- Re-rendering is deterministic and leaves process, mechanics, officiating, judging and presentation
  RNG state unchanged.

## Phase 13 — COMPLETED: Live Broadcast Controls

### Goal

Make long watched cards easier to read without losing the complete record.

### Delivered

- The active viewer switches between Broadcast and Detailed in place while preserving the reached
  source frontier, sealed scorecards and immutable archived transcript.
- Stronger round separators and dedicated knockdown/finish tags improve chronological scanning.
- A compact indicator shows the voice attached to the current fight log.

## Phase 14 — COMPLETED: Evidence-Bound Context

### Goal

Let individual fighters, corners and stakes shape the broadcast without invented narrative.

### Delivered

- Recorded signatures/mastery, stance matchups, plan changes, momentum, accumulated damage,
  camp/coach identity, championship stakes and rivalry evidence can enrich commentary.
- Context is emitted only from scheduled-bout, fighter or completed-trace facts and never adds a
  mechanics modifier or consumes combat RNG.

## Phase 15 — COMPLETED: Commentary Release Gates

### Goal

Turn commentary quality and mechanical isolation into permanent automated checks.

### Delivered

- Focused tests reject excessive repetition, missing actor/move/outcome evidence, contradictory
  defense prose, broken finish continuity, duplicate official results and technical-suffix leakage.
- The canonical runner executes the fixed 3,840-bout audit and rejects any change from 2,319 finishes,
  633 KOs or 731 TKOs before the rounded 60.39% / 16.48% / 19.04% rates can conceal it.

## Regression Matrix

The dedicated fight-engine suite should include at least these scenarios:

| Area | Required regression |
| --- | --- |
| Determinism | Same combat seed returns the same mechanics with commentary on or off |
| Identity | Same-name fighters retain separate state, plans, stats and winner identity |
| Symmetry | Mirrored red/blue assignments remain statistically neutral |
| Striking | Attempts, lands, counters, knockdowns and target damage agree |
| Wrestling | Shots, sprawls, cage transitions and mat returns remain legal |
| Grappling | Position ownership and submission escape consequences remain valid |
| Fatigue | Higher workload costs gas; conditioning improves sustainable output |
| Damage | Hurt may recover; accumulated physical damage does not disappear |
| Judging | Cards follow trace evidence and totals match the official result |
| Stoppages | Finish evidence precedes the stoppage and no action follows it |
| Finish-rate preservation | Overall, tier, matchup, method and timing rates remain inside the baseline gates |
| Round structure | Three-, five-, six- and seven-round configurations retain every boundary |
| Shared rules | Player, game-AI, academy and sandbox MMA paths use the same mechanics |
| Compatibility | Existing saves and legacy booked cards receive safe defaults |
| Performance | Large game-AI batches remain within the established calendar budget |

## Delivery Strategy

Implement one phase at a time. Do not combine the RNG/trace migration, judging rewrite, damage
rewrite and tactical system into one patch. Each phase should:

1. capture its pre-change baseline;
2. add the narrow regression that proves the old limitation;
3. implement the smallest coherent change;
4. compare behavioural and performance reports;
5. pass the finish-rate preservation report;
6. run the canonical regression suite; and
7. update `CHANGELOG.md`, `README.md`, `AGENTS.md` and this plan.

## Recommended First Release Slice

The first implementation release should contain only Phases 0 and 1:

- `fight_engine_regression_test.py`;
- isolated combat, officiating and presentation RNG streams;
- a structured `FightResult` and trace;
- commentary rendered from trace events;
- compatibility with the existing result tuple; and
- deterministic parity tests across player, game-AI, academy and sandbox calls.

Trace-only parts of this slice must retain exact result parity. Stream separation must preserve the
locked aggregate and subgroup distributions and prove commentary-bank independence; it must never
rebase the frozen benchmark to hide drift.

That foundation makes every later realism improvement safer to build, inspect and tune.
