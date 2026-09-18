# Pool-aware boxing combination trial

## Scope

`--boxing-chain-pool --gift-wrap-mount` is an isolated audit-only policy on the
mount-refined candidate. It does not change production defaults or package the 400-move
engine. The jab repetition experiment and earlier stronger/commitment policies remain off.

The [refreshed 300-bout chain audit](../analysis/mount_chain_selection_300.json) has exact
full-bout and terminal-RNG parity in every instrumented bout. It records 4,667 roots,
1,522 completions and 961 different-action choices with a positive continuation preview.
Among declared actions without completion, 37 lose to authored priority (22 power punches),
and 11 to ordinary-pool exclusion (five jabs, two power punches).

This does not establish a broken selector. The old preview estimates static eligibility,
whereas the actual selector also applies contextual ranking and authored priorities.
The trial tests whether avoiding currently unavailable follow-ups makes intent more useful.

## Implementation boundaries

- Inspect only jab and power-punch demand, whose target fingerprints are deterministic.
- Run only after the existing preview validates a live, legal continuation.
- Reproduce current named-pool score arithmetic, rarity, counter and authored priorities.
- Remove a continuation bonus only when that current pool has no declared successor.
- Preserve the existing action list, integer ticket total, skill/gas cap and survival paths.
- Leave initiative, named selection, two-tick expiry and interrupted-root accounting unchanged.
- Reject incompatible tuning in both direct and nested contexts; matching nested trials do not stack.

This is a pre-resolution estimate, not a guarantee about the final pool after resolution.
It adds candidate scoring but no random draws. Actual named selection remains independent.
The base chain observer's raw bonus hook runs before this filter; do not present it as
filtered-trial telemetry without adapting that observer explicitly.

## Coverage result

The [fresh five-arm report](../analysis/joint_candidate_boxing_pool_coverage.json) retains
exact normal/content-only/entries mechanical signatures against the mount base.

| Metric | Mount base | Pool-aware trial |
| --- | ---: | ---: |
| Completed roots / attempted roots | 1,522 / 4,667 | 1,548 / 4,656 |
| Chained-selection share | 20.19% | 20.62% |
| Mean distinct moves | 16.4183 | 16.5333 |
| Top-ten move share | 25.67% | 25.49% |
| Median attempted chain length | 1 | 1 |
| Unused active IDs | 25 | 26 |

The 26 additional completions are a changed-cohort result, not 26 recovered fixed roots.
Variety, concentration, median length and aggregate unused-ID targets still fail. Hard
content findings are empty; named sample absences remain advisory under the user policy.

## Verification

`fight_boxing_chain_pool_test.py` covers same-state actual-selector pool agreement for
head/body targets and counters, authored/low-rank exclusion, unchanged legal alternatives,
expiry, initiative, nested error cleanup and normal-play full-bout parity.

A real-bout regression uses coverage seed9330000: at R1 tick18, power-punch continuation
intent targets `one_two`, while the current pool contains only
`muay_thai_teep_cross_elbow_knee`. The observation preserves full audit and terminal RNG
equality against the uninstrumented trial.

```powershell
py -3 analysis/evaluate_joint_fight_candidate.py --coverage --gift-wrap-mount --boxing-chain-pool --output analysis/NEW_POOL_COVERAGE.json
py -3 analysis/evaluate_joint_fight_candidate.py --gift-wrap-mount --boxing-chain-pool --output analysis/NEW_POOL_CALIBRATION.json
py -3 analysis/benchmark_boxing_chain_pool.py --output analysis/NEW_POOL_PERFORMANCE.json
```

The benchmark adds the disjoint `boxing_pool` and `select_exchange_move` profile times
so moving work outside the selector cannot hide its cost. It also reports whole-sample
CPU/wall time. This is a complete-fight benchmark, not a whole-career latency guarantee.

## Full calibration and decision

The [fresh calibration](../analysis/joint_candidate_boxing_pool_calibration.json) retains
all 3,840 fights and 39 canonical groups. It records **2,267 finishes / 598 KO / 727 TKO**,
versus the mount base's 2,275 / 605 / 725. Competitive finishes fall from 47.53% to
47.33%; this is the sole calibration failure, with timing still passing.

Keep the pool-aware policy opt-in, not the new working base or a shipping fix. Better
sampled combination follow-through does not offset the worse full-corpus balance result
or the remaining coverage failures. There is no new damage multiplier, forced continuation,
changed finish reference, normal-play setting, save change or rebuilt executable.

The final affected run passes all 97 tests, including prepared-submission boundaries and
the existing rejected-policy suites. These are focused checks, not a clean full shipping
suite; the separately documented historical fixture-fingerprint issue remains unresolved.

## Performance result

The [800-move paired benchmark](../analysis/boxing_chain_pool_800_benchmark.json) passes
the 15% profile budget in both arms: control 10.74%, trial **12.27% including preview**.
The trial's selector-only 10.41% would hide the added work. All three trial samples
record 262 boxing-pool previews and identical repeated mechanical signatures; all
registry, fixture and caller-RNG purity checks pass.

Median profiled CPU time per 44-bout sample rises from 9.45 to 10.66 seconds; wall time
rises from 12.54 to 14.59 seconds. These are profiled, changed-trajectory workloads,
not isolated overhead estimates or a whole-career latency guarantee. The trial does
add work and is not promoted despite passing the selector budget. Production retains
its existing code path and this preview never runs unless explicitly enabled in audits.
