"""Deterministic, non-mutating MMA fight-engine audit helpers.

This module deliberately sits outside the Tk UI.  It supplies the frozen
measurement surface required by FIGHT_ENGINE_DEVELOPMENT_PLAN.md without
changing careers, saves, or the caller's global RNG state.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from constants import DETAILED_SKILL_GROUPS, FINISH_METHODS, KO_METHODS, SUBMISSION_METHODS
from fight_engine import FightEngineMixin
from fight_moves import DEFENSE_REGISTRY, MOVE_REGISTRY
from models import Fighter


BASELINE_SCHEMA_VERSION = 1
ACCEPTED_RESULT_CALIBRATION = {
    "fight_count": 3840,
    "finishes": 2319,
    "methods": {"KO": 633, "TKO": 731},
    "rates": {"finish_pct": 60.39, "KO": 16.48, "TKO": 19.04},
}
METHOD_FAMILIES = {
    **{method: "KO/TKO" for method in KO_METHODS},
    **{method: "Submission" for method in SUBMISSION_METHODS},
    **{method: "Other finish" for method in FINISH_METHODS - KO_METHODS - SUBMISSION_METHODS},
    "Decision": "Decision", "Draw": "Draw",
    "Technical Decision": "Decision", "No Contest": "Draw",
}

# These two detailed attributes operate before the opening bell. Dedication
# shapes development/professionalism and weight_cutting shapes the persistent
# weigh-in penalty consumed by the fight engine. Every other detailed skill is
# expected to be read directly by fight_engine.py.
PREFIGHT_DETAILED_SKILLS = {
    "dedication": "Development and camp professionalism; reflected through prepared fighter state.",
    "weight_cutting": "Weigh-in quality; reflected through weight_cut_penalty and starting gas.",
}


class FightAuditHarness(FightEngineMixin):
    """Small engine host with no UI, career state, finance, or persistence."""

    def __init__(self, rules=None, engine_settings=None):
        self.rules = {
            "rounds": 3, "title_rounds": 5, "round_length": 5,
            **dict(rules or {}),
        }
        self.engine_settings = {
            "ko_power": 1.0, "submission_finish": 1.0,
            "decision_noise": 1.0, "gas_cost": 1.0, "damage": 1.0,
            **dict(engine_settings or {}),
        }
        self.month = 1
        self.week = 1
        self._active_card_day = None

    def ensure_rule_defaults(self):
        self.rules.setdefault("rounds", 3)
        self.rules.setdefault("title_rounds", 5)
        self.rules.setdefault("round_length", 5)

    @staticmethod
    def gym_quality(_name):
        return 50

    @staticmethod
    def fighter_rest_days(_fighter, _month, _week, _day):
        return None


def stable_fighter_id(name):
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]
    return f"AUD-{digest}"


STYLE_PROFILES = {
    "Boxer": {"striking": 5, "wrestling": -4, "grappling": -4, "power": 3,
              "punch_technique": 7, "hand_speed": 6, "head_movement": 5, "kick_defence": -2},
    "Kickboxer": {"striking": 4, "wrestling": -3, "grappling": -3,
                  "high_kick_technique": 6, "low_kick_technique": 7, "kick_defence": 5},
    "Muay Thai": {"striking": 4, "wrestling": -2, "grappling": -3,
                   "knees": 7, "elbows": 7, "thai_plum": 8, "clinch_control": 5},
    "Wrestler": {"striking": -4, "wrestling": 6, "grappling": 2,
                  "takedowns": 7, "chain_wrestling": 7, "top_control": 6, "sprawl": 5},
    "BJJ": {"striking": -5, "wrestling": -1, "grappling": 7,
             "submission_attack": 8, "guard_work": 7, "back_control": 7, "leg_locks": 4},
    "Sambo": {"striking": 1, "wrestling": 4, "grappling": 5,
               "throws": 7, "takedowns": 5, "submission_attack": 6, "leg_locks": 5},
    "Karate": {"striking": 4, "wrestling": -3, "grappling": -4,
                "footwork": 8, "reflexes": 6, "creative_kicks": 7, "head_movement": 5},
    "Dutch Kickboxer": {"striking": 5, "wrestling": -3, "grappling": -4,
                         "combination_punching": 7, "low_kick_technique": 7, "guard_defence": 5},
    "Taekwondo": {"striking": 4, "wrestling": -5, "grappling": -5,
                   "high_kick_speed": 8, "high_kick_technique": 7, "creative_kicks": 8, "mobility": 6},
    "Sanda": {"striking": 3, "wrestling": 2, "grappling": -3,
               "side_kicks": 7, "clinch_takedowns": 6, "throws": 5, "mobility": 5},
    "Freestyle Wrestler": {"striking": -5, "wrestling": 7, "grappling": 1,
                            "takedown_speed": 8, "chain_wrestling": 8, "scrambles": 6},
    "Catch Wrestler": {"striking": -4, "wrestling": 5, "grappling": 5,
                        "ride_control": 7, "submission_attack": 6, "front_headlock": 7},
    "Luta Livre": {"striking": -4, "wrestling": 1, "grappling": 7,
                    "leg_locks": 7, "submission_attack": 7, "scrambles": 6},
    "Judo": {"striking": -4, "wrestling": 6, "grappling": 3,
              "throws": 8, "clinch_takedowns": 7, "balance": 6, "top_control": 5},
    "Grappler": {"striking": -5, "wrestling": 3, "grappling": 7,
                  "top_control": 7, "transitions": 7, "submission_attack": 5},
    "Submission Grappler": {"striking": -6, "wrestling": -1, "grappling": 8,
                             "submission_attack": 9, "back_control": 7, "leg_locks": 6},
    "Well-Rounded": {},
    "MMA Generalist": {},
}

BASELINE_STYLES = (
    "Boxer", "Kickboxer", "Muay Thai", "Wrestler",
    "BJJ", "Sambo", "Karate", "MMA Generalist",
)

BEHAVIOURS = (
    "Pressure", "Volume", "Counter", "Cautious", "Control",
    "Submission Hunter", "Sprawl And Brawl", "Dynamic Attacker",
)


def synthetic_fighter(name, level, style="MMA Generalist", behaviour="Dynamic Attacker", corner=0):
    """Create a stable, style-shaped fighter without consuming random state."""
    level = max(35, min(94, int(level)))
    details = {
        key: level
        for keys in DETAILED_SKILL_GROUPS.values()
        for key in keys
    }
    profile = STYLE_PROFILES.get(style, {})
    for key, delta in profile.items():
        if key in details:
            details[key] = max(1, min(99, details[key] + delta))
    broad = {
        "striking": level, "wrestling": level, "grappling": level,
        "cardio": level, "chin": level, "power": level,
    }
    for key in broad:
        broad[key] = max(1, min(99, broad[key] + profile.get(key, 0)))
    fighter = Fighter(
        name=name, fighter_id=stable_fighter_id(name), weight="Lightweight", age=28,
        record_w=max(2, level // 4), record_l=max(1, (92 - level) // 9),
        popularity=50, momentum=0, morale=60, purse=20_000,
        gender="Male", style=style, stance="Southpaw" if corner % 3 == 1 else "Orthodox",
        behaviour=behaviour, trait="Gym Rat", potential=min(99, level + 5),
        prime_start=26, prime_end=33, detailed_skills=details,
        takedown_defence=level, ground_control=level, submissions=level,
        submission_defence=level, recovery=level, toughness=level,
        fight_iq=level, finishing_instinct=level, professionalism=level,
        camp_quality=50, camp_weeks=8, camp_boost=0, scale_weight=155.0,
        **broad,
    )
    return fighter


def clone_fighter(fighter):
    return Fighter(**asdict(fighter))


def _fighter_slot(fighter, state):
    return state.get("fighter_keys", {}).get(id(fighter), fighter.name)


def run_audited_fight(engine, fighter_a, fighter_b, seed, fight=None):
    """Run one disposable fight and return mechanics evidence.

    The original fighters and the caller's process RNG are observationally
    unchanged. The temporary resolver wrapper captures position and state deltas
    without altering the action result or random-call order.
    """
    original_rng = random.getstate()
    original_resolver = engine.resolve_exchange
    events = []
    a = clone_fighter(fighter_a)
    b = clone_fighter(fighter_b)
    fight = {
        "fighters": [a.name, b.name], "title": False, "main": False,
        "tier": "Main Card", "region": "Audit",
        **dict(fight or {}),
    }

    def recording_resolver(actor, defender, action, state, round_stats):
        actor_key = _fighter_slot(actor, state)
        defender_key = _fighter_slot(defender, state)
        before = {
            "position": state.get("position"),
            "gas": {actor_key: state["gas"][actor_key], defender_key: state["gas"][defender_key]},
            "damage": {actor_key: state["damage"][actor_key], defender_key: state["damage"][defender_key]},
            "head": {actor_key: state["head"][actor_key], defender_key: state["head"][defender_key]},
            "body": {actor_key: state["body"][actor_key], defender_key: state["body"][defender_key]},
            "leg": {actor_key: state["leg"][actor_key], defender_key: state["leg"][defender_key]},
            "stats": deepcopy(state["stats"]),
        }
        result = original_resolver(actor, defender, action, state, round_stats)
        events.append({
            "round": state.get("round", 1), "tick": state.get("tick", 1),
            "actor": actor_key, "defender": defender_key, "action": action,
            "position_before": before["position"], "position_after": state.get("position"),
            "result": result or "",
            "gas_before": before["gas"],
            "damage_delta": {
                key: state["damage"][key] - before["damage"][key]
                for key in (actor_key, defender_key)
            },
            "head_delta": {key: state["head"][key] - before["head"][key] for key in (actor_key, defender_key)},
            "body_delta": {key: state["body"][key] - before["body"][key] for key in (actor_key, defender_key)},
            "leg_delta": {key: state["leg"][key] - before["leg"][key] for key in (actor_key, defender_key)},
            "sig_delta": state["stats"][actor_key]["sig"] - before["stats"][actor_key]["sig"],
            "sig_att_delta": state["stats"][actor_key]["sig_att"] - before["stats"][actor_key]["sig_att"],
            "td_delta": state["stats"][actor_key]["td"] - before["stats"][actor_key]["td"],
            "td_att_delta": state["stats"][actor_key]["td_att"] - before["stats"][actor_key]["td_att"],
            "sub_att_delta": state["stats"][actor_key]["sub_att"] - before["stats"][actor_key]["sub_att"],
        })
        return result

    try:
        random.seed(int(seed))
        engine.resolve_exchange = recording_resolver
        winner, loser, method, round_no, commentary = engine.simulate_fight(a, b, fight)
        scorecards = [line.strip() for line in commentary if line.strip().startswith("Judge ")]
        native_result = getattr(engine, "_last_fight_result", None)
        result = {
            "seed": int(seed), "a_id": a.fighter_id, "b_id": b.fighter_id,
            "winner_id": "" if method in ("Draw", "No Contest") else winner.fighter_id,
            "loser_id": "" if method in ("Draw", "No Contest") else loser.fighter_id,
            "method": method, "round": round_no, "scorecards": scorecards,
            "stats": {"a": deepcopy(a.last_fight_stats), "b": deepcopy(b.last_fight_stats)},
            "position_ticks": {}, "events": events,
            "trace": deepcopy(list(getattr(native_result, "trace", ()) or ())),
        }
        for event in events:
            position = event["position_before"]
            result["position_ticks"][position] = result["position_ticks"].get(position, 0) + 1
        result["signature"] = fight_signature(result)
        return result
    finally:
        engine.resolve_exchange = original_resolver
        random.setstate(original_rng)


def fight_signature(result):
    payload = {
        "winner_id": result.get("winner_id", ""), "method": result.get("method"),
        "round": result.get("round"), "scorecards": result.get("scorecards", []),
        "stats": result.get("stats", {}),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def matchup_specs():
    """Stable realistic-card corpus with competitive and mismatch groups."""
    tiers = {"Low": (58, 62), "Mid": (70, 75), "High": (83, 88)}
    styles = BASELINE_STYLES
    specs = []
    for tier, (low, high) in tiers.items():
        for index, style in enumerate(styles):
            opponent_style = styles[(index + 3) % len(styles)]
            specs.append({
                "id": f"{tier.lower()}-competitive-{index + 1}", "tier": tier,
                "matchup": "Competitive", "a_level": low + index % 3,
                "b_level": min(high, low + (index + 1) % 4),
                "a_style": style, "b_style": opponent_style,
                "a_behaviour": BEHAVIOURS[index % len(BEHAVIOURS)],
                "b_behaviour": BEHAVIOURS[(index + 4) % len(BEHAVIOURS)],
                "fight": {"title": index % 7 == 0, "main": index % 5 == 0},
            })
    for index, style in enumerate(styles):
        specs.append({
            "id": f"mismatch-{index + 1}", "tier": "Mixed", "matchup": "Mismatch",
            "a_level": 84 + index % 4, "b_level": 58 + index % 4,
            "a_style": style, "b_style": styles[(index + 5) % len(styles)],
            "a_behaviour": BEHAVIOURS[index % len(BEHAVIOURS)],
            "b_behaviour": BEHAVIOURS[(index + 2) % len(BEHAVIOURS)],
            "fight": {"title": False, "main": index % 4 == 0},
        })
    return specs


def move_report_specs():
    """Retain the frozen corpus while sampling every supported style."""
    specs = list(matchup_specs())
    baseline = set(BASELINE_STYLES)
    for index, style in enumerate(name for name in STYLE_PROFILES if name not in baseline):
        specs.append({
            "id": f"style-coverage-{index + 1}", "tier": "Style coverage",
            "matchup": "Competitive", "a_level": 76, "b_level": 75,
            "a_style": style, "b_style": "MMA Generalist",
            "a_behaviour": BEHAVIOURS[index % len(BEHAVIOURS)],
            "b_behaviour": BEHAVIOURS[(index + 3) % len(BEHAVIOURS)],
            "fight": {"title": False, "main": index % 3 == 0},
        })
    specs.extend((
        {
            "id": "stance-coverage-closed", "tier": "Stance coverage", "matchup": "Competitive",
            "a_level": 76, "b_level": 75, "a_style": "Boxer", "b_style": "Kickboxer",
            "a_behaviour": "Counter", "b_behaviour": "Pressure",
            "a_stance": "Orthodox", "b_stance": "Orthodox", "fight": {"title": False, "main": False},
        },
        {
            "id": "stance-coverage-switch", "tier": "Stance coverage", "matchup": "Competitive",
            "a_level": 76, "b_level": 75, "a_style": "Karate", "b_style": "Wrestler",
            "a_behaviour": "Dynamic Attacker", "b_behaviour": "Control",
            "a_stance": "Switch", "b_stance": "Orthodox", "fight": {"title": False, "main": False},
        },
    ))
    return specs


def Wilson_interval(successes, total, z=1.96):
    if total <= 0:
        return [0.0, 0.0]
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return [round(max(0, centre - margin) * 100, 2), round(min(1, centre + margin) * 100, 2)]


def summarize_results(results):
    groups = {}

    def add(group, result):
        row = groups.setdefault(group, {
            "total": 0, "finishes": 0, "methods": {}, "rounds": {},
            "families": {}, "finish_timing": {"Early": 0, "Middle": 0, "Late": 0},
        })
        row["total"] += 1
        method = result["method"]
        row["methods"][method] = row["methods"].get(method, 0) + 1
        family = METHOD_FAMILIES.get(method, "Other finish")
        row["families"][family] = row["families"].get(family, 0) + 1
        row["rounds"][str(result["round"])] = row["rounds"].get(str(result["round"]), 0) + 1
        if method in FINISH_METHODS:
            row["finishes"] += 1
            scheduled = max(1, int(result.get("scheduled_rounds", 3)))
            progress = result["round"] / scheduled
            timing = "Early" if progress <= 1 / 3 else "Middle" if progress <= 2 / 3 else "Late"
            row["finish_timing"][timing] += 1

    for result in results:
        add("Overall", result)
        if int(result.get("scheduled_rounds", 3) or 3) == 5:
            add("Five Round", result)
        add(result["matchup"], result)
        if result["matchup"] == "Competitive":
            add(f"Competitive {result['tier']}", result)
        add(f"Style {result['a_style']} vs {result['b_style']}", result)
        add(f"Behaviour {result['a_behaviour']} vs {result['b_behaviour']}", result)
    for row in groups.values():
        row["finish_pct"] = round(row["finishes"] / max(1, row["total"]) * 100, 2)
        row["finish_ci95"] = Wilson_interval(row["finishes"], row["total"])
        row["method_pct"] = {
            method: round(count / row["total"] * 100, 2)
            for method, count in sorted(row["methods"].items())
        }
        row["family_pct"] = {
            family: round(count / row["total"] * 100, 2)
            for family, count in sorted(row["families"].items())
        }
        row["finish_timing_pct"] = {
            timing: round(count / row["total"] * 100, 2)
            for timing, count in row["finish_timing"].items()
        }
        row["finish_timing_share_pct"] = {
            timing: round(count / max(1, row["finishes"]) * 100, 2)
            for timing, count in row["finish_timing"].items()
        }
    return groups


def build_baseline(seeds_per_matchup=120):
    engine = FightAuditHarness()
    results = []
    parity = []
    for spec_index, spec in enumerate(matchup_specs()):
        a = synthetic_fighter(
            f"Audit {spec['id']} A", spec["a_level"], spec["a_style"], spec["a_behaviour"], 0,
        )
        b = synthetic_fighter(
            f"Audit {spec['id']} B", spec["b_level"], spec["b_style"], spec["b_behaviour"], 1,
        )
        for seed_index in range(int(seeds_per_matchup)):
            seed = 8_210_000 + spec_index * 10_000 + seed_index
            audited = run_audited_fight(engine, a, b, seed, spec["fight"])
            row = {
                "spec_id": spec["id"], "seed": seed, "tier": spec["tier"],
                "matchup": spec["matchup"], "a_style": spec["a_style"],
                "b_style": spec["b_style"], "a_behaviour": spec["a_behaviour"],
                "b_behaviour": spec["b_behaviour"], "method": audited["method"],
                "round": audited["round"], "winner_id": audited["winner_id"],
                "scheduled_rounds": 5 if spec["fight"].get("title") or spec["fight"].get("main") else 3,
            }
            results.append(row)
            parity.append({**row, "signature": audited["signature"]})
    return {
        "schema_version": BASELINE_SCHEMA_VERSION,
        "seeds_per_matchup": int(seeds_per_matchup),
        "matchup_count": len(matchup_specs()), "fight_count": len(results),
        "groups": summarize_results(results), "parity": parity,
    }


def build_action_baseline(seeds_per_matchup=120):
    """Summarize pre-expansion action use from the accepted fixed corpus."""
    engine = FightAuditHarness()
    actions = {}
    styles = {}

    def row_for(collection, key):
        return collection.setdefault(key, {
            "exchanges": 0, "effective": 0, "finishing_exchanges": 0,
            "strike_attempts": 0, "strikes_landed": 0,
            "takedown_attempts": 0, "takedowns": 0, "submission_attempts": 0,
            "knockdowns": 0, "damage": 0.0, "energy_spent": 0.0,
            "counter_windows": 0, "counters_consumed": 0, "positions": {},
        })

    for spec_index, spec in enumerate(matchup_specs()):
        a = synthetic_fighter(
            f"Audit {spec['id']} A", spec["a_level"], spec["a_style"], spec["a_behaviour"], 0,
        )
        b = synthetic_fighter(
            f"Audit {spec['id']} B", spec["b_level"], spec["b_style"], spec["b_behaviour"], 1,
        )
        corner_styles = {"a": spec["a_style"], "b": spec["b_style"]}
        for seed_index in range(int(seeds_per_matchup)):
            seed = 8_210_000 + spec_index * 10_000 + seed_index
            audited = run_audited_fight(engine, a, b, seed, spec["fight"])
            for event in audited["trace"]:
                if event.get("type") != "exchange":
                    continue
                actor = event.get("actor", "")
                action = str(event.get("action", "generic") or "generic")
                rows = (row_for(actions, action), row_for(styles, corner_styles.get(actor, "Unknown")))
                for row in rows:
                    row["exchanges"] += 1
                    row["effective"] += int(event.get("outcome") in {
                        "landed", "knockdown", "takedown", "submission_attempt", "position_change",
                    })
                    row["finishing_exchanges"] += int(bool(event.get("stoppage")))
                    row["strike_attempts"] += int(event.get("sig_att_delta", 0))
                    row["strikes_landed"] += int(event.get("sig_delta", 0))
                    row["takedown_attempts"] += int(event.get("td_att_delta", 0))
                    row["takedowns"] += int(event.get("td_delta", 0))
                    row["submission_attempts"] += int(event.get("sub_att_delta", 0))
                    row["knockdowns"] += sum(int(value) for value in event.get("knockdown_delta", {}).values())
                    row["damage"] += sum(max(0.0, float(value)) for value in event.get("damage_delta", {}).values())
                    row["energy_spent"] += max(0.0, -float(event.get("gas_delta", {}).get(actor, 0)))
                    flags = event.get("flags", {})
                    row["counter_windows"] += int(bool(flags.get("counter_window")))
                    row["counters_consumed"] += int(bool(flags.get("counter_consumed")))
                    position = str(event.get("position_before", "unknown") or "unknown")
                    row["positions"][position] = row["positions"].get(position, 0) + 1

    def finalize(collection):
        for row in collection.values():
            total = max(1, row["exchanges"])
            row["effective_pct"] = round(row["effective"] / total * 100, 2)
            row["finish_pct_per_exchange"] = round(row["finishing_exchanges"] / total * 100, 3)
            row["damage"] = round(row["damage"], 2)
            row["energy_spent"] = round(row["energy_spent"], 2)
            row["positions"] = dict(sorted(row["positions"].items()))
        return dict(sorted(collection.items()))

    return {
        "schema_version": 1,
        "seeds_per_matchup": int(seeds_per_matchup),
        "matchup_count": len(matchup_specs()),
        "fight_count": len(matchup_specs()) * int(seeds_per_matchup),
        "actions": finalize(actions),
        "styles": finalize(styles),
    }


def build_move_report(seeds_per_matchup=20, minimum_group_sample=30):
    """Build a deterministic move-usage and registry-safety release report.

    This is intentionally separate from the frozen action baseline: adding or
    rebalancing trace-level techniques should change this report without
    rewriting the accepted broad-action comparison surface.
    """
    engine = FightAuditHarness()
    moves = {}
    defenses = {}
    group_rows = {
        dimension: {} for dimension in ("styles", "behaviours", "tiers", "stances", "stance_matchups")
    }
    illegal_counter_uses = []
    illegal_position_uses = []
    illegal_target_uses = []

    def add_row(collection, key, move_id, effective):
        row = collection.setdefault(key, {"attempts": 0, "effective": 0, "moves": {}})
        row["attempts"] += 1
        row["effective"] += int(effective)
        move_row = row["moves"].setdefault(move_id, {"attempts": 0, "effective": 0})
        move_row["attempts"] += 1
        move_row["effective"] += int(effective)

    report_specs = move_report_specs()
    for spec_index, spec in enumerate(report_specs):
        a = synthetic_fighter(
            f"Move audit {spec['id']} A", spec["a_level"], spec["a_style"], spec["a_behaviour"], 0,
        )
        b = synthetic_fighter(
            f"Move audit {spec['id']} B", spec["b_level"], spec["b_style"], spec["b_behaviour"], 1,
        )
        a.stance = spec.get("a_stance", a.stance)
        b.stance = spec.get("b_stance", b.stance)
        corner_context = {
            "a": {"style": a.style, "behaviour": a.behaviour, "stance": a.stance},
            "b": {"style": b.style, "behaviour": b.behaviour, "stance": b.stance},
        }
        stance_matchup = (
            "switch" if "Switch" in (a.stance, b.stance)
            else "open" if {a.stance, b.stance} == {"Orthodox", "Southpaw"}
            else "closed"
        )
        for seed_index in range(int(seeds_per_matchup)):
            seed = 9_310_000 + spec_index * 10_000 + seed_index
            audited = run_audited_fight(engine, a, b, seed, spec["fight"])
            for trace_index, event in enumerate(audited["trace"]):
                if event.get("type") != "exchange":
                    continue
                move_id = str(event.get("move_id", "") or "")
                definition = MOVE_REGISTRY.get(move_id)
                if definition is None:
                    continue
                actor = str(event.get("actor", "") or "")
                defense_id = str(event.get("defense_id", "") or "generic_defense")
                defense_row = defenses.setdefault(defense_id, {"attempts": 0, "successful": 0})
                defense_row["attempts"] += 1
                defense_row["successful"] += int(event.get("outcome") in {"defended", "control"})
                context = corner_context.get(actor, {})
                effective = event.get("outcome") in {
                    "landed", "knockdown", "takedown", "submission_attempt", "position_change",
                }
                row = moves.setdefault(move_id, {
                    "name": definition.name, "family": event.get("move_family", "Other"),
                    "parent_action": definition.parent_action, "attempts": 0, "effective": 0,
                    "finishes": 0, "competitive_attempts": 0, "mismatch_attempts": 0,
                    "counter_uses": 0, "positions": {}, "targets": {},
                })
                row["attempts"] += 1
                row["effective"] += int(effective)
                row["finishes"] += int(bool(event.get("stoppage")))
                row[f"{spec['matchup'].lower()}_attempts"] += 1
                row["counter_uses"] += int(bool(event.get("counter")))
                position = str(event.get("position_before", "unknown") or "unknown")
                target = str(event.get("move", {}).get("target", "") or "none")
                row["positions"][position] = row["positions"].get(position, 0) + 1
                row["targets"][target] = row["targets"].get(target, 0) + 1
                add_row(group_rows["styles"], context.get("style", "Unknown"), move_id, effective)
                add_row(group_rows["behaviours"], context.get("behaviour", "Unknown"), move_id, effective)
                add_row(group_rows["tiers"], spec["tier"], move_id, effective)
                add_row(group_rows["stances"], context.get("stance", "Unknown"), move_id, effective)
                add_row(group_rows["stance_matchups"], stance_matchup, move_id, effective)

                evidence = {"spec_id": spec["id"], "seed": seed, "trace_index": trace_index, "move_id": move_id}
                if "counter" in definition.tags and not event.get("counter"):
                    illegal_counter_uses.append(evidence)
                if definition.positions and position not in definition.positions:
                    illegal_position_uses.append({**evidence, "position": position})
                if definition.targets and target not in definition.targets:
                    illegal_target_uses.append({**evidence, "target": target})

    for row in moves.values():
        row["effective_pct"] = round(row["effective"] / max(1, row["attempts"]) * 100, 2)
        row["positions"] = dict(sorted(row["positions"].items()))
        row["targets"] = dict(sorted(row["targets"].items()))

    for collection in group_rows.values():
        for row in collection.values():
            row["effective_pct"] = round(row["effective"] / max(1, row["attempts"]) * 100, 2)
            row["sample_ok"] = row["attempts"] >= int(minimum_group_sample)
            for move_row in row["moves"].values():
                move_row["effective_pct"] = round(
                    move_row["effective"] / max(1, move_row["attempts"]) * 100, 2,
                )
            row["moves"] = dict(sorted(row["moves"].items()))

    for row in group_rows["styles"].values():
        family_counts = {}
        for move_id, move_row in row["moves"].items():
            family = moves.get(move_id, {}).get("family", "Other")
            family_counts[family] = family_counts.get(family, 0) + move_row["attempts"]
        row["move_family_pct"] = {
            family: round(count / max(1, row["attempts"]) * 100, 2)
            for family, count in sorted(family_counts.items())
        }
        row["top_moves"] = [
            {"move_id": move_id, "attempts": move_row["attempts"]}
            for move_id, move_row in sorted(
                row["moves"].items(), key=lambda item: (-item[1]["attempts"], item[0]),
            )[:5]
        ]

    style_distances = {}
    indistinct_style_pairs = []
    style_names = sorted(group_rows["styles"])
    for index, style_a in enumerate(style_names):
        row_a = group_rows["styles"][style_a]
        for style_b in style_names[index + 1:]:
            row_b = group_rows["styles"][style_b]
            move_ids = set(row_a["moves"]) | set(row_b["moves"])
            distance = 50 * sum(abs(
                row_a["moves"].get(move_id, {}).get("attempts", 0) / max(1, row_a["attempts"])
                - row_b["moves"].get(move_id, {}).get("attempts", 0) / max(1, row_b["attempts"])
            ) for move_id in move_ids)
            key = f"{style_a} vs {style_b}"
            style_distances[key] = round(distance, 2)
            if distance < 5:
                indistinct_style_pairs.append({"styles": [style_a, style_b], "distance_pct": round(distance, 2)})

    dominant_moves = []
    action_position_totals = {}
    for row in moves.values():
        for position, attempts in row["positions"].items():
            key = (row["parent_action"], position)
            action_position_totals[key] = action_position_totals.get(key, 0) + attempts
    for move_id, row in moves.items():
        parent = row["parent_action"]
        for position, attempts in row["positions"].items():
            total = action_position_totals.get((parent, position), 0)
            legal_alternatives = sum(
                1 for definition in MOVE_REGISTRY.values()
                if definition.parent_action == parent
                and (not definition.positions or position in definition.positions)
            )
            if legal_alternatives > 1 and total >= minimum_group_sample:
                share = attempts / total * 100
                if share > 85:
                    dominant_moves.append({
                        "move_id": move_id, "parent_action": parent,
                        "position": position, "share_pct": round(share, 2),
                    })

    unreachable_registry_moves = []
    reachability_artist = synthetic_fighter(
        "Move audit reachability specialist", 94, "MMA Generalist", "Dynamic Attacker", 0,
    )
    reachability_opponent = synthetic_fighter(
        "Move audit reachability opponent", 94, "MMA Generalist", "Dynamic Attacker", 1,
    )
    reachability_artist.detailed_skills = {
        key: 99 for key in reachability_artist.detailed_skills
    }
    for definition in MOVE_REGISTRY.values():
        reachability_artist.style = (
            definition.preferred_styles[0]
            if definition.preferred_styles else "MMA Generalist"
        )
        reachability_artist.secondary_style = ""
        reachability_artist.signature_moves = [definition.move_id]
        selected = False
        for tick in range(1, 321):
            state = {"round": 2, "tick": tick, "plans": {}, "move_reads": {}, "counter_window": None}
            if "counter" in definition.tags:
                state["counter_window"] = {"fighter": reachability_artist.name}
            target = sorted(definition.targets)[0] if definition.targets else ""
            position = sorted(definition.positions)[0] if definition.positions else "range"
            move = engine.select_exchange_move(
                reachability_artist, reachability_opponent, definition.parent_action,
                position, target, state,
            )
            if move["move_id"] == definition.move_id:
                selected = True
                break
        if not selected:
            unreachable_registry_moves.append(definition.move_id)

    unreachable_defense_ids = []
    for definition in DEFENSE_REGISTRY.values():
        reachability_opponent.move_mastery = {f"defense:{definition.defense_id}": 100}
        selected = False
        for tick in range(1, 80):
            defense = engine.select_exchange_defense(
                reachability_opponent,
                {"defense_families": definition.families, "tags": ()},
                sorted(definition.positions)[0],
                {"round": 1, "tick": tick, "plans": {}},
            )
            if defense["defense_id"] == definition.defense_id:
                selected = True
                break
        if not selected:
            unreachable_defense_ids.append(definition.defense_id)

    registered = set(MOVE_REGISTRY)
    observed = set(moves)
    diagnostics = {
        "dead_moves_in_sample": sorted(registered - observed),
        "unreachable_registry_moves": sorted(unreachable_registry_moves),
        "dominant_moves": sorted(dominant_moves, key=lambda item: item["move_id"]),
        "mismatch_only_moves": sorted(
            move_id for move_id, row in moves.items()
            if row["mismatch_attempts"] and not row["competitive_attempts"]
        ),
        "illegal_counter_uses": illegal_counter_uses,
        "illegal_position_uses": illegal_position_uses,
        "illegal_target_uses": illegal_target_uses,
        "unsafe_energy_moves": sorted(
            move_id for move_id, definition in MOVE_REGISTRY.items()
            if not 0.75 <= float(definition.energy) <= 1.75
        ),
        "indistinct_style_pairs": indistinct_style_pairs,
        "unknown_defense_ids": sorted(defense_id for defense_id in defenses if defense_id not in DEFENSE_REGISTRY),
        "unreachable_defense_ids": sorted(unreachable_defense_ids),
    }
    return {
        "schema_version": 1,
        "seeds_per_matchup": int(seeds_per_matchup),
        "minimum_group_sample": int(minimum_group_sample),
        "matchup_count": len(report_specs),
        "fight_count": len(report_specs) * int(seeds_per_matchup),
        "registered_move_count": len(registered),
        "observed_move_count": len(observed),
        "registered_defense_count": len(DEFENSE_REGISTRY),
        "observed_defense_count": len(set(defenses).intersection(DEFENSE_REGISTRY)),
        "defenses": dict(sorted(defenses.items())),
        "moves": dict(sorted(moves.items())),
        "groups": {
            dimension: dict(sorted(collection.items()))
            for dimension, collection in group_rows.items()
        },
        "diagnostics": diagnostics,
        "style_identity_distances": dict(sorted(style_distances.items())),
    }


def specialist_transition_specs():
    """Purpose-built full-fight matchups for rare multi-step positions."""
    return (
        {
            "id": "failed-shot-front-headlock", "required_positions": ("failed shot", "front headlock"),
            "required_actions": ("front_headlock", "re_shot", "recover_shot"),
            "a": {"style": "Wrestler", "behaviour": "Control", "level": 74,
                  "broad": {"wrestling": 76},
                  "skills": {"takedowns": 76, "takedown_speed": 42, "takedown_setup": 38,
                             "chain_wrestling": 38, "sprawl": 44}},
            "b": {"style": "Catch Wrestler", "behaviour": "Counter", "level": 80,
                  "broad": {"wrestling": 96, "takedown_defence": 97},
                  "skills": {"sprawl": 99, "front_headlock": 99, "clinch_control": 96,
                             "chain_wrestling": 92, "submission_attack": 94}},
        },
        {
            "id": "standing-back-control", "required_positions": ("standing back control",),
            "required_actions": ("mat_return", "standing_back_ride", "standing_escape"),
            "a": {"style": "Wrestler", "behaviour": "Control", "level": 88,
                  "broad": {"wrestling": 98, "grappling": 98},
                  "skills": {"clinch_control": 99, "cage_wrestling": 99, "cage_pressure": 99,
                             "back_control": 99, "ride_control": 98, "strength": 97}},
            "b": {"style": "Boxer", "behaviour": "Cautious", "level": 64,
                  "broad": {"takedown_defence": 45, "grappling": 45},
                  "skills": {"clinch_defence": 42, "scrambles": 50, "get_ups": 50}},
        },
        {
            "id": "leg-entanglement", "required_positions": ("leg entanglement",),
            "required_actions": ("leg_attack", "counter_leg_lock", "leg_escape"),
            "a": {"style": "Luta Livre", "behaviour": "Submission Hunter", "level": 89,
                  "trait": "Submission Ace", "broad": {"wrestling": 30, "takedown_defence": 25,
                                                            "grappling": 98, "submissions": 98},
                  "skills": {"leg_locks": 99, "submission_attack": 99, "guard_work": 98,
                             "positional_ability": 96, "transitions": 98, "sprawl": 25,
                             "takedown_defence_detail": 25}},
            "b": {"style": "Wrestler", "behaviour": "Control", "level": 69,
                  "broad": {"wrestling": 98, "submission_defence": 45},
                  "skills": {"takedowns": 99, "takedown_speed": 99, "takedown_setup": 99,
                             "chain_wrestling": 98, "submission_defence_detail": 42,
                             "top_control": 72, "scrambles": 54}},
        },
    )


def build_specialist_transition_report(seeds_per_matchup=240):
    """Exercise rare positions in complete fights without mutating a career."""
    engine = FightAuditHarness()
    scenarios = {}
    all_positions = {}
    all_actions = {}
    all_moves = {}
    for spec_index, spec in enumerate(specialist_transition_specs()):
        fighters = []
        for corner, slot in enumerate(("a", "b")):
            settings = spec[slot]
            fighter = synthetic_fighter(
                f"Transition {spec['id']} {slot.upper()}", settings["level"],
                settings["style"], settings["behaviour"], corner,
            )
            for key, value in settings.get("broad", {}).items():
                setattr(fighter, key, value)
            fighter.detailed_skills.update(settings.get("skills", {}))
            fighter.trait = settings.get("trait", fighter.trait)
            fighters.append(fighter)
        row = {"fights": int(seeds_per_matchup), "positions": {}, "actions": {}, "moves": {}}
        for seed_index in range(int(seeds_per_matchup)):
            audited = run_audited_fight(
                engine, fighters[0], fighters[1],
                10_410_000 + spec_index * 10_000 + seed_index,
            )
            for event in audited["trace"]:
                if event.get("type") != "exchange":
                    continue
                action = str(event.get("action", "") or "")
                move_id = str(event.get("move_id", "") or "")
                positions = set(event.get("position_path", ()) or ())
                positions.update((event.get("position_before"), event.get("position_after")))
                for position in positions - {None, ""}:
                    row["positions"][position] = row["positions"].get(position, 0) + 1
                    all_positions[position] = all_positions.get(position, 0) + 1
                row["actions"][action] = row["actions"].get(action, 0) + 1
                row["moves"][move_id] = row["moves"].get(move_id, 0) + 1
                all_actions[action] = all_actions.get(action, 0) + 1
                all_moves[move_id] = all_moves.get(move_id, 0) + 1
        row["positions"] = dict(sorted(row["positions"].items()))
        row["actions"] = dict(sorted(row["actions"].items()))
        row["moves"] = dict(sorted(row["moves"].items()))
        row["required_position_hits"] = {
            position: row["positions"].get(position, 0) for position in spec["required_positions"]
        }
        row["required_action_hits"] = {
            action: row["actions"].get(action, 0) for action in spec["required_actions"]
        }
        scenarios[spec["id"]] = row
    missing_positions = sorted(
        f"{spec['id']}:{position}"
        for spec in specialist_transition_specs()
        for position in spec["required_positions"]
        if not scenarios[spec["id"]]["required_position_hits"][position]
    )
    missing_action_families = sorted(
        spec["id"] for spec in specialist_transition_specs()
        if not any(scenarios[spec["id"]]["required_action_hits"].values())
    )
    return {
        "schema_version": 1,
        "seeds_per_matchup": int(seeds_per_matchup),
        "fight_count": len(specialist_transition_specs()) * int(seeds_per_matchup),
        "scenarios": scenarios,
        "totals": {
            "positions": dict(sorted(all_positions.items())),
            "actions": dict(sorted(all_actions.items())),
            "moves": dict(sorted(all_moves.items())),
        },
        "diagnostics": {
            "missing_required_positions": missing_positions,
            "missing_required_action_families": missing_action_families,
        },
    }


def write_baseline(path, seeds_per_matchup=120):
    payload = build_baseline(seeds_per_matchup)
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def compare_to_baseline(current, baseline, exact_parity=False):
    """Return human-readable preservation failures for one generated audit."""
    failures = []
    current_groups = current.get("groups", {})
    baseline_groups = baseline.get("groups", {})

    def difference(group, field, key=None):
        current_row = current_groups.get(group, {})
        baseline_row = baseline_groups.get(group, {})
        current_value = current_row.get(field, {}) if key is not None else current_row.get(field)
        baseline_value = baseline_row.get(field, {}) if key is not None else baseline_row.get(field)
        if key is not None:
            current_value = current_value.get(key, 0)
            baseline_value = baseline_value.get(key, 0)
        if current_value is None or baseline_value is None:
            failures.append(f"Missing {group} {field}{' ' + key if key else ''} baseline evidence")
            return 0
        return abs(float(current_value) - float(baseline_value))

    def confidence_intervals_overlap(group):
        current_ci = current_groups.get(group, {}).get("finish_ci95", [0, 0])
        baseline_ci = baseline_groups.get(group, {}).get("finish_ci95", [0, 0])
        return max(float(current_ci[0]), float(baseline_ci[0])) <= min(float(current_ci[1]), float(baseline_ci[1]))

    if difference("Overall", "finish_pct") > 1.0:
        failures.append("Overall finish rate moved by more than 1.0 percentage point")
    for method in ("KO", "TKO"):
        if difference("Overall", "method_pct", method) > 1.0:
            failures.append(f"{method} rate moved by more than 1.0 percentage point")
    for tier in ("Low", "Mid", "High"):
        group = f"Competitive {tier}"
        if difference(group, "finish_pct") > 1.5 and not confidence_intervals_overlap(group):
            failures.append(f"Competitive {tier} finish rate moved by more than 1.5 percentage points")
    current_gap = current_groups.get("Mismatch", {}).get("finish_pct", 0) - current_groups.get("Competitive", {}).get("finish_pct", 0)
    baseline_gap = baseline_groups.get("Mismatch", {}).get("finish_pct", 0) - baseline_groups.get("Competitive", {}).get("finish_pct", 0)
    if (abs(current_gap - baseline_gap) > 1.5
            and not confidence_intervals_overlap("Mismatch")):
        failures.append("Competitive-to-mismatch finish-rate gap moved by more than 1.5 percentage points")
    for family in ("KO/TKO", "Submission"):
        if difference("Overall", "family_pct", family) > 2.0:
            failures.append(f"{family} family share moved by more than 2.0 percentage points")
    for timing in ("Early", "Middle", "Late"):
        if difference("Overall", "finish_timing_pct", timing) > 2.0:
            failures.append(f"{timing} finish timing moved by more than 2.0 percentage points")
    for group, baseline_row in baseline_groups.items():
        if not group.startswith(("Style ", "Behaviour ")) or baseline_row.get("total", 0) < 100:
            continue
        if difference(group, "finish_pct") > 3.0 and not confidence_intervals_overlap(group):
            failures.append(f"{group} finish rate moved by more than 3.0 percentage points")
    if exact_parity:
        expected = {(row["spec_id"], row["seed"]): row["signature"] for row in baseline.get("parity", [])}
        actual = {(row["spec_id"], row["seed"]): row["signature"] for row in current.get("parity", [])}
        missing = sorted(set(expected) - set(actual))
        changed = sorted(key for key, signature in expected.items() if actual.get(key) != signature)
        if missing:
            failures.append(f"Exact parity audit omitted {len(missing)} baseline bouts")
        if changed:
            failures.append(f"Exact parity changed {len(changed)} of {len(expected)} baseline bouts")
    return failures


def compare_to_accepted_calibration(current):
    """Reject any change to the approved 3,840-bout headline calibration.

    The older preservation baseline remains useful for distribution tolerances,
    but the accepted post-roadmap result is now an exact release invariant.  It
    is expressed as integer counts first so a rounded percentage cannot hide a
    one-bout change.
    """
    expected = ACCEPTED_RESULT_CALIBRATION
    overall = (current.get("groups", {}) or {}).get("Overall", {}) or {}
    failures = []
    total = int(overall.get("total", current.get("fight_count", 0)) or 0)
    finishes = int(overall.get("finishes", 0) or 0)
    methods = overall.get("methods", {}) or {}
    if total != expected["fight_count"]:
        failures.append(
            f"Accepted calibration requires {expected['fight_count']} fights; current audit has {total}"
        )
    if finishes != expected["finishes"]:
        failures.append(
            f"Accepted finish count changed from {expected['finishes']} to {finishes}"
        )
    for method, expected_count in expected["methods"].items():
        current_count = int(methods.get(method, 0) or 0)
        if current_count != expected_count:
            failures.append(
                f"Accepted {method} count changed from {expected_count} to {current_count}"
            )
    for reachable_method in ("Doctor Stoppage", "Injury Stoppage"):
        if int(methods.get(reachable_method, 0) or 0) <= 0:
            failures.append(f"{reachable_method} became unreachable in the accepted corpus")
    competitive = (current.get("groups", {}) or {}).get("Competitive", {}) or {}
    competitive_total = int(competitive.get("total", 0) or 0)
    competitive_finishes = int(competitive.get("finishes", 0) or 0)
    competitive_methods = competitive.get("methods", {}) or {}
    if competitive_total <= 0:
        failures.append("Accepted calibration omitted competitive fights")
    else:
        competitive_finish_pct = competitive_finishes / competitive_total * 100
        competitive_sub_pct = sum(
            int(competitive_methods.get(method, 0) or 0) for method in SUBMISSION_METHODS
        ) / competitive_total * 100
        if not 48.0 <= competitive_finish_pct <= 54.0:
            failures.append(
                f"Competitive finish rate is {competitive_finish_pct:.2f}%; expected 48.00-54.00%"
            )
        if not 15.0 <= competitive_sub_pct <= 19.0:
            failures.append(
                f"Competitive submission rate is {competitive_sub_pct:.2f}%; expected 15.00-19.00%"
            )
    five_round = (current.get("groups", {}) or {}).get("Five Round", {}) or {}
    late_share = float((five_round.get("finish_timing_share_pct", {}) or {}).get("Late", 0) or 0)
    if int(five_round.get("total", 0) or 0) <= 0:
        failures.append("Accepted calibration omitted five-round fights")
    elif late_share < 6.0:
        failures.append(
            f"Rounds 4-5 produced only {late_share:.2f}% of five-round finishes; minimum is 6.00%"
        )
    if total:
        observed_rates = {
            "finish_pct": round(finishes / total * 100, 2),
            "KO": round(int(methods.get("KO", 0) or 0) / total * 100, 2),
            "TKO": round(int(methods.get("TKO", 0) or 0) / total * 100, 2),
        }
        for key, expected_rate in expected["rates"].items():
            if observed_rates[key] != expected_rate:
                failures.append(
                    f"Accepted {key} changed from {expected_rate:.2f}% to {observed_rates[key]:.2f}%"
                )
    return failures


def detailed_skill_usage(source_text):
    usage = {}
    for group, keys in DETAILED_SKILL_GROUPS.items():
        for key in keys:
            if key in PREFIGHT_DETAILED_SKILLS:
                usage[key] = {"group": group, "usage": "pre-fight", "evidence": PREFIGHT_DETAILED_SKILLS[key]}
            else:
                usage[key] = {
                    "group": group, "usage": "direct" if key in source_text else "missing",
                    "evidence": "Referenced by MMA action selection/resolution." if key in source_text else "No fight-engine reference.",
                }
    return usage
