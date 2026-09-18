"""Identity-safe selection and mutation checks for the standalone database editor."""

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from database_editor import UniverseDatabaseEditor
from feature_foundation import FoundationMixin
from models import Fighter
from views import ViewMixin


class DatabaseEditorIdentityTests(unittest.TestCase):
    @staticmethod
    def fighter(**overrides):
        values = {
            "name": "Test Fighter", "fighter_id": "test-fighter", "weight": "Lightweight", "age": 25,
            "record_w": 0, "record_l": 0, "striking": 50, "wrestling": 50, "grappling": 50,
            "cardio": 50, "chin": 50, "popularity": 10, "momentum": 0, "morale": 50, "purse": 1000,
        }
        values.update(overrides)
        return Fighter(**values)

    @staticmethod
    def harness():
        app = object.__new__(UniverseDatabaseEditor)
        app.pack = {
            "sections": {
                "fighters": {"all_fighters": []},
                "companies": {"player_company": {"name": "Player Company"}, "promotions": [], "regional_feeders": []},
            }
        }
        app.fighter_selection = None
        app.company_selection = None
        app._selected_fighter_record = None
        app._selected_company_record = None
        app.fighter_row_map = {}
        app.company_row_map = {}
        return app

    def test_validate_is_observational_and_does_not_sync_live_pack(self):
        pack_path = Path(__file__).resolve().parent / "Databases" / "Default Universe.universe.json"
        app = object.__new__(UniverseDatabaseEditor)
        app.pack = json.loads(pack_path.read_text(encoding="utf-8"))
        app.path = pack_path
        app.status_var = type("Status", (), {"set": lambda self, _value: None})()
        app.ensure_database_loaded = lambda: True
        before = copy.deepcopy(app.pack)
        with patch("database_editor.messagebox.showinfo"):
            app.validate_database()
        self.assertEqual(app.pack, before)

    def test_row_keys_prefer_saved_ids_and_hash_legacy_payloads(self):
        stable = {"fighter_id": "fighter-7", "name": "Stable"}
        legacy = {"name": "Legacy", "owner": "Free Agent"}
        self.assertEqual(UniverseDatabaseEditor._database_row_key("fighter", stable), "fighter:fighter-7")
        first = UniverseDatabaseEditor._database_row_key("fighter", legacy)
        second = UniverseDatabaseEditor._database_row_key("fighter", dict(legacy))
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("fighter:legacy:"))
        self.assertNotEqual(first, UniverseDatabaseEditor._database_row_key("company", legacy))

    def test_selected_fighter_follows_source_record_after_reorder(self):
        app = self.harness()
        first = {"fighter_id": "f-1", "name": "First"}
        second = {"fighter_id": "f-2", "name": "Second"}
        app.fighter_records().extend([first, second])
        app._selected_fighter_record = first
        app.fighter_selection = "fighter:f-1"
        app.fighter_row_map = {"fighter:f-1": first, "fighter:f-2": second}
        app.fighter_records()[:] = [second, first]
        self.assertIs(app.selected_fighter(), first)

    def test_selected_company_follows_source_record_after_reorder(self):
        app = self.harness()
        first = {"company_id": "c-1", "name": "First"}
        second = {"company_id": "c-2", "name": "Second"}
        app.company_records().extend([first, second])
        app._selected_company_record = first
        app.company_selection = "company:c-1"
        app.company_row_map = {"company:c-1": first, "company:c-2": second}
        app.company_records()[:] = [second, first]
        self.assertIs(app.selected_company(), first)

    def test_delete_fighter_removes_selected_object_not_stale_source_index(self):
        app = self.harness()
        first = {"fighter_id": "f-1", "name": "First"}
        second = {"fighter_id": "f-2", "name": "Second"}
        app.fighter_records().extend([first, second])
        app._selected_fighter_record = first
        app.fighter_selection = "fighter:f-1"
        app.fighter_row_map = {"fighter:f-1": first, "fighter:f-2": second}
        app.fighter_records()[:] = [second, first]
        app.refresh_fighters = lambda: None
        with patch("database_editor.messagebox.askyesno", return_value=True):
            app.delete_fighter()
        self.assertEqual(app.fighter_records(), [second])

    def test_delete_company_removes_selected_object_not_stale_source_index(self):
        app = self.harness()
        first = {"company_id": "c-1", "name": "First"}
        second = {"company_id": "c-2", "name": "Second"}
        app.company_records().extend([first, second])
        app._selected_company_record = first
        app.company_selection = "company:c-1"
        app.company_row_map = {"company:c-1": first, "company:c-2": second}
        app.company_records()[:] = [second, first]
        app.refresh_companies = lambda: None
        with patch("database_editor.messagebox.askyesno", return_value=True):
            app.delete_company()
        self.assertEqual(app.company_records(), [second])

    def test_current_career_editor_row_identity_is_not_a_sort_position(self):
        athlete = self.fighter(name="Same Name", fighter_id="fighter-7", weight="Lightweight", age=25)
        first = ViewMixin._career_editor_row_identity("Player Co", athlete, index=0)
        second = ViewMixin._career_editor_row_identity("Player Co", athlete, index=99)
        other_owner = ViewMixin._career_editor_row_identity("World Boxing", athlete, index=0)
        self.assertEqual(first, second)
        self.assertNotEqual(first, other_owner)

    def test_current_career_editor_legacy_identity_is_deterministic(self):
        athlete = self.fighter(name="Legacy Name", fighter_id="", weight="Welterweight", age=28)
        first = ViewMixin._career_editor_row_identity("Free Agent", athlete, index=0)
        second = ViewMixin._career_editor_row_identity("Free Agent", athlete, index=4)
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("legacy-editor:"))

    def test_editor_transfer_records_destination_membership_before_roster_insert(self):
        class Harness(ViewMixin, FoundationMixin):
            pass

        app = Harness()
        app.month, app.week = 8, 2
        app.promotions = []
        app.player_company_name = "Player Co"
        app.roster = []
        app.ensure_foundation_state()
        athlete = self.fighter(name="Transfer Name", fighter_id="fighter-transfer", weight="Lightweight", age=25)
        fact = app._record_editor_membership_arrival(athlete, "World Boxing")
        self.assertEqual(fact["action"], "join")
        self.assertEqual(fact["promotion_name"], "World Boxing")
        rows = app.foundation_membership_events(fighter_id=athlete.fighter_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_transaction"], fact["source_transaction"])


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    if not result.result.wasSuccessful():
        raise SystemExit(1)
