"""Headless regression coverage for the player-owned staff policy slice."""

import unittest
from copy import deepcopy
from types import SimpleNamespace

from contract_batch_workbench import ContractBatchWorkbenchMixin
from staff_management import StaffManagementMixin
from world import WorldMixin
from feature_foundation import FoundationMixin


class TreeStub:
    def __init__(self):
        self.rows = {}
        self.selected = ()

    def selection(self):
        return self.selected

    def selection_set(self, row_id):
        self.selected = (row_id,)

    def get_children(self):
        return tuple(self.rows)

    def delete(self, *row_ids):
        for row_id in row_ids:
            self.rows.pop(row_id, None)

    def insert(self, _parent, _where, iid, **kwargs):
        self.rows[iid] = kwargs


class ListStub:
    def __init__(self):
        self.items = []
        self.selected = set()

    def get(self, start, end=None):
        if end is None:
            return self.items[int(start)]
        return tuple(self.items[int(start):])

    def curselection(self):
        return tuple(sorted(self.selected))

    def delete(self, _start, _end=None):
        self.items = []
        self.selected = set()

    def insert(self, _where, value):
        self.items.append(value)

    def selection_set(self, index):
        self.selected.add(int(index))


class StaffHarness(StaffManagementMixin, FoundationMixin):
    def __init__(self):
        self.month, self.week = 3, 2
        self.cash = 100_000
        self.player_company_name = "Staff FC"
        self.staff = [
            {"staff_id": "staff-1", "name": "Alex Scout", "role": "Scout", "skill": 70, "morale": 80},
            {"staff_id": "staff-2", "name": "Morgan Match", "role": "Matchmaker", "skill": 66, "morale": 72},
            {"staff_id": "staff-3", "name": "Pat Doctor", "role": "Doctor", "skill": 64, "morale": 90},
            {"staff_id": "staff-4", "name": "Taylor Marketing", "role": "Marketing", "skill": 62, "morale": 78},
        ]
        self.rules = {"auto_assign_idle_scouts": True, "drug_testing": "Standard"}
        self.drug_testing_state = {"provider_id": "legacy-promotion-testing", "sample_count": 6, "configuration_revision": 1}
        self.promotions = []
        self.scheduled_events = []
        self.player_combat_divisions = {}
        self.combat_sport_worlds = {}
        self.ensure_foundation_state()
        self.ensure_staff_management_state()

    def drug_testing_case_rows(self, *, include_closed=True):
        return [{"case_id": "case-1", "fighter_id": "fighter-1", "fighter": "Sample", "status": "Preliminary review"}]

    def drug_testing_configuration(self):
        return {
            "provider": {"provider_id": "legacy-promotion-testing", "name": "Promotion Testing Desk"},
            "policy": {"policy_id": "Standard", "name": "Standard"}, "sample_count": 6,
        }

    def drug_testing_quote(self):
        return {"amount": 15000, "planning_only": True}


class ContractStaffHarness(StaffManagementMixin, ContractBatchWorkbenchMixin, FoundationMixin):
    """Small live-path harness for the explicit Talent Relations adapter."""

    def __init__(self):
        self.month, self.week = 4, 2
        self.cash = 500_000
        self.player_company_name = "Staff FC"
        self.staff = [{"staff_id": "talent-1", "name": "Taylor Talent", "role": "Talent Relations", "skill": 70, "morale": 80}]
        self.roster = [SimpleNamespace(
            fighter_id="fighter-contract", name="Renewal Target", age=29, purse=10_000,
            popularity=45, momentum=0, champion=False, exclusive=True,
            contract_months=1, retired=False, retirement_pending=False, morale=75,
            relationship_trust=70, champions_clause=False, title_shot_clause=False,
            main_event_promise=False, top_opponent_promise=False,
        )]
        self.ensure_foundation_state()
        self.ensure_staff_management_state()
        self.ensure_contract_batch_state()

    def fighter_identity_key(self, value):
        return value.fighter_id

    def resolve_fighter(self, reference):
        return next((row for row in self.roster if row.fighter_id == str(reference)), None)

    def player_monthly_office_cost(self):
        return 5_000

    def strategic_investment_upkeep(self):
        return 1_000


class StaffWorldHarness(StaffManagementMixin, WorldMixin):
    def __init__(self):
        self.staff = [
            {"staff_id": "staff-low-morale", "name": "Raw Skill", "role": "Marketing", "skill": 90, "morale": 10},
            {"staff_id": "staff-effective", "name": "Effective Lead", "role": "Marketing", "skill": 84, "morale": 95},
        ]


class CalendarStaffOrderHarness(StaffManagementMixin, WorldMixin):
    def __init__(self):
        self.month, self.week = 3, 2
        self.rules = {"autosave_interval_months": 2}
        self.calls = []

    def world_week_steps(self):
        return [("World work", lambda: self.calls.append("world"))]

    def process_due_player_combat_events(self):
        self.calls.append("cards")

    def process_staff_autonomy_boundary(self, completed_month=None, completed_week=None):
        self.calls.append(("staff", completed_month, completed_week))
        return []

    def process_owner_goals_boundary(self, completed_month=None, completed_week=None):
        self.calls.append(("goals", completed_month, completed_week))
        return []


class StaffManagementTests(unittest.TestCase):
    def test_brief_view_ids_are_explicit_for_saved_and_legacy_rows(self):
        saved = {"brief_id": "brief-7", "objective": "Review cards"}
        self.assertEqual(StaffManagementMixin._staff_brief_view_id(saved, 4), "brief-7")
        legacy = StaffManagementMixin._staff_brief_view_id({"objective": "Legacy"}, 4)
        self.assertTrue(legacy.startswith("staff-brief:legacy:"))
        self.assertEqual(legacy, StaffManagementMixin._staff_brief_view_id({"objective": "Legacy"}, 99))
        self.assertEqual(StaffManagementMixin._staff_brief_view_id({"brief_id": "brief-7"}, 9), "brief-7")

    def test_summary_and_autonomy_readers_do_not_normalize_malformed_policy(self):
        app = StaffHarness()
        app.staff_management = {
            "autonomy_mode": "future-mode",
            "department_overrides": "not-a-mapping",
            "briefs": "not-a-list",
            "exceptions": {"retained": "raw"},
            "revision": "unknown",
            "per_action_ceiling": "not-a-mapping",
        }
        retained = deepcopy(app.staff_management)
        summary = app.staff_management_summary()
        self.assertEqual(summary["mode"], "Manual")
        self.assertEqual(summary["active_briefs"], 0)
        self.assertEqual(summary["exceptions"], 0)
        self.assertEqual(app.staff_effective_autonomy("Marketing"), "Manual")
        self.assertEqual(app.staff_management, retained)

    def test_staff_readers_fail_closed_for_overflow_ledger_values(self):
        app = StaffHarness()
        app.staff_management = {
            "revision": float("inf"),
            "work_log": [{
                "work_id": "overflow-work", "operation_id": "overflow-op",
                "brief_id": "brief-overflow", "department": "Marketing",
                "action_id": "campaign_plan_commit", "status": "Executed",
                "boundary": "3:2", "spend": float("inf"),
                "evidence_key": "staff:evidence:overflow",
            }],
            "briefs": [], "exceptions": [], "progression": {},
        }
        before = deepcopy(app.staff_management)
        summary = app.staff_management_summary()
        audit = app.staff_evidence_audit()
        self.assertEqual(summary["revision"], 1)
        self.assertEqual(audit["status"], "Needs attention")
        self.assertIn("invalid_spend", {row["code"] for row in audit["findings"]})
        self.assertEqual(app.staff_management, before)

    def test_staff_boundary_runs_after_cards_with_completed_date(self):
        app = CalendarStaffOrderHarness()
        steps, month_changed = app.calendar_week_steps(include_autosave=False)
        self.assertFalse(month_changed)
        for _label, task in steps:
            task()
        self.assertEqual(app.calls, ["world", "cards", ("staff", 3, 2), ("goals", 3, 2)])

    def test_month_end_staff_boundary_waits_for_monthly_business(self):
        app = CalendarStaffOrderHarness()
        app.week = 4
        app.world_month_steps = lambda _player_ran_show: [("Monthly work", lambda: app.calls.append("monthly"))]
        app.monthly_player_business_steps = lambda: [("Business work", lambda: app.calls.append("business"))]
        steps, month_changed = app.calendar_week_steps(include_autosave=False)
        self.assertTrue(month_changed)
        for _label, task in steps:
            task()
        self.assertEqual(app.calls, ["world", "cards", "monthly", "business", ("staff", 3, 4), ("goals", 3, 4)])

    def test_spectator_fast_forward_never_grants_staff_authority(self):
        app = StaffHarness()
        ok, _text, brief = app.create_staff_department_brief("Matchmaking", "Review the next card", ["fighter-1"])
        self.assertTrue(ok)
        self.assertTrue(app.commit_staff_department_brief(brief["brief_id"])[0])
        app.set_staff_autonomy("Recommendations")
        app.spectator_mode = True
        before = deepcopy(app.staff_management)
        self.assertEqual(app.process_staff_autonomy_boundary(3, 2), [])
        self.assertEqual(app.staff_management, before)

    def test_default_is_manual_and_all_modes_are_explicit(self):
        app = StaffHarness()
        self.assertEqual(app.staff_effective_autonomy("Marketing"), "Manual")
        self.assertEqual(tuple(app.STAFF_AUTONOMY_MODES), ("Manual", "Recommendations", "Selective Recommendations", "Full Auto"))
        before = app.staff_management.copy()
        ok, _text, _state = app.set_staff_autonomy("Not a mode")
        self.assertFalse(ok)
        self.assertEqual(app.staff_management["autonomy_mode"], before["autonomy_mode"])

    def test_company_and_department_overrides_are_save_owned(self):
        app = StaffHarness()
        ok, _text, _state = app.set_staff_autonomy("Recommendations")
        self.assertTrue(ok)
        ok, _text, _state = app.set_staff_autonomy("Selective Recommendations", "Matchmaking")
        self.assertTrue(ok)
        self.assertEqual(app.staff_effective_autonomy("Marketing"), "Recommendations")
        self.assertEqual(app.staff_effective_autonomy("Matchmaking"), "Selective Recommendations")

    def test_autonomy_ui_projection_uses_selected_department_override(self):
        app = StaffHarness()
        app.staff_autonomy_choice = type("Var", (), {"value": "Manual", "get": lambda self: self.value, "set": lambda self, value: setattr(self, "value", value)})()
        app.staff_department_choice = type("Var", (), {"value": "Company default", "get": lambda self: self.value, "set": lambda self, value: setattr(self, "value", value)})()
        app.set_staff_autonomy("Recommendations")
        app.set_staff_autonomy("Full Auto", "Marketing")
        app.staff_department_choice.set("Marketing")
        app.staff_sync_autonomy_choice()
        self.assertEqual(app.staff_autonomy_choice.get(), "Full Auto")
        app.staff_department_choice.set("Company default")
        app.staff_sync_autonomy_choice()
        self.assertEqual(app.staff_autonomy_choice.get(), "Recommendations")

    def test_autonomy_selector_refresh_does_not_normalize_malformed_policy(self):
        app = StaffHarness()
        app.staff_autonomy_choice = type("Var", (), {"value": "Full Auto", "get": lambda self: self.value, "set": lambda self, value: setattr(self, "value", value)})()
        app.staff_department_choice = type("Var", (), {"value": "Company default", "get": lambda self: self.value, "set": lambda self, value: setattr(self, "value", value)})()
        app.staff_management = {"autonomy_mode": "Recommendations", "department_overrides": "malformed"}
        before = deepcopy(app.staff_management)
        app.staff_sync_autonomy_choice()
        self.assertEqual(app.staff_management, before)
        self.assertEqual(app.staff_autonomy_choice.get(), "Recommendations")

    def test_staff_receipt_rows_retain_saved_operation_selection(self):
        app = StaffHarness()
        app.staff_brief_tree = TreeStub()
        app.staff_work_tree = TreeStub()
        app.staff_management["work_log"] = [
            {"work_id": "work-a", "operation_id": "op-a", "action_id": "scouting_review", "target_ref": "fighter-a", "spend": 0, "status": "Recommendation", "evidence_key": "e-a"},
            {"work_id": "work-b", "operation_id": "op-b", "action_id": "medical_review", "target_ref": "fighter-b", "spend": 0, "status": "Recommendation", "evidence_key": "e-b"},
        ]
        app.refresh_staff_management_panel()
        app.staff_work_tree.selection_set("staff-work:op-b")
        app.staff_management["work_log"].insert(0, {
            "work_id": "work-new", "operation_id": "op-new", "action_id": "scouting_review", "target_ref": "fighter-new", "spend": 0, "status": "Recommendation", "evidence_key": "e-new",
        })
        app.refresh_staff_management_panel()
        self.assertEqual(app.staff_work_tree.selection(), ("staff-work:op-b",))
        self.assertEqual(StaffHarness._staff_work_view_id({"operation_id": "op-b"}), "staff-work:op-b")
        legacy = StaffHarness._staff_work_view_id({}, index=3)
        self.assertTrue(legacy.startswith("staff-work-card:legacy:"))
        self.assertEqual(legacy, StaffHarness._staff_work_view_id({}, index=99))

    def test_retention_watch_rows_use_staff_identity_and_preserve_selection(self):
        app = StaffHarness()
        app.staff_brief_tree = TreeStub()
        app.staff_retention_tree = TreeStub()
        app.refresh_staff_management_panel()
        selected_id = "staff-retention:staff-2"
        app.staff_retention_tree.selection_set(selected_id)
        app.staff = list(reversed(app.staff))
        app.refresh_staff_management_panel()
        self.assertEqual(app.staff_retention_tree.selection(), (selected_id,))
        self.assertIs(app.staff_retention_rows[selected_id], next(member for member in app.staff if member["staff_id"] == "staff-2"))
        self.assertEqual(StaffHarness._staff_management_row_id(app.staff[0], 0, "staff-retention"), "staff-retention:staff-4")
        legacy_id = StaffHarness._staff_management_row_id({"name": "Legacy", "role": "Doctor"}, 3, "staff-retention")
        self.assertTrue(legacy_id.startswith("staff-retention:legacy:"))
        self.assertEqual(legacy_id, StaffHarness._staff_management_row_id({"name": "Legacy", "role": "Doctor"}, 99, "staff-retention"))
        opaque_id = StaffHarness._staff_management_row_id({}, 3, "staff-retention")
        self.assertTrue(opaque_id.startswith("staff-retention:legacy:opaque:"))
        self.assertEqual(opaque_id, StaffHarness._staff_management_row_id({}, 99, "staff-retention"))
        self.assertEqual(
            opaque_id,
            StaffHarness._staff_management_row_id({}, 0, "staff-retention"),
            "Opaque legacy identity must not depend on the visible row position.",
        )
        self.assertEqual(
            StaffHarness._staff_management_row_id([], 0, "staff-retention"),
            StaffHarness._staff_management_row_id([], 5, "staff-retention"),
        )

    def test_staff_brief_table_shows_action_progress_without_dropping_work_count(self):
        app = StaffHarness()
        app.staff_brief_tree = TreeStub()
        ok, _text, brief = app.create_staff_department_brief(
            "Marketing", "Review then commit", ["event-1"],
            action_ids=["campaign_plan_review", "campaign_plan_commit"],
        )
        self.assertTrue(ok)
        app.refresh_staff_management_panel()
        self.assertEqual(app.staff_brief_tree.rows[brief["brief_id"]]["values"][-2:], ("0/2", 0))
        app.staff_management["briefs"][0]["completed_action_ids"] = ["campaign_plan_review"]
        app.staff_management["briefs"][0]["work_ids"] = ["work-1"]
        app.refresh_staff_management_panel()
        self.assertEqual(app.staff_brief_tree.rows[brief["brief_id"]]["values"][-2:], ("1/2", 1))

    def test_staff_action_list_can_save_multiple_actions_in_authored_order(self):
        app = StaffHarness()
        app.staff_brief_department_choice = type(
            "Var", (), {"get": lambda self: "Marketing"},
        )()
        app.staff_brief_action_choice = type(
            "Var", (), {"get": lambda self: "Review campaign plan", "set": lambda self, _value: None},
        )()
        app.staff_brief_action_list = ListStub()
        app.staff_brief_objective_entry = type("Entry", (), {"get": lambda self: "Run the next campaign"})()
        app.staff_brief_target_entry = type("Entry", (), {"get": lambda self: "event-1"})()
        app.staff_refresh_brief_action_choices()
        app.staff_brief_action_list.selection_set(1)
        saved = app.staff_save_brief_from_ui()
        self.assertTrue(saved)
        self.assertEqual(
            app.staff_management["briefs"][0]["allowed_action_ids"],
            ["campaign_plan_review", "campaign_plan_commit"],
        )

    def test_guardrails_are_bounded_and_versioned(self):
        app = StaffHarness()
        before = app.staff_management["revision"]
        ok, _text, _state = app.set_staff_guardrails(25000, 10000)
        self.assertTrue(ok)
        self.assertEqual(app.staff_management["monthly_ceiling"], 25000)
        self.assertEqual(app.staff_management["minimum_cash_reserve"], 10000)
        self.assertGreater(app.staff_management["revision"], before)
        self.assertFalse(app.set_staff_guardrails("not money", 0)[0])
        self.assertTrue(app.set_staff_action_ceiling("campaign_plan_review", 750)[0])
        self.assertEqual(app.staff_management["per_action_ceiling"]["campaign_plan_review"], 750)
        app.cash = 400
        ok, reason, _details = app.staff_budget_status(500, "other_action")
        self.assertFalse(ok)
        self.assertIn("cash reserve", reason)

    def test_staff_budget_mutations_fail_closed_for_nonfinite_inputs(self):
        app = StaffHarness()
        before = deepcopy(app.staff_management)
        self.assertFalse(app.set_staff_guardrails(float("inf"), 0)[0])
        self.assertFalse(app.set_staff_action_ceiling("campaign_plan_review", float("nan"))[0])
        quote = app.staff_brief_quote("Marketing", "Review", spend_ceiling=float("inf"))
        self.assertEqual(quote["details"]["spend_ceiling"], 0)
        ok, _reason, _details = app.staff_budget_status(float("inf"), "campaign_plan_review", _state=before)
        self.assertTrue(ok)
        self.assertEqual(app.staff_management["monthly_ceiling"], before["monthly_ceiling"])

    def test_budget_reader_skips_malformed_work_numbers_without_crashing_or_repairing(self):
        app = StaffHarness()
        app.staff_management["work_log"] = [
            {"work_id": "bad-spend", "status": "Executed", "month": 3, "action_id": "campaign_plan_review", "spend": "unknown"},
            {"work_id": "bad-month", "status": "Executed", "month": None, "action_id": "campaign_plan_review", "spend": 900},
            {"work_id": "valid", "status": "Executed", "month": 3, "action_id": "campaign_plan_review", "spend": 100},
        ]
        app.staff_management["monthly_ceiling"] = "not-a-number"
        app.staff_management["per_action_ceiling"] = {"campaign_plan_review": "also-bad"}
        before = deepcopy(app.staff_management)
        ok, reason, details = app.staff_budget_status(250, "campaign_plan_review", _state=app.staff_management)
        self.assertTrue(ok)
        self.assertIn("Within staff budget", reason)
        self.assertEqual(details["spent"], 100)
        self.assertEqual(details["action_spent"], 1000)
        self.assertEqual(app.staff_management, before)

    def test_lead_selection_is_morale_adjusted_with_stable_roster_tie_break(self):
        app = StaffHarness()
        lead = app.staff_effective_lead("Scouting")
        self.assertEqual(lead["staff_id"], "staff-1")
        self.assertEqual(app.staff_effective_lead("Matchmaking")["staff_id"], "staff-2")
        self.assertIsNone(app.staff_effective_lead("Drug Testing Officer"))

    def test_lead_and_specialty_readers_fail_closed_for_nonfinite_staff_values(self):
        app = StaffWorldHarness()
        malformed = {
            "staff_id": "staff-nonfinite", "name": "Unclear Lead", "role": "Marketing",
            "skill": float("inf"), "morale": float("nan"), "specialty": "Campaign Coordinator",
        }
        app.staff.append(malformed)
        before = deepcopy(malformed)
        lead = app.staff_effective_lead("Marketing")
        self.assertEqual(lead["staff_id"], "staff-effective")
        self.assertEqual(app.staff_member_for_role("Marketing")["staff_id"], "staff-effective")
        self.assertEqual(app.staff_specialty_cost_reduction("Marketing", float("inf"), cost_type="media_campaign"), 0)
        note = app.staff_specialty_cost_note("Marketing", float("nan"), cost_type="media_campaign")
        self.assertEqual(note["subtotal"], 0)
        self.assertEqual(note["saving"], 0)
        self.assertEqual(malformed, before)

    def test_world_contribution_lookup_uses_the_same_effective_lead(self):
        app = StaffWorldHarness()
        self.assertEqual(app.staff_member_for_role("Marketing")["staff_id"], "staff-effective")

    def test_approved_specialty_savings_are_bounded_lead_scoped_and_pure(self):
        app = StaffWorldHarness()
        app.staff.extend([
            {"staff_id": "staff-campaign", "name": "Campaign Lead", "role": "Marketing", "skill": 96, "morale": 96, "specialty": "Campaign Coordinator"},
            {"staff_id": "staff-contract", "name": "Contract Lead", "role": "Talent Relations", "skill": 60, "morale": 65, "specialty": "Contract Administrator"},
            {"staff_id": "staff-production", "name": "Production Lead", "role": "Broadcast Producer", "skill": 96, "morale": 96, "specialty": "Production Coordinator"},
        ])
        before = deepcopy(app.staff)
        self.assertEqual(app.staff_specialty_cost_reduction("Marketing", 10_000, cost_type="media_campaign"), 200)
        self.assertEqual(app.staff_specialty_cost_reduction("Talent Relations", 2_600, cost_type="negotiation_administration"), 52)
        self.assertEqual(app.staff_specialty_cost_reduction("Broadcast Producer", 50_000, cost_type="production_staging"), 1_000)
        self.assertEqual(app.staff_specialty_cost_reduction("Marketing", 10_000, cost_type="production_staging"), 0)
        self.assertEqual(app.staff_specialty_cost_reduction("Marketing", 0, cost_type="media_campaign"), 0)
        contract_lead = next(member for member in app.staff if member.get("role") == "Talent Relations")
        admin_discount = app.staff_negotiation_administration_saving(2_600)
        contract_lead["specialty"] = "Contract trust"
        plain_discount = app.staff_negotiation_administration_saving(2_600)
        self.assertEqual(admin_discount - plain_discount, 52)
        contract_lead["specialty"] = "Contract Administrator"
        self.assertEqual(app.staff, before)

    def test_quote_is_observational_and_capability_matrix_is_honest(self):
        app = StaffHarness()
        state_before = repr(app.staff_management)
        quote = app.staff_brief_quote("Marketing", "Review next event", ["event-1"])
        self.assertEqual(quote["amount"], 0)
        self.assertEqual(repr(app.staff_management), state_before)
        matrix = app.staff_capability_matrix()
        self.assertTrue(matrix["Marketing"]["advice"])
        self.assertTrue(matrix["Marketing"]["automation"])
        self.assertTrue(matrix["Drug Testing Officer"]["advice"])
        self.assertIn("approved provider", matrix["Drug Testing Officer"]["note"])
        self.assertIn("costs", matrix["Marketing"])
        self.assertIn("stop_conditions", matrix["Broadcast Producer"])
        self.assertEqual(matrix["Matchmaking"]["actions"][0]["id"], "matchmaking_review")
        self.assertEqual(repr(app.staff_management), state_before)

    def test_capability_matrix_exposes_handler_and_evidence_gate_per_action(self):
        app = StaffHarness()
        matrix = app.staff_capability_matrix()
        self.assertEqual(set(matrix), set(app.STAFF_DEPARTMENTS))
        for department, row in matrix.items():
            self.assertEqual(row["action_count"], len(row["actions"]))
            self.assertTrue(row["evidence_required"])
            self.assertIn(row["execution_state"], ("Ready", "Gated"))
            for action in row["actions"]:
                self.assertIn(action["execution_state"], ("Registered", "Gated"))
                self.assertTrue(action["evidence_required"])
                self.assertIn(action["id"], [item["id"] for item in row["actions"]])

    def test_capability_matrix_exposes_safe_read_action_ids_separately(self):
        app = StaffHarness()
        matrix = app.staff_capability_matrix()
        marketing = matrix["Marketing"]
        self.assertEqual(marketing["safe_read_action_ids"], ["campaign_plan_review"])
        self.assertNotIn("campaign_plan_commit", marketing["safe_read_action_ids"])
        for department, row in matrix.items():
            action_ids = {action["id"] for action in row["actions"]}
            self.assertTrue(set(row["safe_read_action_ids"]) <= action_ids, department)

    def test_capability_and_evidence_readers_fail_closed_for_nonfinite_staff_fields(self):
        app = StaffHarness()
        malformed = {
            "staff_id": "staff-nonfinite", "name": "Unclear Staff", "role": "Marketing",
            "skill": float("inf"), "morale": float("nan"), "salary": float("inf"),
            "contract_months": float("nan"),
        }
        app.staff.append(malformed)
        before = deepcopy((app.staff, app.staff_management))
        matrix = app.staff_capability_matrix()
        self.assertIn(matrix["Marketing"]["execution_state"], ("Ready", "Gated"))
        audit = app.staff_evidence_audit({"work_log": [], "briefs": [], "progression": {}})
        self.assertEqual((app.staff, app.staff_management), before)
        findings = [row for row in audit["findings"] if row.get("staff_id") == "staff-nonfinite"]
        codes = {row["code"] for row in findings}
        self.assertIn("invalid_staff_salary", codes)
        self.assertIn("invalid_staff_contract", codes)

    def test_staff_evidence_audit_is_pure_and_reports_long_run_findings(self):
        app = StaffHarness()
        state = {
            "work_log": [
                {
                    "work_id": "work-1", "operation_id": "op-1", "brief_id": "brief-1",
                    "department": "Marketing", "action_id": "not-registered", "status": "Executed",
                    "boundary": "3:2", "spend": 0, "progression_eligible": True,
                },
                {
                    "work_id": "work-1", "operation_id": "op-1", "brief_id": "brief-2",
                    "department": "Marketing", "action_id": "campaign_plan_review", "status": "Recommendation",
                    "boundary": "3:3", "spend": 10, "recommendations": None,
                },
            ],
            "briefs": [
                {"brief_id": "brief-1", "status": "Completed", "allowed_action_ids": ["campaign_plan_review"], "completed_action_ids": []},
                {"brief_id": "brief-2", "status": "Draft", "allowed_action_ids": ["campaign_plan_review"], "completed_action_ids": ["outside-allowlist"]},
            ],
            "progression": {"staff-4": {"credited_work_ids": ["missing-work"]}},
        }
        before = deepcopy(state)
        audit = app.staff_evidence_audit(state)
        self.assertEqual(state, before)
        self.assertEqual(audit["status"], "Needs attention")
        self.assertEqual(audit["work_count"], 2)
        self.assertEqual(audit["executed_count"], 1)
        self.assertEqual(audit["recommendation_count"], 1)
        codes = {row["code"] for row in audit["findings"]}
        self.assertTrue({
            "missing_evidence", "invalid_progression", "unsupported_action",
            "paid_recommendation", "invalid_recommendation_payload",
            "duplicate_work_id", "duplicate_operation_id",
            "completed_action_not_allowlisted", "incomplete_brief_sealed",
            "orphaned_progression",
        } <= codes)

    def test_staff_evidence_audit_marks_complete_evidence_ledger_healthy(self):
        app = StaffHarness()
        state = {
            "work_log": [{
                "work_id": "work-ok", "operation_id": "op-ok", "brief_id": "brief-ok",
                "department": "Marketing", "action_id": "campaign_plan_commit", "status": "Executed",
                "boundary": "3:2", "spend": 250, "evidence_key": "media-evidence:1",
                "progression_eligible": True,
            }],
            "briefs": [{
                "brief_id": "brief-ok", "status": "Completed",
                "allowed_action_ids": ["campaign_plan_commit"], "completed_action_ids": ["campaign_plan_commit"],
            }],
            "progression": {"staff-4": {"credited_work_ids": ["work-ok"]}},
        }
        audit = app.staff_evidence_audit(state)
        self.assertEqual(audit["status"], "Healthy")
        self.assertEqual(audit["finding_count"], 0)
        self.assertEqual(audit["qualified_count"], 1)
        self.assertEqual(audit["boundary_count"], 1)

    def test_staff_evidence_audit_surfaces_malformed_rows_and_missing_operation_ids(self):
        app = StaffHarness()
        state = {
            "work_log": [
                None,
                {
                    "work_id": "work-missing-operation", "operation_id": "",
                    "brief_id": "brief-legacy", "status": "Recommendation",
                    "spend": 0, "recommendations": [],
                },
                {"work_id": "work-unknown-status", "operation_id": "op-unknown", "status": "Mystery"},
            ],
            "briefs": [None],
            "progression": {},
        }
        before = deepcopy(state)
        audit = app.staff_evidence_audit(state)
        self.assertEqual(state, before)
        codes = {row["code"] for row in audit["findings"]}
        self.assertTrue({
            "invalid_work_row", "missing_operation_identity", "invalid_brief_row",
            "unsupported_work_status",
        } <= codes)
        self.assertEqual(audit["status"], "Needs attention")

    def test_staff_evidence_audit_surfaces_malformed_collections(self):
        app = StaffHarness()
        state = {"work_log": {"bad": True}, "briefs": "legacy", "progression": {}}
        before = deepcopy(state)
        audit = app.staff_evidence_audit(state)
        self.assertEqual(state, before)
        codes = {row["code"] for row in audit["findings"]}
        self.assertTrue({"invalid_work_collection", "invalid_brief_collection"} <= codes)

    def test_staff_evidence_audit_surfaces_malformed_progression_credit_payloads(self):
        app = StaffHarness()
        state = {
            "work_log": [], "briefs": [],
            "progression": {"staff-1": {"credited_work_ids": "not-a-list"}},
        }
        before = deepcopy(state)
        audit = app.staff_evidence_audit(state)
        self.assertEqual(state, before)
        codes = {row["code"] for row in audit["findings"]}
        self.assertIn("invalid_progression_credits", codes)

        malformed_collection = {"work_log": [], "briefs": [], "progression": ["legacy"]}
        audit = app.staff_evidence_audit(malformed_collection)
        self.assertIn("invalid_progression_collection", {row["code"] for row in audit["findings"]})

    def test_staff_evidence_audit_reports_employment_identity_and_obligation_findings(self):
        app = StaffHarness()
        app.staff = [
            {"staff_id": "staff-dup", "name": "Employed One", "role": "Marketing", "salary": 5000, "contract_months": 12},
            {"staff_id": "staff-bad", "name": "Malformed Terms", "role": "", "salary": "not-a-number", "contract_months": -2},
            {"name": "Legacy Without ID", "role": "Scout", "salary": 4200, "contract_months": 6},
        ]
        app.staff_candidates = [
            {"staff_id": "staff-dup", "name": "Duplicate Market Copy", "role": "Marketing", "salary": 6000, "contract_months": 18},
            {"staff_id": "staff-market-bad", "name": "Negative Market Quote", "role": "Doctor", "salary": -10, "contract_months": "unknown"},
        ]
        before = deepcopy((app.staff, app.staff_candidates))
        audit = app.staff_evidence_audit({"work_log": [], "briefs": [], "progression": {}})
        self.assertEqual((app.staff, app.staff_candidates), before)
        codes = {row["code"] for row in audit["findings"]}
        self.assertTrue({
            "duplicate_staff_identity", "missing_staff_identity", "missing_staff_role",
            "invalid_staff_salary", "invalid_staff_contract",
        } <= codes)
        duplicate = next(row for row in audit["findings"] if row["code"] == "duplicate_staff_identity")
        self.assertEqual(duplicate["staff_id"], "staff-dup")
        self.assertIn("employed", duplicate["message"].lower())
        self.assertEqual(duplicate["source"], "Employed roster / Shared market")
        for row in audit["findings"]:
            self.assertIn("source", row)
            self.assertIn("staff_id", row)

    def test_full_auto_rejects_handler_result_without_evidence(self):
        app = StaffHarness()
        ok, _text, brief = app.create_staff_department_brief(
            "Marketing", "Commit the next campaign", ["event-1"],
            action_ids=["campaign_plan_commit"],
        )
        self.assertTrue(ok)
        self.assertTrue(app.commit_staff_department_brief(brief["brief_id"])[0])
        app.set_staff_autonomy("Full Auto", "Marketing")
        app.staff_action_handlers = {
            "campaign_plan_commit": lambda **_kwargs: {
                "ok": True, "spend": 50, "result": {"action": "campaign_plan_commit"},
            },
        }
        before_log = list(app.staff_management["work_log"])
        result = app.process_staff_autonomy_boundary(3, 3)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "Needs attention")
        self.assertIn("evidence key", result[0]["reason"])
        self.assertEqual(app.staff_management["work_log"], before_log)
        self.assertEqual(app.staff_management["briefs"][0]["status"], "Needs attention")

    def test_testing_officer_review_is_read_only_case_evidence(self):
        app = StaffHarness()
        handler = app._staff_builtin_action_handlers()["testing_case_review"]
        before = deepcopy(app.drug_testing_state)
        outcome = handler(
            brief={"brief_id": "brief-testing", "last_attempt_boundary": "3:2"},
            action_id="testing_case_review", target_ref="",
        )
        self.assertTrue(outcome["ok"])
        self.assertEqual(outcome["spend"], 0)
        self.assertEqual(outcome["result"]["case_count"], 1)
        self.assertTrue(outcome["result"]["quote"]["planning_only"])
        self.assertEqual(app.drug_testing_state, before)

    def test_brief_creation_has_no_gameplay_effect_and_cancel_is_explicit(self):
        app = StaffHarness()
        before_revision = app.staff_management["revision"]
        ok, _text, brief = app.create_staff_department_brief(
            "Marketing", "Prepare a regional event campaign", ["event-1", "event-1"], spend_ceiling=5000,
        )
        self.assertTrue(ok)
        self.assertEqual(brief["target_refs"], ["event-1"])
        self.assertEqual(brief["status"], "Draft")
        self.assertGreater(app.staff_management["revision"], before_revision)
        ok, _text, cancelled = app.cancel_staff_department_brief(brief["brief_id"])
        self.assertTrue(ok)
        self.assertEqual(cancelled["status"], "Cancelled")
        self.assertFalse(app.cancel_staff_department_brief(brief["brief_id"])[0])

    def test_brief_action_allowlist_is_identity_deduplicated(self):
        app = StaffHarness()
        ok, _text, brief = app.create_staff_department_brief(
            "Marketing", "Review one campaign once", ["event-1"],
            action_ids=["campaign_plan_review", "campaign_plan_review"],
        )
        self.assertTrue(ok)
        self.assertEqual(brief["allowed_action_ids"], ["campaign_plan_review"])

    def test_invalid_briefs_fail_without_creating_rows(self):
        app = StaffHarness()
        before = len(app.staff_management["briefs"])
        self.assertFalse(app.create_staff_department_brief("Drug Testing", "Check cases")[0])
        self.assertFalse(app.create_staff_department_brief("Marketing", "")[0])
        self.assertEqual(len(app.staff_management["briefs"]), before)

    def test_calendar_boundary_is_retry_safe_and_full_auto_fails_closed(self):
        app = StaffHarness()
        ok, _text, brief = app.create_staff_department_brief("Marketing", "Review the next card", ["event-1"])
        self.assertTrue(ok)
        self.assertTrue(app.commit_staff_department_brief(brief["brief_id"])[0])
        app.set_staff_autonomy("Full Auto")
        first = app.process_staff_autonomy_boundary()
        second = app.process_staff_autonomy_boundary()
        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertEqual(first[0]["status"], "Needs attention")
        self.assertEqual(app.staff_management["briefs"][0]["status"], "Needs attention")
        self.assertEqual(len(app.staff_management["exceptions"]), 1)

    def test_recommendations_produce_advice_record_without_execution(self):
        app = StaffHarness()
        ok, _text, brief = app.create_staff_department_brief("Matchmaking", "Find a ranked pairing", ["fighter-1"])
        self.assertTrue(ok)
        app.commit_staff_department_brief(brief["brief_id"])
        app.set_staff_autonomy("Recommendations")
        results = app.process_staff_autonomy_boundary()
        self.assertEqual(results[0]["status"], "Recommendation")
        self.assertEqual(app.staff_management["briefs"][0]["status"], "Recommendation Ready")
        self.assertEqual(app.staff_management["exceptions"], [])
        self.assertEqual(len(app._foundation_state["operations"]), 1)

    def test_recommendation_handler_adds_evidence_without_executing_domain_work(self):
        app = StaffHarness()
        calls = []
        app.staff_action_handlers = {
            "matchmaking_review": lambda **kwargs: calls.append(kwargs) or {
                "ok": True, "spend": 0, "evidence_key": "matchmaking-evidence-1",
                "result": {"proposal": "fighter-1 vs fighter-2"},
            },
        }
        ok, _text, brief = app.create_staff_department_brief(
            "Matchmaking", "Prepare ranked pairing advice", ["fighter-1"], action_ids=["matchmaking_review"],
        )
        self.assertTrue(ok)
        self.assertTrue(app.commit_staff_department_brief(brief["brief_id"])[0])
        app.set_staff_autonomy("Recommendations")
        results = app.process_staff_autonomy_boundary()
        self.assertEqual(len(calls), 1)
        self.assertEqual(results[0]["status"], "Recommendation")
        recommendation = results[0]["recommendations"][0]
        self.assertEqual(recommendation["status"], "Ready")
        self.assertEqual(recommendation["evidence_key"], "matchmaking-evidence-1")
        self.assertEqual(recommendation["result"]["proposal"], "fighter-1 vs fighter-2")
        self.assertEqual(results[0]["spend"], 0)
        self.assertEqual(app.staff_management["briefs"][0]["status"], "Recommendation Ready")

    def test_broad_recommendations_never_runs_marketing_commit_action(self):
        app = StaffHarness()
        calls = []
        app.staff_action_handlers = {
            "campaign_plan_review": lambda **_kwargs: calls.append("review") or {
                "ok": True, "spend": 0, "evidence_key": "review-evidence",
            },
            "campaign_plan_commit": lambda **_kwargs: calls.append("commit") or {
                "ok": True, "spend": 25, "evidence_key": "commit-evidence",
            },
        }
        ok, _text, brief = app.create_staff_department_brief(
            "Marketing", "Prepare the next campaign", ["event-1"],
            action_ids=["campaign_plan_commit", "campaign_plan_review"],
        )
        self.assertTrue(ok)
        self.assertTrue(app.commit_staff_department_brief(brief["brief_id"])[0])
        app.set_staff_autonomy("Recommendations")
        result = app.process_staff_autonomy_boundary()
        self.assertEqual(calls, ["review"])
        self.assertEqual(result[0]["status"], "Recommendation")
        self.assertEqual([row["action_id"] for row in result[0]["recommendations"]], ["campaign_plan_review"])

    def test_selective_recommendations_rejects_mutating_action_instead_of_falling_back(self):
        app = StaffHarness()
        calls = []
        app.staff_action_handlers = {
            "campaign_plan_review": lambda **_kwargs: calls.append("review") or {
                "ok": True, "spend": 0, "evidence_key": "review-evidence",
            },
            "campaign_plan_commit": lambda **_kwargs: calls.append("commit") or {
                "ok": True, "spend": 25, "evidence_key": "commit-evidence",
            },
        }
        ok, _text, brief = app.create_staff_department_brief(
            "Marketing", "Commit only after approval", ["event-1"],
            action_ids=["campaign_plan_commit"],
        )
        self.assertTrue(ok)
        self.assertTrue(app.commit_staff_department_brief(brief["brief_id"])[0])
        app.set_staff_autonomy("Selective Recommendations")
        result = app.process_staff_autonomy_boundary()
        self.assertEqual(calls, [])
        recommendation = result[0]["recommendations"][0]
        self.assertEqual(recommendation["action_id"], "recommendation")
        self.assertEqual(recommendation["status"], "Needs attention")
        self.assertIn("not available as a read-only recommendation", recommendation["reason"])

    def test_staff_work_details_preserves_full_recommendation_payload(self):
        app = StaffHarness()
        work = {
            "work_id": "staff-advice:brief-1:3:2",
            "brief_id": "brief-1", "department": "Matchmaking", "status": "Recommendation",
            "boundary": "3:2", "action_id": "matchmaking_review", "target_ref": "fighter-1",
            "spend": 0, "operation_id": "work-1",
            "recommendations": [{
                "action_id": "matchmaking_review", "status": "Ready", "evidence_key": "evidence-1",
                "result": {"fighter": "Anchor", "alternatives": [{"name": "Contender", "world_rank": "#12", "hard_blocks": [], "cautions": ["Rematch cooldown"]}], "eligible_alternatives": 1},
            }],
        }
        app.staff_management["work_log"] = [work]
        receipt = app.foundation_record_work(
            "staff:brief-1:3:2:committed:recommendation", domain="staff", action="recommendation",
            target_id="fighter-1", status="committed", result={"work_id": work["work_id"], "recommendations": work["recommendations"]},
        )
        work["operation_id"] = receipt["operation_id"]
        before = repr(app.staff_management)
        detail = app.staff_work_details(operation_id=receipt["operation_id"])
        self.assertEqual(detail["work"]["work_id"], work["work_id"])
        self.assertEqual(detail["recommendations"][0]["result"]["alternatives"][0]["world_rank"], "#12")
        self.assertEqual(detail["card"]["status_label"], "Completed")
        self.assertEqual(repr(app.staff_management), before)
        self.assertIsNone(app.staff_work_details(operation_id="missing"))

    def test_registered_handler_executes_once_and_budget_denial_is_visible(self):
        app = StaffHarness()
        app.STAFF_CAPABILITIES = deepcopy(app.STAFF_CAPABILITIES)
        app.STAFF_CAPABILITIES["Marketing"]["automation"] = True
        calls = []
        app.staff_action_handlers = {
            "campaign_plan_review": lambda **kwargs: calls.append(kwargs) or {"spend": 500, "evidence_key": "evidence-1", "progression_eligible": True},
        }
        app.set_staff_guardrails(1000, 100)
        ok, _text, brief = app.create_staff_department_brief("Marketing", "Prepare a campaign", ["event-1"], action_ids=["campaign_plan_review"])
        self.assertTrue(ok)
        app.commit_staff_department_brief(brief["brief_id"])
        app.set_staff_autonomy("Full Auto")
        result = app.process_staff_autonomy_boundary()
        self.assertEqual(result[0]["status"], "Executed")
        self.assertEqual(len(calls), 1)
        self.assertEqual(app.staff_management["briefs"][0]["status"], "Completed")
        self.assertEqual(len(app._foundation_state["operations"]), 1)
        self.assertEqual(app.staff_management["progression"]["staff-4"]["credited_work_ids"], ["staff-work:staff-brief-1:3:2:campaign_plan_review"])

        app2 = StaffHarness()
        app2.STAFF_CAPABILITIES = deepcopy(app2.STAFF_CAPABILITIES)
        app2.STAFF_CAPABILITIES["Marketing"]["automation"] = True
        app2.staff_action_handlers = {"campaign_plan_review": lambda **_kwargs: {"spend": 500}}
        app2.cash = 400
        app2.set_staff_guardrails(1000, 100)
        app2.set_staff_action_ceiling("campaign_plan_review", 400)
        ok, _text, brief = app2.create_staff_department_brief("Marketing", "Prepare a campaign", ["event-1"], action_ids=["campaign_plan_review"])
        app2.commit_staff_department_brief(brief["brief_id"])
        app2.set_staff_autonomy("Full Auto")
        denied = app2.process_staff_autonomy_boundary()
        self.assertEqual(denied[0]["status"], "Needs attention")
        self.assertIn("action ceiling", denied[0]["reason"].lower())

    def test_partial_full_auto_resumes_unattempted_actions_only(self):
        app = StaffHarness()
        app.STAFF_CAPABILITIES = deepcopy(app.STAFF_CAPABILITIES)
        app.STAFF_CAPABILITIES["Marketing"]["automation"] = True
        calls = []

        def review_handler(**_kwargs):
            calls.append("review")
            return {"ok": True, "spend": 0, "evidence_key": "review-evidence"}

        def commit_handler(**_kwargs):
            calls.append("commit")
            if calls.count("commit") == 1:
                return {"ok": False, "reason": "The campaign target became unavailable."}
            return {"ok": True, "spend": 0, "evidence_key": "commit-evidence"}

        app.staff_action_handlers = {
            "campaign_plan_review": review_handler,
            "campaign_plan_commit": commit_handler,
        }
        ok, _text, brief = app.create_staff_department_brief(
            "Marketing", "Review then commit the next campaign", ["event-1"],
            action_ids=["campaign_plan_review", "campaign_plan_commit"],
        )
        self.assertTrue(ok)
        self.assertTrue(app.commit_staff_department_brief(brief["brief_id"])[0])
        app.set_staff_autonomy("Full Auto")

        first = app.process_staff_autonomy_boundary(3, 2)
        saved = app.staff_management["briefs"][0]
        self.assertEqual(calls, ["review", "commit"])
        self.assertEqual(saved["status"], "Partially completed")
        self.assertEqual(saved["completed_action_ids"], ["campaign_plan_review"])
        self.assertEqual(
            [row.get("action_id") for row in app.staff_management["work_log"]],
            ["campaign_plan_review"],
        )
        self.assertEqual(first[-1]["status"], "Needs attention")

        self.assertTrue(app.requeue_staff_department_brief(brief["brief_id"])[0])
        retry = app.process_staff_autonomy_boundary(3, 3)
        self.assertEqual(calls, ["review", "commit", "commit"])
        self.assertEqual([row["action_id"] for row in retry if row.get("status") == "Executed"], ["campaign_plan_commit"])
        self.assertEqual(app.staff_management["briefs"][0]["status"], "Completed")
        self.assertEqual(app.staff_management["briefs"][0]["completed_action_ids"], ["campaign_plan_review", "campaign_plan_commit"])
        self.assertEqual(
            [row.get("action_id") for row in app.staff_management["work_log"]],
            ["campaign_plan_review", "campaign_plan_commit"],
        )

    def test_builtin_marketing_review_is_read_only_and_evidence_backed(self):
        app = StaffHarness()
        app.ensure_player_media_state = lambda: {"media_primary_plan": {
            "plan_id": "media-plan-1", "objective": "Event Promotion", "target_id": "event-1",
            "status": "Draft", "allowed_action_ids": ["Interview"],
        }}
        app.media_plan_quote = lambda objective, target_id, action, fighter: {
            "domain": "media", "action": action, "target_id": target_id, "amount": 250,
            "details": {"objective": objective, "fighter": getattr(fighter, "name", "")},
        }
        app.media_desk_fighter = lambda: None
        ok, _text, brief = app.create_staff_department_brief(
            "Marketing", "Review the active campaign", ["event-1"], action_ids=["campaign_plan_review"],
        )
        self.assertTrue(ok)
        app.commit_staff_department_brief(brief["brief_id"])
        app.set_staff_autonomy("Full Auto")
        before = repr(app.staff_management)
        result = app.process_staff_autonomy_boundary()
        self.assertEqual(result[0]["status"], "Executed")
        self.assertEqual(result[0]["spend"], 0)
        self.assertTrue(result[0]["evidence_key"].startswith("staff-media-review:"))
        self.assertNotEqual(repr(app.staff_management), before)  # only work/receipt state changed
        self.assertEqual(app.staff_management["progression"], {})

    def test_builtin_marketing_commit_runs_selected_media_action_once(self):
        app = StaffHarness()
        fighter = type("FighterStub", (), {"fighter_id": "fighter-1", "name": "Spokesperson"})()
        app.ensure_player_media_state = lambda: {"media_primary_plan": {
            "plan_id": "media-plan-commit", "objective": "Event Promotion", "target_id": "event-1",
            "target_kind": "event", "status": "Draft", "allowed_action_ids": ["Interview"],
        }}
        app.media_plan_quote = lambda objective, target_id, action, _fighter, region="": {
            "domain": "media", "action": action, "target_id": target_id, "amount": 250,
            "details": {"objective": objective, "region": region},
        }
        app.media_desk_fighter = lambda: fighter
        calls = []
        app.execute_media_campaign_plan = lambda action, spokesperson, target=None, region="": calls.append((action, spokesperson, target, region)) or (
            True, "Campaign resolved", {"evidence_key": "campaign-evidence:1", "row": {"cost": 250, "outcome": "Strong"}},
        )
        ok, _text, brief = app.create_staff_department_brief(
            "Marketing", "Run the event campaign", ["event-1"], action_ids=["campaign_plan_commit"],
        )
        self.assertTrue(ok)
        self.assertEqual(brief["allowed_action_ids"], ["campaign_plan_commit"])
        self.assertTrue(app.commit_staff_department_brief(brief["brief_id"])[0])
        app.set_staff_guardrails(500, 0)
        app.set_staff_autonomy("Full Auto")
        result = app.process_staff_autonomy_boundary()
        self.assertEqual(result[0]["status"], "Executed")
        self.assertEqual(result[0]["action_id"], "campaign_plan_commit")
        self.assertEqual(result[0]["spend"], 250)
        self.assertEqual(result[0]["evidence_key"], "campaign-evidence:1")
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][1], fighter)
        self.assertEqual(app.staff_management["briefs"][0]["status"], "Completed")
        self.assertEqual(app.staff_management["progression"]["staff-4"]["credited_work_ids"], ["staff-work:staff-brief-1:3:2:campaign_plan_commit"])
        self.assertEqual(app.process_staff_autonomy_boundary(), [])

    def test_builtin_marketing_commit_checks_budget_before_media_apply(self):
        app = StaffHarness()
        fighter = type("FighterStub", (), {"fighter_id": "fighter-1", "name": "Spokesperson"})()
        app.cash = 400
        app.ensure_player_media_state = lambda: {"media_primary_plan": {
            "plan_id": "media-plan-budget", "objective": "Event Promotion", "target_id": "event-1",
            "target_kind": "event", "status": "Draft", "allowed_action_ids": ["Interview"],
        }}
        app.media_plan_quote = lambda *_args, **_kwargs: {"amount": 500, "details": {}}
        app.media_desk_fighter = lambda: fighter
        calls = []
        app.execute_media_campaign_plan = lambda *_args, **_kwargs: calls.append(True) or (True, "should not run", {"row": {"cost": 500}})
        ok, _text, brief = app.create_staff_department_brief(
            "Marketing", "Run the event campaign", ["event-1"], action_ids=["campaign_plan_commit"],
        )
        self.assertTrue(ok)
        app.commit_staff_department_brief(brief["brief_id"])
        app.set_staff_guardrails(1000, 100)
        app.set_staff_autonomy("Full Auto")
        result = app.process_staff_autonomy_boundary()
        self.assertEqual(result[0]["status"], "Needs attention")
        self.assertIn("cash reserve", result[0]["reason"].lower())
        self.assertEqual(calls, [])

    def test_builtin_marketing_commit_honours_brief_spend_ceiling(self):
        app = StaffHarness()
        fighter = type("FighterStub", (), {"fighter_id": "fighter-1", "name": "Spokesperson"})()
        app.ensure_player_media_state = lambda: {"media_primary_plan": {
            "plan_id": "media-plan-brief-cap", "objective": "Event Promotion", "target_id": "event-1",
            "target_kind": "event", "status": "Draft", "allowed_action_ids": ["Interview"],
        }}
        app.media_plan_quote = lambda *_args, **_kwargs: {"amount": 500, "details": {}}
        app.media_desk_fighter = lambda: fighter
        calls = []
        app.execute_media_campaign_plan = lambda *_args, **_kwargs: calls.append(True) or (
            True, "should not run", {"row": {"cost": 500}},
        )
        ok, _text, brief = app.create_staff_department_brief(
            "Marketing", "Run the capped campaign", ["event-1"],
            action_ids=["campaign_plan_commit"], spend_ceiling=400,
        )
        self.assertTrue(ok)
        self.assertTrue(app.commit_staff_department_brief(brief["brief_id"])[0])
        app.set_staff_guardrails(1000, 0)
        app.set_staff_autonomy("Full Auto")
        before_cash = app.cash
        result = app.process_staff_autonomy_boundary()
        self.assertEqual(result[0]["status"], "Needs attention")
        self.assertIn("brief ceiling", result[0]["reason"].lower())
        self.assertEqual(calls, [])
        self.assertEqual(app.cash, before_cash)

    def test_builtin_scouting_and_medical_reviews_are_read_only(self):
        app = StaffHarness()
        fighter = type("FighterStub", (), {"fighter_id": "fighter-1", "name": "Prospect One", "injured": 2, "available_week": 8})()
        app.resolve_fighter = lambda ref: fighter if str(ref) == "fighter-1" else None
        app.scouting_report_for = lambda _fighter, migrate=False: {
            "status": "Complete", "confidence": 72, "recommendation": "Worth a closer look",
        }
        app.scouting_intel_report = lambda report: report
        app.scouting_effective_confidence = lambda report: report.get("confidence", 0)
        first_ok, _text, scout_brief = app.create_staff_department_brief(
            "Scouting", "Review dossier", ["fighter-1"], action_ids=["scouting_review"],
        )
        second_ok, _text, doctor_brief = app.create_staff_department_brief(
            "Doctor", "Review return status", ["fighter-1"], action_ids=["medical_review"],
        )
        self.assertTrue(first_ok and second_ok)
        app.commit_staff_department_brief(scout_brief["brief_id"])
        app.commit_staff_department_brief(doctor_brief["brief_id"])
        app.set_staff_autonomy("Full Auto")
        before = (repr(app.staff_management), fighter.injured, fighter.available_week)
        results = app.process_staff_autonomy_boundary()
        self.assertEqual([result["status"] for result in results], ["Executed", "Executed"])
        self.assertTrue(all(result["spend"] == 0 for result in results))
        self.assertTrue(all(result["evidence_key"].startswith("staff-") for result in results))
        self.assertEqual((fighter.injured, fighter.available_week), before[1:])
        self.assertEqual(app.staff_management["progression"], {})

    def test_builtin_matchmaking_contract_and_production_reviews_are_read_only(self):
        app = StaffHarness()
        fighter = type("FighterStub", (), {
            "fighter_id": "fighter-2", "name": "Contender", "weight": "Lightweight",
            "record": "8-2-0", "status": "Ready", "contract_type": "Exclusive",
            "contract_months": 14, "purse": 9000, "relationship_trust": 71,
            "champions_clause": True, "title_shot_clause": False,
            "main_event_promise": True, "top_opponent_promise": False,
        })()
        app.resolve_fighter = lambda ref: fighter if str(ref) == "fighter-2" else None
        app.rank_label_for_fighter = lambda *_args, **_kwargs: "#4"
        app.booking_workbench_candidate_rows = lambda *_args, **_kwargs: [
            {"fighter_id": "fighter-3", "name": "Ranked Alternative", "company_rank": "#7",
             "world_rank": "#18", "hard_blocks": [], "cautions": ["Rematch cooldown"],
             "fit": 81, "build": 74},
        ]
        app.relationship_case_rows = lambda include_closed=False: [{
            "case_id": "CASE-1", "fighter_id": "fighter-2", "status": "Open",
            "reason": "Main-event promise needs a review", "available_actions": [("review_contract", "Review contract")],
            "fighter": fighter,
        }]
        app.scheduled_events = [{"event_id": "event-2", "name": "Saturday Card",
                                 "venue": "Regional Arena", "region": "Canada",
                                 "required_production": 60, "fights": [{"id": "bout-1"}, {"id": "bout-2"}]}]
        app.resolve_event_production_tier = lambda _event: ("Premium", {"cost": 1.25})
        app.media_event_production_quality = lambda _event: ("Premium", 65)
        handlers = app._staff_builtin_action_handlers()
        brief = {"brief_id": "brief-x", "last_attempt_boundary": "3:2"}
        match = handlers["matchmaking_review"](brief=brief, action_id="matchmaking_review", target_ref="fighter-2")
        contract = handlers["contract_review"](brief=brief, action_id="contract_review", target_ref="fighter-2")
        production = handlers["production_review"](brief=brief, action_id="production_review", target_ref="event-2")
        self.assertTrue(match["ok"] and contract["ok"] and production["ok"])
        self.assertEqual(match["result"]["rank"], "#4")
        self.assertEqual(match["result"]["eligible_alternatives"], 1)
        self.assertEqual(match["result"]["alternatives"][0]["world_rank"], "#18")
        self.assertEqual(contract["result"]["promises"], ["Champion's clause", "Main-event promise"])
        self.assertEqual(contract["result"]["case_count"], 1)
        self.assertEqual(contract["result"]["relationship_cases"][0]["case_id"], "CASE-1")
        self.assertEqual(production["result"]["tier"], "Premium")
        self.assertEqual(production["result"]["production_quality"], 65)
        self.assertEqual(production["result"]["required_quality"], 60)
        self.assertEqual(production["result"]["readiness"], "Ready")
        self.assertEqual(production["result"]["bout_count"], 2)
        self.assertEqual(app.cash, 100_000)

    def test_staff_target_resolution_fails_closed_for_duplicate_name_only_careers(self):
        app = StaffHarness()
        first = SimpleNamespace(fighter_id="fighter-a", name="Same Name", injured=0, available_week=0)
        second = SimpleNamespace(fighter_id="fighter-b", name="Same Name", injured=4, available_week=9)
        unique = SimpleNamespace(fighter_id="fighter-c", name="Unique Name", injured=2, available_week=7)
        app.resolve_fighter = lambda _reference: None
        app.all_fighter_objects = lambda: [first, second, unique]
        handler = app._staff_builtin_action_handlers()["medical_review"]
        brief = {"brief_id": "brief-duplicate", "last_attempt_boundary": "3:2"}
        ambiguous = handler(brief=brief, action_id="medical_review", target_ref="Same Name")
        self.assertFalse(ambiguous["ok"])
        self.assertIn("no longer available", ambiguous["reason"].lower())
        resolved = handler(brief=brief, action_id="medical_review", target_ref="fighter-c")
        self.assertTrue(resolved["ok"])
        self.assertEqual(resolved["result"]["fighter_id"], "fighter-c")

    def test_talent_relations_commit_is_full_auto_only_and_recommendations_stay_read_only(self):
        app = ContractStaffHarness()
        matrix = app.staff_capability_matrix()["Talent Relations"]
        self.assertTrue(matrix["automation_available"])
        self.assertEqual(matrix["safe_read_action_ids"], ["contract_review"])
        self.assertEqual(
            [row["id"] for row in matrix["actions"]],
            ["contract_review", "contract_batch_commit"],
        )
        self.assertTrue(matrix["actions"][1]["handler_registered"])
        self.assertFalse(matrix["actions"][1]["recommendation"])

    def test_talent_relations_contract_commit_preflights_conservative_ceiling(self):
        app = ContractStaffHarness()
        ok, _note, batch = app.create_contract_batch([app.roster[0]])
        self.assertTrue(ok)
        calls = []
        app.contract_batch_executor = lambda *_args: calls.append(True) or {
            "renewed": 1, "failed": 0,
            "results": [{"name": "Renewal Target", "status": "renewed", "cost": 20_000}],
        }
        # Exclusive quotes require a 1.75x delegated ceiling for the existing
        # negotiator's persona/RNG range.  A lower brief cap must stop before
        # Foundation invokes the domain executor.
        required = int(batch["rows"][0]["required_cash"])
        allowed_cap = int(required * 1.4)
        created, _text, brief = app.create_staff_department_brief(
            "Talent Relations", "Renew the expiring fighter", [batch["batch_id"]],
            action_ids=["contract_batch_commit"], spend_ceiling=allowed_cap,
        )
        self.assertTrue(created)
        self.assertTrue(app.commit_staff_department_brief(brief["brief_id"])[0])
        app.set_staff_autonomy("Full Auto")
        before_cash = app.cash
        result = app.process_staff_autonomy_boundary()
        self.assertEqual(result[0]["status"], "Needs attention")
        self.assertIn("preflight", result[0]["reason"].lower())
        self.assertEqual(calls, [])
        self.assertEqual(app.cash, before_cash)
        self.assertEqual(app.contract_batch_snapshot(batch["batch_id"])["status"], "Draft")

    def test_talent_relations_contract_commit_seals_batch_with_actual_evidence(self):
        app = ContractStaffHarness()
        ok, _note, batch = app.create_contract_batch([app.roster[0]])
        self.assertTrue(ok)

        def execute(fighter_obj, _row):
            app.cash -= 20_000
            return {
                "renewed": 1, "failed": 0,
                "results": [{"name": fighter_obj.name, "status": "renewed", "cost": 20_000}],
            }

        app.contract_batch_executor = execute
        created, _text, brief = app.create_staff_department_brief(
            "Talent Relations", "Renew the expiring fighter", [batch["batch_id"]],
            action_ids=["contract_batch_commit"], spend_ceiling=100_000,
        )
        self.assertTrue(created)
        self.assertTrue(app.commit_staff_department_brief(brief["brief_id"])[0])
        app.set_staff_autonomy("Full Auto")
        result = app.process_staff_autonomy_boundary()
        self.assertEqual(result[0]["status"], "Executed")
        self.assertEqual(result[0]["spend"], 20_000)
        self.assertTrue(result[0]["evidence_key"].startswith("staff-contract-commit:"))
        self.assertEqual(result[0]["result"]["batch_id"], batch["batch_id"])
        self.assertEqual(result[0]["result"]["actual_spend"], 20_000)
        self.assertEqual(app.contract_batch_snapshot(batch["batch_id"])["status"], "Completed")
        self.assertEqual(app.contract_batch_snapshot(batch["batch_id"])["results"][0]["cost"], 20_000)

    def test_needs_attention_can_be_explicitly_requeued_after_policy_changes(self):
        app = StaffHarness()
        ok, _text, brief = app.create_staff_department_brief("Marketing", "Prepare a campaign", ["event-1"], action_ids=["campaign_plan_review"])
        self.assertTrue(ok)
        app.commit_staff_department_brief(brief["brief_id"])
        app.set_staff_autonomy("Full Auto")
        first = app.process_staff_autonomy_boundary()
        self.assertEqual(first[0]["status"], "Needs attention")
        app.STAFF_CAPABILITIES = deepcopy(app.STAFF_CAPABILITIES)
        app.STAFF_CAPABILITIES["Marketing"]["automation"] = True
        app.staff_action_handlers = {"campaign_plan_review": lambda **_kwargs: {"spend": 0, "evidence_key": "evidence-retry"}}
        self.assertTrue(app.requeue_staff_department_brief(brief["brief_id"])[0])
        retry = app.process_staff_autonomy_boundary()
        self.assertEqual(retry[0]["status"], "Executed")

    def test_progression_requires_explicit_evidence_and_deduplicates_periods(self):
        app = StaffHarness()
        member = app.staff[3]
        before = (member.get("skill"), member.get("morale"))
        state = app.ensure_staff_management_state()
        work = {"work_id": "work-1", "boundary": "3:2", "action_id": "campaign_plan_review", "target_ref": "event-1"}
        self.assertIsNone(app._record_staff_progression(state, member, work, {"evidence_key": "e-1"}))
        self.assertEqual(state["progression"], {})
        first = app._record_staff_progression(
            state, member, work, {"evidence_key": "e-1", "progression_eligible": True},
        )
        self.assertEqual(first["credit_count"] if "credit_count" in first else len(first["credited_work_ids"]), 1)
        duplicate = app._record_staff_progression(
            state, member, work, {"evidence_key": "e-1", "progression_eligible": True},
        )
        self.assertEqual(len(duplicate["credited_work_ids"]), 1)
        second = dict(work, work_id="work-2", boundary="3:3")
        app._record_staff_progression(state, member, second, {"evidence_key": "e-2", "progression_eligible": True})
        snapshot = app.staff_progression_snapshot(member)
        self.assertEqual(snapshot["credit_count"], 2)
        self.assertEqual(snapshot["period_count"], 2)
        self.assertEqual(snapshot["annual_gain"], 0)
        self.assertIn("2 credits / 2 periods", snapshot["progression_label"])
        self.assertIn("+0/4 skill this year", snapshot["progression_label"])
        self.assertEqual((member.get("skill"), member.get("morale")), before)

    def test_quarter_close_applies_only_paid_multi_month_evidence(self):
        app = StaffHarness()
        app.month, app.week = 3, 4
        state = app.ensure_staff_management_state()
        member = app.staff[3]
        state["work_log"] = [
            {"work_id": "paid-1", "status": "Executed", "spend": 400, "month": 1, "lead_id": member["staff_id"], "target_ref": "event-a", "progression_eligible": True},
            {"work_id": "paid-2", "status": "Executed", "spend": 300, "month": 2, "lead_id": member["staff_id"], "target_ref": "event-b", "progression_eligible": True},
            {"work_id": "paid-3", "status": "Executed", "spend": 200, "month": 3, "lead_id": member["staff_id"], "target_ref": "event-a", "progression_eligible": True},
            {"work_id": "paid-review", "status": "Executed", "spend": 900, "month": 3, "lead_id": member["staff_id"], "target_ref": "event-c", "progression_eligible": False},
            {"work_id": "review-only", "status": "Executed", "spend": 0, "month": 3, "lead_id": member["staff_id"], "target_ref": "event-c"},
        ]
        before = member["skill"]
        gains = app.process_staff_progression_quarter_close()
        self.assertEqual(len(gains), 1)
        self.assertEqual(member["skill"], before + 1)
        self.assertEqual(app.process_staff_progression_quarter_close(), [])
        history = state["progression"][member["staff_id"]]["growth_history"][0]
        self.assertEqual(history["work_ids"], ["paid-1", "paid-2", "paid-3"])
        self.assertEqual(
            state["progression"][member["staff_id"]]["credited_work_ids"],
            ["paid-1", "paid-2", "paid-3"],
        )
        self.assertEqual(
            state["progression"][member["staff_id"]]["completed_periods"],
            ["1:4", "2:4", "3:4"],
        )

    def test_paid_work_explicitly_marked_non_progression_is_not_credited(self):
        app = StaffHarness()
        app.month, app.week = 3, 4
        state = app.ensure_staff_management_state()
        member = app.staff[3]
        state["work_log"] = [
            {"work_id": f"paid-no-credit-{month}", "status": "Executed", "spend": 500,
             "month": month, "lead_id": member["staff_id"], "target_ref": f"event-{month}",
             "progression_eligible": False}
            for month in (1, 2, 3)
        ]
        before = member["skill"]
        self.assertEqual(app.process_staff_progression_quarter_close(), [])
        self.assertEqual(member["skill"], before)
        progress = state["progression"][member["staff_id"]]
        self.assertEqual(progress["qualified_quarters"], [])
        self.assertEqual(progress["credited_work_ids"], [])

    def test_retention_snapshot_reports_observed_concerns_only(self):
        app = StaffHarness()
        member = dict(app.staff[3], morale=40)
        app.staff_contract_remaining = lambda _member: 2
        snapshot = app.staff_progression_snapshot(member)
        self.assertIn("Contract review due", snapshot["retention_concerns"])
        self.assertIn("Low morale", snapshot["retention_concerns"])
        self.assertNotIn("departure", " ".join(snapshot["retention_concerns"]).lower())
        self.assertEqual(snapshot["retention_evidence"]["workload"]["credited_work"], 0)
        self.assertEqual(snapshot["retention_evidence"]["workload"]["distinct_periods"], 0)
        self.assertEqual(snapshot["retention_evidence"]["pay"]["salary_per_month"], 0)
        self.assertEqual(snapshot["retention_evidence"]["role"]["value"], "Marketing")
        self.assertIn("Manual review only", snapshot["retention_evidence"]["review"])

    def test_retention_snapshot_marks_missing_role_without_inventing_a_departure_rule(self):
        app = StaffHarness()
        member = {"staff_id": "staff-no-role", "name": "No Role", "salary": "bad", "morale": 80}
        snapshot = app.staff_progression_snapshot(member)
        self.assertIn("Missing role", snapshot["retention_concerns"])
        self.assertEqual(snapshot["role"], "Operations")
        self.assertEqual(snapshot["retention_evidence"]["role"]["value"], "Not recorded")
        self.assertEqual(snapshot["retention_evidence"]["pay"]["salary_per_month"], 0)
        self.assertIn("Manual review only", snapshot["retention_evidence"]["review"])

    def test_progression_snapshot_is_observational_for_malformed_legacy_state(self):
        app = StaffHarness()
        app.staff_management = {
            "progression": {
                "staff-4": {
                    "completed_periods": "not-a-list",
                    "credited_work_ids": {"work": "not-a-list"},
                    "growth_history": ["raw legacy note", {"boundary": "1:1"}],
                    "qualified_quarters": None,
                    "annual_gains": ["not-a-dict"],
                },
            },
            "legacy_marker": {"keep": True},
        }
        before = deepcopy(app.staff_management)
        snapshot = app.staff_progression_snapshot(app.staff[3])
        self.assertEqual(snapshot["completed_periods"], [])
        self.assertEqual(snapshot["credited_work_ids"], [])
        self.assertEqual(snapshot["growth_history"], [{"boundary": "1:1"}])
        self.assertEqual(snapshot["qualified_quarters"], [])
        self.assertEqual(snapshot["annual_gains"], {})
        self.assertEqual(app.staff_management, before)

    def test_quarter_close_skips_malformed_work_evidence_without_crashing(self):
        app = StaffHarness()
        state = app.ensure_staff_management_state()
        state["work_log"] = [
            {"work_id": "valid-1", "status": "Executed", "spend": 100, "month": 1,
             "lead_id": "staff-4", "target_ref": "event-a", "progression_eligible": True},
            {"work_id": "valid-2", "status": "Executed", "spend": 100, "month": 2,
             "lead_id": "staff-4", "target_ref": "event-b", "progression_eligible": True},
            {"work_id": "valid-3", "status": "Executed", "spend": 100, "month": 3,
             "lead_id": "staff-4", "target_ref": "event-a", "progression_eligible": True},
            {"work_id": "bad-spend", "status": "Executed", "spend": "unknown", "month": 3,
             "lead_id": "staff-4", "target_ref": "event-c", "progression_eligible": True},
            {"work_id": "bad-month", "status": "Executed", "spend": 100, "month": "unknown",
             "lead_id": "staff-4", "target_ref": "event-d", "progression_eligible": True},
        ]
        before_log = deepcopy(state["work_log"])
        results = app.process_staff_progression_quarter_close()
        gained = next(row for row in results if row["staff_id"] == "staff-4")
        self.assertEqual(gained["skill"], 63)
        self.assertEqual(state["work_log"], before_log)

    def test_quarter_close_keeps_qualified_evidence_when_skill_baseline_is_malformed(self):
        app = StaffHarness()
        state = app.ensure_staff_management_state()
        member = app.staff[3]
        member["skill"] = "unknown"
        state["work_log"] = [
            {"work_id": f"malformed-skill-{month}", "status": "Executed", "spend": 100, "month": month,
             "lead_id": member["staff_id"], "target_ref": f"event-{month}", "progression_eligible": True}
            for month in (1, 2, 3)
        ]
        self.assertEqual(app.process_staff_progression_quarter_close(), [])
        progress = state["progression"][member["staff_id"]]
        self.assertEqual(progress["qualified_quarters"], [])
        self.assertEqual(member["skill"], "unknown")

    def test_quarter_close_ignores_duplicate_or_idless_receipts(self):
        app = StaffHarness()
        app.month, app.week = 3, 4
        state = app.ensure_staff_management_state()
        member = app.staff[3]
        state["work_log"] = [
            {"work_id": "duplicated", "status": "Executed", "spend": 100, "month": 1,
             "lead_id": member["staff_id"], "target_ref": "event-a", "progression_eligible": True},
            {"work_id": "duplicated", "status": "Executed", "spend": 100, "month": 2,
             "lead_id": member["staff_id"], "target_ref": "event-b", "progression_eligible": True},
            {"work_id": "unique", "status": "Executed", "spend": 100, "month": 3,
             "lead_id": member["staff_id"], "target_ref": "event-c", "progression_eligible": True},
            {"work_id": "", "status": "Executed", "spend": 100, "month": 3,
             "lead_id": member["staff_id"], "target_ref": "event-d", "progression_eligible": True},
        ]
        before = member["skill"]
        self.assertEqual(app.process_staff_progression_quarter_close(), [])
        self.assertEqual(member["skill"], before)
        self.assertEqual(state["progression"][member["staff_id"]]["qualified_quarters"], [])


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    if not result.result.wasSuccessful():
        raise SystemExit(1)
