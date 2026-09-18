"""Focused regressions for persistence, result identity, and world integrity fixes."""

import inspect
import random
import tempfile
from pathlib import Path
from unittest.mock import patch

import persistence
import world as world_module
from models import Fighter
from persistence import (
    PersistenceMixin,
    migrate_serialized_career_archetypes,
    serialize_fighter_model,
)
from views import ViewMixin
from world import WorldMixin


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def test_career_archetype_migration_is_explicit_and_non_destructive():
    source = {
        "month": 24,
        "roster": [
            {"fighter_id": "legacy-1", "career_archetype": "Standard Prime"},
            {"fighter_id": "healthy-1", "career_archetype": "Balanced Development"},
        ],
        "promotions": [{"name": "Legacy FC", "roster": [
            {"fighter_id": "legacy-2", "career_archetype": "Long Prime"},
        ]}],
        "combat_sport_worlds": {"Boxing": {"roster": [
            {"fighter_id": "legacy-3", "career_archetype": "Early Peak"},
        ]}},
        "authored": {"career_archetype": "Future authored label"},
    }
    migrated, changes = migrate_serialized_career_archetypes(source)
    check(source["roster"][0]["career_archetype"] == "Standard Prime", "migration mutated its source payload")
    check(migrated["roster"][0]["career_archetype"] == "Balanced Development", "standard prime was not normalised")
    check(migrated["promotions"][0]["roster"][0]["career_archetype"] == "Durable Career", "nested promotion row was not normalised")
    check(migrated["combat_sport_worlds"]["Boxing"]["roster"][0]["career_archetype"] == "Early Maturation", "child-sport row was not normalised")
    check(migrated["authored"]["career_archetype"] == "Future authored label", "unknown authored value was rewritten")
    check(len(changes) == 3, f"expected three migration changes, got {len(changes)}")
    check(all("path" in row and row["from"] != row["to"] for row in changes), "migration audit lacks source paths")


def fighter(name="Test Fighter", fighter_id="FTR-test", **updates):
    values = dict(
        name=name, weight="Lightweight", age=28, record_w=5, record_l=2,
        striking=70, wrestling=68, grappling=69, cardio=72, chin=70,
        popularity=45, momentum=0, morale=70, purse=12_500,
        fighter_id=fighter_id,
    )
    values.update(updates)
    return Fighter(**values)


class ResultProbe(WorldMixin):
    def scorecard_summary_from_lines(self, _lines):
        return ""


class TransactionProbe(PersistenceMixin):
    def __init__(self):
        self.cash = 100
        self.roster = ["original"]
        self.marker = {"career": "original"}

    def _apply_world_data_unchecked(self, data):
        self.cash = data["cash"]
        self.roster.append("staged mutation")
        self.marker["career"] = "incoming"
        if data.get("fail"):
            raise ValueError("late migration failure")

    def set_player_event_location_default(self):
        pass


class SaveFailureProbe(PersistenceMixin):
    def __init__(self, current_path, selected_path=None):
        self.current_path = Path(current_path)
        self.selected_path = Path(selected_path) if selected_path else None
        self.active_save_name = "Current"
        self.active_save_group = "Main"
        self.booked = []
        self.applied_payload = None
        self.closed_busy = False
        self.backup_attempts = []

    def active_save_path(self):
        return self.current_path

    def selected_save_path(self):
        return self.selected_path

    def serialize_world(self):
        return {"cash": 100}

    def save_metadata(self, slot_name):
        return {"slot": slot_name}

    def backup_save_file(self, path, reason="manual"):
        self.backup_attempts.append((Path(path), reason))
        raise OSError("recovery drive unavailable")

    def write_save_metadata_sidecar(self, *_args):
        return True

    def prune_save_backups(self):
        pass

    def show_busy_overlay(self, *_args):
        return object()

    def update_busy_overlay(self, *_args):
        pass

    def apply_world_data(self, data):
        self.applied_payload = data

    def set_active_save_location(self, name, group):
        self.active_save_name = name
        self.active_save_group = group

    def save_slot_name_from_path(self, _path):
        return "Selected"

    def save_slot_group_from_path(self, _path):
        return "Main"

    def refresh_all(self):
        pass

    def write_log(self):
        pass

    def set_save_manager_status(self, _message):
        pass

    def close_busy_overlay(self, _busy):
        self.closed_busy = True


def test_save_library_reader_does_not_create_missing_save_directory():
    probe = PersistenceMixin()
    with tempfile.TemporaryDirectory() as root:
        missing = Path(root) / "Saves"
        with patch.object(persistence, "SAVE_DIR", missing):
            check(probe.primary_save_paths(create=False) == [], "reader should return an empty library")
            check(not missing.exists(), "save library reader created a missing save directory")
            check(probe.autosave_dir("weekly", create=False) == missing / "Game 1" / "Autosaves" / "Weekly",
                  "read-only autosave enumeration resolved the wrong slot path")
            check(probe.rolling_backup_files(create=False) == [],
                  "read-only backup enumeration returned phantom files")
            check(not missing.exists(), "read-only autosave/backup enumeration created save directories")
            check(probe.primary_save_paths() == [], "create-on-demand compatibility path changed")
            check(missing.exists(), "explicit create-on-demand path did not create the save directory")


class WorldProbe(WorldMixin):
    def __init__(self):
        self.month = 1
        self.week = 1
        self.booked = []
        self.scheduled_events = []
        self.roster = []
        self.free_agents = []
        self.news = []
        self.inbox = []
        self.rules = {"auto_assign_idle_scouts": True, "drug_testing": "Standard"}
        self.belts = {}
        self.interim_belts = {}
        self.belt_history = {}
        self.special_belts = {}
        self.player_company_name = "Regression FC"
        self.player_region = "USA"
        self.company_pop = 40
        self.company_stability = 60

    def is_event_due(self, _event):
        return False

    def event_fight_participants(self, fight):
        return list(fight.get("fighters", []))

    def event_fight_participant_references(self, fight):
        names = self.event_fight_participants(fight)
        ids = list(fight.get("fighter_ids", []))
        return ids if len(ids) == len(names) and all(ids) else names

    def vacate_fighter_belts(self, _fighter, _roster, belts, interim, history, _reason):
        return belts, interim, history

    def vacate_special_belts_held_by(self, *_args):
        pass

    def resolve_title_shot_inbox(self, *_args):
        pass

    def ensure_company_champions(self, _roster, belts, _name, _region, _pop, **kwargs):
        return belts, kwargs.get("interim_belts", {}), kwargs.get("belt_history", {})

    def record_change(self, *_args):
        pass


def test_result_index_is_idempotent():
    probe = ResultProbe()
    first = {
        "date": "Month 1 Week 1", "company": "Test FC", "event": "Test FC 1",
        "summary": "Card one", "fights": 1,
        "fight_logs": [{"label": "MAIN", "a": "A", "b": "B", "a_id": "a", "b_id": "b", "result": "A - Decision", "scorecards": "29-28"}],
    }
    second = {
        **first, "summary": "A genuinely different card",
        "fight_logs": [{"label": "MAIN", "a": "C", "b": "D", "a_id": "c", "b_id": "d", "result": "D - KO", "scorecards": ""}],
    }
    probe.result_records = [first, second]
    old_row = probe.result_index_row(first, has_replay=True)
    old_row.pop("record_id", None)
    old_row["key"] = "Month 1 Week 1|Test FC|Test FC 1"
    duplicate = dict(old_row)
    duplicate["key"] += "|2"
    probe.result_index = [old_row, duplicate]
    probe.promotions = []
    probe.ensure_result_index()
    keys_after_first = [row["key"] for row in probe.result_index]
    check(len(keys_after_first) == 2, "duplicate legacy row was not collapsed or distinct card was lost")
    probe.ensure_result_index()
    check([row["key"] for row in probe.result_index] == keys_after_first, "result migration was not idempotent")


def test_transactional_apply_rolls_back():
    probe = TransactionProbe()
    original_roster = list(probe.roster)
    try:
        probe.apply_world_data({"cash": 999, "fail": True})
    except ValueError:
        pass
    else:
        raise AssertionError("deliberately late load failure did not propagate")
    check(probe.cash == 100, "failed load changed live cash")
    check(probe.roster == original_roster, "failed load mutated the live roster")
    check(probe.marker == {"career": "original"}, "failed load partially changed nested career state")


def test_serialization_and_metadata_invariants():
    source = inspect.getsource(PersistenceMixin.serialize_world)
    check("ensure_all_company_champions()" not in source, "serialization still performs champion/roster repair")
    load_source = inspect.getsource(PersistenceMixin._apply_world_data_unchecked)
    check("ensure_all_company_champions()" not in load_source, "loading still performs champion/roster repair")
    original_writer = persistence.atomic_write_json_compact
    original_logging = persistence.LOGGER.disabled
    persistence.atomic_write_json_compact = lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("sidecar unavailable"))
    persistence.LOGGER.disabled = True
    try:
        with tempfile.TemporaryDirectory() as folder:
            check(TransactionProbe().write_save_metadata_sidecar(Path(folder) / "save.json", {"slot": "Test"}) is False,
                  "metadata cache failure was not isolated from the primary save")
    finally:
        persistence.atomic_write_json_compact = original_writer
        persistence.LOGGER.disabled = original_logging


def test_optional_backup_failures_do_not_block_save_or_slot_load():
    original_writer = persistence.atomic_write_split_save
    original_info = persistence.messagebox.showinfo
    original_error = persistence.messagebox.showerror
    original_logging = persistence.LOGGER.disabled
    writes = []
    errors = []
    persistence.atomic_write_split_save = lambda path, data: writes.append((Path(path), data))
    persistence.messagebox.showinfo = lambda *_args, **_kwargs: None
    persistence.messagebox.showerror = lambda *args, **_kwargs: errors.append(args)
    persistence.LOGGER.disabled = True
    try:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            current = root / "current.json"
            selected = root / "selected.json"
            current.write_text('{"cash": 100}', encoding="utf-8")
            selected.write_text('{"cash": 250}', encoding="utf-8")
            quick_probe = SaveFailureProbe(current)
            check(quick_probe.save_game() is True, "quick save was blocked by an optional backup failure")
            check(writes and writes[-1][0] == current, "quick save did not commit after backup failure")
            load_probe = SaveFailureProbe(current, selected)
            load_probe.load_selected_slot()
            check(load_probe.applied_payload == {"cash": 250},
                  "slot load was blocked by an optional current-slot backup failure")
            check(load_probe.closed_busy, "slot load did not close its busy overlay")
            check(not errors, "optional backup failures displayed a blocking operation error")
    finally:
        persistence.atomic_write_split_save = original_writer
        persistence.messagebox.showinfo = original_info
        persistence.messagebox.showerror = original_error
        persistence.LOGGER.disabled = original_logging


def test_backup_restore_validates_before_touching_destination():
    original_writer = persistence.atomic_write_split_save
    writes = []
    persistence.atomic_write_split_save = lambda path, data: writes.append((Path(path), data))
    try:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "backup.json"
            target = root / "savegame.json"
            source.write_text("[]", encoding="utf-8")
            target.write_text('{"cash": 100}', encoding="utf-8")
            probe = SaveFailureProbe(target)
            try:
                probe.restore_backup_file(source, target)
            except ValueError as exc:
                check("JSON object" in str(exc), "invalid top-level save received an unclear validation error")
            else:
                raise AssertionError("non-object backup payload was accepted for restore")
            check(not probe.backup_attempts, "destination backup ran before source validation")
            check(not writes, "invalid backup payload reached the save writer")
            check(target.read_text(encoding="utf-8") == '{"cash": 100}',
                  "invalid backup payload changed the destination slot")
    finally:
        persistence.atomic_write_split_save = original_writer


def test_external_block_prune_skips_symlink_entries():
    original_is_symlink = Path.is_symlink
    try:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            save = root / "savegame.json"
            block_root = root / "DataBlocks"
            block_root.mkdir()
            protected = block_root / "protected.link"
            stale = block_root / "stale.tmp"
            protected.write_text("keep", encoding="utf-8")
            stale.write_text("remove", encoding="utf-8")
            Path.is_symlink = lambda item: item.name == "protected.link" or original_is_symlink(item)
            persistence.prune_external_save_blocks(save, [])
            check(protected.exists(), "external-block pruning removed a symlinked entry")
            check(not stale.exists(), "external-block pruning did not remove an ordinary stale entry")
    finally:
        Path.is_symlink = original_is_symlink


def test_save_menu_selection_summary_and_action_state():
    class Value:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    class Button:
        def __init__(self):
            self.state = ""

        def configure(self, **kwargs):
            self.state = kwargs.get("state", self.state)

    class Listbox:
        def __init__(self):
            self.selected = ()

        def curselection(self):
            return self.selected

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "savegame.json"
        path.write_text('{"cash": 100}', encoding="utf-8")
        probe = TransactionProbe()
        probe.save_slot_list = Listbox()
        probe.save_slot_files = [path]
        probe.save_slot_sources = {path: "Career One"}
        probe.save_slot_groups = {path: "Main"}
        probe.save_selection_title = Value()
        probe.save_selection_detail = Value()
        probe.active_save_path = lambda: path
        probe.read_save_metadata_fast = lambda _path: {
            "company": "Regression FC", "month": 3, "week": 2, "saved_at": "2026-08-31T12:30",
        }
        probe.format_game_date = lambda month, week: f"Month {month}, Week {week}"
        for name in (
            "save_load_button", "save_copy_button", "save_delete_button",
            "save_backup_button", "save_move_button", "save_migrate_archetypes_button",
        ):
            setattr(probe, name, Button())
        probe.refresh_save_selection_summary()
        check(probe.save_load_button.state == "disabled", "save actions were enabled without a selection")
        probe.save_slot_list.selected = (0,)
        probe.refresh_save_selection_summary()
        check(probe.save_load_button.state == "normal" and probe.save_move_button.state == "normal",
              "save actions did not enable for a valid selection")
        check(probe.save_selection_title.value == "Career One  |  Main | ACTIVE",
              "save inspector did not identify the selected active career")
        check("Regression FC" in probe.save_selection_detail.value and "Month 3, Week 2" in probe.save_selection_detail.value,
              "save inspector did not expose selected metadata")


def test_save_menu_selection_summary_fails_closed_for_malformed_dates():
    class Value:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    class Button:
        def configure(self, **_kwargs):
            pass

    class Listbox:
        def curselection(self):
            return (0,)

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "savegame.json"
        path.write_text('{"cash": 100}', encoding="utf-8")
        probe = TransactionProbe()
        probe.save_slot_list = Listbox()
        probe.save_slot_files = [path]
        probe.save_slot_sources = {path: "Malformed Career"}
        probe.save_slot_groups = {path: "Main"}
        probe.save_selection_title = Value()
        probe.save_selection_detail = Value()
        probe.active_save_path = lambda: path
        probe.read_save_metadata_fast = lambda _path: {
            "company": "Legacy FC", "month": float("inf"), "week": float("nan"),
            "saved_at": "2026-08-31T12:30",
        }
        probe.format_game_date = lambda month, week: f"Month {int(month)}, Week {int(week)}"
        for name in (
            "save_load_button", "save_copy_button", "save_delete_button",
            "save_backup_button", "save_move_button", "save_migrate_archetypes_button",
        ):
            setattr(probe, name, Button())
        probe.refresh_save_selection_summary()
        check("Unknown game date" in probe.save_selection_detail.value,
              "malformed save metadata crashed or produced a fabricated calendar date")


def test_save_menu_identity_preserves_duplicate_folder_selection():
    main = Path("C:/MMA Saves/Shared/savegame.json")
    test_folder = Path("C:/MMA Saves/Folders/Shared/savegame.json")
    main_key = PersistenceMixin.save_entry_identity(main)
    test_key = PersistenceMixin.save_entry_identity(test_folder)
    check(main_key != test_key, "duplicate display names in different folders collapsed to one save identity")
    reordered = [test_key, main_key]
    check(PersistenceMixin.save_entry_index(reordered, main_key) == 1,
          "save selection did not follow its stable path identity after reorder")
    check(PersistenceMixin.save_entry_index(reordered, "save-entry:missing") is None,
          "missing save identity was silently mapped to another row")


def test_database_menu_identity_is_path_bound():
    first = Path("C:/MMA Databases/Default.universe.json")
    second = Path("C:/MMA Databases/Archive/Default.universe.json")
    first_key = PersistenceMixin.database_entry_identity(first)
    second_key = PersistenceMixin.database_entry_identity(second)
    check(first_key != second_key, "database rows with the same display stem collapsed to one identity")
    check(PersistenceMixin.save_entry_index([second_key, first_key], first_key) == 1,
          "database selection did not follow its stable path identity after refresh")


def test_finish_bonus_save_compatibility():
    current = fighter(finish_bonus_pct=17)
    row = serialize_fighter_model(current)
    check(row["finish_bonus_pct"] == 17, "current fighter serialization lost finish bonus")
    check(Fighter(**row).finish_bonus_pct == 17, "current fighter round trip lost finish bonus")
    row.pop("finish_bonus_pct")
    check(Fighter(**row).finish_bonus_pct == 0, "legacy fighter data did not receive the safe finish-bonus default")


def test_friend_identity_save_compatibility():
    current = fighter("Friend Identity", "FTR-friend-owner")
    current.friend = "Trusted Teammate"
    current.friend_fighter_id = "FTR-trusted-teammate"
    row = serialize_fighter_model(current)
    check(row["friend_fighter_id"] == "FTR-trusted-teammate", "current fighter serialization lost friend identity")
    check(Fighter(**row).friend_fighter_id == "FTR-trusted-teammate", "current fighter round trip lost friend identity")
    row.pop("friend_fighter_id")
    check(Fighter(**row).friend_fighter_id == "", "legacy fighter data did not receive the safe friend-ID default")
    current.relationship_story_keys = ["relationship:FTR-friend-owner:FTR-trusted-teammate"]
    row = serialize_fighter_model(current)
    check(Fighter(**row).relationship_story_keys == current.relationship_story_keys,
          "current fighter round trip lost the active relationship story key")
    row.pop("relationship_story_keys")
    check(Fighter(**row).relationship_story_keys == [],
          "legacy fighter data did not receive the safe relationship-story default")


def test_academy_prospect_identity_save_compatibility():
    current = fighter("Academy Identity", "FTR-academy-graduate")
    current.academy_graduate = True
    current.academy_prospect_id = "academy-prospect-42"
    row = serialize_fighter_model(current)
    check(row["academy_prospect_id"] == "academy-prospect-42",
          "current fighter serialization lost academy prospect identity")
    check(Fighter(**row).academy_prospect_id == "academy-prospect-42",
          "current fighter round trip lost academy prospect identity")
    row.pop("academy_prospect_id")
    check(Fighter(**row).academy_prospect_id == "",
          "legacy fighter data did not receive the safe academy prospect-ID default")


def test_contract_story_identity_save_compatibility():
    current = fighter("Contract Story Identity", "FTR-contract-story")
    current.contract_story_key = "contract-saga:FTR-contract-story:company:12:1"
    row = serialize_fighter_model(current)
    check(row["contract_story_key"] == current.contract_story_key,
          "current fighter serialization lost the active contract story key")
    check(Fighter(**row).contract_story_key == current.contract_story_key,
          "current fighter round trip lost the active contract story key")
    row.pop("contract_story_key")
    check(Fighter(**row).contract_story_key == "",
          "legacy fighter data did not receive the safe empty contract story key")


def test_feeder_story_identity_save_compatibility():
    current = fighter("Feeder Story Identity", "FTR-feeder-story")
    current.feeder_story_key = "feeder-pathway:FTR-feeder-story:child-company:12:1"
    row = serialize_fighter_model(current)
    check(row["feeder_story_key"] == current.feeder_story_key,
          "current fighter serialization lost the active feeder story key")
    check(Fighter(**row).feeder_story_key == current.feeder_story_key,
          "current fighter round trip lost the active feeder story key")
    row.pop("feeder_story_key")
    check(Fighter(**row).feeder_story_key == "",
          "legacy fighter data did not receive the safe empty feeder story key")


def test_breakout_story_identity_save_compatibility():
    current = fighter("Breakout Story Identity", "FTR-breakout-story")
    current.breakout_story_key = "breakout:FTR-breakout-story:12:1:FTR-opponent:5:2:0"
    row = serialize_fighter_model(current)
    check(row["breakout_story_key"] == current.breakout_story_key,
          "current fighter serialization lost the active breakout story key")
    check(Fighter(**row).breakout_story_key == current.breakout_story_key,
          "current fighter round trip lost the active breakout story key")
    row.pop("breakout_story_key")
    check(Fighter(**row).breakout_story_key == "",
          "legacy fighter data did not receive the safe empty breakout story key")


def test_crossroads_story_identity_save_compatibility():
    current = fighter("Crossroads Story Identity", "FTR-crossroads-story")
    current.crossroads_story_key = "crossroads:FTR-crossroads-story:12:1:FTR-opponent:14:9:1"
    row = serialize_fighter_model(current)
    check(row["crossroads_story_key"] == current.crossroads_story_key,
          "current fighter serialization lost the active crossroads story key")
    check(Fighter(**row).crossroads_story_key == current.crossroads_story_key,
          "current fighter round trip lost the active crossroads story key")
    row.pop("crossroads_story_key")
    check(Fighter(**row).crossroads_story_key == "",
          "legacy fighter data did not receive the safe empty crossroads story key")


def test_farewell_story_identity_save_compatibility():
    current = fighter("Farewell Story Identity", "FTR-farewell-story")
    current.farewell_story_key = "farewell:FTR-farewell-story:12"
    row = serialize_fighter_model(current)
    check(row["farewell_story_key"] == current.farewell_story_key,
          "current fighter serialization lost the active farewell story key")
    check(Fighter(**row).farewell_story_key == current.farewell_story_key,
          "current fighter round trip lost the active farewell story key")
    row.pop("farewell_story_key")
    check(Fighter(**row).farewell_story_key == "",
          "legacy fighter data did not receive the safe empty farewell story key")


def test_staff_story_identity_save_compatibility():
    probe = WorldProbe()
    current = {
        "name": "Staff Story Identity", "role": "Matchmaker", "skill": 74,
        "salary": 8_500, "morale": 72, "staff_id": "STF-story-current",
        "staff_story_key": "staff-tenure:STF-story-current:company:12:1",
        "staff_milestone_kinds": ["standout_card", "sellout_campaign", "standout_card"],
        "staff_legacy_score": 9,
    }
    legacy = {
        "name": "Legacy Staff Story", "role": "Doctor", "skill": 65,
        "salary": 7_000, "morale": 68, "staff_id": "STF-story-legacy",
        "staff_milestone_kinds": "malformed legacy value", "staff_legacy_score": "not-a-score",
    }
    probe.staff = [current, legacy]
    probe.staff_candidates = []
    rng_before = random.getstate()
    probe.ensure_staff_profiles()
    check(current["staff_story_key"] == "staff-tenure:STF-story-current:company:12:1",
          "current staff normalization lost the active tenure story key")
    check(current["staff_milestone_kinds"] == ["standout_card", "sellout_campaign"]
          and current["staff_legacy_score"] == 9,
          "current staff normalization lost or duplicated career milestones")
    check(legacy["staff_story_key"] == "",
          "legacy staff data did not receive the safe empty tenure story key")
    check(legacy["staff_milestone_kinds"] == [] and legacy["staff_legacy_score"] == 0,
          "legacy staff data did not receive safe empty career-milestone defaults")
    check(random.getstate() == rng_before,
          "staff story compatibility repair consumed simulation RNG")


def test_world_domain_integrity():
    probe = WorldProbe()
    expiring = fighter("Popular Champion", "FTR-expired", champion=True, popularity=90, contract_months=0)
    probe.roster = [expiring]
    probe.update_contracts()
    check(expiring not in probe.roster and expiring in probe.free_agents, "expired star received a hidden free renewal")
    check(expiring.contract_months == 0 and not expiring.exclusive, "released fighter retained an active contract")

    scheduled = fighter("Same Name", "FTR-scheduled")
    namesake = fighter("Same Name", "FTR-namesake")
    probe.scheduled_events = [{"month": 2, "week": 1, "fights": [{"fighters": [scheduled.name], "fighter_ids": [scheduled.fighter_id]}]}]
    check(probe.fighter_has_scheduled_fight(scheduled), "stable scheduled fighter ID was not recognized")
    check(not probe.fighter_has_scheduled_fight(namesake), "display-name collision incorrectly marked a namesake busy")

    probe.roster = [fighter("Debt Fighter", "FTR-debt", morale=70)]
    probe.finance = {}
    probe.cash = -10_000
    probe.apply_player_financial_pressure()
    check(probe.finance["negative_cash_months"] == 1 and probe.company_stability == 58,
          "first debt month did not persist a modest stability consequence")
    check(probe.roster[0].morale == 69, "debt pressure did not reach roster morale")
    probe.cash = 500
    probe.apply_player_financial_pressure()
    check(probe.finance["negative_cash_months"] == 0, "positive cash did not reset the debt streak")


def test_outside_draw_and_full_purse():
    probe = WorldProbe()
    contracted = fighter("Outside Fighter", "FTR-outside", exclusive=False)
    opponent = fighter("Outside Opponent", "FTR-opponent")
    probe.roster = [contracted]
    draw_calls = []
    probe.create_generated_fighter = lambda *_args: opponent
    probe.simulate_fight = lambda *_args: (contracted, opponent, "Draw", 3, [])
    probe.apply_draw_result = lambda a, b, fight: (setattr(a, "record_d", a.record_d + 1), draw_calls.append((a, b, fight)))
    rolls = iter((0.0, 1.0))
    original_random = world_module.random.random
    world_module.random.random = lambda: next(rolls)
    try:
        probe.simulate_nonexclusive_outside_fights()
    finally:
        world_module.random.random = original_random
    check(draw_calls and contracted.record_d == 1 and contracted.record_l == 2,
          "outside draw bypassed shared draw handling or became a loss")

    probe.finance = {
        "ticket_price": 50, "media_rights": {}, "sponsor_deals": [], "commentators": [],
        "broadcast_cut": 0.1, "sponsor_income": 0, "merch_rate": 0.0, "production_base": 0,
        "medical_base": 0, "marketing_budget": 0, "drug_test_cost": 0, "tax_rate": 0.0,
    }
    probe.engine_settings = {"config_version": 2, "ko_power": 1.0, "submission_finish": 1.0, "decision_noise": 1.0, "gas_cost": 1.0, "damage": 1.0}
    probe.business_settings = {"config_version": 1, "gate_multiplier": 1.0}
    probe.broadcasters = []
    probe.post_show_bonuses = {"fight": 0, "ko": 0, "sub": 0}
    probe.venue_capacity_for = lambda _venue: 1000
    probe.event_atmosphere = lambda *_args: {"attendance_factor": 1.0, "sponsor_factor": 1.0, "merch_factor": 1.0}
    probe.ensure_finance_defaults = lambda: None
    finance = probe.calculate_event_finance(40, 15_000, {"venue": "Test", "fights": []}, [], contracted_fighter_pay=25_000)
    check(finance["fighter_pay"] == 25_000 and finance["contracted_fighter_pay"] == 25_000,
          "event finance discounted a signed purse")
    check(finance["tier_purse_savings"] == 0, "event finance still reports hidden purse savings")


def test_scout_auto_assignment_toggle():
    probe = WorldProbe()
    probe.rules["auto_assign_idle_scouts"] = False
    probe.staff = [{"name": "Scout", "role": "Scout"}]
    probe.scout_workload = lambda _name: 0
    probe.start_scout_report_for_fighter = lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("disabled automation assigned a scout"))
    probe.auto_assign_idle_scouts()


def test_legacy_style_identity_normalization():
    for raw_style, expected in (
        ("Wushu", "Sanda"),
        ("Submission Hunter", "BJJ"),
        ("Dynamic Attacker", "Well-Rounded"),
        ("Unknown Style", "Well-Rounded"),
    ):
        row = persistence.serialize_fighter_model(fighter(style=raw_style))
        row.pop("secondary_style", None)
        loaded = persistence.load_model_row(
            row, Fighter, persistence.FIGHTER_SAVE_FIELDS, "legacy style probe",
        )
        check(loaded.style == expected and loaded.secondary_style == "",
              f"legacy style {raw_style!r} did not normalize safely")
    row = persistence.serialize_fighter_model(
        fighter(style="Kickboxer", secondary_style="BJJ"),
    )
    loaded = persistence.load_model_row(
        row, Fighter, persistence.FIGHTER_SAVE_FIELDS, "mixed style probe",
    )
    check(loaded.style == "Kickboxer" and loaded.secondary_style == "BJJ",
          "supported mixed style identity did not survive a model round trip")
    check(loaded.style_label == "Kickboxer / BJJ",
          "mixed style identity did not produce its player-facing label")


def test_legacy_boxing_skill_derivation():
    legacy = fighter(detailed_skills={
        "punch_technique": 82, "hand_speed": 76, "conditioning": 70,
        "creative_punches": 68, "feints": 74, "reflexes": 80,
        "head_movement": 77, "adaptability": 71,
    })
    ViewMixin.ensure_detailed_skills(object(), legacy)
    check(legacy.detailed_skills["combination_punching"] == 76,
          "legacy combination punching was not derived from the saved boxing profile")
    check(legacy.detailed_skills["body_punching"] == 75,
          "legacy body punching was not derived from the saved boxing profile")
    check(legacy.detailed_skills["counter_timing"] == 76,
          "legacy counter timing was not derived from the saved defensive profile")


def test_signature_move_save_compatibility():
    original = fighter(
        signature_moves=["one_two", "rear_naked_choke"],
        career_signature_stats={"one_two": {"attempts": 8, "landed": 5, "finishes": 1}},
        career_move_family_stats={"Boxing": {"attempts": 12, "effective": 7}},
    )
    loaded = persistence.load_model_row(
        persistence.serialize_fighter_model(original), Fighter,
        persistence.FIGHTER_SAVE_FIELDS, "signature move probe",
    )
    check(loaded.signature_moves == original.signature_moves
          and loaded.career_signature_stats == original.career_signature_stats
          and loaded.career_move_family_stats == original.career_move_family_stats,
          "signature move identity or career totals did not survive a save round trip")
    row = persistence.serialize_fighter_model(original)
    row["signature_moves"] = ["unknown_future_move", "one_two", "one_two"]
    repaired = persistence.load_model_row(row, Fighter, persistence.FIGHTER_SAVE_FIELDS, "unknown signature probe")
    check(repaired.signature_moves == ["one_two"],
          "unknown or duplicate signature IDs did not degrade to the legal move pool")


def main():
    random.seed(4401)
    test_career_archetype_migration_is_explicit_and_non_destructive()
    test_result_index_is_idempotent()
    test_transactional_apply_rolls_back()
    test_serialization_and_metadata_invariants()
    test_optional_backup_failures_do_not_block_save_or_slot_load()
    test_backup_restore_validates_before_touching_destination()
    test_external_block_prune_skips_symlink_entries()
    test_save_menu_selection_summary_and_action_state()
    test_save_menu_selection_summary_fails_closed_for_malformed_dates()
    test_finish_bonus_save_compatibility()
    test_friend_identity_save_compatibility()
    test_academy_prospect_identity_save_compatibility()
    test_contract_story_identity_save_compatibility()
    test_feeder_story_identity_save_compatibility()
    test_breakout_story_identity_save_compatibility()
    test_crossroads_story_identity_save_compatibility()
    test_farewell_story_identity_save_compatibility()
    test_staff_story_identity_save_compatibility()
    test_world_domain_integrity()
    test_outside_draw_and_full_purse()
    test_scout_auto_assignment_toggle()
    test_legacy_style_identity_normalization()
    test_legacy_boxing_skill_derivation()
    test_signature_move_save_compatibility()
    test_save_library_reader_does_not_create_missing_save_directory()
    print("PERSISTENCE REGRESSION TEST PASSED")


if __name__ == "__main__":
    main()
