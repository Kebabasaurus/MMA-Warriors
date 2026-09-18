"""Single-jab copy varies while complete mechanical evidence stays unchanged."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine import FightEngineMixin, SINGLE_JAB_DISPLAY_VARIANTS
from fight_engine_audit import FightAuditHarness, run_audited_fight, synthetic_fighter
from analysis.generate_variety_opportunity_report import TerminalRngHarness
from analysis.generate_fight_commentary_report import causal_trace_event
from fight_engine_audit import matchup_specs
from constants import FIGHT_COMMENTARY_PERSONALITIES, TRAITS


class JabWordingTests(unittest.TestCase):
    def test_actual_tko_fixtures_keep_causal_exchange_jab_label(self):
        # These are the two real failures from the complete 256-bout copy gate.
        camps = ('Audit Boxing Lab', 'Audit Kick Team', 'Audit Wrestling Room',
                 'Audit Jiu-Jitsu House', 'Audit Clinch Club', 'Audit Sambo School')
        for spec_index, seed_index, label in ((9, 6, 'lead jab'), (22, 7, 'lead-hand straight')):
            spec = matchup_specs()[spec_index]
            seed = 9410000 + spec_index * 100 + seed_index
            a = synthetic_fighter(f"Commentary {spec['id']} A", spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
            b = synthetic_fighter(f"Commentary {spec['id']} B", spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
            offset = (spec_index * 8 + seed_index) * 2
            a.trait, b.trait = TRAITS[offset % len(TRAITS)], TRAITS[(offset + 1) % len(TRAITS)]
            a.camp, b.camp = camps[offset % len(camps)], camps[(offset + 1) % len(camps)]
            engine = TerminalRngHarness()
            engine.rules['fight_commentary_personality'] = FIGHT_COMMENTARY_PERSONALITIES[
                (spec_index + seed_index) % len(FIGHT_COMMENTARY_PERSONALITIES)]
            previous_rng = random.getstate()
            try:
                random.seed(seed)
                result = engine.simulate_fight_result(a, b, spec['fight'])
            finally:
                random.setstate(previous_rng)
            self.assertEqual(result.method, 'TKO')
            winner_key = 'a' if result.winner_id == a.fighter_id else 'b'
            causal = causal_trace_event(result.trace, winner_key, result.round_no)
            self.assertEqual(causal['move_id'], 'single_jab')
            self.assertEqual(engine.exchange_display_move(causal), label)
            official = next(line for line in engine._last_fight_result.commentary if 'official result:' in line.casefold())
            self.assertIn(label, official.casefold())

    def test_variants_are_stable_pure_and_keep_identity(self):
        state = random.getstate()
        labels = set()
        for tick in range(1,101):
            event = dict(move_id='single_jab',action='jab',actor='a',round=1,tick=tick,
                         position_before='range',outcome='defended',
                         move=dict(move_id='single_jab',name='single jab',target='head'))
            original = deepcopy(event)
            label = FightEngineMixin.exchange_display_move(event)
            self.assertEqual(label,FightEngineMixin.exchange_display_move(event))
            self.assertEqual(event,original)
            labels.add(label)
        self.assertEqual(labels,set(SINGLE_JAB_DISPLAY_VARIANTS))
        self.assertEqual(random.getstate(),state)

    def test_other_jabs_and_resolved_submissions_keep_their_names(self):
        for move_id in ('double_jab','pawing_jab','up_jab','flicker_jab'):
            event = dict(move_id=move_id,action='jab',move=dict(name='authored jab'))
            self.assertEqual(FightEngineMixin.exchange_display_move(event),'authored jab')
        event = dict(move_id='single_jab',submission_technique=dict(name='guillotine'))
        self.assertEqual(FightEngineMixin.exchange_display_move(event),'guillotine')
        self.assertIn(FightEngineMixin.exchange_display_move({'move':{'move_id':'single_jab'}}),
                      SINGLE_JAB_DISPLAY_VARIANTS)

    def test_complete_bouts_differ_only_in_rendered_commentary(self):
        display = FightEngineMixin.exchange_display_move
        def original_display(event):
            move = event.get('move') or {}
            if ((event.get('move_id') or move.get('move_id')) == 'single_jab'
                    and not (event.get('submission_technique') or {}).get('name')):
                return move.get('name') or 'single jab'
            return display(event)
        saw_jab = False
        for seed in (9310000,9320000):
            a = synthetic_fighter('Wording A',70,'Boxer','Balanced',0)
            b = synthetic_fighter('Wording B',70,'Kickboxer','Balanced',1)
            control,expanded = TerminalRngHarness(),TerminalRngHarness()
            with patch.object(FightAuditHarness,'exchange_display_move',staticmethod(original_display)):
                before = run_audited_fight(control,a,b,seed,{'rounds':3})
            after = run_audited_fight(expanded,a,b,seed,{'rounds':3})
            self.assertEqual(control.terminal_rng_states,expanded.terminal_rng_states)
            self.assertEqual(len(before['trace']),len(after['trace']))
            for old,new in zip(before['trace'],after['trace']):
                saw_jab |= new.get('move_id')=='single_jab'
                old.pop('commentary',None)
                new.pop('commentary',None)
            self.assertEqual(before,after)
        self.assertTrue(saw_jab)


if __name__=='__main__': unittest.main()
