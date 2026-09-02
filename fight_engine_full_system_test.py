"""Broad deterministic integration stress test for the upgraded MMA fight engine.

This complements the narrow regressions with complete bouts across every fight
plan, major style family, same-name identity, and 3/5/6/7-round rules. It checks
the structured trace against the final box score rather than merely accepting a
plausible-looking result.
"""

import random

from constants import FIGHT_PLANS, STYLES
from fight_engine_audit import FINISH_METHODS, FightAuditHarness, run_audited_fight, synthetic_fighter
import test_support


DECISION_METHODS = {"Decision", "Technical Decision", "Draw", "No Contest"}
VALID_METHODS = FINISH_METHODS | DECISION_METHODS
CORE_ACTIONS = {
    "jab", "power_punch", "kick", "shoot", "clinch",
    "dirty_boxing", "takedown", "cage_control", "break_clinch",
    "ground_control", "ground_strikes", "advance_position", "submission",
    "recover_guard", "sweep", "bottom_submission", "cling", "stand_up",
}
STYLE_MATCHUPS = (
    ("Boxer", "Wrestler", "Pressure", "Control"),
    ("Kickboxer", "BJJ", "Volume", "Submission Hunter"),
    ("Muay Thai", "Judo", "Pressure", "Dynamic Attacker"),
    ("Karate", "Sambo", "Counter", "Control"),
    ("Wrestler", "Submission Grappler", "Control", "Submission Hunter"),
    ("BJJ", "Boxer", "Submission Hunter", "Sprawl And Brawl"),
    ("MMA Generalist", "Well-Rounded", "Dynamic Attacker", "Cautious"),
    ("Sanda", "Luta Livre", "Counter", "Dynamic Attacker"),
)
RULE_SETS = (
    (3, 3, False),
    (3, 5, True),
    (6, 6, False),
    (7, 7, True),
)


def require(condition, message):
    if not condition:
        raise AssertionError(test_support.contextual_message(message, subsystem=test_support.caller_name()))


def validate_complete_bout(engine, a, b, fight, expected_rounds, action_coverage):
    result = engine.simulate_fight_result(a, b, fight)
    require(result.method in VALID_METHODS, f"Unknown official method: {result.method}")
    require(1 <= result.round_no <= expected_rounds,
            f"Bout ended in round {result.round_no} outside its {expected_rounds}-round rules")
    require(result.commentary and result.trace, "Completed bout omitted commentary or structured trace")
    require(result.trace[-1]["type"] == "official_result", "Trace did not end with one official result")
    require(sum(event.get("type") == "official_result" for event in result.trace) == 1,
            "Trace retained multiple official results")
    require(result.trace[-1]["method"] == result.method,
            "Trace method disagreed with the structured result")
    require(len(result.scorecards) == 3, "Bout did not retain three official scorecards")

    exchanges = list(result.trace[:-1])
    require(exchanges and all(event.get("type") == "exchange" for event in exchanges),
            "Non-exchange evidence appeared before the official result")
    require(all(event.get("stoppage") is None for event in exchanges[:-1]),
            "An exchange occurred after a recorded stoppage")
    # Corner stoppages are made between rounds, so their official-result event
    # is terminal without attaching the decision to the prior exchange.
    if result.method in (FINISH_METHODS - {"Corner Stoppage"}) | {"No Contest", "Technical Decision"}:
        require(exchanges[-1].get("stoppage") is not None,
                f"{result.method} omitted its terminal stoppage evidence")

    totals = {
        key: {"sig": 0, "sig_att": 0, "td": 0, "td_att": 0, "sub_att": 0, "knockdowns": 0}
        for key in ("a", "b")
    }
    for event in exchanges:
        actor = event["actor"]
        defender = event["defender"]
        require({actor, defender} == {"a", "b"}, "Exchange lost corner identity")
        require(1 <= int(event["round"]) <= result.round_no, "Exchange escaped the official round boundary")
        require(event["sig_delta"] <= event["sig_att_delta"], "Exchange landed more strikes than attempted")
        require(event["td_delta"] <= event["td_att_delta"], "Exchange completed more takedowns than attempted")
        require(all(value >= 0 for value in event["damage_delta"].values()), "Exchange healed accumulated damage")
        require(all(value >= 0 for value in event["head_delta"].values()), "Exchange healed accumulated head damage")
        require(all(value >= 0 for value in event["body_delta"].values()), "Exchange healed accumulated body damage")
        require(all(value >= 0 for value in event["leg_delta"].values()), "Exchange healed accumulated leg damage")
        path = event.get("position_path", [])
        require(path and path[0] == event["position_before"] and path[-1] == event["position_after"],
                "Position path disagreed with its exchange endpoints")
        for previous, current in zip(path, path[1:]):
            require(current in engine.ALLOWED_FIGHT_TRANSITIONS.get(previous, ()),
                    f"Illegal recorded transition: {previous} -> {current}")
        action_coverage.add(event["action"])
        move = event.get("move", {})
        require(event.get("move_id") and move.get("parent_action") == event["action"],
                "Exchange omitted a move identity or attached it to the wrong action")
        require(move.get("target", "") in ("", "head", "body", "leg"),
                "Move trace retained an unsupported target")
        totals[actor]["sig"] += event["sig_delta"]
        totals[actor]["sig_att"] += event["sig_att_delta"]
        totals[actor]["td"] += event["td_delta"]
        totals[actor]["td_att"] += event["td_att_delta"]
        totals[actor]["sub_att"] += event["sub_att_delta"]
        for key in ("a", "b"):
            totals[key]["knockdowns"] += event["knockdown_delta"][key]
        if any(event["knockdown_delta"].values()):
            require(event["knockdown_delta"][actor] > 0 and event["knockdown_delta"][defender] == 0,
                    "Knockdown credit was assigned to the wrong corner")
            require(event["outcome"] == "knockdown" and event["flags"]["knockdown"],
                    "Knockdown statistics were not classified as knockdown trace evidence")
        for damage_event in event.get("visible_damage_events", []) or []:
            channel = damage_event.get("channel")
            require(damage_event.get("defender") == defender
                    and damage_event.get("actor") == actor,
                    "Visible damage evidence was assigned to the wrong fighter")
            require(channel in {"head", "body", "leg"}
                    and event[f"{channel}_delta"][defender] > 0,
                    "Visible damage was narrated without fresh trauma in that location")
            require(damage_event.get("move_id") == event.get("move_id"),
                    "Visible damage lost the exchange identity that produced its threshold crossing")

    trace_state = {"trace": exchanges}
    for round_no in {event["round"] for event in exchanges}:
        evidence = engine.round_evidence_from_trace(trace_state, round_no)
        for key in ("a", "b"):
            expected_knockdowns = sum(
                event["knockdown_delta"][key]
                for event in exchanges if event["round"] == round_no
            )
            require(evidence[key]["knockdowns"] == expected_knockdowns,
                    f"Round {round_no} {key} judging evidence credited knockdowns to the wrong corner")

    for key in ("a", "b"):
        stats = result.metrics[key]
        for metric in ("sig", "sig_att", "td", "td_att", "sub_att", "knockdowns"):
            require(stats[metric] == totals[key][metric],
                    f"{key} {metric} box score disagreed with the exchange trace")
        require(stats["damage_taken"] == stats["head_damage"] + stats["body_damage"] + stats["leg_damage"],
                f"{key} visible damage total disagreed with its locations")
        require(stats["cuts"] == len(stats["cut_details"]), f"{key} cut count disagreed with cut evidence")
        trace_damage = [
            damage_event
            for event in exchanges
            for damage_event in (event.get("visible_damage_events", []) or [])
            if damage_event.get("defender") == key
        ]
        require(stats.get("visible_damage", []) == trace_damage,
                f"{key} visible-damage summary disagreed with the chronological trace")
        require(stats["plan_effective_actions"] <= stats["plan_attempts"],
                f"{key} plan credited more effective actions than attempts")

    if result.method in ("Draw", "No Contest"):
        require(not result.winner_id and not result.loser_id, f"{result.method} invented a winner identity")
    else:
        require({result.winner_id, result.loser_id} == {a.fighter_id, b.fighter_id},
                "Official winner/loser identity did not match the two participants")
    if result.method in ("Decision", "Draw"):
        require(all(len(card["a"]) == expected_rounds and len(card["b"]) == expected_rounds
                    for card in result.scorecards),
                "Completed decision did not score every scheduled round")
    return result


def test_full_plan_style_and_round_matrix():
    action_coverage = set()
    methods = set()
    completed = 0
    for rule_index, (regular_rounds, title_rounds, title) in enumerate(RULE_SETS):
        for plan_index, plan in enumerate(FIGHT_PLANS):
            for style_index, (a_style, b_style, a_behaviour, b_behaviour) in enumerate(STYLE_MATCHUPS):
                seed = 510_000 + rule_index * 10_000 + plan_index * 100 + style_index
                engine = FightAuditHarness({"rounds": regular_rounds, "title_rounds": title_rounds})
                a = synthetic_fighter(f"Matrix A {seed}", 58 + (plan_index * 3 + style_index) % 34,
                                      a_style, a_behaviour, 0)
                b = synthetic_fighter(f"Matrix B {seed}", 58 + (plan_index * 5 + style_index * 2) % 34,
                                      b_style, b_behaviour, 1)
                if (plan_index + style_index) % 2 == 0 and b_style != a.style:
                    a.secondary_style = b_style
                if (plan_index + style_index) % 3 == 0 and a_style != b.style:
                    b.secondary_style = a_style
                fight = {
                    "title": title, "main": False,
                    "fight_plans": {a.fighter_id: plan, b.fighter_id: FIGHT_PLANS[-plan_index - 1]},
                }
                random.seed(seed)
                result = validate_complete_bout(
                    engine, a, b, fight, title_rounds if title else regular_rounds, action_coverage,
                )
                require(result.metrics["a"]["fight_plan"] == plan,
                        "Requested red-corner plan was not used")
                require(result.metrics["b"]["fight_plan"] == FIGHT_PLANS[-plan_index - 1],
                        "Requested blue-corner plan was not used")
                require(all(style in STYLES for style in engine.fighter_styles(a)),
                        "Mixed-style red corner lost a supported style identity")
                methods.add(result.method)
                completed += 1
    require(completed == len(RULE_SETS) * len(FIGHT_PLANS) * len(STYLE_MATCHUPS),
            "The full engine matrix skipped a configured bout")
    require(CORE_ACTIONS <= action_coverage,
            "Full engine matrix missed core actions: " + ", ".join(sorted(CORE_ACTIONS - action_coverage)))
    require(methods & {"KO", "TKO"} and methods & {"Submission", "Technical Submission"}
            and "Decision" in methods,
            "Full engine matrix did not exercise striking, submission, and decision results")


def test_same_name_and_extreme_attribute_bouts_remain_identity_safe():
    action_coverage = set()
    for index, (a_level, b_level) in enumerate(((35, 35), (94, 94), (35, 94), (94, 35))):
        engine = FightAuditHarness({"rounds": 3, "title_rounds": 5})
        a = synthetic_fighter("Duplicate Name", a_level, "Boxer", "Pressure", 0)
        b = synthetic_fighter("Duplicate Name", b_level, "BJJ", "Submission Hunter", 1)
        a.fighter_id = f"duplicate-a-{index}"
        b.fighter_id = f"duplicate-b-{index}"
        random.seed(880_000 + index)
        result = validate_complete_bout(engine, a, b, {
            "title": index % 2 == 1,
            "fight_plans": {a.fighter_id: "Counter striking", b.fighter_id: "Submission hunt"},
        }, 5 if index % 2 == 1 else 3, action_coverage)
        if result.method not in ("Draw", "No Contest"):
            require(result.winner_id != result.loser_id,
                    "Same-name result collapsed distinct fighter identities")


def test_audit_adapter_does_not_invent_no_contest_winner():
    engine = FightAuditHarness()
    a = synthetic_fighter("Audit A", 70, "Boxer", "Pressure", 0)
    b = synthetic_fighter("Audit B", 70, "Wrestler", "Control", 1)

    def forced_no_contest(red, blue, _fight):
        red.last_fight_stats = {}
        blue.last_fight_stats = {}
        return red, blue, "No Contest", 1, ["Official result: No Contest"]

    engine.simulate_fight = forced_no_contest
    result = run_audited_fight(engine, a, b, 990_001)
    require(not result["winner_id"] and not result["loser_id"],
            "The audit adapter invented winner/loser IDs for a No Contest")


def _run_suite():
    test_full_plan_style_and_round_matrix()
    test_same_name_and_extreme_attribute_bouts_remain_identity_safe()
    test_audit_adapter_does_not_invent_no_contest_winner()
    print("FIGHT ENGINE FULL SYSTEM TEST PASSED")


def main():
    return test_support.run_suite("fight_engine_full_system", _run_suite)


if __name__ == "__main__":
    main()
