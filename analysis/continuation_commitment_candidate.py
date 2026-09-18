"""Audit-only probability-bounded commitment, using the existing single apportioner."""
from contextlib import contextmanager
import random
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness


def committed_bonuses(weights, bonuses, ready=True):
    """Mix at most half of action demand toward preview-supported actions.

    q = strongest existing skill/gas/target-weighted bonus / 4, capped at 0.5.
    The equivalent bonus rescaling lets the ordinary apportioner run once and
    combine prepared intent by maximum. No absent action or zero preview gains
    support. This is a mechanical trial, not a final-legality guarantee.
    """
    positive = {key: value for key, value in bonuses.items() if key in weights and value > 0}
    if not ready or not positive:
        return dict(bonuses)
    cleaned = {key: max(1, int(value)) for key, value in weights.items()}
    mass = sum(cleaned[key] * value for key, value in positive.items())
    q = min(0.5, max(positive.values()) / 4)
    scale = 1 + q * (sum(cleaned.values()) + mass) / ((1 - q) * mass)
    return {key: value * scale if key in positive else value for key, value in bonuses.items()}


@contextmanager
def continuation_commitment_trial(enabled=False):
    original, rng = FightAuditHarness._chain_action_weights, random.getstate()

    def adjusted(engine, fighter, opponent, state, weights, round_no, tick):
        if not getattr(engine, '_experimental_chain_action_weighting', False):
            return original(engine, fighter, opponent, state, weights, round_no, tick)
        slot = engine.fight_state_key(fighter, state)
        ready = (state.get('gas', {}).get(slot, 0) >= 42
                 and state.get('hurt', {}).get(slot, 0) <= fighter.toughness * 0.65)
        preview = engine._chain_action_bonuses

        def committed(*args, **kwargs):
            return committed_bonuses(weights, preview(*args, **kwargs), ready)

        with patch.object(engine, '_chain_action_bonuses', committed):
            return original(engine, fighter, opponent, state, weights, round_no, tick)

    adjusted._continuation_commitment_trial = True
    try:
        if enabled and not getattr(original, '_continuation_commitment_trial', False):
            with patch.object(FightAuditHarness, '_chain_action_weights', adjusted):
                yield
        else:
            yield
    finally:
        random.setstate(rng)
