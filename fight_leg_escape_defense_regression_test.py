"""Knee-line retention contests use specialist skills only in the candidate."""
from copy import deepcopy
import random
import pickle
import unittest
from unittest.mock import patch

from fight_engine_audit import run_audited_fight
import fight_top_leg_entry_regression_test as fixture


class LegEscapeDefenseTests(unittest.TestCase):
    setUp = fixture.TopLegEntryTests.setUp

    def state(self, slot='a', position='leg entanglement'):
        state = deepcopy(self.initial)
        state.update(position=position, top=slot, bottom='b' if slot == 'a' else 'a')
        return state

    def test_leg_skill_direction_both_slots_without_state_or_rng_changes(self):
        for slot, fighter in (('a', self.a), ('b', self.b)):
            state = self.state(slot)
            rng = random.getstate()
            fighter.detailed_skills['leg_locks'] = 45
            low = self.engine.action_defence_value(fighter, 'leg_escape', state)
            fighter.detailed_skills['leg_locks'] = 90
            high = self.engine.action_defence_value(fighter, 'leg_escape', state)
            self.assertAlmostEqual(high - low, 6.75)
            fighter.detailed_skills['get_ups'] = 1
            before = pickle.dumps(state)
            self.assertEqual(self.engine.action_defence_value(fighter, 'leg_escape', state), high)
            self.assertEqual(pickle.dumps(state), before)
            self.assertEqual(random.getstate(), rng)

    def test_equal_skill_baseline_preserves_coefficient_budget(self):
        for slot, fighter in (('a', self.a), ('b', self.b)):
            fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 75)
            fighter.grappling = fighter.wrestling = 75
            state = self.state(slot)
            self.engine._experimental_specialist_entries = False
            legacy = self.engine.action_defence_value(fighter, 'leg_escape', state)
            self.engine._experimental_specialist_entries = True
            self.assertEqual(self.engine.action_defence_value(fighter, 'leg_escape', state), legacy)

    def test_default_position_ownership_and_other_actions_keep_legacy_value(self):
        for slot, fighter in (('a', self.a), ('b', self.b)):
            fighter.detailed_skills['leg_locks'] = 99
            fighter.grappling = 91
            fighter.wrestling = 22
            other = 'b' if slot == 'a' else 'a'
            for action, position, owner in (
                    ('leg_escape', 'guard', slot), ('leg_escape', 'leg entanglement', other),
                    ('leg_control', 'leg entanglement', slot),
                    ('disengage_leg', 'leg entanglement', slot),
                    ('counter_leg_lock', 'leg entanglement', slot)):
                state = self.state(owner, position)
                self.engine._experimental_specialist_entries = False
                legacy = self.engine.action_defence_value(fighter, action, state)
                self.engine._experimental_specialist_entries = True
                self.assertEqual(self.engine.action_defence_value(fighter, action, state), legacy)
            state = self.state(slot)
            self.engine._experimental_specialist_entries = False
            original = self.engine.action_defence_value(fighter, 'leg_escape', state)
            fighter.detailed_skills['leg_locks'] = 1
            self.assertEqual(self.engine.action_defence_value(fighter, 'leg_escape', state), original)

    def test_complete_bout_default_off_parity_and_reachable_escape_path(self):
        self.engine._experimental_specialist_entries = False
        calls = []
        def choose(actor, defender, state, round_no, tick):
            actor_key = self.engine.fight_state_key(actor, state)
            defender_key = self.engine.fight_state_key(defender, state)
            state.update(position='leg entanglement', top=defender_key, bottom=actor_key)
            calls.append((round_no, tick))
            return 'leg_escape'
        with patch.object(self.engine, 'choose_action', side_effect=choose):
            first = run_audited_fight(self.engine, self.a, self.b, 843091, {})
            first_rng = random.getstate()
            del self.engine._experimental_specialist_entries
            second = run_audited_fight(self.engine, self.a, self.b, 843091, {})
            self.assertEqual(random.getstate(), first_rng)
        self.assertTrue(calls)
        self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()
