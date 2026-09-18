"""Interrupted roots stay in the chain diagnostic denominator."""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import fight_moves

from analysis.generate_chain_opportunity_report import inspect_trace, summarize, maximum_three_move_coverage


def event(tick, move="jab", occurrence=None, depth=1, continuation=True, round_no=1):
    return {"type": "exchange", "actor": "a", "round": round_no, "tick": tick,
            "move_id": move, "action": move, "position_before": "range", "position_after": "range",
            "chain_depth": depth, "sequence_occurrence_id": occurrence or f"a:{round_no}:{tick}",
            "move_sequence": {"continuation_available": continuation}}


class ChainOpportunityTests(unittest.TestCase):
    def test_trace_only_stage_breakdown_preserves_counts_bounds_and_purity(self):
        for action, stage in (("survive", "undeclared_survive"),
                              ("kick", "undeclared_other_action"),
                              ("jab", "declared_action_no_named_completion")):
            root = event(1, "single_jab")
            root["action"] = "jab"
            root["move"] = {"follow_up_ids": ["double_jab"]}
            following = event(2, action, continuation=False)
            trace = [root, following, event(1, round_no=2, continuation=False)]
            before, rng = deepcopy(trace), random.getstate()
            rows = inspect_trace(trace)
            report = summarize(rows)
            self.assertEqual(report["stage_loss_breakdown"], {stage: 1})
            self.assertEqual((report["attempted_roots"], report["completed_roots"]), (1, 0))
            legacy_rows = [{key: value for key, value in row.items() if key != "stage_loss_reason"}
                           for row in rows]
            legacy_report = summarize(legacy_rows)
            for key in report:
                if key != "stage_loss_breakdown":
                    self.assertEqual(report[key], legacy_report[key])
            self.assertEqual((trace, random.getstate()), (before, rng))

    def test_declared_survival_is_not_mislabeled_as_undeclared_survival(self):
        root = event(1)
        root["move"] = {"follow_up_ids": ["test_named_recovery"]}
        definition = SimpleNamespace(parent_action="survive", deprecated=False, positions=("range",))
        with patch.dict(fight_moves.MOVE_REGISTRY, {"test_named_recovery": definition}):
            row = inspect_trace([root, event(2, "survive", continuation=False),
                                 event(1, round_no=2, continuation=False)])[0]
        self.assertEqual(row["stage_loss_reason"], "declared_action_no_named_completion")

    def test_missing_branch_evidence_does_not_claim_undeclared_action(self):
        for payload in ({"follow_up_ids": ["unknown_future_move"]}, {"follow_up_ids": "double_jab"}, {}):
            root = event(1, "unknown_root")
            root["move"] = payload
            row = inspect_trace([root, event(2, "jab", continuation=False),
                                 event(1, round_no=2, continuation=False)])[0]
            self.assertEqual(row["stage_loss_reason"], "branch_evidence_unavailable")
        root = event(1, "single_jab")
        self.assertIn(root["move_id"], fight_moves.MOVE_REGISTRY)
        row = inspect_trace([root, event(2, "jab", continuation=False),
                             event(1, round_no=2, continuation=False)])[0]
        self.assertEqual(row["stage_loss_reason"], "branch_evidence_unavailable")

    def test_active_registry_resolves_recorded_plural_and_singular_branches(self):
        definitions = {
            "test_root": SimpleNamespace(follow_ups=("test_kick",)),
            "test_kick": SimpleNamespace(parent_action="kick", deprecated=False, positions=("range",)),
        }
        with patch.dict(fight_moves.MOVE_REGISTRY, definitions):
            root = event(1, "test_root")
            root["move"] = {"follow_up_id": "test_kick"}
            following = event(2, "kick", continuation=False)
            trace = [root, following, event(1, round_no=2, continuation=False)]
            self.assertEqual(inspect_trace(trace)[0]["stage_loss_reason"], "declared_action_no_named_completion")
            root["move"] = {"follow_up_ids": ["double_jab"]}
            self.assertEqual(inspect_trace(trace)[0]["stage_loss_reason"], "undeclared_other_action")
            root["move"] = {"follow_up_ids": ["test_kick"]}
            definitions["test_kick"].positions = ("guard",)
            self.assertEqual(inspect_trace(trace)[0]["stage_loss_reason"], "undeclared_other_action")

    def test_completed_and_expired_stages_take_priority_over_branch_labels(self):
        for tick, depth, occurrence, expected in ((2, 2, "a:1:1", "completed"),
                                                   (4, 1, "other", "two_tick_expiry")):
            root = event(1)
            root["move"] = {"follow_up_ids": ["double_jab"]}
            following = event(tick, "jab", occurrence, depth, False)
            row = inspect_trace([root, following, event(1, round_no=2, continuation=False)])[0]
            self.assertEqual(row["stage_loss_reason"], expected)

    def test_three_move_union_deduplicates_cases_and_handles_fewer_choices(self):
        self.assertEqual(maximum_three_move_coverage([]), 0)
        self.assertEqual(maximum_three_move_coverage([[], []]), 0)
        self.assertEqual(maximum_three_move_coverage([["a"], ["a", "b"], ["b"]]), 3)
        self.assertEqual(maximum_three_move_coverage([["a"], ["b"], ["c"], ["d"]]), 3)
        self.assertEqual(maximum_three_move_coverage([["a", "b"], ["a", "b"], ["c"], ["d"]]), 4)

    def test_unrelated_attack_starts_another_root_and_failed_root_is_counted(self):
        trace = [event(1), event(2, "kick"), event(1, "jab", round_no=2, continuation=False)]
        before, rng = deepcopy(trace), random.getstate()
        report = summarize(inspect_trace(trace))
        self.assertEqual(report["attempted_roots"], 2)
        self.assertEqual(report["completed_roots"], 0)
        self.assertEqual(report["loss_reasons"], {"next_action_not_completed_as_declared_successor": 1, "round_boundary": 1})
        self.assertEqual((trace, random.getstate()), (before, rng))

    def test_completed_chain_counted_once_even_with_terminal_successor(self):
        trace = [event(1), event(2, "cross", "a:1:1", 2, False), event(1, round_no=2, continuation=False)]
        report = summarize(inspect_trace(trace))
        self.assertEqual((report["attempted_roots"], report["completed_roots"]), (1, 1))
        self.assertEqual(inspect_trace(trace[:2]), [])

    def test_expiry_and_ownership_loss_are_not_branch_opportunities(self):
        for following, reason in ((event(4), "two_tick_expiry"), (event(2), "ownership_role_changed")):
            root = event(1)
            if reason == "ownership_role_changed":
                root.update(position_after="guard", top_after="a", bottom_after="b")
                following.update(position_before="guard", top_before="b", bottom_before="a")
            trace = [root, following, event(1, round_no=2, continuation=False)]
            row = inspect_trace(trace)[0]
            self.assertEqual(row["reason"], reason)
            self.assertEqual(row["timely_same_role_next_action"], "")

    def test_optimistic_bound_uses_at_most_three_actions_per_root_identity(self):
        rows = [{"root_move_id": "jab", "completed": False, "reason": "missing_branch",
                 "timely_same_role_next_action": action} for action in ("jab", "jab", "cross", "shot", "kick")]
        report = summarize(rows)
        self.assertEqual(report["optimistic_three_action_completions_fixed_cohort"], 4)
        self.assertEqual(report["optimistic_three_action_pct_fixed_cohort"], 80)

    def test_existing_move_opportunities_are_per_id_frequency_with_context(self):
        rows = [
            {"root_move_id": "single_jab", "completed": False, "reason": "missing",
             "stage_loss_reason": "declared_action_no_named_completion",
             "timely_same_role_next_action": "jab", "timely_next_position": "range",
             "timely_next_target": "head", "position_target_legal_next_ids": ["double_jab", "single_jab", "double_jab"]},
            {"root_move_id": "single_jab", "completed": False, "reason": "missing",
             "stage_loss_reason": "undeclared_other_action",
             "timely_same_role_next_action": "jab", "timely_next_position": "range",
             "timely_next_target": "body", "position_target_legal_next_ids": ["double_jab"]},
        ]
        before = deepcopy(rows)
        report = summarize(rows)
        opportunities = {row["move_id"]: row for row in report["timely_existing_move_opportunities"]}
        self.assertEqual(opportunities["double_jab"]["eligible_case_count"], 2)
        self.assertEqual(opportunities["single_jab"]["eligible_case_count"], 1)
        self.assertEqual(opportunities["double_jab"]["parent_action"], "jab")
        self.assertEqual(opportunities["double_jab"]["recommended_contexts"], [
            {"action": "jab", "position": "range", "target": "body", "count": 1},
            {"action": "jab", "position": "range", "target": "head", "count": 1},
        ])
        # Counts overlap by design; they are not added to the fixed denominator.
        self.assertEqual(report["attempted_roots"], 2)
        self.assertEqual(rows, before)

    def test_opportunity_aggregation_skips_malformed_ids_and_never_claims_universal_scope(self):
        rows = [{"root_move_id": "single_jab", "completed": False, "reason": "missing",
                 "timely_same_role_next_action": "jab",
                 "position_target_legal_next_ids": [None, 3, "unknown_future_move"]}]
        report = summarize(rows)
        self.assertEqual(report["timely_existing_move_opportunities"], [])
        module = __import__("analysis.generate_chain_opportunity_report", fromlist=["build_report"])
        self.assertIn("or proves universal feasibility", module.__doc__.casefold())

    def test_root_specific_candidates_do_not_merge_and_declared_ids_are_visible(self):
        declared = fight_moves.MOVE_REGISTRY["single_jab"].follow_ups[0]
        declared_action = fight_moves.MOVE_REGISTRY[declared].parent_action
        rows = [
            {"root_move_id": "single_jab", "completed": False, "reason": "missing",
             "timely_same_role_next_action": declared_action, "timely_next_position": "range",
             "timely_next_target": "head", "position_target_legal_next_ids": [declared, "lead_hook_cross"]},
            {"root_move_id": "single_jab", "completed": False, "reason": "missing",
             "timely_same_role_next_action": declared_action, "timely_next_position": "range",
             "timely_next_target": "head", "position_target_legal_next_ids": [declared]},
            {"root_move_id": "double_jab", "completed": False, "reason": "missing",
             "timely_same_role_next_action": "jab", "timely_next_position": "range",
             "timely_next_target": "body", "position_target_legal_next_ids": ["single_jab"]},
        ]
        before = deepcopy(rows)
        report = summarize(rows)
        roots = {row["root_move_id"]: row for row in report["root_existing_move_opportunities"]}
        self.assertEqual(roots["single_jab"]["attempted"], 2)
        self.assertEqual(roots["double_jab"]["attempted"], 1)
        candidates = {row["move_id"]: row for row in roots["single_jab"]["candidate_moves"]}
        self.assertEqual(candidates[declared]["eligible_case_count"], 2)
        self.assertTrue(candidates[declared]["already_declared"])
        self.assertEqual(roots["single_jab"]["candidate_action_coverage"], [
            {"parent_action": declared_action, "eligible_case_count": 2},
        ])
        self.assertEqual(roots["single_jab"]["current_registered_follow_ups"],
                         list(fight_moves.MOVE_REGISTRY["single_jab"].follow_ups))
        self.assertIn(fight_moves.MOVE_REGISTRY[declared].parent_action,
                      roots["single_jab"]["current_registered_parent_actions"])
        self.assertEqual({row["move_id"] for row in roots["double_jab"]["candidate_moves"]},
                         {"single_jab"})
        self.assertEqual(rows, before)

    def test_empty_start_role_is_runtime_wildcard_not_an_ownership_loss(self):
        root, following = event(1), event(2, "survive", continuation=False)
        following.update(position_before="guard", top_before="b", bottom_before="a")
        rows = inspect_trace([root, following, event(1, round_no=2, continuation=False)])
        self.assertEqual(rows[0]["timely_same_role_next_action"], "survive")
        self.assertEqual(rows[0]["reason"], "next_action_not_completed_as_declared_successor")

    def test_either_actors_neutral_restart_remains_an_interrupted_root(self):
        for reset_actor in ("a", "b"):
            for reason in ("stalled_failed_shot", "stalled_standing_back"):
                root = event(1)
                reset = event(2, continuation=False)
                reset.update(actor=reset_actor, neutral_scramble_reset={"reason": reason})
                following = event(3, continuation=False)
                trace = [root, reset, following, event(1, round_no=2, continuation=False)]
                before = deepcopy(trace)
                rows = inspect_trace(trace)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["reason"], "neutral_restart")
                self.assertEqual(rows[0]["timely_same_role_next_action"], "")
                self.assertEqual(rows[0]["position_target_legal_next_ids"], [])
                report = summarize(rows)
                self.assertEqual(report["attempted_roots"], 1)
                self.assertEqual(report["completed_roots"], 0)
                self.assertEqual(report["optimistic_three_action_completions_fixed_cohort"], 0)
                self.assertEqual(trace, before)

    def test_root_commitment_cohorts_use_recorded_facts_and_reconcile(self):
        completed = event(1, "single_jab")
        completed.update(outcome="landed", position_after="range", actor_streak=3,
                         actor_gas_after=64.25,
                         move={"follow_up_ids": ["one_two", "jab_to_shot"]})
        follow = event(2, "one_two", occurrence="a:1:1", depth=2, continuation=False)
        failed = event(3, "single_jab")
        failed.update(outcome="landed", position_after="range", actor_streak=1,
                      actor_gas_after=31,
                      move={"follow_up_ids": ["one_two", "jab_to_shot"]})
        boundary = event(1, round_no=2, continuation=False)
        rows = inspect_trace([completed, follow, failed, boundary])
        report = summarize(rows)
        cohorts = {(row["dimension"], row["value"]): row
                   for row in report["root_completion_cohorts"]}
        self.assertEqual(cohorts[("position", "range")]["attempted"], 2)
        self.assertEqual(cohorts[("position", "range")]["completed"], 1)
        self.assertEqual(cohorts[("actor_streak", "3+")]["completion_pct"], 100)
        self.assertEqual(cohorts[("actor_streak", "1")]["completion_pct"], 0)
        self.assertEqual(cohorts[("gas", "60+")]["completion_pct"], 100)
        self.assertEqual(cohorts[("gas", "under-35")]["completion_pct"], 0)
        self.assertEqual(cohorts[("successor_actions", "2")]["attempted"], 2)
        for dimension in ("position", "outcome", "actor_streak", "gas", "successor_actions"):
            rows_for_dimension = [row for row in report["root_completion_cohorts"]
                                  if row["dimension"] == dimension]
            self.assertEqual(sum(row["attempted"] for row in rows_for_dimension), 2)
            self.assertEqual(sum(row["completed"] for row in rows_for_dimension), 1)

    def test_missing_commitment_facts_remain_unknown(self):
        root = event(1, "unknown_root")
        root["move"] = {}
        rows = inspect_trace([root, event(2, "jab", continuation=False),
                              event(1, round_no=2, continuation=False)])
        self.assertIsNone(rows[0]["root_actor_gas_after"])
        self.assertIsNone(rows[0]["declared_successor_action_count"])
        cohorts = {(row["dimension"], row["value"])
                   for row in summarize(rows)["root_completion_cohorts"]}
        self.assertIn(("gas", "unknown"), cohorts)
        self.assertIn(("successor_actions", "unknown"), cohorts)


if __name__ == "__main__":
    unittest.main()
