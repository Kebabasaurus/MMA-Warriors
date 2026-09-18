# Jab timing investigation

The experiment is audit-only: mount-refined control versus the same candidate with
earlier independent-jab repetition scoring. No production defaults or EXE changes.

## What the timing failure means

The historical timing baseline contains 695 middle-period finishes out of 3,840 bouts
(18.10%). Mount refinement has 770 (20.05%); the jab trial has 776 (20.21%). The base
was already near the two-percentage-point limit. The six additional middle finishes
do not, by themselves, establish that jabs delay stoppages. New finishes and movements
from either early or late periods must be separated in a paired transition matrix.

Timing uses finish round divided by scheduled rounds, matching the canonical audit:
round two is middle in a three-round bout, while rounds two and three are middle in a
five-round bout. Decisions and other nonfinishes retain their own category.

## Mechanism under investigation

Named selection follows resolution of the current broad exchange. A different jab ID
cannot retroactively change that exchange's strike damage. It can change the available
successor graph and later move reads. The graph feeds initiative and action weighting;
the next independently resolved actions can therefore differ without any extra RNG draw.

For example, pawing and retreating jabs have different grappling/striking successors.
This is expected coupling, not a demonstrated bug. Tactical-plan adaptation is disabled
in the frozen calibration and cannot explain its outcome changes.

## Reproduction

```powershell
py -3 -m unittest fight_jab_timing_diagnostics_test fight_repertoire_readaptation_regression_test
py -3 analysis/jab_timing_diagnostics.py --output analysis/NEW_JAB_TIMING.json
```

The full paired report must reproduce both existing calibrations in all 39 groups,
preserve inputs and registry bindings, retain source hashes and refuse output overwrite.
Short `--coverage-fights N` runs are diagnostics only. Existing references remain unchanged.

## Completed paired evidence

The [complete pair](../analysis/mount_vs_jab_timing_3840.json) exactly reproduces both
saved calibrations in all 39 groups. Across all 3,840 paired bouts:

| Change | Bouts |
| --- | ---: |
| Nonfinish to finish | 25 |
| Finish to nonfinish | 15 |
| Early to middle | 3 |
| Middle to late | 2 |
| Late to middle | 3 |

Middle-period net movement is **+3 from early +3 from late +9 new finishes -2 to late
-7 lost finishes = +6**. Thus the failed timing gate is not evidence of a general
stoppage delay. Among competitive bouts, 24 gain finishes and 13 lose them, explaining
the net eleven-finish improvement. All gained/lost finishes involve decisions.

The original full report's `mechanical` field is only a selected-field projection, not
every engine mechanic; its `plan` field can mislabel unmatched trace tails. Do not use
those prototype labels as causal evidence. Their reporting bugs do not affect the
canonical outcomes or timing matrix. The source artifact is retained unchanged.

The [corrected changed-path recheck](../analysis/mount_vs_jab_changed_paths.json) reruns
all 75 bouts whose method, round or winner changes. Every complete audit and terminal
RNG hash matches its full-parent bout exactly. It retains the full-parent denominators,
but does not characterize the paths of unchanged-outcome bouts. `mechanical_projection`
explicitly records its compared fields and their values; unequal tails are length
differences, and plan comparisons require the same actor, round and tick. No plan
differences occur in these 75 rechecked cases.

All 75 begin with a jab identity change. At the first differing projected action,
the actor is unchanged in every case. Examples of observed downstream changes:

- **Seed 8320071, mid-competitive-4:** at R1 tick5, flicker jab becomes spearing body
  jab. At tick6, the same fighter follows with a single jab instead of a one-two.
  The control's R2 TKO becomes a decision.
- **Seed 8310108, mid-competitive-3:** at R2 tick1, flicker jab becomes power jab.
  At tick2, a kick becomes a successful double-leg entry. The decision becomes a
  R2 submission.
- **Seed 8350023, mid-competitive-7:** at R2 tick1, pawing jab becomes up jab. At
  tick3, a lead teep becomes a lead-hook cross; the R3 TKO moves to R2.

These are paired trajectories, not proof that one action universally causes the final
outcome. Power-punch-to-jab is the first projected action difference in three gained
and three lost finishes; kick-to-shot also appears three times in each. A blanket
anti-jab or anti-grappling correction is not supported. Root-row `move_sequence.branch_options`
describes the prior chain; do not mistake it for the newly selected root's successor map.

## Decision and verification

Keep the jab-only trial disabled and retain the mount-refined working base. No specific
combat bug was demonstrated, so no new damage, timing, initiative or combination-weight
adjustment was made. Next mechanical work should address useful action/chain opportunities,
not tune weights to recover these particular seeded outcomes. Remaining acceptance
failures are unchanged; this investigation is not a release or performance sign-off.

Three new negative tests reproduced the reporting faults before correction and pass
after it. Recheck guards reject short parents, incomplete fixtures and mechanical
source drift. Use this command to refresh changed-path reporting without claiming a
new calibration or permitting changed combat sources:

```powershell
py -3 analysis/jab_timing_diagnostics.py --recheck-changed analysis/mount_vs_jab_timing_3840.json --output analysis/NEW_CHANGED_PATHS.json
```

The final affected run passes all 57 tests across timing diagnostics, jab scoring,
paired striking diagnostics, mount refinement, chain weighting and initiative. The
separately known historical fixture-hash failure is not repaired by this work; do not
interpret these focused results as a clean full shipping suite.
