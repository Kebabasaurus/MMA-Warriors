from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from analysis.kick_power_candidate import scale_kick_power, kick_power_trial, patched_resolver
from analysis.generate_variety_opportunity_report import TerminalRngHarness
from fight_engine_audit import FightAuditHarness, synthetic_fighter, run_audited_fight


class KickPowerTests(unittest.TestCase):
    def test_scope(self):
        self.assertEqual(scale_kick_power(100, 'kick'), 101)
        self.assertEqual(scale_kick_power(100, 'jab'), 100)
        self.assertEqual(scale_kick_power(100, 'dirty_boxing'), 100)

    def test_resolver_structure_is_fail_closed(self):
        with patch('analysis.kick_power_candidate.inspect.getsource', return_value='def resolve_strike(self):\n    pass\n'):
            with self.assertRaisesRegex(ValueError, 'one kick-margin'):
                patched_resolver(FightAuditHarness.resolve_strike)

    def test_draw_parity_nested_restore_and_normal_parity(self):
        original, rng = FightAuditHarness.resolve_strike, random.getstate()
        with self.assertRaisesRegex(RuntimeError, 'stop'):
            with kick_power_trial(True):
                active = FightAuditHarness.resolve_strike
                with kick_power_trial(True):
                    self.assertIs(FightAuditHarness.resolve_strike, active)
                with self.assertRaises(ValueError):
                    with kick_power_trial(False):
                        pass
                raise RuntimeError('stop')
        self.assertIs(FightAuditHarness.resolve_strike, original)
        self.assertEqual(random.getstate(), rng)
        a = synthetic_fighter('Kick A', 75, 'Kickboxer', 'Pressure', 0)
        b = synthetic_fighter('Kick B', 75, 'Wrestler', 'Control', 1)
        first = TerminalRngHarness(); expected = run_audited_fight(first, a, b, 81244, {})
        with kick_power_trial(False):
            second = TerminalRngHarness(); self.assertEqual(run_audited_fight(second, a, b, 81244, {}), expected)
            self.assertEqual(first.terminal_rng_states, second.terminal_rng_states)


if __name__ == '__main__':
    unittest.main()
