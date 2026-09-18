# Verification routes

Run from the repository root with Python 3 and working Tkinter. Replace `python`
with the configured interpreter when necessary. Keep committed paths portable.
Contracts routed by [AGENTS.md](../AGENTS.md) may require additional checks.

## Isolated runner

Pass exact script names as positional arguments:

```powershell
python .\run_regression_suite.py fighter_profile_regression_test.py smoke_test.py
```

Add `--summary-dir <directory>` to retain a unique JSON result with interpreter,
working-tree Python-source fingerprint, exact selection/arguments, per-suite
status/duration/exit code and honest trailing `not_run` rows after fail-fast.
`--run-id <label>` supplies a readable filename stem; collisions receive a
numeric suffix instead of overwriting prior evidence. Example:

```powershell
python .\run_regression_suite.py --summary-dir .\analysis\runs --run-id media-fix media_plan_regression_test.py
```

The summary option does not retry or resume work. An interruption is recorded as
interrupted when Python can catch it; a force-killed process can leave only the
last atomic in-progress summary. Do not treat either as a pass.

`run_regression_suite.py::SUITES` is the manifest, including audit-tool arguments.
Selection requires exact registered paths without a leading `./` or `.\`.
Globs, group names, `--suite` and script arguments are unsupported. Suites run
sequentially in manifest order and stop on failure; unknown names exit code 2.

Each suite gets a temporary `MMA_WARRIORS_DATA_DIR` with copied databases and
separate Saves/Logs. It is removed even after failure; preserve useful output.
When a retained summary is requested, the runner routes the move-coverage report
and the three ground/striking/bottom expansion comparisons to that run's unique
`<run-id>-artifacts` directory and records their hashes. Direct script calls keep
their existing default paths; use `--output` for a unique discretionary run.
Other audit scripts can still write repository `analysis/` outputs. Review exact
arguments and the diff before a full run.

For unregistered tests, inspect setup and arrange equivalent isolation before
execution. Never run mutating tests against the active career's runtime data.

For the complete shipping suite:

```powershell
python .\run_regression_suite.py
```

`Run Smoke Tests.bat` invokes the full suite and pauses interactively. Resolve
Tcl/Tk initialization failures before claiming a passing game test.

## Choose checks by change

Names below are runner arguments. Add focused behavior coverage and domain
acceptance gates. Compile changed Python modules for a quick syntax check first.

| Changed area | Minimum route |
|---|---|
| Documentation only | Review Markdown, links and commands; `git diff --check`. No runtime test/build. |
| Models, seeding, saves or identity | `persistence_regression_test.py`, `identity_persistence_regression_test.py`, `smoke_test.py`, `stability_test.py` |
| Calendar, AI or performance | `app_performance_regression_test.py`, `simulation_performance_regression_test.py`, `smoke_test.py`, `stability_test.py`; add `ai_card_logic_regression_test.py` for card policy |
| Spectator stops/checkpoints | `simulation_pause_policy_regression_test.py`, `pinned_checkpoint_regression_test.py`, persistence and calendar checks |
| Fight Night presentation/archive/layout | `fight_night_presentation_test.py`, `fight_night_archive_regression_test.py`, `fight_night_layout_regression_test.py`, `fight_night_experience_regression_test.py`, `fight_audio_regression_test.py`, `window_lifecycle_regression_test.py`, smoke and stability |
| Fight mechanics/commentary | `fight_engine_regression_test.py`, `fight_engine_full_system_test.py`, affected focused fight tests, smoke; follow engine contracts for native and frozen result/action audits |
| Release engine | All six `fight_release_*_test.py` suites (expand names), mechanics checks and full shipping suite |
| Traits | `fighter_traits_regression_test.py`, `fighter_profile_regression_test.py`, persistence; fresh source-bound native gates for combat changes |
| UI/themes/lifecycle | `ui_data_regression_test.py`, `window_lifecycle_regression_test.py`, smoke; live-window theme/size checks |
| Profiles, history or scouting | `fighter_profile_regression_test.py`, `scouting_regression_test.py`, smoke; add `j10_comparison_regression_test.py` for comparisons |
| Staff work/employment | `staff_management_regression_test.py`, `staff_specialty_regression_test.py`, `staff_employment_regression_test.py`; add calendar checks for worker order |
| Booking and title decisions | `booking_workbench_regression_test.py`, `foundation_regression_test.py`; add `title_decision_resume_regression_test.py`, `last_minute_replacement_regression_test.py`, `rebooking_regression_test.py` for those paths |
| Contract batches or roster transitions | `contract_batch_workbench_regression_test.py`, `contracts_finance_regression_test.py`, Foundation and identity checks |
| Finance, offers or media | `finance_audit_regression_test.py`, `event_economics_regression_test.py`, `media_system_test.py`; add `cash_runway_regression_test.py` for forecasts and `media_plan_regression_test.py` for plans |
| Child companies/owned schedule | `child_promotion_interactions_test.py`, `child_promotion_loan_return_regression_test.py`, `child_promotion_long_run_test.py`, `owned_schedule_regression_test.py` |
| Combat sports or Grand Prix | `combat_sports_regression_test.py` or `grand_prix_regression_test.py`; relevant history, persistence and event checks |
| Universe/editor | `universe_validation_regression_test.py`, `database_editor_identity_regression_test.py`, `database_editor_save_as_test.py`, `database_editor_ui_audit.py`, `database_editor.py` |

The registered `database_editor.py` entry supplies `--validate` and the shipped
universe path automatically. Do not pass those flags to the runner itself.
Search `SUITES` for regional, owner-goal, testing, narrative and preparation checks.

## Test inventory contract

Every runnable root `*_test.py` is registered in `run_regression_suite.py::SUITES`
or must be named with a non-empty reason in `ROOT_TEST_EXCLUSIONS`. The runner
summary regression enforces this classification. The former seven omissions—six
portrait scripts and `g0_repair_regression_test.py`—are registered. Their focused
classification run passed after the main portrait suite was rebound to the
[current source review](FIGHTER_PORTRAIT_CURRENT_REVIEW.md); old review artifacts
remain retained rather than overwritten.

## Release and evidence

Build an EXE only when requested. An authorized release requires the full suite,
packaging contract/README workflow, both executables and packaged launch/portable
checks. Match `constants.py::GAME_VERSION` to README and the latest changelog.

Report commands, results and environment limitations. Old certificates do not
verify changed sources; diagnostic samples do not replace release gates. Retain
baseline/audit evidence and never regenerate expectations to conceal regressions.
