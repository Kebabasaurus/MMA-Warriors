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

`Build Portable.bat` is the canonical release workflow and must produce both `MMA Warriors.exe` and
`MMA Warriors Database Editor.exe`; do not require a second editor build in release instructions.
Within that workflow, root `MMA Warriors.spec` is the single authority for the game's entry point,
bundled assets, optional dependency policy and output name. The batch file invokes that spec directly
and controls only verification, runtime-data preservation and build/output locations. Static shipping
tests must inspect this invoked definition. Do not add parallel game flags to the batch file or silently
exclude optional modules without tracing the active import graph.

The proposed source-delivery boundary is recorded in
`docs/developer/delivery-manifest.json` and explained by
`docs/developer/DELIVERY_SNAPSHOT.md`. Every included input has a role, byte size
and SHA-256 hash; exclusions have reasons. Refresh the manifest after final source
or handoff edits, then validate a new copy outside the repository. Validation must
operate on that copy for hashes, local imports, registered scripts/fixtures,
packaging inputs and Python syntax so dependencies cannot resolve back to the
working checkout. Never include active careers, logs or credentials, and do not
stage files merely because the delivery proposal requires them.
Failure paths must restore any staged `Saves`, `Databases`, and `Logs`, and stale staging data must
not resurrect files deliberately removed from the package. `Portable Check.bat` must verify both
executables.

Never solve a build problem by deleting runtime saves. After a packaging or core-runtime change,
start the packaged `MMA Warriors.exe` briefly and run the portable check when available.

