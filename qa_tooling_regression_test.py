"""Focused regressions for the Brett-Dev QA/tooling stabilization pass."""

import re
from pathlib import Path

from admin import AdminMixin
from models import Fighter


ROOT = Path(__file__).resolve().parent


class Value:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class TextSink:
    def __init__(self):
        self.value = ""

    def config(self, **_kwargs):
        return None

    def delete(self, *_args):
        self.value = ""

    def insert(self, _where, value):
        self.value += str(value)


class AuditHarness(AdminMixin):
    def __init__(self):
        self.audit_runs = Value(10)
        self.audit_text = TextSink()
        self.name_counts = {"existing": 7}
        self.engine_settings = {"config_version": 2, "ko_power": 1.0, "submission_finish": 1.0, "decision_noise": 1.0, "gas_cost": 1.0, "damage": 1.0}
        self.business_settings = {"config_version": 1, "gate_multiplier": 1.0}
        self._fighter_number = 0

    def apply_engine_settings(self):
        return None

    def create_generated_fighter(
        self, _min_pop, _max_pop, min_skill, max_skill, weight=None, gender=None, **_kwargs
    ):
        self._fighter_number += 1
        base = (min_skill + max_skill) // 2
        fighter = Fighter(
            name=f"Audit Fighter {self._fighter_number}",
            weight=weight or "Lightweight",
            gender=gender or "Male",
            age=25,
            record_w=5,
            record_l=2,
            striking=base,
            wrestling=base,
            grappling=base,
            cardio=base,
            chin=base,
            purse=5_000,
            popularity=35,
            momentum=0,
            morale=70,
        )
        # Model the generator's identity reservation so the audit regression
        # proves the live career dictionary is restored after the sandbox run.
        self.name_counts[fighter.name] = 1
        return fighter

    def fight_hype(self, _a, _b, _fight):
        return 45

    def match_build_score(self, _a, _b, _fight):
        return 55

    def simulate_fight(self, a, b, _fight):
        return a, b, "Decision", 3, []


def test_simulation_audit_is_competitive_and_non_mutating():
    harness = AuditHarness()
    harness.run_simulation_audit()
    report = harness.audit_text.value
    assert "Competitive matchup coverage:" in report
    assert "100.0%) at OVR gap <= 6" in report
    assert "Competitive finish rate by generated tier:" in report
    assert "not the player event-finance model" in report
    assert harness.name_counts == {"existing": 7}


def test_windows_launchers_do_not_embed_a_developer_profile():
    for name in (
        "Launch MMA Warriors.bat",
        "Run Smoke Tests.bat",
        "Build Portable.bat",
        "Build Database Editor.bat",
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "C:\\Users\\" not in text, name
        assert "%APP_DIR%" in text, name


def test_build_specs_are_portable_and_bundle_runtime_graphics():
    game_spec = (ROOT / "MMA Warriors.spec").read_text(encoding="utf-8")
    editor_spec = (ROOT / "MMA Warriors Database Editor.spec").read_text(encoding="utf-8")
    portable_build = (ROOT / "Build Portable.bat").read_text(encoding="utf-8")

    for name, text in (
        ("MMA Warriors.spec", game_spec),
        ("MMA Warriors Database Editor.spec", editor_spec),
    ):
        assert not re.search(r"[A-Za-z]:\\+", text), name
        assert "/Users/" not in text and "/home/" not in text, name
        assert "Path(SPECPATH).resolve()" in text, name

    assert "(str(PROJECT_ROOT / 'assets'), 'assets')" in game_spec
    assert "(str(PROJECT_ROOT / 'country_flags'), 'country_flags')" in game_spec
    assert '--add-data "%APP_DIR%assets;assets"' in portable_build
    assert '--add-data "%APP_DIR%country_flags;country_flags"' in portable_build
    assert 'BUNDLE_DIR / "country_flags"' in (ROOT / "views.py").read_text(encoding="utf-8")
    assert any((ROOT / "country_flags").glob("*.png"))


def test_shipping_scripts_preserve_failures_and_require_complete_output():
    portable_build = (ROOT / "Build Portable.bat").read_text(encoding="utf-8")
    editor_build = (ROOT / "Build Database Editor.bat").read_text(encoding="utf-8")
    portable_check = (ROOT / "Portable Check.bat").read_text(encoding="utf-8")
    smoke_launcher = (ROOT / "Run Smoke Tests.bat").read_text(encoding="utf-8")

    assert 'if exist "%RUNTIME_BACKUP%" rmdir /S /Q "%RUNTIME_BACKUP%"' in portable_build
    assert ":restore_runtime_after_failure" in portable_build
    assert "if errorlevel 2 goto backup_failed" in portable_build
    assert portable_build.count("goto build_failed") >= 7
    assert 'if errorlevel 1 goto build_failed' in portable_build
    assert 'if not exist "%APP_DIR%output_database_editor\\MMA Warriors Database Editor.exe"' in editor_build
    assert "could not be copied to the portable package" in editor_build
    assert 'if not exist "%APP_DIR%MMA Warriors Database Editor.exe"' in portable_check
    assert '"%PY%" "%APP_DIR%run_regression_suite.py"' in smoke_launcher
    assert smoke_launcher.count("exit /b 1") >= 2


if __name__ == "__main__":
    test_simulation_audit_is_competitive_and_non_mutating()
    test_windows_launchers_do_not_embed_a_developer_profile()
    test_build_specs_are_portable_and_bundle_runtime_graphics()
    test_shipping_scripts_preserve_failures_and_require_complete_output()
    print("QA tooling regression tests passed.")
