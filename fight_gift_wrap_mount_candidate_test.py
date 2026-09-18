"""Mount-specific follow-up authoring must retain original back-control branches."""
from dataclasses import replace
import random
import unittest

import fight_moves
from analysis.gift_wrap_control_candidate import ROOT_ID, ORIGINAL
from analysis.gift_wrap_mount_candidate import apply_gift_wrap_mount, MOUNT_REPLACEMENT
from analysis.fight_candidate_context import candidate_context
from analysis.compare_candidate_striking import fixture_schedule
from analysis.generate_variety_opportunity_report import TerminalRngHarness
from fight_engine_audit import synthetic_fighter, run_audited_fight


def bout(index, enabled):
    fixture = fixture_schedule(index + 1)[index]
    spec = fixture['spec']
    a = synthetic_fighter(fixture['a_name'], spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
    b = synthetic_fighter(fixture['b_name'], spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
    a.stance, b.stance = spec.get('a_stance', a.stance), spec.get('b_stance', b.stance)
    with candidate_context(entries=True, chains=True, draft_content=True, gift_wrap_mount=enabled):
        engine = TerminalRngHarness()
        audit = run_audited_fight(engine, a, b, fixture['seed'], spec['fight'])
        return audit, engine.terminal_rng_states


class GiftWrapMountTests(unittest.TestCase):
    def test_single_root_mount_only_edge_and_idempotence(self):
        definitions = fight_moves.MOVE_DEFINITIONS
        result = apply_gift_wrap_mount(definitions)
        self.assertEqual([a.move_id for a,b in zip(definitions,result) if a!=b], [ROOT_ID])
        root = next(d for d in result if d.move_id==ROOT_ID)
        self.assertEqual(root.follow_ups, MOUNT_REPLACEMENT)
        self.assertEqual(root.follow_ups[1:], ORIGINAL[1:])
        self.assertEqual(len(root.follow_ups), 3)
        self.assertEqual(replace(root,follow_ups=ORIGINAL), fight_moves.MOVE_REGISTRY[ROOT_ID])
        self.assertEqual(apply_gift_wrap_mount(result), result)

    def test_missing_duplicate_and_position_drift_rejected(self):
        definitions = fight_moves.MOVE_DEFINITIONS
        invalid = (definitions+definitions[:1], tuple(d for d in definitions if d.move_id!=ROOT_ID),
                   tuple(replace(d,positions=frozenset({'back control'}))
                         if d.move_id=='high_mount_arm_pinch' else d for d in definitions))
        for rows in invalid:
            with self.assertRaises(ValueError):
                apply_gift_wrap_mount(rows)

    def test_context_error_cleanup_and_conflicting_modes(self):
        registry, rng = fight_moves.MOVE_REGISTRY, random.getstate()
        with self.assertRaisesRegex(RuntimeError, 'stop'):
            with candidate_context(entries=True,chains=True,draft_content=True,gift_wrap_mount=True):
                with candidate_context(entries=True,chains=True,draft_content=True,gift_wrap_mount=True):
                    self.assertEqual(fight_moves.MOVE_REGISTRY[ROOT_ID].follow_ups, MOUNT_REPLACEMENT)
                raise RuntimeError('stop')
        self.assertIs(fight_moves.MOVE_REGISTRY, registry)
        self.assertEqual(random.getstate(), rng)
        for args in ({}, {'chains':True,'gift_wrap_control':True}):
            with self.assertRaises(ValueError):
                with candidate_context(gift_wrap_mount=True, **args):
                    pass

    def test_previously_disrupted_back_bout_retains_result(self):
        # Broad hip replacement changed this fixture's submission into a decision.
        plain, plain_rng = bout(21, False)
        refined, refined_rng = bout(21, True)
        self.assertEqual((plain['method'], plain['round']), ('Submission', 3))
        self.assertEqual((refined['method'], refined['round']), ('Submission', 3))
        self.assertEqual(plain['signature'], refined['signature'])
        self.assertEqual(plain_rng, refined_rng)
        self.assertTrue(any(e.get('move_id')=='body_triangle_back_control'
                            and e.get('sequence_source_id')==ROOT_ID for e in refined['trace']))

    def test_real_mount_control_followthrough(self):
        refined, _ = bout(60, True)
        followups = [e for e in refined['trace'] if e.get('move_id')=='high_mount_arm_pinch'
                     and e.get('sequence_source_id')==ROOT_ID]
        self.assertTrue(followups)
        for event in followups:
            self.assertEqual(event['position_before'], 'mount')
            self.assertEqual(event['actor'], event['top_before'])
            self.assertGreaterEqual(event['chain_depth'], 2)


if __name__ == '__main__':
    unittest.main()
