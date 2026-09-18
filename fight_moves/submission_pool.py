"""Pre-draw experimental variants with per-ticket mechanical-family conservation.

Only repeated original tickets are replaceable; the first occurrence of every
original technique remains intact. No seed, current outcome, observed frequency
or random source participates. Unqualified families retain their original ticket.
"""
from collections import defaultdict


# Exact identity, resolved name, choke flag. Leg classification uses the same
# explicit name tokens as resolve_submission. No unsupported setup is inferred.
SUBMISSION_VARIANTS = (
    ("half_guard_americana", "Americana", False),
    ("half_guard_arm_triangle", "arm-triangle choke", True),
    ("half_guard_shoulder_choke", "shoulder-pressure choke", True),
    ("guard_top_head_arm", "arm-triangle choke", True),
    ("guard_can_opener", "can-opener neck crank", False),
    ("guard_top_wrist_lock", "wrist lock", False),
    ("guard_top_punch_choke", "punch choke", True),
    ("guard_gogoplata", "gogoplata", True),
    ("guard_reverse_armbar", "reverse armbar", False),
    ("guard_wrist_lock", "wrist lock", False),
    ("guard_overhook_shoulder_lock", "overhook shoulder lock", False),
    ("guard_inverted_triangle", "inverted triangle", True),
    ("front_high_elbow_guillotine", "high-elbow guillotine", True),
    ("front_arm_in_guillotine", "arm-in guillotine", True),
    ("front_ten_finger_guillotine", "ten-finger guillotine", True),
    ("entangled_belly_down_ankle_lock", "belly-down ankle lock", False),
    ("entangled_figure_four_toe_hold", "figure-four toe hold", False),
    ("entangled_rolling_kneebar", "rolling kneebar", False),
    ("sambo_rolling_kneebar_finisher", "rolling kneebar", False),
    ("bjj_triangle_armbar_finisher", "triangle-to-armbar finish", False),
    ("submission_grappler_rear_triangle_finisher", "rear-triangle choke", True),
)


def submission_ticket_family(ticket):
    name, choke = ticket
    return bool(choke), any(token in name.casefold() for token in (
        "heel", "knee", "ankle", "toe hold", "slicer", "cloverleaf",
    ))


def adapt_submission_tickets(tickets, eligible_ids):
    """Preserve length, first originals and each index's choke/leg flags."""
    tickets = list(tickets)
    alternatives = defaultdict(list)
    for move_id, name, choke in SUBMISSION_VARIANTS:
        ticket = (name, choke)
        family = submission_ticket_family(ticket)
        if move_id in eligible_ids and ticket not in alternatives[family]:
            alternatives[family].append(ticket)
    seen, used = set(), defaultdict(int)
    result = []
    for ticket in tickets:
        family = submission_ticket_family(ticket)
        variants = alternatives[family]
        if ticket in seen and variants:
            result.append(variants[used[family] % len(variants)])
            used[family] += 1
        else:
            result.append(ticket)
        seen.add(ticket)
    return result
