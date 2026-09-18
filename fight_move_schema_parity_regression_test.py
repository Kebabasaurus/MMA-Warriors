"""Strict, explicit registry deprecation schema migration; no runtime schema edits."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import fight_moves
from tools.move_registry_parity import (
    DEFAULT_REFERENCE, build_dump, compare_deprecation_update, envelope, main,
)


class DeprecationSchemaParityTests(unittest.TestCase):
    def setUp(self):
        self.source_path = DEFAULT_REFERENCE.with_name("move_registry_phase31_revised.json")
        self.source = json.loads(self.source_path.read_text(encoding="utf-8"))
        self.actual = deepcopy(self.source["dump"])
        self.actual["schema_version"] = 2
        for move in self.actual["moves"]:
            move["deprecated"] = False

    def test_exact_additive_migration_and_source_purity(self):
        before = deepcopy(self.source)
        self.assertEqual(compare_deprecation_update(self.source, self.actual), [])
        self.assertEqual(self.source, before)

    def test_builder_reads_explicit_registry_version_with_legacy_default(self):
        registry = SimpleNamespace(**vars(fight_moves))
        registry.__dict__.pop("REGISTRY_SCHEMA_VERSION", None)
        self.assertEqual(build_dump(registry)["schema_version"], 1)
        registry.REGISTRY_SCHEMA_VERSION = 2
        self.assertEqual(build_dump(registry)["schema_version"], 2)

    def test_corrupt_source_already_migrated_source_and_noop_fail(self):
        corrupt = deepcopy(self.source)
        corrupt["sha256"] = "0" * 64
        self.assertIn("checksum", " ".join(compare_deprecation_update(corrupt, self.actual)))
        already_migrated = envelope(self.actual, "already-migrated")
        self.assertTrue(compare_deprecation_update(already_migrated, self.actual))
        self.assertTrue(compare_deprecation_update(self.source, self.source["dump"]))
        for version in (True, 1.0, "1"):
            source = deepcopy(self.source["dump"])
            source["schema_version"] = version
            self.assertTrue(compare_deprecation_update(envelope(source, "invalid-schema"), self.actual))
        for version in (True, 2.0, "2", 1):
            changed = deepcopy(self.actual)
            changed["schema_version"] = version
            self.assertTrue(compare_deprecation_update(self.source, changed))

    def test_deprecated_requires_literal_false_on_every_move(self):
        for value in (True, 0, 0.0, None, "false", [], {}):
            with self.subTest(value=value):
                changed = deepcopy(self.actual)
                changed["moves"][-1]["deprecated"] = value
                self.assertTrue(compare_deprecation_update(self.source, changed))
        for key in ("deprecated", "name"):
            changed = deepcopy(self.actual)
            del changed["moves"][-1][key]
            self.assertTrue(compare_deprecation_update(self.source, changed))

    def test_other_fields_order_lookups_and_ids_remain_exact(self):
        mutations = (
            lambda d: d["move_order"].reverse(),
            lambda d: d["moves"].reverse(),
            lambda d: d["moves"][0].update(name="Renamed technique"),
            lambda d: d["moves"][0].update(move_id="new_identity"),
            lambda d: d["moves"][0].update(energy=999),
            lambda d: d["moves"][0].update(follow_ups=[]),
            lambda d: d["moves"].append(dict(d["moves"][0], move_id="new_move")),
            lambda d: d["legal_moves"].reverse(),
            lambda d: d["legal_moves"][0].update(ids=["invented"]),
            lambda d: d["defense_order"].reverse(),
            lambda d: d["defenses"][0].update(name="Renamed defense"),
            lambda d: d.update(extra_field=True),
            lambda d: d.pop("legal_moves"),
            lambda d: d["moves"][0].update(minimum_skill=float(d["moves"][0]["minimum_skill"])),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                changed = deepcopy(self.actual)
                # Pick a guaranteed nonempty successor field for that mutation.
                if index == 5:
                    next(row for row in changed["moves"] if row["follow_ups"])["follow_ups"] = []
                else:
                    mutate(changed)
                self.assertTrue(compare_deprecation_update(self.source, changed))

    def test_missing_or_retrofitted_source_fields_fail_even_with_fresh_checksum(self):
        for mutation in (lambda d: d["moves"][0].pop("name"),
                         lambda d: d["moves"][0].update(deprecated=False),
                         lambda d: d.pop("defenses")):
            changed = deepcopy(self.source["dump"])
            mutation(changed)
            self.assertTrue(compare_deprecation_update(envelope(changed, "malformed-source"), self.actual))

    def test_cli_mode_verifies_without_writing_source(self):
        before = (self.source_path.read_bytes(), self.source_path.stat().st_mtime_ns)
        with patch("tools.move_registry_parity.build_dump", return_value=self.actual), redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--verify-deprecation", str(self.source_path)]), 0)
        changed = deepcopy(self.actual)
        changed["moves"][0]["deprecated"] = True
        with patch("tools.move_registry_parity.build_dump", return_value=changed), redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--verify-deprecation", str(self.source_path)]), 1)
        self.assertEqual((self.source_path.read_bytes(), self.source_path.stat().st_mtime_ns), before)


if __name__ == "__main__":
    unittest.main()
