# MMA Fight Engine Preservation Baseline

## Purpose

This is the Phase 0 reference for the fight-engine roadmap. It records the existing distribution
that later realism and architecture work must preserve. It is not a target assembled from desired
results; it is a fixed-seed measurement of the current engine.

Generate the baseline with:

```powershell
py -3.13 analysis/generate_fight_engine_baseline.py --seeds-per-matchup 120
```

Verify the current engine against it with:

```powershell
py -3.13 analysis/generate_fight_engine_baseline.py --verify analysis/fight_engine_baseline.json
```

## Corpus

- 3,840 fights
- 32 stable style-shaped matchups
- 120 fixed seeds per matchup
- 2,880 competitive fights with overall gaps no greater than six
- 960 deliberately separated mismatches
- Low, mid and high competitive tiers
- Three- and five-round scheduled fights
- Eight behaviours and eight style profiles

## Frozen Results

| Group | Fights | Finish rate | 95% confidence interval |
| --- | ---: | ---: | ---: |
| Overall | 3,840 | 59.64% | 58.07–61.18% |
| Competitive | 2,880 | 48.06% | 46.23–49.88% |
| Competitive low | 960 | 52.19% | 49.03–55.33% |
| Competitive mid | 960 | 44.27% | 41.16–47.43% |
| Competitive high | 960 | 47.71% | 44.56–50.87% |
| Mismatch | 960 | 94.38% | 92.73–95.66% |

### Overall method distribution

| Method | Count | Share of all fights |
| --- | ---: | ---: |
| Decision | 1,549 | 40.34% |
| Draw | 1 | 0.03% |
| KO | 603 | 15.70% |
| TKO | 755 | 19.66% |
| Submission | 856 | 22.29% |
| Technical submission | 45 | 1.17% |
| Corner stoppage | 28 | 0.73% |
| Injury stoppage | 3 | 0.08% |

KO/TKO accounts for 35.36% of all fights. The combined submission family accounts for 23.46%.
Other stoppages account for 0.81%.

### Finish timing

| Timing band | Count | Share of all fights |
| --- | ---: | ---: |
| Early | 1,173 | 30.55% |
| Middle | 695 | 18.10% |
| Late | 422 | 10.99% |

Timing bands are relative to scheduled length: the first third, middle third and final third.

## Preservation Gates

- Architecture-only changes must retain every frozen parity signature unless the roadmap explicitly
  records why an RNG decoupling changes individual bouts.
- Overall finish rate may move no more than 1.0 percentage point.
- KO and TKO rates are each independently locked within 1.0 percentage point.
- Each competitive tier may move no more than 1.5 percentage points; as with other subgroup cuts,
  a nominal crossing is release-blocking when its 95% interval also separates from baseline.
- The competitive-to-mismatch finish gap may move no more than 1.5 percentage points.
- KO/TKO and submission family shares may move no more than 2.0 percentage points.
- Early, middle and late finish shares may move no more than 2.0 percentage points.
- An adequately sampled style or behaviour group may move no more than 3.0 percentage points without
  an explicitly approved balance change. A small-group delta is release-blocking only when its 95%
  confidence interval also separates from the frozen interval; sample noise remains visible in the
  report but is not misclassified as proof of drift.

Do not change `competitive_finish_conversion()` or rewrite final methods to force these gates. Fix
the new mechanic responsible for any drift.

After separating combat, officiating and presentation streams plus mechanically meaningful foul
recovery, the same corpus reports 59.79% finishes, 16.25% KO, 18.98% TKO and 35.23% combined
KO/TKO. The baseline itself was not regenerated.

After trace-backed judging, the corpus reports 59.32% finishes, 16.25% KO and 19.24% TKO. After
separating transient hurt from lasting location trauma and calibrating recovery, it reports 60.39%
finishes, 16.48% KO, 19.04% TKO and 35.52% combined KO/TKO. Every figure remains inside the locked
gates; the original baseline remains unchanged.

After adding ID-keyed fight plans, real counter windows, target/pace effects and trace-led corner
adaptation, legacy/unplanned bouts report the same 60.39% finishes, 16.48% KO, 19.04% TKO and
35.52% combined KO/TKO. The compatibility path remains Balanced without automatic switching;
planned player bouts and explicitly AI-controlled bouts opt into tactical behavior. The converter
and frozen baseline remain unchanged.

The Phase 5 exchange-chain trace adds setup, explicit defense, real counter-window and ordered
combination evidence without adding a mechanics draw. The corpus consequently remains exactly at
60.39% finishes, 16.48% KO, 19.04% TKO and 35.52% combined KO/TKO; the original benchmark and
competitive finish conversion remain unchanged.

Phase 6 adds validated settled and within-exchange grappling transitions, including failed shots,
front headlocks, turtle, standing back control and leg entanglements. Unconsolidated scrambles keep
their full legal position path but settle to the same mechanically justified endpoint, preventing a
brief position from perturbing later action draws. The corpus remains exactly at 60.39% finishes,
16.48% KO, 19.04% TKO and 35.52% combined KO/TKO, with the baseline and converter unchanged.

## Current Exact Headline Gate and Signature Audit

The accepted post-roadmap corpus is now additionally locked by integer count: 3,840 fights must
produce exactly 2,319 finishes, 633 KOs and 731 TKOs. `compare_to_accepted_calibration()` runs beside
the original tolerance comparison, and the canonical isolated regression runner executes the full
generator. A one-bout change fails even when the rounded displayed percentage would look unchanged.

The original per-bout `signature` hashes remain Phase-0 historical evidence, not a valid current
commentary gate. An audit found that they include rendered scorecard strings and the complete
`last_fight_stats` payload; later plan, move-family, signature and analysis telemetry therefore changes
the hash even when winner, method and round are unchanged. Commentary work is instead checked with
paired same-seed current-engine runs across every voice, while the exact accepted counts guard the
release outcome. The Phase-0 file is deliberately retained and must not be regenerated to conceal
that history.
