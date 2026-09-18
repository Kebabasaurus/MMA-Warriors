"""Actual save, universe and world consumers retain the release move profile."""
from copy import deepcopy
import json
import unittest

from constants import DETAILED_SKILL_GROUPS, REGIONS, STYLES
from fight_engine import FightEngineMixin
from fight_release import ReleaseFightEngineMixin
from fight_moves import MOVE_DEFINITIONS, MOVE_REGISTRY, DEFENSE_REGISTRY
from fight_moves.release_registry import RELEASE_MOVE_DEFINITIONS, RELEASE_MOVE_REGISTRY
from models import Fighter
from persistence import FIGHTER_SAVE_FIELDS, load_model_row, serialize_fighter_model
from seeding import SeedMixin
from universe_validation import validate_universe_section_issues
from world import WorldMixin


ADDITIONS = sorted(set(RELEASE_MOVE_REGISTRY) - set(MOVE_REGISTRY))


def fighter(**updates):
    values = dict(name="Release Save Probe", fighter_id="FTR-release-save-probe",
                  weight="Lightweight", age=28, record_w=5, record_l=2,
                  striking=90, wrestling=90, grappling=90, cardio=90, chin=90,
                  popularity=45, momentum=0, morale=70, purse=12500,
                  detailed_skills={key: 90 for group in DETAILED_SKILL_GROUPS.values()
                                   for key in group})
    values.update(updates)
    return Fighter(**values)


class LegacyHost(SeedMixin, WorldMixin, FightEngineMixin):
    month = 3


class ReleaseHost(SeedMixin, WorldMixin, ReleaseFightEngineMixin):
    month = 3


class ReleasePersistenceTests(unittest.TestCase):
    def test_actual_fighter_json_save_roundtrip_preserves_all_94_additions(self):
        self.assertEqual(len(ADDITIONS), 94)
        defense = "defense:" + next(iter(DEFENSE_REGISTRY))
        mastery = dict.fromkeys(ADDITIONS, 77)
        mastery[defense] = 66
        for offset in range(0, len(ADDITIONS), 3):
            signatures = ADDITIONS[offset:offset + 3]
            original = fighter(signature_moves=signatures, move_mastery=dict(mastery))
            encoded = json.dumps(serialize_fighter_model(original))
            loaded = load_model_row(json.loads(encoded), Fighter, FIGHTER_SAVE_FIELDS,
                                    "release move JSON roundtrip")
            self.assertEqual(loaded.signature_moves, signatures)
            self.assertEqual(loaded.move_mastery, mastery)
            self.assertEqual(original.signature_moves, signatures)
        row = json.loads(encoded)
        row["signature_moves"] = ["unknown_future_move", ADDITIONS[0], ADDITIONS[0]]
        row["move_mastery"]["unknown_future_move"] = 80
        loaded = load_model_row(row, Fighter, FIGHTER_SAVE_FIELDS, "unknown move probe")
        self.assertEqual(loaded.signature_moves, [ADDITIONS[0]])
        self.assertNotIn("unknown_future_move", loaded.move_mastery)

    def test_universe_validator_accepts_release_ids_without_mutating_pack(self):
        record = dict(name="Release Universe Probe", fighter_id="FTR-release-universe",
                      placement="Free Agent", owner="Free Agent", weight="Lightweight",
                      gender="Male", rating=90, age=28, region=next(iter(REGIONS)),
                      nationality="British", style=next(iter(STYLES)))
        for offset in range(0, len(ADDITIONS), 3):
            pack = {"schema": 5, "all_fighters": [dict(
                record, signature_moves=ADDITIONS[offset:offset + 3])]}
            before = deepcopy(pack)
            self.assertEqual(validate_universe_section_issues("fighters", pack), [])
            self.assertEqual(pack, before)
        pack["all_fighters"][0]["signature_moves"] = ["unknown_future_move"]
        issues = validate_universe_section_issues("fighters", pack)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, "signature_moves")
        self.assertIn("unknown_future_move", issues[0].reason)

    def test_actual_application_class_uses_release_profile_without_tk_startup(self):
        from main import FightEmpireApp
        self.assertTrue(issubclass(FightEmpireApp, ReleaseFightEngineMixin))
        self.assertIs(FightEmpireApp._fight_move_registry, RELEASE_MOVE_REGISTRY)
        self.assertIs(FightEmpireApp._fight_move_definitions, RELEASE_MOVE_DEFINITIONS)
        self.assertEqual(len(FightEmpireApp._fight_move_registry), 440)
        self.assertEqual(len(MOVE_REGISTRY), 346)
        self.assertIs(LegacyHost()._fight_move_registry, MOVE_REGISTRY)

    def test_signature_seeding_preserves_release_authored_ids_and_legacy_isolation(self):
        release, legacy = ReleaseHost(), LegacyHost()
        authored = fighter(signature_moves=ADDITIONS[:3])
        self.assertEqual(release.assign_fighter_signature_moves(authored), ADDITIONS[:3])
        historical = fighter(signature_moves=ADDITIONS[:3])
        seeded = legacy.assign_fighter_signature_moves(historical)
        self.assertTrue(seeded)
        self.assertTrue(set(seeded) <= set(MOVE_REGISTRY))
        # Exercise actual ranking, not only preservation of authored signatures.
        selected_additions = set()
        for index in range(40):
            generated = fighter(fighter_id=f"FTR-release-ranking-{index}")
            selected_additions.update(release.assign_fighter_signature_moves(generated))
        self.assertTrue(selected_additions.intersection(ADDITIONS))
        self.assertEqual(len(MOVE_DEFINITIONS), 346)

    def test_world_mastery_development_uses_host_profile(self):
        initial = dict.fromkeys(MOVE_REGISTRY, 100)
        released = fighter(signature_moves=ADDITIONS[:3], move_mastery=dict(initial))
        result = ReleaseHost().develop_fighter_move_mastery(released, weeks=3)
        self.assertTrue(set(ADDITIONS[:3]) <= result.keys())
        self.assertTrue(all(result[key] >= 60 for key in ADDITIONS[:3]))
        self.assertTrue((set(result) - set(initial) - set(ADDITIONS[:3])).intersection(ADDITIONS))
        self.assertEqual(released.signature_moves, ADDITIONS[:3])
        self.assertEqual(released.move_mastery_last_month, 3)
        historical = fighter(signature_moves=ADDITIONS[:3], move_mastery=dict(initial))
        old_result = LegacyHost().develop_fighter_move_mastery(historical, weeks=3)
        self.assertFalse(set(old_result).intersection(ADDITIONS))
        self.assertTrue(set(historical.signature_moves) <= set(MOVE_REGISTRY))


if __name__ == "__main__":
    unittest.main()
