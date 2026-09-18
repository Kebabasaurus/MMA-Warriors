# Move concentration: measured cause and revised implementation plan

## Finding

The proposed general repetition/underuse adjustment is not sufficient on the observed
action paths. There are exactly ten active `survive` identities. The top ten most-used
IDs must account for at least as many selections as any particular set of ten IDs,
including those ten recovery moves.

| Bouts | All move selections | Survival selections | Survival-only lower bound | Actual top-ten share |
| --- | ---: | ---: | ---: | ---: |
| 300 | 13,149 | 3,324 | 25.2795% | 25.66% |
| 3,000 | 130,047 | 33,024 | 25.3939% | 25.97% |
| 25,000 | 1,107,314 | 287,295 | 25.9452% | 26.55% |

All three retained head/kick reports have identical engine/source and registry hashes.
None records a generic survival identity. This establishes the bound for these paths;
it does not prove universal impossibility after a mechanical change. Different selected
IDs can affect later reads, chains and outcomes, even without an additional RNG draw.

Sources: [300 bouts](../analysis/standing_head_plus_kick_1pct_coverage.json),
[3,000 bouts](../analysis/standing_head_plus_kick_1pct_coverage_3000.json),
[25,000 bouts](../analysis/standing_head_plus_kick_1pct_coverage_25000.json).

## Selector investigation

The fresh retained-candidate observer reproduces 13,149 selections and 25.66% concentration.
Each observed bout is compared against a plain control for full audit and terminal RNG
equality. It records scored eligibility after the existing static/rarity gates, final
pool membership, actual choice, previous uses, style, position and round. Choice-time
gas/hurt facts are separate from post-resolution named-selection facts. These observations
are not a census of all theoretically legal actions or predictions of alternative outcomes.

| Top-ten ID | Selections |
| --- | ---: |
| composed_survival | 658 |
| shell_and_reset | 465 |
| heavy_top_breather | 364 |
| circling_breather | 340 |
| clinch_lean_recovery | 289 |
| single_jab | 285 |
| bottom_frame_survival | 257 |
| hip_frame_ground_breather | 244 |
| forearm_shell_survival | 236 |
| clinch_wrist_tie_breather | 236 |

Survival has 907 third-or-later selections, including 274 with an unseen final-pool
alternative within 2.2 score points. The existing repetition penalty already starts
on third use and caps at 14 points. Earlier exposure has been tried previously for
broad and jab-only scopes. No new general damping trial is justified by these totals.

`choose_action()` returns survival from emergency checks: gas below 8, exhaustion below
22, or hurt above the existing toughness threshold. Ordinary action menus do not contain
survival. Changing those checks or recovery efficiency would change stamina/fight balance.
The observer records eligibility facts without replaying random checks or claiming which
overlapping emergency branch won.

The [verified 300-bout observer](../analysis/concentration_retained_damage_verified_300.json)
records 1,776 survival choices below gas 8, 1,284 at gas 8 to below 22, and 264 at gas 22
or higher. Thus 3,060/3,324 (92.06%) occur while exhausted. This is a choice-time condition,
not attribution to one particular random branch.

The [five-arm count report](../analysis/concentration_counts_five_arm_control_300.json)
reproduces every previous per-arm field exactly; its only added arm field is per-move
counts. For diagnosis alone, removing survival selections leaves 9,825 other selections
whose own top-ten concentration is 18.4020%. This includes attacks, positional work and
generic fallbacks; it is not an attack-only statistic or a replacement release score.
All 54 focused diagnostics/context/coverage tests pass, and `git diff --check` passes.
The saved observer predates final summary hardening that includes zero-selected IDs and
explicitly rejects mismatched choice context; these additions have focused parity tests.

## Disposition of the original steps

1. **Instrument and locate concentration:** implemented through the existing audit-only
   observer. Retain per-move counts in future coverage artifacts so a large run does not
   lose its leading IDs. Full-bout control parity and denominator regressions are required.
2. **Soft repetition damping:** defer. It cannot bring the observed fixed-action floor
   below 25%; do not tune repeated survivals into attacks merely to clear this measure.
3. **Opportunity-weighted alternatives:** defer for the same reason. Preserve actual
   legal pools, counter/authored/chain priorities and skill gates. Do not add cosmetic
   move IDs or use unobserved specialists as padding.
4. **Cradle/guard submission frequency:** remains a separate investigation; its two rare
   identities cannot account for the recovery-dominated concentration problem.
5. **Calibration and performance:** no new mechanical candidate was introduced. Existing
   calibration remains historical evidence for the retained candidate. No new 25,000-bout
   balance claim or executable build follows from this diagnostic work.

## Recommended next design decision

Measure attacking/positional repertoire separately from emergency recovery for diagnosis,
while continuing to display the unchanged all-move concentration gate. Recovery frequency
should be evaluated through time spent exhausted, recovery episodes and subsequent ability
to act, rather than assuming repeated survival names establish an attacking-variety defect.
Any proposal to alter the acceptance gate needs an explicit product decision; this work
does not waive it or silently redefine its denominator.

If a gameplay problem is demonstrated, implement one recovery-mechanics slice with clear
physical ownership and context, then compare fixed fixtures for fatigue residence, finishes,
KO/TKO, competitive tiers and timing. Adding genuine recovery techniques is also a possible
content expansion, but requires a deliberate change to the 400-ID inventory contract.
Neither route should be disguised as a neutral selector refactor.

After a mechanical slice passes focused regressions, run the ordinary five-arm coverage,
3,000-bout frequency check and frozen 3,840-bout calibration. A promising candidate can then
receive the 25,000-bout frequency run and whole-bout CPU profiling. Retain all failures and
advisories; extended frequency evidence does not replace the ordinary coverage gate.

## Reproduce diagnostics

```powershell
py -3 -m unittest fight_repertoire_diagnostics_test fight_candidate_context_regression_test fight_move_coverage_regression_test
py -3 analysis/repertoire_selection_diagnostics.py --retained-damage --fights 300 --output analysis/NEW_CONCENTRATION_OBSERVER.json
```

Output paths must be new. Normal-play mechanics, saved careers and EXEs are unaffected.
