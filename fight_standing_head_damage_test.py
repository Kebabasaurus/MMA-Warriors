from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from analysis.standing_head_damage_candidate import scale_impact, standing_head_damage_trial, patched_resolver
from analysis.generate_variety_opportunity_report import TerminalRngHarness
from fight_engine_audit import FightAuditHarness, synthetic_fighter, run_audited_fight


class StandingHeadDamageTests(unittest.TestCase):
    def test_scope_and_fractional_gain(self):
        for action in ('jab', 'power_punch', 'kick', 'dirty_boxing', 'ground_strikes'):
            for position in ('range', 'pocket', 'clinch', 'guard'):
                for target in ('head', 'high', 'body', 'leg'):
                    state = dict(position=position, last_strike_target=target)
                    expected = (action in {'jab','power_punch','kick'} and position in {'range','pocket'}
                                and target in {'head','high'})
                    self.assertAlmostEqual(scale_impact(1, action, state), 1.02 if expected else 1)

    def test_real_resolver_channels_and_draws(self):
        self.addCleanup(random.setstate, random.getstate())
        a = synthetic_fighter('Damage A', 80, 'Boxer', 'Pressure', 0)
        b = synthetic_fighter('Damage B', 80, 'Wrestler', 'Control', 1)
        engine = FightAuditHarness()
        captured = []
        class Ready(Exception):
            pass
        def capture(actor, defender, state, round_no, tick):
            captured.append(deepcopy(state))
            raise Ready()
        with patch.object(engine, 'choose_action', side_effect=capture):
            with self.assertRaises(Ready):
                engine.simulate_fight(a, b, {})
        for action, target, position, multiplier, margin, roll in (
                ('jab','head','range',1.02,20,.99), ('power_punch','head','pocket',1.02,20,.99),
                ('kick','high','range',1.02,20,.99), ('jab','body','range',1,20,.99),
                ('power_punch','body','pocket',1,20,.99), ('kick','body','range',1,20,.99),
                ('kick','leg','range',1,20,.99), ('ground_strikes','head','mount',1,20,.99),
                ('dirty_boxing','head','clinch',1,20,.99), ('jab','head','range',1.02,20,0),
                ('jab','head','range',1,-50,.99)):
            outcomes = []
            for enabled in (False, True):
                state = deepcopy(captured[0])
                state.update(position=position, top='a' if position=='mount' else None,
                             bottom='b' if position=='mount' else None)
                stats = {key: dict(impact=0, danger=0, control=0) for key in ('a','b')}
                with standing_head_damage_trial(enabled), \
                     patch.object(engine, 'punch_target_shares', return_value={'body':int(target=='body')}), \
                     patch.object(engine, 'kick_target_shares', return_value={k:int(k==target) for k in ('teep','high','body','leg')}), \
                     patch.object(engine, 'weighted_choice', return_value='punch'), \
                     patch.object(engine, 'fight_mechanics_rng') as rng:
                    rng.return_value.random.return_value = roll
                    rng.return_value.randint.return_value = 2
                    engine.resolve_strike(a,b,action,margin,state,stats)
                    outcomes.append((state,stats,list(rng.return_value.mock_calls)))
            old,new = outcomes
            self.assertEqual(old[2],new[2])
            bonus = 8 if roll == 0 else 0
            self.assertAlmostEqual(new[0]['damage']['b'] - bonus, (old[0]['damage']['b'] - bonus) * multiplier)
            self.assertAlmostEqual(new[1]['a']['impact'], old[1]['a']['impact'] * multiplier)
            for key in ('body','leg','gas','stats','knockdowns'):
                self.assertEqual(old[0][key],new[0][key])
            self.assertAlmostEqual(new[0]['head']['b'] - bonus, (old[0]['head']['b'] - bonus) * multiplier)
            self.assertAlmostEqual(new[0]['head_trauma']['b'], old[0]['head_trauma']['b'] * multiplier)

    def test_changed_award_structure_rejected(self):
        with patch('analysis.standing_head_damage_candidate.inspect.getsource', return_value=
                   "def resolve_strike(self):\n    state['damage']['b'] += impact\n"):
            with self.assertRaisesRegex(ValueError, 'exactly two'):
                patched_resolver(FightAuditHarness.resolve_strike)

    def test_nested_errors_restore_and_default_off_bout_parity(self):
        original, rng = FightAuditHarness.resolve_strike, random.getstate()
        with self.assertRaisesRegex(RuntimeError,'stop'):
            with standing_head_damage_trial(True):
                active = FightAuditHarness.resolve_strike
                with standing_head_damage_trial(True):
                    self.assertIs(FightAuditHarness.resolve_strike,active)
                with self.assertRaises(ValueError):
                    with standing_head_damage_trial(False):
                        pass
                random.random()
                raise RuntimeError('stop')
        self.assertIs(FightAuditHarness.resolve_strike, original)
        self.assertEqual(random.getstate(),rng)
        a = synthetic_fighter('Normal A',70,'Boxer','Pressure',0)
        b = synthetic_fighter('Normal B',70,'BJJ','Control',1)
        first = TerminalRngHarness()
        expected = run_audited_fight(first,a,b,81243,{})
        with standing_head_damage_trial(False):
            second = TerminalRngHarness()
            self.assertEqual(run_audited_fight(second,a,b,81243,{}),expected)
            self.assertEqual(first.terminal_rng_states,second.terminal_rng_states)


if __name__ == '__main__':
    unittest.main()
