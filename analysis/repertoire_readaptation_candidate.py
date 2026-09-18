"""Audit-only earlier repertoire adaptation without penalizing live follow-ups."""
from contextlib import contextmanager
import random
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness


@contextmanager
def repertoire_readaptation_trial(enabled=False, *, actions=None):
    """Apply one earlier exposure on independent choices, keeping the 14-point cap.

    No new score coefficient or eligibility gate. A live eligible continuation
    retains the original repetition penalty and its existing sequence bonus.
    Optional action filtering isolates a mechanical slice. Identical nested scopes
    do not stack; conflicting enabled scopes fail instead of silently inheriting.
    """
    original, rng = FightAuditHarness._move_contextual_score, random.getstate()
    actions = None if actions is None else frozenset(actions)
    if enabled and getattr(original, '_repertoire_readaptation_trial', False):
        if original._repertoire_readaptation_actions != actions:
            raise ValueError('Conflicting nested repertoire action filters')

    def adapted(engine, actor, defender, definition, state, actor_key, styles,
                active_counter, active_chain, chain_candidates, context=None, definition_tags=None):
        if context is None:
            context = engine._move_context_inputs(actor, defender, state, actor_key, styles)
        score, reasons = original(engine, actor, defender, definition, state, actor_key, styles,
                                  active_counter, active_chain, chain_candidates,
                                  context=context, definition_tags=definition_tags)
        if (not getattr(engine, '_experimental_chain_action_weighting', False)
                or definition.move_id in chain_candidates
                or (actions is not None and definition.parent_action not in actions)):
            return score, reasons
        repeats = context['actor_reads'].get('moves', {}).get(definition.move_id, 0)
        if repeats < 1:
            return score, reasons
        unit = 2.6 + max(0, context['adaptability'] - 65) / 55
        previous = min(14.0, max(0, repeats - 1) * unit)
        earlier = min(14.0, repeats * unit)
        if earlier > previous:
            return score - (earlier - previous), (*reasons, 'earlier-repertoire-readaptation')
        return score, reasons

    adapted._repertoire_readaptation_trial = True
    adapted._repertoire_readaptation_actions = actions
    try:
        if enabled and not getattr(original, '_repertoire_readaptation_trial', False):
            with patch.object(FightAuditHarness, '_move_contextual_score', adapted):
                yield
        else:
            yield
    finally:
        random.setstate(rng)
