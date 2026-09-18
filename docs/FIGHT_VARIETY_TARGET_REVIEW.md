# Variety target review — 6 September 2026

## Conclusion

The all-bout 20–24 distinct-move target is a poor standalone release criterion for the
recorded mount-refined sample. Limited action opportunities pull its mean down, while
fighters with many selections already use broad repertoires. This supports reviewing
the target, not making worse tactical choices or prolonging fights to increase variety.
**No variety, unused-ID or concentration target is changed by this review.**

The user separately accepted attempted-chain median one for now. That waiver is
implemented in both Phase 31 and joint candidate gates; the measurement remains an
advisory. Other chain and release checks remain intact, and old reports are unchanged.

## Recorded opportunity evidence

[Derived cohort report](../analysis/mount_repertoire_cohorts_300.json), based on the
existing exact-parity mount observer and matching coverage inventory. This is analysis
of a recorded source snapshot, not new simulation or a fresh mechanical calibration.
Both fighter slots are retained for every bout, including zero-action appearances.

| Selections per fighter appearance | Appearances | Mean distinct moves | Fixed-pool matching bound |
| --- | ---: | ---: | ---: |
| 0–9 | 191 | 3.63 | 3.79 |
| 10–19 | 146 | 12.06 | 13.29 |
| 20–29 | 78 | 19.31 | 21.59 |
| 30–44 | 117 | 28.43 | 32.79 |
| 45+ | 68 | 37.71 | 43.26 |
| All | 600 | 16.42 | 18.55 |

337/600 appearances (56.17%) have fewer than 20 selections. Each is incapable of 20
distinct moves on that observed path, even if every selection were unique. All 185
appearances with at least 30 selections reach at least 20 distinct moves. These are
fighter-bout appearances, not 600 unique persistent fighters.

Maximum bipartite matching assigns exchanges to distinct IDs from their observed final
pools. Its mean bound is 18.545, including generic fallback singletons. This is not
universal infeasibility: changed IDs can alter later chains, tactics and fight paths.
It does show that simply choosing different names from the same recorded pools cannot
raise this sample's average to 20. Do not exclude short appearances from the published
overall mean or present an opportunity-conditioned figure as its replacement.

## Unused catalogue

Of 25 unused active IDs, six were offered in at least one final pool but never selected:

- dutch_high_guard_cross_hook_finisher
- dutch_high_guard_hook_cross_low_kick
- heel_hook
- overhook_shoulder_fence_drive
- turtle_arm_drag_back_take
- turtle_far_side_head_punches

The remaining 19 never entered a final pool on these paths. This does not prove they
are illegal or unreachable: style, skill, rare setup, resolved hold and ranking gates
can legitimately exclude them. Ordinary selection reweighting alone cannot select an
ID absent from its final pool. The full report retains all 19 identities for targeted
eligibility/setup review. Individual named absence is already advisory; the separate
aggregate eight-unused limit remains hard until explicitly changed.

## Recommendation, not a policy change

Accepted by the user on 6 September: make the unconditional 20–24 average advisory and use opportunity-conditioned cohorts
alongside the unchanged overall metric when assessing the playtest. Do not impose a
hard 24-move upper ceiling on long fights. Any replacement hard threshold needs explicit
approval and validation beyond this sample; the fixed-path bound is not such a threshold.

Keep legality, identity/provenance, counter/chain rules and sampled concentration visible.
Review rare setup reachability rather than force all 25 IDs into 300 bouts. Do not
waive the aggregate unused-ID limit by treating the individual absence waiver as equivalent.

There is no supported reason here to add more repetition penalties, extra simulation
passes or forced move selection. With the target-policy recommendation accepted, the
next substantive release work remains competitive balance and the fixture-hash regression.

## Verification

52 affected tests pass: cohort matching/purity and zero slots, mismatched data rejection,
coverage policy, joint gate boundaries and prior repertoire diagnostics. No mechanics,
save data, simulation runtime cost or EXE changes were made. This does not replace full
release verification or repair the separately known historical fixture-hash mismatch.

```powershell
py -3 analysis/repertoire_opportunity_cohorts.py --output analysis/NEW_REPERTOIRE_COHORTS.json
py -3 -m unittest fight_repertoire_cohorts_test fight_move_coverage_regression_test fight_candidate_context_regression_test fight_repertoire_diagnostics_test
```
