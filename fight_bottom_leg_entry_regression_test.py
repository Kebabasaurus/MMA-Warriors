"""Bottom-guard knee-line entries are positional intent, never credited sweeps."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter, run_audited_fight


class BottomLegEntryTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.engine._experimental_specialist_entries = True
        self.a = synthetic_fighter('Red', 75, 'BJJ', 'Control', 0)
        self.b = synthetic_fighter('Blue', 75, 'Wrestler', 'Control', 1)
        self.addCleanup(random.setstate, random.getstate())
        for fighter in (self.a, self.b):
            fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 60)
            for key in ('leg_locks', 'scrambles', 'flexibility'):
                fighter.detailed_skills[key] = 75
        class Ready(Exception):
            pass
        captured = []
        def capture(actor, defender, state, round_no, tick):
            captured.append(state)
            raise Ready()
        with patch.object(self.engine, 'choose_action', side_effect=capture):
            with self.assertRaises(Ready):
                self.engine.simulate_fight(self.a, self.b, {})
        self.initial = captured[0]

    def resolve(self, slot='a', margin=9):
        actor, defender = (self.a, self.b) if slot == 'a' else (self.b, self.a)
        other = 'b' if slot == 'a' else 'a'
        state = dict(deepcopy(self.initial), position='guard', top=other, bottom=slot)
        stats = {k: {'impact': 0, 'danger': 0, 'control': 0} for k in ('a', 'b')}
        before = self.engine.fight_trace_snapshot(self.a, self.b, state)
        prior = deepcopy(stats)
        with patch.object(self.engine, 'action_attack_value', return_value=margin), \
             patch.object(self.engine, 'action_defence_value', return_value=0), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.randint.return_value = 0
            text = self.engine.resolve_exchange(actor, defender, 'sweep', state, stats)
            rng.return_value.randint.assert_called_once_with(-18, 18)
            rng.return_value.random.assert_not_called()
            rng.return_value.choice.assert_not_called()
        event = self.engine.record_fight_trace_exchange(self.a, self.b, actor, defender,
            'sweep', text, before, prior, state, stats)
        return actor, defender, state, stats, before, event

    def test_threshold_credit_and_trace_both_slots(self):
        for slot in ('a', 'b'):
            other = 'b' if slot == 'a' else 'a'
            for margin, success in ((8, False), (8.001, True), (9, True)):
                actor, defender, state, stats, before, event = self.resolve(slot, margin)
                fact = state['last_bottom_leg_entry']
                self.assertEqual(fact, dict(source='bottom_guard_sweep_intent', actor=slot,
                    controller=slot if success else None, position_before='guard',
                    position_after='leg entanglement' if success else 'guard',
                    round=state['round'], tick=state['tick'], success=success,
                    intent_edge=15, entry_margin=margin + 2))
                self.assertEqual((state['top'], state['bottom']), (slot, other) if success else (other, slot))
                self.assertEqual(stats[slot], {'impact': 0, 'danger': 0, 'control': 0})
                self.assertEqual(stats[other]['control'], 0 if success else 1)
                self.assertEqual(state['stats'], before['stats'])
                self.assertEqual(event['bottom_leg_entry'], fact)
                self.assertEqual(event['move_id'], 'generic_bottom_leg_entry')
                self.assertEqual(event['move']['parent_action'], 'sweep')
                self.assertFalse(event['move']['signature'])
                self.assertFalse(event['move_sequence']['completed_follow_up'])
                self.assertFalse(event['move']['sequence_source_id'])
                self.assertEqual(event['outcome'], 'position_change' if success else 'defended')
                for technical in (False, True):
                    rendered = self.engine.render_exchange_trace_event(event, technical=technical)
                    self.assertIn('knee', rendered)
                    self.assertNotIn('sweep', rendered)
                    self.assertIn('neither fighter has physical top control' if success else 'remains underneath', rendered)

    def test_intent_scope_ties_and_skill_threshold(self):
        for slot, actor in (('a', self.a), ('b', self.b)):
            other = 'b' if slot == 'a' else 'a'
            state = dict(self.initial, position='guard', top=other, bottom=slot)
            self.assertEqual(self.engine._bottom_leg_entry_intent(actor, 'sweep', state), 15)
            for position in ('half guard', 'mount', 'back control', 'side control', 'leg entanglement'):
                self.assertIsNone(self.engine._bottom_leg_entry_intent(actor, 'sweep', dict(state, position=position)))
            self.assertIsNone(self.engine._bottom_leg_entry_intent(actor, 'submission', state))
            self.assertIsNone(self.engine._bottom_leg_entry_intent(actor, 'sweep', dict(state, top=slot, bottom=other)))
            actor.detailed_skills['leg_locks'] = 61
            self.assertIsNone(self.engine._bottom_leg_entry_intent(actor, 'sweep', state))
            actor.detailed_skills['leg_locks'] = 62
            self.assertGreater(self.engine._bottom_leg_entry_intent(actor, 'sweep', state), 0)
            actor.detailed_skills = dict.fromkeys(actor.detailed_skills, 75)
            self.assertIsNone(self.engine._bottom_leg_entry_intent(actor, 'sweep', state))
            actor.detailed_skills['strength'] = 90
            self.assertIsNone(self.engine._bottom_leg_entry_intent(actor, 'sweep', state))

    def test_coverage_rejects_missing_or_false_entry_credit(self):
        from analysis.generate_move_coverage_report import bottom_leg_entry_observation
        for slot in ('a', 'b'):
            for margin, expected in ((8, 'denied'), (9, 'entered')):
                event = self.resolve(slot, margin)[-1]
                self.assertEqual(bottom_leg_entry_observation(event), expected)
                for key, value in (('td_delta', 1), ('td_att_delta', 1),
                                   ('sub_att_delta', 1), ('move_mastery', 1)):
                    bad = deepcopy(event)
                    bad[key] = value
                    self.assertEqual(bottom_leg_entry_observation(bad), 'invalid')
                bad = deepcopy(event)
                bad['round_metric_delta'][slot]['control'] = 4
                self.assertEqual(bottom_leg_entry_observation(bad), 'invalid')
                bad = deepcopy(event)
                bad['bottom_leg_entry']['intent_edge'] = float('nan')
                self.assertEqual(bottom_leg_entry_observation(bad), 'invalid')
                if expected == 'entered':
                    bad = deepcopy(event)
                    del bad['bottom_leg_entry']
                    self.assertEqual(bottom_leg_entry_observation(bad), 'invalid')

    def test_default_off_and_conventional_tie_keep_sweep(self):
        for disabled in (True, False):
            self.engine._experimental_specialist_entries = not disabled
            if not disabled:
                self.a.detailed_skills = dict.fromkeys(self.a.detailed_skills, 75)
            _, _, state, stats, _, event = self.resolve(margin=11)
            self.assertNotIn('last_bottom_leg_entry', state)
            self.assertEqual((state['position'], state['top']), ('guard', 'a'))
            self.assertEqual(stats['a']['control'], 4)

    def test_fact_expires_next_exchange(self):
        actor, defender, state, stats, *_ = self.resolve()
        with patch.object(self.engine, '_resolve_exchange_action', return_value='Defense.'):
            self.engine.resolve_exchange(defender, actor, 'survive', state, stats)
        self.assertNotIn('last_bottom_leg_entry', state)

    def test_horns_clear_fact_in_real_round_loop(self):
        rounds = []
        def choose(actor, defender, state, round_no, tick):
            if tick == 1:
                self.assertNotIn('last_bottom_leg_entry', state)
                self.assertEqual(state['position'], 'range')
                rounds.append(round_no)
            self.engine.set_fight_position(state, 'guard',
                top=self.engine.fight_state_key(defender, state), bottom=self.engine.fight_state_key(actor, state))
            return 'sweep'
        with patch.object(self.engine, 'choose_action', side_effect=choose), \
             patch.object(self.engine, 'action_attack_value', return_value=100), \
             patch.object(self.engine, 'action_defence_value', return_value=0):
            self.engine.simulate_fight(self.a, self.b, {})
        self.assertEqual(rounds, [1, 2, 3])

    def test_default_off_full_bout_parity(self):
        self.engine._experimental_specialist_entries = False
        normal = run_audited_fight(self.engine, self.a, self.b, 81231, {})
        normal_rng = random.getstate()
        with patch.object(self.engine, '_bottom_leg_entry_intent', return_value=None):
            baseline = run_audited_fight(self.engine, self.a, self.b, 81231, {})
        self.assertEqual(normal, baseline)
        self.assertEqual(random.getstate(), normal_rng)


if __name__ == '__main__':
    unittest.main()
