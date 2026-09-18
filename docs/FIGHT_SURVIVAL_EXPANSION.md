# Survival repertoire expansion

The user approved growing the combined catalogue from 400 to 440 moves rather than
removing existing techniques. `--survival-expansion` adds 40 recovery techniques to the
existing ten. It is an explicit audit candidate until the remaining release checks pass.

| Context | Additions | Examples |
| --- | ---: | --- |
| Standing | 8 | Cross-arm cover, chin-behind-shoulder recovery, tucked-elbow cover, short-step guarded recovery |
| Clinch/cage | 6 | Inside-biceps frame, collarbone frame, overhook brace, fence-backed base |
| Ordinary ground top | 6 | Low posture inside guard, wide-base half guard, knee-post side control, palm-post mount |
| Ordinary ground bottom | 8 | Biceps shield, knee shield, elbow wedge, elbow-knee shell, two-hand neck protection |
| Specialist positions | 12 | Turtle shell, front-headlock neck brace, stalled-shot recovery, rear-clinch grip cover, heel protection |

The complete authored list and skill bundles are in
[`survival_development.py`](../fight_moves/catalogue/survival_development.py).
Names describe protective postures or recovery work; they do not claim an escape,
successful attack, position gain or extra recovery reward.

## Mechanics and ownership

The existing survival decision, gas/hurt recovery and deterministic selector are reused.
The additions have narrow positions and explicit top/bottom or controller/controlled
roles. Ground top is physical ownership; leg-entanglement top means knee-line ownership.
Fence-backed recovery requires the controlled cage fighter. Missing ownership excludes
owned techniques. Neutral resets can conservatively remove an owned option.

The candidate also filters the existing `bottom_frame_survival`,
`hip_frame_ground_breather` and `heavy_top_breather` by physical ownership. Those names
can no longer appear for the opposite role or as physical-top work in leg entanglement.
There is no new repetition multiplier, forced move, extra RNG draw or additional
production simulation pass. Skill scoring and existing repeat penalties select among
eligible techniques. New entries declare no follow-ups, finishers or signature tags.

The role filter runs on the indexed action/position pool, not the entire 440-move
catalogue. Its wrapper still has runtime cost; whole-bout CPU must be measured rather
than claiming cost-free selection. Audit-only trace validation checks every selected
addition against the recorded action, position and ownership in coverage and calibration.

## Verification workflow

```powershell
py -3 -m unittest fight_survival_catalogue_test fight_survival_expansion_test fight_candidate_context_regression_test fight_move_coverage_regression_test
py -3 analysis/evaluate_joint_fight_candidate.py --coverage --survival-expansion --standing-head-damage --kick-power --gift-wrap-mount --heel-hook-identity --hold-transitions --cradle-setup --output analysis/NEW_SURVIVAL_COVERAGE.json
py -3 analysis/evaluate_joint_fight_candidate.py --survival-expansion --standing-head-damage --kick-power --gift-wrap-mount --heel-hook-identity --hold-transitions --cradle-setup --output analysis/NEW_SURVIVAL_CALIBRATION.json
py -3 analysis/benchmark_survival_expansion.py --output analysis/NEW_SURVIVAL_CPU.json
```

Output files are exclusive and existing references remain intact. Only the expanded
combined arm requires 440 active moves; the ordinary 400-move candidate keeps its count
contract. All other concentration, unused-ID, chain, provenance and balance gates stay
in place. The approved distinct-move mean and chain median remain advisories.

## Results collected

The [final-source five-arm check](../analysis/survival_expansion_440_release_check_300.json)
includes the actor-name and causal-jab finish wording repairs. All five mechanical
signatures exactly match the earlier verified five-arm run. The combined arm has
19.03% concentration, a defense-clause peak of four, 1,359 validated new survival
selections with zero invalid roles, no content/chain failures, and the unchanged
27-unobserved-ID failure. This is the current standard-coverage checkpoint.

The [25,000-bout defense-wording recheck](../analysis/survival_expansion_440_defense_fix_25000.json)
reduces the rolling-300 identical-defense-clause peak from 12 to 6 and has no reported
extended-run failures. Its mechanical signature, registry fingerprint and every move
selection count exactly match the preceding 25,000-bout report. Top-ten concentration
is 19.47%; 115,461 new survival selections have zero invalid roles. Only
`catch_cradle_neck_crank_finisher` and `guard_submission_chain` remain absent.

This verifies the defense-clause change, not a waiver of the ordinary 300-bout
unused-ID gate. The [source-bound selector diagnostic](../analysis/survival_expansion_440_unused_stage_source_bound_300.json)
reproduces all 300 paired bouts and finds 19 absent moves with zero observed eligible
offers plus eight offered-but-unselected IDs. Different move draws on those same
observed pools cannot alone meet the maximum-eight absence target. That does not
prove global unreachability, and does not justify forced actions or named identities.

The first 300-bout pass reduced top-ten concentration from 25.66% to 19.03%, with
38/40 additions observed. Its ownership-count field was incomplete because the cradle
wrapper hid a method marker. Preserve that first artifact as preliminary evidence;
the verified report uses a scoped harness flag and rejects missing validation counts.

The [full calibration](../analysis/survival_expansion_440_calibration.json) records
2,292 finishes, 603 KO, 736 TKO and 1,387/2,880 competitive finishes (48.16%). There are
no calibration failures and 16,371 new survival selections have zero invalid roles.
This collection precedes the reporting-marker correction, which changes observation
activation and nesting guards rather than move mechanics. No reference was overwritten.

The [verified five-arm run](../analysis/survival_expansion_440_verified_300.json) retains
19.03% concentration and validates all 1,359 selections of new survival IDs with zero
invalid roles. All five mechanical signatures match the preliminary run across the
reporting correction. The four non-expanded arms also match the retained control.
There are 27 absent active IDs in this small sample: 25 existing IDs and two additions,
`turtle_inside_elbow_recovery` and `front_headlock_neck_brace_recovery`. The unchanged
eight-absence limit still fails; concentration now passes.

The [paired CPU benchmark](../analysis/survival_expansion_440_cpu.json) uses three
44-bout repetitions per arm on actual 400/440 registries. Median CPU is 2.453125 seconds
for control and 2.4375 seconds for expansion (-0.64%). This is no measured slowdown
within a small, noisy sample, not a guaranteed speed improvement or a whole-career
latency claim. Inputs, caller RNG and repeated same-arm outcomes are checked.

The [3,000-bout frequency run](../analysis/survival_expansion_440_frequency_3000.json)
observes all 40 additions. Top-ten concentration is 19.30% versus 25.97% in the retained
3,000-bout control; 13,247 new recovery selections have zero invalid ownership claims.
The least frequent addition appears ten times. Only the four pre-existing IDs
`catch_cradle_neck_crank_finisher`, `entangled_outside_heel_hook`, `guard_submission_chain`
and `judo_kesa_armbar_finisher` remain unobserved. This extended diagnostic has no measured
target failures, but does not replace the ordinary 300-bout release gate or full shipping
verification. No EXE was rebuilt or default candidate promoted.

All 63 focused catalogue/ownership/diagnostic/context/coverage tests pass, as do the fight
engine regression and full-system suites. The full calibration retains all 39 canonical
group summaries exactly against the retained damage candidate.

The smoke suite passes. Its unrelated matchmaking click-selection probe was skipped
because the test display could not lay out the fighter table. `git diff --check` passes.
