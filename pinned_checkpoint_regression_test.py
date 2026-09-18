"""Regression coverage for explicit pinned spectator/career checkpoints."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import persistence
from persistence import PersistenceMixin


class CheckpointProbe(PersistenceMixin):
    def __init__(self, root):
        self._root = Path(root)
        self.active_save_name = "Testing V2"
        self.active_save_group = "Main"
        self.event_log = []
        self.status = ""

    def save_slot_dir(self, name=None, create=True, group=None):
        path = self._root / str(name or self.active_save_name)
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def serialize_world(self):
        return {"month": 2, "week": 3, "rules": {"simulation_pause_policy": {}}}

    def save_metadata(self, slot_name=""):
        return {"slot_name": slot_name, "saved_at": "2026-09-12T12:00:00", "company": "Spectator Mode"}

    def write_save_metadata_sidecar(self, _path, _metadata):
        return True

    def set_save_manager_status(self, message=""):
        self.status = str(message)

    def format_game_date(self, month=None, week=None, **_kwargs):
        return f"Sep 2026 W{week or 3}"


class PinnedCheckpointTests(unittest.TestCase):
    def test_pin_is_explicit_atomic_and_kept_separate_from_slot(self):
        with tempfile.TemporaryDirectory() as root:
            probe = CheckpointProbe(root)
            path = probe.pin_current_checkpoint("Before long simulation")
            self.assertIsNotNone(path)
            self.assertTrue(path.exists())
            self.assertEqual(path.parent.name, "Pinned Checkpoints")
            self.assertEqual(len(probe.pinned_checkpoint_files()), 1)
            self.assertFalse((Path(root) / "Testing V2" / "savegame.json").exists())
            self.assertIn("Pinned checkpoint created", probe.status)

    def test_duplicate_labels_receive_stable_suffix_without_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            probe = CheckpointProbe(root)
            first = probe.pin_current_checkpoint("Boundary")
            second = probe.pin_current_checkpoint("Boundary")
            self.assertNotEqual(first, second)
            self.assertEqual(len(probe.pinned_checkpoint_files()), 2)

    def test_limit_prevents_unbounded_manual_growth(self):
        with tempfile.TemporaryDirectory() as root:
            probe = CheckpointProbe(root)
            folder = probe.pinned_checkpoint_dir()
            for index in range(12):
                (folder / f"Existing {index}.json.gz").write_bytes(b"x")
            self.assertIsNone(probe.pin_current_checkpoint("Overflow"))
            self.assertIn("limit reached", probe.status)

    def test_failed_atomic_write_leaves_no_checkpoint(self):
        with tempfile.TemporaryDirectory() as root:
            probe = CheckpointProbe(root)
            with patch.object(persistence, "atomic_write_json_gzip", side_effect=OSError("disk full")):
                self.assertIsNone(probe.pin_current_checkpoint("Disk failure"))
            self.assertEqual(probe.pinned_checkpoint_files(), [])
            self.assertIn("Checkpoint failed", probe.status)

    def test_delete_rejects_paths_outside_current_slot(self):
        with tempfile.TemporaryDirectory() as root:
            probe = CheckpointProbe(root)
            outside = Path(root) / "outside.json.gz"
            outside.write_bytes(b"x")
            self.assertFalse(probe.delete_pinned_checkpoint(outside))
            self.assertTrue(outside.exists())


if __name__ == "__main__":
    unittest.main()
