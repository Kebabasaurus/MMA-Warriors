# Lost Features + Multisport Access Guide

This file records the features that were lost or rolled back during the shipping-folder cleanup recovery, plus a guide for accessing the multisport system that still exists in the current source.

## July 14 repair pass

The missing systems listed below have now been rebuilt into the source and packaged exe again: academy scouting/network/development/UI, child combat-sport strategy/finance/card recap polish, finance clarity, long-run audit tables/export/warnings, fight-night readability, AI company strategy visibility, market scouting panel, distressed buyout recovery, and late-era world replenishment.

The sections below are kept as a recovery checklist/history plus the multisport access guide.

## Recovery status

The current source was restored from `Backups/MMA_Warriors_20260713_085215`, then the most critical safe fixes were reapplied:

- player event log-tab crash fix
- AI distressed promotion buyout instead of promotion deletion
- late-era world replenishment safety check
- smoke test updated for the buyout behavior

The July 14 packaged exe that contained the very latest source state was not recoverable. The remaining `_internal` folder did not contain the Python app archive, and the current exe file itself was gone.

## Features known to be lost or rolled back

### Academy deep scouting/network system

Lost from the current source:

- User-funded academy starting at max 8 prospects.
- Regional scouting network setup.
- Scouting network cancellation.
- 2-month setup timer for each new scouting network.
- Region-specific prospect generation based on chosen scouting region.
- Distance-based scouting cost from company HQ/player region.
- Distance-based signing cost.
- Weekly recruitment list.
- Prospects appearing for a limited 2-3 week signing window.
- Leads being lost if not signed in time.
- Scout quality affecting report accuracy.
- Scout confidence percentage.
- Current rating range display, e.g. `42-51`.
- Potential ability range display, e.g. `82-97`.
- High-potential prospects costing more to sign.
- Blue-chip academy signing cost tuning.
- Player hiring/choosing scout to set up the network.
- Scout name/skill stored on the active network.
- `last_scout_report` style network status messaging.

### Academy development depth

Lost from the current source:

- Proper bi-weekly academy cards.
- Academy cards using all eligible pairable prospects.
- Full amateur bout simulation through the fight engine-style flow.
- Amateur bouts directly improving development.
- More detailed development gains from fight method/win/loss.
- Automatic training using weak spots/style fit.
- Manual focus system with recommended focus.
- Sport-specific academy focuses feeding naturally into child sport rosters.
- Prospect fatigue/injury handling around academy cards.
- Academy card recap popup.
- Academy development visibility beyond basic rating/week progression.
- Clearer progression graph/readout.
- Individual prospect profile window.
- Amateur history viewer.
- Recommended focus hint in prospect list/profile.
- Scout accuracy visibly affecting reports.
- Graduation to player-owned combat sport divisions.
- Sport identity on academy sport graduates.
- Unique-name handling for academy graduates into sport rosters.
- Academy graduate history into sport crossover history.
- 18+ pro graduation lock/tuning.

### Academy UI polish

Lost from the current source:

- Scrollable/deeper academy UI.
- Talent lead list with signing costs and expiry.
- Network status line showing active/building/cancelled network.
- Region/scout selectors for network setup.
- Cancel network button.
- Prospect profile/history button.
- Academy card recap popup.
- Recommended focus display.
- More detailed prospect row including development, injuries, ratings, and amateur record.
- Destination selector for graduating to MMA or an opened child sport.

### Finance clarity/UI additions

Lost or rolled back from the current source:

- Expanded finance forecast line.
- Upcoming payroll summary.
- Academy monthly cost forecast.
- Sport division lifetime net included in finance summary.
- Medical expected cost forecast.
- Media/sponsor expected income per event line.
- Child sport unrecovered setup/card cost display in the finance screen.

### Long-run audit upgrades

Lost or rolled back from the current source:

- Balance warnings section in play audit results.
- Yearly health table with defunct count, average cash, minimum cash, sport cards, and academy size.
- Roster population by gender.
- Roster population by weight/gender.
- Company financial health table.
- Combat sport impact section.
- Export Results button for play audit reports.
- Scrollbars in the play audit results window.
- Academy/multisport impact reporting over time.

### Combat sport/player division polish

The core multisport system survived, but these later polish pieces may be missing or partially rolled back:

- Player child sport strategy selector: Balanced / Prospect Builder / Star Showcase / Title Focus.
- Sport-specific player title name field such as `BAMMA Boxing Championship`.
- Player sport division lifetime revenue/cost/net display.
- Player sport card recap popup.
- Sport card finance summary popup.
- Athlete development/trend column in child sport roster.
- Richer latest-event recap text.
- More developed child division strategy impact on target bout count.

### Fight-night presentation polish

Lost or rolled back from the current source:

- Live fight read/status line.
- Corner/fatigue/morale/camp indicator line in event result output.
- Stronger scorecard visual tagging.
- Cleaner fight-list completion marker.
- Some newer finish/readability display improvements.

### AI company strategy visibility

Lost or rolled back from the current source:

- Company profile `AI STRATEGY READ` section.
- Financial pressure label.
- Prospect/star roster tilt.
- Explanation of why the AI company is booking/signing that way.
- Clearer strategy identity/current direction presentation.

### Free-agent scouting UI polish

Lost or rolled back from the current source:

- Free-agent scouting read side panel.
- Selected market fighter detail helper.
- Basic/full scout report UI.
- Scouting confidence text on free-agent profiles.
- Rival offer/action recommendation text.
- Cleaner market scouting summary.

### Packaging/shipping cleanup state

Current package was rebuilt and launches, but it is based on restored July 13 source plus reconstructed critical fixes. It should be considered a recovered build, not the full July 14 feature-complete build.

## Features that survived

### Multisport/combat sports

These are present in the current source:

- Combat sports universe window.
- Sports seeded:
  - Boxing
  - Kickboxing
  - Muay Thai
  - Wrestling
  - Brazilian Jiu-Jitsu
- Lethwei legends are included inside the Muay Thai world.
- Real combat sport roster data exists in `seeding.py`.
- AI sport promotions exist for each sport.
- Sport rosters are saved/loaded.
- Sport athletes have `sport_employer`.
- AI sport cards run.
- Player can open child sport divisions.
- Player child sport divisions can run cards.
- Player can sign athletes from the flagship sport promotion.
- Combat sport rankings exist.
- Combat sport development exists.
- Rare combat sport crossover into MMA exists.

### Academy basic version

These are present in the current source:

- Fighting Academy window.
- User can open academy for cash.
- Academy has level/capacity/weekly cost.
- Talent pool exists.
- Prospects list exists.
- Basic auto training exists.
- Basic plan cycling exists.
- Manual amateur bout exists.
- Basic amateur history exists.
- Promotion to MMA roster exists.
- Academy save/load exists.

## How to access multisport in-game

### Open the Combat Sports Universe

1. Launch the game.
2. Go to the `World` screen from the left navigation.
3. Use the `Combat Sports` button.
4. This opens the `Combat Sports Universe` window.

### What you will see

The Combat Sports window lists each available sport world. Each sport has:

- sport name
- flagship AI promotion
- champion
- roster size
- latest media/event notes

Available sport worlds should include:

- Boxing
- Kickboxing
- Muay Thai
- Wrestling
- Brazilian Jiu-Jitsu

Muay Thai also includes Lethwei legends/athletes as part of that world.

### Open a player child division

1. Open `World`.
2. Click `Combat Sports`.
3. Select a sport from the list.
4. Click the option to open/take a player division.
5. The game charges the startup cost.
6. A group of athletes from that sport joins your player-owned child division.

The player child division is treated as part of the MMA business umbrella, not a separate player company.

### Run a player sport card

1. Open `World`.
2. Click `Combat Sports`.
3. Select a sport where you already opened a player division.
4. Open that division.
5. Use `Run Smart Card`.

The system builds a sport-specific card from your signed athletes and applies results to their records/rankings.

### Sign sport athletes

1. Open the player child division window for the sport.
2. Look at the signable flagship athletes list.
3. Select an athlete.
4. Use `Sign Selected`.

This buys/signs the athlete from the sport's main AI promotion into your child division if you have enough cash.

### Where sport cards/results are stored

Combat sport worlds live in:

- `self.combat_sport_worlds`

Player child divisions live in:

- `self.player_combat_divisions`

Save/load support is in:

- `persistence.py`

Sport seeding/real athlete data is in:

- `seeding.py`

Sport simulation/card/development logic is mostly in:

- `world.py`

Sport UI is mostly in:

- `views.py`

## How to access the current academy

1. Launch the game.
2. Go to the `Staff` screen.
3. Click `Fighting Academy`.
4. If you do not own one, accept the purchase prompt.

Current academy controls include:

- `Sign Selected Talent`
- `Cycle Training Plan`
- `Run Amateur Bout`
- `Promote to Pro`
- `Upgrade Capacity (+2)`

Important: this is the older/basic academy version. It does not currently include the deeper scouting network/recruitment system listed above.

## Recommended rebuild priority

If rebuilding lost features, recommended order:

1. Restore academy scouting network and signing windows.
2. Restore bi-weekly academy cards that use all eligible prospects.
3. Restore academy prospect profile/history/recommended focus UI.
4. Restore academy graduation to child sport rosters.
5. Restore finance forecast and child sport finance summaries.
6. Restore play-audit export/warnings/tables.
7. Restore AI strategy visibility in company profiles.
8. Restore fight-night presentation polish.
