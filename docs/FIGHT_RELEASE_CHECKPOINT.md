# Fight release checkpoint

## 6 September: v3.0.10 built and launch-verified

The user approved the 25,000-bout rare-ID measurement and requested the executable.
This supersedes the unresolved 300-bout unused-ID blocker described in the historical
checkpoint below, without changing other gates. Version 3.0.10 now wires the native
440 profile into the application, saves, development, editor and universe validation.
The old audit engine remains separate. The full 3,840 paired native bouts now match
the retained candidate's complete audits and all four terminal RNG streams exactly;
all 39 groups are identical and balance/provenance failures are empty. The native
300-bout report also preserves every move count and mechanical hash, with 19.03%
top-ten concentration and a defense repetition peak of four.

Three alternating warmed 300-bout CPU pairs measure candidate/native medians of
15.344/15.672 seconds (+2.14%, approximately 1.1ms per audited bout). This is small
dispatch overhead, not evidence of zero cost or a benchmark of whole-career latency.
The narrative and simulation performance regressions separately pass; narrative CPU
overhead is -0.25% in its paired 12-week aggregate check. No extra simulation passes
or random draws were introduced. Evidence: `analysis/release_native_cpu_300.log`,
`analysis/release_native_calibration_parity_3840.json` and
`analysis/release_native_coverage_300.json`.

Fresh native 25,000 coverage passes with 19.47% top-ten concentration, defense peak
six, 115,461 valid new-survival selections and zero invalid roles. Only cradle neck
crank and guard submission chain remain unobserved. Every move count and mechanical
signature matches the retained 25,000 candidate. The composed current native engine
certificate passes: `analysis/release_native_engine_certification_v2.json`.

Raw reports remain immutable. Two obsolete test fixtures were migrated after
collection (strong cage work can reach standing back; deprecation patches the host
profile). Certification records those exact test/policy-source changes while requiring
unchanged runtime/audit helpers and references. All 140 canonical shipping suite entries
pass across the recorded resumed batches. One Matchmaking click-layout probe was skipped
because its test display could not lay out the fighter table; this is not full UI coverage.
The three stability seeds reached month four with 172, 184 and 174 events respectively.

Game and editor builds succeeded using the canonical toolchain/options and separate staging
destinations. Both are installed under `dist/MMA Warriors`; the packaged editor's universe
validation and final portable checks pass. The previous portable package is retained at
`build/portable_previous_3_0_9_20260906`. All 63 existing save/database/active-universe files
match that backup byte-for-byte after launch. Logs retain their history and append startup;
no new crash report appeared.

Computer Use visually verified the installed v3.0.10 Game Menu in windowed and maximized
layouts and responsive navigation to Weekly Command Centre. No career was loaded, advanced
or saved during this launch check. The user requested shutdown after these successful checks.

The prior checkpoint below is historical, not the current production wiring policy.

## 6 September: defense fix and integration gate

The current combined candidate has 440 moves. The retained 25,000-bout frequency
report, `analysis/survival_expansion_440_coverage_25000_v2.json`, records 19.47%
top-ten concentration, all 40 added survival IDs, and two absent old IDs. It also
records a blocking defense-clause peak of 12 within a rolling 300 bouts. An empty
`measured_final_target_failures` list did not mean the whole report passed.

The ordinary five-arm 300-bout report still has 27 absent active IDs in the
combined arm against the maximum eight. Extended frequency evidence does not
currently supersede that gate. The 440 mechanics therefore remain audit-only;
the production registry and executable have not been promoted.

The defense wording fix expands the deterministic clause pool from three to 16.
Its focused tests prove unchanged complete-bout facts and terminal RNG streams.
The candidate CLI now aggregates content, chain and measured-target failures by
arm before choosing its exit status. Both fixes are integrated into source and
the canonical test workflow. The fresh 25,000-bout defense recheck now passes with a
rolling-300 peak of six; mechanics, registry and every move count match the prior run.
Shipping verification exposed separate historical fixture/rendering incompatibilities
and survival actor/finish-label omissions. Those are now repaired: both historical
44-bout snapshots verify exactly, and the complete 256-bout commentary gate has zero
failures (previously 46). Historical verification explicitly reconstructs the recognized
fixture schema and renderer while retaining strict reference/trace checks. The standard
unused-ID policy remains unresolved. Both frozen 3,840-bout result/action baselines
pass, as do Fight Night, database validation and editor checks. Stability passes for
all three seeds through Month 4 (179/183/190 recorded events). Every canonical suite
has passed after the failed parity/commentary checks were repaired and rerun; the
new diagnostic tests were also run through the isolated runner. The smoke click-selection
probe was skipped because the test display could not lay out the fighter table.
The final-source five-arm report `analysis/survival_expansion_440_release_check_300.json`
preserves every earlier mechanical signature. The combined arm has only its existing
27-unobserved-ID target failure; its defense-clause peak is four. Control-arm findings
remain separately visible and are not a verdict on candidate acceptance.

The historical tests run with the frozen three-defense-clause, sixteen-survival-template
and canonical-jab renderer. Current wording is separately covered by the live commentary
gate and full-bout/RNG parity regressions. New captures always retain current fighter
fields and rendering. No historical reference was replaced.

For the current candidate's actual selector pools and resolved holds, run:

```powershell
py -3 analysis/survival_unused_diagnostics.py --output analysis/NEW_UNUSED_STAGES.json
```

The diagnostic pairs each observed bout with its control, verifies complete
audit/RNG parity, retains fixture/input/source/registry hashes and writes exclusively.
Scored eligibility, final-pool offers and selections are separate observations;
zero offers on recorded paths do not establish universal unreachability.

## Earlier checkpoints (historical measurements)

The 2% head-damage trial is retained as an approved experimental change: it raises
competitive finishes by 13 to 47.99%. The user accepts middle-timing drift as advisory;
competitive and coverage blockers remain, so it stays audit-only.

The subsequent [1% kick-power trial](FIGHT_KICK_POWER_TRIAL.md), combined with 2% head
damage, clears full calibration at 1,387/2,880 competitive (48.16%) with no calibration
failures. Coverage still fails 25 unused IDs and 25.66% top-ten concentration, so the
candidate remains unpromoted and unbuilt.

Latest work: [submission development](FIGHT_SUBMISSION_DEVELOPMENT.md) implements
evidence-backed hold transitions and contested cradle setup/follow-through, audit-only.
Fresh separate/joint full calibration keeps all39 group summaries unchanged (competitive
47.53% still fails). Joint300 unused IDs fall25 to24; top-ten25.77% still fails. Natural
cradle use remains unobserved, including the separate240-bout Catch cohort. Controlled
resolver tests pass. Whole-bout profiling measured+2.55% CPU; no extra gameplay simulation
pass or RNG draw was added. Neither candidate was promoted or packaged.

Latest unused-move work: the [heel-hook identity repair](FIGHT_UNUSED_MOVE_REPAIR.md)
recovers three named submissions in the extended 900-bout diagnostic without new
absences. The default-off repair is not release acceptance: the 300-bout sample still
has25 unused IDs and top-ten share25.67%; all39 full calibration groups match the mount
base and competitive47.53% still fails. All102 affected tests pass. No EXE change.

6 September amendment: the user has accepted attempted-chain median one for now; this
is now advisory, with all other gates preserved. The [variety target review](FIGHT_VARIETY_TARGET_REVIEW.md)
finds that 337/600 recorded fighter appearances had fewer than 20 selections, while all
185 with 30+ selections used at least 20 distinct moves. Subsequent user approval makes
the unconditional 20–24 mean advisory too, not the unused-ID or concentration gates.
These are recorded-path cohorts, not fresh calibration or release acceptance.

Latest combination work: the [pool-aware boxing trial](FIGHT_BOXING_COMBINATION_TRIAL.md)
raises sampled completions to 1,548/4,656 but lowers full competitive finishes to 47.33%.
It stays disabled; the mount-refined base remains the experimental continuation point.
All 97 affected tests pass. No new candidate has been accepted or packaged.

The requested 400-move release is **not accepted and has not been packaged**.

### 6 September competitive-balance triage

Read-only comparison of `joint_candidate_gift_wrap_mount_calibration.json` against its
hash-matching frozen `fight_engine_baseline.json` (all 39 groups retained):

| Competitive cohort | Frozen baseline finishes | Mount candidate finishes | Difference |
| --- | ---: | ---: | ---: |
| Low (960 bouts) | 501 | 473 | -28 |
| Mid (960 bouts) | 425 | 443 | +18 |
| High (960 bouts) | 458 | 453 | -5 |
| All (2,880 bouts) | 1,384 | 1,369 | -15 |

The frozen baseline here is distinct from the later accepted historical headline
calibration. The current candidate needs 14 additional competitive finishes to reach
1,383/2,880 and clear the 48% floor. Low-tier differences include -17 TKO and -15
submission-family finishes, offset partly by +4 KO. Across competitive style cohorts,
Wrestler versus Karate has the largest finish deficit (-17); these style cohorts do
not identify the low-tier/style intersection without per-fixture evidence.

Prioritize paired low-tier resolver paths and that matchup for the next mechanical
investigation. Aggregate counts do not establish causation or justify a global damage
boost, a tired-fighter fix or another gate waiver. This is analysis of saved evidence,
not a new calibration. The unused-ID/concentration failures and fixture-hash regression
also remain unresolved. All 52 affected policy/cohort tests pass; no EXE was rebuilt.

The ordinary game retains 346 registered moves; the 54 additional identities and
specialist/chain mechanics remain audit-only. Passing regression tests does not
promote that candidate.

## Latest checkpoint amendment

The sections below retain the earlier specialist-style checkpoint. The current working
experimental base is the [mount-specific gift-wrap refinement](FIGHT_GIFT_WRAP_TRIAL.md):
its complete 3,840-bout calibration records 2,275 finishes / 605 KO / 725 TKO, with
competitive finishes at 47.53% still failing the 48–54% range. Timing passes. Its coverage
has 16.4183 distinct moves, 25 unused active IDs, 25.67% top-ten share and median chain
length one; chained-selection share passes at 20.19%.

The user has since made individual named-move sample absences advisory. Older reports
and the historical table below retain their original findings; those named absences are
no longer release blockers. Aggregate unused-ID, variety and other acceptance gates
remain unchanged. See the [repertoire investigation](FIGHT_REPERTOIRE_TRIAL.md) for the
next isolated jab-only experiment. No new candidate has been promoted or packaged.
That experiment is now complete: competitive finishes reach 47.92%, but a new
middle-timing failure and persistent repertoire failures prevent acceptance. The latest
focused checks pass 39/39; a broader run passes 29/30, with historical fixture-hash drift
isolated from unchanged fight/selection fingerprints. The earlier full-suite success
below must not be presented as current all-green verification.
The [subsequent timing investigation](FIGHT_JAB_TIMING_INVESTIGATION.md) reproduces both
full calibrations and exactly rechecks all 75 changed outcomes. It finds mixed path
trade-offs, not a general delay or a demonstrated combat bug. Diagnostic reporting is
corrected and 57 affected tests pass; the jab trial remains disabled and the EXE unchanged.

## Verification completed

- The complete `py -3 run_regression_suite.py` run exited successfully, including
  both 3,840-fight normal baselines, the full fight-system test, editor/database
  checks and final stability playtest. Its three stability worlds reached Month 4.
- The run started before the latest specialist-style integration. All six affected
  suites were separately rerun after integration: 60 tests passed, including the
  new style policy, default-off parity, plan ordering and survival guards.
- The smoke matchmaking click-selection probe was skipped because the test display
  could not lay out the fighter table. Do not describe this as complete UI coverage.
- The fresh [combined selector benchmark](../analysis/specialist_style_combined_800_selector_benchmark.json)
  expands the actual candidate from 400 to 800 moves. Its median selector share
  is 10.8815%, below 15%, across three 44-bout samples. All purity checks pass.
  This is selector cost, not proof of unchanged whole-career simulation latency.

## Current candidate failures

The [full calibration](../analysis/joint_candidate_specialist_style_calibration.json)
retains all 3,840 bouts and 39 canonical groups. It records 2,272 finishes,
606 KO and 725 TKO. Its sole calibration failure is competitive finishes at
47.40%, against 48–54%; the accepted historical-total tolerance has not been changed.

The [five-arm coverage report](../analysis/joint_candidate_specialist_style_coverage.json)
still records these failures in the fixed 300-bout combined arm:

| Requirement | Current result |
| --- | --- |
| Mean distinct moves 20–24 | 16.4117 |
| Attempted-chain median at least 2 | 1 |
| Top-ten move share at most 25% | 25.65% |
| At most 8 unused active IDs | 24 |
| Required ordinary Von Flue and guard high-elbow coverage | Both absent |

Chained-selection share passes at 20.18%, but does not establish chain length.
Five draft IDs are unused; draft-only absence is not the full-registry count.
This checkpoint is not a claim that every other item in the move-system plan
has received a final release audit.

## Next mechanical decision

The current read-only 300-bout chain report found 4,665 attempted roots and 1,521
completions (32.60%). Losses partition into 1,120 other action choices, 613 survival
choices, 786 expiries, 312 round boundaries, 82 terminal bouts, 35 role changes and
196 declared-action cases without named completion. Its optimistic fixed-cohort
bound is not proof of universal feasibility or permission to omit failed roots.

The proposed next trial is a stronger skill/fatigue-bounded continuation preference.
**The user has approved an audit-only trial above +2.** The first opt-in trial doubles
the existing action bonus, bounded at +4; the default candidate retains +2. It leaves
initiative and prepared readiness unchanged. The trial must preserve legal actions, survival priority,
expiry, accounting, immutable references and all final release targets, and receive
fresh full calibration and coverage. Approval authorizes investigation, not
guarantee a passing result or authorize packaging a failure.

### First stronger trial result: not accepted

The [full +4 trial](../analysis/joint_candidate_stronger_continuation_calibration.json)
retains all 3,840 bouts and 39 groups. It records 2,289 finishes, 626 KO and 727 TKO.
Competitive finishes reach 47.47%, with mid tier falling to 44.48%. Its three calibration
failures are competitive finish rate, middle-fight timing drift and no doctor stoppages
in the accepted sample. Zero observations do not prove global unreachability.

The [trial coverage](../analysis/joint_candidate_stronger_continuation_coverage.json)
has 21.47% chained selections, 16.4483 distinct moves, attempted median one, 27.05% top-ten
concentration and 23 unused active IDs. Guard high-elbow coverage is recovered, while
ordinary Von Flue coverage remains absent. These mixed results do not pass the plan.

Every arm of the [fresh default control](../analysis/joint_candidate_strength_control_coverage.json)
exactly matches the preceding specialist-style report. The trial's normal, content-only
and entries-only arms also match that control. The +4 trial remains opt-in and is not
the default candidate or a packaged build.

### Earlier repertoire adaptation result: not accepted

The independent-choice repetition trial keeps the existing score curve and ceiling but
applies it one use earlier. Live eligible follow-ups retain their original score. Its
[full calibration](../analysis/joint_candidate_readaptation_calibration.json) retains
3,840 bouts and 39 groups: 2,267 finishes, 611 KO and 715 TKO. Competitive finishes
47.26% and middle-fight timing fail. It is not promoted.

The [coverage trial](../analysis/joint_candidate_readaptation_coverage.json) improves
distinct variety to 17.1833, still below 20–24. Chained share is 20.57%, attempted median
one, top-ten concentration 25.53%, and 23 active IDs (five drafts) are unused. Required
ordinary Von Flue and guard high-elbow coverage remain absent. The
[fresh control](../analysis/joint_candidate_readaptation_control_coverage.json) exactly
matches every preceding default-candidate arm; trial normal/content-only/entries arms
match that control. Source fingerprints were verified after collection with no mismatches.
The five affected test modules pass all 42 tests, including the new trial's five tests.

The default candidate therefore remains the specialist-style candidate above. Neither
later experiment is a replacement release candidate. Static combined-registry checks
find 400 active moves, 40 defenses, no validation errors or undersupplied styles, and
363 moves with follow-ups. Catalogue files peak at 224 lines, below the 400-line limit;
these static successes do not resolve the measured runtime failures.

## Follow-through fix attempt and reporting correction

The probability-bounded fresh/unhurt commitment trial remains disabled. Its
[full calibration](../analysis/joint_candidate_probability_commitment_calibration.json)
retains 3,840 bouts and 39 groups: 2,269 finishes / 614 KO / 734 TKO. Competitive
finishes 47.05% and both early/middle timing fail. Coverage raises chained share to
21.88% but retains median one, worsens variety to 16.0717 and top-ten share to 25.98%,
and leaves 24 active IDs unused. No acceptance thresholds or references changed.

That trial exposed a separate validator bug: a pending Von Flue wrap at a horn was
reported as missing cancellation evidence in the next round because ordinary traces
omit explicit round-end events. Forward round transitions now expire validator pending
state. Stale setup claims still fail and no game mechanics change. The new regression
fails before this fix; all 71 affected tests pass afterward. Calibration above was
collected before this reporting-only correction; it is not a new mechanical candidate.
The [fresh corrected coverage](../analysis/joint_candidate_probability_commitment_verified_coverage.json)
preserves all five mechanical signatures exactly. Four complete arms are unchanged; the
combined arm changes only the angle boundary count and removal of its false provenance
failure. All genuine content, variety and chain failures remain. Current source hashes verify.

## Packaging

The [scarf investigation](FIGHT_SCARF_COVERAGE_INVESTIGATION.md) finds no demonstrated
selector bug: one changed fight loses all three prior setup opportunities, while the other14
observations are identical. A900-bout frequency extension records76 setups and2 ordinary uses.
This establishes reachable use, not a fixed300 coverage pass. No mechanics were changed.

The subsequent mount-specific gift-wrap refinement is retained as an experimental continuation
point, not a shipping promotion. Its [full calibration](../analysis/joint_candidate_gift_wrap_mount_calibration.json)
records2,275 finishes /605 KO /725 TKO and competitive47.53%; timing passes, while the48%
floor remains failing. Its [coverage](../analysis/joint_candidate_gift_wrap_mount_coverage.json)
retains median one,25 unused IDs and missing scarf-hold coverage. Thirty affected tests pass.

The subsequent [single-root gift-wrap trial](FIGHT_GIFT_WRAP_TRIAL.md) is also disabled:
local root completion improves, but full calibration records 2,267 finishes /608 KO /725 TKO,
competitive47.19% and a middle-timing failure. Scarf-hold armbar coverage disappears. Thirty
affected tests pass; no default-candidate or normal-play promotion follows from these tests.

The existing `dist/MMA Warriors/MMA Warriors.exe` is unchanged: last write
4 September 2026, 23:58:04 local time; size 4,565,816 bytes. It is not a new
400-move build. Player saves have not been rewritten or removed.

Build the requested candidate only after its acceptance failures are resolved,
normal-play promotion is tested, and the complete final release audit passes.
