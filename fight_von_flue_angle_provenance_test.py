"""Trace provenance cannot substitute a generic position for an actual neck wrap."""
from copy import deepcopy
import random
import unittest

from analysis.von_flue_angle_provenance import validate_von_flue_angles


def origin(top='a'):
    bottom = 'b' if top == 'a' else 'a'
    fact = dict(top=top, bottom=bottom, position='half guard', round=1, created_tick=3,
                tick=3, status='pending', attempted=False)
    return dict(type='exchange', round=1, tick=3, actor=bottom, action='bottom_submission',
                position_before='half guard', position_after='half guard', top_before=top, top_after=top,
                bottom_before=bottom, bottom_after=bottom, clinch_before=None, clinch_after=None,
                submission_technique={'name': 'guillotine choke', 'choke': True}, von_flue_angle=fact,
                guillotine_defense=dict(top=top, bottom=bottom, position='half guard', round=1, tick=3,
                    adjusted_margin=-20, retention_margin=2, shoulder_margin=-1, pressure_stopped=True,
                    neck_wrap_retained=True, shoulder_angle_established=False, top_control_consolidated=True))


def work(top='a', raw=10, shoulder=-5):
    event = origin(top)
    event.pop('guillotine_defense')
    event.pop('submission_technique')
    ready = raw + .2 * shoulder > 8
    event.update(tick=4, actor=top, action='ground_control', move_id='generic_ground_control',
                 move={'move_id': 'generic_ground_control', 'generic': True})
    event['von_flue_angle'].update(tick=4, status='ready' if ready else 'cleared', attempted=True,
                                   raw_margin=raw, shoulder_margin=shoulder, adjusted_margin=raw + .2 * shoulder)
    if ready:
        event['von_flue_setup'] = dict(top=top, bottom=event['bottom_before'], position='half guard',
                                      round=1, created_tick=4, origin_tick=3, source='angle_work', status='created')
    return event


class VonFlueAngleProvenanceTests(unittest.TestCase):
    def test_exchange_only_horn_expires_pending_without_missing_evidence(self):
        next_round = dict(type='exchange', round=2, tick=1, action='jab')
        trace = [origin(), next_round]
        before = deepcopy(trace)
        self.assertEqual(validate_von_flue_angles(trace)['counts'], {'pending': 1, 'boundary': 1})
        self.assertEqual(trace, before)
        stale = work()
        stale['round'] = 2
        self.assertEqual(validate_von_flue_angles([origin(), stale])['counts'],
                         {'pending': 1, 'boundary': 1, 'invalid': 1})
        # Missing/malformed/backward rounds cannot launder a dropped cancellation.
        for value in (None, True, 0):
            malformed = dict(next_round, round=value)
            self.assertEqual(validate_von_flue_angles([origin(), malformed])['counts'],
                             {'pending': 1, 'invalid': 1})

    def test_ready_clear_boundary_and_purity_both_slots(self):
        for top in ('a', 'b'):
            for raw in (9, 9.0001):
                trace = [origin(top), work(top, raw)]
                before, rng = deepcopy(trace), random.getstate()
                result = validate_von_flue_angles(trace)
                status = 'ready' if raw > 9 else 'cleared'
                self.assertEqual(result['counts'], {'pending': 1, status: 1})
                self.assertEqual(result['valid_creation_keys'], {(1, 4, top, trace[0]['bottom_before'])} if raw > 9 else set())
                self.assertEqual(trace, before)
                self.assertEqual(random.getstate(), rng)
        self.assertEqual(validate_von_flue_angles([origin(), {'type': 'round_end'}])['counts'], {'pending': 1, 'boundary': 1})

    def test_origin_rejects_wrong_hold_role_scores_and_facts(self):
        missing = origin()
        missing.pop('von_flue_angle')
        self.assertEqual(validate_von_flue_angles([missing])['counts'], {'invalid': 1})
        changes = [('submission_technique', {'name': 'arm-in guillotine', 'choke': True}),
                   ('actor', 'a'), ('bottom_after', 'a'), ('position_before', 'guard')]
        for field, value in changes:
            event = origin()
            event[field] = value
            self.assertEqual(validate_von_flue_angles([event, work()])['counts']['invalid'], 2)
        for field, value in [('retention_margin', 0), ('shoulder_margin', 0), ('adjusted_margin', -10),
                             ('retention_margin', float('nan')), ('pressure_stopped', False)]:
            event = origin()
            event['guillotine_defense'][field] = value
            self.assertEqual(validate_von_flue_angles([event])['counts'], {'invalid': 1})

    def test_missing_origin_intervening_event_and_false_control_credit(self):
        self.assertEqual(validate_von_flue_angles([work()])['counts'], {'invalid': 1})
        for changes in ({'signature': True}, {'move_mastery': {'level': 2}}, {'sequence_source_id': 'old'},
                        {'actor': 'b'}, {'top_after': 'b'}, {'move_id': None}, {'submission_technique': {'name': 'Von Flue choke'}}):
            event = work()
            event.update(changes)
            self.assertEqual(validate_von_flue_angles([origin(), event])['counts']['invalid'], 1)
        event = work()
        event['move']['generic'] = False
        self.assertEqual(validate_von_flue_angles([origin(), event])['counts']['invalid'], 1)
        event = dict(type='exchange', action='survive')
        self.assertEqual(validate_von_flue_angles([origin(), event, work()])['counts']['invalid'], 2)

    def test_rejects_nonfinite_arithmetic_wrong_source_and_stale_epoch(self):
        for field, value in [('raw_margin', float('inf')), ('adjusted_margin', 10),
                             ('shoulder_margin', True), ('created_tick', 2), ('round', 2), ('tick', 5)]:
            event = work()
            event['von_flue_angle'][field] = value
            self.assertEqual(validate_von_flue_angles([origin(), event])['counts']['invalid'], 1)
        for field, value in [('source', 'position'), ('origin_tick', 2), ('created_tick', 3), ('top', 'b')]:
            event = work()
            event['von_flue_setup'][field] = value
            self.assertEqual(validate_von_flue_angles([origin(), event])['valid_creation_keys'], set())

    def test_cancelled_ready_referee_still_proves_alternative_creation(self):
        event = work()
        event['von_flue_angle'].update(status='cancelled', reason='referee_standup')
        event['von_flue_setup'].update(status='cancelled', reason='referee_standup')
        event.update(position_after='range', top_after=None, bottom_after=None,
                     referee_ground_action={'type': 'standup'})
        result = validate_von_flue_angles([origin(), event])
        self.assertEqual(result['counts'], {'pending': 1, 'cancelled': 1})
        self.assertEqual(result['valid_creation_keys'], {(1, 4, 'a', 'b')})
        for changes in ({'top_after': 'a'}, {'referee_ground_action': None}, {'clinch_after': 'a'}):
            broken = deepcopy(event)
            broken.update(changes)
            self.assertEqual(validate_von_flue_angles([origin(), broken])['counts']['invalid'], 1)
        cleared = work(raw=9)
        cleared['von_flue_angle'].update(status='cancelled', reason='referee_standup')
        cleared.update(position_after='range', top_after=None, bottom_after=None,
                       referee_ground_action={'type': 'standup'})
        result = validate_von_flue_angles([origin(), cleared])
        self.assertEqual(result['counts'], {'pending': 1, 'cancelled': 1})
        self.assertFalse(result['valid_creation_keys'])

    def test_unattempted_cancellation_consumes_without_ready_claim(self):
        event = origin()
        event.pop('guillotine_defense')
        event.pop('submission_technique')
        event.update(tick=4, actor='a', action='survive')
        event['von_flue_angle'].update(tick=4, status='cancelled', reason='next_action_or_context_changed')
        result = validate_von_flue_angles([origin(), event])
        self.assertEqual(result['counts'], {'pending': 1, 'cancelled': 1})
        self.assertFalse(result['valid_creation_keys'])
        event['action'] = 'ground_control'
        self.assertEqual(validate_von_flue_angles([origin(), event])['counts']['invalid'], 1)


if __name__ == '__main__':
    unittest.main()
