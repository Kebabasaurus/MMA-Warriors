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

