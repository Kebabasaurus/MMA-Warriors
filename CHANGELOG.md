# Changelog

## Unreleased - Matt-Dev

### Fight Excitement

- Fixed AI and regional cards scoring about fourteen points more exciting than the player's for no gameplay reason. Those paths passed raw combined popularity as promotional heat while player cards passed the real hype value, so the same fight scored 66 on an AI show and 53 on yours. Every caller now uses one scale, and the gap measures zero.
- Rebalanced the metric so the fight decides the score rather than the poster. Promotional heat was roughly three-quarters of the number: who was fighting moved it more than what they did, which sent Fight of the Night to the biggest names instead of the best fight. Heat now contributes about a fifth, and the bout itself drives 61% of the variation, up from 43%.
- Fixed a finish scoring worse than going the distance. Later rounds paid up to fifteen points while a knockout or submission paid twelve, so a five-round decision outscored a first-round knockout. Finishes now score eighteen and beat decisions by fourteen points on average.
- Removed round number as a driver of excitement entirely. A fight is exciting or it is not, and when it ends does not change that.
- The score now reads what actually happened in the cage instead of inferring it. Knockdowns, submission attempts, significant strikes landed per round, and how two-way the exchanges were all feed the number, using stats the fight engine already produced but nothing consumed. A back-and-forth war and a one-sided shutout no longer score the same.
- Halved the even-matchup bonus, which sat at 15 or 16 of a possible 16 on almost every bout and acted as a flat offset rather than telling good fights from bad ones.
- Recalibrated every threshold that reads excitement to the range real cards actually produce. Event grades of A and B required 78 and 64, above the highest score a card average could ever reach, so no show in the game could earn either; meanwhile the median card graded F and failed the owner-goal excitement check outright. Grades now run A at 53, B at 49, C at 44 and D at 40, producing a normal spread of 7% A, 21% B, 47% C, 21% D and 5% F.
- The owner-goal excitement gate now passes 82% of cards instead of either all or almost none, so it rewards a good show without being a formality.
- Retuned the fanbase reaction to the top and bottom fifth of card averages, and the technical-crowd bonus to a level a card can actually reach; both previously sat above the maximum and never triggered.
- Separated the per-fight bonus labels from the event-level bands. Individual bouts spread far wider than card averages, so Fight Night now flags roughly the top sixth of bouts as bonus contenders rather than reusing an event threshold no single fight was measured against.

### Build & Tests

- Fixed the portable build aborting before it reached PyInstaller. `Build Portable.bat` gates on the smoke test, which failed on every run with `AttributeError: 'FightEmpireApp' object has no attribute 'city_box'`: management screens build lazily when first opened, and the event-booking city check read a booking widget roughly two hundred lines before that screen was built. The test now opens the booking screen before reading from it, and repopulates its fighter table afterwards so later checks see the current roster.
- Made the Matchmaking click-selection check tolerate a display that cannot lay out the fighter table. It drove clicks through real pixel coordinates, which do not exist when the booking pane is never mapped on a headless or minimised build machine. The full assertions still run wherever Tk lays the table out; elsewhere the test reports the skip explicitly and still exercises the underlying selection logic, instead of failing a build for an environment limit.
- Raised the youth-market batch assertion to match the larger combat sport intake.

### Starting Database

- Brought every real fighter over 42 in the starting database down to their prime age, so a new world opens with recognisable names competing rather than retiring. Twenty-seven athletes were affected, including Bobby Lashley (50 to 30), Chael Sonnen (49 to 31), Vitor Belfort (49 to 27), Brock Lesnar (48 to 28) and Holly Holm (44 to 31). Each new age comes from the database's own convention of prime start plus three, so every fighter lands inside their authored prime window with ratings, records and profiles untouched.

### Combat Sports (Child Promotions)

- Opening a combat sport division now asks for confirmation first. Selecting a sport and pressing the manage button launched the promotion immediately and spent the $120,000 startup investment with no prompt; the dialog now states the cost, your cash after launch, that the promotion starts with no athletes, and that it cannot be undone. Insufficient funds are reported before anything is charged.
- Added a combat sport free-agent market, kept entirely separate from the MMA free-agent pool. Established athletes aged 22 to 33 arrive with real records, ratings and popularity, so a division can be staffed with competitors who are ready now rather than only teenagers.
- Fixed thin hiring markets. The signable pool targeted four athletes per division, capped additions at twelve per refresh, and only ever generated 18- and 19-year-olds — across roughly twenty divisions per sport that left many showing a single name or none. The youth target was raised and the free-agent pool added alongside it.
- Fixed a per-pass intake cap that left over half of Boxing's thirty-four gender and weight combinations short of four prospects however many times the market refreshed. Launching a division, or refreshing its market, now fills every division to its full target in a single pass instead of a fixed batch, while normal two-monthly replenishment stays paced. Every division of every combat sport now opens with six youth prospects and three established free agents per gender.
- Added contract terms for combat sport athletes. Signings previously set no contract length at all, so athletes could never expire, be renewed, or be negotiated with.
- Added negotiation to sport signings and renewals: a contract dialog shows the athlete's expected purse and term, lets you set both, and offers a Test Reaction check before sending. Athletes accept, hold out for closer terms, or reject outright based on their rating, popularity and age, with prospects favouring long deals and established names favouring short ones.
- Sport contracts now count down monthly and raise inbox warnings at three, two and one month, plus an expiry notice when a deal lapses.
- Added a Combat Sports tab to the Contracts screen listing every child-promotion athlete with sport, division, rating, time remaining and purse, using the same red/orange/yellow expiry highlighting as the MMA roster, with Negotiate Renewal and Release Athlete actions and a per-bout payroll total.

### Regional Titles & Lineage

- Fixed regional belts changing hands in ordinary development bouts. The championship flag was matched on the *division* rather than on the reserved contenders, so once a circuit booked a title fight every other bout in that division on the same card was flagged a championship too — and each one ran the crowning routine. The belt ended up on whoever won the last development bout of the night instead of the actual title contest, changed hands on cards where no title fight was scheduled, and left the real champion competing in bouts that were never recognised as defences. Championship status now matches the specific reserved pairing.
- Verified across 96 simulated feeder cards (390 bouts): divisions carrying more than one championship bout on a card went from roughly ten per month to zero, and reigning champions placed into non-title bouts went to zero.
- Added a TITLE LINEAGE panel to the fighter profile listing every championship event in a career — inaugural reigns, crownings, defences, and vacancies — across every promotion the fighter has competed for. The profile previously showed a single line and only for a *reigning* champion, so a vacated or lost title vanished from the fighter's record entirely; 156 vacated championships in the reference career were invisible.

### Title Fights & Booking Conflicts

- Fixed a scheduled title fight silently losing its champion, and with it the championship on the fighter's record. The double-booking repair that runs on every save load resolved clashes purely by date, so an ordinary undercard booking made a week earlier would win the fighter and the champion was quietly replaced with a TBA in their own title defence — leaving a belt advertised in a bout the champion never appeared in, an unrelated free agent signed into the empty corner on fight night, and the champion's record showing the other, non-title bout instead. Championship bouts now claim their fighters first regardless of date.
- A bout that still loses a fighter to a booking clash now has its championship sanction removed rather than continuing to advertise a belt nobody present can win, and the downgrade is announced in the news feed and the inbox.
- Interim status is now recomputed for title fights that survive a booking repair, instead of keeping whatever was true when the bout was first booked.
- Fixed any bout still holding a TBA slot skipping the weigh-in completely. Weigh-ins ran before the opponent was resolved, so neither corner was ever weighed: no scale weight was recorded, a missed weight could not be detected, and a blown cut could never downgrade a title bout to a catchweight non-title contest. A 240 lb fighter could contest a 155 lb championship without ever stepping on the scale. TBA opponents are now signed before the weigh-in, and the whole existing weight-miss, fine, and commission-removal pipeline applies to them normally.

### Fight Night

- Fixed the fight-log corner read always reporting an 8-week camp for both fighters. It read `red_camp` / `blue_camp` / `camp_weeks` from the booking dictionary, keys nothing has ever written, so every bout fell through to the hardcoded default and hid the real preparation — including short-notice replacements who had no camp at all. It now reads the fighter's actual camp length, matching the corner read already used elsewhere in the engine.

### Fighter Weight & Division Fit

**Root cause fix — walk weight was decided before the division was.**

- Fixed walk weight being derived from a randomly rolled division inside the fighter generator and then left stale when the caller overwrote the fighter's division. A fighter built as a heavyweight could be seeded straight into flyweight and keep a 295 lb frame, cutting 169 lb every camp and sitting permanently pinned at the maximum weigh-in penalty. This affected 13% of every world (43% of all regional-feeder fighters).
- Added a `weight` parameter to regional-feeder fighter creation so the division is known at build time instead of being patched on afterwards, and updated the initial feeder roster build and the monthly regional youth intake to pass it.
- Added `assign_fighter_division()` as the single supported way to change a fighter's division, so the frame and the class can no longer silently disagree.
- Added `plausible_walk_weight_band()`, derived from the same limit and spread constants as the fighter generator so the builder and the validator cannot drift apart again.
- Added `repair_walk_weight_for_division()`, which pulls an impossible frame back into its division's believable band and reports how far out it was.

**Save repair for existing careers.**

- Extended the division-frame migration to repair frames in both directions against each division's plausible band, rather than only the undersized tail, and bumped its version so careers created before this fix are repaired on load.
- The repair message now reports oversized and undersized counts separately along with the worst mismatch found.
- On the reference career this reset 861 frames (790 far too heavy for their class, 71 far too light; worst mismatch 148 lb) and refreshed division-fit ratings across the roster.

**Division moves.**

- Fixed the move-up path never checking whether a fighter could make the target weight. It measured frame fit only, so a 227 lb featherweight was waved into lightweight as an "undersized" move — he could not make 155 lb either, and moving up one class does not fix a frame that belongs three classes higher. Both directions now check cut feasibility.
- Fixed division-fit penalty messages blaming the wrong cause. The penalty is the sum of two independent terms — a frame that is light for the class, and a naturally small build — but the text hardcoded the walk-weight explanation, telling players a 227 lb lightweight's "walk weight is light for Lightweight" when every point came from his build. Messages now name the term that actually produced the penalty.
- Added `division_size_penalty_parts()` and `division_fit_reason()`; `division_size_penalty_for()` is now a thin wrapper over them so all callers stay consistent.
- A completed division move now carries the fighter's real frame across intact and only repairs it when it was never credible for either division.
- Made the closed-division roster reassignment generic to any promotion rather than one company, and made it move fighters to the nearest still-open division for their gender instead of a hardcoded Welterweight — dropping a heavyweight into welterweight moved them ninety pounds and left a frame that fitted neither.

**Acclimatisation.**

- Kept growing into a division as the loose, common path: a fighter competing above their natural size fills out toward the class over months, and the division-fit penalty eases as they do.
- Added the reverse path so an oversized fighter can recompose down toward their division, but only when the body allows it — cutting skill, conditioning, a smaller natural build and youth all gate it, at roughly half the speed and a third of the frequency of growing. Large-framed, poor-cutting or older fighters stay where they are and are steered toward a move up instead.
- Acclimatisation now runs on fighters carrying no penalty but an oversized frame, which the previous penalty-gated check skipped entirely.

**Tracking.**

- Added a per-fighter `division_fit_log` recording every acclimatisation step with date, division, walk weight, direction and resulting division fit, retained for the last 24 entries and persisted with the career.
- Added a DIVISION ACCLIMATION panel to the fighter profile showing the recent trail and the net frame change over it.
- The profile's Walk Weight row now shows the difference against the division limit, and a new Camp Cut row shows how much the fighter has to lose to make weight.

**Measured effect on the reference career:** every division's frames now sit inside their plausible band (0 out of band, previously 793 fighters more than 25 lb over their limit); newly generated feeder fighters are correct at birth (0 of 400 out of band, previously 252 of 400); with a normal eight-week camp 1,968 of 2,000 fighters make weight on a 10 lb median cut and a median penalty of 0; and the annual division review still applies about one move per promotion per year.

## 3.0.5 - 2026-07-31

### Fight Night Audio

- Added a 0-100 volume slider directly to the live Fight Night viewer; changes take effect on the next cue, persist with the career, and share the same normalized setting as Game Settings.
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

- Made ordinary Matchmaking row clicks toggle fighters into or out of the current selection, so players can build pairs and tournament groups without keyboard modifiers; double-click still opens the fighter under the pointer, and the persistent Matchup Insight summary explains the interaction.
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
