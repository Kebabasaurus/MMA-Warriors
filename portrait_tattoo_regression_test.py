"""Regression coverage for cosmetic tattoo catalogue and rarity rules."""

from types import SimpleNamespace
from unittest.mock import patch
import unittest

from fighter_portraits.identity import (CURRENT_PORTRAIT_VERSION, derived_portrait_identity,
                                        ensure_portrait_identity, trait_hash)
from fighter_portraits.render import rasterize_portrait
from fighter_portraits.state import portrait_state
from fighter_portraits.styles import TATTOO_DESIGNS
from fighter_portraits.tattoos import FAMOUS_TATTOOS, named_tattoo


def fighter(fighter_id="FTR-tattoo", name="Generated Fighter", version=CURRENT_PORTRAIT_VERSION):
    return SimpleNamespace(
        fighter_id=fighter_id, name=name, portrait_version=version, age=27,
        gender="Male", birth_country="USA", nationality="American", region="USA",
        birth_region="", record_w=8, record_l=2, record_d=0, last_fight_stats={},
        injured=0, serious_injury="", portrait_identity={"skin": 1, "hair_style": 0,
                                                           "hair_colour": 1},
    )


class TattooRegressionTests(unittest.TestCase):
    def test_catalogue_has_240_append_only_stable_ids(self):
        self.assertEqual(240, len(TATTOO_DESIGNS))
        self.assertEqual(240, len(set(TATTOO_DESIGNS)))
        self.assertEqual("crown_00", TATTOO_DESIGNS[0])
        self.assertEqual("abstract_09", TATTOO_DESIGNS[-1])
        self.assertEqual(set(range(240)), {
            trait_hash(f"FTR-tattoo-design-{index}", "tattoo_design", len(TATTOO_DESIGNS))
            for index in range(6000)
        })

    def test_generated_tattoos_are_rare_id_stable_and_v4_only(self):
        rows = [fighter(f"FTR-tattoo-rare-{index}") for index in range(5000)]
        designs = [portrait_state(row)["tattoo_design"] for row in rows]
        rate = sum(design is not None for design in designs) / len(designs)
        self.assertGreater(rate, .01)
        self.assertLess(rate, .04)
        self.assertEqual(
            portrait_state(fighter("FTR-tattoo-stable", name="First")),
            portrait_state(fighter("FTR-tattoo-stable", name="Renamed")),
        )
        self.assertIsNone(portrait_state(fighter(version=3))["tattoo_design"])

    def test_complete_v3_identity_is_never_rewritten_by_the_v4_bump(self):
        row = fighter("FTR-saved-v3", version=3)
        row.portrait_identity = derived_portrait_identity(row)
        before = dict(row.portrait_identity)
        ensure_portrait_identity(row)
        self.assertEqual(3, row.portrait_version)
        self.assertEqual(before, row.portrait_identity)
        self.assertIsNone(portrait_state(row)["tattoo_design"])

    def test_named_crop_visible_tattoos_are_explicit_and_rendered(self):
        self.assertEqual({"Conor McGregor", "Charles Oliveira", "Cody Garbrandt"},
                         set(FAMOUS_TATTOOS))
        for name, (design, placement) in FAMOUS_TATTOOS.items():
            design_id, actual_placement = named_tattoo(name)
            self.assertEqual((design, placement), (TATTOO_DESIGNS[design_id], actual_placement))
        row = fighter("FTR-conor-tattoo", "Conor McGregor", version=3)
        with_tattoo = rasterize_portrait(row, 104).pixels
        with patch("fighter_portraits.render.named_tattoo", return_value=None):
            without_tattoo = rasterize_portrait(row, 104).pixels
        self.assertNotEqual(with_tattoo, without_tattoo)

    def test_tattoos_do_not_mutate_or_use_simulation_values(self):
        row = fighter()
        row.popularity, row.striking, row.ability, row.simulation_value = 99, 72, 68, 55
        before = dict(row.__dict__)
        portrait_state(row)
        rasterize_portrait(row, 72)
        self.assertEqual(before, row.__dict__)


if __name__ == "__main__":
    unittest.main()
