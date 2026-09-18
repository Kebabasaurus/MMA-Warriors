"""A corner break ends actor streaks, not the ordinary in-round comeback rule."""
import random
import unittest
from unittest.mock import patch

from analysis.fight_candidate_context import candidate_context
from fight_engine_audit import FightAuditHarness, run_audited_fight, synthetic_fighter


class RoundStreakResetTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(random.setstate, random.getstate())
        self.engine = FightAuditHarness()
        self.a = synthetic_fighter("Streak Red", 75, "Boxer", "Pressure", 0)
        self.b = synthetic_fighter("Streak Blue", 75, "Boxer", "Pressure", 1)

    def test_both_actual_initiative_calls_observe_candidate_horn_reset(self):
        seen = []
        original = self.engine.initiative

        def observe(fighter, opponent, state):
            if state["tick"] == 1:
                seen.append((state["round"], self.engine.fight_state_key(fighter, state),
                             state["last_actor"], state["actor_streak"]))
            return original(fighter, opponent, state)

        # Survival keeps the bout free of attack finishes so the lifecycle
        # assertion cannot disappear when an unrelated attack is recalibrated.
        for entries in (False, True):
            seen.clear()
            with candidate_context(entries=entries, chains=True, draft_content=True), \
                 patch.object(self.engine, "initiative", side_effect=observe), \
                 patch.object(self.engine, "choose_action", return_value="survive"):
                run_audited_fight(self.engine, self.a, self.b, 7229, {})
            later = [row for row in seen if row[0] > 1]
            self.assertGreaterEqual(len(later), 2)
            for round_no in {row[0] for row in later}:
                self.assertEqual([row[1] for row in later if row[0] == round_no], ["a", "b"])
            self.assertTrue(all(row[2:] == (None, 0) for row in later), later)

    def test_same_round_streak_and_comeback_intervention_are_retained(self):
        chosen = []
        initiative_state = []
        original_rng = self.engine.fight_mechanics_rng

        class ComebackRng:
            def randint(self, lower, upper):
                if (lower, upper) == (-8, 18):
                    return 18
                return original_rng().randint(lower, upper)

            def random(self):
                return 0.0

            def __getattr__(self, name):
                return getattr(original_rng(), name)

        def initiative(fighter, opponent, state):
            initiative_state.append((state["round"], state["tick"], state["actor_streak"]))
            return 100 if fighter is self.a else 99

        def choose(fighter, opponent, state, round_no, tick):
            chosen.append((round_no, tick, self.engine.fight_state_key(fighter, state), state["actor_streak"]))
            return "survive"

        # Exercise the actual comeback branch with a favorable contest/draw.
        # This short forced-survival fixture tests lifecycle, not calibration.
        class StopAfterThree(Exception):
            pass

        def bounded_initiative(fighter, opponent, state):
            if state["tick"] > 3:
                raise StopAfterThree()
            return initiative(fighter, opponent, state)

        with candidate_context(entries=True, chains=True, draft_content=True), \
             patch.object(self.engine, "initiative", side_effect=bounded_initiative), \
             patch.object(self.engine, "choose_action", side_effect=choose), \
             patch.object(self.engine, "fight_mechanics_rng", return_value=ComebackRng()):
            with self.assertRaises(StopAfterThree):
                self.engine.simulate_fight(self.a, self.b, {})
        self.assertEqual(chosen, [(1, 1, "a", 1), (1, 2, "a", 2), (1, 3, "b", 1)])
        self.assertEqual([row[2] for row in initiative_state], [0, 0, 1, 1, 2, 2])

    def test_default_off_whole_bout_matches_explicit_legacy_boundary(self):
        # Model the former boundary by restoring the immediately preceding
        # chosen actor/streak before the next round's initiative. With the
        # experimental flags off this must be an exact no-op, not just produce
        # the same winner. Compare the complete audited result and final RNG.
        control = run_audited_fight(self.engine, self.a, self.b, 7229, {})
        control_rng = random.getstate()
        original_initiative = self.engine.initiative
        original_choose = self.engine.choose_action
        previous = {}
        restored = []

        def choose(fighter, opponent, state, round_no, tick):
            previous.update(round=round_no, actor=state["last_actor"], streak=state["actor_streak"])
            return original_choose(fighter, opponent, state, round_no, tick)

        def legacy_initiative(fighter, opponent, state):
            if state["tick"] == 1 and previous.get("round", 0) < state["round"] and previous:
                restored.append((state["last_actor"], state["actor_streak"], previous["actor"], previous["streak"]))
                state["last_actor"], state["actor_streak"] = previous["actor"], previous["streak"]
            return original_initiative(fighter, opponent, state)

        self.engine._experimental_specialist_entries = False
        self.engine._experimental_chain_action_weighting = False
        with patch.object(self.engine, "initiative", side_effect=legacy_initiative), \
             patch.object(self.engine, "choose_action", side_effect=choose):
            observed = run_audited_fight(self.engine, self.a, self.b, 7229, {})
        self.assertGreater(len(restored), 0)
        self.assertTrue(all(row[:2] == row[2:] for row in restored), restored)
        self.assertEqual(observed, control)
        self.assertEqual(random.getstate(), control_rng)


if __name__ == "__main__":
    unittest.main()
