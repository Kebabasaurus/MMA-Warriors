"""Small authoring helpers; existing catalogue definitions remain literal and unchanged."""
from .schema import move, STANDING_POSITIONS, CLINCH_POSITIONS


def _preset(move_id, name, defaults, styles, tags, overrides):
    values = dict(defaults)
    values.update(overrides)
    values["preferred_styles"] = tuple(styles)
    values["tags"] = tuple(dict.fromkeys((*defaults.get("tags", ()), *tags)))
    action, positions = values.pop("action"), values.pop("positions")
    return move(move_id, name, action, positions, **values)


def punch(move_id, name, *, styles=(), tags=(), **overrides):
    return _preset(move_id, name, {
        "action": "power_punch", "positions": STANDING_POSITIONS,
        "attack_skills": ("punch_technique", "hand_speed"),
        "defense_skills": ("head_movement", "guard_defence"),
        "side": "lead", "range_band": "pocket", "defense_families": ("block", "parry"),
        "tags": ("strike", "punch"),
    }, styles, tags, overrides)


def kick(move_id, name, *, target, side, styles=(), tags=(), **overrides):
    skill_prefix = "low" if target == "leg" else "high"
    return _preset(move_id, name, {
        "action": "kick", "positions": STANDING_POSITIONS, "targets": frozenset({target}),
        "attack_skills": (f"{skill_prefix}_kick_technique", f"{skill_prefix}_kick_speed"),
        "defense_skills": ("kick_defence", "footwork"),
        "side": side, "range_band": "kicking", "defense_families": ("check", "evade"),
        "tags": ("strike", "kick"),
    }, styles, tags, overrides)


def takedown(move_id, name, *, entry_family, finish_positions, styles=(), tags=(), **overrides):
    return _preset(move_id, name, {
        "action": "takedown", "positions": CLINCH_POSITIONS,
        "attack_skills": ("takedowns", "chain_wrestling"),
        "defense_skills": ("takedown_defence_detail", "sprawl"),
        "entry_family": entry_family, "finish_positions": tuple(finish_positions),
        "defense_families": ("sprawl", "balance"), "tags": ("wrestling", "takedown"),
    }, styles, tags, overrides)


def submission(move_id, name, *, positions, attack_path, failure_outcomes,
               styles=(), tags=(), **overrides):
    return _preset(move_id, name, {
        "action": "submission", "positions": positions,
        "attack_skills": ("submission_attack", "positional_ability"),
        "defense_skills": ("submission_defence_detail", "composure"),
        "attack_path": attack_path, "failure_outcomes": tuple(failure_outcomes),
        "tags": ("ground", "submission"),
    }, styles, tags, overrides)


def recovery(move_id, name, *, positions, styles=(), tags=(), **overrides):
    return _preset(move_id, name, {
        "action": "recover_guard", "positions": positions,
        "attack_skills": ("guard_work", "bottom_control", "scrambles"),
        "defense_skills": ("top_control", "positional_ability"),
        "tags": ("ground", "escape", "recovery"),
    }, styles, tags, overrides)
