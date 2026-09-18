# Specialist-state implementation audit

## Latest measured candidate: standing-back reset credit fix

The 385-definition developer trial (346 production definitions plus 39 drafts) reaches twelve
pre-selection positions in 300 combined bouts. Pocket and leg entanglement are still absent.
All eight rear-standing drafts appear. Its 3,840-bout calibration is rejected: 2,244 finishes,
572 KO and 708 TKO, versus the required 2,319 / 633 / 731. Exact source and registry fingerprints
are in `analysis/joint_candidate_standing_back_credit_fix_calibration.json`; coverage is in the
corresponding `_coverage.json`. The normal-play result gate separately remains exact.

Automatic failed-shot/rear-lock resets now preserve earned control but cannot grant extra
recovery, tactical/judging effectiveness or contextual praise, and break both fighters' chains.
Chain diagnostics keep these interrupted roots in their denominator and exclude them from
optimistic successor opportunities. Earlier sections below record prior development stages.

### Leg-retention trial and next distance slice

The first 400-definition leg-retention trial reaches thirteen positions but only three leg
entanglement exchanges in 300 combined bouts. It fails full calibration at 2,248 / 572 / 709
finishes / KO / TKO. Its immutable `joint_candidate_leg_retention_*` reports predate the named
submission identity fix: compatible identity must follow the actual mechanical lock, not merely
the same parent action. Unsupported delivery variants cannot receive signature/mastery credit.

Pocket investigation found range and pocket sharing all five action weights and no ordinary
entry writer. The new experimental slice uses an already contested punch to establish
or escape distance, keeps it persistent, and adds modest close-range action preferences. Context
`pressure` means psychological big-fight pressure, not forward movement: use footwork, aggression,
cage pressure and reach instead. Attribute defender pivots to the defender, preserve hit/miss and
damage facts, never overwrite caught-kick/knockdown outcomes, and do not award control or response
credit for a mere distance change. Measure pocket occupancy against range plus pocket beats;
the 8% threshold is an acceptance measure, never a runtime quota. The slice passes six focused
tests and the exact normal 44-fight comparison. Its ordinary coverage and 3,840-fight calibration
are running as new `joint_candidate_pocket_distance_*` reports; acceptance is still unproven.

Status: Phase 34 entry findings; normal play retains the verified entry rules.
An explicitly opt-in developer candidate now tests ordinary failed-shot and open-clinch
front-headlock entries. It is not accepted or enabled in normal game instances.
The narrow specialist inactivity-classification fix below is implemented and covered by regressions.
The current 300-fight coverage sample sees eight of fourteen pre-selection positions and nineteen
of thirty-three registered actions. Intermediate trace positions do not establish selection reachability.

## Submission-pool follow-up after identity correction

The identity-corrected candidate reveals a position/action mismatch in the mechanical pool:
top and bottom guard share one list, top half guard lacks several top attacks, and front headlock
uses a generic fallback. Adding names to the post-resolution registry cannot fix these gaps.
The new experimental slice is a pre-draw, context-legal technique adapter that replaces repeated
weighted tickets with authored variants while preserving array length/order and each ticket's
choke and leg/non-leg classification. It must run before the existing mechanical choice, not
rename an already resolved attempt. Twenty-one variants are implemented, with 56 focused tests
and the exact normal 44-fight snapshot passing. Ordinary use and full calibration are running
in the new `joint_candidate_submission_pool_*` artifacts; this is not release acceptance.

Verify registry position/action, actual controller role, minimum skill and explicit exclusive
style gates. Do not treat preferred styles as exclusivity. Preserve an original ticket if no legal
variant qualifies. Von Flue, scarf-hold and cradle attacks need genuine setup evidence, not a
position-only inference. Broad submission-chain identities are not generic aliases for every
lock, and existing `heel_hook`/`toe_hold` IDs are positional counter actions, not submission rolls.
Keep unsupported cases visible until their mechanics exist; test ticket conservation, setup/role
negatives, resolved identity, finish short-circuit and default-off parity before calibration.

## Entry blockers

The table describes the normal-play baseline, not the experimental candidate.

| Position | Current blocker |
| --- | --- |
| Pocket | No runtime writer enters it. Range and pocket currently share action weights. |
| Failed shot | Stuffed-shot entry requires margin at most -35 and simultaneous +45/+35 detailed-skill advantages. `front_headlock` falls back to broad wrestling rather than an authored detailed attribute. |
| Front headlock | Depends on the failed-shot bottleneck. No ordinary clinch snapdown entry exists. |
| Turtle | Entered from front-headlock sequences, not ordinary bottom turn-away responses. |
| Standing back control | Cage pummeling needs margin above 32 and a +45 back-control advantage. The reversal branch exits to cage before this possibility. |
| Leg entanglement | Requires Submission Ace, leg-lock skill at least 88, a +45 defensive mismatch and dangerous non-finishing bottom submission margin above 38. Coverage fighters use Gym Rat; that sample cannot enter this route. No sweep entry exists. |

These conditions are in `resolve_takedown`, `resolve_exchange`, `resolve_submission` and
the specialist branches of `choose_action`/`resolve_exchange` in [fight_engine.py](../fight_engine.py).
Five states have downstream mechanics already; pocket lacks an entry writer entirely.

## Additional defects to address with the first mechanical slice

- `force_cage` is chosen only from failed shot, but `fence_drive` permits only clinch positions.
  Correct its real context through an explicitly reviewed metadata migration; do not hide it in a generic fallback.
- `turtle_ride` can be chosen from front headlock while `turtle_breakdown` is turtle-only.
  Add an appropriate identity or explicitly review the technique's allowed starting position.
- Fixed: `update_ground_inactivity` now recognizes specialist submission attacks, back takes and
  active escape attempts, matching common-action semantics even when defended. Static rides and holds
  retain warning/stand-up behavior. The focused ground-activity suite covers both ownership directions.
- Failed shot and standing back control need bounded stalemate exits.
- Clinch-to-front-headlock is not currently a legal validated edge. Add only edges actually implemented.

## Ordered Class C implementation

1. Failed shot/front headlock: skill-sensitive branches within already-rolled stuffed-shot outcomes;
   retain clean defended-shot returns to range. Add a properly owned clinch snapdown route.
2. Turtle/standing back: ordinary bottom turn-away responses and cage reversal/rear-control outcomes,
   preserving the correct controller and settling until the next exchange.
3. Leg entanglement: leg-lock skill and mechanical attempt evidence instead of a mandatory trait
   plus extreme mismatch; explicit attacking/defending roles and reversal/exit paths.
4. Pocket: persistent distance entry/exit driven by pressure, footwork and reach. Measure occupancy
   from exchanges, not distinct context tuples; use range plus pocket as the primary standing denominator.

After each slice test matched-rating entries, both actor orientations, boundary negatives, legal
non-generic next selections, exits, inactivity, horn reset, duplicate names, determinism and finish continuity.
The full target remains fourteen reachable positions, zero position-orphaned moves, ordinary
guillotine/leg-lock use and pocket occupancy at least eight percent.

## Calibration authority

### First candidate result

The first full 3,840-bout trial produced 2,277 finishes, 575 KO and 719 TKO
(59.30%, 14.97%, 18.72%), versus the required 2,319 / 633 / 731. It also missed
the competitive finish lower bound at 47.60%. Therefore it remains disabled by default.
Its five focused tests cover 48 complete matched bouts, both ownership directions,
contested entries, clean exits and horn reset; the 356-bout full-system test passed.
Passing reachability and structural tests does not compensate for failed calibration.

`analysis/evaluate_specialist_entry_candidate.py` enables the private developer switch only
on its audit harness and prints a read-only full-corpus comparison. A nonzero exit means
the candidate is rejected; do not add it to the passing shipping-suite list or overwrite
the frozen reference. Continue developing chains and specialist mechanics together before
considering promotion to normal play.

Five associated identities are drafted in `fight_moves/catalogue/specialist_entry_development.py`
with isolated payload/legality tests. They are deliberately unregistered, so candidate full-bout
snapdowns still use the generic identity until the experimental content is integrated. A neutral
failed-shot stall reset now has explicit trace evidence and factual narration; it is not described
as a referee stand-up or credited to one fighter. Normal traces omit this optional fact entirely.

The post-isolation normal-play rerun passes the full 3,840-fight headline gate with exactly
2,319 / 633 / 731. The immutable 44-fight selection snapshot and 346-move structural snapshot
also pass; the candidate is not being accepted by substituting those normal-play results.
The post-isolation 3,840-bout action baseline also passes, as do fight regression, the
356-bout full-system suite, 256-bout commentary audit, eight candidate/isolation tests and
three draft-authoring tests. No portable executable has been built for this unfinished slice.

### Next joint experiment: legal chain-aware action weighting

The bounded weighting described below is now implemented behind
`_experimental_chain_action_weighting` and tested, but remains disabled in normal play.
The first five-arm trial (300 fights per arm) gives:

| Arm | Chained selections | Completed / attempted roots | Distinct moves / fighter | Positions |
| --- | --- | --- | --- | --- |
| Normal | 17.51% | 1,450 / 5,217 | 16.5683 | 8 |
| Draft content only | 17.51% | 1,450 / 5,217 | 16.5683 | 8 |
| Entries + drafts | 17.17% | 1,460 / 5,200 | 16.7250 | 11 |
| Chain weighting + drafts | 19.34% | 1,495 / 4,969 | 16.2400 | 8 |
| Combined | 19.15% | 1,512 / 4,967 | 16.4083 | 11 |

All arms retain the earlier content gates, but every attempted-chain median is still one.
The combined arm's top-ten share is 25.88% and top-submission share is 19.08%. All five
drafted entry techniques appear when entries are enabled; new preselection states are failed
shot, front headlock and turtle. Content alone leaves the 300 mechanical signatures unchanged.
These are partial improvements, not Phase 31/34 or full-upgrade acceptance.

The first diagnostic artifact is `analysis/joint_candidate_chain_entry_coverage.json`.
Its `observed_draft_ids` field mistakenly includes generic fallback IDs alongside the five
real draft IDs; use the explicit draft catalogue to distinguish them. Preserve this original
artifact and correct the evaluator/filter with regression coverage before the next capture.
The evaluator now filters against explicit draft IDs and records a canonical registry digest
including successor lists and ordered lookups. Regression tests reject generic-ID inflation,
prove graph changes alter that digest, and protect existing output files before costly simulation.

The combined 3,840-fight candidate fails calibration with 2,251 finishes / 570 KO / 728 TKO
(58.62% / 14.84% / 18.96%). Its competitive finish rate is 46.81%, also below the 48% floor.
`analysis/joint_candidate_chain_entry_calibration.json` preserves this rejected experiment;
neither the release reference nor `competitive_finish_conversion()` was changed.

The subsequent 360-move audit-only trial adds nine front-headlock definitions. In its combined
300-fight arm, chaining is 19.17%, attempted roots complete 1,513 / 4,980, distinct moves average
16.4117, and the broad mechanical signature is identical to the preceding 351-move combined arm.
The generic front-headlock ride disappears. Twelve of fourteen drafts appear; high-elbow and
arm-in guillotines remain absent from this combined sample (arm-in appears in the entries-only
arm). Do not treat isolated selector reachability as ordinary-frequency acceptance for these gaps.
`analysis/joint_candidate_front_headlock_coverage.json` preserves the full five-arm evidence and
registry digest. The 360-move candidate has not had a separate full-corpus calibration run.

The latest 377-move trial adds ten turtle and seven failed-shot identities, plus acyclic
guillotine grip-change successors. Its combined 300-fight arm selects 27 of 31 drafts,
including every turtle addition, and no longer emits generic specialist disengage, back-take
or ride identities. Four drafts remain unobserved: corner-turn single-leg re-shot, tripod
head withdrawal, high-elbow guillotine and arm-in guillotine. The last appears in the entries-only
arm. The fixed sample still exposes the same four pre-existing common-action generic IDs.

Chaining is 19.18%, completed roots are 1,518 / 5,002, distinct moves average 16.4633,
top-ten concentration is 26.02%, and top-submission concentration is 19.06%. All earlier
content gates pass; the attempted median remains one and only eleven positions are observed.
See `analysis/joint_candidate_turtle_failed_shot_coverage.json`, whose candidate registry digest
is `2421ea17abe669515762a2297d0f2ce1360abeebdef9c9162ebb31ea86b1bb31`.

The same 377-move candidate's full 3,840-fight calibration yields 2,252 finishes, 567 KO
and 731 TKO (58.65%, 14.77%, 19.04%). TKO matches, but overall finishes, KO and the 46.84%
competitive finish rate fail; the candidate remains disabled. The rejected result is preserved
in `analysis/joint_candidate_turtle_failed_shot_calibration.json` with the same registry digest.
The fresh normal-play smoke, fight regression, 356-bout full-system and both 3,840-bout baseline
checks pass. One display-dependent smoke click-selection probe was skipped. These passing normal
checks establish isolation only, not acceptance of the failed candidate or completion of the upgrade.

Next work must include the missing standing-back/leg-entanglement entry mechanics, persistent
pocket distance and the remaining 23 move definitions. Merely increasing catalogue size has
not delivered the 20-24 distinct-move or median-two targets; assess legitimate selection variety
and continuation opportunities alongside the completed specialist mechanics. Preserve every failed
trial rather than accepting its calibration or dropping unused drafts from the target denominator.

Evaluate a bounded continuation preference immediately before existing weighted action draws.
Emergency survival overrides remain earlier and unchanged. Preview only existing successors
whose parent action is already legal, then apply the same position, role, style, minimum-skill,
counter and deterministic rarity restrictions as named selection. Count an action once even if
multiple successors share it. Preview counters from the current counter window, not the stale
`last_exchange_counter` left by the prior exchange. Target-dependent kicks need probability-weighted
opportunity credit without drawing or forcing a target.

The first implementation uses at most a 1.25 multiplier, conserving integer total weight and action order through
deterministic rounding. Do not add random draws or promise a named successor: actual selection
still follows resolution and applies its own eligibility gates. Keep root expiry, failed-root
denominators and interrupted-chain behavior unchanged. This is experimental, not accepted
calibrated behavior. Pair it with specialist-entry trials and assess variety,
ground/standing occupancy and the locked finish counts before enabling either in normal play.

Additional audit work remains: specialist ground control is absent from the live control-tick
attribution tuple, some existing specialist scoring still references unsupported detailed skills,
and front-headlock rides lack an appropriate named starting-position identity. Resolve these
explicitly rather than letting newly frequent specialist exchanges hide generic or incomplete facts.

These are Class C changes. Existing action and selection signatures may legitimately differ,
but old references must remain immutable evidence. The user's headline lock remains exactly
2,319 finishes, 633 KO and 731 TKO in 3,840 bouts (60.39%, 16.48%, 19.04%).
Do not modify `competitive_finish_conversion`, force results, detect test fixtures or apply quotas.
Use legitimate shared mechanical tuning and compare every slice against the existing references.
Different headline numbers require explicit user acceptance; they cannot be self-approved.
Any new accepted action/selection reference requires a documented Class C migration after the
headline gate passes. See [the full move plan](FIGHT_MOVE_SYSTEM_PLAN.md).

## Submission geometry audit after chain-intent trials

`analysis/joint_candidate_chain_commitment_coverage.json` is the evidence source for this
checkpoint, not a measurement of later pool corrections. Its combined 300-bout arm has 602
generic submission identities: 444 top, 147 bottom and 11 front-headlock attempts. The reported
47.39% top-submission concentration is 444 generic payloads divided by 937 attempts, not one
specific lock dominating. All actual technique facts remain present.

Only two generic events already have a matching compatible action/position identity; their
remaining skill/style eligibility must not be bypassed. Four straightforward content gaps account
for 64 events before eligibility: mount/side-control kimura (31), back-control armbar (12), short
choke from back control (10), and mounted triangle from mount (11). These require position-correct
authoring, not aliases to bottom guard or half-guard moves.

Mechanical geometry takes priority over taxonomy: 145 generic top guard/half-guard leg attempts
need actual knee-line entry semantics, while 59 generic bottom attempts outside guard/half guard
expose position-derived top techniques mixed into bottom pools. Side-control mounted triangles,
mount north-south chokes and setup-dependent Von Flue/scarf-hold attacks cannot be repaired by
calling them another signature. The next pool correction must preserve default-off behaviour,
keep preview and resolution on the same pure pool, and receive a new calibration trial. Adapter
ticket conservation applies to that adapter's input, not to retaining impossible legacy holds.

Review of the role-aware pool identified one unintended omission: top-guard no-gi Ezekiel already
has an exact compatible registry identity, but its base ticket was removed. Restore that ticket
only for top guard, with an eligibility/negative-position regression; do not reopen the old mixed
pool. A separate existing defense defect also remains: non-leg submissions can admit
`leg_lock_rotation` through their shared `stack` family. A high-mastery probe selects a leg-lock
escape against a non-leg hold. Correct attack-family filtering in a separately tested slice so
valid attack geometry does not receive contradictory defensive narration.

## Next setup-dependent mechanics

For top-guard straight-ankle entries, use the existing submission draw and contest in two beats:
first establish the knee line without a finish roll or phantom pass/control credit, then permit
ordinary leg attacks or opposing escapes/counters. Keep half guard excluded until trapped-leg
extraction is actually modeled. The existing guard-only identity must not be broadened by alias.

Von Flue requires new explicit retained-neck-grip evidence: the current generic failed-guillotine
aftermath does not prove the setup. A candidate can resolve a mildly denied plain arm-out guillotine
from bottom half guard into relieved choke pressure with a retained neck wrap, replacing the
contradictory "grips cleared" consequence. Only then may top half guard gain a Von Flue option.
Use stable bout slots, same owners/position/round and the immediately following exchange; any
intervening action, ownership/position change, neutral reset, horn or finish invalidates it.
Previews must remain pure, and the actual draw consumes a single-use opportunity without forcing
the hold or its result. Arm-in/high-elbow variants and generic headlocks are not implicit aliases.
This is proposed mechanics, not implemented evidence or accepted tuning.

The retained-wrap slice is now implemented and regression-tested; ordinary use/calibration remain
pending in the working plan. For the remaining scarf-hold armbar, reuse a contested `ground_control`
action from actual top side control to establish ordinary scarf orientation and near-arm isolation.
Keep the existing control award, add no submission/danger/RNG from setup alone, and use the same
single-next-exchange ownership/position lifetime. A valid setup may expose the exact scarf-hold
armbar; Judo exclusivity must remain intact for its finisher. Post-resolution reverse-scarf/cradle
identities cannot prove or contradict this setup: emit explicit facts and honest generic control
identity until compatible authoring exists, preserving the 400-definition budget. This scarf-hold
slice is now implemented with actual creation/use trace-pair tests and a consecutive-provenance
report gate. It remains experimental; representative use and locked calibration must be measured
separately. The prior Von Flue ordinary sample produced no setups: all nine relevant guillotines
were strongly denied before the mild-denial window. Its next refinement must explicitly distinguish
stopping choke pressure from clearing the neck grip, not simply widen a cutoff to fit those cases.

The next retained-wrap proposal separates three facts inside the existing strong-denial branch:
pressure stopped, grip retained, and top shoulder angle established. Preserve its two top-control
points. A proposed retention contest compares bottom guard work/strength/submission attack with
top submission defense/hand speed/composure, penalized by 0.10 of denial magnitude beyond ten.
A separate angle contest compares top control/positional ability/strength with bottom
control/mobility/guard work. Require positive retention and nonnegative angle before exposing the
existing single-use opportunity; retained grip without angle is not a Von Flue setup. These are
unimplemented design parameters, not calibrated thresholds or proof of ordinary use. Keep all
danger/finish paths ahead of this assessment and reject wrong technique, position or ownership.
This proposal is now implemented experimentally with six focused regression methods, explicit
current-exchange facts and a report gate. The formulas remain uncalibrated: implementation and
boundary tests do not prove ordinary use or accepted finish distribution. Setup-follow-through
reports retain every creation, including opponent interruptions and alternative top choices.

## Remaining specialist skill and control accounting

A current read-only menu/resolver probe finds unsupported `balance` in standing escape and
`front_headlock` in the front-headlock submission chooser/attack plus shared ride/drive attack.
They currently fall back to broad ratings. Experimental corrections should use mobility for
standing escape, positional ability for headlock submission positioning, and split drive/ride
skill bundles by their real action: cage wrestling/clinch control/cage pressure/strength for
force-cage; back control/clinch control/ride control/strength for standing-back ride; top
control/positional ability/ride control/strength for turtle ride. The disengagement menu's broad
fight-IQ term should be explicit rather than requested as a nonexistent detailed skill. Preserve
its rounding and default-off behavior; do not add phantom detailed attributes to satisfy names.

Live control-time attribution also omits front headlock and turtle because it recognizes only
the five ordinary ground positions before falling back to `clinch_controller`. Their actual top
controller should receive earned physical-control time. Do not include leg-entanglement knee-line
ownership automatically: that is not physical top control. Test both orientations, settled
escapes/reversals, one credit per exchange, trace/box-score reconciliation and no neutral/horn
credit. These ticks influence plans and judging as well as display, so this is a separate
experimental mechanical slice requiring fresh calibration, not a presentation-only correction.
This correction is now implemented behind the experimental flag. A five-field credit-point
snapshot (position, top, bottom, clinch controller, credited controller) preserves timing through
referee resets. Actual-resolution regressions and report gates check one award, proper owners,
knee-line exclusion, final control seconds and missing telemetry. Fresh trial results remain the
acceptance authority; implementation alone does not close the full specialist phase.

## Next calibration investigation: striking effectiveness

The specialist-accounting candidate has 45 fewer KO and 38 fewer TKO than the locked overall
counts: together, 83 of its 92 missing finishes. The matched 300-bout coverage arms do not support
a blanket loss of striking actions: normal/combined totals are 3,379/3,415. Power punches rise
600/698, jabs 1,123/1,146 and dirty boxing 637/663; kicks fall 533/473 and ground strikes 486/435.
Back-control plus mount occupancy rises 643/887 despite fewer ground strikes. These are action
and occupancy counts, not measured damage, effectiveness or causal finish attribution.

Next compare matched normal/candidate landed impact, head-kick attempts, knockdowns, stoppage
checks, unanswered-pressure resets and survival recovery by action and position. Preserve actual
defensive responses and fatigue recovery while collecting evidence; do not add blanket damage
bonuses or change competitive conversion to compensate for a headline deficit. The checked-in
historical baseline's subgroup totals are not a current-normal comparator: its older overall
2,290/603/755 differs from the separately locked 2,319/633/731. Run a current paired comparator
before attributing subgroup changes to experimental mechanics.

## Pending retained-wrap positioning

The explicit strong-guillotine retained-wrap/no-angle fact previously disappeared before any
follow-up could act on it. The experimental pending-wrap stage now permits one immediate top
control contest, distinct from both passing position and attempting a choke. It cannot refresh,
and a failed angle contest clears the defender's wrapping arm. Ready Von Flue setup starts only
after successful angle work and retains its original expiry. Generic control selection avoids
false named technique/mastery/chain credit. The angle regression and pure provenance suites
cover real resolution, defender clearance, source tampering, cancellation and absent origins;
fresh ordinary-frequency and calibration evidence must still establish suitability for release.
