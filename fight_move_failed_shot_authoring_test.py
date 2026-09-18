"""Unregistered failed-shot vocabulary and actual shooter/controller contracts."""
from collections import Counter, defaultdict
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import ALL_POSITIONS, MOVE_DEFINITIONS, MoveIndex
from fight_moves.catalogue.failed_shot_development import FAILED_SHOT_DEVELOPMENT
from fight_moves.catalogue.front_headlock_development import FRONT_HEADLOCK_DEVELOPMENT
from fight_moves.catalogue.specialist_entry_development import SPECIALIST_ENTRY_DEVELOPMENT
from fight_moves.chains import MoveChainGraph, sequence_role_allows
from fight_moves.validation import validate_move_registry


class FailedShotAuthoringTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.a = synthetic_fighter('Same Name', 75, 'Wrestler', 'Control', 0)
        self.b = synthetic_fighter('Same Name', 75, 'Grappler', 'Control', 1)
        self.addCleanup(random.setstate, random.getstate())

    def combined(self):
        return (*MOVE_DEFINITIONS, *SPECIALIST_ENTRY_DEVELOPMENT,
                *FRONT_HEADLOCK_DEVELOPMENT, *FAILED_SHOT_DEVELOPMENT)

    def state(self, actor_key, controller):
        other = 'b' if actor_key == 'a' else 'a'
        return {'position': 'failed shot', 'clinch_controller': controller,
                'top': None, 'bottom': None, 'round': 1, 'tick': 2,
                'fighter_keys': {id(self.a): actor_key, id(self.b): other},
                'stats': {key: defaultdict(int) for key in ('a', 'b')},
                'gas': {'a': 80, 'b': 80}, 'hurt': {'a': 0, 'b': 0}}

    def test_seven_unique_neutral_moves_and_twenty_one_draft_graph(self):
        definitions = self.combined()
        self.assertEqual(len(FAILED_SHOT_DEVELOPMENT), 7)
        self.assertEqual(len(definitions), len(MOVE_DEFINITIONS) + 21)
        self.assertEqual(Counter(m.parent_action for m in FAILED_SHOT_DEVELOPMENT),
                         {'re_shot': 3, 'recover_shot': 2, 'disengage': 2})
        self.assertEqual(validate_move_registry(definitions), [])
        self.assertEqual(len({m.name for m in definitions}), len(definitions))
        MoveChainGraph(definitions)
        index = MoveIndex(definitions)
        for move in FAILED_SHOT_DEVELOPMENT:
            self.assertEqual((move.energy, move.miss_risk, move.counter_risk), (1, 1, 1))
            self.assertTrue(1 <= len(move.follow_ups) <= 3)
            for position in ALL_POSITIONS:
                self.assertEqual(move in index.legal_moves(move.parent_action, position), position == 'failed shot')

    def test_chooser_enforces_controller_and_shooter_actions_both_slots(self):
        for actor_key in ('a', 'b'):
            for controller in ('a', 'b'):
                state = self.state(actor_key, controller)
                with patch.object(self.engine, 'weighted_choice', side_effect=lambda weights: weights):
                    actions = self.engine.choose_action(self.a, self.b, state, 1, 2)
                for move in FAILED_SHOT_DEVELOPMENT:
                    self.assertEqual(move.parent_action in actions,
                                     (actor_key == controller) == (move.parent_action == 'disengage'))

    def test_real_resolver_boundaries_and_followup_role_for_every_outcome(self):
        by_id = {move.move_id: move for move in self.combined()}
        cases = {'re_shot': ((7, 'guard'), (6, 'cage'), (-6, 'cage'), (-7, 'front headlock')),
                 'recover_shot': ((-2, 'range'), (-3, 'cage')),
                 'disengage': ((-30, 'range'), (30, 'range'))}
        for move in FAILED_SHOT_DEVELOPMENT:
            for actor_key in ('a', 'b'):
                other = 'b' if actor_key == 'a' else 'a'
                controller = actor_key if move.parent_action == 'disengage' else other
                seen = set()
                for margin, expected in cases[move.parent_action]:
                    with self.subTest(move=move.move_id, actor=actor_key, margin=margin):
                        state = self.state(actor_key, controller)
                        with patch.object(self.engine, 'action_attack_value', return_value=margin), \
                             patch.object(self.engine, 'action_defence_value', return_value=0), \
                             patch.object(self.engine, 'fight_mechanics_rng') as rng:
                            rng.return_value.randint.return_value = 0
                            self.engine._resolve_exchange_action(self.a, self.b, move.parent_action, state,
                                                                {k: defaultdict(int) for k in ('a', 'b')})
                            rng.return_value.randint.assert_called_once_with(-18, 18)
                            rng.return_value.random.assert_not_called()
                        self.assertEqual(state['position'], expected)
                        self.engine.validate_fight_transition('failed shot', expected, state)
                        if expected == 'guard':
                            self.assertEqual(state['top'], actor_key)
                        elif expected == 'front headlock':
                            self.assertEqual(state['top'], other)
                            self.assertEqual(state['bottom'], actor_key)
                        elif expected == 'cage':
                            self.assertEqual(state['clinch_controller'], actor_key if move.parent_action == 're_shot' else other)
                        available = {key for key in move.follow_ups if expected in by_id[key].positions
                                     and sequence_role_allows(by_id[key].parent_action, expected, actor_key,
                                                             state['top'], state['bottom'])}
                        self.assertTrue(available)
                        seen.update(available)
                self.assertEqual(seen, set(move.follow_ups))

    def test_isolated_payload_selection_is_named_and_rng_pure(self):
        for move in FAILED_SHOT_DEVELOPMENT:
            for actor_key in ('a', 'b'):
                other = 'b' if actor_key == 'a' else 'a'
                state = self.state(actor_key, actor_key if move.parent_action == 'disengage' else other)
                before = random.getstate()
                with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves):
                    payload = self.engine.select_exchange_move(self.a, self.b, move.parent_action,
                                                              'failed shot', '', state)
                self.assertEqual(payload['move_id'], move.move_id)
                self.assertFalse(payload['generic'])
                self.assertEqual(random.getstate(), before)


if __name__ == '__main__':
    unittest.main()
