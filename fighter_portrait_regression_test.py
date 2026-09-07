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
    IDENTITY_TRAITS, JAW_SHAPES, MOUTH_SHAPES, NOSE_SHAPES, SKIN, FEMALE_HAIR_STYLES,
    MALE_HAIR_STYLES, FEATURE_COUNTS, IRIS_COLOURS, DYE,
)
from fighter_portraits.overrides import (
    PORTRAIT_ICON_OVERRIDES, PORTRAIT_OVERRIDES, PORTRAIT_PARTIAL_OVERRIDES,
    PORTRAIT_TOP_RATED_OVERRIDES,
)
from fighter_portraits.ranked_51_100 import PORTRAIT_RANK_51_100_OVERRIDES


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
        self.assertEqual(151, len(HAIR_STYLES))
        self.assertEqual(66, len(FACIAL_HAIR))
        hair = {derived_portrait_identity(fighter(f"FTR-hair-{i}"))["hair_style"] for i in range(5000)}
        beard = {derived_portrait_identity(fighter(f"FTR-beard-{i}"))["facial_hair"] for i in range(5000)}
        self.assertEqual(set(MALE_HAIR_STYLES), hair)
        self.assertEqual(set(range(66)), beard)

    def test_every_appearance_category_has_ten_or_more_options(self):
        categories = (SKIN, HAIR, HAIR_STYLES, FACIAL_HAIR, BROW_STYLES, EYE_SHAPES,
                      EYE_SPACINGS, EYE_SIZES, NOSE_SHAPES, MOUTH_SHAPES, JAW_SHAPES,
                      CHIN_SHAPES, CHEEK_SHAPES, FACE_LENGTHS, EAR_SHAPES, BACKGROUND)
        self.assertTrue(all(len(category) >= 10 for category in categories))

    def test_fifty_additions_per_category_and_gender_pool(self):
        self.assertEqual(98, len(MALE_HAIR_STYLES))
        self.assertEqual(77, len(FEMALE_HAIR_STYLES))
        self.assertEqual(tuple(range(48, 98)), MALE_HAIR_STYLES[48:])
        self.assertEqual(tuple(range(98, 148)), FEMALE_HAIR_STYLES[27:])
        for category in (SKIN, HAIR, BACKGROUND):
            self.assertEqual(62, len(category))
            self.assertEqual(len(category), len(set(category)))
        self.assertEqual(61, len(DYE))
        self.assertEqual(61, len(set(DYE.values())))
        self.assertEqual(60, len(set(IRIS_COLOURS)))
        for category in (BROW_STYLES, EYE_SHAPES, EYE_SPACINGS, EYE_SIZES,
                         NOSE_SHAPES, MOUTH_SHAPES, JAW_SHAPES, CHIN_SHAPES,
                         CHEEK_SHAPES, FACE_LENGTHS, EAR_SHAPES):
            self.assertEqual(60, len(set(category)))
        self.assertEqual(set(IDENTITY_TRAITS), set(FEATURE_COUNTS))

    def test_new_shades_preserve_country_family_probabilities(self):
        from fighter_portraits.expansion import PALETTE_PARENTS, expand_distribution
        from fighter_portraits.regions import TONE_PROFILES
        parents = tuple(range(12)) + PALETTE_PARENTS
        for old in TONE_PROFILES.values():
            choices, weights = expand_distribution(old)
            for family in range(12):
                mass = sum(w for i, w in zip(choices, weights) if parents[i] == family)
                self.assertAlmostEqual(old[family]/sum(old), mass/sum(weights))

    def test_all_v2_catalogue_ids_are_append_only(self):
        from fighter_portraits import styles
        lengths = {"HAIR_STYLES":48, "FACIAL_HAIR":16, "FEMALE_HAIR_STYLES":27,
                   "SKIN":12, "HAIR":12, "BACKGROUND":12, "IRIS_COLOURS":10,
                   "BROW_STYLES":10, "EYE_SHAPES":10, "EYE_SPACINGS":10, "EYE_SIZES":10,
                   "NOSE_SHAPES":10, "MOUTH_SHAPES":10, "JAW_SHAPES":10, "CHIN_SHAPES":10,
                   "CHEEK_SHAPES":10, "FACE_LENGTHS":10, "EAR_SHAPES":10, "IDENTITY_TRAITS":27}
        payload = {key:getattr(styles,key)[:count] for key,count in lengths.items()}
        payload["DYE"] = dict(tuple(styles.DYE.items())[:10])
        digest = hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        self.assertEqual("6af28d788867c394b9ef6dea6f2ba1dee38d8786091912b8848a1b8f1f81bef6",digest)

    def test_expanded_anatomical_controls_stay_bounded(self):
        from fighter_portraits.expansion import control_value, feature_value
        self.assertEqual(list(range(10)), [control_value(i) for i in range(10)])
        values = [control_value(i) for i in range(10, 60)]
        self.assertEqual(50, len(set(values)))
        self.assertTrue(all(0 < value < 9 for value in values))
        self.assertTrue(all(0 < feature_value(tuple(range(100)), i) < 99 for i in range(100, 150)))

    def test_v3_catalogue_prefix_and_authored_only_extensions(self):
        payload = {"HAIR_STYLES": HAIR_STYLES[:148], "FACIAL_HAIR": FACIAL_HAIR,
                   "DYE": dict(tuple(DYE.items())[:60])}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual("bfdf864f4094a2b523f7ba299d311c002f72267373e2cf5234f7b1148eb2bd16", digest)
        self.assertEqual(("authored_wavy_side_part", "authored_compact_mullet", "authored_shoulder_sweep"),
                         tuple(row[0] for row in HAIR_STYLES[148:]))
        for weights in GENDER_HAIR_STYLE_WEIGHTS.values():
            self.assertEqual((0, 0, 0), weights[148:])
        self.assertEqual("burgundy", tuple(DYE)[-1])

    def test_all_original_v3_hair_pixels_are_unchanged(self):
        from fighter_portraits.render import rasterize_portrait
        row = fighter("FTR-historical-hair", name="Historical Hair", birth_country="UK")
        base = derived_portrait_identity(row)
        digest = hashlib.sha256()
        for style in range(148):
            row.portrait_identity = dict(base, hair_style=style, facial_hair=0, skin=1, hair_colour=2)
            digest.update(bytes(c for pixel in rasterize_portrait(row, 72).pixels for c in pixel))
        # Captured with c4e4045's render.py AND hair.py, not this new renderer.
        self.assertEqual("f6fb139f71d080db1d86ee1f5152b4708b26e1f3e5ed2251f866ebdb0b5a90e6", digest.hexdigest())

    def test_reviewed_ranked_contact_sheet_pixels_at_all_ui_sizes(self):
        import struct
        import zlib
        from fighter_portraits.render import rasterize_portrait
        root = Path(__file__).parent
        rows = json.loads((root / "Databases" / "Default Universe.universe.json").read_text(encoding="utf-8"))["sections"]["fighters"]["all_fighters"]
        cohort = sorted(rows, key=lambda row: (-int(row.get("rating", 0) or 0), row["name"]))[50:100]
        for size in (72, 98, 104, 180):
            png = (root / "analysis" / "portraits" / "top_51_100_2026_09" / f"portraits_{size}.png").read_bytes()
            self.assertEqual(b"\x89PNG\r\n\x1a\n", png[:8])
            self.assertEqual((size*10, size*5), struct.unpack(">II", png[16:24]))
            offset, compressed = 8, bytearray()
            while offset < len(png):
                length = struct.unpack(">I", png[offset:offset+4])[0]
                if png[offset+4:offset+8] == b"IDAT":
                    compressed.extend(png[offset+8:offset+8+length])
                offset += length + 12
            raw = zlib.decompress(compressed)
            stride = size*10*3 + 1
            self.assertEqual(stride*size*5, len(raw))
            self.assertTrue(all(raw[y*stride] == 0 for y in range(size*5)))
            for index, record in enumerate(cohort):
                row = SimpleNamespace(**record)
                before = copy.deepcopy(row.__dict__)
                pixels = rasterize_portrait(row, size).pixels
                ox, oy = (index % 10)*size, (index // 10)*size
                expected = b"".join(raw[(oy+y)*stride+1+ox*3:(oy+y)*stride+1+(ox+size)*3] for y in range(size))
                self.assertEqual(expected, bytes(c for pixel in pixels for c in pixel), (record["name"], size))
                self.assertEqual(before, row.__dict__)

    def test_labelled_review_and_offset_match_the_ranked_cohort(self):
        import base64
        from html.parser import HTMLParser
        from analysis.portraits.generate_portrait_contact_sheet import png_bytes
        from fighter_portraits.render import rasterize_portrait

        class ReviewParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.images = []

            def handle_starttag(self, tag, attrs):
                if tag == "img":
                    self.images.append(dict(attrs))

        root = Path(__file__).parent
        directory = root / "analysis" / "portraits" / "top_51_100_2026_09"
        manifest = json.loads((directory / "identities.json").read_text(encoding="utf-8"))
        parser = ReviewParser()
        parser.feed((directory / "review.html").read_text(encoding="utf-8"))
        self.assertEqual([row["name"] for row in manifest], [image["alt"] for image in parser.images])
        self.assertEqual(50, len(parser.images))
        self.assertEqual("Matthew Green", parser.images[0]["alt"])
        self.assertEqual("Arnold Allen", parser.images[-1]["alt"])
        rows = json.loads((root / "Databases" / "Default Universe.universe.json").read_text(encoding="utf-8"))["sections"]["fighters"]["all_fighters"]
        by_name = {row["name"]: row for row in rows}
        for item in parser.images:
            self.assertTrue(item["src"].startswith("data:image/png;base64,"))
            expected = png_bytes(180, 180, rasterize_portrait(SimpleNamespace(**by_name[item["alt"]]), 180).pixels)
            self.assertEqual(expected, base64.b64decode(item["src"].split(",", 1)[1]))

    def test_expanded_features_render_for_both_genders_at_all_ui_sizes(self):
        from fighter_portraits.render import rasterize_portrait
        for gender in ("Male", "Female"):
            for size in (72, 98, 104, 180):
                for step in range(50):
                    vector = {key: count-50+step for key, count in FEATURE_COUNTS.items() if key != "dye"}
                    vector["hair_style"] = (48 if gender == "Male" else 98) + step
                    vector["dye"] = tuple(DYE)[10+step]
                    row = fighter(gender=gender, portrait_identity=vector)
                    before = copy.deepcopy(row.__dict__)
                    self.assertEqual(size*size, len(rasterize_portrait(row, size).pixels))
                    self.assertEqual(before, row.__dict__)
                    if gender == "Female":
                        self.assertEqual(0, portrait_identity(row)["facial_hair"])

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
        self.assertEqual(set(MALE_HAIR_STYLES), {style for style, weight in
                         enumerate(GENDER_HAIR_STYLE_WEIGHTS["Male"]) if weight > 0})
        self.assertEqual(set(FEMALE_HAIR_STYLES), {style for style, weight in
                         enumerate(GENDER_HAIR_STYLE_WEIGHTS["Female"]) if weight > 0})
        male = [derived_portrait_identity(fighter(f"FTR-gender-{index}", gender="Male"))["hair_style"] for index in range(5000)]
        female = [derived_portrait_identity(fighter(f"FTR-gender-{index}", gender="Female"))["hair_style"] for index in range(5000)]
        self.assertEqual(set(MALE_HAIR_STYLES), set(male))
        self.assertEqual(set(FEMALE_HAIR_STYLES), set(female))
        self.assertGreater(sum(value in (21, 24, 33, 35, 37, 43, 44) for value in female),
                           sum(value in (21, 24, 33, 35, 37, 43, 44) for value in male))

    def test_womens_catalogue_and_no_beards_apply_after_saves_and_overrides(self):
        from unittest.mock import patch
        for style in range(len(HAIR_STYLES)):
            row = fighter(gender="Female", portrait_identity={"hair_style": style, "skin": 6,
                          "facial_hair": 15, "jaw": 8})
            saved = copy.deepcopy(row.__dict__)
            vector = portrait_identity(row)
            self.assertIn(vector["hair_style"], FEMALE_HAIR_STYLES)
            if style in FEMALE_HAIR_STYLES:
                self.assertEqual(style, vector["hair_style"])
            self.assertEqual((0, 6, 8), (vector["facial_hair"], vector["skin"], vector["jaw"]))
            self.assertEqual(saved, row.__dict__)
        # Specific real-fighter hair exceptions remain possible, never beards.
        row = fighter(gender="Female")
        for beard in range(len(FACIAL_HAIR)):
            with patch.dict(PORTRAIT_OVERRIDES, {row.name: {"hair_style": 0, "facial_hair": beard}}):
                vector = portrait_identity(row)
                self.assertEqual(0, vector["hair_style"])
                self.assertEqual(0, vector["facial_hair"])

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
                row.portrait_identity.update(skin=61, hair_style=97, facial_hair=65, beard_colour=14,
                                             nose=59, jaw=59, neck_width=59, iris_colour=59)
                row.portrait_version = 3
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
        for trait, count in (("complexion", 60), ("hair_style", len(HAIR_STYLES))):
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
                if (key not in PORTRAIT_TOP_RATED_OVERRIDES.get(name, {})
                        and key not in PORTRAIT_RANK_51_100_OVERRIDES.get(name, {})):
                    self.assertEqual(value, PORTRAIT_OVERRIDES[name][key], (name, key))

    def test_paddy_pimblett_keeps_his_blond_bowl_cut_direction(self):
        vector = PORTRAIT_OVERRIDES["Paddy Pimblett"]
        self.assertEqual(15, vector["hair_style"])
        self.assertEqual(5, vector["hair_colour"])

    def test_requested_named_appearances_override_old_saved_choices(self):
        from fighter_portraits.identity import ensure_portrait_identity
        requested = {
            "Markell Holmes": {"skin":5, "hair_colour":0, "hair_style":13, "facial_hair":8},
            "Brett Akey": {"hair_style":0},
            "Conor McGregor": {"skin":0, "hair_colour":1, "hair_style":4,
                               "facial_hair":11, "beard_colour":14, "iris_colour":4},
        }
        for name, expected in requested.items():
            row = fighter(name=name, portrait_identity={"skin":0,"hair_style":25,
                          "hair_colour":7,"facial_hair":0,"bg":9}, portrait_version=1)
            saved = copy.deepcopy(row.__dict__)
            effective = ensure_portrait_identity(row)
            self.assertEqual(expected, {key:effective[key] for key in expected})
            self.assertEqual(saved, row.__dict__)

    def test_authored_beard_colour_only_changes_beard_pixels(self):
        from fighter_portraits.render import portrait_cache_key, rasterize_portrait
        for style in (1, 8, 11, 22):
            row = fighter(portrait_identity={"hair_style":4,"hair_colour":1,
                          "facial_hair":style,"skin":1,"complexion":0})
            before = rasterize_portrait(row,104).pixels
            cached_key = portrait_cache_key(row,104)
            row.portrait_identity["beard_colour"] = 14
            self.assertNotEqual(cached_key,portrait_cache_key(row,104))
            after = rasterize_portrait(row,104).pixels
            self.assertNotEqual(before,after)
            self.assertEqual(before[:48*104],after[:48*104])
            row.gender = "Female"
            female = rasterize_portrait(row,104).pixels
            row.portrait_identity["beard_colour"] = 6
            self.assertEqual(female,rasterize_portrait(row,104).pixels)
        row.gender = "Male"
        row.portrait_identity["facial_hair"] = 0
        clean = rasterize_portrait(row,104).pixels
        row.portrait_identity.pop("beard_colour")
        self.assertEqual(clean,rasterize_portrait(row,104).pixels)
        # A matching authored colour must follow exactly the same greying as
        # the default scalp-linked beard, including at full career age.
        row.portrait_identity.update(hair_colour=14, facial_hair=11, dye="")
        for age in (27,52):
            row.age = age
            linked = rasterize_portrait(row,104).pixels
            row.portrait_identity["beard_colour"] = 14
            self.assertEqual(linked,rasterize_portrait(row,104).pixels)
            row.portrait_identity.pop("beard_colour")

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
        # The next 49 photo-reviewed records intentionally change this manifest.
        self.assertEqual("5bb93f7be0a4c7bbcb10eb29f4c2a8c61350204593d4bc2fb6ef0c37e6d2997a", digest)
        outside = [entry for row, entry in zip(rows, manifest)
                   if row["name"] not in PORTRAIT_RANK_51_100_OVERRIDES]
        outside_digest = hashlib.sha256(json.dumps(outside, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        # Captured using the pre-batch c4e4045 override table: no other identity changes.
        self.assertEqual("c8baea306e96831773be7d1f530c07a59bb6053382813670cdcd4a2240544a65", outside_digest)

    def test_next_fifty_ranked_coverage_and_nonmutating_saved_corrections(self):
        from fighter_portraits.identity import ensure_portrait_identity
        source = Path(__file__).with_name("Databases") / "Default Universe.universe.json"
        rows = json.loads(source.read_text(encoding="utf-8"))["sections"]["fighters"]["all_fighters"]
        cohort = sorted(rows, key=lambda row: (-int(row.get("rating", 0) or 0), row["name"]))[50:100]
        self.assertEqual({row["name"] for row in cohort} - {"Matthew Green"}, set(PORTRAIT_RANK_51_100_OVERRIDES))
        self.assertEqual(49, len(PORTRAIT_RANK_51_100_OVERRIDES))
        for name, authored in PORTRAIT_RANK_51_100_OVERRIDES.items():
            self.assertEqual(set(IDENTITY_TRAITS) - {"bg"} | {"beard_colour"}, set(authored))
            for key, value in authored.items():
                if key == "dye":
                    self.assertTrue(value == "" or value in DYE)
                else:
                    self.assertTrue(0 <= value < (len(HAIR) if key == "beard_colour" else FEATURE_COUNTS[key]), (name, key))
            row = fighter(name=name, portrait_version=2)
            row.portrait_identity = dict(derived_portrait_identity(row), hair_style=25, facial_hair=65, bg=9)
            before = copy.deepcopy(row.__dict__)
            effective = ensure_portrait_identity(row)
            self.assertEqual(authored, {key: effective[key] for key in authored})
            self.assertEqual(PORTRAIT_OVERRIDES[name].get("bg", 9), effective["bg"])
            self.assertEqual(before, row.__dict__)

    def test_cyborg_display_gender_never_changes_database_or_bypasses_beard_guard(self):
        from unittest.mock import patch
        from fighter_portraits.render import rasterize_portrait, portrait_cache_key
        from fighter_portraits.styles import portrait_gender
        row = fighter(name="Cristiane Justino", gender="Male", popularity=51, striking=82,
                      portrait_identity={"facial_hair":65, "hair_style":1})
        before = copy.deepcopy(row.__dict__)
        self.assertEqual("Female", portrait_gender(row))
        self.assertEqual(0, portrait_identity(row)["facial_hair"])
        for size in (72, 98, 104, 180):
            pixels, key = rasterize_portrait(row, size).pixels, portrait_cache_key(row, size)
            row.gender = "Female"
            self.assertEqual(pixels, rasterize_portrait(row, size).pixels)
            self.assertEqual(key, portrait_cache_key(row, size))
            row.gender = "Male"
            identity = dict(portrait_identity(row), facial_hair=65)
            with patch("fighter_portraits.render.portrait_identity", return_value=identity):
                self.assertEqual(pixels, rasterize_portrait(row, size).pixels)
        self.assertEqual(before, row.__dict__)

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
        # New highest IDs must survive the real serializer too, not just the
        # older, small integer vectors used by the historical save fixture.
        row.portrait_identity = {key:count-1 for key,count in FEATURE_COUNTS.items()}
        row.portrait_identity.update(hair_style=97, dye=tuple(DYE)[-1], beard_colour=14)
        row.portrait_version = 3
        restored = load_model_row(serialize_fighter_model(row), Fighter, FIGHTER_SAVE_FIELDS, "expanded portrait regression")
        self.assertEqual(row.portrait_identity, restored.portrait_identity)
        self.assertEqual(3, restored.portrait_version)

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
        # Freeze the complete v2 vectors, not partially generated fixtures:
        # catalogue growth can affect missing draws, never saved visual meaning.
        old_vectors = json.loads((Path(__file__).parent / "analysis/portraits/legacy_v2_vectors.json").read_text())
        signatures = []
        for row, vector in zip(fixtures, old_vectors):
            row.portrait_identity = vector
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
