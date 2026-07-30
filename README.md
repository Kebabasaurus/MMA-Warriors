# MMA Warriors

MMA Warriors is a deep Windows desktop promotion-management simulation. Choose any real-world-inspired promotion, take control of an existing company, or create a new one from scratch. Build a roster, negotiate contracts and transfer deals, book cards, develop prospects, manage finances and media, and try to turn a regional operation into the sport's defining brand.

Every career lives inside a persistent MMA world. Fighters age, improve or decline, move between promotions, chase titles, suffer injuries, join gyms, build rivalries, and eventually retire. Rival companies sign athletes, run events, spend money, and pursue their own identities, so your decisions reshape a living competitive landscape instead of a static roster.

## Run The Game

Double-click:

```text
Launch MMA Warriors.bat
```

Or run directly:

```powershell
python main.py
```

The packaged EXE has no Python requirement. Keep the whole `MMA Warriors` folder together and run it from a normal local folder, not from inside a ZIP archive. The game stores quick saves, save slots, databases, and logs beside the app when that folder is writable. If it is installed in a protected folder such as `Program Files`, it automatically uses `%LOCALAPPDATA%\MMA Warriors` instead.

The shipped starting universe is one editable file: `Databases\Default Universe.universe.json`. It contains MMA fighters, combat-sport athletes, companies, media, and regions. Cloned custom universes are separate files created only when the player makes one.

`MMA Warriors Database Editor.exe` ships beside the game EXE. It is a developer-facing editor for universe files, with a database selector, browse/copy-current/save/save-as workflow, automatic backups, validation, bulk fighter/company changes, and per-record JSON editing. It edits starting databases only, never an active career save.

Each game now owns a self-contained folder, for example `Saves\Game 1\savegame.json`. Its two rolling recovery backups, autosaves, crash recovery files, and spectator archives stay inside that same `Game 1` folder, so multiple careers cannot overwrite one another. Autosaves use the same two-slot rolling policy per cadence, overwriting the oldest snapshot instead of accumulating files. Spectator Mode also writes a permanent archive at every completed decade, such as `Game 1 - 10 Years.json.gz`, under `Saves\Game 1\Snapshots`. Existing flat saves remain loadable and move to the folder layout the next time they are saved. Runtime diagnostics live in `Logs\mma_warriors.log`; unexpected failures create a separate report in `Logs\Crashes`.

Before moving a build to another laptop, run `Portable Check.bat` from the packaged folder. It confirms that the EXE is present and tells you whether runtime data will be stored beside it or in the user profile fallback.

Fight Night uses one live broadcast viewer for MMA, boxing, kickboxing, Muay Thai, wrestling, and Brazilian jiu-jitsu. Other-sport replays include sport-native round/period/match starts, clocked exchanges, cumulative scoring, stamina and condition reads, and an official result. The viewer is laptop-sized, has visible scrollbars, adjustable text size, a Follow live toggle, round/period navigation, and paced holds for round summaries and finishes.

Striking commentary uses action-specific situation banks rather than shared generic calls. Boxing, kickboxing, Muay Thai, Lethwei presentation, and MMA distinguish entries, counters, body work, leg damage, kick checks, pocket/clinch work, rope or fence pressure, defensive exits, knockdowns, cuts, and damage-aware follow-up attacks. Recent-line memory prevents the same broadcast template from cycling repeatedly during a watched fight.

## Smoke Test

Before shipping a build, run:

```text
Run Smoke Tests.bat
```

The test launcher runs `smoke_test.py`, `stability_test.py`, and `media_system_test.py`. The smoke test checks startup, core promotions, roster sizes, gyms, save/load serialization, and fight simulation. The stability playtest additionally completes normal and retirement events, verifies two-year retirement-card thresholds, popularity ordering, weight-safe matchmaking, weekly card caps and contract-expiry releases, opens every major UI viewer, exercises academy scouting, all-eligible showcase matchmaking, cooldowns, structured amateur history, adult-weight graduation, and child-sport pathways, round-trips a progressed world through JSON, and advances several independent worlds while watching for Tk callback errors. The media test covers editable outlets, player and AI offers/contracts, campaign limits, audience reporting, old-save migration, and a save/load round trip.

The current development model is documented in `FIGHTER_DEVELOPMENT_GUIDE.md`; current clinch, cage, ground, and damage mechanics are documented in `FIGHT_DAMAGE_AND_CLINCH_AUDIT.md`.

## Build A Portable Windows Version

Run:

```text
Build Portable.bat
```

The script runs smoke tests first, installs PyInstaller if needed, then creates:

```text
dist\MMA Warriors\MMA Warriors.exe
dist\MMA Warriors\MMA Warriors Database Editor.exe
```

Close the packaged game before rebuilding. The build script preserves packaged `Saves`, `Databases`, and `Logs` in a staging backup and restores them after PyInstaller replaces the folder.

## Current Core Features

- Choose any established promotion at the start of a career, including BAMMA, UFC, PFL, ONE Championship, RIZIN, KSW, Cage Warriors, LFA, Oktagon MMA, BRAVE Combat Federation, ACA, PRIDE Fighting Championships, Strikeforce, and World Extreme Cagefighting. You can also Create Your Own Promotion. The legacy promotions include prime-era legends such as Kimbo Slice, Kazushi Sakuraba, Gilbert Melendez, Cung Le, Miguel Torres, and more.
- Change control to another promotion through the company screen, or begin a custom-promotion career with its own region, scale, divisions, identity, and initial roster draft.
- Guide fighter career journeys from Roster > Career Goals: academy graduates can pursue a homegrown title, veterans can request a final run, troubled prospects can reset their habits or weight cut, camp fit can be rebuilt, and champions need real opponents, visibility, and contract security to stay invested.
- Start a Spectator Mode save to hand the selected player promotion to the AI, fast-forward the living world by week, month, year, or a chosen date, and watch any promotion's latest card in the live fight-night viewer before taking control of a company.
- Book main cards, prelims, early prelims, title fights, TBA fights, and career-affecting 4/8-fighter one-night MMA tournaments. Tournament entrants are seeded by rank, use the normal camp and weigh-in system, accumulate fatigue between rounds, can crown a champion in the final, and remain reserved from other bookings.
- Schedule shows by month and week, then watch or instantly simulate them.
- Advance from the persistent top bar; world simulation runs in responsive queued steps with live phase/progress feedback, guarded controls, and efficient batched spectator fast-forward.
- Fight-night viewer with play-by-play, a tale-of-the-tape scoreboard, live round-by-round scores, red/blue gas and condition bars, card progress and bout states, colour-coded knockdowns and finishes, auto-play, round timing, scorecards, skip controls, post-event bonuses, and live/completed tournament bracket viewing.
- End-of-year awards (Fighter, Fight, Knockout, Submission, Prospect, Veteran, and Promotion of the Year) crowned automatically each January, with a browsable awards history.
- A living world where fighters age a year each season, prospects break out, veterans decline, title contenders emerge on win streaks, and busy regions grow.
- Regional feeder circuits where 16+ prospects build records, develop, graduate to free agency, and can return to stay active; AI promotions scout them through budgeted, stealable contract offers.
- Player-built Fighting Academy with hired-scout regional networks that take eight weeks to establish, scout-quality-driven lead strength and report accuracy, and no fallback phantom scout. Only one network can be active, and its live recruitment list caps at eight leads. Prospects arrive aged 12–15 with 30–60 current rating; potential is normally 60–98, while 99–100 generational prospects are exceptionally rare. Pros can graduate from age 16 (16–17 requires an early-debut confirmation) into MMA or any open child-sport promotion. Every eligible prospect receives safely matched biweekly full-engine amateur bouts with cooldowns and suitable guest opponents.
- Playable Media Desk with a laptop-safe vertical layout: company media strategy, limited weekly campaign actions and fighter cooldowns, campaign risk/outcomes, public trust and buzz, contract offers, deal buyouts, delivery standards, outlet relationships, audience ratings/viewership, campaign history, a persistent editable outlet market, and direct Chronicle/news context. AI promotions negotiate, campaign, deliver, and renew through the same media-contract rules. Older headline-only saves and rights deals remain compatible.
- Detailed fight engine using striking, wrestling, grappling, clinch, physical, mental, stamina, momentum, traits, morale, camps, and fight context.
- Playable Boxing, Kickboxing, Muay Thai/Lethwei, Wrestling, and Brazilian Jiu-Jitsu child promotions with AI promotions, manual or smart cards, titles, finances, sport-specific development, and paced live replays. Opening one creates an empty branded promotion named for your chosen parent company, such as `UFC BJJ`: sign athletes, select two roster members, add a matchup to **Your Booked Card**, then run/watch the event. Child-promotion setup, signings, and card profit/loss feed into parent-company cash while also tracking their own revenue, costs and history. Native development follows each sport's own technical skill pool, potential ceiling and prime/decline curve; gym quality, facilities, fit, dedication, professionalism, morale, activity, fatigue and injury all affect progress. Child-promotion rosters and athlete profiles show a normalized Sport Rating, career stage, potential runway, 12-month trend and recent development instead of misleading MMA overall growth. BJJ playback tracks standing, guard, side-control, mount, and back-control ownership so takedowns, pulls, sweeps, passes, escapes, recoveries, and submission chains follow legal positional sequences; submission results now end on a visible winner-led tap sequence. Each circuit uses its own authentic weight ladder (including kg wrestling classes and IBJJF-style BJJ classes), with 270 real athletes seeded into career-appropriate prime divisions.
- Division Management is available from Roster. Closing a gender/weight division releases its athletes to free agency, vacates its belts and removes booked bouts; it can later be reopened for free. Closed divisions are removed from roster and Matchmaking selectors but their free agents remain visible and highlighted. Free-agent information visibility is controlled persistently in **Game & Saves → Game Settings**; new games require scouting reports by default.
- Expanded style identities including Dutch kickboxing, Taekwondo, Sanda, freestyle and catch wrestling, Luta Livre, and submission grappling; styles influence action selection and matchup context.
- Shared weight-management model across live cards, AI cards, and the Simulation Lab: walking weight, natural size, cutting skill, camp length, camp quality, scale weight, missed weight, and cut penalties all affect the bout. Player fighters can only change division when their body can credibly make the move.
- Simulation Lab with gender and weight-class filters, side-by-side fighter scouting cards, full profile access, one-off fight watching, engine audits, and sandbox 4/8/16-fighter tournaments that never alter careers or saves.
- Fighter profiles with portraits, nationality, records, rankings, detailed skill sheets, camp info, morale, annual overall peaks, and fight history.
- Curated real-fighter profiles with deterministic ratings, real fighting styles, career-appropriate traits, and one-time migration for older saves; see `REAL_FIGHTER_RATING_AUDIT.md`.
- Company and world rankings by gender, division, company, and worldwide scope.
- Contracts, bidding wars, exclusive/non-exclusive deals, market churn, and AI signings.
- Rival AI promotions run shows, manage budgets, sign fighters, and produce event histories.
- World regions with cities, local popularity, economy, drug-testing accuracy, venues, and promotional benefits.
- Gym system with quality, facilities, reputation, morale, specialties, capacity, scouting, camp development, and a gym viewer.
- Fighter development, aging, retirement, unretirement flow, morale, injuries, fatigue, weight cuts, traits, rivalries, and media callouts. Promotions do not renew declared retirees at contract expiry; retirement-pending free agents can receive ordinary showcase bouts, while a two-year queue of at least ten pairable veterans creates a popularity-ordered independent retirement card. Cards stay within gender/weight classes, carry at most 12 bouts, and are capped at two in one week even under a severe backlog.
- Staff market, scouting assignments, drug testing, post-show bonuses, inbox decisions, owner goals, finance ledger, broadcasters, and rules editor.
- Full database editor with searchable world roster, fighter identity/combat/contract editing, promotion/free-agent transfers, retirement, editable detailed fight attributes, save slots, database export/load, searchable results, and event replay archive.

## Shipping Checklist

1. Run `Run Smoke Tests.bat` and confirm both the smoke and stability playtests pass.
2. Start the game from `Launch MMA Warriors.bat`.
3. Confirm the Game Menu company picker shows every listed promotion once, including Oktagon MMA, BRAVE Combat Federation, and ACA.
4. Schedule a small event for the current week and simulate it.
5. Save, close, relaunch, and load the save.
6. Run `Build Portable.bat` for the distributable exe.
7. On the target laptop, extract/copy the complete `dist\MMA Warriors` folder to a local writable location, then launch `MMA Warriors.exe` once before moving across any existing saves.
