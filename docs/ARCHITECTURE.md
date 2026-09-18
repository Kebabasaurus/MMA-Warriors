# Developer architecture map

Find the owner here, then the contract via [AGENTS.md](../AGENTS.md).
See [state rules](STATE_OWNERSHIP.md) and [tests](TESTING.md).
Paths below are repository-relative.

## Application composition

`main.py::FightEmpireApp` combines sibling mixins over shared state. Duplicate
methods resolve in base-class order: inspect the declaration and callers before
adding helpers. Prefer static inspection; imports can initialize runtime paths.

The current direct bases, in order, are audio, UI, admin, seeding, media, staff
management, views, Grand Prix, events, the release fight engine, world,
Foundation, booking workbench, contract batch workbench, persistence and awards.
`main.py` aliases `ReleaseFightEngineMixin` as `FightEngineMixin`, rather than
composing the historical base directly.

## Where to start

| Work area | Owner and search entry points |
|---|---|
| Startup/models | `main.py::FightEmpireApp.__init__`; `models.py::{Fighter,Gym,Promotion}`; `constants.py` for shared values and paths |
| Layout/navigation/themes | `ui.py::{build_layout,ensure_screen_built,create_managed_window,semantic_status_palette}`; `views.py::ViewMixin` populates rows/profiles |
| Calendar/AI/finance/rosters | `world.py::{calendar_week_steps,world_week_steps,world_month_steps,build_ai_card}` and named domain operations |
| Booking, negotiations, weigh-ins and event settlement | `events.py::EventMixin`; `schedule_event`, `prepare_event_result`, `finish_event`; `world.py::{apply_result,apply_draw_result,apply_no_contest_result}` |
| Fight Night/replays | `events.py::{open_live_fight_window,open_event_replay_window}` owns playback; `fight_night_layout.py`, `fight_night_presentation.py`, `fight_night_archive.py` are presentation helpers; `audio.py` owns sound |
| Fight mechanics | `fight_release.py::ReleaseFightEngineMixin`, `fight_release_extensions.py`, `fight_engine.py`; consult [release checkpoint](FIGHT_RELEASE_CHECKPOINT.md) and engine contracts |
| Move definitions, selection and defenses | `fight_moves/{schema,registry,release_registry,index,defenses}.py`, `fight_moves/catalogue/`; start with [move schema](FIGHT_MOVE_SCHEMA.md) |
| Traits and development | `fighter_traits.py::{TRAIT_DEFINITIONS,effective_injury_tendency,progress_camp_trait}`; camp application in `events.py`, calendar development in `world.py` |
| Identities/receipts/membership | `feature_foundation.py::{ensure_foundation_ids,record_membership_event}`; called by migration/transaction owners |
| Planning workbenches | `booking_workbench.py::{generate_booking_proposal,review_booking_proposal,commit_booking_proposal}` and locked-slot counterparts; `contract_batch_workbench.py::{create_contract_batch,review_contract_batch,commit_contract_batch}` |
| Staff | `staff_management.py::process_staff_autonomy_boundary`; employment here, effects/calendar hooks also in `world.py` |
| Grand Prix/awards | `grand_prix.py::advance_grand_prix_after_event`; `awards.py` for seasons, milestones and super-events |
| Media/help | `media.py` for actions, stories and rights; `rules_help.py` for authored help text |
| Save/load/library | `persistence.py::{serialize_world,apply_world_data,load_save_payload,atomic_write_json_gzip}`; inspect staging for field changes |
| Universe/editor | `seeding.py`, `real_sport_profiles.py`, `database_editor.py`; shipped data: `Databases/Default Universe.universe.json` |
| Titles/admin | `admin.py::vacate_fighter_belts`; result owners handle crown transitions |

Domain mixins also contain UI methods; names alone do not prove reader purity.

## Lifecycle boundaries

- Startup seeds or loads model/state, then builds the UI. Page construction and
  refresh project that state; they must not repair saved envelopes or simulate work.
- `calendar_week_steps` assembles ordered tasks. `begin_advance_sequence` schedules
  them through Tk; each task still runs synchronously. Staff and owner-objective
  workers receive the captured completed boundary after cards and business work.
- Event preparation produces the package used by playback and archives. Playback
  controls presentation; `finish_event` and result owners settle durable outcomes.
  Opening an archive is observational and must not repeat settlement.
- `serialize_world` projects save data; `apply_world_data` stages a load and applies
  compatibility rules. Read screens must not become extra migration boundaries.

## Cross-file change paths

| Change | Follow these dependencies |
|---|---|
| Add persistent state | Model/app default → seeding where relevant → serialization and load compatibility → explicit mutation owner → reader → persistence/identity tests |
| Transfer, retire or remove a fighter | Resolve stable identity → title vacancy hook before changing identity/roster → membership transition hook → roster/contract mutation → finance/history projections |
| Add a page or table action | UI builder/lazy route → defensive reader → stable source-to-row map → explicit action handler → theme, selection and lifecycle verification |
| Change a fight result path | Application release engine → recorded package → all relevant world result owners → settlement/awards/history → replay and save compatibility |
| Add a calendar task | Ordered week/month owner → captured boundary and retry behavior → spectator policy → persistence if durable → focused and stability tests |

## Files and evidence

`constants.py` selects `DATA_DIR`: `MMA_WARRIORS_DATA_DIR`, otherwise the writable
application directory or a user-profile fallback. Saves, databases and logs use
that root; assets use bundle/application anchors. Keep commands portable.

`run_regression_suite.py::SUITES` is the test manifest, including some `tools/`
and `analysis/` scripts. Read [analysis guidance](../analysis/README.md) before
changing baselines. `docs/archive/` is historical evidence; [the index](README.md)
links current plans, unresolved acceptance criteria and deferred decisions.
