"""Unregistered turtle catalogue roles, settled outcomes and selector identities."""
from collections import Counter, defaultdict
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import ALL_POSITIONS, MOVE_DEFINITIONS, MoveIndex
from fight_moves.catalogue.specialist_entry_development import SPECIALIST_ENTRY_DEVELOPMENT
from fight_moves.catalogue.front_headlock_development import FRONT_HEADLOCK_DEVELOPMENT
from fight_moves.catalogue.turtle_development import TURTLE_DEVELOPMENT
from fight_moves.chains import MoveChainGraph, sequence_role_allows
from fight_moves.validation import validate_move_registry


class TurtleAuthoringTests(unittest.TestCase):
    def combined(self):
        drafts = (*SPECIALIST_ENTRY_DEVELOPMENT, *FRONT_HEADLOCK_DEVELOPMENT, *TURTLE_DEVELOPMENT)
        additions = {move.move_id: move for move in drafts}
        for move in MOVE_DEFINITIONS:
            if move.move_id in additions:
                self.assertEqual(move, additions[move.move_id])
        return (*[move for move in MOVE_DEFINITIONS if move.move_id not in additions], *drafts)

    def test_ten_neutral_unique_definitions_and_combined_graph(self):
        definitions = self.combined()
        self.assertEqual(len(TURTLE_DEVELOPMENT), 10)
        self.assertEqual(Counter(move.parent_action for move in TURTLE_DEVELOPMENT),
                         {"take_back": 3, "ground_strikes": 2, "turtle_ride": 2,
                          "turtle_escape": 2, "recover_guard": 1})
        self.assertEqual(validate_move_registry(definitions), [])
        self.assertEqual(len({move.name for move in definitions}), len(definitions))
        MoveChainGraph(definitions)
        for move in TURTLE_DEVELOPMENT:
            self.assertEqual((move.energy, move.miss_risk, move.counter_risk), (1, 1, 1))
            self.assertLessEqual(move.minimum_skill, 50)

    def test_turtle_only_contexts_roles_and_outcome_followups(self):
        index = MoveIndex(self.combined())
        existing = {move.move_id: move for move in MOVE_DEFINITIONS}
        self.assertEqual(len(index.legal_moves("take_back", "turtle")), 3)
        outcomes = {"take_back": ("back control", "turtle"), "ground_strikes": ("turtle",),
                    "turtle_ride": ("turtle",), "turtle_escape": ("range", "guard", "turtle"),
                    "recover_guard": ("guard", "turtle")}
        for move in TURTLE_DEVELOPMENT:
            bottom = move.parent_action in {"turtle_escape", "recover_guard"}
            top, trapped = ("b", "a") if bottom else ("a", "b")
            self.assertTrue(sequence_role_allows(move.parent_action, "turtle", "a", top, trapped))
            self.assertFalse(sequence_role_allows(move.parent_action, "turtle", "b", top, trapped))
            for position in ALL_POSITIONS:
                self.assertEqual(move in index.legal_moves(move.parent_action, position), position == "turtle")
            self.assertTrue(1 <= len(move.follow_ups) <= 3)
            for key in move.follow_ups:
                self.assertIn(key, existing)
                self.assertTrue(any(position in existing[key].positions and
                                    sequence_role_allows(existing[key].parent_action, position, "a", top, trapped)
                                    for position in outcomes[move.parent_action]), (move.move_id, key))

    def test_real_resolver_outcomes_and_payloads_both_roles_and_orientations(self):
        engine = FightAuditHarness()
        actor = synthetic_fighter("Turtle A", 75, "Grappler", "Control", 0)
        defender = synthetic_fighter("Turtle B", 75, "Wrestler", "Control", 1)
        self.addCleanup(random.setstate, random.getstate())
        captured = {}
        class StateCaptured(Exception):
            pass
        def capture(_actor, _defender, state, *_args):
            captured.update(deepcopy(state))
            raise StateCaptured()
        with patch.object(engine, "choose_action", side_effect=capture):
            with self.assertRaises(StateCaptured):
                engine.simulate_fight(actor, defender, {})
        existing = {move.move_id: move for move in MOVE_DEFINITIONS}
        for move in TURTLE_DEVELOPMENT:
            bottom = move.parent_action in {"turtle_escape", "recover_guard"}
            for actor_key, opponent_key in (("a", "b"), ("b", "a")):
                for margin in (-30, 30):
                    with self.subTest(move=move.move_id, actor=actor_key, margin=margin):
                        state = deepcopy(captured)
                        top, trapped = (opponent_key, actor_key) if bottom else (actor_key, opponent_key)
                        state.update(position="turtle", top=top, bottom=trapped, clinch_controller=None,
                                     fighter_keys={id(actor): actor_key, id(defender): opponent_key})
                        before = deepcopy(state)
                        with patch.object(engine, "action_attack_value", return_value=margin), \
                             patch.object(engine, "action_defence_value", return_value=0), \
                             patch.object(engine, "fight_mechanics_rng") as rng:
                            rng.return_value.randint.return_value = 0
                            rng.return_value.random.return_value = 1.0
                            rng.return_value.choice.side_effect = lambda options: options[0]
                            engine._resolve_exchange_action(actor, defender, move.parent_action, state,
                                                            {key: defaultdict(int) for key in ("a", "b")})
                        engine.validate_fight_transition("turtle", state["position"], state)
                        expected = "turtle"
                        if margin > 0:
                            expected = {"take_back": "back control", "turtle_escape": "range",
                                        "recover_guard": "guard"}.get(move.parent_action, "turtle")
                        self.assertEqual(state["position"], expected)
                        if expected != "range":
                            self.assertEqual((state["top"], state["bottom"]), (top, trapped))
                        self.assertTrue(any(expected in existing[key].positions and
                                            sequence_role_allows(existing[key].parent_action, expected,
                                                                actor_key, state["top"], state["bottom"])
                                            for key in move.follow_ups))
                        target = "head" if move.parent_action == "ground_strikes" else ""
                        rng_before = random.getstate()
                        with patch("fight_engine.legal_moves", side_effect=MoveIndex((move,)).legal_moves):
                            payload = engine.select_exchange_move(actor, defender, move.parent_action,
                                                                  "turtle", target, state, ownership_before=before)
                        self.assertEqual(payload["move_id"], move.move_id)
                        self.assertFalse(payload["generic"])
                        self.assertEqual(random.getstate(), rng_before)


if __name__ == "__main__":
    unittest.main()
