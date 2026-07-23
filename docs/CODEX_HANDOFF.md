# MMA Warriors Codex Handoff

Last updated: 2026-07-19

This is a working handoff for continuing MMA Warriors in a fresh Codex session on another machine. It is a curated project summary, not a verbatim chat transcript.

## Start Here

Open the project folder and ask the new agent to read, in order:

1. `AGENTS.md`
2. `CODEX_HANDOFF.md` (this file)
3. `README.md`

Suggested first message:

> Read AGENTS.md and CODEX_HANDOFF.md. Continue MMA Warriors as a Windows desktop MMA promotion-management simulator. Preserve save compatibility, work in the existing modular architecture, and run smoke tests before changing core systems.

## Project Location and Delivery

- Source project (current machine): `D:\CodexFILES\MMA Warriors`
- Main source entry point: `main.py`
- Packaged game: `dist\MMA Warriors\MMA Warriors.exe`
- Runtime data folders: `Saves\`, `Databases\`
- Build output is intentionally only the current `dist\MMA Warriors` folder.

The packaged EXE was rebuilt and startup-tested on 2026-07-19 after the custom-promotion
roster draft, event-date matchmaking, and grouped-save work. Close `MMA Warriors.exe`
before rebuilding and preserve packaged `Saves`, `Databases`, and `Logs`.

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

Core competitive promotions are BAMMA, UFC, PFL, ONE, RIZIN, KSW, Cage Warriors, LFA,
Oktagon, BRAVE, ACA, PRIDE, Strikeforce, and WEC. The expanded feeder network covers
Japan, the UK, North America, Europe, Asia, Brazil, Latin America, Canada, Oceania,
Africa, the US Midwest, the Nordic region, Korea, South America, and Britain.

## Important Recent Work

### July 18-19: starting mode, matchmaking, and saves

- `Create Your Own Promotion` now launches a proper setup and roster-draft flow. The
  player chooses active genders/weights, scale, philosophy, theme, roster depth, and a
  Balanced/Star Led/Prospect Heavy allocation strategy.
- Custom divisions target 8, 10, or 12 fighters. The interactive draft enforces a hard
  six-fighter viability floor in every active division and a scale/division-based annual
  contract budget. Automatic selection reserves every division's complete baseline before
  spending extra on stars, avoiding the old three-fighter and last-division starvation bugs.
- The test save that exposed the problem was a local men's promotion with eight active
  weights and only three fighters in each. Existing saves are not rewritten; the improved
  allocation applies to newly created promotions.
- Closed custom divisions now survive save/load, AI handoff, and later takeover. AI
  recruitment/champion repair respects them. Free-agent rows say `DIVISION CLOSED`
  rather than the ambiguous `CLOSED`, and explain how to reopen the division.
- Matchmaking status is now based on the selected event date. Month/year/week changes
  refresh the list, `Ready` means ready for that card, and `All` shows exact return dates.
  Recovery conflicts use an in-game notice instead of a surprise Windows popup.
- Save slots can be grouped in-game. Root slots are the `Main` folder; user folders live at
  `Saves\Folders\<Folder>\<Slot>`. The Game Menu can create folders, filter the list, and
  move a complete slot (including backups, autosaves, and snapshots) into `Tests` or another
  group. `active_save_group` is serialized with the career.
- Fighter rows in core roster, contract, matchmaking, and free-agent views use durable
  fighter IDs, avoiding duplicate-name Treeview collisions. Ranking maps also use identity.

### World and roster simulation

- AI card construction now de-duplicates fighters and rejects any card that books a fighter twice.
- Independent/free-agent showcase bouts now impose a three-month per-fighter layoff, increasing rotation.
- Auto-renew exists on the contracts screen and uses morale, role, potential, reserve cash, and payroll checks.
- Popularity changes are contextual: stakes, finish, upset, rivalry, previous popularity, and inactivity all matter.
- Promotions have weekly finance history; event revenues/costs and monthly overhead are tracked.
- AI roster demand now scales by promotion size and thin divisions; renewal logic protects champions and necessary card depth without double-charging future purses at signing.
- Distressed promotions still receive the requested buyout/cash injection and lose most fighters, but new ownership has a six-year protected rebuild with lender workouts instead of annual roster purges.
- Independent and overdue farewell bouts now complete retirement, including paired pending veterans and long-waiting medical clearances.
- Late worlds maintain an age-structured youth pipeline in thin divisions instead of relying only on a raw population floor.
- World news, inbox, results, and finance screens are more interactive than their original static versions.

### Fight engine

- Three judge cards are simulated with mildly different judging priorities: damage-first, balanced, and control-sensitive.
- Round scoring supports draws correctly; fight output includes cards and round detail.
- The calibration target is competitive matchmaking, not random mismatches. See the fight-engine section in `AGENTS.md` before tuning.
- Controlled competitive finish rates are approximately low 53%, mid 42%, high 42%, and realistic mixed cards 49%. Ordinary AI bouts are constrained to a six-point OVR gap; title/rivalry/retirement exceptions remain possible.
- Existing engine requirements: attributes should affect the relevant actions, stamina/momentum must matter, commentary cannot continue after a finish, and score totals must agree with the announced result.

### Fighters and development

- Fighters have career archetypes: Early Maturation, Balanced Development, Late Maturation, and Durable Career.
- Player profiles present an upside assessment and career stage rather than exposing a confusing exact "standard prime" label.
- Normal development is gated by prime window; durable careers get a small tail, while rare late resurgence remains possible.
- Generated fighters now randomize archetypes correctly and use age-aware starting ability, credible age-based record caps, and larger young-prospect potential gaps.
- Fighter profile/editor work has recently expanded to expose many career, body, market, contract, and relationship fields.

### UI and usability

- Results cards open a selectable bout viewer with full logs, fighter profile links, and individual free-agent negotiation actions.
- Inbox has state/type filtering, urgent/unread styling, contextual navigation, owner-goal tracking, and hiding of message types.
- Finance shows 48 weeks of opening balance, revenue, costs, net, and closing balance.
- World news uses a selectable story list/detail screen instead of one long text wall.
- Fighter profile stat meters use a dark value gutter, fixing white-on-white scores.
- Theme selector now includes branded looks for the full core-promotion roster, the child combat-sport worlds, and Sky Sports/ESPN/BBC Sport-inspired media views.
- The player closes/reopens MMA divisions through one **Manage Divisions** popup with its own gender/weight selectors. It shows roster, booked-purse, and payroll impact before closure. Closed divisions release their roster, vacate titles, remove booked bouts, are hidden from roster/Matchmaking dropdowns, and can be reopened for free. Their released free agents remain visible with an amber `DIVISION CLOSED` highlight and an eligibility explanation.
- Free-agent scouting visibility is now a persistent setting under **Game & Saves → Game Settings**, not a checkbox on the market. New games default to scouting required; exact market information is hidden until scouted. Existing saves retain their recorded choice.

### Academy and child combat-sport promotions

- The player academy is one shared development system. It can promote graduates into MMA or any opened child sport (BJJ, Boxing, Kickboxing, Muay Thai, Wrestling, etc.). It is not a separate academy per sport.
- Academy networks take eight weeks to establish, only one may be active at once, and leads are generated weekly until the live shortlist cap of eight. Leads expire after 2–3 weeks.
- Academy prospects arrive aged 12–15, with 30–60 current rating. Potential is normally 60–98; 99–100 generational prospects are deliberately very rare and need a strong scout plus academy reputation. Pros can be promoted from age 16; 16–17 requires an explicit early-debut confirmation.
- Opening a sport creates an empty branded child promotion such as `BAMMA BJJ` (or `UFC BJJ` when UFC is the parent). The player signs athletes, selects two roster members, adds manual bouts to **Your Booked Card**, runs the card, and can watch its replay. Smart Card remains an optional automatic shortcut. Child-promotion startup/signing/card finances feed into parent cash while retaining separate division revenue/cost/history tracking.
- Non-MMA sport classes are repaired for every athlete during save load. Older saves stored MMA placeholders (for example Tyson Fury as Bantamweight with no `sport_weight_class`); the migration restores the real sport-specific class before any combat-sport UI is opened.

## Known Follow-up Work

These are intentional next tasks, not reasons to undo recent work.

1. **Old-save normalization:** legacy fighters can still carry the internal archetype string `Standard Prime`. The profile translates it, but a save-repair migration would clean the data.
2. **Finance completeness:** weekly history captures event and overhead flows, but some direct cash actions may not yet be recorded as transactions.
3. **Inbox preferences:** hidden mail types currently work during the running session but have not been verified as serialized into saves.
4. **Extreme-horizon audit:** the 30-year play-level audit is complete; a future overnight 100-year audit can validate the new youth/retirement equilibrium beyond three generations.
5. **UI sweep:** highest-value interactive upgrades are Companies, Regions, Personal Assistant, Staff/Scouting, and the Chronicle. Many links now exist, but these still contain static information surfaces.
6. **Child-promotion scheduling:** player child promotions now support manual booked cards and smart cards, but they run immediately rather than being put on the parent-style future event calendar.
7. **Native-dialog cleanup:** routine matchmaking recovery and several academy/scouting
   decisions have moved into game surfaces, but older validation, delete confirmation, and
   fight-day flows still use Tk message boxes. Replace them opportunistically with inline or
   themed decisions; keep modal confirmation for destructive actions.
8. **Grouped-save edge audit:** Main-to-folder creation/move/filter paths are tested. When
   changing backup, restore, delete, crash-recovery, or decade-snapshot code, explicitly test
   both `Saves\<Slot>` and `Saves\Folders\<Folder>\<Slot>` layouts.

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
& "C:\Users\Tanks\AppData\Local\Programs\Python\Python313\python.exe" -m PyInstaller --noconfirm --clean --distpath ".\output_current" --workpath ".\build_current" ".\MMA Warriors.spec"
```

Copy the built EXE and `_internal` directory into the existing `dist\MMA Warriors`
package without replacing `Saves`, `Databases`, or `Logs`. Start the packaged EXE briefly
as a final sanity check and confirm no new crash report appears.

## Transfer Checklist

Copy the complete `MMA Warriors` project folder to the laptop, including:

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

- The 2026-07-19 player-experience pass added an actionable weekly command centre,
  attributed MMA development profiles, inline medical decisions, unscouted contract
  talks with hidden ratings, and a substantial watched Fight Night presentation pass.
- `smoke_test.py` passes with exact development-factor parity and a regression check
  that opens contract talks for a genuinely unscouted free agent.
- The broader responsiveness suite reached 2.14s on its spectator-batch UI guard
  (threshold 2.0s); no gameplay or persistence assertion failed before that guard.

- `smoke_test.py` passed on 2026-07-19 after custom-promotion draft, event-date
  availability, grouped saves, and closed-division wording changes.
- The roster-allocation matrix passed for Local, Regional, and National starts under all
  three draft strategies. Each tested three-division roster received exactly eight fighters
  per division and remained inside its annual commitment budget.
- The interactive draft was opened and completed through its real Tk UI; the test roster
  contained eight fighters and remained inside budget.
- A targeted matchmaking test moved a fighter's return to Mar W3 2026, verified that an
  earlier event displayed `Available Mar W3 2026`, then verified `Ready` on that date.
- A temporary save was moved physically from Main to Tests, disappeared under a Main-only
  filter, and appeared under Tests.
- The three-seed stability playtest passed through Month 4 with 104-114 recorded events.
- The child-sport weight audit passed against new data plus legacy source and packaged saves: all 270 mapped real athletes resolve to their recorded Boxing/Kickboxing/Muay Thai/Lethwei/Wrestling/BJJ classes.
- AI duplicate-booking stress tests passed across competitive promotions.
- Fight judge-card variance and draw handling were smoke-tested.
- The latest EXE at `dist\MMA Warriors\MMA Warriors.exe` was rebuilt and startup-tested on
  2026-07-19. It remained running for the startup probe and produced no new crash report.
