"""Audit-only boxing continuation demand bounded by the current named pool."""
from contextlib import contextmanager
import random
from unittest.mock import patch
import zlib

from fight_engine import COUNTER_TAG, FINISHER_TAG, STYLE_FINISHER_TAG, STYLE_COMBINATION_TAG
from fight_engine_audit import FightAuditHarness
from fight_moves.chains import sequence_role_allows
from fight_moves.selection_pool import ordinary_selection_pool


def boxing_pool(engine, fighter, opponent, state, action):
    """Pure pre-resolution pool; not a guarantee of post-resolution eligibility.

    Only jab/power-punch targets are deterministic at this point. Reuse the
    selector's arithmetic, gates and bounded pool; never select/resolve a move.
    Caller supplies a live chain verified by the ordinary opportunity preview.
    """
    if action not in {'jab', 'power_punch'}:
        raise ValueError('Only deterministic boxing targets are supported')
    identity = str(getattr(fighter, 'fighter_id', '') or fighter.name)
    material = f"{identity}|{state['round']}|{state['tick']}|{action}|punch-target"
    body = zlib.crc32(material.encode()) % 10000 / 10000 < engine.punch_target_shares(fighter, state)['body']
    target, position = 'body' if body else 'head', state['position']
    candidates, styles, identity, actor, counter = engine._move_candidates(fighter, action, position, target, state)
    chain = (state.get('move_chains') or {}).get(actor) or {}
    options = set(chain.get('branch_options') or (chain.get('next_move_id'),))
    chain_ids = {d.move_id for d in candidates if d.move_id in options and
                 sequence_role_allows(d.parent_action, position, actor, state.get('top'), state.get('bottom'))}
    signatures = set(getattr(fighter, 'signature_moves', []) or [])
    finishers = {d.move_id for d in candidates if d.move_id in signatures and
                 set(d.tags).intersection({FINISHER_TAG, STYLE_FINISHER_TAG})}
    boxing = {key: engine.ds(fighter, key, fallback) for key, fallback in (
        ('combination_punching', fighter.striking), ('body_punching', fighter.striking),
        ('counter_timing', fighter.fight_iq))}
    context = engine._move_context_inputs(fighter, opponent, state, actor, styles)
    rows = []
    for definition in candidates:
        static = engine._move_static_score(fighter, definition, styles, boxing, signatures, finishers)
        if static is None:
            continue
        proficiency, style, signature, mastery, tags = static
        bonus, _ = engine._move_contextual_score(fighter, opponent, definition, state, actor,
            styles, counter, chain, chain_ids, context=context, definition_tags=tags)
        material = f"{identity}|{state['round']}|{state['tick']}|{action}|{position}|{target}|{definition.move_id}"
        fingerprint = zlib.crc32(material.encode())
        if engine._move_rarity_gate(fighter, tags, fingerprint, identity, action, position, target, state):
            value = proficiency + style + signature + mastery + bonus + fingerprint % 901 / 100
            if value > -10000:
                rows.append((value, definition))
    rows.sort(key=lambda row: (-row[0], row[1].move_id))
    if counter:
        counters = [row for row in rows if COUNTER_TAG in row[1].tags]
        rows = counters or rows
    if not rows:
        return frozenset(), frozenset(chain_ids)
    top = rows[0][1]
    if top.move_id in signatures or set(top.tags).intersection({STYLE_COMBINATION_TAG, STYLE_FINISHER_TAG}):
        pool = rows[:1]
    else:
        pool, _ = ordinary_selection_pool(rows, chain_ids, chain, expanded=True)
    return frozenset(d.move_id for _, d in pool), frozenset(chain_ids)


@contextmanager
def boxing_chain_pool_trial(enabled=False):
    """Filter action demand only. Initiative, named choice and caps stay unchanged."""
    original, rng = FightAuditHarness._chain_action_weights, random.getstate()

    def adjusted(engine, fighter, opponent, state, weights, round_no, tick):
        if not getattr(engine, '_experimental_chain_action_weighting', False):
            return original(engine, fighter, opponent, state, weights, round_no, tick)
        preview = engine._chain_action_bonuses

        def filtered(*args, **kwargs):
            bonuses = dict(preview(*args, **kwargs))
            actor = engine.fight_state_key(fighter, state)
            snapshot = dict(state, round=round_no, tick=tick,
                last_exchange_counter=(state.get('counter_window') or {}).get('fighter') == actor)
            for action in ('jab', 'power_punch'):
                if bonuses.get(action, 0) > 0:
                    pool, successors = boxing_pool(engine, fighter, opponent, snapshot, action)
                    if not pool.intersection(successors):
                        bonuses.pop(action)
            return bonuses

        with patch.object(engine, '_chain_action_bonuses', filtered):
            return original(engine, fighter, opponent, state, weights, round_no, tick)

    adjusted._boxing_chain_pool_trial = True
    try:
        if enabled and not getattr(original, '_boxing_chain_pool_trial', False):
            with patch.object(FightAuditHarness, '_chain_action_weights', adjusted):
                yield
        else:
            yield
    finally:
        random.setstate(rng)
