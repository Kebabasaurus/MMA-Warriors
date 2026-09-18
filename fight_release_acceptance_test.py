"""The approved long-run rare-ID rule changes no other release gate."""
import copy
import tempfile
import unittest
from pathlib import Path
from analysis.validate_fight_release import (
    PINS, ROOT, load_reviewed_bundle, policy_failures, validate_reviewed_bundle, validate_native_reports,
    source_projection, main,
)


class ReleaseAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reports = load_reviewed_bundle()

    def test_reviewed_policy_passes_without_certifying_runtime(self):
        result = validate_reviewed_bundle()
        self.assertTrue(result["historical_policy_passed"])
        self.assertFalse(result["runtime_release_certified"])
        self.assertEqual(len(result["unobserved_active_move_ids"]), 2)
        self.assertIn("combined: More than eight active moves unobserved", result["raw_standard_findings"])
        self.assertEqual(len(set(result["historical_engine_sha256"].values())), 3)

    def test_each_other_failure_still_blocks(self):
        for field in ("content_gate_failures", "chain_gate_failures", "measured_final_target_failures"):
            with self.subTest(field=field):
                reports = copy.deepcopy(self.reports)
                reports["standard"]["arms"]["combined"][field].append("Unexpected failure")
                self.assertIn("standard: Unexpected failure", policy_failures(reports))

    def test_unknown_root_failure_blocks(self):
        reports = copy.deepcopy(self.reports)
        reports["standard"]["failures"].append("source drift")
        self.assertIn("standard: source drift", policy_failures(reports))

    def test_rare_inventory_and_exact_sample_required(self):
        for count in (300, 24999, 25001):
            reports = copy.deepcopy(self.reports)
            reports["frequency"]["fights_per_arm"] = count
            self.assertTrue(policy_failures(reports))
        reports = copy.deepcopy(self.reports)
        reports["frequency"]["arms"]["combined"]["unobserved_active_move_ids"] = list(map(str, range(9)))
        self.assertTrue(policy_failures(reports))

    def test_concentration_and_rolling_window_not_long_run_average(self):
        for key, value in (("top_ten_move_share_pct", 25.01),
                           ("maximum_identical_defense_clause", 10),
                           ("defense_repetition_window_fights", 25000)):
            reports = copy.deepcopy(self.reports)
            reports["standard"]["arms"]["combined"][key] = value
            self.assertTrue(policy_failures(reports))

    def test_missing_canonical_groups_registry_or_trial_rejected(self):
        for change in (lambda r: r["calibration"]["groups"].pop("Competitive"),
                       lambda r: r["calibration"].update(registry_sha256="0" * 64),
                       lambda r: r["frequency"].update(kick_power_trial=False)):
            reports = copy.deepcopy(self.reports)
            change(reports)
            self.assertTrue(policy_failures(reports))

    def test_edited_envelope_and_output_overwrite_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum"):
                load_reviewed_bundle({role: path for role in PINS})
            with self.assertRaises(FileExistsError):
                main(["--reviewed-historical-bundle", "--output", str(path)])


class NativeReleaseAcceptanceTests(unittest.TestCase):
    def native_evidence(self):
        from analysis.evaluate_release_runtime import source_hashes, schedule_fingerprint
        from analysis.verify_release_integration import sources, fixture_schedule, digest
        reviewed = load_reviewed_bundle()
        current = source_hashes()
        reports = []
        for role, count in (("standard", 300), ("frequency", 25000)):
            arm = copy.deepcopy(reviewed[role]["arms"]["combined"])
            arm["fight_count"] = count
            reports.append(dict(native_release_runtime=True, experimental_only=False,
                source_guard_passed=True, fights_per_arm=count, arms={"combined": arm},
                source_sha256=current, engine_sha256=current["fight_engine.py"],
                schedule_sha256=schedule_fingerprint(count), failures=[]))
        schedule = fixture_schedule(None, calibration_corpus=True)
        parity = dict(fights=3840, calibration_corpus=True, all_complete_bouts_and_rng_equal=True,
            source_sha256=sources(), schedule_sha256=digest(schedule), fixture_sha256="a" * 64,
            pairs=[dict(seed=item["seed"], spec_id=item["spec"]["id"],
                        audit_sha256="b" * 64, terminal_rng_sha256="c" * 64) for item in schedule],
            groups=reviewed["calibration"]["groups"], failures=[],
            validations={kind: reviewed["calibration"][field] for kind, field in (
                ("holds", "hold_transition_counts"), ("cradle", "cradle_setup_counts"),
                ("survival", "survival_expansion_counts"))})
        import hashlib
        parity["reference_sha256"] = {name: hashlib.sha256((ROOT / "analysis" / name).read_bytes()).hexdigest()
                                      for name in ("fight_engine_baseline.json", "survival_expansion_440_calibration.json")}
        return reports + [parity]

    def test_complete_consistent_native_evidence_passes_policy(self):
        # Synthetic checksummed report structures test validation, not fight parity.
        result = validate_native_reports(*self.native_evidence())
        self.assertTrue(result["runtime_release_certified"], result["failures"])
        self.assertEqual(len(result["unobserved_active_move_ids"]), 2)

    def test_native_rejects_stale_sources_missing_pairs_and_claimed_success(self):
        mutations = (
            lambda r: r[0].update(source_sha256={}),
            lambda r: r[1].update(source_guard_passed=False),
            lambda r: r[2].update(all_complete_bouts_and_rng_equal=False),
            lambda r: r[2]["pairs"].pop(),
            lambda r: r[2]["pairs"][0].update(seed=-1),
            lambda r: r[2]["groups"].pop("Competitive"),
            lambda r: r[2].update(validations={}),
            lambda r: r[2].update(reference_sha256={}),
            lambda r: r[0]["arms"]["combined"]["chain_gate_failures"].append("broken chain"),
            lambda r: r[2]["failures"].append("failed competitive floor"),
            lambda r: r[1]["arms"]["combined"].update(unobserved_active_move_ids=list(map(str, range(9)))),
        )
        evidence = self.native_evidence()
        for mutate in mutations:
            reports = copy.deepcopy(evidence)
            mutate(reports)
            result = validate_native_reports(*reports)
            self.assertFalse(result["runtime_release_certified"])
            self.assertTrue(result["failures"])

    def test_exact_reviewed_projection_retains_old_and_new_hashes(self):
        current = {"fight_engine.py": "a" * 64, "identity_persistence_regression_test.py": "b" * 64,
                   "analysis/validate_fight_release.py": "c" * 64}
        recorded = dict(current, **{"identity_persistence_regression_test.py": "d" * 64})
        failures, changes = source_projection(recorded, current)
        self.assertEqual(failures, [])
        self.assertEqual(changes, [{"path": "identity_persistence_regression_test.py",
                                   "recorded_sha256": "d" * 64, "current_sha256": "b" * 64}])
        for name in ("fight_engine.py", "analysis/evaluate_release_runtime.py",
                     "analysis/generate_move_coverage_report.py", "other_test.py"):
            with self.subTest(name=name):
                now = dict(current, **{name: "a" * 64})
                old = dict(now, **{name: "e" * 64})
                self.assertTrue(source_projection(old, now)[0])
        self.assertTrue(source_projection({}, current)[0])
        invalid = dict(recorded, **{"identity_persistence_regression_test.py": "not-a-hash"})
        self.assertTrue(source_projection(invalid, current)[0])

    def test_native_certification_transparently_records_reviewed_test_edit(self):
        reports = self.native_evidence()
        for report in reports:
            report["source_sha256"] = dict(report["source_sha256"])
            report["source_sha256"]["identity_persistence_regression_test.py"] = "d" * 64
        result = validate_native_reports(*reports)
        self.assertTrue(result["runtime_release_certified"], result["failures"])
        for role in ("standard", "frequency", "parity"):
            self.assertEqual(result["reviewed_post_collection_source_changes"][role][0]["recorded_sha256"], "d" * 64)
        self.assertEqual(result["certification_policy_sha256"], result["source_sha256"]["analysis/validate_fight_release.py"])

    def test_deprecation_profile_test_is_the_only_new_reviewed_exception(self):
        from analysis.validate_fight_release import REVIEWED_POST_COLLECTION_FILES
        self.assertEqual(REVIEWED_POST_COLLECTION_FILES, {
            "identity_persistence_regression_test.py", "fight_move_deprecation_regression_test.py",
            "fight_release_acceptance_test.py", "analysis/validate_fight_release.py"})
        path = "fight_move_deprecation_regression_test.py"
        failures, changes = source_projection({path: "a" * 64}, {path: "b" * 64})
        self.assertEqual(failures, [])
        self.assertEqual(changes, [{"path": path, "recorded_sha256": "a" * 64,
                                    "current_sha256": "b" * 64}])


if __name__ == "__main__":
    unittest.main()
