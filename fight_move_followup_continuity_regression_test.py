"""Second-layer registration: genuine alternatives, no deleted roots or illegal roles."""
from dataclasses import asdict, replace
import json
from pathlib import Path
import unittest

from fight_moves import MOVE_DEFINITIONS, STANDING_POSITIONS
from fight_moves.chains import MoveChainGraph, sequence_role_allows
from fight_moves.followup_continuity import CONTINUITY_FOLLOWUP_UPDATES
from fight_moves.followup_diversity import ACTION_DIVERSE_FOLLOWUP_UPDATES
from fight_moves.validation import validate_move_registry
from tools.move_registry_parity import build_dump, compare_followup_update
import fight_moves


def combined_definitions():
    return tuple(replace(move, follow_ups=CONTINUITY_FOLLOWUP_UPDATES[move.move_id])
                 if move.move_id in CONTINUITY_FOLLOWUP_UPDATES else move
                 for move in MOVE_DEFINITIONS)


def outcome_contexts(move):
    standing_actions = {"jab", "power_punch", "kick", "shoot", "clinch"}
    top_actions = {"ground_strikes", "ground_control", "advance_position", "submission"}
    tie_actions = {"dirty_boxing", "cage_control", "takedown", "break_clinch"}
    if move.parent_action in {"jab", "power_punch", "kick"}:
        return {(position, None, None) for position in STANDING_POSITIONS}, standing_actions
    if move.parent_action in {"stand_up", "break_clinch"}:
        return {("range", None, None)}, standing_actions
    if move.parent_action == "clinch":
        return {("clinch", None, None), ("cage", None, None)}, tie_actions
    if move.parent_action in {"dirty_boxing", "cage_control"}:
        return {(position, None, None) for position in move.positions}, tie_actions
    if move.parent_action == "cling":
        return {(position, "b", "a") for position in move.positions}, {
            "bottom_submission", "recover_guard", "stand_up", "sweep", "cling"}
    if move.parent_action == "advance_position":
        next_positions = {"guard": {"half guard"}, "half guard": {"side control"},
                          "side control": {"mount", "back control"}, "mount": {"back control"},
                          # Legacy resolver fallback for this declared source;
                          # not evidence that ordinary turtle action choice emits it.
                          "turtle": {"side control"}}
        positions = set().union(*(next_positions[position] for position in move.positions))
    elif move.parent_action in {"ground_control", "ground_strikes"}:
        positions = move.positions
    else:
        raise AssertionError(f"Unreviewed continuity source action: {move.parent_action}")
    return {(position, "a", "b") for position in positions}, top_actions


class FollowupContinuityTests(unittest.TestCase):
    def test_unknown_source_position_is_not_given_an_invented_outcome(self):
        move = next(m for m in MOVE_DEFINITIONS if m.move_id == "back_take_transition")
        with self.assertRaises(KeyError):
            outcome_contexts(replace(move, positions=frozenset({"unreviewed position"})))

    def test_registered_updates_and_exact_source_bound_manifest(self):
        root = Path(__file__).resolve().parent / "analysis"
        source = json.loads((root / "move_registry_followup_diversity.json").read_text(encoding="utf-8"))
        manifest = json.loads((root / "move_followup_continuity_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["updates"], {
            key: {"follow_ups": list(value)} for key, value in CONTINUITY_FOLLOWUP_UPDATES.items()})
        self.assertEqual(compare_followup_update(source, build_dump(fight_moves), manifest), [])
        by_id = {move.move_id: move for move in MOVE_DEFINITIONS}
        for key, value in CONTINUITY_FOLLOWUP_UPDATES.items():
            self.assertEqual(by_id[key].follow_ups, value)

    def test_thirty_additional_roots_only_change_successors(self):
        updates = CONTINUITY_FOLLOWUP_UPDATES
        self.assertEqual(len(updates), 30)
        self.assertFalse(updates.keys() & ACTION_DIVERSE_FOLLOWUP_UPDATES.keys())
        self.assertTrue(updates.keys() <= {move.move_id for move in MOVE_DEFINITIONS})
        combined = combined_definitions()
        self.assertEqual(validate_move_registry(combined), [])
        self.assertEqual([move.move_id for move in combined], [move.move_id for move in MOVE_DEFINITIONS])
        for old, new in zip(MOVE_DEFINITIONS, combined):
            expected = asdict(old)
            expected["follow_ups"] = updates.get(old.move_id, old.follow_ups)
            self.assertEqual(asdict(new), expected)
            if old.move_id in updates:
                self.assertTrue(old.follow_ups, "Only existing attempted roots are in scope")
                self.assertTrue(new.follow_ups, "An abandoned root must not be hidden by deletion")

    def test_bounded_acyclic_and_action_diverse_targets(self):
        definitions = combined_definitions()
        by_id = {move.move_id: move for move in definitions}
        graph = MoveChainGraph(definitions)
        for source, targets in CONTINUITY_FOLLOWUP_UPDATES.items():
            with self.subTest(source=source):
                self.assertTrue(1 <= len(targets) <= 3)
                self.assertEqual(len(targets), len(set(targets)))
                self.assertGreaterEqual(len({by_id[target].parent_action for target in targets}), 2)
                for target in targets:
                    self.assertIn(target, by_id)
                    self.assertFalse(by_id[target].deprecated)
                    self.assertNotEqual(by_id[target].parent_action, "survive")
                    self.assertGreater(graph.chain_depth(source), graph.chain_depth(target))

    def test_every_branch_has_a_real_success_position_and_role(self):
        by_id = {move.move_id: move for move in combined_definitions()}
        for source, targets in CONTINUITY_FOLLOWUP_UPDATES.items():
            contexts, allowed_actions = outcome_contexts(by_id[source])
            for target in targets:
                definition = by_id[target]
                with self.subTest(source=source, target=target):
                    self.assertIn(definition.parent_action, allowed_actions)
                    self.assertTrue(any(position in definition.positions and sequence_role_allows(
                        definition.parent_action, position, "a", top, bottom)
                        for position, top, bottom in contexts))

    def test_new_bottom_branches_cannot_claim_top_actions(self):
        by_id = {move.move_id: move for move in combined_definitions()}
        sources = [source for source in CONTINUITY_FOLLOWUP_UPDATES if by_id[source].parent_action == "cling"]
        self.assertEqual(len(sources), 4)
        for source in sources:
            for target in CONTINUITY_FOLLOWUP_UPDATES[source]:
                self.assertIn(by_id[target].parent_action, {"recover_guard", "bottom_submission", "stand_up"})


if __name__ == "__main__":
    unittest.main()
