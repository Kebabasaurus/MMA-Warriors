"""User-approved audit-only action-continuation strength; never production policy."""
from contextlib import contextmanager
import random
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness

CONTINUATION_MULTIPLIER = 2.0


@contextmanager
def continuation_strength_trial(enabled=False):
    """Scale the legal preview only during action-ticket apportionment.

    The existing skill/gas curve remains authoritative (+2 becomes at most +4).
    Initiative calls the unscaled preview. Prepared intent still combines by max
    in the original apportioner, preserving its ticket budget and legal options.
    Single-threaded disposable audits only; nested contexts do not stack.
    """
    original, rng = FightAuditHarness._chain_action_weights, random.getstate()

    def adjusted(engine, fighter, opponent, state, weights, round_no, tick):
        if not getattr(engine, '_experimental_chain_action_weighting', False):
            return original(engine, fighter, opponent, state, weights, round_no, tick)
        preview = engine._chain_action_bonuses

        def scaled(*args, **kwargs):
            return {key: value * CONTINUATION_MULTIPLIER
                    for key, value in preview(*args, **kwargs).items()}

        with patch.object(engine, '_chain_action_bonuses', scaled):
            return original(engine, fighter, opponent, state, weights, round_no, tick)

    adjusted._stronger_continuation_trial = True
    try:
        if enabled and not getattr(original, '_stronger_continuation_trial', False):
            with patch.object(FightAuditHarness, '_chain_action_weights', adjusted):
                yield
        else:
            yield
    finally:
        random.setstate(rng)
