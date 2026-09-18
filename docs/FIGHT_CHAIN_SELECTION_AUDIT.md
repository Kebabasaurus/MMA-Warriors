# Live chain-selection audit

The 300-bout combined-candidate audit reproduces 4,665 attempted roots and 1,521
completed roots (32.60%). Every instrumented bout exactly matches its uninstrumented
control's complete audit and four terminal RNG streams. Inputs and registry are unchanged.
No mechanics, acceptance targets or executable were changed.

Authoritative evidence: [verified report](../analysis/chain_selection_verified_300.json).
It retains fixture/seed identities, per-root observations, input/audit/RNG hashes and
source fingerprints. This is the standard coverage schedule, not full calibration.

## Different-action choices: 1,120

- 968 had a positive continuation preview but chose another action.
- 152 had no positive continuation preview.
- In the 968 cases, the mean combined ticket probability of preview-supported actions
  was 53.48%. This average is conditional on the observed different-action cases, not an
  overall expected chain-completion rate. Preview eligibility can change during resolution.

## Declared action without named completion: 196

| Observed stage | Cases |
| --- | ---: |
| Actual resolved submission hold incompatible with successor IDs | 86 |
| No context-compatible successor in the initial candidate list | 49 |
| Eligible successor excluded by authored-move priority | 36 |
| Eligible successor excluded from ordinary final pool | 11 |
| Successor in final pool, another move selected | 4 |
| Context successors rejected by static/rarity gates | 5 |
| Context successors absent from live chain pool after initial candidate lookup | 5 |

The 49 initial-context cases include 41 kicks. This bin does not independently isolate
target, position and style restrictions. The final five cases retain their explicit
uncertainty; they are not proven ranking failures. No case in this cohort selected a
successor and then failed to receive recorded completion.

## What this establishes

Only 51 of these cases reach eligible-successor pool exclusion or a losing final draw.
Even recovering all 51 on these fixed trajectories would raise completion only to
33.70%, far short of the median-two requirement. That is an observed-cohort illustration,
not a prediction: changing selected IDs can change later trajectories.

Action choice is the larger investigation surface. This does not prove those choices
are wrong or authorize forcing follow-ups. Preserve survival, expired roots and opponent
interruptions. Submission identity must match the hold actually resolved; never rename a
different hold to manufacture chain credit.

## Reproduction and validation

```powershell
py -3 analysis/chain_selection_diagnostics.py --fights 300 --output analysis/NEW.json
py -3 -m unittest fight_chain_selection_diagnostics_test fight_chain_opportunity_regression_test fight_variety_opportunity_regression_test
```

All 30 tests pass. Outputs use exclusive creation. The first
`chain_selection_live_300.json` report lacks explicit resolved-hold classification;
`chain_selection_live_resolved_300.json` contains a superseded classifier that applied
hold compatibility to non-submission actions. Do not use either for final attribution.
The verified report includes the action-scoped correction, regression protection and
a fresh complete paired run. All three runs retained identical bout outcomes.
