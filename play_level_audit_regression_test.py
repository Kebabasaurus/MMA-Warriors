"""Regression coverage for isolated long-run audit checkpoints."""

import json
import inspect
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from admin import (
    AdminMixin,
    PLAY_AUDIT_DEFAULT_TIME_LIMIT_SECONDS,
    PLAY_AUDIT_MAX_TIME_LIMIT_SECONDS,
    PLAY_AUDIT_MIN_TIME_LIMIT_SECONDS,
    _audit_collection_count,
)
from play_level_audit import (
    AuditCheckpointError,
    append_measurement,
    audit_balance_findings,
    audit_hard_invariant_findings,
    audit_measurement_evidence_findings,
    build_audit_identity,
    build_audit_measurement,
    build_audit_report_accounting,
    build_calendar_timing_measurement,
    decode_rng_state,
    make_checkpoint,
    read_checkpoint,
    validate_checkpoint,
    write_checkpoint_atomic,
)
import play_level_audit


class PlayLevelAuditCheckpointTests(unittest.TestCase):
    def identity(self, root, *, target_weeks=8, config=None):
        return build_audit_identity(
            seed=260712,
            target_weeks=target_weeks,
            configuration=config or {"rules": {"drug_testing": "Standard"}},
            source_root=root,
            source_paths=("constants.py", "world.py"),
            native_profile="release",
        )

    def test_default_source_inventory_covers_reader_and_testing_contracts(self):
        self.assertIn("views.py", play_level_audit.DEFAULT_SOURCE_PATHS)
        self.assertIn("drug_testing_catalogue.py", play_level_audit.DEFAULT_SOURCE_PATHS)

    def checkpoint(self, identity, *, completed=4):
        state = random.getstate()
        return make_checkpoint(
            identity=identity,
            completed_weeks=completed,
            target_weeks=identity["target_weeks"],
            rng_state=state,
            world_state={"month": 2, "week": 1, "roster": [{"id": "f-1"}]},
            methods={"Decision": 2},
            snapshots=[{"year": 2026, "active": 1}],
            output_cursor={"last_line": 7},
        )

    def test_audit_sport_event_count_accepts_live_counter_and_legacy_collection(self):
        """Yearly reports accept the live combat-sport counter shape."""
        self.assertEqual(_audit_collection_count(0), 0)
        self.assertEqual(_audit_collection_count(7), 7)
        self.assertEqual(_audit_collection_count([{"event_id": "e-1"}]), 1)
        self.assertEqual(_audit_collection_count({"event_id": "e-1"}), 1)
        self.assertEqual(_audit_collection_count(True), 0)
        self.assertEqual(_audit_collection_count("malformed"), 0)

    def test_play_audit_seed_is_explicit_and_checkpoint_bound(self):
        audit = AdminMixin()
        audit.play_audit_seed = 987654
        identity = audit.play_audit_identity(2)
        self.assertEqual(identity["seed"], 987654)
        self.assertIn("play_audit_987654_2y.checkpoint.json", str(audit.play_audit_checkpoint_path(2)))
        self.assertEqual(audit.play_audit_seed_value(0), 1)
        self.assertEqual(audit.play_audit_seed_value("bad"), 260712)

    def test_play_audit_time_limit_is_bounded_and_defaults_safely(self):
        audit = AdminMixin()
        self.assertEqual(
            audit.play_audit_time_limit_value(),
            PLAY_AUDIT_DEFAULT_TIME_LIMIT_SECONDS,
        )
        self.assertEqual(
            audit.play_audit_time_limit_value(1),
            PLAY_AUDIT_MIN_TIME_LIMIT_SECONDS,
        )
        self.assertEqual(
            audit.play_audit_time_limit_value(999999),
            PLAY_AUDIT_MAX_TIME_LIMIT_SECONDS,
        )
        self.assertEqual(
            audit.play_audit_time_limit_value("not-a-number"),
            PLAY_AUDIT_DEFAULT_TIME_LIMIT_SECONDS,
        )

    def test_play_audit_time_limit_decision_is_monotonic_and_bounded(self):
        audit = AdminMixin()
        self.assertFalse(audit.play_audit_time_limit_reached(100.0, 300, now=399.9))
        self.assertTrue(audit.play_audit_time_limit_reached(100.0, 300, now=400.0))
        # Invalid clocks fail closed; the weekly loop can still retain its
        # exact state rather than claiming a timeout from malformed metadata.
        self.assertFalse(audit.play_audit_time_limit_reached("bad", 300, now=10_000.0))
        self.assertFalse(audit.play_audit_time_limit_reached(100.0, "bad", now=100.0))
        self.assertTrue(
            audit.play_audit_time_limit_reached(100.0, 1, now=130.0),
            "the minimum 30-second limit must be applied before comparison",
        )

    def test_play_audit_status_reports_elapsed_and_remaining_budget(self):
        source = inspect.getsource(AdminMixin.run_play_level_audit)
        self.assertIn("elapsed_seconds", source)
        self.assertIn("remaining_seconds", source)
        self.assertIn("s elapsed /", source)

    def test_time_limited_checkpoint_retains_reason_and_limit(self):
        root = Path(__file__).resolve().parent
        identity = self.identity(root)
        payload = make_checkpoint(
            identity=identity,
            completed_weeks=4,
            target_weeks=identity["target_weeks"],
            rng_state=random.getstate(),
            world_state={"month": 2, "week": 1},
            status="time_limit",
            time_limit_seconds=300,
            stop_reason="time_limit",
        )
        self.assertEqual(payload["status"], "time_limit")
        self.assertEqual(payload["time_limit_seconds"], 300)
        self.assertEqual(payload["stop_reason"], "time_limit")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.checkpoint.json"
            write_checkpoint_atomic(path, payload)
            loaded = validate_checkpoint(read_checkpoint(path), identity)
        self.assertEqual(loaded["time_limit_seconds"], 300)
        self.assertEqual(loaded["stop_reason"], "time_limit")

    def test_raw_report_round_trip_is_seed_bound_and_read_only(self):
        audit = AdminMixin()
        audit.play_audit_seed = 987654
        with tempfile.TemporaryDirectory() as directory, patch("admin.LOG_DIR", Path(directory)):
            report = "1-YEAR PLAY-LEVEL AUDIT\nSeed: 987654\nHARD INVARIANT FINDINGS: none"
            path = audit.write_play_audit_report(report, years=1)
            self.assertTrue(path.name.endswith("987654_1y.report.txt"))
            self.assertEqual(audit.read_play_audit_report(years=1), report)
            self.assertEqual(path.read_text(encoding="utf-8"), report)

    def test_audit_manifest_is_retry_idempotent_and_retains_source_bound_paths(self):
        audit = AdminMixin()
        identity = self.identity(Path(__file__).resolve().parent, target_weeks=48)
        with tempfile.TemporaryDirectory() as directory, patch("admin.LOG_DIR", Path(directory)):
            first = audit.write_play_audit_manifest_row(
                identity=identity,
                completed_weeks=24,
                status="paused",
                report_path=Path(directory) / "first.report.txt",
                checkpoint_path=Path(directory) / "first.checkpoint.json",
            )
            second = audit.write_play_audit_manifest_row(
                identity=identity,
                completed_weeks=48,
                status="complete",
                report_path=Path(directory) / "second.report.txt",
                checkpoint_path=Path(directory) / "second.checkpoint.json",
            )
            rows = audit.read_play_audit_manifest()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["run_key"], first["run_key"])
        self.assertEqual(rows[0]["run_key"], second["run_key"])
        self.assertEqual(rows[0]["seed"], 260712)
        self.assertEqual(rows[0]["target_weeks"], 48)
        self.assertEqual(rows[0]["completed_weeks"], 48)
        self.assertEqual(rows[0]["status"], "complete")
        self.assertEqual(rows[0]["identity_digest"], identity["identity_digest"])
        self.assertEqual(rows[0]["source_digest"], identity["source_digest"])
        self.assertTrue(rows[0]["report_path"].endswith("second.report.txt"))
        self.assertTrue(rows[0]["checkpoint_path"].endswith("second.checkpoint.json"))

    def test_audit_manifest_reader_is_bounded_and_does_not_repair_malformed_rows(self):
        audit = AdminMixin()
        with tempfile.TemporaryDirectory() as directory, patch("admin.LOG_DIR", Path(directory)):
            path = audit.play_audit_manifest_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"schema_version": 1, "rows": [{"run_key": str(index)} for index in range(205)]}
            raw = json.dumps(payload, indent=2)
            path.write_text(raw, encoding="utf-8")
            rows = audit.read_play_audit_manifest()
            self.assertEqual(len(rows), 200)
            self.assertEqual(rows[0]["run_key"], "5")
            self.assertEqual(path.read_text(encoding="utf-8"), raw)
            malformed = "{\"rows\": \"not-a-list\"}"
            path.write_text(malformed, encoding="utf-8")
            self.assertEqual(audit.read_play_audit_manifest(), [])
            self.assertEqual(path.read_text(encoding="utf-8"), malformed)

    def test_audit_manifest_summary_distinguishes_completion_source_and_reports(self):
        audit = AdminMixin()
        audit.read_play_audit_manifest = lambda: [
            {"seed": 1, "target_weeks": 48, "completed_weeks": 48, "status": "complete", "source_digest": "source-a", "report_path": "report-a.txt"},
            {"seed": 2, "target_weeks": 96, "completed_weeks": 48, "status": "paused", "source_digest": "source-old", "report_path": "missing.txt"},
            {"seed": 3, "target_weeks": 48, "completed_weeks": 12, "status": "failed_invariant", "source_digest": "source-a", "report_path": "report-a.txt"},
        ]
        audit.play_audit_identity = lambda _years, seed=None: {"source_digest": "source-a" if seed in (1, 3) else "source-current"}
        summary = audit.play_audit_manifest_summary()
        self.assertEqual(summary["rows"], 3)
        self.assertEqual(summary["complete"], 1)
        self.assertEqual(summary["paused"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["unique_seeds"], 3)
        self.assertEqual(summary["current_source"], 2)
        self.assertEqual(summary["reports_available"], 0)
        self.assertEqual(summary["threshold_policy"], "Pending approval")
        self.assertEqual(summary["current_source_recipes"], [{
            "years": 1, "complete_runs": 1, "unique_seeds": 1, "seeds": [1],
        }])

    def test_audit_manifest_summary_counts_time_limited_runs(self):
        audit = AdminMixin()
        audit.read_play_audit_manifest = lambda: [
            {"seed": 1, "target_weeks": 48, "completed_weeks": 12, "status": "time_limit", "source_digest": "source-a"},
        ]
        audit.play_audit_identity = lambda _years, seed=None: {"source_digest": "source-a"}
        summary = audit.play_audit_manifest_summary()
        self.assertEqual(summary["time_limited"], 1)
        self.assertEqual(summary["failed"], 0)

    def test_audit_manifest_summary_groups_complete_current_source_recipes_by_seed(self):
        audit = AdminMixin()
        audit.read_play_audit_manifest = lambda: [
            {"seed": 10, "target_weeks": 96, "completed_weeks": 96, "status": "complete", "source_digest": "source-a"},
            {"seed": 11, "target_weeks": 96, "completed_weeks": 96, "status": "complete", "source_digest": "source-a"},
            {"seed": 12, "target_weeks": 96, "completed_weeks": 48, "status": "paused", "source_digest": "source-a"},
            {"seed": 13, "target_weeks": 48, "completed_weeks": 48, "status": "complete", "source_digest": "source-a"},
        ]
        audit.play_audit_identity = lambda _years, seed=None: {"source_digest": "source-a"}
        summary = audit.play_audit_manifest_summary()
        self.assertEqual(summary["current_source_recipes"], [
            {"years": 1, "complete_runs": 1, "unique_seeds": 1, "seeds": [13]},
            {"years": 2, "complete_runs": 2, "unique_seeds": 2, "seeds": [10, 11]},
        ])

    def test_fresh_and_resumed_checkpoint_round_trip_preserves_rng_and_progress(self):
        root = Path(__file__).resolve().parent
        identity = self.identity(root)
        expected_rng = random.getstate()
        payload = self.checkpoint(identity)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.checkpoint.json"
            write_checkpoint_atomic(path, payload)
            loaded = validate_checkpoint(read_checkpoint(path), identity)
        self.assertEqual(loaded["completed_weeks"], 4)
        self.assertEqual(loaded["methods"], {"Decision": 2})
        self.assertEqual(decode_rng_state(loaded["rng_state"]), expected_rng)
        self.assertEqual(loaded["world_state"]["roster"][0]["id"], "f-1")

    def test_source_or_configuration_mismatch_is_rejected(self):
        root = Path(__file__).resolve().parent
        identity = self.identity(root)
        payload = self.checkpoint(identity)
        changed_source = self.identity(root, config={"rules": {"drug_testing": "Strict"}})
        with self.assertRaisesRegex(AuditCheckpointError, "identity"):
            validate_checkpoint(payload, changed_source)

    def test_atomic_failure_cleans_temporary_file_and_leaves_destination(self):
        root = Path(__file__).resolve().parent
        identity = self.identity(root)
        payload = self.checkpoint(identity)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.checkpoint.json"
            path.write_text("previous", encoding="utf-8")
            with patch("play_level_audit.os.replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    write_checkpoint_atomic(path, payload)
            self.assertEqual(path.read_text(encoding="utf-8"), "previous")
            self.assertEqual(list(Path(directory).glob(".*.tmp")), [])

    def test_measurements_are_bounded_and_defensive(self):
        root = Path(__file__).resolve().parent
        identity = self.identity(root)
        payload = self.checkpoint(identity)
        rows = append_measurement(payload, {"year": 2027, "active": 3}, limit=1)
        self.assertEqual(rows["snapshots"], [{"year": 2027, "active": 3}])
        rows["world_state"]["roster"].append({"id": "mutated"})
        self.assertEqual(payload["world_state"]["roster"], [{"id": "f-1"}])

    def test_read_shape_rejects_malformed_json_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
            with self.assertRaises(AuditCheckpointError):
                read_checkpoint(path)

    def test_invalid_schema_type_fails_with_checkpoint_error(self):
        with self.assertRaises(AuditCheckpointError):
            from play_level_audit import validate_checkpoint_shape
            validate_checkpoint_shape({"schema_version": "not-a-number"})

    def test_yearly_measurement_keeps_company_division_backlog_and_archive_detail(self):
        state = {
            "roster": [],
            "promotions": [{
                "promotion_id": "promo-1", "name": "Player FC", "cash": 125000,
                "stability": 74,
                "roster": [{"fighter_id": "f-1", "gender": "Female", "weight": "Flyweight"}],
                "belts": {"Female|Flyweight": "f-1"},
                "staff": [{"staff_id": "s-1"}],
                "scheduled_events": [{"event_id": "event-1"}],
                "super_event_offers": [{"id": "se-1", "status": "Planning"}],
                "finance": {"week_transactions": [{"id": "tx-1"}], "weekly_history": [{"week": 1}]},
            }],
            "staff": [{"staff_id": "player-staff", "salary": 2_000}],
            "foundation": {"historical": {"collections": {"membership": [{"membership_id": "m-1"}]}}},
            "booking_workbench": {"proposals": [{"proposal_id": "p-1"}]},
            "contract_batch_workbench": {"rows": [{"fighter_id": "f-1"}]},
            "drug_testing_state": {"cases": [{"case_id": "c-1"}]},
            "media_primary_plan": {"status": "Planned"},
            "result_index": [{"key": "event-1"}], "result_records": [],
            "ai_event_archive": [], "player_event_archive": [], "event_log": ["event"],
        }
        result = build_audit_measurement(state, year=2027)
        self.assertEqual(result["measurement_year"], 2027)
        self.assertEqual(result["company_measurements"][0]["active_roster"], 1)
        self.assertEqual(result["company_measurements"][0]["division_counts"], {"Female:Flyweight": 1})
        self.assertEqual(result["company_measurements"][0]["eligible_title_challengers"], 0)
        self.assertEqual(result["division_counts"], {"Female:Flyweight": 1})
        self.assertEqual(result["staff_total"], 2)
        self.assertEqual(result["backlogs"]["staff_payroll_total"], 2_000)
        self.assertEqual(result["backlogs"]["staff_salary_unknown"], 1)
        self.assertEqual(result["backlogs"]["testing_cases"], 1)
        self.assertEqual(result["backlogs"]["media_plan_active"], 1)
        self.assertEqual(result["archive_sizes"]["result_index"], 1)
        self.assertEqual(result["title_holders"], 1)
        self.assertEqual(result["title_history_entries"], 0)
        self.assertEqual(result["regional_feeders"], 0)
        self.assertGreaterEqual(result["history_total"], 2)
        state["promotions"][0]["roster"].append({"fighter_id": "mutated"})
        self.assertEqual(result["company_measurements"][0]["roster_total"], 1)

    def test_yearly_measurement_retains_staff_evidence_metrics_without_mutation(self):
        state = {
            "promotions": [],
            "staff_management": {
                "work_log": [
                    {"work_id": "work-1", "operation_id": "op-1"},
                    "bad work row",
                ],
                "briefs": [{"brief_id": "brief-1"}],
                "exceptions": [None],
                "progression": {
                    "staff-1": {"credited_work_ids": ["work-1", "work-2"]},
                    "staff-bad": "legacy",
                },
            },
        }
        before = json.loads(json.dumps(state))
        result = build_audit_measurement(state, year=2027)
        self.assertEqual(state, before)
        backlogs = result["backlogs"]
        self.assertEqual(backlogs["staff_work_log"], 2)
        self.assertEqual(backlogs["staff_briefs"], 1)
        self.assertEqual(backlogs["staff_exceptions"], 1)
        self.assertEqual(backlogs["staff_progression_rows"], 2)
        self.assertEqual(backlogs["staff_progression_credits"], 2)
        self.assertEqual(backlogs["staff_malformed_evidence_rows"], 3)

        malformed = {
            "staff_management": {
                "work_log": "bad",
                "briefs": None,
                "exceptions": {},
                "progression": [],
            },
        }
        malformed_result = build_audit_measurement(malformed, year=2027)
        self.assertEqual(malformed_result["backlogs"]["staff_malformed_evidence_rows"], 4)

    def test_yearly_measurement_bounds_malformed_staff_salary_without_mutation(self):
        state = {
            "staff": [
                {"staff_id": "valid", "salary": 4_500},
                {"staff_id": "bad", "salary": "unknown"},
                {"staff_id": "nonfinite", "salary": float("inf")},
                "legacy staff",
            ],
        }
        before = json.loads(json.dumps(state, allow_nan=True))
        result = build_audit_measurement(state, year=2027)
        self.assertEqual(state, before)
        self.assertEqual(result["staff_total"], 4)
        self.assertEqual(result["backlogs"]["staff_payroll_total"], 4_500)
        self.assertEqual(result["backlogs"]["staff_salary_unknown"], 3)

    def test_yearly_measurement_reports_explicit_overdue_commitments_without_mutation(self):
        state = {
            "month": 8, "week": 2,
            "roster": [
                {"fighter_id": "promise-1", "main_event_promise": True, "promise_deadline_month": 7,
                 "career_arc": {"status": "active", "deadline_month": 7}},
                {"fighter_id": "current-1", "top_opponent_promise": True, "promise_deadline_month": 8},
            ],
            "promotions": [{
                "promotion_id": "promo-1",
                "super_event_offers": [
                    {"id": "offer-overdue", "status": "Planning", "deadline_month": 7},
                    {"id": "offer-open", "status": "Planning", "deadline_month": 8},
                    {"id": "offer-closed", "status": "Expired", "deadline_month": 1},
                ],
                "roster": [],
                "academy": {"prospects": [{"prospect_id": "prospect-1", "promise": {"deadline_week": 28, "fulfilled": False}}]},
            }],
            "super_event_offers": [{"id": "top-overdue", "status": "Offered", "deadline_month": 6}],
            "booking_workbench": {
                "proposals": [
                    {"proposal_id": "booking-overdue", "status": "Draft", "target_month": 7, "target_week": 4},
                    {"proposal_id": "booking-committed", "status": "Committed", "target_month": 1, "target_week": 1},
                ],
                "locked_slot_proposals": [{"proposal_id": "locked-overdue", "status": "Draft", "target_month": 7, "target_week": 1}],
                "medical_plans": [{"plan_id": "medical-overdue", "status": "Tentative", "target_month": 7, "target_week": 2}],
            },
            "media_primary_plan": {"status": "Draft", "deadline": {"month": 7, "week": 4}},
            "staff_management": {"briefs": [
                {"brief_id": "staff-overdue", "status": "Committed", "due": {"month": 7, "week": 3}},
                {"brief_id": "staff-current", "status": "Committed", "due": {"month": 8, "week": 2}},
            ]},
            "owner_goals": [
                {"goal_id": "goal-overdue", "status": "Active", "deadline": 7},
                {"goal_id": "goal-complete", "status": "Complete", "deadline": 1},
            ],
        }
        before = json.loads(json.dumps(state))
        result = build_audit_measurement(state, year=2027)
        self.assertEqual(state, before)
        backlogs = result["backlogs"]
        self.assertEqual(backlogs["overdue_commitments"], 11)
        self.assertEqual(backlogs["overdue_commitment_breakdown"], {
            "super_event_offers": 2,
            "booking_proposals": 1,
            "locked_slot_proposals": 1,
            "medical_plans": 1,
            "media_plans": 1,
            "staff_briefs": 1,
            "owner_goals": 1,
            "career_promises": 1,
            "career_arcs": 1,
            "academy_promises": 1,
        })

    def test_spectator_owner_goals_are_reported_as_paused_context_not_overdue_work(self):
        state = {
            "month": 8, "week": 2, "spectator_mode": True,
            "owner_goals": [
                {"goal": "Legacy objective", "status": "Active", "deadline": 1},
                {"goal": "Current objective", "status": "Active", "deadline": 8},
                {"goal": "Sealed objective", "status": "Complete", "deadline": 1},
            ],
        }
        before = json.loads(json.dumps(state))
        result = build_audit_measurement(state, year=2027)
        self.assertEqual(state, before)
        self.assertEqual(result["backlogs"]["overdue_commitments"], 0)
        self.assertEqual(result["backlogs"]["overdue_commitment_breakdown"]["owner_goals"], 0)
        self.assertEqual(result["backlogs"]["spectator_paused_owner_goals"], 1)

    def test_overdue_commitment_reader_fails_closed_for_missing_clock_and_malformed_deadlines(self):
        state = {
            "month": "not-a-month", "week": 2,
            "super_event_offers": [{"status": "Planning", "deadline_month": 1}],
            "media_primary_plan": {"status": "Draft", "deadline": {"month": "unknown", "week": 1}},
            "staff_management": {"briefs": [{"status": "Committed", "due": None}]},
        }
        before = json.loads(json.dumps(state))
        result = build_audit_measurement(state, year=2027)
        self.assertEqual(state, before)
        self.assertEqual(result["backlogs"]["overdue_commitments"], 0)
        self.assertTrue(all(value == 0 for value in result["backlogs"]["overdue_commitment_breakdown"].values()))

    def test_calendar_timing_measurement_is_bounded_and_fails_closed(self):
        timings = [
            ("Cards", 0.25),
            {"label": "Cards", "seconds": 0.75},
            ("Finance", "bad"),
            ("Malformed", float("inf")),
            ("Negative", -1),
            ("Boolean", True),
            ("", 0.5),
        ]
        before = list(timings)
        result = build_calendar_timing_measurement(timings)
        self.assertEqual(timings, before)
        self.assertEqual(result["count"], 3)
        self.assertAlmostEqual(result["total_seconds"], 1.5)
        self.assertAlmostEqual(result["by_task"]["Cards"]["total_seconds"], 1.0)
        self.assertEqual(result["by_task"]["Unknown task"]["count"], 1)

    def test_yearly_measurement_retains_recruit_challenger_vacancy_and_expiry_evidence(self):
        state = {
            "month": 8, "week": 2,
            "free_agents": [{"fighter_id": "free-1"}, {"fighter_id": "free-2"}],
            "roster": [
                {"fighter_id": "eligible-1", "record_w": 4, "record_l": 3, "career_win_streak": 0},
                {"fighter_id": "eligible-2", "record_w": 1, "record_l": 0, "career_win_streak": 1},
                {"fighter_id": "champion", "record_w": 5, "record_l": 0, "champion": True},
            ],
            "belts": {"Male|Lightweight": ""},
            "belt_history": {"Male|Lightweight": [{
                "action": "Vacated", "date": "Month 6 Week 2", "fighter_id": "former-1",
            }]},
            "super_event_offers": [
                {"id": "expired-1", "status": "Expired"},
                {"id": "open-1", "status": "Planning"},
            ],
            "regional_invitations": [{"invitation_id": "expired-2", "status": "Expired"}],
        }
        before = json.loads(json.dumps(state))
        result = build_audit_measurement(state, year=2027)
        self.assertEqual(state, before)
        self.assertEqual(result["free_agents"], 2)
        self.assertEqual(result["eligible_title_challengers"], 1)
        self.assertEqual(result["title_vacancies"], 1)
        self.assertEqual(result["vacancy_duration_total_weeks"], 8)
        self.assertEqual(result["vacancy_duration_max_weeks"], 8)
        self.assertEqual(result["expired_offers"], 2)

    def test_yearly_measurement_exposes_cohorts_event_coverage_and_identity_quality(self):
        state = {
            "roster": [
                {"fighter_id": "player-1", "gender": "Male", "weight": "Lightweight"},
                {"fighter_id": "player-1", "gender": "Male", "weight": "Welterweight"},
                {"gender": "Female", "weight": "Flyweight"},
            ],
            "staff": [{"staff_id": "player-staff"}],
            "scheduled_events": [{"event_id": "event-player"}],
            "promotions": [
                {
                    "promotion_id": "ai-1", "is_child_promotion": False,
                    "roster": [{"fighter_id": "ai-1", "gender": "Male", "weight": "Heavyweight"}],
                    "staff": [{"staff_id": "ai-staff"}],
                    "scheduled_events": [{"event_id": "event-ai"}],
                },
                {
                    "promotion_id": "ai-1", "is_child_promotion": True,
                    "roster": [{"fighter_id": "child-1", "gender": "Female", "weight": "Bantamweight"}],
                    "staff": [],
                    "scheduled_events": [{"event_id": "event-child"}],
                },
            ],
            "combat_sport_worlds": {
                "Boxing": {"events": [{"event_id": "event-sport"}]},
            },
            "player_combat_divisions": {
                "Boxing": {"Lightweight": {"scheduled_events": [{"event_id": "event-owned-sport"}]}},
            },
        }
        before = json.loads(json.dumps(state))
        result = build_audit_measurement(state, year=2027)
        self.assertEqual(state, before)
        self.assertEqual(result["cohort_measurements"]["player"]["active_talent"], 3)
        self.assertEqual(result["cohort_measurements"]["ai_promotions"]["active_talent"], 1)
        self.assertEqual(result["cohort_measurements"]["owned_child"]["active_talent"], 1)
        self.assertEqual(result["cohort_measurements"]["player"]["division_count"], 3)
        self.assertEqual(result["event_counts"], {
            "player_scheduled": 1,
            "ai_scheduled": 1,
            "owned_child_scheduled": 1,
            "owned_sport_scheduled": 1,
        })
        self.assertEqual(result["identity_quality"]["fighter_id"]["duplicates"], 1)
        self.assertEqual(result["identity_quality"]["fighter_id"]["missing"], 1)
        self.assertEqual(result["identity_quality"]["promotion_id"]["duplicates"], 1)
        self.assertEqual(result["identity_quality"]["event_id"]["duplicates"], 0)
        evidence = dict(result)
        evidence["calendar_task_timings"] = {
            "count": 1, "total_seconds": 0.25, "max_seconds": 0.25, "by_task": {"Cards": {"count": 1, "total_seconds": 0.25, "max_seconds": 0.25}},
        }
        self.assertEqual(audit_measurement_evidence_findings([evidence]), [])

    def test_measurement_evidence_audit_reports_missing_and_inconsistent_rows_without_mutation(self):
        rows = [{
            "free_agents": 2, "eligible_title_challengers": 3, "title_vacancies": 1,
            "vacancy_duration_total_weeks": 4, "vacancy_duration_max_weeks": 6,
            "expired_offers": 0,
            "calendar_task_timings": {"count": 2, "total_seconds": 1.0, "max_seconds": 1.5, "by_task": {}},
        }, {"free_agents": "bad", "calendar_task_timings": None}]
        before = json.loads(json.dumps(rows))
        findings = audit_measurement_evidence_findings(rows)
        self.assertEqual(rows, before)
        codes = {row["code"] for row in findings}
        self.assertTrue({
            "invalid_vacancy_duration", "invalid_calendar_task_timings",
            "missing_yearly_measurement", "invalid_yearly_measurement",
        } <= codes)
        self.assertTrue(all(row["severity"] == "warning" for row in findings))

    def test_hard_invariant_scan_is_read_only_and_reports_only_explicit_breaks(self):
        state = {
            "roster": [{"fighter_id": "f-1"}],
            "free_agents": [{"fighter_id": "f-1"}],
            "promotions": [{
                "name": "Child", "roster": [], "loaned_fighter_ids": ["missing"],
                "finance": {"week_transactions": [{"id": "tx-1"}, {"id": "tx-1"}]},
            }],
            "scheduled_events": [{"event_id": "event-1", "fights": [{"fighter_ids": ["f-1", "missing"]}]}],
            "result_index": [{"key": "event-1"}, {"key": "event-1"}],
            "foundation": {"historical": {"collections": {"membership": [
                {"membership_id": "m-1"}, {"membership_id": "m-1"},
            ]}}},
            "rules": {"remaining_obligation": -1},
        }
        before = json.loads(json.dumps(state))
        findings = audit_hard_invariant_findings(state)
        self.assertEqual(state, before)
        codes = {row["code"] for row in findings}
        self.assertTrue({
            "duplicate_fighter_identity", "duplicate_settlement_transaction",
            "duplicate_result_index", "duplicate_membership_fact",
            "negative_remaining_obligation", "orphan_scheduled_fighter",
            "orphan_loan_reference",
        } <= codes)

    def test_hard_invariant_scan_reports_staff_identity_and_term_breaks(self):
        state = {
            "staff": [{"staff_id": "staff-1", "role": "Scout", "salary": 1000, "contract_months": 6}],
            "staff_candidates": [{"staff_id": "staff-1", "role": "Scout", "salary": 1000, "contract_months": 6},
                                 {"role": "Marketing", "salary": -1, "contract_months": "unknown"}],
            "promotions": [{"name": "AI FC", "staff": [{"staff_id": "staff-2", "salary": 900, "contract_months": -2}]}],
        }
        before = json.loads(json.dumps(state))
        findings = audit_hard_invariant_findings(state)
        self.assertEqual(state, before)
        codes = {row["code"] for row in findings}
        self.assertTrue({
            "duplicate_staff_identity", "staff_missing_identity", "negative_staff_term",
            "invalid_staff_term",
        } <= codes)

    def test_spectator_player_staff_projection_is_not_reported_as_duplicate_employment(self):
        state = {
            "spectator_mode": True,
            "staff": [{"staff_id": "STF-player", "name": "Player Staff", "role": "Scout", "salary": 100, "contract_months": 12}],
            "staff_candidates": [],
            "promotions": [{
                "name": "Former Player Promotion",
                "staff": [{"staff_id": "STF-player", "name": "Player Staff", "role": "Scout", "salary": 100, "contract_months": 12}],
            }],
        }
        findings = audit_hard_invariant_findings(state)
        self.assertFalse(any(row["code"] == "duplicate_staff_identity" for row in findings))

    def test_hard_invariant_scan_reports_staff_work_identity_and_orphaned_progression(self):
        state = {
            "staff_management": {
                "work_log": [
                    {"work_id": "work-1", "operation_id": "op-1", "status": "Executed"},
                    {"work_id": "work-1", "operation_id": "op-1", "status": "Recommendation"},
                    {"status": "Executed", "operation_id": "op-3"},
                    "malformed work",
                ],
                "progression": {
                    "staff-1": {"credited_work_ids": ["work-1", "missing-work"]},
                    "staff-bad": "legacy",
                },
            },
        }
        before = json.loads(json.dumps(state))
        findings = audit_hard_invariant_findings(state)
        self.assertEqual(state, before)
        codes = {row["code"] for row in findings}
        self.assertTrue({
            "duplicate_staff_work_id", "duplicate_staff_operation_id",
            "staff_missing_work_id", "invalid_staff_work_record",
            "orphan_staff_progression_credit", "invalid_staff_progression_record",
        } <= codes)

    def test_report_accounting_exposes_coverage_gaps_without_inventing_fights(self):
        result = build_audit_report_accounting(
            {"Decision": 4, "Submission": 2},
            [{"year": 2027}],
            completed_weeks=96,
            target_weeks=144,
        )
        self.assertEqual(result["fights_total"], 6)
        self.assertEqual(result["expected_year_boundaries"], 2)
        self.assertFalse(result["complete"])
        self.assertTrue(any("expected 2" in error for error in result["errors"]))

    def test_balance_audit_flags_extinction_title_starvation_cash_and_history(self):
        rows = [
            {
                "year": 2027, "active": 24, "viable": 2, "title_holders": 2,
                "avg_cash": 5_000_000, "history_total": 120, "free_agents": 80,
                "regional_feeders": 2,
            },
            {
                "year": 2028, "active": 0, "viable": 0, "title_holders": 0,
                "avg_cash": 600_000_000, "history_total": 120, "free_agents": 4,
                "regional_feeders": 0,
            },
            {
                "year": 2029, "active": 0, "viable": 0, "title_holders": 0,
                "avg_cash": 600_000_000, "history_total": 300_000, "free_agents": 4,
                "regional_feeders": 0,
            },
        ]
        before = json.loads(json.dumps(rows))
        findings = audit_balance_findings(rows, target_years=3)
        self.assertEqual(rows, before)
        codes = {row["code"] for row in findings}
        self.assertTrue({
            "roster_extinction", "promotion_extinction", "title_starvation",
            "runaway_cash", "unbounded_history_growth", "free_agent_starvation",
            "regional_feeder_shortage",
        } <= codes)
        self.assertTrue(all("severity" in row and "path" in row and "detail" in row for row in findings))

    def test_balance_audit_accepts_a_healthy_multi_generation_sample(self):
        rows = [
            {
                "year": year, "active": 410 + year, "viable": 9,
                "title_holders": 48, "avg_cash": 8_000_000 + year * 10_000,
                "history_total": (year - 2026) * 300, "free_agents": 90,
                "regional_feeders": 4,
            }
            for year in range(2027, 2030)
        ]
        self.assertEqual(audit_balance_findings(rows, target_years=3), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
