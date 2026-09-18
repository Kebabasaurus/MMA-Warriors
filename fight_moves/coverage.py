"""Evidence-scoped reachability diagnostics; absence is not proof of impossibility."""
from .catalogue import MOVE_DEFINITIONS
from .index import MoveIndex
from constants import STYLES


def unreachable_moves(reachable_positions, reachable_actions, roster_skill_p50,
                      *, definitions=MOVE_DEFINITIONS, reachable_contexts=None,
                      available_styles=STYLES):
    """Return reasons relative to supplied engine/roster evidence, never registry positions.

    Context triples are (action, pre-exchange position, requested target). An
    intermediate position path is not a legal next-selection opportunity.
    Skill medians flag specialist gates; they do not establish absolute dead code.
    """
    positions, actions = set(reachable_positions), set(reachable_actions)
    styles = set(available_styles)
    contexts = None if reachable_contexts is None else set(reachable_contexts)
    result = {}
    for move in definitions:
        reasons = []
        if move.parent_action not in actions:
            reasons.append("no-parent-action")
        if not move.positions.intersection(positions):
            reasons.append("position-never-entered")
        if contexts is not None and not reasons:
            relevant = [(a, p, t) for a, p, t in contexts
                        if a == move.parent_action and p in move.positions]
            if not relevant:
                reasons.append("no-parent-action")
            elif not any(not move.targets or (t and t in move.targets) for _, _, t in relevant):
                reasons.append("target-never-requested")
        if set(move.tags).intersection({"style-combination", "style-finisher"}):
            if len(move.preferred_styles) != 1 or not styles.intersection(move.preferred_styles):
                reasons.append("style-gate-unsatisfiable")
        if roster_skill_p50 is not None and move.attack_skills:
            score = sum(roster_skill_p50.get(skill, 0) for skill in move.attack_skills) / len(move.attack_skills)
            if score < move.minimum_skill:
                reasons.append("skill-gate-above-roster")
        if reasons:
            result[move.move_id] = reasons
    return result


def coverage_report(reachable_contexts, *, definitions=MOVE_DEFINITIONS,
                    minimum_pool=4, minimum_style=18):
    """Pool depths only for action/position/target keys supported by supplied evidence."""
    index = MoveIndex(definitions)
    pools = []
    for action, position in sorted({(a, p) for a, p, _ in reachable_contexts}):
        targets = {t for a, p, t in reachable_contexts if (a, p) == (action, position)}
        ids = {m.move_id for target in targets for m in index.legal_moves(action, position, target)}
        pools.append({"action": action, "position": position, "depth": len(ids),
                      "minimum": minimum_pool, "below_floor": len(ids) < minimum_pool})
    styles = {style: len(index.by_style(style)) for style in STYLES}
    return {"pools": pools, "style_counts": styles,
            "thin_styles": {style: count for style, count in styles.items() if count < minimum_style}}
