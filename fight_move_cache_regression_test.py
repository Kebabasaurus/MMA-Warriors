"""Bout-scoped selector cache lifetime, mutation boundaries and patched definitions."""
from dataclasses import replace
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import MOVE_REGISTRY


class MoveCacheTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.a = synthetic_fighter("Cache A", 76, "Boxer", "Pressure", 0)
        self.b = synthetic_fighter("Cache B", 76, "Wrestler", "Control", 1)
        self.rng = random.getstate()
        self.addCleanup(random.setstate, self.rng)

    def state(self):
        return {"fighter_keys": {id(self.a): "a", id(self.b): "b"}, "round": 1, "tick": 2,
                "plans": self.engine.fight_plan_state(self.a, self.b, {})}

    def select(self):
        return self.engine.select_exchange_move(self.a, self.b, "jab", "range", "head", self.state())

    def test_cache_warms_only_during_bout_and_is_removed_afterward(self):
        def simulation(*_args):
            self.assertEqual(self.engine._fight_move_score_cache, {})
            first = self.select()
            size = len(self.engine._fight_move_score_cache)
            self.assertGreater(size, 0)
            self.assertEqual(first, self.select())
            self.assertEqual(len(self.engine._fight_move_score_cache), size)
            return first
        with patch.object(self.engine, "_simulate_fight_with_caches", side_effect=simulation):
            self.engine.simulate_fight(self.a, self.b, {})
            self.assertFalse(hasattr(self.engine, "_fight_move_score_cache"))
            self.engine.simulate_fight(self.a, self.b, {})
        self.assertFalse(hasattr(self.engine, "_fight_move_score_cache"))

    def test_nested_and_failed_fights_restore_outer_cache_objects(self):
        outer = {"outer": object()}
        self.engine._fight_move_score_cache = outer
        nested = False
        def simulation(*_args):
            nonlocal nested
            cache = self.engine._fight_move_score_cache
            self.assertEqual(cache, {})
            self.assertIsNot(cache, outer)
            if nested:
                cache["failed"] = True
                raise RuntimeError("nested failure")
            nested = True
            cache["live"] = True
            with self.assertRaisesRegex(RuntimeError, "nested failure"):
                self.engine.simulate_fight(self.a, self.b, {})
            self.assertIs(self.engine._fight_move_score_cache, cache)
            self.assertEqual(cache, {"live": True})
            raise RuntimeError("outer failure")
        with patch.object(self.engine, "_simulate_fight_with_caches", side_effect=simulation):
            with self.assertRaisesRegex(RuntimeError, "outer failure"):
                self.engine.simulate_fight(self.a, self.b, {})
        self.assertIs(self.engine._fight_move_score_cache, outer)
        self.assertEqual(set(outer), {"outer"})

    def test_same_id_replaced_definition_cannot_reuse_stale_proficiency(self):
        ordinary = MOVE_REGISTRY["single_jab"]
        impossible = replace(ordinary, minimum_skill=1000)
        def simulation(*_args):
            with patch("fight_engine.legal_moves", return_value=(ordinary,)):
                self.assertFalse(self.select()["generic"])
            with patch("fight_engine.legal_moves", return_value=(impossible,)):
                self.assertTrue(self.select()["generic"])
        with patch.object(self.engine, "_simulate_fight_with_caches", side_effect=simulation):
            self.engine.simulate_fight(self.a, self.b, {})

    def test_direct_calls_and_later_bouts_see_developed_fighter_attributes(self):
        definition = replace(MOVE_REGISTRY["single_jab"],
                             attack_skills=("combination_punching",), minimum_skill=70)
        self.a.detailed_skills = {}
        def simulation(*_args):
            return self.select()
        with (patch("fight_engine.legal_moves", return_value=(definition,)),
              patch.object(self.engine, "_simulate_fight_with_caches", side_effect=simulation)):
            self.a.striking = 90
            self.assertFalse(self.select()["generic"])
            self.assertFalse(self.engine.simulate_fight(self.a, self.b, {})["generic"])
            self.a.striking = 10
            self.assertTrue(self.select()["generic"])
            self.assertTrue(self.engine.simulate_fight(self.a, self.b, {})["generic"])
        self.assertFalse(hasattr(self.engine, "_fight_move_score_cache"))


if __name__ == "__main__":
    unittest.main()
