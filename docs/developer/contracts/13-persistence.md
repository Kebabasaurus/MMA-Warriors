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

### Career-to-database conversion

`PersistenceMixin.convert_career_to_database()` is an explicit J12 migration path, not a
normal save or a database-editor overwrite. `build_career_database_package()` and
`career_conversion_preflight()` must remain pure over a serialized mapping: preserve stable
fighter/promotion IDs, current skills/age/records, roster ownership and supported contracts;
reset time, cash, finance, inbox, pause targets, scheduled work and other live commitments.
Nested promotion and combat-sport event ledgers must be stripped from the playable package.
Detailed history and every excluded obligation are retained in a sibling
`<name>.conversion.json` manifest with structured severity/entity/field/evidence/remedy rows.
Unknown fields, duplicate top-level fighter IDs, invalid divisions and missing promotion
owners are structural errors and refuse the write. Populated ongoing work requires a visible
acceptance prompt; cancellation and destination conflicts are non-destructive. Write the
manifest and database only after staged validation, clean both artifacts on a failed new
conversion, and never modify the source career save. Career-start databases are hidden from
the legacy list by their manifest suffix and are labelled in the Game & Saves database panel.
Run `j12_conversion_regression_test.py`, persistence/UI regressions and the smoke check when
this path changes. Do not rebuild an EXE or touch user saves as part of conversion work.

