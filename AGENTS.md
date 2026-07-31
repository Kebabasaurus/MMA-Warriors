# MMA Warriors AI Developer Guide

This file is for coding agents working on MMA Warriors. Read it before editing.

## Multi-Agent Collaboration

Multi-agent delegation and parallel agent work are explicitly enabled for this project.
Agents may spawn sub-agents whenever independent investigation, implementation, review, or
testing work can be performed safely in parallel. Keep delegated tasks focused, coordinate
shared-file edits, and have the primary agent integrate and verify the final result.

## Approval Policy

Do not ask for approval before performing ordinary, in-scope development actions. Proceed
autonomously with reading, editing, testing, building, and other reversible project work.
Ask the user only when essential information is missing or an action would materially expand
the requested scope, affect external systems or people, or be destructive and irreversible.

## Project Goal

MMA Warriors is a desktop MMA promotion management sim. The target feel is a deep WMMA-style world: promotions compete, fighters age and develop, gyms matter, contracts and morale matter, and fight simulation produces believable MMA results without fudging outcomes.

The game should remain:

- A shippable Windows desktop game.
- A deep business/world simulation, not a web app.
- Dark, readable, game-like, and not cluttered.
- Data-rich, but navigable.

Current working source path: `D:\CodexFILES\MMA Warriors`.
Current packaged game: `D:\CodexFILES\MMA Warriors\dist\MMA Warriors\MMA Warriors.exe`.

## Important Files

The app was split from one large `main.py` into flat sibling modules. `FightEmpireApp`
is assembled from mixin classes (one per module) so cross-cutting `self.x()` calls keep
working with no behaviour change. All modules live beside `main.py` so `Path(__file__)`
save-path anchoring is unchanged.

- `main.py` - Entry point. Imports the mixins, defines `class FightEmpireApp(*mixins)`, holds `__init__`, and the `if __name__ == "__main__"` launcher.
- `constants.py` - Module constants and path anchors (`APP_DIR`, `SAVE_FILE`, `SAVE_DIR`, `DATABASE_DIR`, weights, regions, skill lists, names, camps).
- `models.py` - `Fighter`, `Gym`, `Promotion` dataclasses (imports `DETAILED_SKILL_GROUPS`).
- `ui.py` - `UIMixin`: theme, layout, tree sorting, all `build_*_tab` builders.
- `admin.py` - `AdminMixin`: sim-lab runs, engine settings, belts, champions, name cleaning.
- `seeding.py` - `SeedMixin`: `seed_*`, real/expanded fighter data, generation, `infer_gender`/`infer_nationality`.
- `views.py` - `ViewMixin`: `refresh_*` screens, fighter/company/region/gym profiles, rankings, contracts, staff, finance, matchmaking helpers.
- `events.py` - `EventMixin`: scheduling, weigh-ins, live fight window, negotiations, `run_event`/`finish_event`, awards.
- `fight_engine.py` - `FightEngineMixin`: `simulate_fight` and all resolve/score/stoppage/`fight_phrase` helpers.
- `world.py` - `WorldMixin`: `apply_result`, elo, finance calc, `advance_month`, world week/month, aging, retirements, AI promotions, market churn.
- `persistence.py` - `PersistenceMixin`: `serialize_world`, `apply_world_data`, save/load, save slots, database import/export, crash handler, `take_control_*`, `new_game`.
- `awards.py` - `AwardsMixin`: end-of-year awards. A season tracker (`self.season_stats`) is fed by `record_season_result` from every decisive fight (player in `finish_event`, AI in `simulate_ai_promotion_month`). `run_end_of_year_awards` fires from `advance_month` at the year rollover (month 13, 25, ...) and stores results in `self.awards_history`.
- Each mixin module shares one import header (`from constants import *`, `from models import Fighter, Gym, Promotion`). Add a new method to whichever mixin fits its concern; a new global constant goes in `constants.py`.
- `main.original_backup_*.py` - Pre-split single-file backup (safe to delete once the split is trusted).
- `smoke_test.py` - Startup/serialization/fight simulation smoke test.
- `Launch MMA Warriors.bat` - Runs the game.
- `Run Smoke Tests.bat` - Runs `smoke_test.py`.
- `Build Portable.bat` - Builds `dist\MMA Warriors\MMA Warriors.exe` with PyInstaller.
- `README.md` - Player/build instructions.
- `savegame.json`, `Saves/`, `Databases/` - Runtime data. Do not delete user saves unless explicitly asked.
- `Logs/mma_warriors.log` - Rotating runtime log. `Logs/Crashes/` stores one timestamped report per unhandled error; crash autosaves are stored in the active slot's `Crash Recovery` folder.

## Required Commands

Use the bundled Python when possible:

```powershell
& "C:\Users\Tanks\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m py_compile "D:\CodexFILES\MMA Warriors\main.py" "D:\CodexFILES\MMA Warriors\smoke_test.py"
```

Run smoke tests:

```powershell
& "C:\Users\Tanks\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "D:\CodexFILES\MMA Warriors\smoke_test.py"
```

Build portable exe from the checked-in spec (use the local Python installation that has
PyInstaller; the bundled test runtime may not include it):

```powershell
& "C:\Users\Tanks\AppData\Local\Programs\Python\Python313\python.exe" -m PyInstaller --noconfirm --clean --distpath "D:\CodexFILES\MMA Warriors\output_current" --workpath "D:\CodexFILES\MMA Warriors\build_current" "D:\CodexFILES\MMA Warriors\MMA Warriors.spec"
```

Copy the resulting EXE and `_internal` tree into the existing
`dist\MMA Warriors` package. Preserve its runtime folders:

```text
dist\MMA Warriors\Saves
dist\MMA Warriors\Databases
dist\MMA Warriors\Logs
dist\MMA Warriors\README.md
```

## Architecture Map

Responsibilities by module (all mixins compose into `FightEmpireApp` in `main.py`):

- Dataclasses (`models.py`): `Fighter`, `Gym`, `Promotion`.
- UI builders (`ui.py`, `UIMixin`): `build_game_menu_tab`, `build_website_tab`,
  `build_assistant_tab`, `build_companies_tab`, `build_regions_tab`, `build_results_tab`,
  `build_company_editor_tab`, `build_inbox_tab`, `build_staff_tab`, `build_finance_tab`,
  `build_roster_tab`, `build_contracts_tab`, `build_booking_tab`, `build_market_tab`,
  `build_world_tab`, `build_rankings_tab`, `build_editor_tab`, `build_sim_lab_tab`,
  `build_log_tab`.
- Screen refresh + profiles (`views.py`, `ViewMixin`): the `refresh_*` methods and the
  profile/viewer windows.
- Data seeding (`seeding.py`, `SeedMixin`): `real_fighter_data`, `expanded_real_fighter_data`,
  `seed_roster`, `seed_free_agents`, `seed_promotions`, `seed_regions`, `seed_gyms`.
- Fight simulation (`fight_engine.py`, `FightEngineMixin`): `simulate_fight` and all
  resolve/score/stoppage/`fight_phrase` helpers.
- Event running + fight-night viewer (`events.py`, `EventMixin`): `run_event`,
  `finish_event`, `open_live_fight_window`, negotiations, weigh-ins.
- World simulation (`world.py`, `WorldMixin`): `process_world_week`,
  `generate_weekly_world_activity`, `simulate_gym_world_activity`, `process_world_month`,
  `simulate_ai_promotion_month`, `market_churn`.
- Save/load (`persistence.py`, `PersistenceMixin`): `serialize_world`, `apply_world_data`,
  `save_game`, and the save-slot/database functions.
- Belts, champions, name cleaning, sim-lab (`admin.py`, `AdminMixin`).
- End-of-year awards (`awards.py`, `AwardsMixin`): season tracking and award resolution.

The calendar runs 4 weeks per month; the year is `2026 + (self.month - 1) // 12`. A new
year begins when `self.month` rolls to 13, 25, ... — `advance_month` triggers end-of-year
awards and `age_world_one_year` (deterministic +1 aging) at that boundary.

## Current Core Promotions

The player starts as `BAMMA`. Rival promotions should include:

- `Ultimate Fighting Championship`
- `Professional Fighters League`
- `ONE Championship`
- `RIZIN Fighting Federation`
- `KSW`
- `Cage Warriors`
- `Legacy Fighting Alliance`
- `Oktagon MMA`
- `BRAVE Combat Federation`
- `Absolute Championship Akhmat`

Regional feeder promotions are also core world objects: `Japan Fight Circuit`, `UK Regional MMA`,
`North American Fighting League`, `European Challenge MMA`, `Asia Rising Championship`,
`Brazilian Combat Circuit`, `Latin American MMA League`, `Canadian Fight Alliance`,
`Oceania Combat League`, `African MMA Championship`, `Midwest Fight League`,
`Nordic Combat League`, `Korean Fighting Championship`, `South American Vale Tudo Circuit`,
and `British Fight League`. They have `is_regional_feeder=True`, no normal commercial
finance simulation, young-prospect generation, and development-card/pathway logic.

If adding/removing core promotions:

1. Update `expanded_real_fighter_data`.
2. Update `seed_promotions`.
3. Update `repair_core_promotions` so old saves heal.
4. Update `promotion_broadcasters`.
5. Update `smoke_test.py`.
6. Update `README.md`.

## Save Compatibility Rules

Do not break existing saves.

When adding new fields to `Fighter`, `Promotion`, `Gym`, or world dictionaries:

- Add defaults in the dataclass when possible.
- Add repair/default logic in `ensure_fighter_business_stats`, `apply_world_data`, or a focused repair function.
- Make old saves load without requiring manual migration.

Current path behavior:

- `APP_DIR` is derived from `__file__`, or from `sys.executable` when packaged.
- `DATA_DIR` uses `APP_DIR` when writable (portable behavior). If the executable is in a protected location, it falls back to `%LOCALAPPDATA%\MMA Warriors`.
- `SAVE_FILE`, `SAVE_DIR`, `DATABASE_DIR`, and `LOG_DIR` are anchored to `DATA_DIR`, never cwd-relative paths.
- Existing ungrouped careers live at `Saves\<Slot>\savegame.json` and are presented as
  the `Main` folder.
- User-created save folders live at `Saves\Folders\<Folder>\<Slot>\savegame.json`.
  `active_save_group` is serialized with the world. Backups, autosaves, snapshots, and
  crash recovery remain inside the owning slot and must move with it.
- Save discovery must use `primary_save_paths`, `save_slot_name_from_path`, and
  `save_slot_group_from_path`; do not reintroduce assumptions that every slot is exactly
  one directory below `SAVE_DIR`.

## New Promotion Starts

`Create New Promotion...` is a real starting mode, not an editor shortcut.

- The Starting Promotion dropdown is the sole entry point for established, custom, and
  Spectator Mode starts. Keep `Start New Game With Selected Promotion` as the only action
  button in that panel; do not restore a separate create-promotion shortcut.

- The player chooses region, scale, event philosophy, theme, genders, and active weights.
- New starts use viable roster targets of 8, 10, or 12 fighters per active division.
- The default is Men Only with Featherweight, Lightweight, and Welterweight selected;
  do not silently reopen every division.
- `Balanced`, `Star Led`, and `Prospect Heavy` alter automatic draft priorities.
- The manual initial-roster draft shows fighter profiles and annual contract commitment.
  Every active division must have at least six selected fighters and the total must remain
  within the scale/division-based budget.
- `auto_select_custom_roster` first reserves a complete affordable baseline for every
  selected division, then upgrades it according to strategy. Do not return to sequential
  spending that can starve the final weight class.
- Closed divisions must persist when the custom company is handed to AI, saved/loaded, or
  taken over later. Custom starts do not remove BAMMA; it becomes an AI promotion.

## Matchmaking Availability

The matchmaking roster is event-date aware.

- `fighter.status` describes current condition and is not sufficient for future booking.
- Use `fighter_booking_status(fighter, month, week)` and `fighter_available_for_date` for
  the selected event date.
- Changing event month, year, or week must refresh the available-fighter table immediately.
- The default `Ready` filter means ready for that event date. The `All` filter may display
  unavailable fighters with an exact return label such as `Available Mar W3 2026`.
- Routine booking conflicts should use the inline matchmaking notice. Avoid Windows
  message boxes for information already representable on the game screen.

## UI Rules

The user strongly dislikes unreadable/cluttered UI.

When editing UI:

- Avoid hard-coded white backgrounds.
- Use `self.colors["cream"]`, `self.colors["text"]`, etc.
- Keep dense database screens sortable and filterable.
- Add double-click profile/viewer behavior where natural.
- Do not add giant explanatory landing pages.
- Do not make text overlap. Keep buttons and badges stable in size.
- Prefer dark, game-like panels.
- Prefer inline status/decision areas over native Windows information popups. Reserve
  modal confirmation for destructive or genuinely blocking decisions.
- A label such as `CLOSED` is too ambiguous. Free agents in a player-disabled division
  display `DIVISION CLOSED`, and the detail panel explains `Roster > Manage Divisions`.

Known theme names:

- `Fight Night`
- `Classic Green`
- `Light Office`
- Promotion themes: `BAMMA`, `UFC`, `PFL`, `Cage Warriors`, `ONE Championship`, `RIZIN`, `KSW`, `LFA`, `Oktagon`, `BRAVE`, `ACA`
- Combat-sport themes: `Boxing`, `Kickboxing`, `Muay Thai`, `Wrestling`, `BJJ`
- Sports-media themes: `Sky Sports`, `ESPN`, `BBC Sport`

## Fight Engine Rules

The fight engine must use simulation factors, not result fudging.

Important design intent:

- Kicks should care about kick speed, power, technique, stamina, distance, and defense.
- Punches should care about hand speed, punch power, punch technique, head movement, guard, chin, and stamina.
- Grappling should care about takedowns, setup, sprawl, guard work, control, submissions, defense, stamina, and position.
- Stamina and momentum should visibly influence the fight.
- Commentary should not repeat impossible actions after a finish.
- Scorecards must produce draws when totals are equal.
- End-of-fight output should include rounds and scores.

If tuning outcomes, audit finish rates **by fighter tier**, not just an aggregate over a
random-paired pool. A pure random-pairing audit is misleading because it over-represents
skill mismatches (which finish easily). Real cards pair similar-tier fighters, so the
per-tier competitive finish rate is what the player actually experiences.

Current calibration target (competitive, same-tier fights):

- Low tier (ovr < 68): ~50-56% finishes
- Mid tier (ovr 68-80): ~32-42% finishes
- High tier (ovr >= 80): ~38-45% finishes

Best single metric: **realistic matchmaking** (pair fighters with an overall gap <= 6, across
all tiers). That mirrors real cards and should land close to real-life UFC rates:
Decision ~47%, KO ~16%, TKO ~15%, Submission ~19%, finishes ~52%. A pure random-pairing
"mixed pool" audit will read much more finish-heavy (subs/KOs ~25%+) because it over-samples
skill mismatches that never get booked in practice - do not tune to that number.

Historically the engine finished LESS as fighters got better (elite title fights went to
decision ~80% of the time) because damage scaled with the strike `margin` (near zero in an
even fight) while defensive stats and the KO threshold scaled up with skill. The fix boosted
`impact` scaling with raw power and flattened the KO-threshold growth, so competitive fights
finish believably. Aggregate finish rate over a mixed random pool now runs ~60-65% (inflated
by mismatches) — that is expected; do not "correct" it back toward a decision-heavy shape.

Do not simply overwrite the final method to hit these numbers. Tune probabilities and
simulation mechanics, then re-run the per-tier audit.

## World/Gym Rules

Gyms are first-class world objects.

Gym effects should consider:

- Quality
- Facilities
- Reputation
- Room morale
- Specialties
- Capacity/crowding
- Scouting
- Fighter style fit
- Fighter age/prime/potential/dedication

Gym viewer is accessible from the World Hub. If gym fields change, update:

- `Gym` dataclass
- `seed_gyms`
- `serialize_world`
- `apply_world_data`
- `refresh_world`
- `open_gym_viewer`
- `smoke_test.py` if core assumptions change

## Data Quality Rules

- Avoid duplicate fighters across companies unless intentionally labeled as a younger variant, e.g. `Tom Aspinall CW`.
- Do not create names with `2` suffixes.
- Keep male/female fighters correctly gendered.
- If adding women with names not in `FEMALE_FIRST_NAMES`, update `infer_gender`.
- Keep each company able to fill divisions and champions.
- Use real fighters where requested, but generated fighters are acceptable for depth.

## Shippability Checklist

Before finishing a meaningful change:

1. Run `py_compile`.
2. Run `smoke_test.py`.
3. If the change affects packaging or core runtime, run `Build Portable.bat` or the PyInstaller command.
4. Start the packaged exe briefly if you rebuilt it.
5. Update README/smoke tests when changing core world expectations.

## Common Pitfalls

- Do not edit saves destructively.
- Do not remove `repair_core_promotions`; it keeps older saves viable.
- Do not put BAMMA in `self.promotions` while it is the player company.
- Do not make save paths cwd-relative.
- Do not add pale hard-coded text panels.
- Do not add new core promotions without updating smoke tests.
- Do not rely on `Cage Empire`; old references are only backward compatibility guards.
- Avoid adding more tabs when an existing viewer/table can be improved.
- Do not use `fighter.status` to decide availability for a future event.
- Do not flatten grouped save paths back into `Saves\<Slot>` during load, move, backup,
  delete, snapshot, or quick-save work.
- Do not restore three-person custom divisions. Eight is the minimum normal target and six
  is the hard draft viability floor.

## Current Product Direction

Best next improvements:

- More readable fight-night pacing and presentation.
- Better AI scheduling logic so promotions avoid overbooking tired fighters.
- More finance tuning for gates/media rights by region and company reputation.
- More staff depth: contracts, poaching, development, and specialist scouting.
- More gym/camp stories and long-term development tracking.
- Keep feeder promotions as a prospect pathway, and retain budgeted AI offers rather than reverting to instant random signings.
- Better company identity/personality in AI booking.
- Spectator Mode is a real observer save: it promotes the former player company into `self.promotions`, persists `spectator_mode`, and should keep all fast-forward controls confined to the Game Menu observer panel.
- Weight cuts use `perform_weigh_in` for player events, AI cards, and sandbox fights. Do not add a separate shortcut calculation: camp length, body fit, cut skill, scale weight, and the resulting penalty must remain aligned.
- More profile polish, especially charts and fight history presentation.

Keep changes focused, testable, and save-compatible.
