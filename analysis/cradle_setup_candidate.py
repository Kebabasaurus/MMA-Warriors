"""Disposable, default-off contested cradle preparation; no production patches."""
from contextlib import ExitStack, contextmanager
from copy import deepcopy
import random
import math
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness
import fight_engine
from fight_moves.submission_identity import COMPATIBLE_SUBMISSION_IDS

HOLD = ('cradle neck crank', False)
MOVE_ID = 'catch_cradle_neck_crank_finisher'
KEY = 'cradle_setup'
FACT = 'last_cradle_setup_event'
_active = False


def valid_cradle_setup(engine, actor, action, state):
    setup = state.get(KEY) or {}
    return (all(type(value) is int and value > 0 for value in
                (setup.get('round'), setup.get('created_tick'), state.get('round'), state.get('tick')))
            and engine._valid_submission_setup(actor, action, state, KEY, 'side control'))


def _cancel(state, reason):
    setup = state.pop(KEY, None)
    if setup:
        state[FACT] = dict(setup, status='cancelled', reason=reason,
                           event_round=state.get('round'), event_tick=state.get('tick'))


def validate_cradle_setups(trace):
    """Independent adjacent-exchange provenance, including missing-fact detection."""
    counts = dict(roots=0, used=0, named=0, invalid=0)
    pending = None
    source_keys = ('top', 'bottom', 'position', 'round', 'created_tick',
                   'raw_margin', 'skill_edge', 'adjusted_margin')
    for event in trace:
        if event.get('type') != 'exchange':
            pending = None
            continue
        fact = event.get(KEY) or {}
        technique = event.get('submission_technique') or {}
        if not isinstance(technique, dict):
            counts['invalid'] += 1
            pending = None
            continue
        named = event.get('move_id') == MOVE_ID
        hold = technique == dict(name=HOLD[0], choke=False)
        if not fact:
            if named or technique.get('name') == HOLD[0]:
                counts['invalid'] += 1
            pending = None
            continue
        if not isinstance(fact, dict):
            counts['invalid'] += 1
            pending = None
            continue
        status = fact.get('status')
        coords = (all(type(fact.get(k)) is int and fact[k] > 0 for k in
                      ('round', 'created_tick', 'event_round', 'event_tick'))
                  and fact.get('event_round') == event.get('round')
                  and fact.get('event_tick') == event.get('tick'))
        finite = all(type(fact.get(k)) in (int, float) and math.isfinite(fact[k])
                     for k in ('raw_margin', 'skill_edge', 'adjusted_margin'))
        margins = finite and math.isclose(fact['adjusted_margin'], fact['raw_margin'] + .2 * fact['skill_edge'], abs_tol=1e-9)
        owners = (fact.get('top') in ('a', 'b') and fact.get('bottom') == ('b' if fact.get('top') == 'a' else 'a')
                  and fact.get('position') == event.get('position_before') == 'side control'
                  and fact.get('top') == event.get('top_before') and fact.get('bottom') == event.get('bottom_before'))
        current_root = fact.get('created_tick') == event.get('tick') and fact.get('round') == event.get('round')
        move = event.get('move') or {}
        generic = (event.get('move_id') == 'generic_ground_control' and move.get('generic') is True
                   and not any(event.get(k) or move.get(k) for k in
                               ('signature', 'move_mastery', 'sequence_source_id', 'sequence_step')))
        valid = coords and margins
        if status in ('created', 'denied') or (status == 'cancelled' and current_root):
            valid = (valid and owners and current_root and generic and not technique
                     and event.get('actor') == fact.get('top') and event.get('action') == 'ground_control'
                     and event.get('sub_att_delta') == 0
                     and event.get('sig_att_delta') == 0 and event.get('td_att_delta') == 0
                     and (event.get('round_metric_delta') or {}).get(fact.get('top')) == dict(control=3, danger=0, impact=0)
                     and ((fact['adjusted_margin'] > 8) if status != 'denied' else (fact['adjusted_margin'] <= 8)))
            if status == 'created':
                valid = valid and all(event.get(k + '_after') == fact.get(k) for k in ('position', 'top', 'bottom'))
                counts['roots'] += int(valid)
            if status == 'cancelled':
                valid = valid and fact.get('reason') == 'referee_standup' and (event.get('referee_ground_action') or {}).get('type') == 'standup'
        elif status in ('used', 'consumed'):
            valid = (valid and owners and pending is not None
                     and all(fact.get(k) == pending.get(k) for k in source_keys)
                     and fact.get('round') == event.get('round') and event.get('tick') == fact.get('created_tick') + 1
                     and event.get('actor') == fact.get('top') and event.get('action') == 'submission'
                     and event.get('sub_att_delta') == 1 and fact.get('technique') == technique
                     and (hold if status == 'used' else bool(technique) and not hold))
            counts['used'] += int(valid and status == 'used')
            counts['named'] += int(valid and status == 'used' and named)
        elif status == 'cancelled':
            valid = valid and pending is not None and all(fact.get(k) == pending.get(k) for k in source_keys) and bool(fact.get('reason'))
        else:
            valid = False
        if named and (status != 'used' or not hold):
            valid = False
        counts['invalid'] += int(not valid)
        pending = fact if valid and status == 'created' else None
    return counts


@contextmanager
def cradle_setup_trial(enabled=False):
    """Single-threaded audit scope; nested scopes agree and never stack.

    Engines additionally require _experimental_specialist_entries. A Catch
    Wrestler's ride intent uses the existing ground-control contest and award.
    One additional hold ticket is appended after duplicate-variant adaptation.
    """
    global _active
    if _active:
        if not enabled:
            raise ValueError('disabled cradle scope inside enabled trial')
        nested_rng = random.getstate()
        try:
            yield
        finally:
            random.setstate(nested_rng)
        return
    if not enabled:
        yield
        return
    rng = random.getstate()
    names = ('_resolve_exchange_action', 'resolve_exchange',
             'submission_technique_tickets', 'submission_technique',
             'select_exchange_move', '_move_candidates', 'record_fight_trace_exchange',
             'set_fight_position', 'recover_between_rounds', 'finalize_fight_result', 'initiative',
             'update_ground_inactivity', 'check_fight_stoppage')
    original = {name: getattr(FightAuditHarness, name) for name in names}

    def action(engine, actor, defender, action, state, stats):
        eligible = (getattr(engine, '_experimental_specialist_entries', False)
                    and action == 'ground_control' and state.get('position') == 'side control'
                    and state.get('top') == engine.fight_state_key(actor, state)
                    and state.get('bottom') == engine.fight_state_key(defender, state)
                    and 'Catch Wrestler' in engine.fighter_styles(actor)
                    and engine._side_control_intent(actor, state) == 'ride_pin'
                    and not engine._valid_von_flue_pending(actor, action, state))
        if not eligible:
            return original['_resolve_exchange_action'](engine, actor, defender, action, state, stats)
        attack = engine.action_attack_value(actor, action, state)
        defence = engine.action_defence_value(defender, action, state)
        margin = attack - defence + engine.fight_mechanics_rng().randint(-18, 18)
        edge = (engine.ds_avg(actor, ('ride_control', 'positional_ability', 'strength'), actor.ground_control)
                - engine.ds_avg(defender, ('bottom_control', 'scrambles', 'flexibility'), defender.grappling))
        adjusted = margin + .2 * edge
        setup = dict(top=state['top'], bottom=state['bottom'], position='side control',
                     round=state['round'], created_tick=state['tick'],
                     raw_margin=margin, skill_edge=edge, adjusted_margin=adjusted)
        stats[state['top']]['control'] += 3
        state[FACT] = dict(setup, status='created' if adjusted > 8 else 'denied',
                           event_round=state['round'], event_tick=state['tick'])
        if adjusted > 8:
            state[KEY] = setup
            return f'{actor.name} secures a cradle and isolates the neck without applying a submission yet.'
        return f'{defender.name} frames against the cradle attempt while {actor.name} retains side control.'

    def exchange(engine, actor, defender, action, state, stats):
        state.pop(FACT, None)
        if not valid_cradle_setup(engine, actor, action, state):
            _cancel(state, 'next_action_or_context_changed')
        result = original['resolve_exchange'](engine, actor, defender, action, state, stats)
        setup = state.get(KEY)
        if setup and any(state.get(k) != setup.get(k) for k in ('position', 'top', 'bottom', 'round')):
            _cancel(state, 'context_changed')
        if any(state.get(k) for k in ('submission_finish', 'instant_finish', 'technical_outcome', 'technical_foul_stoppage')):
            _cancel(state, 'finish')
        return result

    def tickets(engine, actor, action, state):
        result = original['submission_technique_tickets'](engine, actor, action, state)
        move = fight_engine.MOVE_REGISTRY.get(MOVE_ID)
        eligible = (move is not None and not move.deprecated and move.parent_action == action
                    and state.get('position') in move.positions and 'Catch Wrestler' in engine.fighter_styles(actor)
                    and sum(engine.ds(actor, skill, 50) for skill in move.attack_skills) / len(move.attack_skills) >= move.minimum_skill)
        return list(result) + [HOLD] if eligible and valid_cradle_setup(engine, actor, action, state) else result

    def technique(engine, actor, action, state):
        valid = valid_cradle_setup(engine, actor, action, state)
        state.pop(FACT, None)
        result = original['submission_technique'](engine, actor, action, state)
        setup = state.pop(KEY, None)
        if setup:
            state[FACT] = dict(setup, status='used' if valid and result == dict(name=HOLD[0], choke=HOLD[1]) else 'consumed',
                               event_round=state.get('round'), event_tick=state.get('tick'),
                               technique=deepcopy(result))
        return result

    def candidates(engine, actor, action, position, target, state):
        rows, *rest = original['_move_candidates'](engine, actor, action, position, target, state)
        fact = state.get(FACT) or {}
        proven = (fact.get('status') == 'used' and fact.get('event_round') == state.get('round')
                  and fact.get('event_tick') == state.get('tick') and fact.get('top') == engine.fight_state_key(actor, state)
                  and fact.get('technique') == dict(name=HOLD[0], choke=False))
        return ([row for row in rows if row.move_id != MOVE_ID or proven], *rest)

    def select(engine, actor, defender, action, position, target, state, ownership_before=None, resolved_technique=None):
        fact = state.get(FACT) or {}
        if (action == 'ground_control' and fact.get('event_round') == state.get('round')
                and fact.get('event_tick') == state.get('tick') and fact.get('status') in {'created', 'denied', 'cancelled'}):
            return engine._move_payload(None, actor, defender, action, target, state,
                                        engine.fight_state_key(actor, state), engine.fighter_styles(actor), False, {}, (), ())
        return original['select_exchange_move'](engine, actor, defender, action, position, target, state,
                                                ownership_before, resolved_technique)

    def record(engine, a, b, actor, defender, action, result, before, round_before, state, stats):
        event = original['record_fight_trace_exchange'](engine, a, b, actor, defender, action, result, before, round_before, state, stats)
        if state.get(FACT):
            event[KEY] = deepcopy(state[FACT])
        return event

    def position(engine, state, position, **kwargs):
        _cancel(state, 'position_reset')
        return original['set_fight_position'](engine, state, position, **kwargs)

    def recover(engine, a, b, state):
        _cancel(state, 'horn')
        return original['recover_between_rounds'](engine, a, b, state)

    def finalize(engine, a, b, winner, loser, method, round_no, lines, state):
        _cancel(state, 'finish')
        return original['finalize_fight_result'](engine, a, b, winner, loser, method, round_no, lines, state)

    def initiative(engine, fighter, opponent, state):
        setup = state.get(KEY)
        if setup and state.get('round') != setup.get('round'):
            _cancel(state, 'round_boundary')
        return original['initiative'](engine, fighter, opponent, state)

    def inactivity(engine, state, action):
        result = original['update_ground_inactivity'](engine, state, action)
        setup = state.get(KEY)
        if setup and any(state.get(k) != setup.get(k) for k in ('position', 'top', 'bottom')):
            _cancel(state, 'referee_standup')
            payload = state.get('last_move_payload')
            if payload and action == 'ground_control':
                # Setup identity was generic when selected; a reset must retain it.
                payload.update(move_id='generic_ground_control', name='ground control', generic=True,
                               signature=False, move_mastery=0, sequence_source_id='', sequence_step=0)
                payload.pop('sequence_occurrence_id', None)
        return result

    def stoppage(engine, actor, defender, state):
        result = original['check_fight_stoppage'](engine, actor, defender, state)
        if result:
            _cancel(state, 'finish')
        return result

    replacements = (action, exchange, tickets, technique, select, candidates, record, position, recover, finalize, initiative,
                    inactivity, stoppage)
    try:
        with ExitStack() as stack:
            for name, replacement in zip(names, replacements):
                stack.enter_context(patch.object(FightAuditHarness, name, replacement))
            stack.enter_context(patch.dict(COMPATIBLE_SUBMISSION_IDS, {HOLD[0]: (MOVE_ID,)}))
            _active = True
            yield
    finally:
        _active = False
        random.setstate(rng)
