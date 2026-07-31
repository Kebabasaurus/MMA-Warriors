# Changelog

## 3.0.5 - 2026-07-31

### Fight Night Audio

- Added and integrated a 36-file crowd-audio pack, edited and mastered from licensed real field recordings, with three distinct variants for each of 12 pre-fight, live-fight, finish, and decision trigger families.
- Fight Night now rotates non-repeating variants for arena buildup, walkouts, opening roars, clean strikes, knockdowns, submission danger, inactivity, round endings, finishes, decision tension, split-card boos, and respectful post-fight applause.
- Playback honors the manifest's per-cue gain, limits simultaneous reactions and repeat frequency so commentary stays clear, and falls back to the existing procedural cues when an asset or playback service is unavailable.
- Hometown fighters now receive the strongest audible crowd lift, while national, adopted-home, and training-base appearances receive smaller nearby-market boosts; the Fight Night introduction identifies the active local connection.
- Included source and license documentation, a reproducible mastering tool, and a cue manifest with suggested triggers, loop capability, duration, playback gain, and provenance.
- Reduced the clean-strike vocal reaction by 3 dB and attenuated the gasp layer inside the knockdown roar so short crowd exclamations no longer overpower the broader arena response.
- Preserved every accepted revised-pack mix as Variant 1 and added alternate-source Variants 2 and 3, including modern large-stadium ambience, goal eruptions, hockey outrage, group gasps, boos, cheers, and applause.

### World Locations

- Added Belleville and Kingston, Ontario to Canada's event-city and generated-fighter hometown pool.
- Updated Brett Akey's authored hometown from the province-level Ontario label to Belleville.

### Fight Night Commentary

- Fixed long five-round fights occasionally losing late-round introductions, transitions, summaries, or action commentary when the fight log exceeded its global line limit.
- Replaced global fight-log truncation with per-round commentary compaction that preserves the opening and closing exchanges while always retaining round boundaries, finishes, scorecards, recaps, and fight metrics.
- Applied the fix to both championship fights and non-title five-round main events.
- Added regression coverage for full-distance title and non-title main events, commentary bounds, and a final-tick Round 5 stoppage.

### Interface Polish

- Replaced the low-contrast grey progress treatment with high-contrast loading bars and distinct red/blue fight freshness bars on a dark track.
- Reworked the top status bar so long promotion names use the flexible space available in maximized windows, while popularity, stability, cash, date, and advance controls remain separate and fully readable.
- Added a modal, themed loading panel with phase and progress feedback for Quick Load and Save Manager slot loads, including recovery-snapshot attempts, so large careers no longer appear frozen while their world state and screens are rebuilt.
- Rebuilt Mail / Decisions discoverability with explicit Owner Goals collapse/expand controls, persistent goal summaries, filter-aware message counts, a one-click Show All action, selection guidance, and responsive side-by-side/stacked panels.
- Reworked Add Show / Matchmaking so Show Details keeps a labelled toggle and status summary, the Current Fight Card remains visible beside fighters or above them on narrow windows, and an instructional empty-card state explains the booking flow.
- Compacted expanded Show Details into two control rows and one shared schedule/broadcast status row on wide screens, with medium and narrow layouts that safely stack the same fields, actions, and forecasts instead of clipping them.
- Consolidated fight-card hype, build, fatigue, and medical-return values into one visible booking-information column, eliminating the page-level horizontal scroll that previously hid the card while preserving the complete 20-column fighter table and its own labelled table scrollbar.
- Gave Available Fighters focused Essentials, Readiness, and Form & Fitness table views plus an All 20 view, preserving every scouting metric while making the default Matchmaking workspace easier to scan.
- Reclaimed fighter-table height with a compact, persistent Matchup Insight disclosure and alerts that only occupy space when they contain actionable text; matchup history, booking context, and the row-colour guide remain available through the labelled Expand control.
- Added a Compare Selected action that opens the existing full side-by-side fighter comparison directly from Matchmaking; all five booking actions use one row on wide fighter panes and a safe two-row grid at narrow widths.
- Shortened the fighter-table view cue so it stays on one line while its tooltip retains the full list of available scouting and readiness metrics.
- Fixed vertical splitters locking to the smaller pre-maximized startup height. Mail / Decisions now also reserves a 425-pixel top pane and a fixed two-row action grid, guaranteeing that all eight Inbox buttons appear at startup even if the sash begins at its minimum; later player adjustments remain preserved.
- Removed the full-width `NEW HERE?` alerts. Concise guidance remains beside Inbox counts, Message Detail, the fighter-column cue, and the empty fight card without consuming the vertical space needed by tables and actions.
- Added responsive layout and sash-startup regressions, full inbox-filter reset coverage, and per-theme contrast checks for the remaining inline discovery cues.

### Contract Negotiations

- Rebalanced free-agent contract evaluation so base purse and annualized compensation matter more than raw contract length.
- Added compensation-gated diminishing returns for contract security through 48 months; longer terms provide no additional signing advantage.
- Enforced the negotiation system's 60-month contract limit even when a player manually enters a higher value.
- Added regression coverage for minimum-pay long-term offers, competitively paid contracts, low-cost prospects, and the duration cap.

### Interface Accessibility

- Rebuilt shared notebook-tab states across all 24 themes with WCAG AA text contrast, a minimum 3:1 selected-surface change, larger labels, and redundant outline/elevation cues for the current tab.
- Added automated per-theme contrast checks and a documented tab palette/state guide.
- The main game window now opens maximized, while retaining its responsive fallback geometry for smaller displays and test environments.

### Developer Workflow

- Made synchronized `CHANGELOG.md`, `README.md`, and `AGENTS.md` updates a required part of every implementation improvement or fix.
- Required focused regression coverage for behavior changes, with documented reproducible manual verification only when reliable automation is not practical.
- Added smoke coverage that keeps runtime version metadata and the documented change contract synchronized across the project guides.
- Corrected the README build instructions to distinguish the portable game build from the separately validated Database Editor build.

## 3.0.4 - 2026-07-30

### Veteran Career Integrity

- Reworked late-career decline so it tapers after meaningful losses from a fighter's peak rather than reducing long-serving veterans into implausibly low-rated active fighters.
- Retirement reviews now account for the ability a fighter has lost from their career peak, while a hard review at age 46 prevents indefinitely active veterans.

## 3.0.3 - 2026-07-30

### Regional Championship Booking

- Fixed regional champions being booked in ordinary development bouts between title defenses. Regional titleholders now only compete when the belt is on the line; if no suitable challenger is ready, they sit out.
- Ranked vacant-title participants and defending challengers by divisional merit instead of promoting whichever ordinary development pairing happened to be drawn first.
- Preserved championship stakes in feeder-promotion fight logs so fighter histories correctly identify title bouts.
- Added regression coverage for champion-only defenses, title cadence, contender selection, and archived title flags.

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
