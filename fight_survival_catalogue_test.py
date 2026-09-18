"""Authoring contracts for the opt-in recovery catalogue."""
import unittest

from fight_moves.catalogue import MOVE_DEFINITIONS
from fight_moves.catalogue.survival_development import (
    SURVIVAL_DEVELOPMENT, SURVIVAL_ROLES, STANDING_RECOVERIES,
    CLINCH_RECOVERIES, TOP_RECOVERIES, BOTTOM_RECOVERIES, SPECIALIST_RECOVERIES,
)
from fight_moves.schema import ALL_POSITIONS, MOVE_TAGS
from fight_moves.validation import KNOWN_SKILLS, validate_move_registry


class SurvivalCatalogueTests(unittest.TestCase):
    def test_unique_additions_and_distribution(self):
        ids = {d.move_id for d in SURVIVAL_DEVELOPMENT}
        self.assertEqual(len(SURVIVAL_DEVELOPMENT), 40)
        self.assertEqual(len(ids), 40)
        self.assertEqual(len({d.name for d in SURVIVAL_DEVELOPMENT}), 40)
        self.assertFalse(ids & {d.move_id for d in MOVE_DEFINITIONS})
        self.assertEqual(tuple(map(len, (STANDING_RECOVERIES, CLINCH_RECOVERIES,
                                        TOP_RECOVERIES, BOTTOM_RECOVERIES,
                                        SPECIALIST_RECOVERIES))), (8, 6, 6, 8, 12))

    def test_valid_schema_skills_and_no_offensive_credit(self):
        self.assertEqual(validate_move_registry(MOVE_DEFINITIONS + SURVIVAL_DEVELOPMENT), [])
        for definition in SURVIVAL_DEVELOPMENT:
            with self.subTest(move=definition.move_id):
                self.assertEqual(definition.parent_action, "survive")
                self.assertTrue(definition.positions <= ALL_POSITIONS)
                self.assertLessEqual(len(definition.positions), 2)
                self.assertTrue(set(definition.attack_skills + definition.defense_skills) <= KNOWN_SKILLS)
                self.assertTrue(set(definition.tags) <= MOVE_TAGS)
                self.assertTrue({"defense", "recovery"} <= set(definition.tags))
                self.assertFalse(set(definition.tags) & {"chain", "combination", "style-combination",
                                                       "style-finisher", "finisher", "escape",
                                                       "submission", "strike", "transition"})
                self.assertEqual(definition.follow_ups, ())
                self.assertEqual(definition.components, ())
                self.assertFalse(definition.targets)

    def test_explicit_roles_and_knee_line_geometry(self):
        self.assertEqual(set(SURVIVAL_ROLES), {d.move_id for d in SURVIVAL_DEVELOPMENT})
        self.assertTrue(set(SURVIVAL_ROLES.values()) <= {"any", "top", "bottom", "controller", "controlled"})
        self.assertTrue(all(SURVIVAL_ROLES[d.move_id] == "top" for d in TOP_RECOVERIES))
        self.assertTrue(all(SURVIVAL_ROLES[d.move_id] == "bottom" for d in BOTTOM_RECOVERIES))
        for definition in SPECIALIST_RECOVERIES:
            self.assertNotEqual(SURVIVAL_ROLES[definition.move_id], "any")
        for definition in SURVIVAL_DEVELOPMENT:
            if "leg entanglement" in definition.positions:
                self.assertEqual(definition.positions, frozenset({"leg entanglement"}))
                self.assertFalse({"ground", "control", "ride"} & set(definition.tags))
        with self.assertRaises(TypeError):
            SURVIVAL_ROLES["cross_arm_recovery"] = "bottom"


if __name__ == "__main__":
    unittest.main()
