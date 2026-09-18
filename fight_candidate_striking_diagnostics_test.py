"""Matched striking diagnostics are observational and use current native facts."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from analysis import compare_candidate_striking as diagnostic


class CandidateStrikingDiagnosticsTests(unittest.TestCase):
    def test_standing_ablation_dispatch_and_nested_exception_restore(self):
        engine = diagnostic.FightAuditHarness()
        original = diagnostic.FightAuditHarness._chain_action_weights
        rng = random.getstate()
        calls = []
        def baseline(self, fighter, opponent, state, weights, round_no, tick):
            calls.append((state['position'], fighter, opponent, round_no, tick))
            return {'original': 3}
        with patch.object(diagnostic.FightAuditHarness, '_chain_action_weights', baseline):
            with diagnostic.standing_chain_ablation(True):
                outer = diagnostic.FightAuditHarness._chain_action_weights
                weights = {'kick': 10, 'jab': 20}
                for position in ('range', 'pocket'):
                    self.assertIs(engine._chain_action_weights('a', 'b', {'position': position}, weights, 2, 4), weights)
                other_positions = ('clinch', 'cage', 'failed shot', 'standing back control', 'front headlock', 'turtle',
                                   'leg entanglement', 'guard', 'half guard', 'side control', 'mount', 'back control')
                for position in other_positions:
                    self.assertEqual(engine._chain_action_weights('a', 'b', {'position': position}, weights, 2, 4), {'original': 3})
                self.assertEqual([call[0] for call in calls], list(other_positions))
                with self.assertRaisesRegex(RuntimeError, 'inner'):
                    with diagnostic.standing_chain_ablation(True):
                        random.random()
                        raise RuntimeError('inner')
                self.assertIs(diagnostic.FightAuditHarness._chain_action_weights, outer)
            self.assertIs(diagnostic.FightAuditHarness._chain_action_weights, baseline)
        self.assertIs(diagnostic.FightAuditHarness._chain_action_weights, original)
        self.assertEqual(random.getstate(), rng)

    def test_ablation_real_control_arm_matches_default_candidate(self):
        rng = random.getstate()
        original = diagnostic.FightAuditHarness._chain_action_weights
        default = diagnostic.build_comparison(4)
        ablation = diagnostic.build_comparison(4, ablate_standing_chains=True)
        self.assertEqual(default['arms']['combined_candidate'], ablation['arms']['combined_candidate'])
        self.assertEqual([r['combined_candidate'] for r in default['paired_bouts']],
                         [r['combined_candidate'] for r in ablation['paired_bouts']])
        self.assertEqual(default['input_sha256'], ablation['input_sha256'])
        self.assertEqual(set(ablation['arms']), {'combined_candidate', 'standing_chain_ablated_candidate'})
        candidate, ablated = ablation['arms'].values()
        self.assertEqual(candidate['registry_sha256'], ablated['registry_sha256'])
        self.assertEqual(ablated['configuration'], dict(specialist_entries=True, chain_action_weighting=True,
                        draft_content=True, bypass_standing_chain_weights=True, pocket_action_bias=True,
                        legacy_failed_shot_retention=False))
        self.assertEqual(random.getstate(), rng)
        self.assertIs(diagnostic.FightAuditHarness._chain_action_weights, original)
        for arm in ablation['arms'].values():
            self.assert_partitions(arm)
        with patch.object(diagnostic, 'build_comparison', return_value={}) as build, redirect_stdout(io.StringIO()):
            diagnostic.main(['--calibration-corpus', '--standing-chain-ablation'])
        build.assert_called_once_with(calibration_corpus=True, ablate_standing_chains=True)

    def test_pocket_bias_ablation_preserves_control_arm_and_cli_dispatch(self):
        default = diagnostic.build_comparison(4)
        ablation = diagnostic.build_comparison(4, ablate_pocket_action_bias=True)
        self.assertEqual(default['arms']['combined_candidate'], ablation['arms']['combined_candidate'])
        self.assertEqual(set(ablation['arms']),
                         {'combined_candidate', 'pocket_action_bias_ablated_candidate'})
        self.assertTrue(ablation['arms']['combined_candidate']['configuration']['pocket_action_bias'])
        self.assertFalse(ablation['arms']['pocket_action_bias_ablated_candidate']['configuration']['pocket_action_bias'])
        with self.assertRaises(ValueError):
            diagnostic.build_comparison(1, ablate_standing_chains=True, ablate_pocket_action_bias=True)
        with patch.object(diagnostic, 'build_comparison', return_value={}) as build, redirect_stdout(io.StringIO()):
            diagnostic.main(['--calibration-corpus', '--pocket-action-bias-ablation'])
        build.assert_called_once_with(calibration_corpus=True, ablate_pocket_action_bias=True)

    def test_failed_shot_ablation_nested_error_restores_class_instance_and_rng(self):
        cls = diagnostic.FightAuditHarness
        original = cls.resolve_takedown
        rng = random.getstate()
        sentinel = object()
        observations = []
        def resolve(engine, actor, defender, margin, state, stats):
            observations.append(engine._experimental_specialist_entries)
            random.random()
            if margin == 'error':
                raise RuntimeError('resolver failed')
            return sentinel
        with patch.object(cls, 'resolve_takedown', resolve), \
             patch.object(cls, '_experimental_specialist_entries', True, create=True):
            for instance_value in ('absent', True, False):
                engine = cls()
                if instance_value != 'absent':
                    engine._experimental_specialist_entries = instance_value
                before = dict(vars(engine))
                with diagnostic.failed_shot_retention_ablation():
                    self.assertIs(cls.resolve_takedown, resolve)
                with diagnostic.failed_shot_retention_ablation(True):
                    outer = cls.resolve_takedown
                    self.assertIs(engine.resolve_takedown(None, None, 0, {}, {}), sentinel)
                    self.assertEqual(vars(engine), before)
                    nested_rng = random.getstate()
                    with self.assertRaisesRegex(RuntimeError, 'resolver failed'):
                        with diagnostic.failed_shot_retention_ablation(True):
                            engine.resolve_takedown(None, None, 'error', {}, {})
                    self.assertIs(cls.resolve_takedown, outer)
                    self.assertEqual(vars(engine), before)
                    self.assertEqual(random.getstate(), nested_rng)
                    self.assertIs(cls._experimental_specialist_entries, True)
                self.assertIs(cls.resolve_takedown, resolve)
                self.assertEqual(vars(engine), before)
                self.assertEqual(random.getstate(), rng)
        self.assertIs(cls.resolve_takedown, original)
        self.assertEqual(observations, [False] * 6)

    def test_failed_shot_ablation_real_resolver_only_changes_retention_both_slots(self):
        rng = random.getstate()
        self.addCleanup(random.setstate, rng)
        engine = diagnostic.FightAuditHarness()
        engine._experimental_specialist_entries = True
        a = diagnostic.synthetic_fighter('Red', 75, 'Wrestler', 'Control', 0)
        b = diagnostic.synthetic_fighter('Blue', 75, 'Wrestler', 'Control', 1)
        captured = []
        class Ready(Exception):
            pass
        def capture(actor, defender, state, round_no, tick):
            captured.append(state)
            raise Ready()
        with patch.object(engine, 'choose_action', side_effect=capture):
            with self.assertRaises(Ready):
                engine.simulate_fight(a, b, {})

        def resolve(slot, position, margin, ablated, setup_owners=None, specialist=True):
            actor, defender = (a, b) if slot == 'a' else (b, a)
            engine._experimental_specialist_entries = specialist
            state = deepcopy(captured[0])
            state['fighters'] = {'a': a, 'b': b}
            state.update(position=position, top=None, bottom=None, clinch_controller=None)
            if setup_owners is not None:
                for key, setup_position in (('von_flue_pending_wrap', 'half guard'),
                                            ('von_flue_setup', 'half guard'),
                                            ('scarf_hold_setup', 'side control')):
                    state[key] = dict(position=setup_position, top=setup_owners[0], bottom=setup_owners[1],
                                      round=1, created_tick=1)
            stats = {key: dict(impact=0, control=0, danger=0) for key in ('a', 'b')}
            mechanics = random.Random(371)
            with patch.object(engine, 'ds', return_value=75), \
                 patch.object(engine, 'ds_avg', return_value=75), \
                 patch.object(engine, 'fight_mechanics_rng', return_value=mechanics), \
                 patch.object(engine, 'fight_phrase', side_effect=lambda category, *args, **kwargs: category), \
                 diagnostic.failed_shot_retention_ablation(ablated):
                result = engine.resolve_takedown(actor, defender, margin, state, stats)
            self.assertEqual(engine._experimental_specialist_entries, specialist)
            self.assertNotIn('set_fight_position', vars(engine))
            return result, state, stats, mechanics.getstate()

        for slot in ('a', 'b'):
            other = 'b' if slot == 'a' else 'a'
            for position in ('range', 'pocket'):
                for margin in (9, 8, 0, -7.99, -8, -17.99):
                    with self.subTest(slot=slot, position=position, margin=margin):
                        control = resolve(slot, position, margin, False)
                        trial = resolve(slot, position, margin, True)
                        self.assertEqual(control, trial)
                candidate = resolve(slot, position, -30, False)
                ablated = resolve(slot, position, -30, True)
                self.assertEqual(candidate[1]['position'], 'failed shot')
                self.assertEqual(candidate[1]['clinch_controller'], other)
                self.assertEqual(ablated[1]['position'], 'range')
                self.assertIsNone(ablated[1]['clinch_controller'])
                self.assertEqual(candidate[1]['stats'], ablated[1]['stats'])
                self.assertEqual(candidate[2], ablated[2])
                self.assertEqual(candidate[2][other]['control'], 2)
                self.assertEqual(candidate[1]['stats'][slot]['td_att'], 1)
                self.assertEqual(candidate[1]['stats'][slot]['td'], 0)
                self.assertEqual(candidate[3], ablated[3])

                for owners in ((slot, other), (other, slot)):
                    # The resolver's downstream transition must still invalidate
                    # candidate setup state, including reversed-owner leftovers.
                    for margin in (-8, -30):
                        control = resolve(slot, position, margin, False, owners)
                        trial = resolve(slot, position, margin, True, owners)
                        for key in ('von_flue_pending_wrap', 'von_flue_setup', 'scarf_hold_setup'):
                            self.assertNotIn(key, control[1])
                            self.assertNotIn(key, trial[1])
                        self.assertEqual(control[1]['last_von_flue_angle'], trial[1]['last_von_flue_angle'])
                        self.assertEqual(trial[1]['last_von_flue_angle']['status'], 'cancelled')
                        self.assertEqual(trial[1]['last_von_flue_angle']['reason'], 'position_or_ownership_changed')
                        if margin == -8:
                            self.assertEqual(control, trial)
                    disabled = resolve(slot, position, -30, False, owners, specialist=False)
                    disabled_trial = resolve(slot, position, -30, True, owners, specialist=False)
                    self.assertEqual(disabled, disabled_trial)
                    for key in ('von_flue_pending_wrap', 'von_flue_setup', 'scarf_hold_setup'):
                        self.assertIn(key, disabled_trial[1])

    def test_failed_shot_ablation_position_delegate_error_restores_overrides(self):
        cls = diagnostic.FightAuditHarness
        original_resolver, original_setter = cls.resolve_takedown, cls.set_fight_position
        rng = random.getstate()
        calls = []
        def resolve(engine, actor, defender, margin, state, stats):
            self.assertFalse(engine._experimental_specialist_entries)
            engine.set_fight_position(state, 'range')
        def fail_setter(engine, state, position, **kwargs):
            calls.append(engine._experimental_specialist_entries)
            random.random()
            raise RuntimeError('transition failed')
        with patch.object(cls, 'resolve_takedown', resolve), patch.object(cls, 'set_fight_position', fail_setter):
            for specialist in (True, False):
                for instance_override in (True, False):
                    engine = cls()
                    engine._experimental_specialist_entries = specialist
                    if instance_override:
                        engine.set_fight_position = fail_setter.__get__(engine, cls)
                    before = dict(vars(engine))
                    with diagnostic.failed_shot_retention_ablation(True):
                        outer = cls.resolve_takedown
                        with self.assertRaisesRegex(RuntimeError, 'transition failed'):
                            with diagnostic.failed_shot_retention_ablation(True):
                                inner = cls.resolve_takedown
                                with diagnostic.failed_shot_retention_ablation(False):
                                    self.assertIs(cls.resolve_takedown, inner)
                                    engine.resolve_takedown(None, None, -30, {}, {})
                        self.assertIs(cls.resolve_takedown, outer)
                        self.assertEqual(vars(engine), before)
                        self.assertIs(cls.set_fight_position, fail_setter)
                    self.assertEqual(vars(engine), before)
                    self.assertEqual(random.getstate(), rng)
        self.assertEqual(calls, [True, True, False, False])
        self.assertIs(cls.resolve_takedown, original_resolver)
        self.assertIs(cls.set_fight_position, original_setter)

    def test_failed_shot_ablation_control_arm_provenance_and_cli(self):
        import fight_moves
        registry = fight_moves.MOVE_DEFINITIONS
        original = diagnostic.FightAuditHarness.resolve_takedown
        rng = random.getstate()
        default = diagnostic.build_comparison(4)
        ablation = diagnostic.build_comparison(4, ablate_failed_shot_retention=True)
        self.assertEqual(default['arms']['combined_candidate'], ablation['arms']['combined_candidate'])
        self.assertEqual([row['combined_candidate'] for row in default['paired_bouts']],
                         [row['combined_candidate'] for row in ablation['paired_bouts']])
        self.assertEqual(default['input_sha256'], ablation['input_sha256'])
        self.assertEqual(set(ablation['arms']),
                         {'combined_candidate', 'failed_shot_retention_ablated_candidate'})
        control, trial = ablation['arms'].values()
        self.assertEqual(control['registry_sha256'], trial['registry_sha256'])
        self.assertFalse(control['configuration']['legacy_failed_shot_retention'])
        self.assertEqual(trial['configuration'], dict(control['configuration'], legacy_failed_shot_retention=True))
        self.assertIs(fight_moves.MOVE_DEFINITIONS, registry)
        self.assertIs(diagnostic.FightAuditHarness.resolve_takedown, original)
        self.assertEqual(random.getstate(), rng)
        for arm in ablation['arms'].values():
            self.assert_partitions(arm)
            for field in ('standing_exits', 'standing_shots_without_takedown'):
                self.assertEqual(arm[field], arm['groups']['Overall'][field])
        with patch.object(diagnostic, 'build_comparison', return_value={}) as build, redirect_stdout(io.StringIO()):
            diagnostic.main(['--calibration-corpus', '--failed-shot-retention-ablation'])
        build.assert_called_once_with(calibration_corpus=True, ablate_failed_shot_retention=True)
        for keyword, flag in (('ablate_standing_chains', '--standing-chain-ablation'),
                              ('ablate_pocket_action_bias', '--pocket-action-bias-ablation')):
            with self.assertRaises(ValueError):
                diagnostic.build_comparison(1, ablate_failed_shot_retention=True, **{keyword: True})
            with patch.object(diagnostic, 'build_comparison') as build, redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    diagnostic.main(['--failed-shot-retention-ablation', flag])
                build.assert_not_called()

    def test_standing_destination_counts_use_observed_zero_takedowns_and_merge(self):
        def exchange(action='shoot', before='range', after='failed shot', td=0):
            return dict(type='exchange', actor='a', action=action, position_before=before,
                        position_after=after, td_delta=td, sig_att_delta=0, sig_delta=0,
                        head_delta={'a': 0, 'b': 0}, body_delta={'a': 0, 'b': 0},
                        leg_delta={'a': 0, 'b': 0}, damage_delta={'a': 0, 'b': 0},
                        knockdown_delta={'a': 0, 'b': 0}, hurt_delta={'a': 0, 'b': 0})
        missing = exchange(after=None)
        missing.pop('td_delta')
        audits = [dict(method='Decision', trace=[exchange(), exchange(after='cage'),
                    exchange(after='guard', td=1), exchange(action='clinch', after='clinch'),
                    exchange(before='clinch', after='guard'), missing]),
                  dict(method='Decision', trace=[exchange(before='pocket', after='range'),
                    exchange(action='takedown', before='pocket', after='cage'),
                    exchange(action='kick', after='guard'), exchange(after=None)])]
        before = deepcopy(audits)
        result = diagnostic.summarize_audits(audits)
        self.assertEqual(result['standing_exits'], {'shoot|failed shot': 1, 'shoot|cage': 1,
                         'shoot|guard': 1, 'clinch|clinch': 1, 'shoot|unknown': 2,
                         'takedown|cage': 1, 'kick|guard': 1})
        self.assertEqual(result['standing_shots_without_takedown'],
                         {'failed shot': 1, 'cage': 2, 'range': 1, 'unknown': 1})
        merged = {}
        for audit in audits:
            diagnostic.merge_summaries(merged, diagnostic.summarize_audits([audit]))
        self.assertEqual(merged, result)
        self.assertEqual(audits, before)

    def test_aggregation_partition_and_recipient_semantics(self):
        def exchange(actor, action, position):
            return dict(type='exchange', actor=actor, action=action, position_before=position,
                        sig_att_delta=3, sig_delta=2, head_delta={'a': 2, 'b': 7},
                        body_delta={'a': 0, 'b': 4}, leg_delta={'a': 1, 'b': 0},
                        damage_delta={'a': 3, 'b': 11}, knockdown_delta={'a': 1, 'b': 0},
                        hurt_delta={'a': -1, 'b': 3}, outcome='landed')
        first = exchange('a', 'power_punch', 'pocket')
        second = exchange('b', 'ground_strikes', 'mount')
        second.update(referee_ground_action={'type': 'standup'}, outcome='neutral_reset')
        audits = [dict(method='KO', trace=[first, dict(type='round_summary'), second])]
        before = deepcopy(audits)
        result = diagnostic.summarize_audits(audits)
        self.assertEqual(audits, before)
        self.assertEqual(result['totals']['attempts'], 6)
        self.assertEqual(result['totals']['landed'], 4)
        self.assertEqual(result['totals']['head'], 18)
        self.assertEqual(result['totals']['referee_standups'], 1)
        self.assertEqual(result['totals']['neutral_resets'], 1)
        self.assertEqual(result['totals']['finishing_exchanges'], 0)
        self.assertEqual(result['bout_outcomes'], {
            'bouts_with_knockdown': 1, 'bouts_with_ko_tko': 1,
            'knockdown_bouts_with_ko_tko': 1, 'knockdown_bouts_without_ko_tko': 0,
            'ko_tko_bouts_without_knockdown': 0,
        })
        self.assertEqual(result['by_action']['power_punch']['knockdown_to_opponent'], 1)
        self.assertEqual(result['by_action']['ground_strikes']['knockdown_to_actor'], 1)
        self.assertEqual(result['methods'], {'KO': 1})
        self.assert_partitions(result)

    def test_finish_and_knockdown_cohorts_use_recorded_trace_facts(self):
        def event(knockdown=0, stoppage=None):
            return dict(type='exchange', actor='a', action='power_punch', position_before='pocket',
                        sig_att_delta=1, sig_delta=1, head_delta={'a': 0, 'b': 1},
                        body_delta={'a': 0, 'b': 0}, leg_delta={'a': 0, 'b': 0},
                        damage_delta={'a': 0, 'b': 1}, knockdown_delta={'a': knockdown, 'b': 0},
                        hurt_delta={'a': 0, 'b': 1}, outcome='knockdown' if knockdown else 'landed',
                        stoppage=stoppage)
        audits = [dict(method='KO', trace=[event(1), event(0, {'method': 'KO'})]),
                  dict(method='Decision', trace=[event(1)]),
                  dict(method='TKO', trace=[event(0, {'method': 'TKO'})])]
        result = diagnostic.summarize_audits(audits)
        self.assertEqual(result['bout_outcomes'], {
            'bouts_with_knockdown': 2, 'bouts_with_ko_tko': 2,
            'knockdown_bouts_with_ko_tko': 1, 'knockdown_bouts_without_ko_tko': 1,
            'ko_tko_bouts_without_knockdown': 1,
        })
        self.assertEqual(result['totals']['finishing_exchanges'], 2)
        self.assertEqual(result['totals']['finishing_knockdowns'], 0)
        self.assertEqual(result['totals']['knockdowns_in_ko_tko_bouts'], 1)
        self.assertEqual(result['totals']['knockdowns_in_other_bouts'], 1)
        self.assert_partitions(result)

    def assert_partitions(self, arm):
        self.assertEqual(sum(arm['methods'].values()), arm['bouts'])
        for key, value in arm['totals'].items():
            for rows in (arm['by_action'].values(), arm['by_pre_position'].values(),
                         arm['by_action_pre_position'], arm['by_action_style'],
                         arm['by_action_quality_context']):
                self.assertAlmostEqual(sum(row[key] for row in rows), value, places=7)

    def test_real_paired_determinism_inputs_rng_and_registry_restore(self):
        import fight_moves
        registry_before = fight_moves.MOVE_DEFINITIONS
        rng_before = random.getstate()
        seen = []
        original = diagnostic.run_audited_fight
        def observe(engine, a, b, seed, fight):
            before = deepcopy((vars(a), vars(b), seed, fight))
            seen.append(before)
            result = original(engine, a, b, seed, fight)
            self.assertEqual(before, (vars(a), vars(b), seed, fight))
            return result
        with patch.object(diagnostic, 'run_audited_fight', side_effect=observe):
            first = diagnostic.build_comparison(4)
        self.assertEqual(seen[:4], seen[4:])
        self.assertEqual(first, diagnostic.build_comparison(4))
        self.assertEqual(random.getstate(), rng_before)
        self.assertIs(fight_moves.MOVE_DEFINITIONS, registry_before)
        self.assertNotEqual(first['arms']['current_normal']['registry_sha256'],
                            first['arms']['combined_candidate']['registry_sha256'])
        for arm in first['arms'].values():
            self.assert_partitions(arm)
            self.assertEqual(arm['bouts'], 4)
            for key, value in arm['totals'].items():
                self.assertAlmostEqual(arm['groups']['Overall']['totals'][key], value, places=7)
            self.assertEqual(arm['groups']['Overall']['methods'], arm['methods'])
            for group in arm['groups'].values():
                self.assert_partitions(group)
        self.assertEqual(len(first['paired_bouts']), 4)

    def test_rng_restoration_on_failure_and_invalid_count(self):
        rng_before = random.getstate()
        def fail(*args):
            random.random()
            raise RuntimeError('probe')
        with patch.object(diagnostic, 'synthetic_fighter', side_effect=fail):
            with self.assertRaisesRegex(RuntimeError, 'probe'):
                diagnostic.build_comparison(1)
        self.assertEqual(random.getstate(), rng_before)

    def test_full_schedule_matches_real_baseline_builder_without_simulating(self):
        import fight_engine_audit
        calls = []
        def stub(engine, a, b, seed, fight):
            calls.append((a.name, b.name, seed, deepcopy(fight)))
            return dict(method='Draw', round=1, winner_id='', signature='probe')
        with patch.object(fight_engine_audit, 'run_audited_fight', side_effect=stub):
            baseline = fight_engine_audit.build_baseline()
        rows = diagnostic.fixture_schedule(calibration_corpus=True)
        self.assertEqual(len(rows), 3840)
        self.assertEqual(calls, [(r['a_name'], r['b_name'], r['seed'], r['spec']['fight']) for r in rows])
        groups = {}
        for row in rows:
            for group in row['groups']:
                groups[group] = groups.get(group, 0) + 1
        self.assertEqual(groups, {key: value['total'] for key, value in baseline['groups'].items()})
        self.assertEqual(rows[0]['seed'], 8_210_000)
        self.assertEqual(rows[119]['seed'], 8_210_119)
        self.assertEqual(rows[120]['seed'], 8_220_000)
        coverage = diagnostic.fixture_schedule()
        self.assertEqual(len(coverage), 300)
        self.assertEqual(coverage[0]['seed'], 9_310_000)
        self.assertTrue(coverage[0]['a_name'].startswith('Move audit '))

    def test_calibration_cannot_be_shortened_and_cli_selects_full_mode(self):
        for count in (1, 300, 3840):
            with self.assertRaises(ValueError):
                diagnostic.build_comparison(count, calibration_corpus=True)
        with patch.object(diagnostic, 'build_comparison', return_value={}) as build:
            with redirect_stdout(io.StringIO()):
                diagnostic.main(['--calibration-corpus'])
            build.assert_called_once_with(calibration_corpus=True)
            with self.assertRaises(SystemExit):
                diagnostic.main(['--calibration-corpus', '--fights', '3840'])
        for count in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                diagnostic.build_comparison(count)

    def test_output_exclusive_and_default_stdout(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'new.json'
            with patch.object(diagnostic, 'build_comparison', return_value={'evidence': 1}) as build:
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(diagnostic.main([]), 0)
                    build.assert_called_with(300)
                    diagnostic.main(['--fights', '2', '--output', str(path)])
                self.assertEqual(json.loads(path.read_text()), {'evidence': 1})
                count = build.call_count
                with self.assertRaises(FileExistsError):
                    diagnostic.main(['--output', str(path)])
                self.assertEqual(build.call_count, count)
                self.assertEqual(json.loads(path.read_text()), {'evidence': 1})

    def test_changed_source_is_rejected_without_writing_or_leaking_rng(self):
        original = Path.read_bytes
        reads = 0
        rng_before = random.getstate()
        def changed(path):
            nonlocal reads
            value = original(path)
            if path == diagnostic.ROOT / 'fight_engine.py':
                reads += 1
                if reads > 1:
                    return value + b'\n# simulated concurrent source edit\n'
            return value
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(RuntimeError, 'Source changed'):
                diagnostic.build_comparison(1)
        self.assertEqual(random.getstate(), rng_before)


if __name__ == '__main__':
    unittest.main()
