"""Pool-aware action demand never forces names or changes initiative/caps."""
from contextlib import redirect_stdout
from copy import deepcopy
from dataclasses import replace
import io
import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from analysis.boxing_chain_pool_candidate import boxing_pool, boxing_chain_pool_trial
from analysis.fight_candidate_context import candidate_context
from analysis import evaluate_joint_fight_candidate as evaluator
from analysis.generate_variety_opportunity_report import final_selection_pool
from fight_engine_audit import FightAuditHarness, run_audited_fight
import fight_chain_action_weighting_regression_test as fixture
from fight_moves import MOVE_REGISTRY
from analysis.benchmark_boxing_chain_pool import preview_stats, ROOT
from analysis.compare_candidate_striking import fixture_schedule
from analysis.generate_variety_opportunity_report import TerminalRngHarness
from fight_engine_audit import synthetic_fighter
from analysis import boxing_chain_pool_candidate as pool_candidate


class BoxingChainPoolTests(unittest.TestCase):
    setUp = fixture.ChainActionWeightingTests.setUp

    def test_profile_counts_preview_outside_selector_and_ignores_other_files(self):
        self.assertEqual(preview_stats(SimpleNamespace(stats={}))['calls'], 0)
        stats = SimpleNamespace(stats={
            (str(ROOT / 'analysis/boxing_chain_pool_candidate.py'), 14, 'boxing_pool'): (3,3,.1,.3,{}),
            (str(ROOT / 'fight_engine.py'), 14, 'boxing_pool'): (90,90,9,9,{})})
        self.assertEqual(preview_stats(stats)['cumulative_seconds'], .3)
        self.assertEqual(preview_stats(stats)['calls'], 3)

    def test_real_muay_thai_authored_priority_suppresses_false_boxing_opportunity(self):
        fixture_row = fixture_schedule(3)[2]
        spec = fixture_row['spec']
        a = synthetic_fighter(fixture_row['a_name'], spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
        b = synthetic_fighter(fixture_row['b_name'], spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
        a.stance, b.stance = spec.get('a_stance', a.stance), spec.get('b_stance', b.stance)
        original, blocked = pool_candidate.boxing_pool, []
        def observe(engine, actor, opponent, state, action):
            result = original(engine, actor, opponent, state, action)
            if not result[0].intersection(result[1]):
                blocked.append((state['round'], state['tick'], action, result))
            return result
        with candidate_context(entries=True, chains=True, draft_content=True, gift_wrap_mount=True, boxing_chain_pool=True):
            control, observed = TerminalRngHarness(), TerminalRngHarness()
            actual = run_audited_fight(control, a, b, fixture_row['seed'], spec['fight'])
            with patch.object(pool_candidate, 'boxing_pool', observe):
                measured = run_audited_fight(observed, a, b, fixture_row['seed'], spec['fight'])
        self.assertEqual(actual, measured)
        self.assertEqual(control.terminal_rng_states, observed.terminal_rng_states)
        self.assertIn((1,18,'power_punch',(frozenset({'muay_thai_teep_cross_elbow_knee'}),
                                         frozenset({'one_two'}))), blocked)

    def test_preview_matches_real_selector_pool_on_same_state(self):
        for tick in (2, 3):
            for action, branch in (('jab', 'single_jab'), ('power_punch', 'one_two')):
                for counter, body in ((None, 0), (None, 1), ({'fighter': 'a'}, 0), ({'fighter': 'a'}, 1)):
                    state = deepcopy(self.state)
                    state.update(tick=tick, last_exchange_counter=bool(counter), counter_window=counter)
                    state['move_chains']['a']['branch_options'] = [branch]
                    before, rng = deepcopy(state), random.getstate()
                    original = self.engine._select_from_pool
                    captured = []
                    def observe(rows, active_counter, signatures, chains, chain, *args):
                        captured.append(final_selection_pool(rows, active_counter, signatures, chains, chain, expanded=True)[0])
                        return original(rows, active_counter, signatures, chains, chain, *args)
                    with patch.object(self.engine, 'punch_target_shares', return_value={'body': body, 'head': 1-body}), \
                         patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('extra draw')):
                        actual, _ = boxing_pool(self.engine, self.a, self.b, state, action)
                        with patch.object(self.engine, '_select_from_pool', observe):
                            self.engine.select_exchange_move(self.a, self.b, action, 'range', 'body' if body else 'head', state)
                    self.assertEqual(actual, frozenset(captured[0]))
                    self.assertEqual(state, before)
                    self.assertEqual(random.getstate(), rng)

    def test_authored_counter_and_low_rank_pools_keep_selector_gates(self):
        root = MOVE_REGISTRY['single_jab']
        definitions = [replace(root, move_id=str(i), tags=()) for i in range(10)]
        self.state['move_chains']['a']['branch_options'] = ['9']
        with patch.object(self.engine, '_move_candidates', return_value=(definitions, ('Boxer',), 'id', 'a', False)), \
             patch.object(self.engine, '_move_static_score', side_effect=lambda f,d,*a: (100-int(d.move_id)*2,0,0,0,d.tags)), \
             patch.object(self.engine, '_move_contextual_score', return_value=(0, ())), \
             patch.object(self.engine, '_move_rarity_gate', return_value=True), \
             patch('analysis.boxing_chain_pool_candidate.zlib.crc32', return_value=1000):
            pool, successors = boxing_pool(self.engine, self.a, self.b, self.state, 'jab')
            self.assertEqual(pool, frozenset(map(str, range(5))))
            self.assertEqual(successors, frozenset({'9'}))
            self.a.signature_moves = ['0']
            self.state['move_chains']['a']['branch_options'] = ['1']
            self.assertEqual(boxing_pool(self.engine, self.a, self.b, self.state, 'jab')[0], frozenset({'0'}))
            self.a.signature_moves = []
            definitions[2] = replace(definitions[2], tags=('counter',))
            with patch.object(self.engine, '_move_candidates', return_value=(definitions, ('Boxer',), 'id', 'a', True)):
                self.assertEqual(boxing_pool(self.engine, self.a, self.b, self.state, 'jab')[0], frozenset({'2'}))

    def test_no_live_bonus_does_not_inspect_pool_or_rescue_expired_chain(self):
        self.state['move_chains']['a']['tick'] = -4
        with boxing_chain_pool_trial(True), \
             patch('analysis.boxing_chain_pool_candidate.boxing_pool', side_effect=AssertionError('expired preview')):
            self.assertIs(self.engine._chain_action_weights(self.a, self.b, self.state, self.weights, 1, 2), self.weights)

    def test_blocked_pool_suppresses_only_boxing_demand_not_actions(self):
        before = deepcopy(self.state)
        with patch.object(self.engine, '_chain_action_bonuses', return_value={'jab': 1, 'kick': 1}) as preview:
            with boxing_chain_pool_trial(True), \
                 patch('analysis.boxing_chain_pool_candidate.boxing_pool', return_value=(frozenset({'other'}), frozenset({'single_jab'}))):
                result = self.engine._chain_action_weights(self.a, self.b, self.state, self.weights, 1, 2)
            self.assertEqual(preview.call_count, 1)
        with patch.object(self.engine, '_chain_action_bonuses', return_value={'kick': 1}):
            expected = self.engine._chain_action_weights(self.a, self.b, self.state, self.weights, 1, 2)
        self.assertEqual(result, expected)
        self.assertEqual(list(result), list(self.weights))
        self.assertEqual(sum(result.values()), sum(self.weights.values()))
        self.assertTrue(all(value >= 1 for value in result.values()))
        self.assertEqual(self.state, before)

    def test_admitted_pool_and_initiative_preview_unchanged(self):
        expected = self.engine._chain_action_weights(self.a, self.b, self.state, self.weights, 1, 2)
        base_preview = self.engine._chain_action_bonuses(self.a, self.b, self.state, self.weights, 1, 2)
        with boxing_chain_pool_trial(True), \
             patch('analysis.boxing_chain_pool_candidate.boxing_pool', return_value=(frozenset({'single_jab'}), frozenset({'single_jab'}))):
            self.assertEqual(self.engine._chain_action_weights(self.a, self.b, self.state, self.weights, 1, 2), expected)
            self.assertEqual(self.engine._chain_action_bonuses(self.a, self.b, self.state, self.weights, 1, 2), base_preview)

    def test_nested_error_cleanup_and_normal_bout_parity(self):
        original, rng = FightAuditHarness._chain_action_weights, random.getstate()
        with boxing_chain_pool_trial(True):
            once = FightAuditHarness._chain_action_weights
            with self.assertRaisesRegex(RuntimeError, 'failure'):
                with boxing_chain_pool_trial(True):
                    self.assertIs(FightAuditHarness._chain_action_weights, once)
                    with patch('analysis.boxing_chain_pool_candidate.boxing_pool', side_effect=RuntimeError('failure')):
                        self.engine._chain_action_weights(self.a, self.b, self.state, self.weights, 1, 2)
            self.assertNotIn('_chain_action_bonuses', self.engine.__dict__)
        self.assertIs(FightAuditHarness._chain_action_weights, original)
        self.assertEqual(random.getstate(), rng)
        self.engine._experimental_chain_action_weighting = False
        baseline = run_audited_fight(self.engine, self.a, self.b, 913007, {'rounds': 3})
        with boxing_chain_pool_trial(True):
            self.assertEqual(run_audited_fight(self.engine, self.a, self.b, 913007, {'rounds': 3}), baseline)

    def test_cli_cannot_shorten_calibration_and_context_rejects_combined_tuning(self):
        for options in ({}, {'chains': True, 'jab_readaptation': True}, {'chains': True, 'stronger_continuation': True}):
            with self.assertRaisesRegex(ValueError, 'Boxing pool trial requires'):
                with candidate_context(boxing_chain_pool=True, **options):
                    self.fail('Invalid combination accepted')
        with patch('sys.argv', ['candidate', '--boxing-chain-pool', '--gift-wrap-mount', '--fights', '1']), \
             patch.object(evaluator, 'calibration_trial', return_value={'failures': ['failed']}) as full, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(evaluator.main(), 1)
        full.assert_called_once_with(boxing_chain_pool=True, gift_wrap_mount=True)

    def test_incompatible_nested_contexts_rejected_in_both_orders(self):
        for policy in ('stronger_continuation', 'continuation_commitment', 'repertoire_readaptation', 'jab_readaptation'):
            for outer, inner in (({policy: True}, {'boxing_chain_pool': True}),
                                 ({'boxing_chain_pool': True}, {policy: True})):
                original, rng = FightAuditHarness._chain_action_weights, random.getstate()
                with candidate_context(chains=True, **outer):
                    with self.assertRaisesRegex(ValueError, 'nested tuning'):
                        with candidate_context(chains=True, **inner):
                            self.fail('Nested tuning accepted')
                self.assertIs(FightAuditHarness._chain_action_weights, original)
                self.assertEqual(random.getstate(), rng)


if __name__ == '__main__':
    unittest.main()
