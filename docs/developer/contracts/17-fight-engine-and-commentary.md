## 9. Fight Engine and Fight-Night Presentation

The fight engine must model the bout rather than pick a desired result and work backward.

`Fighter.style` is the supported primary compatibility and search identity. `secondary_style` is an
optional, distinct supported cross-training identity; display it through `Fighter.style_label` and
apply it only through bounded shared style helpers. Never store behaviours such as Dynamic Attacker
or Submission Hunter in either style field. New-universe secondary assignment is deterministic and
must not consume simulation RNG; old saves safely default to an empty secondary style.
Every `create_generated_fighter()` result must finish with a supported primary style and a validated
distinct secondary style. The final generator guard may normalize blank or legacy labels but must be
deterministic and must not add another random draw; smoke coverage should sample generated entrants.

### Mechanical intent

- Kicks depend on kick speed, power, technique, stamina, distance, and defense.
- Punches depend on hand speed, punch power, technique, head movement, guard, chin, and stamina.
- Grappling depends on takedowns and setup, sprawl, guard work, control, submissions and defense,
  stamina, and position.
- Stamina and momentum should visibly influence later exchanges.
- Ground, clinch, and cage position must reset or transition according to the rules; state must not
  leak impossibly across a horn.
- `clinch_controller`, `top`, `bottom`, damage, stamina, and unanswered offense use private per-bout
  fighter slots. Compare them through `fight_state_key()`, never a display name. An unanswered
  sequence advances only when significant strikes land, clears when the pressured fighter lands or
  creates a meaningful grappling/positional response, and resets at every horn.
- Tournament participant names are presentation. Resolve the aligned `fighter_ids` list for the
  bracket, replacements, and temporary state; use object identity for private in-memory snapshots
  such as pre-view fatigue so same-name entrants remain independent.
- Commentary must never describe new actions after a finish.
- Equal score totals must be capable of producing draws.
- End-of-fight output includes the completed rounds and scorecards where applicable.

### Round count

The event data decides championship pacing. A fight marked `title` or `main` uses the configured
`title_rounds` value, including player-selected six- and seven-round settings; ordinary fights use
the normal `rounds` count. Never hard-code five introductions or four transitions in the watcher.
Test title and non-title five-round main events plus an extended configured title fight.

### Commentary structure

Five-round fights generate enough text to exceed a Tk text widget's comfortable live-display size.
The engine and archived fight log retain every generated action call and the original round-summary
telemetry. The live watcher defaults to a derived `Broadcast` stream that may condense repeated,
low-value timestamped calls; `Detailed` mode and completed-bout review expose the complete stored
transcript. Viewer compaction must be deterministic, must not mutate the archive, and must never
consume a simulation RNG stream. Structural and evidential lines must always survive:

- tale of the tape and opening context;
- every round introduction;
- every horn/round transition;
- every round summary;
- stoppage and official-result lines; and
- decision scores.

The live watcher may redact exact judge cards until the official result, but it must not replace or
shorten the round-summary line itself. Apply any display name cleanup before inserting a line into
the Tk `Text` widget; post-insert formatting cannot repair text that was already presented or alter
its tags. `stability_test.py` must advance a real five-round title viewer through each round and
verify all five original summaries, the scorecard reveal, metrics, and official result remain visible.

The live density control is presentation state. Switching an active or completed bout between
Broadcast and Detailed must rebuild only the reached visible lines, preserve the same raw-source
playback frontier, keep sealed scorecards sealed and leave the archived transcript unchanged. Round
separators, knockdown emphasis and finish emphasis are Tk tags/layout only. The visible personality
indicator reports the voice saved with that fight log; it must not imply a mechanics setting.

`FIGHT_COMMENTARY_ROUND_LINE_LIMIT`, `FIGHT_COMMENTARY_ROUND_HEAD_LINES`, and
`FIGHT_COMMENTARY_ROUND_TAIL_LINES` bound only ordinary timestamped calls in the derived Broadcast
view. Important middle-round evidence outranks head/tail position, so never use a blind slice. Never
deduplicate or trim `FightResult.commentary`, the archived `lines`, or the structured trace. A legacy
technical suffix may be removed from Broadcast prose, while its target, defense, follow-up, move and
position remain available in Detailed commentary or `round_analysis`.

Completed offense and ground-state progress are important Broadcast evidence. Landed standing
strikes, successful takedowns, landed ground strikes, passes, sweeps/reversals, escapes and stand-ups
receive priority over routine movement; identical calls remain capped at two even when their position
or outcome makes them high-priority, and repeated failed
attempts or passive control may condense. A same-position sweep is proven by changed
top/bottom ownership even when the position label remains `guard`. Any compact note must count the
actual omitted standing, standing-striking, takedown, ground-control and ground-striking lanes without
inventing success, damage or a position change.

Fact-driven wording variation must be selected from stable trace/bout material or the isolated
presentation stream; it must never call the mechanics, officiating, judging or process-global RNG.
Every exchange call must agree with the recorded actor, move, outcome, named defense, counter flag and
settled position. Context is evidence-bound: signature/mastery comes from the selected move payload,
stance and plan from trace state, damage/momentum from completed public deltas, camp/coach from fighter
data, and championship/rivalry stakes from the scheduled bout and identity-safe relationship helpers.
The bout-local commentary profile may record derived standing, ground and defensive strengths, but it
is presentation evidence only: use the strength relevant to the recorded weapon or transition, never
consume RNG or change an exchange. A failed submission trace must retain the actual technique chosen by
`submission_technique()`, a legal named defense and a natural consequence. A referee inactivity reset
is a separate structured fact; never credit the preceding ride/cling action with escaping to range or
use the referee's reset as effective-action evidence for trait or camp praise. The contextual
generators must return before consuming their per-fighter call allowance on a referee stand-up. Never
append old-position colour after a fighter has reached the feet. Ground presence lines must respect
current top/bottom ownership and every `GROUND_POSITIONS` state.
Do not infer a coach, rivalry, stance switch, plan change, blocked strike or successful counter from
style flavour alone. A failed sweep, stand-up, pass or transition must be described as an attempt,
not settled success. KO/TKO attribution must use causal damage/impact evidence rather than whichever
non-damaging move happens to be the final trace row.

Required regression scenarios include:

1. a five-round title decision with all five introductions and summaries;
2. a non-title five-round main-event decision with the same structure; and
3. a late round-five finish with the round-five introduction and official result preserved.

4. a configured seven-round title decision with all seven summaries, transitions, scorecards,
   metrics, and the official result preserved.

### Outcome calibration

The move-system expansion follows `docs/FIGHT_MOVE_SYSTEM_PLAN.md`. Its Step 0 reference is
`analysis/move_registry_parity.json`, captured directly from revision `4a73923` by
`tools/move_registry_parity.py --capture-ref 4a73923`. Capture refuses to overwrite a reference;
ordinary structural verification uses `--verify analysis/move_registry_parity.json` and writes
nothing. Preserve tuple and candidate order while sorting unordered sets. The parity regression
must reject reordered definitions and legal pools, changed fields and corrupt checksums. This
registry gate supplements, never replaces, the complete result and action corpus gates.
After approved content additions, preserve the original snapshot and its `compare_legacy`
projection against the immutable Slice 6 snapshot to protect every old record and lookup order.
Phase 31 permits only 125 reviewed successor-list updates through
`--verify-followups analysis/move_registry_slice6.json --followup-manifest analysis/move_followup_phase31_revised_manifest.json`.
The manifest binds the source checksum; every other field, ID, order and lookup remains exact.
The parity regression proves both historical links. Exact structural parity now uses the
separate `analysis/move_registry_followup_continuity.json` content snapshot. The prior Phase 31 snapshot is
connected through `compare_deprecation_update`, allowing only schema 1 to 2 and `deprecated=False`
on each move, into the immutable `analysis/move_registry_schema2.json`. A second successor-only
manifest, `analysis/move_followup_diversity_manifest.json`, binds that schema-2 source to the
30-root diversity update, followed by `analysis/move_followup_continuity_manifest.json` binding
the frozen diversity snapshot to the second 30-root layer. Each historical manifest must compare
its own source/destination, not silently allow all subsequent changes.
`analysis/compare_followup_diversity.py` compares the latest layer's complete paired bouts,
rejecting mechanical drift or a failure to improve chained selection share. Future content snapshots require
explicit reviewed additions, never replacement of the historical reference. Append new persisted
IDs to `EXPANSION_MOVE_IDS` so deletion protection covers new techniques as well as the original 200.
Sequence ownership checks must match the resolver in common and specialist ground positions,
including turtle, front headlock and leg entanglement. Chain acceptance cannot use a completed-only
median (which excludes interrupted roots by definition) as proof of the attempted-chain median.
The report records `phase_31_acceptance_failures`; `--require-phase31` enforces this unfinished
phase's targets before sign-off, separately from the already accepted content gates.
Use `analysis/generate_chain_opportunity_report.py` to diagnose failed roots before changing chain
weights or lifecycle. Keep its denominator aligned with the coverage report. Its best-three-action
bound ignores move eligibility and graph constraints and is conditional on existing observed roots;
never cite it as proof that a different catalogue cannot meet the target. Do not count an unrelated
action in an old occurrence unless a real declared graph edge connects it.
Separate emergency survival from other undeclared successor actions and from declared actions
without named completion. Derive declarations from the recorded branch IDs, not all moves sharing
an action. Trace-only diagnostics must not attribute losses to unrecorded ranking/eligibility gates;
retain every interrupted root and the existing optimistic-bound calculations.
The second, existing-technique bound must use union coverage over at most three move IDs, not
the sum of their individual counts. It filters both the root's settled context and the next
selection context, but intentionally omits skills, rarity, ranking and acyclicity. Preserve these
limitations when using the diagnostic to propose changes to the phase order.
`followup_defensive_continuity.py` is an unregistered append-only experiment, covered by the draft
authoring regression. Its four named recovery nodes have graph successors but ordinary `survive`
control outcomes do not seed another live step. Do not mark the longer-chain target complete from
those graph edges or add control tags merely to bypass the runtime effectiveness rule.
Use `tools/benchmark_move_selector.py --check` for the fixed 15% selector-time target at 800 moves.
It appends immutable benchmark-only clones, restores registry bindings and RNG, and compares repeat
mechanics. Windows CPU-clock quantization makes per-function CPU attribution unreliable; the tool
reports high-resolution cProfile attribution plus whole-sample CPU and wall time separately.
Structural selector edits must also pass `tools/move_selection_parity.py --verify analysis/move_selection_followup_continuity.json`.
The selection regression reconstructs the immutable schema-2 content in memory and checks all
44 original Phase 31 bout hashes through the strict deprecation migration. Preserve this historical
test as well as the current-content snapshot; the follow-up content update is not a refactor waiver.
Keep each catalogue source at or below 400 lines; the registry regression enforces the plan's
reviewability ceiling, so split new domain content rather than rebuilding a monolithic catalogue.
The immutable pre-refactor snapshot binds the exact registry checksum, complete fixture definitions,
ordered traces, move/defense/sequence payloads and mechanics for 44 bouts. It supplements rather
than replaces the 3,840-bout result/action gates. Never recapture this snapshot to hide refactor drift.
The six `_move_candidates`, `_move_static_score`, `_move_contextual_score`, `_move_rarity_gate`,
`_select_from_pool` and `_move_payload` helpers retain engine ownership of selection. Preserve
left-associated score addition, candidate-relative signature-finisher exclusion, authored-top
priority, counter restrictions, threshold boundaries and generic payload defaults when optimizing.
`_fight_move_score_cache` lives inside `simulate_fight` and must restore the previous object on
nested calls or exceptions. Cache by fighter and definition identity, retaining the definition;
same-ID registry replacements must not reuse stale scores. Do not cache dynamic candidate-relative
signature exclusions or exchange context across ticks. `fight_move_cache_regression_test.py`
protects warmup, isolation, development boundaries and replacement definitions.
Retirement uses `MoveDefinition.deprecated`, a strict boolean defaulting to false. Keep retired IDs
in `MOVE_REGISTRY`, signature/mastery normalization and replay lookup; exclude them from `MoveIndex`,
live successor branches, new generated signatures, camp growth and mastery-to-signature promotion. Existing retired
signatures/mastery remain intact (ordinary age decline may still apply). The deprecation tests
must distinguish preserving a learned move from acquiring a new one.
The registered `followup_diversity.py` layer has separate authoring tests. Clinch-entry successors
must be checked against the resulting clinch/cage state, not the entry's standing start position.
Keep historical authoring checks layered through explicit expected follow-ups, not field omissions.
Specialist attacks/back takes/escapes reset ground inactivity even on defended attempts, just like
ordinary submission and recovery attempts. Stationary rides/holds still advance referee inactivity.
Run `fight_ground_activity_regression_test.py` for both ownership directions and warning thresholds.
Phase 29's fresh 300-fight coverage report must show all 16 additions, at least six legal top
submissions in guard and half guard, and at most 25% concentration in one top submission. Retain
the ungated `top_submission_chain` for fighters below specialist skill gates. Technique identity
must not alter the broad submission resolver's selected choke/lock mechanics or finish result.
Phase 30/33 adds 33 moves and 22 defenses. Its full-fight report must show every new move, four
recoveries per ground position, two definitions per referenced defense family and fewer than ten
uses of an identical rendered defense clause across 300 fights. Count clauses actually present in
rendered commentary, not all candidate wording. Body-only and punch-only defensive tags constrain
selection before scoring. Name/wording choices must remain deterministic and consume no RNG.
Explicit kick/knee/elbow tags override a broad power-punch or dirty-boxing action when checking
punch-only defense eligibility; those calibrated actions are not proof of a boxing weapon.
The named-defense reachability probe must supply a permitted incoming target/weapon for restricted
defenses. Blank synthetic attack metadata is not evidence that a body-only or punch-only defense
is unreachable; keep the negative runtime eligibility test alongside the positive audit probe.
`analysis/compare_bottom_move_expansion.py` reconstructs the reviewed Phase 29 registry in memory
for paired 300-fight evidence: bottom vocabulary must grow while outcome and broad exchange
signatures remain equal. Do not overwrite user fighters, saves or historical source to run the pair.
Protect defensive mastery IDs through `PERSISTENT_DEFENSE_IDS` as well as move ID protection.

`fight_engine_audit.py` and `analysis/fight_engine_baseline.json` are the preservation authority for
the staged fight-engine roadmap. The UI-free harness clones its inputs, restores process RNG, and
captures per-exchange evidence without changing the underlying engine result. Before and after each
fight-engine phase, run `analysis/generate_fight_engine_baseline.py --verify
analysis/fight_engine_baseline.json`. Use `--exact-parity` only for an architecture slice that does
not intentionally remove legacy presentation draws from the combat stream. RNG separation is
accepted on the locked distribution gates, with hard overall/KO/TKO limits and confidence-aware
small-group checks; do not require identical individual outcomes after stream decoupling. Do not
regenerate the checked-in baseline after a code change merely to make drift disappear. A deliberate
baseline replacement requires an explicit balance change and synchronized report/document updates.
`analysis/fight_engine_action_baseline.json` is the pre-move-expansion authority for action frequency,
effectiveness, damage, energy, counter, position and finishing contribution. Regenerate it only for
an explicitly approved mechanical baseline replacement; verify it with
`analysis/generate_fight_action_baseline.py --verify analysis/fight_engine_action_baseline.json`.
The canonical isolated runner executes this verifier after the result baseline so presentation-only
changes prove that neither finish rates nor the amount and effectiveness of the ground game moved.

`compare_to_accepted_calibration()` is the exact headline release gate layered over the older
tolerance report. The canonical isolated runner executes the complete 3,840-fight verifier and must
reject a one-bout change from 2,319 finishes, 633 KOs or 731 TKOs. Do not weaken this to rounded-rate
comparison: the displayed 60.39% / 16.48% / 19.04% values are derived from those integer counts.
It must also reject a competitive finish rate outside 48-54%, a competitive submission-family rate
outside 15-19%, zero Doctor or Injury Stoppages, missing five-round evidence, or fewer than 6% of
five-round finishes in rounds four and five. The current accepted corpus has 1,408 competitive
finishes (48.89%), 488 competitive submission-family finishes (16.94%), four Doctor Stoppages, ten
Injury Stoppages, and 164 of 839 five-round finishes in rounds four or five (19.55%). These checks
reconcile the historical finish audit without applying its obsolete global retunes: mismatch bouts
drive the 60.39% aggregate, while competitive fights already meet its realism bands. Do not lower
global KO/submission conversion or halve championship dampers unless the user explicitly authorizes
a new mechanical baseline.

`FINISH_METHODS`, `KO_METHODS`, `SUBMISSION_METHODS`, and `KNOCKOUT_AWARD_METHODS` in `constants.py`
are the downstream method-classification authority. Career stats, seasonal counters, recovery,
contractual finish bonuses and excitement use the shared finish families. Knockout of the Year uses
the narrower highlight set so Doctor and Corner Stoppages cannot win a strike-highlight award.
Never reintroduce substring or exclusion-based finish detection in a consumer.

The original frozen baseline rates are 59.64% finishes, 15.70% KO, 19.66% TKO, 22.29% submission
and 1.17% technical submission across 3,840 fights. The accepted post-roadmap calibration is 60.39%
finishes, 16.48% KO and 19.04% TKO. Competitive low/mid/high and mismatch results are separate groups;
follow the tolerances in `FIGHT_ENGINE_DEVELOPMENT_PLAN.md`. Detailed-skill coverage also
distinguishes direct fight inputs from `dedication` and `weight_cutting`, which operate through camp/
development and weigh-in state respectively. Do not add a detailed fighter attribute without either
using it mechanically or documenting and testing its pre-fight role.

`FightResult` is the structured MMA result boundary. `simulate_fight_result()` returns it directly;
legacy callers continue through `simulate_fight()` and its five-item tuple. Native trace events use
private `a`/`b` slots and retain action, position ownership, gas, location damage, cuts, knockdowns,
strikes, takedowns and submission deltas, followed by exactly one `official_result` event. Adding
trace evidence must not consume RNG or change any baseline signature.

`fight_moves/` is the canonical MMA move registry, preserving the former module's public imports.
`schema.py` owns immutable definitions and closed metadata vocabularies; `catalogue/` contains
domain modules whose historical batches are concatenated in explicit order. Never regroup those
batches by family: tie-breaking and fallback order are compatibility behavior. `index.py` builds
immutable ordered lookup tables once; empty targets exclude targeted moves, while unknown targets
still allow untargeted moves. `validation.py` rejects unknown tags, metadata and removal of IDs in
`legacy_ids.py`; keep that permanent ID set synchronized with the historical parity reference.
Behavioral tag constants live in the schema and are reused by selection. Run both registry test
suites and the byte-identical parity gate after structural changes, followed by full fight gates.
`coverage.py` (re-exported by validation) reports eligibility relative to supplied engine contexts.
Use pre-exchange position/action/target triples from complete traces, never registry declarations
or intermediate position paths as proof of a selection opportunity. The 300-fight coverage reference
is a named allow-list for existing gaps, not evidence that rare specialist positions are impossible.
New gaps must fail; tighten resolved allowances rather than expanding them to hide dead content.
The variety report's denominator is every exchange selection; per-fighter variety includes both
corners, including a zero-action fighter. Keep draft authoring modules outside catalogue assembly
until the preceding runtime revision's gates finish; test combined definitions without mutating
the active registry. Register each reviewed batch with permanent IDs, an exact versioned snapshot
and fresh ordinary-fight appearance evidence before calling it delivered.
The Slice 5 paired test reconstructs `move_registry_phase30_33.json` and patches only an isolated
process's move lookup/registry for the two arms. Keep the reference immutable and compare broad
mechanical signatures alongside actual selection evidence; registry legality alone is insufficient.
The Slice 6 paired test uses the immutable Slice 5 snapshot. Its registration regression also
locks an authored minimum of 18 moves per supported style plus an exclusive combination/finisher;
do not restore the initial thin-style allowances once these floors have been reached.
When comparing a Slice 6 source definition with the live registry, apply the registered
`ACTION_DIVERSE_FOLLOWUP_UPDATES` and `CONTINUITY_FOLLOWUP_UPDATES` first. Those reviewed layers
intentionally replace `follow_ups`; equality against the earlier source literal is a stale test,
while any difference in another field remains a regression.
Skill-median warnings distinguish representative use from maximum-skill reachability. Authoring
helpers in `presets.py` leave existing definitions untouched; document fields and required metadata
in `docs/FIGHT_MOVE_SCHEMA.md` and run the coverage/preset regression plus unchanged parity.
Move IDs are stable trace/save-facing identity;
`fight_moves/chains.py` validates an immutable follow-up graph during registry construction.
Use iterative topological ordering so large catalogues do not depend on Python's recursion limit.
`chain_depth(move_id)` counts maximum possible successor edges (leaf zero); actual trace sequence
length must be measured from selected exchanges, never copied from this potential-depth value.
Run `fight_move_chain_regression_test.py` and exact registry parity after graph-only changes.
definitions must use supported positions, styles and detailed skills, and follow-up IDs must resolve.
Broad actions remain the calibrated resolution boundary. Deterministic move selection may use detailed
skills, style, stance, matchup and a real counter window, but must not consume mechanics, officiating,
judging or presentation RNG. Move energy, miss risk and counter vulnerability may only alter later
legal move identity through bounded, decaying bout-local state; they must not alter broad gas, damage,
landing or finish conversion. An unavailable move uses
an explicit `generic_<action>` fallback rather than inventing an illegal technique.

Release move audits must keep the frozen `matchup_specs()` corpus unchanged. Supplemental style coverage
belongs in `move_report_specs()` so the exact 3,840-fight result/action baselines remain comparable. A move
missing from the general sample is not automatically dead: the targeted registry reachability check must
prove whether a legal, skill-supported specialist can select it. Dominance comparisons must use the same
parent action and legal position, not aggregate techniques that cannot compete in the same state.
Direct registry reachability is not proof of full-fight reachability when a test supplies a target or position
that the broad resolver never emits. New ordinary standing and common-position ground content must also appear
in the representative 880-fight report; reserve probe-only absence for genuinely rare specialist
positions/actions. The expanded catalogue retains one exclusive combination and one
exclusive finisher for each of the 18 supported styles, ten earlier expanded standing combinations,
six uncommon authored standing finishers and 23 expanded ground techniques. The turtle wrist-ride striking chain
is the only latest addition intentionally absent from the representative corpus; targeted reachability and
the specialist transition path remain its gates.

Moves tagged `style-combination` must name exactly one supported `preferred_styles` owner, retain at
least three ordered `components`, and be filtered before scoring unless that owner is the fighter's
primary or secondary style. Signature or mastery data must never bypass this eligibility rule. These
chains remain identities beneath one already-resolved broad action: their components, follow-ups and
commentary may change, but they must not add a strike, landing, damage, transition or finish roll.

Moves tagged `style-finisher` follow the same single-owner primary/secondary-style restriction and
must be either a strike or submission. Their deterministic appearance window may make an already
selected technique more recognisable, but it must never create or convert a KO, TKO, submission,
damage event or stoppage. KO/TKO narration must use trace-backed impact from the causal move;
submission narration must use the last resolved submission payload. Every style finisher must remain
reachable, appear in the 880-fight representative report and preserve exactly one official result.
When a fighter owns another legal signature finisher, that individual signature takes selection
priority over the generic style finisher during the bounded authored-finisher window.

The Standing group includes `combination_punching`, `body_punching` and `counter_timing`. Legacy
non-empty detailed profiles derive them in `ensure_detailed_skills()` from existing saved ratings;
never replace them with generic 50s or consume RNG during load. Distance management remains the
existing footwork/feints/mobility/reach bundle rather than a duplicate detailed attribute.
Profile stats, detailed-skill popups and skill-card readers must use a copied,
deterministic projection rather than `ensure_detailed_skills()`. An empty
legacy dictionary may display bounded values derived from the saved broad
ratings, but opening or refreshing a profile must not generate, persist or
repair detailed skills. Explicit load, editor, simulation and migration paths
remain the only owners of the RNG-backed repair.
Academy rival-program tables must likewise call `rival_academy_program(...,
repair=False)` and render a defensive projection. They must not seed missing
AI youth-program strategy data while the Academy page is opened or refreshed;
calendar progression and explicit rival-academy actions keep the repairing
default.
When a detailed-skill group expands, preserve development exposure as well as serialization. Standing
training scales its successful-block point budget for these three added skills; otherwise a fixed budget
silently dilutes every striker's development even though fight-result calibration remains unchanged.

Kick-tagged registry moves must define a supported target, `side`, `range_band`, and at least one
`defense_families` entry. Spinning/flying/high-risk techniques require a meaningful minimum-skill
floor, energy/counter risk above neutral, and the deterministic rarity gate in move selection. Reuse
the existing high/low/creative kick, knee, elbow, flexibility, mobility and reflex ratings unless a
future skill audit proves a genuinely distinct axis.
The `finisher` tag is a rare identity gate, not a finish modifier. A finisher must be a skill-gated
standing strike with above-neutral energy and counter risk; its shared deterministic gate may select the
named move only after the broad action has resolved and must not consume RNG or alter finish conversion.
When a KO or TKO has causal trace evidence, the registry move is the authoritative strike name. Legacy
finish-color banks may not leave a second, contradictory uppercut/hook/kick beside that causal move.

Takedown-tagged registry moves must define `entry_family`, non-empty `defense_families`, and only
legal `finish_positions`. The resolved trace remains authoritative for the actual position path and
controller; registry metadata must never claim a finish position the broad resolver did not reach.
Current common shot and takedown success settles in guard/half guard, not side control. Draft
entry follow-ups must include legal top-ground continuations; a cage finish can cover a near-success
entry, but should not be the only branch offered after a completed takedown.
Hand fighting, underhooks and wall walking currently reuse clinch control/defense, cage wrestling,
get-ups and scrambles rather than adding duplicate detailed attributes.

Submission-tagged registry moves must define a position-legal `attack_path` and non-empty
`failure_outcomes`. The resolver's recorded `submission_escape` and actual position path remain
authoritative; move metadata may describe legal possibilities but must not invent a finish or a
transition. Chaining currently reuses transitions, positional ability, submission attack, leg locks,
control, scrambles and fight IQ rather than adding a catch-all submission-chaining rating.

Common ground moves must be restricted to positions where their broad action can actually be chosen.
Position-specific ground striking still resolves through `ground_strikes`; passes/climbs through
`advance_position`; sweeps through `sweep`; recoveries/get-ups through `recover_guard` or `stand_up`; and rides
through `ground_control`. Named identity must not directly change damage, success, position or finish chance.
Every authored ground-strike chain needs a factual component template that reconciles realistic 10-26-strike
broad volume, and a ground TKO must name the causal registered strike chain rather than generic legacy copy.
An effective registry move tagged `control` may seed one legal bounded follow-up from an existing `control`
outcome; this changes only later move identity and must never grant a free exchange or change control scoring.

`Fighter.signature_moves` contains at most three unique stable registry IDs. New-universe generation
may derive skill-supported signatures deterministically; ordinary save load must only normalize known
IDs and must not invent a new set. A legal signature receives a bounded selection preference but
never bypasses minimum skill, position, target, counter-window, defense, or finish resolution.
`career_signature_stats` folds the last fight's attempts/effective uses/finishes during the same
career-stat commit that clears `last_fight_stats`; preserve fighter-ID separation in persistence and UI.

`Fighter.move_mastery` contains normalized 0-100 values keyed by a move ID or `defense:<defense_id>`.
It is persistent fighter development, but it may only shape named technique selection beneath the broad
resolver. Camps may improve focus-aligned mastery and grant a signature at the audited threshold;
academy prospects retain their own mastery dictionary and copy it on graduation; annual veteran decline
may reduce high mastery after `prime_end + 2`. Legacy load defaults to an empty dictionary and must not
consume RNG or invent mastery merely by opening a profile.

`DEFENSE_REGISTRY` is the canonical defensive identity surface. Every exchange trace retains a known
`defense_id` and payload selected from the attacking move's legal defense families and the defender's
skills. Named defense is evidence, not a second success roll: never use it to retroactively change the
already-resolved outcome or consume another combat draw.

Tactical move reads are bout-local, derived only from earlier public trace, and capped per counter.
Plans may weight matching move tags; body/leg/setup evidence may open later families; repeated move IDs
may be penalized; and opponent-pattern counter bonuses require a real counter window. Preserve
`selection_reasons` for explainability. Never persist these reads, scan career history during a fight,
or convert a move-family preference into direct landing/finish probability.

Registry follow-ups may create a bout-local move chain only after effective use. A matching legal
alternative may receive continuation preference only after normal style, skill, target, counter
and rarity gates, and only within the strongest five ordinary candidates. Keep the authored-top
bypass. Selection happens after resolution, so ownership eligibility must use the supplied
pre-exchange snapshot, not the newly reversed top/bottom state. Seed successor roles from the
actual settled ownership; same-position sweeps are effective, referee resets are not.
Occurrence IDs use actor/starting round/tick and actual depth increments only on a selected branch;
do not confuse this with the graph's maximum possible depth.
follow-up receives a bounded selection preference for at most two ticks in the same round, and the trace
must identify its source and completed step. It remains one ordinary broad action, never a free attack.
Multiple follow-ups are legal branches. Choose only a branch valid for the resulting position, retain
the options/reason in trace evidence, and let a named frame/evasion/escape select the alternate branch.
Authored strike-combination templates must identify their actual component weapons and reconcile sequence
numbers and landed totals at realistic broad-action volume; a generic action fallback is not sufficient
coverage for a newly named sequence.
All supported primary styles must retain explicit tag preferences and stay distinguishable in the
pairwise release-report distance check. Stance and striker/grappler matchup reasons must remain traceable.
Dynamic stance changes are bout-local and cooldown-bound. They require a natural switch stance or high
footwork/adaptability, retain from/to/round/tick/plan evidence, and must not mutate the fighter's saved
base stance or add a new mechanics RNG draw.

Archived fight logs may persist bounded `round_analysis` derived from their completed trace. Replay UI
must tolerate old logs without it and show only recorded moves, defenses, sequences, stance switches and
plan history; it must not reconstruct results, expose sealed cards early or mutate career state.

Fight presentation must render from the completed trace. Natural Broadcast prose uses the recorded
actor, move, outcome and salient target, defense or position; it must never join a named move to the
older broad-action `result` text. Detailed commentary and `round_analysis` retain target, defense and
meaningful follow-up labels without raw bracket metadata. Finish prose must use the final exchange's
actual move and settled position, retain authored submission/medical/injury/head-kick/walk-off detail,
and contain at most one intervention clause and one official announcement. A body- or leg-kick
knockdown is not an `injury_stoppage`; only the separate body/leg stoppage check may assign that
finish method. Doctor review uses structured cut evidence and may become eligible only at the
between-round tick. Presentation-only walk-off variation may use the presentation stream, but an
existing mechanics draw must not be removed, added or reordered merely to select wording.
Round/UI summaries expose bounded move-family effective/used counts, never raw unbounded dumps or
unsealed judge totals. `last_fight_stats`, FightResult metrics and `career_move_family_stats` must
reconcile with the same exchange events; presentation must not draw simulation RNG.

At the start of a bout, `simulate_fight()` establishes explicit mechanics, officiating, and
presentation streams. All combat draws go through `fight_mechanics_rng()`, referee/stoppage/judging
draws through `fight_officiating_rng()`, and wording through the presentation helpers. Do not add a
direct `random.random()`, `random.randint()`, or `random.choice()` call to `fight_engine.py`; the
focused regression treats one as an accidental stream leak. The caller's public RNG advances to the
combat stream's final state so sequential unseeded cards continue to vary.

Commentary variation uses the bout-local presentation RNG through `fight_presentation_choice()` and
`fight_presentation_random()`. Do not add global `random` calls for wording, clocks, ambience, or
phrase selection. A foul or other event that changes gas, damage, position, scoring, or stoppage
risk belongs in a mechanical resolver before its text is rendered; `dynamic_flavor_line()` must
remain presentation-only. The phrase-bank regression must keep winner, method, round, stats and
cards identical when wording is replaced.

`fight_commentary_mode` defaults to `Broadcast`; `fight_commentary_personality` defaults to
`Balanced`, with `Technical`, `Excitable`, and `Concise` as presentation-only alternatives. Both live
in `rules`, require old-save normalization, and may affect wording or density only. Corner advice may
cite completed public trace evidence such as gas, damage, control, repeated moves and effective
families; never expose hidden ratings or repeat developer-facing text about an unassigned plan.
Between-round feedback must name a verified head coach and Gym when available, give a factual round
read and a separate actionable instruction, and vary delivery by commentary personality without RNG.
If both opponents share one verified Gym, identify each fighter's camp corner without assigning the
same head coach to opposing stools. The commentary report permanently gates speaker/fighter identity,
actionable wording and hidden-rating leakage across representative complete fights.

`TRAIT_COMMENTARY_INTROS` must cover `TRAITS` exactly. Every saved trait receives one natural opening
line, but a live trait call requires completed trace evidence matching its claim: target, move tag,
counter, position, submission attempt, plan change, accumulated damage, recorded gas, timing or bout
context. `record_fight_trace_exchange()` stores the selected line and enforces at most one contextual
trait call per fighter per round and two per fighter per bout. Rendering that line is deterministic,
must not consume any RNG stream, and must never imply survival, a finish or an injury that has not
already been resolved. Do not restore the older random trait branches in `dynamic_flavor_line()`.

Camp commentary must resolve `Fighter.camp` against an actual current `Gym` before naming a coach,
city, region or specialty. Saved camp strings may instead be promotion, feeder, academy, unknown or
legacy labels; introduce those with natural neutral wording and never infer Gym facts from the label.
When both opponents resolve to the same verified Gym, emit one stablemate-room introduction rather
than assigning the same head coach to two opposing corners. A contextual
camp call requires a completed exchange matching one of the resolved Gym's recorded specialties:
boxing, kickboxing, wrestling, BJJ, sambo, clinch, gameplanning or conditioning. Store the selected
line on the exchange trace, cap it at one per fighter per round and two per bout, preserve it in
Broadcast, and consume no RNG. `Prospect Development` is opening identity only unless future trace
evidence provides a genuine live-fight predicate. Focused coverage must compare the same seeded bout
with and without verified Gym metadata and require identical result, metrics, scoring, mechanical
trace and process RNG state.

Audit finish rates by fighter tier, not only across a random-paired pool. Random pairing
over-represents mismatches, which finish more easily than realistic cards.

MMA judging consumes `round_evidence_from_trace()` only. Do not award score value for gas,
professionalism, discipline, home support, experience, pressure, popularity, or names; those inputs
may change execution but are not judging criteria. Apply effective striking/grappling first,
effective aggression only when that evidence is close, and control only when both are close. Judge
variance belongs on the judging substream and only inside the ambiguity band, so scoring work cannot
change a later stoppage draw or reverse clear dominance. Store the player-facing verdict separately
from canonical `Decision`/`Draw` method values for save and downstream compatibility. Every 10-8 and
point deduction must retain round evidence in the official card and trace.

In-bout `damage`, `head_trauma`, `body`, and `leg` are persistent trauma channels; `hurt` is the
transient stun/instability channel used by immediate survival and calibrated stoppage checks. The
legacy `head` channel is a short-term reaction load and may settle during survival, while every head
impact must also increment `head_trauma`; trace and post-fight metrics expose only the permanent
channel. Defensive success, `survive`, and `recover_between_rounds()` may reduce `hurt` and restore
bounded gas, but must never subtract persistent location damage. Body trauma affects output/fatigue,
leg trauma affects mobility/kicks/shots/stand-ups, and head trauma affects reactions. Cuts use `cut_state`
  records with location, severity, bleeding, swelling and vision risk while the numeric `cuts` count
  remains compatibility telemetry. `last_fight_stats` is the shared Fight Night/post-fight medical
  record; recovery logic must read its damage and `cut_details` rather than inventing unrelated harm.
  Run `set_post_fight_recovery()` and `apply_visible_trauma_consequences()` before
  `commit_career_stats()`, because that final commit clears `last_fight_stats` after the medical
  evidence has been consumed.

Visible damage narration is a deterministic presentation layer over those persistent totals. A bout
latches each head, body and leg milestone once, records the structured event in its trace, and retains
the corresponding line in Broadcast and round analysis. It must not consume any RNG, alter trauma,
or add a stoppage opportunity. Broad milestones may describe only supported visible states such as
bruising, guarding, a weight shift or a limp; never infer fractures, organ damage, concussion, or an
exact body-part location. Exact location, bleeding, swelling and vision language must come from the
structured `cut_state` record. When damage copy changes, run the focused milestone/RNG regression,
the commentary report and both frozen result/action baselines.

Fight plans are scheduled-bout state keyed by `fighter_id`, never display name. Player-created
bouts must store an explicit plan for every known corner; `apply_world_data()` normalizes supported
values and gives legacy missing entries Balanced. AI/world bouts must set `ai_controlled` so
`ai_fight_plan()` uses the shared execution model. A payload with no plan marker is a compatibility
bout: it stays Balanced and does not begin automatic between-round switching. Plan effects belong
in action weights, target shares, counter opportunities and energy cost—not direct result or finish
modifiers. `adapt_fight_plans()` may read trace evidence, gas and visible trauma only. Evidence-led
changes retain the repeated opponent move or successful own family, adjustment round and confidence;
do not oscillate more than once in a round. When changing
plans, run `fight_engine_regression_test.py`, the save/load smoke test and the frozen 3,840-bout
verifier; do not alter `competitive_finish_conversion()` or regenerate the baseline to absorb drift.

Each exchange trace must retain a bounded `exchange` chain with setup, defensive response, counter
opportunity/consumption, follow-up, ordered combination components and no more than five phases.
Derive semantic labels from the already-resolved action, position and skills; recording trace detail
must never consume another mechanics draw. A counter is valid only when a prior failed or defended
attack created its `counter_window`. Combination components are evidence for aggregate strike stats,
not extra attacks: their landed count must stay at or below attempts. Preserve deterministic chains
and the controlled Counter-striking-versus-Pressure regression when changing initiative or actions.

`ALLOWED_FIGHT_TRANSITIONS`, `GROUND_POSITIONS`, `validate_fight_transition()` and
`set_fight_position()` are the MMA positional authority. Ground states require distinct `a`/`b`
top and bottom owners and no clinch controller; open range retains none. Use
`record_intermediate_position()` for a real but unconsolidated state inside one exchange, and keep
its complete validated `position_path` in the trace. Elite specialists may consolidate a failed shot,
standing rear lock or leg entanglement into a persistent next-tick state only at the audited thresholds;
the 720-fight specialist report must continue to prove each state has legal follow-up action families.
Other brief positions require the resolver to award durable control. Submission attempts that do not
finish must set `last_submission_escape`
with their retained, recovered, reversed or worsened consequence. Any new grappling position needs
an allowed entry, exit, action selection, ownership test and commentary consistent with the trace.

Competitive same-tier targets:

- Low tier (`overall < 68`): about 50-56% finishes.
- Mid tier (`overall 68-80`): about 32-42% finishes.
- High tier (`overall >= 80`): about 38-45% finishes.

The best single audit is realistic matchmaking: pair fighters with an overall gap of at most six
across all tiers. A useful comparison shape is Decision ~47%, KO ~16%, TKO ~15%, Submission ~19%,
or roughly 52% finishes. A mixed random pool may report 60-65% finishes because of mismatches; that
is expected and should not be tuned away by weakening the whole engine.

Historically, elite competitive fights became too decision-heavy because damage scaled with strike
margin while defense and KO thresholds rose with skill. The current model gives impact meaningful
raw-power scaling and flatter threshold growth. Tune mechanics and probabilities, then rerun the
per-tier audit. Never overwrite the final method merely to hit a target percentage.

