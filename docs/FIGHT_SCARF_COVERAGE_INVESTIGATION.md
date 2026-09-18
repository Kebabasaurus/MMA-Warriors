# Scarf-hold coverage investigation

## Finding

No scarf selection or setup-lifecycle bug was demonstrated. The mount-specific gift-wrap
refinement changes the path of the one coverage bout that previously selected the named
scarf-hold armbar. Keep the refined candidate experimental; do not force that old path back.

The affected fixture is coverage bout117, seed9600002, mismatch-6. In the original candidate:

- R1 tick10: gift-wrap work reaches mount.
- R1 tick11: the fighter advances to back control.
- The bout later returns to side control. R2 tick9 creates a scarf setup and tick10 uses
  the actual scarf-hold straight armbar with the compatible named identity.
- Two more scarf setups are created at R2 ticks11 and14; the opponent interrupts both.

In the mount refinement, R1 tick11 instead selects mounted hammerfists as an ordinary
legal attack. The later path never creates a scarf setup. Total pre-exchange side-control
occupancy falls from13 exchanges to2. The result changes from a round-two corner stoppage
to a round-two submission. This is not a claim that either outcome is preferable; it explains
why the former scarf opportunity is absent rather than rejected.

## Complete 300-bout setup reconciliation

| Observation | Original candidate | Mount refinement |
| --- | ---: | ---: |
| Created scarf setups | 17 | 14 |
| Opponent interventions | 8 | 6 |
| Top fighter chooses another action | 6 | 6 |
| Top fighter chooses another hold | 2 | 2 |
| Actual scarf use | 1 | 0 |

The other14 scarf observations match exactly, including action tickets, selected actions,
prepared-ticket shares and readiness. Each of the eight uninterrupted weighted menus in
the refinement has a positive scarf ticket share (between2/17 and4/17). None has missing
observations, invalid observations or missing draws. The only lost observations are the
three setups in bout117: one use and two opponent interventions.

Evidence comes from the existing
[original five-arm coverage](../analysis/joint_candidate_specialist_style_coverage.json),
[refined five-arm coverage](../analysis/joint_candidate_gift_wrap_mount_coverage.json),
and a fresh paired reproduction of bout117 through the current candidate contexts.

## Verification and scope

The [900-bout frequency diagnostic](../analysis/gift_wrap_mount_scarf_frequency_900.json)
uses `--coverage --combined-only --gift-wrap-mount --fights 900`, extending the same
schedule rather than replacing calibration. It records76 created scarf setups and2 uses:
3 context changes,24 opponent interventions,24 other top actions,23 other holds and2 uses
reconcile to all76 roots. Prepared diagnostics have no invalid, incomplete or missing-draw
observations. The first300 setup observations exactly match the preceding refined report.
Current source fingerprints verify.

Required authored-content absence checks are empty in this longer sample, demonstrating
ordinary reachable use, not a pass of the fixed300-bout gate. The longer report still fails
unused IDs, distinct variety, median chain length and top-ten concentration. The900-bout
results do not justify forcing rare techniques or quietly widening the acceptance sample.

All29 tests in `fight_scarf_hold_setup_regression_test`,
`fight_prepared_submission_regression_test` and `fight_prepared_diagnostics_regression_test`
pass. No simulation logic, weights, expiry, signatures, saves or executable were changed.
This investigation does not waive the fixed300-bout required-content gate or establish
that setup frequency is sufficient. Wider frequency diagnostics cannot replace that gate.
