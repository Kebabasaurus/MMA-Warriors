# MMA Warriors

A Windows desktop promotion-management simulation with MMA and other combat
sports, a living world, fighter development, business management and watched
Fight Night broadcasts.

## Version 3.0.10

See the [player and feature guide](docs/PLAYER_GUIDE.md) for detailed behavior and
compatibility notes, and the [changelog](CHANGELOG.md) for recorded changes.
The [documentation index](docs/README.md) routes development tasks to the relevant
code, contracts, tests and approved plans.

For the current audit and ordered implementation queue, see the
[Luna Max next-work plan](docs/LUNA_MAX_NEXT_WORK_PLAN.md). It separates reproduced
defects from optional features and gives each work item a completion boundary.

These documentation links are for the source checkout. The portable package
includes this quick start; the full `docs/` collection is kept with the source.

## Run The Game

Run `Launch MMA Warriors.bat`, or use a Python installation with working Tkinter:

```powershell
python main.py
```

The packaged game needs no Python installation. Keep the complete portable folder
together and launch `MMA Warriors.exe` outside a ZIP file. Saves, databases and logs
live beside the app when writable, otherwise under `%LOCALAPPDATA%\MMA Warriors`.
Use `Portable Check.bat` when moving the package to another computer.

The starting database is `Databases/Default Universe.universe.json`.
`MMA Warriors Database Editor.exe` edits starting universes; active careers have
their own save folders. Back up careers before intentional migration work.

To begin, select an established company, Create New Promotion or Spectator Mode,
then use the start-new-game action. Use Game & Saves for career loading, Quick
Save, backups and settings. Rules Help explains the game's authored rules and
routes to available screens. Keep the entire career folder when backing it up.

## Current Core Features

Promotion management, scouting, contracts, matchmaking, finances, media, Staff,
Academy, child companies, tournaments, world history and spectator simulation are
documented in the [complete guide](docs/PLAYER_GUIDE.md#current-core-features).
Its existing feature details and compatibility notes have been retained.
The [feature ledger](analysis/ui_review_20260912/MMA_WARRIORS_FEATURE_DEVELOPMENT_PLAN.md)
distinguishes delivered work from proposals and deferred policy decisions.

## Developer Change Contract

Every implementation change includes an observable `CHANGELOG.md` entry,
appropriate player/workflow documentation, the relevant developer contract linked
from [AGENTS.md](AGENTS.md), and focused verification. Update `README.md` for
quick-start/navigation changes and [the player guide](docs/PLAYER_GUIDE.md) for
feature details. Update `AGENTS.md` for universal instructions or routing; put
subsystem details in its linked contracts. Avoid copying the same explanation
into every document.

Documentation-only changes require link/command review, preservation checks for
moved material and `git diff --check`; they do not require artificial runtime tests.
The current full workflow is in [AGENTS.md](AGENTS.md#mandatory-change-package).

## Smoke Test

```powershell
python run_regression_suite.py
```

`Run Smoke Tests.bat` invokes the same canonical sequential runner. It isolates
runtime saves, databases and logs for each registered suite. For a focused change,
pass exact registered script names; see [TESTING.md](docs/TESTING.md) for selection
and additional required gates. Analysis outputs may still be written to their
explicit repository destinations.

## Build A Portable Windows Version

When a build is requested, use `Build Portable.bat`. It validates the pinned
offline toolchain, runs the shipping checks, and builds the game and Database
Editor together under `dist/MMA Warriors`. `Build Database Editor.bat` builds only
the editor. The toolchain is defined in `build-toolchain.json` and
`requirements-build.txt`; the build scripts do not install dependencies. The root
`MMA Warriors.spec` is the authoritative game-package definition used by the
portable workflow; do not duplicate its entry point, assets or dependency policy
as command-line flags.

Close the packaged game first. Preserve packaged Saves, Databases and Logs using
the existing build workflow. Detailed packaging contracts are linked from
[TESTING.md](docs/TESTING.md).

## Shipping Checklist

Run the full isolated suite and required source-bound acceptance gates. For a
requested release build, validate both executables, launch-check the package and
run `Portable Check.bat`. Record the actual checks and any environment limitations;
an older verification report does not certify changed code.

## Version 3.0.7 Stabilization Notes

Retained in the [player guide](docs/PLAYER_GUIDE.md#version-307-stabilization-notes).
