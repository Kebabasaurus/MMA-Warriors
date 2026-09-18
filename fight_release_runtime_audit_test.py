"""Native coverage uses real release methods and restores only its audit bindings."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analysis import evaluate_release_runtime as runtime
from analysis import generate_move_coverage_report as coverage


class NativeCoverageTests(unittest.TestCase):
    def test_actual_native_bouts_have_provenance_and_prepared_diagnostics(self):
        original = coverage.FightAuditHarness, coverage.PreparedFightAuditHarness
        report = runtime._build_native_report(2)
        self.assertEqual(original, (coverage.FightAuditHarness, coverage.PreparedFightAuditHarness))
        self.assertTrue(runtime.NativeFightAuditHarness._submission_chain_trial)
        self.assertTrue(runtime.NativeFightAuditHarness._cradle_setup_trial)
        self.assertTrue(report["cradle_setup_counts"])
        self.assertIn("invalid", report["cradle_setup_counts"])
        self.assertEqual(report["cradle_setup_counts"]["invalid"], 0)
        self.assertIn("invalid", report["hold_transition_counts"])
        self.assertIn("observations", report["prepared_submission_diagnostics"])
        arm = runtime.summarize_report(report)
        self.assertEqual(arm["active_moves"], 440)
        self.assertEqual(arm["registry_sha256"],
                         "7e6428db43f0e25011975e954db97746cb55d9721837a7377b5bbb7ead1d6a39")

    def test_error_restores_audit_bindings(self):
        original = coverage.FightAuditHarness, coverage.PreparedFightAuditHarness
        with patch.object(coverage, "build_report", side_effect=RuntimeError("test")):
            with self.assertRaisesRegex(RuntimeError, "test"):
                runtime._build_native_report(1)
        self.assertEqual(original, (coverage.FightAuditHarness, coverage.PreparedFightAuditHarness))

    def test_rejects_noncanonical_counts_before_simulation(self):
        for count in (1, 299, 301, 24999, 25001, True, 300.0):
            with self.assertRaises(ValueError):
                runtime.evaluate(count)

    def test_source_change_fails_closed(self):
        with patch.object(runtime, "source_hashes", side_effect=({"fight_engine.py": "old"}, {})), \
                patch.object(runtime, "_build_native_report", return_value={}), \
                patch.object(runtime, "summarize_report", return_value={}):
            with self.assertRaisesRegex(RuntimeError, "Source or registry"):
                runtime.evaluate(300)

    def test_existing_output_rejected_before_collection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.json"
            path.write_text("{}", encoding="utf-8")
            with patch.object(runtime, "evaluate") as collect:
                with self.assertRaises(FileExistsError):
                    runtime.main(["--fights", "300", "--output", str(path)])
                collect.assert_not_called()

    def test_schedule_hash_is_stable_and_count_sensitive(self):
        self.assertEqual(runtime.schedule_fingerprint(300), runtime.schedule_fingerprint(300))
        self.assertNotEqual(runtime.schedule_fingerprint(300), runtime.schedule_fingerprint(25000))


if __name__ == "__main__":
    unittest.main()
