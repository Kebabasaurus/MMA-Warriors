"""Focused deterministic regressions for the MMA fight engine audit surface."""

import json
import random
from copy import deepcopy
from pathlib import Path

from constants import (
    DETAILED_SKILL_GROUPS,
    FIGHT_ENGINE_CONFIG_VERSION,
    FIGHT_PLANS,
    FINISH_METHODS,
    KNOCKOUT_AWARD_METHODS,
    KO_METHODS,
    STYLES,
    SUBMISSION_METHODS,
    TRAITS,
)
from fight_engine import FightEngineMixin, TRAIT_COMMENTARY_INTROS
from events import EventMixin
from fight_moves import DEFENSE_REGISTRY, DEFENSE_REGISTRY_ERRORS, MOVE_REGISTRY, MOVE_REGISTRY_ERRORS
from fight_engine_audit import (
    ACCEPTED_RESULT_CALIBRATION,
    FightAuditHarness,
    build_move_report,
    build_specialist_transition_report,
    compare_to_accepted_calibration, compare_to_baseline, detailed_skill_usage,
    matchup_specs,
    run_audited_fight,
    synthetic_fighter,
)
from world import WorldMixin
from awards import AwardsMixin
from seeding import SeedMixin
import test_support


ROOT = Path(__file__).resolve().parent
BASELINE_PATH = ROOT / "analysis" / "fight_engine_baseline.json"
ACTION_BASELINE_PATH = ROOT / "analysis" / "fight_engine_action_baseline.json"


def require(condition, message):
    if not condition:
        raise AssertionError(test_support.contextual_message(message, subsystem=test_support.caller_name()))


def test_audited_fight_is_deterministic_and_non_mutating():
    engine = FightAuditHarness()
    a = synthetic_fighter("Determinism A", 74, "Boxer", "Counter", 0)
    b = synthetic_fighter("Determinism B", 72, "Wrestler", "Pressure", 1)
    a_before = a.__dict__.copy()
    b_before = b.__dict__.copy()
    random.seed(9917)
    rng_before = random.getstate()
    first = run_audited_fight(engine, a, b, 661201)
    second = run_audited_fight(engine, a, b, 661201)
    require(first == second, "Fixed-seed audited fight was not byte-stable")
    require(a.__dict__ == a_before and b.__dict__ == b_before, "Fight audit mutated an input fighter")
    require(random.getstate() == rng_before, "Fight audit consumed the caller's global RNG")
    require(first["events"] and sum(first["position_ticks"].values()) == len(first["events"]),
            "Fight audit did not retain exchange/position evidence")


def test_trace_metrics_are_internally_consistent():
    engine = FightAuditHarness()
    a = synthetic_fighter("Trace A", 78, "Kickboxer", "Volume", 0)
    b = synthetic_fighter("Trace B", 78, "BJJ", "Submission Hunter", 1)
    result = run_audited_fight(engine, a, b, 771103, {"main": True})
    for corner in ("a", "b"):
        stats = result["stats"][corner]
        require(stats["sig"] <= stats["sig_att"], f"{corner} landed more significant strikes than attempted")
        require(stats["td"] <= stats["td_att"], f"{corner} completed more takedowns than attempted")
        require(all(stats[key] >= 0 for key in ("head_damage", "body_damage", "leg_damage", "cuts")),
                f"{corner} retained negative damage telemetry")
    require(result["method"] in FINISH_METHODS | {"Decision", "Draw"}, "Audit returned an unknown MMA method")
    require(all(event["sig_delta"] <= event["sig_att_delta"] for event in result["events"]),
            "An exchange landed more significant strikes than it attempted")
    native_events = engine._last_fight_result.trace[:-1]
    require(all(event.get("outcome") in {
        "knockdown", "submission_attempt", "takedown", "landed",
        "defended", "position_change", "control",
    } for event in native_events), "A trace exchange omitted its mechanical outcome")
    require(all(isinstance(event.get("commentary"), list) for event in native_events),
            "A trace exchange omitted its rendered commentary list")
    require(all(isinstance(event.get("visible_damage_events"), list)
                and isinstance(event.get("damage_narrative"), list)
                for event in native_events),
            "A trace exchange omitted its structured visible-damage evidence or narrative")
    require(all(set(event.get("flags", {})) == {"hurt", "knockdown", "cut", "position_changed"}
                for event in native_events),
            "A trace exchange omitted its hurt/cut/knockdown/position flags")
    require(all(set(event.get("hurt_delta", {})) == {"a", "b"}
                and set(event.get("cut_events", {})) == {"a", "b"}
                for event in native_events),
            "A trace exchange omitted transient-hurt or structured-cut evidence")
    require(all(set(event.get("exchange", {})) >= {
        "setup", "defensive_response", "counter_opportunity", "counter_consumed",
        "counter_success", "follow_up", "combination", "beats",
    } for event in native_events), "A trace exchange omitted its setup/defense/counter/follow-up chain")
    require(all(len(event["exchange"]["beats"]) <= 5 for event in native_events),
            "An exchange exceeded the bounded mechanical beat budget")
    for event in native_events:
        combination = event["exchange"]["combination"]
        require(sum(1 for strike in combination if strike["landed"]) <= len(combination),
                "Combination evidence landed more strikes than it attempted")
        require([strike["sequence"] for strike in combination] == list(range(1, len(combination) + 1)),
                "Combination evidence lost its individual strike order")
    rendered_events = [engine.render_exchange_trace_event(event) for event in native_events]
    require(all(engine.exchange_display_move(event).casefold() in rendered.casefold()
                for event, rendered in zip(native_events, rendered_events)),
            "Exchange commentary did not name the player-facing move derived from its trace event")
    require(all(" [" not in rendered for rendered in rendered_events),
            "Default exchange commentary leaked a raw technical bracket suffix")
    require(all(event.get("stoppage") is None for event in native_events[:-1]),
            "A trace reports a stoppage before the final mechanical exchange")
    metrics = engine._last_fight_result.metrics
    require(set(metrics.get("damage_summary", {})) == {"a", "b"},
            "Fight result omitted its per-corner visible-damage summary")
    require(all(metrics["damage_summary"][corner]
                == metrics[corner].get("visible_damage", []) for corner in ("a", "b")),
            "Fight metrics disagreed about the visible-damage timeline")
    require(set(metrics.get("techniques", {})) == {"a", "b"},
            "Fight result omitted per-corner technique analysis")
    require(all("top_moves" in metrics["techniques"][corner]
                and "completed_sequences" in metrics["techniques"][corner]
                and "average_mechanics" in metrics["techniques"][corner]
                for corner in ("a", "b")),
            "Technique analysis omitted top moves, sequences, or mechanical load")
    if result["method"] in FINISH_METHODS:
        require(native_events[-1]["stoppage"] is not None,
                "A finished fight omitted the mechanical reason from its final exchange")


def test_native_structured_result_matches_legacy_result():
    engine = FightAuditHarness()
    a = synthetic_fighter("Structured A", 76, "Sambo", "Dynamic Attacker", 0)
    b = synthetic_fighter("Structured B", 75, "Muay Thai", "Pressure", 1)
    random.seed(551908)
    structured = engine.simulate_fight_result(a, b, {"main": True, "title": False})
    require(structured.trace and structured.trace[-1]["type"] == "official_result",
            "Structured fight result omitted its terminal official-result event")
    require(all(event["type"] == "exchange" for event in structured.trace[:-1]),
            "Structured fight trace contains an unclassified mechanical event")
    require(structured.method in FINISH_METHODS | {"Decision", "Draw"},
            "Structured fight result returned an invalid method")
    require(structured.verdict,
            "Structured fight result omitted its explicit finish or decision verdict")
    legacy = structured.legacy_tuple(a, b)
    require((legacy[2], legacy[3], tuple(legacy[4]))
            == (structured.method, structured.round_no, structured.commentary),
            "Structured result compatibility tuple changed the official result")
    require(structured.metrics["a"] == a.last_fight_stats and structured.metrics["b"] == b.last_fight_stats,
            "Structured result metrics diverged from the legacy fighter telemetry")


def test_every_detailed_attribute_has_a_fight_role():
    source = (ROOT / "fight_engine.py").read_text(encoding="utf-8")
    usage = detailed_skill_usage(source)
    expected = {key for keys in DETAILED_SKILL_GROUPS.values() for key in keys}
    require(set(usage) == expected, "Detailed-skill usage audit omitted a model attribute")
    missing = sorted(key for key, row in usage.items() if row["usage"] == "missing")
    require(not missing, f"Detailed attributes have no direct or documented pre-fight role: {missing}")


def test_frozen_baseline_contract_and_representative_determinism():
    require(BASELINE_PATH.exists(), "Fight-engine preservation baseline has not been generated")
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    require(baseline.get("fight_count", 0) >= 3_000, "Finish-rate baseline sample is too small")
    require("Overall" in baseline.get("groups", {}), "Finish-rate baseline omitted overall results")
    require(all(f"Competitive {tier}" in baseline["groups"] for tier in ("Low", "Mid", "High")),
            "Finish-rate baseline omitted a competitive tier")
    specs = {row["id"]: row for row in matchup_specs()}
    engine = FightAuditHarness()
    # Individual outcomes may change when a formerly shared presentation draw
    # is removed. A small fixed slice still catches nondeterminism cheaply;
    # the full generator enforces the locked distribution before each phase.
    for expected in baseline.get("parity", [])[::240]:
        spec = specs[expected["spec_id"]]
        a = synthetic_fighter(f"Audit {spec['id']} A", spec["a_level"], spec["a_style"], spec["a_behaviour"], 0)
        b = synthetic_fighter(f"Audit {spec['id']} B", spec["b_level"], spec["b_style"], spec["b_behaviour"], 1)
        actual = run_audited_fight(engine, a, b, expected["seed"], spec["fight"])
        repeated = run_audited_fight(engine, a, b, expected["seed"], spec["fight"])
        require(actual["signature"] == repeated["signature"],
                f"Fight-engine determinism changed for {expected['spec_id']} seed {expected['seed']}")


def test_commentary_bank_does_not_change_mechanics():
    engine = FightAuditHarness()
    a = synthetic_fighter("Commentary A", 79, "Kickboxer", "Volume", 0)
    b = synthetic_fighter("Commentary B", 78, "BJJ", "Submission Hunter", 1)
    original = run_audited_fight(engine, a, b, 902114, {"main": True})
    engine.fight_phrase = lambda category, actor, defender, **context: f"[{category}]"
    changed = run_audited_fight(engine, a, b, 902114, {"main": True})
    require(original["signature"] == changed["signature"],
            "Changing the commentary phrase bank altered the mechanical fight result")


def semantic_commentary_event(outcome="landed"):
    """Return one deliberately contradictory event for renderer regressions."""
    event = {
        "type": "exchange", "round": 1, "tick": 4, "clock": "1:12",
        "actor": "a", "defender": "b",
        "actor_name": "Semantic A", "defender_name": "Semantic B",
        "action": "jab", "move_id": "single_jab",
        "move": {
            "move_id": "single_jab", "name": "Single jab", "target": "head",
            "tags": ("punch",), "signature": False,
        },
        "defense_id": "outside_parry",
        "defense": {"defense_id": "outside_parry", "name": "Outside parry"},
        "position_before": "range", "position_after": "range",
        "outcome": outcome,
        # The renderer must ignore this compatibility descriptor because it
        # conflicts with the structured move, target, and actor above.
        "result": "Semantic B lands a body kick on Semantic A.",
        "exchange": {
            "setup": "lead-hand probe",
            "defensive_response": "Outside parry — defense breached",
            "counter_opportunity": False, "counter_consumed": False,
            "counter_success": False, "follow_up": "follow-up pressure",
            "combination": [{"sequence": 1, "weapon": "jab", "landed": outcome == "landed"}],
            "beats": [],
        },
        "flags": {"hurt": False, "knockdown": False, "cut": False, "position_changed": False},
    }
    if outcome == "defended":
        event["exchange"]["defensive_response"] = "Outside parry — attack denied"
    elif outcome == "takedown":
        event["action"] = "shoot"
        event["move_id"] = "double_leg"
        event["move"].update({"move_id": "double_leg", "name": "Double leg", "target": "hips", "tags": ("takedown",)})
        event["position_after"] = "half guard"
        event["flags"]["position_changed"] = True
    return event


def test_fact_driven_exchange_commentary_and_personality_contract():
    engine = FightAuditHarness()
    landed = semantic_commentary_event("landed")
    rendered = engine.render_exchange_trace_event(landed, personality="Balanced")
    folded = rendered.casefold()
    require("semantic a" in folded and "single jab" in folded and "head" in folded,
            "Fact-driven landed call omitted its actor, recorded move, or target")
    require("body kick" not in folded and landed["result"].casefold() not in folded,
            "Exchange renderer relied on a contradictory compatibility result string")
    require(" [" not in rendered,
            "Balanced exchange commentary exposed raw bracket metadata")

    defended = semantic_commentary_event("defended")
    defended_call = engine.render_exchange_trace_event(defended, personality="Technical")
    require("outside parry" in defended_call.casefold(),
            "Defended exchange commentary omitted the recorded named defense")
    require(" [" not in defended_call,
            "Technical exchange commentary exposed raw bracket metadata")

    takedown = semantic_commentary_event("takedown")
    takedown_call = engine.render_exchange_trace_event(takedown, personality="Balanced")
    require("double leg" in takedown_call.casefold() and "half guard" in takedown_call.casefold(),
            "Takedown commentary omitted its recorded move or settled position")

    technical_call = engine.render_exchange_trace_event(landed, personality="Technical", technical=True)
    require("single jab" in technical_call.casefold() and "outside parry" in technical_call.casefold(),
            "Technical commentary did not retain natural move and defense detail")
    require(" [" not in technical_call,
            "Technical commentary restored the removed raw bracket suffix")

    for personality in ("Balanced", "Technical", "Excitable", "Concise"):
        call = engine.render_exchange_trace_event(landed, personality=personality)
        require(call and "single jab" in call.casefold(),
                f"{personality} personality failed the fact-driven renderer contract")


def test_trait_specific_commentary_is_complete_contextual_and_rng_pure():
    engine = FightAuditHarness()
    engine._fight_mechanics_rng = random.Random(77_310)
    engine._fight_presentation_rng = random.Random(77_311)
    mechanics_before = engine._fight_mechanics_rng.getstate()
    presentation_before = engine._fight_presentation_rng.getstate()
    global_before = random.getstate()

    require(set(TRAIT_COMMENTARY_INTROS) == set(TRAITS),
            "Trait commentary does not cover every supported saved fighter trait")
    intros = set()
    for index, trait in enumerate(TRAITS):
        fighter = synthetic_fighter(f"Trait Voice {index}", 76, "MMA Generalist", "Dynamic Attacker", index)
        fighter.trait = trait
        line = engine.commentary_trait_intro(fighter)
        require(fighter.name in line and len(line.split()) >= 7,
                f"{trait} does not have a natural fighter-specific introduction")
        intros.add(line.replace(fighter.name, "{fighter}"))
    require(len(intros) == len(TRAITS),
            "Two supported traits collapsed into the same generic introduction")

    body_event = semantic_commentary_event("landed")
    body_event["move"].update({"target": "body", "tags": ("punch", "body")})
    body_event.update({
        "actor_commentary_profile": {"trait": "Body Hunter"},
        "defender_commentary_profile": {"trait": "Quiet Professional"},
        "actor_damage_after": 0, "actor_gas_after": 78,
    })
    contextual = ""
    for tick in range(1, 30):
        body_event["tick"] = tick
        candidate = engine.render_exchange_trace_event(body_event, personality="Balanced")
        if "body-hunting" in candidate.casefold() or "investment downstairs" in candidate.casefold():
            contextual = candidate
            break
    require(contextual and "semantic a" in contextual.casefold(),
            "Body Hunter commentary did not connect the saved trait to recorded body offense")

    unrelated = deepcopy(body_event)
    unrelated["actor_commentary_profile"] = {"trait": "Leg Kicker"}
    unrelated_calls = " ".join(
        engine.render_exchange_trace_event({**unrelated, "tick": tick}, personality="Balanced")
        for tick in range(1, 30)
    ).casefold()
    require("specialised leg work" not in unrelated_calls and "attacking the base" not in unrelated_calls,
            "Leg-kicker commentary was emitted for body-punch evidence")

    finishing_blow = semantic_commentary_event("knockdown")
    finishing_blow.update({
        "actor_commentary_profile": {"trait": "Knockout Artist"},
        "defender_commentary_profile": {"trait": "Iron Chin"},
        "flags": {"hurt": True, "knockdown": True, "cut": False, "position_changed": False},
        "actor_damage_after": 0, "actor_gas_after": 70,
        "stoppage": {"method": "KO"},
    })
    finishing_calls = " ".join(
        engine.render_exchange_trace_event({**finishing_blow, "tick": tick}, personality="Balanced")
        for tick in range(1, 30)
    ).casefold()
    require("iron chin" not in finishing_calls and "durability" not in finishing_calls,
            "Iron Chin commentary was attached to the blow that stopped the fight")

    slow_starter_finish = deepcopy(finishing_blow)
    slow_starter_finish["actor_commentary_profile"] = {"trait": "Slow Starter"}
    slow_starter_calls = " ".join(
        engine.render_exchange_trace_event({**slow_starter_finish, "tick": tick}, personality="Balanced")
        for tick in range(1, 7)
    ).casefold()
    require("customary time" not in slow_starter_calls and "opening read" not in slow_starter_calls,
            "Slow Starter commentary contradicted an effective early finishing exchange")

    light_damage = semantic_commentary_event("landed")
    light_damage.update({
        "actor_commentary_profile": {"trait": "Big Finisher"},
        "defender_commentary_profile": {"trait": "Quiet Professional"},
        "hurt_delta": {"a": 0, "b": 1},
        "actor_damage_after": 0, "actor_gas_after": 74,
    })
    light_damage_calls = " ".join(
        engine.render_exchange_trace_event({**light_damage, "tick": tick}, personality="Balanced")
        for tick in range(1, 30)
    ).casefold()
    require("finishing instinct" not in light_damage_calls and "known for converting" not in light_damage_calls,
            "Big Finisher commentary treated an ordinary damaging jab as a finishing window")
    meaningful_hurt = deepcopy(light_damage)
    meaningful_hurt["hurt_delta"] = {"a": 0, "b": 7}
    meaningful_hurt_calls = " ".join(
        engine.render_exchange_trace_event({**meaningful_hurt, "tick": tick}, personality="Balanced")
        for tick in range(1, 30)
    ).casefold()
    require("finishing instinct" in meaningful_hurt_calls or "known for converting" in meaningful_hurt_calls,
            "Big Finisher commentary did not recognise a trace-backed meaningful hurt gain")

    title_event = semantic_commentary_event("landed")
    title_event.update({
        "actor_commentary_profile": {"trait": "Title Mentality"},
        "defender_commentary_profile": {"trait": "Quiet Professional"},
        "championship": True, "round": 3,
        "actor_damage_after": 0, "actor_gas_after": 60,
    })
    round_three_calls = " ".join(
        engine.render_exchange_trace_event({**title_event, "tick": tick}, personality="Balanced")
        for tick in range(1, 30)
    ).casefold()
    require("championship rounds" not in round_three_calls and "title-fight composure" not in round_three_calls,
            "Title Mentality commentary called round three a championship round")
    round_four_calls = " ".join(
        engine.render_exchange_trace_event({**title_event, "round": 4, "tick": tick}, personality="Balanced")
        for tick in range(1, 30)
    ).casefold()
    require("championship rounds" in round_four_calls or "title-fight composure" in round_four_calls,
            "Title Mentality commentary did not activate in the recorded championship rounds")

    cut_event = semantic_commentary_event("control")
    cut_event.update({
        "actor_commentary_profile": {"trait": "Bad Weight Cut", "weight_cut_penalty": 0},
        "defender_commentary_profile": {"trait": "Quiet Professional"},
        "actor_damage_after": 0, "actor_gas_after": 24,
    })
    unsupported_cut_calls = " ".join(
        engine.render_exchange_trace_event({**cut_event, "tick": tick}, personality="Balanced")
        for tick in range(1, 30)
    ).casefold()
    require("difficult cut" not in unsupported_cut_calls and "weight cut" not in unsupported_cut_calls,
            "Bad Weight Cut commentary blamed low gas on a cut without a recorded penalty")
    supported_cut = deepcopy(cut_event)
    supported_cut["actor_commentary_profile"]["weight_cut_penalty"] = 4
    supported_cut_calls = " ".join(
        engine.render_exchange_trace_event({**supported_cut, "tick": tick}, personality="Balanced")
        for tick in range(1, 30)
    ).casefold()
    require("difficult cut" in supported_cut_calls or "weight cut" in supported_cut_calls,
            "Bad Weight Cut commentary ignored a recorded penalty with low gas")

    durability_response = semantic_commentary_event("landed")
    durability_response.update({
        "actor_commentary_profile": {"trait": "Iron Chin"},
        "defender_commentary_profile": {"trait": "Quiet Professional"},
        "actor_damage_after": 26, "actor_gas_after": 61,
    })
    durability_calls = " ".join(
        engine.render_exchange_trace_event({**durability_response, "tick": tick}, personality="Balanced")
        for tick in range(1, 30)
    ).casefold()
    require("durability" in durability_calls or "after absorbing damage" in durability_calls,
            "Iron Chin commentary did not wait for a later effective response after recorded damage")

    require(engine._fight_mechanics_rng.getstate() == mechanics_before
            and engine._fight_presentation_rng.getstate() == presentation_before
            and random.getstate() == global_before,
            "Trait-specific commentary consumed a fight or process RNG stream")

    bout_engine = FightAuditHarness()
    body_hunter = synthetic_fighter("Trait Bout A", 79, "Boxer", "Pressure", 0)
    leg_kicker = synthetic_fighter("Trait Bout B", 78, "Kickboxer", "Counter", 1)
    body_hunter.trait = "Body Hunter"
    leg_kicker.trait = "Leg Kicker"
    random.seed(77_312)
    result = bout_engine.simulate_fight_result(body_hunter, leg_kicker, {"main": True})
    transcript = "\n".join(result.commentary)
    require(bout_engine.commentary_trait_intro(body_hunter) in transcript
            and bout_engine.commentary_trait_intro(leg_kicker) in transcript,
            "A completed fight omitted its natural pre-fight trait introductions")
    for corner in ("a", "b"):
        contextual_rows = [
            event for event in result.trace
            if event.get("type") == "exchange" and event.get("actor") == corner
            and event.get("trait_commentary")
        ]
        rounds = [int(event.get("round", 0) or 0) for event in contextual_rows]
        require(len(contextual_rows) <= 2 and len(rounds) == len(set(rounds)),
                "Contextual trait commentary exceeded two calls per bout or one call per round")


def test_camp_specific_commentary_is_fact_driven_bounded_and_rng_pure():
    engine = FightAuditHarness()
    engine._fight_mechanics_rng = random.Random(78_410)
    engine._fight_presentation_rng = random.Random(78_411)
    mechanics_before = engine._fight_mechanics_rng.getstate()
    presentation_before = engine._fight_presentation_rng.getstate()
    global_before = random.getstate()
    gym = type("AuditGym", (), {
        "name": "Forge Combat", "head_coach": "Mara Stone",
        "specialties": ["Boxing", "Gameplanning"],
        "city": "Leeds", "region": "UK",
    })()
    engine.gyms = [gym]
    fighter = synthetic_fighter("Camp Voice", 78, "Boxer", "Counter", 0)
    fighter.camp = gym.name
    identity = engine.commentary_corner_identity(fighter)
    require(identity == {
        "camp": "Forge Combat", "coach": "Mara Stone",
        "specialties": ("Boxing", "Gameplanning"), "city": "Leeds", "region": "UK",
        "verified_gym": True,
    }, "Camp commentary identity omitted or invented a saved gym fact")
    intro = engine.commentary_camp_intro(fighter)
    for fact in (fighter.name, gym.name, gym.head_coach, "Leeds", "Boxing", "Gameplanning"):
        require(fact in intro, f"Camp introduction omitted recorded {fact} evidence")

    legacy = synthetic_fighter("Legacy Camp", 72, "MMA Generalist", "Cautious", 1)
    legacy.camp = "Old Save Dojo"
    legacy_intro = engine.commentary_camp_intro(legacy)
    require("Old Save Dojo" in legacy_intro and "listed out of" in legacy_intro
            and "details recorded" not in legacy_intro,
            "Unknown legacy camp did not degrade without inventing coach or specialty facts")
    independent = synthetic_fighter("Independent Camp", 72, "MMA Generalist", "Cautious", 2)
    independent.camp = "Independent"
    require(engine.commentary_camp_intro(independent) == "",
            "Independent fighter received an invented formal camp introduction")

    boxing = semantic_commentary_event("landed")
    boxing.update({
        "actor_camp": gym.name, "actor_coach": gym.head_coach,
        "actor_camp_specialties": tuple(gym.specialties),
        "actor_camp_city": gym.city, "actor_camp_region": gym.region,
        "actor_commentary_profile": {"trait": "Quiet Professional"},
        "defender_commentary_profile": {"trait": "Quiet Professional"},
        "actor_damage_after": 0, "actor_gas_after": 72,
    })
    boxing_calls = " ".join(
        engine.render_exchange_trace_event({**boxing, "tick": tick}, personality="Balanced")
        for tick in range(1, 35)
    )
    require("Forge Combat" in boxing_calls and (
                "boxing work" in boxing_calls.casefold() or "boxing emphasis" in boxing_calls.casefold()),
            "Boxing-specialist camp commentary did not connect to recorded punch offense")

    kick = deepcopy(boxing)
    kick.update({"action": "kick", "move_id": "round_kick"})
    kick["move"] = {
        "move_id": "round_kick", "name": "Round kick", "target": "body",
        "tags": ("kick", "combination"),
    }
    kick_calls = " ".join(
        engine.render_exchange_trace_event({**kick, "tick": tick}, personality="Balanced")
        for tick in range(1, 35)
    ).casefold()
    require("boxing work" not in kick_calls and "boxing emphasis" not in kick_calls,
            "Boxing camp commentary was emitted for unrelated kick-only evidence")

    plan_event = deepcopy(boxing)
    plan_event.update({
        "actor_camp_specialties": ("Gameplanning",),
        "plan": "Counter", "plan_change": {"from": "Pressure", "to": "Counter"},
        "counter": True,
    })
    plan_event["exchange"] = {"counter_consumed": True, "counter_success": True}
    plan_calls = [
        engine.render_exchange_trace_event({**plan_event, "tick": tick}, personality="Balanced")
        for tick in range(1, 35)
    ]
    contextual_plan = next((line for line in plan_calls if gym.name in line), "")
    require(contextual_plan and contextual_plan.count(gym.name) == 1
            and contextual_plan.count(gym.head_coach) <= 1 and "Counter plan" in contextual_plan,
            "Gameplanning commentary repeated the same camp/coach within one exchange")

    stablemate = synthetic_fighter("Camp Stablemate", 77, "Boxer", "Balanced", 3)
    stablemate.camp = gym.name
    shared_opening = engine.commentary_opening_context(
        fighter, stablemate, {}, {"head_to_head": {"meetings": 0, "a_wins": 0, "b_wins": 0}}
    )
    shared_line = next((line for line in shared_opening if gym.name in line), "")
    require(shared_line and fighter.name in shared_line and stablemate.name in shared_line
            and shared_line.count(gym.name) == 1 and shared_line.count(gym.head_coach) == 1
            and "stablemates" in shared_line,
            "Same-gym opponents received contradictory duplicate corner introductions")

    require(engine._fight_mechanics_rng.getstate() == mechanics_before
            and engine._fight_presentation_rng.getstate() == presentation_before
            and random.getstate() == global_before,
            "Camp-specific commentary consumed a fight or process RNG stream")

    opponent_gym = type("AuditGym", (), {
        "name": "River Grappling", "head_coach": "Iris Vale",
        "specialties": ["Wrestling", "BJJ", "Conditioning"],
        "city": "York", "region": "UK",
    })()
    bout_engine = FightAuditHarness()
    bout_engine.gyms = [gym, opponent_gym]
    a = synthetic_fighter("Camp Bout A", 79, "Boxer", "Pressure", 0)
    b = synthetic_fighter("Camp Bout B", 79, "Wrestler", "Control", 1)
    a.camp, b.camp = gym.name, opponent_gym.name
    random.seed(78_412)
    result = bout_engine.simulate_fight_result(a, b, {"main": True})
    broadcast = EventMixin.fight_night_commentary_lines(list(result.commentary), mode="Broadcast")
    for athlete in (a, b):
        athlete_intro = bout_engine.commentary_camp_intro(athlete)
        require(athlete_intro in result.commentary and athlete_intro in broadcast,
                "Broadcast did not retain a recorded camp/coach/specialty introduction")
    for corner in ("a", "b"):
        rows = [
            event for event in result.trace
            if event.get("type") == "exchange" and event.get("actor") == corner
            and event.get("camp_commentary")
        ]
        rounds = [int(event.get("round", 0) or 0) for event in rows]
        require(len(rows) <= 2 and len(rounds) == len(set(rounds)),
                "Contextual camp commentary exceeded two calls per bout or one call per round")

    def mechanics_only_trace(completed):
        cleaned = []
        for row in deepcopy(completed.trace):
            for key in tuple(row):
                if key == "commentary" or key == "camp_commentary" or key.startswith("actor_camp") \
                        or key == "actor_coach":
                    row.pop(key, None)
            cleaned.append(row)
        return cleaned

    verified_engine = FightAuditHarness()
    verified_engine.gyms = [gym, opponent_gym]
    plain_engine = FightAuditHarness()
    plain_engine.gyms = []
    verified_a = synthetic_fighter("Camp A/B A", 80, "Boxer", "Pressure", 6)
    verified_b = synthetic_fighter("Camp A/B B", 78, "Wrestler", "Control", 7)
    plain_a = synthetic_fighter("Camp A/B A", 80, "Boxer", "Pressure", 6)
    plain_b = synthetic_fighter("Camp A/B B", 78, "Wrestler", "Control", 7)
    for left, right in ((verified_a, plain_a), (verified_b, plain_b)):
        right.fighter_id = left.fighter_id
    verified_a.camp = plain_a.camp = gym.name
    verified_b.camp = plain_b.camp = opponent_gym.name
    random.seed(78_413)
    verified_result = verified_engine.simulate_fight_result(verified_a, verified_b, {"main": True})
    verified_rng_after = random.getstate()
    random.seed(78_413)
    plain_result = plain_engine.simulate_fight_result(plain_a, plain_b, {"main": True})
    plain_rng_after = random.getstate()
    require(
        (verified_result.winner_id, verified_result.loser_id, verified_result.method,
         verified_result.verdict, verified_result.round_no, verified_result.scorecards,
         verified_result.metrics, mechanics_only_trace(verified_result), verified_rng_after)
        ==
        (plain_result.winner_id, plain_result.loser_id, plain_result.method,
         plain_result.verdict, plain_result.round_no, plain_result.scorecards,
         plain_result.metrics, mechanics_only_trace(plain_result), plain_rng_after),
        "Verified gym commentary changed a seeded fight's mechanics, result, stats, or RNG state",
    )


def test_commentary_outcome_variants_are_deterministic_and_rng_pure():
    engine = FightAuditHarness()
    engine._fight_presentation_rng = random.Random(551_108)
    global_before = random.getstate()
    presentation_before = engine._fight_presentation_rng.getstate()

    events = {}
    events["landed"] = semantic_commentary_event("landed")
    events["blocked"] = semantic_commentary_event("defended")
    events["slipped"] = semantic_commentary_event("defended")
    events["slipped"]["defense"] = {
        "defense_id": "slip_angle", "name": "Slip and angle exit", "tags": ("evade", "angle"),
    }
    events["slipped"]["defense_id"] = "slip_angle"
    events["countered"] = semantic_commentary_event("landed")
    events["countered"].update({"counter": True})
    events["countered"]["exchange"].update({"counter_consumed": True, "counter_success": True})
    events["transitioned"] = semantic_commentary_event("takedown")
    events["escaped"] = semantic_commentary_event("position_change")
    events["escaped"].update({
        "action": "stand_up", "move_id": "wall_walk",
        "move": {"move_id": "wall_walk", "name": "Wall walk", "target": "", "tags": ("escape",)},
        "position_before": "half guard", "position_after": "range",
    })

    for expected_kind, event in events.items():
        snapshot = deepcopy(event)
        require(engine.exchange_commentary_kind(event) == expected_kind,
                f"Structured {expected_kind} event was assigned the wrong commentary lane")
        first = engine.render_exchange_trace_event(event, personality="Balanced", technical=True)
        second = engine.render_exchange_trace_event(event, personality="Balanced", technical=True)
        require(first == second, f"{expected_kind} commentary was not stable for identical trace facts")
        require(event == snapshot, f"{expected_kind} commentary mutated its completed trace event")
        require(first and " [" not in first and event["result"].casefold() not in first.casefold(),
                f"{expected_kind} commentary leaked a suffix or compatibility result")

    variants = set()
    for tick in range(1, 19):
        event = semantic_commentary_event("landed")
        event["tick"] = tick
        variants.add(engine.render_exchange_trace_event(event, personality="Balanced"))
    require(len(variants) >= 2,
            "Fact-driven landed commentary did not provide interchangeable deterministic calls")
    require(random.getstate() == global_before,
            "Fact-driven commentary consumed the process-global RNG")
    require(engine._fight_presentation_rng.getstate() == presentation_before,
            "Fact-driven commentary consumed the bout presentation RNG")


def test_commentary_quality_gate_handles_missing_and_conflicting_facts():
    engine = FightAuditHarness()
    minimal = {
        "type": "exchange", "round": 1, "tick": 1,
        "actor": "a", "defender": "b", "outcome": "control",
        "position_before": "range", "position_after": "range",
        "exchange": {}, "result": "Contradictory legacy result must not appear.",
    }
    minimal_call = engine.render_exchange_trace_event(minimal, personality="Technical", technical=True)
    require(minimal_call.strip() and "none" not in minimal_call.casefold()
            and "contradictory legacy" not in minimal_call.casefold(),
            "Renderer failed to degrade safely when optional trace facts were missing")
    require(" [" not in minimal_call,
            "Missing-fact fallback leaked raw bracket metadata")

    landed = semantic_commentary_event("landed")
    landed_call = engine.render_exchange_trace_event(landed, personality="Technical", technical=True).casefold()
    require("outside parry" in landed_call and "attempted" in landed_call,
            "Landed technical call did not qualify the recorded defense as an attempt")
    require(not any(claim in landed_call for claim in (
        "outside parry stops", "outside parry denies", "succeeded with the outside parry",
    )), "Landed call falsely described the breached defense as successful")

    defended = semantic_commentary_event("defended")
    defended_call = engine.render_exchange_trace_event(defended, personality="Balanced").casefold()
    require("outside parry" in defended_call,
            "Defended call omitted the defense that actually succeeded")
    require(not any(claim in defended_call for claim in ("lands the", "gets through", "scores with")),
            "Defended call contradicted the trace by claiming the attack landed")


def test_commentary_uses_only_available_fighter_and_fight_context():
    engine = FightAuditHarness()
    event = semantic_commentary_event("knockdown")
    event.update({
        "signature": True, "move_mastery": 92,
        "actor_style": "Muay Thai", "defender_style": "Boxer",
        "actor_stance": "Southpaw", "defender_stance": "Orthodox",
        "stance_matchup": "open", "actor_camp": "Northstar MMA",
        "actor_coach": "Coach Vega",
        "plan": "Attack the body",
        "plan_change": {"round": 1, "plan": "Attack the body", "reason": "body success"},
        "actor_streak": 3, "championship": True, "rivalry_heat": 68,
        "flags": {"hurt": True, "knockdown": True, "cut": False, "position_changed": False},
        "damage_delta": {"a": 0, "b": 11},
    })
    call = engine.render_exchange_trace_event(event, personality="Technical", technical=True).casefold()
    for fact in (
        "signature", "northstar mma", "coach vega", "attack the body", "southpaw", "open-stance",
        "muay thai", "boxer", "11 damage", "championship", "rivalry",
    ):
        require(fact in call, f"Context-rich commentary omitted available {fact} evidence")

    mastered = semantic_commentary_event("landed")
    mastered.update({"signature": False, "move_mastery": 81})
    mastery_call = engine.render_exchange_trace_event(mastered, personality="Technical", technical=True)
    require("Recorded Single jab mastery: 81." in mastery_call,
            "Technical commentary omitted available move-mastery evidence")

    fighter_a = synthetic_fighter("Camp A", 78, "Muay Thai", "Pressure", 0)
    fighter_b = synthetic_fighter("Camp B", 77, "Boxer", "Counter", 1)
    fighter_a.camp = "Northstar MMA"
    engine.gyms = [type("AuditGym", (), {"name": "Northstar MMA", "head_coach": "Coach Vega"})()]
    opening = engine.commentary_opening_context(
        fighter_a, fighter_b, {},
        state={"head_to_head": {"meetings": 0, "a_wins": 0, "b_wins": 0, "last_result": ""}},
    )
    require(any("Northstar MMA" in line and "Coach Vega" in line for line in opening),
            "Opening commentary omitted the saved gym and head-coach identity")


def test_commentary_hides_engine_placeholders_and_denied_transitions():
    engine = FightAuditHarness()
    survival = semantic_commentary_event("control")
    survival.update({
        "move_id": "composed_survival", "action": "cling",
        "move": {"move_id": "composed_survival", "name": "Composed survival", "target": "", "tags": ("defense",)},
        "position_before": "half guard", "position_after": "half guard",
        "position_path": ["half guard", "half guard"],
    })
    survival_call = engine.render_exchange_trace_event(survival, personality="Balanced")
    require("composed survival" not in survival_call.casefold()
            and "defensive ground work" in survival_call.casefold(),
            "Player-facing commentary leaked the composed-survival engine placeholder")
    require("maintain control" not in survival_call.casefold()
            and "in control" not in survival_call.casefold(),
            "Defensive survival commentary falsely claimed positional control")

    for action, move_id, move_name in (
        ("sweep", "hip_bump_sweep", "Hip-bump sweep"),
        ("stand_up", "technical_stand_up", "Technical stand-up"),
        ("pass", "knee_slice_pass", "Knee-slice pass"),
        ("advance_position", "side_control_transition", "Side-control transition"),
    ):
        denied = semantic_commentary_event("control")
        denied.update({
            "action": action, "move_id": move_id,
            "move": {"move_id": move_id, "name": move_name, "target": "", "tags": ("transition",)},
            "position_before": "half guard", "position_after": "half guard",
            "position_path": ["half guard", "half guard"],
        })
        call = engine.render_exchange_trace_event(denied, personality="Balanced").casefold()
        require(engine.exchange_commentary_kind(denied) == "denied_transition",
                f"Failed {action} did not enter the denied-transition commentary lane")
        require(any(term in call for term in ("attempt", "denies", "does not advance", "stops")),
                f"Failed {action} commentary falsely described successful control")
        require(not any(term in call for term in ("completes", "settles in", "moves the fight")),
                f"Failed {action} commentary claimed a transition not present in position_path")

    successful_sweep = semantic_commentary_event("position_change")
    successful_sweep.update({
        "action": "sweep", "move_id": "butterfly_sweep",
        "move": {
            "move_id": "butterfly_sweep", "name": "Butterfly sweep",
            "target": "", "tags": ("ground", "transition", "sweep"),
        },
        "position_before": "guard", "position_after": "guard",
        "position_path": ["guard", "guard"],
        "top_before": "b", "top_after": "a",
        "bottom_before": "a", "bottom_after": "b",
        "clinch_before": None, "clinch_after": None,
    })
    sweep_call = engine.render_exchange_trace_event(successful_sweep, personality="Balanced").casefold()
    require(engine.exchange_commentary_kind(successful_sweep) == "transitioned",
            "A successful same-position sweep ignored the recorded top/bottom ownership change")
    require(any(term in sweep_call for term in ("move the fight", "carries", "completes"))
            and "denies" not in sweep_call,
            "A successful same-position sweep was narrated as a denied transition")


def test_commentary_stats_style_submission_and_referee_facts():
    engine = FightAuditHarness()

    power = synthetic_fighter("Power Profile", 78, "Boxer", "Pressure", 0)
    power.detailed_skills = {
        "punch_power": 99, "killer_instinct": 96, "strength": 94,
        "hand_speed": 35, "reflexes": 35, "footwork": 35,
        "combination_punching": 35, "aggression": 35, "conditioning": 35,
        "punch_technique": 35, "counter_timing": 35, "feints": 35,
        "low_kick_technique": 35, "high_kick_technique": 35, "creative_kicks": 35,
        "dirty_boxing": 35, "elbows": 35, "knees": 35, "clinch_control": 35,
    }
    speed = synthetic_fighter("Speed Profile", 78, "Karate", "Counter", 1)
    speed.detailed_skills = {
        "punch_power": 35, "killer_instinct": 35, "strength": 35,
        "hand_speed": 99, "reflexes": 97, "footwork": 96,
        "combination_punching": 35, "aggression": 35, "conditioning": 35,
        "punch_technique": 35, "counter_timing": 35, "feints": 35,
        "low_kick_technique": 35, "high_kick_technique": 35, "creative_kicks": 35,
        "dirty_boxing": 35, "elbows": 35, "knees": 35, "clinch_control": 35,
    }
    power_profile = engine.commentary_fighter_profile(power)
    speed_profile = engine.commentary_fighter_profile(speed)
    require(power_profile["standing"] == "power" and speed_profile["standing"] == "speed",
            "Standing commentary identity did not follow deliberately distinct fighter attributes")

    power_event = semantic_commentary_event("landed")
    power_event.update({
        "commentary_salt": 711, "actor_style": "Boxer",
        "actor_commentary_profile": power_profile,
    })
    speed_event = deepcopy(power_event)
    speed_event.update({
        "actor_style": "Karate", "actor_commentary_profile": speed_profile,
    })
    power_call = engine.render_exchange_trace_event(power_event, personality="Balanced")
    speed_call = engine.render_exchange_trace_event(speed_event, personality="Balanced")
    require(power_call != speed_call and "single jab" in power_call.casefold()
            and "single jab" in speed_call.casefold(),
            "Distinct stats and styles did not shape fact-consistent standing commentary")

    salted_calls = set()
    for salt in range(24):
        event = deepcopy(power_event)
        event["commentary_salt"] = salt
        salted_calls.add(engine.render_exchange_trace_event(event, personality="Balanced"))
    require(len(salted_calls) >= 4,
            "Different bouts did not rotate enough standing calls for the same factual exchange")

    submission = semantic_commentary_event("submission_attempt")
    submission.update({
        "action": "bottom_submission", "move_id": "bottom_submission_chain",
        "move": {
            "move_id": "bottom_submission_chain", "name": "Bottom-position submission chain",
            "target": "", "tags": ("ground", "submission"),
        },
        "submission_technique": {"name": "triangle choke", "choke": True},
        "defense_id": "stack_escape",
        "defense": {"defense_id": "stack_escape", "name": "stack-and-turn escape"},
        "submission_escape": {"consequence": "guard recovered", "position": "guard"},
        "position_before": "guard", "position_after": "guard",
        "position_path": ["guard", "guard"],
        "top_before": "b", "top_after": "b", "bottom_before": "a", "bottom_after": "a",
        "actor_style": "BJJ",
        "actor_commentary_profile": {"ground": "submission", "standing": "precision", "defense": "submission defense"},
        "defender_commentary_profile": {"ground": "control", "standing": "power", "defense": "submission defense"},
    })
    submission_call = engine.render_exchange_trace_event(submission, personality="Balanced").casefold()
    for fact in ("semantic a", "triangle choke", "stack-and-turn escape", "guard"):
        require(fact in submission_call, f"Ground submission sequence omitted {fact}")
    require("top-position submission chain" not in submission_call
            and "bottom-position submission chain" not in submission_call,
            "Ground submission sequence exposed the generic registry placeholder instead of the technique")

    referee = deepcopy(submission)
    referee.update({
        "outcome": "position_change", "action": "ground_control",
        "move_id": "heavy_ride_control",
        "move": {"move_id": "heavy_ride_control", "name": "Heavy ride control", "target": "", "tags": ("ground", "control")},
        "submission_technique": None, "submission_escape": None,
        "position_before": "half guard", "position_after": "range",
        "position_path": ["half guard", "range"],
        "referee_ground_action": {
            "type": "standup", "position": "half guard",
            "text": "The referee stands both fighters up after the ground action stalls.",
        },
    })
    referee_call = engine.render_exchange_trace_event(referee, personality="Balanced")
    require(engine.exchange_commentary_kind(referee) == "referee_standup",
            "A referee stand-up was still classified as a fighter escape")
    require("referee" in referee_call.casefold() and "stands" in referee_call.casefold()
            and "heavy ride" not in referee_call.casefold(),
            "Referee stand-up commentary credited the preceding fighter action with the reset")

    fighter_escape = deepcopy(referee)
    fighter_escape.update({
        "action": "stand_up", "move_id": "technical_standup",
        "move": {"move_id": "technical_standup", "name": "Technical stand-up", "target": "", "tags": ("ground", "escape")},
        "referee_ground_action": None,
    })
    escape_call = engine.render_exchange_trace_event(fighter_escape, personality="Balanced").casefold()
    require("technical stand-up" in escape_call and "range" in escape_call
            and not any(term in escape_call for term in (
                "guard stays active", "hips stay heavy", "knee shield", "still controlled",
            )), "Successful ground escape appended contradictory old-position colour")

    mismatched_transition = deepcopy(submission)
    mismatched_transition.update({
        "outcome": "position_change", "action": "advance_position",
        "move_id": "back_take_transition",
        "move": {
            "move_id": "back_take_transition", "name": "Back-take transition",
            "target": "", "tags": ("ground", "transition", "back-take"),
        },
        "submission_technique": None, "submission_escape": None,
        "position_before": "side control", "position_after": "mount",
        "position_path": ["side control", "mount"],
        "top_before": "a", "top_after": "a", "bottom_before": "b", "bottom_after": "b",
    })
    transition_call = engine.render_exchange_trace_event(
        mismatched_transition, personality="Balanced",
    ).casefold()
    require("mount" in transition_call and "back-take" not in transition_call,
            "Player-facing transition name contradicted the recorded settled position")

    top = deepcopy(submission)
    top.update({"actor": "a", "top_after": "a", "bottom_after": "b"})
    bottom = deepcopy(top)
    bottom.update({"top_after": "b", "bottom_after": "a"})
    top_detail = engine.commentary_position_detail(top).casefold()
    bottom_detail = engine.commentary_position_detail(bottom).casefold()
    require(top_detail != bottom_detail
            and any(term in top_detail for term in ("heavy", "pressure", "hips"))
            and any(term in bottom_detail for term in ("guard", "frames", "hip")),
            "Ground position colour did not distinguish top pressure from bottom survival")


def test_technical_personality_analysis_is_rate_limited():
    engine = FightAuditHarness()
    contextual = []
    for tick in range(1, 25):
        event = semantic_commentary_event("landed")
        event.update({
            "tick": tick, "actor_style": "Kickboxer", "defender_style": "Wrestler",
            "actor_stance": "Southpaw", "defender_stance": "Orthodox", "stance_matchup": "open",
        })
        contextual.append(engine.render_exchange_trace_event(event, personality="Technical"))
    analysis_count = sum("Stance read:" in call or "Style read:" in call for call in contextual)
    require(0 < analysis_count < len(contextual) // 2,
            "Technical personality appended the same analysis frame to nearly every exchange")
    require(len(set(contextual)) >= 3,
            "Technical personality did not rotate its deterministic exchange calls")


def test_finish_attribution_walks_back_to_causal_trace_evidence():
    engine = FightAuditHarness()
    winner = synthetic_fighter("Causal A", 82, "Muay Thai", "Pressure", 0)
    loser = synthetic_fighter("Causal B", 80, "Boxer", "Counter", 1)
    causal = semantic_commentary_event("landed")
    causal.update({
        "round": 2, "tick": 3,
        "actor": "a", "defender": "b", "actor_name": winner.name, "defender_name": loser.name,
        "move_id": "spinning_elbow", "action": "power_punch",
        "move": {"move_id": "spinning_elbow", "name": "Spinning elbow", "target": "head", "tags": ("elbow", "spinning")},
        "flags": {"hurt": True, "knockdown": False, "cut": False, "position_changed": False},
        "damage_delta": {"a": 0, "b": 13}, "hurt_delta": {"a": 0, "b": 13},
        "sig_delta": 1, "round_metric_delta": {"a": {"impact": 12}, "b": {"impact": 0}},
    })
    noncausal = semantic_commentary_event("control")
    noncausal.update({
        "round": 2, "tick": 4,
        "actor": "a", "defender": "b", "actor_name": winner.name, "defender_name": loser.name,
        "move_id": "composed_survival", "action": "stand_up",
        "move": {"move_id": "composed_survival", "name": "Composed survival", "target": "", "tags": ("defense",)},
        "flags": {"hurt": False, "knockdown": False, "cut": False, "position_changed": False},
        "damage_delta": {"a": 0, "b": 0}, "hurt_delta": {"a": 0, "b": 0},
        "sig_delta": 0, "round_metric_delta": {"a": {"impact": 0}, "b": {"impact": 0}},
    })
    state = {
        "fighter_keys": {id(winner): "a", id(loser): "b"},
        "fighters": {"a": winner, "b": loser},
        "trace": [causal, noncausal], "position": "range", "round": 2, "tick": 4,
        "official_time": "4:08",
        "last_move_actor": "a", "last_move_payload": noncausal["move"], "referee": "standard",
    }
    detail = engine.finish_strike_text(winner, loser, state, clean=False)
    sequence = engine.finish_sequence(winner, loser, "TKO", detail, state)
    require("spinning elbow" in sequence.casefold(),
            "TKO commentary did not walk back to the latest causal strike")
    require("composed survival" not in sequence.casefold() and "technical stand-up" not in sequence.casefold(),
            "TKO commentary attributed the finish to a non-causal engine action")
    require(sequence.casefold().count("official result") == 1,
            "Causal TKO sequence emitted a duplicate official result")

    no_cause = deepcopy(state)
    no_cause["trace"] = [noncausal]
    generic = engine.finish_sequence(winner, loser, "TKO", "", no_cause)
    require("composed survival" not in generic.casefold()
            and "unanswered offense" in generic.casefold(),
            "Evidence-free TKO failed to use a safe generic finish description")


def test_legacy_no_plan_corner_advice_does_not_repeat_consecutively():
    engine = FightAuditHarness()
    a = synthetic_fighter("Advice A", 75, "Boxer", "Cautious", 0)
    b = synthetic_fighter("Advice B", 75, "Wrestler", "Control", 1)
    state = {
        "fighter_keys": {id(a): "a", id(b): "b"}, "trace": [], "round": 1,
        "gas": {"a": 70, "b": 70}, "head": {"a": 0, "b": 0},
        "body": {"a": 0, "b": 0}, "leg": {"a": 0, "b": 0},
        "move_reads": {
            "a": {"moves": {}, "targets": {}, "tags": {}, "setups": {}},
            "b": {"moves": {}, "targets": {}, "tags": {}, "setups": {}},
        },
        "plans": engine.fight_plan_state(a, b, {}),
    }
    first = engine.adapt_fight_plans(a, b, state, 1, 3)
    second = engine.adapt_fight_plans(a, b, state, 2, 3)
    require(first[0] != second[0] and first[1] != second[1],
            "Legacy no-plan corners repeated identical consecutive advice")
    require("no pre-fight tactical instruction" not in " ".join(first + second).casefold(),
            "Legacy no-plan advice restored the old developer-facing fallback")


def test_commentary_personalities_preserve_mechanics():
    signatures = []
    calls = []
    for personality in ("Balanced", "Technical", "Excitable", "Concise"):
        engine = FightAuditHarness(rules={"fight_commentary_personality": personality})
        a = synthetic_fighter("Personality A", 79, "Kickboxer", "Volume", 0)
        b = synthetic_fighter("Personality B", 78, "BJJ", "Submission Hunter", 1)
        result = run_audited_fight(engine, a, b, 912_774, {"main": True})
        signatures.append(result["signature"])
        calls.append(next(event["commentary"][0] for event in engine._last_fight_result.trace[:-1]
                          if event.get("commentary")))
    require(len(set(signatures)) == 1,
            "Changing commentary personality altered the mechanical fight signature")
    require(len(set(calls)) >= 3,
            "Commentary personalities did not produce meaningfully different exchange voices")


def test_unassigned_plan_corner_advice_uses_visible_evidence():
    engine = FightAuditHarness()
    a = synthetic_fighter("Corner A", 76, "Boxer", "Pressure", 0)
    b = synthetic_fighter("Corner B", 76, "Wrestler", "Control", 1)
    state = {
        "fighter_keys": {id(a): "a", id(b): "b"}, "round": 1,
        "trace": [_trace_event("b", "a", impact=18, danger=5, attempts=4, landed=4)],
        "gas": {"a": 64, "b": 72}, "head": {"a": 12, "b": 0},
        "body": {"a": 0, "b": 0}, "leg": {"a": 0, "b": 0},
        "plans": engine.fight_plan_state(a, b, {}),
        "move_reads": {"a": {"moves": {}}, "b": {"moves": {"double_leg": 4}}},
    }
    advice = engine.adapt_fight_plans(a, b, state, 1, 3)
    a_line = next(line for line in advice if a.name in line)
    require("no pre-fight tactical instruction" not in a_line.casefold(),
            "Legacy no-plan corner advice leaked developer-facing setup text")
    require(any(term in a_line.casefold() for term in ("cleaner offense", "repeated double leg", "activity")),
            "No-plan corner advice did not cite visible round evidence")
    require(state["plans"]["a"]["current"] == "Balanced",
            "Presentation-only no-plan advice changed the fighter's plan")


def test_coach_feedback_is_personal_specific_and_rng_pure():
    engine = FightAuditHarness(rules={"fight_commentary_personality": "Balanced"})
    engine._fight_mechanics_rng = random.Random(91_220)
    engine._fight_presentation_rng = random.Random(91_221)
    gym = type("CoachFeedbackGym", (), {
        "name": "Summit Fight Lab", "head_coach": "Elena Cross",
        "specialties": ["Gameplanning", "Kickboxing"],
        "city": "Liverpool", "region": "UK",
    })()
    engine.gyms = [gym]
    a = synthetic_fighter("Feedback Red", 77, "Boxer", "Pressure", 0)
    b = synthetic_fighter("Feedback Blue", 77, "Kickboxer", "Counter", 1)
    a.camp = gym.name
    b.camp = "Independent"
    damaging_kick = _trace_event("b", "a", impact=22, danger=10, attempts=4, landed=3)
    damaging_kick.update({
        "move_id": "rear_round_kick", "move_family": "Kicking",
        "knockdown_delta": {"a": 0, "b": 1}, "outcome": "knockdown",
    })
    state = {
        "fighter_keys": {id(a): "a", id(b): "b"}, "round": 1,
        "trace": [damaging_kick], "gas": {"a": 62, "b": 71},
        "head": {"a": 16, "b": 0}, "body": {"a": 0, "b": 0},
        "leg": {"a": 5, "b": 0},
        "plans": engine.fight_plan_state(a, b, {}),
        "move_reads": {
            "a": {"moves": {}, "targets": {}, "tags": {}, "setups": {}},
            "b": {"moves": {"rear_round_kick": 4}, "targets": {}, "tags": {}, "setups": {}},
        },
    }
    mechanics_before = engine._fight_mechanics_rng.getstate()
    presentation_before = engine._fight_presentation_rng.getstate()
    global_before = random.getstate()
    advice = engine.adapt_fight_plans(a, b, state, 1, 3)
    red_line = next(line for line in advice if a.name in line)
    for fact in (gym.head_coach, gym.name, a.name, b.name, "knockdown"):
        require(fact.casefold() in red_line.casefold(),
                f"Coach feedback omitted the supported {fact} fact")
    require(any(command in red_line.casefold() for command in (
        "raise the activity", "prepare for", "stay balanced", "switch to", "stay with",
    )), "Coach feedback gave a round read without an actionable instruction")
    require(not any(term in red_line.casefold() for term in (
        "observable round evidence", "deficit", "confidence", "adaptability", "discipline rating",
    )), "Coach feedback leaked developer-facing or hidden-rating language")

    voice_lines = []
    for personality in ("Balanced", "Technical", "Excitable", "Concise"):
        engine.rules["fight_commentary_personality"] = personality
        voice_lines.append(engine.render_corner_feedback(
            a, b, 1, f"{b.name} has repeated the rear round kick four times",
            "Step outside the kick and return down the middle",
        ))
    require(len(set(voice_lines)) == 4,
            "Broadcast personalities did not produce distinct coach-feedback deliveries")
    require(all(a.name in line and gym.head_coach in line and gym.name in line for line in voice_lines),
            "A coach-feedback personality dropped the verified speaker or fighter identity")
    require(engine._fight_mechanics_rng.getstate() == mechanics_before
            and engine._fight_presentation_rng.getstate() == presentation_before
            and random.getstate() == global_before,
            "Coach feedback consumed a mechanics, presentation, or process RNG stream")

    b.camp = gym.name
    shared_speaker = engine.commentary_corner_speaker(a, b)
    require(gym.name in shared_speaker and gym.head_coach not in shared_speaker,
            "Stablemates assigned the same verified head coach to opposing between-round corners")


def test_finish_commentary_uses_current_move_and_one_official_result():
    engine = FightAuditHarness()
    winner = synthetic_fighter("Finish A", 82, "Muay Thai", "Pressure", 0)
    loser = synthetic_fighter("Finish B", 80, "Boxer", "Counter", 1)
    engine._fight_presentation_rng = random.Random(18)
    causal = semantic_commentary_event("knockdown")
    causal.update({
        "round": 2, "tick": 4,
        "actor": "a", "defender": "b", "actor_name": winner.name, "defender_name": loser.name,
        "move_id": "spinning_elbow", "action": "power_punch",
        "move": {
            "move_id": "spinning_elbow", "name": "Spinning elbow",
            "target": "head", "tags": ("elbow", "spinning"),
        },
        "flags": {"hurt": True, "knockdown": True, "cut": False, "position_changed": False},
        "damage_delta": {"a": 0, "b": 18}, "hurt_delta": {"a": 0, "b": 18},
        "knockdown_delta": {"a": 1, "b": 0}, "sig_delta": 1,
        "round_metric_delta": {"a": {"impact": 18}, "b": {"impact": 0}},
    })
    state = {
        "position": "pocket", "round": 2, "tick": 4, "official_time": "3:41",
        "fighter_keys": {id(winner): "a", id(loser): "b"},
        "fighters": {"a": winner, "b": loser}, "trace": [causal],
        "last_move_actor": "a", "last_move_payload": causal["move"],
        "finish_category": "ko_finish", "referee": "standard",
    }
    detail = engine.finish_strike_text(winner, loser, state, clean=True)
    require("spinning elbow" in detail.casefold(),
            "Strike finish commentary ignored the current recorded finishing move")
    sequence = engine.finish_sequence(winner, loser, "KO", detail, state)
    require("spinning elbow" in sequence.casefold(),
            "Final sequence lost continuity with the recorded finishing move")
    require(sequence.casefold().count("official") == 1,
            "Finish sequence emitted anything other than one official-result announcement")
    already_official = (
        f"Official result: {winner.name} defeats {loser.name} by Doctor Stoppage at 3:41 of round 2."
    )
    duplicate_guard = engine.finish_sequence(
        winner, loser, "Doctor Stoppage", already_official,
        {**state, "last_move_payload": {}, "trace": []},
    )
    require(duplicate_guard.casefold().count("official result") == 1,
            "Finish sequence duplicated an official result already present in its evidence text")


def test_random_streams_are_explicit_and_separate():
    source = (ROOT / "fight_engine.py").read_text(encoding="utf-8")
    require("random.random(" not in source and "random.randint(" not in source
            and "random.choice(" not in source,
            "Fight engine contains a random draw outside its explicit bout streams")
    require("fight_mechanics_rng().random()" in source,
            "Combat resolution does not use the mechanics stream")
    require("fight_officiating_rng().random()" in source,
            "Stoppage or judging resolution does not use the officiating stream")
    require("fight_judging_rng().uniform()" not in source,
            "Judging stream regression probe contains an invalid zero-argument draw")
    require("fight_presentation_random()" in source,
            "Commentary variation does not use the presentation stream")


def _trace_event(actor="a", defender="b", impact=0, danger=0, control=0,
                 attempts=0, landed=0, takedowns=0, submissions=0, knockdowns=0):
    return {
        "type": "exchange", "round": 1, "actor": actor, "defender": defender,
        "round_metric_delta": {
            "a": {"impact": impact if actor == "a" else 0,
                  "danger": danger if actor == "a" else 0,
                  "control": control if actor == "a" else 0},
            "b": {"impact": impact if actor == "b" else 0,
                  "danger": danger if actor == "b" else 0,
                  "control": control if actor == "b" else 0},
        },
        "control_delta": {"a": control if actor == "a" else 0,
                          "b": control if actor == "b" else 0},
        "sig_att_delta": attempts, "sig_delta": landed,
        "td_att_delta": takedowns, "td_delta": takedowns,
        "sub_att_delta": submissions,
        "knockdown_delta": {defender: knockdowns, actor: 0},
        "outcome": "knockdown" if knockdowns else "landed" if landed else "control",
    }


def test_trace_backed_judging_hierarchy_and_verdicts():
    engine = FightAuditHarness()
    a = synthetic_fighter("Judge A", 76, "Boxer", "Pressure", 0)
    b = synthetic_fighter("Judge B", 76, "Wrestler", "Control", 1)
    state = {
        "fighter_keys": {id(a): "a", id(b): "b"}, "round": 1,
        "trace": [_trace_event(impact=32, danger=18, attempts=4, landed=4, knockdowns=1),
                  _trace_event(impact=12, danger=8, attempts=3, landed=3)],
    }
    for profile in ("Damage-first", "Balanced", "Control-sensitive"):
        engine._fight_judging_rng = random.Random(44)
        winner, loser, score = engine.score_round(a, b, {}, state, {"profile": profile})
        require((winner, loser, score) == (a, b, 8),
                f"{profile} judge overturned a clearly dominant trace-backed round")

    original = (a.name, b.name)
    engine._fight_judging_rng = random.Random(71)
    before = engine.score_round(a, b, {}, state, {"profile": "Balanced"})
    a.name, b.name = "Renamed Red", "Renamed Blue"
    engine._fight_judging_rng = random.Random(71)
    after = engine.score_round(a, b, {}, state, {"profile": "Balanced"})
    a.name, b.name = original
    require(before == after, "Changing fighter presentation names altered a judge's card")

    close_state = {
        "fighter_keys": {id(a): "a", id(b): "b"}, "round": 1,
        "trace": [_trace_event("a", "b", impact=3, attempts=2, landed=1),
                  _trace_event("b", "a", impact=3, attempts=2, landed=1)],
    }

    class FixedJudge:
        def __init__(self, value):
            self.value = value

        def uniform(self, _low, _high):
            return self.value

    engine._fight_judging_rng = FixedJudge(1.6)
    red_lean = engine.score_round(a, b, {}, close_state, {"profile": "Balanced"})
    engine._fight_judging_rng = FixedJudge(-1.6)
    blue_lean = engine.score_round(a, b, {}, close_state, {"profile": "Balanced"})
    require(red_lean[0] is a and blue_lean[0] is b,
            "Genuinely close trace evidence cannot split across judges")
    even_state = {"fighter_keys": {id(a): "a", id(b): "b"}, "round": 1, "trace": []}
    require(engine.score_round(a, b, {}, even_state, {"profile": "Balanced"}) == (None, None, 10),
            "A round with no separating evidence did not produce a justified 10-10")

    cards = [
        {"name": "J1", "profile": "Balanced", "a": [10, 10, 10], "b": [9, 9, 9], "rounds": []},
        {"name": "J2", "profile": "Balanced", "a": [10, 10, 10], "b": [9, 9, 9], "rounds": []},
        {"name": "J3", "profile": "Balanced", "a": [9, 9, 9], "b": [10, 10, 10], "rounds": []},
    ]
    decision = engine.decision_from_judges(a, b, {"fighter_keys": {id(a): "a", id(b): "b"}, "judge_scores": cards})
    require(decision["winner"] is a and decision["verdict"] == "Split Decision",
            "Judge votes and split-decision verdict disagree")
    cards[2]["a"], cards[2]["b"] = [10, 9, 10], [10, 10, 9]
    decision = engine.decision_from_judges(a, b, {"fighter_keys": {id(a): "a", id(b): "b"}, "judge_scores": cards})
    require(decision["winner"] is a and decision["verdict"] == "Majority Decision",
            "Two winning cards plus one tied card did not produce a majority decision")
    cards[1]["a"], cards[1]["b"] = [9, 9, 9], [10, 10, 10]
    decision = engine.decision_from_judges(a, b, {"fighter_keys": {id(a): "a", id(b): "b"}, "judge_scores": cards})
    require(decision["winner"] is None and decision["verdict"] == "Split Draw",
            "One card each plus one tied card did not produce a split draw")


def test_repeated_foul_creates_visible_point_deduction():
    engine = FightAuditHarness()
    a = synthetic_fighter("Fouling A", 70, "Boxer", "Pressure", 0)
    b = synthetic_fighter("Fouled B", 70, "Wrestler", "Control", 1)

    class FoulRng:
        def random(self):
            return 0.0

        def choice(self, _values):
            return "grounded knee"

    engine._fight_mechanics_rng = FoulRng()
    state = {
        "fighter_keys": {id(a): "a", id(b): "b"}, "position": "cage",
        "gas": {"a": 80, "b": 80}, "gas_cap": {"a": 100, "b": 100},
        "fouls": {"a": [], "b": []}, "point_deductions": {"a": {}, "b": {}},
        "round": 2, "tick": 7,
    }
    first = engine.resolve_fight_incident(a, b, state)
    second = engine.resolve_fight_incident(a, b, state)
    third = engine.resolve_fight_incident(a, b, state)
    require("warns" in first and "warns" in second,
            "Initial illegal grounded knees were not visibly warned")
    require("deducts one point" in third and state["point_deductions"]["a"][2] == 1,
            "Repeated foul did not create a visible round-specific point deduction")
    require({key: state["last_foul"][key] for key in ("round", "tick", "fighter", "type", "point_deducted")} == {
        "round": 2, "tick": 7, "fighter": "a", "type": "grounded knee", "point_deducted": True,
    }, "Point deduction omitted its trace-ready foul evidence")
    require(state["last_foul"]["warning_number"] == 3
            and state["last_foul"]["referee"] == "standard"
            and state["last_foul"]["accidental"],
            "Foul evidence omitted its warning, referee, or intent classification")
    require(engine.resolve_fight_incident(a, b, state) == "" and len(state["fouls"]["a"]) == 3,
            "The bout-local foul cap allowed an unlimited fourth incident")


def test_referee_profiles_technical_outcomes_and_review_flags():
    engine = FightAuditHarness()
    a = synthetic_fighter("Technical A", 76, "Boxer", "Pressure", 0)
    b = synthetic_fighter("Technical B", 76, "Wrestler", "Control", 1)
    require({name: profile["stoppage_modifier"] for name, profile in engine.REFEREE_PROFILES.items()} == {
        "cautious": 0.04, "standard": 0.0, "permissive": -0.03, "late": -0.06,
    }, "Explicit referee profiles changed the calibrated stoppage modifiers")
    require({name: profile["standup_threshold"] for name, profile in engine.REFEREE_PROFILES.items()} == {
        "cautious": 4, "standard": 5, "permissive": 6, "late": 7,
    }, "Explicit referee profiles changed the calibrated stand-up thresholds")

    base = {
        "fighter_keys": {id(a): "a", id(b): "b"}, "fighters": {"a": a, "b": b},
        "technical_foul_stoppage": {"offender": "a", "injured": "b", "foul": "eye poke", "accidental": True, "round": 1},
        "round": 1, "max_rounds": 3, "judge_scores": [],
    }
    winner, loser, method, detail = engine.technical_foul_outcome(a, b, base)
    require(method == "No Contest" and "Only 0 round(s)" in detail
            and base["technical_outcome"]["required_rounds"] == 2,
            "An accidental foul before two completed rounds did not produce a No Contest")

    cards = [
        {"name": "J1", "profile": "Balanced", "a": [10, 10], "b": [9, 9], "rounds": []},
        {"name": "J2", "profile": "Balanced", "a": [10, 10], "b": [9, 9], "rounds": []},
        {"name": "J3", "profile": "Balanced", "a": [9, 9], "b": [10, 10], "rounds": []},
    ]
    scored = dict(base, round=3, judge_scores=cards,
                  technical_foul_stoppage={"offender": "b", "injured": "a", "foul": "low blow", "accidental": True, "round": 3})
    winner, loser, method, detail = engine.technical_foul_outcome(a, b, scored)
    require(winner is a and loser is b and method == "Technical Decision"
            and scored["decision_verdict"] == "Technical Split Decision",
            "A foul stoppage after the completed-round threshold ignored the sealed scorecards")

    review_state = {
        "fighter_keys": {id(a): "a", id(b): "b"}, "hurt": {"a": 98, "b": 0},
        "knockdowns": {"a": 0, "b": 3}, "unanswered": {"a": 12, "b": 0},
        "cuts": {"a": 1, "b": 0}, "referee": "late",
    }
    review = engine.stoppage_review_from_evidence(a, "TKO", review_state)
    require(review["flag"] == "unusually late" and review_state["hurt"]["a"] == 98,
            "Post-fight review failed to flag trace evidence or rewrote the official state")


def test_hurt_recovers_without_healing_trauma_and_medical_uses_same_evidence():
    class MedicalHarness(FightAuditHarness, WorldMixin):
        @staticmethod
        def staff_effect(_role):
            return 0

    engine = MedicalHarness()
    fighter = synthetic_fighter("Medical A", 74, "Boxer", "Pressure", 0)
    opponent = synthetic_fighter("Medical B", 74, "Wrestler", "Control", 1)
    state = {
        "fighter_keys": {id(fighter): "a", id(opponent): "b"},
        "gas": {"a": 45, "b": 45}, "gas_cap": {"a": 100, "b": 100},
        "damage": {"a": 28, "b": 0}, "hurt": {"a": 18, "b": 0},
        "head": {"a": 17, "b": 0}, "body": {"a": 8, "b": 0},
        "leg": {"a": 6, "b": 0}, "round": 1, "championship_pacing": False,
    }
    persistent_before = (state["damage"]["a"], state["head"]["a"], state["body"]["a"], state["leg"]["a"])
    engine.recover_between_rounds(fighter, opponent, state)
    require(state["hurt"]["a"] < 18 and state["gas"]["a"] > 45,
            "Corner work did not reduce transient hurt and restore bounded gas")
    require((state["damage"]["a"], state["head"]["a"], state["body"]["a"], state["leg"]["a"]) == persistent_before,
            "Between-round recovery healed accumulated physical trauma")

    cut_state = {"fighter_keys": {id(fighter): "a"}, "cut_state": {"a": []}, "round": 2, "tick": 9}
    cut = engine.record_structured_cut(fighter, cut_state, 18, weapon="elbow")
    require(set(cut) == {"location", "severity", "bleeding", "swelling", "vision_risk", "weapon", "round", "tick"},
            "Structured cut omitted medical location/severity evidence")

    fighter.last_fight_stats = {
        "head_damage": 39, "body_damage": 24, "leg_damage": 31,
        "cut_details": [{"severity": 5, "location": "left eyebrow"}],
    }
    fighter.available_week = 0
    fighter.available_day = 0
    fighter.last_fight_day_index = 1
    rng_before = random.getstate()
    random.seed(2204)
    engine.set_post_fight_recovery(fighter, "TKO", lost=True)
    random.setstate(rng_before)
    require(fighter.last_fight_stats["medical_layoff_weeks"] == 4,
            "Post-fight layoff ignored the bounded trauma shown in Fight Night metrics")
    require(fighter.last_fight_stats["medical_basis"]["leg_damage"] == 31 and fighter.injured >= 1,
            "Severe visible trauma did not feed the injury and medical-return path")
    fighter.morale = 70
    fighter.motivation = 70
    fighter.serious_injury_recurrence = 0
    engine.apply_visible_trauma_consequences(fighter, lost=True)
    require(fighter.morale == 67 and fighter.motivation == 68
            and fighter.serious_injury_recurrence == 1,
            "Displayed multi-location trauma did not drive bounded confidence and recurrence effects")
    require(fighter.last_fight_stats["trauma_consequences"] == {
        "markers": 3, "confidence_loss": 3, "recurrence_gain": 1,
    }, "Long-term trauma effects did not retain their visible evidence basis")


def test_location_damage_has_distinct_mechanical_effects():
    engine = FightAuditHarness()
    fighter = synthetic_fighter("Damage A", 76, "Kickboxer", "Dynamic Attacker", 0)
    opponent = synthetic_fighter("Damage B", 76, "Wrestler", "Control", 1)

    def state(head=0, body=0, leg=0):
        return {
            "fighter_keys": {id(fighter): "a", id(opponent): "b"},
            "gas": {"a": 70, "b": 70}, "hurt": {"a": 0, "b": 0},
            "head": {"a": head, "b": 0}, "body": {"a": body, "b": 0},
            "leg": {"a": leg, "b": 0}, "round": 2, "early_round": False,
            "night_form": {"a": 0, "b": 0}, "context": {},
        }

    healthy = state()
    body_hurt = state(body=20)
    leg_hurt = state(leg=20)
    head_hurt = state(head=20)
    require(engine.action_attack_value(fighter, "power_punch", body_hurt)
            < engine.action_attack_value(fighter, "power_punch", healthy),
            "Lasting body damage did not reduce burst output")
    require(engine.action_attack_value(fighter, "kick", leg_hurt)
            < engine.action_attack_value(fighter, "kick", healthy),
            "Lasting leg damage did not reduce kicking mobility")
    require(engine.action_defence_value(fighter, "power_punch", head_hurt)
            < engine.action_defence_value(fighter, "power_punch", healthy),
            "Lasting head trauma did not reduce striking reactions")


def test_visible_damage_milestones_are_fact_driven_latched_and_rng_pure():
    engine = FightAuditHarness()
    actor = synthetic_fighter("Damage Narrator", 78, "Kickboxer", "Pressure", 0)
    defender = synthetic_fighter("Damage Subject", 76, "Boxer", "Counter", 1)
    engine._fight_mechanics_rng = random.Random(7101)
    engine._fight_officiating_rng = random.Random(7102)
    engine._fight_presentation_rng = random.Random(7103)
    global_before = random.getstate()
    stream_before = (
        engine._fight_mechanics_rng.getstate(),
        engine._fight_officiating_rng.getstate(),
        engine._fight_presentation_rng.getstate(),
    )

    expected_ids = {
        damage_id
        for thresholds in engine.VISIBLE_DAMAGE_MILESTONES.values()
        for _threshold, damage_id, _label, _keyword in thresholds
    }
    observed_ids = set()
    for channel, thresholds in engine.VISIBLE_DAMAGE_MILESTONES.items():
        for tier, (threshold, damage_id, _label, keyword) in enumerate(thresholds, 1):
            state = {
                "fighter_keys": {id(actor): "a", id(defender): "b"},
                "head": {"a": 0, "b": 0}, "head_trauma": {"a": 0, "b": 0},
                "body": {"a": 0, "b": 0}, "leg": {"a": 0, "b": 0},
                "visible_damage": {"a": [], "b": []},
                "visible_damage_milestones": {
                    "a": {name: 0 for name in engine.VISIBLE_DAMAGE_MILESTONES},
                    "b": {name: 0 for name in engine.VISIBLE_DAMAGE_MILESTONES},
                },
                "last_move_payload": {"move_id": "single_jab", "name": "single jab", "target": "head"},
                "round": 2, "tick": 4, "commentary_salt": 44,
            }
            state["visible_damage_milestones"]["b"][channel] = tier - 1
            state["head_trauma" if channel == "head" else channel]["b"] = threshold
            before = {
                "head": {"a": 0, "b": threshold - 1 if channel == "head" else 0},
                "body": {"a": 0, "b": threshold - 1 if channel == "body" else 0},
                "leg": {"a": 0, "b": threshold - 1 if channel == "leg" else 0},
            }
            damage_events = engine.record_visible_damage_events(actor, defender, before, state)
            require(len(damage_events) == 1 and damage_events[0]["damage_id"] == damage_id,
                    f"{channel} tier {tier} did not emit its one supported milestone")
            observed_ids.add(damage_id)
            event = {
                "commentary_salt": 44, "round": 2, "tick": 4,
                "actor": "a", "defender": "b",
                "actor_name": actor.name, "defender_name": defender.name,
                "move_id": "single_jab",
                "move": {"move_id": "single_jab", "name": "single jab", "target": "head"},
                "outcome": "landed", "defense_id": "high_guard",
                "position_before": "range", "position_after": "range",
                "visible_damage_events": damage_events,
                "cut_events": {"a": [], "b": []},
            }
            lines = engine.render_visible_damage_narratives(event)
            require(len(lines) == 1 and actor.name in lines[0] and defender.name in lines[0]
                    and keyword in lines[0].casefold(),
                    f"{damage_id} narrative omitted its actor, subject, or observable symptom")
            require(not any(term in lines[0].casefold() for term in (
                "fracture", "broken rib", "torn ligament", "organ", "concussion",
                "lead leg", "nose", "mouth",
            )), f"{damage_id} narrative invented an unsupported diagnosis or location")
            repeated_before = deepcopy(before)
            repeated_before[channel]["b"] = threshold
            require(not engine.record_visible_damage_events(actor, defender, repeated_before, state),
                    f"{damage_id} repeated after its tier had already been recorded")

    require(observed_ids == expected_ids and len(observed_ids) == 12,
            "The focused damage probe did not cover all twelve visible milestones")

    base_cut_event = {
        "commentary_salt": 91, "round": 2, "tick": 7,
        "actor": "a", "defender": "b",
        "actor_name": actor.name, "defender_name": defender.name,
        "move_id": "clinch_elbow",
        "move": {"move_id": "clinch_elbow", "name": "clinch elbow", "target": "head"},
        "outcome": "landed", "defense_id": "high_guard",
        "position_before": "clinch", "position_after": "clinch",
        "visible_damage_events": [],
    }
    mild = deepcopy(base_cut_event)
    mild["cut_events"] = {"a": [], "b": [{
        "location": "nose", "severity": 1, "bleeding": 1,
        "swelling": 0, "vision_risk": False,
    }]}
    mild_line = engine.render_visible_damage_narratives(mild)[0].casefold()
    require("nose" in mild_line and "cut" in mild_line
            and not any(term in mild_line for term in ("eye", "line of sight", "streaming", "doctor")),
            "A mild nose cut invented eye risk, severe bleeding, or a doctor inspection")
    vision = deepcopy(base_cut_event)
    vision["cut_events"] = {"a": [], "b": [{
        "location": "left eyebrow", "severity": 3, "bleeding": 3,
        "swelling": 2, "vision_risk": True,
    }]}
    vision_line = engine.render_visible_damage_narratives(vision)[0].casefold()
    require("left eyebrow" in vision_line and "swelling" in vision_line
            and "nose" not in vision_line,
            "A vision-risk eyebrow cut lost or contradicted its exact structured evidence")

    require(random.getstate() == global_before and stream_before == (
        engine._fight_mechanics_rng.getstate(),
        engine._fight_officiating_rng.getstate(),
        engine._fight_presentation_rng.getstate(),
    ), "Visible damage classification or narrative consumed an RNG stream")


def test_fight_plans_change_actions_energy_targets_and_counter_windows():
    engine = FightAuditHarness()
    a = synthetic_fighter("Plan A", 74, "MMA Generalist", "Dynamic Attacker", 0)
    b = synthetic_fighter("Plan B", 74, "MMA Generalist", "Dynamic Attacker", 1)

    def plan_state(plan):
        return {
            "fighter_keys": {id(a): "a", id(b): "b"}, "position": "range",
            "gas": {"a": 75, "b": 75}, "hurt": {"a": 0, "b": 0},
            "head": {"a": 0, "b": 0}, "body": {"a": 0, "b": 0},
            "leg": {"a": 0, "b": 0}, "round": 1, "early_round": True,
            "night_form": {"a": 0, "b": 0}, "context": {}, "counter_window": None,
            "plans": engine.fight_plan_state(a, b, {
                "fight_plans": {a.fighter_id: plan, b.fighter_id: "Balanced"},
            }),
        }

    def action_counts(plan, seed=812):
        state = plan_state(plan)
        engine._fight_mechanics_rng = random.Random(seed)
        counts = {}
        for _ in range(1200):
            action = engine.choose_action(a, b, state, 1, 1)
            counts[action] = counts.get(action, 0) + 1
        return counts, state

    balanced, _ = action_counts("Balanced")
    wrestle, _ = action_counts("Wrestle early")
    pressure, pressure_state = action_counts("Pressure and volume")
    conserve, conserve_state = action_counts("Conserve energy")
    require(wrestle.get("shoot", 0) > balanced.get("shoot", 0) * 1.25,
            "Wrestle-early plan did not measurably increase shot selection")
    require(pressure.get("jab", 0) + pressure.get("power_punch", 0)
            > conserve.get("jab", 0) + conserve.get("power_punch", 0),
            "Pressure and conserve plans did not separate striking pace/action mix")
    require(engine.plan_energy_multiplier(a, pressure_state)
            > engine.plan_energy_multiplier(a, conserve_state),
            "Fight plans did not create distinct energy costs")
    balanced_targets = engine.kick_target_shares(a, plan_state("Balanced"))
    body_targets = engine.kick_target_shares(a, plan_state("Attack the body"))
    leg_targets = engine.kick_target_shares(a, plan_state("Damage the lead leg"))
    require(body_targets["body"] > balanced_targets["body"],
            "Body-attack plan did not measurably change kick target selection")
    require(leg_targets["leg"] > balanced_targets["leg"],
            "Lead-leg plan did not measurably change kick target selection")

    counter_state = plan_state("Counter striking")
    counter_state.update({
        "stats": {"a": {"sig": 0}, "b": {"sig": 0}},
        "unanswered": {"a": 0, "b": 0}, "top": None, "bottom": None,
        "clinch_controller": None, "tick": 1,
    })
    original_resolver = engine._resolve_exchange_action
    engine._resolve_exchange_action = lambda *_args, **_kwargs: "The attack is defended."
    engine.resolve_exchange(b, a, "power_punch", counter_state, {
        "a": {"impact": 0, "control": 0, "danger": 0},
        "b": {"impact": 0, "control": 0, "danger": 0},
    })
    engine._resolve_exchange_action = original_resolver
    require(counter_state["counter_window"]["fighter"] == "a",
            "A defended attack did not create a one-beat counter opportunity")
    normal_weights = {"jab": 100.0, "power_punch": 100.0, "kick": 100.0}
    boosted = engine.apply_fight_plan_weights(a, b, counter_state, "range", dict(normal_weights), 1)
    counter_state["counter_window"] = None
    unboosted = engine.apply_fight_plan_weights(a, b, counter_state, "range", dict(normal_weights), 1)
    require(boosted["power_punch"] > unboosted["power_punch"],
            "Counter-striking plan did not exploit its actual counter window")


def test_fight_plan_defaults_identity_ai_and_adaptation():
    engine = FightAuditHarness()
    a = synthetic_fighter("Same Plan Name", 78, "Wrestler", "Control", 0)
    b = synthetic_fighter("Same Plan Name", 78, "Kickboxer", "Counter", 1)
    b.fighter_id = f"{b.fighter_id}-blue"
    default = engine.fight_plan_state(a, b, {})
    require(default["a"]["current"] == default["b"]["current"] == "Balanced",
            "Legacy fight payload did not default both corners to Balanced")
    explicit = engine.fight_plan_state(a, b, {"fight_plans": {
        a.fighter_id: "Wrestle early", b.fighter_id: "Counter striking",
    }})
    require(explicit["a"]["current"] == "Wrestle early" and explicit["b"]["current"] == "Counter striking",
            "Duplicate-name fighters did not retain independent ID-keyed plans")
    ai = engine.fight_plan_state(a, b, {"ai_controlled": True})
    require(ai["a"]["current"] in FIGHT_PLANS and ai["b"]["current"] in FIGHT_PLANS
            and ai["a"]["current"] != "Balanced",
            "AI fighters did not use the shared style/matchup plan model")

    a.detailed_skills["adaptability"] = 90
    a.detailed_skills["discipline"] = 90
    a.fight_iq = 90
    b.detailed_skills["adaptability"] = 35
    b.detailed_skills["discipline"] = 35
    b.fight_iq = 35
    state = {
        "fighter_keys": {id(a): "a", id(b): "b"}, "round": 1,
        "trace": [_trace_event("b", "a", impact=18, danger=8, attempts=5, landed=4)],
        "gas": {"a": 70, "b": 70}, "head": {"a": 10, "b": 0},
        "body": {"a": 0, "b": 0}, "leg": {"a": 0, "b": 0},
        "plans": engine.fight_plan_state(a, b, {"fight_plans": {
            a.fighter_id: "Balanced", b.fighter_id: "Balanced",
        }}),
    }
    advice = engine.adapt_fight_plans(a, b, state, 1, 3)
    require(state["plans"]["a"]["current"] != "Balanced"
            and state["plans"]["b"]["current"] == "Balanced",
            "Adaptable and inflexible fighters responded identically to a failing plan")
    require(any("Corner advice" in line and a.name in line for line in advice),
            "Plan adjustment did not produce observable, rating-free corner advice")


def test_fight_plan_evolves_from_repeated_move_evidence():
    engine = FightAuditHarness()
    a = synthetic_fighter("Adaptive Counter", 78, "Boxer", "Counter", 0)
    b = synthetic_fighter("Readable Pressure", 78, "Kickboxer", "Pressure", 1)
    a.detailed_skills.update({"adaptability": 90, "discipline": 90, "counter_timing": 90})
    a.fight_iq = 90
    trace = []
    for _ in range(4):
        event = _trace_event("b", "a", impact=6, danger=3, attempts=2, landed=2)
        event.update({"move_id": "rear_round_kick", "move_family": "Kicking"})
        trace.append(event)
    state = {
        "fighter_keys": {id(a): "a", id(b): "b"}, "round": 1, "trace": trace,
        "gas": {"a": 70, "b": 70}, "head": {"a": 10, "b": 0},
        "body": {"a": 0, "b": 0}, "leg": {"a": 0, "b": 0},
        "move_reads": {
            "a": {"moves": {}, "targets": {}, "tags": {}, "setups": {}},
            "b": {"moves": {"rear_round_kick": 4}, "targets": {}, "tags": {}, "setups": {}},
        },
        "plans": engine.fight_plan_state(a, b, {"fight_plans": {
            a.fighter_id: "Balanced", b.fighter_id: "Pressure and volume",
        }}),
    }
    engine.adapt_fight_plans(a, b, state, 1, 3)
    row = state["plans"]["a"]
    require(row["current"] == "Counter striking" and row["adjustments"] == 1,
            "Repeated opponent technique evidence did not trigger the expected counter plan")
    require(row["history"][-1]["evidence"]["repeated_count"] == 4
            and row["history"][-1]["confidence"] > 0.5,
            "Plan evolution did not retain its evidence or confidence")
    engine.adapt_fight_plans(a, b, state, 1, 3)
    require(row["current"] == "Counter striking" and row["adjustments"] == 1,
            "A corner oscillated to a second plan inside the same round")


def test_exchange_counter_plan_produces_more_successful_counters():
    def sample(plan):
        attempted = successful = 0
        signatures = []
        for seed in range(9_100, 9_160):
            engine = FightAuditHarness()
            a = synthetic_fighter("Exchange A", 76, "Boxer", "Counter", 0)
            b = synthetic_fighter("Exchange B", 76, "Boxer", "Pressure", 1)
            fight = {"fight_plans": {
                a.fighter_id: plan,
                b.fighter_id: "Pressure and volume",
            }}
            random.seed(seed)
            result = engine.simulate_fight_result(a, b, fight)
            metrics = result.metrics["exchanges"]["a"]
            attempted += metrics["counters_attempted"]
            successful += metrics["counters_successful"]
            signatures.append((result.winner_id, result.method, result.round_no, tuple(
                (event.get("action"), event.get("outcome"), event.get("exchange", {}).get("counter_success"))
                for event in result.trace if event.get("type") == "exchange"
            )))
        return attempted, successful, signatures

    counter_attempts, counter_successes, first_signatures = sample("Counter striking")
    pressure_attempts, pressure_successes, _ = sample("Pressure and volume")
    _repeat_attempts, _repeat_successes, repeated_signatures = sample("Counter striking")
    require(counter_attempts > pressure_attempts and counter_successes > pressure_successes,
            "Comparable counter fighters did not generate more attempted and successful counters")
    require(first_signatures == repeated_signatures,
            "Fixed-seed exchange chains were not deterministic")


def test_grappling_state_machine_ownership_paths_and_escapes():
    engine = FightAuditHarness()
    legal = {"position": "range", "top": None, "bottom": None, "clinch_controller": None}
    engine.set_fight_position(legal, "guard", top="a", bottom="b")
    require(engine.validate_fight_transition("guard", "guard", legal),
            "Legal ground ownership did not pass state validation")
    engine.set_fight_position(legal, "leg entanglement", top="a", bottom="b")
    require(legal["position"] == "leg entanglement",
            "A legal guard-to-leg-entanglement entry was not reachable")
    path_probe = {"position": "range", "top": None, "bottom": None, "clinch_controller": None}
    engine.set_fight_position(path_probe, "failed shot", controller="b")
    engine.set_fight_position(path_probe, "front headlock", top="b", bottom="a")
    engine.set_fight_position(path_probe, "turtle", top="b", bottom="a")
    engine.set_fight_position(path_probe, "range")
    engine.set_fight_position(path_probe, "clinch", controller="b")
    engine.set_fight_position(path_probe, "standing back control", controller="b")
    require(path_probe["position"] == "standing back control",
            "Expanded failed-shot/front-headlock/turtle/standing-back chain was not legally reachable")
    illegal = dict(legal, top="a", bottom="a")
    try:
        engine.validate_fight_transition("guard", "guard", illegal)
    except AssertionError:
        pass
    else:
        raise AssertionError("State validator accepted the same fighter on top and bottom")
    try:
        engine.validate_fight_transition("range", "mount", legal)
    except AssertionError:
        pass
    else:
        raise AssertionError("State validator accepted an illegal range-to-mount transition")

    totals = {}
    reached = set()
    nonterminal_submission_attempts = 0
    explicit_escapes = 0
    for style, behaviour in (("Wrestler", "Control"), ("BJJ", "Submission Hunter"), ("Boxer", "Pressure")):
        actions = {}
        for seed in range(13_000, 13_060):
            bout = FightAuditHarness()
            a = synthetic_fighter("Path A", 78, style, behaviour, 0)
            b = synthetic_fighter("Path B", 76, "MMA Generalist", "Dynamic Attacker", 1)
            random.seed(seed)
            result = bout.simulate_fight_result(a, b, {})
            for event in result.trace:
                if event.get("type") != "exchange":
                    continue
                reached.add(event["position_after"])
                require(event.get("result") or event.get("stoppage"),
                        "A legal grappling exchange produced no matching trace commentary")
                if event.get("actor") == "a":
                    actions[event["action"]] = actions.get(event["action"], 0) + 1
                if event.get("sub_att_delta", 0) and not event.get("stoppage"):
                    nonterminal_submission_attempts += 1
                    explicit_escapes += int(event.get("submission_escape") is not None)
        totals[style] = actions

    require(explicit_escapes == nonterminal_submission_attempts,
            "A failed submission omitted its explicit escape or retained-position consequence")
    require(totals["Wrestler"].get("shoot", 0) + totals["Wrestler"].get("takedown", 0)
            > totals["Boxer"].get("shoot", 0) + totals["Boxer"].get("takedown", 0),
            "Wrestlers and strikers did not produce distinct takedown paths")
    submission_actions = ("submission", "bottom_submission", "front_headlock_submission", "leg_attack")
    require(sum(totals["BJJ"].get(action, 0) for action in submission_actions)
            > sum(totals["Wrestler"].get(action, 0) for action in submission_actions),
            "Submission specialists and control wrestlers did not produce distinct grappling paths")


def test_finish_distribution_comparator_rejects_drift():
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    changed = json.loads(json.dumps(baseline))
    changed["groups"]["Overall"]["finish_pct"] += 1.01
    failures = compare_to_baseline(changed, baseline)
    require(any("Overall finish rate" in failure for failure in failures),
            "Finish-distribution comparator accepted an out-of-bounds overall drift")
    changed = json.loads(json.dumps(baseline))
    changed["groups"]["Overall"]["method_pct"]["KO"] += 1.01
    failures = compare_to_baseline(changed, baseline)
    require(any("KO rate" in failure for failure in failures),
            "Finish-distribution comparator accepted an out-of-bounds KO drift")
    changed = json.loads(json.dumps(baseline))
    changed["parity"][0]["signature"] = "changed"
    failures = compare_to_baseline(changed, baseline, exact_parity=True)
    require(any("Exact parity changed" in failure for failure in failures),
            "Exact-parity comparator accepted a changed frozen bout")

    accepted_methods = dict(ACCEPTED_RESULT_CALIBRATION["methods"])
    accepted_methods.update({"Doctor Stoppage": 1, "Injury Stoppage": 1})
    accepted = {
        "fight_count": ACCEPTED_RESULT_CALIBRATION["fight_count"],
        "groups": {
            "Overall": {
                "total": ACCEPTED_RESULT_CALIBRATION["fight_count"],
                "finishes": ACCEPTED_RESULT_CALIBRATION["finishes"],
                "methods": accepted_methods,
            },
            "Competitive": {
                "total": 2880,
                "finishes": 1408,
                "methods": {"Submission": 450, "Technical Submission": 38},
            },
            "Five Round": {
                "total": 100,
                "finishes": 50,
                "finish_timing_share_pct": {"Early": 50.0, "Middle": 42.0, "Late": 8.0},
            },
        },
    }
    require(not compare_to_accepted_calibration(accepted),
            "Exact accepted-calibration comparator rejected the approved counts")
    for field in ("finishes", "KO", "TKO"):
        changed = deepcopy(accepted)
        if field == "finishes":
            changed["groups"]["Overall"][field] += 1
        else:
            changed["groups"]["Overall"]["methods"][field] += 1
        failures = compare_to_accepted_calibration(changed)
        expected_label = "finish" if field == "finishes" else field.casefold()
        require(any(expected_label in failure.casefold() for failure in failures),
                f"Accepted calibration failed to reject a one-count {field} change")
    for method in ("Doctor Stoppage", "Injury Stoppage"):
        changed = deepcopy(accepted)
        changed["groups"]["Overall"]["methods"][method] = 0
        failures = compare_to_accepted_calibration(changed)
        require(any(method.casefold() in failure.casefold() and "unreachable" in failure.casefold()
                    for failure in failures),
                f"Accepted calibration failed to reject unreachable {method}")
    changed = deepcopy(accepted)
    changed["groups"]["Competitive"]["finishes"] = 1556
    require(any("competitive finish rate" in failure.casefold()
                for failure in compare_to_accepted_calibration(changed)),
            "Accepted calibration failed to reject excessive competitive finishes")
    changed = deepcopy(accepted)
    changed["groups"]["Competitive"]["methods"]["Submission"] = 393
    require(any("competitive submission rate" in failure.casefold()
                for failure in compare_to_accepted_calibration(changed)),
            "Accepted calibration failed to reject deficient competitive submissions")
    changed = deepcopy(accepted)
    changed["groups"].pop("Five Round")
    require(any("five-round" in failure.casefold()
                for failure in compare_to_accepted_calibration(changed)),
            "Accepted calibration failed to reject missing five-round evidence")
    changed = deepcopy(accepted)
    changed["groups"]["Five Round"]["finish_timing_share_pct"]["Late"] = 5.99
    require(any("rounds 4-5" in failure.casefold()
                for failure in compare_to_accepted_calibration(changed)),
            "Accepted calibration failed to reject deficient late championship finishes")


def test_action_frequency_baseline_is_complete():
    baseline = json.loads(ACTION_BASELINE_PATH.read_text(encoding="utf-8"))
    require(baseline["schema_version"] == 1 and baseline["fight_count"] == 3840,
            "Move-expansion action baseline does not cover the accepted corpus")
    required_actions = {
        "jab", "power_punch", "kick", "shoot", "clinch", "dirty_boxing",
        "takedown", "ground_strikes", "submission", "bottom_submission",
        "advance_position", "recover_guard", "sweep", "stand_up",
    }
    require(required_actions <= set(baseline["actions"]),
            "Move-expansion action baseline omitted core MMA actions")
    require(all(row["exchanges"] > 0 and "effective_pct" in row
                and "energy_spent" in row and "positions" in row
                for row in baseline["actions"].values()),
            "Action baseline omitted frequency, effectiveness, energy, or position evidence")


def test_move_registry_trace_contract_and_rng_purity():
    require(not MOVE_REGISTRY_ERRORS and len(MOVE_REGISTRY) >= 30,
            "Canonical MMA move registry is invalid or unexpectedly thin")
    engine = FightAuditHarness()
    a = synthetic_fighter("Move Trace A", 78, "Kickboxer", "Pressure", 0)
    b = synthetic_fighter("Move Trace B", 77, "Wrestler", "Control", 1)
    a.secondary_style = "BJJ"
    random.seed(740_021)
    result = engine.simulate_fight_result(a, b, {"title": True})
    exchanges = [event for event in result.trace if event.get("type") == "exchange"]
    require(exchanges and all(event.get("move_id") and isinstance(event.get("move"), dict)
                              for event in exchanges),
            "A resolved exchange omitted its move identity")
    kick_moves = [definition for definition in MOVE_REGISTRY.values() if "kick" in definition.tags]
    require(kick_moves and all(definition.targets and definition.side and definition.range_band
                               and definition.defense_families for definition in kick_moves),
            "A registered kick omitted target, side, range, or defensive-family metadata")
    high_risk = [definition for definition in MOVE_REGISTRY.values() if "high-risk" in definition.tags]
    require(high_risk and all(definition.minimum_skill >= 60 and definition.energy > 1
                              and definition.counter_risk > 1 for definition in high_risk),
            "High-risk spinning/flying techniques are not skill-gated and counterable")
    for event in exchanges:
        move = event["move"]
        require(move["parent_action"] == event["action"],
                "Move parent action disagreed with the resolved exchange")
        if not move.get("generic"):
            definition = MOVE_REGISTRY[event["move_id"]]
            require(event["position_before"] in definition.positions,
                    "Move was selected from an illegal position")
            require(not definition.targets or move["target"] in definition.targets,
                    "Targeted move was attached to the wrong damage location")

    def mechanics_signature(harness):
        red = synthetic_fighter("Move Purity A", 76, "Boxer", "Counter", 2)
        blue = synthetic_fighter("Move Purity B", 76, "BJJ", "Submission Hunter", 3)
        random.seed(740_022)
        value = harness.simulate_fight_result(red, blue, {"main": True})
        return (value.winner_id, value.loser_id, value.method, value.round_no,
                value.scorecards, value.metrics["a"], value.metrics["b"])

    require(mechanics_signature(FightAuditHarness()) == mechanics_signature(FightAuditHarness()),
            "Move-aware fight resolution is not deterministic")

    counter_state = {
        "round": 1, "tick": 3, "position": "range",
        "counter_window": {"fighter": a.name, "source_counter_risk": 1.18},
    }
    counter_move = engine.select_exchange_move(a, b, "power_punch", "range", "head", counter_state)
    require("counter" in counter_move["tags"],
            "A real counter window did not unlock a counter-only boxing technique")
    counter_state["counter_window"] = None
    ordinary_move = engine.select_exchange_move(a, b, "power_punch", "range", "head", counter_state)
    require("counter" not in ordinary_move["tags"],
            "A counter-only boxing technique appeared without a counter window")

    body_artist = synthetic_fighter("Body Combination Artist", 75, "Boxer", "Pressure", 4)
    head_hunter = synthetic_fighter("Head Combination Artist", 75, "Boxer", "Pressure", 5)
    body_artist.detailed_skills["body_punching"] = 99
    head_hunter.detailed_skills["body_punching"] = 20
    body_sequences = 0
    head_sequences = 0
    target_state = {"round": 1, "plans": {}, "counter_window": None}
    for tick in range(1, 121):
        target_state["tick"] = tick
        body_sequences += engine.select_exchange_move(
            body_artist, b, "power_punch", "range", "head", target_state,
        )["move_id"] == "body_head_change"
        head_sequences += engine.select_exchange_move(
            head_hunter, b, "power_punch", "range", "head", target_state,
        )["move_id"] == "body_head_change"
    require(body_sequences > head_sequences,
            "Body-punching skill did not materially change deterministic body-head combination selection")

    style_mixes = {}
    high_risk_attempts = 0
    total_kicks = 0
    for style_index, style in enumerate(("Sanda", "Taekwondo", "Karate", "Kickboxer", "Muay Thai")):
        striker = synthetic_fighter(f"{style} Move Mix", 82, style, "Dynamic Attacker", 10 + style_index)
        counts = {}
        selection_state = {"round": 1, "plans": {}, "counter_window": None}
        for tick in range(1, 181):
            selection_state["tick"] = tick
            target = ("leg", "body", "head")[tick % 3]
            move = engine.select_exchange_move(striker, b, "kick", "range", target, selection_state)
            counts[move["move_id"]] = counts.get(move["move_id"], 0) + 1
            high_risk_attempts += "high-risk" in move["tags"]
            total_kicks += 1
        style_mixes[style] = tuple(sorted(counts.items()))
    require(len(set(style_mixes.values())) == len(style_mixes),
            "Sanda, Taekwondo, Karate, Kickboxer, and Muay Thai did not produce distinct kick mixes")
    require(0 < high_risk_attempts < total_kicks * 0.2,
            "Skill-gated spinning/flying move frequency is absent or no longer uncommon")

    takedown_moves = [definition for definition in MOVE_REGISTRY.values() if "takedown" in definition.tags]
    require(takedown_moves and all(definition.entry_family and definition.finish_positions
                                   and definition.defense_families for definition in takedown_moves),
            "A registered takedown omitted entry, finish-position, or defense metadata")
    require(all(set(definition.finish_positions) <= {"guard", "half guard", "side control", "back control"}
                for definition in takedown_moves),
            "A takedown advertises an impossible finish position")
    wrestling_mixes = {}
    for style_index, style in enumerate(("Wrestler", "Judo", "Sambo", "Sanda")):
        wrestler = synthetic_fighter(f"{style} Takedown Mix", 82, style, "Control", 20 + style_index)
        counts = {}
        selection_state = {"round": 1, "plans": {}, "counter_window": None}
        for tick in range(1, 181):
            selection_state["tick"] = tick
            move = engine.select_exchange_move(wrestler, b, "takedown", "clinch", "", selection_state)
            counts[move["move_id"]] = counts.get(move["move_id"], 0) + 1
        wrestling_mixes[style] = tuple(sorted(counts.items()))
    require(len(set(wrestling_mixes.values())) == len(wrestling_mixes),
            "Wrestler, Judo, Sambo, and Sanda did not produce distinct legal takedown mixes")

    submission_moves = [definition for definition in MOVE_REGISTRY.values() if "submission" in definition.tags]
    require(submission_moves and all(definition.attack_path and definition.failure_outcomes
                                     for definition in submission_moves),
            "A registered submission omitted its legal attack path or explicit failure outcomes")
    submission_mixes = {}
    selection_cases = (
        ("submission", "back control"), ("submission", "mount"),
        ("bottom_submission", "guard"), ("front_headlock_submission", "front headlock"),
        ("leg_attack", "leg entanglement"),
    )
    for style_index, style in enumerate(("BJJ", "Luta Livre", "Catch Wrestler", "Submission Grappler", "Sambo")):
        grappler = synthetic_fighter(f"{style} Submission Mix", 84, style, "Submission Hunter", 30 + style_index)
        counts = {}
        selection_state = {"round": 1, "plans": {}, "counter_window": None}
        for tick in range(1, 201):
            selection_state["tick"] = tick
            action, position = selection_cases[tick % len(selection_cases)]
            move = engine.select_exchange_move(grappler, b, action, position, "", selection_state)
            counts[move["move_id"]] = counts.get(move["move_id"], 0) + 1
        submission_mixes[style] = tuple(sorted(counts.items()))
    require(len(set(submission_mixes.values())) == len(submission_mixes),
            "BJJ, Luta Livre, Catch Wrestler, Submission Grappler, and Sambo did not produce distinct submission mixes")

    signature_artist = synthetic_fighter("Signature Artist", 80, "Boxer", "Pressure", 40)
    signature_artist.signature_moves = ["one_two"]
    ordinary_artist = synthetic_fighter("Signature Artist", 80, "Boxer", "Pressure", 40)
    signature_counts = []
    for fighter in (signature_artist, ordinary_artist):
        count = 0
        selection_state = {"round": 1, "plans": {}, "counter_window": None}
        for tick in range(1, 241):
            selection_state["tick"] = tick
            move = engine.select_exchange_move(fighter, b, "power_punch", "range", "head", selection_state)
            count += move["move_id"] == "one_two"
        signature_counts.append(count)
    require(signature_counts[0] > signature_counts[1] and signature_counts[0] < 240,
            "A signature move was not preferred more often or became guaranteed")
    opponent = synthetic_fighter("Signature Opponent", 77, "Wrestler", "Control", 41)
    random.seed(740_023)
    signature_result = engine.simulate_fight_result(signature_artist, opponent, {"main": True})
    marked = [event for event in signature_result.trace if event.get("signature")]
    require(all(event["move_id"] in signature_artist.signature_moves for event in marked),
            "Trace signature markers disagreed with the fighter's move set")
    require(signature_result.metrics["signature_moves"]["a"] == signature_artist.last_fight_stats["signature_moves"],
            "Post-fight signature metrics diverged from fighter telemetry")
    before_attempts = signature_artist.career_signature_stats.get("one_two", {}).get("attempts", 0)
    engine.commit_career_stats(signature_artist, signature_result.method, won=signature_result.winner_id == signature_artist.fighter_id)
    require(signature_artist.career_signature_stats.get("one_two", {}).get("attempts", 0) >= before_attempts,
            "Signature attempts did not fold into persistent career totals")
    signature_exchanges = [event for event in signature_result.trace if event.get("type") == "exchange"]
    for event in signature_exchanges:
        rendered = engine.render_exchange_trace_event(event)
        require(event["move"]["name"].casefold() in rendered.casefold(),
                "Fight Night call did not describe the recorded move")
        require(" [" not in rendered,
                "Fight Night call exposed raw target/defense/follow-up metadata")
        technical = engine.render_exchange_trace_event(event, personality="Technical", technical=True)
        require(event["move"]["name"].casefold() in technical.casefold(),
                "Technical Fight Night call did not describe the recorded move")
        if event.get("outcome") == "defended":
            require(event["defense"]["name"].casefold() in technical.casefold(),
                    "Technical defended call omitted its named defensive technique")
        require(" [" not in technical,
                "Technical Fight Night call restored raw bracket metadata")
    for slot in ("a", "b"):
        family_rows = signature_result.metrics["exchanges"][slot]["move_families"]
        require(sum(row["attempts"] for row in family_rows.values())
                == sum(event.get("actor") == slot for event in signature_exchanges),
                "Bounded move-family summary did not reconcile with the raw trace")
    round_summaries = [line for line in signature_result.commentary if line.startswith("Round ") and "summary:" in line]
    require(all("Move families (effective/used)" in line for line in round_summaries),
            "A completed-round telemetry line omitted its bounded move-family summary")

    tactical_artist = synthetic_fighter("Tactical Move Artist", 82, "Boxer", "Dynamic Attacker", 42)
    plan_mixes = {}
    for plan in ("Pressure and volume", "Chase a finish"):
        counts = {}
        tactical_state = {
            "round": 2, "counter_window": None, "move_reads": {},
            "plans": {tactical_artist.name: {"initial": plan, "current": plan, "execution": 1.0,
                                                    "history": [], "effective_actions": 0, "attempts": 0}},
        }
        for tick in range(1, 201):
            tactical_state["tick"] = tick
            move = engine.select_exchange_move(tactical_artist, opponent, "power_punch", "range", "head", tactical_state)
            counts[move["move_id"]] = counts.get(move["move_id"], 0) + 1
        plan_mixes[plan] = tuple(sorted(counts.items()))
    require(len(set(plan_mixes.values())) == 2,
            "Existing fight plans did not produce different beneath-action move mixes")

    clean_count = repeated_count = 0
    for tick in range(1, 201):
        clean_state = {"round": 2, "tick": tick, "plans": {}, "counter_window": None, "move_reads": {}}
        repeated_state = {
            "round": 2, "tick": tick, "plans": {}, "counter_window": None,
            "move_reads": {tactical_artist.name: {"moves": {"one_two": 9}, "targets": {}, "tags": {}, "setups": {}}},
        }
        clean_count += engine.select_exchange_move(tactical_artist, opponent, "power_punch", "range", "head", clean_state)["move_id"] == "one_two"
        repeated_count += engine.select_exchange_move(tactical_artist, opponent, "power_punch", "range", "head", repeated_state)["move_id"] == "one_two"
    require(repeated_count < clean_count,
            "Repeated in-bout move patterns did not become less selectable")

    counter_read_state = {
        "round": 2, "tick": 9, "plans": {},
        "counter_window": {"fighter": tactical_artist.name, "source_counter_risk": 1.2},
        "move_reads": {opponent.name: {"moves": {"double_leg_entry": 6}, "targets": {}, "tags": {}, "setups": {}}},
    }
    counter_read = engine.select_exchange_move(tactical_artist, opponent, "power_punch", "range", "head", counter_read_state)
    require("counter" in counter_read["tags"]
            and "opponent-pattern-counter" in counter_read["selection_reasons"],
            "An adaptable counter fighter did not exploit a repeated opponent pattern")
    require(all(value <= 12 for fighter_reads in signature_result.metrics.get("move_reads", {}).values()
                for bucket in fighter_reads.values() for value in bucket.values())
            if signature_result.metrics.get("move_reads") else True,
            "Bout-local opponent recognition exceeded its bounded counters")

    mechanics_state = {
        "move_exertion": {"a": 0.0, "b": 0.0},
        "move_miss_pressure": {"a": 0.0, "b": 0.0},
        "move_counter_vulnerability": {"a": 0.0, "b": 0.0},
    }
    mechanics_event = {
        "actor": "b", "defender": "a", "outcome": "defended",
        "move": {"energy": 1.4, "miss_risk": 1.3, "counter_risk": 1.5},
    }
    engine.update_move_mechanics(mechanics_state, mechanics_event)
    require(mechanics_state["move_exertion"]["b"] > 0
            and mechanics_state["move_miss_pressure"]["b"] > 0
            and mechanics_state["move_counter_vulnerability"]["b"] > 0,
            "Move energy, miss risk, and counter risk remained inert metadata")
    risk_counter_state = {
        **mechanics_state, "round": 2, "tick": 11, "plans": {}, "move_reads": {},
        "fighter_keys": {id(tactical_artist): "a", id(opponent): "b"},
        "counter_window": {"fighter": "a", "source_counter_risk": 1.5},
    }
    risk_counter = engine.select_exchange_move(
        tactical_artist, opponent, "power_punch", "range", "head", risk_counter_state,
    )
    require("counter" in risk_counter["tags"]
            and "technique-counter-risk" in risk_counter["selection_reasons"],
            "A risky failed technique did not shape the defender's legal counter choice")

    exertion_artist = synthetic_fighter("Move Exertion Artist", 94, "Muay Thai", "Dynamic Attacker", 45)
    exertion_artist.detailed_skills = {key: 99 for keys in DETAILED_SKILL_GROUPS.values() for key in keys}
    fresh_energy = []
    strained_energy = []
    for tick in range(1, 321):
        base = {"round": 2, "tick": tick, "plans": {}, "move_reads": {}, "counter_window": None}
        fresh_move = engine.select_exchange_move(
            exertion_artist, opponent, "kick", "range", "head", base,
        )
        strained_move = engine.select_exchange_move(
            exertion_artist, opponent, "kick", "range", "head",
            {**base, "move_exertion": {exertion_artist.name: 12.0}},
        )
        fresh_energy.append(float(fresh_move["energy"]))
        strained_energy.append(float(strained_move["energy"]))
    require(sum(strained_energy) < sum(fresh_energy),
            "Accumulated move exertion did not reduce repeated high-energy technique selection")

    sequence_artist = synthetic_fighter("Move Sequence Artist", 92, "Boxer", "Pressure", 46)
    sequence_artist.detailed_skills = {key: 96 for keys in DETAILED_SKILL_GROUPS.values() for key in keys}
    clean_follow_up = chained_follow_up = 0
    for tick in range(2, 202):
        base = {"round": 1, "tick": tick, "plans": {}, "move_reads": {}, "counter_window": None}
        clean_follow_up += engine.select_exchange_move(
            sequence_artist, opponent, "power_punch", "range", "head", base,
        )["move_id"] == "one_two"
        chained_follow_up += engine.select_exchange_move(
            sequence_artist, opponent, "power_punch", "range", "head",
            {**base, "move_chains": {sequence_artist.name: {
                "source_move_id": "single_jab", "next_move_id": "one_two",
                "step": 1, "round": 1, "tick": tick - 1,
            }}},
        )["move_id"] == "one_two"
    require(chained_follow_up > clean_follow_up,
            "A successful setup did not increase its legal next-exchange follow-up")
    sequence_state = {"move_chains": {"a": {}, "b": {}}}
    setup_event = {
        "actor": "a", "round": 1, "tick": 3, "outcome": "landed", "move_id": "single_jab",
        "move": {"follow_up_id": "one_two", "sequence_source_id": "", "sequence_step": 0},
    }
    engine.update_move_sequence(sequence_state, setup_event)
    require(sequence_state["move_chains"]["a"]["next_move_id"] == "one_two"
            and setup_event["move_sequence"]["step"] == 0,
            "A successful setup did not create a bounded cross-exchange sequence")

    unreachable = []
    reachability_artist = synthetic_fighter("Move Reachability Artist", 94, "MMA Generalist", "Dynamic Attacker", 43)
    reachability_artist.detailed_skills = {key: 99 for keys in DETAILED_SKILL_GROUPS.values() for key in keys}
    reachability_opponent = synthetic_fighter("Move Reachability Opponent", 80, "MMA Generalist", "Dynamic Attacker", 44)
    for definition in MOVE_REGISTRY.values():
        reachability_artist.style = (
            definition.preferred_styles[0]
            if definition.preferred_styles else "MMA Generalist"
        )
        reachability_artist.secondary_style = ""
        reachability_artist.signature_moves = [definition.move_id]
        position = sorted(definition.positions)[0]
        target = sorted(definition.targets)[0] if definition.targets else ""
        found = False
        for tick in range(1, 321):
            state = {"round": 2, "tick": tick, "plans": {}, "move_reads": {}, "counter_window": None}
            if "counter" in definition.tags:
                state["counter_window"] = {"fighter": reachability_artist.name, "source_counter_risk": 1.2}
            selected = engine.select_exchange_move(
                reachability_artist, reachability_opponent, definition.parent_action, position, target, state,
            )
            if selected["move_id"] == definition.move_id:
                found = True
                break
        if not found:
            unreachable.append(definition.move_id)
    require(not unreachable, f"Registered moves cannot be selected even by a supported signature specialist: {unreachable}")


def test_versioned_tuning_defaults_and_dead_finish_paths_are_removed():
    config = SeedMixin()
    migrated_fight = config.normalize_engine_settings({"ko_power": 9, "damage": "bad", "gate_multiplier": 1.35})
    migrated_business = config.normalize_business_settings(None, {"gate_multiplier": 1.35})
    require(migrated_fight["config_version"] == FIGHT_ENGINE_CONFIG_VERSION
            and migrated_fight["ko_power"] == 2.0 and migrated_fight["damage"] == 1.0,
            "Versioned fight settings did not clamp or repair legacy values")
    require("gate_multiplier" not in migrated_fight and migrated_business["gate_multiplier"] == 1.35,
            "Legacy gate tuning was not migrated out of fight mechanics")
    require(not hasattr(FightEngineMixin, "finish_chance") and not hasattr(FightEngineMixin, "finish_method"),
            "A duplicate dead finish-resolution path remains callable")
    require(KO_METHODS == frozenset({"KO", "TKO", "Doctor Stoppage", "Corner Stoppage"})
            and SUBMISSION_METHODS == frozenset({"Submission", "Technical Submission"})
            and FINISH_METHODS == KO_METHODS | SUBMISSION_METHODS | frozenset({"Injury Stoppage"})
            and KNOCKOUT_AWARD_METHODS == frozenset({"KO", "TKO"}),
            "Canonical finish-method families changed or became inconsistent")
    fighter = synthetic_fighter("Technical Decision Stats", 72, "MMA Generalist", "Dynamic Attacker", 4)
    fighter.last_fight_stats = {"sig": 1, "td": 0, "control_secs": 0, "knockdowns": 0, "sub_att": 0, "rounds": 2}
    fighter.career_finishes = 0
    FightAuditHarness().commit_career_stats(fighter, "Technical Decision", won=True)
    require(fighter.career_finishes == 0 and fighter.career_stat_fights == 1,
            "Technical decision participation was incorrectly classified as a finish")

    expected_counters = {
        "Doctor Stoppage": (1, 1, 0),
        "Corner Stoppage": (1, 1, 0),
        "Injury Stoppage": (1, 0, 0),
        "Submission": (1, 0, 1),
        "Technical Submission": (1, 0, 1),
    }
    for index, (method, expected) in enumerate(expected_counters.items(), start=20):
        winner = synthetic_fighter(f"{method} Stats", 72, "MMA Generalist", "Dynamic Attacker", index)
        winner.last_fight_stats = {
            "sig": 1, "td": 0, "control_secs": 0, "knockdowns": 0,
            "sub_att": 1 if method in SUBMISSION_METHODS else 0, "rounds": 2,
        }
        winner.career_finishes = winner.career_knockouts = winner.career_submissions = 0
        FightAuditHarness().commit_career_stats(winner, method, won=True)
        observed = (winner.career_finishes, winner.career_knockouts, winner.career_submissions)
        require(observed == expected,
                f"{method} career classification was {observed}, expected {expected}")

        tracker = AwardsMixin()
        tracker.month = tracker.week = 1
        tracker.season_stats = {}
        tracker.awards_history = []
        tracker.achievement_log = []
        tracker.inbox = []
        tracker.record_season_result(
            winner, fighter, method, 2, {"title": False, "main": False}, 50, "Audit FC",
        )
        season = tracker.season_bucket()["fighters"][winner.name]
        require(season["finishes"] == 1
                and season["kos"] == int(method in KO_METHODS)
                and season["subs"] == int(method in SUBMISSION_METHODS),
                f"{method} season classification disagreed with the canonical method families")

        winner.last_fight_stats = {"sig": 12, "knockdowns": 0, "sub_att": 0, "rounds": 2}
        fighter.last_fight_stats = {"sig": 10, "knockdowns": 0, "sub_att": 0, "rounds": 2}
        finish_score = WorldMixin.fight_excitement(
            FightAuditHarness(), winner, fighter, winner, fighter, method, 2, {}, hype=10,
        )
        decision_score = WorldMixin.fight_excitement(
            FightAuditHarness(), winner, fighter, winner, fighter, "Decision", 2, {}, hype=10,
        )
        require(finish_score == decision_score + 18,
                f"{method} did not receive the canonical finish excitement bonus")


def test_authored_finish_banks_and_kick_categories_are_reachable_and_rng_safe():
    engine = FightAuditHarness()
    actor = synthetic_fighter("Finish Bank A", 82, "BJJ", "Submission Hunter", 60)
    defender = synthetic_fighter("Finish Bank B", 80, "Kickboxer", "Counter", 61)
    calls = []
    original_phrase = engine.fight_phrase

    def recorded_phrase(category, red, blue, **context):
        calls.append((category, context))
        return original_phrase(category, red, blue, **context)

    engine.fight_phrase = recorded_phrase
    submission = engine.submission_finish_text(
        actor, defender, {"name": "rear-naked choke", "choke": True}, technical=False,
    )
    require(calls[-1] == ("submission_finish", {"technique": "rear-naked choke"})
            and "rear-naked choke" in submission.casefold(),
            "Ordinary submission finishes bypassed their authored category or lost the technique")

    state = {
        "position": "back control", "round": 3, "official_time": "1:17",
        "fighter_keys": {id(actor): "a", id(defender): "b"},
        "last_move_payload": {"name": "Rear-naked choke", "target": "neck"},
        "trace": [],
    }
    authored_detail = f"{actor.name} traps {defender.name} and forces the tap with a rear-naked choke."
    sequence = engine.finish_sequence(actor, defender, "Submission", authored_detail, state)
    require(authored_detail in sequence and sequence.casefold().count("official result") == 1,
            "Submission finish continuity discarded authored detail or duplicated the result")

    ko_state = {
        **state,
        "position": "pocket", "finish_category": "walkoff_ko",
        "trace": [{
            "type": "exchange", "round": 3, "tick": 5, "actor": "a", "defender": "b",
            "action": "power_punch", "move_id": "overhand_right",
            "move": {"name": "Overhand right", "target": "head", "tags": ("punch",)},
            "flags": {"knockdown": True, "hurt": True},
            "damage_delta": {"a": 0, "b": 14}, "hurt_delta": {"a": 0, "b": 14},
            "knockdown_delta": {"a": 1, "b": 0}, "sig_delta": 1,
            "round_metric_delta": {"a": {"impact": 14}, "b": {"impact": 0}},
        }],
        "tick": 5,
    }
    walkoff_detail = f"{actor.name} lands once and walks away before {defender.name} hits the canvas."
    ko_sequence = engine.finish_sequence(actor, defender, "KO", walkoff_detail, ko_state)
    require("overhand right" in ko_sequence.casefold() and "walks away" in ko_sequence.casefold()
            and ko_sequence.casefold().count("official result") == 1,
            "Walk-off behavior was discarded or disconnected from the recorded finishing move")

    require(engine.kick_knockdown_categories("high") == ("head_kick_ko", "knockdown")
            and engine.kick_knockdown_categories("body") == (
                "body_kick_knockdown", "body_kick_knockdown")
            and engine.kick_knockdown_categories("leg") == (
                "leg_kick_knockdown", "leg_kick_knockdown"),
            "Kick knockdowns regressed to a generic injury-stoppage identity")

    serious_cut = {
        "count": 3, "max_severity": 3, "max_bleeding": 3,
        "vision_risk": True, "worst_location": "left eyebrow",
    }
    require(not engine.doctor_stoppage_window({"tick": 7, "ticks_per_round": 8}, serious_cut)
            and engine.doctor_stoppage_window({"tick": 8, "ticks_per_round": 8}, serious_cut)
            and not engine.doctor_stoppage_window(
                {"tick": 8, "ticks_per_round": 8}, {**serious_cut, "count": 2}),
            "Doctor checks did not remain limited to between-round serious-cut evidence")

    engine._fight_mechanics_rng = random.Random(998)
    engine._fight_presentation_rng = random.Random(1)
    mechanics_before = engine._fight_mechanics_rng.getstate()
    category = engine.knockdown_finish_category("power_punch", 8)
    require(category == "walkoff_ko" and engine._fight_mechanics_rng.getstate() == mechanics_before,
            "Walk-off copy is unreachable for a normal knockdown or consumed combat RNG")
    presentation_before = engine._fight_presentation_rng.getstate()
    require(engine.knockdown_finish_category("kick", 12) == "ko_finish"
            and engine._fight_presentation_rng.getstate() == presentation_before,
            "Non-punch finish presentation consumed an unrelated RNG stream")

    flush_engine = FightAuditHarness()
    flush_engine._fight_mechanics_rng = random.Random(1)
    flush_engine._fight_presentation_rng = random.Random(9)
    flush_calls = []
    flush_engine.fight_phrase = lambda category, *_args, **context: (
        flush_calls.append(category) or f"{category}:{context.get('technique', '')}"
    )
    flush_state = {
        "fighter_keys": {id(actor): "a", id(defender): "b"},
        "danger": {"a": 0, "b": 0}, "damage": {"a": 0, "b": 0},
        "head": {"a": 0, "b": 0}, "head_trauma": {"a": 0, "b": 0},
        "knockdowns": {"a": 0, "b": 0},
    }
    flush_round_stats = {"a": {"danger": 0}, "b": {"danger": 0}}
    flush_engine.deliver_flush_knockout(actor, defender, "power_punch", flush_state, flush_round_stats)
    instant_detail = flush_state["instant_finish"][3]
    require(flush_state["finish_category"] == "walkoff_ko"
            and flush_calls[:2] == ["signature_ko", "walkoff_ko"]
            and "signature_ko" in instant_detail and "walkoff_ko" in instant_detail,
            "Flush-KO trace selected a walk-off finish without exposing authored walk-off copy")


def test_expanded_standing_combinations_and_finishers_are_reachable_and_causal():
    combination_weapons = {
        "jab_cross_lead_hook": ("jab", "cross", "lead hook"),
        "jab_uppercut_lead_hook": ("jab", "rear uppercut", "lead hook"),
        "double_jab_body_cross": ("body jab", "body jab", "cross to head"),
        "cross_body_hook_lead_hook": ("cross", "body hook", "lead hook to head"),
        "stance_shift_cross_hook": ("stance-shift cross", "lead hook"),
        "boxing_pressure_flurry": ("jab", "cross", "lead hook", "rear cross", "lead hook"),
        "double_jab_low_kick": ("jab", "jab", "outside low kick"),
        "cross_hook_body_kick": ("cross", "lead hook", "body kick"),
        "jab_cross_rear_knee": ("jab", "cross", "rear knee to head"),
        "hook_elbow_knee": ("lead hook", "rear elbow", "lead knee"),
    }
    combination_ids = set(combination_weapons)
    finisher_ids = {
        "rear_uppercut", "corkscrew_cross", "spinning_backfist",
        "axe_kick", "jumping_front_kick", "switch_flying_knee",
    }
    require(combination_ids | finisher_ids <= set(MOVE_REGISTRY),
            "The expanded standing catalogue lost a required authored technique")
    require(all("combination" in MOVE_REGISTRY[move_id].tags
                or "mixed-combination" in MOVE_REGISTRY[move_id].tags
                for move_id in combination_ids),
            "An authored standing sequence is not classified as a combination")
    require(all("finisher" in MOVE_REGISTRY[move_id].tags
                and set(MOVE_REGISTRY[move_id].positions) <= {"range", "pocket"}
                for move_id in finisher_ids),
            "An authored finisher is not a legal standing finishing technique")

    engine = FightAuditHarness()
    actor = synthetic_fighter("Expanded Standing Artist", 94, "MMA Generalist", "Dynamic Attacker", 80)
    defender = synthetic_fighter("Expanded Standing Target", 88, "MMA Generalist", "Cautious", 81)
    actor.detailed_skills = {key: 99 for key in actor.detailed_skills}
    mechanics_before = engine.fight_mechanics_rng().getstate()
    presentation_before = engine.fight_presentation_rng().getstate()
    for move_id in sorted(combination_ids | finisher_ids):
        definition = MOVE_REGISTRY[move_id]
        actor.signature_moves = [move_id]
        selected = None
        target = sorted(definition.targets)[0] if definition.targets else ""
        for tick in range(1, 401):
            state = {"round": 2, "tick": tick, "plans": {}, "move_reads": {}, "counter_window": None}
            candidate = engine.select_exchange_move(
                actor, defender, definition.parent_action, "range", target, state,
            )
            if candidate["move_id"] == move_id:
                selected = candidate
                break
        require(selected is not None, f"Expanded standing technique {move_id} is unreachable")
        if move_id in combination_ids:
            components = engine.exchange_combination_components(
                definition.parent_action, 12, 7, target, move_id,
            )
            require(len(components) == 12
                    and [row["sequence"] for row in components] == list(range(1, 13))
                    and sum(row["landed"] for row in components) == 7
                    and tuple(row["weapon"] for row in components[:len(combination_weapons[move_id])])
                    == combination_weapons[move_id],
                    f"Standing combination {move_id} lost reconciled component evidence")
    require(engine.fight_mechanics_rng().getstate() == mechanics_before
            and engine.fight_presentation_rng().getstate() == presentation_before,
            "Expanded standing technique selection consumed a fight RNG stream")

    actor.signature_moves = []
    selected_finishers = 0
    for tick in range(1, 1001):
        move = engine.select_exchange_move(
            actor, defender, "power_punch", "range", "head",
            {"round": 2, "tick": tick, "plans": {}, "move_reads": {}, "counter_window": None},
        )
        selected_finishers += move["move_id"] in finisher_ids
    require(0 < selected_finishers <= 160,
            "Authored finishers are absent or no longer bounded beneath ordinary standing offense")

    causal_state = {
        "fighter_keys": {id(actor): "a", id(defender): "b"},
        "position": "pocket", "round": 2, "tick": 7, "official_time": "2:11",
        "flush_knockout": True, "finish_category": "walkoff_ko",
        "trace": [{
            "type": "exchange", "round": 2, "tick": 7, "actor": "a", "defender": "b",
            "action": "power_punch", "move_id": "spinning_backfist",
            "move": {"name": "spinning backfist", "target": "head",
                     "tags": ("strike", "punch", "power", "head", "finisher")},
            "flags": {"knockdown": True, "hurt": True},
            "damage_delta": {"a": 0, "b": 16}, "hurt_delta": {"a": 0, "b": 16},
            "knockdown_delta": {"a": 1, "b": 0}, "sig_delta": 1,
            "round_metric_delta": {"a": {"impact": 16}, "b": {"impact": 0}},
        }],
    }
    finish = engine.finish_sequence(
        actor, defender, "KO",
        f"{actor.name} lands an uppercut and knocks {defender.name} out.", causal_state,
    )
    require("spinning backfist" in finish.casefold() and "uppercut" not in finish.casefold()
            and finish.casefold().count("official result") == 1,
            "A new standing finisher was disconnected from, or contradicted by, the official finish sequence")
    causal_state["flush_knockout"] = False
    causal_state["finish_category"] = "ko_finish"
    ordinary_finish = engine.finish_sequence(
        actor, defender, "KO",
        f"{actor.name} lands a shovel uppercut and knocks {defender.name} out.", causal_state,
    )
    require("spinning backfist" in ordinary_finish.casefold()
            and "uppercut" not in ordinary_finish.casefold(),
            "A normal KO retained a contradictory legacy technique beside its causal registry move")


def test_expanded_ground_catalogue_is_position_legal_reachable_and_causal():
    ground_strike_weapons = {
        "guard_posture_elbows": ("postured punch", "short elbow"),
        "half_guard_crossface_strikes": ("crossface punch", "short elbow"),
        "crucifix_elbows": ("short crucifix elbow",),
        "mounted_hammerfist_flurry": ("hammerfist", "straight punch", "hammerfist"),
        "back_control_short_punches": ("short punch", "punch around the guard"),
        "turtle_wrist_ride_strikes": ("wrist-ride punch", "hammerfist", "short elbow"),
    }
    transition_ids = {
        "headquarters_pass", "body_lock_pass", "underhook_half_guard_pass",
        "knee_on_belly_climb", "gift_wrap_transition",
    }
    sweep_ids = {"scissor_sweep", "flower_sweep", "waiter_sweep", "lockdown_sweep"}
    escape_ids = {
        "post_and_build_getup", "tripod_standup", "elbow_knee_guard_recovery",
        "back_control_handfight_recovery", "closed_guard_retention",
    }
    control_ids = {
        "half_guard_crossface_control", "mount_grapevine_control", "body_triangle_back_control",
    }
    new_ground_ids = set(ground_strike_weapons) | transition_ids | sweep_ids | escape_ids | control_ids
    require(len(new_ground_ids) == 23 and new_ground_ids <= set(MOVE_REGISTRY),
            "The expanded ground catalogue lost a required technique")
    ground_positions = {
        "guard", "half guard", "side control", "mount", "back control", "turtle",
        "front headlock", "leg entanglement",
    }
    require(all("ground" in MOVE_REGISTRY[move_id].tags
                and set(MOVE_REGISTRY[move_id].positions) <= ground_positions
                for move_id in new_ground_ids),
            "An expanded ground technique is tagged for an illegal standing or clinch position")

    engine = FightAuditHarness()
    actor = synthetic_fighter("Expanded Ground Artist", 94, "BJJ", "Submission Hunter", 82)
    defender = synthetic_fighter("Expanded Ground Target", 88, "Wrestler", "Control", 83)
    actor.detailed_skills = {key: 99 for key in actor.detailed_skills}
    mechanics_before = engine.fight_mechanics_rng().getstate()
    presentation_before = engine.fight_presentation_rng().getstate()
    for move_id in sorted(new_ground_ids):
        definition = MOVE_REGISTRY[move_id]
        actor.signature_moves = [move_id]
        selected = None
        for position in sorted(definition.positions):
            for tick in range(1, 321):
                candidate = engine.select_exchange_move(
                    actor, defender, definition.parent_action, position, "",
                    {"round": 2, "tick": tick, "plans": {}, "move_reads": {}, "counter_window": None},
                )
                if candidate["move_id"] == move_id:
                    selected = candidate
                    break
            if selected:
                break
        require(selected is not None, f"Expanded ground technique {move_id} is unreachable")
        require(selected["parent_action"] == definition.parent_action,
                f"Expanded ground technique {move_id} escaped its broad action boundary")
        if move_id in ground_strike_weapons:
            components = engine.exchange_combination_components(
                "ground_strikes", 18, 10, "head", move_id,
            )
            expected = ground_strike_weapons[move_id]
            require(len(components) == 18
                    and [row["sequence"] for row in components] == list(range(1, 19))
                    and sum(row["landed"] for row in components) == 10
                    and tuple(row["weapon"] for row in components[:len(expected)]) == expected,
                    f"Ground striking sequence {move_id} lost its factual component mapping")
    require(engine.fight_mechanics_rng().getstate() == mechanics_before
            and engine.fight_presentation_rng().getstate() == presentation_before,
            "Expanded ground technique selection consumed a fight RNG stream")

    branch_state = {"move_chains": {"a": {}, "b": {}}}
    branch_event = {
        "actor": "a", "round": 2, "tick": 4, "outcome": "landed",
        "move_id": "mounted_hammerfist_flurry", "position_after": "mount",
        "defense": {"tags": ("frame",)},
        "move": {
            "follow_up_ids": ("arm_triangle", "top_armbar"),
            "sequence_source_id": "", "sequence_step": 0,
        },
    }
    engine.update_move_sequence(branch_state, branch_event)
    require(branch_state["move_chains"]["a"]["next_move_id"] == "top_armbar"
            and branch_state["move_chains"]["a"]["branch_reason"] == "defensive-reaction",
            "Mounted ground offense did not retain its legal reaction-based submission branch")
    control_state = {"move_chains": {"a": {}, "b": {}}}
    control_event = {
        "actor": "a", "round": 2, "tick": 5, "outcome": "control",
        "move_id": "half_guard_crossface_control", "position_after": "half guard",
        "defense": {"tags": ()},
        "move": {
            "tags": ("ground", "control", "pressure", "underhook"),
            "follow_up_ids": ("underhook_half_guard_pass",),
            "sequence_source_id": "", "sequence_step": 0,
        },
    }
    engine.update_move_sequence(control_state, control_event)
    require(control_state["move_chains"]["a"]["next_move_id"] == "underhook_half_guard_pass",
            "Effective registered ground control did not seed its ordinary next-action transition")

    causal_state = {
        "fighter_keys": {id(actor): "a", id(defender): "b"},
        "position": "mount", "round": 3, "tick": 6, "official_time": "1:44",
        "trace": [{
            "type": "exchange", "round": 3, "tick": 6, "actor": "a", "defender": "b",
            "action": "ground_strikes", "move_id": "mounted_hammerfist_flurry",
            "move": {"name": "mounted hammerfist flurry", "target": "head",
                     "tags": ("ground", "strike", "punch", "combination", "mount", "power")},
            "flags": {"knockdown": False, "hurt": True},
            "damage_delta": {"a": 0, "b": 18}, "hurt_delta": {"a": 0, "b": 18},
            "knockdown_delta": {"a": 0, "b": 0}, "sig_delta": 4,
            "round_metric_delta": {"a": {"impact": 18}, "b": {"impact": 0}},
        }],
    }
    finish = engine.finish_sequence(
        actor, defender, "TKO", f"{actor.name} lands generic punches until the stoppage.", causal_state,
    )
    require("mounted hammerfist flurry" in finish.casefold()
            and "generic punches" not in finish.casefold()
            and finish.casefold().count("official result") == 1,
            "A ground TKO was disconnected from its causal registered technique")


def test_every_supported_style_has_an_exclusive_authored_combination():
    definitions = [
        definition for definition in MOVE_REGISTRY.values()
        if "style-combination" in definition.tags
    ]
    by_style = {
        definition.preferred_styles[0]: definition
        for definition in definitions
        if len(definition.preferred_styles) == 1
    }
    require(set(by_style) == set(STYLES) and len(definitions) == len(STYLES),
            "Every supported MMA style must own exactly one authored combination")
    require(all(len(definition.components) >= 3 for definition in definitions),
            "A style combination lost its ordered component evidence")

    engine = FightAuditHarness()
    mechanics_before = engine.fight_mechanics_rng().getstate()
    presentation_before = engine.fight_presentation_rng().getstate()
    defender = synthetic_fighter("Style Combination Target", 88, "Well-Rounded", "Cautious", 990)
    defender.secondary_style = ""
    defender.detailed_skills = {key: 99 for key in defender.detailed_skills}

    for style_index, style in enumerate(STYLES):
        definition = by_style[style]
        actor = synthetic_fighter(f"{style} Combination Artist", 94, style, "Dynamic Attacker", 1000 + style_index)
        actor.secondary_style = ""
        actor.detailed_skills = {key: 99 for key in actor.detailed_skills}
        actor.signature_moves = [definition.move_id]
        position = "range" if "range" in definition.positions else sorted(definition.positions)[0]
        target = sorted(definition.targets)[0] if definition.targets else ""
        selected = None
        for tick in range(1, 501):
            state = {"round": 2, "tick": tick, "plans": {}, "move_reads": {}, "counter_window": None}
            candidate = engine.select_exchange_move(
                actor, defender, definition.parent_action, position, target, state,
            )
            if candidate["move_id"] == definition.move_id:
                selected = candidate
                break
        require(selected is not None, f"{style} authored combination is unreachable")
        require(tuple(selected["components"]) == definition.components,
                f"{style} authored combination lost its component payload")

        if definition.parent_action in {"jab", "power_punch", "kick", "dirty_boxing", "ground_strikes"}:
            evidence = engine.exchange_combination_components(
                definition.parent_action, 9, 5, target, definition.move_id,
            )
            require(tuple(row["weapon"] for row in evidence[:len(definition.components)]) == definition.components
                    and sum(row["landed"] for row in evidence) == 5,
                    f"{style} combination components did not reconcile with aggregate striking")

        unrelated_style = next(candidate for candidate in STYLES if candidate != style)
        outsider = synthetic_fighter(
            f"{unrelated_style} Outsider", 94, unrelated_style, "Dynamic Attacker", 2000 + style_index,
        )
        outsider.secondary_style = ""
        outsider.detailed_skills = {key: 99 for key in outsider.detailed_skills}
        outsider.signature_moves = [definition.move_id]
        for tick in range(1, 41):
            candidate = engine.select_exchange_move(
                outsider, defender, definition.parent_action, position, target,
                {"round": 2, "tick": tick, "plans": {}, "move_reads": {}, "counter_window": None},
            )
            require(candidate["move_id"] != definition.move_id,
                    f"{style} combination leaked to unrelated style {unrelated_style}")

    require(engine.fight_mechanics_rng().getstate() == mechanics_before
            and engine.fight_presentation_rng().getstate() == presentation_before,
            "Style-specific combination selection consumed fight RNG")


def test_every_supported_style_has_an_exclusive_causal_finisher():
    definitions = [
        definition for definition in MOVE_REGISTRY.values()
        if "style-finisher" in definition.tags
    ]
    by_style = {
        definition.preferred_styles[0]: definition
        for definition in definitions
        if len(definition.preferred_styles) == 1
    }
    require(set(by_style) == set(STYLES) and len(definitions) == len(STYLES),
            "Every supported MMA style must own exactly one authored finisher")
    require(all(set(definition.tags).intersection({"strike", "submission"}) for definition in definitions),
            "A style finisher is neither a finishing strike nor submission")

    engine = FightAuditHarness()
    mechanics_before = engine.fight_mechanics_rng().getstate()
    presentation_before = engine.fight_presentation_rng().getstate()
    defender = synthetic_fighter("Style Finisher Target", 88, "Well-Rounded", "Cautious", 2990)
    defender.secondary_style = ""
    defender.detailed_skills = {key: 99 for key in defender.detailed_skills}

    for style_index, style in enumerate(STYLES):
        definition = by_style[style]
        actor = synthetic_fighter(f"{style} Finisher Artist", 96, style, "Dynamic Attacker", 3000 + style_index)
        actor.secondary_style = ""
        actor.detailed_skills = {key: 99 for key in actor.detailed_skills}
        actor.signature_moves = [definition.move_id]
        position = "range" if "range" in definition.positions else sorted(definition.positions)[0]
        target = sorted(definition.targets)[0] if definition.targets else ""
        selected = None
        for tick in range(1, 1201):
            candidate = engine.select_exchange_move(
                actor, defender, definition.parent_action, position, target,
                {"round": 2, "tick": tick, "plans": {}, "move_reads": {}, "counter_window": None},
            )
            if candidate["move_id"] == definition.move_id:
                selected = candidate
                break
        require(selected is not None, f"{style} authored finisher is unreachable")

        outsider_style = next(candidate for candidate in STYLES if candidate != style)
        outsider = synthetic_fighter(
            f"{outsider_style} Finisher Outsider", 96, outsider_style, "Dynamic Attacker", 4000 + style_index,
        )
        outsider.secondary_style = ""
        outsider.detailed_skills = {key: 99 for key in outsider.detailed_skills}
        outsider.signature_moves = [definition.move_id]
        for tick in range(1, 51):
            candidate = engine.select_exchange_move(
                outsider, defender, definition.parent_action, position, target,
                {"round": 2, "tick": tick, "plans": {}, "move_reads": {}, "counter_window": None},
            )
            require(candidate["move_id"] != definition.move_id,
                    f"{style} finisher leaked to unrelated style {outsider_style}")

        tags = set(definition.tags)
        method = "Submission" if "submission" in tags else "TKO" if "ground" in tags else "KO"
        state = {
            "fighter_keys": {id(actor): "a", id(defender): "b"},
            "position": position, "round": 2, "tick": 7, "official_time": "2:31",
            "last_move_payload": selected,
            "trace": [{
                "type": "exchange", "round": 2, "tick": 7, "actor": "a", "defender": "b",
                "action": definition.parent_action, "move_id": definition.move_id, "move": selected,
                "flags": {"hurt": method in {"KO", "TKO"}}, "damage_delta": {"b": 8},
                "hurt_delta": {"b": 6}, "sig_delta": 1,
                "round_metric_delta": {"a": {"impact": 8}},
            }],
        }
        finish = engine.finish_sequence(actor, defender, method, "", state)
        require(definition.name.casefold() in finish.casefold()
                and finish.casefold().count("official result") == 1,
                f"{style} finisher was disconnected from the official finish sequence")

    require(engine.fight_mechanics_rng().getstate() == mechanics_before
            and engine.fight_presentation_rng().getstate() == presentation_before,
            "Style-specific finisher selection consumed fight RNG")


def test_move_release_report_covers_groups_and_registry_safety():
    report = build_move_report(seeds_per_matchup=20, minimum_group_sample=30)
    require(report["fight_count"] == 880,
            "Move release report lost its representative 880-fight corpus")
    require(report["registered_move_count"] == len(MOVE_REGISTRY),
            "Move release report did not cover the canonical registry")
    require(set(report["groups"]) == {"styles", "behaviours", "tiers", "stances", "stance_matchups"},
            "Move release report omitted a required distribution dimension")
    require(all(report["groups"][dimension] for dimension in report["groups"]),
            "Move release report produced an empty required distribution dimension")
    diagnostics = report["diagnostics"]
    for key in (
        "unreachable_registry_moves", "illegal_counter_uses", "illegal_position_uses",
        "illegal_target_uses", "unsafe_energy_moves", "indistinct_style_pairs",
        "unknown_defense_ids",
        "unreachable_defense_ids",
    ):
        require(not diagnostics[key], f"Move release report found unsafe registry evidence: {key}")
    require(all(row["sample_ok"] for row in report["groups"]["stance_matchups"].values()),
            "A stance matchup lacked a release-report sample")
    expanded_standing_ids = {
        "jab_cross_lead_hook", "jab_uppercut_lead_hook", "double_jab_body_cross",
        "cross_body_hook_lead_hook", "stance_shift_cross_hook", "boxing_pressure_flurry",
        "double_jab_low_kick", "cross_hook_body_kick", "jab_cross_rear_knee", "hook_elbow_knee",
        "rear_uppercut", "corkscrew_cross", "spinning_backfist", "axe_kick",
        "jumping_front_kick", "switch_flying_knee",
    }
    require(not expanded_standing_ids.intersection(diagnostics["dead_moves_in_sample"]),
            "A new standing combination or finisher never appeared in representative complete fights")
    style_combination_ids = {
        move_id for move_id, definition in MOVE_REGISTRY.items()
        if "style-combination" in definition.tags
    }
    require(len(style_combination_ids) == len(STYLES)
            and not style_combination_ids.intersection(diagnostics["dead_moves_in_sample"]),
            "A supported style lost its authored combination in representative complete fights")
    style_finisher_ids = {
        move_id for move_id, definition in MOVE_REGISTRY.items()
        if "style-finisher" in definition.tags
    }
    require(len(style_finisher_ids) == len(STYLES)
            and not style_finisher_ids.intersection(diagnostics["dead_moves_in_sample"]),
            "A supported style lost its authored finisher in representative complete fights")
    ordinary_ground_ids = {
        "guard_posture_elbows", "half_guard_crossface_strikes", "crucifix_elbows",
        "mounted_hammerfist_flurry", "back_control_short_punches", "headquarters_pass",
        "body_lock_pass", "underhook_half_guard_pass", "knee_on_belly_climb",
        "gift_wrap_transition", "scissor_sweep", "flower_sweep", "waiter_sweep",
        "lockdown_sweep", "post_and_build_getup", "tripod_standup",
        "elbow_knee_guard_recovery", "back_control_handfight_recovery",
        "closed_guard_retention",
        "half_guard_crossface_control", "mount_grapevine_control", "body_triangle_back_control",
    }
    require(not ordinary_ground_ids.intersection(diagnostics["dead_moves_in_sample"]),
            "A common-position ground addition never appeared in representative complete fights")


def test_specialist_transitions_occur_in_complete_fights():
    report = build_specialist_transition_report()
    require(report["fight_count"] == 720,
            "Specialist transition report lost its deterministic sample size")
    require(not report["diagnostics"]["missing_required_positions"],
            "A specialist position never appeared in complete fights")
    require(not report["diagnostics"]["missing_required_action_families"],
            "A specialist transition produced no legal follow-up action in complete fights")
    require(report["totals"]["moves"].get("turtle_wrist_ride_strikes", 0) > 0,
            "The turtle-specific wrist-ride striking chain never appeared in complete specialist fights")


def test_defense_mastery_stance_branching_and_round_analysis():
    engine = FightAuditHarness()
    require(not DEFENSE_REGISTRY_ERRORS and len(DEFENSE_REGISTRY) == 18,
            "Named defensive registry failed validation or lost expected coverage")
    a = synthetic_fighter("Systems A", 88, "Boxer", "Counter", 71)
    b = synthetic_fighter("Systems B", 86, "Wrestler", "Pressure", 72)
    a.detailed_skills.update({"footwork": 90, "adaptability": 90, "guard_defence": 90, "reflexes": 90})
    state = {
        "fighter_keys": {id(a): "a", id(b): "b"}, "round": 1, "tick": 8,
        "plans": engine.fight_plan_state(a, b, {"fight_plans": {a.fighter_id: "Counter striking"}}),
        "current_stance": {"a": "Orthodox", "b": "Orthodox"},
        "stance_switch_tick": {"a": -99, "b": -99}, "stance_switches": {"a": [], "b": []},
    }
    for tick in range(1, 20):
        state["tick"] = tick
        engine.update_dynamic_stance(a, b, state)
    require(state["stance_switches"]["a"], "A high-skill fighter never made a deliberate stance change")

    move = engine.select_exchange_move(b, a, "shoot", "range", "", state)
    defense = engine.select_exchange_defense(a, move, "range", state)
    require(defense["defense_id"] in DEFENSE_REGISTRY and not defense["generic"],
            "A legal wrestling attack did not receive a named defensive technique")

    branch_state = {"move_chains": {"a": {}, "b": {}}}
    branch_event = {
        "actor": "a", "round": 1, "tick": 2, "outcome": "landed", "move_id": "single_jab",
        "position_after": "range", "defense": {"tags": ("evasion",)},
        "move": {"follow_up_ids": ("one_two", "jab_to_shot"), "sequence_source_id": "", "sequence_step": 0},
    }
    engine.update_move_sequence(branch_state, branch_event)
    require(branch_state["move_chains"]["a"]["next_move_id"] == "jab_to_shot"
            and branch_state["move_chains"]["a"]["branch_reason"] == "defensive-reaction",
            "An evasive defense did not select the alternate legal sequence branch")

    engine.month = 12
    a.signature_moves = []
    a.move_mastery = {
        move_id: 74 for move_id, definition in MOVE_REGISTRY.items()
        if set(definition.tags).intersection({"punch", "combination", "counter"})
    }
    WorldMixin.develop_fighter_move_mastery(engine, a, 8, "Boxing")
    require(a.signature_moves and all(a.move_mastery[move_id] >= 75 for move_id in a.signature_moves),
            "Camp mastery did not develop into a learned signature")
    a.age = a.prime_end + 4
    learned_move = a.signature_moves[0]
    before = a.move_mastery[learned_move]
    WorldMixin.decline_fighter_move_mastery(a)
    require(a.move_mastery[learned_move] == before - 1, "Veteran technique mastery did not decline")

    trace = [{
        "type": "exchange", "round": 1, "actor": "a", "defender": "b", "move_id": "one_two",
        "move_family": "Boxing", "outcome": "landed", "defense_id": defense["defense_id"],
        "move_sequence": {"completed_follow_up": True, "source_move_id": "single_jab", "step": 2,
                          "branch_reason": "primary-continuation"},
    }]
    analysis = engine.build_round_analysis(trace, state["plans"], state["stance_switches"])
    require(analysis[0]["corners"]["a"]["moves"]["one_two"] == 1
            and analysis[0]["corners"]["b"]["defenses"][defense["defense_id"]] == 1,
            "Per-round explorer data did not reconcile move and defense evidence")


def _run_suite():
    test_audited_fight_is_deterministic_and_non_mutating()
    test_trace_metrics_are_internally_consistent()
    test_native_structured_result_matches_legacy_result()
    test_every_detailed_attribute_has_a_fight_role()
    test_frozen_baseline_contract_and_representative_determinism()
    test_commentary_bank_does_not_change_mechanics()
    test_fact_driven_exchange_commentary_and_personality_contract()
    test_trait_specific_commentary_is_complete_contextual_and_rng_pure()
    test_camp_specific_commentary_is_fact_driven_bounded_and_rng_pure()
    test_commentary_outcome_variants_are_deterministic_and_rng_pure()
    test_commentary_quality_gate_handles_missing_and_conflicting_facts()
    test_commentary_uses_only_available_fighter_and_fight_context()
    test_commentary_hides_engine_placeholders_and_denied_transitions()
    test_commentary_stats_style_submission_and_referee_facts()
    test_technical_personality_analysis_is_rate_limited()
    test_finish_attribution_walks_back_to_causal_trace_evidence()
    test_legacy_no_plan_corner_advice_does_not_repeat_consecutively()
    test_commentary_personalities_preserve_mechanics()
    test_unassigned_plan_corner_advice_uses_visible_evidence()
    test_coach_feedback_is_personal_specific_and_rng_pure()
    test_finish_commentary_uses_current_move_and_one_official_result()
    test_random_streams_are_explicit_and_separate()
    test_trace_backed_judging_hierarchy_and_verdicts()
    test_repeated_foul_creates_visible_point_deduction()
    test_referee_profiles_technical_outcomes_and_review_flags()
    test_hurt_recovers_without_healing_trauma_and_medical_uses_same_evidence()
    test_location_damage_has_distinct_mechanical_effects()
    test_visible_damage_milestones_are_fact_driven_latched_and_rng_pure()
    test_fight_plans_change_actions_energy_targets_and_counter_windows()
    test_fight_plan_defaults_identity_ai_and_adaptation()
    test_fight_plan_evolves_from_repeated_move_evidence()
    test_exchange_counter_plan_produces_more_successful_counters()
    test_grappling_state_machine_ownership_paths_and_escapes()
    test_finish_distribution_comparator_rejects_drift()
    test_action_frequency_baseline_is_complete()
    test_move_registry_trace_contract_and_rng_purity()
    test_versioned_tuning_defaults_and_dead_finish_paths_are_removed()
    test_authored_finish_banks_and_kick_categories_are_reachable_and_rng_safe()
    test_expanded_standing_combinations_and_finishers_are_reachable_and_causal()
    test_every_supported_style_has_an_exclusive_authored_combination()
    test_every_supported_style_has_an_exclusive_causal_finisher()
    test_expanded_ground_catalogue_is_position_legal_reachable_and_causal()
    test_move_release_report_covers_groups_and_registry_safety()
    test_specialist_transitions_occur_in_complete_fights()
    test_defense_mastery_stance_branching_and_round_analysis()
    print("FIGHT ENGINE REGRESSION TEST PASSED")


def main():
    return test_support.run_suite("fight_engine", _run_suite)


if __name__ == "__main__":
    main()
