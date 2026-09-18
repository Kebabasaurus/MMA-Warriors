"""Draft front-headlock roles, resolution contexts and named selector coverage."""
from collections import Counter, defaultdict
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import ALL_POSITIONS, MOVE_DEFINITIONS, MoveIndex
from fight_moves.catalogue.front_headlock_development import FRONT_HEADLOCK_DEVELOPMENT
from fight_moves.catalogue.specialist_entry_development import SPECIALIST_ENTRY_DEVELOPMENT
from fight_moves.chains import MoveChainGraph, sequence_role_allows
from fight_moves.validation import validate_move_registry


class FrontHeadlockAuthoringTests(unittest.TestCase):
    def test_guillotine_grip_changes_are_declared_forward_branches(self):
        moves = {move.move_id: move for move in FRONT_HEADLOCK_DEVELOPMENT}
        for source, successor in (("front_ten_finger_guillotine", "front_high_elbow_guillotine"),
                                  ("front_high_elbow_guillotine", "front_arm_in_guillotine")):
            self.assertIn(successor, moves[source].follow_ups)
            self.assertNotIn(source, moves[successor].follow_ups)
            self.assertEqual(moves[successor].parent_action, "front_headlock_submission")
            self.assertEqual(moves[source].positions, moves[successor].positions)
            self.assertIn("guard_top_guillotine", moves[source].follow_ups)

    def combined(self):
        drafts = (*SPECIALIST_ENTRY_DEVELOPMENT, *FRONT_HEADLOCK_DEVELOPMENT)
        additions = {move.move_id: move for move in drafts}
        for move in MOVE_DEFINITIONS:
            if move.move_id in additions:
                self.assertEqual(move, additions[move.move_id])
        return (*[move for move in MOVE_DEFINITIONS if move.move_id not in additions], *drafts)

    def test_nine_unique_neutral_definitions_and_combined_graph(self):
        definitions = self.combined()
        self.assertEqual(len(FRONT_HEADLOCK_DEVELOPMENT), 9)
        self.assertEqual(Counter(move.parent_action for move in FRONT_HEADLOCK_DEVELOPMENT),
                         {"front_headlock_submission": 3, "turtle_ride": 2,
                          "front_headlock_escape": 2, "recover_guard": 1, "take_back": 1})
        self.assertEqual(validate_move_registry(definitions), [])
        self.assertEqual(len({move.name for move in definitions}), len(definitions))
        MoveChainGraph(definitions)
        for move in FRONT_HEADLOCK_DEVELOPMENT:
            self.assertEqual((move.energy, move.miss_risk, move.counter_risk), (1, 1, 1))
            self.assertLessEqual(move.minimum_skill, 54)
            if move.parent_action == "front_headlock_submission":
                self.assertTrue(move.attack_path)
                self.assertTrue(move.failure_outcomes)
                self.assertIn("choke", move.tags)

    def test_front_only_role_contracts_and_real_outcome_followups(self):
        index = MoveIndex(self.combined())
        existing = {move.move_id: move for move in self.combined()}
        self.assertEqual(len(index.legal_moves("turtle_ride", "front headlock")), 2)
        outcomes = {"front_headlock_submission": ("front headlock", "guard"),
                    "turtle_ride": ("turtle",), "take_back": ("back control", "turtle"),
                    "front_headlock_escape": ("guard", "turtle", "back control"),
                    "recover_guard": ("guard", "front headlock")}
        for move in FRONT_HEADLOCK_DEVELOPMENT:
            bottom = move.parent_action in {"front_headlock_escape", "recover_guard"}
            top, trapped = ("b", "a") if bottom else ("a", "b")
            self.assertTrue(sequence_role_allows(move.parent_action, "front headlock", "a", top, trapped))
            self.assertFalse(sequence_role_allows(move.parent_action, "front headlock", "b", top, trapped))
            for position in ALL_POSITIONS:
                self.assertEqual(move in index.legal_moves(move.parent_action, position), position == "front headlock")
            self.assertTrue(1 <= len(move.follow_ups) <= 3)
            for key in move.follow_ups:
                self.assertIn(key, existing)
                successor = existing[key]
                self.assertTrue(any(position in successor.positions and
                                    sequence_role_allows(successor.parent_action, position, "a", top, trapped)
                                    for position in outcomes[move.parent_action]), (move.move_id, key))

    def test_resolved_contexts_and_isolated_nongeneric_payloads_both_orientations(self):
        engine = FightAuditHarness()
        actor = synthetic_fighter("Front A", 75, "Grappler", "Control", 0)
        defender = synthetic_fighter("Front B", 75, "Wrestler", "Control", 1)
        self.addCleanup(random.setstate, random.getstate())
        existing = {move.move_id: move for move in self.combined()}
        for move in FRONT_HEADLOCK_DEVELOPMENT:
            bottom = move.parent_action in {"front_headlock_escape", "recover_guard"}
            for actor_key, opponent_key in (("a", "b"), ("b", "a")):
                with self.subTest(move=move.move_id, actor=actor_key):
                    top, trapped = (opponent_key, actor_key) if bottom else (actor_key, opponent_key)
                    state = {"position": "front headlock", "top": top, "bottom": trapped,
                             "clinch_controller": None, "round": 1, "tick": 2,
                             "fighter_keys": {id(actor): actor_key, id(defender): opponent_key},
                             "stats": {key: defaultdict(int) for key in ("a", "b")},
                             "gas": {"a": 80, "b": 80}, "danger": {"a": 0, "b": 0}}
                    ownership = dict(state)
                    with patch.object(engine, "action_attack_value", return_value=30), \
                         patch.object(engine, "action_defence_value", return_value=0), \
                         patch.object(engine, "fight_mechanics_rng") as rng:
                        rng.return_value.randint.return_value = 0
                        rng.return_value.random.return_value = 1.0
                        rng.return_value.choice.side_effect = lambda options: options[0]
                        engine._resolve_exchange_action(actor, defender, move.parent_action, state,
                                                        {key: defaultdict(int) for key in ("a", "b")})
                    engine.validate_fight_transition("front headlock", state["position"], state)
                    self.assertTrue(any(state["position"] in existing[key].positions and
                                        sequence_role_allows(existing[key].parent_action, state["position"],
                                                            actor_key, state["top"], state["bottom"])
                                        for key in move.follow_ups))
                    before = random.getstate()
                    with patch("fight_engine.legal_moves", side_effect=MoveIndex((move,)).legal_moves):
                        payload = engine.select_exchange_move(actor, defender, move.parent_action,
                                                              "front headlock", "", state, ownership_before=ownership)
                    self.assertEqual(payload["move_id"], move.move_id)
                    self.assertFalse(payload["generic"])
                    self.assertEqual(random.getstate(), before)


if __name__ == "__main__":
    unittest.main()
