"""Survival expansion preserves ownership, defaults, streams and scoped bindings."""
import random
import unittest
from analysis.fight_candidate_context import candidate_context
from analysis.survival_expansion_candidate import role_allows, survival_expansion_trial, validate_survival_trace
from fight_moves.catalogue.survival_development import SURVIVAL_DEVELOPMENT, SURVIVAL_ROLES
from analysis.generate_variety_opportunity_report import TerminalRngHarness
from fight_engine_audit import FightAuditHarness, run_audited_fight, synthetic_fighter

class SurvivalExpansionTests(unittest.TestCase):
    def test_roles_cover_both_slots_and_missing_ownership(self):
        for move in SURVIVAL_DEVELOPMENT:
            role = SURVIVAL_ROLES[move.move_id]
            for slot,other in (('a','b'),('b','a')):
                state = dict(top=slot,bottom=other,clinch_controller=slot)
                position = next(iter(move.positions))
                self.assertEqual(role_allows(move.move_id,position,slot,state),role in {'any','top','controller'})
                self.assertEqual(role_allows(move.move_id,position,other,state),role in {'any','bottom','controlled'})
                self.assertEqual(role_allows(move.move_id,position,slot,{}),role=='any')
        self.assertFalse(role_allows('heavy_top_breather','leg entanglement','a',dict(top='a',bottom='b')))
        self.assertFalse(role_allows('bottom_frame_survival','guard','a',dict(top='a',bottom='b')))

    def test_nested_error_restores_bindings_and_rng(self):
        method, rng = FightAuditHarness._move_candidates,random.getstate()
        with survival_expansion_trial(True):
            once = FightAuditHarness._move_candidates
            with survival_expansion_trial(True):
                self.assertIs(FightAuditHarness._move_candidates,once)
            with self.assertRaises(ValueError):
                with survival_expansion_trial(False): pass
            with self.assertRaises(RuntimeError):
                with survival_expansion_trial(True):
                    random.random()
                    raise RuntimeError('test')
        self.assertIs(FightAuditHarness._move_candidates,method)
        self.assertEqual(random.getstate(),rng)

    def test_defaults_and_registry_restore(self):
        import fight_moves
        definitions = fight_moves.MOVE_DEFINITIONS
        a,b = synthetic_fighter('A',65,'Boxer','Balanced',0),synthetic_fighter('B',65,'BJJ','Balanced',1)
        control,actual = TerminalRngHarness(),TerminalRngHarness()
        expected = run_audited_fight(control,a,b,9310000,{'rounds':3})
        with candidate_context(survival_expansion=False):
            observed = run_audited_fight(actual,a,b,9310000,{'rounds':3})
        self.assertEqual(expected,observed)
        self.assertEqual(control.terminal_rng_states,actual.terminal_rng_states)
        with candidate_context(entries=True,chains=True,draft_content=True,survival_expansion=True) as expanded:
            self.assertEqual(len([d for d in expanded if not d.deprecated]),440)
            audit = run_audited_fight(actual,a,b,9310000,{'rounds':3})
            counts = validate_survival_trace(audit['trace'])
            self.assertGreater(counts.get('selected',0),0)
            self.assertEqual(counts.get('invalid',0),0)
        self.assertIs(fight_moves.MOVE_DEFINITIONS,definitions)

    def test_trace_validator_rejects_false_roles_and_actions(self):
        move = next(m for m in SURVIVAL_DEVELOPMENT if SURVIVAL_ROLES[m.move_id]=='bottom')
        event = dict(type='exchange',move_id=move.move_id,action='survive',actor='b',
                     position_before=next(iter(move.positions)),top_before='a',bottom_before='b')
        self.assertEqual(validate_survival_trace([event]),{'selected':1,'invalid':0})
        for change in ({'actor':'a'},{'action':'submission'},{'position_before':'range'}):
            self.assertEqual(validate_survival_trace([dict(event,**change)])['invalid'],1)

    def test_benchmark_preserves_inputs_and_repeat_results(self):
        from analysis.benchmark_survival_expansion import build_report
        report = build_report(fights=2,repeats=2)
        for samples in report['arms'].values():
            self.assertEqual(len({s['audit_sha256'] for s in samples}),1)
        self.assertGreater(report['median_control_cpu_seconds'],0)

    def test_composed_cradle_observer_cannot_hide_survival_validation(self):
        from analysis.generate_move_coverage_report import build_report
        with candidate_context(entries=True,chains=True,draft_content=True,survival_expansion=True,
                               gift_wrap_mount=True,heel_hook_identity=True,hold_transitions=True,
                               cradle_setup=True,standing_head_damage=True,kick_power=True) as definitions:
            report = build_report(4,definitions=definitions)
            selected = sum(report['move_selection_counts'].get(m.move_id,0) for m in SURVIVAL_DEVELOPMENT)
            self.assertGreater(selected,0)
            self.assertEqual(report['survival_expansion_counts']['selected'],selected)
            self.assertEqual(report['survival_expansion_counts']['invalid'],0)
            from analysis.evaluate_joint_fight_candidate import measured_target_failures
            report['survival_expansion_counts'] = {}
            self.assertIn('Survival validation does not reconcile with selected IDs',
                          measured_target_failures(report,definitions,expected_active_moves=440))

if __name__ == '__main__':
    unittest.main()
