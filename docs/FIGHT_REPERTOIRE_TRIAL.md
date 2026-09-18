# Mount-refined repertoire investigation

## Scope and evidence

The [300-bout observer report](../analysis/mount_repertoire_selection_300.json) compares
each instrumented bout against an uninstrumented mount-refined control, with exact full
audit and terminal RNG equality. It records 13,212 actual selections, including generic
identities. This is evidence for that source snapshot, not for later mechanics.

Among second-or-later choices, 80 jab selections and 65 ground-control selections have
an unused alternative within 2.2 score points in the actual final pool. Alternative IDs
overlap: these are opportunities, not guaranteed additional distinct moves. Survival
accounts for most repetition and is deliberately excluded from this trial.

Actual variety is 16.4183 moves per fighter. Maximum bipartite matching between observed
exchanges and their final legal pools yields a fixed-path mean bound of 18.545, including
both fighter slots in every bout. This is not universal infeasibility: different chosen
IDs can change later chains, plans and trajectories. The 20–24 requirement remains.

## Jab-only experiment

`--jab-readaptation --gift-wrap-mount` applies the existing independent-move repetition
curve one use earlier only for jabs. It retains the 14-point cap, original live-chain
scores, every non-jab score, legal pools and existing random draws. Broad readaptation
is a separate rejected trial and cannot be combined with this switch. No normal-play
default, save data or executable changes are part of this experiment.

```powershell
py -3 -m unittest fight_repertoire_readaptation_regression_test fight_repertoire_diagnostics_test fight_candidate_context_regression_test fight_gift_wrap_mount_candidate_test
py -3 analysis/evaluate_joint_fight_candidate.py --coverage --gift-wrap-mount --jab-readaptation --output analysis/NEW_JAB_COVERAGE.json
py -3 analysis/evaluate_joint_fight_candidate.py --gift-wrap-mount --jab-readaptation --output analysis/NEW_JAB_CALIBRATION.json
```

Output files must be new. Coverage cannot substitute for full calibration. Individual
named-move sample absences are now advisory by user decision; aggregate unused IDs,
variety, concentration, chains, legality, timing, balance and performance remain gates.

## Coverage and regression results

The [fresh five-arm report](../analysis/joint_candidate_mount_jab_coverage.json) retains
exact normal, content-only and entries mechanical signatures against the mount-refined
reference. Combined variety rises only from 16.4183 to 16.45, top-ten share falls from
25.67% to 25.61%, and chained-selection share rises from 20.19% to 20.28%. Median chain
length remains one. Completed roots in the round-two-bout cohort fall from 1,522/4,667
to 1,511/4,666; the higher selection share is not improved root completion. There are
still 25 unused active IDs. Variety, aggregate unused IDs, concentration and median still fail.
There are no hard content findings; three named sample absences remain advisory.

All 39 directly affected tests pass. A separate 30-test adaptability/variety/selection/
chain run passes 29 and fails the historical original-content selection snapshot.
That failure reproduces alone without the trial: all 44 fixture input hashes differ,
while every recorded mechanics, trace, move, defense, sequence and count fingerprint
matches. The original reference is untouched. This isolates the failed comparison,
not the cause of fixture drift, and must not be reported as a clean shipping suite.

## Full calibration decision

The [complete fresh calibration](../analysis/joint_candidate_mount_jab_calibration.json)
retains all 3,840 bouts and 39 canonical groups: 2,285 finishes / 605 KO / 719 TKO,
versus the mount base's 2,275 / 605 / 725. Competitive finishes improve from 47.53%
to 47.92%, still below 48%. Middle finish timing now deviates by more than two
percentage points and fails. These are the two calibration failures; neither is waived.

Do not adopt this trial as the new default candidate. The tiny coverage gain, fewer
completed roots and added timing failure do not establish a net improvement. Retain
the mount-refined base and both reports. A next investigation can compare changed
competitive and middle-timing bouts to locate downstream path changes, rather than
increasing repetition penalties globally or forcing finishes. No fresh performance
acceptance was collected for this rejected trial, and no EXE was rebuilt.
