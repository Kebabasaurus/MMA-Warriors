"""Graph safety gates before denser follow-up authoring."""
from dataclasses import replace, FrozenInstanceError
import unittest
from fight_moves import MOVE_DEFINITIONS, CHAIN_GRAPH, MoveChainGraph, move, validate_move_registry


def node(key, *targets):
    return move(key, key, "jab", {"range"}, follow_ups=targets)


class ChainGraphTests(unittest.TestCase):
    def test_current_registry_is_acyclic_and_ordered(self):
        self.assertEqual(validate_move_registry(), [])
        for definition in MOVE_DEFINITIONS:
            self.assertEqual(CHAIN_GRAPH.adjacency[definition.move_id], definition.follow_ups)
        self.assertEqual(CHAIN_GRAPH.report()["unresolved_targets"], [])

    def test_branch_depth_counts_edges_not_observed_fight_actions(self):
        graph = MoveChainGraph((node("a", "b", "d"), node("b", "c"), node("c"), node("d")))
        self.assertEqual(graph.roots, ("a",))
        self.assertEqual([graph.chain_depth(k) for k in ("a", "b", "c", "d")], [2, 1, 0, 0])
        self.assertEqual(graph.max_depth, 2)
        with self.assertRaises(KeyError):
            graph.chain_depth("unknown")

    def test_cycles_self_loops_and_unknown_targets_fail(self):
        for definitions in ((node("a", "a"),), (node("a", "b"), node("b", "a"))):
            with self.assertRaisesRegex(ValueError, "cycle"):
                MoveChainGraph(definitions)
        with self.assertRaisesRegex(ValueError, "Unresolved chain targets: absent"):
            MoveChainGraph((node("a", "absent"),))

    def test_registry_validator_rejects_authored_cycle(self):
        first, *rest = MOVE_DEFINITIONS
        changed = (replace(first, follow_ups=(first.move_id,)), *rest)
        self.assertTrue(any("cycle" in error for error in validate_move_registry(changed)))

    def test_import_time_registry_construction_rejects_cycle(self):
        import importlib
        from unittest.mock import patch
        import fight_moves.catalogue as catalogue
        import fight_moves.registry as registry
        first, *rest = MOVE_DEFINITIONS
        changed = (replace(first, follow_ups=(first.move_id,)), *rest)
        try:
            with patch.object(catalogue, "MOVE_DEFINITIONS", changed):
                with self.assertRaisesRegex(ValueError, "cycle"):
                    importlib.reload(registry)
        finally:
            importlib.reload(registry)

    def test_long_catalogues_do_not_depend_on_python_recursion_limit(self):
        graph = MoveChainGraph(tuple(node(str(i), *([str(i + 1)] if i < 1999 else [])) for i in range(2000)))
        self.assertEqual(graph.chain_depth("0"), 1999)
        with self.assertRaises(TypeError):
            graph.adjacency["0"] = ()
        with self.assertRaises(FrozenInstanceError):
            graph.max_depth = 0


if __name__ == "__main__":
    unittest.main()
