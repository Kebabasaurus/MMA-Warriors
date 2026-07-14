# MMA Warriors Codex Handoff

Last updated: 2026-07-12

This is a working handoff for continuing MMA Warriors in a fresh Codex session on another machine. It is a curated project summary, not a verbatim chat transcript.

## Start Here

Open the project folder and ask the new agent to read, in order:

1. `AGENTS.md`
2. `CODEX_HANDOFF.md` (this file)
3. `README.md`

Suggested first message:

> Read AGENTS.md and CODEX_HANDOFF.md. Continue MMA Warriors as a Windows desktop MMA promotion-management simulator. Preserve save compatibility, work in the existing modular architecture, and run smoke tests before changing core systems.

## Project Location and Delivery

- Source project: `D:\CodexFILES\MMA Warriors`
- Main source entry point: `main.py`
- Packaged game: `dist\MMA Warriors\MMA Warriors.exe`
- Runtime data folders: `Saves\`, `Databases\`
- Build output is intentionally only the current `dist\MMA Warriors` folder.

The source has a few newer edits than the currently packaged EXE. Before treating the EXE as the current build, run the smoke test and package it again. Close `MMA Warriors.exe` first: `Build Portable.bat` now detects an open package and preserves packaged runtime data across the rebuild.

## Architecture

The old single-file app has been split into mixins composed by `FightEmpireApp` in `main.py`:

- `constants.py`: paths, regions, names, skill constants, camps.
- `models.py`: `Fighter`, `Gym`, and `Promotion` dataclasses.
- `ui.py`: all Tkinter tab construction, themes, sorting widgets.
- `views.py`: refresh logic, profiles, rankings, contracts, finance, editor, results viewers.
- `events.py`: booking, weigh-ins, fight-night viewing, negotiations, event payouts.
- `fight_engine.py`: action resolution, commentary, scoring, stoppages.
- `world.py`: calendar, AI promotions, aging/development, gyms, market, finance, retirement.
- `seeding.py`: real/generated fighters, companies, regions, gyms, promotion data.
- `persistence.py`: save/load, world serialization, databases, save slots.
- `admin.py`: Sim Lab, rules, belt and engine tools.
- `awards.py`: season tracking and year-end awards.

Use the module that owns a behavior. Do not recreate a giant `main.py`.

## Current Product Direction

The intended game is a deep, dark, playable WMMA-style business and world simulation:

- Start with a promotion, run cards, sign fighters, negotiate, manage finances and media.
- Other promotions book, sign, pay, develop, and compete in the same world.
- Regional feeders develop young fighters and struggling veterans.
- Fights resolve through mechanics and attributes, never post-result fudging.
- The UI should be data-rich, readable, linked, and game-like rather than a wall of static text.

Core competitive promotions are BAMMA, UFC, PFL, ONE, RIZIN, KSW, Cage Warriors, LFA, Oktagon, BRAVE, and ACA. Feeder promotions exist as non-player regional circuits.

## Important Recent Work

### World and roster simulation

- AI card construction now de-duplicates fighters and rejects any card that books a fighter twice.
- Independent/free-agent showcase bouts now impose a three-month per-fighter layoff, increasing rotation.
- Auto-renew exists on the contracts screen and uses morale, role, potential, reserve cash, and payroll checks.
- Popularity changes are contextual: stakes, finish, upset, rivalry, previous popularity, and inactivity all matter.
- Promotions have weekly finance history; event revenues/costs and monthly overhead are tracked.
- World news, inbox, results, and finance screens are more interactive than their original static versions.

### Fight engine

- Three judge cards are simulated with mildly different judging priorities: damage-first, balanced, and control-sensitive.
- Round scoring supports draws correctly; fight output includes cards and round detail.
- The calibration target is competitive matchmaking, not random mismatches. See the fight-engine section in `AGENTS.md` before tuning.
- Existing engine requirements: attributes should affect the relevant actions, stamina/momentum must matter, commentary cannot continue after a finish, and score totals must agree with the announced result.

### Fighters and development

- Fighters have career archetypes: Early Maturation, Balanced Development, Late Maturation, and Durable Career.
- Player profiles present an upside assessment and career stage rather than exposing a confusing exact "standard prime" label.
- Normal development is gated by prime window; durable careers get a small tail, while rare late resurgence remains possible.
- Generated fighters now randomize archetypes correctly. Before the fix, they were effectively all balanced.
- Fighter profile/editor work has recently expanded to expose many career, body, market, contract, and relationship fields.

### UI and usability

- Results cards open a selectable bout viewer with full logs, fighter profile links, and individual free-agent negotiation actions.
- Inbox has state/type filtering, urgent/unread styling, contextual navigation, owner-goal tracking, and hiding of message types.
- Finance shows 48 weeks of opening balance, revenue, costs, net, and closing balance.
- World news uses a selectable story list/detail screen instead of one long text wall.
- Fighter profile stat meters use a dark value gutter, fixing white-on-white scores.

## Known Follow-up Work

These are intentional next tasks, not reasons to undo recent work.

1. **Development tuning:** career archetypes now work but feel too subtle in long tests. Young generated fighters can also debut too highly rated. Make early/late/durable paths more visible without making growth deterministic or forcing decline.
2. **Old-save normalization:** legacy fighters can still carry the internal archetype string `Standard Prime`. The profile translates it, but a save-repair migration would clean the data.
3. **Finance completeness:** weekly history captures event and overhead flows, but some direct cash actions may not yet be recorded as transactions.
4. **Inbox preferences:** hidden mail types currently work during the running session but have not been verified as serialized into saves.
5. **Long-run audit:** run a fresh 100- and 200-year audit after recent AI-card, feeder, retirement, and showcase changes. Earlier audits exposed too-high long-term company reputation, title/Hall-of-Fame counts, and weak late-world free-agent throughput.
6. **UI sweep:** highest-value interactive upgrades are Companies, Regions, Personal Assistant, Staff/Scouting, and the Chronicle. Many links now exist, but these still contain static information surfaces.
7. **Fresh build:** recent result-card negotiation and database-editor field additions were syntax-checked, but the portable EXE should be rebuilt after a full smoke test.

## Testing and Build

Use the bundled Python path from `AGENTS.md` when it exists on the machine. On a new laptop, use the project Python environment or a compatible Python installation with PyInstaller.

Compile:

```powershell
python -m py_compile main.py smoke_test.py
```

Smoke test:

```powershell
python smoke_test.py
```

Build:

```powershell
python -m PyInstaller --noconfirm --windowed --name "MMA Warriors" --distpath ".\dist" --workpath ".\build" --specpath ".\build" ".\main.py"
```

After building, ensure `dist\MMA Warriors\Saves` and `dist\MMA Warriors\Databases` exist, then copy `README.md` into the same packaged folder. Start `dist\MMA Warriors\MMA Warriors.exe` briefly as a final sanity check.

## Transfer Checklist

Copy the complete `D:\CodexFILES\MMA Warriors` project folder to the laptop, including:

- All `.py`, `.bat`, `.md`, and asset files.
- `Saves\` and `Databases\` if you want current saves/custom databases.
- `Logs\` if you want historical runtime and crash diagnostics.
- `dist\MMA Warriors\` if you want the currently packaged playable build.

Do not rely on copying `build\` as a source of truth; it is disposable PyInstaller output. Keep a separate backup of `Saves\` before testing migration or long simulations. The portable folder is used for data when writable; a protected install automatically redirects runtime data to `%LOCALAPPDATA%\MMA Warriors`.

Run `Portable Check.bat` in the packaged folder after transfer. It verifies the EXE is present and reports whether the portable folder itself is writable.

## Guardrails for the Next Agent

- Never delete or overwrite user saves as part of a code change.
- Keep old saves loadable by adding dataclass defaults and repair paths.
- Do not tune fight results by overwriting outcomes. Adjust the actual engine factors and audit representative matchmaking.
- Do not add duplicate fighters across companies except deliberate younger-variant labels.
- Maintain sex- and weight-class-safe matchmaking, rivalries, rankings, and titles.
- Favor real fighters for roster depth, but use diverse localized generated names where needed.
- Avoid light/white UI surfaces with white text. All dense screens should be sortable/filterable where appropriate.
- Build and launch the EXE after meaningful core changes.
- Preserve timestamped crash reports and crash autosaves; they are diagnostic evidence, not disposable game output.

## Recent Verification Snapshot

- `smoke_test.py` passed after the inbox, finance, world-news, auto-renew, and showcase changes.
- AI duplicate-booking stress tests passed across competitive promotions.
- Fight judge-card variance and draw handling were smoke-tested.
- The latest database-editor field expansion was `py_compile` checked; rerun the full smoke test before release packaging.
