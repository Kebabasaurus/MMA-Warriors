"""Production registry matches the accepted candidate without global mutation."""
from dataclasses import FrozenInstanceError
import hashlib
from types import SimpleNamespace
import unittest

import fight_moves
from fight_moves.release_registry import (
    RELEASE_MOVE_DEFINITIONS, RELEASE_MOVE_REGISTRY, RELEASE_MOVE_INDEX,
    RELEASE_CHAIN_GRAPH,
    normalize_release_signature_moves, normalize_release_move_mastery,
)
from tools.move_registry_parity import build_dump, canonical_bytes


class ReleaseRegistryTests(unittest.TestCase):
    def test_exact_accepted_candidate_registry_and_lookup_fingerprint(self):
        from analysis.fight_candidate_context import candidate_context
        profile = SimpleNamespace(
            MOVE_DEFINITIONS=RELEASE_MOVE_DEFINITIONS,
            KNOWN_PARENT_ACTIONS=fight_moves.KNOWN_PARENT_ACTIONS,
            ALL_POSITIONS=fight_moves.ALL_POSITIONS,
            REGISTRY_SCHEMA_VERSION=fight_moves.REGISTRY_SCHEMA_VERSION,
            DEFENSE_DEFINITIONS=fight_moves.DEFENSE_DEFINITIONS,
            legal_moves=RELEASE_MOVE_INDEX.legal_moves,
        )
        actual = build_dump(profile)
        with candidate_context(entries=True, chains=True, draft_content=True,
                               gift_wrap_mount=True, heel_hook_identity=True,
                               survival_expansion=True):
            self.assertEqual(RELEASE_MOVE_DEFINITIONS, fight_moves.MOVE_DEFINITIONS)
            self.assertEqual(actual, build_dump(fight_moves))
            self.assertEqual(dict(RELEASE_CHAIN_GRAPH.adjacency),
                             dict(fight_moves.CHAIN_GRAPH.adjacency))
        self.assertEqual(hashlib.sha256(canonical_bytes(actual)).hexdigest(),
                         "7e6428db43f0e25011975e954db97746cb55d9721837a7377b5bbb7ead1d6a39")

    def test_valid_complete_immutable_profile(self):
        self.assertEqual(len(RELEASE_MOVE_REGISTRY), 440)
        self.assertEqual(fight_moves.validate_move_registry(RELEASE_MOVE_DEFINITIONS), [])
        self.assertEqual(fight_moves.validate_chain_graph(RELEASE_MOVE_DEFINITIONS), [])
        self.assertEqual(sum(move.parent_action == "survive"
                             for move in RELEASE_MOVE_DEFINITIONS), 50)
        with self.assertRaises(TypeError):
            RELEASE_MOVE_REGISTRY["single_jab"] = None
        with self.assertRaises(FrozenInstanceError):
            RELEASE_MOVE_REGISTRY["single_jab"].name = "changed"
        with self.assertRaises(TypeError):
            RELEASE_CHAIN_GRAPH.adjacency["single_jab"] = ()

    def test_historical_registry_stays_separate(self):
        self.assertEqual(len(fight_moves.MOVE_DEFINITIONS), 346)
        self.assertEqual(fight_moves.MOVE_REGISTRY["heel_hook"].parent_action, "counter_leg_lock")
        self.assertEqual(RELEASE_MOVE_REGISTRY["heel_hook"].parent_action, "leg_attack")
        self.assertEqual(RELEASE_MOVE_REGISTRY["fence_drive"].positions, frozenset({"failed shot"}))
        self.assertEqual(RELEASE_MOVE_REGISTRY["gift_wrap_transition"].follow_ups,
                         ("high_mount_arm_pinch", "rear_naked_choke", "body_triangle_back_control"))
        self.assertEqual(RELEASE_MOVE_REGISTRY["single_jab"], fight_moves.MOVE_REGISTRY["single_jab"])
        self.assertTrue(set(fight_moves.MOVE_REGISTRY) <= set(RELEASE_MOVE_REGISTRY))

    def test_release_normalization_preserves_all_new_ids_and_defenses(self):
        additions = sorted(set(RELEASE_MOVE_REGISTRY) - set(fight_moves.MOVE_REGISTRY))
        self.assertEqual(len(additions), 94)
        self.assertEqual(normalize_release_signature_moves(additions, limit=94), additions)
        self.assertEqual(normalize_release_move_mastery(dict.fromkeys(additions, 73)),
                         dict.fromkeys(additions, 73))
        self.assertEqual(fight_moves.normalize_signature_moves(additions), [])
        self.assertEqual(fight_moves.normalize_move_mastery(dict.fromkeys(additions, 73)), {})
        defense = "defense:" + next(iter(fight_moves.DEFENSE_REGISTRY))
        self.assertEqual(normalize_release_move_mastery({
            additions[0]: 102, additions[1]: -4, defense: "74.4",
            "unknown_future_move": 88, "defense:unknown": 88, "single_jab": "bad",
        }), {additions[0]: 100, additions[1]: 0, defense: 74})
        self.assertEqual(normalize_release_signature_moves([
            "unknown_future_move", " " + additions[0] + " ", additions[0], additions[1],
        ], limit=2), additions[:2])

    def test_release_normalization_keeps_legacy_sanitation_and_deprecation_semantics(self):
        for values in (None, {}, "single_jab", ["single_jab", "single_jab", "unknown"],
                       [move.move_id for move in RELEASE_MOVE_DEFINITIONS if move.deprecated]):
            self.assertEqual(normalize_release_signature_moves(values),
                             fight_moves.normalize_signature_moves(values,
                                                                   registry=RELEASE_MOVE_REGISTRY))
        deprecated = {move.move_id: 65 for move in RELEASE_MOVE_DEFINITIONS if move.deprecated}
        self.assertEqual(normalize_release_move_mastery(deprecated), deprecated)
        for values in (None, [], "single_jab", {"single_jab": "52.7"}):
            self.assertEqual(normalize_release_move_mastery(values),
                             fight_moves.normalize_move_mastery(values,
                                                                registry=RELEASE_MOVE_REGISTRY))


if __name__ == "__main__":
    unittest.main()
