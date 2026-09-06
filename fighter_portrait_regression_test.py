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
        self.assertEqual(48, len(HAIR_STYLES))
        self.assertEqual(16, len(FACIAL_HAIR))
        hair = {derived_portrait_identity(fighter(f"FTR-hair-{i}"))["hair_style"] for i in range(5000)}
        beard = {derived_portrait_identity(fighter(f"FTR-beard-{i}"))["facial_hair"] for i in range(5000)}
        self.assertEqual(set(range(len(HAIR_STYLES))), hair)
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
        self.assertTrue(all(len(weights) == len(HAIR_STYLES) for weights in GENDER_HAIR_STYLE_WEIGHTS.values()))
        self.assertTrue(all(weight > 0 for weights in GENDER_HAIR_STYLE_WEIGHTS.values() for weight in weights))
        male = [derived_portrait_identity(fighter(f"FTR-gender-{index}", gender="Male"))["hair_style"] for index in range(5000)]
        female = [derived_portrait_identity(fighter(f"FTR-gender-{index}", gender="Female"))["hair_style"] for index in range(5000)]
        self.assertEqual(set(range(len(HAIR_STYLES))), set(male))
        self.assertEqual(set(range(len(HAIR_STYLES))), set(female))
        self.assertGreater(sum(value in (21, 24, 33, 35, 37, 43, 44) for value in female),
                           sum(value in (21, 24, 33, 35, 37, 43, 44) for value in male))

    def test_identity_does_not_touch_game_values(self):
        import random
        from fighter_portraits.render import rasterize_portrait
        row = fighter(striking=72, popularity=48, ability=63, simulation_value=99)
        before = copy.deepcopy(row.__dict__)
        rng = random.getstate()
        portrait_identity(row)
        rasterize_portrait(row, 72)
        self.assertEqual(before, row.__dict__)
        self.assertEqual(rng, random.getstate())

    def test_runtime_without_optional_image_dependencies(self):
        script = '''
import sys
class BlockOptional:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('numpy', 'PIL'):
            raise AssertionError('Optional image dependency: ' + fullname)
sys.meta_path.insert(0, BlockOptional())
from types import SimpleNamespace
from fighter_portraits.render import rasterize_portrait
row = SimpleNamespace(fighter_id='stdlib-only', gender='Female', birth_country='Nigeria')
assert len(rasterize_portrait(row,72).pixels) == 72*72
'''
        result = subprocess.run([sys.executable, "-S", "-c", script], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_appearance_changes_leave_complete_bouts_and_rng_unchanged(self):
        self._check_appearance_bout_parity(native=False)

    def test_native_appearance_changes_leave_complete_bouts_and_rng_unchanged(self):
        self._check_appearance_bout_parity(native=True)

    def _check_appearance_bout_parity(self, native):
        from fight_engine_audit import FightAuditHarness, run_audited_fight, synthetic_fighter

        class RecordedHarness(FightAuditHarness):
            def _simulate_fight_with_caches(self, *args):
                result = super()._simulate_fight_with_caches(*args)
                self.terminal_rng = tuple(getattr(self, f"_fight_{name}_rng").getstate()
                                          for name in ("mechanics", "officiating", "judging", "presentation"))
                return result

        harness = RecordedHarness
        if native:
            # This portrait-only commit also works on pre-release checkouts.
            # Never hide a broken dependency inside an existing release module.
            try:
                from fight_release import ReleaseFightEngineMixin
            except ModuleNotFoundError as exc:
                if exc.name != "fight_release":
                    raise
                self.skipTest("Native release engine is absent from this checkout")
            class NativeHarness(ReleaseFightEngineMixin, RecordedHarness):
                pass
            harness = NativeHarness
        for seed in (9310000, 9320000):
            a = synthetic_fighter("Cosmetic A", 70, "Boxer", "Balanced", 0)
            b = synthetic_fighter("Cosmetic B", 70, "Wrestler", "Balanced", 1)
            control, restyled = harness(), harness()
            before = run_audited_fight(control, a, b, seed, {"rounds": 3})
            for row in (a, b):
                row.portrait_identity = derived_portrait_identity(row)
                row.portrait_identity.update(skin=11, hair_style=47, facial_hair=14,
                                             nose=9, jaw=9, neck_width=9, iris_colour=9)
                row.portrait_version = 2
            after = run_audited_fight(restyled, a, b, seed, {"rounds": 3})
            self.assertEqual(before, after)
            self.assertEqual(control.terminal_rng, restyled.terminal_rng)

    def test_country_aliases_and_unknown_origin_fallback(self):
        from fighter_portraits.regions import skin_distribution
        self.assertEqual("USA", appearance_region(fighter(birth_country="United States of America")))
        self.assertEqual("USA", appearance_region(fighter(birth_country="USA")))
        self.assertEqual("UK", appearance_region(fighter(birth_country="United Kingdom")))
        self.assertEqual("Japan", appearance_region(fighter(birth_country="Unknown", nationality="Japan")))
        self.assertEqual(skin_distribution(fighter(birth_country="China")),
                         skin_distribution(fighter(birth_country="People's Republic of China")))
        self.assertNotEqual(skin_distribution(fighter(birth_country="Nigeria")),
                            skin_distribution(fighter(birth_country="Morocco")))
        for country, nationality in (("India", "Indian"), ("South Africa", "South African"),
                                     ("Japan", "Japanese"), ("Poland", "Polish")):
            self.assertEqual(skin_distribution(fighter(birth_country=country)),
                             skin_distribution(fighter(birth_country="Unknown", nationality=nationality)))

    def test_country_sampling_matches_wide_tone_weights(self):
        from collections import Counter
        from fighter_portraits.regions import skin_distribution
        luminance = {}
        for country in ("Nigeria", "UK", "Japan", "Brazil", "India"):
            values, weights = skin_distribution(fighter(birth_country=country))
            counts = Counter(derived_portrait_identity(fighter(f"FTR-distribution-{i}", birth_country=country))["skin"] for i in range(4000))
            self.assertGreaterEqual(len(counts), 8)
            for value, weight in zip(values, weights):
                self.assertAlmostEqual(counts[value]/4000, weight/sum(weights), delta=.025)
            luminance[country] = sum(int(SKIN[value][0][1:3],16)*count for value,count in counts.items())/4000
        self.assertGreater(luminance["UK"] - luminance["Nigeria"], 65)
        self.assertGreater(luminance["Japan"], luminance["India"])

    def test_women_render_differently_even_with_identical_saved_traits(self):
        from fighter_portraits.render import rasterize_portrait, portrait_cache_key
        row = fighter(portrait_identity=derived_portrait_identity(fighter()))
        male = rasterize_portrait(row, 72).pixels
        male_key = portrait_cache_key(row, 72)
        for label in ("Female", "female", " F ", "Women"):
            row.gender = label
            before = copy.deepcopy(row.__dict__)
            female = rasterize_portrait(row, 72).pixels
            self.assertNotEqual(male, female)
            self.assertNotEqual(male_key, portrait_cache_key(row, 72))
            row.portrait_identity["facial_hair"] = 0
            self.assertEqual(female, rasterize_portrait(row, 72).pixels)
            row.__dict__.update(before)
        self.assertEqual(0, derived_portrait_identity(fighter(gender="female"))["facial_hair"])

    def test_added_features_are_visible_and_do_not_reshuffle_saved_traits(self):
        from fighter_portraits.render import rasterize_portrait
        row = fighter(portrait_identity=derived_portrait_identity(fighter()))
        saved = copy.deepcopy(row.portrait_identity)
        for key in ("neck_width", "shoulder_width", "iris_colour", "nose_length", "lip_fullness", "hair_volume", "hair_part", "complexion", "feature_offset"):
            row.portrait_identity = dict(saved, hair_style=36, facial_hair=0)
            row.portrait_identity[key] = 0
            first = rasterize_portrait(row, 104).pixels
            row.portrait_identity[key] = 2 if key == "complexion" else 9
            self.assertNotEqual(first, rasterize_portrait(row, 104).pixels, key)
        legacy = {key:value for key,value in saved.items() if key not in {"neck_width", "shoulder_width", "iris_colour", "nose_length", "lip_fullness", "hair_volume", "hair_part", "complexion", "feature_offset"}}
        row.portrait_identity = legacy
        derived = portrait_identity(row)
        self.assertEqual(legacy, {key:derived[key] for key in legacy})

    def test_beard_styles_have_different_masks_and_moustache_leaves_jaw_bare(self):
        from fighter_portraits.render import rasterize_portrait
        row = fighter(portrait_identity={"hair_style":0, "facial_hair":0})
        clean = rasterize_portrait(row,90).pixels
        portraits = []
        for style in range(len(FACIAL_HAIR)):
            row.portrait_identity["facial_hair"] = style
            portraits.append(tuple(rasterize_portrait(row,90).pixels))
        self.assertEqual(len(portraits),len(set(portraits)))
        self.assertEqual(clean[62*90:67*90],list(portraits[3][62*90:67*90]))

    def test_all_complexions_and_hair_styles_are_visually_distinct(self):
        from fighter_portraits.render import rasterize_portrait
        for trait, count in (("complexion", 10), ("hair_style", len(HAIR_STYLES))):
            images = set()
            for value in range(count):
                row = fighter(portrait_identity={"hair_style":0, "facial_hair":0,
                                                  "skin":1, "hair_colour":1, trait:value})
                images.add(tuple(rasterize_portrait(row,104).pixels))
            self.assertEqual(count, len(images), trait)

    def test_generated_vectors_and_neutral_colour_face_crops_are_distinct(self):
        from fighter_portraits.render import rasterize_portrait
        identities = set()
        portraits = set()
        for index in range(5000):
            row = fighter(f"FTR-collision-{index}")
            vector = derived_portrait_identity(row)
            identities.add(tuple(sorted(vector.items())))
            if index < 128:
                row.portrait_identity = dict(vector, bg=0, skin=2, hair_colour=1)
                pixels = rasterize_portrait(row,72).pixels
                portraits.add(tuple(pixels[y*72+x] for y in range(5,54) for x in range(16,56)))
        self.assertEqual(5000,len(identities))
        self.assertEqual(128,len(portraits))

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
        for name, vector in PORTRAIT_ICON_OVERRIDES.items():
            for key, value in vector.items():
                if key not in PORTRAIT_TOP_RATED_OVERRIDES.get(name, {}):
                    self.assertEqual(value, PORTRAIT_OVERRIDES[name][key], (name, key))

    def test_paddy_pimblett_keeps_his_blond_bowl_cut_direction(self):
        vector = PORTRAIT_OVERRIDES["Paddy Pimblett"]
        self.assertEqual(15, vector["hair_style"])
        self.assertEqual(5, vector["hair_colour"])

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
        self.assertEqual("95a2d934b8726ea811b2e9db4fab43ca684495f1fd9990c11ba6bc1320a0d664", digest)

    def test_save_round_trip_preserves_identity(self):
        from models import Fighter
        from persistence import FIGHTER_SAVE_FIELDS, load_model_row, serialize_fighter_model
        row = Fighter(name="Save Portrait", fighter_id="FTR-save-roundtrip", weight="Lightweight", age=27,
                      record_w=8, record_l=2, striking=70, wrestling=70, grappling=70, cardio=70,
                      chin=70, popularity=40, momentum=0, morale=60, purse=1_000,
                      portrait_identity={"skin": 4, "hair_style": 23, "dye": "rainbow",
                                         "neck_width": 8, "complexion": 9, "iris_colour": 5}, portrait_version=1)
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
            "8a1b42d0f83620299d2cae6dcd4bfe979a33b6fb149b10b9e70224b217fc527e",
            "97c51716c98fca440464d7d0524719a1ecb13c45a263737f74700164e61e021a",
            "5dd3185789970206926adba954c016c02659bbc042cb36f17f1f3fcee84a7699",
        ), tuple(signatures))


if __name__ == "__main__":
    unittest.main()
