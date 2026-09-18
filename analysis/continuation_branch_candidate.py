"""Audit-only additions to sparse authored roots; never production registration.

The fixed 300-bout opportunity report found 84 disjoint action opportunities
across these 259 roots, not 84 guaranteed completions. All current selectors,
identity/provenance gates and failed-root accounting must remain authoritative.
"""
from dataclasses import replace
from types import MappingProxyType

from fight_moves.chains import validate_chain_graph


CONTINUATION_ADDITIONS = MappingProxyType({
    "side_control_frame_elbows": ("reverse_scarf_hold_control", "short_ground_elbows"),
    "guard_can_opener": ("standing_guard_opening_pass", "guard_top_head_arm"),
    "karate_blitz_cross_hook_exit": ("retreating_jab",),
    "karate_blitz_reverse_cross_finisher": ("retreating_jab",),
    "double_jab_body_cross": ("single_jab",),
    "guard_top_punch_choke": ("guard_top_head_arm",),
    "stance_shift_cross_hook": ("retreating_jab",),
    "duck_under_single_entry": ("guard_top_head_arm",),
    "overhand": ("single_jab",),
    "lead_body_round_kick": ("single_jab",),
    "lead_body_uppercut": ("lead_hook_cross",),
    "guard_top_ezekiel": ("guard_posture_elbows",),
    "side_control_short_hooks": ("reverse_scarf_hold_control",),
})

CONTINUATION_RATIONALES = MappingProxyType({
    "side_control_frame_elbows": "Consolidate the frame/hip orientation or continue compact elbows before climbing.",
    "guard_can_opener": "Follow guard-opening pressure with an actual pass or independently resolved head/arm attack.",
    "karate_blitz_cross_hook_exit": "Cover withdrawal from the blitz with the lead hand.",
    "karate_blitz_reverse_cross_finisher": "Recover distance with a lead-hand strike after the reverse cross.",
    "double_jab_body_cross": "Re-establish the lead hand after the rear-hand combination.",
    "guard_top_punch_choke": "Change choking configuration while actual top guard ownership remains intact.",
    "stance_shift_cross_hook": "Re-establish distance after the stance-shifting combination.",
    "duck_under_single_entry": "After a real takedown settles, allow a separately resolved top head/arm attack.",
    "overhand": "Retain the level-change option and add lead-hand range recovery.",
    "lead_body_round_kick": "Re-establish punching distance after retracting the body kick.",
    "lead_body_uppercut": "Follow body work upstairs with a separately chosen head combination.",
    "guard_top_ezekiel": "Release the choke to posture and strike while top guard remains intact.",
    "side_control_short_hooks": "Consolidate positional control after short hooks instead of always advancing.",
})


def apply_continuation_branches(definitions):
    """Return an ordered disposable catalogue, rejecting drift or invalid graphs.

    Existing successors stay first and unchanged. An exact already-appended
    suffix is idempotent for nested audit contexts; partial overlaps fail.
    No registry, source definition or global random state is mutated.
    """
    original = tuple(definitions)
    ids = [definition.move_id for definition in original]
    if len(set(ids)) != len(ids):
        raise ValueError("Continuation candidate input contains duplicate move IDs")
    by_id = {definition.move_id: definition for definition in original}
    missing_roots = sorted(set(CONTINUATION_ADDITIONS) - by_id.keys())
    missing_successors = sorted({key for ids in CONTINUATION_ADDITIONS.values() for key in ids} - by_id.keys())
    if missing_roots or missing_successors:
        raise ValueError(f"Continuation candidate missing roots {missing_roots} or successors {missing_successors}")
    result = []
    for definition in original:
        current = tuple(definition.follow_ups)
        additions = CONTINUATION_ADDITIONS.get(definition.move_id, ())
        applied = bool(additions and current[-len(additions):] == additions)
        combined = current if applied else current + additions
        if len(set(combined)) != len(combined):
            raise ValueError(f"Duplicate continuation for {definition.move_id}")
        if len(combined) > 3:
            raise ValueError(f"More than three continuations for {definition.move_id}")
        result.append(replace(definition, follow_ups=combined) if additions and not applied else definition)
    errors = validate_chain_graph(result)
    if errors:
        raise ValueError("Invalid continuation candidate graph: " + "; ".join(errors))
    return tuple(result)
