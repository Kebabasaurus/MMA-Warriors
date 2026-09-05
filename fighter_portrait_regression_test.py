"""Headless regression coverage for the portrait identity contract."""

import copy
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import unittest
from types import SimpleNamespace

from fighter_portraits.identity import derived_portrait_identity, identity_keys_are_stable, portrait_identity, trait_hash
from fighter_portraits.regions import REGION_APPEARANCE, appearance_region
from fighter_portraits.styles import FACIAL_HAIR, HAIR_STYLES, IDENTITY_TRAITS
from fighter_portraits.overrides import PORTRAIT_OVERRIDES


def fighter(fighter_id="FTR-portrait", **changes):
    values = {"fighter_id": fighter_id, "name": "Portrait Test", "birth_country": "Nigeria", "nationality": "Nigerian", "region": "USA", "birth_region": "", "record_w": 8, "record_l": 2, "record_d": 0, "age": 27, "gender": "Male", "portrait_identity": {}, "portrait_version": 0}
    values.update(changes)
    return SimpleNamespace(**values)


class PortraitIdentityRegressionTests(unittest.TestCase):
    def test_trait_hash_is_fighter_id_based_and_independent(self):
        self.assertEqual(trait_hash("FTR-x", "skin", 7), trait_hash("FTR-x", "skin", 7))
        self.assertNotEqual(derived_portrait_identity(fighter("FTR-one")), derived_portrait_identity(fighter("FTR-two")))
        original = derived_portrait_identity(fighter("FTR-stable"))
        self.assertEqual(original, derived_portrait_identity(fighter("FTR-stable", name="A renamed fighter")))

    def test_vector_contract_and_style_reachability(self):
        self.assertEqual(tuple(IDENTITY_TRAITS), identity_keys_are_stable())
        self.assertEqual(32, len(HAIR_STYLES))
        self.assertEqual(16, len(FACIAL_HAIR))
        hair = {derived_portrait_identity(fighter(f"FTR-hair-{i}"))["hair_style"] for i in range(800)}
        beard = {derived_portrait_identity(fighter(f"FTR-beard-{i}"))["facial_hair"] for i in range(800)}
        self.assertEqual(set(range(32)), hair)
        self.assertEqual(set(range(16)), beard)

    def test_region_order_and_wide_profiles(self):
        row = fighter(birth_country="Nigeria", nationality="Japanese", region="USA")
        self.assertEqual("Africa", appearance_region(row))
        row.birth_country = ""
        self.assertEqual("Japan", appearance_region(row))
        row.nationality = ""
        self.assertEqual("USA", appearance_region(row))
        for values, weights in REGION_APPEARANCE.values():
            self.assertGreaterEqual(len([weight for weight in weights if weight]), 3)
            self.assertEqual(len(values), len(weights))

    def test_identity_does_not_touch_game_values(self):
        row = fighter(striking=72, popularity=48, ability=63, simulation_value=99)
        before = copy.deepcopy(row.__dict__)
        portrait_identity(row)
        self.assertEqual(before, row.__dict__)

    def test_identity_cannot_read_ratings_or_simulation_values(self):
        class CosmeticOnlyFighter:
            fighter_id = "FTR-cosmetic-only"
            birth_country = "Nigeria"
            nationality = "Nigerian"
            region = "Africa"
            birth_region = ""
            name = "No Rating Access"
            portrait_identity = {}
            portrait_version = 0
            def __getattribute__(self, name):
                if name in {"striking", "wrestling", "grappling", "cardio", "chin", "popularity", "ability", "rating", "overall"}:
                    raise AssertionError(f"portrait identity read cosmetic-forbidden field {name}")
                return object.__getattribute__(self, name)
        portrait_identity(CosmeticOnlyFighter())

    def test_cross_process_determinism(self):
        script = "from types import SimpleNamespace as S; from fighter_portraits.identity import derived_portrait_identity; import json; print(json.dumps(derived_portrait_identity(S(fighter_id='FTR-x',birth_country='Nigeria',nationality='',region='',birth_region='')),sort_keys=True))"
        outputs = [subprocess.check_output([sys.executable, "-c", script], text=True).strip() for _ in range(2)]
        self.assertEqual(outputs[0], outputs[1])

    def test_persisted_vector_is_not_restyled(self):
        from fighter_portraits.identity import CURRENT_PORTRAIT_VERSION, ensure_portrait_identity
        row = fighter("FTR-save", portrait_identity={"skin": 6, "hair_style": 2}, portrait_version=0)
        preserved = ensure_portrait_identity(row)
        self.assertEqual(6, preserved["skin"])
        self.assertEqual(2, preserved["hair_style"])
        self.assertEqual(0, row.portrait_version)
        legacy = fighter("FTR-legacy", portrait_identity={}, portrait_version=0)
        expected = derived_portrait_identity(legacy)
        self.assertEqual(expected, ensure_portrait_identity(legacy))
        self.assertEqual(CURRENT_PORTRAIT_VERSION, legacy.portrait_version)

    def test_rasterisation_is_deterministic_and_stateful(self):
        from fighter_portraits.render import rasterize_portrait
        active = fighter("FTR-art", age=25, record_w=1, record_l=0)
        veteran = fighter("FTR-art", age=48, record_w=24, record_l=18)
        self.assertEqual(rasterize_portrait(active, 90).pixels, rasterize_portrait(active, 90).pixels)
        self.assertNotEqual(rasterize_portrait(active, 90).pixels, rasterize_portrait(veteran, 90).pixels)

    def test_career_state_saturates_and_injury_is_binary(self):
        from fighter_portraits.state import portrait_state
        veteran = fighter(age=80, record_w=120, record_l=80, injured=1)
        state = portrait_state(veteran)
        self.assertEqual(1.0, state["grey"])
        self.assertEqual(1.0, state["recede"])
        self.assertEqual(1.0, state["cauli"])
        self.assertEqual(1.0, state["scar"])
        self.assertEqual(1.0, state["nose_damage"])
        self.assertEqual(1.0, state["swell"])

    def test_authored_overrides_resolve_to_shipped_fighters(self):
        source = Path(__file__).with_name("Databases") / "Default Universe.universe.json"
        names = {row["name"] for row in json.loads(source.read_text(encoding="utf-8"))["sections"]["fighters"]["all_fighters"]}
        self.assertGreaterEqual(len(PORTRAIT_OVERRIDES), 50)
        self.assertEqual(set(), set(PORTRAIT_OVERRIDES) - names)

    def test_shipped_identity_manifest_is_stable(self):
        source = Path(__file__).with_name("Databases") / "Default Universe.universe.json"
        rows = json.loads(source.read_text(encoding="utf-8"))["sections"]["fighters"]["all_fighters"]
        manifest = [(row["fighter_id"], portrait_identity(SimpleNamespace(**row))) for row in rows]
        digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        self.assertEqual("028c9da5bba1c41519e2fb2ac85cffa665f162510d6bafa76d805445d48e3491", digest)


if __name__ == "__main__":
    unittest.main()
