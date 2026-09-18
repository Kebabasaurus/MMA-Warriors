"""Focused tests for truthful, optional regression-run summaries."""

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import run_regression_suite as runner


def _run(tmp_path, outcomes, selection=("one_test.py", "two_test.py")):
    calls = []
    values = iter(outcomes)

    def fake_process(command, **_kwargs):
        calls.append(command)
        value = next(values)
        if value == "interrupt":
            raise KeyboardInterrupt
        return SimpleNamespace(returncode=value)

    ticks = iter(range(100))
    with patch.object(runner, "ROOT", tmp_path), \
         patch.object(runner, "SUITES", (("one_test.py", ()), ("two_test.py", ()))), \
         patch.object(runner, "isolated_environment", lambda _path: {}), \
         patch.object(runner, "source_identity", lambda: {"algorithm": "sha256", "digest": "source", "files": []}):
        code = runner.run(["--summary-dir", str(tmp_path / "summaries"), "--run-id", "fixture", *selection],
                          run_process=fake_process, clock=lambda: next(ticks))
    summary = json.loads(next((tmp_path / "summaries").glob("*.json")).read_text(encoding="utf-8"))
    return code, summary, calls


def test_summary_records_success_and_uses_unique_names():
    with tempfile.TemporaryDirectory(prefix="runner-summary-") as raw:
        root = Path(raw)
        code, summary, calls = _run(root, [0, 0])
        assert code == 0
        assert summary["overall_status"] == "passed"
        assert [row["status"] for row in summary["suites"]] == ["passed", "passed"]
        assert summary["source_identity"]["digest"] == "source"
        assert len(calls) == 2
        code, _summary, _calls = _run(root, [0, 0])
        assert code == 0
        assert sorted(path.name for path in (root / "summaries").glob("*.json")) == ["fixture-2.json", "fixture.json"]


def test_failure_leaves_trailing_suite_not_run():
    with tempfile.TemporaryDirectory(prefix="runner-summary-") as raw:
        code, summary, calls = _run(Path(raw), [7])
        assert code == 7
        assert summary["overall_status"] == "failed"
        assert [row["status"] for row in summary["suites"]] == ["failed", "not_run"]
        assert len(calls) == 1


def test_interrupt_is_not_recorded_as_a_pass():
    with tempfile.TemporaryDirectory(prefix="runner-summary-") as raw:
        code, summary, calls = _run(Path(raw), ["interrupt"])
        assert code == 130
        assert summary["overall_status"] == "interrupted"
        assert [row["status"] for row in summary["suites"]] == ["interrupted", "not_run"]
        assert len(calls) == 1


def test_unknown_suite_records_invalid_selection_without_running():
    with tempfile.TemporaryDirectory(prefix="runner-summary-") as raw:
        root = Path(raw)
        with patch.object(runner, "ROOT", root), \
             patch.object(runner, "SUITES", (("one_test.py", ()),)), \
             patch.object(runner, "source_identity", lambda: {"algorithm": "sha256", "digest": "source", "files": []}):
            code = runner.run(["--summary-dir", str(root / "summaries"), "unknown.py"],
                              run_process=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not run")))
        summary = json.loads(next((root / "summaries").glob("*.json")).read_text(encoding="utf-8"))
        assert code == 2
        assert summary["overall_status"] == "invalid_selection"
        assert summary["unknown_suites"] == ["unknown.py"]
        assert summary["suites"] == []


def test_every_root_test_is_registered_or_explicitly_excluded():
    registered = {script for script, _arguments in runner.SUITES}
    discovered = {path.name for path in runner.ROOT.glob("*_test.py")}
    excluded = set(runner.ROOT_TEST_EXCLUSIONS)
    assert not (registered & excluded), "A test cannot be both registered and excluded"
    assert discovered == (registered & discovered) | excluded, sorted(discovered - registered - excluded)
    assert excluded <= discovered, sorted(excluded - discovered)
    assert all(str(reason).strip() for reason in runner.ROOT_TEST_EXCLUSIONS.values())


def test_known_audit_outputs_are_unique_and_source_bound_to_summary():
    with tempfile.TemporaryDirectory(prefix="runner-artifacts-") as raw:
        root = Path(raw)
        first = root / "run.json"
        second = root / "run-2.json"
        arguments = ("--verify", "analysis/move_coverage_reference.json", "--output", "analysis/move_coverage_report.json")
        first_args, first_output = runner._run_specific_arguments(
            "analysis/generate_move_coverage_report.py", arguments, first)
        second_args, second_output = runner._run_specific_arguments(
            "analysis/generate_move_coverage_report.py", arguments, second)
        assert first_output != second_output
        assert str(first_output) in first_args and str(second_output) in second_args
        assert "analysis/move_coverage_reference.json" in first_args
        for script, filename in runner.RUN_SPECIFIC_OUTPUTS.items():
            routed, output = runner._run_specific_arguments(script, (), first)
            assert output.name == filename
            assert routed[-2:] == ("--output", str(output))


if __name__ == "__main__":
    test_summary_records_success_and_uses_unique_names()
    test_failure_leaves_trailing_suite_not_run()
    test_interrupt_is_not_recorded_as_a_pass()
    test_unknown_suite_records_invalid_selection_without_running()
    test_every_root_test_is_registered_or_explicitly_excluded()
    test_known_audit_outputs_are_unique_and_source_bound_to_summary()
    print("Regression runner summary tests passed.")
