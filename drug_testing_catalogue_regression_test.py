"""Regression coverage for the J5 provider/policy planning boundary."""

import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from views import ViewMixin
from persistence import atomic_write_split_save, load_save_payload


class TestingDeskHarness(ViewMixin):
    def __init__(self):
        self.month, self.week = 3, 2
        self.rules = {"drug_testing": "Standard"}
        self.finance = {"drug_test_cost": 2500}
        self.drug_testing_state = self._default_drug_testing_state()


class DrugTestingCatalogueRegressionTests(unittest.TestCase):
    def test_catalogues_are_stable_and_defensive(self):
        app = TestingDeskHarness()
        providers = app.drug_testing_provider_catalogue()
        policies = app.drug_testing_policy_catalogue()
        self.assertEqual([row["provider_id"] for row in providers], [
            "legacy-promotion-testing", "regional-integrity-labs", "national-compliance-network",
        ])
        self.assertEqual([row["policy_id"] for row in policies], ["None", "Standard", "Strict", "Olympic"])
        for row in providers:
            for key in ("provider_id", "name", "tier", "effectiveness", "coverage", "turnaround", "cost_multiplier", "supported_tests", "confirmation", "false_positive_handling", "notes"):
                self.assertIn(key, row)
        for row in policies:
            for key in ("policy_id", "name", "strictness", "coverage", "confirmation", "description"):
                self.assertIn(key, row)
        providers[0]["name"] = "mutated"
        self.assertEqual(app.drug_testing_provider_catalogue()[0]["name"], "Promotion Testing Desk")

    def test_quote_is_pure_and_more_effective_options_cost_more(self):
        app = TestingDeskHarness()
        before_state = repr(app.drug_testing_state)
        before_rng = random.getstate()
        quotes = [app.drug_testing_quote(provider_id=row["provider_id"], sample_count=6) for row in app.drug_testing_provider_catalogue()]
        self.assertEqual([quote["amount"] for quote in quotes], [15_000, 18_750, 22_500])
        self.assertEqual(quotes[0]["base_subtotal"], 15_000)
        self.assertEqual(quotes[0]["provider_adjustment"], 0)
        self.assertEqual(quotes[1]["provider_adjustment"], 3_750)
        self.assertEqual(quotes[2]["provider_adjustment"], 7_500)
        self.assertEqual([quote["planning_only"] for quote in quotes], [True, True, True])
        self.assertTrue(all("no cash" in " ".join(quote["assumptions"]).lower() for quote in quotes))
        self.assertEqual(repr(app.drug_testing_state), before_state)
        self.assertEqual(random.getstate(), before_rng)

    def test_quote_fails_closed_for_nonfinite_inputs_without_mutation(self):
        app = TestingDeskHarness()
        before_state = repr(app.drug_testing_state)
        before_rng = random.getstate()
        app.finance["drug_test_cost"] = float("inf")
        quote = app.drug_testing_quote(
            provider_id="national-compliance-network",
            sample_count=float("nan"),
        )
        self.assertEqual(quote["sample_count"], 0)
        self.assertEqual(quote["requested_sample_count"], 0)
        self.assertEqual(quote["base_cost_per_sample"], 0)
        self.assertEqual(quote["base_subtotal"], 0)
        self.assertEqual(quote["provider_adjustment"], 0)
        self.assertEqual(quote["amount"], 0)
        self.assertEqual(repr(app.drug_testing_state), before_state)
        self.assertEqual(random.getstate(), before_rng)

    def test_commission_preview_exposes_approval_cost_and_is_pure(self):
        app = TestingDeskHarness()
        app.roster = [object()]
        app.cash = 20_000
        app.set_drug_testing_provider_selection("regional-integrity-labs", 4)
        before_state = repr(app.drug_testing_state)
        before_rules = repr(app.rules)
        before_cash = app.cash
        before_rng = random.getstate()
        preview = app.drug_testing_commission_preview()
        self.assertTrue(preview["available"])
        self.assertEqual(preview["provider_id"], "regional-integrity-labs")
        self.assertEqual(preview["policy_id"], "Standard")
        self.assertEqual(preview["requested_samples"], 4)
        self.assertEqual(preview["sample_count"], 1)
        self.assertEqual(preview["quoted_total"], 3_125)
        self.assertEqual(preview["estimated_charge"], 3_125)
        self.assertEqual(preview["available_cash"], 20_000)
        self.assertEqual(repr(app.drug_testing_state), before_state)
        self.assertEqual(repr(app.rules), before_rules)
        self.assertEqual(app.cash, before_cash)
        self.assertEqual(random.getstate(), before_rng)

    def test_commission_preview_reports_blockers_without_repairing_state(self):
        app = TestingDeskHarness()
        app.cash = 100
        app.drug_testing_state["provider_id"] = "retired-provider"
        before_state = repr(app.drug_testing_state)
        preview = app.drug_testing_commission_preview()
        self.assertFalse(preview["available"])
        self.assertTrue(any("provider" in blocker.lower() for blocker in preview["blockers"]))
        self.assertEqual(repr(app.drug_testing_state), before_state)

    def test_commission_confirmation_rejects_a_stale_quote(self):
        app = TestingDeskHarness()
        app.roster = [object()]
        app.cash = 10_000
        notices = []
        app._staff_status_notice = lambda message, warning=False: notices.append((message, warning))
        before_cases = list(app.drug_testing_state["cases"])

        def change_settings_before_confirmation(*_args, **_kwargs):
            app.set_drug_testing_provider_selection("national-compliance-network", 1)
            return True

        with patch("views.messagebox.askyesno", side_effect=change_settings_before_confirmation), patch.object(
            app, "run_drug_tests", side_effect=AssertionError("stale quote must not commission"),
        ):
            result = app.confirm_drug_testing_commission()
        self.assertEqual(result, [])
        self.assertTrue(notices)
        self.assertIn("expired", notices[-1][0].lower())
        self.assertEqual(app.drug_testing_state["cases"], before_cases)

    def test_disabled_policy_quotes_zero_samples_and_zero_cost(self):
        app = TestingDeskHarness()
        quote = app.drug_testing_quote(policy_id="None", provider_id="national-compliance-network", sample_count=6)
        self.assertEqual(quote["sample_count"], 0)
        self.assertEqual(quote["requested_sample_count"], 6)
        self.assertEqual(quote["amount"], 0)
        self.assertEqual(quote["coverage"], "No samples")

    def test_legacy_enhanced_policy_label_is_not_silently_rewritten(self):
        app = TestingDeskHarness()
        quote = app.drug_testing_quote(policy_id="Enhanced", sample_count=6)
        self.assertEqual(quote["policy_id"], "Enhanced")
        self.assertEqual(quote["policy"], "Enhanced")
        self.assertIn("Legacy", quote["policy_coverage"])

    def test_case_workflow_separates_preliminary_alert_from_gated_outcomes(self):
        app = TestingDeskHarness()
        positive = app.record_drug_testing_case(
            type("FighterStub", (), {"fighter_id": "fighter-1", "name": "Sample"})(),
            test_id="drug-test-0003-02-000002", result="positive", policy="Standard",
        )
        negative = app.record_drug_testing_case(
            type("FighterStub", (), {"fighter_id": "fighter-2", "name": "Other"})(),
            test_id="drug-test-0003-02-000003", result="negative", policy="Standard",
        )
        before = repr(app.drug_testing_state)
        projection = app.drug_testing_case_workflow(positive["case_id"])
        self.assertEqual(projection["stages"][1]["status"], "Alert")
        self.assertEqual(projection["stages"][2]["status"], "Gated")
        self.assertIn("request_confirmation", {row["action_id"] for row in projection["next_actions"]})
        closed = app.drug_testing_case_workflow(negative["case_id"])
        self.assertEqual(closed["stages"][4]["status"], "Closed negative")
        self.assertFalse(closed["sanctions_enabled"])
        self.assertEqual(repr(app.drug_testing_state), before)

    def test_inconclusive_and_invalid_samples_remain_distinct_review_evidence(self):
        app = TestingDeskHarness()
        inconclusive = app.record_drug_testing_case(
            type("FighterStub", (), {"fighter_id": "fighter-inconclusive", "name": "Unclear"})(),
            test_id="drug-test-0003-02-000007", result="inconclusive", policy="Standard",
        )
        invalid = app.record_drug_testing_case(
            type("FighterStub", (), {"fighter_id": "fighter-invalid", "name": "Invalid"})(),
            test_id="drug-test-0003-02-000008", result="invalid_sample", policy="Standard",
        )
        self.assertEqual(inconclusive["preliminary_result"], "inconclusive")
        self.assertEqual(inconclusive["status"], "Inconclusive review")
        self.assertEqual(invalid["preliminary_result"], "invalid")
        self.assertEqual(invalid["status"], "Invalid sample")
        inconclusive_workflow = app.drug_testing_case_workflow(inconclusive["case_id"])
        invalid_workflow = app.drug_testing_case_workflow(invalid["case_id"])
        self.assertEqual(inconclusive_workflow["screening_result"], "inconclusive")
        self.assertEqual(inconclusive_workflow["stages"][1]["status"], "Inconclusive")
        self.assertEqual(inconclusive_workflow["stages"][4]["status"], "Gated")
        self.assertEqual(invalid_workflow["screening_result"], "invalid")
        self.assertEqual(invalid_workflow["stages"][1]["status"], "Invalid")
        self.assertEqual(invalid_workflow["stages"][4]["status"], "Invalid sample")
        summary = app.drug_testing_summary()
        self.assertEqual(summary["inconclusive_cases"], 1)
        self.assertEqual(summary["invalid_cases"], 1)
        self.assertEqual(summary["unresolved_cases"], 2)

    def test_case_contract_retains_event_scope_and_future_lifecycle_containers(self):
        app = TestingDeskHarness()
        fighter = type("FighterStub", (), {"fighter_id": "fighter-event", "name": "Event Sample"})()
        case = app.record_drug_testing_case(
            fighter,
            test_id="drug-test-0003-02-000006",
            result="positive",
            policy="Strict",
            event_id="event-2030-0042",
            event_reference={"event_id": "event-2030-0042", "source": "scheduled_events"},
        )
        self.assertEqual(case["schema_version"], app.DRUG_TESTING_CASE_SCHEMA_VERSION)
        self.assertEqual(case["event_id"], "event-2030-0042")
        self.assertEqual(case["event_reference"]["source"], "scheduled_events")
        self.assertEqual(case["confirmation"]["status"], "not_enabled")
        self.assertEqual(case["confirmation"]["records"], [])
        self.assertEqual(case["appeals"], [])
        self.assertEqual(case["provisional_restriction"]["status"], "none")
        self.assertEqual(case["sanction"]["status"], "not_enabled")
        self.assertEqual(case["final_resolution"]["status"], "gated")
        display_rows = app.drug_testing_case_read_model()
        self.assertEqual(display_rows[0]["event_id"], "event-2030-0042")
        self.assertEqual(display_rows[0]["event_reference"]["source"], "scheduled_events")
        self.assertEqual(display_rows[0]["event_label"], "event-2030-0042 · scheduled_events")
        before = repr(app.drug_testing_state)
        workflow = app.drug_testing_case_workflow(case["case_id"])
        workflow["event_reference"]["source"] = "mutated"
        workflow["confirmation_record_count"] = 99
        workflow["frozen_contract"]["provider_snapshot"]["name"] = "mutated"
        self.assertEqual(workflow["event_id"], "event-2030-0042")
        reread = app.drug_testing_case_workflow(case["case_id"])
        self.assertEqual(reread["event_reference"]["source"], "scheduled_events")
        self.assertEqual(reread["confirmation_record_count"], 0)
        self.assertEqual(reread["frozen_contract"]["provider_id"], "legacy-promotion-testing")
        self.assertEqual(reread["frozen_contract"]["policy_id"], "Strict")
        self.assertEqual(reread["frozen_contract"]["provider_snapshot"]["name"], "Promotion Testing Desk")
        self.assertEqual(repr(app.drug_testing_state), before)

    def test_case_event_label_prefers_retained_name_and_manual_scope(self):
        app = TestingDeskHarness()
        named = {"event_id": "event-1", "event_reference": {"event_name": "Friday Fight Night", "source": "results"}}
        self.assertEqual(app.drug_testing_case_event_label(named), "Friday Fight Night · results")
        self.assertEqual(app.drug_testing_case_event_label({"event_id": "event-2"}), "event-2")
        self.assertEqual(app.drug_testing_case_event_label({}), "Manual / no event")

    def test_provider_selection_persists_without_changing_live_policy(self):
        app = TestingDeskHarness()
        ok, message, config = app.set_drug_testing_provider_selection("national-compliance-network", 8)
        self.assertTrue(ok)
        self.assertIn("planning provider", message.lower())
        self.assertEqual(config["provider"]["provider_id"], "national-compliance-network")
        self.assertEqual(config["sample_count"], 8)
        self.assertEqual(app.rules["drug_testing"], "Standard")
        self.assertEqual(app.drug_testing_quote()["amount"], 30_000)
        self.assertEqual(app.drug_testing_state["configuration_revision"], 2)

    def test_invalid_provider_selection_fails_closed(self):
        app = TestingDeskHarness()
        before = dict(app.drug_testing_state)
        ok, message, config = app.set_drug_testing_provider_selection("not-a-provider", 6)
        self.assertFalse(ok)
        self.assertIn("catalogue", message.lower())
        self.assertEqual(app.drug_testing_state, before)
        self.assertEqual(config["provider"]["provider_id"], "legacy-promotion-testing")

    def test_malformed_saved_configuration_is_explicitly_unavailable(self):
        app = TestingDeskHarness()
        app.drug_testing_state["provider_id"] = "retired-provider"
        app.rules["drug_testing"] = "retired-policy"
        before = repr(app.drug_testing_state)
        config = app.drug_testing_configuration()
        self.assertFalse(config["available"])
        self.assertEqual(config["provider"]["name"], "Unavailable provider")
        self.assertEqual(config["policy"]["name"], "Unavailable policy")
        self.assertEqual(len(config["issues"]), 2)
        quote = app.drug_testing_quote(sample_count=6)
        self.assertFalse(quote["available"])
        self.assertEqual(quote["amount"], 0)
        self.assertIn("retired-provider", quote["quote_status"])
        self.assertIn("retired-policy", quote["quote_status"])
        self.assertEqual(repr(app.drug_testing_state), before)

    def test_malformed_rules_or_finance_quote_is_bounded_and_non_mutating(self):
        app = TestingDeskHarness()
        app.rules = ["malformed"]
        app.finance = ["malformed"]
        before_state = repr(app.drug_testing_state)
        quote = app.drug_testing_quote(sample_count=6)
        self.assertFalse(quote["available"])
        self.assertEqual(quote["amount"], 0)
        self.assertIn("unavailable", quote["quote_status"])
        config = app.drug_testing_configuration()
        self.assertFalse(config["available"])
        self.assertIn("rules envelope", config["issues"][0])
        self.assertEqual(repr(app.drug_testing_state), before_state)

    def test_case_reader_marks_cross_wired_contract_unavailable(self):
        app = TestingDeskHarness()
        app.drug_testing_state = {
            "cases": [{
                "case_id": "cross-wired", "fighter": "Legacy Case",
                "status": "Preliminary review", "preliminary_result": "positive",
                "provider_id": "retired-provider",
                "provider_snapshot": {"provider_id": "legacy-promotion-testing", "name": "Wrong desk"},
                "policy": "retired-policy",
                "policy_snapshot": {"policy_id": "Standard", "name": "Wrong policy"},
                "quote_snapshot": {"actual_total": 7500},
            }],
        }
        before = repr(app.drug_testing_state)
        row = app.drug_testing_case_read_model()[0]
        self.assertFalse(row["contract_available"])
        self.assertEqual(row["provider_name"], "Unavailable provider")
        self.assertEqual(row["policy_name"], "Unavailable policy")
        self.assertEqual(row["recorded_total"], 0)
        self.assertEqual(row["next_action_label"], "Review saved contract")
        summary = app.drug_testing_summary()
        self.assertEqual(summary["unavailable_contracts"], 1)
        self.assertEqual(summary["total_spend"], 0)
        status = app.drug_testing_case_reader_status()
        self.assertEqual(status["status"], "Needs review")
        self.assertEqual(status["contract_issue_count"], 1)
        self.assertEqual(repr(app.drug_testing_state), before)

    def test_case_reader_marks_empty_frozen_contract_unavailable(self):
        app = TestingDeskHarness()
        app.drug_testing_state = {
            "cases": [{
                "case_id": "empty-snapshot", "fighter": "Legacy Case",
                "status": "Preliminary review", "preliminary_result": "positive",
                "provider_id": "legacy-promotion-testing", "provider_snapshot": {},
                "policy": "Standard", "policy_snapshot": {},
            }],
        }
        before = repr(app.drug_testing_state)
        row = app.drug_testing_case_read_model()[0]
        self.assertFalse(row["contract_available"])
        self.assertIn("provider snapshot is missing provider ID", row["contract_issues"])
        self.assertIn("policy snapshot is missing policy ID", row["contract_issues"])
        self.assertEqual(row["next_action_label"], "Review saved contract")
        self.assertEqual(app.drug_testing_summary()["unavailable_contracts"], 1)
        self.assertEqual(repr(app.drug_testing_state), before)

    def test_provider_selection_and_case_evidence_survive_atomic_save_load(self):
        app = TestingDeskHarness()
        app.set_drug_testing_provider_selection("regional-integrity-labs", 9)
        case = app.record_drug_testing_case(
            type("FighterStub", (), {"fighter_id": "fighter-1", "name": "Sample"})(),
            test_id="drug-test-0003-02-000001", result="negative", policy="Strict",
            provider_id="legacy-promotion-testing", sample_count=1,
            provider_snapshot={"provider_id": "legacy-promotion-testing", "name": "Promotion Testing Desk"},
            policy_snapshot={"policy_id": "Strict", "name": "Strict"},
            quote_snapshot={"actual_total": 2500},
        )
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "testing.json"
            atomic_write_split_save(path, {"drug_testing_state": app.drug_testing_state})
            loaded = load_save_payload(path)
        state = loaded["drug_testing_state"]
        self.assertEqual(state["provider_id"], "regional-integrity-labs")
        self.assertEqual(state["sample_count"], 9)
        self.assertEqual(state["cases"][0]["case_id"], case["case_id"])
        self.assertEqual(state["cases"][0]["policy_snapshot"]["policy_id"], "Strict")
        self.assertEqual(state["cases"][0]["quote_snapshot"]["actual_total"], 2500)

    def test_policy_selection_is_validated_versioned_and_rng_free(self):
        app = TestingDeskHarness()
        before_rng = random.getstate()
        ok, message, config = app.set_drug_testing_policy_selection("Strict")
        self.assertTrue(ok)
        self.assertIn("policy set", message.lower())
        self.assertEqual(app.rules["drug_testing"], "Strict")
        self.assertEqual(config["policy"]["policy_id"], "Strict")
        self.assertEqual(app.drug_testing_state["configuration_revision"], 2)
        self.assertEqual(random.getstate(), before_rng)
        # Re-selecting the same policy is idempotent and does not create a
        # second configuration revision.
        app.set_drug_testing_policy_selection("Strict")
        self.assertEqual(app.drug_testing_state["configuration_revision"], 2)
        before = (dict(app.rules), dict(app.drug_testing_state))
        ok, _message, _config = app.set_drug_testing_policy_selection("not-a-policy")
        self.assertFalse(ok)
        self.assertEqual((app.rules, app.drug_testing_state), before)

    def test_case_read_model_filters_and_is_defensive(self):
        app = TestingDeskHarness()
        positive = app.record_drug_testing_case(
            type("FighterStub", (), {"fighter_id": "fighter-1", "name": "Sample Alpha"})(),
            test_id="drug-test-0003-02-000004", result="positive", policy="Standard",
            provider_id="regional-integrity-labs", sample_count=2,
        )
        app.record_drug_testing_case(
            type("FighterStub", (), {"fighter_id": "fighter-2", "name": "Sample Beta"})(),
            test_id="drug-test-0003-02-000005", result="negative", policy="Standard",
            provider_id="legacy-promotion-testing", sample_count=2,
        )
        before = repr(app.drug_testing_state)
        before_rng = random.getstate()
        rows = app.drug_testing_case_read_model(status="Preliminary review", query="alpha")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["case_id"], positive["case_id"])
        self.assertEqual(rows[0]["provider_name"], "Regional Integrity Labs")
        self.assertEqual(rows[0]["screening_label"], "Preliminary alert")
        self.assertGreaterEqual(rows[0]["next_action_count"], 1)
        rows[0]["provider_name"] = "mutated"
        rows[0]["workflow"]["stages"][0]["status"] = "mutated"
        self.assertEqual(repr(app.drug_testing_state), before)
        self.assertEqual(random.getstate(), before_rng)
        self.assertEqual(app.drug_testing_case_read_model(query="beta")[0]["screening_label"], "Negative screen")

    def test_case_read_model_and_summary_expose_spend_without_mutating_evidence(self):
        app = TestingDeskHarness()
        app.record_drug_testing_case(
            type("FighterStub", (), {"fighter_id": "fighter-cost", "name": "Costed"})(),
            test_id="drug-test-0003-02-000006", result="negative", policy="Standard",
            sample_count=2, quote_snapshot={"actual_total": 5_000},
        )
        before = repr(app.drug_testing_state)
        row = app.drug_testing_case_read_model()[0]
        summary = app.drug_testing_summary()
        self.assertEqual(row["recorded_total"], 5_000)
        self.assertEqual(row["next_action_label"], "Review evidence")
        self.assertEqual(summary["samples_collected"], 2)
        self.assertEqual(summary["total_spend"], 5_000)
        self.assertEqual(repr(app.drug_testing_state), before)

    def test_case_settings_are_frozen_and_drift_is_visible_without_mutation(self):
        app = TestingDeskHarness()
        case = app.record_drug_testing_case(
            type("FighterStub", (), {"fighter_id": "fighter-drift", "name": "Drifted"})(),
            test_id="drug-test-drift-0001", result="positive", policy="Standard",
            provider_id="legacy-promotion-testing",
        )
        self.assertEqual(
            app.drug_testing_case_configuration_drift(case)["status"],
            "Frozen settings still selected",
        )
        app.drug_testing_state["provider_id"] = "national-compliance-network"
        app.rules["drug_testing"] = "Strict"
        drift = app.drug_testing_case_configuration_drift(case)
        self.assertTrue(drift["changed"])
        self.assertEqual(drift["differences"], ["provider changed", "policy changed"])
        before_reader = repr(app.drug_testing_state)
        row = app.drug_testing_case_read_model()[0]
        self.assertEqual(row["configuration_drift_label"], "Current settings differ")
        self.assertEqual(row["configuration_drift"]["frozen_provider_id"], "legacy-promotion-testing")
        self.assertEqual(row["configuration_drift"]["current_policy_id"], "Strict")
        # The reader reports the change but never rewrites the case contract.
        self.assertEqual(case["provider_id"], "legacy-promotion-testing")
        self.assertEqual(case["policy"], "Standard")
        self.assertEqual(repr(app.drug_testing_state), before_reader)

    def test_case_settings_drift_fails_closed_when_current_envelope_is_missing(self):
        app = TestingDeskHarness()
        case = {
            "case_id": "legacy-case", "provider_id": "legacy-promotion-testing", "policy": "Standard",
        }
        app.drug_testing_state = None
        app.rules = None
        drift = app.drug_testing_case_configuration_drift(case)
        self.assertTrue(drift["changed"])
        self.assertEqual(drift["differences"], ["current provider unavailable", "current policy unavailable"])

    def test_case_write_rejects_mismatched_or_unknown_frozen_contracts(self):
        app = TestingDeskHarness()
        fighter = type("FighterStub", (), {"fighter_id": "fighter-contract", "name": "Contracted"})()
        before = repr(app.drug_testing_state)
        mismatched_provider = app.record_drug_testing_case(
            fighter, test_id="drug-test-contract-provider", result="negative", policy="Standard",
            provider_id="regional-integrity-labs",
            provider_snapshot={"provider_id": "legacy-promotion-testing", "name": "Wrong desk"},
        )
        self.assertIsNone(mismatched_provider)
        self.assertEqual(repr(app.drug_testing_state), before)
        unknown_policy = app.record_drug_testing_case(
            fighter, test_id="drug-test-contract-policy", result="negative", policy="Unapproved",
            provider_id="legacy-promotion-testing",
        )
        self.assertIsNone(unknown_policy)
        self.assertEqual(repr(app.drug_testing_state), before)
        mismatched_policy = app.record_drug_testing_case(
            fighter, test_id="drug-test-contract-policy-snapshot", result="negative", policy="Strict",
            provider_id="legacy-promotion-testing",
            policy_snapshot={"policy_id": "Standard", "name": "Standard"},
        )
        self.assertIsNone(mismatched_policy)
        self.assertEqual(repr(app.drug_testing_state), before)

    def test_case_writer_respects_disabled_policy(self):
        app = TestingDeskHarness()
        fighter = type("FighterStub", (), {"fighter_id": "fighter-disabled", "name": "Disabled"})()
        before = repr(app.drug_testing_state)
        case = app.record_drug_testing_case(
            fighter, test_id="drug-test-disabled", result="negative", policy="None",
        )
        self.assertIsNone(case)
        self.assertEqual(repr(app.drug_testing_state), before)

    def test_legacy_cost_field_remains_visible_when_quote_envelope_is_absent(self):
        app = TestingDeskHarness()
        app.drug_testing_state = {
            "cases": [{
                "case_id": "legacy-cost-case", "fighter": "Legacy Cost",
                "fighter_id": "legacy-fighter", "status": "Closed negative",
                "preliminary_result": "negative", "sample_count": 2,
                "cost": 4321,
            }],
        }
        before = repr(app.drug_testing_state)

        row = app.drug_testing_case_read_model()[0]
        summary = app.drug_testing_summary()

        self.assertEqual(row["recorded_total"], 4321)
        self.assertEqual(summary["total_spend"], 4321)
        self.assertEqual(repr(app.drug_testing_state), before)

    def test_case_ui_identity_disambiguates_duplicates_without_rewriting_source_id(self):
        rows = [
            {"case_id": "case-duplicate", "fighter": "Alpha"},
            {"case_id": "case-duplicate", "fighter": "Beta"},
            {"fighter": "Legacy"},
        ]
        used = set()
        ids = [ViewMixin.drug_testing_case_ui_identity(row, used_ids=used) for row in rows]
        self.assertEqual(ids[0], "case:case-duplicate")
        self.assertEqual(ids[1], "case:case-duplicate#2")
        self.assertTrue(ids[2].startswith("legacy-case:"))
        self.assertEqual(rows[0]["case_id"], "case-duplicate")
        again_used = set()
        self.assertEqual(
            ids,
            [ViewMixin.drug_testing_case_ui_identity(row, used_ids=again_used) for row in rows],
        )

    def test_case_readers_do_not_normalise_malformed_saved_envelope(self):
        app = TestingDeskHarness()
        app.drug_testing_state = {
            "schema_version": "legacy",
            "cases": "not-a-list",
            "provider_id": "not-a-provider",
            "sample_count": "not-a-number",
        }
        before = repr(app.drug_testing_state)
        self.assertEqual(app.drug_testing_case_rows(), [])
        self.assertEqual(app.drug_testing_case_read_model(), [])
        status = app.drug_testing_case_reader_status()
        self.assertEqual(status["status"], "Unavailable")
        self.assertIn("cases collection", status["issues"][0])
        self.assertIsNone(app.drug_testing_case_details("missing"))
        self.assertIsNone(app.drug_testing_case_workflow("missing"))
        summary = app.drug_testing_summary()
        self.assertEqual(summary["total_cases"], 0)
        self.assertEqual(summary["total_spend"], 0)
        self.assertEqual(repr(app.drug_testing_state), before)

    def test_case_reader_status_flags_malformed_rows_without_touching_the_envelope(self):
        app = TestingDeskHarness()
        app.drug_testing_state = {"cases": [{"case_id": "case-1"}, "legacy-corrupt-row"]}
        before = repr(app.drug_testing_state)
        status = app.drug_testing_case_reader_status()
        self.assertEqual(status["status"], "Needs review")
        self.assertEqual(status["malformed_count"], 1)
        self.assertEqual(repr(app.drug_testing_state), before)

    def test_duplicate_case_id_detail_lookup_fails_closed(self):
        app = TestingDeskHarness()
        app.drug_testing_state = {
            "cases": [
                {"case_id": "duplicate-case", "fighter": "Alpha", "status": "Preliminary review"},
                {"case_id": "duplicate-case", "fighter": "Beta", "status": "Closed negative"},
            ],
        }
        before = repr(app.drug_testing_state)
        self.assertIsNone(app.drug_testing_case_details("duplicate-case"))
        self.assertIsNone(app.drug_testing_case_workflow("duplicate-case"))
        self.assertEqual(repr(app.drug_testing_state), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
