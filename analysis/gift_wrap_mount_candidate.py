"""Audit-only mount-specific refinement retaining both original back branches."""
from dataclasses import replace
from fight_moves.chains import validate_chain_graph
from analysis.gift_wrap_control_candidate import ROOT_ID, ORIGINAL

MOUNT_REPLACEMENT = ('high_mount_arm_pinch', 'rear_naked_choke', 'body_triangle_back_control')


def apply_gift_wrap_mount(definitions):
    """Trade only the mount striking edge for mount arm-control consolidation.

    Three authored successors remain. Back choke/control edges are unchanged;
    ordinary hammerfists remain legal but no longer receive this root's credit.
    Does not infer a completed armbar or change named-move eligibility.
    """
    definitions = tuple(definitions)
    lookup = {d.move_id: d for d in definitions}
    if len(lookup) != len(definitions):
        raise ValueError('Duplicate move IDs')
    if ROOT_ID not in lookup or any(key not in lookup for key in MOUNT_REPLACEMENT):
        raise ValueError('Missing mount-refinement definitions')
    if lookup[ROOT_ID].follow_ups not in (ORIGINAL, MOUNT_REPLACEMENT):
        raise ValueError('Gift-wrap root drift or conflicting trial')
    if lookup[MOUNT_REPLACEMENT[0]].positions != frozenset({'mount'}):
        raise ValueError('Mount-only control identity drifted')
    result = tuple(replace(d, follow_ups=MOUNT_REPLACEMENT) if d.move_id == ROOT_ID else d for d in definitions)
    errors = validate_chain_graph(result)
    if errors:
        raise ValueError('; '.join(errors))
    return result
