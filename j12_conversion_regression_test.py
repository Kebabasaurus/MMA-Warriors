"""Regression coverage for the bounded J12 career-to-database conversion."""

import copy
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import persistence
from persistence import PersistenceMixin, build_career_database_package, career_conversion_preflight


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def source_world():
    fighter = {"fighter_id": "FTR-1", "name": "A Fighter", "weight": "Lightweight", "age": 29, "record_w": 8, "record_l": 2}
    return {
        "player_company_name": "Test FC",
        "player_region": "USA",
        "player_reputation": "Regional Player Company",
        "roster": [fighter],
        "free_agents": [],
        "promotions": [{
            "name": "Test FC", "region": "USA", "size": 2, "cash": 99_000,
            "roster": [copy.deepcopy(fighter)],
            "scheduled_events": [{"id": "event-1"}],
            "finance": {"cash": 99_000},
        }],
        "combat_sport_worlds": {"Kickboxing": {"roster": [], "events": [{"id": "old"}], "scheduled_events": [{"id": "next"}]}},
        "player_combat_divisions": {"Kickboxing": {"Lightweight": {"events": [{"id": "old"}], "booked_bouts": [{"id": "next"}]}}},
        "cash": 425_000,
        "month": 18,
        "week": 3,
        "finance": {"revenue": 100},
        "inbox": [{"kind": "contract"}],
        "owner_goals": [{"status": "Active"}],
        "scheduled_events": [{"id": "main"}],
        "pending_rebookings": [{"id": "rebook"}],
        "booking_workbench": {"draft": {"id": "draft"}},
        "contract_batch_workbench": {"queue": [{"id": "batch"}]},
        "super_event_project": {"status": "Planning"},
        "super_event_offers": [{"id": "offer"}],
        "result_history": [{"date": "Month 17"}],
        "result_records": [{"event": "Test FC 17"}],
        "event_log": ["A completed event"],
        "change_journal": [{"type": "Migration"}],
        "world_chronicle": [{"summary": "history"}],
        "staff": [],
        "staff_candidates": [],
        "rules": {},
        "regions": {},
        "gyms": [],
        "broadcasters": [],
        "weight_classes": ["Lightweight"],
    }


class ConversionProbe(PersistenceMixin):
    def __init__(self, data, source_path=None):
        self._data = copy.deepcopy(data)
        self.source_path = Path(source_path) if source_path else None
        self.database_name = SimpleNamespace(get=lambda: "Converted Career")
        self.active_save_name = "Live Career"
        self.status = ""
        self.refreshes = 0

    def serialize_world(self):
        return copy.deepcopy(self._data)

    def active_save_path(self):
        return self.source_path or Path("Live Career")

    def safe_filename(self, value):
        return "".join(ch for ch in str(value) if ch.isalnum() or ch in " _-").strip() or "Career Start"

    def set_save_manager_status(self, message):
        self.status = message

    def refresh_game_menu(self):
        self.refreshes += 1


def test_package_is_new_start_and_manifest_is_lossless():
    original = source_world()
    package, manifest = build_career_database_package(original, "Converted Career", source_save="Live Career")
    check(original["cash"] == 425_000 and "scheduled_events" in original, "conversion mutated the source mapping")
    check("cash" not in package and "month" not in package and "finance" not in package, "live counters leaked into new-start database")
    check(package["active_save_name"] == "Converted Career Start" and package["active_save_group"] == "Main", "live save identity leaked into new-start database")
    check(package["roster"][0]["fighter_id"] == "FTR-1", "fighter identity was not preserved")
    check("scheduled_events" not in package["promotions"][0] and "finance" not in package["promotions"][0], "nested live promotion state leaked")
    check("events" not in package["combat_sport_worlds"]["Kickboxing"], "nested history leaked into combat-sport start")
    check(manifest["provenance"]["result_history"] == original["result_history"], "history was not retained in provenance")
    check(manifest["provenance"]["ongoing"]["scheduled_events"] == original["scheduled_events"], "ongoing work was not retained in provenance")
    check(manifest["complete"] is False, "active work incorrectly reported as a complete conversion")


def test_preflight_reports_structural_issues_without_rng_or_mutation():
    data = source_world()
    data["roster"].append(copy.deepcopy(data["roster"][0]))
    data["roster"][0]["weight"] = "Imaginaryweight"
    data["promotions"][0]["parent_company"] = "Missing Owner"
    data["belts"] = {"Male Lightweight": "Missing Champion"}
    before = copy.deepcopy(data)
    issues = career_conversion_preflight(data)
    fields = {(row["entity"], row["field"]) for row in issues if row["severity"] == "error"}
    check(("roster", "fighter_id") in fields, "duplicate fighter ID was not surfaced")
    check(any(row["field"] == "weight" for row in issues), "invalid division was not surfaced")
    check(any(row["field"] == "parent_company" for row in issues), "missing owner reference was not surfaced")
    check(any(row["field"] == "Male Lightweight" for row in issues), "missing title-holder reference was not surfaced")
    check(data == before, "preflight mutated source data")


def test_player_owned_parent_reference_is_valid():
    data = source_world()
    data["promotions"].append({"name": "Child Circuit", "parent_company": "Test FC", "roster": []})
    issues = career_conversion_preflight(data)
    check(not any(row["field"] == "parent_company" and row["severity"] == "error" for row in issues),
          "valid player-owned parent was incorrectly rejected")


def test_ui_conversion_requires_acceptance_and_writes_pair():
    with tempfile.TemporaryDirectory() as folder:
        old_dir = persistence.DATABASE_DIR
        persistence.DATABASE_DIR = Path(folder)
        try:
            source_path = Path(folder) / "live-save.json"
            source_path.write_bytes(b'{"live": "untouched"}')
            before_source = source_path.read_bytes()
            probe = ConversionProbe(source_world(), source_path)
            with patch.object(persistence.messagebox, "askyesno", return_value=False), \
                patch.object(persistence.messagebox, "showinfo") as info:
                check(probe.convert_career_to_database() is None, "cancelled conversion returned a destination")
                check(not (Path(folder) / "Converted Career.json").exists() and
                      not (Path(folder) / "Converted Career.conversion.json").exists(),
                      "cancelled conversion wrote files")
                info.assert_not_called()

            with patch.object(persistence.messagebox, "askyesno", return_value=True), \
                 patch.object(persistence.messagebox, "showinfo"):
                target = probe.convert_career_to_database()
            check(target == Path(folder) / "Converted Career.json", "conversion target path was wrong")
            manifest_path = Path(folder) / "Converted Career.conversion.json"
            check(target.exists() and manifest_path.exists(), "conversion did not write database and manifest")
            loaded = json.loads(target.read_text(encoding="utf-8"))
            check("cash" not in loaded and loaded["database_name"] == "Converted Career", "written package is not a new-start database")
            check(source_path.read_bytes() == before_source, "career conversion touched the live save")
            check(probe.status.startswith("Created career-start database"), "conversion status was not recorded")
            check(probe.refreshes == 1, "database list was not refreshed once")
        finally:
            persistence.DATABASE_DIR = old_dir


def test_destination_conflict_is_non_destructive():
    with tempfile.TemporaryDirectory() as folder:
        old_dir = persistence.DATABASE_DIR
        persistence.DATABASE_DIR = Path(folder)
        try:
            target = Path(folder) / "Converted Career.json"
            target.write_text('{"keep": true}', encoding="utf-8")
            probe = ConversionProbe(source_world())
            with patch.object(persistence.messagebox, "showwarning") as warning:
                check(probe.convert_career_to_database() is None, "conflicting destination was overwritten")
            check(json.loads(target.read_text(encoding="utf-8")) == {"keep": True}, "conflict changed existing database")
            warning.assert_called_once()
        finally:
            persistence.DATABASE_DIR = old_dir


if __name__ == "__main__":
    tests = [
        test_package_is_new_start_and_manifest_is_lossless,
        test_preflight_reports_structural_issues_without_rng_or_mutation,
        test_player_owned_parent_reference_is_valid,
        test_ui_conversion_requires_acceptance_and_writes_pair,
        test_destination_conflict_is_non_destructive,
    ]
    for test in tests:
        test()
    print("J12 CAREER CONVERSION REGRESSION TEST PASSED")
