"""Focused regression contract for the photo-directed ranked 101--200 cohort."""

import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from fighter_portraits.identity import ensure_portrait_identity
from fighter_portraits.ranked_101_200 import PORTRAIT_RANK_101_200_OVERRIDES
from fighter_portraits.render import rasterize_portrait
from fighter_portraits.styles import IDENTITY_TRAITS


class Ranked101To200PortraitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).with_name("Databases") / "Default Universe.universe.json"
        rows = json.loads(source.read_text(encoding="utf-8"))["sections"]["fighters"]["all_fighters"]
        cls.cohort = sorted(rows, key=lambda row: (-int(row.get("rating", 0) or 0), row["name"]))[100:200]

    def test_authored_names_match_the_ranked_database_slice(self):
        self.assertEqual({row["name"] for row in self.cohort}, set(PORTRAIT_RANK_101_200_OVERRIDES))
        self.assertEqual(100, len(PORTRAIT_RANK_101_200_OVERRIDES))

    def test_every_authored_vector_merges_without_mutating_the_saved_identity(self):
        complete = set(IDENTITY_TRAITS) - {"bg"} | {"beard_colour"}
        for record in self.cohort:
            fighter = SimpleNamespace(**record)
            fighter.portrait_identity = {"hair_style": 97, "facial_hair": 65, "skin": 61}
            saved = dict(fighter.portrait_identity)
            actual = ensure_portrait_identity(fighter)
            authored = PORTRAIT_RANK_101_200_OVERRIDES[fighter.name]
            self.assertEqual(complete, set(authored), fighter.name)
            self.assertEqual(authored, {key: actual[key] for key in authored}, fighter.name)
            self.assertEqual(saved, fighter.portrait_identity, fighter.name)

    def test_the_shared_renderer_draws_a_cohort_spread_at_all_ui_sizes(self):
        # Full-pixel snapshot coverage lives in the contact-sheet regression;
        # this focused contract keeps the per-commit smoke check fast.
        for record in self.cohort[::10]:
            fighter = SimpleNamespace(**record)
            for size in (72, 98, 104, 180):
                self.assertEqual(size * size, len(rasterize_portrait(fighter, size).pixels), (fighter.name, size))


if __name__ == "__main__":
    unittest.main()
