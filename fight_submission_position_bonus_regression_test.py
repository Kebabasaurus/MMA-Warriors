"""Candidate positional bonuses require ownership; legacy calibration stays sealed."""
from collections import defaultdict
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter


class SubmissionPositionBonusTests(unittest.TestCase):
    def setUp(self):
        self.engine = FightAuditHarness()
        self.engine._experimental_specialist_entries = True
        self.a = synthetic_fighter('Same Name', 75, 'BJJ', 'Control', 0)
        self.b = synthetic_fighter('Same Name', 75, 'Wrestler', 'Control', 1)
        self.addCleanup(random.setstate, random.getstate())

    def resolve(self, position, top, *, slot='a', margin=8, skill=95,
                action=None, roll=1, missing_owner=False):
        other = 'b' if slot == 'a' else 'a'
        state = {'position': position, 'top': slot if top else other,
                 'bottom': other if top else slot,
                 'fighter_keys': {id(self.a): slot, id(self.b): other},
                 'stats': {k: defaultdict(int) for k in ('a', 'b')},
                 'gas': {'a': 80, 'b': 80}, 'danger': {'a': 0, 'b': 0}}
        if missing_owner:
            del state['top']
        ownership_before = {key: state.get(key) for key in ('position', 'top', 'bottom')}
        stats = {k: defaultdict(int) for k in ('a', 'b')}
        def ds(fighter, key, fallback=50):
            return skill if key in ('guard_work', 'mount_control', 'back_control') else 50
        with patch.object(self.engine, 'skill_bundle', return_value=55), \
             patch.object(self.engine, 'ds', side_effect=ds), \
             patch.object(self.engine, 'submission_technique', return_value={'name': 'wrist lock', 'choke': False}), \
             patch.object(self.engine, 'submission_finish_text', return_value='Finish.'), \
             patch.object(self.engine, 'fight_phrase', side_effect=lambda category, *_: category), \
             patch.object(self.engine, 'competitive_finish_conversion', return_value=1), \
             patch.object(self.engine, 'fight_mechanics_rng') as rng:
            rng.return_value.random.return_value = roll
            text = self.engine.resolve_submission(self.a, self.b,
                action or ('submission' if top else 'bottom_submission'), margin, state, stats)
            draws = rng.return_value.random.call_count
            rng.return_value.choice.assert_not_called()
        self.assertEqual(state['stats'][slot]['sub_att'], 1)
        self.assertEqual({key: state.get(key) for key in ownership_before}, ownership_before)
        return state, stats, draws, text

    def test_bottom_dominant_positions_no_phantom_danger_or_energy_at_threshold(self):
        for slot in ('a', 'b'):
            other = 'b' if slot == 'a' else 'a'
            for position in ('mount', 'back control', 'side control'):
                for skill in (30, 95):
                    state, stats, draws, _ = self.resolve(position, False, slot=slot, skill=skill, margin=0)
                    self.assertEqual((state['danger'][slot], stats[slot]['danger'], draws), (0, 0, 0))
                    self.assertEqual(state['gas'][other], 80)
                    state, stats, draws, text = self.resolve(position, False, slot=slot, skill=skill)
                    self.assertEqual((state['danger'][slot], stats[slot]['danger'], draws), (0, 5, 0))
                    self.assertEqual(state['gas'][other], 80)
                    self.assertEqual(text, 'submission_threat')
                    state, _, draws, _ = self.resolve(position, False, slot=slot, skill=skill, margin=8.001)
                    self.assertEqual((state['danger'][slot], state['gas'][other], draws), (14, 70, 1))

    def test_top_dominant_bonuses_and_finish_multiplier_match_legacy(self):
        for slot in ('a', 'b'):
            for position, factor in (('mount', 1.2), ('back control', 1.2), ('side control', 1.08)):
                for skill in (30, 95):
                    bonus = 9 + max(0, skill - 55) * (0.2 if position == 'mount' else 0.26 if position == 'back control' else 0)
                    threshold = (0.085 + (20 + bonus) / 240) * factor
                    for roll in (threshold - 0.000001, threshold + 0.000001):
                        candidate = self.resolve(position, True, slot=slot, skill=skill, margin=20, roll=roll)
                        self.engine._experimental_specialist_entries = False
                        legacy = self.resolve(position, True, slot=slot, skill=skill, margin=20, roll=roll)
                        self.engine._experimental_specialist_entries = True
                        self.assertEqual(candidate, legacy)
                        self.assertEqual('submission_finish' in candidate[0], roll < threshold)

    def test_bottom_dominant_finish_uses_neutral_multiplier(self):
        threshold = (0.085 + 20 / 240) * 0.92
        for slot in ('a', 'b'):
            for position in ('mount', 'back control', 'side control'):
                for roll in (threshold - 0.000001, threshold + 0.000001):
                    state, _, draws, _ = self.resolve(position, False, slot=slot, margin=20, roll=roll)
                    self.assertEqual('submission_finish' in state, roll < threshold)
                    self.assertEqual(draws, 1)

    def test_guard_half_base_and_legitimate_bottom_bonus_unchanged(self):
        for slot in ('a', 'b'):
            for position in ('guard', 'half guard'):
                for top in (False, True):
                    for skill in (30, 95):
                        candidate = self.resolve(position, top, slot=slot, skill=skill, margin=0)
                        self.engine._experimental_specialist_entries = False
                        legacy = self.resolve(position, top, slot=slot, skill=skill, margin=0)
                        self.engine._experimental_specialist_entries = True
                        self.assertEqual(candidate, legacy)
                        self.assertEqual(candidate[2], int(not top and skill == 95))

    def test_bottom_guard_work_requires_actual_bottom_guard_half(self):
        for position, top in (('guard', True), ('half guard', True), ('turtle', False),
                              ('leg entanglement', False), ('front headlock', False)):
            state, _, draws, _ = self.resolve(position, top, action='bottom_submission', margin=0)
            self.assertEqual((state['danger']['a'], draws), (0, 0))

    def test_default_off_keeps_legacy_missing_top_and_bottom_bonus(self):
        self.engine._experimental_specialist_entries = False
        for position in ('mount', 'back control', 'side control'):
            state, _, draws, _ = self.resolve(position, False, margin=0, missing_owner=True)
            self.assertEqual((state['danger']['a'], state['gas']['b'], draws), (14, 70, 1))


if __name__ == '__main__':
    unittest.main()
