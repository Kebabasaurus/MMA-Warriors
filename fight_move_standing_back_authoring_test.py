"""Draft rear-standing move identities, resolver boundaries and chooser ownership."""
from collections import Counter, defaultdict
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import ALL_POSITIONS, MOVE_DEFINITIONS, MoveIndex
from fight_moves.catalogue.standing_back_development import STANDING_BACK_DEVELOPMENT
from fight_moves.catalogue.specialist_entry_development import SPECIALIST_ENTRY_DEVELOPMENT
from fight_moves.catalogue.front_headlock_development import FRONT_HEADLOCK_DEVELOPMENT
from fight_moves.catalogue.failed_shot_development import FAILED_SHOT_DEVELOPMENT
from fight_moves.catalogue.turtle_development import TURTLE_DEVELOPMENT
from fight_moves.chains import MoveChainGraph, sequence_role_allows
from fight_moves.validation import validate_move_registry


class StandingBackAuthoringTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.a = synthetic_fighter('Same Name', 75, 'Wrestler', 'Control', 0)
        self.b = synthetic_fighter('Same Name', 75, 'Grappler', 'Control', 1)
        self.addCleanup(random.setstate, random.getstate())

    def combined(self):
        drafts = (*SPECIALIST_ENTRY_DEVELOPMENT, *FRONT_HEADLOCK_DEVELOPMENT,
                  *FAILED_SHOT_DEVELOPMENT, *TURTLE_DEVELOPMENT, *STANDING_BACK_DEVELOPMENT)
        additions = {m.move_id: m for m in drafts}
        for move in MOVE_DEFINITIONS:
            if move.move_id in additions:
                self.assertEqual(move, additions[move.move_id])
        return (*[m for m in MOVE_DEFINITIONS if m.move_id not in additions], *drafts)

    def state(self, actor_key, controller):
        other = 'b' if actor_key == 'a' else 'a'
        return {'position': 'standing back control', 'top': None, 'bottom': None,
                'clinch_controller': controller, 'round': 1, 'tick': 2,
                'fighter_keys': {id(self.a): actor_key, id(self.b): other},
                'stats': {k: defaultdict(int) for k in ('a', 'b')},
                'gas': {'a': 80, 'b': 80}, 'hurt': {'a': 0, 'b': 0}}

    def test_eight_neutral_distinct_moves_and_combined_graph(self):
        definitions = self.combined()
        self.assertEqual(len(definitions), 385)
        self.assertEqual(len(STANDING_BACK_DEVELOPMENT), 8)
        self.assertEqual(Counter(m.parent_action for m in STANDING_BACK_DEVELOPMENT),
                         {'mat_return': 3, 'standing_back_ride': 2, 'standing_escape': 2, 'recover_shot': 1})
        self.assertEqual(validate_move_registry(definitions), [])
        self.assertEqual(len({m.name for m in definitions}), len(definitions))
        MoveChainGraph(definitions)
        index = MoveIndex(definitions)
        for move in STANDING_BACK_DEVELOPMENT:
            self.assertEqual((move.energy, move.miss_risk, move.counter_risk), (1, 1, 1))
            self.assertTrue(1 <= len(move.follow_ups) <= 3)
            for position in ALL_POSITIONS:
                self.assertEqual(move in index.legal_moves(move.parent_action, position),
                                 position == 'standing back control')

    def test_chooser_controller_and_trapped_actions_both_orientations(self):
        for actor_key in ('a', 'b'):
            for controller in ('a', 'b'):
                with patch.object(self.engine, 'weighted_choice', side_effect=lambda weights: weights):
                    actions = self.engine.choose_action(self.a, self.b, self.state(actor_key, controller), 1, 2)
                self.assertEqual(set(actions), {'mat_return', 'dirty_boxing', 'standing_back_ride'}
                                 if actor_key == controller else {'standing_escape', 'recover_shot'})
                for move in STANDING_BACK_DEVELOPMENT:
                    self.assertEqual(move.parent_action in actions,
                                     (actor_key == controller) == (move.parent_action in {'mat_return', 'standing_back_ride'}))

    def test_actual_resolver_thresholds_and_poststate_successors(self):
        by_id = {m.move_id: m for m in self.combined()}
        cases = {'mat_return': ((-1, 'back control'), (-2, 'cage')),
                 'standing_back_ride': ((-30, 'standing back control'), (30, 'standing back control')),
                 'standing_escape': ((3, 'range'), (2, 'standing back control')),
                 'recover_shot': ((-2, 'range'), (-3, 'cage'))}
        for move in STANDING_BACK_DEVELOPMENT:
            for actor_key in ('a', 'b'):
                other = 'b' if actor_key == 'a' else 'a'
                controller = actor_key if move.parent_action in {'mat_return', 'standing_back_ride'} else other
                available = set()
                for margin, expected in cases[move.parent_action]:
                    with self.subTest(move=move.move_id, actor=actor_key, margin=margin):
                        state = self.state(actor_key, controller)
                        stats = {k: defaultdict(int) for k in ('a', 'b')}
                        with patch.object(self.engine, 'action_attack_value', return_value=margin), \
                             patch.object(self.engine, 'action_defence_value', return_value=0), \
                             patch.object(self.engine, 'fight_mechanics_rng') as rng:
                            rng.return_value.randint.return_value = 0
                            self.engine._resolve_exchange_action(self.a, self.b, move.parent_action, state, stats)
                            rng.return_value.randint.assert_called_once_with(-18, 18)
                            rng.return_value.random.assert_not_called()
                        self.assertEqual(state['position'], expected)
                        self.engine.validate_fight_transition('standing back control', expected, state)
                        if expected == 'back control':
                            self.assertEqual((state['top'], state['bottom']), (actor_key, other))
                            self.assertIsNone(state['clinch_controller'])
                            self.assertEqual(state['stats'][actor_key]['td'], 1)
                        elif expected in {'cage', 'standing back control'}:
                            self.assertEqual(state['clinch_controller'], controller)
                            self.assertIsNone(state['top'])
                            self.assertIsNone(state['bottom'])
                        else:
                            self.assertIsNone(state['clinch_controller'])
                        available.update(key for key in move.follow_ups if expected in by_id[key].positions
                                         and sequence_role_allows(by_id[key].parent_action, expected, actor_key,
                                                                 state['top'], state['bottom']))
                self.assertEqual(available, set(move.follow_ups))

    def test_named_payloads_both_controller_orientations_without_rng(self):
        for move in STANDING_BACK_DEVELOPMENT:
            for actor_key in ('a', 'b'):
                other = 'b' if actor_key == 'a' else 'a'
                controller = actor_key if move.parent_action in {'mat_return', 'standing_back_ride'} else other
                state = self.state(actor_key, controller)
                before = random.getstate()
                with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves):
                    payload = self.engine.select_exchange_move(self.a, self.b, move.parent_action,
                                                              'standing back control', '', state)
                self.assertEqual(payload['move_id'], move.move_id)
                self.assertFalse(payload['generic'])
                self.assertEqual(random.getstate(), before)


if __name__ == '__main__':
    unittest.main()
