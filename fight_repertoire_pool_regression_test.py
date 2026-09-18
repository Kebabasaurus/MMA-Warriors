"""Expanded ordinary choices preserve bounded quality and existing priorities."""
from types import SimpleNamespace
import unittest
from fight_moves.selection_pool import ordinary_selection_pool
from analysis.generate_variety_opportunity_report import final_selection_pool
from fight_engine_audit import FightAuditHarness


class RepertoirePoolTests(unittest.TestCase):
    def rows(self):
        return [(100-i, SimpleNamespace(move_id=str(i), tags=())) for i in range(10)]

    def test_quality_cap_default_and_no_mutation(self):
        rows = self.rows()
        before = list(rows)
        self.assertEqual(ordinary_selection_pool(rows, set(), {}, False), (rows[:5], 'ordinary'))
        self.assertEqual(ordinary_selection_pool(rows, set(), {}, True), (rows[:7], 'ordinary'))
        rows[7] = (93.4, rows[7][1])
        self.assertEqual(len(ordinary_selection_pool(rows, set(), {}, True)[0]), 8)
        self.assertEqual(before[:7], rows[:7])
        self.assertEqual(ordinary_selection_pool([], set(), {}, True), ([], 'ordinary'))

    def test_chain_priority_cannot_promote_low_rank_successor(self):
        rows = self.rows()
        self.assertEqual(ordinary_selection_pool(rows, {'1', '3'}, {'next_move_id': '3'}, True),
                         ([rows[3]], 'chain'))
        self.assertEqual(ordinary_selection_pool(rows, {'6'}, {'next_move_id': '6'}, True),
                         (rows[:7], 'ordinary'))

    def test_real_selector_observer_priority_and_membership(self):
        rows = self.rows()
        rows[3][1].tags = ('counter',)
        engine = FightAuditHarness()
        for enabled in (False, True):
            engine._experimental_chain_action_weighting = enabled
            for counter, signature, chain in ((False, set(), set()), (True, set(), set()),
                                              (False, {'0'}, set()), (False, set(), {'1'})):
                pool, _kind = final_selection_pool(rows, counter, signature, chain, {}, expanded=enabled)
                seen = set()
                for tick in range(1, 201):
                    move = engine._select_from_pool(list(rows), counter, signature, chain, {},
                        'fighter', 'jab', 'range', 'head', {'round': 1, 'tick': tick})
                    self.assertIn(move.move_id, pool)
                    seen.add(move.move_id)
                if enabled and not counter and not signature and not chain:
                    self.assertTrue(seen.intersection({'5', '6'}))


if __name__ == '__main__':
    unittest.main()
