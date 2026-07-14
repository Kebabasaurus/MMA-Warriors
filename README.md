# MMA Warriors

A desktop MMA promotion management game about building a fight company, booking events, negotiating contracts, developing fighters, and competing with rival promotions.

## Run The Game

Double-click:

```text
Launch MMA Warriors.bat
```

Or run directly:

```powershell
C:\Users\Tanks\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe "D:\CodexFILES\MMA Warriors\main.py"
```

The packaged EXE has no Python requirement. Keep the whole `MMA Warriors` folder together and run it from a normal local folder, not from inside a ZIP archive. The game stores quick saves, save slots, databases, and logs beside the app when that folder is writable. If it is installed in a protected folder such as `Program Files`, it automatically uses `%LOCALAPPDATA%\MMA Warriors` instead.

Quick saves are atomic and retain one previous version as `savegame.previous.json`. Runtime diagnostics live in `Logs\mma_warriors.log`; unexpected failures create a separate report in `Logs\Crashes` and a timestamped emergency save in `Saves`.

Before moving a build to another laptop, run `Portable Check.bat` from the packaged folder. It confirms that the EXE is present and tells you whether runtime data will be stored beside it or in the user profile fallback.

## Smoke Test

Before shipping a build, run:

```text
Run Smoke Tests.bat
```

The test launcher runs both `smoke_test.py` and `stability_test.py`. The smoke test checks startup, core promotions, roster sizes, gyms, save/load serialization, and fight simulation. The stability playtest additionally completes normal and retirement events, opens every major UI viewer, tests isolated academy and child-sport matchmaking, round-trips a progressed world through JSON, and advances several independent worlds while watching for Tk callback errors.

For a reproducible 500-fight commentary, metrics, and finish-distribution report, run:

```text
python fight_text_audit.py
```

It writes `fight_text_500_audit_latest.txt` beside the game without changing saves or careers.

The current development model is documented in `FIGHTER_DEVELOPMENT_GUIDE.md`; current clinch, cage, ground, and damage mechanics are documented in `FIGHT_DAMAGE_AND_CLINCH_AUDIT.md`.

## Build A Portable Windows Version

Run:

```text
Build Portable.bat
```

The script runs smoke tests first, installs PyInstaller if needed, then creates:

```text
dist\MMA Warriors\MMA Warriors.exe
```

Close the packaged game before rebuilding. The build script preserves packaged `Saves`, `Databases`, and `Logs` in a staging backup and restores them after PyInstaller replaces the folder.

## Current Core Features

- Play as BAMMA and compete against UFC, PFL, ONE Championship, RIZIN, KSW, Cage Warriors, LFA, Oktagon MMA, BRAVE Combat Federation, and ACA.
- Switch control to another promotion through the company screen.
- Start a Spectator Mode save to hand BAMMA to the AI, fast-forward the living world by week, month, year, or a chosen date, and watch any promotion's latest card in the live fight-night viewer before taking control of a company.
- Book main cards, prelims, early prelims, title fights, and TBA fights.
- Schedule shows by month and week, then watch or instantly simulate them.
- Fight-night viewer with play-by-play, a tale-of-the-tape scoreboard, a live round-by-round score, colour-coded knockdowns and finishes, auto-play, round time, scorecards, skip controls, and post-event bonuses.
- End-of-year awards (Fighter, Fight, Knockout, Submission, Prospect, Veteran, and Promotion of the Year) crowned automatically each January, with a browsable awards history.
- A living world where fighters age a year each season, prospects break out, veterans decline, title contenders emerge on win streaks, and busy regions grow.
- Regional feeder circuits where 16+ prospects build records, develop, graduate to free agency, and can return to stay active; AI promotions scout them through budgeted, stealable contract offers.
- Player-built Fighting Academy with regional scouting networks, reports that become more accurate while leads are observed, prospect dedication/coachability/confidence, academy philosophies, individual training focus and intensity, full-engine amateur showcases with watchable replays, graduation-readiness guidance, MMA or child-sport pathways, finances, reputation, milestones, and persistent alumni careers.
- Detailed fight engine using striking, wrestling, grappling, clinch, physical, mental, stamina, momentum, traits, morale, camps, and fight context.
- Playable Boxing, Kickboxing, Muay Thai/Lethwei, Wrestling, and Brazilian Jiu-Jitsu child divisions with AI promotions, smart cards, titles, finances, sport-specific development, and paced live replays. Their bouts use the same camp, gym, morale, motivation, fatigue, weight-cut, trait, damage, injury, and medical-recovery foundation as MMA while retaining sport-specific rules and skills.
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
- Fighter development, aging, retirement, unretirement flow, morale, injuries, fatigue, weight cuts, traits, rivalries, and media callouts.
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
