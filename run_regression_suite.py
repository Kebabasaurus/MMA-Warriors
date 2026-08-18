"""Run every maintained regression in a fresh runtime-data directory.

The game deliberately stores portable runtime data beside the application.  A
test process must not share that mutable directory with another test, otherwise
database markers, saves, and logs make the result depend on execution order.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITES = (
    ("smoke_test.py", ()),
    ("persistence_regression_test.py", ()),
    ("contracts_finance_regression_test.py", ()),
    ("finance_audit_regression_test.py", ()),
    ("ui_data_regression_test.py", ()),
    ("qa_tooling_regression_test.py", ()),
    ("media_system_test.py", ()),
    ("child_promotion_interactions_test.py", ()),
    ("child_promotion_long_run_test.py", ()),
    ("custom_promotion_division_integrity_test.py", ()),
    ("identity_persistence_regression_test.py", ()),
    ("universe_validation_regression_test.py", ()),
    ("fight_audio_regression_test.py", ()),
    ("advance_notifications_regression_test.py", ()),
    ("window_lifecycle_regression_test.py", ()),
    ("database_editor_save_as_test.py", ()),
    ("database_editor_ui_audit.py", ()),
    ("database_editor.py", ("--validate", "Databases/Default Universe.universe.json")),
    ("stability_test.py", ()),
)


def isolated_environment(temp_dir):
    data_dir = Path(temp_dir) / "runtime"
    source_databases = ROOT / "Databases"
    if source_databases.exists():
        shutil.copytree(source_databases, data_dir / "Databases")
    else:
        (data_dir / "Databases").mkdir(parents=True)
    (data_dir / "Saves").mkdir(parents=True, exist_ok=True)
    (data_dir / "Logs").mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["MMA_WARRIORS_DATA_DIR"] = str(data_dir)
    return environment


def main():
    requested = set(sys.argv[1:])
    known = {script for script, _arguments in SUITES}
    unknown = requested - known
    if unknown:
        print("Unknown suite(s): " + ", ".join(sorted(unknown)), file=sys.stderr)
        return 2
    suites = tuple((script, arguments) for script, arguments in SUITES if not requested or script in requested)
    for script, arguments in suites:
        with tempfile.TemporaryDirectory(prefix="mma_warriors_regression_") as temp_dir:
            print(f"\n=== {script} ===", flush=True)
            completed = subprocess.run(
                [sys.executable, str(ROOT / script), *arguments],
                cwd=ROOT,
                env=isolated_environment(temp_dir),
            )
            if completed.returncode:
                print(f"\nFAILED: {script} (runtime data kept only until this process exits)", file=sys.stderr)
                return completed.returncode
    print("\nALL REQUESTED ISOLATED REGRESSION SUITES PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
