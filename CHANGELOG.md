# Changelog

## 3.0.4 - 2026-07-30

### Championship Integrity

- Fixed regional champions being booked in ordinary development bouts between title defenses. Regional titleholders now only compete when the belt is on the line; if no suitable challenger is ready, they sit out.
- Added a regression scenario covering the regional title-defense cadence and title-history flags.
- Reworked late-career decline so it tapers after meaningful losses from a fighter's peak rather than reducing long-serving veterans into implausibly low-rated active fighters.
- Retirement reviews now account for the ability a fighter has lost from their career peak, while a hard review at age 46 prevents indefinitely active veterans.

### Interface Accessibility

- Rebuilt shared notebook-tab states across all 24 themes with WCAG AA text contrast, a minimum 3:1 selected-surface change, larger labels, and redundant outline/elevation cues for the current tab.
- Added automated per-theme contrast checks and a documented tab palette/state guide.
- The main game window now opens maximized, while retaining its responsive fallback geometry for smaller displays and test environments.

## 3.0.2 - 2026-07-30

### Database Editor And Universe Data

- Rebuilt the fighter Skills tab as an all-skill sheet: each of the 67 individual attributes has a direct labelled 1-99 slider and numeric input, grouped by fighting discipline.
- Added live Current OVR, Suggested OVR, and difference readouts; database authors can apply the entire sheet, synchronize broad core ratings, or use the calculated suggested OVR.
- Authored exact opening detailed skills, career archetypes, Prime Start, and Prime End values for every seeded MMA fighter. The Database Editor and future new games now use the same values.
- Clarified `prime_age` as an optional legend-age override. Normal fighters now display their actual Prime Start and Prime End values and blank optional overrides no longer block edits.
- Hardened seed record lookup so same-name curated variants on different promotions keep their own authored profile rather than accidentally borrowing another variant's values.
- Added a hidden-Tk editor acceptance audit that exercises all database field controls, all 67 skill sliders, skill-sheet persistence, and authored prime windows without saving the database.

## 3.0.1 - 2026-07-30

### Hotfixes

- Fixed the shipped Universe Database Editor failing at startup because its window title referenced an undefined `GAME_TITLE` constant.

## 3.0.0 - 2026-07-30

### Highlights

- Expanded MMA finish logic with a much larger set of submissions, technical submissions, striking stoppages, TKO outcomes, and context-aware broadcast commentary.
- Improved watched-card pacing and fight-night presentation, including complete-card end handling, keyboard arrow navigation, and broader visual theme support.
- Made booking calendar-aware with named event days, recovery and camp time measured in days, and better AI contender availability and scheduling.
- Added player-directed scouting goals, recommendation controls, randomized starting scouts for custom companies, and stronger stat-driven scouting results.
- Added fighter career journeys: academy homegrown-title aims, veteran final runs, discipline and weight-management support, camp-fit work, and champion retention pressure.
- Consolidated the starting universe into one editable database file and shipped the MMA Warriors Universe Database Editor with safer selectors, copying, validation, filters, sorting, and constrained inputs.
- Improved UI responsiveness and dense-screen usability across rankings, profiles, editor tools, themes, and varied desktop resolutions.
- Reworked AI promotion financial stability and simulation efficiency while preserving save compatibility and the existing finance protections.

### Compatibility

- Existing career saves remain supported. New fields have load-time defaults and repair paths where needed.
- The distributed universe database is `Databases\\Default Universe.universe.json`; active saves remain separate and are never edited by the database editor.
