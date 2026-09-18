"""Run every maintained regression in a fresh runtime-data directory.

The game deliberately stores portable runtime data beside the application.  A
test process must not share that mutable directory with another test, otherwise
database markers, saves, and logs make the result depend on execution order.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUITES = (
    ("fight_night_presentation_test.py", ()),
    ("fight_night_archive_regression_test.py", ()),
    ("fight_night_layout_regression_test.py", ()),
    ("fighter_portrait_regression_test.py", ()),
    ("fighter_portrait_ranked_101_200_test.py", ()),
    ("portrait_authored_clone_regression_test.py", ()),
    ("portrait_custom_style_regression_test.py", ()),
    ("portrait_scalp_finish_regression_test.py", ()),
    ("portrait_tattoo_regression_test.py", ()),
    ("fighter_traits_regression_test.py", ()),
    ("fight_release_registry_test.py", ()),
    ("fight_release_extensions_test.py", ()),
    ("fight_release_acceptance_test.py", ()),
    ("fight_release_integration_test.py", ()),
    ("fight_release_persistence_test.py", ()),
    ("fight_release_runtime_audit_test.py", ()),
    ("fight_defense_wording_benchmark_test.py", ()),
    ("fight_survival_unused_diagnostics_test.py", ()),
    ("fight_defense_wording_test.py", ()),
    ("fight_jab_wording_test.py", ()),
    ("fight_survival_commentary_test.py", ()),
    ("fight_survival_catalogue_test.py", ()),
    ("fight_survival_expansion_test.py", ()),
    ("fight_kick_power_test.py", ()),
    ("fight_standing_head_damage_test.py", ()),
    ("fight_cradle_matchup_diagnostics_test.py", ()),
    ("fight_submission_chain_candidate_test.py", ()),
    ("fight_cradle_setup_candidate_test.py", ()),
    ("fight_heel_hook_identity_test.py", ()),
    ("fight_repertoire_cohorts_test.py", ()),
    ("fight_boxing_chain_pool_test.py", ()),
    ("fight_jab_timing_diagnostics_test.py", ()),
    ("fight_repertoire_diagnostics_test.py", ()),
    ("fight_gift_wrap_mount_candidate_test.py", ()),
    ("fight_gift_wrap_control_candidate_test.py", ()),
    ("fight_continuation_commitment_test.py", ()),
    ("fight_chain_selection_diagnostics_test.py", ()),
    ("smoke_test.py", ()),
    ("persistence_regression_test.py", ()),
    ("drug_testing_regression_test.py", ()),
    ("drug_testing_catalogue_regression_test.py", ()),
    ("j8_tournament_history_regression_test.py", ()),
    ("grand_prix_regression_test.py", ()),
    ("j12_conversion_regression_test.py", ()),
    ("g0_repair_regression_test.py", ()),
    ("foundation_regression_test.py", ()),
    ("last_minute_replacement_regression_test.py", ()),
    ("title_decision_resume_regression_test.py", ()),
    ("rebooking_regression_test.py", ()),
    ("booking_workbench_regression_test.py", ()),
    ("contract_batch_workbench_regression_test.py", ()),
    ("j2_event_preparation_regression_test.py", ()),
    ("rules_help_regression_test.py", ()),
    ("j10_comparison_regression_test.py", ()),
    ("simulation_pause_policy_regression_test.py", ()),
    ("pinned_checkpoint_regression_test.py", ()),
    ("play_level_audit_regression_test.py", ()),
    ("contracts_finance_regression_test.py", ()),
    ("finance_audit_regression_test.py", ()),
    ("player_finance_progression_regression_test.py", ()),
    ("event_economics_regression_test.py", ()),
    ("narrative_system_regression_test.py", ()),
    ("narrative_long_run_storage_regression_test.py", ()),
    ("narrative_performance_regression_test.py", ()),
    ("simulation_performance_regression_test.py", ()),
    ("ui_data_regression_test.py", ()),
    ("fighter_profile_regression_test.py", ()),
    ("app_performance_regression_test.py", ()),
    ("ai_card_logic_regression_test.py", ()),
    ("scouting_regression_test.py", ()),
    ("regional_feasibility_regression_test.py", ()),
    ("regional_invitation_regression_test.py", ()),
    ("combat_sports_regression_test.py", ()),
    ("database_editor_identity_regression_test.py", ()),
    ("qa_tooling_regression_test.py", ()),
    ("regression_runner_regression_test.py", ()),
    ("media_system_test.py", ()),
    ("media_plan_regression_test.py", ()),
    ("staff_management_regression_test.py", ()),
    ("staff_specialty_regression_test.py", ()),
    ("staff_employment_regression_test.py", ()),
    ("academy_coach_regression_test.py", ()),
    ("owned_schedule_regression_test.py", ()),
    ("owner_goal_regression_test.py", ()),
    ("cash_runway_regression_test.py", ()),
    ("super_event_closeout_regression_test.py", ()),
    ("recruitment_decision_pack_regression_test.py", ()),
    ("relationship_case_regression_test.py", ()),
    ("story_briefing_regression_test.py", ()),
    ("child_promotion_interactions_test.py", ()),
    ("child_promotion_loan_return_regression_test.py", ()),
    ("child_promotion_long_run_test.py", ()),
    ("custom_promotion_division_integrity_test.py", ()),
    ("identity_persistence_regression_test.py", ()),
    ("fight_engine_regression_test.py", ()),
    ("fight_ground_activity_regression_test.py", ()),
    ("fight_specialist_entry_regression_test.py", ()),
    ("fight_standing_back_entry_regression_test.py", ()),
    ("fight_leg_entry_regression_test.py", ()),
    ("fight_submission_identity_regression_test.py", ()),
    ("fight_pocket_distance_regression_test.py", ()),
    ("fight_submission_pool_regression_test.py", ()),
    ("fight_submission_position_bonus_regression_test.py", ()),
    ("fight_submission_defense_regression_test.py", ()),
    ("fight_top_leg_entry_regression_test.py", ()),
    ("fight_bottom_leg_entry_regression_test.py", ()),
    ("fight_dirty_boxing_preview_regression_test.py", ()),
    ("fight_round_streak_reset_test.py", ()),
    ("fight_counter_fallback_regression_test.py", ()),
    ("fight_continuation_branch_candidate_test.py", ()),
    ("fight_continuation_strength_regression_test.py", ()),
    ("fight_repertoire_readaptation_regression_test.py", ()),
    ("fight_chain_reaction_provenance_test.py", ()),
    ("fight_von_flue_setup_regression_test.py", ()),
    ("fight_scarf_hold_setup_regression_test.py", ()),
    ("fight_guillotine_defense_regression_test.py", ()),
    ("fight_prepared_submission_regression_test.py", ()),
    ("fight_prepared_diagnostics_regression_test.py", ()),
    ("fight_candidate_striking_diagnostics_test.py", ()),
    ("fight_standing_counter_diagnostics_test.py", ()),
    ("fight_failed_shot_escape_intent_test.py", ()),
    ("fight_round_counter_expiry_test.py", ()),
    ("fight_leg_escape_defense_regression_test.py", ()),
    ("fight_move_adaptability_regression_test.py", ()),
    ("fight_repertoire_pool_regression_test.py", ()),
    ("fight_specialist_plan_regression_test.py", ()),
    ("fight_specialist_style_regression_test.py", ()),
    ("fight_von_flue_angle_regression_test.py", ()),
    ("fight_von_flue_angle_provenance_test.py", ()),
    ("fight_specialist_accounting_regression_test.py", ()),
    ("fight_candidate_context_regression_test.py", ()),
    ("fight_chain_action_weighting_regression_test.py", ()),
    ("fight_chain_initiative_regression_test.py", ()),
    ("fight_move_specialist_entry_authoring_test.py", ()),
    ("fight_move_front_headlock_authoring_test.py", ()),
    ("fight_move_turtle_authoring_test.py", ()),
    ("fight_move_failed_shot_authoring_test.py", ()),
    ("fight_move_standing_back_authoring_test.py", ()),
    ("fight_move_leg_entanglement_authoring_test.py", ()),
    ("fight_move_parity_regression_test.py", ()),
    ("fight_move_registry_regression_test.py", ()),
    ("fight_move_chain_regression_test.py", ()),
    ("fight_move_sequence_regression_test.py", ()),
    ("fight_chain_opportunity_regression_test.py", ()),
    ("fight_variety_opportunity_regression_test.py", ()),
    ("fight_move_selector_benchmark_regression_test.py", ()),
    ("fight_move_cache_regression_test.py", ()),
    ("fight_move_deprecation_regression_test.py", ()),
    ("fight_move_schema_parity_regression_test.py", ()),
    ("fight_move_selection_parity_regression_test.py", ()),
    ("tools/move_selection_parity.py", ("--verify", "analysis/move_selection_followup_continuity.json",
                                       "--historical-portrait-fixtures", "--historical-wording")),
    ("tools/benchmark_move_selector.py", ("--check",)),
    ("fight_move_followup_authoring_test.py", ()),
    ("fight_move_followup_diversity_regression_test.py", ()),
    ("fight_move_followup_continuity_regression_test.py", ()),
    ("fight_move_followup_defensive_continuity_regression_test.py", ()),
    ("fight_move_followup_comparison_regression_test.py", ()),
    ("analysis/compare_followup_diversity.py", ()),
    ("fight_move_followup_parity_regression_test.py", ()),
    ("fight_move_coverage_regression_test.py", ()),
    ("analysis/generate_move_coverage_report.py", ("--verify", "analysis/move_coverage_reference.json", "--output", "analysis/move_coverage_report.json")),
    ("fight_move_expansion_regression_test.py", ()),
    ("fight_move_bottom_defense_regression_test.py", ()),
    ("fight_move_striking_expansion_regression_test.py", ()),
    ("fight_move_kick_authoring_test.py", ()),
    ("fight_move_clinch_authoring_test.py", ()),
    ("fight_move_wrestling_authoring_test.py", ()),
    ("fight_move_ground_top_authoring_test.py", ()),
    ("fight_move_bottom_submission_authoring_test.py", ()),
    ("fight_move_ground_expansion_regression_test.py", ()),
    ("analysis/compare_ground_move_expansion.py", ()),
    ("analysis/compare_striking_move_expansion.py", ()),
    ("analysis/compare_bottom_move_expansion.py", ()),
    ("tools/move_registry_parity.py", ("--verify", "analysis/move_registry_followup_continuity.json")),
    ("analysis/generate_fight_commentary_report.py", ()),
    ("analysis/generate_fight_engine_baseline.py", ("--verify", "analysis/fight_engine_baseline.json")),
    ("analysis/generate_fight_action_baseline.py", ("--verify", "analysis/fight_engine_action_baseline.json")),
    ("fight_engine_full_system_test.py", ()),
    ("fight_night_experience_regression_test.py", ()),
    ("universe_validation_regression_test.py", ()),
    ("fight_audio_regression_test.py", ()),
    ("advance_notifications_regression_test.py", ()),
    ("window_lifecycle_regression_test.py", ()),
    ("database_editor_save_as_test.py", ()),
    ("database_editor_ui_audit.py", ()),
    ("database_editor.py", ("--validate", "Databases/Default Universe.universe.json")),
    ("stability_test.py", ()),
)

# Every runnable root ``*_test.py`` belongs in SUITES or in this explicit map.
# Keep exclusions exceptional and explain why the file is not maintained coverage.
ROOT_TEST_EXCLUSIONS = {}


def isolated_environment(temp_dir):
    data_dir = Path(temp_dir) / "runtime"
    source_databases = ROOT / "Databases"
    if source_databases.exists():
        shutil.copytree(source_databases, data_dir / "Databases")
    else:
        (data_dir / "Databases").mkdir(parents=True)
    (data_dir / "Saves").mkdir(parents=True, exist_ok=True)
    (data_dir / "Logs").mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["MMA_WARRIORS_DATA_DIR"] = str(data_dir)
    return environment


def source_identity():
    """Fingerprint the current Python working tree, including untracked sources."""
    excluded_parts = {".git", ".claude", ".codex-remote-attachments", ".pytest_cache", ".venv",
                      "build", "dist", "Saves", "Logs", "__pycache__"}
    rows = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in excluded_parts for part in path.relative_to(ROOT).parts):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append({"path": path.relative_to(ROOT).as_posix(), "sha256": digest})
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"algorithm": "sha256", "digest": hashlib.sha256(encoded).hexdigest(), "files": rows}


def _summary_path(directory, run_id):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", str(run_id or "").strip()).strip(".-")
    if not stem:
        stem = datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ") + f"-{os.getpid()}"
    candidate = directory / f"{stem}.json"
    suffix = 2
    while candidate.exists():
        candidate = directory / f"{stem}-{suffix}.json"
        suffix += 1
    return candidate


def _write_summary(path, summary):
    if path is None:
        return
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


RUN_SPECIFIC_OUTPUTS = {
    "analysis/generate_move_coverage_report.py": "move_coverage_report.json",
    "analysis/compare_ground_move_expansion.py": "ground_move_expansion_comparison.json",
    "analysis/compare_striking_move_expansion.py": "striking_move_expansion_comparison.json",
    "analysis/compare_bottom_move_expansion.py": "bottom_move_expansion_comparison.json",
}


def _run_specific_arguments(script, arguments, summary_path):
    """Route known diagnostic outputs beside a retained run summary."""
    arguments = list(arguments)
    filename = RUN_SPECIFIC_OUTPUTS.get(script)
    if summary_path is None or not filename:
        return tuple(arguments), None
    artifact_dir = summary_path.parent / f"{summary_path.stem}-artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output = artifact_dir / filename
    if "--output" in arguments:
        arguments[arguments.index("--output") + 1] = str(output)
    else:
        arguments.extend(("--output", str(output)))
    return tuple(arguments), output


def run(argv=None, *, run_process=subprocess.run, clock=time.perf_counter):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suites", nargs="*", help="Exact registered suite paths; omit for the full manifest.")
    parser.add_argument("--summary-dir", help="Optional directory for a unique source-bound JSON run summary.")
    parser.add_argument("--run-id", help="Optional readable summary filename stem; collisions receive a suffix.")
    options = parser.parse_args(sys.argv[1:] if argv is None else argv)
    requested_list = list(options.suites)
    requested = set(requested_list)
    known = {script for script, _arguments in SUITES}
    unknown = requested - known
    summary_path = _summary_path(options.summary_dir, options.run_id) if options.summary_dir else None
    raw_selected = tuple((script, arguments) for script, arguments in SUITES if not requested or script in requested)
    selected = tuple(
        (script, *_run_specific_arguments(script, arguments, summary_path))
        for script, arguments in raw_selected
    )
    summary = {
        "schema_version": 1,
        "run_id": summary_path.stem if summary_path else str(options.run_id or ""),
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "finished_at_utc": None,
        "interpreter": sys.executable,
        "requested": requested_list,
        "selection_mode": "explicit" if requested else "full_manifest",
        "unknown_suites": sorted(unknown),
        "source_identity": source_identity(),
        "overall_status": "invalid_selection" if unknown else "running",
        "exit_code": 2 if unknown else None,
        "suites": [
            {"script": script, "arguments": list(arguments), "status": "not_run", "duration_seconds": None,
             "exit_code": None, "artifact": str(artifact) if artifact else None, "artifact_sha256": None}
            for script, arguments, artifact in selected
        ],
    }
    _write_summary(summary_path, summary)
    if unknown:
        print("Unknown suite(s): " + ", ".join(sorted(unknown)), file=sys.stderr)
        summary["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        _write_summary(summary_path, summary)
        if summary_path:
            print(f"Run summary: {summary_path}")
        return 2
    exit_code = 0
    try:
        for index, (script, arguments, artifact) in enumerate(selected):
            row = summary["suites"][index]
            started = clock()
            with tempfile.TemporaryDirectory(prefix="mma_warriors_regression_") as temp_dir:
                print(f"\n=== {script} ===", flush=True)
                try:
                    completed = run_process(
                        [sys.executable, str(ROOT / script), *arguments],
                        cwd=ROOT,
                        env=isolated_environment(temp_dir),
                    )
                except KeyboardInterrupt:
                    row.update(status="interrupted", duration_seconds=round(clock() - started, 6), exit_code=130)
                    summary["overall_status"] = "interrupted"
                    exit_code = 130
                    raise
            row.update(
                status="passed" if completed.returncode == 0 else "failed",
                duration_seconds=round(clock() - started, 6),
                exit_code=int(completed.returncode),
            )
            if artifact and artifact.exists():
                row["artifact_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
            _write_summary(summary_path, summary)
            if completed.returncode:
                print(f"\nFAILED: {script} (isolated runtime data was removed)", file=sys.stderr)
                summary["overall_status"] = "failed"
                exit_code = int(completed.returncode)
                break
        else:
            summary["overall_status"] = "passed"
            print("\nALL REQUESTED ISOLATED REGRESSION SUITES PASSED")
    except KeyboardInterrupt:
        print("\nINTERRUPTED: isolated runtime data was removed", file=sys.stderr)
    finally:
        summary["exit_code"] = exit_code
        summary["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        _write_summary(summary_path, summary)
        if summary_path:
            print(f"Run summary: {summary_path}")
    return exit_code


def main():
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
