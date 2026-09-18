"""Audit-only repair of an attacking hold incorrectly authored as a reversal."""
from dataclasses import replace


def apply_heel_hook_identity(definitions):
    definitions = tuple(definitions)
    matches = [move for move in definitions if move.move_id == 'heel_hook']
    if len(matches) != 1:
        raise ValueError('Heel-hook identity repair requires exactly one heel_hook')
    move = matches[0]
    if (move.positions != frozenset({'leg entanglement'}) or
            move.parent_action not in {'counter_leg_lock', 'leg_attack'}):
        raise ValueError('Heel-hook geometry changed; review the identity repair')
    repaired = replace(move, parent_action='leg_attack',
                       tags=tuple(tag for tag in move.tags if tag != 'counter'))
    return tuple(repaired if row.move_id == 'heel_hook' else row for row in definitions)
