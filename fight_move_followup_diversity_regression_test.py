"""Registered successor diversity: exact fields, acyclic branches and real outcome lanes."""
from dataclasses import asdict, replace
import json
from pathlib import Path
import unittest

from fight_moves import MOVE_DEFINITIONS, STANDING_POSITIONS
from fight_moves.chains import MoveChainGraph, sequence_role_allows
from fight_moves.followup_diversity import ACTION_DIVERSE_FOLLOWUP_UPDATES
from fight_moves.validation import validate_move_registry
from tools.move_registry_parity import compare_followup_update


def combined_definitions():
    return tuple(replace(move, follow_ups=ACTION_DIVERSE_FOLLOWUP_UPDATES[move.move_id])
                 if move.move_id in ACTION_DIVERSE_FOLLOWUP_UPDATES else move
                 for move in MOVE_DEFINITIONS)


def successful_contexts(definition):
    """Possible resolved outcomes, not a claim that every branch fits every outcome."""
    action = definition.parent_action
    if action == "clinch":
        return {("clinch", None, None), ("cage", None, None)}, {
            "dirty_boxing", "cage_control", "takedown", "break_clinch"}
    if action == "break_clinch":
        return {("range", None, None)}, {"jab", "power_punch", "kick", "shoot", "clinch"}
    if action == "jab":
        return {(position, None, None) for position in STANDING_POSITIONS}, {
            "jab", "power_punch", "kick", "shoot", "clinch"}
    if action == "cage_control":
        return {(position, None, None) for position in definition.positions}, {
            "dirty_boxing", "cage_control", "takedown", "break_clinch"}
    if action == "advance_position":
        next_positions = {"guard": {"half guard"}, "half guard": {"side control"},
                          "side control": {"mount", "back control"}, "mount": {"back control"}}
        positions = set().union(*(next_positions[position] for position in definition.positions))
    elif action in {"ground_control", "ground_strikes"}:
        positions = definition.positions
    else:
        raise AssertionError(f"Unreviewed draft source action: {action}")
    return {(position, "a", "b") for position in positions}, {
        "ground_control", "ground_strikes", "advance_position", "submission"}


class FollowupDiversityTests(unittest.TestCase):
    def test_registered_updates_and_source_bound_manifest(self):
        root = Path(__file__).resolve().parent / "analysis"
        source = json.loads((root / "move_registry_schema2.json").read_text(encoding="utf-8"))
        manifest = json.loads((root / "move_followup_diversity_manifest.json").read_text(encoding="utf-8"))
        frozen = json.loads((root / "move_registry_followup_diversity.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["updates"], {
            key: {"follow_ups": list(value)} for key, value in ACTION_DIVERSE_FOLLOWUP_UPDATES.items()})
        self.assertEqual(compare_followup_update(source, frozen["dump"], manifest), [])
        by_id = {move.move_id: move for move in MOVE_DEFINITIONS}
        for key, value in ACTION_DIVERSE_FOLLOWUP_UPDATES.items():
            self.assertEqual(by_id[key].follow_ups, value)

    def test_exact_thirty_updates_only_change_successors(self):
        self.assertEqual(len(ACTION_DIVERSE_FOLLOWUP_UPDATES), 30)
        self.assertTrue(ACTION_DIVERSE_FOLLOWUP_UPDATES.keys() <= {move.move_id for move in MOVE_DEFINITIONS})
        combined = combined_definitions()
        self.assertEqual(validate_move_registry(combined), [])
        self.assertEqual([move.move_id for move in combined], [move.move_id for move in MOVE_DEFINITIONS])
        for original, updated in zip(MOVE_DEFINITIONS, combined):
            expected = asdict(original)
            expected["follow_ups"] = ACTION_DIVERSE_FOLLOWUP_UPDATES.get(original.move_id, original.follow_ups)
            self.assertEqual(asdict(updated), expected)

    def test_bounded_unique_resolved_acyclic_action_diverse_branches(self):
        definitions = combined_definitions()
        by_id = {move.move_id: move for move in definitions}
        graph = MoveChainGraph(definitions)
        for source, targets in ACTION_DIVERSE_FOLLOWUP_UPDATES.items():
            with self.subTest(source=source):
                self.assertIsInstance(targets, tuple)
                self.assertTrue(1 <= len(targets) <= 3)
                self.assertEqual(len(targets), len(set(targets)))
                self.assertGreaterEqual(len({by_id[target].parent_action for target in targets}), 3)
                for target in targets:
                    self.assertIn(target, by_id)
                    self.assertFalse(by_id[target].deprecated)
                    self.assertGreater(graph.chain_depth(source), graph.chain_depth(target))

    def test_each_successor_has_a_real_outcome_position_and_actor_role(self):
        by_id = {move.move_id: move for move in combined_definitions()}
        for source, targets in ACTION_DIVERSE_FOLLOWUP_UPDATES.items():
            contexts, actions = successful_contexts(by_id[source])
            for target in targets:
                definition = by_id[target]
                with self.subTest(source=source, target=target):
                    self.assertIn(definition.parent_action, actions)
                    self.assertTrue(any(
                        position in definition.positions
                        and sequence_role_allows(definition.parent_action, position, "a", top, bottom)
                        for position, top, bottom in contexts))

    def test_clinch_entries_follow_the_resolved_tie_up_not_the_standing_source(self):
        by_id = {move.move_id: move for move in combined_definitions()}
        entries = [source for source in ACTION_DIVERSE_FOLLOWUP_UPDATES
                   if by_id[source].parent_action == "clinch"]
        self.assertEqual(len(entries), 5)
        for source in entries:
            self.assertTrue(by_id[source].positions <= STANDING_POSITIONS)
            for target in ACTION_DIVERSE_FOLLOWUP_UPDATES[source]:
                self.assertTrue(by_id[target].positions & {"clinch", "cage"})
                self.assertFalse(by_id[target].positions & STANDING_POSITIONS)


if __name__ == "__main__":
    unittest.main()
