"""Draft-only defensive alternatives; no runtime registration or mechanics edits."""
from dataclasses import asdict, replace
import unittest

from fight_moves import MOVE_DEFINITIONS, MOVE_REGISTRY
from fight_moves.chains import MoveChainGraph, sequence_role_allows
from fight_moves.followup_defensive_continuity import DEFENSIVE_CONTINUITY_ADDITIONS
from fight_moves.validation import validate_move_registry


def draft_definitions():
    return tuple(replace(move, follow_ups=(*move.follow_ups, DEFENSIVE_CONTINUITY_ADDITIONS[move.move_id]))
                 if move.move_id in DEFENSIVE_CONTINUITY_ADDITIONS else move
                 for move in MOVE_DEFINITIONS)


class DefensiveContinuityDraftTests(unittest.TestCase):
    def test_twenty_unregistered_append_only_edges(self):
        self.assertEqual(len(DEFENSIVE_CONTINUITY_ADDITIONS), 20)
        definitions = draft_definitions()
        self.assertEqual(validate_move_registry(definitions), [])
        self.assertEqual(len(definitions), len(MOVE_DEFINITIONS))
        for old, new in zip(MOVE_DEFINITIONS, definitions):
            expected = asdict(old)
            if old.move_id in DEFENSIVE_CONTINUITY_ADDITIONS:
                addition = DEFENSIVE_CONTINUITY_ADDITIONS[old.move_id]
                self.assertTrue(old.follow_ups)
                self.assertNotIn(addition, old.follow_ups)
                expected['follow_ups'] = (*old.follow_ups, addition)
            self.assertEqual(asdict(new), expected)

    def test_all_branches_resolve_and_remain_bounded_acyclic(self):
        definitions = draft_definitions()
        graph = MoveChainGraph(definitions)
        for move in definitions:
            self.assertLessEqual(len(move.follow_ups), 3)
            self.assertEqual(len(move.follow_ups), len(set(move.follow_ups)))
            for target in move.follow_ups:
                self.assertGreater(graph.chain_depth(move.move_id), graph.chain_depth(target))

    def test_named_nonterminal_defenses_only(self):
        self.assertEqual(set(DEFENSIVE_CONTINUITY_ADDITIONS.values()), {
            'forearm_shell_survival', 'long_guard_breather',
            'clinch_wrist_tie_breather', 'hip_frame_ground_breather'})
        for target in DEFENSIVE_CONTINUITY_ADDITIONS.values():
            move = MOVE_REGISTRY[target]
            self.assertEqual(move.parent_action, 'survive')
            self.assertFalse(move.deprecated)
            self.assertTrue(move.follow_ups)
            self.assertNotIn('control', move.tags)

    def test_actual_source_positions_and_actor_roles(self):
        for source, target in DEFENSIVE_CONTINUITY_ADDITIONS.items():
            attack, defense = MOVE_REGISTRY[source], MOVE_REGISTRY[target]
            with self.subTest(source=source):
                self.assertIn(attack.parent_action, {
                    'jab', 'power_punch', 'kick', 'dirty_boxing',
                    'cage_control', 'bottom_submission', 'cling'})
                # These sources retain position after an effective nonfinish;
                # bottom submissions and clings retain the bottom actor.
                self.assertTrue(set(attack.positions) <= set(defense.positions))
                is_bottom = attack.parent_action in {'bottom_submission', 'cling'}
                self.assertEqual(target == 'hip_frame_ground_breather', is_bottom)
                for position in attack.positions:
                    top, bottom = ('b', 'a') if is_bottom else (None, None)
                    self.assertTrue(sequence_role_allows(defense.parent_action, position, 'a', top, bottom))


if __name__ == '__main__':
    unittest.main()
