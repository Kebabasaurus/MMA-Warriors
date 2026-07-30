# Changelog

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
