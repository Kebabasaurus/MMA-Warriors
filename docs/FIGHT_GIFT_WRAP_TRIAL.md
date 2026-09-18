# Single-root gift-wrap trial

## Mount-specific refinement

The opt-in `--gift-wrap-mount` refinement is separate from the broad hip-pressure
replacement below. It preserves both original back-control successors and trades only
the mounted hammerfist chain edge for `high_mount_arm_pinch`, a mount-only control identity.
Hammerfists remain ordinary legal actions. This uses three authored branches, not a hidden
fourth branch or position-based relabeling of an unrelated action.

A paired 300-bout inspection of the broad trial found 17 first exchange differences:
nine began with body-triangle versus hip-pressure selection from back control; the other
eight began in mount. Bout21 (seed9520000, high-competitive-6) lost a round-three submission
to a five-round decision following the back-control identity change. The refinement
restores that fixture's complete result signature and terminal RNG states. This is one
confirmed fixture, not a claim that all full-calibration timing changes are explained.

The missing scarf-hold armbar came from coverage bout117 (seed9600002, mismatch-6).
Its first difference was a mount advance/back-take versus mounted hammerfists at R1 tick11,
not a back-control identity swap. Preserving the back branches therefore did not, by
itself, recover scarf coverage.

Fresh refinement root diagnostics record 22/58 gift-wrap completions, versus default17/58
and broad-trial26/60, in the same round-two-bout cohort. Across all 300 bouts, gift-wrap
chains retain nine body-triangle selections and include eleven rear-naked chokes, seven
mount arm-pinches and two arm-triangles. These are selections, not additional finished bouts.
The count of attempted roots matching the default does not imply identical trajectories.

Thirty affected tests pass, including real mount arm-pinch follow-through and recovery of
the previously disrupted back-control fixture, graph/drift checks and nested/error cleanup.
Use `--gift-wrap-mount` for this refinement; combining it with `--gift-wrap-control` fails.

The [fresh refinement coverage](../analysis/joint_candidate_gift_wrap_mount_coverage.json)
retains exact normal/content-only/entries arms. Combined coverage has 1,522 completed roots
out of 4,667, distinct variety 16.4183, chained share 20.19%, median one and top-ten share
25.67%. Twenty-five active IDs are unobserved; ordinary Von Flue, scarf-hold armbar and
guard high-elbow coverage fail. The local five-completion gain is only one extra completed
root overall after changed trajectories. All release targets remain unchanged.

The [full refinement calibration](../analysis/joint_candidate_gift_wrap_mount_calibration.json)
retains 3,840 bouts and 39 canonical groups: 2,275 finishes /605 KO /725 TKO.
Competitive finishes improve to 47.53%, versus default47.40% and broad-trial47.19%.
Its sole calibration failure is the 48% competitive floor; the broad trial's timing
failure is absent. Both new reports' source fingerprints verify. Retain this refinement
as the experimental continuation point, not a production promotion or complete acceptance.
Coverage still loses scarf-hold armbar and fails median, variety, concentration and unused IDs.

## Reason for the trial

The high-frequency jab roots already have plausible three-action follow-ups. Their
unselected alternatives alone do not establish an authoring error. The narrower
gift-wrap root has a positional coverage gap: its control successor is back-only,
while the root can settle in mount. The prior live audit records six different-action
mount-control choices among 58 attempted gift-wrap roots in bouts reaching round two.

The opt-in `--gift-wrap-control` trial replaces only `body_triangle_back_control` with
`hip_pressure_ride`. Mounted hammerfists and rear-naked choke remain unchanged. The new
control identity supports both mount and back riding, without inventing a setup,
changing ownership, adding a fourth branch or forcing an action. Body-triangle control
remains in the catalogue and is selectable normally; only this root's edge changes.

## Fresh 300-bout findings

| Metric | Default candidate | Single-root trial |
| --- | ---: | ---: |
| Gift-wrap attempted roots, round-two-bout cohort | 58 | 60 |
| Gift-wrap completed roots in that cohort | 17 | 26 |
| All attempted roots in that cohort | 4,665 | 4,677 |
| All completed roots in that cohort | 1,521 | 1,532 |
| Mean distinct moves | 16.4117 | 16.4367 |
| Chained selection share | 20.18% | 20.19% |
| Attempted median length | 1 | 1 |
| Top-ten share | 25.65% | 25.71% |
| Unobserved active IDs | 24 | 25 |

Changed roots/trajectories mean this is not nine guaranteed recovered old cases.
Across all 300 bouts (a separate denominator), the prior gift-wrap chains included nine
body-triangle selections. The trial includes ten hip-pressure selections from back
control and seven from mount. Thus it replaces real existing content as well as closing
the mount gap. A natural-bout regression pins the new mount continuation at coverage
bout60 and verifies that it is absent from the unchanged control.

The [five-arm coverage report](../analysis/joint_candidate_gift_wrap_control_coverage.json)
preserves normal, content-only and entries arms exactly. The combined arm still fails
variety, unused IDs, concentration and median length. Scarf-hold straight-armbar coverage
disappears, adding a content failure alongside ordinary Von Flue and guard high-elbow
guillotine absence. This is not an accepted replacement candidate.

## Verification

The [full calibration](../analysis/joint_candidate_gift_wrap_control_calibration.json)
retains all 3,840 bouts and 39 groups: 2,267 finishes / 608 KO / 725 TKO. Competitive
finishes fall from 47.40% to 47.19%, and middle-fight timing adds a failure. Source
fingerprints for both new reports verify. The local follow-through improvement therefore
does not justify retaining this replacement in the default candidate. Keep the trial disabled.

Thirty affected tests pass, including actual resolver-to-trace mount follow-through,
single-definition replacement, full-DAG checks, idempotence, drift rejection and nested
context/RNG restoration. No release references, normal-play defaults, saves or EXE changed.

```powershell
py -3 -m unittest fight_gift_wrap_control_candidate_test fight_candidate_context_regression_test fight_continuation_branch_candidate_test
py -3 analysis/evaluate_joint_fight_candidate.py --coverage --gift-wrap-control --output analysis/NEW_COVERAGE.json
py -3 analysis/evaluate_joint_fight_candidate.py --gift-wrap-control --output analysis/NEW_CALIBRATION.json
```
