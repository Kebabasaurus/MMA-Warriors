"""Ensure the structural parity gate rejects changes that alter selection."""

from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace
import unittest

import fight_moves
from tools.move_registry_parity import DEFAULT_REFERENCE, build_dump, compare, compare_legacy, compare_followup_update, compare_deprecation_update, envelope


class MoveParityTests(unittest.TestCase):
    def setUp(self):
        self.dump = build_dump(fight_moves)
        self.reference = envelope(self.dump, "test")

    def test_checked_in_reference_matches(self):
        reference = json.loads(DEFAULT_REFERENCE.read_text(encoding="utf-8"))
        source = json.loads(DEFAULT_REFERENCE.with_name("move_registry_slice6.json").read_text(encoding="utf-8"))
        manifest = json.loads(DEFAULT_REFERENCE.with_name("move_followup_phase31_revised_manifest.json").read_text(encoding="utf-8"))
        followups = json.loads(DEFAULT_REFERENCE.with_name("move_registry_phase31_revised.json").read_text(encoding="utf-8"))
        schema2 = json.loads(DEFAULT_REFERENCE.with_name("move_registry_schema2.json").read_text(encoding="utf-8"))
        diversity = json.loads(DEFAULT_REFERENCE.with_name("move_followup_diversity_manifest.json").read_text(encoding="utf-8"))
        frozen_diversity = json.loads(DEFAULT_REFERENCE.with_name("move_registry_followup_diversity.json").read_text(encoding="utf-8"))
        continuity = json.loads(DEFAULT_REFERENCE.with_name("move_followup_continuity_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(compare_legacy(reference, source["dump"]), [])
        self.assertEqual(compare_followup_update(source, followups["dump"], manifest), [])
        self.assertEqual(compare_deprecation_update(followups, schema2["dump"]), [])
        self.assertEqual(compare_followup_update(schema2, frozen_diversity["dump"], diversity), [])
        self.assertEqual(compare_followup_update(frozen_diversity, self.dump, continuity), [])

    def test_current_content_snapshot_matches(self):
        reference = json.loads(DEFAULT_REFERENCE.with_name("move_registry_followup_continuity.json").read_text(encoding="utf-8"))
        self.assertEqual(compare(reference, self.dump), [])

    def test_legacy_projection_does_not_hide_changed_historical_fields(self):
        reference = json.loads(DEFAULT_REFERENCE.read_text(encoding="utf-8"))
        changed = deepcopy(reference["dump"])
        original_id = reference["dump"]["move_order"][0]
        next(row for row in changed["moves"] if row["move_id"] == original_id)["name"] = "changed"
        self.assertTrue(compare_legacy(reference, changed))

    def test_reordered_definitions_fail_even_with_same_records(self):
        registry = SimpleNamespace(**vars(fight_moves))
        registry.MOVE_DEFINITIONS = tuple(reversed(registry.MOVE_DEFINITIONS))
        changed = build_dump(registry)
        self.assertEqual(self.dump["moves"], changed["moves"])
        self.assertIn("Registry parity changed: move_order", compare(self.reference, changed))

    def test_changed_field_fails(self):
        registry = SimpleNamespace(**vars(fight_moves))
        first, *rest = registry.MOVE_DEFINITIONS
        registry.MOVE_DEFINITIONS = (replace(first, energy=first.energy + 0.1), *rest)
        self.assertIn("Registry parity changed: moves", compare(self.reference, build_dump(registry)))

    def test_lookup_order_and_target_semantics_are_protected(self):
        registry = SimpleNamespace(**vars(fight_moves))
        registry.legal_moves = lambda action, position, target="": tuple(
            reversed(fight_moves.legal_moves(action, position, target)))
        self.assertIn("Registry parity changed: legal_moves", compare(self.reference, build_dump(registry)))
        registry.legal_moves = lambda action, position, target="": fight_moves.legal_moves(
            action, position, target or "head")
        self.assertIn("Registry parity changed: legal_moves", compare(self.reference, build_dump(registry)))

    def test_corrupt_reference_fails(self):
        broken = deepcopy(self.reference)
        broken["dump"]["move_order"].reverse()
        self.assertIn("Reference checksum does not match its dump", compare(broken, self.dump))

    def test_lookup_cross_product_is_complete(self):
        self.assertEqual(len(self.dump["legal_moves"]), len(fight_moves.KNOWN_PARENT_ACTIONS) * 14 * 4)
        self.assertEqual(len({(row["action"], row["position"], row["target"])
                              for row in self.dump["legal_moves"]}), len(self.dump["legal_moves"]))


if __name__ == "__main__":
    unittest.main()
