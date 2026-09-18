# Submission development — 6 September 2026

## Implemented, not promoted

`--hold-transitions` and `--cradle-setup` are separate, default-off audit candidates.
The measured working context also enables the mount refinement and heel-hook repair.
Production registration, saves, player UI and the EXE are unchanged.

Top and guard submission chains now require an explicit authored transition between
two actual dangerous holds on immediately consecutive exchanges. Actor, round,
position and ownership must remain consistent. Safe defenses, repeated holds,
interventions, transitions, referee resets and horns do not license chain credit.
The existing technique draw is never changed to obtain a successor. When selected,
the chain is labelled with the two actual holds rather than an invented generic sequence.

A Catch Wrestler choosing side-control ride work can contest a cradle using the
existing control margin. Preparation keeps only the existing three control points;
it awards no submission attempt, damage, danger, signature, mastery or completed chain.
On the next same-top side-control submission, a qualified fighter gets one cradle-crank
ticket after normal adaptation. The existing hold draw consumes the opportunity even
if another hold wins. Skill 64, style, ownership and strict expiry remain enforced.

Both features have trace-based provenance validators in coverage and every bout of
full calibration. They reject missing, mismatched or interrupted evidence, not just
wrong final move names. No extra RNG draw or second gameplay simulation pass is added.

## Measurement

| Full canonical corpus | Finishes | KO | TKO | Proven transitions / named chains | Invalid provenance |
| --- | ---: | ---: | ---: | ---: | ---: |
| Hold transitions only | 2,275 | 605 | 725 | 76 / 57 | 0 |
| Cradle only | 2,275 | 605 | 725 | Not enabled | 0 |
| Joint | 2,275 | 605 | 725 | 76 / 57 | 0 |

Each report retains all 3,840 fights and 39 canonical groups. Every group summary
matches the prior mount/heel candidate. Competitive finishes still fail at 47.53%
against the unchanged 48% floor. Identical group summaries do not establish universal
mechanical neutrality. The canonical roster creates no cradle opportunities, so it
does not establish cradle-specific balance or reachability.

The joint five-arm 300-bout coverage report has five proven transitions, four named
chains, three cradle roots and no cradle uses. Unused IDs fall from 25 to 24; top-ten
share is 25.77% and still fails. Normal, content-only, entries and chains control-arm
mechanical signatures match the prior report; the combined signature changes.

The supplementary 900-bout frequency run has 13 proven transitions, 11 named chains,
six cradle roots and no uses; 11 IDs remain unused. It cannot replace the standard
300-bout gate. Neither zero observed cradle uses nor a passing controlled resolver
test is a reason to increase its weights to force coverage.

Artifacts:

- `analysis/hold_transitions_calibration.json` and `analysis/hold_transitions_coverage.json`
- `analysis/cradle_setup_calibration.json` and `analysis/cradle_setup_coverage.json`
- `analysis/submission_development_calibration.json` and `analysis/submission_development_coverage.json`
- `analysis/submission_development_frequency_900.json`

## Performance and tests

The separate `analysis/cradle_natural_matchups_240.json` uses fixed Catch-Wrestler
matchups across levels55/70/85 against four opponent styles (240 bouts per arm).
The trial creates61 cradle roots;16 immediately following submissions choose other
holds, and no crank is observed. Both arms select four top submission chains and no
guard chain. Finishes change from80 to79. Source, registry, input and RNG checks pass.
This is supplementary evidence, not a replacement corpus or demonstrated natural cradle
completion. Tests prove the guard-chain and cradle resolver paths, but neither gains
ordinary named coverage in these recorded samples. Do not force their selection.

The 800-move benchmark profiles three repeated 44-bout samples per arm. Median whole-bout
CPU is 6.125 seconds for control and 6.28125 seconds for the joint trial (+2.55%).
This includes wrapper overhead and changed trajectories; it is not a pure overhead
estimate or whole-career speed guarantee. Selector-only shares are 10.79% and 10.68%,
but omit wrapper work and must not be used to claim the feature is free.
All benchmark registry/input/RNG/repetition checks pass. Report:
`analysis/submission_development_800_benchmark.json`.

All 117 affected regressions pass, as do the fight-engine regression and full-system
suites. The broader release still has unresolved balance,
unused-ID/concentration and historical fixture-hash issues. No release package was made.

```powershell
py -3 -m unittest fight_submission_chain_candidate_test fight_cradle_setup_candidate_test
py -3 analysis/evaluate_joint_fight_candidate.py --coverage --gift-wrap-mount --heel-hook-identity --hold-transitions --cradle-setup --output analysis/NEW_SUBMISSION_COVERAGE.json
py -3 analysis/evaluate_joint_fight_candidate.py --gift-wrap-mount --heel-hook-identity --hold-transitions --cradle-setup --output analysis/NEW_SUBMISSION_CALIBRATION.json
py -3 analysis/benchmark_submission_development.py --output analysis/NEW_SUBMISSION_PROFILE.json
```

Keep new output paths: existing evidence is never overwritten.
