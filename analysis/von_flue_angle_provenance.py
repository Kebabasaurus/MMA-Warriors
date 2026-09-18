"""Pure provenance validation for a retained wrap followed by shoulder-angle work."""
from collections import Counter
import math


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _owners(event, fact, suffix):
    return (event.get('position_' + suffix) == fact.get('position') == 'half guard'
            and event.get('top_' + suffix) == fact.get('top')
            and event.get('bottom_' + suffix) == fact.get('bottom')
            and event.get('clinch_' + suffix) is None)


def _generic_control(event):
    move = event.get('move') or {}
    move_id = event.get('move_id', move.get('move_id', '')) if isinstance(move, dict) else None
    return (isinstance(move, dict) and move.get('generic') is True
            and isinstance(move_id, str) and move_id.startswith('generic_')
            and not event.get('submission_technique')
            and not any(event.get(key) or move.get(key) for key in
                        ('signature', 'move_mastery', 'sequence_source_id')))


def _origin(event, fact, *, settled=True):
    defense = event.get('guillotine_defense') or {}
    technique = event.get('submission_technique') or {}
    if not isinstance(defense, dict) or not isinstance(technique, dict):
        return False
    scores = [defense.get(key) for key in ('adjusted_margin', 'retention_margin', 'shoulder_margin')]
    return (all(_finite(value) for value in scores) and scores[0] < -10 and scores[1] > 0 and scores[2] < 0
            and all(defense.get(key) == fact.get(key) for key in ('top', 'bottom', 'position', 'round', 'tick'))
            and defense.get('pressure_stopped') is True and defense.get('neck_wrap_retained') is True
            and defense.get('shoulder_angle_established') is False and defense.get('top_control_consolidated') is True
            and event.get('action') == 'bottom_submission' and event.get('actor') == fact['bottom']
            and technique.get('name') == 'guillotine choke' and technique.get('choke') is True
            and fact['created_tick'] == fact['tick'] and _owners(event, fact, 'before')
            and (not settled or _owners(event, fact, 'after')))


def validate_von_flue_angles(trace):
    """Return counts and valid (round, tick, top, bottom) alternative-creation keys.

    A root expires at any intervening exchange or round/fight boundary. Scores
    validate recorded arithmetic, not unrecorded skill rolls. No state is edited.
    """
    counts, creations, pending = Counter(), set(), None
    for event in trace:
        if event.get('type') != 'exchange':
            if pending is not None:
                counts['boundary'] += 1
            pending = None
            continue
        # Ordinary audited traces may omit horn markers. A proven forward round
        # change expires the pending origin just as an explicit boundary does;
        # it does not license angle work or stale setup facts in the new round.
        if (pending is not None and type(event.get('round')) is int
                and event['round'] > pending['round']):
            counts['boundary'] += 1
            pending = None
        fact = event.get('von_flue_angle')
        previous, pending = pending, None
        if fact is None:
            defense = event.get('guillotine_defense') or {}
            implied = dict(defense, created_tick=defense.get('tick')) if isinstance(defense, dict) else {}
            expected_origin = (implied.get('top') in ('a', 'b')
                               and implied.get('bottom') == ('b' if implied['top'] == 'a' else 'a')
                               and type(implied.get('tick')) is int and type(implied.get('round')) is int
                               and _origin(event, implied, settled=False))
            if previous is not None or expected_origin:
                counts['invalid'] += 1  # Dropped required consumption/cancellation evidence.
            continue
        if not isinstance(fact, dict):
            counts['invalid'] += 1
            continue
        status, top, bottom = fact.get('status'), fact.get('top'), fact.get('bottom')
        base = (top in ('a', 'b') and bottom == ('b' if top == 'a' else 'a')
                and fact.get('position') == 'half guard'
                and all(type(fact.get(key)) is int and fact[key] > 0 for key in ('round', 'tick', 'created_tick'))
                and fact.get('round') == event.get('round') and fact.get('tick') == event.get('tick'))
        if not base:
            counts['invalid'] += 1
            continue
        scores = [fact.get(key) for key in ('raw_margin', 'shoulder_margin', 'adjusted_margin')]
        attempted = fact.get('attempted', False)
        score_ok = (attempted is True and all(_finite(value) for value in scores)
                    and math.isclose(scores[2], scores[0] + .2 * scores[1], rel_tol=0, abs_tol=1e-9))
        unattempted = attempted is False and all(value is None for value in scores)
        linked = (previous is not None and all(fact.get(key) == previous.get(key)
                  for key in ('top', 'bottom', 'position', 'round', 'created_tick'))
                  and fact['tick'] == previous['created_tick'] + 1)
        control = (linked and event.get('action') == 'ground_control' and event.get('actor') == top
                   and _owners(event, fact, 'before') and _generic_control(event))
        setup = event.get('von_flue_setup') or {}
        setup_ok = (isinstance(setup, dict) and setup.get('source') == 'angle_work'
                    and setup.get('origin_tick') == fact['created_tick'] and setup.get('created_tick') == fact['tick']
                    and all(setup.get(key) == fact.get(key) for key in ('top', 'bottom', 'position', 'round')))
        valid, creation = False, False
        if status == 'pending':
            valid = unattempted and _origin(event, fact) and not setup
            if valid:
                pending = dict(fact)
                if previous is not None:
                    counts['replaced_by_new_origin'] += 1
        elif status in ('ready', 'cleared'):
            ready = score_ok and scores[2] > 8
            valid = (control and score_ok and _owners(event, fact, 'after')
                     and (status == 'ready') == ready)
            valid = valid and (setup_ok and setup.get('status') == 'created' if ready else not setup)
            creation = valid and ready
        elif status == 'cancelled':
            reason = fact.get('reason')
            referee = event.get('referee_ground_action') or {}
            origin_now = unattempted and _origin(event, fact, settled=False)
            live = linked or origin_now
            if reason == 'referee_standup':
                reset = (isinstance(referee, dict) and referee.get('type') == 'standup'
                         and event.get('position_after') == 'range'
                         and all(event.get(key) is None for key in ('top_after', 'bottom_after', 'clinch_after')))
                if attempted is True:
                    ready = score_ok and scores[2] > 8
                    valid = (control and score_ok and reset
                             and (setup_ok and setup.get('status') == 'cancelled' and setup.get('reason') == reason
                                  if ready else not setup))
                    creation = valid and ready
                else:
                    valid = live and unattempted and reset and not setup
            elif reason == 'next_action_or_context_changed':
                valid = (linked and unattempted and not setup and
                         (event.get('action') != 'ground_control' or event.get('actor') != top
                          or not _owners(event, fact, 'before')))
            elif reason == 'position_or_ownership_changed':
                valid = live and unattempted and not setup and not _owners(event, fact, 'after')
            elif reason == 'fight_finished':
                valid = (live and bool(event.get('stoppage')) and
                         ((unattempted and not setup) or (control and score_ok and scores[2] > 8
                           and setup_ok and setup.get('status') == 'created')))
                creation = valid and attempted is True
        counts[status if valid else 'invalid'] += 1
        if creation:
            creations.add((fact['round'], fact['tick'], top, bottom))
    if pending is not None:
        counts['unobserved'] += 1
    return {'counts': dict(counts), 'valid_creation_keys': creations}
