"""Focused regression coverage for transactional Database Editor Save As."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from constants import REGIONS
from database_editor import UniverseDatabaseEditor
from universe_validation import COMBAT_SPORTS


class _Status:
    def __init__(self):
        self.value = ""

    def set(self, value):
        self.value = value


class _SaveAsEditor:
    """Headless editor shell exposing only the Save As collaborators."""

    save_database_as = UniverseDatabaseEditor.save_database_as
    _save_database_to_path = UniverseDatabaseEditor._save_database_to_path

    def __init__(self, source_path, pack):
        self.path = Path(source_path)
        self.pack = pack
        self.database_dir = self.path.parent
        self.status_var = _Status()
        self.dirty = True
        self.refreshes = []
        self.sync_count = 0

    def ensure_database_loaded(self):
        return True

    def sync_for_save(self):
        self.sync_count += 1

    def refresh_all(self):
        pass

    def refresh_database_selector(self, *, select_name):
        self.refreshes.append(select_name)


class DatabaseEditorSaveAsTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.source = self.root / "Original.universe.json"
        self.source.write_text("{\"original\": true}\n", encoding="utf-8")

    @staticmethod
    def valid_pack():
        """A pack that actually satisfies the shared universe schema.

        Save As validates before writing, so a fixture missing a required
        section makes the success-path tests exercise the rejection path
        instead, and raises an unpatched warning dialog that blocks a headless
        run.  ``test_fixture_pack_is_actually_valid`` keeps this honest.
        """
        return {
            "type": "universe_database",
            "sections": {
                "fighters": {
                    "all_fighters": [{
                        "name": "Test Fighter", "placement": "free_agents", "owner": "Free Agent",
                        "weight": "Lightweight", "gender": "Male", "rating": 70, "age": 28,
                        "region": "USA", "nationality": "United States", "record_w": 0,
                        "record_l": 0, "record_d": 0,
                    }],
                },
                "combat_sports": {
                    "rosters": {sport: [] for sport in COMBAT_SPORTS},
                    "profiles": {},
                    "prime_divisions": {},
                },
                "companies": {
                    "promotions": [{
                        "name": "Test Promotion", "region": "USA", "size": 40,
                        "cash": 1_000_000, "roster_key": "test_promotion",
                    }],
                    "regional_feeders": [],
                },
                "media": {
                    "player_broadcasters": [{"name": "Test Webcast", "reach": 20, "fee": 10_000, "type": "Streaming"}],
                    "rights_packages": [{"id": "test_pack", "name": "Test Rights", "reach": 30, "base_fee": 25_000}],
                },
                "regions": {region: {} for region in REGIONS},
            },
        }

    def test_fixture_pack_is_actually_valid(self):
        from database_editor import validate_universe_pack

        self.assertEqual([], validate_universe_pack(self.valid_pack()))

    def test_save_as_commits_path_only_after_successful_atomic_write(self):
        target = self.root / "Saved Copy.universe.json"
        editor = _SaveAsEditor(self.source, self.valid_pack())

        with patch("database_editor.filedialog.asksaveasfilename", return_value=str(target)):
            self.assertIsNone(editor.save_database_as())

        self.assertEqual(editor.path, target)
        self.assertEqual(editor.refreshes, [target.name])
        self.assertTrue(target.exists())
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), editor.pack)
        self.assertTrue(editor.dirty)

    def test_save_as_validation_failure_keeps_original_path_and_dirty_pack(self):
        target = self.root / "Invalid Copy.universe.json"
        pack = {"type": "universe_database", "sections": {}}
        editor = _SaveAsEditor(self.source, pack)

        with (
            patch("database_editor.filedialog.asksaveasfilename", return_value=str(target)),
            patch("database_editor.messagebox.showwarning") as warning,
        ):
            editor.save_database_as()

        self.assertEqual(editor.path, self.source)
        self.assertIs(editor.pack, pack)
        self.assertTrue(editor.dirty)
        self.assertEqual(editor.refreshes, [])
        self.assertFalse(target.exists())
        warning.assert_called_once()

    def test_save_as_write_failure_keeps_original_path_and_dirty_pack(self):
        target = self.root / "Unwritable Copy.universe.json"
        pack = self.valid_pack()
        editor = _SaveAsEditor(self.source, pack)

        with (
            patch("database_editor.filedialog.asksaveasfilename", return_value=str(target)),
            patch("database_editor.atomic_write_json", side_effect=OSError("disk full")),
            patch("database_editor.messagebox.showerror") as error,
        ):
            editor.save_database_as()

        self.assertEqual(editor.path, self.source)
        self.assertIs(editor.pack, pack)
        self.assertTrue(editor.dirty)
        self.assertEqual(editor.refreshes, [])
        self.assertFalse(target.exists())
        error.assert_called_once()

    def test_save_as_cancel_keeps_current_database(self):
        editor = _SaveAsEditor(self.source, self.valid_pack())

        with patch("database_editor.filedialog.asksaveasfilename", return_value=""):
            editor.save_database_as()

        self.assertEqual(editor.path, self.source)
        self.assertEqual(editor.refreshes, [])
        self.assertEqual(editor.sync_count, 0)


if __name__ == "__main__":
    unittest.main()
