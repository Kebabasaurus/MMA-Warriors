# Standing opportunity audit

Scope: step 1 of the candidate recovery plan. The 346-move production engine remains the
playtest checkpoint. These experiments investigate the rejected 400-move candidate; they
do not replace the locked 3,840-bout reference or authorize a new balance target.

## Starting evidence

The retained candidate has 2,264 finishes, 586 KO and 714 TKO, against required counts of
2,319 / 633 / 731. The paired [style/quality report](../analysis/current_normal_vs_candidate_style_quality_calibration.json)
uses the full canonical schedule. Its standing rows combine range and pocket when comparing
normal play with the candidate, because normal play has no ordinary pocket residence.

For fighters with post-action gas at least 60:

| Action and actor streak | Normal exchanges | Candidate exchanges | Normal knockdowns | Candidate knockdowns |
| --- | ---: | ---: | ---: | ---: |
| Kick, first action, no counter | 1,649 | 1,469 | 85 | 81 |
| Kick, first action, counter | 228 | 164 | 29 | 20 |
| Kick, second consecutive action | 871 | 606 | 67 | 30 |
| Kick, third or later consecutive action | 719 | 469 | 52 | 21 |
| Power punch, first action, counter | 296 | 242 | 32 | 15 |

These are descriptive cohorts from each arm's realized trajectories. They do not establish
that the same missed opportunity would have produced a knockdown in the other arm. In particular,
fresh power-punch volume increases overall while knockdowns fall; simply adding more attacks
does not establish recovery of the missing finishes.

## Retained-shot attribution experiment

`resolve_takedown()` shares successful takedown and cage-progress resolution between the arms.
After a strong denial, the candidate can retain a connected failed-shot scramble. Its next
action can lead into front-headlock, cage or ground work. This is a concrete route by which
standing opportunities can be displaced without changing standing attack or defence strength.

The new `--failed-shot-retention-ablation` compares the unchanged combined candidate with the
legacy denied-shot retention gate only. It keeps other specialist entries, draft content,
pocket preferences, chains and finish formulas active. The nested position setter retains the
candidate's pending/ready submission setup cleanup. Tests protect both fighter slots, boundary
contests, successful takedowns, cage progress, inherited/instance flags and nested exceptions.

Reproduce the complete experiment with a fresh output filename:

```powershell
py -3 analysis/compare_candidate_striking.py --calibration-corpus --failed-shot-retention-ablation --output analysis/failed_shot_retention_ablation_calibration.json
```

The report retains every canonical group, fixture identity, source/input/registry hashes and
per-bout trace hashes. Standing departures use actual settled destinations. Standing shots
with zero recorded takedowns include cage progress, so that count is not labelled a pure failure
rate. A gain from this ablation would establish sensitivity to retention, not justify deleting
the specialist game.

### Full-corpus result: reject the ablation as a gameplay change

The [complete paired artifact](../analysis/failed_shot_retention_ablation_calibration.json)
contains 3,840 bouts per arm. All 3,840 control-arm trace hashes, outcomes, fixture identities
and the input hash match the saved current-candidate comparison. The
[derived result-gate summary](../analysis/failed_shot_retention_gate_summary.json) reconstructs
the canonical result groups from those recorded outcomes and reconciles every group's method
counts to the paired report; it is not a separate simulation or full-plan acceptance.

| Measure | Current candidate | Legacy retention trial | Required |
| --- | ---: | ---: | ---: |
| Finishes | 2,264 | 2,279 | 2,319 |
| KO | 586 | 609 | 633 |
| TKO | 714 | 724 | 731 |
| Competitive finish rate | 47.26% | 47.67% | 48–54% |
| Standing exchanges | 57,584 | 58,340 | Diagnostic |
| Fresh-fighter kick exchanges / knockdowns | 2,708 / 152 | 2,782 / 164 | Diagnostic |
| Fresh-fighter power-punch exchanges / knockdowns | 4,810 / 287 | 4,931 / 308 | Diagnostic |
| Failed-shot pre-exchange observations | 754 | 0 | Specialist state must remain reachable |

Fresh here means post-action gas at least 60. Standing includes range plus pocket.
The trial recovers 15 finishes, 23 KO and 10 TKO, while ordinary plus technical submissions
fall from 938 to 919. All 23 additional KOs and nine of the ten additional TKOs come from
mismatches. Competitive KOs remain 274; competitive finishes improve by 12 but remain below
the gate. Competitive Mid finishes fall from 442 to 439, so the aggregate improvement is not
uniform. The historical middle-finish-timing tolerance also still fails.

There are 294 recorded standing shots into failed-shot state in the control arm. Reverting
retention removes this route and also changes subsequent clinch/ground paths. Total knockdowns
barely change (1,661 to 1,662), and bouts with any knockdown fall from 1,384 to 1,380. Therefore
the finish gain must not be described as simply creating more knockdown bouts: the composition
and continuation of the trajectories also change.

**Decision:** retain the existing candidate mechanics and preserve this rejected ablation as
attribution evidence. Removing specialist retention is not an acceptable fix, even though it
partly restores high-gas standing work. No new gameplay candidate or executable is promoted.

### Narrower escape-intent implementation: small gain, still audit-only

The current failed-shot menu uses skill bundles but does not apply the ordinary standing menu's
Sprawl And Brawl preference. The new [escape-intent trial](../analysis/failed_shot_escape_intent.py)
tests this exact omission: a Sprawl And Brawl fighter controlling a failed shot gives disengagement
1.58 times its ordinary demand, borrowing the existing trapped-clinch escape-preference intensity.
It apportions the original integer ticket budget, retains every alternative and action order,
then delegates ordinary chain weighting. Survival overrides and contested retention remain intact.
Nested trials do not stack. No fighter ratings, damage or finish formula changes.

The [full 3,840-fight calibration](../analysis/failed_shot_escape_intent_calibration.json) records
**2,265 finishes / 591 KO / 714 TKO**: one extra finish and five extra KOs, with four fewer
submission-family finishes. Competitive finish rate remains 47.26%. The trial therefore still
fails exact counts, competitive finish rate and the existing TKO/middle-timing tolerance checks.
All canonical groups, reference/schedule/registry/source hashes and failure messages are retained.

The [300-bout coverage arm](../analysis/failed_shot_escape_intent_coverage.json) exactly matches
the previous candidate's complete coverage arm and mechanical-signature hash. It still observes
all 14 positions, including 46 failed-shot and 14 leg-entanglement exchanges. Variety remains
16.22, attempted-chain median one, top-ten concentration 26.70%, and ten drafts are unobserved.
This sample demonstrates no coverage improvement; the full calibration is the evidence for the
small outcome change. It must not be described as full recovery of standing opportunities.

Reproduce with a fresh output filename:

```powershell
py -3 analysis/failed_shot_escape_intent.py --output analysis/failed_shot_escape_intent_calibration.json
```

**Step 1 outcome:** retained scrambles demonstrably displace some fresh standing offense, and
an intent-sensitive escape preference produces a small, legal experimental improvement. Neither
trial satisfies release calibration. Keep the narrower implementation available in its explicit
audit context; do not enable it in normal play or package it. Further recovery remains unresolved
and must retain the competitive/mismatch distinction established by these experiments.

## Counter-window lifecycle observation

The [300-bout-per-arm observer](../analysis/standing_counter_opportunities_300.json) confirms
that windows can survive a horn. Its denominator is **initiative calls for both fighters**,
not selected exchanges. It leaves the window and initiative calculation unchanged.

| Observed standing calls | Normal | Candidate |
| --- | ---: | ---: |
| All standing initiative calls | 9,900 | 9,770 |
| No counter window | 8,930 | 8,820 |
| Opponent window created in a previous round | 161 | 189 |
| Opponent window older than two ticks in the same round | 42 | 32 |

The candidate's 221 older opponent-window observations occur across 114 bouts. Of those calls,
139 meet the independent gas/hurt readiness limits (130 previous-round, nine same-round).
No missing or future metadata was observed. The other fighter's initiative call observes the
same window as actor-owned; those mirrored observations are not additional windows.

These observations are **not 221 lost attacks or even 139 lost bonuses**: the observer does
not run a counterfactual legal-chain preview, and pending move chains already expire at horns.
The defect also exists in normal play, which has no experimental cadence bonus. Consequently
this sample establishes a lifecycle issue but does not establish that it causes the candidate's
finish deficit. Any lifecycle correction needs its own isolated full calibration; no change
to production counter expiry is included here.

Reproduce with a fresh output filename:

```powershell
py -3 analysis/standing_counter_diagnostics.py --fights 300 --output analysis/standing_counter_opportunities_300.json
```

## Performance and release boundary

### Follow-up: round-boundary counter expiry

The default-off `analysis/round_counter_expiry.py` trial clears proven prior-round windows
before the first initiative score of a new round in the combined candidate only. Both fighters
then see the cleared state. Current-round windows, including older same-round windows, remain
unchanged. It adds no RNG draw and does not modify the production engine.

The full locked corpus gives **2,257 finishes / 586 KO / 708 TKO**, against the combined
control's **2,264 / 586 / 714**. Competitive finish rate falls to **47.05%**, below the
48–54% gate. This isolated lifecycle correction therefore does not recover the candidate's
finish deficit and is not promoted.

The five-arm coverage comparison leaves normal, content-only, entries and chains exactly
unchanged. Combined distinct-move mean is 16.195, chained share 20.13%, attempted-chain median
one and top-ten share 26.75%. The same ten draft identities remain absent. All 14 positions
remain observed. These results do not establish an improvement in standing offense.

Final-tooling artifacts are
[full calibration](../analysis/round_counter_expiry_validated_calibration.json) and
[five-arm coverage](../analysis/round_counter_expiry_validated_coverage.json).
Earlier `round_counter_expiry_calibration.json` and `round_counter_expiry_coverage.json` retain
the initial run before CLI/provenance hardening; neither replaces the final-tooling reports.
Both commands refuse existing output files. Coverage failures now print and return nonzero,
including each arm's content, chain and measured-target failures.

Six focused tests cover both first-tick initiative calls, current/invalid metadata, nested
restoration, default-off whole-bout parity, real multi-round lifecycle, source guards and
exclusive output. No EXE rebuild or player setting change is part of this follow-up.
The final-tooling reruns exactly reproduce the initial calibration groups/failures and all
five coverage arms. All 31 focused tests pass through the isolated runner, alongside the
simulation-performance regression, syntax checks, local report links and `git diff --check`.

### Previous checkpoint performance

The diagnostics are outside normal game execution. The simulation-performance regression passes.
The fixed 800-move, three-sample selector benchmark measures **13.96%** median selector share,
below the unchanged 15% ceiling; repeated mechanics match. The benchmark artifact is
[standing_opportunity_selector_benchmark.json](../analysis/standing_opportunity_selector_benchmark.json).

Final verification passes all 25 focused diagnostic/escape-intent tests in the isolated runner,
the existing specialist-entry, pocket-distance, candidate-context and variety-opportunity suites,
syntax checks, local report links and `git diff --check`. Production engine/model/catalogue source
hashes still match the saved checkpoint. No executable was rebuilt or experimental feature enabled.

Earlier unretained attack-margin tuning and prototypes that bypassed move eligibility or chain
lifetime are not acceptance evidence. In particular, the previously discussed 19.53 distinct-move
and median-two prototype cannot be used as a passing coverage checkpoint.
