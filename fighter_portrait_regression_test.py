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
from fighter_portraits.regions import GENDER_HAIR_STYLE_WEIGHTS, REGION_APPEARANCE, appearance_region
from fighter_portraits.styles import (
    BACKGROUND, BROW_STYLES, CHEEK_SHAPES, CHIN_SHAPES, EAR_SHAPES, EYE_SHAPES,
    EYE_SIZES, EYE_SPACINGS, FACIAL_HAIR, FACE_LENGTHS, HAIR, HAIR_STYLES,
    IDENTITY_TRAITS, JAW_SHAPES, MOUTH_SHAPES, NOSE_SHAPES, SKIN,
)
from fighter_portraits.overrides import (
    PORTRAIT_ICON_OVERRIDES, PORTRAIT_OVERRIDES, PORTRAIT_PARTIAL_OVERRIDES,
    PORTRAIT_TOP_RATED_OVERRIDES,
)


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

    def test_every_appearance_category_has_ten_or_more_options(self):
        categories = (SKIN, HAIR, HAIR_STYLES, FACIAL_HAIR, BROW_STYLES, EYE_SHAPES,
                      EYE_SPACINGS, EYE_SIZES, NOSE_SHAPES, MOUTH_SHAPES, JAW_SHAPES,
                      CHIN_SHAPES, CHEEK_SHAPES, FACE_LENGTHS, EAR_SHAPES, BACKGROUND)
        self.assertTrue(all(len(category) >= 10 for category in categories))

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

    def test_gender_aware_hair_distribution_is_broad_and_deterministic(self):
        self.assertEqual(set(range(32)), set(range(len(GENDER_HAIR_STYLE_WEIGHTS["Male"]))))
        self.assertTrue(all(weight > 0 for weights in GENDER_HAIR_STYLE_WEIGHTS.values() for weight in weights))
        male = {derived_portrait_identity(fighter(f"FTR-gender-{index}", gender="Male"))["hair_style"] for index in range(1600)}
        female = {derived_portrait_identity(fighter(f"FTR-gender-{index}", gender="Female"))["hair_style"] for index in range(1600)}
        self.assertEqual(set(range(32)), male)
        self.assertEqual(set(range(32)), female)
        self.assertNotEqual(
            derived_portrait_identity(fighter("FTR-gender-difference", gender="Male"))["hair_style"],
            derived_portrait_identity(fighter("FTR-gender-difference", gender="Female"))["hair_style"],
        )

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

    def test_recent_recorded_damage_controls_transient_portrait_layers(self):
        from fighter_portraits.state import portrait_state
        row = fighter(last_fight_stats={"head_damage": 28, "cut_details": [{"severity": 5, "location": "left brow"}]})
        state = portrait_state(row)
        self.assertEqual(.7, state["recent_head_damage"])
        self.assertEqual(5 / 6, state["recent_cut"])
        self.assertEqual("left brow", state["recent_cut_location"])
        self.assertGreater(state["swell"], 0)

    def test_authored_overrides_resolve_to_shipped_fighters(self):
        source = Path(__file__).with_name("Databases") / "Default Universe.universe.json"
        names = {row["name"] for row in json.loads(source.read_text(encoding="utf-8"))["sections"]["fighters"]["all_fighters"]}
        self.assertGreaterEqual(len(PORTRAIT_ICON_OVERRIDES), 50)
        self.assertGreaterEqual(len(PORTRAIT_PARTIAL_OVERRIDES), 200)
        self.assertTrue(all(set(row) <= {"skin", "hair_style", "facial_hair"} for row in PORTRAIT_PARTIAL_OVERRIDES.values()))
        self.assertEqual(set(), set(PORTRAIT_OVERRIDES) - names)
        self.assertEqual(0, PORTRAIT_OVERRIDES["Jon Jones"]["hair_style"])

    def test_top_fifty_rated_fighters_have_explicit_visual_direction(self):
        source = Path(__file__).with_name("Databases") / "Default Universe.universe.json"
        rows = json.loads(source.read_text(encoding="utf-8"))["sections"]["fighters"]["all_fighters"]
        top_fifty = sorted(rows, key=lambda row: (-int(row.get("rating", 0) or 0), row["name"]))[:50]
        self.assertEqual({row["name"] for row in top_fifty}, set(PORTRAIT_TOP_RATED_OVERRIDES))
        self.assertTrue(all({"skin", "hair_style", "facial_hair"} <= set(vector)
                            for vector in PORTRAIT_TOP_RATED_OVERRIDES.values()))

    def test_shipped_identity_manifest_is_stable(self):
        source = Path(__file__).with_name("Databases") / "Default Universe.universe.json"
        rows = json.loads(source.read_text(encoding="utf-8"))["sections"]["fighters"]["all_fighters"]
        manifest = [(row["fighter_id"], portrait_identity(SimpleNamespace(**row))) for row in rows]
        digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        self.assertEqual("904882a0ae301a9c088682d7d91c6c0d717326ca7d4bbf4fe60460892a881245", digest)

    def test_save_round_trip_preserves_identity(self):
        from models import Fighter
        from persistence import FIGHTER_SAVE_FIELDS, load_model_row, serialize_fighter_model
        row = Fighter(name="Save Portrait", fighter_id="FTR-save-roundtrip", weight="Lightweight", age=27,
                      record_w=8, record_l=2, striking=70, wrestling=70, grappling=70, cardio=70,
                      chin=70, popularity=40, momentum=0, morale=60, purse=1_000,
                      portrait_identity={"skin": 4, "hair_style": 23, "dye": "rainbow"}, portrait_version=1)
        restored = load_model_row(serialize_fighter_model(row), Fighter, FIGHTER_SAVE_FIELDS, "portrait regression")
        self.assertEqual(row.portrait_identity, restored.portrait_identity)
        self.assertEqual(row.portrait_version, restored.portrait_version)

    def test_every_shipped_style_rasterises(self):
        from fighter_portraits.render import rasterize_portrait
        for hair_style in range(len(HAIR_STYLES)):
            row = fighter(f"FTR-style-{hair_style}", portrait_identity={"hair_style": hair_style})
            self.assertEqual(90 * 90, len(rasterize_portrait(row, 90).pixels))
        for facial_hair in range(len(FACIAL_HAIR)):
            row = fighter(f"FTR-beard-{facial_hair}", portrait_identity={"facial_hair": facial_hair})
            self.assertEqual(90 * 90, len(rasterize_portrait(row, 90).pixels))

    def test_portrait_cache_is_lru_bounded(self):
        from fighter_portraits.render import PORTRAIT_CACHE_LIMIT, _cache_get, _cache_store, clear_portrait_cache, portrait_cache_info
        clear_portrait_cache()
        for index in range(PORTRAIT_CACHE_LIMIT + 3):
            _cache_store(("portrait", index), object())
        self.assertEqual(PORTRAIT_CACHE_LIMIT, portrait_cache_info()["size"])
        self.assertIsNone(_cache_get(("portrait", 0)))
        retained = _cache_get(("portrait", 3))
        self.assertIsNotNone(retained)
        _cache_store(("portrait", "new"), object())
        self.assertIs(retained, _cache_get(("portrait", 3)))
        clear_portrait_cache()

    def test_shared_status_seal_keeps_retired_contract(self):
        from fighter_portraits.render import _draw_status_markers
        calls = []
        class Canvas:
            def cget(self, field): return "104" if field == "width" else "104"
            def create_oval(self, *args, **kwargs): calls.append(("oval", kwargs))
            def create_text(self, *args, **kwargs): calls.append(("text", kwargs))
            def create_rectangle(self, *args, **kwargs): calls.append(("rectangle", kwargs))
        _draw_status_markers(Canvas(), fighter(retired=True), 104)
        self.assertIn(("oval", {"fill": "#315a70", "outline": "#bfe6f2", "width": 1}), calls)
        self.assertIn(("text", {"text": "RTD", "fill": "#ffffff", "font": ("Impact", 7)}), calls)

    def test_fixed_portrait_render_fingerprints_are_stable(self):
        from fighter_portraits.render import rasterize_portrait
        fixtures = (
            fighter("FTR-render-one", portrait_identity={"hair_style": 0, "facial_hair": 0, "skin": 2}),
            fighter("FTR-render-two", age=41, record_w=28, record_l=12,
                    portrait_identity={"hair_style": 23, "facial_hair": 10, "skin": 6, "dye": "rainbow"}),
            fighter("FTR-render-three", gender="Female", portrait_identity={"hair_style": 21, "facial_hair": 15, "skin": 1}),
        )
        signatures = []
        for row in fixtures:
            pixels = rasterize_portrait(row, 90).pixels
            payload = bytes(max(0, min(255, round(channel))) for pixel in pixels for channel in pixel)
            signatures.append(hashlib.sha256(payload).hexdigest())
        self.assertEqual((
            "00c4825f71bb4bffc1b162fd790568b55855ea69476737b38e4de4024a52e76b",
            "c91b8939c456e64921d6c0f13be9aa8210a36bd3a019a211a65a18c88fe2d5f2",
            "911c018e3cb3261d0889a8d9fc385be1413ac402f8714fd899e6991c6a48dc7c",
        ), tuple(signatures))


if __name__ == "__main__":
    unittest.main()
