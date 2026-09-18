"""Single-root audit trial: retain control after gift-wrap work settles in mount."""
from dataclasses import replace
from fight_moves.chains import validate_chain_graph

ROOT_ID = 'gift_wrap_transition'
ORIGINAL = ('mounted_hammerfist_flurry', 'rear_naked_choke', 'body_triangle_back_control')
REPLACEMENT = ('mounted_hammerfist_flurry', 'rear_naked_choke', 'hip_pressure_ride')


def apply_gift_wrap_control(definitions):
    """Replace only the root's control branch; no new IDs, weights or legality."""
    definitions = tuple(definitions)
    lookup = {d.move_id: d for d in definitions}
    if len(lookup) != len(definitions):
        raise ValueError('Duplicate move IDs')
    if ROOT_ID not in lookup or any(key not in lookup for key in REPLACEMENT):
        raise ValueError('Missing gift-wrap candidate definitions')
    if lookup[ROOT_ID].follow_ups not in (ORIGINAL, REPLACEMENT):
        raise ValueError('Gift-wrap successor map drifted')
    result = tuple(replace(d, follow_ups=REPLACEMENT) if d.move_id == ROOT_ID else d for d in definitions)
    errors = validate_chain_graph(result)
    if errors:
        raise ValueError('; '.join(errors))
    return result
