"""Regression coverage for roster-only portrait silhouettes and facial marks."""

from types import SimpleNamespace
import unittest

from fighter_portraits.identity import portrait_identity
from fighter_portraits.overrides import PORTRAIT_SIGNATURE_FEATURES
from fighter_portraits.regions import GENDER_HAIR_STYLE_WEIGHTS
from fighter_portraits.render import rasterize_portrait
from fighter_portraits.styles import HAIR_STYLES


def fighter(name, gender="Male"):
    return SimpleNamespace(
        fighter_id="FTR-custom-" + name, name=name, gender=gender,
        birth_country="USA", nationality="American", region="USA", birth_region="",
        record_w=12, record_l=3, record_d=0, age=29, portrait_identity={}, portrait_version=3,
    )


class CustomPortraitStyleRegressionTests(unittest.TestCase):
    def test_authored_styles_are_append_only_and_not_generated(self):
        self.assertEqual(
            ("authored_spiked_icehawk", "authored_rainbow_lockfall",
             "authored_topknot_undercut", "authored_fighter_braided_ponytail",
             "authored_short_braid_crown", "authored_swept_fade"),
            tuple(row[0] for row in HAIR_STYLES[151:]),
        )
        for weights in GENDER_HAIR_STYLE_WEIGHTS.values():
            self.assertEqual((0,) * 9, weights[148:])

    def test_famous_fighter_assignments_and_female_beard_guard(self):
        expected = {
            "Sean O'Malley": 152,
            "Chuck Liddell": 151,
            "Jiri Prochazka": 153,
            "Ronda Rousey": 154,
            "Valentina Shevchenko": 154,
            "Israel Adesanya": 155,
            "Conor McGregor": 156,
        }
        for name, style in expected.items():
            row = fighter(name, "Female" if name in {"Ronda Rousey", "Valentina Shevchenko"} else "Male")
            before = dict(row.__dict__)
            identity = portrait_identity(row)
            self.assertEqual(style, identity["hair_style"])
            if row.gender == "Female":
                self.assertEqual(0, identity["facial_hair"])
            self.assertEqual(before, row.__dict__)
            for size in (72, 180):
                self.assertEqual(size * size, len(rasterize_portrait(row, size).pixels))
        self.assertEqual("under_eye_tattoo", PORTRAIT_SIGNATURE_FEATURES["Sean O'Malley"])
        conor = portrait_identity(fighter("Conor McGregor"))
        self.assertEqual(156, conor["hair_style"])
        self.assertEqual(1, conor["hair_colour"])
        self.assertEqual(6, conor["beard_colour"])
        self.assertEqual(10, conor["facial_hair"])


if __name__ == "__main__":
    unittest.main()
