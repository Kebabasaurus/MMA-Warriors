"""Candidate counter windows must retain authored fallback when no counter is eligible."""
from copy import deepcopy
from dataclasses import replace
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import run_audited_fight
from fight_moves import MOVE_REGISTRY
from fight_moves.schema import COUNTER_TAG
import fight_bottom_leg_entry_regression_test as entry_fixture


class CounterFallbackTests(unittest.TestCase):
    def setUp(self):
        entry_fixture.BottomLegEntryTests.setUp(self)
        self.engine._experimental_chain_action_weighting = True
        self.a.detailed_skills = dict.fromkeys(self.a.detailed_skills, 85)
        self.combo = MOVE_REGISTRY['bjj_arm_drag_back_take_chain']
        self.counter = replace(self.combo, move_id='audit_counter_transition',
                               tags=('ground', 'transition', COUNTER_TAG), minimum_skill=50)
        self.state = dict(deepcopy(self.initial), position='guard', top='a', bottom='b',
                          round=1, tick=2, last_exchange_counter=True,
                          counter_window={'fighter': 'a', 'created_round': 1, 'created_tick': 1})
        self.state['move_chains'] = {'a': dict(round=1, tick=1, branch_options=[self.combo.move_id]), 'b': {}}

    def select(self, rows, state=None):
        return self.engine.select_exchange_move(self.a, self.b, 'advance_position', 'guard', '',
                                                self.state if state is None else state)

    def test_empty_counter_lane_preserves_authored_combination(self):
        with patch('fight_engine.legal_moves', return_value=(self.combo,)):
            self.assertEqual(self.select((self.combo,))['move_id'], self.combo.move_id)

    def test_counter_skill_and_rarity_failures_allow_fallback(self):
        for rejected in ('skill', 'rarity'):
            counter = replace(self.counter, minimum_skill=99 if rejected == 'skill' else 50)
            with patch('fight_engine.legal_moves', return_value=(self.combo, counter)), \
                 patch.object(self.engine, '_move_rarity_gate', side_effect=lambda actor, tags, *args:
                              not (rejected == 'rarity' and COUNTER_TAG in tags)):
                self.assertEqual(self.select((self.combo, counter))['move_id'], self.combo.move_id)

    def test_eligible_counter_keeps_priority_and_wrong_style_stays_excluded(self):
        with patch('fight_engine.legal_moves', return_value=(self.combo, self.counter)), \
             patch.object(self.engine, '_move_rarity_gate', return_value=True):
            self.assertEqual(self.select((self.combo, self.counter))['move_id'], self.counter.move_id)
        wrong_style = replace(self.combo, preferred_styles=('Boxer',))
        with patch('fight_engine.legal_moves', return_value=(wrong_style,)):
            self.assertEqual(self.select((wrong_style,))['move_id'], 'generic_advance_position')

    def test_preview_and_final_agree_for_eligible_and_ineligible_counter(self):
        for mode in ('missing', 'skill', 'rarity', 'eligible'):
            counter = replace(self.counter, minimum_skill=99 if mode == 'skill' else 50)
            rows = (self.combo,) if mode == 'missing' else (self.combo, counter)
            with patch('fight_engine.legal_moves', return_value=rows), \
                 patch.object(self.engine, '_move_rarity_gate', side_effect=lambda actor, tags, *args:
                              not (mode == 'rarity' and COUNTER_TAG in tags)):
                preview = self.engine._chain_action_bonuses(self.a, self.b, self.state,
                                                          {'advance_position': 80}, 1, 2)
                payload = self.select(rows)
            if mode == 'eligible':
                self.assertNotIn('advance_position', preview)
                self.assertEqual(payload['move_id'], counter.move_id)
            else:
                self.assertGreater(preview.get('advance_position', 0), 0)
                self.assertEqual(payload['move_id'], self.combo.move_id)
                self.assertEqual(payload['sequence_step'], 2)

    def test_default_off_full_bout_parity_and_legacy_filter(self):
        self.engine._experimental_chain_action_weighting = False
        self.engine._experimental_specialist_entries = False
        with patch('fight_engine.legal_moves', return_value=(self.combo,)):
            self.assertEqual(self.select((self.combo,))['move_id'], 'generic_advance_position')
        control = run_audited_fight(self.engine, self.a, self.b, 76323, {})
        rng = random.getstate()
        original = self.engine._move_candidates
        def legacy(*args, **kwargs):
            rows, styles, identity, key, active = original(*args, **kwargs)
            if active:
                rows = [row for row in rows if 'style-combination' not in row.tags or COUNTER_TAG in row.tags]
            return rows, styles, identity, key, active
        with patch.object(self.engine, '_move_candidates', side_effect=legacy):
            expected = run_audited_fight(self.engine, self.a, self.b, 76323, {})
        self.assertEqual(control, expected)
        self.assertEqual(random.getstate(), rng)


if __name__ == '__main__':
    unittest.main()
