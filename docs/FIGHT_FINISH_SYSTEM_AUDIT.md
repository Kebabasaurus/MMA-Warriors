# Fight Finish System Audit

## Outcome

The historical finish-system checklist has been reconciled against the current engine. Its valid
classification, reachability, commentary and verification work is implemented. Its old global
balance changes are intentionally not applied because the engine has since been recalibrated and
the current competitive sample already meets those targets.

The accepted 3,840-fight release corpus is unchanged:

| Measure | Current evidence | Release rule |
| --- | ---: | --- |
| All finishes | 2,319 / 3,840 (60.39%) | Exact count |
| KO | 633 / 3,840 (16.48%) | Exact count |
| TKO | 731 / 3,840 (19.04%) | Exact count |
| Competitive finishes | 1,408 / 2,880 (48.89%) | 48-54% |
| Competitive submissions | 488 / 2,880 (16.94%) | 15-19% |
| Doctor Stoppage | 4 | Must remain reachable |
| Injury Stoppage | 10 | Must remain reachable |
| Rounds 4-5 of five-round finishes | 164 / 839 (19.55%) | At least 6% |

Mismatch bouts account for much of the difference between the 48.89% competitive rate and the
60.39% aggregate. A global reduction would suppress ordinary competitive bouts to solve behavior
that is intentional in major skill mismatches.

## Checklist Reconciliation

### Global finish and submission conversion

No mechanical retune was made. The historical 48-54% finish and 15-19% submission targets are now
permanent checks on the competitive group, where the current engine measures 48.89% and 16.94%.
The overall exact counts remain locked, and `competitive_finish_conversion()` is unchanged.

### Injury and doctor stoppages

Both methods are already reachable in the accepted corpus, so their thresholds were not lowered.
Body- and leg-kick knockdowns now use distinct strike commentary categories rather than falsely
identifying the exchange as an injury stoppage. A real body or leg Injury Stoppage still comes only
from the separate accumulated-trauma check.

Doctor eligibility is expressed as a named between-round serious-cut window. It requires structured
cut evidence: at least three cuts plus major bleeding or vision risk. The existing officiating roll
and threshold remain unchanged, preserving stoppage frequency and RNG order.

### Championship-round finishes

No damper change was made. The current five-round sample produces 164 round-four/five finishes from
839 total finishes, or 19.55%, already well above the historical 6% minimum. Halving the dampers
would move the engine in the wrong direction and replace the accepted balance.

### Finish paths and commentary

Dead duplicate finish helpers remain removed. The live finish sequence now retains authored detail
for submissions, doctor and injury stoppages, signature/head-kick knockouts and walk-off knockouts,
while connecting KO/TKO prose to the recorded causal move and emitting one official result. Ordinary
submission endings retain several multi-beat setups and call the technique-aware authored finish
bank for the final lock and tap.

### Method classification

The canonical sets live in `constants.py`:

- `FINISH_METHODS` controls career finishes, seasonal finishes, contractual bonuses and excitement.
- `KO_METHODS` controls KO-family career/season counts and recovery consequences.
- `SUBMISSION_METHODS` controls submission-family career/season counts and recovery consequences.
- `KNOCKOUT_AWARD_METHODS` is deliberately narrower: only direct KO/TKO results qualify for
  Knockout of the Year.

This removes substring and exclusion-based disagreements between fight settlement, statistics,
awards and finance.

## Verification

Run these checks after any finish-system change:

```powershell
py -3.13 fight_engine_regression_test.py
py -3.13 fight_engine_full_system_test.py
py -3.13 analysis/generate_fight_engine_baseline.py --verify analysis/fight_engine_baseline.json
py -3.13 analysis/generate_fight_action_baseline.py --verify analysis/fight_engine_action_baseline.json
py -3.13 smoke_test.py
```

The canonical release runner executes the same result and action baselines in isolated data roots.
Never regenerate either checked-in baseline merely to absorb an unintended drift.
