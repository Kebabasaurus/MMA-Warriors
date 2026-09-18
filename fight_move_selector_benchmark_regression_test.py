"""Profiler isolation and evidence contracts, without a machine-speed assertion."""
import random
import unittest
from unittest.mock import patch

import fight_engine
from fight_moves import MOVE_DEFINITIONS
from tools.benchmark_move_selector import benchmark, expanded_definitions


class SelectorBenchmarkTests(unittest.TestCase):
    def test_expansion_keeps_original_objects_and_is_exactly_eight_hundred(self):
        expanded = expanded_definitions(MOVE_DEFINITIONS)
        self.assertEqual(len(expanded), 800)
        self.assertEqual(len({m.move_id for m in expanded}), 800)
        self.assertTrue(all(old is new for old, new in zip(MOVE_DEFINITIONS, expanded)))
        with self.assertRaises(ValueError):
            expanded_definitions(())

    def test_repeated_bouts_restore_state_and_report_honest_denominator(self):
        registry, lookup, rng = fight_engine.MOVE_REGISTRY, fight_engine.legal_moves, random.getstate()
        report = benchmark(fight_count=1, repeats=2)
        self.assertTrue(all(report["self_checks"].values()))
        self.assertIs(fight_engine.MOVE_REGISTRY, registry)
        self.assertIs(fight_engine.legal_moves, lookup)
        self.assertEqual(random.getstate(), rng)
        self.assertEqual(report["maximum_selector_share_pct"], 15)
        for sample in report["samples"]:
            self.assertEqual(sample["simulation"]["calls"], 1)
            self.assertAlmostEqual(sample["selector_share_pct"],
                100 * sample["selector"]["cumulative_seconds"] / sample["simulation"]["cumulative_seconds"])

    def test_injected_failure_restores_registry_and_rng(self):
        registry, lookup, rng = fight_engine.MOVE_REGISTRY, fight_engine.legal_moves, random.getstate()
        with patch("tools.benchmark_move_selector.run_audited_fight", side_effect=RuntimeError("injected")):
            with self.assertRaisesRegex(RuntimeError, "injected"):
                benchmark(fight_count=1, repeats=1)
        self.assertIs(fight_engine.MOVE_REGISTRY, registry)
        self.assertIs(fight_engine.legal_moves, lookup)
        self.assertEqual(random.getstate(), rng)
        for fights, repeats in ((0, 1), (1, 0)):
            with self.assertRaises(ValueError):
                benchmark(fights, repeats)


if __name__ == "__main__":
    unittest.main()
