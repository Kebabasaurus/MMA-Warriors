"""Real attacking heel hooks must not depend on a standing counter window."""
from copy import deepcopy
from dataclasses import replace
import random
import unittest
from unittest.mock import patch

import fight_moves
from analysis.fight_candidate_context import candidate_context
from analysis.heel_hook_identity_candidate import apply_heel_hook_identity
from analysis.generate_variety_opportunity_report import TerminalRngHarness
from fight_engine_audit import FightAuditHarness, synthetic_fighter, run_audited_fight


class HeelHookIdentityTests(unittest.TestCase):
    def test_only_action_and_counter_tag_change(self):
        original = fight_moves.MOVE_DEFINITIONS
        fixed = apply_heel_hook_identity(original)
        changed = [(a, b) for a, b in zip(original, fixed) if a != b]
        self.assertEqual(len(changed), 1)
        before, after = changed[0]
        self.assertEqual(after.move_id, 'heel_hook')
        self.assertEqual(after.minimum_skill, 66)
        self.assertEqual(after.parent_action, 'leg_attack')
        self.assertNotIn('counter', after.tags)
        self.assertEqual(replace(after, parent_action=before.parent_action, tags=before.tags), before)
        self.assertEqual(apply_heel_hook_identity(fixed), fixed)
        self.assertEqual(fight_moves.validate_move_registry(fixed), [])
        for invalid in (tuple(m for m in original if m.move_id != 'heel_hook'),
                        original + (before,),
                        tuple(replace(m, positions=frozenset({'guard'})) if m == before else m
                              for m in original)):
            with self.assertRaises(ValueError):
                apply_heel_hook_identity(invalid)

    def test_scoped_restoration_and_default_off_bout_parity(self):
        registry, rng = fight_moves.MOVE_REGISTRY, random.getstate()
        with self.assertRaisesRegex(RuntimeError, 'stop'):
            with candidate_context(entries=True, draft_content=True, heel_hook_identity=True):
                self.assertEqual(fight_moves.MOVE_REGISTRY['heel_hook'].parent_action, 'leg_attack')
                with candidate_context(entries=True, draft_content=True, heel_hook_identity=True):
                    self.assertEqual(fight_moves.MOVE_REGISTRY['heel_hook'].parent_action, 'leg_attack')
                for disabled in ({}, {'entries': True, 'heel_hook_identity': False}):
                    with self.assertRaisesRegex(ValueError, 'nested'):
                        with candidate_context(**disabled):
                            pass
                self.assertEqual(fight_moves.MOVE_REGISTRY['heel_hook'].parent_action, 'leg_attack')
                raise RuntimeError('stop')
        self.assertIs(fight_moves.MOVE_REGISTRY, registry)
        self.assertEqual(random.getstate(), rng)
        with self.assertRaises(ValueError):
            with candidate_context(heel_hook_identity=True):
                pass
        a = synthetic_fighter('Plain A', 70, 'BJJ', 'Control', 0)
        b = synthetic_fighter('Plain B', 70, 'Sambo', 'Control', 1)
        first = TerminalRngHarness()
        expected = run_audited_fight(first, a, b, 8421, {})
        with candidate_context(heel_hook_identity=False):
            second = TerminalRngHarness()
            self.assertEqual(run_audited_fight(second, a, b, 8421, {}), expected)
            self.assertEqual(second.terminal_rng_states, first.terminal_rng_states)

    def test_real_resolver_to_trace_and_skill_boundary(self):
        self.addCleanup(random.setstate, random.getstate())
        with candidate_context(entries=True, chains=True, draft_content=True, heel_hook_identity=True):
            engine = FightAuditHarness()
            a = synthetic_fighter('Heel A', 90, 'BJJ', 'Control', 0)
            b = synthetic_fighter('Heel B', 90, 'Wrestler', 'Control', 1)
            captured = []
            class Ready(Exception):
                pass
            def capture(actor, defender, state, round_no, tick):
                captured.append(deepcopy(state))
                raise Ready()
            with patch.object(engine, 'choose_action', side_effect=capture):
                with self.assertRaises(Ready):
                    engine.simulate_fight(a, b, {})
            state = captured[0]
            state.update(position='leg entanglement', top='a', bottom='b', clinch_controller=None,
                         counter_window={}, last_exchange_counter=False)
            stats = {key: {'impact': 0, 'danger': 0, 'control': 0} for key in ('a', 'b')}
            before = engine.fight_trace_snapshot(a, b, state)
            prior = deepcopy(stats)
            with patch.object(engine, 'action_attack_value', return_value=30), \
                 patch.object(engine, 'action_defence_value', return_value=0), \
                 patch.object(engine, 'fight_mechanics_rng') as rng:
                rng.return_value.randint.return_value = 0
                rng.return_value.choice.side_effect = lambda tickets: next(t for t in tickets if t[0] == 'heel hook')
                rng.return_value.random.return_value = 0
                text = engine.resolve_exchange(a, b, 'leg_attack', state, stats)
                rng.return_value.choice.assert_called_once()
                rng.return_value.random.assert_called_once()
            event = engine.record_fight_trace_exchange(a, b, a, b, 'leg_attack', text,
                                                      before, prior, state, stats)
            self.assertEqual(event['submission_technique']['name'], 'heel hook')
            self.assertEqual(event['move_id'], 'heel_hook')
            for name in ('inside heel hook', 'outside heel hook', 'kneebar'):
                payload = engine.select_exchange_move(a, b, 'leg_attack', 'leg entanglement', '', state,
                                                      resolved_technique={'name': name})
                self.assertNotEqual(payload['move_id'], 'heel_hook')
            engine._fight_move_score_cache = None
            for skill, expected in ((65.99, False), (66, True)):
                with patch.object(engine, 'ds', return_value=skill):
                    payload = engine.select_exchange_move(a, b, 'leg_attack', 'leg entanglement', '', state,
                                                          resolved_technique={'name': 'heel hook'})
                self.assertEqual(payload['move_id'] == 'heel_hook', expected)
            counter_ids = {m.move_id for m in engine._move_candidates(b, 'counter_leg_lock',
                           'leg entanglement', '', state)[0]}
            self.assertNotIn('heel_hook', counter_ids)
            self.assertTrue({'inside_leg_pummel_counter', 'heel_hide_counter_grip'} <= counter_ids)


if __name__ == '__main__':
    unittest.main()
