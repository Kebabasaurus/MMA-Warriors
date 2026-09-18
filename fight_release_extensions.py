"""Native retained submission mechanics; no audit contexts or runtime patching.

Compose ReleaseCradleMixin before ReleaseSubmissionChainMixin before the engine.
The private setup facts are exchange-local and never persisted as fighter data.
"""
from copy import deepcopy

from fight_moves.submission_transition import transition_identity

PENDING = '_hold_transition_root'
HOLD = ('cradle neck crank', False)
MOVE_ID = 'catch_cradle_neck_crank_finisher'
KEY = 'cradle_setup'
FACT = 'last_cradle_setup_event'


def geometry(state):
    return tuple(state.get(key) for key in ('position', 'top', 'bottom'))


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


class ReleaseSubmissionChainMixin:
    """Identity requires two actually dangerous, consecutive compatible holds."""
    _submission_chain_trial = True

    def resolve_exchange(self, actor, defender, action, state, stats):
        root = state.pop(PENDING, None)
        state.pop('last_hold_transition', None)
        slot = self.fight_state_key(actor, state)
        before = geometry(state)
        danger_before = stats[slot].get('danger', 0)
        result = super().resolve_exchange(actor, defender, action, state, stats)
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
        if (kind and settled and not state.get('submission_finish') and not state.get('instant_finish')
                and (state.get('last_submission_escape') or {}).get('consequence') == 'late defense; position retained'):
            state[PENDING] = dict(actor=slot, kind=kind, round=state['round'], tick=state['tick'],
                                  position=before[0], top=before[1], bottom=before[2], hold=hold['name'].casefold())
        return result

    def select_exchange_move(self, actor, defender, action, position, target, state,
                             ownership_before=None, resolved_technique=None):
        payload = super().select_exchange_move(actor, defender, action, position, target, state,
                                               ownership_before=ownership_before, resolved_technique=resolved_technique)
        fact = (resolved_technique or {}).get('transition')
        if payload['move_id'] in {'top_submission_chain', 'guard_submission_chain'} and fact:
            payload['name'] = f"{fact['from']} to {fact['to']}"
        return payload

    def record_fight_trace_exchange(self, a, b, actor, defender, action, text, before, prior, state, stats):
        event = super().record_fight_trace_exchange(a, b, actor, defender, action, text, before, prior, state, stats)
        if state.get('last_hold_transition'):
            event['hold_transition'] = deepcopy(state['last_hold_transition'])
        if state.get(PENDING):
            event['hold_transition_root'] = deepcopy(state[PENDING])
        return event

    def set_fight_position(self, state, *args, **kwargs):
        before = geometry(state)
        result = super().set_fight_position(state, *args, **kwargs)
        if before != geometry(state):
            state.pop(PENDING, None)
        return result

    def recover_between_rounds(self, a, b, state):
        state.pop(PENDING, None)
        state.pop('last_hold_transition', None)
        return super().recover_between_rounds(a, b, state)

    def update_ground_inactivity(self, state, action):
        result = super().update_ground_inactivity(state, action)
        if (state.get('last_referee_ground_action') or {}).get('type') == 'standup':
            state.pop(PENDING, None)
        return result

    def finalize_fight_result(self, a, b, winner, loser, method, round_no, lines, state):
        state.pop(PENDING, None)
        return super().finalize_fight_result(a, b, winner, loser, method, round_no, lines, state)


class ReleaseCradleMixin:
    """Contested Catch cradle setup followed by one eligible, single-use ticket."""
    _cradle_setup_trial = True

    def _resolve_exchange_action(self, actor, defender, action, state, stats):
        eligible = (getattr(self, '_experimental_specialist_entries', False)
                    and action == 'ground_control' and state.get('position') == 'side control'
                    and state.get('top') == self.fight_state_key(actor, state)
                    and state.get('bottom') == self.fight_state_key(defender, state)
                    and 'Catch Wrestler' in self.fighter_styles(actor)
                    and self._side_control_intent(actor, state) == 'ride_pin'
                    and not self._valid_von_flue_pending(actor, action, state))
        if not eligible:
            return super()._resolve_exchange_action(actor, defender, action, state, stats)
        attack = self.action_attack_value(actor, action, state)
        defence = self.action_defence_value(defender, action, state)
        margin = attack - defence + self.fight_mechanics_rng().randint(-18, 18)
        edge = (self.ds_avg(actor, ('ride_control', 'positional_ability', 'strength'), actor.ground_control)
                - self.ds_avg(defender, ('bottom_control', 'scrambles', 'flexibility'), defender.grappling))
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

    def resolve_exchange(self, actor, defender, action, state, stats):
        state.pop(FACT, None)
        if not valid_cradle_setup(self, actor, action, state):
            _cancel(state, 'next_action_or_context_changed')
        result = super().resolve_exchange(actor, defender, action, state, stats)
        setup = state.get(KEY)
        if setup and any(state.get(k) != setup.get(k) for k in ('position', 'top', 'bottom', 'round')):
            _cancel(state, 'context_changed')
        if any(state.get(k) for k in ('submission_finish', 'instant_finish', 'technical_outcome', 'technical_foul_stoppage')):
            _cancel(state, 'finish')
        return result

    def submission_technique_tickets(self, actor, action, state):
        result = super().submission_technique_tickets(actor, action, state)
        move = self._fight_move_registry.get(MOVE_ID)
        eligible = (move is not None and not move.deprecated and move.parent_action == action
                    and state.get('position') in move.positions and 'Catch Wrestler' in self.fighter_styles(actor)
                    and sum(self.ds(actor, skill, 50) for skill in move.attack_skills) / len(move.attack_skills) >= move.minimum_skill)
        return list(result) + [HOLD] if eligible and valid_cradle_setup(self, actor, action, state) else result

    def submission_technique(self, actor, action, state):
        valid = valid_cradle_setup(self, actor, action, state)
        state.pop(FACT, None)
        result = super().submission_technique(actor, action, state)
        setup = state.pop(KEY, None)
        if setup:
            state[FACT] = dict(setup, status='used' if valid and result == dict(name=HOLD[0], choke=HOLD[1]) else 'consumed',
                               event_round=state.get('round'), event_tick=state.get('tick'), technique=deepcopy(result))
        return result

    def _move_candidates(self, actor, action, position, target, state):
        rows, *rest = super()._move_candidates(actor, action, position, target, state)
        fact = state.get(FACT) or {}
        proven = (fact.get('status') == 'used' and fact.get('event_round') == state.get('round')
                  and fact.get('event_tick') == state.get('tick') and fact.get('top') == self.fight_state_key(actor, state)
                  and fact.get('technique') == dict(name=HOLD[0], choke=False))
        return ([row for row in rows if row.move_id != MOVE_ID or proven], *rest)

    def select_exchange_move(self, actor, defender, action, position, target, state,
                             ownership_before=None, resolved_technique=None):
        fact = state.get(FACT) or {}
        if (action == 'ground_control' and fact.get('event_round') == state.get('round')
                and fact.get('event_tick') == state.get('tick') and fact.get('status') in {'created', 'denied', 'cancelled'}):
            return self._move_payload(None, actor, defender, action, target, state,
                                      self.fight_state_key(actor, state), self.fighter_styles(actor), False, {}, (), ())
        return super().select_exchange_move(actor, defender, action, position, target, state,
                                            ownership_before, resolved_technique)

    def record_fight_trace_exchange(self, a, b, actor, defender, action, result, before, round_before, state, stats):
        event = super().record_fight_trace_exchange(a, b, actor, defender, action, result, before, round_before, state, stats)
        if state.get(FACT):
            event[KEY] = deepcopy(state[FACT])
        return event

    def set_fight_position(self, state, position, **kwargs):
        _cancel(state, 'position_reset')
        return super().set_fight_position(state, position, **kwargs)

    def recover_between_rounds(self, a, b, state):
        _cancel(state, 'horn')
        return super().recover_between_rounds(a, b, state)

    def finalize_fight_result(self, a, b, winner, loser, method, round_no, lines, state):
        _cancel(state, 'finish')
        return super().finalize_fight_result(a, b, winner, loser, method, round_no, lines, state)

    def initiative(self, fighter, opponent, state):
        setup = state.get(KEY)
        if setup and state.get('round') != setup.get('round'):
            _cancel(state, 'round_boundary')
        return super().initiative(fighter, opponent, state)

    def update_ground_inactivity(self, state, action):
        result = super().update_ground_inactivity(state, action)
        setup = state.get(KEY)
        if setup and any(state.get(k) != setup.get(k) for k in ('position', 'top', 'bottom')):
            _cancel(state, 'referee_standup')
            payload = state.get('last_move_payload')
            if payload and action == 'ground_control':
                payload.update(move_id='generic_ground_control', name='ground control', generic=True,
                               signature=False, move_mastery=0, sequence_source_id='', sequence_step=0)
                payload.pop('sequence_occurrence_id', None)
        return result

    def check_fight_stoppage(self, actor, defender, state):
        result = super().check_fight_stoppage(actor, defender, state)
        if result:
            _cancel(state, 'finish')
        return result
