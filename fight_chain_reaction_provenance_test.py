"""Selected defense labels cannot author a candidate's preferred successor."""
import random
import unittest
from unittest.mock import patch

from analysis.generate_chain_opportunity_report import inspect_trace
from analysis.fight_candidate_context import candidate_context
from fight_engine_audit import FightAuditHarness, run_audited_fight, synthetic_fighter, move_report_specs
from fight_moves import MOVE_REGISTRY
from fight_moves.selection_pool import ordinary_selection_pool


class ChainReactionProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(random.setstate, random.getstate())
        self.engine = FightAuditHarness()

    def root(self, tags=(), followups=("arm_triangle", "top_armbar")):
        return {
            "type": "exchange", "actor": "a", "round": 2, "tick": 4,
            "action": "ground_strikes", "outcome": "landed",
            "move_id": "mounted_hammerfist_flurry", "position_before": "mount",
            "position_after": "mount", "top_before": "a", "top_after": "a",
            "bottom_before": "b", "bottom_after": "b", "defense": {"tags": tags},
            "move": {"follow_up_ids": followups, "sequence_source_id": "", "sequence_step": 0},
        }

    def update(self, event, independent=True):
        state = {"move_chains": {"a": {}, "b": {}}}
        self.engine.update_move_sequence(state, event, independent_alternatives=independent)
        return state

    def test_landed_defense_tags_do_not_choose_candidate_alternative(self):
        baseline = None
        for tags in ((), ("frame",), ("evasion",), ("escape",), ("block",)):
            event = self.root(tags)
            rng = random.getstate()
            chain = self.update(event)["move_chains"]["a"]
            self.assertEqual(chain["branch_options"], ["arm_triangle", "top_armbar"])
            self.assertEqual(chain["next_move_id"], "")
            self.assertEqual(chain["branch_reason"], "legal-alternatives")
            self.assertTrue(event["move_sequence"]["continuation_available"])
            self.assertFalse(event["move_sequence"]["completed_follow_up"])
            self.assertEqual(random.getstate(), rng)
            if baseline is not None:
                self.assertEqual(chain, baseline)
            baseline = chain

    def test_pool_keeps_both_legal_continuations_without_forcing_second(self):
        chain = self.update(self.root(("frame",)))["move_chains"]["a"]
        rows = [(50, MOVE_REGISTRY["arm_triangle"]), (49, MOVE_REGISTRY["top_armbar"])]
        pool, kind = ordinary_selection_pool(rows, set(chain["branch_options"]), chain, expanded=True)
        self.assertEqual(pool, rows)
        self.assertEqual(kind, "chain")
        observed = set()
        for tick in range(1, 101):
            move = self.engine._select_from_pool(list(rows), False, set(), set(chain["branch_options"]),
                chain, "fighter", "submission", "mount", "", {"round": 2, "tick": tick})
            observed.add(move.move_id)
        self.assertEqual(observed, {"arm_triangle", "top_armbar"})

    def test_legacy_second_index_and_single_legal_candidate(self):
        chain = self.update(self.root(("frame",)), independent=False)["move_chains"]["a"]
        self.assertEqual(chain["next_move_id"], "top_armbar")
        self.assertEqual(chain["branch_reason"], "defensive-reaction")
        event = self.root(("frame",), ("top_armbar", "single_jab"))
        chain = self.update(event)["move_chains"]["a"]
        self.assertEqual(chain["branch_options"], ["top_armbar"])
        self.assertEqual(chain["next_move_id"], "top_armbar")
        self.assertEqual(chain["branch_reason"], "sole-legal-continuation")

    def test_expired_interrupted_and_terminal_roots_stay_in_denominator(self):
        for reason, next_round, next_tick, neutral in (
            ("two_tick_expiry", 2, 7, False), ("round_boundary", 3, 1, False),
            ("neutral_restart", 2, 5, True), ("fight_ended_before_next_own_action", None, None, False),
        ):
            root = self.root(("frame",))
            state = self.update(root)
            trace = [root]
            if next_round is not None:
                following = self.root((), ())
                following.update(round=next_round, tick=next_tick, outcome="control")
                if neutral:
                    following["neutral_scramble_reset"] = {"reason": "test reset"}
                self.engine.update_move_sequence(state, following, independent_alternatives=True)
                trace.append(following)
            rows = inspect_trace(trace)
            self.assertEqual(len(rows), 1, rows)
            self.assertEqual(rows[0]["reason"], reason)
            self.assertEqual(rows[0]["depth"], 1)
            if neutral:
                self.assertEqual(state["move_chains"], {"a": {}, "b": {}})

    def test_default_off_complete_bout_parity_with_explicit_legacy_updater(self):
        a = synthetic_fighter("Red", 75, "Boxer", "Pressure", 0)
        b = synthetic_fighter("Blue", 75, "Wrestler", "Control", 1)
        baseline = run_audited_fight(self.engine, a, b, 94187, {})
        baseline_rng = random.getstate()
        original = self.engine.update_move_sequence

        def legacy(state, event, **kwargs):
            self.assertFalse(kwargs.get("independent_alternatives", False))
            return original(state, event, independent_alternatives=False)

        self.engine._experimental_chain_action_weighting = False
        with patch.object(self.engine, "update_move_sequence", side_effect=legacy):
            observed = run_audited_fight(self.engine, a, b, 94187, {})
        self.assertEqual(observed, baseline)
        self.assertEqual(random.getstate(), baseline_rng)

    def test_real_recorder_uses_independent_candidate_alternatives(self):
        spec = move_report_specs()[0]
        a = synthetic_fighter(f"Move audit {spec['id']} A", spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
        b = synthetic_fighter(f"Move audit {spec['id']} B", spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
        original = self.engine.update_move_sequence
        seen = []
        def observe(state, event, **kwargs):
            self.assertTrue(kwargs.get('independent_alternatives'))
            original(state, event, **kwargs)
            chain = state['move_chains'].get(event['actor'], {})
            if len(chain.get('branch_options', [])) > 1:
                seen.append((chain['next_move_id'], chain['branch_reason']))
        with candidate_context(entries=True, chains=True, draft_content=True), \
             patch.object(self.engine, 'update_move_sequence', side_effect=observe):
            run_audited_fight(self.engine, a, b, 9310000, spec['fight'])
        self.assertTrue(seen)
        self.assertTrue(all(row == ('', 'legal-alternatives') for row in seen))


if __name__ == "__main__":
    unittest.main()
