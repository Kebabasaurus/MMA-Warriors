"""Candidate-only tactical preferences for proven physical-top specialist roles."""
import math


_TOP_POLICY_ACTIONS = {
    "turtle": {
        "take_back": "advance_position",
        "turtle_ride": "ground_control",
        "ground_strikes": "ground_strikes",
    },
    "front headlock": {
        "take_back": "advance_position",
        "turtle_ride": "ground_control",
        "front_headlock_submission": "submission",
    },
}


def specialist_style_weights(engine, fighter, state, weights):
    """Reuse existing top-style policy for physical-top specialist menus.

    Independent of tactical-plan enablement. Aliases are lookup keys, never new
    actions; apply once after survival and before plan/chain preferences.
    """
    if not getattr(engine, "_experimental_specialist_entries", False):
        return weights
    aliases = _TOP_POLICY_ACTIONS.get(state.get("position"))
    actor_key = engine.fight_state_key(fighter, state)
    if (aliases is None or state.get("top") != actor_key
            or state.get("bottom") not in ("a", "b") or state.get("bottom") == actor_key
            or state.get("clinch_controller") is not None):
        return weights
    policy_weights = dict.fromkeys(
        (aliases[action] for action in weights if action in aliases), 1.0,
    )
    if not policy_weights:
        return weights
    engine.apply_style_bias(fighter, policy_weights, "top")
    return {action: weight * policy_weights[aliases[action]] if action in aliases else weight
            for action, weight in weights.items()}


def specialist_plan_weights(engine, fighter, opponent, state, weights, round_no):
    """Reuse ordinary top-plan preferences without inventing a legal action.

    Call after survival overrides and before chain apportionment. Aliases are
    policy lookups only: the returned menu retains the original action keys and
    order. Neither leg knee-line ownership nor standing clinch ownership is top.
    """
    if not getattr(engine, "_experimental_specialist_entries", False):
        return weights
    aliases = _TOP_POLICY_ACTIONS.get(state.get("position"))
    if aliases is None:
        return weights
    actor_key = engine.fight_state_key(fighter, state)
    if state.get("top") != actor_key:
        return weights
    row = engine.fight_plan_for(fighter, state)
    if not row.get("enabled", False):
        return weights
    try:
        execution = float(row.get("execution", 0))
    except (TypeError, ValueError, OverflowError):
        return weights
    if not math.isfinite(execution) or execution <= 0:
        return weights
    execution = min(1.0, execution)
    # Isolate the one bounded field; the ordinary policy reads this shallow
    # view but never mutates bout state, plan history or fighter data.
    plan_state = dict(state)
    plans = dict(state.get("plans") or {})
    plans[actor_key] = dict(row, execution=execution)
    plan_state["plans"] = plans
    policy_weights = dict.fromkeys(
        (aliases[action] for action in weights if action in aliases), 1.0,
    )
    if not policy_weights:
        return weights
    engine.apply_fight_plan_weights(
        fighter, opponent, plan_state, "top", policy_weights, round_no,
    )
    return {
        action: weight * policy_weights[aliases[action]] if action in aliases else weight
        for action, weight in weights.items()
    }
