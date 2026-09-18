"""Fifteen draft leg identities: controller roles, no invented submission credit."""
from collections import Counter, defaultdict
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import ALL_POSITIONS, MOVE_DEFINITIONS, MoveIndex
from analysis.fight_candidate_context import DRAFT_MOVE_DEFINITIONS
from fight_moves.catalogue.leg_entanglement_development import (
    LEG_ATTACK_DEVELOPMENT, LEG_POSITION_DEVELOPMENT, LEG_ENTANGLEMENT_DEVELOPMENT,
)
from fight_moves.chains import MoveChainGraph, sequence_role_allows
from fight_moves.validation import validate_move_registry


class LegEntanglementAuthoringTests(unittest.TestCase):
    def combined(self):
        result = {}
        for move in (*MOVE_DEFINITIONS, *DRAFT_MOVE_DEFINITIONS, *LEG_ENTANGLEMENT_DEVELOPMENT):
            if move.move_id in result:
                self.assertEqual(result[move.move_id], move)
            result[move.move_id] = move
        return tuple(result.values())

    def test_budget_385_plus_15_and_neutral_valid_graph(self):
        combined = self.combined()
        added_ids = {move.move_id for move in LEG_ENTANGLEMENT_DEVELOPMENT}
        self.assertEqual(sum(move.move_id not in added_ids for move in combined), 385)
        self.assertEqual(len(combined), 400)  # Draft union, not production registration.
        self.assertEqual((len(LEG_ATTACK_DEVELOPMENT), len(LEG_POSITION_DEVELOPMENT)), (5, 10))
        self.assertEqual(Counter(move.parent_action for move in LEG_ENTANGLEMENT_DEVELOPMENT),
                         {"leg_attack": 5, "leg_control": 3, "leg_escape": 3,
                          "counter_leg_lock": 2, "disengage_leg": 2})
        self.assertEqual(validate_move_registry(combined), [])
        self.assertEqual(len({move.name for move in combined}), len(combined))
        MoveChainGraph(combined)
        for move in LEG_ENTANGLEMENT_DEVELOPMENT:
            self.assertEqual((move.energy, move.miss_risk, move.counter_risk), (1, 1, 1))
            if move.parent_action == "leg_attack":
                self.assertTrue(move.attack_path and move.failure_outcomes)
                self.assertIn("submission", move.tags)
            if move.parent_action == "counter_leg_lock":
                self.assertNotIn("submission", move.tags)
                # This is a leg-pummel reversal, not the striking counter gate.
                self.assertNotIn("counter", move.tags)

    def test_positions_opposite_roles_and_legal_acyclic_successors(self):
        combined = self.combined()
        index, by_id = MoveIndex(combined), {move.move_id: move for move in combined}
        for move in LEG_ENTANGLEMENT_DEVELOPMENT:
            bottom = move.parent_action in {"leg_escape", "counter_leg_lock"}
            top, trapped = ("b", "a") if bottom else ("a", "b")
            self.assertTrue(sequence_role_allows(move.parent_action, "leg entanglement", "a", top, trapped))
            self.assertFalse(sequence_role_allows(move.parent_action, "leg entanglement", "b", top, trapped))
            for position in ALL_POSITIONS:
                self.assertEqual(move in index.legal_moves(move.parent_action, position), position == "leg entanglement")
            # Possible settled role/position pairs for this actor. A successful
            # counter grants knee-line control without sweeping to physical top.
            outcomes = (("leg entanglement", "a", "b"),)
            if move.parent_action == "leg_escape":
                outcomes = (("range", None, None), ("guard", "b", "a"), ("leg entanglement", "b", "a"))
            elif move.parent_action == "disengage_leg":
                outcomes = (("range", None, None),)
            self.assertTrue(1 <= len(move.follow_ups) <= 3)
            for key in move.follow_ups:
                successor = by_id[key]
                self.assertTrue(any(position in successor.positions and
                                    sequence_role_allows(successor.parent_action, position, "a", owner, other)
                                    for position, owner, other in outcomes), (move.move_id, key))

    def test_real_resolver_ownership_exits_and_isolated_payloads(self):
        engine = FightAuditHarness()
        engine._experimental_specialist_entries = True
        actor = synthetic_fighter("Leg A", 80, "Grappler", "Control", 0)
        defender = synthetic_fighter("Leg B", 80, "Wrestler", "Control", 1)
        self.addCleanup(random.setstate, random.getstate())
        combined_registry = {move.move_id: move for move in self.combined()}
        for move in LEG_ENTANGLEMENT_DEVELOPMENT:
            bottom = move.parent_action in {"leg_escape", "counter_leg_lock"}
            for actor_key, other_key in (("a", "b"), ("b", "a")):
                for margin in (-30, 0, 30):
                    with self.subTest(move=move.move_id, actor=actor_key, margin=margin):
                        owner, trapped = (other_key, actor_key) if bottom else (actor_key, other_key)
                        state = {"position": "leg entanglement", "top": owner, "bottom": trapped,
                                 "clinch_controller": None, "round": 1, "tick": 2,
                                 "fighter_keys": {id(actor): actor_key, id(defender): other_key},
                                 "stats": {key: defaultdict(int) for key in ("a", "b")},
                                 "gas": {"a": 80, "b": 80}, "danger": {"a": 0, "b": 0}}
                        before = deepcopy(state)
                        stats = {key: defaultdict(int) for key in ("a", "b")}
                        with patch.object(engine, "action_attack_value", return_value=margin), \
                             patch.object(engine, "action_defence_value", return_value=0), \
                             patch.object(engine, "fight_mechanics_rng") as rng:
                            rng.return_value.randint.return_value = 0
                            rng.return_value.random.return_value = 1.0
                            # Only inside/outside heel hooks currently have an
                            # exactly matching mechanical delivery. Do not
                            # manufacture rolling/belly-down/figure-four facts.
                            expected_technique = {
                                "entangled_inside_heel_hook": "inside heel hook",
                                "entangled_outside_heel_hook": "outside heel hook",
                            }.get(move.move_id, "heel hook")
                            rng.return_value.choice.side_effect = lambda options: next(
                                row for row in options if row[0] == expected_technique)
                            engine._resolve_exchange_action(actor, defender, move.parent_action, state, stats)
                            if move.parent_action == "counter_leg_lock":
                                rng.return_value.random.assert_not_called()
                                rng.return_value.choice.assert_not_called()
                        engine.validate_fight_transition("leg entanglement", state["position"], state)
                        expected = "leg entanglement"
                        if move.parent_action == "disengage_leg" or move.parent_action == "leg_escape" and margin > 8:
                            expected = "range"
                        elif move.parent_action == "leg_escape" and margin > -5:
                            expected = "guard"
                        self.assertEqual(state["position"], expected)
                        if expected == "range":
                            self.assertIsNone(state["top"])
                            self.assertIsNone(state["bottom"])
                        elif move.parent_action == "counter_leg_lock" and margin > 5:
                            self.assertEqual((state["top"], state["bottom"]), (actor_key, other_key))
                            self.assertEqual(stats[actor_key]["danger"], 3)
                        else:
                            self.assertEqual((state["top"], state["bottom"]), (owner, trapped))
                        self.assertEqual(state["stats"][actor_key]["sub_att"], int(move.parent_action == "leg_attack"))
                        self.assertEqual(state["stats"][actor_key]["td"], 0)
                        if move.parent_action == "counter_leg_lock":
                            self.assertEqual(stats[actor_key]["control"], 0)
                            self.assertNotIn("submission_finish", state)
                        rng_before = random.getstate()
                        with patch("fight_engine.legal_moves", side_effect=MoveIndex((move,)).legal_moves), \
                             patch("fight_engine.MOVE_REGISTRY", combined_registry):
                            # An isolated payload proves authored eligibility,
                            # not that the resolver attempted that named lock.
                            payload = engine.select_exchange_move(actor, defender, move.parent_action,
                                                                  "leg entanglement", "", state, ownership_before=before)
                            if move.parent_action == "leg_attack":
                                resolved = engine.select_exchange_move(
                                    actor, defender, move.parent_action, "leg entanglement", "", state,
                                    ownership_before=before, resolved_technique=state["last_submission_technique"])
                                compatible = move.move_id in {
                                    "entangled_inside_heel_hook", "entangled_outside_heel_hook"}
                                self.assertEqual(resolved["generic"], not compatible)
                                if compatible:
                                    self.assertEqual(resolved["move_id"], move.move_id)
                                else:
                                    self.assertFalse(resolved["signature"])
                                    self.assertNotEqual(resolved["move_id"], move.move_id)
                        self.assertEqual(payload["move_id"], move.move_id)
                        self.assertFalse(payload["generic"])
                        self.assertEqual(random.getstate(), rng_before)


if __name__ == "__main__":
    unittest.main()
