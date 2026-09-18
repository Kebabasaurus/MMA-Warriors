# Fight Night presentation overhaul

The live viewer now gives the action timeline the main reading area, with a compact
matchup header and separate Card, Round Read and Bout Desk panels. Portraits render
at 136px normally and 104px below 700px window height. Existing portrait identities
and rendering rules are unchanged.

## Reading and navigation

- Round headings and official results have stronger visual emphasis; complete
  round summaries use quieter analysis styling.
- Timestamped actions have hanging indentation and paragraph spacing. The helper
  preserves supplied text, adding only a missing terminal newline.
- Impact, control and threat have paired visual bars alongside the numeric table.
  They use only telemetry already presented during playback.
- Secondary reading, speed, audio and replay shortcuts live in Playback Settings.
  Core playback and skip controls remain visible.
- The event archive shares the timeline styling, adds scrollbars and keeps bout
  and round selections independent. Detailed commentary remains available.

## Preservation boundaries

No fight mechanics, RNG draws, archived commentary, round analysis or save schemas
are changed by this presentation work. Existing density modes retain their existing
behavior. Switching modes cannot reveal commentary beyond the presented frontier;
official judge totals remain sealed until the result. Existing skip confirmations,
completion gates, audio handling and failed-commit retry behavior remain in place.

No EXE is rebuilt and no user save is edited. Preview screenshots use an isolated
viewer, synthetic fighters and explicitly illustrative commentary, not Testing V2.

## Verification

The presentation, archive, layout and existing Fight Night experience suites cover
text preservation, independent selection, sealed playback, responsive portraits,
multiple themes and the actual 820x540 live viewer. Audio, window-lifecycle, smoke
and stability suites provide additional integration checks.

On 8 September 2026 all eight selected integration suites passed: presentation,
archive, layout, Fight Night experience, audio, window lifecycle, smoke and
stability. The smoke suite retained one display-limited matchmaking-layout skip.
Stability completed all three seeded world loops through Month 4. The four focused
Fight Night suites were rerun successfully after the final summary-style adjustment.

Generate preview images with `py -3 analysis/preview_fight_night.py`. The actual
viewer captures are `analysis/ui_previews/fight_night_live_preview.png` and
`analysis/ui_previews/fight_night_live_preview_compact.png`.

An additional direct run of `fighter_portrait_regression_test.py` on 8 September
2026 passed 46 of 50 tests. Four failures concern the existing ranked-cohort review
image size, Max Holloway contact-sheet pixels, Conor McGregor override expectations
and shipped identity-manifest hash. The Fight Night change does not edit these
catalogue definitions, reference assets or expected fingerprints. These failures
remain unresolved; the broader portrait suite must not be described as passing.
