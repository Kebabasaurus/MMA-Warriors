"""Sparse continuation authoring is pure, bounded and audit-only."""
from dataclasses import asdict, replace
import random
import unittest

from analysis.continuation_branch_candidate import (
    CONTINUATION_ADDITIONS, CONTINUATION_RATIONALES, apply_continuation_branches,
)
from analysis.fight_candidate_context import DRAFT_MOVE_DEFINITIONS
import fight_moves
from fight_moves.chains import validate_chain_graph


class ContinuationBranchCandidateTests(unittest.TestCase):
    def setUp(self):
        self.definitions = tuple(fight_moves.MOVE_DEFINITIONS) + DRAFT_MOVE_DEFINITIONS

    def test_full_400_graph_order_existing_edges_and_nonmutation(self):
        before = tuple(asdict(row) for row in self.definitions)
        rng = random.getstate()
        candidate = apply_continuation_branches(iter(self.definitions))
        self.assertEqual(len(candidate), 400)
        self.assertEqual(validate_chain_graph(candidate), [])
        self.assertEqual(len(CONTINUATION_ADDITIONS), 13)
        self.assertEqual(set(CONTINUATION_RATIONALES), set(CONTINUATION_ADDITIONS))
        self.assertTrue(all(CONTINUATION_RATIONALES.values()))
        for original, updated in zip(self.definitions, candidate):
            self.assertEqual(original.move_id, updated.move_id)
            self.assertEqual(updated.follow_ups[:len(original.follow_ups)], original.follow_ups)
            self.assertEqual(updated.follow_ups[len(original.follow_ups):],
                             CONTINUATION_ADDITIONS.get(original.move_id, ()))
            self.assertLessEqual(len(updated.follow_ups), 3)
            old, new = asdict(original), asdict(updated)
            old.pop('follow_ups'); new.pop('follow_ups')
            self.assertEqual(old, new)
            if original.move_id not in CONTINUATION_ADDITIONS:
                self.assertIs(updated, original)
        self.assertEqual(tuple(asdict(row) for row in self.definitions), before)
        self.assertEqual(random.getstate(), rng)

    def test_normal_registry_and_lookup_bindings_remain_unchanged(self):
        definitions = fight_moves.MOVE_DEFINITIONS
        registry = fight_moves.MOVE_REGISTRY
        graph = fight_moves.CHAIN_GRAPH
        index = fight_moves.MOVE_INDEX
        snapshot = dict(registry)
        apply_continuation_branches(self.definitions)
        self.assertIs(fight_moves.MOVE_DEFINITIONS, definitions)
        self.assertIs(fight_moves.MOVE_REGISTRY, registry)
        self.assertIs(fight_moves.CHAIN_GRAPH, graph)
        self.assertIs(fight_moves.MOVE_INDEX, index)
        self.assertEqual(dict(registry), snapshot)
        self.assertEqual(len(definitions), 346)

    def test_missing_roots_successors_and_duplicate_ids_are_rejected(self):
        for missing in ('overhand', 'single_jab'):
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, 'missing'):
                apply_continuation_branches(row for row in self.definitions if row.move_id != missing)
        with self.assertRaisesRegex(ValueError, 'duplicate move IDs'):
            apply_continuation_branches(self.definitions + (self.definitions[0],))
        conflicting = replace(self.definitions[0], name='Conflicting duplicate')
        with self.assertRaisesRegex(ValueError, 'duplicate move IDs'):
            apply_continuation_branches(self.definitions + (conflicting,))

    def test_repeated_application_is_idempotent_without_stacking(self):
        candidate = apply_continuation_branches(self.definitions)
        repeated = apply_continuation_branches(candidate)
        self.assertEqual(repeated, candidate)
        self.assertTrue(all(a is b for a, b in zip(candidate, repeated)))

    def test_excess_successors_duplicates_and_cycles_are_rejected(self):
        replacements = (
            ('overhand', ('double_leg_entry', 'single_leg_entry', 'collar_tie_entry'), 'More than three'),
            ('overhand', ('double_leg_entry', 'double_leg_entry'), 'Duplicate continuation'),
            ('single_jab', ('overhand',), 'Invalid continuation candidate graph'),
        )
        for key, successors, message in replacements:
            changed = tuple(replace(row, follow_ups=successors) if row.move_id == key else row
                            for row in self.definitions)
            with self.subTest(key=key, successors=successors), self.assertRaisesRegex(ValueError, message):
                apply_continuation_branches(changed)


if __name__ == '__main__':
    unittest.main()
