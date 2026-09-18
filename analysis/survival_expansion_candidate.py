"""Opt-in survival catalogue with ownership-filtered existing selection pools."""
from contextlib import contextmanager
from collections import Counter
import random
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness
from fight_moves.catalogue.survival_development import SURVIVAL_DEVELOPMENT, SURVIVAL_ROLES


LEGACY_ROLES = {'bottom_frame_survival': 'bottom', 'hip_frame_ground_breather': 'bottom',
                'heavy_top_breather': 'top'}
PHYSICAL_GROUND = frozenset({'guard','half guard','side control','mount','back control','turtle','front headlock'})


def role_allows(move_id, position, actor_key, state):
    role = SURVIVAL_ROLES.get(move_id, LEGACY_ROLES.get(move_id, 'any'))
    if move_id in LEGACY_ROLES and position not in PHYSICAL_GROUND:
        return False
    if role == 'any':
        return True
    if actor_key not in {'a','b'}:
        return False
    if role in {'top','bottom'}:
        return (state.get(role) == actor_key and state.get('top') in {'a','b'}
                and state.get('bottom') in {'a','b'} and state.get('top') != state.get('bottom'))
    controller = state.get('clinch_controller')
    if role == 'controller':
        return controller == actor_key
    if role == 'controlled':
        return controller in {'a','b'} and controller != actor_key
    raise ValueError(f'Unknown survival role: {role}')


def expanded_definitions(definitions):
    result = list(definitions)
    by_id = {move.move_id: move for move in definitions}
    for move in SURVIVAL_DEVELOPMENT:
        if move.move_id in by_id:
            if by_id[move.move_id] != move:
                raise ValueError('Conflicting survival identity: ' + move.move_id)
        else:
            result.append(move)
    return tuple(result)


def validate_survival_trace(trace):
    definitions = {move.move_id: move for move in SURVIVAL_DEVELOPMENT}
    counts = Counter()
    for event in trace:
        move = definitions.get(event.get('move_id'))
        if move is None:
            continue
        position, actor = event.get('position_before'), event.get('actor')
        ownership = {key:event.get(key+'_before') for key in ('top','bottom','clinch_controller')}
        ownership['clinch_controller'] = event.get('clinch_before')
        valid = (event.get('type') == 'exchange' and event.get('action') == 'survive'
                 and position in move.positions and role_allows(move.move_id,position,actor,ownership))
        counts['selected'] += 1
        counts['invalid'] += not valid
    return dict(counts)


@contextmanager
def survival_expansion_trial(enabled=False):
    original, rng = FightAuditHarness._move_candidates, random.getstate()
    active = getattr(FightAuditHarness,'_survival_expansion_enabled',False)
    if active and not enabled:
        raise ValueError('Cannot disable nested survival expansion')

    def filtered(engine, actor, action, position, target, state):
        candidates, styles, identity, actor_key, counter = original(engine,actor,action,position,target,state)
        if action == 'survive':
            candidates = [move for move in candidates if role_allows(move.move_id,position,actor_key,state)]
        return candidates,styles,identity,actor_key,counter

    filtered._survival_expansion_trial = True
    try:
        if enabled and not active:
            with patch.object(FightAuditHarness,'_move_candidates',filtered), \
                 patch.object(FightAuditHarness,'_survival_expansion_enabled',True,create=True):
                yield
        else:
            yield
    finally:
        random.setstate(rng)
