# MMA Warriors AI Developer Guide

This guide is the working contract for coding agents that inspect, change, test, or package
MMA Warriors. Read it before editing. It documents how agents should collaborate, where game
state lives, and which product invariants must survive every change.

> **Terminology:** In this document, an **agent** is an AI coding collaborator. The promotions,
> executives, matchmakers, fighters, and media organizations simulated by the game are referred
> to as **game AI** or **simulation actors**. They are ordinary Python state and logic, not
> independent agent processes.

## 1. Working Agreement for Coding Agents

### Agent roles

The roles below describe responsibilities, not permanent identities. One agent may fill more
than one role on a small task.

- **Primary agent / integrator**: owns the user request end to end. It defines scope, inspects
  existing behavior, delegates bounded work where useful, resolves overlapping changes, runs the
  final verification, and reports what changed and what remains uncertain.
- **Investigator**: traces a bug or subsystem without making broad edits. It should return concrete
  evidence: relevant files and methods, reproduction conditions, likely cause, and suggested tests.
- **Implementer**: makes a focused change in explicitly owned files. It must preserve save
  compatibility and existing user changes, and should add or update the narrowest useful test.
- **Reviewer / verifier**: reviews the integrated diff rather than the intended design alone. It
  looks for regressions, stale documentation, save/load gaps, UI overflow, duplicated methods, and
  missing tests, then runs the checks appropriate to the change.

The primary agent remains responsible for the final result even when work is delegated.

### Multi-agent collaboration

Multi-agent delegation and parallel work are explicitly enabled for this project when independent
investigation, implementation, review, or testing can be performed safely.

1. Give each delegated task a narrow question, named file set, or read-only scope.
2. Avoid having two agents edit the same file at the same time. If overlap is unavoidable, name one
   integrator and have the other agent return findings instead of a competing patch.
3. Delegated agents should report evidence and assumptions, not only a conclusion.
4. The primary agent reviews the combined diff and runs the final tests after all edits settle.

Example delegation:

```text
Investigator: trace how a five-round bout chooses max_rounds; do not edit files.
Implementer: patch fight_engine.py and the focused regression in smoke_test.py.
Reviewer: inspect the final diff for missing structural commentary and run fight tests.
Primary: integrate, resolve conflicts, run the full shipping suite, and update docs.
```

### Approval policy

Do not ask for approval before ordinary, in-scope development work. Proceed autonomously with
reading, editing, testing, building, and other reversible project actions. Ask the user only when:

- essential information cannot be discovered locally;
- the choice would materially change the requested scope;
- the action affects external systems or people; or
- the action is destructive or difficult to reverse.

Preserve unrelated working-tree changes. Never delete or rewrite user saves unless explicitly
requested.

### Repository hygiene

- Inspect `git status --short` before and after work so existing edits are not mistaken for yours.
- Review untracked files before staging. Add required source, tests, documentation, and intentional
  assets; leave out saves, logs, caches, local databases, and generated build output unless the
  project explicitly tracks them.
- Stage only the files that belong to the requested change. Do not silently bundle unrelated user
  work into a commit.
- Run `git diff --check` before handoff to catch whitespace and patch artifacts.

### Mandatory change package

Every implementation update, improvement, bug fix, balance change, data change, UI change, tooling
change, or packaging change must include all of the following in the same working diff:

1. **`CHANGELOG.md`**: add a concise entry under the current release describing the observable fix,
   improvement, compatibility effect, or developer-facing change.
2. **`README.md`**: update the relevant feature, workflow, test, build, or compatibility description
   so the repository's main documentation matches the implemented behavior.
3. **`AGENTS.md`**: update the relevant architecture map, invariant, integration point, pitfall, test
   rule, or workflow guidance so a future coding agent does not reintroduce the old behavior.
4. **Tests**: add or update the narrowest useful automated regression and run the affected suite.
   A bug fix test should fail against the broken behavior and pass with the fix. An enhancement
   should cover its main path and important boundary or compatibility case.

These are required deliverables, not optional cleanup. Do not make empty timestamp/touch edits just
to satisfy the list; each document change must explain something useful about the change. If a
runtime behavior genuinely cannot be automated, add the closest stable invariant test and document
the reproducible manual verification. Documentation-only changes do not require a new game-runtime
test, but still require Markdown/link review and `git diff --check`.

### Definition of done

A meaningful code change is complete only when the primary agent has:

1. inspected the existing implementation and adjacent state flow;
2. implemented the smallest coherent fix;
3. added or updated regression coverage, or documented why only manual verification is possible;
4. run the checks appropriate to the affected subsystem;
5. reviewed the final diff for accidental or unrelated edits; and
6. made meaningful, synchronized updates to `CHANGELOG.md`, `README.md`, and `AGENTS.md`.

## 2. Product Goal and Design Principles

MMA Warriors is a Windows desktop MMA promotion-management simulation. The target feel is a deep,
living WMMA-style world: promotions compete, fighters age and develop, gyms matter, contracts and
morale matter, and fight outcomes emerge from the simulation rather than being forced.

The game should remain:

- a shippable Windows desktop game;
- a deep business and world simulation, not a web app;
- dark, readable, game-like, and uncluttered;
- data-rich but navigable; and
- compatible with existing careers whenever possible.

Treat the repository root as the directory containing this file. Do not put developer-specific
absolute paths or Windows usernames into source code, documentation, batch files, or tests.

## 3. Architecture at a Glance

The application was split from one large `main.py` into flat sibling modules. `FightEmpireApp` is
assembled from mixins so existing cross-cutting `self.some_method()` calls continue to work.

The current mixin order in `main.py` is:

```python
class FightEmpireApp(
    FightNightAudioMixin,
    UIMixin,
    AdminMixin,
    SeedMixin,
    MediaMixin,
    ViewMixin,
    EventMixin,
    FightEngineMixin,
    WorldMixin,
    PersistenceMixin,
    AwardsMixin,
):
    ...
```

Python resolves duplicate method names in that order. Before adding a common-sounding helper, use
`rg` to make sure another mixin does not already define it. Add a method to the module that owns its
behavior; add a true global constant or path anchor to `constants.py`.

### Source modules

| File | Primary responsibility | Important integration points |
| --- | --- | --- |
| `main.py` | Entry point, `FightEmpireApp`, initialization, startup splash, crash hooks, launcher | Imports every mixin; initializes shared state before builders and refreshes use it |
| `constants.py` | Version/title, path anchors, weights, regions, skills, names, camps, tuning constants | Paths must remain portable; fight and UI limits belong here |
| `models.py` | `Fighter`, `Gym`, and `Promotion` dataclasses | New fields need safe defaults and load repair |
| `ui.py` | `UIMixin`: theme setup, shared layout, sorting, and all `build_*_tab` methods | Widgets are populated by refresh methods in `views.py` and other domain mixins |
| `views.py` | `ViewMixin`: `refresh_*` methods, profiles, rankings, contracts, staff, finance, matchmaking views | Reads shared app state; must tolerate old-save defaults |
| `admin.py` | `AdminMixin`: sim lab, engine settings, belts, champions, name cleanup | Useful for calibration and repair tools, not outcome fudging |
| `seeding.py` | `SeedMixin`: universe database loading, roster/company/region/gym seeding, generated fighters, repair data | Core-promotion and data-quality changes usually start here |
| `events.py` | `EventMixin`: scheduling, negotiations, weigh-ins, live fight window, `run_event`, `finish_event`, awards | Calls the fight engine, world result application, media, audio, and season tracking |
| `fight_engine.py` | `FightEngineMixin`: `simulate_fight`, action resolution, damage, stoppages, scoring, commentary | Returns simulation results; must not mutate presentation state unpredictably |
| `world.py` | `WorldMixin`: availability, result application, Elo, finance, calendar, aging, retirements, game AI promotions, market churn | Owns weekly/monthly world progression and AI-company activity |
| `persistence.py` | `PersistenceMixin`: serialization, load/apply, slots/folders, database import/export, crash recovery | All persistent model/state changes need a compatibility path here |
| `awards.py` | `AwardsMixin`: season tracking and end-of-year awards | Decisive player and AI fights must both call `record_season_result` |
| `media.py` | `MediaMixin`: media desk, stories, broadcaster/media-rights state and presentation | Persistent media fields need save defaults and `media_system_test.py` coverage |
| `audio.py` | `FightNightAudioMixin`: optional fight-night sound and playback lifecycle | The game must still work when audio files or playback support are unavailable |
| `real_sport_profiles.py` | Authored real-sport fighter/profile data | Keep data deterministic and consistent with seeding rules |
| `database_editor.py` | Standalone universe database editor | Has its own executable, spec, build script, and UI audit |

The older `main.original_backup_*.py` files, when present, are historical pre-split backups. They are
not the active implementation. Do not copy fixes into them.

### Tests, scripts, and runtime data

- `smoke_test.py`: broad startup, release-document synchronization, state, save/load, UI-adjacent,
  contract, and fight regressions.
- `stability_test.py`: longer-running deterministic and progression playtests.
- `media_system_test.py`: media-system state and workflow regressions.
- `database_editor_ui_audit.py`: database-editor UI audit.
- `Run Smoke Tests.bat`: runs smoke, stability, and media-system suites.
- `Launch MMA Warriors.bat`: starts the source game.
- `Build Portable.bat`: tests and builds the portable game package.
- `Build Database Editor.bat`: builds the standalone database editor.
- `Portable Check.bat`: checks the packaged runtime.
- `README.md`: player, source-run, test, and build instructions.
- `CHANGELOG.md`: release-facing behavior changes.
- `TAB_ACCESSIBILITY.md`: tab contrast and interaction requirements.
- `savegame.json`, `Saves/`, `Databases/`: runtime data. Do not delete or overwrite user careers.
- `Logs/mma_warriors.log`: rotating runtime log. `Logs/Crashes/` contains timestamped crash reports;
  crash autosaves live in the active slot's `Crash Recovery` folder.

## 4. State Ownership and Control Flow

`FightEmpireApp` is a shared stateful object. Mixins cooperate through `self`, so a local-looking
change can affect save/load, refreshes, and world simulation. Trace both writers and readers before
changing a field.

Two `Fighter` model invariants are especially important:

- `Fighter` uses `@dataclass(eq=False)` deliberately. In-memory membership and comparisons use
  object identity for performance. Persistent and UI identity uses `fighter_id`; display names are
  not unique identifiers.
- `Fighter.overall` is a derived read-only property. Change the underlying broad/detailed skills or
  use the relevant calibration helper; do not assign directly to `overall`.

### Canonical flows

**Player fight flow**

```text
booking UI
  -> event-date availability checks
  -> perform_weigh_in (shared weight-cut model)
  -> simulate_fight (mechanics + complete structured commentary)
  -> finish_event
       -> record_season_result
       -> apply_result or apply_draw_result
       -> finance, injuries, rankings, history, awards, and media
  -> viewer and save/refresh
```

**Game-AI fight flow**

```text
calendar_week_steps
  -> world_week_steps
  -> ai_should_run_show
  -> simulate_ai_promotion_month
  -> AI booking and perform_weigh_in
  -> simulate_fight
  -> AI-specific Elo, records, recovery, title, and finance updates
  -> record_season_result
  -> promotion history, media, and world state
```

Do not create a shortcut version of a shared rule for AI fights. Player events, AI cards, and
sandbox fights should call the same underlying mechanics wherever the rules are meant to match.
The current AI event path does not call `apply_result`; it performs equivalent domain updates inside
`simulate_ai_promotion_month`. When changing result semantics, inspect and test both paths.

**Save/load flow**

```text
live dataclasses and world dictionaries
  -> serialize_world / model serializers
  -> JSON in the active slot and group
  -> apply_world_data
  -> defaults + focused repair functions
  -> UI refresh
```

### Calendar model

- A month has four simulation weeks.
- The displayed year is `2026 + (self.month - 1) // 12`.
- A new year begins when `self.month` rolls to 13, 25, and so on.
- Despite its legacy name, `advance_month()` synchronously advances **one week** for tests, audits,
  and non-UI callers. It consumes `calendar_week_steps()` and only crosses a month boundary when
  advancing from week 4.
- `begin_advance_sequence()` is the responsive Tk path. It also consumes `calendar_week_steps()`
  but schedules work through the event queue so the window remains usable.
- At a year boundary, the calendar rollover runs end-of-year awards and `age_world_one_year`.
- Annual aging is deterministic `+1`; do not add a second birthday path.

## 5. Save Compatibility and Persistent State

Do not break existing saves. New data must be optional when an old career does not contain it.

When adding a field to `Fighter`, `Promotion`, `Gym`, or a persisted world dictionary:

1. add a safe dataclass/default value where possible;
2. seed it for new universes;
3. serialize it if the existing serializer does not already do so;
4. restore it in `apply_world_data` with `get`, `setdefault`, or a focused repair helper;
5. update profile/refresh code so missing legacy data is harmless; and
6. add an old-save or round-trip assertion to `smoke_test.py`.

Example pattern:

```python
# models.py
morale_trend: int = 0

# persistence.py, while applying legacy data
fighter.morale_trend = int(saved.get("morale_trend", 0))

# smoke_test.py
assert loaded_fighter.morale_trend == 0      # legacy-shaped input
assert round_trip.morale_trend == original   # current save
```

### Path and slot rules

- `APP_DIR` comes from `__file__`, or from `sys.executable` in a packaged build.
- `DATA_DIR` uses `APP_DIR` when writable. In a protected install location it falls back to
  `%LOCALAPPDATA%\MMA Warriors`.
- `SAVE_FILE`, `SAVE_DIR`, `DATABASE_DIR`, and `LOG_DIR` are anchored to `DATA_DIR`, never the
  current working directory.
- Existing ungrouped careers live at `Saves\<Slot>\savegame.json` and appear as the `Main` group.
- User-created groups live at `Saves\Folders\<Group>\<Slot>\savegame.json`.
- `active_save_group` is persisted. Backups, autosaves, snapshots, and crash recovery remain inside
  the owning slot and must move with it.
- Save discovery and manipulation must use `primary_save_paths`, `save_slot_name_from_path`, and
  `save_slot_group_from_path`. Do not assume every slot is exactly one directory below `SAVE_DIR`.

### Known serialization side effect

`serialize_world()` currently calls `ensure_all_company_champions()`. That can fill thin divisions,
add fighters, and consume simulation RNG. It is deliberately mirrored with load-time repair so the
round trip remains stable. Do not treat serialization as a read-only operation in tests, and do not
remove this call as an isolated cleanup. A correct refactor must move division top-up out of both
save and load and into one explicit simulation step, with migration and regression coverage.

## 6. Promotions, Spectator Mode, and World AI

### Shipped-universe source of truth

New careers load `Databases\Default Universe.universe.json` through
`load_universe_database_pack()`. Its `fighters`, `combat_sports`, `companies`, `media`, and `regions`
sections are independently editable and are the source of truth for the shipped starting world.
The pack has a top-level schema version, and complex sections such as `fighters` and
`combat_sports` also carry their own schema versions. Python seed specs provide defaults, generated
depth, and repair fallbacks; changing only a fallback may not change a new game built from the
database.

Use `database_editor.py` or a carefully reviewed data edit for starting-universe changes, then
validate the file. The standalone database editor changes universe database packs; it does **not**
edit an active career save.

### Company ownership invariant

During a normal player career, the player company is represented by player-owned fields such as
`self.player_company_name`, `self.roster`, `self.cash`, and `self.company_pop`. It must not also be
present in `self.promotions`, or it will be simulated twice.

`Create Your Own Promotion` keeps BAMMA in the world as an AI promotion. Spectator Mode is different:
it promotes the former player company into `self.promotions`, persists `spectator_mode`, and keeps
all observer fast-forward controls in the Game Menu observer panel.

### Current core promotions

The default player company is BAMMA. The core rival/company set includes:

- Ultimate Fighting Championship
- Professional Fighters League
- ONE Championship
- RIZIN Fighting Federation
- KSW
- Cage Warriors
- Legacy Fighting Alliance
- Oktagon MMA
- BRAVE Combat Federation
- Absolute Championship Akhmat
- PRIDE Fighting Championships
- Strikeforce
- World Extreme Cagefighting

Regional feeder promotions are also first-class world objects:

- Japan Fight Circuit
- UK Regional MMA
- North American Fighting League
- European Challenge MMA
- Asia Rising Championship
- Brazilian Combat Circuit
- Latin American MMA League
- Canadian Fight Alliance
- Oceania Combat League
- African MMA Championship
- Midwest Fight League
- Nordic Combat League
- Korean Fighting Championship
- South American Vale Tudo Circuit
- British Fight League
- Eurasian Fight Circuit

Feeders have `is_regional_feeder=True`, do not use the normal commercial-finance simulation, and
support young-prospect generation, development cards, and pathways. The Eurasian circuit has
authored male-only behavior; preserve its origin and roster-depth rules.

### How game-AI promotions decide

Promotion behavior is persistent state, not a fresh random personality on every card:

- `show_personality` is the stable event-cadence and card-construction identity, such as
  `Super Shows`, `Seasonal`, or `Prospect Builder`.
- `strategy` stores stable identity (`identity`, `media_voice`, star/prospect/merit focus, risk and
  commercial traits) plus mutable state such as `current_mode`, financial pressure, roster health,
  and market momentum.
- `executive` stores leadership traits (`aggression`, `patience`, `discipline`, job security) and a
  board mandate with progress and deadline state.
- `update_ai_promotion_strategy` chooses `Financial Recovery`, `Prospect Rebuild`, `Star Chasing`,
  `Contender Cycle`, `Title Push`, or `Balanced` from cash, stability, reputation, momentum, and the
  persistent identity.
- `ai_should_run_show` gates scheduling with cash, named-day readiness, fatigue limits, roster depth,
  current mode, executive pressure, and show personality.
- `ai_offer_*` fields on a fighter represent a visible pending contract offer. The offer persists
  until its deadline and resolves later; do not replace this with instant random signing.
- Regional feeders branch into development-focused behavior and bypass normal commercial finance.

Simplified decision flow:

```python
strategy = self.update_ai_promotion_strategy(promotion)
if self.ai_should_run_show(promotion):
    self.simulate_ai_promotion_month(promotion)

# Separately, the contract market creates a pending offer.
fighter.ai_offer_company = promotion.name
fighter.ai_offer_deadline_month = self.month + 1
# A later market step accepts, rejects, or clears it.
```

When adding, removing, or renaming a core promotion:

1. update the `companies` section of the shipped universe database and the relevant fighter
   ownership/roster records;
2. update authored Python fighter data and fallback `default_promotion_specs`/`seed_promotions`;
3. update `repair_core_promotions` so old saves heal;
4. update promotion executives, strategies, identities, and `promotion_broadcasters` where relevant;
5. update regional feeder specs if it is a feeder;
6. validate the universe database and update `smoke_test.py`; and
7. update `README.md` and release notes when player-visible.

## 7. New Promotion Starts

`Create New Promotion...` is a real starting mode, not an editor shortcut.

- The Starting Promotion dropdown is the sole entry point for established, custom, and
  Spectator Mode starts. Keep `Start New Game With Selected Promotion` as the only action
  button in that panel; do not restore a separate create-promotion shortcut.

- The player chooses region, scale, event philosophy, theme, supported genders, and active weights.
- New starts use viable roster targets of 8, 10, or 12 fighters per active division.
- The default is Men Only with Featherweight, Lightweight, and Welterweight active. Do not silently
  reopen every division.
- `Balanced`, `Star Led`, and `Prospect Heavy` change automatic-draft priorities.
- The manual initial-roster draft exposes fighter profiles and annual contract commitment.
- Every active division needs at least six selected fighters, and the total must remain inside the
  scale/division budget.
- `auto_select_custom_roster` must reserve a complete affordable baseline for every active division
  before spending remaining budget on upgrades. Sequential spending can starve the last division.
- Closed divisions persist when saved/loaded, handed to AI, or taken over later.

## 8. Matchmaking and Availability

Matchmaking is event-date aware. `fighter.status` describes the fighter's current condition; it is
not enough to decide whether the fighter can compete on a future date.

- Use `fighter_booking_status(fighter, month, week)` for the human-readable week-level state.
- Use `fighter_available_for_date(fighter, month, week, day)` for authoritative named-day
  eligibility.
- Refresh available fighters immediately when event year, month, or week changes.
- The default `Ready` filter means ready for the selected event date.
- The `All` filter may show unavailable fighters with a precise label such as
  `Available Mar W3 2026`.
- Routine conflicts belong in the inline matchmaking notice, not a native Windows message box.

Example:

```python
status = self.fighter_booking_status(fighter, selected_month, selected_week)
event_day = self.selected_booking_day()
if self.fighter_available_for_date(fighter, selected_month, selected_week, event_day):
    eligible.append(fighter)
else:
    display_unavailable(fighter, status)
```

## 9. Fight Engine and Fight-Night Presentation

The fight engine must model the bout rather than pick a desired result and work backward.

### Mechanical intent

- Kicks depend on kick speed, power, technique, stamina, distance, and defense.
- Punches depend on hand speed, punch power, technique, head movement, guard, chin, and stamina.
- Grappling depends on takedowns and setup, sprawl, guard work, control, submissions and defense,
  stamina, and position.
- Stamina and momentum should visibly influence later exchanges.
- Ground, clinch, and cage position must reset or transition according to the rules; state must not
  leak impossibly across a horn.
- Commentary must never describe new actions after a finish.
- Equal score totals must be capable of producing draws.
- End-of-fight output includes the completed rounds and scorecards where applicable.

### Round count

The event data decides championship pacing. A fight marked `title` or `main` uses the configured
five-round path when the active rules provide five title rounds; ordinary fights use the normal
round count. Test title and non-title five-round main events because both are supported.

### Commentary structure

Five-round fights generate enough text to exceed a Tk text widget's comfortable live-display size.
The engine therefore compacts only ordinary action calls within each round. Structural lines must
always survive:

- tale of the tape and opening context;
- every round introduction;
- every horn/round transition;
- every round summary;
- stoppage and official-result lines; and
- decision scores.

`FIGHT_COMMENTARY_ROUND_LINE_LIMIT`, `FIGHT_COMMENTARY_ROUND_HEAD_LINES`, and
`FIGHT_COMMENTARY_ROUND_TAIL_LINES` define the per-round action budget. If the budget is exceeded,
keep the opening and late-round calls with a single summary marker between them. Do not slice the
finished global commentary list; that was the source of missing rounds.

Required regression scenarios include:

1. a five-round title decision with all five introductions and summaries;
2. a non-title five-round main-event decision with the same structure; and
3. a late round-five finish with the round-five introduction and official result preserved.

### Outcome calibration

Audit finish rates by fighter tier, not only across a random-paired pool. Random pairing
over-represents mismatches, which finish more easily than realistic cards.

Competitive same-tier targets:

- Low tier (`overall < 68`): about 50-56% finishes.
- Mid tier (`overall 68-80`): about 32-42% finishes.
- High tier (`overall >= 80`): about 38-45% finishes.

The best single audit is realistic matchmaking: pair fighters with an overall gap of at most six
across all tiers. A useful comparison shape is Decision ~47%, KO ~16%, TKO ~15%, Submission ~19%,
or roughly 52% finishes. A mixed random pool may report 60-65% finishes because of mismatches; that
is expected and should not be tuned away by weakening the whole engine.

Historically, elite competitive fights became too decision-heavy because damage scaled with strike
margin while defense and KO thresholds rose with skill. The current model gives impact meaningful
raw-power scaling and flatter threshold growth. Tune mechanics and probabilities, then rerun the
per-tier audit. Never overwrite the final method merely to hit a target percentage.

## 10. Contracts, Weigh-ins, and Shared Rules

### Contract terms

Player-negotiated contract duration is normalized to 1-60 months. Duration is secondary to fair
compensation: fighters should not accept badly under-market base pay only because the company asks
for years of control. Security has diminishing value through 48 months and no additional scoring
benefit beyond that point. Keep `normalized_contract_months` and
`contract_duration_offer_score` aligned with the negotiation UI and smoke regressions.

### Weight cuts

Use `perform_weigh_in` for player events, AI cards, and sandbox fights. Do not add a second shortcut
calculation. Camp length, body fit, cut skill, scale weight, title-fight rules, and the resulting
performance penalty must stay consistent across every fight path.

## 11. Gyms, Development, and Awards

Gyms are first-class world objects. Their effects consider:

- quality, facilities, and reputation;
- room morale and capacity/crowding;
- specialties and scouting;
- fighter style fit; and
- fighter age, prime, potential, and dedication.

The gym viewer is accessible from the World Hub. If gym fields change, inspect and usually update:

- the `Gym` dataclass;
- `seed_gyms`;
- serialization and `apply_world_data`;
- `refresh_world` and `open_gym_viewer`; and
- `smoke_test.py` when core assumptions change.

Season statistics are fed by `record_season_result` for every decisive player and AI fight.
`run_end_of_year_awards` runs at the year rollover and appends to `awards_history`. Adding a new fight
path without season tracking silently biases awards toward whichever path still records results.

## 12. UI, Themes, and Accessibility

The user strongly dislikes unreadable or cluttered UI. The game is normally played maximized, but
layouts must still degrade cleanly at smaller supported widths.

- Avoid hard-coded white or pale backgrounds. Use `self.colors["cream"]`,
  `self.colors["text"]`, and the active palette.
- Do not leave player-facing `ttk.Progressbar` widgets on the native grey defaults. Loading activity
  uses `Activity.Horizontal.TProgressbar`; live-fight freshness uses the red/blue corner styles, all
  with a dark track and a fill-to-track contrast ratio of at least 3:1.
- Keep dense database screens sortable and filterable.
- Add double-click profile/viewer behavior where it is natural.
- Do not add giant explanatory landing pages or unnecessary tabs.
- Do not allow text to overlap. Keep buttons and badges stable in size.
- Use flexible grid columns for variable-length names and separate fixed cells for critical stats.
  For example, promotion name and `Popularity` must never share one clipped label.
- Prefer dark, game-like panels and inline status/decision areas.
- Reserve modal confirmation for destructive or genuinely blocking decisions.
- Synchronous operations that can visibly stall the Tk event loop, especially Quick Load and Save
  Manager slot loads, must open the reusable `show_busy_overlay` panel before heavy work, update it
  at stable phase boundaries, and close it in every success and failure path. Keep the panel modal so
  users cannot start a second state-changing action while the first is rebuilding shared state.
- Inbox and Matchmaking deliberately set `_force_viewport_width` because their internal responsive
  panes and table scrollbars own overflow. Do not let either screen's natural table width widen the
  entire page canvas again. `configure_inbox_panel_layout` stacks Owner Goals below Inbox on narrow
  pages; `configure_booking_panel_layout` moves Current Fight Card above Available Fighters.
- Collapsible content must use `disclosure_section`: its named Expand / Collapse button and summary
  remain visible when content is closed. The two disclosure states live in save-compatible `rules`
  keys. Never replace these with arrow-only headers or blank collapsed space.
- Do not restore full-width first-visit or `NEW HERE?` banners on dense management screens. Put brief
  instructions in persistent local summaries, table cues, detail placeholders, or meaningful empty
  states so onboarding help does not push data and action buttons below the viewport.
- Vertical resizers must keep applying their configured fractional target while the window moves
  through its startup and maximize sizes. Stop automatic placement only after the player releases
  directly on the sash; otherwise a small pre-maximized layout can permanently clip action footers.
  Mail / Decisions additionally reserves a 425-pixel top pane and grids its eight actions into two
  non-shrinking rows; only the Inbox table row may absorb a vertical-space shortage.
- Current Fight Card groups hype, build, fatigue A/B, and medical return A/B in its `booking` column
  so the complete card fits without page-level horizontal scrolling. Available Fighters intentionally
  retains all 20 dense columns and its local horizontal scrollbar, plus the visible column-count cue.
- `CLOSED` is too ambiguous. Free agents in a player-disabled division show `DIVISION CLOSED`, and
  the detail panel points to `Roster > Manage Divisions`.

The main window requests Windows' `zoomed` state and falls back safely when unavailable. Do not
replace that with a fixed screen-size geometry.

### Tabs and themes

Tab states must remain distinguishable for mouse and keyboard users: default, selected, hover, and
focus styling should meet the rules in `TAB_ACCESSIBILITY.md`. Derive tab colors through
`tab_style_palette`; do not hand-pick a one-off color that only works in one theme.

Known themes are:

- Base: `Fight Night`, `Classic Green`, `Light Office`.
- Promotion: `BAMMA`, `UFC`, `PFL`, `Cage Warriors`, `ONE Championship`, `RIZIN`, `KSW`, `LFA`,
  `Oktagon`, `BRAVE`, `ACA`.
- Combat sport: `Boxing`, `Kickboxing`, `Muay Thai`, `Wrestling`, `BJJ`.
- Sports media: `Sky Sports`, `ESPN`, `BBC Sport`.
- Special: `Matrix`, `Champion`.

When changing shared UI, verify representative dark, light, promotion, and special themes, not only
the currently selected theme.

## 13. Data Quality

- Avoid duplicate fighters across companies unless intentionally labeled as a historical/younger
  variant, for example `Tom Aspinall CW`.
- Never create names with a `2` suffix as a collision workaround.
- Keep male and female fighters correctly gendered.
- When adding women whose names are absent from `FEMALE_FIRST_NAMES`, update `infer_gender`.
- Keep each company deep enough to fill its active divisions and champions.
- Use real fighters where requested; generated fighters are acceptable for roster depth.
- Generated data and tests should be deterministic under an explicit seed. Isolate test RNG setup
  from serialization and unrelated name generation.

## 14. Testing and Shipping

Use the configured bundled Python runtime when available. Otherwise use a local Python 3
installation with Tkinter. Commands in documentation must be repository-relative; replace `python`
with the full path to the configured interpreter when necessary.

### Fast syntax check

```powershell
$PythonSources = Get-ChildItem -LiteralPath . -Filter '*.py' -File | Select-Object -ExpandProperty FullName
python -m py_compile $PythonSources
```

### Shipping test suite

```powershell
.\Run Smoke Tests.bat
```

The batch file pauses for interactive use. Automated agents may run the equivalent commands
directly:

```powershell
python .\smoke_test.py
python .\stability_test.py
python .\media_system_test.py
```

Validate the shipped universe database after data or editor changes:

```powershell
python .\database_editor.py --validate '.\Databases\Default Universe.universe.json'
python .\database_editor_ui_audit.py
```

Tkinter startup tests require a Python installation with working Tcl/Tk data. If a sandboxed
runtime cannot find `init.tcl`, distinguish an environment failure from a game failure and rerun
with the configured Windows runtime when permitted.

### Release metadata

`constants.py::GAME_VERSION` is the runtime version source. For a release, keep it synchronized with
the version shown in `README.md` and the newest section of `CHANGELOG.md`. Changelog entries should
describe player-visible behavior and important compatibility changes, not merely list edited files.

### Test selection

| Change | Minimum verification |
| --- | --- |
| Documentation only | Read rendered Markdown, check links/commands, run `git diff --check` |
| Models, seeding, saves, calendar, game AI | Syntax check + smoke + stability |
| Fight mechanics or commentary | Syntax check + smoke regressions + relevant tier/long-run audit |
| Media Desk or rights | Syntax check + smoke + media-system test |
| Shared UI/theme/layout | Syntax check + smoke + manual maximized-window check in representative themes |
| Universe data or database editor | Syntax check + universe `--validate` command + `database_editor_ui_audit.py`; build if packaging changed |
| Packaging, assets, paths, startup | Full shipping suite + portable build + launch packaged executable briefly |

Randomized tests should assert robust invariants or aggregate behavior. Do not hide a real
regression by widening a threshold without explaining why the sample design was wrong.

### Portable builds

For the game:

```powershell
.\Build Portable.bat
```

For the standalone universe editor:

```powershell
.\Build Database Editor.bat
```

The game build must preserve these runtime folders and files in `dist\MMA Warriors`:

```text
Saves
Databases
Logs
README.md
Portable Check.bat
```

Never solve a build problem by deleting runtime saves. After a packaging or core-runtime change,
start the packaged `MMA Warriors.exe` briefly and run the portable check when available.

## 15. Common Change Recipes

### Add a persistent fighter or promotion field

```text
model default
  -> seed value
  -> serialize
  -> legacy load default/repair
  -> viewer or simulation consumer
  -> old-save + round-trip smoke assertions
```

### Add a new core promotion

```text
shipped universe company + fighter ownership data
  -> authored Python roster data and fallback promotion seed spec
  -> old-save repair
  -> executive/strategy/identity/broadcaster data
  -> champion and division viability
  -> universe validation + smoke expectations
  -> README/changelog
```

### Add a new fight result path

```text
simulate_fight result
  -> finish/result presentation
  -> apply_result
  -> injury/ranking/finance updates
  -> record_season_result
  -> event and promotion history
  -> save/load regression
```

### Change a shared UI header or tab

```text
build widget with flexible geometry
  -> refresh every field independently
  -> verify long values and spectator mode
  -> verify keyboard/mouse states across representative themes
  -> check maximized and narrower supported widths
```

## 16. Common Pitfalls

- Do not edit saves destructively.
- Do not remove `repair_core_promotions`; it keeps older saves viable.
- Do not put the active player company in `self.promotions` during a normal career.
- Do not make save paths current-working-directory relative.
- Do not assume `serialize_world` is currently side-effect free.
- Do not add pale hard-coded panels or theme-specific tab colors.
- Do not add a core promotion without updating repairs, data, smoke tests, and docs.
- Do not rely on `Cage Empire`; old references are backward-compatibility guards only.
- Do not add a new tab when an existing viewer or table can be extended cleanly.
- Do not use `fighter.status` as future-date availability.
- Do not flatten grouped save paths during load, move, backup, delete, snapshot, or quick save.
- Do not restore three-person custom divisions. Eight is the minimum normal target and six is the
  hard draft viability floor.
- Do not bypass `perform_weigh_in`, season tracking, or other shared mechanics for a new fight path.
- Do not trim global fight commentary in a way that can delete round structure or the official result.

## 17. Current Product Direction

Prefer focused, testable improvements in these areas:

- more readable fight-night pacing and presentation;
- better AI scheduling so promotions avoid overbooking tired fighters;
- finance tuning for gates and media rights by region and company reputation;
- deeper staff contracts, poaching, development, and specialist scouting;
- more gym/camp stories and long-term development tracking;
- feeder promotions as a prospect pathway, retaining budgeted AI offers instead of instant random
  signings;
- stronger company identity and personality in AI booking;
- robust Spectator Mode as a true observer save;
- one shared weight-cut model through `perform_weigh_in`; and
- more polished fighter profiles, charts, and fight histories.

Keep every change focused, testable, portable, and save-compatible.
