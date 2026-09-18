# Unused-move repair — 6 September 2026

## Confirmed defect and scoped correction

The legacy `heel_hook` identity belongs to `counter_leg_lock`, which resolves a
knee-line ownership reversal, not a submission attempt. Its counter tag also requires
a separate counter window. Meanwhile the real `leg_attack` resolver can draw a plain
heel hook, but previously had no compatible named identity for it.

`--heel-hook-identity` reparents that one identity to `leg_attack` inside the audit
context and removes only its counter tag. Position, minimum skill 66, other tags,
energy and other definition fields are preserved. Only an explicitly resolved plain
heel hook licenses the identity; inside/outside heel hooks retain their own identities.
The two draft positional counter-grips remain available for knee-line reversals.
No resolver weights, RNG draws, legal action menus or production defaults change.

This is an eligibility repair, not a guarantee that a selected sample uses the move.
The candidate remains opt-in; no EXE was rebuilt.

## Fresh measurement

The five-arm 300-bout report is
`analysis/joint_candidate_heel_identity_coverage.json`. All five mechanical signatures
match the prior mount report. The combined arm still has 25 unused IDs and a 25.67%
top-ten share. It contains only five leg attacks: one belly-down ankle lock, three
figure-four toe holds and one inside heel hook. No plain heel hook was drawn, so this
sample cannot demonstrate ordinary use of the repaired identity.

The full 3,840-bout report is
`analysis/joint_candidate_heel_identity_calibration.json`. All 39 group summaries match
the prior mount candidate: 2,275 finishes, 605 KO, 725 TKO. Competitive finishes remain
47.53%, failing the unchanged 48% floor. These matching summaries are not a claim of
complete trace parity or release acceptance.

The extended `analysis/heel_identity_frequency_900.json` records three correctly named
plain heel hooks. Compared with the prior 900-bout mount diagnostic, unused IDs fall
from 13 to 12, with no newly absent identities and an unchanged measured mechanical
signature. This proves ordinary reachability beyond the controlled resolver test; it
does not replace or pass the still-failing 300-bout unused-ID gate.

The saved reports precede a later audit-context nesting guard. That amendment rejects
disabled inner scopes inside an enabled repair context, without changing top-level
fight execution. Reports retain their original source hashes and were not rewritten
or recollected. The guard regression failed before the fix and passes afterward;
all 102 affected tests pass on the final source. Enabled nesting and exception cleanup
remain supported. This is a partial unused-content repair, not full release completion.

## Other absences

Pure eligibility checks found real resolver tickets and legal matching identities for
triangle choke, anaconda choke, kneebar and straight ankle lock. There is no evidence
supporting lowered skill limits or forced selection for those moves. The earlier
900-bout mount diagnostic already reduces the absent list from 25 to 13, showing that
some absences are sample-dependent. It does not replace the ordinary coverage gate.

The broad top/guard submission-chain identities and cradle finisher cannot simply be
mapped to a single arbitrary hold: their authored multi-step/setup evidence is not
established by the current resolver. Completing that content needs explicit provenance,
not a compatibility alias. Rare scarf/Von Flue opportunities retain their existing
setup and expiry rules.

## Reproduction

```powershell
py -3 -m unittest fight_heel_hook_identity_test fight_submission_identity_regression_test fight_move_leg_entanglement_authoring_test fight_candidate_context_regression_test
py -3 analysis/evaluate_joint_fight_candidate.py --coverage --gift-wrap-mount --heel-hook-identity --output analysis/NEW_HEEL_COVERAGE.json
py -3 analysis/evaluate_joint_fight_candidate.py --gift-wrap-mount --heel-hook-identity --output analysis/NEW_HEEL_CALIBRATION.json
```

Outputs use exclusive creation. Keep all failures and historical reports; do not
package the candidate while release gates remain unresolved.
