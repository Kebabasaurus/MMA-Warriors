"""Phase 29 content, fallback, save identity and complete-fight acceptance."""
import json
from pathlib import Path
import random
import unittest

from fight_engine_audit import FightAuditHarness, synthetic_fighter
from fight_moves import MOVE_DEFINITIONS, legal_moves, normalize_move_mastery, normalize_signature_moves
from fight_moves.catalogue.top_submissions import PHASE_29
from fight_moves.validation import validate_move_registry
from analysis.generate_move_coverage_report import phase_29_failures


class SubmissionExpansionTests(unittest.TestCase):
    def test_sixteen_new_moves_fill_top_position_pools(self):
        self.assertEqual(len(PHASE_29), 16)
        self.assertEqual(sum(m.parent_action == "submission" for m in MOVE_DEFINITIONS), 25)
        for position in ("guard", "half guard"):
            self.assertGreaterEqual(len(legal_moves("submission", position)), 6)
        self.assertTrue(all(m.follow_ups and m.attack_path and m.failure_outcomes for m in PHASE_29))
        self.assertEqual(validate_move_registry(), [])

    def test_low_skill_fighter_keeps_the_ungated_fallback_without_rng_draws(self):
        engine = FightAuditHarness()
        a = synthetic_fighter("Novice", 30, "Boxer", "Balanced", 0)
        b = synthetic_fighter("Opponent", 30, "Boxer", "Balanced", 1)
        a.detailed_skills = dict.fromkeys(a.detailed_skills, 20)
        before = random.getstate()
        for position in ("guard", "half guard"):
            move = engine.select_exchange_move(a, b, "submission", position, "", {"round": 1, "tick": 1})
            self.assertEqual(move["move_id"], "top_submission_chain")
        self.assertEqual(random.getstate(), before)

    def test_new_ids_persist_and_cannot_be_removed(self):
        ids = [m.move_id for m in PHASE_29[:3]]
        self.assertEqual(normalize_signature_moves(ids), ids)
        mastery = {key: 70 for key in ids}
        self.assertEqual(normalize_move_mastery(json.loads(json.dumps(mastery))), mastery)
        remaining = [m for m in MOVE_DEFINITIONS if m.move_id != ids[0]]
        self.assertTrue(any(ids[0] in error for error in validate_move_registry(remaining)))

    def test_complete_fight_report_meets_phase_targets(self):
        report = json.loads((Path(__file__).resolve().parent / "analysis" / "move_coverage_report.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(report["fight_count"], 300)
        self.assertEqual(phase_29_failures(report), [])


if __name__ == "__main__":
    unittest.main()
