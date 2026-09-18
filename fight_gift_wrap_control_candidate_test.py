"""One successor replacement must not become a global catalogue change."""
from dataclasses import replace
import random
import unittest

import fight_moves
from analysis.fight_candidate_context import candidate_context
from analysis.gift_wrap_control_candidate import apply_gift_wrap_control, ROOT_ID, ORIGINAL, REPLACEMENT
from analysis.compare_candidate_striking import fixture_schedule
from fight_engine_audit import FightAuditHarness, run_audited_fight, synthetic_fighter


class GiftWrapControlTests(unittest.TestCase):
    def test_actual_mount_followthrough_and_control_arm(self):
        fixture = fixture_schedule(61)[60]
        spec = fixture['spec']
        a = synthetic_fighter(fixture['a_name'], spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
        b = synthetic_fighter(fixture['b_name'], spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
        a.stance, b.stance = spec.get('a_stance', a.stance), spec.get('b_stance', b.stance)
        for enabled in (False, True):
            with candidate_context(entries=True, chains=True, draft_content=True, gift_wrap_control=enabled):
                trace = run_audited_fight(FightAuditHarness(), a, b, fixture['seed'], spec['fight'])['trace']
                following = [e for e in trace if e.get('type') == 'exchange'
                             and e.get('sequence_source_id') == ROOT_ID
                             and e.get('move_id') == 'hip_pressure_ride' and e.get('position_before') == 'mount']
                self.assertEqual(bool(following), enabled)
                for event in following:
                    self.assertEqual(event['actor'], event['top_before'])
                    self.assertGreaterEqual(event['chain_depth'], 2)

    def test_exact_single_root_change_and_idempotence(self):
        with candidate_context(entries=True, chains=True, draft_content=True) as definitions:
            candidate = apply_gift_wrap_control(definitions)
            self.assertEqual(len(candidate), 400)
            self.assertEqual([a.move_id for a,b in zip(definitions,candidate) if a!=b], [ROOT_ID])
            old, new = next(d for d in definitions if d.move_id==ROOT_ID), next(d for d in candidate if d.move_id==ROOT_ID)
            self.assertEqual(old.follow_ups, ORIGINAL)
            self.assertEqual(replace(new, follow_ups=ORIGINAL), old)
            self.assertEqual(apply_gift_wrap_control(candidate), candidate)
            replacement = next(d for d in candidate if d.move_id==REPLACEMENT[-1])
            self.assertEqual(replacement.parent_action, 'ground_control')
            self.assertTrue({'mount','back control'} <= replacement.positions)

    def test_context_nested_error_restores_registry_and_rng(self):
        original, rng = fight_moves.MOVE_REGISTRY, random.getstate()
        with self.assertRaisesRegex(RuntimeError, 'stop'):
            with candidate_context(entries=True, chains=True, draft_content=True, gift_wrap_control=True):
                self.assertEqual(fight_moves.MOVE_REGISTRY[ROOT_ID].follow_ups, REPLACEMENT)
                with candidate_context(entries=True, chains=True, draft_content=True, gift_wrap_control=True):
                    self.assertEqual(fight_moves.MOVE_REGISTRY[ROOT_ID].follow_ups, REPLACEMENT)
                raise RuntimeError('stop')
        self.assertIs(fight_moves.MOVE_REGISTRY, original)
        self.assertEqual(random.getstate(), rng)
        self.assertEqual(original[ROOT_ID].follow_ups, ORIGINAL)

    def test_drift_missing_duplicates_and_disabled_chain_rejected(self):
        definitions = fight_moves.MOVE_DEFINITIONS
        for broken in (definitions + definitions[:1], tuple(d for d in definitions if d.move_id==ROOT_ID),
                       tuple(replace(d,follow_ups=()) if d.move_id==ROOT_ID else d for d in definitions)):
            with self.assertRaises(ValueError):
                apply_gift_wrap_control(broken)
        with self.assertRaises(ValueError):
            with candidate_context(gift_wrap_control=True):
                pass


if __name__ == '__main__':
    unittest.main()
