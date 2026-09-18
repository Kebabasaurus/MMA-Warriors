"""Opt-in named chains from two real, immediately consecutive held submissions."""
from contextlib import contextmanager, ExitStack
from copy import deepcopy
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness
from fight_moves.submission_transition import transition_identity

PENDING = '_hold_transition_root'


def geometry(state):
    return tuple(state.get(key) for key in ('position', 'top', 'bottom'))


@contextmanager
def submission_chain_trial(enabled=False):
    active = getattr(FightAuditHarness, '_submission_chain_trial', False)
    if active:
        if not enabled:
            raise ValueError('Cannot disable submission chains inside a nested trial')
        yield
        return
    if not enabled:
        yield
        return
    original = {name: getattr(FightAuditHarness, name) for name in
                ('resolve_exchange', 'select_exchange_move', 'record_fight_trace_exchange',
                 'recover_between_rounds', 'finalize_fight_result', 'set_fight_position', 'update_ground_inactivity')}

    def resolve(self, actor, defender, action, state, stats):
        root = state.pop(PENDING, None)
        state.pop('last_hold_transition', None)
        slot = self.fight_state_key(actor, state)
        before = geometry(state)
        danger_before = stats[slot].get('danger', 0)
        result = original['resolve_exchange'](self, actor, defender, action, state, stats)
        hold = state.get('last_submission_technique') or {}
        if action not in {'submission', 'bottom_submission'} or not hold:
            return result
        kind = ('guard' if action == 'bottom_submission' and before[0] == 'guard' and slot == before[2]
                else 'top' if action == 'submission' and before[0] in {'mount', 'side control'}
                and slot == before[1] else None)
        settled = geometry(state) == before and not state.get('last_neutral_scramble_reset')
        held = stats[slot].get('danger', 0) - danger_before >= 14
        if (kind and held and settled and root and root['actor'] == slot and root['kind'] == kind
                and root['round'] == state.get('round') and root['tick'] + 1 == state.get('tick')
                and (root['position'], root['top'], root['bottom']) == before):
            fact = dict(root, root_tick=root['tick'], tick=state['tick'],
                        **{'from': root['hold'], 'to': hold['name'].casefold()})
            evidence = dict(hold, transition=fact)
            if transition_identity(evidence):
                state['last_submission_technique'] = evidence
                state['last_hold_transition'] = fact
        # A safely defended or grip-cleared hold is not retained pressure.
        if (kind and settled and not state.get('submission_finish') and not state.get('instant_finish')
                and (state.get('last_submission_escape') or {}).get('consequence') == 'late defense; position retained'):
            state[PENDING] = dict(actor=slot, kind=kind, round=state['round'], tick=state['tick'],
                                  position=before[0], top=before[1], bottom=before[2], hold=hold['name'].casefold())
        return result

    def select(self, actor, defender, action, position, target, state, ownership_before=None, resolved_technique=None):
        payload = original['select_exchange_move'](self, actor, defender, action, position, target, state,
                                                  ownership_before=ownership_before, resolved_technique=resolved_technique)
        fact = (resolved_technique or {}).get('transition')
        if payload['move_id'] in {'top_submission_chain', 'guard_submission_chain'} and fact:
            payload['name'] = f"{fact['from']} to {fact['to']}"
        return payload

    def record(self, a, b, actor, defender, action, text, before, prior, state, stats):
        event = original['record_fight_trace_exchange'](self, a, b, actor, defender, action, text, before, prior, state, stats)
        if state.get('last_hold_transition'):
            event['hold_transition'] = deepcopy(state['last_hold_transition'])
        if state.get(PENDING):
            event['hold_transition_root'] = deepcopy(state[PENDING])
        return event

    def position(self, state, *args, **kwargs):
        before = geometry(state)
        result = original['set_fight_position'](self, state, *args, **kwargs)
        if before != geometry(state):
            state.pop(PENDING, None)
        return result

    def recover(self, a, b, state):
        state.pop(PENDING, None)
        state.pop('last_hold_transition', None)
        return original['recover_between_rounds'](self, a, b, state)

    def inactivity(self, state, action):
        result = original['update_ground_inactivity'](self, state, action)
        if (state.get('last_referee_ground_action') or {}).get('type') == 'standup':
            state.pop(PENDING, None)
        return result

    def finish(self, a, b, winner, loser, method, round_no, lines, state):
        state.pop(PENDING, None)
        return original['finalize_fight_result'](self, a, b, winner, loser, method, round_no, lines, state)

    with ExitStack() as stack:
        stack.enter_context(patch.object(FightAuditHarness, '_submission_chain_trial', True, create=True))
        for name, function in (('resolve_exchange', resolve), ('select_exchange_move', select),
                               ('record_fight_trace_exchange', record), ('set_fight_position', position),
                               ('update_ground_inactivity', inactivity),
                               ('recover_between_rounds', recover), ('finalize_fight_result', finish)):
            stack.enter_context(patch.object(FightAuditHarness, name, function))
        yield


def validate_hold_transitions(trace):
    """Reconcile every claimed transition against the immediately preceding root."""
    errors, roots, used, named = [], 0, 0, 0
    previous = None
    for event in trace:
        root = event.get('hold_transition_root')
        roots += bool(root)
        fact = event.get('hold_transition')
        identity = transition_identity(event.get('submission_technique'))
        chain = event.get('move_id') in {'top_submission_chain', 'guard_submission_chain'}
        evidence = (event.get('submission_technique') or {}).get('transition')
        if evidence != fact:
            errors.append('Transition evidence copies disagree')
        def matches_geometry(data):
            return (data.get('kind') in {'guard', 'top'}
                    and event.get('sub_att_delta') == 1
                    and (event.get('round_metric_delta') or {}).get(event.get('actor'), {}).get('danger', 0) >= 14
                    and event.get('action') == ('bottom_submission' if data.get('kind') == 'guard' else 'submission')
                    and data.get('actor') == data.get('bottom' if data.get('kind') == 'guard' else 'top')
                    and event.get('position_after') == data.get('position')
                    and event.get('top_before') == data.get('top') and event.get('bottom_before') == data.get('bottom')
                    and event.get('top_after') == data.get('top') and event.get('bottom_after') == data.get('bottom'))
        if root and (event.get('actor') != root.get('actor') or event.get('round') != root.get('round')
                     or event.get('tick') != root.get('tick')
                     or (event.get('submission_technique') or {}).get('name', '').casefold() != root.get('hold')
                     or (event.get('submission_escape') or {}).get('consequence') != 'late defense; position retained'
                     or event.get('position_before') != root.get('position')
                     or event.get('position_after') != root.get('position')
                     or not matches_geometry(root)):
            errors.append('Unproved retained submission root')
        if fact:
            used += 1
            prior = (previous or {}).get('hold_transition_root')
            if (not identity or not prior or not matches_geometry(fact) or fact.get('root_tick') != prior.get('tick')
                    or any(fact.get(key) != prior.get(key) for key in
                           ('actor', 'kind', 'round', 'position', 'top', 'bottom'))
                    or fact.get('from') != prior.get('hold')
                    or event.get('actor') != fact.get('actor')
                    or event.get('round') != fact.get('round') or event.get('tick') != fact.get('tick')
                    or event.get('position_before') != fact.get('position')):
                errors.append('Unproved consecutive submission transition')
        if chain:
            named += 1
            if not fact or identity != event['move_id']:
                errors.append('Submission-chain identity lacks transition evidence')
        previous = event
    return dict(roots=roots, transitions=used, named=named, invalid=len(errors))
