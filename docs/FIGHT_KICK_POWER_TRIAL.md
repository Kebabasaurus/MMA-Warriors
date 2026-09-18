# Kick-power trial — 6 September 2026

The default-off `--kick-power` candidate scales resolved kick power by 1% immediately
before the existing kick contest. It composes with the retained 2% standing head-damage
change. Kick type/target selection, kick frequency, punch/body/leg damage, non-kick
actions and RNG calls are unchanged.

## Full calibration result

On the frozen 3,840-bout corpus, the combined head-damage + kick-power candidate records:

- 2,292 overall finishes
- 603 KO, 736 TKO
- 1,387 competitive finishes / 2,880 = 48.16%
- no full-calibration failures

This clears the exact 48% competitive floor and the approved middle-timing advisory.
The preceding head-damage-only candidate was 1,382 competitive finishes (47.99%), so
the kick adjustment adds five competitive finishes in this combined run.

## Remaining release blockers

The 300-bout coverage report still records 25 unused active IDs and 25.66% top-ten
concentration. The overall distinct-move mean remains advisory. These content gates,
plus the separately known historical fixture-hash regression, still prevent release.
The kick-power change is therefore retained as an experimental candidate, not enabled
in normal play or packaged in the EXE.

Reports: `analysis/standing_head_plus_kick_1pct_calibration.json` and
`analysis/standing_head_plus_kick_1pct_coverage.json`. Focused kick scope/parity tests
pass; `git diff --check` is clean apart from normal CRLF conversion warnings. The AST
instrumentation fails closed if the kick-margin assignment structure changes, and no
extra simulation pass or random draw was introduced.
