"""Regression coverage for cosmetic shaved/buzzed scalp variation."""

from types import SimpleNamespace
from unittest.mock import patch
import hashlib
import unittest

from fighter_portraits.render import rasterize_portrait
from fighter_portraits.state import portrait_state
from fighter_portraits.styles import SCALP_FINISHES


def fighter(fighter_id="FTR-scalp", age=38, name="Scalp Test"):
    return SimpleNamespace(
        fighter_id=fighter_id, name=name, age=age, gender="Male",
        birth_country="USA", nationality="American", region="USA", birth_region="",
        record_w=12, record_l=4, record_d=0, injured=0, serious_injury="",
        last_fight_stats={}, portrait_version=3,
        portrait_identity={"hair_style": 0, "hair_colour": 1, "skin": 1},
    )


class ScalpFinishRegressionTests(unittest.TestCase):
    def test_finish_catalogue_is_broad_and_id_stable(self):
        self.assertEqual(24, len(SCALP_FINISHES))
        seen = {portrait_state(fighter(f"FTR-scalp-{index}"))["scalp_finish"]
                for index in range(600)}
        self.assertEqual(set(range(len(SCALP_FINISHES))), seen)
        self.assertEqual(
            portrait_state(fighter("FTR-stable", name="One"))["scalp_finish"],
            portrait_state(fighter("FTR-stable", name="Renamed"))["scalp_finish"],
        )
        self.assertIsNone(portrait_state(fighter(age=29))["scalp_finish"])

    def test_each_finish_visibly_changes_the_same_shaved_portrait(self):
        row = fighter()
        common = {
            "grey": 0.0, "recede": 0.0, "cauli": 0.0, "scar": 0.0,
            "nose_damage": 0.0, "recent_head_damage": 0.0, "recent_cut": 0.0,
            "recent_cut_location": "", "swell": 0.0,
        }
        renders = set()
        for finish in range(len(SCALP_FINISHES)):
            with patch("fighter_portraits.render.portrait_state",
                       return_value=dict(common, scalp_finish=finish)):
                pixels = rasterize_portrait(row, 104).pixels
            renders.add(hashlib.sha256(bytes(channel for pixel in pixels for channel in pixel)).hexdigest())
        self.assertEqual(len(SCALP_FINISHES), len(renders))

    def test_portrait_state_does_not_mutate_or_read_simulation_values(self):
        row = fighter()
        row.popularity, row.striking, row.ability, row.simulation_value = 99, 72, 68, 55
        before = dict(row.__dict__)
        portrait_state(row)
        self.assertEqual(before, row.__dict__)


if __name__ == "__main__":
    unittest.main()
