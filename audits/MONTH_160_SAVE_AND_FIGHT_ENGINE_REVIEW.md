# Month 160 Save And Fight Engine Review

Audit target: `dist/MMA Warriors/Saves/Game 1.json` at Month 160, Week 4.

## World Integrity

- 2,270 unique active or free-agent MMA fighters after save migration.
- No duplicate fighter IDs and no duplicate exact fighter names.
- 1,024 free agents. The unsigned market is large enough to support independent cards and AI recruitment.
- The most recent 120 archived cards contain 831 linked bouts. There were no mixed-gender bouts and no self-fights.
- 89 archived bout links do not resolve to a currently active fighter object. These are historical records for fighters who have retired, moved out of the active MMA pool, or were otherwise removed from the current database; the historical result itself remains valid.

## Promotion Health

| Promotion | Active roster | Cash | Stability | Thin divisions (<4) |
| --- | ---: | ---: | ---: | ---: |
| BAMMA | 66 | -$2.30m | 1 | 2 |
| KSW | 109 | $63k | 58 | 0 |
| BRAVE Combat Federation | 77 | $2.33m | 33 | 1 |
| ACA | 77 | $2.37m | 43 | 2 |
| Cage Warriors | 96 | $9.95m | 37 | 0 |
| UFC | 124 | $31.14m | 79 | 0 |

BAMMA is in an active post-buyout financial-recovery cycle, not silently broken. Its last bridge workout was Month 151; the normal recovery mechanism provides another when its protected interval expires. It should not make more cuts while its existing divisions are thin.

## Matchmaking Finding

The Eamon Gupta vs Ruben Mendoza series was a real historical failure of card construction:

- Eamon Gupta: OVR 97, 46-7, ELO 1799, momentum +5.
- Ruben Mendoza: OVR 95, 5-36, ELO 1294, momentum -5.
- Their histories recorded 21 meetings, most recently Month 130.

The broad ratings hid a material style/detail mismatch. Eamon has the stronger striking, durability, reflexes, form, and confidence layer; Ruben's high overall is driven much more by grappling. Before the current engine adjustment, Eamon won 87.7% of neutral direct simulations and 99.5% under the saved context.

Changes now in source:

1. Each bout gets bounded fight-night form driven partly by consistency. It affects initiative and technical exchanges; it does not choose a winner.
2. Momentum remains important but no longer overwhelms technical exchanges.
3. AI matchmaking rejects recent, repeatedly lopsided non-rival rematches and gives severe losing-streak fighters a fresh, close reset matchup when their division has one. It does not award a win or create a large ability mismatch.
4. Monthly AI roster reviews release selected redundant, expensive, inactive, or poor-form fighters into the real free-agent market. Champions, booked fighters, high-upside young prospects, and shallow divisions are protected.

After the initial fight-night form adjustment, the same saved matchup tested at 68.3% Eamon / 31.3% Ruben / 0.3% draw under neutral conditions, and 80.3% / 19.7% under current context. A later modest widening of the same zero-centred form roll, verified against the retained Month 160 backup, moved that to 63.0% Eamon / 36.3% Ruben / 0.7% draw under neutral conditions and 76.2% / 23.8% under saved context. The better fighter remains better, but the underdog can now win through the actual exchange simulation.

The original reset allowance was tightened after review: it now permits at most a nine-OVR booking gap and prefers an opponent only three OVR lower, not eight. Separately, a 10+ meeting series with a major career win-rate split remains unavailable while the losing fighter is still in a severe slump. In 30 saved-world BAMMA card builds, Eamon vs Ruben was booked zero times. No outcome is assigned by this rule.

## Finish Calibration

Historic archive (831 resolved bouts, produced before this review):

| Result | Count | Rate |
| --- | ---: | ---: |
| Decision | 336 | 40.4% |
| TKO | 185 | 22.3% |
| KO | 128 | 15.4% |
| Submission | 115 | 13.8% |
| Doctor stoppage | 32 | 3.9% |
| Corner stoppage | 27 | 3.2% |
| Technical submission | 8 | 1.0% |

The important defect was not ordinary knockout probability: doctor and corner stoppages were being tested too frequently. Doctor stoppages could be rolled after every exchange once a fighter had two cuts, and corner stoppages began at an 8% between-round base chance.

The revised engine requires a doctor inspection at the end of a round and three visible cuts, with severity, resilience, and damage affecting the chance. Corner stoppages now require materially worse accumulated damage and begin at a 1.2% between-round chance. These are mechanism changes, not method replacement.

Post-change competitive 500-fight sample (same gender/weight, OVR gap <=8):

| Result | Count | Rate |
| --- | ---: | ---: |
| Decision | 256 | 51.2% |
| TKO | 129 | 25.8% |
| KO | 60 | 12.0% |
| Submission | 50 | 10.0% |
| Technical submission | 3 | 0.6% |
| Doctor stoppage | 1 | 0.2% |
| Corner stoppage | 1 | 0.2% |

Underdog win rates in the same sample were 52.0% at 0-2 OVR, 35.1% at 3-5 OVR, and 24.7% at 6-8 OVR. This is the correct direction: a close contest is volatile, but the favourite's chance rises with a real ability gap.

## Next Engine Target

Medical/corner stoppages are now in a credible range. The remaining calibration work is to shift some competitive TKOs into earned submissions and KOs through ground-position, submission-chain, and sustained-strike mechanics. That should be audited by fighter tier and style matchup, not by overwriting result categories.
