"""Regression coverage for shared, non-mutating universe validation."""

import json
import tempfile
import unittest
from pathlib import Path

from admin import AdminMixin
from seeding import SeedMixin
from universe_validation import validate_universe_pack, validate_universe_pack_issues


ROOT = Path(__file__).resolve().parent
DEFAULT_PACK = ROOT / "Databases" / "Default Universe.universe.json"


class SeedProbe(SeedMixin, AdminMixin):
    def __init__(self, default_path):
        self.default_path = Path(default_path)

    def universe_database_path(self, _name):
        return self.default_path


class UniverseValidationRegressionTest(unittest.TestCase):
    def load_default(self):
        return json.loads(DEFAULT_PACK.read_text(encoding="utf-8"))

    def test_shipped_pack_passes_shared_validator(self):
        self.assertEqual(validate_universe_pack(self.load_default()), [])

    def test_bad_media_and_scalar_types_are_reported_not_raised(self):
        pack = self.load_default()
        pack["sections"]["media"]["rights_packages"] = [{"name": "Broken", "base_fee": "not-a-number", "reach": "high"}]
        issues = validate_universe_pack_issues(pack)
        self.assertTrue(any(issue.section == "media" and issue.field == "base_fee" for issue in issues))
        self.assertTrue(any(issue.section == "media" and issue.field == "reach" for issue in issues))

    def test_missing_cross_section_and_combat_data_are_reported(self):
        pack = self.load_default()
        del pack["sections"]["regions"]
        pack["sections"]["combat_sports"]["profiles"]["Boxing"] = "broken"
        messages = validate_universe_pack(pack)
        self.assertTrue(any(message.startswith("regions") for message in messages))
        self.assertTrue(any(message.startswith("combat_sports.Boxing.profiles") for message in messages))

    def test_normal_load_keeps_legacy_source_bytes_and_mtime_unchanged(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / DEFAULT_PACK.name
            pack = self.load_default()
            del pack["sections"]["combat_sports"]["schema"]
            path.write_text(json.dumps(pack, indent=2), encoding="utf-8")
            before_bytes = path.read_bytes()
            before_mtime = path.stat().st_mtime_ns
            loaded = SeedProbe(path).load_universe_database_pack(path)
            self.assertGreaterEqual(loaded["sections"]["combat_sports"]["schema"], 4)
            self.assertEqual(path.read_bytes(), before_bytes)
            self.assertEqual(path.stat().st_mtime_ns, before_mtime)


if __name__ == "__main__":
    unittest.main(verbosity=2)
