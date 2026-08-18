# Comprehensive Code Review

Review date: 2026-08-17  
Scope: the current working tree of the MMA Warriors desktop application, including runtime mixins, persistence, universe data loading, database editor, build/test tooling, and the focused child-promotion changes already present in the working tree.

## 1. Executive Summary

The codebase is feature-rich and currently passes the broad sequential regression, stability, media, database-editor, and child-promotion suites, but its central risks come from identity handling, transactional boundaries, and the size and coupling of the Tkinter/mixin architecture. The most serious correctness defect is that duplicate fighter names can collapse transient fight state and other domain lookups even though `fighter_id` is the durable identity, which can corrupt a bout without crashing. Persistence and event completion also have failure paths that can leave partial state, while save-sidecar path handling and split database validation create avoidable integrity and local-security exposure. The dominant maintainability pattern is large stateful functions that mix simulation, persistence, UI, dialogs, and refreshes; the application remains workable, but fixes increasingly require broad regression coverage and careful sequencing.

## Review scope and evidence

Reviewed the Python runtime, models, persistence and save migration paths, world simulation, events and fight engine, UI/view construction, media/audio, database editor, universe data, batch/build scripts, and test suites. The following checks passed sequentially: child-promotion interaction, child-promotion long-run, custom-promotion division integrity, persistence, contracts/finance, smoke, UI-data, QA tooling, media, database-editor UI audit, stability playtest, universe-database validation, compilation, and `git diff --check`. The stability playtest reached Month 4 for three deterministic seeds and recorded 172, 176, and 174 events respectively. `pyflakes` was not installed, so import/dead-code candidates below should be confirmed with a linter before deletion.

The current working-tree modifications and untracked child-promotion tests were treated as in-scope user work and were not altered. The current child-promotion protections reviewed in `world.py`, `views.py`, and `persistence.py` passed their focused tests; the findings below are remaining codebase-level risks, not a re-report of those completed fixes.

## 2. Prioritised Action Items

Priority definitions: **P0** — will cause data loss, security breach, or production crash; **P1** — likely to cause bugs or meaningfully degrade UX/performance under real conditions; **P2** — technical debt that compounds if left, including refactors and pattern inconsistencies; **P3** — polish, consistency, and minor developer-experience improvements.

### P0 — No confirmed findings

No confirmed P0 issue was found in the reviewed working tree. No hard-coded secrets, `eval`/`exec`, unsafe deserialization such as `pickle`, SQL surface, or obvious unauthenticated network endpoint was found. The P1 save-sidecar path issue is still worth fixing because this is a local desktop application handling user files, but the review found no evidence of an immediate production-wide breach or confirmed destructive data-loss path.

### P1-01 — Duplicate fighter names corrupt fight state and domain identity

**Affected files / functions:** `fight_engine.py:simulate_fight`; `world.py` combat-sport simulation around the stamina/damage dictionaries; `views.py:get_fighter`, `views.py:open_fighter_profile_window`; event participant helpers in `events.py`.

**Problem:** `Fighter` deliberately uses `fighter_id` as persistent/UI identity, but the fight engine initializes transient dictionaries using `a.name` and `b.name` as keys for gas, damage, cuts, control, scores, knockdowns, stats, and related state. Two legitimate fighters with the same display name therefore share state. A direct probe with two same-name Lightweight fighters completed without crashing but produced merged state and an incorrect-looking draw result. Similar name-keyed state and name-first lookup patterns exist in world simulation and profile/event resolution. This is silent correctness corruption, not merely a display issue.

**Fix prompt:**

> In `fight_engine.py:simulate_fight` and the combat-sport simulation in `world.py`, replace every transient state key based on `fighter.name` with `fighter_id` or a stable object-local slot. Keep display names only in commentary and UI. In `views.py:get_fighter`, resolve exact `fighter_id` before attempting a legacy/name fallback; make `get_fighter` pure and do not mutate rosters during lookup. Update `events.py` participant references and profile/company resolution to carry IDs end-to-end, retaining names only for legacy-save migration and presentation. Add regression tests for two same-name MMA fighters, two same-name combat-sport actors, stale references, and a profile opened for each identity. Verify scorecards, records, stats, and commentary remain attached to the correct fighter.

### P1-02 — Name-based event resolution can restore or select the wrong fighter

**Affected files / functions:** `events.py:event_fight_participant_references`, `events.py:event_fight_fighters`, `events.py:duplicate_event_participant_references`; `views.py:get_fighter`; schedule/result and title-holder lookups in `world.py`, `admin.py`, and views.

**Problem:** Event payloads and several domain paths still carry display names. `get_fighter` searches by name before ID and has a fallback that can move a retired or free-agent fighter back into the player roster while resolving a scheduled reference. Duplicate names, stale event references, and a name that happens to equal another fighter’s ID can all produce the wrong object or mutate state during what callers expect to be a read. This undermines event history, belt ownership, contract state, and UI identity.

**Fix prompt:**

> Introduce a pure `resolve_fighter(reference, scope)` helper in a domain module. Resolve `fighter_id` first, then use a narrowly documented name fallback only for legacy records, and return an explicit unresolved result rather than changing a roster. Move any intentional restoration of a booked fighter into a separate command used during validated event migration. Update `events.py` participant references, result application, `world.py` title/contract logic, `admin.py` repair, and profile views to use IDs. Add tests for duplicate names, ID/name collisions, retired fighters, free agents, stale schedule entries, and save/load round trips. Log unresolved legacy references for repair instead of silently inventing ownership.

### P1-03 — Event completion is not an atomic transaction

**Affected files / functions:** `events.py:finish_event`; result application and finance/award/media calls reached from `finish_event`; crash-save handling in `main.py`/`persistence.py`.

**Problem:** `finish_event` updates cash and finance near the start, then applies results and many downstream side effects before archiving and refreshing. `capture_player_change_snapshot()` is change tracking, not a complete rollback transaction. If a late result, award, tournament, media, or UI-adjacent handler raises, the career can contain a partially applied event: money may be committed while records, belts, history, injuries, or awards are not. A crash autosave can preserve that hybrid state.

**Fix prompt:**

> Refactor `events.py:finish_event` into validate, stage, commit, and present phases. Validate every participant, result, payout, belt, award, media, and archive field before mutation. Stage all model changes in a transaction object or a complete persistent-state snapshot; commit domain changes once, then perform UI refreshes and notifications outside the commit. On any commit exception, restore the complete pre-event state and write a diagnostic log without showing a false success. Keep existing result-index idempotence and child-promotion finance behavior. Add failure-injection tests that raise at each major post-result step and assert cash, records, belts, rosters, histories, awards, finance, and RNG state are unchanged.

### P1-04 — Universe validation is split and the shipping gate is incomplete

**Affected files / functions:** `database_editor.py:validate_universe_pack`; `persistence.py:validate_universe_section`; `Build Portable.bat`; universe-load path in `seeding.py`.

**Problem:** The database editor validator focuses mainly on fighter/company/core feeder data, while the persistence validator contains richer checks for media and other sections. The build calls the editor validator, so a database can pass the package gate and still fail when the game loads a malformed `combat_sports`, `media`, or `regions` section. The runtime validator also calls direct conversions such as `int(package[key])`; malformed values can raise instead of returning actionable validation issues. A direct malformed-media probe raised `ValueError`.

**Fix prompt:**

> Create one shared, side-effect-free universe schema validator used by `database_editor.py`, `persistence.py`, `seeding.py`, and the build CLI. Validate every top-level section, nested record, required field, enum, numeric range, foreign key, and cross-section identity. Return structured errors with section, record, field, and reason; never let malformed user data escape as an uncaught `ValueError`. Make `Build Portable.bat` call the same validator as runtime loading and add fixtures for malformed media, regions, combat sports, company references, duplicate fighter IDs, and wrong scalar types. Keep compatibility migrations separate from validation.

### P1-05 — External save-block paths are not constrained to the save directory

**Affected files / functions:** `persistence.py:hydrate_external_save_blocks`; external block serialization/loading around `_external_save_blocks`.

**Problem:** The loader accepts a relative path from `_external_blocks` and reads `path.parent / relative` without a resolved containment check or strict filename policy. A corrupt or crafted save can use traversal or an absolute path to make the app read an arbitrary local JSON file. This is a local desktop threat rather than a server endpoint, but it violates the save format’s trust boundary and can expose unrelated local data to the running process.

**Fix prompt:**

> Harden `persistence.py:hydrate_external_save_blocks`. Resolve the owning save directory and candidate block path, reject absolute paths, traversal outside the owning directory, symlink escapes, unexpected extensions, and filenames not generated by the save writer. Only read known block files under the save’s `DataBlocks` directory, and treat invalid references as a recoverable save warning. Add tests for `..`, rooted paths, symlinks where supported, malformed JSON, missing blocks, and valid legacy/current save blocks.

### P1-06 — Event and result histories grow without a retention policy

**Affected files / functions:** `events.py:finish_event` around `event_log` and `result_history` updates; `persistence.py` serialization and load of those fields; result/archive limits in `world.py` and `constants.py`.

**Problem:** `event_log` and `result_history` are prepended without a cap, while several AI/player archives and the result index are bounded. `serialize_world()` persists the growing collections and external save blocks include the event log. Long careers can therefore accumulate memory, UI rendering, save size, and load-time costs indefinitely, especially because the app is designed for long-running progression.

**Fix prompt:**

> Define explicit retention limits for event summaries, result summaries, detailed fight replays, and audit/finance history in `constants.py`. Update `events.py:finish_event` and persistence serialization to enforce those limits, preserving the newest summaries and stable result-index entries while moving detailed replay data into a bounded or separately pruned archive. Add a compatibility migration that trims only excess historical data, never current pending events. Add a long-career regression that advances at least 10 simulated years, asserts bounded collection sizes, and measures save size/load time.

### P1-07 — Release tests do not include the focused promotion regressions and are not isolated for parallel execution

**Affected files / functions:** `Run Smoke Tests.bat`; `Build Portable.bat`; all tests that mutate shared `Databases`, `Saves`, `Logs`, or active database/cache state.

**Problem:** The batch runners do not include the current focused child-promotion tests (`child_promotion_interactions_test.py`, `child_promotion_long_run_test.py`, and `custom_promotion_division_integrity_test.py`). The packaging gate also omits several persistence, contract, UI, QA, and focused tests. A parallel review run raced shared runtime data and reported a missing default universe database; the same tests passed sequentially. This makes CI/release confidence dependent on ordering and leaves the recently fixed promotion paths outside the shipping gate.

**Fix prompt:**

> Create one canonical ordered test runner used by `Run Smoke Tests.bat`, `Build Portable.bat`, and CI. Include every maintained regression suite, including the three child-promotion tests. Give each test an isolated temporary data root or immutable copied universe database; prevent tests from sharing `Saves`, `Logs`, active database markers, generated caches, or packaged output. Make failures retain their isolated artifacts for diagnosis. Add a parallel-safety test or explicit serialization guard, update `README.md` and `AGENTS.md` to describe the canonical runner, and make the packaging gate fail before building if any suite fails.

### P1-08 — Save loading is tolerant of missing fields but brittle to forward or malformed rows

**Affected files / functions:** `persistence.py` world/model row application around `_apply_world_data_unchecked`; `models.py` dataclass construction; save migration helpers.

**Problem:** Loading constructs `Fighter(**row)` and `Promotion(**row)`-style objects with defaults for missing fields, but there is no complete versioned schema layer that filters unknown future keys or validates row types before construction. A newer save field or malformed nested row can fail the load rather than produce a targeted migration/error. This is especially risky because the project promises old-save compatibility and transactional load recovery.

**Fix prompt:**

> Add versioned save schemas and focused migrations in `persistence.py`. Before dataclass construction, validate row shape and scalar/container types, filter or preserve unknown future fields according to an explicit compatibility policy, and report the exact record/field on rejection. Keep the transactional load guarantee: malformed candidates must leave the live career untouched. Add legacy, current, extra-field, missing-field, wrong-type, and nested-corruption tests for fighters, promotions, gyms, finance, event history, and child-promotion state.

### P2-01 — Giant mixins and UI methods make domain changes high-risk

**Affected files / functions:** `views.py` (12k+ lines; `open_player_combat_division_window`, `render_academy_screen`, `open_fighter_profile_window`); `world.py` (13k+ lines; `build_ai_card`, `simulate_ai_promotion_month`, `simulate_regional_feeder_month`); `events.py:open_live_fight_window`; `fight_engine.py:mma_striking_commentary_expansion` and `fight_phrase`; `persistence.py:_apply_world_data_unchecked`; `smoke_test.py:main`.

**Problem:** The mixin composition preserves legacy `self.method()` calls, but it also creates a very large implicit interface. Tk construction, simulation rules, persistence, finance, dialogs, and refreshes are interleaved in methods hundreds of lines long. The result is difficult to reason about, difficult to unit-test without a Tk root, and prone to accidental MRO collisions or partial mutation.

**Fix prompt:**

> Introduce small domain services/controllers without changing player-visible behavior: an identity/index service, event transaction service, finance ledger service, AI promotion service, and persistence migration service. Extract pure calculations first, then make Tk windows thin adapters that render returned view models and dispatch commands. Split the largest UI windows into tab/section builders and split AI event simulation into validation, matchmaking, result application, and finance phases. Preserve the public `FightEmpireApp` methods as compatibility shims while adding focused unit tests for each extracted service.

### P2-02 — Repeated linear scans and duplicate resolution work degrade long-run performance

**Affected files / functions:** `views.py:get_fighter`; `events.py:event_fight_fighters`, `duplicate_event_participant_references`; repeated `self.get_fighter(...)` loops in `world.py`; current child-promotion repair scans in `persistence.py`/`world.py`.

**Problem:** Many paths repeatedly scan the player roster, all fighters, or child rosters by name/ID. `event_fight_fighters` resolves each reference more than once, and duplicate detection uses `references.count(...)` inside a loop, creating O(n²) behavior. Repair code can scan all fighters and then rescan each child roster. These costs are modest for a short career but compound in long simulations and UI refreshes.

**Fix prompt:**

> Build and maintain explicit `fighter_id -> Fighter` indexes for global, player, promotion, and child-roster scopes, rebuilding them after load and ownership changes. Resolve each event reference once and pass the object/ID through the pipeline. Replace repeated list counts with `Counter`/sets, index child loan IDs, and avoid full-roster scans in refresh paths. Preserve identity and legacy fallback semantics. Add benchmarks for a large seeded universe and a 10-year simulation, and assert no stale index remains after loan, transfer, retirement, takeover, and save/load repair.

### P2-03 — Domain code is tightly coupled to Tk dialogs, refreshes, and timers

**Affected files / functions:** Tk/messagebox/`root.after` calls throughout `world.py`, `events.py`, `persistence.py`, and `views.py`; especially calendar advance and event completion paths.

**Problem:** Simulation and persistence methods directly show message boxes, mutate inbox/news, schedule callbacks, and call UI refreshes. Errors can therefore happen after domain mutation, headless testing requires a hidden Tk environment, and long-running simulation cannot be reused cleanly by tooling or future alternate UI surfaces. The coupling also obscures which actions are safe to call from tests or background progression.

**Fix prompt:**

> Separate domain commands from presentation. Make world advancement, event completion, finance, and persistence return typed outcomes, notifications, and recoverable errors without creating Tk widgets or calling `messagebox`, `root.after`, or refresh methods. Add a UI adapter in `views.py`/`events.py` that consumes those outcomes and chooses dialogs, toasts, inbox entries, and refresh timing. Preserve modal blockers that are genuine user decisions, but test domain flows with no Tk root and test the adapter separately.

### P2-04 — Popup lifecycle is inconsistent and repeated actions can create duplicate windows

**Affected files / functions:** numerous `tk.Toplevel` creators in `views.py`, `events.py`, `awards.py`, `admin.py`, and `persistence.py`; existing guards such as `views.py` news/child-manager windows and `events.py` live-fight cleanup.

**Problem:** Only some windows have a logical-window guard or close cleanup. Repeated clicks can create duplicate fighter profiles, company screens, reports, or editors with stale data and callbacks. Duplicate windows consume resources, confuse navigation, and can leave callbacks targeting destroyed widgets. The current child-manager duplicate-window protection is a good local pattern but is not centralized.

**Fix prompt:**

> Add a central window registry keyed by logical window type and stable entity ID. Make every reusable detail/editor/report window register on creation, focus/reuse an existing live window, unregister on close, and cancel scheduled callbacks. Explicitly mark which windows are intentionally multi-instance. Migrate all `Toplevel` creators in `views.py`, `events.py`, `awards.py`, `admin.py`, and `persistence.py`, and add UI regression checks for repeated open/close, stale entity updates, and destroyed-widget callbacks.

### P2-05 — Database loading has a surprising write side effect

**Affected files / functions:** `seeding.py:load_universe_database_pack`; `write_seed_database_file`; cache/mtime handling.

**Problem:** Loading the shipped universe can enrich missing/default sections and write the modified data back to the source path. A read operation can therefore mutate the user’s database, change its mtime, invalidate caches, and make source data differ depending on which executable loaded it. This is especially surprising for the standalone editor and for build/reproducibility workflows.

**Fix prompt:**

> Make `seeding.py:load_universe_database_pack` read-only. Move enrichment and schema migration into an explicit versioned migration command that writes a backup and reports the resulting path. Loading should return normalized in-memory defaults without rewriting the source file. Add tests asserting unchanged file bytes and mtime after a normal load, explicit migration tests, and cache tests for both migrated and already-current packs.

### P2-06 — Database editor Save As can leave the UI pointed at an unsaved target

**Affected files / functions:** `database_editor.py:save_database_as`, `database_editor.py:save_database`.

**Problem:** `save_database_as` assigns `self.path = Path(target)` before the target write/validation completes. If validation, backup creation, or the atomic write fails, the editor still points at the new target even though the original file is the last known saved location. Subsequent Save actions can write to an unexpected path.

**Fix prompt:**

> Refactor `database_editor.py:save_database_as` to keep the target in a local variable, validate and atomically write it, and assign `self.path` only after success. On failure, retain the original path, preserve the dirty state, and show an actionable error. Add tests for validation failure, target write failure, backup failure, cancel, and successful Save As; verify subsequent Save writes to the correct path.

### P2-07 — Broad exception handling hides state and operational failures

**Affected files / functions:** broad `except Exception` blocks across `persistence.py`, `views.py`, `audio.py`, `database_editor.py`, `events.py`, and `world.py`.

**Problem:** Some broad catches are appropriate for optional audio or metadata fallback, but many catch-and-continue paths can hide partial state failures, leave stale UI, or make a broken save appear successful. The pattern is inconsistent: callers cannot tell whether a failure was expected, recoverable, or fatal, and logs often lack operation/entity context.

**Fix prompt:**

> Audit every `except Exception` in the runtime and classify it as expected fallback, recoverable user-data error, or fatal invariant failure. Replace broad catches with narrow exception types where possible, add structured context (operation, fighter/promotion/save ID), and ensure state-mutating paths never silently continue after a partial failure. For optional audio/metadata, keep graceful fallback but record a warning. Add failure-injection tests for save, event completion, database validation, UI refresh, and audio startup.

### P2-08 — Save staging uses a heuristic runtime-UI detector

**Affected files / functions:** `persistence.py:_is_runtime_ui_value`; transactional staging around `apply_world_data`.

**Problem:** The runtime/UI detector recursively inspects containers but only samples the first 32 list/tuple entries. A widget or Tk value later in a larger collection can be copied into staged state, producing Tcl errors, hidden widget copies, or a transaction that is not actually isolated from UI objects. A heuristic is fragile as the shared app state grows.

**Fix prompt:**

> Replace `_is_runtime_ui_value` heuristics with an explicit persistent-state allowlist or registry. Define which app attributes are serializable model state and which are runtime UI handles, callbacks, variables, caches, or locks. Stage only the allowlisted persistent state, with explicit serializers for special values. Add a transactional-load test containing a UI object after index 32 in a nested collection and assert no widget is copied, no Tcl error occurs, and rollback remains complete.

### P2-09 — Calendar advancement can stack modal interruptions

**Affected files / functions:** `world.py:calendar_week_steps`, `advance_month`, `begin_advance_sequence`, `_finish_advance_sequence` and post-advance contract/broadcast/event prompts.

**Problem:** A synchronous or fast-forward advance can complete several domain actions and then show multiple message boxes in sequence. This interrupts the player repeatedly, obscures the final state, and can make it appear that the game is frozen. The underlying events are valid, but the notification flow is not a good long-run UX.

**Fix prompt:**

> Keep due-event or explicit player-decision blockers modal, but aggregate routine post-advance notices into one non-blocking inbox/toast summary with counts and drill-down links. Update `world.py` advancement callbacks and notification producers so each step returns structured notices instead of opening dialogs directly. Add UI tests for fast-forward with multiple contracts, broadcasts, news items, and a due event, verifying one summary plus the required decision blocker.

### P2-10 — Smoke and stability tests are too monolithic for diagnosis

**Affected files / functions:** `smoke_test.py:main` (approximately 2,200 lines); `stability_test.py`; related test helpers.

**Problem:** The suites provide valuable broad coverage but combine setup, data fixtures, assertions, UI probes, persistence checks, and release synchronization in very large scripts. A failure is hard to localize, shared fixtures can leak state, and new features tend to be appended rather than given focused invariants. This directly contributed to the parallel test-data collision observed during review.

**Fix prompt:**

> Split `smoke_test.py` into focused modules for startup/docs, identity, persistence, events/finance, UI data, and universe loading. Keep a small smoke entry point that composes them. Refactor `stability_test.py` around reusable isolated-career fixtures and invariant assertions. Add clear setup/teardown of temporary data roots and deterministic seeds. Preserve the existing batch command names while making each failure report its subsystem, seed, and retained artifact path.

### P2-11 — Build tooling is not fully reproducible

**Affected files / functions:** `Build Portable.bat`; `Build Database Editor.bat`; `tools/build_crowd_audio_pack.py`; project dependency documentation.

**Problem:** The portable build script can install PyInstaller during the build and does not express a locked toolchain. This can mutate the developer environment, depend on current network/package state, and produce different binaries on different days. The optional audio pack builder has separate native/numerical dependencies that are not clearly separated from core runtime requirements.

**Fix prompt:**

> Define a pinned build environment for the portable game and database editor, including Python/PyInstaller versions and optional audio-pack dependencies. Make build scripts verify the environment and fail with an actionable install command rather than silently installing packages. Record the generated tool versions in build metadata and update `README.md` with reproducible build setup and the distinction between core and optional audio tooling.

### P3-01 — Replace wildcard imports and remove verified dead imports

**Affected files / functions:** nearly every runtime module using `from constants import *`; import blocks in `admin.py`, `awards.py`, `events.py`, `fight_engine.py`, `main.py`, `media.py`, `persistence.py`, `seeding.py`, `ui.py`, `views.py`, `world.py`, and `database_editor_ui_audit.py`.

**Problem:** Wildcard constants imports hide dependencies and make static analysis unreliable. An AST audit found likely unused imports including `compact_json` in `database_editor_ui_audit.py`, `dataclass` in `persistence.py`, and groups of `json`, `sys`, `traceback`, `datetime`, `asdict`, `Path`, Tk, and model imports in several mixins. Some candidates may be used dynamically, so blind deletion is unsafe.

**Fix prompt:**

> Run a pinned linter such as Ruff or Pyflakes across all Python files, verify wildcard/dynamic consumers, replace `from constants import *` with explicit imports, and remove only imports confirmed unused by static and runtime checks. Keep import grouping consistent, run all regression suites, and ensure the resulting modules still support the mixin assembly in `main.py`.

### P3-02 — Protect fight-engine cache cleanup with `try/finally`

**Affected files / functions:** `fight_engine.py:simulate_fight` and `finish_result` cache lifecycle.

**Problem:** Fight simulation installs temporary skill-bundle and finish-conversion caches and restores them on normal completion. An exception path can leave stale caches on the app, causing later fights to observe data from the failed bout.

**Fix prompt:**

> Wrap the temporary cache lifecycle in `fight_engine.py:simulate_fight` with `try/finally`, restoring or clearing both caches on every exit path. Add an injected exception test between cache setup and result conversion, then run a second fight and assert no cache state from the failed fight is visible.

### P3-03 — Initialize the audio cue lock deterministically

**Affected files / functions:** `audio.py` lazy `_fight_night_audio_lock` initialization around the cue/playback helpers.

**Problem:** The lock is initialized lazily without a separate initialization guard. The normal Tk path is effectively single-threaded, but background playback or future callers could race and replace the lock, defeating the intended cue cap or causing inconsistent shutdown behavior.

**Fix prompt:**

> Initialize the fight-night audio lock during app/audio subsystem construction, or protect lazy initialization with a class-level initialization lock. Preserve the no-audio fallback and shutdown behavior. Add a small concurrent cue test that verifies one stable lock, bounded playback, and clean teardown.

### P3-04 — Add explicit shared-state typing and collection defaults

**Affected files / functions:** `models.py`; mixin shared `self` methods across `main.py`, `world.py`, `events.py`, `views.py`, and `persistence.py`.

**Problem:** Many mixins rely on an undocumented shared `self` API and dictionaries with implicit shapes. Model collection fields use `None` in places where callers repeatedly write `or []`/`or {}`. This is compatible with current saves but increases null-handling noise and makes refactors harder.

**Fix prompt:**

> Add `TypedDict`/protocol definitions for persisted promotion, event, finance, and strategy records, and a protocol for the mixin methods required by each domain service. Convert semantically always-present model collections to `field(default_factory=...)` while retaining explicit legacy-load normalization. Add type checking to CI and update save migration tests to prove old `null`/missing values still load safely.

### P3-05 — Resolve documentation and test-runner drift

**Affected files / functions:** `README.md`, `AGENTS.md`, `Run Smoke Tests.bat`, `Build Portable.bat`, and any future CI workflow.

**Problem:** Documentation describes a narrower runner than the batch file actually invokes, while the current focused tests are not listed in either release path. Duplicated or stale build/test descriptions reduce confidence in what “green” means.

**Fix prompt:**

> Make the canonical test runner the single source of truth, have both batch files call it, and update `README.md` and `AGENTS.md` to list the actual suites and isolation rules. Add a documentation synchronization assertion so adding/removing a maintained suite requires updating the runner manifest and release docs together.

## 3. Quick Wins

These are small, low-risk changes that can be batched after confirming consumers:

- Remove the verified-unused `compact_json` import from `database_editor_ui_audit.py` and other imports confirmed by Ruff/Pyflakes; do not delete candidates that are used through dynamic names.
- Replace one-line Tk construction statements with the project’s normal multi-line style in `views.py` and neighboring UI modules where it improves readability.
- Replace `references.count(...)` inside duplicate-event loops with a `Counter` or set-based check.
- Resolve each event fighter reference once in `events.py:event_fight_fighters` instead of calling the getter repeatedly.
- Add a small constant for repeated window-registry keys and close/unregister hooks to the windows that already have guards.
- Add `try/finally` around fight cache cleanup and initialize the audio lock during setup.
- Correct `README.md`/`AGENTS.md` runner descriptions after the canonical runner is established.
- Add explicit return annotations to new child-promotion and persistence repair helpers as a first step toward typed shared state.

**Batch fix prompt:**

> In the MMA Warriors repository, apply only safe hygiene changes: run Ruff/Pyflakes, remove imports proven unused, replace the O(n²) duplicate-reference check in `events.py`, resolve event references once, protect `fight_engine.py` temporary caches with `try/finally`, initialize the audio cue lock deterministically, and synchronize `README.md`/`AGENTS.md` with the canonical test runner. Do not change simulation outcomes or save formats. Run the full sequential regression suite, `git diff --check`, and confirm no child-promotion tests or current user changes were removed.

## 4. Redundancy Removal Log

The entries below are deletion candidates. “Verify” means the item should be removed only after the stated consumer/search check; the review does not authorize deleting compatibility behavior solely because it looks old.

- `views.py:_open_academy_window_legacy` — appears to have no call sites after the academy moved into the current notebook/screen flow; remove after confirming no external plugin or saved callback references it.
- `database_editor_ui_audit.py:compact_json` import — AST audit found no use; delete after a linter confirms no dynamic reference.
- Verified-unused imports in `admin.py`, `awards.py`, `events.py`, `fight_engine.py`, `main.py`, `media.py`, `persistence.py`, `seeding.py`, `ui.py`, `views.py`, and `world.py` — delete only the exact names confirmed by Ruff/Pyflakes and runtime tests.
- `from constants import *` statements — remove each wildcard import after replacing it with the explicit constants actually used; this is a dependency cleanup, not a behavior deletion.
- One of the duplicate universe validators (`database_editor.py:validate_universe_pack` or the persistence-side implementation) — delete the old implementation after the shared validator in P1-04 is adopted and all callers are migrated.
- Repeated local fighter lookup helpers that only wrap name scans — consolidate into the ID-first identity service from P1-01/P1-02, then delete the wrappers after call-site migration.
- Any duplicate `Toplevel` construction path superseded by the central window registry — delete only after each caller is migrated and close/callback behavior is covered.
- `constants.py:FIGHT_COMMENTARY_ROUND_LINE_LIMIT`, `FIGHT_COMMENTARY_ROUND_HEAD_LINES`, and `FIGHT_COMMENTARY_ROUND_TAIL_LINES` — candidate legacy tuning flags; `AGENTS.md` explicitly says they are retained for compatibility and `smoke_test.py` still references one, so do not delete until external tuning-tool consumers and tests are confirmed absent.
- `Academy and Combat Sports Tabs Plan.txt` — untracked planning artifact; delete only if it is confirmed obsolete and not being used as the active product plan.
- Any historical `main.original_backup_*.py` files if later found in the repository — they are not active implementation; remove only with explicit repository-history/backup policy confirmation.
- Duplicate release-script documentation entries that describe the same `Build Portable.bat` behavior — consolidate after the canonical runner/build wording is established.

### Review conclusion

The next implementation sequence should be P1-01/P1-02 identity normalization, P1-03 event transactionality, and P1-04/P1-07 validation and release-test isolation. Those changes reduce the chance of silent career corruption and make subsequent P2 refactors safer. The current focused child-promotion behavior is passing, but it should remain in the canonical release gate so future identity, persistence, and UI refactors cannot regress it unnoticed.
