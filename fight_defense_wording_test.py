"""Defense wording reduces repetition without modifying fight facts or RNG."""
from collections import Counter
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine import FightEngineMixin
from fight_engine_audit import FightAuditHarness, run_audited_fight, synthetic_fighter
from analysis.generate_variety_opportunity_report import TerminalRngHarness


class DefenseWordingTests(unittest.TestCase):
    def test_repeated_defense_facts_get_stable_variety_without_new_facts(self):
        rng = random.getstate()
        for defense in ('high guard', 'slip', 'shin check', 'sprawl', 'submission defense'):
            event = dict(round=1, actor='a', defender='b', move_id='single_jab',
                         outcome='defended', defense_id=defense, position_before='range',
                         position_after='range', defense=dict(name=defense))
            counts = Counter()
            for tick in range(1, 49):
                row = dict(event, tick=tick)
                before = deepcopy(row)
                clause = FightEngineMixin.commentary_defense_clause(row, 'Defender', defense)
                self.assertEqual(clause, FightEngineMixin.commentary_defense_clause(row, 'Defender', defense))
                self.assertEqual(row, before)
                self.assertIn('Defender', clause)
                self.assertIn(defense, clause)
                counts[clause] += 1
            # The former three-phrase pool necessarily repeats a clause >=16 times.
            self.assertLess(max(counts.values()), 10)
        self.assertEqual(random.getstate(), rng)

    def test_complete_bouts_and_all_terminal_streams_match_old_three_phrase_copy(self):
        choose = FightEngineMixin.stable_commentary_choice
        def old_choice(event, channel, values):
            if channel == 'named-defense-clause':
                values = values[:3]
            return choose(event, channel, values)
        saw_different_copy = False
        for seed in (9310000, 9320000, 9330000):
            a = synthetic_fighter('Defense A', 70, 'Boxer', 'Balanced', 0)
            b = synthetic_fighter('Defense B', 70, 'Wrestler', 'Balanced', 1)
            old_engine, new_engine = TerminalRngHarness(), TerminalRngHarness()
            with patch.object(FightEngineMixin, 'stable_commentary_choice', staticmethod(old_choice)):
                old = run_audited_fight(old_engine, a, b, seed, {'rounds': 3})
            new = run_audited_fight(new_engine, a, b, seed, {'rounds': 3})
            self.assertEqual(old_engine.terminal_rng_states, new_engine.terminal_rng_states)
            for previous, current in zip(old['trace'], new['trace']):
                saw_different_copy |= previous.get('commentary') != current.get('commentary')
                previous.pop('commentary', None)
                current.pop('commentary', None)
            self.assertEqual(old, new)
        self.assertTrue(saw_different_copy)


if __name__ == '__main__':
    unittest.main()
