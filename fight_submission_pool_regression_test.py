"""Pre-draw candidate variants conserve every original mechanical ticket family."""
from collections import defaultdict
from copy import deepcopy
from dataclasses import replace
import random
import unittest
from unittest.mock import patch

import fight_engine
from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import ALL_POSITIONS, MOVE_REGISTRY, MoveIndex
from analysis.fight_candidate_context import DRAFT_MOVE_DEFINITIONS
from fight_moves.submission_pool import SUBMISSION_VARIANTS, adapt_submission_tickets, submission_ticket_family
from fight_moves.submission_identity import compatible_submission_ids


class SubmissionPoolTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.a = synthetic_fighter('Same Name', 85, 'BJJ', 'Control', 0)
        self.b = synthetic_fighter('Same Name', 85, 'Wrestler', 'Control', 1)
        self.a.detailed_skills = dict.fromkeys(self.a.detailed_skills, 85)
        self.registry = dict(MOVE_REGISTRY, **{m.move_id: m for m in DRAFT_MOVE_DEFINITIONS})
        self.addCleanup(random.setstate, random.getstate())

    def state(self, position, parent, actor_key='a'):
        other = 'b' if actor_key == 'a' else 'a'
        bottom = parent == 'bottom_submission'
        return {'position': position, 'top': other if bottom else actor_key,
                'bottom': actor_key if bottom else other, 'clinch_controller': None,
                'round': 1, 'tick': 2, 'fighter_keys': {id(self.a): actor_key, id(self.b): other},
                'stats': {k: defaultdict(int) for k in ('a', 'b')},
                'gas': {'a': 80, 'b': 80}, 'danger': {'a': 0, 'b': 0}}

    def pool(self, state, action, enabled):
        self.engine._experimental_specialist_entries = enabled
        with patch('fight_engine.MOVE_REGISTRY', self.registry), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.choice.side_effect = lambda options: options[0]
            self.engine.submission_technique(self.a, action, state)
            rng.return_value.choice.assert_called_once()
            rng.return_value.random.assert_not_called()
            rng.return_value.randint.assert_not_called()
            return rng.return_value.choice.call_args.args[0]

    def test_all_positions_actions_slots_preserve_length_order_family_and_first_originals(self):
        for position in ALL_POSITIONS:
            for action in ('submission', 'bottom_submission', 'leg_attack', 'front_headlock_submission'):
                for actor_key in ('a', 'b'):
                    state = self.state(position, action, actor_key)
                    before = deepcopy(state)
                    # Conservation belongs to the variant adapter, not to the
                    # separately recalibrated role-aware mechanical base pool.
                    with patch.object(self.engine, '_experimental_submission_tickets',
                                      side_effect=lambda actor, parent, context, expanded: expanded):
                        baseline = self.pool(state, action, True)
                    candidate = self.pool(state, action, True)
                    self.assertEqual(len(candidate), len(baseline))
                    self.assertEqual(list(map(submission_ticket_family, candidate)),
                                     list(map(submission_ticket_family, baseline)))
                    first = set()
                    for index, ticket in enumerate(baseline):
                        if ticket not in first:
                            self.assertEqual(candidate[index], ticket)
                            first.add(ticket)
                    self.assertEqual(state, before)

    def test_no_gi_ezekiel_retained_only_in_top_guard(self):
        for slot in ('a', 'b'):
            for position in ('guard', 'half guard'):
                for action in ('submission', 'bottom_submission'):
                    pool = self.pool(self.state(position, action, slot), action, True)
                    self.assertEqual(pool.count(('Ezekiel choke', True)),
                                     int(position == 'guard' and action == 'submission'))

    def test_no_eligible_family_preserves_original_tickets_and_rng(self):
        original = [('heel hook', False), ('heel hook', False), ('guillotine choke', True)]
        rng = random.getstate()
        self.assertEqual(adapt_submission_tickets(original, set()), original)
        self.assertEqual(adapt_submission_tickets(original, {'guard_gogoplata'}), original)
        self.assertEqual(random.getstate(), rng)

    def test_pure_pool_matches_draw_input_without_mutation_or_rng(self):
        for enabled in (False, True):
            for position in ALL_POSITIONS:
                for action in ('submission', 'bottom_submission'):
                    state = self.state(position, action)
                    expected = self.pool(state, action, enabled)
                    before, rng_before = deepcopy(state), random.getstate()
                    with patch('fight_engine.MOVE_REGISTRY', self.registry), \
                         patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('pool drew RNG')):
                        actual = self.engine.submission_technique_tickets(self.a, action, state)
                    self.assertEqual(actual, expected)
                    self.assertEqual(state, before)
                    self.assertEqual(random.getstate(), rng_before)

    def test_every_variant_is_resolved_pre_draw_with_compatible_identity(self):
        for move_id, name, choke in SUBMISSION_VARIANTS:
            move = self.registry[move_id]
            self.a.style = move.preferred_styles[0]
            self.a.signature_moves = [move_id]
            position = 'back control' if move_id == 'submission_grappler_rear_triangle_finisher' else sorted(move.positions)[0]
            action = move.parent_action
            state = self.state(position, action)
            self.engine._experimental_specialist_entries = True
            with patch('fight_engine.MOVE_REGISTRY', self.registry), \
                 patch.object(self.engine, 'fight_mechanics_rng') as rng:
                def choose(options):
                    self.assertIn((name, choke), options, move_id)
                    return name, choke
                rng.return_value.choice.side_effect = choose
                actual = self.engine.submission_technique(self.a, action, state)
                rng.return_value.choice.assert_called_once()
            self.assertEqual(actual, {'name': name, 'choke': choke})
            self.assertIn(move_id, compatible_submission_ids(actual))
            with patch('fight_engine.legal_moves', side_effect=MoveIndex((move,)).legal_moves), \
                 patch.object(self.engine, '_move_rarity_gate', return_value=True):
                payload = self.engine.select_exchange_move(self.a, self.b, action, position, '', state,
                                                          resolved_technique=actual)
            self.assertEqual(payload['move_id'], move_id)
            self.assertTrue(payload['signature'])

    def test_skill_role_action_position_style_and_deprecation_boundaries(self):
        self.engine._experimental_specialist_entries = True
        move = self.registry['guard_gogoplata']
        baseline = [('triangle choke', True)] * 3
        state = self.state('guard', 'bottom_submission')
        def adapted(registry=None, action='bottom_submission'):
            with patch('fight_engine.MOVE_REGISTRY', registry or {move.move_id: move}):
                return self.engine._experimental_submission_tickets(self.a, action, state, baseline)
        self.assertIn(('gogoplata', True), adapted())  # Preferred BJJ is not required.
        self.a.style = 'Boxer'
        self.assertIn(('gogoplata', True), adapted())
        with patch.object(self.engine, 'ds', return_value=1):
            self.assertEqual(adapted(), baseline)
        self.assertEqual(adapted({move.move_id: replace(move, deprecated=True)}), baseline)
        state['bottom'], state['top'] = state['top'], state['bottom']
        self.assertEqual(adapted(), baseline)
        state = self.state('mount', 'bottom_submission')
        self.assertEqual(adapted(), baseline)
        state = self.state('guard', 'bottom_submission')
        self.assertEqual(adapted(action='counter_leg_lock'), baseline)
        exclusive = replace(move, tags=(*move.tags, 'style-finisher'))
        self.assertEqual(adapted({move.move_id: exclusive}), baseline)

    def test_unproved_setups_and_positional_counter_locks_are_not_adapted(self):
        ids = {row[0] for row in SUBMISSION_VARIANTS}
        self.assertFalse(ids.intersection({'half_guard_von_flue', 'catch_cradle_neck_crank_finisher',
                                          'scarf_hold_straight_armbar', 'judo_kesa_armbar_finisher',
                                          'heel_hook', 'toe_hold', 'top_submission_chain', 'guard_submission_chain'}))

    def test_adapter_runs_before_real_finish_roll_with_same_family_draw_count(self):
        state = self.state('leg entanglement', 'leg_attack')
        self.engine._experimental_specialist_entries = True
        with patch('fight_engine.MOVE_REGISTRY', self.registry), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.choice.side_effect = lambda options: next(row for row in options if row[0] == 'rolling kneebar')
            rng.return_value.random.return_value = 0
            result = self.engine.resolve_submission(self.a, self.b, 'submission', 30, state,
                                                   {k: defaultdict(int) for k in ('a', 'b')})
            self.assertIsNone(result)
            self.assertEqual(state['last_submission_technique']['name'], 'rolling kneebar')
            self.assertIn('rolling kneebar', state['submission_finish'][2])
            rng.return_value.choice.assert_called_once()
            rng.return_value.random.assert_called_once()  # Joint lock, no choke-only second draw.

    def test_dominant_bottom_pools_cannot_draw_top_only_or_guard_only_attacks(self):
        for actor_key in ('a', 'b'):
            for position in ('mount', 'back control', 'side control'):
                state = self.state(position, 'bottom_submission', actor_key)
                pool = self.pool(state, 'bottom_submission', True)
                names = {name for name, _ in pool}
                allowed = {'wrist lock'} if position != 'side control' else {'wrist lock', 'kimura', 'buggy choke'}
                self.assertEqual(names, allowed)
                self.assertNotIn('rear-naked choke', names)
                self.assertNotIn('triangle choke', names)
                if position != 'side control':
                    self.assertFalse(any(choke for _, choke in pool))
        self.a.detailed_skills['flexibility'] = 64
        state = self.state('side control', 'bottom_submission')
        self.assertNotIn('buggy choke', {name for name, _ in self.pool(state, 'bottom_submission', True)})

    def test_top_pools_exclude_bottom_guard_and_wrong_orientation_or_setup_labels(self):
        bottom_only = {'triangle choke', 'reverse triangle', 'gogoplata', 'omoplata',
                       'belly-down armbar', 'inverted triangle', 'buggy choke'}
        setup_only = {'Von Flue choke', 'scarf-hold choke', 'paper-cutter choke', 'bow-and-arrow choke'}
        for actor_key in ('a', 'b'):
            for position in ('guard', 'half guard', 'mount', 'side control', 'back control'):
                state = self.state(position, 'submission', actor_key)
                pool = self.pool(state, 'submission', True)
                names = {name for name, _ in pool}
                self.assertFalse(names & setup_only)
                if position in ('guard', 'half guard'):
                    self.assertFalse(names & bottom_only)
                    legs = [ticket for ticket in pool if submission_ticket_family(ticket)[1]]
                    self.assertEqual(legs, [('straight ankle lock', False)] if position == 'guard' else [])
                if position == 'mount':
                    self.assertNotIn('north-south choke', names)
                if position == 'side control':
                    self.assertNotIn('mounted triangle', names)
                    self.assertNotIn('mounted arm-triangle', names)

    def test_bottom_half_requires_guard_recovery_for_full_guard_attacks(self):
        full_guard = {'triangle choke', 'omoplata', 'gogoplata', 'inverted triangle'}
        guard = {name for name, _ in self.pool(self.state('guard', 'bottom_submission'), 'bottom_submission', True)}
        half = {name for name, _ in self.pool(self.state('half guard', 'bottom_submission'), 'bottom_submission', True)}
        self.assertTrue(full_guard <= guard)
        self.assertFalse(full_guard & half)

    def test_real_bottom_mount_resolution_and_preview_share_wrist_pool(self):
        for actor_key in ('a', 'b'):
            state = self.state('mount', 'bottom_submission', actor_key)
            self.engine._experimental_specialist_entries = True
            pure = self.engine.submission_technique_tickets(self.a, 'bottom_submission', state)
            with patch.object(self.engine, 'fight_mechanics_rng') as rng:
                rng.return_value.choice.side_effect = lambda options: options[0]
                rng.return_value.random.return_value = 1
                self.engine.resolve_submission(self.a, self.b, 'bottom_submission', 30, state,
                                               {k: defaultdict(int) for k in ('a', 'b')})
                self.assertEqual(rng.return_value.choice.call_args.args[0], pure)
                rng.return_value.choice.assert_called_once()
                rng.return_value.random.assert_called_once()
            self.assertEqual(state['last_submission_technique'], {'name': 'wrist lock', 'choke': False})
            self.assertEqual(state['position'], 'mount')
            self.assertEqual(state['bottom'], actor_key)
            self.assertEqual(state['stats'][actor_key]['sub_att'], 1)

    def test_default_pool_still_keeps_legacy_mixed_geometry_without_candidate_rewrite(self):
        for actor_key in ('a', 'b'):
            state = self.state('mount', 'bottom_submission', actor_key)
            legacy = {name for name, _ in self.pool(state, 'bottom_submission', False)}
            self.assertTrue({'north-south choke', 'mounted triangle', 'triangle choke', 'omoplata'} <= legacy)
            self.assertEqual({name for name, _ in self.pool(state, 'bottom_submission', True)}, {'wrist lock'})


if __name__ == '__main__':
    unittest.main()
