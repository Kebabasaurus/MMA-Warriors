"""Observation never changes a fight, draw budget, or prepared setup."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from analysis.prepared_submission_diagnostics import PreparedSubmissionDiagnosticsMixin, PreparedFightAuditHarness
from analysis.fight_candidate_context import candidate_context
from fight_engine_audit import FightAuditHarness, move_report_specs, run_audited_fight, synthetic_fighter


class FakeBase:
    _experimental_specialist_entries = True
    action = 'submission'
    menus = 1
    apportion_calls = 0
    draws = 0

    def fight_state_key(self, actor, state):
        return actor

    def _valid_scarf_hold_setup(self, actor, action, state):
        setup = state.get('scarf_hold_setup')
        return isinstance(setup, dict) and actor == setup.get('top') and state['tick'] == setup['created_tick'] + 1

    def _valid_von_flue_setup(self, *args):
        return False

    def _prepared_submission_opportunity(self, *args):
        return {'readiness': .5}

    def submission_technique_tickets(self, *args):
        return [('scarf-hold straight armbar', False)] * 2 + [('kimura', False)] * 6

    def _chain_action_weights(self, actor, opponent, state, weights, round_no, tick):
        self.apportion_calls += 1
        return weights

    def choose_action(self, actor, opponent, state, round_no, tick):
        if self.action == 'survive':
            return self.action
        for _ in range(self.menus):
            self._chain_action_weights(actor, opponent, state, {'submission': 2.9, 'control': 6.9}, round_no, tick)
        return self.action

    def submission_technique(self, actor, action, state):
        self.draws += 1
        state.pop('scarf_hold_setup', None)
        return {'name': 'kimura', 'choke': False}

    def simulate_fight(self, state):
        return self.choose_action('a', 'b', state, 1, 4)


class FakeDiagnostics(PreparedSubmissionDiagnosticsMixin, FakeBase):
    pass


class FinalRNG:
    def finalize_fight_result(self, *args, **kwargs):
        result = super().finalize_fight_result(*args, **kwargs)
        self.terminal_rng = tuple(getattr(self, name)().getstate() for name in
            ('fight_mechanics_rng', 'fight_officiating_rng', 'fight_judging_rng', 'fight_presentation_rng'))
        return result


class PlainHarness(FinalRNG, FightAuditHarness):
    pass


class ObservedHarness(FinalRNG, PreparedFightAuditHarness):
    pass


class SetupScenario:
    """Arrange side control on alternating beats; resolve the real setup contest."""
    def choose_action(self, actor, opponent, state, round_no, tick):
        if tick % 2:
            state.update(position='side control', top=self.fight_state_key(actor, state),
                         bottom=self.fight_state_key(opponent, state), clinch_controller=None)
            return 'ground_control'
        return super().choose_action(actor, opponent, state, round_no, tick)

    def action_attack_value(self, actor, action, state, *, erratic_roll=None):
        return 100 if action == 'ground_control' else super().action_attack_value(
            actor, action, state, erratic_roll=erratic_roll)


class ScenarioPlain(FinalRNG, SetupScenario, FightAuditHarness):
    pass


class ScenarioObserved(FinalRNG, PreparedSubmissionDiagnosticsMixin, SetupScenario, FightAuditHarness):
    pass


class PreparedDiagnosticsTests(unittest.TestCase):
    def state(self):
        return {'round': 1, 'tick': 4, 'scarf_hold_setup': {
            'top': 'a', 'bottom': 'b', 'position': 'side control', 'round': 1, 'created_tick': 3}}

    def test_exact_bounded_math_duplicate_observations_and_pre_draw_snapshot(self):
        engine, state = FakeDiagnostics(), self.state()
        engine.menus = 1
        before = deepcopy(state)
        self.assertEqual(engine.choose_action('a', 'b', state, 1, 4), 'submission')
        self.assertEqual(engine.apportion_calls, 1)  # No extra apportion by observer.
        self.assertEqual(state, before)
        engine.choose_action('a', 'b', state, 1, 4)  # Same setup never creates another row.
        self.assertEqual(engine.apportion_calls, 2)
        engine.submission_technique('a', 'submission', state)
        self.assertEqual(engine.draws, 1)
        report = engine.prepared_submission_diagnostics()
        self.assertEqual(len(report['observations']), 1)
        row = report['observations'][0]
        self.assertEqual((row['action_probability'], row['prepared_ticket_share'], row['expected_use_probability']), (.25, .25, .0625))
        self.assertEqual((row['draw_prepared_tickets'], row['draw_total_tickets']), (2, 8))
        self.assertEqual(row['selected_technique'], 'kimura')
        self.assertEqual(report['by_setup']['scarf']['conditional_expected_uses'], .0625)
        report['observations'][0]['readiness'] = 999
        self.assertEqual(engine.prepared_submission_diagnostics()['observations'][0]['readiness'], .5)

    def test_duplicate_menus_and_missing_actual_draw_are_visible(self):
        engine = FakeDiagnostics()
        engine.menus = 2
        engine.choose_action('a', 'b', self.state(), 1, 4)
        report = engine.prepared_submission_diagnostics()
        row, summary = report['observations'][0], report['by_setup']['scarf']
        self.assertEqual(row['weight_observations'], 2)
        self.assertEqual(summary['invalid_observations'], 1)
        self.assertEqual(summary['missing_draws'], 1)
        self.assertEqual(summary['prepared_choices'], 0)
        self.assertEqual(summary['conditional_expected_uses'], 0)  # Ambiguous menu excluded, not represented as a valid zero probability.
        self.assertEqual(row['expected_use_probability'], .0625)

    def test_survival_opponent_and_missing_menu_remain_unknown_not_probability_zero(self):
        for action, actor, menus, expected in (('survive', 'a', 1, 'emergency_survival'),
                ('control', 'b', 1, 'opponent_intervention'), ('control', 'a', 0, 'unobserved_menu')):
            engine = FakeDiagnostics()
            engine.action, engine.menus = action, menus
            engine.choose_action(actor, 'b' if actor == 'a' else 'a', self.state(), 1, 4)
            row = engine.prepared_submission_diagnostics()['observations'][0]
            self.assertEqual(row['classification'], expected)
            self.assertIsNone(row['action_probability'])
            self.assertIsNone(row['expected_use_probability'])

    def test_missing_setup_disabled_mode_and_per_bout_reset(self):
        engine = FakeDiagnostics()
        for state in ({'round': 1, 'tick': 4}, {'round': 1, 'tick': 4, 'scarf_hold_setup': []}):
            engine.simulate_fight(state)
            self.assertEqual(engine.prepared_submission_diagnostics()['observations'], [])
        engine.simulate_fight(self.state())
        self.assertEqual(len(engine.prepared_submission_diagnostics()['observations']), 1)
        engine.simulate_fight({'round': 1, 'tick': 4})
        self.assertEqual(engine.prepared_submission_diagnostics()['observations'], [])
        engine._experimental_specialist_entries = False
        engine.simulate_fight(self.state())
        self.assertEqual(engine.prepared_submission_diagnostics()['observations'], [])

    def test_complete_bout_trace_result_and_all_rng_streams_exact(self):
        original_rng = random.getstate()
        self.addCleanup(random.setstate, original_rng)
        for enabled in (False, True):
            plain, observed = PlainHarness(), ObservedHarness()
            for engine in (plain, observed):
                engine._experimental_specialist_entries = enabled
                engine._experimental_chain_action_weighting = enabled
            for index, spec in enumerate(move_report_specs()[:24]):
                a = synthetic_fighter('Audit A', spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
                b = synthetic_fighter('Audit B', spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
                expected = run_audited_fight(plain, a, b, 9710000 + index, deepcopy(spec['fight']))
                actual = run_audited_fight(observed, a, b, 9710000 + index, deepcopy(spec['fight']))
                self.assertEqual(actual, expected)
                self.assertEqual(observed.terminal_rng, plain.terminal_rng)
                self.assertEqual(random.getstate(), original_rng)

    def test_complete_real_setup_scenario_is_observed_with_exact_parity(self):
        original_rng = random.getstate()
        self.addCleanup(random.setstate, original_rng)
        plain, observed = ScenarioPlain(), ScenarioObserved()
        for engine in (plain, observed):
            engine._experimental_specialist_entries = True
            engine._experimental_chain_action_weighting = True
        a = synthetic_fighter('Setup A', 90, 'Judo', 'Control', 0)
        b = synthetic_fighter('Setup B', 90, 'Judo', 'Control', 1)
        for fighter in (a, b):
            fighter.detailed_skills = dict.fromkeys(fighter.detailed_skills, 90)
        expected = run_audited_fight(plain, a, b, 9710011, {})
        actual = run_audited_fight(observed, a, b, 9710011, {})
        self.assertEqual(actual, expected)
        self.assertEqual(observed.terminal_rng, plain.terminal_rng)
        self.assertEqual(random.getstate(), original_rng)
        report = observed.prepared_submission_diagnostics()
        self.assertGreater(len(report['observations']), 0)
        self.assertGreater(report['by_setup']['scarf']['weighted_menus'], 0)
        self.assertGreater(report['by_setup']['scarf']['submission_choices'], 0)
        self.assertEqual(report['by_setup']['scarf']['missing_draws'], 0)
        self.assertEqual(report['by_setup']['scarf']['invalid_observations'], 0)

    def test_known_natural_corpus_setup_has_exact_trace_result_and_rng_parity(self):
        # Pinned natural observation in joint_candidate_counter_fallback_coverage:
        # bout84, style-coverage-9, seed9710001, R1 setup at tick15. The former
        # seed9710000 fixture no longer creates a setup after the candidate edits.
        # This is a pinned regression fixture, not a retry-until-success search.
        original_rng = random.getstate()
        self.addCleanup(random.setstate, original_rng)
        specs = move_report_specs()
        self.assertEqual(len(specs), 44)
        spec = specs[40]
        self.assertEqual(spec['id'], 'style-coverage-9')
        a = synthetic_fighter(f"Move audit {spec['id']} A", spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
        b = synthetic_fighter(f"Move audit {spec['id']} B", spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
        a.stance = spec.get('a_stance', a.stance)
        b.stance = spec.get('b_stance', b.stance)
        plain, observed = PlainHarness(), ObservedHarness()
        with candidate_context(entries=True, chains=True, draft_content=True):
            expected = run_audited_fight(plain, a, b, 9710001, deepcopy(spec['fight']))
            actual = run_audited_fight(observed, a, b, 9710001, deepcopy(spec['fight']))
        self.assertEqual(actual, expected)
        self.assertEqual(observed.terminal_rng, plain.terminal_rng)
        self.assertEqual(random.getstate(), original_rng)
        report = observed.prepared_submission_diagnostics()
        self.assertTrue(report['observations'])
        self.assertTrue(any(row['kind'] == 'scarf' and row['round'] == 1 and row['created_tick'] == 15
                            for row in report['observations']))
        self.assertGreater(report['by_setup']['scarf']['weighted_menus'], 0)
        self.assertEqual(report['by_setup']['scarf']['invalid_observations'], 0)
        self.assertEqual(report['by_setup']['scarf']['missing_draws'], 0)


if __name__ == '__main__':
    unittest.main()
