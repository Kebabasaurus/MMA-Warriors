"""Successor-only Phase 31 authoring and registration contracts."""
from dataclasses import asdict, replace
import json
from pathlib import Path
import unittest

from fight_moves import MOVE_DEFINITIONS
from fight_moves.chains import MoveChainGraph
from fight_moves.followup_expansion import LEGACY_FOLLOWUP_UPDATES
from fight_moves.followup_diversity import ACTION_DIVERSE_FOLLOWUP_UPDATES
from fight_moves.followup_continuity import CONTINUITY_FOLLOWUP_UPDATES
from fight_moves.legacy_ids import LEGACY_MOVE_IDS
from fight_moves.validation import validate_move_registry

APPLIED_FOLLOWUP_UPDATES = {
    **LEGACY_FOLLOWUP_UPDATES, **ACTION_DIVERSE_FOLLOWUP_UPDATES, **CONTINUITY_FOLLOWUP_UPDATES}


class FollowupAuthoringTests(unittest.TestCase):
    def combined(self):
        return tuple(replace(m, follow_ups=APPLIED_FOLLOWUP_UPDATES[m.move_id])
                     if m.move_id in APPLIED_FOLLOWUP_UPDATES else m for m in MOVE_DEFINITIONS)

    def test_legacy_quota_and_successor_only_changes(self):
        self.assertTrue(LEGACY_FOLLOWUP_UPDATES.keys() <= LEGACY_MOVE_IDS)
        baseline = json.loads((Path(__file__).resolve().parent / "analysis" / "move_registry_parity.json").read_text(encoding="utf-8"))
        original = {m["move_id"]: m for m in baseline["dump"]["moves"]}
        newly_wired = [key for key in LEGACY_FOLLOWUP_UPDATES if not original[key]["follow_ups"]]
        self.assertGreaterEqual(len(newly_wired), 101)
        self.assertGreaterEqual(sum(bool(m.follow_ups) for m in self.combined() if m.move_id in LEGACY_MOVE_IDS), 150)
        for definition in MOVE_DEFINITIONS:
            if definition.move_id in APPLIED_FOLLOWUP_UPDATES:
                self.assertEqual(definition.follow_ups, APPLIED_FOLLOWUP_UPDATES[definition.move_id])
        for old, changed in zip(MOVE_DEFINITIONS, self.combined()):
            expected = asdict(old)
            expected["follow_ups"] = APPLIED_FOLLOWUP_UPDATES.get(old.move_id, old.follow_ups)
            self.assertEqual(asdict(changed), expected)

    def test_graph_has_no_cycles_or_unresolved_targets(self):
        combined = self.combined()
        self.assertEqual(validate_move_registry(combined), [])
        graph = MoveChainGraph(combined)
        self.assertGreater(graph.max_depth, 1)
        for source, targets in APPLIED_FOLLOWUP_UPDATES.items():
            self.assertTrue(1 <= len(targets) <= 3)
            self.assertEqual(len(set(targets)), len(targets))
            for target in targets:
                self.assertGreater(graph.chain_depth(source), graph.chain_depth(target))

    def test_successor_positions_and_actor_roles(self):
        by_id = {m.move_id: m for m in self.combined()}
        top_actions = {"ground_control", "ground_strikes", "advance_position", "submission", "turtle_ride", "take_back"}
        bottom_actions = {"recover_guard", "bottom_submission", "sweep", "stand_up", "cling"}
        standing_actions = {"jab", "power_punch", "kick", "shoot", "clinch"}
        for source, targets in APPLIED_FOLLOWUP_UPDATES.items():
            definition = by_id[source]
            action = definition.parent_action
            if action in {"shoot", "takedown"}:
                positions, actions = {"guard", "half guard", "cage"}, top_actions | {"takedown"}
            elif action == "clinch":
                positions, actions = {"clinch", "cage"}, {"dirty_boxing", "cage_control", "takedown", "break_clinch"}
            elif action in {"break_clinch", "stand_up"}:
                positions, actions = {"range"}, standing_actions
            elif action in {"recover_guard", "bottom_submission"}:
                positions, actions = {"guard"} if action == "recover_guard" else set(definition.positions), bottom_actions
            elif action == "sweep":
                positions, actions = {"guard"}, top_actions
            elif action == "cling":
                positions, actions = set(definition.positions), bottom_actions
            elif action == "advance_position":
                next_positions = {"guard": "half guard", "half guard": "side control", "side control": "mount", "mount": "back control"}
                positions, actions = {next_positions[p] for p in definition.positions if p in next_positions}, top_actions
            elif action in top_actions:
                positions, actions = set(definition.positions), top_actions
            elif action in {"dirty_boxing", "cage_control"}:
                positions, actions = {"clinch", "cage"}, {"dirty_boxing", "cage_control", "takedown", "break_clinch"}
            else:
                positions, actions = {"range", "pocket"}, standing_actions
            for target in targets:
                with self.subTest(source=source, target=target):
                    self.assertTrue(by_id[target].positions & positions)
                    self.assertIn(by_id[target].parent_action, actions)

    def test_original_shots_retain_cage_and_top_success_options(self):
        for definition in self.combined():
            if definition.move_id not in LEGACY_MOVE_IDS or definition.parent_action != "shoot":
                continue
            targets = [next(m for m in self.combined() if m.move_id == key) for key in definition.follow_ups]
            for position in {"guard", "half guard", "cage"}:
                self.assertTrue(any(position in target.positions for target in targets), (definition.move_id, position))


if __name__ == "__main__":
    unittest.main()
