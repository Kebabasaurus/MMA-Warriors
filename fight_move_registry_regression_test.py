"""Authoring errors must fail before they silently change move eligibility."""
from dataclasses import replace
from pathlib import Path
import unittest

from fight_moves import MOVE_DEFINITIONS, DEFENSE_DEFINITIONS
from fight_moves.validation import validate_move_registry, validate_defense_registry
from fight_moves.index import MoveIndex


class RegistryValidationTests(unittest.TestCase):
    def test_domain_catalogues_remain_small_enough_to_review(self):
        catalogue = Path(__file__).resolve().parent / "fight_moves" / "catalogue"
        sources = tuple(catalogue.rglob("*.py"))
        self.assertTrue(sources)
        for source in sources:
            with self.subTest(source=source.name):
                self.assertLessEqual(len(source.read_text(encoding="utf-8").splitlines()), 400)

    def test_existing_catalogue_validates(self):
        self.assertEqual(validate_move_registry(), [])
        self.assertEqual(validate_defense_registry(), [])

    def test_misspelled_behavior_tag_is_rejected(self):
        rows = (replace(MOVE_DEFINITIONS[0], tags=("style_finisher",)), *MOVE_DEFINITIONS[1:])
        self.assertTrue(any("style_finisher" in error for error in validate_move_registry(rows)))

    def test_bad_catalogue_fails_at_import(self):
        import importlib
        from unittest.mock import patch
        import fight_moves.catalogue as catalogue
        import fight_moves.registry as registry
        rows = (replace(MOVE_DEFINITIONS[0], tags=("style_finisher",)), *MOVE_DEFINITIONS[1:])
        try:
            with patch.object(catalogue, "MOVE_DEFINITIONS", rows):
                with self.assertRaisesRegex(ValueError, "style_finisher"):
                    importlib.reload(registry)
        finally:
            importlib.reload(registry)

    def test_removed_and_duplicate_ids_are_rejected(self):
        self.assertTrue(any("Removed stable move IDs" in error
                            for error in validate_move_registry(MOVE_DEFINITIONS[1:])))
        self.assertIn("Move IDs must be unique", validate_move_registry(
            (*MOVE_DEFINITIONS, MOVE_DEFINITIONS[0])))

    def test_closed_metadata_vocabularies(self):
        for field, value in (("defense_families", ("spawrl",)),
                             ("entry_family", "doubel leg"),
                             ("attack_path", "unknown path")):
            with self.subTest(field=field):
                rows = (replace(MOVE_DEFINITIONS[0], **{field: value}), *MOVE_DEFINITIONS[1:])
                self.assertTrue(any(f"unknown {field}" in error for error in validate_move_registry(rows)))
        rows = (replace(DEFENSE_DEFINITIONS[0], families=("parrry",)), *DEFENSE_DEFINITIONS[1:])
        self.assertTrue(any("parrry" in error for error in validate_defense_registry(rows)))


class MoveIndexTests(unittest.TestCase):
    def test_lookup_matches_legacy_scan_including_unknown_values(self):
        index = MoveIndex(MOVE_DEFINITIONS)
        from fight_moves import ALL_POSITIONS, KNOWN_PARENT_ACTIONS
        for action in (*KNOWN_PARENT_ACTIONS, "unknown"):
            for position in (*ALL_POSITIONS, "unknown"):
                for target in ("", "head", "body", "leg", "unknown", None):
                    expected = tuple(move for move in MOVE_DEFINITIONS
                                     if move.parent_action == action and position in move.positions
                                     and (not move.targets or (target and target in move.targets)))
                    self.assertEqual(index.legal_moves(action, position, target), expected,
                                     (action, position, target))

    def test_returns_cached_immutable_rows_and_indexes(self):
        index = MoveIndex(MOVE_DEFINITIONS)
        rows = index.legal_moves("power_punch", "range", "head")
        self.assertIs(rows, index.legal_moves("power_punch", "range", "head"))
        with self.assertRaises(TypeError):
            index._by_key[("power_punch", "range", "head")] = ()
        from dataclasses import FrozenInstanceError
        with self.assertRaises(FrozenInstanceError):
            index._by_key = {}
        self.assertEqual(index.by_action("jab"), tuple(m for m in MOVE_DEFINITIONS if m.parent_action == "jab"))
        self.assertEqual(index.by_style("Boxer"), tuple(m for m in MOVE_DEFINITIONS if "Boxer" in m.preferred_styles))
        self.assertEqual(index.by_tag("counter"), frozenset(m.move_id for m in MOVE_DEFINITIONS if "counter" in m.tags))

    def test_lookup_never_revisits_definitions_at_800_moves(self):
        rows = [replace(MOVE_DEFINITIONS[i % len(MOVE_DEFINITIONS)], move_id=f"benchmark_{i}")
                for i in range(800)]
        index = MoveIndex(rows)
        expected = index.legal_moves("jab", "range")
        rows.clear()
        self.assertTrue(expected)
        self.assertIs(index.legal_moves("jab", "range"), expected)


if __name__ == "__main__":
    unittest.main()
