"""Focused regressions for the Brett-Dev QA/tooling stabilization pass."""

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
        self.engine_settings = {"gate_multiplier": 1.0}
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


if __name__ == "__main__":
    test_simulation_audit_is_competitive_and_non_mutating()
    test_windows_launchers_do_not_embed_a_developer_profile()
    print("QA tooling regression tests passed.")
