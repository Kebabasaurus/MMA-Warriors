# Native-sport development overhaul: longitudinal audit

## Audit contract

- Final stable core: `world.py` SHA-256 begins `63E409BB`.
- Four fresh-world seeds: `101`, `202`, `303`, and `404`.
- Fifteen simulated years per seed; snapshots at years 3, 5, 10, and 15.
- Production `process_combat_sport_worlds` runs every month and production `age_world_one_year` runs at each year boundary.
- All rating metrics use `combat_sport_display_rating`, the normalized player-facing 1-99 native-sport scale.
- Original athletes and every generated prospect are tracked through development, activity, retirement, crossover, and replenishment.
- No save was loaded or written. No core game file was edited by this audit.

Artifacts:

- Post-overhaul data: `audits/combat_sport_longitudinal_audit_latest.json`
- Pre-overhaul baseline: `audits/combat_sport_longitudinal_audit_baseline_pre_overhaul.json` and `.md`
- Reusable runner: `tools/combat_sport_longitudinal_audit.py`

The old raw ratings were divided by their sport's current display scale when making before/after comparisons.

## Original-roster development

| Sport | Start | Baseline Y3 change | Post Y3 | Baseline Y5 | Post Y5 | Post Y10 | Post Y15 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Boxing | 88.78 | -5.37 | **+1.97** | -5.30 | **+2.53** | -0.25 | -3.31 |
| Kickboxing | 90.01 | +1.06 | **+1.31** | +1.15 | **+1.55** | -0.31 | -1.47 |
| Muay Thai | 91.33 | +0.27 | **+0.94** | +0.37 | **+1.08** | -0.75 | -2.17 |
| Wrestling | 92.85 | +1.33 | **+1.54** | +1.49 | **+1.74** | +0.83 | -0.32 |
| Brazilian Jiu-Jitsu | 94.59 | +1.22 | **+0.87** | +1.35 | **+0.96** | +0.41 | -1.62 |

The Boxing synchronization regression is fixed. Instead of losing over five normalized points, the initial cohort gains 1.97 by year 3 and peaks at 91.53 around age 33.0.

The overhaul also introduces visible decline. Every original cohort is below its own peak by year 10 and below its starting level by year 15; Wrestling remains closest to flat at -0.32.

## Production prospect development

| Sport | Baseline entry | Post entry | Baseline gain to observed peak | Post gain to peak | Three-year gain | Per year | Five-year gain where observed |
|---|---:|---:|---:|---:|---:|---:|---:|
| Boxing | 51.93 | **67.33** | +0.71 | **+8.93** | +8.05 | +2.68 | +9.85 |
| Kickboxing | 53.24 | **65.53** | +0.70 | **+9.48** | +7.26 | +2.42 | +9.51 |
| Muay Thai | 51.46 | **68.14** | +0.66 | **+8.34** | +6.53 | +2.18 | +8.62 |
| Wrestling | 51.89 | **68.29** | +0.65 | **+8.70** | +6.90 | +2.30 | +9.63 |
| Brazilian Jiu-Jitsu | 52.11 | **67.83** | +0.62 | **+6.62** | +7.86 | +2.62 | Not yet observed |

Prospect development is now plainly visible and materially different between careers. The old pipeline gained only about 0.6-0.7 points to its observed peak; the new pipeline gains 6.6-9.5.

No generated prospect reached ten years of circuit tenure during the 15-year audit because replenishment does not begin until the original retirement wave. BJJ prospects also entered too late to produce a complete five-year sample.

## Activity, retirement, and replenishment

| Sport | Bouts/year Y3 | Bouts/year Y10 | Mean retirement age | Active Y15 | Original active Y15 | Prospect active Y15 | Crossovers Y15 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Boxing | 3.95 | 3.71 | 39.44 | 44.75 | 0.25 | 44.50 | 0.50 |
| Kickboxing | 3.95 | 3.25 | 38.11 | 44.75 | 0.00 | 44.75 | 1.00 |
| Muay Thai | 3.14 | 2.86 | 37.78 | 63.50 | 0.50 | 63.00 | 0.25 |
| Wrestling | 4.19 | 3.54 | 38.31 | 44.50 | 0.50 | 44.00 | 0.25 |
| Brazilian Jiu-Jitsu | 3.80 | 3.85 | 40.35 | 44.75 | 5.00 | 39.75 | 0.25 |

- No original athlete had zero new fights at any checkpoint.
- Active headcount remains 89.0%-90.7% of starting size at year 15.
- Sport-specific retirement timing is visible: Muay Thai retires earliest, BJJ latest.
- BJJ preserves considerably more of its original roster at year 15 than before: 5.0 active versus 2.0 in the baseline.

## Long-save circuit quality: before and after

| Sport | Baseline active rating Y15 | Post Y15 | Improvement | Gap from starting standard |
|---|---:|---:|---:|---:|
| Boxing | 53.11 | **76.21** | +23.10 | -12.57 (-14.2%) |
| Kickboxing | 54.60 | **75.04** | +20.44 | -14.97 (-16.6%) |
| Muay Thai | 52.71 | **76.52** | +23.81 | -14.81 (-16.2%) |
| Wrestling | 52.52 | **77.07** | +24.55 | -15.78 (-17.0%) |
| Brazilian Jiu-Jitsu | 54.47 | **76.41** | +21.94 | -18.18 (-19.2%) |

The previous catastrophic 39%-43% talent collapse is gone. A smaller 12%-19% generational drop remains because the game begins with a nearly all-elite real-name roster and later replaces it with developing prospects. Whether this remaining decline is desirable depends on whether the starting world is intended to be an exceptional golden generation or a permanently maintained global standard.

## Target assessment

Controlled calibration targets supplied for the final implementation:

- Early career: +3.5 to +4.4 native-rating points/year.
- Prime: +1.2 to +1.7/year.
- First two post-prime years: near 0 to -0.5/year.
- Deep decline: -2.2 to -3.5/year.

Production-world observations:

1. **Early development misses low.** Generated prospects with three complete years gain +2.18 to +2.68/year, below the +3.5 to +4.4 controlled target in every sport. These are mixed real-world entrants aged 18-23, so some cross into prime during the window, but the production pipeline still develops more slowly than the controlled early cohort.

2. **The initial elite cohort is ceiling-constrained.** Its first-three-year pace is only +0.29 to +0.66/year, below the controlled prime target. These athletes start at 89-95 with limited potential room, so this is expected potential-cap behavior rather than proof the controlled prime calibration failed.

3. **Early post-prime behavior is close to flat, but Boxing remains positive.** Between years 3 and 5, annual movement is Boxing +0.28, Kickboxing +0.12, Muay Thai +0.07, Wrestling +0.10, and BJJ +0.05. Four sports are effectively flat; Boxing is still outside the intended flat-to-negative band.

4. **Visible deep decline misses substantially low.** From years 5 to 10, observed annual changes are only Boxing -0.56, Kickboxing -0.37, Muay Thai -0.37, Wrestling -0.18, and BJJ -0.11. Retirement freezes some ratings before a full decline can accumulate, but BJJ has little retirement by year 10 and still shows only -0.11/year. The production career path does not display the controlled -2.2 to -3.5/year decline rate.

5. **Age-40 decline is poorly observable.** Mean retirement ages range from 37.78 to 40.35, so most non-BJJ careers end before a sustained deep-decline sample develops. The controlled decline audit and the longitudinal world audit are measuring different populations.

## Overall conclusion

The overhaul fixes the two critical baseline failures: Boxing no longer collapses on first synchronization, and generated prospects now develop strongly enough to keep mature circuits in the mid/high 70s rather than the low 50s. Activity, headcount, final-fight retirement, and sport-specific career length remain stable across seeds.

The main remaining calibration question is the gap between controlled stage tests and production careers. Real generated prospects undershoot the early target, and real long-save veterans decline much more slowly than the controlled deep-decline target before retirement censors the curve.
