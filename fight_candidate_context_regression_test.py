"""Experimental fight candidates restore globals and cannot promote calibration drift."""
from contextlib import redirect_stdout
from copy import deepcopy
from dataclasses import replace
import io
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import fight_engine
import fight_moves
import fight_moves.catalogue as catalogue
import fight_moves.registry as registry
from analysis.fight_candidate_context import candidate_context, DRAFT_MOVE_DEFINITIONS
from analysis import evaluate_joint_fight_candidate as evaluator
from analysis import generate_move_coverage_report as coverage
from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves.catalogue.specialist_entry_development import SPECIALIST_ENTRY_DEVELOPMENT


class FightCandidateContextTests(unittest.TestCase):
    def test_coverage_cli_fails_for_each_arm_gate_and_preserves_artifact(self):
        for field in ('content_gate_failures', 'chain_gate_failures',
                      'measured_final_target_failures'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                destination = Path(directory) / 'coverage.json'
                result = {'arms': {'combined': {field: ['unresolved gate']}},
                          'scope': 'Frequency diagnostic'}
                with patch('sys.argv', ['candidate', '--coverage', '--combined-only',
                                        '--output', str(destination)]), \
                     patch.object(evaluator, 'coverage_trial', return_value=result), \
                     redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(evaluator.main(), 1)
                saved = json.loads(destination.read_text(encoding='utf-8'))
                self.assertEqual(saved, json.loads(output.getvalue()))
                self.assertEqual(saved['failures'], ['combined: unresolved gate'])
                self.assertEqual(saved['arms']['combined'][field], ['unresolved gate'])
                self.assertEqual(saved['scope'], 'Frequency diagnostic')

    def test_coverage_cli_keeps_advisories_nonblocking_and_all_arms_visible(self):
        result = {'arms': {'normal': {'content_gate_failures': ['control gap']},
                          'combined': {'chain_advisories': ['accepted median'],
                                       'variety_advisories': ['accepted mean']}}}
        self.assertEqual(evaluator.reported_failures(result), ['normal: control gap'])
        result['arms']['normal']['content_gate_failures'] = []
        with patch('sys.argv', ['candidate', '--coverage']), \
             patch.object(evaluator, 'coverage_trial', return_value=result), \
             redirect_stdout(io.StringIO()) as output:
            self.assertEqual(evaluator.main(), 0)
        saved = json.loads(output.getvalue())
        self.assertEqual(saved['failures'], [])
        self.assertEqual(saved['arms']['combined']['chain_advisories'], ['accepted median'])

    def test_fence_drive_can_be_selected_after_resolving_to_cage(self):
        actor = synthetic_fighter('Fence A', 75, 'Wrestler', 'Control', 0)
        defender = synthetic_fighter('Fence B', 75, 'Boxer', 'Control', 1)
        state = {'round': 1, 'tick': 1, 'position': 'cage', 'top': None, 'bottom': None,
                 'clinch_controller': 'a', 'fighter_keys': {id(actor): 'a', id(defender): 'b'}}
        rng = random.getstate()
        with candidate_context(entries=True, chains=True, draft_content=True):
            engine = FightAuditHarness()
            observed = set()
            for tick in range(1, 101):
                state['tick'] = tick
                payload = engine.select_exchange_move(actor, defender, 'force_cage',
                                                      'failed shot', '', state)
                observed.add(payload['move_id'])
            self.assertIn('fence_drive', observed)
            self.assertEqual(random.getstate(), rng)

    def test_fence_drive_uses_failed_shot_source_only_in_entry_candidate(self):
        snapshot, rng = self.snapshot(), random.getstate()
        original = fight_moves.MOVE_REGISTRY['fence_drive']
        with candidate_context(chains=True, draft_content=True):
            self.assertIs(fight_moves.MOVE_REGISTRY['fence_drive'], original)
        with candidate_context(entries=True, chains=True, draft_content=True) as definitions:
            repaired = fight_moves.MOVE_REGISTRY['fence_drive']
            self.assertEqual(repaired, replace(original, positions=frozenset({'failed shot'})))
            self.assertIn(repaired, fight_moves.legal_moves('force_cage', 'failed shot'))
            for position in fight_moves.ALL_POSITIONS - {'failed shot'}:
                self.assertNotIn(repaired, fight_moves.legal_moves('force_cage', position))
            self.assertEqual(len(definitions), 400)
            with self.assertRaisesRegex(RuntimeError, 'restore entry'):
                with candidate_context(entries=True):
                    self.assertEqual(fight_moves.MOVE_REGISTRY['fence_drive'], repaired)
                    raise RuntimeError('restore entry')
            self.assertIs(fight_moves.MOVE_REGISTRY['fence_drive'], repaired)
        self.assert_restored(snapshot)
        self.assertEqual(random.getstate(), rng)

    def test_registered_inventory_ignores_generic_unknown_and_retired_ids(self):
        base = fight_moves.MOVE_DEFINITIONS[0]
        moves = (replace(base, move_id='present'), replace(base, move_id='missing'),
                 replace(base, move_id='retired', deprecated=True))
        report = {'observed_move_ids': ['present', 'present', 'generic_missing', 'unknown']}
        self.assertEqual(evaluator.registered_move_inventory(report, moves), {
            'unobserved_active_move_ids': ['missing'], 'active_moves_with_follow_ups': 2})
        self.assertEqual(evaluator.registered_move_inventory({}, moves)['unobserved_active_move_ids'],
                         ['missing', 'present'])

    def test_continuation_branch_trial_is_explicit_nested_and_restored(self):
        snapshot = self.snapshot()
        with candidate_context(chains=True, draft_content=True) as original:
            old = {move.move_id: move for move in original}
            self.assertNotIn('single_jab', old['overhand'].follow_ups)
            with candidate_context(chains=True, draft_content=True, continuation_branches=True) as changed:
                new = {move.move_id: move for move in changed}
                self.assertEqual(new['overhand'].follow_ups, (*old['overhand'].follow_ups, 'single_jab'))
                self.assertEqual(len(changed), 400)
                with candidate_context(chains=True, continuation_branches=True) as nested:
                    self.assertEqual(nested, changed)
            self.assertIs(fight_moves.MOVE_REGISTRY['overhand'], old['overhand'])
        self.assert_restored(snapshot)
        with self.assertRaisesRegex(ValueError, 'requires chain mechanics'):
            with candidate_context(continuation_branches=True):
                self.fail('Branch trial accepted without chain mechanics')
        self.assert_restored(snapshot)

    def test_continuation_cli_keeps_full_calibration_and_failures(self):
        with patch('sys.argv', ['candidate', '--continuation-branches', '--fights', '1']), \
             patch.object(evaluator, 'calibration_trial', return_value={'failures': ['balance failure']}) as full, \
             patch.object(evaluator, 'coverage_trial') as coverage_call, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(evaluator.main(), 1)
        full.assert_called_once_with(continuation_branches=True)
        coverage_call.assert_not_called()
        self.assertTrue(json.loads(output.getvalue())['continuation_branch_trial'])

    def test_policy_source_change_rejects_output(self):
        original = Path.read_bytes
        reads = 0
        def changed(path):
            nonlocal reads
            data = original(path)
            if path == evaluator.ROOT / 'fight_moves/selection_pool.py':
                reads += 1
                if reads > 1:
                    return data + b'changed'
            return data
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'candidate.json'
            with patch.object(Path, 'read_bytes', changed), \
                 patch.object(evaluator, 'coverage_trial', return_value={}), \
                 patch('sys.argv', ['candidate', '--coverage', '--output', str(output)]):
                with self.assertRaisesRegex(RuntimeError, 'sources changed'):
                    evaluator.main()
            self.assertFalse(output.exists())

    def snapshot(self):
        keys = ("MOVE_DEFINITIONS", "MOVE_REGISTRY", "MOVE_INDEX", "legal_moves", "CHAIN_GRAPH", "chain_depth")
        pairs = [(module, key) for module in (fight_moves, registry) for key in keys]
        pairs += [(fight_engine, key) for key in ("MOVE_REGISTRY", "legal_moves")]
        pairs += [(catalogue, "MOVE_DEFINITIONS")]
        return [(module, key, getattr(module, key)) for module, key in pairs]

    def assert_restored(self, snapshot):
        for module, key, value in snapshot:
            self.assertIs(getattr(module, key), value, f"{module.__name__}.{key}")

    def test_error_restores_all_bindings_flags_and_rng(self):
        snapshot, rng = self.snapshot(), random.getstate()
        flags = ("_experimental_specialist_entries", "_experimental_chain_action_weighting",
                 "_experimental_pocket_action_bias")
        before = {key: FightAuditHarness.__dict__.get(key) for key in flags}
        present = {key: key in FightAuditHarness.__dict__ for key in flags}
        with self.assertRaisesRegex(RuntimeError, "audit failure"):
            with candidate_context(entries=True, chains=True, draft_content=True, pocket_action_bias=False):
                self.assertTrue(FightAuditHarness()._experimental_specialist_entries)
                self.assertTrue(FightAuditHarness()._experimental_chain_action_weighting)
                self.assertFalse(FightAuditHarness()._experimental_pocket_action_bias)
                random.random()
                raise RuntimeError("audit failure")
        self.assert_restored(snapshot)
        self.assertEqual(random.getstate(), rng)
        for key in flags:
            self.assertEqual(key in FightAuditHarness.__dict__, present[key])
            self.assertIs(FightAuditHarness.__dict__.get(key), before[key])

    def test_nested_context_restores_outer_candidate_and_rng(self):
        snapshot = self.snapshot()
        with candidate_context(entries=True, chains=False, draft_content=True, pocket_action_bias=True) as outer:
            outer_snapshot, rng = self.snapshot(), random.getstate()
            with candidate_context(entries=False, chains=True, draft_content=True, pocket_action_bias=False) as inner:
                self.assertEqual(inner, outer)
                self.assertFalse(FightAuditHarness()._experimental_specialist_entries)
                self.assertTrue(FightAuditHarness()._experimental_chain_action_weighting)
                self.assertFalse(FightAuditHarness()._experimental_pocket_action_bias)
                random.random()
            self.assert_restored(outer_snapshot)
            self.assertEqual(random.getstate(), rng)
            self.assertTrue(FightAuditHarness()._experimental_specialist_entries)
            self.assertFalse(FightAuditHarness()._experimental_chain_action_weighting)
            self.assertTrue(FightAuditHarness()._experimental_pocket_action_bias)
        self.assert_restored(snapshot)

    def test_conflicting_draft_id_is_rejected_without_overwriting_globals(self):
        conflicting = replace(SPECIALIST_ENTRY_DEVELOPMENT[0], name="Conflicting user definition")
        with patch.object(fight_moves, "MOVE_DEFINITIONS", (*fight_moves.MOVE_DEFINITIONS, conflicting)):
            snapshot, rng = self.snapshot(), random.getstate()
            with self.assertRaisesRegex(ValueError, "Conflicting candidate move"):
                with candidate_context(draft_content=True):
                    self.fail("Conflict was accepted")
            self.assert_restored(snapshot)
            self.assertEqual(random.getstate(), rng)

    def test_draft_definitions_reach_runtime_lookup_and_both_coverage_paths(self):
        original_count = len(fight_moves.MOVE_DEFINITIONS)
        draft_ids = {move.move_id for move in SPECIALIST_ENTRY_DEVELOPMENT}
        self.assertEqual(original_count, 346)
        with candidate_context(draft_content=True) as definitions:
            self.assertEqual(len(definitions), 400)
            self.assertEqual({move.move_id for move in fight_engine.legal_moves("force_cage", "failed shot")},
                             draft_ids - {"clinch_snapdown_front_headlock"})
            self.assertIn("clinch_snapdown_front_headlock",
                          {move.move_id for move in registry.legal_moves("front_headlock", "clinch")})
            # Actual short simulations exercise both explicit and late-bound
            # default definitions, rather than relying on a mocked report.
            for kwargs in ({}, {"definitions": definitions}):
                report = coverage.build_report(1, **kwargs)
                for field in ("exchange_position_counts", "action_selection_counts", "move_selection_counts"):
                    self.assertEqual(sum(report[field].values()), report["total_move_selections"])
                self.assertEqual(sum(int(beats) * count for beats, count in report["pocket_residence_histogram"].items()),
                                 report["exchange_position_counts"].get("pocket", 0))
                self.assertEqual(sum(report["pocket_exit_counts"].values()), report["pocket_observed_episodes"])
                self.assertEqual(sum(row["count"] for row in report["submission_identity_contexts"]),
                                 report["submission_attempt_identity_count"])
                for family in ("von_flue", "scarf_hold"):
                    self.assertEqual(sum(report[f"{family}_followthrough_counts"].values()),
                                     report[f"{family}_setup_counts"].get("created", 0))
                accounted = set(report["observed_move_ids"]) | set(report["eligibility_warnings"])
                self.assertTrue(draft_ids <= accounted)
                expected = sum("Well-Rounded" in move.preferred_styles for move in definitions)
                self.assertEqual(report["coverage"]["style_counts"]["Well-Rounded"], expected)
        self.assertEqual(len(fight_moves.MOVE_DEFINITIONS), original_count)

    def test_all_54_drafts_reach_exact_scoped_runtime_lookup(self):
        snapshot, rng = self.snapshot(), random.getstate()
        self.assertEqual(len(DRAFT_MOVE_DEFINITIONS), 54)
        with candidate_context(draft_content=True):
            for move in DRAFT_MOVE_DEFINITIONS:
                for position in move.positions:
                    self.assertIn(move, fight_engine.legal_moves(move.parent_action, position))
                    self.assertIs(fight_engine.MOVE_REGISTRY[move.move_id], move)
            self.assertEqual(len(fight_engine.MOVE_REGISTRY), 400)
        self.assert_restored(snapshot)
        self.assertEqual(random.getstate(), rng)

    def test_calibration_uses_reference_seed_count_and_reports_failures_without_writes(self):
        reference = evaluator.ROOT / "analysis" / "fight_engine_baseline.json"
        before = reference.read_bytes()
        expected_seeds = int(json.loads(before)["seeds_per_matchup"])
        result = {"fight_count": 3840, "groups": {
            "Overall": {"finishes": 2400},
            "Competitive": {"finishes": 1300, "methods": {"KO": 300}},
            "Mismatch": {"finishes": 1100, "methods": {"KO": 200}},
        }}
        with patch.object(evaluator, "build_baseline", return_value=result) as build, \
             patch.object(evaluator, "compare_to_baseline", return_value=["distribution drift"]), \
             patch.object(evaluator, "compare_to_accepted_calibration", return_value=["locked count drift"]), \
             patch.object(Path, "write_text", side_effect=AssertionError("Unexpected write")), \
             patch.object(Path, "write_bytes", side_effect=AssertionError("Unexpected write")):
            report = evaluator.calibration_trial()
        build.assert_called_once_with(expected_seeds)
        self.assertEqual(report["fights"], 3840)
        self.assertEqual(report["groups"], result["groups"])
        self.assertEqual(report["overall"], report["groups"]["Overall"])
        self.assertEqual(report["failures"], ["distribution drift", "locked count drift"])
        self.assertTrue(report["experimental_only"])
        self.assertEqual(reference.read_bytes(), before)

    def test_head_damage_approval_reclassifies_only_middle_timing(self):
        result = {"fight_count": 3840, "groups": {"Overall": {"finishes": 2275}}}
        with patch.object(evaluator, "build_baseline", return_value=result), \
             patch.object(evaluator, "compare_to_baseline", return_value=[
                 "Middle finish timing moved by more than 2.0 percentage points", "other drift"]), \
             patch.object(evaluator, "compare_to_accepted_calibration", return_value=[]):
            report = evaluator.calibration_trial(standing_head_damage=True)
        self.assertEqual(report["failures"], ["other drift"])
        self.assertEqual(report["balance_advisories"],
                         ["Middle finish timing drift accepted by user for the 2% head-damage trial"])

    def test_default_cli_cannot_shorten_or_promote_failed_calibration(self):
        original_open = Path.open
        def read_only_open(path, mode="r", *args, **kwargs):
            self.assertFalse(any(flag in mode for flag in "wax+"), mode)
            return original_open(path, mode, *args, **kwargs)
        for argv in (["candidate"], ["candidate", "--fights", "1"]):
            with patch("sys.argv", argv), redirect_stdout(io.StringIO()), \
                 patch.object(evaluator, "calibration_trial", return_value={"failures": ["locked count drift"]}) as calibration, \
                 patch.object(evaluator, "coverage_trial") as short_trial, \
                 patch.object(Path, "open", read_only_open), \
                 patch.object(Path, "write_text", side_effect=AssertionError("Unexpected write")), \
                 patch.object(Path, "write_bytes", side_effect=AssertionError("Unexpected write")):
                self.assertEqual(evaluator.main(), 1)
                calibration.assert_called_once_with()
                short_trial.assert_not_called()

    def test_draft_filter_excludes_generic_fallbacks_and_normal_moves(self):
        draft = SPECIALIST_ENTRY_DEVELOPMENT[0].move_id
        self.assertEqual(evaluator.observed_drafts([draft, "generic_front_headlock", "single_jab", draft]), [draft])

    def test_combined_only_uses_identical_fights_and_keeps_failures(self):
        factorial = evaluator.coverage_trial(1)
        focused = evaluator.coverage_trial(1, combined_only=True)
        self.assertEqual(set(focused["arms"]), {"combined"})
        self.assertEqual(focused["arms"]["combined"], factorial["arms"]["combined"])
        self.assertTrue(focused["arms"]["combined"]["measured_final_target_failures"])
        self.assertIn("frequency diagnostic", focused["scope"])
        self.assertEqual(focused["fights_per_arm"], 1)

    def test_combined_only_cannot_replace_calibration(self):
        with patch("sys.argv", ["candidate", "--combined-only"]), \
             patch.object(evaluator, "calibration_trial") as calibration, \
             patch.object(evaluator, "coverage_trial") as coverage_trial, \
             self.assertRaises(SystemExit) as error:
            evaluator.main()
        self.assertEqual(error.exception.code, 2)
        calibration.assert_not_called()
        coverage_trial.assert_not_called()

    def test_measured_targets_keep_exact_boundaries_and_exclude_retired_moves(self):
        moves = [replace(fight_moves.MOVE_DEFINITIONS[0], move_id=f"probe_{i}") for i in range(400)]
        report = dict(mean_distinct_moves_per_fighter=20, chained_selection_pct=15,
                      observed_move_ids=[move.move_id for move in moves],
                      pocket_exchange_share_pct=8,
                      median_attempted_chain_length_round2_fights=2, top_ten_move_share_pct=25,
                      top_submission_largest_share_pct=20,
                      contexts=[("probe", position, "") for position in fight_moves.ALL_POSITIONS])
        self.assertEqual(evaluator.measured_target_failures(report, moves), [])
        self.assertEqual(evaluator.measured_target_failures(
            dict(report, median_attempted_chain_length_round2_fights=1), moves), [])
        for unused in (8, 9):
            partial = dict(report, observed_move_ids=[move.move_id for move in moves[unused:]])
            failures = evaluator.measured_target_failures(partial, moves)
            self.assertEqual('More than eight active moves unobserved' in failures, unused == 9)
        for with_followups in (199, 200):
            branch_moves = [move if i < with_followups else replace(move, follow_ups=())
                            for i, move in enumerate(moves)]
            failures = evaluator.measured_target_failures(report, branch_moves)
            self.assertEqual('Fewer than 200 active moves declare follow-ups' in failures, with_followups == 199)
        for mean in (0, 19.99, 20, 24, 24.01, 40):
            advisory_report = dict(report, mean_distinct_moves_per_fighter=mean)
            self.assertEqual(evaluator.measured_target_failures(advisory_report, moves), [])
            self.assertEqual(bool(evaluator.variety_advisories(advisory_report)), not 20 <= mean <= 24)
            self.assertEqual(advisory_report["mean_distinct_moves_per_fighter"], mean)
        for key, value in (("chained_selection_pct", 14.99),
                           ("top_ten_move_share_pct", 25.01),
                           ("top_submission_largest_share_pct", 20.01),
                           ("pocket_exchange_share_pct", 7.99),
                           ("incompatible_submission_identity_count", 1),
                           ("missing_submission_technique_count", 1),
                           ("incompatible_submission_defense_count", 1),
                           ("top_leg_entry_counts", {"invalid": 1}),
                           ("von_flue_setup_counts", {"invalid": 1}),
                           ("scarf_hold_setup_counts", {"invalid": 1}),
                           ("guillotine_defense_counts", {"invalid": 1}),
                           ("von_flue_angle_counts", {"invalid": 1}),
                           ("control_award_counts", {"invalid": 1}),
                           ("missing_control_award_count", 1),
                           *(('prepared_submission_diagnostics', {'by_setup': {'scarf': {key: 1}}})
                             for key in ('invalid_observations', 'missing_draws', 'incomplete', 'unobserved_menus'))):
            with self.subTest(key=key, value=value):
                self.assertEqual(len(evaluator.measured_target_failures(dict(report, **{key: value}), moves)), 1)
        moves[-1] = replace(moves[-1], deprecated=True)
        self.assertEqual(evaluator.measured_target_failures(report, moves), ["Active move count is not 400"])

    def test_experimental_report_rejects_removed_control_evidence(self):
        original = FightAuditHarness.record_fight_trace_exchange
        def omit_award(engine, *args, **kwargs):
            event = original(engine, *args, **kwargs)
            event.pop("control_award", None)
            return event
        with candidate_context(entries=True, draft_content=True) as definitions:
            report = coverage.build_report(1, definitions=definitions)
            self.assertEqual(report["missing_control_award_count"], 0)
            self.assertEqual(sum(report["control_award_counts"].values()), report["total_move_selections"])
            with patch.object(FightAuditHarness, "record_fight_trace_exchange", omit_award):
                broken = coverage.build_report(1, definitions=definitions)
            self.assertEqual(broken["missing_control_award_count"], broken["total_move_selections"])
            self.assertGreater(broken["missing_control_award_count"], 0)
            self.assertIn("Experimental exchange lacks control-award evidence",
                          evaluator.measured_target_failures(broken, definitions))

    def test_registry_digest_binds_followups_and_restores(self):
        initial = evaluator.registry_fingerprint()
        with candidate_context(draft_content=True):
            expanded = evaluator.registry_fingerprint()
            self.assertNotEqual(initial, expanded)
            definitions = fight_moves.MOVE_DEFINITIONS
            changed = replace(definitions[-1], follow_ups=())
            with patch.object(fight_moves, "MOVE_DEFINITIONS", (*definitions[:-1], changed)):
                self.assertNotEqual(expanded, evaluator.registry_fingerprint())
        self.assertEqual(initial, evaluator.registry_fingerprint())

    def test_prepared_reconciliation_rejects_missing_kind_row_and_draw_classification(self):
        row = dict(kind='scarf', bout_index=2, round=1, created_tick=8, top='a', bottom='b')
        report = {
            'scarf_hold_followthrough_counts': {'used': 1, 'context_changed': 4, 'unobserved': 1},
            'prepared_submission_diagnostics': {
                'by_setup': {'scarf': dict(opportunities=1, weighted_menus=1,
                    submission_choices=1, prepared_choices=1)}, 'observations': [row]}}
        self.assertTrue(evaluator.prepared_diagnostics_consistent(report))
        for change in ('whole_diagnostics', 'kind', 'row', 'duplicate', 'draw', 'choice', 'menu'):
            broken = deepcopy(report)
            diagnostic = broken['prepared_submission_diagnostics']
            if change == 'whole_diagnostics':
                broken.pop('prepared_submission_diagnostics')
            elif change == 'kind':
                diagnostic['by_setup'].clear()
            elif change == 'row':
                diagnostic['observations'].clear()
            elif change == 'duplicate':
                diagnostic['observations'].append(dict(row))
            else:
                key = {'draw': 'submission_choices', 'choice': 'prepared_choices', 'menu': 'weighted_menus'}[change]
                diagnostic['by_setup']['scarf'][key] = 0
            with self.subTest(change=change):
                self.assertFalse(evaluator.prepared_diagnostics_consistent(broken))

    def test_optional_output_is_exclusive_and_retains_failure_status(self):
        with tempfile.TemporaryDirectory(prefix="mma-candidate-test-") as directory:
            output = Path(directory) / "trial.json"
            with patch("sys.argv", ["candidate", "--output", str(output)]), \
                 patch.object(evaluator, "calibration_trial", return_value={"experimental_only": True,
                                                                             "failures": ["locked count drift"]}), \
                 redirect_stdout(io.StringIO()):
                self.assertEqual(evaluator.main(), 1)
                before = output.read_bytes()
                self.assertEqual(json.loads(before)["failures"], ["locked count drift"])
                with self.assertRaises(FileExistsError):
                    evaluator.main()
                self.assertEqual(output.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
