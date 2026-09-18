"""Explicit mechanical submission evidence governs candidate defense identity."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter, move_report_specs, run_audited_fight
from fight_moves.submission_identity import SUBMISSION_PARENT_ACTIONS
from tools.move_selection_parity import project_audit


class SubmissionDefenseTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.engine._experimental_specialist_entries = True
        self.a = synthetic_fighter('Same Name', 80, 'BJJ', 'Control', 0)
        self.b = synthetic_fighter('Same Name', 80, 'Wrestler', 'Control', 1)
        self.b.move_mastery = {'defense:leg_lock_rotation': 10000}
        self.addCleanup(random.setstate, random.getstate())

    def payload(self, parent='bottom_submission', generic=False):
        return {'move_id': 'generic_bottom_submission' if generic else 'guard_armbar',
                'parent_action': parent, 'generic': generic, 'target': 'submission',
                'tags': ('submission', 'leg-lock'), 'defense_families': ('stack', 'leg escape')}

    def select(self, payload, evidence=None, slot='a', stale='heel hook'):
        other = 'b' if slot == 'a' else 'a'
        state = {'round': 1, 'tick': 2, 'position': 'guard', 'top': other, 'bottom': slot,
                 'fighter_keys': {id(self.a): slot, id(self.b): other},
                 'last_submission_technique': {'name': stale}}
        before, rng = deepcopy(state), random.getstate()
        with patch.object(self.engine, 'fight_mechanics_rng', side_effect=AssertionError('presentation drew mechanics')):
            result = self.engine.select_exchange_defense(self.b, payload, 'guard', state,
                                                         resolved_technique=evidence)
        self.assertEqual(state, before)
        self.assertEqual(random.getstate(), rng)
        return result

    def test_all_submission_parents_nonleg_reject_leg_escape_despite_metadata_and_mastery(self):
        for slot in ('a', 'b'):
            for parent in SUBMISSION_PARENT_ACTIONS:
                for generic in (False, True):
                    for name in ('armbar', 'wrist lock', 'guillotine choke'):
                        result = self.select(self.payload(parent, generic), {'name': name}, slot)
                        self.assertNotIn('leg-lock', result['tags'])

    def test_actual_leg_retains_rotation_for_generic_and_contradictory_named_payload(self):
        for slot in ('a', 'b'):
            for generic in (False, True):
                payload = self.payload(generic=generic)
                payload.update(tags=('submission', 'choke'), defense_families=('submission defense',))
                for name in ('heel hook', 'kneebar', 'figure-four toe hold'):
                    result = self.select(payload, {'name': name}, slot, stale='armbar')
                    self.assertEqual(result['defense_id'], 'leg_lock_rotation')

    def test_missing_evidence_ignores_stale_state_and_default_off_is_unchanged(self):
        payload = self.payload()
        for evidence in (None, {}, {'name': ''}, {'name': None}, 'armbar'):
            self.assertEqual(self.select(payload, evidence, stale='armbar')['defense_id'], 'leg_lock_rotation')
        self.engine._experimental_specialist_entries = False
        self.assertEqual(self.select(payload, {'name': 'armbar'})['defense_id'], 'leg_lock_rotation')

    def test_positional_counter_and_scramble_keep_leg_defenses(self):
        for parent in ('counter_leg_lock', 'leg_escape', 'scramble', 'leg_control'):
            self.assertEqual(self.select(self.payload(parent), {'name': 'armbar'})['defense_id'],
                             'leg_lock_rotation')

    def test_real_resolver_trace_uses_current_technique_for_both_actor_slots(self):
        class Ready(Exception):
            pass
        captured = []
        def capture(actor, defender, state, round_no, tick):
            captured.append(state)
            raise Ready()
        with patch.object(self.engine, 'choose_action', side_effect=capture):
            with self.assertRaises(Ready):
                self.engine.simulate_fight(self.a, self.b, {})
        for actor, defender, slot, other in ((self.a, self.b, 'a', 'b'), (self.b, self.a, 'b', 'a')):
            defender.move_mastery = {'defense:leg_lock_rotation': 10000}
            for actual in ('armbar', 'heel hook'):
                state = deepcopy(captured[0])
                state.update(position='guard', top=other, bottom=slot, clinch_controller=None,
                             last_submission_technique={'name': 'heel hook' if actual == 'armbar' else 'armbar'})
                before = self.engine.fight_trace_snapshot(self.a, self.b, state)
                stats = {k: {'impact': 0, 'danger': 0, 'control': 0} for k in ('a', 'b')}
                prior = deepcopy(stats)
                with patch.object(self.engine, 'action_attack_value', return_value=30), \
                     patch.object(self.engine, 'action_defence_value', return_value=0), \
                     patch.object(self.engine, 'fight_mechanics_rng') as rng:
                    rng.return_value.randint.return_value = 0
                    rng.return_value.choice.side_effect = lambda options: next(row for row in options if row[0] == actual)
                    rng.return_value.random.return_value = 0
                    text = self.engine.resolve_exchange(actor, defender, 'bottom_submission', state, stats)
                    rng.return_value.choice.assert_called_once()
                    rng.return_value.random.assert_called_once()
                with patch('fight_engine.legal_moves', return_value=()):
                    event = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender,
                        'bottom_submission', text, before, prior, state, stats)
                self.assertEqual(event['submission_technique']['name'], actual)
                self.assertTrue(event['move']['generic'])
                self.assertEqual('leg-lock' in event['defense']['tags'], actual == 'heel hook')

    def test_24_complete_candidate_bouts_keep_mechanics_with_old_defense_filter(self):
        selected_defense = self.engine.select_exchange_defense
        def old_filter(defender, payload, position, state, resolved_technique=None):
            # Only disable the new presentation compatibility filter. Keep all
            # specialist mechanics, pools and chain weighting identical.
            return selected_defense(defender, payload, position, state)
        changed = 0
        self.engine._experimental_chain_action_weighting = True
        for index, spec in enumerate(move_report_specs()[:24]):
            a = synthetic_fighter('Defense audit A', spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
            b = synthetic_fighter('Defense audit B', spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
            for fighter in (a, b):
                fighter.move_mastery = {'defense:leg_lock_rotation': 10000}
            seed = 9_970_000 + index
            candidate = run_audited_fight(self.engine, a, b, seed, deepcopy(spec['fight']))
            with patch.object(self.engine, 'select_exchange_defense', side_effect=old_filter):
                old = run_audited_fight(self.engine, a, b, seed, deepcopy(spec['fight']))
            self.assertEqual(project_audit(candidate)['mechanics'], project_audit(old)['mechanics'])
            changed += sum(a.get('defense') != b.get('defense')
                           for a, b in zip(candidate['trace'], old['trace']))
        self.assertGreater(changed, 0, 'Paired corpus must exercise the corrected defense filter')


if __name__ == '__main__':
    unittest.main()
