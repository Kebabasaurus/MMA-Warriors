"""Successor migration must not turn historical parity into a permissive check."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from dataclasses import make_dataclass, replace
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import fight_moves
from fight_moves import MoveIndex
from fight_moves.followup_expansion import LEGACY_FOLLOWUP_UPDATES
from tools.move_registry_parity import (build_dump, compare, compare_legacy,
                                       compare_followup_update, envelope, main)


class FollowupParityTests(unittest.TestCase):
    def setUp(self):
        self.reference = json.loads((Path(__file__).resolve().parent / "analysis" /
                                     "move_registry_slice6.json").read_text(encoding="utf-8"))
        self.manifest = {"schema_version": 1, "source_sha256": self.reference["sha256"],
                         "updates": {key: {"follow_ups": list(value)}
                                     for key, value in LEGACY_FOLLOWUP_UPDATES.items()}}
        # Reconstruct the immutable source, independent of integration timing.
        historical_move = make_dataclass("SchemaOneMove", list(self.reference["dump"]["moves"][0]), frozen=True)
        rows = {}
        for row in self.reference["dump"]["moves"]:
            values = {key: frozenset(value) if key in {"positions", "targets"}
                      else tuple(value) if isinstance(value, list) else value
                      for key, value in row.items()}
            rows[row["move_id"]] = historical_move(**values)
        definitions = tuple(rows[key] for key in self.reference["dump"]["move_order"])
        definitions = tuple(replace(move, follow_ups=LEGACY_FOLLOWUP_UPDATES[move.move_id])
                            if move.move_id in LEGACY_FOLLOWUP_UPDATES else move for move in definitions)
        registry = SimpleNamespace(**vars(fight_moves))
        registry.REGISTRY_SCHEMA_VERSION = 1
        registry.MOVE_DEFINITIONS = definitions
        registry.legal_moves = MoveIndex(definitions).legal_moves
        self.actual = build_dump(registry)

    def check_failure(self, actual=None, manifest=None, reference=None):
        self.assertTrue(compare_followup_update(
            self.reference if reference is None else reference,
            self.actual if actual is None else actual,
            self.manifest if manifest is None else manifest))

    def test_reviewed_updates_pass_without_mutating_inputs(self):
        before = deepcopy((self.reference, self.actual, self.manifest))
        self.assertEqual(compare_followup_update(self.reference, self.actual, self.manifest), [])
        self.assertEqual((self.reference, self.actual, self.manifest), before)
        self.assertTrue(compare(self.reference, self.actual))
        self.assertTrue(compare_legacy(self.reference, self.actual))

    def test_unapproved_fields_and_order_stay_exact(self):
        for field, value in (("name", "changed"), ("minimum_skill", 99), ("attack_skills", ["strength"])):
            with self.subTest(field=field):
                actual = deepcopy(self.actual)
                actual["moves"][0][field] = value
                self.check_failure(actual=actual)
        for field in ("move_order", "defense_order", "legal_moves"):
            actual = deepcopy(self.actual)
            actual[field].reverse()
            self.check_failure(actual=actual)
        actual = deepcopy(self.actual)
        next(row for row in actual["legal_moves"] if len(row["ids"]) > 1)["ids"].reverse()
        self.check_failure(actual=actual)

    def test_corrupt_source_and_wrong_binding_fail(self):
        reference = deepcopy(self.reference)
        reference["dump"]["moves"][0]["name"] = "tampered"
        self.check_failure(reference=reference)
        manifest = deepcopy(self.manifest)
        manifest["source_sha256"] = "0" * 64
        self.check_failure(manifest=manifest)
        reference = envelope(reference["dump"], "different-valid-source")
        self.check_failure(reference=reference)

    def test_malformed_or_extra_manifest_fields_fail(self):
        for manifest in ([], {}, {**self.manifest, "unexpected": True},
                         {**self.manifest, "schema_version": True},
                         {**self.manifest, "schema_version": 2},
                         {**self.manifest, "updates": []}, {**self.manifest, "updates": {}}):
            self.check_failure(manifest=manifest)
        key = next(iter(self.manifest["updates"]))
        for update in ([], {}, {"follow_ups": "one_two"}, {"follow_ups": [None]},
                       {"follow_ups": ["missing"]}, {"follow_ups": [key]},
                       {"follow_ups": ["one_two", "one_two"]},
                       {"follow_ups": [], "name": "unapproved"}):
            manifest = deepcopy(self.manifest)
            manifest["updates"][key] = update
            self.check_failure(manifest=manifest)

    def test_unknown_source_and_noop_fail(self):
        manifest = deepcopy(self.manifest)
        manifest["updates"]["missing"] = {"follow_ups": ["one_two"]}
        self.check_failure(manifest=manifest)
        key = next(iter(self.manifest["updates"]))
        manifest = deepcopy(self.manifest)
        original = next(row for row in self.reference["dump"]["moves"] if row["move_id"] == key)
        manifest["updates"][key] = {"follow_ups": original["follow_ups"]}
        self.check_failure(manifest=manifest)

    def test_added_removed_or_unlisted_changes_fail(self):
        for operation in ("add", "remove", "unlisted"):
            actual = deepcopy(self.actual)
            if operation == "add":
                actual["moves"].append(dict(actual["moves"][0], move_id="unapproved_new_move"))
                actual["move_order"].append("unapproved_new_move")
            elif operation == "remove":
                removed = actual["moves"].pop()
                actual["move_order"].remove(removed["move_id"])
            else:
                row = next(row for row in actual["moves"] if row["move_id"] not in self.manifest["updates"])
                row["follow_ups"] = ["unapproved_successor"]
            self.check_failure(actual=actual)

    def test_cli_rejects_missing_or_unrelated_manifest_option(self):
        for args in (("--verify-followups", "unused.json"),
                     ("--verify", "unused.json", "--followup-manifest", "unused.json")):
            with self.subTest(args=args), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main(args)
            self.assertEqual(error.exception.code, 2)

    def test_cli_verification_reads_only_and_reports_success(self):
        output = io.StringIO()
        with (patch.object(Path, "read_text", side_effect=[json.dumps(self.reference), json.dumps(self.manifest)]),
              patch.object(Path, "open", side_effect=AssertionError("Verification must not write files")),
              patch("tools.move_registry_parity.build_dump", return_value=self.actual),
              redirect_stdout(output)):
            result = main(("--verify-followups", "source.json", "--followup-manifest", "updates.json"))
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue())["failures"], [])


if __name__ == "__main__":
    unittest.main()
