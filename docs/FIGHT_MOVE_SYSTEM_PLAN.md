# Fight Move System Plan — Architecture and Expansion

The user-approved release profile now contains 440 active moves, including 50 survival
techniques. `fight_release.py` integrates the accepted combined recipe natively; the
historical 346-move audit profile and rejected trials remain separate. The maximum-eight
unobserved-ID gate is now measured over 25,000 bouts by explicit user approval. Other
300-bout content/concentration/chain gates and full calibration remain unchanged.
See [release checkpoint](FIGHT_RELEASE_CHECKPOINT.md) for current verification/build status.

## 6 September policy amendment

The user accepts attempted-chain median one for now. Keep reporting this metric, but
treat median below two as advisory in both Phase 31 and joint evaluation. This supersedes
older median requirements below. Subsequent user approval also makes the unconditional
20–24 distinct-move mean advisory, as proposed in [the opportunity review](FIGHT_VARIETY_TARGET_REVIEW.md).
No replacement hard threshold is introduced; unused-ID, concentration and all other
targets remain unchanged. Historical measurement artifacts are retained unchanged.

## Acceptance amendment: close finish rates, not identical counts

The user has approved preserving the old finish-heavy feel without reproducing exact totals.
This supersedes all exact 2,319 / 633 / 731 acceptance requirements later in this document.
Keep those observations and all reference artifacts immutable. Overall finish, KO and TKO
rates may differ by at most **two percentage points** in both historical comparison gates;
accepted-checkpoint limits derive from exact counts rather than rounded displayed rates.
The full 3,840-fight schedule, competitive 48–54% finish band, submission balance, subgroup
and finish-timing protections remain. So do all content, chain, legality and performance gates.
Past failed reports remain accurate records of the policy under which they were collected.
Reassessing saved groups under this policy is not a fresh simulation or automatic promotion.
The saved counter-cadence candidate now passes the headline count/rate checks, but still fails
competitive finishes (47.26% versus 48–54%) and middle finish timing. Its existing variety,
chain and ordinary-use failures also remain. No mechanical change or EXE rebuild accompanies
this policy amendment.

### Specialist retention correction

The experimental leg-escape contest now tests the knee-line owner's leg_locks,
positional_ability, discipline and grappling instead of generic bottom-game skills.
`analysis/joint_candidate_leg_escape_defense_coverage.json` retains all five arms;
every arm is exactly unchanged from the prior coverage checkpoint. The fresh full
`analysis/joint_candidate_leg_escape_defense_calibration.json` likewise retains identical
canonical groups (2,264 finishes / 586 KO / 714 TKO). This corrects skill direction without
establishing increased ordinary leg residence. Competitive finishes and middle timing still
fail the revised balance policy. Four focused tests plus adjacent specialist suites pass.

**Goal: double the catalogue from 200 moves to 400**, with the structure left able to reach 800+
without another rewrite. This document covers the code changes that have to land first, then the
per-action authoring budget that gets to 400.

## Current implementation checkpoint

| Requirement | Current evidence | Status |
| --- | --- | --- |
| 400 active moves | 346 active; all 54 specialist additions drafted, 400 in audit context | Open; promotion requires acceptance |
| About 40 named defenses | 40 registered | Implemented |
| Chained selections at least 15% | 17.51% in 300 fights | Pass |
| Attempted-chain median at least 2 | 1; 1,450/5,217 roots complete | Open; joint chain/specialist development approved |
| Mean distinct moves 20–24 | 16.5683 | Open |
| Top-ten move share at most 25% | 26.26% | Open |
| Top-submission share at most 20% | 19.64% | Pass |
| All 14 positions reachable | Eight observed before selection | Open |
| Locked finish/KO/TKO totals | 2,319 / 633 / 731 in the new 3,840-fight gate | Pass |
| Selector share at most 15% with 800 moves | 13.97% on the latest three-sample rerun | Pass |
| Full shipping suite and both portable EXEs | Passed and rebuilt for the 346-move production checkpoint on 2026-09-04 | Pass for playtest; 400-move candidate remains gated |

This checkpoint does not replace the detailed per-phase acceptance criteria below.

### Latest measured experimental candidate

The current follow-up adds a bounded near-score ordinary repertoire and tactical plan support
for physical-top turtle/front headlock. The latter is covered by enabled-plan natural-bout
tests; the frozen calibration/coverage schedule leaves plans disabled, so it cannot establish
that fix's balance impact. The retained reports are
`analysis/joint_candidate_specialist_top_plans_calibration.json` and
`analysis/joint_candidate_specialist_top_plans_coverage.json`.

The full 3,840-bout result is **2,254 finishes / 594 KO / 701 TKO**. Finish timing now passes;
competitive finishes remain **46.91%**, below 48–54%. Coverage gives **16.3367 distinct moves**,
**19.69% chained selections**, attempted median **one**, and top-ten share **26.67%**.
Eleven draft IDs are unused (high-crotch recollection joins the prior scarcity list).
This is an experimental tradeoff, not release acceptance. Normal play retains the original
five-choice pool and no specialist policy hook effect. Full engine regression, focused pool,
plan and observer tests pass; the 800-move selector benchmark is **14.20%**, under 15%.
No replacement EXE was built.

The preceding repertoire-only reports (`joint_candidate_close_repertoire_*`) contain the
same final results but predate the explicit new-policy module fingerprints. Keep them as
attribution diagnostics, not substitutes for the final source-guarded reports.

### Previous adaptability checkpoint

The latest candidate includes the knee-line defence and adaptability-direction corrections.
Its fresh `analysis/joint_candidate_adaptive_repertoire_calibration.json` records 2,262 finishes,
587 KO and 712 TKO. The matching five-arm coverage report records 16.23 distinct moves,
20.03% chained selections, attempted median one and top-ten concentration 26.72%; the same
ten draft IDs remain unused. Normal, content-only and entries coverage arms are unchanged
by the adaptability correction. These are correctness fixes, not achievement of the remaining
balance/variety/chain targets. The 800-move selector benchmark passes at 13.89% median.
Full engine regression and 32 focused adjacent tests pass. The 400-move candidate is still
not release-ready and no replacement EXE has been built.

### Historical counter-cadence checkpoint

`analysis/joint_candidate_counter_cadence_coverage.json` and its matching calibration artifact
describe the latest completed trial, not release acceptance or a measurement of subsequent edits.

| Measure | Trial result | Required |
| --- | --- | --- |
| Audit catalogue / observed positions | 400 / 14 | 400 / 14 |
| Distinct moves per fighter | 16.22 | 20–24 |
| Chained selections / attempted median | 20.10% / 1 | At least 15% / 2 |
| Top-ten / top-submission concentration | 26.70% / 16.83% | At most 25% / 20% |
| Finish / KO / TKO counts in 3,840 bouts | 2,264 / 586 / 714 | 2,319 / 633 / 731 |
| Setup-dependent ordinary use | Neither scarf armbar nor Von Flue observed | Both required |

The candidate is rejected and disabled in normal play. Specialist skill/control accounting,
retained-wrap shoulder positioning and counter-aware standing cadence are implemented and tested,
but prepared follow-through frequency, chain completion, variety and calibration remain open.
The separate standing-chain ablation below is not represented by this table.

The chain-opportunity report now keeps existing-move recommendations per root, including current
successors, ranked candidate IDs, action-family union coverage and observed contexts. That evidence
supported a candidate-only trial for `one_two`, `mount_transition` and
`half_guard_shoulder_choke`. In 300 fights it moved chained selections from 20.10% to 21.25%, mean
distinct moves from 16.22 to 16.315 and top-ten concentration from 26.70% to 26.21%, but the full
3,840-fight corpus fell to 2,243 finishes / 595 KO / 680 TKO. A one-two-only full ablation also
failed at 2,246 / 579 / 697. Both successor maps were removed, their temporary artifacts were
discarded, and the latest valid candidate remains the checkpoint above. This demonstrates that
action-diverse graph breadth alone does not solve the median-one lifecycle and can displace finish
paths even when it introduces no new random draw.

The next lifecycle diagnostic records completion cohorts from existing root facts. Across the
current 4,615 attempted roots, completion is 32.65%. Three declared successor action families are
the strongest single cohort at 41.00%; gas at least 35 yields about 38%, clinch/pocket roots about
38–40%, and actor streak at least three only 35.05%. Observable conjunctions can exceed 50%, but
the best broadly retained example (`gas >= 35`, at least two successor actions, actor streak at
least two) keeps only 382 of 1,507 completed roots (25.08%). It would fail the independent chained
selection target. Near-hard action commitment plus all-position cadence proves the lifecycle can
produce median two, but raises chained selections above 31% and worsens top-ten/submission
concentration. No tuning or denominator filter from these trials is integrated.

A subsequent representative-frequency probe targeted the otherwise absent
`turtle_short_side_hammerfists`. It appeared twice in the 300-fight candidate, but
`outside_ashi_hip_clamp` then disappeared, leaving nine unused drafts. Full calibration retained
2,264 finishes and 714 TKO but moved KO from 586 to 585. The bonus and temporary artifacts were
removed. Rare-position entry frequency must be solved upstream without cannibalising the locked
finish paths; downstream static-score boosts cannot satisfy the unused-content target.

The paired striking diagnostic now records trace-proven finishing exchanges and bout-level
knockdown/KO-TKO cohorts. Across the full locked schedule, normal play has 1,452 bouts with a
knockdown and 1,364 KO/TKO outcomes; the candidate has 1,384 and 1,300. Of the knockdown bouts,
883 normal and 819 candidate bouts reach KO/TKO, while both arms have exactly 481 KO/TKO bouts
without a knockdown. The 64-outcome KO/TKO deficit therefore tracks 68 fewer bouts creating any
knockdown much more closely than a new failure after the knockdown. Range-to-pocket redistribution
loses 159 combined standing knockdowns, led by 95 fewer kick knockdowns and 28 fewer power-punch
knockdowns at the action level.

A clean pocket-menu ablation tested the candidate's 1.10 power-punch, 0.85 kick and 1.05 clinch
factors without disabling pocket movement or any other candidate system. It increased total
knockdowns from 1,661 to 1,672, but reduced KO from 586 to 574 and total finishes from 2,264 to
2,258. That ablation is rejected; the existing candidate preference remains. Further calibration
must recover high-quality standing knockdown opportunities without assuming that more raw
knockdowns automatically restore the exact finish composition.

Quality attribution shows this is not an exhaustion problem. Candidate high-gas kicks fall by
759 exchanges and 81 knockdowns. High-gas power punches rise by 437 exchanges but still produce
17 fewer knockdowns and 27 fewer finishing exchanges. Style rows show broad displacement rather
than one broken style factor: Kickboxer and Sambo each lose 15 kick finishes, Karate loses nine,
while Boxer loses 13 power-punch and 15 dirty-boxing finishes. A cap-only initiative experiment
was mechanically inert because the underlying continuation value already maxes at two. Scaling
the initiative signal itself to 2.5x then failed the 300-bout screen (decisions 130 to 136, KO
45 to 43, TKO 67 to 63) and was removed without spending a full calibration run. The next trial
must preserve fresh style-appropriate standing offense without globally increasing action weights
or continuation initiative.

Step 1 of the recovery investigation is recorded in
[the standing opportunity audit](FIGHT_STANDING_OPPORTUNITY_AUDIT.md). The follow-up audit-only
round-boundary counter-expiry trial worsens finishes to 2,257 / 586 KO / 708 TKO, with
47.05% competitive finishes. Its five-arm coverage preserves the four unaffected arms but
does not close variety/chain gaps. It is not promoted; the production playtest build stays
unchanged. Its isolated denied-shot
retention comparison and counter-window observer preserve the current candidate as the control.
They are attribution diagnostics, not a replacement candidate or permission to package a failing
revision. The performance rerun remains below the fixed selector ceiling (13.96% at 800 moves).
The full retained-shot ablation improves 2,264 / 586 / 714 to 2,279 / 609 / 724, but still
fails calibration and removes all observed failed-shot residence. All additional KOs come from
mismatches. It is rejected as a gameplay change; the next grounded question is escape intent
after a denial while retaining the specialist state, not a global strike-power increase.
That narrower audit-only Sprawl And Brawl escape preference has now been tested with a conserved
integer ticket budget. It reaches 2,265 / 591 / 714 in the full corpus, while the 300-bout
coverage arm remains exactly unchanged. This is a small experimental gain, not acceptance;
the default combined candidate and production executable remain unchanged.

### Approved development-order change

The user approved developing unfinished Phase 31 chaining and Phase 34 specialist mechanics
together. This supersedes the sequential entry prerequisite below, not any acceptance target.
Integrate specialist entry mechanics in small, separately measured slices before their associated
content. Keep historical evidence immutable and re-run the 3,840-bout calibration after each
mechanical slice. The accepted 2,319 finishes, 633 KO and 731 TKO remain release requirements;
do not change `competitive_finish_conversion()`, force results or recapture failures as acceptance.
The checkpoint measurements above describe the last verified pre-specialist revision, not the
in-progress mechanical candidate. Packaging remains gated on complete integrated verification.

The first entry candidate failed its full-corpus trial: 2,277 finishes / 575 KO / 719 TKO,
versus the locked 2,319 / 633 / 731. It is now explicitly opt-in for developer audits and
disabled in normal play. Five corresponding snapdown/fence-drive definitions are drafted and
tested but unregistered; they do not increase the active count of 346. Continue with the joint
chain/mechanics design and honest candidate comparisons, not a changed acceptance baseline.

The next candidate adds nine front-headlock identities: three guillotines, two turtle breakdowns,
two head-clearance escapes, knee-insertion guard recovery and an elbow-shuck go-behind. These
complete the front-headlock family's ten-addition draft budget (including the earlier clinch
snapdown), alongside four drafted fence drives. The audit-only catalogue has 360 moves; normal
play still has 346. Forty specialist additions remain unauthored. Explicit draft membership and
canonical registry fingerprints now accompany joint trial reports; generic fallback IDs are not
counted as authored additions.

The subsequent candidate added ten turtle moves and seven failed-shot/re-shot moves,
bringing the audit-only catalogue to 377. The remaining 23 additions are eight standing-back
techniques and fifteen leg-entanglement/leg-attack techniques. Turtle and failed-shot drafts
have combined graph, resolver and named-selection tests; ordinary-frequency and calibration
evidence must still precede any production registration. The guillotine drafts now include a
bounded ten-finger → high-elbow → arm-in alternative-grip chain with guard/go-behind exits;
all intermediate actions still resolve independently and may fail or be interrupted.

The standing-back candidate then added moderate skill-sensitive rear-control entries from cage
pummelling and bounded stationary-lock separation, with eight associated draft mat returns,
controls and escapes. That audit-only catalogue had 385 moves; the remaining fifteen definitions
belong to leg entanglement/leg attacks. Normal play still uses the prior calibrated entry rules.
Review exposed automatic-separation credit leaking into recovery, plan/judging evidence and
contextual praise; do not accept the initial standing-back trial as the corrected implementation.
That leak is fixed with regressions for both fighter orientations and both reset reasons. Actual
control work remains credited, but neutral resets cannot award extra recovery, tactical/judging
effectiveness, contextual praise or chain completion, and invalidate both pending chains.
The six focused suites pass 48 tests, and the 44-fight semantic and 346-move registry snapshots
remain exact. Corrected five-arm coverage is recorded in
`analysis/joint_candidate_standing_back_credit_fix_coverage.json`: the combined arm observes
12 positions, 18.68% chained selections and 16.755 distinct moves per fighter. Median attempted
chain length remains 1 (1,530 completions / 5,096 roots); top-ten share is 26.40% and top-submission
share 20.48%. Pocket and leg entanglement remain absent. These are development failures, not
accepted replacements for the targets. The corrected full calibration in
`analysis/joint_candidate_standing_back_credit_fix_calibration.json` fails: 2,244 finishes,
572 KO and 708 TKO (58.44% / 14.90% / 18.44%), with competitive finishes at 46.60%.
The corresponding normal-play 3,840-fight result verification remains exact at 2,319 / 633 / 731.
The earlier artifacts remain historical; the candidate is not release-ready.

Leg-entry investigation found 145 bottom submissions, 35 mechanically selected leg techniques
and only one dangerous non-finishing leg attempt in the 300-fight combined candidate. Relaxing
the existing post-finish-roll retention gate alone therefore cannot establish broad leg-game
coverage. Preserve mechanical technique selection and knee-line ownership when developing this
slice; a partial sweep into entanglement must not receive completed-sweep/top-control credit.

The next experimental slice now implements skill-sensitive knee-line retention after the existing
dangerous, non-finishing bottom leg-submission branch. It requires leg skill at least 65 and a
nonnegative retention edge plus one quarter of the existing danger-adjusted margin; no new roll
or finish conversion is introduced. The original default-off predicate is unchanged. All fifteen
leg definitions are drafted and integrated into the scoped audit context: five attacks, three
controls, three escapes, two positional counter-lock reversals and two disengagements. This reaches
400 audit definitions, not 400 production moves. Seven focused suites pass 49 tests.
The `analysis/joint_candidate_leg_retention_coverage.json` trial observes thirteen positions,
but only three leg-entanglement exchanges in 300 combined bouts. Thirteen of the fifteen new
leg definitions remain unobserved. Mean distinct moves is 16.76, chained selections 18.65%,
median attempted chain length 1 and top-ten share 26.39%; pocket is absent. Full calibration in
`analysis/joint_candidate_leg_retention_calibration.json` fails at 2,248 finishes / 572 KO / 709 TKO
(58.54% / 14.90% / 18.46%), with competitive finishes 46.70%. These reports predate the
submission-identity correction described below and cannot verify that correction.
Independent review found and fixed a further experimental identity defect: named submission
selection could disagree with the mechanically attempted lock and receive false signature/mastery
credit. All four submission action families now filter by explicit resolved-technique compatibility
before signature exclusions. The mapping covers 48 mechanical labels, with compatible identities
for 29 labels; unsupported or unknown techniques use an uncredited generic identity. The existing
leg authoring test now distinguishes isolated eligibility from actual resolved identity. Six new
regressions cover real resolver-to-trace-to-finish-summary credit, stale preview isolation and
unsupported delivery fallback; these and fourteen adjacent/context tests pass. Default 44-fight
semantics remain exact. `joint_candidate_submission_identity_coverage.json` reveals the genuine
remaining taxonomy gap: 16.2833 distinct moves, 16.71% chaining, 29.25% top-ten share and 65.73%
top-submission concentration (generic fallback dominates). Nine Phase 29 and five Slice 6 moves
are absent. Thirteen positions remain observed. Mechanical pools must actually support authored
deliveries before this can pass; do not weaken identity compatibility to recover false coverage.
Full calibration in `joint_candidate_submission_identity_calibration.json` fails at
2,242 finishes / 567 KO / 712 TKO (58.39% / 14.77% / 18.54%); competitive finishes are 46.49%.
The corresponding normal-suite rerun subsequently passed. No mechanical draw
or technique pool was changed to match a narrated name or inflate ordinary reachability.
Pocket diagnostics now include entries, occupied-beat residence histograms and exit reasons,
including zero-beat entries before a horn or finish. Twenty-six coverage/context tests pass;
the histogram reconciles with actual pocket pre-selection occupancy. The next experimental slice
implements persistent pocket entry from an already contested landed punch, defender pivots,
range-favouring jab exits and a neutral three-idle-beat disengagement. Pocket weights modestly
favour power punches and close ties over kicks. Six focused tests pass including real bouts,
damage/gas/RNG parity for the same resolved action, proper distance attribution and protected
knockdowns/finishes. `joint_candidate_pocket_distance_coverage.json` now observes all fourteen
positions in 300 combined bouts. Pocket occupies 1,612 / 4,754 standing exchanges (33.91%), with
653 entries and mean residence 2.4686 pre-selection beats. No exit is unexplained. Leg entanglement
still contributes only three exchanges. Distinct moves remain 16.2017, chaining 16.56%, attempted
median 1, top-ten share 29.12% and top-submission concentration 66.17%; these still fail final
variety targets. Full pocket calibration fails at 2,235 finishes / 584 KO / 700 TKO
(58.20% / 15.21% / 18.23%), with competitive finishes 46.15%. New submission-identity context reporting
separates compatible names, generic fallbacks and contradictory claims; 27 reporting/context
tests pass, including the permanent incompatible-identity rejection gate.

The next experimental slice adds a pre-draw submission adapter with 21 legal authored variants
and thirteen exact-name compatibility additions. Only repeated weighted tickets are substituted;
pool length, per-index choke/leg flags and each original technique's first occurrence are preserved.
Position, ownership, skill and exclusive-style eligibility are checked before the existing draw.
Von Flue, cradle/scarf-hold setups, broad chain identities and positional counter-lock aliases
remain excluded pending genuine mechanics. Seven focused suites pass 56 tests, including all
position/action/slot ticket conservation and real pre-draw finish identity. Its ordinary trial
(`joint_candidate_submission_pool_coverage.json`) records 1,150 submission identities: 592 generic,
none incompatible and none missing technique facts. Only Von Flue and scarf-hold armbar remain
absent from the earlier content slices. Distinct moves are 16.4833, chaining 16.55%, top-ten share
27.85% and top-submission concentration 46.27%. Full calibration still fails at 2,242 / 585 / 704
finishes / KO / TKO (58.39% / 15.23% / 18.33%); competitive finishes are 46.39%.

The current chain audit counts 4,947 attempted roots and 1,389 completions (28.08%); 2,176 roots
have a next action that does not complete the declared successor and 899 expire after two ticks.
The next experimental slice replaces the flat 25% opportunity bonus with bounded action-specific
skill, adaptability and discipline intent attenuated by gas (maximum 2 bonus before apportionment).
Existing eligibility, named selection, survival overrides, two-tick expiry and interrupted-root
accounting are unchanged. Twenty-eight focused/context tests pass; new complete-bout evidence is
required before claiming any chain improvement. Normal-play smoke, fight regression, full-system
and both frozen 3,840-bout result/action gates passed the preceding run.
Independent review confirms the weighting invariants but identifies a remaining preview weakness:
statically legal submission successors can still be preferred when their exact mechanical technique
is unavailable (notably setup-dependent Von Flue). A pure pre-draw technique-pool preview should
exclude those impossible continuations without consulting stale previous-exchange evidence.

The completed intent trial (`joint_candidate_chain_commitment_coverage.json`) improves chained
selections from 16.55% to 19.15%, but attempted-root completion remains 1,473 / 4,529 (32.52%)
and median length remains one. Mean distinct moves falls to 16.0933; top-ten share is 28.21%
and top-submission share 47.39%. Thirteen positions are observed, with no leg-entanglement
exchange in this sample. All 1,150 submission attempts retain technique facts and no incompatible
named claims, but 602 use generic identities. Full calibration in
`joint_candidate_chain_commitment_calibration.json` still fails: 2,263 finishes / 577 KO / 687 TKO
(58.93% / 15.03% / 17.89%), with competitive finishes 47.22%. Higher chaining alone does not
establish improved overall variety or acceptance; this candidate remains disabled in normal play.

The subsequent preview correction extracts a pure shared mechanical ticket pool. Joint experimental
chain intent now uses compatible ticket probability after current eligibility and signature gates;
overlapping branches count once and impossible setup-dependent holds contribute nothing.
The resolver retains its existing single technique draw. Three new regressions cover pool purity,
stale evidence, unavailable holds and union weighting; these do not establish final calibration.
Read-only taxonomy review attributes the preceding 47.39% concentration to 444 generic top
submissions out of 937, not dominance by one actual lock. Only two of all 602 generic events have
an already-compatible action/position identity, still subject to skill/style gates. Next content
opportunities are position-correct top kimuras, back-control armbars, short chokes and mounted
triangles. Top leg-entry and bottom-role pool validity need separate mechanical investigation;
do not repair them by broadening name aliases or fabricating setup evidence.

The completed preview coverage (`joint_candidate_submission_preview_coverage.json`) records
19.45% chained selections, 1,495 / 4,647 completed roots, median one, 16.2733 distinct moves,
28.27% top-ten share and 48.77% top-submission share. Thirteen positions are observed and 558
submission attempts use generic identities. The pure-preview correction improves correctness,
but still does not establish the required variety, chain median or specialist frequency.
Its full calibration (`joint_candidate_submission_preview_calibration.json`) fails at 2,228
finishes / 567 KO / 700 TKO (58.02% / 14.77% / 18.23%), with competitive finishes 46.18%.
This precedes the role-aware pool correction and must not be cited as verification of it.

The next candidate separates submission base pools by actual top/bottom ownership and position.
Bottom mount/back retain only wrist isolation; bottom side permits kimura/wrist and a skill-gated
buggy choke; half guard excludes full-guard attacks. Top guard/half exclude bottom-only attacks
and diving leg locks until real entry mechanics exist. Mount, side and back pools no longer mix
mounted/north-south, gi-dependent or unproved setup labels. The variant adapter still preserves
each input pool's length, first occurrences and per-ticket family, but the base distributions
intentionally differ from the previous candidate. No finish formula changed. New calibration is
required. Inherited top-position danger bonuses on bottom attempts and bottom action frequency
remain explicit follow-up work; pool correctness is not final balance acceptance.
Integrated verification passes 53 focused regressions and exact 44-fight normal semantic parity.
The new five-arm coverage and full calibration runs are pending. A controlled resolver probe
confirms the next ownership bug in both slots: skills 55, margin zero and an actual bottom wrist
lock cause no finish draw/danger in guard, but underneath mount/back/side cause a finish draw,
14 danger and ten defender gas loss. Dominant-position and guard-work bonuses need actor-role
checks; retain neutral baseline terms and do not remove legal bottom actions in that narrow fix.

The role-pool coverage trial (`joint_candidate_role_pool_coverage.json`) observes all fourteen
positions, 20.10% chaining and 15.96% top-submission concentration. Generic identities fall to
247 / 1,024 submission attempts, with no incompatible identities. Mean distinct moves is 16.22,
top-ten share 26.10%, and median attempted length remains one (1,515 / 4,682 roots complete).
Von Flue, scarf-hold armbar, top-guard ankle lock and top-guard Ezekiel remain absent; truthful
setup/entry support is still required rather than reopening invalid pools. These are pre-bonus-fix
measurements, not final acceptance.
The completed calibration (`joint_candidate_role_pool_calibration.json`) fails at 2,235 finishes,
580 KO and 696 TKO (58.20% / 15.10% / 18.12%); competitive finishes are 46.42%. The improved
submission coverage therefore does not authorize release or replacement of the locked references.

The subsequent ownership correction gates dominant-position danger, mount/back skill benefits and
finish multipliers on actual top ownership. Bottom guard-work benefits require actual bottom guard
or half guard. Neutral, legitimate top and guard terms remain unchanged, as does default-off play.
The top-guard Ezekiel ticket removed unintentionally by the previous pool cleanup is restored only
in its correct context, with existing named skill requirements. New position-bonus tests are
registered in the canonical runner; this candidate requires fresh coverage and calibration.
Sixty integrated focused tests pass, and the 44-fight normal semantic reference remains exact.
A read-only mutation restoring the old ownership predicates fails the new negative regression.
New `joint_candidate_submission_ownership_*` coverage/calibration runs are pending. The normal
canonical run has passed smoke, fight regression and the exact 3,840-fight result gate at
2,319 / 633 / 731; action-baseline/full-system checks are still running. These default-off checks
prove isolation, not acceptance of the experimental candidate.

The preceding normal canonical run subsequently completed: smoke, fight regression, full-system,
and both frozen 3,840-fight result/action gates pass (one display-dependent smoke probe skipped).
Ownership coverage (`joint_candidate_submission_ownership_coverage.json`) records all fourteen
positions, 20.07% chaining, 16.12% top-submission share, 16.2933 distinct moves and 26.42% top-ten
share. Attempted median remains one (1,527 / 4,687 completed roots). There are 250 generic
identities among 1,023 submissions and no incompatible named claims. Restored top-guard Ezekiel
now appears; Von Flue, top-guard ankle lock and scarf-hold armbar still need genuine setup/entry
support. This report predates the submission-defense compatibility gate.
The ownership calibration (`joint_candidate_submission_ownership_calibration.json`) fails at
2,230 finishes / 583 KO / 694 TKO (58.07% / 15.18% / 18.07%), with competitive finishes 46.28%.

The next correction passes explicit current hold evidence into experimental defense selection.
Confirmed non-leg submissions exclude leg-lock-only defenses even when shared `stack` families,
authored metadata or mastery would prefer one. Genuine leg attempts retain knee-line defenses,
including generic move identities; positional counter-lock/scramble actions are not recast as
submission attempts. A new permanent candidate report count rejects incompatible defense tags.
Missing technique facts remain a separate gate. These presentation corrections do not alter
normal-play selection or mechanics RNG and require integrated verification before acceptance.
The defense regression includes 24 paired complete bouts with all candidate mechanics enabled in
both arms and only the defense filter changed: mechanical audit evidence remains exact while
defense identities genuinely differ. The default 44-fight semantic reference also remains exact.
Seventy-two integrated focused tests pass. The new `joint_candidate_submission_defense_*`
coverage/calibration runs are pending; coverage now records and rejects leg-only defenses against
confirmed non-leg attempts. Further development must model top-to-knee-line entry and the absent
setup-dependent submissions, alongside variety/chain work, rather than reopen invalid role pools.
Completed defense coverage (`joint_candidate_submission_defense_coverage.json`) records zero
contradictory leg-only defenses in the combined arm versus 114 in the unchanged normal arm.
Combined variety, chains and submission concentration remain exactly 16.2933 / 20.07% / 16.12%,
consistent with the paired mechanics proof. This is a presentation correctness pass, not full
move-plan acceptance.
The full defense calibration (`joint_candidate_submission_defense_calibration.json`) is unchanged
at 2,230 finishes / 583 KO / 694 TKO (58.07% / 15.18% / 18.07%), competitive finishes 46.28%.
It still fails the locked acceptance totals; unchanged mechanics is not sufficient for release.

The next experimental slice adds one straight-ankle ticket from actual top guard when leg skill
exceeds 62. The existing raw contest plus 0.2 times attacker entry-skill versus defender retention
edge must exceed eight to establish the knee line. Neither entry success nor denial rolls a
same-beat finish or awards pass/takedown/sweep/control/danger credit; one actual attempt is counted.
Subsequent leg attack/escape/counter menus remain unchanged. Structured entry facts clear on the
next exchange/horn, preserve preselection guard identity and render the actual settled position.
Half guard remains excluded. Coverage counts validated entries/denials and rejects inconsistent
position/ownership evidence. This is new uncalibrated mechanics, not an accepted frequency target.
Seventy-one focused integration tests pass, including real trace-to-report entry classification,
and the default 44-bout semantic reference remains exact. New `joint_candidate_top_leg_entry_*`
coverage/calibration and normal canonical fight-suite reruns are pending. The next setup-dependent
slice is explicit retained-guillotine evidence for Von Flue, as designed in the specialist audit;
half-guard position or a stale previous submission name alone must never enable that hold.
The top-entry coverage (`joint_candidate_top_leg_entry_coverage.json`) observes one validated
entry and four denials in 300 combined bouts, with ten leg-entanglement exchanges and all fourteen
positions. Top-guard ankle lock now appears. Distinct moves remain 16.2483, chaining 20.23%,
top-ten share 26.32% and top-submission share 16.20%; attempted median still fails. Von Flue and
scarf-hold armbar are the remaining absent earlier-slice identities. Entry frequency is still
low; reachability alone does not finish this development work.
The completed calibration (`joint_candidate_top_leg_entry_calibration.json`) fails at 2,227 finishes,
585 KO and 693 TKO (57.99% / 15.23% / 18.05%); competitive finishes are 46.11%. This remains
experimental and does not replace the accepted finish distribution.

The next experimental slice explicitly resolves retained plain-guillotine neck wraps from bottom
half guard after a mildly denied adjusted contest (-10 through zero), only when top defensive
control matches or exceeds bottom retention. No finish/danger branch is reinterpreted. The top
fighter gains one Von Flue ticket only on the next exchange with identical owners, position and
round; all other actions, transitions, horns and finishes invalidate it. Real technique selection
consumes it, without forcing the hold. Created/used facts replace contradictory grip-cleared prose,
and candidate coverage rejects attempts lacking immediate setup provenance. Ninety-one integrated
focused tests pass, including actual trace-pair validation in both orientations. New ordinary
coverage and locked calibration are required before any acceptance claim.
The default 44-bout semantic reference remains exact. New `joint_candidate_von_flue_setup_*`
coverage/calibration runs are pending; the ongoing normal canonical rerun has passed smoke and
fight regression so far (display-dependent click probe skipped). Scarf-hold arm isolation remains
unimplemented: it needs an explicit contested ground-control setup, not reverse-scarf narrative
credit or side-control position alone.
The completed Von Flue coverage (`joint_candidate_von_flue_setup_coverage.json`) records no setup
creation or use in 300 combined bouts, despite nine actual bottom-half-guard plain guillotine
attempts. Other headline metrics remain unchanged from the top-entry trial. Targeted lifecycle
tests establish legality, not representative frequency; investigate the actual exclusion stages
before changing universal setup conditions. Von Flue ordinary-use acceptance remains open.
The 3,840-fight Von Flue calibration (`joint_candidate_von_flue_setup_calibration.json`) remains
2,227 / 585 / 693 finishes / KO / TKO, still rejected. A read-only 300-bout probe reproduces all
nine relevant guillotines: every adjusted margin is below -10 and returns top-control consolidation;
none reaches the setup window. Five independently pass the defensive-control comparison. The
nearest margin (-10.229) fails that comparison too. Probe engine hash:
`9f8f4dd3dd5f85c4da6dcbeefd5ec8b0ca4d8788d2d4a851fb8b757444345185`.
The legitimate next refinement is explicit neck-grip retention after pressure is stopped, not a
slightly widened margin cutoff or retroactive reinterpretation of every strong denial.

The scarf-hold setup slice is now implemented behind the existing experimental flag. A contested
top-side-control action can isolate the near arm while retaining its ordinary three control points;
only the immediately following top submission has one scarf-hold straight-armbar ticket. Other
actions, owner/position changes, horns and finishes clear it. Creation is generic rather than falsely
claiming a reverse-scarf signature, mastery or completed chain. Actual armbar identity retains its
Judo/minimum-skill restrictions. The report rejects nonconsecutive or contradictory setup evidence.
One hundred integrated focused tests pass, including real setup/use traces in both orientations.
The normal canonical rerun completed smoke, fight regression, frozen result/action checks and the
356-bout full-system suite successfully (display-dependent click probe skipped). The default
44-bout selection reference also remains exact. Fresh `joint_candidate_scarf_hold_setup_*`
coverage and calibration are in progress; this does not establish ordinary-use or release acceptance.
The completed initial scarf sample records 115 creations and two actual uses with no invalid
provenance in 300 combined bouts. It reaches 400 definitions and all 14 positions, but distinct
variety is 16.1167, chaining 19.74%, attempted median one, top-ten share 25.95% and top-submission
share 15.85%. Von Flue and near-side cradle are absent. The corresponding 3,840-bout calibration
records 2,231 finishes, 584 KO and 689 TKO (58.10%, 15.21%, 17.94%); competitive finishes are
46.22%. This candidate is rejected, not promoted or packaged.

Independent review then reproduced a same-exchange referee-stand-up defect outside that sample:
the engine reached range but retained the new scarf setup and narrated ground framing. A failing
regression now passes after explicit cancellation cleanup and referee-first rendering. Cancelled
facts retain generic identity, cannot seed a later armbar, and require settled range/no owners in
the report. Referee timing and control awards remain unchanged. All 104 focused tests and the exact
44-bout default selection check pass. Fresh `joint_candidate_scarf_standup_fix_*` diagnostics are
required for this corrected revision; the prior artifacts remain immutable pre-fix evidence.
Those corrected diagnostics have completed: all five 300-bout arms retain their earlier mechanical
signatures, and the full calibration is still 2,231 / 584 / 689 with the same failures. No candidate
has been promoted. The absence of near-side cradle is a setup-intent defect: all successful
side-control holds currently try to establish scarf orientation. Separate arm-isolation intent
from ordinary ride/pin intent before the contest, using existing skills, bounded style familiarity
and enabled fight plans. Do not force a cradle, infer setup from a post-selected name or change the
400-definition budget. Explicit strong-guillotine grip/shoulder contests remain a later slice.
Control intent is now implemented: arm-isolation ability averages submission attack, throws and
positional ability; ride/pin ability averages ride control, top control and strength. Judo/Sambo
familiarity adds four toward isolation, wrestling familiarity four toward riding, without stacking
styles or imposing exclusivity. Enabled submission/conservation plans contribute four times bounded
execution to their relevant lane. Ties retain ordinary control. Only chosen isolation evaluates the
existing contest; it cannot force an armbar or a named control. One hundred eight integrated tests
and the exact 44-bout default reference pass. Fresh `joint_candidate_control_intent_*` diagnostics
and the normal canonical suites are running. Calibration reports now retain all canonical groups;
the frozen reference, full corpus and both failure comparisons are unchanged.
The control-intent sample restores near-side cradle appearance but leaves both setup-dependent
submissions absent: 14 scarf creations produce no armbar use, and Von Flue remains absent. Combined
variety is 16.2517, chaining 20.12%, top-ten share 26.27% and top-submission share 16.26%; attempted
median remains one. The completed calibration records 2,226 finishes, 587 KO and 695 TKO and is
rejected. Do not solve weak follow-through by making every control action a scarf setup again.
Measure actual next-exchange interruption, action choice and technique choice separately before
tuning legitimate prepared-attack preference. Strong-guillotine grip/angle assessment is the next
implemented slice under test; it does not change the mild-denial window or the locked acceptance.
The strong-denial assessment is now implemented after existing dangerous/finish checks, preserving
the two top-control points. Retention compares bottom grip-related skills against top grip-clearing
skills with a 0.10 severity penalty beyond a ten-point denial; a separate top-versus-bottom positional
contest establishes shoulder angle. Only positive retention plus nonnegative angle creates a
single-use opportunity. Three factual aftermaths distinguish cleared grip, retained wrap without
angle and a potential counter-choke setup. This adds no RNG or immediate attack/danger/finish.
Explicit trace facts and finite-score/ownership/provenance gates accompany six new regression
methods. All 116 integrated focused tests pass, as does exact 44-bout default parity. Fresh
`joint_candidate_guillotine_grip_*` audits are running; ordinary frequency and calibration remain
unproven. The normal canonical run has passed smoke (display click probe skipped) and is continuing.
Setup follow-through diagnostics now count every creation, including failed/aborted opportunities,
so future tactical work can distinguish action selection from technique selection and interruption.
The completed grip sample reports five cleared grips and four retained wraps without a shoulder
angle; none creates a Von Flue opportunity. Its 14 scarf roots end in five opponent interventions,
eight other top actions and one different submission. The full calibration remains 2,226 / 587 /
695 and rejected. These results justify measuring bounded prepared-action/technique preference,
not forcing an armbar or weakening the grip/angle predicates. A retained wrap without angle may
need a later explicitly contested positioning beat; it is not already a counter-choke setup.
Prepared follow-through is now implemented experimentally. A pure current-context eligibility
preview checks the actual setup and compatible move gates. Readiness combines submission attack,
adaptability and discipline with gas and enabled-plan execution. Its bounded action bonus combines
with existing chain intent by maximum before one integer apportionment. The prepared hold may
receive at most four extra duplicate same-family tickets after variant adaptation, preserving pool
length, per-index choke/leg flags and every other technique's first occurrence. Survival, remaining
actions, actual draw, ownership, expiry and finish resolution remain authoritative. All 125 focused
tests pass, including non-stacking and real setup-to-attempt trace evidence. The normal canonical
run has completed both 3,840-fight gates and the 356-bout full-system suite successfully; smoke's
display-only click probe was skipped. A fresh prepared-preference trial is required before making
an ordinary-use or calibration claim. Compare its unaffected normal/content-only/chain-only arms
with the preceding grip trial to detect accidental chain-refactor drift.
The prepared-preference audits have completed: normal, content-only and chain-only mechanical
hashes are identical to the preceding trial. Combined scarf evidence contains 12 creations and
one correctly cancelled setup; follow-through is three opponent interventions, seven other top
actions and two other submissions, with no armbar use. Both setup-dependent submissions remain
absent. The complete calibration is 2,227 / 588 / 693 and rejected. Preserve this evidence; stronger
preference cannot be accepted merely because it raises a targeted probe's chance of selection.
The specialist skill/control correction is now implemented experimentally. Unsupported detailed
skill names were replaced by position-appropriate supported skills; disengagement reads broad
fight IQ explicitly without changing legacy rounding. Front headlock/turtle now receive earned
physical-control time, while knee-line ownership remains excluded. The existing credit point
records its actual position/owners before a possible referee reset; trace gates reject wrong,
duplicate or missing awards. Real three-round tests reconcile control seconds, ownership changes,
escapes, neutral resets, horns and pre-referee control. Fresh ordinary coverage and calibration
must measure this revision; it is not a presentation-only change because control informs tactics
and judging. Normal-play behavior remains behind the unchanged default-off boundary.
The corrected coverage has completed: all 13,011 combined-arm exchanges have valid control-award
evidence, with zero missing or invalid awards. All 132 integrated focused tests and the exact
44-bout normal-play snapshot pass. Ordinary content still misses Von Flue and scarf armbar;
12 scarf creations end in three opponent interventions, seven other actions and two other holds.
The fresh 3,840-bout candidate calibration remains rejected at 2,227 finishes, 588 KO and 693 TKO,
with competitive finishes at 46.08%. These results are recorded in the specialist-accounting
artifacts named above; they do not replace the locked references or authorize packaging.
An instrumented replay of the same 300 bouts confirms prepared preference is active: three roots
are interrupted by the opponent, one by emergency survival, six by another ordinary action and
two reach a submission draw. Those two pools give the prepared armbar 4/17 and 3/17 tickets;
missing it twice has probability 62.98%. Zero observed use is not evidence of broken wiring.
Before further mechanical tuning, add conditional action probabilities, prepared-ticket shares
and expected-use totals to permanent follow-through diagnostics, then measure a larger fixed
corpus. Preserve survival, real opponent reactions and the bounded two-stage selection.
Permanent prepared-opportunity instrumentation is now implemented in the audit harness, with
per-bout reset, actual returned action-ticket probabilities, pre-choice technique shares and
conditional expected-use totals. Opponent interventions and emergency survival keep unknown
probabilities rather than fabricated zero-probability menus. Incomplete/ambiguous observations
are rejected separately from frequency targets. Six diagnostics regressions include 48 ordinary
paired bouts and a positively exercised real setup scenario with exact trace/result/four-stream
RNG parity; the integrated focused run passes 57 tests. The normal 3,840-bout result gate again
passes exact 2,319/633/731. Fresh five-arm `joint_candidate_prepared_diagnostics_coverage.json`
and 3,000-bout combined-only `joint_candidate_prepared_diagnostics_extended.json` runs are in
progress. No mechanical preference, finish threshold or acceptance reference changed.
The five-arm diagnostic run is complete: every arm's mechanical hash is identical to the
specialist-accounting trial. Combined observations reproduce 12 scarf opportunities, eight
ordinary menus, three opponent interventions and one emergency survival; two submission draws
produce zero scarf armbars, against 0.8258 conditional expected uses. No incomplete/ambiguous
menus or missing draws were found. The normal canonical run has now completed smoke, fight
regression, both 3,840-bout result/action gates and the 356-bout full-system suite successfully;
smoke's display-only click probe remains skipped. The larger frequency sample is still running.
The 3,000-bout sample is complete: 131,701 exchanges, all 14 positions, 16.4402 distinct moves,
20.18% chained selections, attempted median one, top-ten share 26.15% and top-submission share
18.07%. Scarf observations reconcile to 238 live opportunities: 146 ordinary menus, 79 opponent
interventions and 13 emergency-survival choices. There are 78 submission choices and 17 actual
scarf armbars, versus 16.3695 conditional expected uses. No stronger preference is justified by
the earlier zero in the smaller sample. Von Flue has only two setups, one opponent intervention
and one different submission: no use, versus 0.0369 conditional expected uses. Geometry/entry
frequency, not selection wiring, remains its main investigation target.

The first extended artifact also exposed an audit-scope bug: defense-clause totals accumulated
across all 3,000 bouts while Phase 33 specifies per 300 fights. The corrected report retains
whole-run totals but gates the peak in every rolling 300-bout window, without weakening the
ten-use threshold or hiding boundary-spanning repetitions. Diagnostic/root reconciliation now
rejects entire missing observation sets as well as ambiguous menus/missing draws. Forty-six
focused tests pass, including a naturally occurring fixed-seed setup with full trace/result/RNG
parity. A corrected extended artifact is required for the revised repetition classification;
the prior artifact remains historical evidence, not a changed acceptance reference.
The corrected extended audit is complete in
`analysis/joint_candidate_prepared_diagnostics_validated_extended.json`. Its mechanical hash is
unchanged. The worst rolling 300-bout defense repetition is nine, versus a whole-run aggregate
of 29; the specified repetition gate passes. Von Flue absence, distinct-move variety, attempted
chain median and top-ten concentration remain failures. The new paired striking tool is ready
for a settled candidate revision; no balance conclusion is claimed before its measured run.
The next experimental slice now preserves a pending neck wrap only after the actual strongly
denied plain guillotine retains grip without an angle. Only the immediately following same-top
control action can contest shoulder position using its existing margin plus 0.2 of the relevant
positional skill difference, with the existing isolation threshold above eight. It consumes the
pending wrap on either outcome: success creates the ordinary one-next-exchange ready setup,
failure explicitly clears the wrapping arm. Positioning adds no RNG/submission/damage/danger
and retains only the existing three control points. Intervening actions/actors, position changes,
horns, resets and finishes invalidate the pending stage; it cannot refresh itself or ready expiry.

Explicit angle facts and source/origin identity are validated across real three-beat traces,
including same-exchange referee cancellation and generic control identity. Both submission beats
use their actual mechanical pool/draw in regression. The integrated focused run passes 160 tests,
and default 44-bout parity remains exact. Five-arm coverage, full candidate calibration and matched
current-normal striking evidence are now running as `joint_candidate_von_flue_angle_*` and
`current_normal_vs_candidate_angle_striking.json`; normal canonical suites are also running.
These are new mechanical trials, not acceptance of the earlier 3,000-bout candidate or permission
to package. The locked finish counts and all remaining variety/chain/content gates are unchanged.
The angle coverage run is complete: its combined 300 bouts contain three real pending-wrap
origins, two cancellations and one successful angle beat creating a ready setup, with no invalid
provenance. No Von Flue attempt follows in that sample; content/variety/chain acceptance remains
open. The paired 300-bout striking report records more candidate damage (18,454 versus 17,298),
knockdowns (130 versus 121), KO (48 versus 41) and TKO (67 versus 55). This is the opposite of
the locked-corpus deficit, so do not treat the coverage sample as a causal balance diagnosis.
Extend paired evidence to the exact full calibration fixture schedule and canonical rating groups
before changing strike balance. Current full candidate calibration is still running.
The angle candidate's full calibration has now completed at 2,227 finishes, 588 KO and 693 TKO,
still rejected and unchanged at headline level from the prior candidate. The paired diagnostic's
full-corpus mode is implemented and passes seven tests, including exact 3,840-fixture/group matching
against the baseline builder and source-change rejection. The current paired run is
`analysis/current_normal_vs_candidate_angle_striking_calibration.json`, using all 3,840 fixtures
per side; the normal canonical suite continues separately. Do not tune against the opposite
direction seen in the 300-bout coverage sample or promote the failed candidate.

The full paired run has completed. Current normal matches all locked counts (2,319 finishes,
633 KO, 731 TKO); the combined angle candidate has 2,227, 588 and 693 respectively. Recorded
total damage is similar (224,096 normal versus 224,468 candidate), while head damage rises
178,860 to 183,857 and knockdowns fall 1,830 to 1,686. Kick exchanges fall 6,056 to 4,895;
ground strikes rise 5,418 to 5,808. These are observed distributions, not proof of causality.
Competitive low-tier damage falls 43,465 to 41,961; mid/high damage rises, yet decisions rise
in all three tiers. Investigate action mix and damage timing rather than a blanket damage boost.
Normal canonical smoke, fight regression, 3,840-bout result and action verification, and 356-bout
full-system checks all pass. The display-only Matchmaking click-selection probe was skipped.
The permanent chain diagnostic now separates undeclared survival, other undeclared next actions
and declared actions without named completion, using recorded branches and retaining unknown
evidence explicitly. All 12 chain-diagnostic and seven paired-striking tests pass. A bounded
44-spec combined probe retains 706 attempted roots and 208 completions: 80 survival interruptions,
176 other undeclared actions, 23 declared-action non-completions, 141 expiries, 59 round boundaries,
13 fight endings and six ownership changes. This is diagnostic, not a replacement 300-bout gate.
The next attribution trial is the paired tool's `--standing-chain-ablation` mode. Both arms retain
the complete candidate; only the second bypasses range/pocket action-weight redistribution. It
does not remove named combinations, pocket movement, specialist positions or ground/clinch intent.
Nine diagnostic, 15 candidate-context and 13 chain-weighting tests pass. A full 3,840-fixture-per-arm
run is collecting `analysis/standing_chain_ablation_angle_calibration.json`; no runtime engine
change or candidate promotion has been made from this experiment.

That full ablation has completed. Bypassing standing chain weights raises kicks from 4,895 to
5,373 and knockdowns from 1,686 to 1,716, but reduces KO from 588 to 573 and TKO from 693 to 685.
Total finishes rise slightly from 2,227 to 2,240 through other methods, still below 2,319. Removing
standing weighting is therefore not an accepted correction: keep the ordinary weighting and test
cadence separately. The control arm reproduces the preceding candidate, not the normal baseline.

Pending that result, a separate cadence hypothesis is ready for a bounded experiment: a live,
eligible range/pocket continuation may contribute at most two initiative points, using existing
action-specific chain readiness and gas attenuation. It must add no roll, leave the existing
actor-streak/comeback path intact, and give no bonus to exhausted/hurt fighters or against an
opponent-owned counter window. Existing target, style, skill, rarity, role and two-tick expiry
checks still apply. This is not implemented or accepted; initiative alone cannot fix the observed
256 timely undeclared actions in the 44-spec probe. Any experiment needs disabled parity,
threshold/counter/expiry/purity tests and fresh full calibration, without removing failed roots.
The cadence slice is now implemented under the existing experimental chain flag. The existing
initiative expression and single roll are preserved when disabled; candidate-only addition uses
the shared legal preview and keeps comeback handling untouched. All 60 focused tests pass,
including gas 22/60, hurt threshold, opponent counters, stale prior-counter flags, actual registry
skill/style/rarity, both fighter slots and no extra RNG. The default 44-bout snapshot remains exact.
Fresh five-arm coverage and full candidate calibration are running as
`analysis/joint_candidate_standing_cadence_coverage.json` and
`analysis/joint_candidate_standing_cadence_calibration.json`; normal canonical suites run separately.
Earlier candidate/ablation measurements do not prove this new slice passes any acceptance gate.
The cadence five-arm coverage is complete. Combined results are 16.1817 distinct moves, 19.99%
chained selections, 1,505/4,637 completed roots (median one), 26.74% top-ten share and 16.55%
top-submission share. Von Flue and scarf armbar remain absent. This does not improve the previous
1,519/4,663 completion fraction, and variety/concentration regress slightly in this fixed sample.
Do not accept cadence merely because its local invariants pass; retain the failed measurements
and await full calibration before deciding whether this mechanical experiment merits retention.
Review also found a cadence-preview legality defect: an actor-owned counter window can make
`one_two` unavailable because eligible counter moves take precedence, yet the shared preview
still awards its initiative bonus. An actor-counter regression must reject that false opportunity
without rejecting ordinary continuations in lanes lacking eligible counter alternatives. This
candidate is not acceptable while that defect remains; full runs already in flight retain their
original source revision and must not be cited as proof for a later correction.
Cadence full calibration completed at 2,266 finishes, 596 KO and 707 TKO (59.01% finish,
47.29% competitive finish). This improves headline counts from the pre-cadence trial but still
fails the locked 2,319/633/731 totals and competitive minimum. The actor-counter regression
reproduces +1.8 false cadence for `one_two` while the actual selector requires `slip_cross`;
the ordinary jab lane remains valid. Correction and a deterministic equal-initiative fixture
are now required before fresh candidate verification. Normal calibration is still running.
The counter-preview defect is corrected: non-submission lanes mirror eligible-counter priority
after static, signature and rarity gates, retaining ordinary choices when no counter survives.
The equal-initiative fixture now proves equal baseline inputs before testing both outcomes.
Three repeated initiative-suite runs pass; the integrated six-suite run passes 62 tests and the
normal 44-bout snapshot remains exact. Fresh five-arm coverage and full calibration are running
as `analysis/joint_candidate_counter_cadence_coverage.json` and
`analysis/joint_candidate_counter_cadence_calibration.json`. Neither the older 2,266-finish run
nor its failed coverage can establish acceptance for this corrected revision.
Corrected counter-cadence coverage is complete: 16.22 distinct moves, 20.10% chained selections,
1,507/4,615 completed roots (median one), 26.70% top-ten share and 16.83% top-submission share.
The counter legality fix passes its regressions but does not close the variety, median or
concentration targets; Von Flue and scarf armbar remain absent in the combined 300 bouts.
Full corrected calibration remains in flight. Next variety diagnosis should measure the distinct
IDs available in actual legal selection pools before adding another sampler preference; a
fixed-trajectory pool bound is diagnostic only, since selected IDs affect subsequent mechanics.
The corrected full calibration has completed at 2,264 finishes, 586 KO and 714 TKO (58.96%
overall, 47.26% competitive finishes), still rejected. Normal result verification again retains
2,319/633/731 exactly; its action/full-system checks continue. A read-only 44-spec pool probe
includes all 88 fighter slots, six with zero selections: 1,901 selections, 16.1591 actual mean
distinct and a maximum matching bound of 18.2159 within the observed final pools. Three paired
bouts preserve entire audits, traces and all four RNG streams. This identifies insufficient
fixed-pool headroom in that cohort, not universal impossibility or permission to lower the target.
The normal canonical run has now finished: smoke, fight regression, 3,840-bout result and action
verification, and the 356-bout full-system check all pass. The display-only Matchmaking probe was
skipped. Experimental counter-cadence remains rejected despite these normal-play compatibility passes.
The permanent variety diagnostic and seven focused tests are integrated; the combined diagnostic
verification passes 28 tests. `analysis/counter_cadence_variety_opportunities_300.json` covers
all 600 fighter slots (31 with zero selections), reproduces 16.22 actual distinct moves, and
finds a fixed-final-pool maximum of 18.3267. There are 13,093 selections, 4,143 singleton pools,
2,632 chain-prioritized calls and 475 unwrapped actual-ID singletons. Source/registry/input/trace
fingerprints and input/pool reconciliation bind the evidence. This strengthens the case for
structural legal-opportunity/branch work rather than another ordinary sampling-weight tweak;
it does not lower the 20–24 target or prove that changed fight trajectories cannot meet it.
A proposed tuple-index reaction slice was rejected and reverted before acceptance. Audit showed
selected defenses were often breached on landed, knockdown and takedown outcomes, while existing
follow-up tuples have no universal primary/evasion/block metadata. Moreover, the next independently
selected action already completed a nonpreferred legal branch in most observed prototype
continuations. The invalid diagnostic artifact was removed; default 44-bout parity and 26 focused
chain/sequence tests pass after reversion. Future branch work must author broader legal action
lanes or explicit reaction provenance rather than relabel tuple positions.
Variety work must also account for selected IDs feeding chains and move-read-driven adaptation.
The existing selector already penalizes repeated use. A future bounded debut preference inside
the ordinary strongest-five pool would need its own mechanical calibration; it is not merely
wording variation, and must preserve authored priority and continuation preference.

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

Implementation evidence: Step 0 now has `tools/move_registry_parity.py`, the historical
`analysis/move_registry_parity.json` captured from `4a73923`, and six negative/coverage regressions
in `fight_move_parity_regression_test.py`. Steps 1–2 now have the package split, closed vocabularies,
permanent legacy IDs and immutable index. Both structural stages passed the complete result corpus;
the integrated smoke, fight regression, 256-fight commentary, 3,840-fight action and 356-fight
full-system gates also passed. Steps 6–7 now have evidence-scoped coverage checks, the initial
300-fight allow-list, five authoring helpers and `docs/FIGHT_MOVE_SCHEMA.md`; their final corpus
verification passed. Phase 29 now adds 16 top submissions (216 total moves; 25 top submissions).
The 300-fight sample selects every addition, with eight legal guard and nine half-guard techniques
and a largest top-submission share of 19.74%. Phase 29 passed full result/action, commentary,
fight regression, full-system and smoke verification (one display-dependent click probe skipped).
The original 200-move snapshot stays immutable; `analysis/move_registry_phase29.json` captures the
expanded registry separately, and `--verify-legacy` protects all original fields and ordering.
Phase 30/33 is now integrated with 33 additional moves and 22 defenses (249/40 total). All 33
appear in the 300-fight sample; every ground recovery pool meets four and every referenced defense
family has two definitions. Identical rendered defense clauses peak at seven uses after adding
deterministic factual variants. Body-block and shoulder-roll eligibility is explicitly constrained.
`analysis/move_registry_phase30_33.json` is the new separate structural reference. Paired bottom
variety comparison passed: 1.5667 to 1.685 distinct bottom moves per fighter, with identical
mechanical evidence across all 300 paired fights. Full regression, both 3,840-fight calibration
gates, 356-fight full-system and smoke gates passed before the final weapon-eligibility correction
below (the display-dependent smoke click probe was skipped). The first fight-suite runs exposed
stale test assumptions: a blank incoming
attack for restricted defenses and an exact 18-defense assertion. Both now reflect the 40-defense
specification, with positive and negative eligibility tests; no runtime restriction was relaxed.
Final diff review also found that broad `power_punch` includes knees and elbows. Punch-only
defenses now reject explicit kick/knee/elbow tags; the new negative regression covers this boundary.
The corrected Phase 30/33 revision passed smoke, fight regression, both 3,840-fight baseline gates,
356-fight full-system, 300-fight coverage, 256-fight commentary and six focused bottom/defense
regressions. These phases are signed off. Running the new weapon
regression with the previous eligibility rule fails all six tested weapon/action combinations.
Slice 5's 53 definitions are now registered after their draft checks: ten power
punches, six jabs, ten kicks, eight inside strikes, seven entries, seven controls and five exits.
Eleven domain tests pass. The paired 300-fight probe selects all 53 additions, preserves every
mechanical signature and raises mean distinct moves per fighter from 15.8733 to 16.28. Top-ten
share falls from 26.31% to 25.97%; chain share rises from 2.25% to 2.88%, still far below Phase 31's
target. See `analysis/striking_move_expansion_comparison.json` for reproducible evidence.
The coverage report now exposes the plan's total selections, per-fighter distinct moves, top-ten
concentration and chained-selection metrics; unit tests lock their denominators. Active content
reached 302 moves / 40 defenses in Slice 5. `analysis/move_registry_slice5.json` is an immutable content
snapshot, with every preceding definition unchanged and all new IDs permanently protected.
Slice 5's gate history and the final contextual-commentary correction are recorded below.
Integrated parity, authoring and 300-fight coverage gates passed. The first commentary run exposed
one false Iron Chin call crediting a referee stand-up as a fighter response. Trait/camp generators
now reject referee resets before consuming their call allowance; a positive/negative regression
passes, and the 256-fight commentary rerun has zero failures. Slice 5's full fight regression,
both 3,840-fight baselines and full-system gates passed; smoke passed with the display click probe
skipped. An additional smoke pass is running after the final referee-context correction.
Slice 6 now registers 44 definitions: six shots, seven takedowns, eight advances,
seven controls, eight ground striking chains and eight bottom submissions. Individual 300-fight
probes select every addition in each domain. Shot/takedown follow-ups explicitly accommodate the
resolver's guard/half-guard landing, while ground-strike component tests cover 10–26 attempts
without counting posture or control as a strike. Combined 300-fight paired verification selects
all 44, preserves mechanical evidence and raises mean distinct moves from 16.28 to 16.5167;
chain share is 3.14%. The active total is 346 moves / 40 defenses, captured separately in
`analysis/move_registry_slice6.json`. All 18 styles now exceed the 18-move floor (minimum 22)
and retain an exclusive combination and finisher; a permanent test enforces Phase 32's content
floor. Slice 6's integrated parity, all domain/registration tests, 300-fight coverage and 256-fight
commentary gates pass. The full fight regression, both 3,840-fight result/action baselines and
356-fight full-system suite also passed: Slice 6 is signed off with exact locked counts. The extra
post-referee-fix smoke run passed on the 302-move revision with the display click probe skipped;
the fresh 346-move smoke run also passed, with the same display-only probe skipped.
Step 5's graph component is now implemented in `fight_moves/chains.py`: immutable ordered
adjacency, import-time cycle/dangling-ID rejection, iterative depth calculation and six positive/
negative tests, including 2,000 nodes without recursive traversal. Actual trace depth and occurrence
identity are now integrated separately from potential graph depth.

Phase 31 investigation: 195/346 definitions have follow-ups, but only 49/200 original moves do.
The same 300 fights yield 3,504 live continuation opportunities, only 660 matching the prematurely
committed next move, versus 895 matching any authored branch. Just 418 continuations are selected
(3.14%). Author compatible legacy successors, resolve alternative branches against the actual next
action, reject wrong top/bottom ownership, and count successful same-position ownership changes
without rewriting calibrated outcomes. Legacy wiring was drafted separately before integration.
Historical definition-field changes require an explicit reviewed parity migration; never
silently waive follow-up differences or replace the original snapshot.
Phase 31 now wires 163/200 original moves through 125 explicit successor-only updates;
the combined 346-node graph remains acyclic. Runtime selection now accepts alternatives matching
the actual next action and gives a continuation priority only within the strongest five normally
eligible moves, retaining authored-signature and counter protection. Pre-exchange ownership is
passed explicitly because selection occurs after resolution. Six regression cases cover branch,
role, expiry/horn, target/style/skill and observed occurrence-depth behavior; a seventh covers
specialist top/bottom restrictions. The initial 300-fight trial reached 12.58% chained selections
but failed the top-submission concentration gate (35.30%). Eight generic successors were replaced
with legal named positional submissions. The revised trial reaches 12.03% chained selections,
20.39% top-submission concentration and passes all earlier content gates.
Trace depth counts selected nodes, with a unique actor/root-round/root-tick occurrence identity;
reports expose both attempted and completed-chain lengths in fights reaching round two. This
distinction prevents a graph's potential depth from masquerading as observed sequence evidence.
The registered map has a checksum-bound successor-only manifest and exact snapshot:
`analysis/move_followup_phase31_revised_manifest.json` and `analysis/move_registry_phase31_revised.json`.
Original Phase 31 trial artifacts remain immutable but are not release acceptance evidence.
The attempted-chain median is still one; completed-chain median two alone cannot prove acceptance.
`--require-phase31` now explicitly rejects this gap. Phase 31 remains unfinished.
The 300-fight root-loss audit finds 5,721 attempted roots in bouts reaching round two, with
1,097 completing. Missing next-action branches account for 2,949 failures, two-tick expiry 997,
round/fight endings 479 and ownership changes 99; ranking/authored priority accounts for only 47.
Stronger ranking bonuses therefore cannot solve the median requirement. An in-memory bounded
defensive-continuity plus jab/control-branch trial improved chain share to 13.13% and completed
roots to 1,200, without mechanical drift, but still had median one. It is not integrated;
broader action-diverse authored successors remain under investigation.
The registered `fight_moves/followup_diversity.py` now authors 30 reviewed roots with three
different next-action lanes each. Four tests validate bounded/acyclic successors and real outcome
positions, including standing clinch entries settling into clinch/cage. The plain 300-fight trial
reaches 15.53% chained selections, 1,323/5,338 completed roots and 20.39% top-submission share,
with identical paired mechanics and all prior content gates passing. Attempted median remains one.
The integrated 300-fight paired rerun confirms 12.03% to 15.53% chained selections, 16.555 to
16.57 distinct moves per fighter and identical mechanics. No defensive-pause retention behavior
is integrated. The successor-only manifest binds the immutable schema-2 source; exact current
content is `analysis/move_registry_followup_diversity.json` (SHA-256
`8a071f8bd31994c8a431f41f2dd9517a09c143ea454b3b6b97d4352fe3796bbe`).
Sixty-two focused authoring/registry/parity tests pass. The integrated fight regression, 300-fight
coverage, 256-fight commentary, exact 3,840-fight headline and action gates, and the 356-fight
full-system suite pass. The new 44-bout semantic snapshot is
`analysis/move_selection_followup_diversity.json` (SHA-256
`b5631121357f44f747f6216d67014594d24fac38699f2e4917ba8c682a2c24bc`).
It follows the reviewed content migration, not a refactor recapture. The selection test also
reconstructs frozen schema-2 content and verifies the original pre-refactor 44-bout evidence.
All 13 selection tests and the new exact snapshot check pass. The latest integrated smoke rerun
passes (one display-dependent matchmaking click probe skipped). The fixed 800-move benchmark
passes at 13.97% median selector share, retaining the unchanged 15% ceiling.

Next sequencing work must add real graph edges, not relabel unrelated actions as continuations.
An effective unrelated attack currently ends the old root and starts another; retaining its old
occurrence ID would falsely improve the median. A possible bounded defensive-pause design would
retain an immutable root deadline and opportunity budget without incrementing depth or extending
expiry. Even the earlier pause trial completed only 27.29% of attempted roots; it is not a proven
solution. Prioritize further action-diverse, acyclic authored branches while preserving the
three-successor limit, all eligibility gates and the unchanged attempted-root denominator.
The reproducible `analysis/generate_chain_opportunity_report.py` now reconciles the integrated
300-fight sample's 5,338 roots/1,323 completions. It finds 969 two-tick expiries, 378 round-boundary
losses, 91 bout endings, 43 role changes and 2,534 timely next actions not completed as declared
successors. Optimistically choosing the three most frequent next-action families for each root
would cover 2,855/5,338 (53.48%), before enforcing skill, style, targets, position or DAG legality.
That bound applies only to this observed cohort; it does not prove the final target impossible.
Five regression tests protect failed-root counting, terminal completions, expiry/ownership and
the three-action bound. The role check mirrors the runtime's empty-role wildcard; a standing root
is not automatically excluded when a later selection is on the ground. Phase 34 entry implementation
was originally gated on Phase 31 acceptance; the approved development-order change above now
permits joint implementation while retaining both phases' acceptance requirements.

The next 30-root continuity layer is now integrated after a separate in-memory trial. It changes
only successor lists for existing moves: no deleted roots, added mechanics or survival-step padding.
The main paired 300-fight rerun confirms chaining 15.53% to 17.51%, completed attempted roots
1,323/5,338 to 1,450/5,217 (27.79%), and top-submission concentration 20.39% to 19.64%.
Distinct moves per fighter are 16.5683 (previous 16.57); top-ten concentration is 26.26% (previous
26.14%), so the final variety/dominance targets still need work. Attempted median remains one.
Seventy-seven focused authoring/parity tests pass. All historical snapshots remain unchanged;
`analysis/move_followup_continuity_manifest.json` binds the preceding diversity snapshot to
`analysis/move_registry_followup_continuity.json` (SHA-256
`16776c4d0ed38a2f1a7d11de11bf98e9472f738e18331805ecd78b5b0277fc44`).
Fresh integrated fight regression, coverage, commentary and locked 3,840-fight finish gates pass.
Smoke and performance checks pass (one display-only smoke probe skipped; selector median 13.97%).
The fresh 3,840-fight action and 356-fight full-system gates also pass. The successor-aware semantic reference
is `analysis/move_selection_followup_continuity.json` (SHA-256
`d15acf267482cef7d44139784a66838349f5ebb7715f961de6ffce36857800fa`); it follows the explicit content
migration, and neither earlier semantic snapshot was overwritten.

The next chain feasibility pass adds an exact best-three-existing-techniques union diagnostic.
On the current 5,217-root cohort, the action-family optimistic ceiling is 2,772 (53.13%); requiring
actual technique IDs with legal root/next positions, roles and targets lowers it to 2,718 (52.10%).
Skills, style, rarity, ranking and DAG constraints are still omitted; this remains a conditional
optimistic bound, not proof that all other catalogues are impossible. Six focused diagnostic tests
cover overlap/dominance handling and the existing denominator/role contracts. A decision has been
requested about moving the remaining chain-length work into the mechanical phase while retaining
the original finish lock. No phase order or mechanical action selection has been changed yet.
The bounded 20-edge defensive trial is retained but unregistered. It appends real named defenses
without deleting existing successors and passes four authoring tests. In 300 paired fights,
chaining rises only 17.51% to 17.77%, with 1,484/5,217 completed roots (28.45%); median remains one.
Fifteen added edges appear in 34 selections. Top-ten share is 26.22%, top-submission share remains
19.64%, and all paired mechanics/earlier content gates match. Named recovery nodes have outgoing
graph edges, but ordinary `survive` control outcomes do not continue the live chain. Real
defense-to-counter continuation requires an explicit lifecycle design, not a fabricated control tag.
The revised map passes focused parity/sequence/coverage tests and the 300-fight content gate.
Its fresh fight-engine regression, 256-fight commentary gate, both 3,840-fight baselines and
356-bout full-system rerun pass. Exact results
remain 2,319 finishes, 633 KO and 731 TKO. The preceding revision also passed smoke, both full
baselines and the 356-bout full-system suite; the smoke display-only click probe was skipped.

Steps 3/4 investigation found selector cost of 28.24% in a diagnostic 30-fight/800-move profile.
The repeatable `tools/benchmark_move_selector.py` (44 fights, three repeats, 800 moves) confirms
27.99% median selector share, above the unchanged 15% target, with identical mechanics across
repeats and successful registry/RNG restoration checks. Static caching alone is insufficient: hoist per-exchange context,
preserve exact floating-point addition and reason order, and keep candidate-relative signature
finisher suppression dynamic. Bout-local caches must restore outer state on exceptions/nesting.
Before refactoring, `analysis/move_selection_phase31.json` freezes 44 complete bouts/1,786 selected
payloads (SHA-256 `988689fc6615e8369868ae6644cae299681e52073074c88fd65c4d7873eded7f`).
Seven regression tests protect full payload fields, trace order, checksums, RNG/exception purity
and read-only verification. The canonical runner verifies this evidence as well as registry parity.
Step 3's six-helper extraction is implemented: the orchestrator is approximately 65 lines,
all 44-bout payload hashes remain exact and the focused graph/follow-up/sequence tests pass.
Step 4 is implemented with bout-only static-score caching and exchange-local context hoisting.
The lifecycle regressions first reproduced missing cache isolation and now pass, also covering
direct-call fighter development and same-ID replacement definitions. Exact 44-bout selection
parity remains unchanged. The fixed 800-move benchmark now measures 14.064%, 14.055%, 14.103%
(median 14.064%, versus the original 27.99%); the canonical runner enforces the 15% ceiling.
The optimized revision passes smoke, simulation-performance, audio, fight regression,
256-fight commentary, 300-fight coverage, both 3,840-fight baselines and the 356-bout full-system gate.
The primary's independent benchmark rerun measured 13.98% median selector share.
Deprecation support is now implemented, excluding retired IDs from active indexes, new generated
signatures and camp growth/promotion while retaining old signature/mastery IDs. Five focused
tests first failed for the missing field and now pass; a sixth prevents retired live successors.
The explicit schema-v2 verifier permits
only default-false additions, and `analysis/move_registry_schema2.json` records the exact result
(SHA-256 `f91913fd3211b9266db192073d6b875f3cb73d096856ebc53a8da53764b1065f`).
The original selection snapshot remains unchanged: migration verification proves the source
registry binding and all 44 bout hashes, allowing only the verified registry digest update.
The deprecation revision passes smoke and the three-seed stability playtest (display-only smoke
click probe skipped). The next integrated revision adds the 30-root map and specialist activity fix.
Phase 34's current entry/metadata/inactivity blockers and required Class C gates are recorded in
[`FIGHT_SPECIALIST_STATE_AUDIT.md`](FIGHT_SPECIALIST_STATE_AUDIT.md). Entry changes remain unimplemented.
The narrow inactivity fix is integrated: seven specialist attempt actions reset the counter while
stationary holds remain inactive. Three focused tests cover both owners, failed attempts, reversal,
warning/stand-up thresholds and common-action compatibility; restoring the old classifier produces
16 assertion failures. No entry probabilities, transitions, RNG draws or finish conversion changed.
Chooser audit also confirms that standing actions do not emit `cage_control`: its declared
range-compatible fallback does not constitute an ordinary reachable pool. Do not pad it with
new range metadata merely to satisfy the plan's inaccurate table observation; new controls are
authored into actual clinch/cage contexts, with explicit fence techniques restricted to cage.

Sequencing correction from current engine evidence: `force_cage` is chosen only from `failed shot`,
not from clinch/cage, and `leg_attack` only from `leg entanglement`, not common guard positions.
Their nine planned additions (+4/+5) must move to the specialist-state slice to avoid new sample
orphans. Preserve their final budgets and the 400-move goal: the common-position milestone is now
346 moves, followed by 54 specialist additions. The per-action arithmetic also gives 53 immediately
eligible striking/clinch additions and 44 wrestling/ground additions, including the eight bottom
submissions omitted from the original combined-slice labels. Phase 34 must repair `fence_drive`'s
starting-position mismatch as well as proving the specialist transitions.
Later structural and content steps remain pending; the historical snapshot
must stay unchanged during structural work.
Verified on 2026-09-04: all six regressions and all 1,848 ordered legal-lookup keys pass;
the full 3,840-bout result verifier exits 0 against the locked calibration. Snapshot SHA-256:
`e722fc750e084786e8ed4711ad4e479a5d8ce91d1573f40090d03c7305be9d62`.
Step 2 lookup benchmark (`py -3 tools/benchmark_move_lookup.py`) measured **0.137 microseconds**
per call at both 200 and 800 moves on 2026-09-04. This is a local timing diagnostic; exhaustive
ordered-lookup equivalence and immutable cached-return tests provide the deterministic gate.
The largest split catalogue file is 224 lines. The historical reference remains byte-identical.
The new deterministic 300-fight sample observes 72 selection contexts across eight starting
positions and reports 19 eligibility warnings. Sixteen are the plan's named common-position gaps;
three more (`fence_drive`, `kneebar`, `straight_ankle_lock`) lack a sampled parent-action context.
These are sample-scoped findings. Existing specialist-transition code must be audited before claiming
absolute unreachability. Five styles, not three, are below the 18-move floor: Dutch Kickboxer and
Freestyle Wrestler also have only 17; Phase 32 must cover all five.

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
things scale badly: the scan itself, and candidates scored per call (mean 6.3 today).

Both are roughly linear in catalogue size, so **doubling to 400 moves roughly doubles selection
cost to ~20% of simulation time**, and 800 moves would take it to about a third. World advancement
already has performance regression coverage, so this is a hard constraint, and it is the reason
Step 2 must land *before* the authoring rather than after it.

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

# Part 4 — The Doubling Budget

## 4.0 Reachable content is the real constraint

**184 of the 200 current moves sit in positions the engine can actually enter. 16 do not** (§2.4).
That splits the doubling into two routes, and they have very different costs:

| Route | What it is | Class | Recalibration |
|---|---|---|---|
| **A — Reachable now** | +155 moves into the 9 positions the engine already enters | **B** | none |
| **B — Position-gated** | +45 moves into the 5 positions Phase 34 unlocks | **C** | required |

**Route A is free and should be done first.** It is pure selection-space work: no new damage
channel, no new transition, no mechanics RNG. The corpus must come back at exactly
60.39 / 16.48 / 19.04.

**Route B cannot be authored until Phase 34 lands.** Writing techniques into `turtle` or
`leg entanglement` today just manufactures more dead content — which is precisely how
`front_headlock_posture_out` became the sixteenth orphan.

## 4.1 Per-action budget

Current counts are exact, from the live registry.

### Route A — +155 into reachable positions

| Action | Now | Target | Add | Notes |
|---|---:|---:|---:|---|
| `submission` | 9 | 25 | **+16** | Phase 29 — one technique serves 31.4% of the fight |
| `power_punch` | 33 | 43 | +10 | body-target variants now that targeting exists |
| `kick` | 28 | 38 | +10 | kick share is low; give it depth at range |
| `recover_guard` | 4 | 14 | **+10** | 1–2 per position today |
| `advance_position` | 12 | 20 | +8 | passing chains |
| `ground_strikes` | 12 | 20 | +8 | weapon typing: elbow / hammerfist / posture punch |
| `dirty_boxing` | 6 | 14 | +8 | |
| `sweep` | 7 | 15 | +8 | weighted toward the bottom fighter winning |
| `bottom_submission` | 8 | 16 | +8 | |
| `clinch` | 9 | 16 | +7 | |
| `cage_control` | 3 | 10 | +7 | only 1 legal at range |
| `takedown` | 9 | 16 | +7 | |
| `ground_control` | 7 | 14 | +7 | |
| `shoot` | 10 | 16 | +6 | |
| `jab` | 6 | 12 | +6 | |
| `stand_up` | 3 | 9 | +6 | |
| `break_clinch` | 5 | 10 | +5 | |
| `cling` | 5 | 10 | +5 | |
| `leg_attack` | 2 | 7 | +5 | |
| `force_cage` | 1 | 5 | +4 | |
| `survive` | 6 | 10 | +4 | |
| | **184** | **339** | **+155** | |

### Route B — +45, gated on Phase 34

| Family | Now | Target | Add | Unlocked by |
|---|---:|---:|---:|---|
| front headlock (incl. guillotine family) | 3 | 13 | +10 | `front headlock` |
| turtle attacks and escapes | 0 | 10 | +10 | `turtle` |
| leg entanglement / leg locks | 2 | 12 | +10 | `leg entanglement` |
| standing back control | 0 | 8 | +8 | `standing back control` |
| failed shot / re-shot scrambles | 0 | 7 | +7 | `failed shot` |
| | **5** | **50** | **+45** | |

**200 + 155 + 45 = 400.**

Defenses are a separate registry and are not counted in the 400: **18 → 40 (+22)**, Phase 33.

## 4.2 Style quotas cut across the budget

Style signature content attaches to the parent actions above rather than adding to the totals, but
it carries its own floor (Phase 32):

- every one of the 18 playable styles owns **≥ 1 `style-combination` and ≥ 1 `style-finisher`**;
- no style holds fewer than **18** authored moves — today `Grappler` has 2, `Well-Rounded` 3,
  `Taekwondo` 12.

## 4.3 Authoring rules for every new move

1. **Reachable position only**, unless the move is explicitly Route B and Phase 34 has landed.
2. **No new mechanical consequence.** A new technique is a name, a skill set and a selection
   weight. If it needs a damage channel or a transition, it is Class C and belongs in its own
   calibrated phase.
3. **Tag from the closed vocabulary** (Step 1), so behavioural tags cannot be typo'd into silence.
4. **Declare 1–3 `follow_ups`** — new content should not add to the 151 moves that have none.
5. **Satisfy the per-tag validator contract:** kicks need target / side / range band / defense
   families; takedowns need entry family and finish positions; submissions need attack path and
   failure outcomes; finishers must be skill-gated standing strikes with energy and counter risk
   above 1; style combinations need exactly one owning style and ≥ 3 components.
6. **Batch by domain, verify per batch.** One commit per action family, each ending in a corpus
   verify. A single 200-move commit is unreviewable and unbisectable.

---

# Part 5 — Content Phases

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

# Part 6 — Sequencing

## 6.1 Architecture steps

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

## 6.2 Combined delivery order

| Slice | Contents | Rationale |
|---|---|---|
| **1** | Steps 0, 1, 2 | Parity harness, schema, index. **Mandatory before authoring** — doubling the catalogue doubles selection cost without the index. |
| **2** | Steps 6, 7 | Reachability tests and authoring presets. The tests stop new orphans; the presets make 155 moves tractable to write. |
| **3** | Phase 29 (+16) | Biggest single concentration in the game, self-contained, immediately visible. |
| **4** | Phases 30, 33 (+37, +22 defenses) | Bottom-position and defensive vocabulary — the thinnest reachable pools. |
| **5** | Striking and clinch depth (+61) | `power_punch`, `kick`, `jab`, `clinch`, `dirty_boxing`, `cage_control`, `break_clinch`, `force_cage`. |
| **6** | Wrestling and ground top (+41) | `shoot`, `takedown`, `advance_position`, `ground_control`, `ground_strikes`. |
| **7** | Step 5 + Phase 31 | Chain graph and the follow-up wiring it validates — same work, land together. |
| **8** | Phase 32 | Style parity pass across everything authored in slices 3–6. |
| **9** | Steps 3, 4 | Decompose selection and add score caching, once the real 355-move cost is measurable. |
| **10** | Phase 34 + Route B (+45) | Class C surgery, sub-stepped and recalibrated, then the content it unlocks. |

Slices 1–2 pay for themselves immediately and must land before anything else. Slices 3–6 are all
Route A: pure Class B work that must leave the corpus at 60.39 / 16.48 / 19.04 exactly. Reaching
**a 355-move registry at the end of slice 8 — 339 of them reachable — is the doubling milestone
that costs no recalibration**; the final 45 (Phase 34 plus Route B) is the part that does.

## 6.3 Working rules

1. **Classify before writing code.** A/B work must leave the corpus untouched; if the verify moves,
   something leaked into Class C — find it.
2. **Never consume the mechanics RNG** for naming or selection.
3. **Run the validator early.** Per-tag contracts are enforced at import.
4. **Preserve authored content from dilution.** New style combinations, style finishers and
   signature moves must be tagged so they inherit the anti-dilution bypass.
5. **Guard the §1.5 invariants.**
6. **Report variety with the same harness every time** so numbers stay comparable across phases.

---

# Part 7 — Targets

## Content

| Metric | Now (`4a73923`) | After Route A | After Route B |
|---|---|---|---|
| Registry size | 200 | **355** | **400** |
| Reachable moves | 184 | 339 | 400 |
| Defenses | 18 | 40 | 40 |
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
