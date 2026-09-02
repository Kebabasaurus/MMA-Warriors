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
| `ui.py` | `UIMixin`: theme setup, shared layout, sorting, all `build_*_tab` methods, and the managed popup registry | Widgets are populated by refresh methods in `views.py` and other domain mixins; runtime popups must use `create_managed_window()` |
| `views.py` | `ViewMixin`: `refresh_*` methods, profiles, rankings, contracts, staff, finance, matchmaking views | Reads shared app state; must tolerate old-save defaults |
| `admin.py` | `AdminMixin`: sim lab, engine settings, belts, champions, name cleanup | Useful for calibration and repair tools, not outcome fudging |
| `seeding.py` | `SeedMixin`: universe database loading, roster/company/region/gym seeding, generated fighters, repair data | Core-promotion and data-quality changes usually start here |
| `events.py` | `EventMixin`: scheduling, negotiations, weigh-ins, live fight window, `run_event`, `finish_event`, awards | Calls the fight engine, world result application, media, audio, and season tracking |
| `fight_engine.py` | `FightEngineMixin`: `simulate_fight`, action resolution, damage, stoppages, scoring, commentary | Returns simulation results; must not mutate presentation state unpredictably |
| `world.py` | `WorldMixin`: availability, result application, Elo, finance, calendar, aging, retirements, game AI promotions, market churn | Owns weekly/monthly world progression and AI-company activity |
| `persistence.py` | `PersistenceMixin`: serialization, load/apply, slots/folders, database import/export, crash recovery | All persistent model/state changes need a compatibility path here |
| `awards.py` | `AwardsMixin`: season tracking and end-of-year awards | Decisive player and AI fights must both call `record_season_result` |
| `media.py` | `MediaMixin`: media desk, stories, broadcaster/media-rights state and presentation | Persistent media fields need save defaults and `media_system_test.py` coverage |
| `audio.py` | `FightNightAudioMixin`: optional fight-night sound, manifest-driven crowd variants, continuous arena-bed sessions, and reaction playback lifecycle | Crowd WAVs live under `assets/crowd_audio`; the game must still work through procedural fallbacks when assets or playback support are unavailable |
| `real_sport_profiles.py` | Authored real-sport fighter/profile data | Keep data deterministic and consistent with seeding rules |
| `database_editor.py` | Standalone universe database editor | Has its own executable, spec, build script, and UI audit |

The older `main.original_backup_*.py` files, when present, are historical pre-split backups. They are
not the active implementation. Do not copy fixes into them.

### Tests, scripts, and runtime data

- `smoke_test.py`: broad startup, release-document synchronization, state, save/load, UI-adjacent,
  contract, and fight regressions.
- `persistence_regression_test.py`: transactional load, metadata sidecar, serialization purity, and
  Results-index idempotence regressions.
- `contracts_finance_regression_test.py`: contract validation, persistent clauses, same-name booking,
  guarantees, and canonical event-payout regressions.
- `finance_audit_regression_test.py`: canonical player/child transaction metadata, weekly cash
  reconciliation, and repairable direct-cash mutation coverage.
- `player_finance_progression_regression_test.py`: annual summaries, revenue mix, roster-cost
  snapshots, milestone projections, strategic investment gates/effects/upkeep, save persistence,
  and Finance-screen population.
- `ui_data_regression_test.py`: lazy staff/scouting UI, Results detail, gym capacity, regional data,
  themed Regions, and fighter-identity regressions.
- `fighter_profile_regression_test.py`: Profile employer/privacy, same-name history, archive identity,
  championship scoping, child-sport query purity, responsive geometry, and stale-action guards.
- `scouting_regression_test.py`: scouting identity migration, RNG purity, report lifecycle,
  rediscovery, staff identity, and recruitment UI-state regressions.
- `combat_sports_regression_test.py`: child-sport roster/booking identity, flagship contracts,
  expiry departures, purse settlement, scheduled-event lifecycle/economics, monthly card limits,
  and AI/player history separation.
- `qa_tooling_regression_test.py`: Simulation Lab isolation/calibration and portable launcher paths.
- `fight_engine_regression_test.py`: deterministic MMA audit purity, trace/stat consistency,
  detailed-attribute usage, and the frozen 3,840-bout finish-distribution parity corpus.
- `fight_engine_full_system_test.py`: 356 complete MMA bouts across every fight plan, major style
  matchups, 3/5/6/7-round rules, extreme ratings and same-name identities; reconciles trace evidence,
  position paths, stoppages, judging knockdowns and final box scores.
- `analysis/generate_fight_move_report.py`: deterministic 880-fight move report across every supported
  style plus behaviour, tier, stance and stance matchup; audits reachability, pairwise style distance,
  dominance, mismatch-only use, legality, move-energy metadata and ordinary use of every exclusive
  style combination and finisher without changing the frozen baseline. Its targeted reachability probe
  must adopt a move's preferred style before testing restricted style content; do not weaken runtime
  exclusivity.
- `analysis/generate_specialist_transition_report.py`: deterministic 720-fight complete-bout proof for
  failed-shot/front-headlock, standing-back-control and leg-entanglement states and legal follow-ups.
- `analysis/generate_fight_commentary_report.py`: deterministic 256-fight, four-voice commentary gate
  covering every factual outcome lane, stat-profile and failed-submission reaction coverage,
  standing/ground repetition, Broadcast compaction, actor/move/defense agreement, referee stand-up
  continuity, finish causality, duplicate results, placeholder removal, technical-suffix leakage,
  visible-damage actor/subject/symptom facts, exact cut locations, all supported trait introductions,
  contextual trait/camp evidence and call caps, verified camp-intro retention and Broadcast damage retention.
  Its `--seeds-per-matchup 64` mode is the 2,048-fight extended transcript audit.
- `analysis/generate_fight_action_baseline.py`: canonical 3,840-fight release gate for broad-action
  frequency, effectiveness, damage, energy, counters, positions and finishing contribution. The
  isolated regression runner verifies the checked-in baseline; do not treat it as an optional report.
- `stability_test.py`: longer-running deterministic and progression playtests.
- `media_system_test.py`: media-system state and workflow regressions.
- `child_promotion_long_run_test.py`: deterministic 48-week MMA child-promotion progression,
  event finance, parent profit sharing, contract countdown, protected loans, callback safety, and
  save/load persistence. It intentionally keeps only the child in the in-memory AI world so the
  calendar pipeline remains real while the focused regression stays fast enough for routine runs.
- `custom_promotion_division_integrity_test.py`: deterministic 48-week AI handoff regression that
  ensures annual weight movement cannot place fighters into a custom promotion's closed divisions.
- `child_promotion_interactions_test.py`: child takeover, empty-launch rollback, champion-loan belt
  protection, closed-division transfer rejection, transfer-ledger accounting, and loan repair.
- `identity_persistence_regression_test.py`: same-name live-fight and tournament identity, clinch
  ownership, unanswered-response semantics, ambiguous legacy relationships, event-commit rollback,
  forward/malformed save rows, and external-block path containment.
- `database_editor_save_as_test.py`: standalone editor Save As success, cancellation, validation,
  and write-failure state preservation.
- `database_editor_ui_audit.py`: database-editor UI audit.
- `universe_validation_regression_test.py`: shared editor/runtime validator malformed-data diagnostics and proof that normal legacy loading does not rewrite source bytes or mtime.
- `fight_audio_regression_test.py`: temporary fight-cache exception cleanup, continuous ambience
  lifecycle/crossfade, priority reservation, mastered later-round routing, and concurrent cue locking.
- `fight_night_experience_regression_test.py`: live-session re-entry, playback/control gating,
  duplicate-name winner identity, skip/review behavior, commit-failure recovery, replay cleanup, and
  responsive end-event invariants.
- `advance_notifications_regression_test.py`: routine contract/broadcast advancement notices collapse into one Inbox summary while due-event decisions remain modal.
- `window_lifecycle_regression_test.py`: runtime popup creators use the shared call-site/entity window registry.
- `event_economics_regression_test.py`: per-event ticket, marketing, production, legacy/default,
  save/load, and identity-safe grudge economics.
- `narrative_system_regression_test.py`: bounded ID-safe story threads, rivalry/title/redemption
  lifecycles, injury/academy/contract/staff/feeder/breakout/weight/gym/coaching/relationship/promotion-war/other-sport/crossover
  chapters, Chronicle linkage, lazy career timelines, annual-review selection, legacy/current save
  normalization, career-journey outcomes, presentation RNG purity, and indexed event-update performance.
- `narrative_performance_regression_test.py`: clean 12-week narrative-disabled/enabled calendar A/B
  comparison across three alternating paired samples, with deterministic test-only generated IDs,
  identical core-world/RNG assertions, a strict median CPU-time budget, and wall-clock diagnostics.
  CPU time is the release gate because it measures simulation work without turning an unrelated OS
  scheduler pause into a false regression; do not remove or loosen the 5% proportional ceiling.
- `narrative_long_run_storage_regression_test.py`: synthetic 25-/50-/100-year story growth, resolved
  cap, serialized-size, RNG isolation, and indexed-lookup scaling.
- `simulation_performance_regression_test.py`: promotion-level card-day caching, precomputed
  head-to-head reuse, batched regional name collision state, and one-card-per-month feeder
  staggering across all four calendar weeks.
- `run_regression_suite.py`: the canonical sequential test runner. It gives every suite an isolated
  `MMA_WARRIORS_DATA_DIR` with copied universe data so tests cannot race through shared saves,
  logs, markers, or caches.
- `Run Smoke Tests.bat`: runs the canonical isolated regression suite.
- `Launch MMA Warriors.bat`: starts the source game.
- `Build Portable.bat`: tests, validates the universe database, and builds both the game executable and the standalone database editor into `dist\\MMA Warriors`.
- `Build Database Editor.bat`: validates and builds only the standalone database editor when a
  full portable rebuild is unnecessary.
- `build-toolchain.json` and `requirements-build.txt`: the checked-in, offline-verifiable portable-build toolchain. Build scripts must validate these and must never install dependencies.
- `Portable Check.bat`: checks the packaged runtime.
- `README.md`: player, source-run, test, and build instructions.
- `FEATURE_DEVELOPMENT_BACKLOG.md`: evidence-backed player-facing feature priorities and phased
  development sequence. Keep it synchronized when a listed feature is shipped or materially
  re-scoped.
- `FIGHT_ENGINE_MOVES_AND_SKILLS_PLAN.md`: phased expansion of MMA styles, move definitions,
  combinations, skill coverage, signatures and tactical selection. Each mechanical slice must keep
  the accepted 60.39% finish, 16.48% KO and 19.04% TKO calibration and must not change
  `competitive_finish_conversion()`.
- `NARRATIVE_SYSTEM_DEVELOPMENT_PLAN.md`: audit and staged design for connecting existing simulation
  facts into persistent story threads. Narrative work must follow its performance guardrails: emit
  bounded updates from existing domain events, use indexed stable identities, isolate presentation
  RNG, and never add a second whole-world weekly history scan.
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
- Live-fight state is private to one bout and uses per-fighter state keys, never `fighter.name`.
  Names are presentation only. ID-first resolution must be pure: do not restore, release, sign, or
  otherwise mutate roster ownership as a side effect of looking a fighter up.
- `Fighter.overall` is a derived read-only property. Change the underlying broad/detailed skills or
  use the relevant calibration helper; do not assign directly to `overall`.
- Model collections that are semantically always present use `default_factory`; persistence must still
  normalise old-save `null` values. Do not replace meaningful optional sentinels such as an inactive
  `Fighter.career_arc is None` with an empty object.

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

The watched presentation is a single live session. Never prepare the same due event again while a
viewer is active: preparation runs mutable press-conference and weigh-in rules. A different replay
must not replace or destroy an unresolved player card. Playback controls must follow bout state;
starting the next fight cannot discard an incomplete transcript, full-card skip requires an
explicit second action, and every bout becomes reviewable after completion or confirmed skip.
`finish_event` remains the settlement transaction; only mark the viewer finished after that commit
succeeds, and keep a failed settlement visibly retryable.

Live telemetry and result presentation are ID-first. Red and blue round metrics use corner slots,
not display names, and current fight logs retain `winner_id` alongside `a_id`/`b_id`. Exact judge
cards and numerical totals remain sealed until the official result; public round summaries may show
metrics, gas, momentum, and an explicitly unofficial leader. Archived replay packages preserve
event economics and location context but always use `apply_results=False`.

`finish_event` is a domain transaction. Stage the pre-event persistent state and RNG before the
first finance or result mutation; if any downstream award, media, archive, history, or refresh
hook fails, restore the staged state before surfacing the failure. UI presentation occurs only after
the commit succeeds. Runtime synchronization objects such as locks, threads and `threading.Event`
audio stop signals, plus non-copyable `random.SystemRandom` audio entropy, must remain live and outside
the deep-copied rollback snapshot.

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

**Player event-economics flow**

```text
booking UI
  -> card-specific ticket price, marketing spend, and production tier
  -> projected attendance/gate/spend from the shared economics helpers
  -> scheduled-event serialization (legacy cards receive company defaults)
  -> finish_event transaction
       -> final demand, gate, merchandise, broadcast and production accounting
       -> canonical finance transaction
```

Forecast and settlement must call the same demand, pricing, production, and grudge helpers. A
booked rivalry is identified by durable fighter IDs; names are presentation and legacy fallback
only. A duplicate-name or stale legacy rivalry must never boost an unrelated bout.

### Calendar model

- A month has four simulation weeks.
- The displayed year is `2026 + (self.month - 1) // 12`.
- A new year begins when `self.month` rolls to 13, 25, and so on.
- Despite its legacy name, `advance_month()` synchronously advances **one week** for tests, audits,
  and non-UI callers. It consumes `calendar_week_steps()` and only crosses a month boundary when
  advancing from week 4.
- `begin_advance_sequence()` is the responsive Tk path. It also consumes `calendar_week_steps()`
  but schedules work through the event queue so the window remains usable.
- Promotion monthly reviews are assigned to stable, evenly sized weekly groups by
  `world_week_steps()`, and `world_month_steps()` must not repeat them at the boundary. Every
  promotion receives one development pass and monthly card opportunity per four-week month; every
  regional circuit runs one dedicated card. Keep feeder promotions out of the generic weekly
  `ai_should_run_show()` path.
- Routine post-advance contract, broadcast, and similar notices are accumulated by
  `queue_advance_notice()` and presented as one Inbox/news summary. Only genuine player decisions,
  such as a due event's watch/simulate choice, may remain modal.
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
  `%LOCALAPPDATA%\MMA Warriors`. `MMA_WARRIORS_DATA_DIR` is an explicit test-only/runtime override
  for an isolated data root; do not set it in shipped launchers.
- `SAVE_FILE`, `SAVE_DIR`, `DATABASE_DIR`, and `LOG_DIR` are anchored to `DATA_DIR`, never the
  current working directory.
- Existing ungrouped careers live at `Saves\<Slot>\savegame.json` and appear as the `Main` group.
- User-created groups live at `Saves\Folders\<Group>\<Slot>\savegame.json`.
- `active_save_group` is persisted. Backups, autosaves, snapshots, and crash recovery remain inside
  the owning slot and must move with it.
- Save discovery and manipulation must use `primary_save_paths`, `save_slot_name_from_path`, and
  `save_slot_group_from_path`. Do not assume every slot is exactly one directory below `SAVE_DIR`.

### Transactional load and result-index rules

- Treat a load as a transaction. Read, validate, migrate, and apply into a guarded candidate state;
  if any phase fails, restore the complete pre-load application state before showing the error.
  Reject a non-object top-level JSON value before external-block hydration or migration.
- `ensure_result_index()` is an idempotent migration. A detailed record already represented by the
  same stable archive/detail key is skipped. Only genuinely distinct cards may receive a sequenced
  key, and repeated Quick Loads must never grow the index.
- Save metadata is auxiliary. A metadata-write problem must not turn an already committed primary
  save into a reported total failure; record it as a recoverable cache warning and rebuild it later
  without leaving a blocking success/failure dialog open.
- Recovery snapshots taken before Quick Save or switching slots are best-effort and must not block
  the requested operation when snapshot creation fails. A backup restore is different: validate the
  source first, then protect the existing destination and atomically replace it; report any failure
  without changing the destination or letting an exception escape the UI callback.
- The Game & Saves Career Library keeps `save_slot_list` as the action index and refreshes its active
  banner, counts, selection inspector, and button state through `refresh_game_menu()` and
  `refresh_save_selection_summary()`. Selection-only actions must remain disabled when no valid row
  is selected, and the blank destination-name field must not be populated from the active career.
- External split-save blocks must use generated `DataBlocks/<save-stamp>/<known-key>.json.gz` paths
  below the owning save slot. Reject rooted paths, traversal, symlink escapes, and unexpected block
  names before reading them. Pruning must skip symlinked entries rather than following or deleting
  them.
- Model rows must be type-checked before dataclass construction. Missing required fields are a
  transactional load error; unknown forward-compatible fields are logged and ignored rather than
  crashing an otherwise usable career.

### Serialization purity

`serialize_world()` and ordinary save loading must be observational: they may normalize JSON-safe
representations, but must not top up divisions, appoint champions, add fighters, or consume
simulation RNG. Champion/division repair belongs to explicit new-game or calendar repair steps;
legacy migrations must be narrowly versioned and may not rewrite a healthy sealed career.
Regression tests must compare fighter counts, champion state, and RNG state across a round trip.

## 6. Promotions, Spectator Mode, and World AI

### Finance invariants

Player, child, and non-feeder AI cash movements must be recorded through the canonical finance
helpers in `world.py`. Transaction rows retain an ID, month/week, category, source, counterparty,
event, reference, entity, revenue, costs, and net movement; legacy ledger strings may remain for
presentation but are not the accounting source of truth. `close_finance_week()` and
`close_promotion_finance_week()` reconcile the stored ledger to actual cash and create an explicit
`Reconciliation` row for an unattributed legacy/direct mutation. New cash paths must add a focused
regression and use a stable reference so repeated weekly closes are idempotent. Finance UI surfaces
must show reconciliation status and promotion detail views must read the canonical weekly history.

Per-event ticket price, marketing spend, and production tier belong to the scheduled-event payload.
Old saves and AI cards that lack those keys must fall back to company-wide defaults without mutating
the source during serialization. Any new or changed event-economics field needs a legacy-shaped
load assertion and a current-format scheduled-card round trip in the focused economics regression.

Player career-stage balance has three derived rules. `apply_opening_player_contract_terms()` runs
only while seeding a new player roster and discounts curated, non-generated talent to the founder
contract factor; never reapply it during load or repair. `player_monthly_office_cost()` derives the
current office bill from the save-compatible base plus company popularity, and every player reserve,
forecast, and month-end charge must use that helper. `player_events_in_month()` drives commercial
cannibalization for a second or later settled player card in the same simulation month: attendance,
sponsor value, and broadcast income fall, but contracted purses, medical, marketing, and production
costs remain whole. Keep `analysis/player_finance_balance_audit.py` and the focused event-economics
regression synchronized when changing purses, media, sponsors, overhead, cadence, or milestone gates.

Long-career finance reporting is compact persistent state, not a second ledger. Canonical
`weekly_history` remains the source for the current annual rollup; `annual_history` preserves a
30-year summary and `roster_cost_history` preserves monthly roster/purse commitments after detailed
weekly rows expire. Revenue mix uses archived player-event breakdowns for gate, broadcast, sponsors
and merchandise, then adds non-event canonical income as Other. Never double-count the event-level
transaction. Milestone ETA may extrapolate cash and event pace, but must show popularity, stability
and safety as blockers rather than inventing a growth rate.

Strategic investments live in `finance["strategic_investments"]`. Purchases and monthly upkeep must
use canonical `Investment` transactions with stable references. Effects are applied by
`strategic_event_multiplier()` and must never reduce contracted fighter pay or bypass event
settlement. Capital approval and upkeep are transactions: restore cash, ownership, ledger rows and
change history if a late recording hook fails, and make a repeated monthly upkeep call idempotent.
New projects require a capital cost, upkeep, milestone/popularity gate, bounded effect,
safe old-save default, Finance UI row, and progression regression. `player_monthly_office_cost()` is
separate from strategic upkeep so forecasts and transaction categories remain explainable.

### Rivalry and media-action invariants

Rivalry records and grudge economics resolve fighters by `fighter_id`. Display names may be retained
for copy and narrowly defined legacy repair, but an ambiguous name is not identity. Matchmaking,
Media Desk escalation, scheduled cards, and fight settlement must all preserve the same ID pair.

Paid or limited-use Media Desk actions are transactions: validate every selected fighter and rival
before charging cash, consuming an action, or changing rivalry/media state. If a late hook fails,
restore the staged cash, action counters, and affected media/rivalry state rather than leaving a
partial action. Add focused coverage for stale and duplicate-name rivals whenever this flow changes.

### Narrative-thread invariants

`story_threads` is a bounded interpretive index over authoritative fight, rivalry, title, contract,
academy, company, and career state. Domain methods emit one deduplicated beat after their real state
change; narrative code must never rescan the whole world, Chronicle, Results archive, or complete
fighter histories during weekly advancement. Active and resolved limits and per-thread beat limits
come from `constants.py`. Thread participants use stable fighter IDs, with names retained only as
presentation snapshots. Rivalries use `rival_fighter_id`, and friendships use `friend_fighter_id`;
legacy names may be backfilled only when the loaded world has one unambiguous match. The transient story-key index is rebuilt once after initialization/load and
maintained on writes. Active/resolved counts are maintained incrementally; do not normalize or sort
the whole collection on an ordinary write, and prune only after a hard cap is exceeded. Narrative
copy must not consume simulation RNG, and transaction rollback must
restore story state with the owning event or paid action. Long prose and career timelines are built
only when their view opens. Run `narrative_system_regression_test.py` after any story trigger,
identity, persistence, matchmaking-context, or career-journey change; run
`narrative_performance_regression_test.py` after changing thread indexing, pruning, or calendar
integration.

Contract Sagas use `Fighter.contract_story_key` as their only live pointer. Renewal warnings,
renewals, expiry/release, free-agent signing, return and cross-company revenge hooks must receive the
fighter and known company names from the domain event already in progress; they may not discover
stories by scanning rosters, free agents, promotions, Results or Chronicle. When
`narrative_tracking_enabled` is false, the lookup helper must return before reading the story key so
the paired performance regression measures the entire feature cost. Clear the fighter pointer only
after a resolving return or revenge outcome; keep the bounded resolved thread as career history.

Staff Tenure stories follow the same pattern through `staff_id` and the optional
`staff_story_key` stored on the staff dictionary. Appointment, contract-warning, negotiation,
renewal, release and expiry actions receive the already-known staff record directly and must not
scan the staff market, promotions, rosters, Chronicle or Results. Normalize missing legacy keys to
an empty string in `ensure_staff_profiles()`. Store bounded `staff_ids`, `staff_names`, and
`staff_role` snapshots on the thread, use the direct key for Staff Profile presentation, and return
before key lookup when narrative tracking is disabled.

Staff career contributions are first-of-kind tenure beats. Scouting reports pass their already-known
scout; medical clearance, settled player events and fulfilled promises may resolve one lead from the
small player staff list only after a qualifying outcome exists. Never run a staff-discovery pass or
inspect archived events to infer a contribution. Bound `contribution_kinds` and
`staff_milestone_kinds` to 12, clamp `staff_legacy_score` to 0–100, deduplicate before writing, and
normalize malformed legacy values without consuming simulation RNG. Event-settlement contribution
writes remain inside the existing event transaction and therefore roll back with a failed commit.

Feeder Pathways use `Fighter.feeder_story_key` as their only live pointer. Loan, recall, paid
transfer, player/AI fight settlement, contract departure, and retirement hooks must receive the
already-known fighter and company; they may not discover alumni by scanning child rosters, parent
rosters, Results, Chronicle, or fight history. `record_feeder_fight_result()` must retain its early
two-key exit before story/company work, and player/AI result callers must avoid entering it when
both supplied keys are empty. Child
undercard results do not need a beat; child main/title results, the first parent bout, one featured
parent breakthrough, and a parent title can advance the bounded chapter. Clear the live key only on
resolution. Loan, recall, and paid-transfer commits use the shared domain snapshot so a late story
failure restores rosters, belts, contracts, cash, ledgers, Chronicle, story indexes, and RNG.

Breakout Runs use `Fighter.breakout_story_key` as their only live pointer. The decisive-result hook
must reuse the eight-point Giant Slayer comparison already calculated by
`evaluate_fight_achievements()`; do not recompute derived ratings or discover upsets from Results,
Chronicle, rankings, rosters, or fight history. A qualifying upset may open one chapter, while only
the directly linked fighter's later result, draw, or retirement can advance it. Bound follow-up
counters and recent result references, clear the pointer on resolution, retain the resolved thread
as career history, and keep the story-aware AI bonus inside already-credible candidate pairs. The
player event transaction must restore both the pointer and thread after a late settlement failure.

Career Crossroads use `Fighter.crossroads_story_key` as their only live pointer. A new chapter may
open only from the already-settled third consecutive in-universe MMA loss for an established fighter
(age 30+, at least 18 professional bouts, or popularity 45+). Origin detection may inspect at most
the first four `bout_rating_history` rows; it must never reconstruct form from complete fight
history, Results, Chronicle, rankings, rosters, or a calendar scan. Once active, draws, later wins or
losses, division moves, release/contract exit, and final-fight retirement must use the direct key and
known domain participants. Keep recent result references and counters bounded, deduplicate retries,
clear the pointer only on resolution, and retain the resolved thread as career history. Player event
rollback must restore the pointer and exact thread, and AI story value remains limited to candidate
pairs the sporting matchmaker already accepted.

Fighter Relationship chapters use the deterministic pair-ID story key plus each participant's
bounded `relationship_story_keys` list. Friendship and featured stablemate results may begin a
chapter; draws, rematches, direct ID-backed rivalry tension, and a later meeting after a camp split
may advance or resolve it. Never query the story index for every ordinary bout: when neither current
friendship/stablemate status nor either fighter's active-key list applies, return before constructing
the pair key. Cap each fighter's list at four, remove the key from both participants on resolution,
and keep the resolved thread in the participant index for profile/annual history. Result callbacks
must deduplicate by stable reference, consume no shared RNG, and remain inside the player event
transaction so rollback restores both fighter-local lists and the exact pair thread. AI story value
may consider the active thread only for an already-credible candidate pair.

Career Farewell chapters use `Fighter.farewell_story_key` as the direct bridge from a retirement
decision to the final opponent and result. `mark_retirement_fight_required()` opens the chapter;
MMA, game-AI, regional, draw, no-contest, and other-sport settlement must resolve it with both known
participants before roster retirement removes the fighter. Meaningful-opponent scoring may only
reorder candidates the sporting matchmaker already accepted. Rival, friend and relationship links
must use fighter IDs; former-opponent meaning must read bounded structured `bout_rating_history`
opponent IDs, never display-name fight-history text. Do not add a retirement discovery pass. The
ordinary result path must exit after the existing `retirement_pending` field check, callbacks must
deduplicate, and player event rollback must restore the pointer, thread, Chronicle and RNG state.

Academy graduation is one such owning transaction: its rollback snapshot includes `story_threads`,
and the transient story indexes must be rebuilt after restoration. Never allow a failed late
graduation hook to leave a thread for a fighter who was not actually created or transferred.

Fighter Career Timeline presentation may combine the selected fighter's bounded local histories
with `story_threads_for_fighter()`. It must not search Results, Chronicle, archived cards, or the
wider fighter world. Annual review selection may inspect the bounded story-thread collection once
at year rollover; it must remain capped and must not become a weekly/monthly discovery pass.

AI story intent is a bounded bonus inside the candidate pairs the matchmaker already evaluates. It
must use cached direct story-key lookups, must never create another all-pairs pass, and must not make
an otherwise invalid matchup legal. The deterministic calendar A/B disables this decision feature
in both arms so it measures tracking cost and RNG purity rather than intentionally different cards.

Promotion Rivalry chapters are two-company, 24-month cycles updated only by an owning contested
signing, academy-recruitment result, or sanctioned superfight. Callers must pass the known companies;
never discover rivalries by comparing every promotion or roster. Stable event references protect the
scoreboard from duplicate callbacks. Coaching Loyalty is likewise event-driven: significant gym
moves open or close a room-specific chapter, and completed meaningful fights update only the two
participants' direct story keys. `Fighter.academy_prospect_id` is the persistent bridge from academy
mentorship to senior-career outcomes; old saves default it to empty rather than scanning alumni.

Hometown Hero chapters are also event-owned. `schedule_event()`/the immediate event path may frame
an already-booked main or title homecoming only when the known fighter has at least 60 market
popularity (or an existing hometown thread). Player and AI result settlement then update that direct
fighter/region key through `record_hometown_fight_story()`. Do not search scheduled events, regional
markets, rosters, or result archives to discover homecomings. Once a home-title or market-icon
resolution exists, later epilogue beats must not overwrite its phase or resolution.

### Shipped-universe source of truth

New careers load `Databases\Default Universe.universe.json` through
`load_universe_database_pack()`. Its `fighters`, `combat_sports`, `companies`, `media`, and `regions`
sections are independently editable and are the source of truth for the shipped starting world.
The pack has a top-level schema version, and complex sections such as `fighters` and
`combat_sports` also carry their own schema versions. Python seed specs provide defaults, generated
depth, and repair fallbacks; changing only a fallback may not change a new game built from the
database.

`universe_validation.py` is the sole side-effect-free schema validator for editor, runtime, and release tooling. It returns actionable section/record/field issues rather than throwing on malformed user JSON. `load_universe_database_pack()` may normalise old packs in memory, but normal loading must never rewrite a source database; explicit reset/migration operations own backups and writes.

All runtime `Toplevel` creators in `admin.py`, `awards.py`, `events.py`, `persistence.py`, and
`views.py` must call `UIMixin.create_managed_window()`. Its default key combines the call site with
available fighter/entity identity, so repeated clicks replace stale popups without conflating two
different fighters. Long-lived screens may provide an explicit stable key.

Fighter Profiles are observational views. Opening or reopening one must not consume simulation RNG,
generate or synchronize ratings, migrate saved history, initialize child-sport circuits, appoint
champions, or otherwise mutate career state. Resolve the displayed employer, opponent, result,
championship and archive by `fighter_id`/stable record identity; ambiguous legacy names may be
omitted but never guessed. Apply scouting visibility to every rendering surface, including portrait
text and identity rows. Profile action visibility is only convenience: contract, comeback, transfer,
and weight-move transactions must revalidate Spectator Mode and current ownership at commit time.
Keep the fixed Profile footer inside the physical display and register fighter windows with the same
explicit key used for focus/reuse.

Use `database_editor.py` or a carefully reviewed data edit for starting-universe changes, then
validate the file. The standalone database editor changes universe database packs; it does **not**
edit an active career save.

Event-city choices and generated-fighter hometowns come from `REGION_CITIES` in `constants.py`.
Keep each city in its broad simulation market (for example, Belleville and Kingston are Canadian
locations), and add smoke coverage for both the booking selector and identity pool. The universe
database's `regions[*].areas` list describes larger tracked areas such as Ontario; do not duplicate
individual cities there merely to make them available for events.

Curated fighter identity edits in the shipped database must keep the full record in
`fighters.all_fighters` synchronized with its compatibility tuple in `fighters.player_roster`,
`fighters.free_agents`, or `fighters.promotions`. For example, Brett Akey's Belleville hometown is
stored in both his `all_fighters` record and his `free_agents` tuple. Validate the database and
retain a named identity assertion in `smoke_test.py` after changing either representation.

### Company ownership invariant

When `take_control_of_company()` transfers an AI promotion to the player, it must reconcile stale zero-month AI contracts first. Those fighters remain in the inherited roster and receive fresh 12-24 month exclusive contracts; a takeover must never mass-release a company's roster merely because legacy AI contract terms reached zero.

The MMA Child Promotions manager in `views.py` is an operations screen, not just a launch dialog. Keep its promotion table synchronized with child cash, stability, roster size, protected loans, parent distributions, and AI mode. Roster filters must only change display; loan, recall, and parent-transfer actions must continue to use fighter IDs and the world-layer ownership rules.
The manager must list only child promotions whose `parent_company` matches the active player company. Its child-roster status filter must not be applied to the separate parent-roster loan source. Parent profit-share transfers and child-fighter transfer fees must use the normal finance transaction recorder. Paid transfers require confirmation, respect closed parent divisions, and taking an expired AI-signed child fighter must assign a fresh contract rather than a one-month stub. Ordinary company takeover must reject child promotions. Empty launches must roll back capital and the promotion when no eligible opening roster can be signed. Champion loans vacate the parent belt before moving the fighter. Loan, recall, and paid-transfer actions are atomic and must retain their Feeder Pathway hook inside the rollback boundary. Load repair must clear stale loan markers for missing, mismatched, retired, or retirement-pending fighters; the manager must reset stale detail text after redraw, preserve duplicate identity labels, show the selected fighter's active feeder chapter, provide vertical roster scrollbars, and reuse one manager window.

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
authored male-only behavior; preserve its origin and roster-depth rules. A multi-fighter intake
batch must build the world-name collision set once, extend it after every generated recruit, and
reuse it for Eurasian renaming; do not rescan the complete fighter population per slot.

### Player-funded MMA child promotions

MMA child promotions are ordinary AI-managed `Promotion` objects with
`is_child_promotion=True`, `parent_company`, `child_strategy`, `parent_profit_share`, and
`loaned_fighter_ids`. They are launched from the Companies screen with player-selected startup
capital; the launch budget funds an opening MMA free-agent roster, after which the existing AI
card, contract, development, finance, and market systems manage the child normally.

The supported child identities are `Balanced`, `Youth Prospects`, `Big Names`, and
`Merit & Contenders`. The identity updates the child's persistent AI focus and card personality;
do not create a second matchmaking engine for it. Positive event profit distributes the configured
0-100% share to the parent company and records the transfer in the child's strategy/finance data.

Loans move a fighter from the player roster into the child roster while preserving the parent
contract. The fighter's `loaned_from_company`/`loaned_to_promotion` fields and the child's
`loaned_fighter_ids` index must stay synchronized. Child contract expiry, roster cuts, upgrade
replacements, distressed buyouts, retirement removal, and save repair must protect loaned fighters;
only the parent loan manager can recall them; the parent may also take an AI-signed child fighter by
paying the transfer fee. New fields require safe load defaults and a round-trip regression in
`smoke_test.py`.

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

`Fighter.style` is the supported primary compatibility and search identity. `secondary_style` is an
optional, distinct supported cross-training identity; display it through `Fighter.style_label` and
apply it only through bounded shared style helpers. Never store behaviours such as Dynamic Attacker
or Submission Hunter in either style field. New-universe secondary assignment is deterministic and
must not consume simulation RNG; old saves safely default to an empty secondary style.
Every `create_generated_fighter()` result must finish with a supported primary style and a validated
distinct secondary style. The final generator guard may normalize blank or legacy labels but must be
deterministic and must not add another random draw; smoke coverage should sample generated entrants.

### Mechanical intent

- Kicks depend on kick speed, power, technique, stamina, distance, and defense.
- Punches depend on hand speed, punch power, technique, head movement, guard, chin, and stamina.
- Grappling depends on takedowns and setup, sprawl, guard work, control, submissions and defense,
  stamina, and position.
- Stamina and momentum should visibly influence later exchanges.
- Ground, clinch, and cage position must reset or transition according to the rules; state must not
  leak impossibly across a horn.
- `clinch_controller`, `top`, `bottom`, damage, stamina, and unanswered offense use private per-bout
  fighter slots. Compare them through `fight_state_key()`, never a display name. An unanswered
  sequence advances only when significant strikes land, clears when the pressured fighter lands or
  creates a meaningful grappling/positional response, and resets at every horn.
- Tournament participant names are presentation. Resolve the aligned `fighter_ids` list for the
  bracket, replacements, and temporary state; use object identity for private in-memory snapshots
  such as pre-view fatigue so same-name entrants remain independent.
- Commentary must never describe new actions after a finish.
- Equal score totals must be capable of producing draws.
- End-of-fight output includes the completed rounds and scorecards where applicable.

### Round count

The event data decides championship pacing. A fight marked `title` or `main` uses the configured
`title_rounds` value, including player-selected six- and seven-round settings; ordinary fights use
the normal `rounds` count. Never hard-code five introductions or four transitions in the watcher.
Test title and non-title five-round main events plus an extended configured title fight.

### Commentary structure

Five-round fights generate enough text to exceed a Tk text widget's comfortable live-display size.
The engine and archived fight log retain every generated action call and the original round-summary
telemetry. The live watcher defaults to a derived `Broadcast` stream that may condense repeated,
low-value timestamped calls; `Detailed` mode and completed-bout review expose the complete stored
transcript. Viewer compaction must be deterministic, must not mutate the archive, and must never
consume a simulation RNG stream. Structural and evidential lines must always survive:

- tale of the tape and opening context;
- every round introduction;
- every horn/round transition;
- every round summary;
- stoppage and official-result lines; and
- decision scores.

The live watcher may redact exact judge cards until the official result, but it must not replace or
shorten the round-summary line itself. Apply any display name cleanup before inserting a line into
the Tk `Text` widget; post-insert formatting cannot repair text that was already presented or alter
its tags. `stability_test.py` must advance a real five-round title viewer through each round and
verify all five original summaries, the scorecard reveal, metrics, and official result remain visible.

The live density control is presentation state. Switching an active or completed bout between
Broadcast and Detailed must rebuild only the reached visible lines, preserve the same raw-source
playback frontier, keep sealed scorecards sealed and leave the archived transcript unchanged. Round
separators, knockdown emphasis and finish emphasis are Tk tags/layout only. The visible personality
indicator reports the voice saved with that fight log; it must not imply a mechanics setting.

`FIGHT_COMMENTARY_ROUND_LINE_LIMIT`, `FIGHT_COMMENTARY_ROUND_HEAD_LINES`, and
`FIGHT_COMMENTARY_ROUND_TAIL_LINES` bound only ordinary timestamped calls in the derived Broadcast
view. Important middle-round evidence outranks head/tail position, so never use a blind slice. Never
deduplicate or trim `FightResult.commentary`, the archived `lines`, or the structured trace. A legacy
technical suffix may be removed from Broadcast prose, while its target, defense, follow-up, move and
position remain available in Detailed commentary or `round_analysis`.

Completed offense and ground-state progress are important Broadcast evidence. Landed standing
strikes, successful takedowns, landed ground strikes, passes, sweeps/reversals, escapes and stand-ups
receive priority over routine movement; identical calls remain capped at two even when their position
or outcome makes them high-priority, and repeated failed
attempts or passive control may condense. A same-position sweep is proven by changed
top/bottom ownership even when the position label remains `guard`. Any compact note must count the
actual omitted standing, standing-striking, takedown, ground-control and ground-striking lanes without
inventing success, damage or a position change.

Fact-driven wording variation must be selected from stable trace/bout material or the isolated
presentation stream; it must never call the mechanics, officiating, judging or process-global RNG.
Every exchange call must agree with the recorded actor, move, outcome, named defense, counter flag and
settled position. Context is evidence-bound: signature/mastery comes from the selected move payload,
stance and plan from trace state, damage/momentum from completed public deltas, camp/coach from fighter
data, and championship/rivalry stakes from the scheduled bout and identity-safe relationship helpers.
The bout-local commentary profile may record derived standing, ground and defensive strengths, but it
is presentation evidence only: use the strength relevant to the recorded weapon or transition, never
consume RNG or change an exchange. A failed submission trace must retain the actual technique chosen by
`submission_technique()`, a legal named defense and a natural consequence. A referee inactivity reset
is a separate structured fact; never credit the preceding ride/cling action with escaping to range or
append old-position colour after a fighter has reached the feet. Ground presence lines must respect
current top/bottom ownership and every `GROUND_POSITIONS` state.
Do not infer a coach, rivalry, stance switch, plan change, blocked strike or successful counter from
style flavour alone. A failed sweep, stand-up, pass or transition must be described as an attempt,
not settled success. KO/TKO attribution must use causal damage/impact evidence rather than whichever
non-damaging move happens to be the final trace row.

Required regression scenarios include:

1. a five-round title decision with all five introductions and summaries;
2. a non-title five-round main-event decision with the same structure; and
3. a late round-five finish with the round-five introduction and official result preserved.

4. a configured seven-round title decision with all seven summaries, transitions, scorecards,
   metrics, and the official result preserved.

### Outcome calibration

`fight_engine_audit.py` and `analysis/fight_engine_baseline.json` are the preservation authority for
the staged fight-engine roadmap. The UI-free harness clones its inputs, restores process RNG, and
captures per-exchange evidence without changing the underlying engine result. Before and after each
fight-engine phase, run `analysis/generate_fight_engine_baseline.py --verify
analysis/fight_engine_baseline.json`. Use `--exact-parity` only for an architecture slice that does
not intentionally remove legacy presentation draws from the combat stream. RNG separation is
accepted on the locked distribution gates, with hard overall/KO/TKO limits and confidence-aware
small-group checks; do not require identical individual outcomes after stream decoupling. Do not
regenerate the checked-in baseline after a code change merely to make drift disappear. A deliberate
baseline replacement requires an explicit balance change and synchronized report/document updates.
`analysis/fight_engine_action_baseline.json` is the pre-move-expansion authority for action frequency,
effectiveness, damage, energy, counter, position and finishing contribution. Regenerate it only for
an explicitly approved mechanical baseline replacement; verify it with
`analysis/generate_fight_action_baseline.py --verify analysis/fight_engine_action_baseline.json`.
The canonical isolated runner executes this verifier after the result baseline so presentation-only
changes prove that neither finish rates nor the amount and effectiveness of the ground game moved.

`compare_to_accepted_calibration()` is the exact headline release gate layered over the older
tolerance report. The canonical isolated runner executes the complete 3,840-fight verifier and must
reject a one-bout change from 2,319 finishes, 633 KOs or 731 TKOs. Do not weaken this to rounded-rate
comparison: the displayed 60.39% / 16.48% / 19.04% values are derived from those integer counts.
It must also reject a competitive finish rate outside 48-54%, a competitive submission-family rate
outside 15-19%, zero Doctor or Injury Stoppages, missing five-round evidence, or fewer than 6% of
five-round finishes in rounds four and five. The current accepted corpus has 1,408 competitive
finishes (48.89%), 488 competitive submission-family finishes (16.94%), four Doctor Stoppages, ten
Injury Stoppages, and 164 of 839 five-round finishes in rounds four or five (19.55%). These checks
reconcile the historical finish audit without applying its obsolete global retunes: mismatch bouts
drive the 60.39% aggregate, while competitive fights already meet its realism bands. Do not lower
global KO/submission conversion or halve championship dampers unless the user explicitly authorizes
a new mechanical baseline.

`FINISH_METHODS`, `KO_METHODS`, `SUBMISSION_METHODS`, and `KNOCKOUT_AWARD_METHODS` in `constants.py`
are the downstream method-classification authority. Career stats, seasonal counters, recovery,
contractual finish bonuses and excitement use the shared finish families. Knockout of the Year uses
the narrower highlight set so Doctor and Corner Stoppages cannot win a strike-highlight award.
Never reintroduce substring or exclusion-based finish detection in a consumer.

The original frozen baseline rates are 59.64% finishes, 15.70% KO, 19.66% TKO, 22.29% submission
and 1.17% technical submission across 3,840 fights. The accepted post-roadmap calibration is 60.39%
finishes, 16.48% KO and 19.04% TKO. Competitive low/mid/high and mismatch results are separate groups;
follow the tolerances in `FIGHT_ENGINE_DEVELOPMENT_PLAN.md`. Detailed-skill coverage also
distinguishes direct fight inputs from `dedication` and `weight_cutting`, which operate through camp/
development and weigh-in state respectively. Do not add a detailed fighter attribute without either
using it mechanically or documenting and testing its pre-fight role.

`FightResult` is the structured MMA result boundary. `simulate_fight_result()` returns it directly;
legacy callers continue through `simulate_fight()` and its five-item tuple. Native trace events use
private `a`/`b` slots and retain action, position ownership, gas, location damage, cuts, knockdowns,
strikes, takedowns and submission deltas, followed by exactly one `official_result` event. Adding
trace evidence must not consume RNG or change any baseline signature.

`fight_moves.py` is the canonical MMA move registry. Move IDs are stable trace/save-facing identity;
definitions must use supported positions, styles and detailed skills, and follow-up IDs must resolve.
Broad actions remain the calibrated resolution boundary. Deterministic move selection may use detailed
skills, style, stance, matchup and a real counter window, but must not consume mechanics, officiating,
judging or presentation RNG. Move energy, miss risk and counter vulnerability may only alter later
legal move identity through bounded, decaying bout-local state; they must not alter broad gas, damage,
landing or finish conversion. An unavailable move uses
an explicit `generic_<action>` fallback rather than inventing an illegal technique.

Release move audits must keep the frozen `matchup_specs()` corpus unchanged. Supplemental style coverage
belongs in `move_report_specs()` so the exact 3,840-fight result/action baselines remain comparable. A move
missing from the general sample is not automatically dead: the targeted registry reachability check must
prove whether a legal, skill-supported specialist can select it. Dominance comparisons must use the same
parent action and legal position, not aggregate techniques that cannot compete in the same state.
Direct registry reachability is not proof of full-fight reachability when a test supplies a target or position
that the broad resolver never emits. New ordinary standing and common-position ground content must also appear
in the representative 880-fight report; reserve probe-only absence for genuinely rare specialist
positions/actions. The current registry has 176 moves, including one exclusive combination and one
exclusive finisher for each of the 18 supported styles, ten earlier expanded standing combinations,
six uncommon authored standing finishers and 23 expanded ground techniques. The turtle wrist-ride striking chain
is the only latest addition intentionally absent from the representative corpus; targeted reachability and
the specialist transition path remain its gates.

Moves tagged `style-combination` must name exactly one supported `preferred_styles` owner, retain at
least three ordered `components`, and be filtered before scoring unless that owner is the fighter's
primary or secondary style. Signature or mastery data must never bypass this eligibility rule. These
chains remain identities beneath one already-resolved broad action: their components, follow-ups and
commentary may change, but they must not add a strike, landing, damage, transition or finish roll.

Moves tagged `style-finisher` follow the same single-owner primary/secondary-style restriction and
must be either a strike or submission. Their deterministic appearance window may make an already
selected technique more recognisable, but it must never create or convert a KO, TKO, submission,
damage event or stoppage. KO/TKO narration must use trace-backed impact from the causal move;
submission narration must use the last resolved submission payload. Every style finisher must remain
reachable, appear in the 880-fight representative report and preserve exactly one official result.
When a fighter owns another legal signature finisher, that individual signature takes selection
priority over the generic style finisher during the bounded authored-finisher window.

The Standing group includes `combination_punching`, `body_punching` and `counter_timing`. Legacy
non-empty detailed profiles derive them in `ensure_detailed_skills()` from existing saved ratings;
never replace them with generic 50s or consume RNG during load. Distance management remains the
existing footwork/feints/mobility/reach bundle rather than a duplicate detailed attribute.
When a detailed-skill group expands, preserve development exposure as well as serialization. Standing
training scales its successful-block point budget for these three added skills; otherwise a fixed budget
silently dilutes every striker's development even though fight-result calibration remains unchanged.

Kick-tagged registry moves must define a supported target, `side`, `range_band`, and at least one
`defense_families` entry. Spinning/flying/high-risk techniques require a meaningful minimum-skill
floor, energy/counter risk above neutral, and the deterministic rarity gate in move selection. Reuse
the existing high/low/creative kick, knee, elbow, flexibility, mobility and reflex ratings unless a
future skill audit proves a genuinely distinct axis.
The `finisher` tag is a rare identity gate, not a finish modifier. A finisher must be a skill-gated
standing strike with above-neutral energy and counter risk; its shared deterministic gate may select the
named move only after the broad action has resolved and must not consume RNG or alter finish conversion.
When a KO or TKO has causal trace evidence, the registry move is the authoritative strike name. Legacy
finish-color banks may not leave a second, contradictory uppercut/hook/kick beside that causal move.

Takedown-tagged registry moves must define `entry_family`, non-empty `defense_families`, and only
legal `finish_positions`. The resolved trace remains authoritative for the actual position path and
controller; registry metadata must never claim a finish position the broad resolver did not reach.
Hand fighting, underhooks and wall walking currently reuse clinch control/defense, cage wrestling,
get-ups and scrambles rather than adding duplicate detailed attributes.

Submission-tagged registry moves must define a position-legal `attack_path` and non-empty
`failure_outcomes`. The resolver's recorded `submission_escape` and actual position path remain
authoritative; move metadata may describe legal possibilities but must not invent a finish or a
transition. Chaining currently reuses transitions, positional ability, submission attack, leg locks,
control, scrambles and fight IQ rather than adding a catch-all submission-chaining rating.

Common ground moves must be restricted to positions where their broad action can actually be chosen.
Position-specific ground striking still resolves through `ground_strikes`; passes/climbs through
`advance_position`; sweeps through `sweep`; recoveries/get-ups through `recover_guard` or `stand_up`; and rides
through `ground_control`. Named identity must not directly change damage, success, position or finish chance.
Every authored ground-strike chain needs a factual component template that reconciles realistic 10-26-strike
broad volume, and a ground TKO must name the causal registered strike chain rather than generic legacy copy.
An effective registry move tagged `control` may seed one legal bounded follow-up from an existing `control`
outcome; this changes only later move identity and must never grant a free exchange or change control scoring.

`Fighter.signature_moves` contains at most three unique stable registry IDs. New-universe generation
may derive skill-supported signatures deterministically; ordinary save load must only normalize known
IDs and must not invent a new set. A legal signature receives a bounded selection preference but
never bypasses minimum skill, position, target, counter-window, defense, or finish resolution.
`career_signature_stats` folds the last fight's attempts/effective uses/finishes during the same
career-stat commit that clears `last_fight_stats`; preserve fighter-ID separation in persistence and UI.

`Fighter.move_mastery` contains normalized 0-100 values keyed by a move ID or `defense:<defense_id>`.
It is persistent fighter development, but it may only shape named technique selection beneath the broad
resolver. Camps may improve focus-aligned mastery and grant a signature at the audited threshold;
academy prospects retain their own mastery dictionary and copy it on graduation; annual veteran decline
may reduce high mastery after `prime_end + 2`. Legacy load defaults to an empty dictionary and must not
consume RNG or invent mastery merely by opening a profile.

`DEFENSE_REGISTRY` is the canonical defensive identity surface. Every exchange trace retains a known
`defense_id` and payload selected from the attacking move's legal defense families and the defender's
skills. Named defense is evidence, not a second success roll: never use it to retroactively change the
already-resolved outcome or consume another combat draw.

Tactical move reads are bout-local, derived only from earlier public trace, and capped per counter.
Plans may weight matching move tags; body/leg/setup evidence may open later families; repeated move IDs
may be penalized; and opponent-pattern counter bonuses require a real counter window. Preserve
`selection_reasons` for explainability. Never persist these reads, scan career history during a fight,
or convert a move-family preference into direct landing/finish probability.

Registry follow-ups may create a bout-local move chain only after effective use. A matching legal
follow-up receives a bounded selection preference for at most two ticks in the same round, and the trace
must identify its source and completed step. It remains one ordinary broad action, never a free attack.
Multiple follow-ups are legal branches. Choose only a branch valid for the resulting position, retain
the options/reason in trace evidence, and let a named frame/evasion/escape select the alternate branch.
Authored strike-combination templates must identify their actual component weapons and reconcile sequence
numbers and landed totals at realistic broad-action volume; a generic action fallback is not sufficient
coverage for a newly named sequence.
All supported primary styles must retain explicit tag preferences and stay distinguishable in the
pairwise release-report distance check. Stance and striker/grappler matchup reasons must remain traceable.
Dynamic stance changes are bout-local and cooldown-bound. They require a natural switch stance or high
footwork/adaptability, retain from/to/round/tick/plan evidence, and must not mutate the fighter's saved
base stance or add a new mechanics RNG draw.

Archived fight logs may persist bounded `round_analysis` derived from their completed trace. Replay UI
must tolerate old logs without it and show only recorded moves, defenses, sequences, stance switches and
plan history; it must not reconstruct results, expose sealed cards early or mutate career state.

Fight presentation must render from the completed trace. Natural Broadcast prose uses the recorded
actor, move, outcome and salient target, defense or position; it must never join a named move to the
older broad-action `result` text. Detailed commentary and `round_analysis` retain target, defense and
meaningful follow-up labels without raw bracket metadata. Finish prose must use the final exchange's
actual move and settled position, retain authored submission/medical/injury/head-kick/walk-off detail,
and contain at most one intervention clause and one official announcement. A body- or leg-kick
knockdown is not an `injury_stoppage`; only the separate body/leg stoppage check may assign that
finish method. Doctor review uses structured cut evidence and may become eligible only at the
between-round tick. Presentation-only walk-off variation may use the presentation stream, but an
existing mechanics draw must not be removed, added or reordered merely to select wording.
Round/UI summaries expose bounded move-family effective/used counts, never raw unbounded dumps or
unsealed judge totals. `last_fight_stats`, FightResult metrics and `career_move_family_stats` must
reconcile with the same exchange events; presentation must not draw simulation RNG.

At the start of a bout, `simulate_fight()` establishes explicit mechanics, officiating, and
presentation streams. All combat draws go through `fight_mechanics_rng()`, referee/stoppage/judging
draws through `fight_officiating_rng()`, and wording through the presentation helpers. Do not add a
direct `random.random()`, `random.randint()`, or `random.choice()` call to `fight_engine.py`; the
focused regression treats one as an accidental stream leak. The caller's public RNG advances to the
combat stream's final state so sequential unseeded cards continue to vary.

Commentary variation uses the bout-local presentation RNG through `fight_presentation_choice()` and
`fight_presentation_random()`. Do not add global `random` calls for wording, clocks, ambience, or
phrase selection. A foul or other event that changes gas, damage, position, scoring, or stoppage
risk belongs in a mechanical resolver before its text is rendered; `dynamic_flavor_line()` must
remain presentation-only. The phrase-bank regression must keep winner, method, round, stats and
cards identical when wording is replaced.

`fight_commentary_mode` defaults to `Broadcast`; `fight_commentary_personality` defaults to
`Balanced`, with `Technical`, `Excitable`, and `Concise` as presentation-only alternatives. Both live
in `rules`, require old-save normalization, and may affect wording or density only. Corner advice may
cite completed public trace evidence such as gas, damage, control, repeated moves and effective
families; never expose hidden ratings or repeat developer-facing text about an unassigned plan.
Between-round feedback must name a verified head coach and Gym when available, give a factual round
read and a separate actionable instruction, and vary delivery by commentary personality without RNG.
If both opponents share one verified Gym, identify each fighter's camp corner without assigning the
same head coach to opposing stools. The commentary report permanently gates speaker/fighter identity,
actionable wording and hidden-rating leakage across representative complete fights.

`TRAIT_COMMENTARY_INTROS` must cover `TRAITS` exactly. Every saved trait receives one natural opening
line, but a live trait call requires completed trace evidence matching its claim: target, move tag,
counter, position, submission attempt, plan change, accumulated damage, recorded gas, timing or bout
context. `record_fight_trace_exchange()` stores the selected line and enforces at most one contextual
trait call per fighter per round and two per fighter per bout. Rendering that line is deterministic,
must not consume any RNG stream, and must never imply survival, a finish or an injury that has not
already been resolved. Do not restore the older random trait branches in `dynamic_flavor_line()`.

Camp commentary must resolve `Fighter.camp` against an actual current `Gym` before naming a coach,
city, region or specialty. Saved camp strings may instead be promotion, feeder, academy, unknown or
legacy labels; introduce those with natural neutral wording and never infer Gym facts from the label.
When both opponents resolve to the same verified Gym, emit one stablemate-room introduction rather
than assigning the same head coach to two opposing corners. A contextual
camp call requires a completed exchange matching one of the resolved Gym's recorded specialties:
boxing, kickboxing, wrestling, BJJ, sambo, clinch, gameplanning or conditioning. Store the selected
line on the exchange trace, cap it at one per fighter per round and two per bout, preserve it in
Broadcast, and consume no RNG. `Prospect Development` is opening identity only unless future trace
evidence provides a genuine live-fight predicate. Focused coverage must compare the same seeded bout
with and without verified Gym metadata and require identical result, metrics, scoring, mechanical
trace and process RNG state.

Audit finish rates by fighter tier, not only across a random-paired pool. Random pairing
over-represents mismatches, which finish more easily than realistic cards.

MMA judging consumes `round_evidence_from_trace()` only. Do not award score value for gas,
professionalism, discipline, home support, experience, pressure, popularity, or names; those inputs
may change execution but are not judging criteria. Apply effective striking/grappling first,
effective aggression only when that evidence is close, and control only when both are close. Judge
variance belongs on the judging substream and only inside the ambiguity band, so scoring work cannot
change a later stoppage draw or reverse clear dominance. Store the player-facing verdict separately
from canonical `Decision`/`Draw` method values for save and downstream compatibility. Every 10-8 and
point deduction must retain round evidence in the official card and trace.

In-bout `damage`, `head_trauma`, `body`, and `leg` are persistent trauma channels; `hurt` is the
transient stun/instability channel used by immediate survival and calibrated stoppage checks. The
legacy `head` channel is a short-term reaction load and may settle during survival, while every head
impact must also increment `head_trauma`; trace and post-fight metrics expose only the permanent
channel. Defensive success, `survive`, and `recover_between_rounds()` may reduce `hurt` and restore
bounded gas, but must never subtract persistent location damage. Body trauma affects output/fatigue,
leg trauma affects mobility/kicks/shots/stand-ups, and head trauma affects reactions. Cuts use `cut_state`
  records with location, severity, bleeding, swelling and vision risk while the numeric `cuts` count
  remains compatibility telemetry. `last_fight_stats` is the shared Fight Night/post-fight medical
  record; recovery logic must read its damage and `cut_details` rather than inventing unrelated harm.
  Run `set_post_fight_recovery()` and `apply_visible_trauma_consequences()` before
  `commit_career_stats()`, because that final commit clears `last_fight_stats` after the medical
  evidence has been consumed.

Visible damage narration is a deterministic presentation layer over those persistent totals. A bout
latches each head, body and leg milestone once, records the structured event in its trace, and retains
the corresponding line in Broadcast and round analysis. It must not consume any RNG, alter trauma,
or add a stoppage opportunity. Broad milestones may describe only supported visible states such as
bruising, guarding, a weight shift or a limp; never infer fractures, organ damage, concussion, or an
exact body-part location. Exact location, bleeding, swelling and vision language must come from the
structured `cut_state` record. When damage copy changes, run the focused milestone/RNG regression,
the commentary report and both frozen result/action baselines.

Fight plans are scheduled-bout state keyed by `fighter_id`, never display name. Player-created
bouts must store an explicit plan for every known corner; `apply_world_data()` normalizes supported
values and gives legacy missing entries Balanced. AI/world bouts must set `ai_controlled` so
`ai_fight_plan()` uses the shared execution model. A payload with no plan marker is a compatibility
bout: it stays Balanced and does not begin automatic between-round switching. Plan effects belong
in action weights, target shares, counter opportunities and energy cost—not direct result or finish
modifiers. `adapt_fight_plans()` may read trace evidence, gas and visible trauma only. Evidence-led
changes retain the repeated opponent move or successful own family, adjustment round and confidence;
do not oscillate more than once in a round. When changing
plans, run `fight_engine_regression_test.py`, the save/load smoke test and the frozen 3,840-bout
verifier; do not alter `competitive_finish_conversion()` or regenerate the baseline to absorb drift.

Each exchange trace must retain a bounded `exchange` chain with setup, defensive response, counter
opportunity/consumption, follow-up, ordered combination components and no more than five phases.
Derive semantic labels from the already-resolved action, position and skills; recording trace detail
must never consume another mechanics draw. A counter is valid only when a prior failed or defended
attack created its `counter_window`. Combination components are evidence for aggregate strike stats,
not extra attacks: their landed count must stay at or below attempts. Preserve deterministic chains
and the controlled Counter-striking-versus-Pressure regression when changing initiative or actions.

`ALLOWED_FIGHT_TRANSITIONS`, `GROUND_POSITIONS`, `validate_fight_transition()` and
`set_fight_position()` are the MMA positional authority. Ground states require distinct `a`/`b`
top and bottom owners and no clinch controller; open range retains none. Use
`record_intermediate_position()` for a real but unconsolidated state inside one exchange, and keep
its complete validated `position_path` in the trace. Elite specialists may consolidate a failed shot,
standing rear lock or leg entanglement into a persistent next-tick state only at the audited thresholds;
the 720-fight specialist report must continue to prove each state has legal follow-up action families.
Other brief positions require the resolver to award durable control. Submission attempts that do not
finish must set `last_submission_escape`
with their retained, recovered, reversed or worsened consequence. Any new grappling position needs
an allowed entry, exit, action selection, ownership test and commentary consistent with the trace.

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

All contract money and percentages are domain-validated, not merely widget-validated. Purse,
signing bonus, win bonus, finish-bonus percentage, PPV points, and guaranteed fights cannot be
negative, and invalid input must fail before cash or roster state changes. An agreed purse is paid at
its full contract value; company scale cannot silently discount it on fight night. Projection,
actual payout, the finance ledger, and the event report must consume the same clause calculation.
Every official player bout, including a draw, consumes one guaranteed fight. Ordinary guarantees
remain visible until fulfilled, and an expired deal never renews for free: use explicit negotiation
or the enabled paid auto-renew workflow.

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

Opening gym membership must be capacity-aware. Shipped elite rooms should not begin at several
times their capacity, because `gym_attention_multiplier` then suppresses the development system the
gym is meant to showcase. Database/seed regressions should flag ordinary gyms above 150% opening
load and keep regional team labels geographically consistent with tracked gyms.

The gym viewer is accessible from the World Hub. If gym fields change, inspect and usually update:

- the `Gym` dataclass;
- `seed_gyms`;
- serialization and `apply_world_data`;
- `refresh_world` and `open_gym_viewer`; and
- `smoke_test.py` when core assumptions change.

Season statistics are fed by `record_season_result` for every decisive player and AI fight.
`run_end_of_year_awards` runs at the year rollover and appends to `awards_history`. Adding a new fight
path without season tracking silently biases awards toward whichever path still records results.

### Staff employment and effects

Staff are dictionary records in `self.staff` and `self.staff_candidates`, seeded in `seeding.py` and
repaired by `WorldMixin.ensure_staff_profiles()`. New or migrated records carry a role, skill,
salary, morale, `contract_months`, `contract_type`, `contract_start_month`,
`contract_expiry_month`, and negotiation heat. Old saves must receive those defaults without losing
the existing staff member.

`constants.STAFF_ROLE_EFFECTS` is the player-facing source of truth for the seven staff roles:
Scout, Doctor, Marketing, Matchmaker, Drug Testing Officer, Broadcast Producer, and Talent
Relations. Every listed role needs both a readable explanation in the Staff screen and a simulation
hook. Staff quality and morale flow through `staff_skill()` and `staff_effect()`; do not add a role
that only changes a label. Current hooks cover scouting and academy reports, recovery and medical
costs, hype and commercial reach, matchup/card quality, drug-test accuracy and cost, broadcast
quality/reach/production cost, and fighter negotiation leverage. Point effects and cash-valued
negotiation benefits are separate: use `staff_effect()` for bounded gameplay points and
`staff_negotiation_discount()` when converting Talent Relations quality into a dollar discount.
Manual drug testing must use the same compliance discount model as event accounting.

Monthly world progression checks staff expiry warnings before decrementing contracts. Expired staff
leave payroll and the roster unless finite Scout work (a report, search, or academy-network setup) is
still using them; that Scout is held for one month so the assignment can finish. An established
ongoing academy network is not finite work: contract expiry closes the network and its open leads
instead of renewing the assigned scout forever. Hiring, renewal, and firing use the Staff screen's
negotiation/severance actions, and firing a busy Scout is blocked. The Expiring Contracts tab is a
filtered operational view, not a second staff list: actions must resolve the selected staff member
by identity and continue to use the world-layer contract rules.

Scouting assignments resolve both fighters and staff by durable IDs. A legacy name-keyed fighter
report may migrate only when the name identifies exactly one live fighter; ambiguous reports must be
quarantined and must never become a read-through fallback for every namesake. Load repair must not
consume simulation RNG, and a legacy report without a trustworthy completion marker is stale rather
than newly current. Starting a replacement report keeps the prior completed snapshot available until
the new work succeeds; cancellation or observation expiry restores that snapshot. Cancelled,
expired, and stale dossiers are eligible for later talent-search rediscovery. Completed searches
retain their ordered fighter-ID lead list, while long assignment/search histories are bounded.
Pending reports contain no hidden-rating-derived notes or estimates. Opinion notes are generated only
at completion and remain separate from structured public/live-fight evidence. Automatic department
work is paid and capped at one dossier per calendar week. Talent searches rank existing world fighters
and must never create supply as a fallback; market churn owns new fighter creation. Search Aim selects
candidate scope, Search Priority changes ranking within that scope, and signing Logic controls the
post-report recommendation. Age/style constraints may return explicitly labelled Near Matches when
the exact pool is thin. Standard briefs finish normally, Priority briefs trade extra cost for time,
and Ongoing briefs retain a scout slot and refresh every 13 weeks; persistence and workload checks
must treat `Monitoring` searches as active. Region knowledge, current report state, bounded prior snapshots, ID-safe
watchlists, structured scouting history, and alert dedupe state are persistent. Report ageing begins
after 26 weeks, and exact current ratings require a comprehensive high-confidence repeated Full
Evaluation; do not turn a single report into a permanent exact-rating unlock. Every decisive and draw
MMA result path must pass ID-first opponent, outcome, method, fight context, and `last_fight_stats`
evidence to `complete_fight_observation()` before `commit_career_stats()` clears the live metrics.

When changing staff behavior, update `constants.py`, seeding, world progression, persistence/load
repair, `ui.py`, and `views.py` together. Add smoke coverage for role descriptions, offer scoring,
legacy migration, expiry removal, and round-trip persistence. Review the fighter Contracts tab as
the parallel player-facing negotiation pattern so staff and fighter contract UX remain consistent.

## 12. UI, Themes, and Accessibility

The user strongly dislikes unreadable or cluttered UI. The game is normally played maximized, but
layouts must still degrade cleanly at smaller supported widths.

- Avoid hard-coded white or pale backgrounds. Use `self.colors["cream"]`,
  `self.colors["text"]`, and the active palette.
- Refresh methods for lazily built screens must start with widget-existence guards. A domain action
  such as starting a scouting report may be used before Staff, Finance, or another screen is built;
  successful state changes must never fail because an unrelated tree does not exist yet.
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
- Matchmaking's Available Fighters tree always retains all 20 underlying columns. Its Essentials,
  Readiness, Form & Fitness, and All 20 presets change only `displaycolumns`; they must not rebuild
  rows, clear selection, or make any metric unreachable. The Compare Selected action reuses the
  shared fighter-comparison window instead of duplicating a second matchmaking tree. Its five
  booking actions use one row on wide panes and the 3+2 grid below 700 pixels; preserve both modes.
- Ordinary Available Fighters row clicks intentionally toggle that row into or out of the current
  selection without requiring Ctrl, for both matchup pairs and 4/8-fighter tournaments. Double-click
  must resolve and open the fighter directly under the pointer rather than the first selected row.
  Keep Matchup Insight synchronized with the empty, one-fighter, pair-ready, and tournament states.
- `configure_show_details_layout` owns the expanded Show Details geometry. It grids stable Event /
  Venue, location/provider, date, primary-action, and show-tool frames into wide, medium, or narrow
  arrangements; never rebuild or reparent their widgets. Keep `schedule_status`,
  `event_broadcaster_status`, and `event_atmosphere_status` managed and wrapped in every mode, and
  retain the canonical field attributes because refresh and event code writes through them.
- Matchup Insight preserves detailed selection history, booking context, and the row-colour guide
  behind a named persistent disclosure (`rules["ui_matchup_insight_collapsed"]`). Empty booking
  notice and title-warning labels must not reserve table height, but must reappear immediately when
  their variables contain actionable text.
- Collapsible content must use `disclosure_section`: its named Expand / Collapse button and summary
  remain visible when content is closed. The three disclosure states live in save-compatible `rules`
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

- Base: `Dark Mode`, `Fight Night`, `Classic Green`, `Light Office`.
- Promotion: `BAMMA`, `UFC`, `PFL`, `Cage Warriors`, `ONE Championship`, `RIZIN`, `KSW`, `LFA`,
  `Oktagon`, `BRAVE`, `ACA`.
- Combat sport: `Boxing`, `Kickboxing`, `Muay Thai`, `Wrestling`, `BJJ`.
- Sports media: `Sky Sports`, `ESPN`, `BBC Sport`.
- Special: `Matrix`, `Champion`.

When changing shared UI, verify representative dark, light, promotion, and special themes, not only
the currently selected theme.

`Dark Mode` is the default startup theme. Plain Tk list controls must use `self.colors["tree"]`
and `self.colors["text"]` at construction time and remain covered by `retheme_plain_widgets` so
theme changes never expose a light-gray native control.

The academy's `active_challenge` and `challenge_history` are persistent coaching decisions. New
challenge choices must resolve through world-layer methods, update the prospect's development and
finance/amateur ledgers, and be repaired with safe defaults for older saves. The academy screen
must expose the active decision without interrupting calendar advancement with an unconditional
modal prompt.

Academy prospects and graduates are identity-first. Challenges, amateur opponent ledgers, replay
telemetry, alumni updates, and graduate Profile actions use `prospect_id` or `fighter_id`; a name is
only a unique legacy fallback. Academy repair normalizes null or malformed collection fields before
iterating them. Automatic showcase status must derive from `last_showcase_week` and the four-week
card check rather than presenting the compatibility-only `showcase_weeks` value as a countdown.
Individual prospects retain a six-week bout cooldown. Weekly training must preserve a meaningful
fatigue trade-off between Light, Standard, Intensive, and Recovery workloads.

Academy schema 6 adds five connected systems. `development_plan` is one active 4/8/12-week block;
completion writes an immutable row to both the prospect's `development_reports` and the academy's
`season_history`. Amateur records retain competition tier and opponent rating, which drive quality
points, strength of schedule, tournament eligibility, titles, and graduation readiness. Youth
trait, satisfaction, loyalty, promise and retention history are persistent; a broken promise or
unsustainable workload may cause a real recorded departure. Graduation destinations are explicit:
main roster, MMA developmental, an open player combat-sport division, or a regional feeder with a
12-month `released_rights` row. Active rights are exercised from Academy Alumni through
`exercise_academy_matching_right()`, which revalidates the fighter, division, cash and feeder belt,
then records canonical signing finance. Do not implement these as UI-only labels.

Major non-child, non-feeder AI promotions store their youth programme under
`Promotion.strategy["youth_academy"]`, which is already covered by Promotion serialization. Rival
cohorts are compact academy prospect dictionaries until graduation, then become ordinary Fighters
on the owning promotion roster. `process_rival_academies()` runs once at week 1, and rival bids on
player-network leads must preserve the lead's `prospect_id`. Keep intake bounded and include rival
academy throughput in long-run population audits before increasing its cadence.

Tournament entry, academy graduation, and matching-right exercise are domain transactions. Stage
cash, canonical finance, the prospect/academy ledgers, affected rosters and belts, narrative queues,
and RNG before their first mutation; a late fight, story, finance, or roster hook must restore that
state and return a failed action. Schema-six scalar repair must normalize malformed values as well as
missing ones. Rival cohort development may raise a stored readiness rating but must never lower it
when recalculating the compact broad-skill average. Keep the rollback assertions in
`stability_test.py` whenever these flows change.

Fighting Academy and Combat Sports are main notebook pages, not Toplevels. Their ownership and
refresh rules:

- `build_academy_tab` and `build_combat_sports_tab` are the registered screen builders; both are
  lazy, like every other screen. The academy delegates to `render_academy_screen`, which owns the
  page content and can rebuild it in place.
- The academy workspace is assembled against a single container widget held in `_academy_window`.
  It is a frame inside `academy_tab`, never a window: do not reintroduce `geometry`, `minsize`, or
  `WM_DELETE_WINDOW` handling there.
- An unbuilt academy renders an inline empty state offering the build purchase. A tab cannot open a
  modal every time it is selected, so the purchase decision belongs on the page.
- `refresh_academy_tab` and `refresh_combat_sports_tab` are the only refresh entry points.
  `refresh_academy_tab` rebuilds when ownership changes so buying an academy elsewhere replaces the
  empty state without a restart.
- Neither page appears in the `refresh_all(full=True)` sweep. `refresh_current_screen` builds a
  screen on demand, so listing them would construct widgets for a player who has never opened them.
  They are refreshed after the sweep, guarded on `_academy_window` / `_combat_sports_redraw` being
  set, which keeps a hidden-but-built page current without creating one.
- `open_academy_window` and `open_combat_sports_window` remain as routers to `select_tab` so
  existing entry points (Finance, Scouting, World news) keep working. They must not open a window.
- Retained detail popups — prospect profiles, card replays, child-promotion management, circuit
  records and history — still create Toplevels, parented to `self.root` rather than the page.

Player-owned Combat Sports divisions are persistent child promotions, distinct from each sport's
AI flagship circuit. `roster_ids` and booked-bout `a_id`/`b_id` fields are authoritative; retained
names are presentation and unambiguous legacy fallback only. Championship maps use `title_ids`, and
lineage, season statistics, records, awards, and Hall of Fame entries retain fighter IDs. One-fight
independent opponents are transient and must not enter persistent circuit statistics or awards.
Load/world repair must be deterministic, deduplicate by fighter ID, and never merge same-name
athletes. Every recruitment source, including flagship buyouts, must set
a negotiated purse, term, exclusivity, employer, and canonical finance transaction. A contract at
zero months receives the displayed renewal window and leaves on the next monthly review if it is
not renewed; expired athletes are not bookable. Player card costs pay the stored purse for both
corners, use a card-specific transaction reference and event label, and may settle at most once per
division per month. Player event counters, completed-card history, and media must not increment or
rewrite the AI flagship's equivalents. Changes to this flow require
`combat_sports_regression_test.py` plus the smoke suite.

Boxing and Muay Thai must remain mechanically distinct, not just commentary skins. Boxing bout
length is level-aware (six/eight/ten rounds) with 12-round title fights; three judge cards own the
official verdict and knockdowns can create 10-8/10-7 rounds. Standard Muay Thai is three rounds and
title Muay Thai is five, with effective kicks, knees, elbows, dumps, balance, and clinch control
weighted above undifferentiated punch volume. Lethwei shares the Muay Thai circuit but keeps five
rounds and a knockout-first/no-winner draw outcome. Preserve `scorecards` and `round_metrics` in
result and replay payloads, and route every new decision/draw label through
`combat_sport_is_decision()` so it cannot count as a finish or receive a stoppage round suffix.

Future Combat Sports cards live in each player division's `scheduled_events`, never in the MMA
`self.scheduled_events` collection. Their payload keeps event ID, month/week, production, marketing,
forecast, and ID-first bouts. Scheduling validates future date, roster ownership, medical
availability, contract coverage, duplicate corners, and the one-card-per-month rule. Scheduled
athletes are unavailable to manual/automatic card generation. `calendar_week_steps()` executes due
cards after entering the new week; forecast and settlement call `combat_sport_event_forecast()` so
the displayed business decision cannot diverge from the charged result. Cancellation removes only
the selected event and does not mutate fighter recovery or contracts.

Every `ttk.Treeview` is sortable by heading. Main tabs may call `make_tree_sortable` explicitly for
custom behavior, but secondary and popup tables rely on the shared Treeview class fallback in
`ui.py`; do not add a new column table with permanently static headings.

Fighter presentation is a boundary concern. `fighter_display_name()` and
`display_fighter_names_in_text()` must be idempotent: stored names may be raw or may already carry
`(C)`, `(IC)`, or `(D)` from an older presentation path, but a screen must render each marker once.
Keep event logs and identity matching raw; normalize only when populating labels, tables, news,
inbox detail, belt history, or Fight Night commentary.

AI roster reviews run during calendar advancement and must use
`scheduled_fighter_references(include_booked=True)` before considering a release or upgrade.
That helper returns durable fighter IDs with legacy-name fallback; keep both review passes safe for
scheduled fighters and cover the path in `ui_data_regression_test.py` so a packaged advance cannot
fail on an undefined schedule set.

## 13. Data Quality

- Avoid duplicate fighters across companies unless intentionally represented as a historical/younger
  or market snapshot. Keep each object on its own durable `fighter_id`; source markers such as
  `Legend`, `FA`, and `BAMMA` are internal seed metadata and must not be exposed as raw suffixes.
  The shared display formatter renders a compact `(D)` marker after duplicate names, including
  narrative and belt-history text. Use company, market, division, or profile context when the
  player needs to distinguish same-name snapshots. Audit the opening world for duplicate IDs and
  normalized base names before changing seeded records.
- Fighter database schema 5 requires a non-empty unique `fighter_id` on every canonical
  `all_fighters` row. New universes preserve that source ID; grouped compatibility tuples omit it.
  Renaming, editing, or moving a source record must preserve its ID, while an intentional duplicate
  must mint a fresh ID. Legacy schema-four packs receive deterministic IDs in memory without source
  rewrites until explicitly saved through the Database Editor.
- The shipped database keeps `birth_country` and `hometown` non-empty for every canonical MMA
  fighter and synchronizes those fields to compatibility tuples. Preserve authored values.
  Deterministic regional fallbacks must carry `birthplace_source: regional_fallback_v1` and must
  not be described as verified biography; verified bundled matches use
  `birthplace_source: bundled_verified_identity`.
- Rights packages presented as global or broad-reach coverage must include every current `REGIONS`
  entry. Add a shipped-database regression whenever the region model or media market list changes.
- Never create names with a `2` suffix as a collision workaround.
- Keep male and female fighters correctly gendered.
- When adding women whose names are absent from `FEMALE_FIRST_NAMES`, update `infer_gender`.
- Keep each company deep enough to fill its active divisions and champions.
- Use real fighters where requested; generated fighters are acceptable for roster depth.
- Generated data and tests should be deterministic under an explicit seed. Isolate test RNG setup
  from serialization and unrelated name generation.
- `Promotion.reputation` is a compact level label used in the World Hub, not a prose-description
  field. Keep long company copy in an explicit description/identity field so it cannot overflow the
  Level column.
- Region `teams` entries must represent teams based in that region. Prefer deriving the display
  from `Gym.region`, and validate authored overrides against the gym database.

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
python .\run_regression_suite.py
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
| Scouting reports, searches, staff identity, or recruitment UI | Syntax check + `scouting_regression_test.py` + smoke |
| Fight mechanics or commentary | Syntax check + `fight_engine_regression_test.py` + `fight_engine_full_system_test.py` + frozen 3,840-bout result and action audits + smoke |
| Fight Night viewer, replay, or event presentation | Syntax check + smoke + `fight_night_experience_regression_test.py` + stability |
| Media Desk or rights | Syntax check + smoke + media-system test |
| Event economics or rivalries | Syntax check + smoke + `event_economics_regression_test.py` + media-system test when media actions change |
| Shared UI/theme/layout | Syntax check + smoke + manual maximized-window check in representative themes |
| Fighter Profile, history, or Profile-launched actions | Syntax check + `fighter_profile_regression_test.py` + smoke |
| Universe data or database editor | Syntax check + universe `--validate` command + `database_editor_ui_audit.py`; build if packaging changed |
| Packaging, assets, paths, startup | Full shipping suite + portable build + launch packaged executable briefly |

Randomized tests should assert robust invariants or aggregate behavior. Do not hide a real
regression by widening a threshold without explaining why the sample design was wrong.

The Simulation Lab fight audit is a competitive calibration tool: generate named low/mid/high
bands, prefer overall gaps of six or less, report finish rates per band, and restore RNG/name state
after the run. Its lightweight gate/profit stress figures are labelled synthetic and must not be
presented as the player event-finance model.

Fight tuning and business tuning are separate persisted surfaces. `engine_settings` contains only
the versioned, bounded mechanics keys declared by `FIGHT_ENGINE_SETTING_DEFAULTS`; Gate Multiplier
lives in versioned `business_settings`. Load through the normalization helpers so malformed values
are clamped and legacy saves migrate `engine_settings.gate_multiplier` without changing behavior.
Simulation Lab must label mechanics controls separately from business-only controls. No Contest is
a participation/medical settlement: it completes contracted participation and recovery but must not
change W/L/D records, Elo, season awards, rivalries or titles. Technical decisions require the
completed-round threshold and the already-sealed cards. Referee review flags are observational and
must never rewrite an official result. Do not restore the removed `finish_chance()` or
`finish_method()` shortcut; all finishes resolve through the active exchange/stoppage mechanics.

### Portable builds

For the complete portable package:

```powershell
.\Build Portable.bat
```

To rebuild only the standalone universe editor:

```powershell
.\Build Database Editor.bat
```

Launcher/test/build batch files resolve Python from the repository `.venv` first, then the `py` or
`python` command available on `PATH`. Never commit a developer username or absolute interpreter
path; packaged builds still take precedence in the player launcher.

The game build must preserve these runtime folders and files in `dist\MMA Warriors`:

```text
Saves
Databases
Logs
README.md
Portable Check.bat
```

`Build Portable.bat` is the canonical release build and must produce both `MMA Warriors.exe` and
`MMA Warriors Database Editor.exe`; do not require a second editor build in release instructions.
Failure paths must restore any staged `Saves`, `Databases`, and `Logs`, and stale staging data must
not resurrect files deliberately removed from the package. `Portable Check.bat` must verify both
executables.

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
- Treat `assets/crowd_audio/manifest.json` as the runtime source of cue intent for the integrated
  crowd pack. Keep audio optional, respect suggested gain, and use multiple reactions
  sparingly rather than allowing ambience to mask commentary. Preserve the source provenance and
  Gregor Quendel CC BY 4.0 credit in `assets/crowd_audio/LICENSES.md`. Rebuild mastered assets through
  `tools/build_crowd_audio_pack.py`; do not add generated noise beds or unlicensed recordings. Keep
  isolated gasp/"ooh" vocals below the sustained crowd bed so reactions accent rather than mask the
  fight commentary; the manifest's `mix_controls` records the accepted vocal-balance limits. Each of
  the 12 trigger families has three source-distinct variants. Preserve the accepted revised-pack cue
  as Variant 1 and name additions `_02`, `_03`, and so on so random playback can group files by
  `family` without breaking the stable base filename. The player must avoid immediate variant
  repeats, retain per-family cooldowns and a simultaneous-cue ceiling, and fall back procedurally if
  a manifest entry cannot be decoded. A manifest `loop` flag is required for the session-scoped
  ambience bed: `start_fight_night_audio_session()` opens one crossfaded loop across the live card,
  one-shot cues remain independently bounded, and `stop_fight_night_audio_session()` must run when
  the owning viewer closes so no sound bleeds into another screen or session. Keep the bed neutral;
  fighter-specific location gain belongs to the current bout's reactions and walkout. Audio variant
  choice and procedural fallbacks use the audio-only `SystemRandom`; never consume simulation RNG
  for sound presentation. Derive local crowd gain through
  `fighter_event_connection`: exact hometowns receive the largest bounded lift, followed by national
  home, adopted home, and training-base connections. Keep this effect presentation-only; it must not
  alter fight mechanics or create a second geographic-proximity model in `audio.py`. The live Fight
  Night viewer and Game Settings share `fight_night_audio_volume`; route both through
  `set_fight_night_audio_volume` so drag-time changes apply to the next cue, malformed legacy values
  repair safely, and saved volume remains clamped to 0-100.

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
