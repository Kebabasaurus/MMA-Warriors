"""Conservative old-helper reconstruction for whole-bout wording benchmarks."""
import unittest
from unittest.mock import patch

from analysis import benchmark_defense_wording as benchmark


class DefenseWordingBenchmarkTests(unittest.TestCase):
    def test_old_helper_returns_exact_first_three_options(self):
        old, fingerprint = benchmark.old_helper()
        self.assertEqual(len(fingerprint), 64)
        engine = benchmark.fight_engine.FightEngineMixin
        with patch.object(engine, 'stable_commentary_choice', staticmethod(lambda event, channel, values: values)):
            for defense in ('slip', 'high guard', 'shin check', 'sprawl', 'submission defense'):
                event = {'defense': {'name': defense}}
                legacy = old(event, 'Defender', defense)
                current = engine.commentary_defense_clause(event, 'Defender', defense)
                self.assertEqual(len(legacy), 3)
                self.assertEqual(len(current), 16)
                self.assertEqual(legacy, current[:3])
            self.assertEqual(old({'defense': {'name': 'high guard'}}, 'Defender', 'high guard'), (
                "Defender's disciplined high guard closes the lane",
                'Defender closes the opening with the high guard',
                "Defender's high guard keeps the attack out"))

    def test_reconstruction_rejects_shape_and_count_drift(self):
        for source in ('def helper():\n    options = (1, 2)\n',
                       'def helper():\n    options = [first, *variants]\n',
                       'def helper():\n    return None\n'):
            with patch.object(benchmark.inspect, 'getsource', return_value=source):
                with self.assertRaises(ValueError):
                    benchmark.old_helper()

    def test_actual_pair_preserves_non_commentary_and_rng(self):
        old, fingerprint = benchmark.old_helper()
        a = benchmark.synthetic_fighter('Benchmark A', 70, 'Boxer', 'Balanced', 0)
        b = benchmark.synthetic_fighter('Benchmark B', 70, 'Wrestler', 'Balanced', 1)
        first, second = benchmark.TerminalRngHarness(), benchmark.TerminalRngHarness()
        with patch.object(benchmark.fight_engine.FightEngineMixin, 'commentary_defense_clause', staticmethod(old)):
            previous = benchmark.run_audited_fight(first, a, b, 9310000, {'rounds': 3})
        current = benchmark.run_audited_fight(second, a, b, 9310000, {'rounds': 3})
        for audit in (previous, current):
            for event in audit['trace']:
                event.pop('commentary', None)
        self.assertEqual(previous, current)
        self.assertEqual(first.terminal_rng_states, second.terminal_rng_states)
        self.assertEqual(fingerprint, benchmark.old_helper()[1])


if __name__ == '__main__':
    unittest.main()
