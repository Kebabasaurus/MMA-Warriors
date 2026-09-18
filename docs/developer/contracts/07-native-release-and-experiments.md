## Native 440 release integration (6 September 2026)

This section supersedes earlier audit-only/default-off instructions **for the exact
accepted release recipe only**. `main.FightEmpireApp` uses
`fight_release.ReleaseFightEngineMixin`: cradle -> hold-transition -> release profile
-> legacy engine. The immutable `fight_moves/release_registry.py` profile reproduces
the accepted 440 definitions/order/fingerprint, mount successor repair and heel-hook
identity. Rejected tuning trials remain audit-only. Never enter candidate contexts,
AST-rewrite methods or mutate process-global registries during normal play.

`FightEngineMixin` and public historical registry retain the 346 reference profile.
Instance lookups and explicit registry parameters route release selection, chains,
components and labels consistently; static historical callers remain supported.
Persistence/editor/universe validation accept release IDs, and seeding/world use the
host profile. Keep all 94 added IDs save-compatible. Native kick scaling must match
the accepted combined trial's detailed `high_kick_power`/`low_kick_power` reads, not a
new global damage multiplier. Head scaling touches only the two landed base-impact
awards with actual standing head/high evidence. No extra draws/passes are permitted.

The user approved measuring the maximum-eight unused active IDs over **25,000 bouts**,
not 300. Ordinary concentration/content/chains remain at 300; identical defense clauses
remain fewer than ten per rolling 300. Raw reports retain all findings. Use explicit
composed acceptance, never erase the standard-sample absence observations. The full
3,840-bout/39-group calibration remains mandatory. Source-bound native reports and
complete-bout/RNG parity must establish integration; historical reports alone cannot.
`analysis/verify_release_integration.py` runs native bouts outside the candidate scope.
`analysis/evaluate_release_runtime.py` substitutes only disposable audit hosts. Native
hold/cradle flags enable provenance diagnostics without relying on trial-global state.
Run all six `fight_release_*_test.py` integration suites and the canonical full shipping
runner before packaging. Preserve portable Saves/Databases/Logs and launch-check both
artifacts; never shut down on a failed build or failed release check.

Legacy identity fixtures must distinguish neutral cage retention from a strong
standing-back transition and provide live knockdown/damage channels. Retirement
tests patch the host `_fight_move_registry`, not a disconnected world-module alias,
and cover both release and legacy development. Native certification retains raw
300/25,000/3,840 reports byte-for-byte. Its exact reviewed exception list covers only
the two migrated fixtures plus acceptance tests and the standalone certificate
validator; every allowed old/new hash is recorded. Source inventories and every
runtime/simulation/audit-helper hash remain exact, and both immutable calibration
reference hashes are checked. Never broaden this to ignore arbitrary test/helper
changes or reuse evidence after mechanics changes.

Every authored survived template must include both `{actor}` and `{move}`; template
count alone does not establish factual completeness. For causal `single_jab` KO/TKO,
`finish_strike_text` and `finish_sequence` reuse `exchange_display_move(causal_event)`
without changing the canonical ID, target or finish evidence. Keep real commentary
fixtures 9410906 and 9412207 in `fight_jab_wording_test.py`, and run the complete
256-bout commentary gate after wording changes.

Historical selection snapshots predate the default `portrait_version=0` and
`portrait_identity={}` fields and the expanded jab/survival/defense wording. Use the
explicit `--historical-portrait-fixtures --historical-wording` verification options
in `tools/move_selection_parity.py` only with its recognized immutable envelopes.
Reject nondefault portrait fields and unexpected renderer AST structure; retain all
other fixture fields, full trace hashes, checksums and strict comparator behavior.
New captures remain full current records/rendering. Historical scopes restore on
errors; current commentary is independently gated by the live commentary audit.

`analysis/survival_unused_diagnostics.py` scopes the paired repertoire observer to
the retained 440 candidate and records explicit current hold/style evidence. Preserve
single delegation, patch restoration, source hashes and exclusive output. Its
`fight_survival_unused_diagnostics_test.py` regression is part of the shipping suite.
In the verified standard sample, 19 of 27 absent moves have no scored/pool opportunity;
eight were offered but unselected. This is an observed-path diagnosis, not proof of
global impossibility or permission to force selection or waive the unused-ID ceiling.

Defense-clause variants in `commentary_defense_clause` use the recorded defender and
defense without inventing a counter, escape, damage or position change. Keep stable
selection and the fewer-than-ten rolling-300 repetition gate. The shipping runner
includes `fight_defense_wording_test.py` for repeated-fact and full-bout/RNG parity.
`analysis/benchmark_defense_wording.py` reconstructs the old three-clause helper by
removing the thirteen added expressions before formatting; slicing rendered choices
would retain their CPU cost. Require exact recognized AST shape, source/input/RNG
guards and full non-commentary parity. The three alternating 44-bout pairs show no
measured slowdown (2.063s/2.047s medians), not a speed guarantee. The shipping runner
includes `fight_defense_wording_benchmark_test.py` for reconstruction and parity checks.

`analysis/evaluate_joint_fight_candidate.py::reported_failures` collects every arm's
content, chain and measured-target failures before output and exit-status selection.
Retain the original per-arm lists and arm-qualified top-level findings. A successful
process exit on a frequency diagnostic does not establish release acceptance; never
ignore another failure category because measured_final_target_failures is empty.
`fight_candidate_context_regression_test.py` verifies all three arm-only failure paths,
saved/console report agreement and advisory-only success.

Single-jab wording variants belong only in exchange_display_move, using a deterministic
exchange fingerprint and SINGLE_JAB_DISPLAY_VARIANTS. Keep canonical single_jab IDs,
payloads, reads, chains and selections unchanged. Synonyms may describe a straight lead-hand
jab, but must not invent speed, power, feints, steps, stance side, target or landed outcomes.
Other authored jab identities retain their names. fight_jab_wording_test.py compares complete
audits after removing only trace commentary and asserts all terminal RNG streams match;
do not substitute extra move IDs or a presentation RNG draw for equivalent phrasing.

Named composed_survival uses at least50 authored survived templates in
evidence_driven_exchange_pool:25 standing and25 ground. Keep placeholders limited to
recorded facts (actor, defender, move, identity, after and position tail); do not invent
new mechanics or imply a successful escape. Preserve deterministic stable commentary
selection, no simulation RNG and the canonical move ID. fight_survival_commentary_test.py
counts both template pools; Fight Night and engine regressions must accept the contextual
label rather than require literal "single jab"-style wording.

The user explicitly approved 40 additional survival identities: the opt-in
--survival-expansion combined candidate has440 active moves/50 survival moves. This
supersedes the400-count target for that arm only, not normal or older candidates.
fight_moves/catalogue/survival_development.py is audit content, with immutable explicit
SURVIVAL_ROLES. analysis/survival_expansion_candidate.py filters the indexed survive
pool by actual roles and also corrects three legacy top/bottom recovery names. Missing
owners fail closed; knee-line ownership is not physical top. Retain emergency choice,
recovery amounts, skill/repetition scoring, RNG and non-survival options. Do not add
cosmetic clones, force follow-ups or claim new recovery/escape credit. Validate actual
new-ID trace roles in coverage and all full-calibration bouts. Default-off/nested/error
parity, catalogue validation and whole-bout CPU are required; no extra draws does not
prove neutral trajectories or zero cost. See docs/FIGHT_SURVIVAL_EXPANSION.md and run
fight_survival_catalogue_test.py plus fight_survival_expansion_test.py.
Detect survival validation through the scoped harness _survival_expansion_enabled flag,
not a marker on _move_candidates: the composed cradle wrapper hides method attributes.
Require selected-validation totals to reconcile with all40 new IDs; empty diagnostics
must fail if coverage contains a new survival selection. Nested trials inspect the same
class flag so wrappers cannot make an enabled trial appear disabled or stack its filter.
The verified440 candidate records19.03% concentration at300 and19.30% at3,000; all40
additions appear in3,000 with13,247 validated selections/zero invalid roles. All39 full
calibration summaries match the retained head/kick candidate. The3,000 absence list
contains four old specialist IDs; the fixed300 gate still has27 unused IDs. Preserve
this distinction. Paired44-bout CPU medians2.453/2.438 seconds show no measured slowdown,
not a guaranteed speedup. Initial coverage lacked validation activation and is superseded
by survival_expansion_440_verified_300.json, which preserves all five mechanical hashes.

Concentration diagnostics now retain per-move selection counts in joint coverage and
support --retained-damage in analysis/repertoire_selection_diagnostics.py. Count scored
eligibility separately from final-pool offers; neither proves every theoretically legal
action was considered. Capture gas/hurt before choose_action without rerunning emergency
checks; post-resolution named-selection gas is a different fact. Prove full audit and
terminal RNG parity. All ten active survive IDs account for287,295/1,107,314 selections
in the25,000-bout retained candidate, creating a25.9452% fixed-action top-ten lower bound.
No generic_survive was observed. Reweighting those IDs cannot clear25% on unchanged
action paths; changed IDs may still affect later mechanics, so this is not universal
infeasibility. Do not force attacks, pad IDs or waive the concentration gate. See
docs/FIGHT_MOVE_CONCENTRATION_PLAN.md and run fight_repertoire_diagnostics_test.py.

The user-approved --kick-power trial scales resolved kick_power by1.01 immediately
before the existing kick-margin contest. Keep kick type/target shares, kick frequency,
RNG calls, target-specific damage and all non-kick actions unchanged. The audit AST
must find exactly one kick-margin assignment and fail closed if that structure drifts;
the trial is default-off, nested-safe and restores RNG/methods. Run fight_kick_power_test.py
plus fresh full calibration and coverage. Record competitive, timing, mismatch and
coverage outcomes; do not waive other gates merely because the damage candidate was kept.

The user-authorized --standing-head-damage trial scales only landed base impact by1.02
for range/pocket jab, power punch and high kick with an actually resolved head target.
Body punches still use legacy head bookkeeping: never use damage_zone to choose scope.
Keep body/leg, clinch/ground strikes and separate knockdown bonuses unchanged. Fractional
impact preserves the small increase instead of rounding it away; downstream impact-based
knockdown/cut/stoppage checks see the scaled value. No direct probability multiplier or
new RNG draw. The audit helper AST-instruments exactly two existing damage awards and
rejects a changed two-award structure; report source hashes bind the rest of the resolver.
Production source stays untouched, scopes restore
methods/RNG and nested trials never stack. Run fight_standing_head_damage_test.py and
fresh full calibration/coverage; a benefit must not override timing or mismatch failures.
The completed 2% trial records 2,287 finishes/604 KO/734 TKO and 1,382 competitive
finishes (47.99%), but fails the exact 48% floor. The user accepted middle-timing drift as
an advisory for this trial. Keep the change experimental and disabled in normal play;
do not round the rate, raise the multiplier or waive other timing checks. Coverage still has 25 unused
IDs and 25.79% top-ten concentration. Preserve failed-candidate evidence.
The combined2% head-damage +1% kick-power calibration records2,292 finishes,
1,387/2,880 competitive (48.16%) and no full-calibration failures. Keep the kick trial
default-off until coverage passes; its300-bout sample still has25 unused IDs and25.66%
top-ten concentration. Preserve the accepted middle-timing advisory and do not infer
that clearing calibration proves content completeness or fixture-hash parity.

Audit-only --hold-transitions and --cradle-setup require experimental entries and remain
default-off. Top/guard chain identity requires an authored pair of actually dangerous
holds on immediately consecutive same-actor exchanges with unchanged round, position
and owners. Safe defenses, repeated holds, interventions, resets and horns cannot earn
it. Preserve actual technique names and transition evidence, never reroll to fit a chain.
Cradle preparation requires Catch ride intent, the existing contested control margin,
and only the existing three control points. Its next same-top side-control submission
gets one eligible crank ticket after adaptation; retain skill64, style and single-use
expiry on every actual hold draw. Creation/denial/cancellation remains generic with no
signature/mastery/chain credit. Validate both adjacent provenance paths in coverage AND
every bout of full calibration; missing or contradictory evidence is a hard failure.
The standalone helpers patch only disposable audit harnesses; reject disabled nested
scopes and restore patches/RNG on errors. Run the submission-chain/cradle tests, fresh
separate-slice and joint calibration, and whole-bout profiling before considering promotion.

The first completed submission-development trial records76 transitions/57 named chains
in3840 bouts, with all39 group summaries unchanged and competitive47.53% still failing.
Joint300 coverage has24 unused IDs, top-ten25.77%, and3 cradle roots/0uses. The900-bout
frequency run has6 cradle roots/0uses and11 unused IDs. The separate fixed240-bout Catch
cohort has61 cradle roots/0uses: preserve zeros, all hold alternatives, seeds and source
hashes rather than tune for sample use. Canonical fixtures contain no cradle roots and
cannot prove cradle-specific balance. Whole-bout800-move profiling adds2.55% CPU in this
sample; selector-only ratios omit wrappers. No universal neutrality/speed claim is valid.

The audit-only --heel-hook-identity repair reparents only heel_hook to leg_attack
and removes its counter tag; retain its knee-line position, skill 66 and all other
fields. A literal resolved heel hook may use that ID, never an inside/outside variant.
Do not enable the repair by default or rename a knee-line reversal as a submission:
counter_leg_lock still uses positional drafts and has no submission roll. The context
requires entries and restores registries/RNG through nested exceptions. Run
fight_heel_hook_identity_test.py, submission identity and leg authoring suites, then
fresh coverage and full calibration. No weights, extra draws or simulation passes are
part of this correction; isolated eligibility is not proof of sampled coverage.
Reject disabled nested contexts inside an enabled heel repair before copying the active
registry. The 900-bout trial observes three named heel hooks, reducing absences 13 to12;
the standard 300-bout sample stays at25. Full39 calibration groups match the mount base
and still fail competitive48%. Do not present extended reachability as passing the
ordinary unused-ID gate. The reports precede only the non-mechanical nesting guard;
retain their original hashes and this provenance distinction.

The subsequent 6 September user approval makes the unconditional 20–24 distinct-move
mean advisory too. Preserve its raw measurement and per-arm variety_advisories;
do not impose a replacement opportunity threshold. This supersedes older instructions
to retain that hard mean gate, not the aggregate unused-ID ceiling, concentration,
chain-share, balance, provenance or performance gates. Test both mean boundaries and
out-of-range values in fight_candidate_context_regression_test.py. Saved reports remain
immutable historical evidence; policy changes are not new mechanical measurements.

User policy on 6 September accepts attempted-chain median one for now. Keep the metric
and phase_31_advisories/chain_advisories, but remove only this median from Phase 31 and
joint hard gates. Do not remove interrupted roots or relax chain share, variety, unused
IDs, concentration, balance, correctness or performance. Historical reports remain intact.
analysis/repertoire_opportunity_cohorts.py derives cohorts from saved mount observations;
it performs no simulation. Preserve both fighter-bout slots including zero selections,
registry agreement, observed mean reconciliation and input hashes. Final-pool matching
is a fixed-path bound, not universal infeasibility. A move never offered in a final pool
is not proven illegal or unreachable. Do not automatically waive variety targets based
on these cohort results; propose policy separately. Run fight_repertoire_cohorts_test.py.

The audit-only --boxing-chain-pool trial filters only jab/power-punch action demand
against a pure current-state final-pool preview. Original preview still validates live
chains first; final resolution may change eligibility, so this is not guaranteed follow-up.
Preserve authored/counter priorities, score arithmetic, target fingerprints, static/rarity
gates, integer budgets and all alternatives. Initiative, caps and final selection stay
unchanged. Reject incompatible active nested tuning as well as same-call flags. Use
fight_boxing_chain_pool_test.py and fresh full calibration/coverage before promotion.
analysis/benchmark_boxing_chain_pool.py counts boxing_pool cumulatives separately from
select_exchange_move, then sums these disjoint paths; selector-only ratios hide added work.
analysis/chain_selection_diagnostics.py --gift-wrap-mount refreshes the base observer.
Do not use its captured raw preview bonuses as filtered-trial telemetry: its hook observes
the original preview before this action-only filter. The refreshed base has 4,667 roots,
1,522 completions, 961 positive-preview other-action losses and 37 authored-priority losses.
The pool-aware boxing trial records 1,548/4,656 coverage roots, variety16.5333 and chained
share20.62%, but median remains one and unused IDs rise to26. Full3,840/39-group calibration
records2,267 finishes /598 KO /727 TKO and competitive47.33%, worse than the mount base.
Timing passes. Do not promote based only on increased completions; retain both reports,
the mount-refined base, all acceptance failures and default-off status. The actual-bout
test at coverage seed9330000 R1tick18 observes authored Muay Thai priority over one_two
without changing the observed trial's complete audit or terminal RNG.
The boxing_pool_800 benchmark records combined selector/preview share12.27% versus
control10.74%, within15%; selector-only10.41% hides new work. Profiled44-bout CPU rises
9.45 to10.66 seconds with changed trajectories. Do not call this zero simulation cost
or a whole-career speed guarantee. Keep the rejected policy default-off.

analysis/jab_timing_diagnostics.py compares mount versus mount-plus-jab on the exact full
calibration schedule and requires both sets of all canonical groups to reproduce saved
calibration evidence. Keep Early/Middle/Late relative to scheduled rounds, and Nonfinish
separate. Distinguish new/lost finishes from earlier/later finishes; a timing failure is
not proof of delayed stoppages. First named, mechanical and plan differences use actual
exchange facts, retaining unequal trace tails. Preserve input/source/registry hashes and
RNG; output is exclusive. Run fight_jab_timing_diagnostics_test.py. Disabled tactical
plans cannot explain frozen-corpus changes; selected IDs can alter chains and reads.
The completed pair reproduces all 39 groups and finds 25 gained/15 lost finishes, with
five later-period and three earlier-period finishes. Do not call this a general delay.
The original full report has prototype divergence labels: use its timing totals, not
its tail-based plan claims. Corrected --recheck-changed validates unchanged combat
sources, complete parent groups/schedule, and exact fresh audit/RNG hashes for all 75
changed method/round/winner bouts. It is not a new calibration or an account of unchanged
outcome paths. mechanical_projection is explicitly partial and retains triggering values;
tails are lengths, and plans compare only aligned actor/round/tick facts. Root-event
move_sequence.branch_options describes the prior chain, not the new root's successor map.

`--jab-readaptation --gift-wrap-mount` isolates earlier independent-jab repetition scoring
on the mount-refined candidate. Preserve the existing curve/cap, all live continuation
scores and every non-jab score. Enabled nested filters must agree, never stack or silently
inherit a different scope. The broad trial remains separately selectable and mutually
exclusive. Run fight_repertoire_readaptation_regression_test.py and fresh full calibration;
named selection can change downstream mechanics despite adding no RNG draws.
The full mount-plus-jab trial records 2,285 finishes / 605 KO / 719 TKO and competitive
47.92%, but adds a middle-finish timing failure. Coverage variety is only 16.45, with
25 unused active IDs and 1,511/4,666 completed roots. Do not promote it based on the
headline finish gain. The separately reproduced historical selection regression differs
only in all 44 fixture hashes; mechanics/trace/payload/count hashes match. Investigate
fixture provenance without rewriting references or claiming the shipping suite passed.

Current user policy supersedes older fixed300 named-content blocking rules: partition the
four known phase/slice named-move absence messages into content_frequency_advisories. Do not
discard observations or weaken unknown/structural failures, aggregate unused-ID ceilings,
variety, chain, correctness, balance or performance targets. Historical artifacts stay immutable.
analysis/repertoire_selection_diagnostics.py observes actual named selectors on the mount-refined
candidate, retaining every exchange and comparing full audits/terminal RNG against control.
Near unseen alternatives must belong to the final pool, not just the eligible registry; multiple
alternatives for one exchange are overlapping opportunities, not additive recoverable variety.
Run fight_repertoire_diagnostics_test.py for policy and observation regressions.

The mount-refinement scarf investigation found no demonstrated selector bug: coverage bout117
(seed9600002) no longer creates its three scarf setups after R1 tick11 takes a different mount
action. Its side-control occupancy falls13 to2. All other14 scarf observations match exactly,
including positive prepared shares in all eight uninterrupted menus. Do not force the old hold,
extend setup expiry or infer an eligibility regression from missing rare sample coverage.
Keep fixed300 content failures separate from any longer frequency diagnostic. See
docs/FIGHT_SCARF_COVERAGE_INVESTIGATION.md;29 focused setup/prepared-diagnostics tests pass.
analysis/gift_wrap_mount_scarf_frequency_900.json extends the identical combined schedule:
76 scarf roots reconcile to3 context changes,24 interventions,24 other actions,23 other
holds and2 uses. First300 prepared observations exactly match the prior refined report.
Long-run content reachability does not replace the fixed300 sample or any full calibration,
variety or chain gate. Do not present the absence of content failures at900 as release acceptance.

analysis/gift_wrap_mount_candidate.py tests --gift-wrap-mount independently of the broad
--gift-wrap-control trial. It changes only the mount hammerfist edge to high_mount_arm_pinch,
retaining rear_naked_choke/body_triangle_back_control and exactly three declared successors.
Do not silently add a fourth branch or remove ordinary hammerfist legality. Strictly validate
the replacement's mount-only source, complete DAG, context restoration and incompatible flags.
The preceding paired 300-bout trace probe found nine first divergences in back-control named
selection; coverage bout21 lost a R3 submission to a decision under the broad hip replacement.
Bout117 lost scarf coverage after a mount action divergence, not a back-control identity swap.
These are coverage-corpus attribution facts, not explanations of all full-calibration changes.
The completed mount refinement records2,275 finishes /605 KO /725 TKO across3,840 bouts and
39 groups; competitive47.53% is its sole calibration failure (floor48%). Timing passes.
Root completion22/58 and retained nine body triangles improve the local tradeoff, but overall
roots1522/4667, median one, variety16.4183, top-ten25.67% and25 unused IDs still fail coverage;
scarf_hold_straight_armbar remains absent. Keep --gift-wrap-mount as an explicit experimental
continuation point, not a production/default promotion. Do not call a positive local gain
full acceptance or infer all full-corpus outcomes from coverage bout21's recovered submission.

analysis/gift_wrap_control_candidate.py is the single-root --gift-wrap-control trial.
Only gift_wrap_transition's third successor changes from body_triangle_back_control to
hip_pressure_ride; retain strikes/choke branches, three-option limit, immutable IDs and
full-DAG validation. The verified live audit records six undeclared mount-control choices
among 58 attempted roots; these are opportunities, not guaranteed extra completions.
Measure displaced back-control completions and fresh full calibration/coverage before
promotion. Default off; run fight_gift_wrap_control_candidate_test.py for strict drift,
single-definition, nested/error restoration and source-immutability boundaries.
The completed gift-wrap trial is rejected for promotion: root completion improves 17/58 to
26/60, but all-root completion is only 1532/4677, median one, variety16.4367, top-ten25.71%
and 25 IDs unused; scarf_hold_straight_armbar also disappears. Full3,840/39-group calibration
has 2267 finishes /608 KO /725 TKO, competitive47.19% and middle timing failures. Retain
artifacts/default-off status, not the replacement in the default candidate. Bout60 proves
actual mount hip-pressure follow-through; changed root counts are not recovered fixed cases.

analysis/continuation_commitment_candidate.py is opt-in via --continuation-commitment.
It rescales returned positive action bonuses into a probability-bounded demand mixture
(q <= 0.5), only at gas >=42 and below the existing hurt guard. The original apportioner
runs once and prepared intent still combines by max. Initiative remains unscaled; no legal
option, expired root or named identity changes. Reject combining with stronger-continuation.
Require fresh five-arm coverage and complete calibration; the trial is not a shipping fix
until acceptance. Run fight_continuation_commitment_test.py for pure-mixture math, budget,
readiness, nested/error restoration, prepared-only parity and normal full-bout parity.
The first probability-commitment trial is rejected: full 3,840/39-group calibration records
2,269 finishes / 614 KO / 734 TKO, competitive 47.05% and early/middle timing failures.
Coverage chained share 21.88% does not pass median one, variety 16.0717, top-ten 25.98%
or 24 unused IDs. Keep it opt-in; do not treat the policy as the new default candidate.
Von Flue angle provenance must accept proven forward round changes as boundaries even when
the trace has exchanges only. Clear validator pending state, never runtime setups or chain
denominators. Reject stale facts after the boundary and malformed/backward round values.
The natural reproducer is coverage bout177, seed9320004, low-competitive-2, R2 tick18 under
the probability-commitment trial. Its pending wrap correctly expires before R3 tick1.

analysis/chain_selection_diagnostics.py observes actual calls only. Copy chain bonuses before
prepared intent mutates them; ignore initiative previews outside choose_action. Scope static,
rarity and pool observations to actual named selection. Preserve the established round-two root
denominator and retain every interruption. Positive preview probability is conditional on the
observed menu, not guaranteed final eligibility or a counterfactual win. Each bout must match
full control audit and all terminal RNG streams; preserve inputs/registry and reject source drift.
Run fight_chain_selection_diagnostics_test.py when changing these hooks. Keep all tooling outside
production state and never package the candidate on diagnostic success alone.
Apply resolved-hold compatibility only to submission parent actions: other actions carry empty
technique payloads. The authoritative chain_selection_verified_300 report supersedes both live
prototype reports (the resolved prototype misclassified non-submission payloads). Its 196 named
losses include 86 actual hold mismatches, 49 initial-context absences, 36 authored-priority losses,
11 ordinary-pool exclusions, four losing pool draws, five static/rarity rejections and five
remaining post-context absences. Do not call all 196 ranking failures or infer that positive
previews in 968 different-action cases guarantee final named eligibility.

analysis/repertoire_readaptation_candidate.py is an opt-in trial for one earlier repetition
exposure on independent named selections. Retain the base adaptability curve and 14-point cap;
live legal chain candidates keep the original score and sequence bonus. No new eligibility,
counter, signature or action-weight rule is implied. Run --repertoire-readaptation through the
joint evaluator, preserve default control arms and source hashes, and recalibrate the full
corpus: changed selected IDs are not inherently presentation-only. Never pad survival chains.
The completed readaptation trial is not accepted: 2,267 finishes / 611 KO / 715 TKO,
competitive 47.26% and middle timing failures across all 3,840 bouts/39 groups. Coverage
variety 17.1833 is an improvement, not a pass; median one, top-ten 25.53% and 23 unused
active IDs remain failures. Default control arms match specialist_style exactly and trial
normal/content-only/entries arms match that control. Keep the helper opt-in and retain both
coverage reports and full calibration; do not substitute improved variety for release acceptance.

The user has now approved testing stronger continuation above +2, not promotion or relaxed
acceptance. analysis/continuation_strength_candidate.py scales the existing legal action bonus
by 2 (maximum +4), only inside _chain_action_weights. Initiative previews remain unscaled;
prepared readiness combines by maximum after scaling and is not itself doubled. Preserve
skill/gas attenuation, ticket totals, every legal alternative, survival and expiry. Contexts
must not stack and must restore class/instance overrides and RNG on error. Use evaluator
--stronger-continuation; keep default candidate unchanged and retain fresh full calibration,
five-arm coverage, source fingerprints and every failure before considering any promotion.
The first +4 stronger_continuation trial is rejected for promotion: 2,289 finishes / 626 KO /
727 TKO across 3,840 bouts and 39 groups; competitive 47.47% with mid tier 44.48%, middle timing
drift and no sampled doctor stoppages fail calibration. Coverage chain share 21.47% improves,
but median stays one, top-ten worsens to 27.05% and 23 active IDs remain unused. Retain artifacts
and do not call zero sampled doctor stoppages proof of universal impossibility. The default
five-arm control exactly matches specialist_style coverage; the stronger helper stays opt-in.

Use docs/FIGHT_RELEASE_CHECKPOINT.md to distinguish verified regression health from candidate
acceptance. The full shipping run and post-style affected reruns passed; the smoke click-selection
probe was skipped for display layout. The specialist_style_combined_800 selector benchmark passes
at 10.88%, not a whole-career speed guarantee. Keep the audit-only scope of cap approval and candidate
failures visible; automatic goal continuations alone are not approval to change design constraints.

specialist_style_weights reuses ordinary top-style factors for genuine physical-top turtle
and front headlock only. Apply it after survival overrides, before specialist_plan_weights
and chain apportionment. Policy aliases are not new actions; preserve original menu keys/order,
primary/secondary style semantics and default-off parity. It is independent of enabled plans.
Never apply physical-top policy to leg knee-line ownership or expand the continuation cap.
Run fight_specialist_style_regression_test.py and fresh full calibration after changes here.
The specialist_style full candidate retains 3,840 fights/39 groups: 2,272 finishes, 606 KO,
725 TKO; competitive 47.40% still fails. Five-arm coverage preserves normal/content-only/chains
mechanics while entry arms change. Distinct 16.4117, chain share 20.18%, attempted median one,
top-ten 25.65% and 24 unused active IDs are mixed evidence, not complete acceptance.

candidate_context(entries=True) corrects fence_drive to the failed-shot pre-selection position.
force_cage is a controller action from failed shot, not a clinch/cage action; do not confuse
the resolver's cage destination with move eligibility. Preserve the stable ID and all other
fields, default-off registry identity, nested/error restoration and fresh candidate calibration.
The fence_source coverage artifact retains identical mechanics in all five arms, but substitutes
overhook_shoulder_fence_drive for fence_drive in the 23-unused list. Do not report this as a net
variety gain or force named tickets to eliminate the remaining sparse-sample absences.
Fresh fence_source calibration has 2,269 finishes / 604 KO / 724 TKO across 3,840 bouts and
39 groups. Competitive finishes at 47.26% remain its sole calibration failure. The unchanged
300-bout mechanical signatures did not imply full-corpus neutrality: one finish changed.

Candidate final-target reporting must cover the entire active registry: no more than eight
unobserved active IDs in the fixed 300-bout sample and at least 200 active moves with follow-ups.
registered_move_inventory excludes deprecated entries and cannot treat generic/unknown payloads
as registered coverage. Keep draft-only counts separately; two missing drafts do not establish
the total unused-move target. Older artifacts without the full inventory cannot prove that gate.
The complete_inventory five-arm report exactly preserves prior mechanical signatures. It finds
23 unused active IDs (including two drafts), failing the maximum eight, while 363 active moves
with follow-ups pass the 200 floor. Treat this as exposed missing evidence, not mechanical drift.

Candidate sequence creation passes independent_alternatives=True explicitly to the static updater.
Multiple legal successors have no designated next_move_id and are labeled legal-alternatives;
only a sole legal successor is designated. Create/count roots from nonempty legal_branches,
never from the optional designated ID. Selected defense tags do not prove a reaction, especially
when the attack landed. Preserve legacy behavior by default and all expiry/interruption accounting.
Fresh independent-continuation calibration retains 3,840 bouts/39 groups: 2,268 finishes,
604 KO and 724 TKO; competitive finishes 47.22% still fail. Coverage records distinct 16.4833,
chained 20.12%, attempted median 1 and top-ten 25.78%; two leg drafts remain unobserved.
The sparse graph trial is disabled in these measurements. Six provenance regressions cover
real recorder integration, alternative selection, legacy parity and all interrupted-root cases.
The fresh independent_continuations_combined_800_selector_benchmark.json passes at 10.89%
median selector share (three 44-bout samples); it is not a whole-career latency guarantee.

analysis/continuation_branch_candidate.py is an explicit audit-only sparse-root graph trial,
enabled through candidate_context(continuation_branches=True, chains=True) and evaluator
--continuation-branches. It adds alternatives to thirteen roots without replacing prior branches,
changing IDs or increasing the registry count. Preserve ordered immutable definitions, idempotent
nested application, duplicate rejection, full-DAG validation and the three-successor limit.
Default candidate and production graphs remain unchanged. The 84 observed extra action cases
are an optimistic fixed-path opportunity count, not predicted completions or median-two acceptance.
The sparse-branch trial records 2,270 finishes / 604 KO / 720 TKO and competitive 47.19%.
Coverage raises chained selections to 20.77% but lowers variety to 16.395, raises top-ten share
to 26.18% and leaves seven draft IDs unobserved. Keep this tradeoff opt-in, not the default candidate.
The fresh default five-arm control is exactly unchanged from the counter-fallback report.

Prior post-counter-fallback artifacts retain all 3,840 fixtures/39 calibration groups and five
300-bout coverage arms: 2,267 finishes, 604 KO, 723 TKO; competitive finishes 47.19% still fail.
Coverage distinct 16.4483, chained 20.20%, attempted median 1 and top-ten 25.70% retain their failures.
Only entangled_outside_heel_hook and entangled_rolling_kneebar draft IDs are unobserved; actual
controller pools and identity mappings support both. Five leg attacks cannot establish broken
eligibility or justify forced selection. Keep the earlier isolated reports for attribution.
analysis/counter_fallback_combined_800_selector_benchmark.json was collected by running the
existing benchmark inside candidate_context(entries=True, chains=True, draft_content=True),
importing its benchmark module inside that context (400 originals expanded to 800). It passes
the selector-share gate at 11.06%; distinguish this profiled ratio from total career latency.

Dirty-boxing chain lanes must reflect actual target resolution: misses retain head; only the
landed knee weapon changes the target to body. Use the shared cleaned weapon tickets and exact
discrete contest probability, including Erratic outcomes, without consuming RNG. Preserve the
real resolver draw order and final selector independence. Multiple successors in one target lane
are overlapping opportunities, not additive bonuses. Collect fresh full calibration after edits.
The chain experimental flag also resets last_actor/actor_streak before both new-round initiative
calls. Keep the existing within-round comeback branch intact, including its RNG. Test chains-only
and joint contexts plus default-off complete-bout parity with fight_round_streak_reset_test.py.
Do not use clinch-preview measurements as evidence for the subsequent round-streak candidate.
In chain-enabled _move_candidates, keep ordinary style combinations until final static/rarity
eligibility is known. Only _select_from_pool's surviving counter rows establish counter priority;
an empty or rejected counter lane must retain ordinary fallback. Keep default-off filtering and
style ownership gates unchanged. fight_counter_fallback_regression_test.py proves rejected-counter
fallback, valid-counter priority, preview/final agreement and complete-bout legacy parity.
The prepared-diagnostics natural scarf fixture is pinned to coverage bout84/style-coverage-9,
seed9710001, R1 tick15 after counter fallback. Retain nonempty observations and exact audited
trace/result/RNG parity; do not turn a disappeared setup into a vacuous passing assertion.

Bottom-guard entry intent is chosen before the existing sweep contest, candidate-only and with
leg skill >=62. Strictly compare leg/scramble/flexibility against bottom-control/transitions/strength;
ties retain the sweep. Cap the entry contest adjustment at two, with no extra draw. Successful
entry assigns knee-line ownership, never sweep, takedown, submission or physical-top credit.
Half guard is excluded. Keep generic_bottom_leg_entry identity and explicit bottom_leg_entry
trace provenance, cleared next exchange/horn. The coverage observer rejects missing facts and
false credit; run fight_bottom_leg_entry_regression_test.py and fresh full calibration before promotion.
The bottom-guard-entry artifacts retain all 3,840 fights and five coverage arms: 2,255 / 593 / 700,
competitive 46.98%, three coverage entries and eighteen leg exchanges. Eleven draft IDs remain
unobserved; do not call the new route sufficient specialist coverage or package this failing candidate.

`fight_moves/specialist_intent.py` maps physical-top turtle/front-headlock action keys to
existing top-plan policy keys only for lookup. Preserve original menu keys/order, enabled-plan
checks, finite clamped execution, actual ownership and survival precedence. Apply once before
chain apportionment, never as an added action or damage multiplier. Do not alias knee-line or
standing clinch control to physical top. `fight_specialist_plan_regression_test.py` covers both
slots, plan direction, disabled/default parity and the real menu hook. Fingerprint new policy
modules in candidate reports and reject edits during collection.
The frozen fixture schedule does not enable tactical plans. Natural-bout enabled-plan tests
prove that integration; unchanged frozen counts are not evidence of its balance benefit.
The combined near-score repertoire trial records 2,254 / 594 / 701 and passes timing, but
competitive finishes remain 46.91%, distinct variety 16.3367 and attempted median one.
Do not promote the tradeoff or hide the eleven unobserved drafts behind its small variety gain.

`fight_moves/selection_pool.py` is the shared pure ordinary pool builder for the candidate
selector and variety observer. Preserve top-five continuation priority before adding up to
three ordinary near-score choices (6.6 points from the best, maximum eight). Extra low-ranked
successors do not acquire forced chain preference. Authored singleton and eligible-counter
priority stay earlier. Default-off keeps the original five. Earlier fixed-five observer notes
remain applicable to legacy mode; candidate instrumentation must pass expanded mode explicitly.
`fight_repertoire_pool_regression_test.py` covers boundaries, priorities and actual selection.

Experimental repertoire anti-repetition pressure must not weaken as adaptability increases.
Retain the existing repeat threshold and 14-point cap, candidate-only chain switch and exact
legacy default-off formula. The actor's selection penalty is not an opponent defensive bonus.
`fight_move_adaptability_regression_test.py` protects monotonic direction, cap, unrelated
score components and parity. Named choices affect later mechanics; collect fresh complete
calibration and coverage rather than calling this a presentation-only adjustment.
The knee-line correction leaves all five coverage arms and full canonical groups unchanged.
The subsequent adaptability correction records 2,262 / 587 / 712, 47.19% competitive finishes,
16.23 distinct moves and 1,501/4,620 completed roots. It does not solve the remaining gates.
Keep both fresh calibration artifacts and their matching coverage reports; do not cite the
older counter-cadence measurements as evidence for this revised candidate.

Experimental `leg_escape` defence in leg entanglement must use the defending knee-line
owner's leg_locks, positional_ability and discipline with grappling, not generic bottom-game
escape expertise. Gate by actual defending ownership and preserve legacy default-off,
other-action and other-position arithmetic. Keep the existing coefficient total, thresholds
and random draws. `fight_leg_escape_defense_regression_test.py` protects skill direction,
both slots and default parity. Do not claim longer residence without fresh ordinary-fight
coverage and full balance calibration.

