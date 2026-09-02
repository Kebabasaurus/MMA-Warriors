"""Run a deterministic, UI-free quality gate over representative MMA commentary."""

from __future__ import annotations

import json
import random
import re
import sys
import argparse
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from constants import FIGHT_COMMENTARY_PERSONALITIES, TRAITS
from events import EventMixin
from fight_engine_audit import FINISH_METHODS, FightAuditHarness, matchup_specs, synthetic_fighter


CLOCK_PATTERN = re.compile(r"^\s*\[\d{1,2}:\d{2}\]\s*(.*)$")
TECHNICAL_SUFFIX_PATTERN = re.compile(r"\[(?:target|defense|next)\b", re.IGNORECASE)
CRITICAL_TERMS = (
    "knockdown", "drops ", "is down", "submission", "tap", "cut ", "foul",
    "referee", "doctor", "stops the fight", "official result", "result:",
    "bruising", "reddening", "swelling", "welt", "limp", "midsection",
    "facial damage", "head damage", "body damage", "leg damage", "shifts weight",
)


def repeat_key(line):
    match = CLOCK_PATTERN.match(str(line))
    body = match.group(1) if match else str(line)
    body = re.sub(r"\b\d+(?::\d+)?\b", "#", body.casefold())
    return re.sub(r"\s+", " ", body).strip()


def normalized_exchange_call(event, line):
    """Remove bout-specific names while retaining technique and prose structure."""
    value = repeat_key(line)
    replacements = (
        (str(event.get("actor_name") or ""), "{actor}"),
        (str(event.get("defender_name") or ""), "{defender}"),
    )
    for source, target in sorted(replacements, key=lambda row: len(row[0]), reverse=True):
        if source:
            value = re.sub(re.escape(source.casefold()), target, value)
    return re.sub(r"\s+", " ", value).strip()


def causal_trace_event(trace, winner_key, round_no):
    excluded = ("composed_survival", "stand_up", "transition", "shot_entry")
    finish_tick = max(
        (int(event.get("tick", 0) or 0) for event in trace
         if event.get("type") == "exchange" and int(event.get("round", 0) or 0) == int(round_no)),
        default=0,
    )
    for event in reversed(trace):
        if event.get("type") != "exchange" or event.get("actor") != winner_key:
            continue
        if int(event.get("round", 0) or 0) != int(round_no):
            continue
        move_id = str(event.get("move_id") or "").casefold()
        action = str(event.get("action") or "").casefold()
        move_tags = {
            str(tag).casefold()
            for tag in ((event.get("move", {}) or {}).get("tags", ()) or ())
        }
        event_tick = int(event.get("tick", 0) or 0)
        if finish_tick and event_tick and finish_tick - event_tick > 3:
            continue
        flags = event.get("flags", {}) or {}
        defender = event.get("defender")
        damage = float((event.get("damage_delta", {}) or {}).get(defender, 0) or 0)
        hurt = float((event.get("hurt_delta", {}) or {}).get(defender, 0) or 0)
        knockdowns = int((event.get("knockdown_delta", {}) or {}).get(event.get("actor"), 0) or 0)
        impact = float(
            (event.get("round_metric_delta", {}) or {}).get(event.get("actor"), {}).get("impact", 0) or 0
        )
        causal = bool(flags.get("hurt") or flags.get("knockdown") or damage > 0 or hurt > 0
                      or knockdowns or (int(event.get("sig_delta", 0) or 0) > 0 and impact > 0))
        if not causal:
            continue
        if any(term in move_id or term in action for term in excluded) and not knockdowns:
            continue
        if ("entry" in move_id or "shot" in move_id or "entry" in move_tags) and not (
                knockdowns or move_tags.intersection({"slam", "suplex"})):
            continue
        return event
    return None


def trait_context_has_support(engine, event):
    """Independently verify the trace predicate behind a contextual trait call."""
    trait = str((event.get("actor_commentary_profile") or {}).get("trait") or "")
    kind = engine.exchange_commentary_kind(event)
    outcome = str(event.get("outcome") or "")
    effective = outcome in {
        "landed", "knockdown", "takedown", "submission_attempt", "position_change",
    }
    move = event.get("move", {}) or {}
    tags = {str(tag).casefold() for tag in (move.get("tags", ()) or ())}
    target = str(move.get("target") or "").casefold()
    round_no = int(event.get("round", 1) or 1)
    tick = int(event.get("tick", 1) or 1)
    streak = int(event.get("actor_streak", 0) or 0)
    damage = float(event.get("actor_damage_after", 0) or 0)
    gas = float(event.get("actor_gas_after", 0) or 0)
    defender_hurt_gain = float(
        (event.get("hurt_delta") or {}).get(event.get("defender"), 0) or 0
    )
    weight_cut_penalty = int(
        ((event.get("actor_commentary_profile") or {}).get("weight_cut_penalty", 0)) or 0
    )
    predicates = {
        "Fast Starter": round_no == 1 and tick <= 6 and effective,
        "Slow Starter": round_no == 1 and tick <= 6 and not effective,
        "Big Finisher": (kind == "knockdown" or defender_hurt_gain >= 6),
        "Fight Finisher": (kind == "knockdown" or defender_hurt_gain >= 6),
        "Knockout Artist": kind == "knockdown",
        "Submission Ace": outcome == "submission_attempt",
        "Pressure Fighter": streak >= 3 and effective,
        "Counter Specialist": kind == "countered",
        "Cardio Machine": round_no >= 2 and gas >= 35 and effective,
        "Comeback Artist": damage >= 20 and effective,
        "Iron Chin": damage >= 20 and effective,
        "Clutch": (round_no >= 3 or bool(event.get("championship"))) and effective,
        "Title Mentality": bool(event.get("championship")) and round_no >= 4 and effective,
        "Warrior Spirit": (damage >= 24 or gas < 32) and effective,
        "Momentum Fighter": streak >= 3 and effective,
        "Bad Weight Cut": weight_cut_penalty > 0 and gas < 32,
        "Adaptable": bool(event.get("plan_change")) and effective,
        "Body Hunter": target == "body" and effective,
        "Leg Kicker": target == "leg" and effective,
        "Cage Specialist": (
            event.get("position_before") == "cage" or event.get("position_after") == "cage"
        ) and effective,
        "Elbow Specialist": "elbow" in tags and effective,
        "Scramble Artist": str(event.get("action") or "") in {
            "sweep", "recover_guard", "stand_up",
        } and kind in {"escaped", "transitioned", "countered"},
    }
    return bool(predicates.get(trait, False))


def camp_context_has_support(engine, event):
    """Independently verify that at least one recorded camp specialty fits the exchange."""
    specialties = {
        str(value).strip().casefold()
        for value in (event.get("actor_camp_specialties", ()) or ()) if str(value).strip()
    }
    if not specialties:
        return False
    kind = engine.exchange_commentary_kind(event)
    outcome = str(event.get("outcome") or "")
    effective = outcome in {
        "landed", "knockdown", "takedown", "submission_attempt", "position_change",
    }
    move = event.get("move", {}) or {}
    tags = {str(tag).casefold() for tag in (move.get("tags", ()) or ())}
    action = str(event.get("action") or "")
    before = str(event.get("position_before") or "")
    after = str(event.get("position_after") or "")
    round_no = int(event.get("round", 1) or 1)
    gas = float(event.get("actor_gas_after", 0) or 0)
    predicates = {
        "boxing": effective and (
            bool(tags.intersection({"punch", "boxing", "hand-strike"}))
            or action in {"jab", "combination", "power_punch", "body_punch"}
        ),
        "kickboxing": effective and bool(tags.intersection({"kick", "knee", "mixed-combination"})),
        "wrestling": effective and (
            outcome == "takedown" or bool(tags.intersection({"wrestling", "takedown", "ride"}))
        ),
        "bjj": outcome == "submission_attempt" or (
            effective and after in engine.GROUND_POSITIONS
            and bool(tags.intersection({"submission", "transition", "guard"}))
        ),
        "sambo": effective and bool(tags.intersection({"trip", "throw", "leg-lock", "submission"})),
        "clinch": effective and (
            before in {"clinch", "cage"} or after in {"clinch", "cage"}
            or bool(tags.intersection({"clinch", "elbow", "knee", "cage"}))
        ),
        "gameplanning": effective and (bool(event.get("plan_change")) or kind == "countered"),
        "conditioning": round_no >= 2 and gas >= 35 and effective,
    }
    return any(predicates.get(specialty, False) for specialty in specialties)


def build_report(seeds_per_matchup=8):
    engine = FightAuditHarness()
    camp_specs = (
        ("Audit Boxing Lab", "Coach Hands", ("Boxing", "Gameplanning"), "Leeds"),
        ("Audit Kick Team", "Coach Range", ("Kickboxing", "Conditioning"), "Glasgow"),
        ("Audit Wrestling Room", "Coach Chain", ("Wrestling", "Conditioning"), "Cardiff"),
        ("Audit Jiu-Jitsu House", "Coach Guard", ("BJJ", "Gameplanning"), "Bristol"),
        ("Audit Clinch Club", "Coach Frame", ("Clinch", "Kickboxing"), "London"),
        ("Audit Sambo School", "Coach Jacket", ("Sambo", "Wrestling"), "Manchester"),
    )
    engine.gyms = [
        type("CommentaryAuditGym", (), {
            "name": name, "head_coach": coach, "specialties": list(specialties),
            "city": city, "region": "UK",
        })()
        for name, coach, specialties, city in camp_specs
    ]
    failures = []
    totals = Counter()
    lane_counts = Counter()
    domain_counts = Counter()
    lane_call_shapes = {}
    immediate_repeat = Counter()
    adjacent_domain_pairs = Counter()
    repeated_max = 0
    suppressed_fights = 0
    profile_events = 0
    submission_escape_events = 0
    submission_escape_complete = 0
    visible_damage_events = 0
    visible_damage_complete = 0
    visible_damage_broadcast = 0
    structured_cut_events = 0
    structured_cut_complete = 0
    trait_intro_complete = 0
    trait_intro_broadcast = 0
    trait_intro_expected = 0
    trait_context_events = 0
    trait_context_complete = 0
    camp_intro_expected = 0
    camp_intro_broadcast = 0
    camp_context_events = 0
    camp_context_complete = 0
    coach_feedback_lines = 0
    coach_feedback_complete = 0

    for trait_index, trait in enumerate(TRAITS):
        fighter = synthetic_fighter(
            f"Trait Audit {trait_index}", 76, "MMA Generalist", "Dynamic Attacker", trait_index,
        )
        fighter.trait = trait
        intro = engine.commentary_trait_intro(fighter)
        complete = bool(fighter.name in intro and len(intro.split()) >= 7)
        trait_intro_complete += int(complete)
        if not complete:
            failures.append(f"{trait}: missing or incomplete natural trait introduction")

    for spec_index, spec in enumerate(matchup_specs()):
        for seed_index in range(int(seeds_per_matchup)):
            personality = FIGHT_COMMENTARY_PERSONALITIES[(spec_index + seed_index) % len(FIGHT_COMMENTARY_PERSONALITIES)]
            engine.rules["fight_commentary_personality"] = personality
            a = synthetic_fighter(
                f"Commentary {spec['id']} A", spec["a_level"], spec["a_style"], spec["a_behaviour"], 0,
            )
            b = synthetic_fighter(
                f"Commentary {spec['id']} B", spec["b_level"], spec["b_style"], spec["b_behaviour"], 1,
            )
            trait_offset = (spec_index * int(seeds_per_matchup) + seed_index) * 2
            a.trait = TRAITS[trait_offset % len(TRAITS)]
            b.trait = TRAITS[(trait_offset + 1) % len(TRAITS)]
            a.camp = engine.gyms[trait_offset % len(engine.gyms)].name
            b.camp = engine.gyms[(trait_offset + 1) % len(engine.gyms)].name
            seed = 9_410_000 + spec_index * 100 + seed_index
            random.seed(seed)
            result = engine.simulate_fight_result(a, b, spec["fight"])
            detailed = list(result.commentary)
            broadcast = EventMixin.fight_night_commentary_lines(detailed, mode="Broadcast")
            totals["fights"] += 1
            totals["detailed_lines"] += len(detailed)
            totals["broadcast_lines"] += len(broadcast)
            suppressed_fights += int(len(broadcast) < len(detailed))

            for fighter in (a, b):
                intro = engine.commentary_trait_intro(fighter)
                if not intro:
                    continue
                trait_intro_expected += 1
                retained = intro in detailed and intro in broadcast
                trait_intro_broadcast += int(retained)
                if not retained:
                    failures.append(
                        f"{spec['id']} seed {seed}: Broadcast omitted {fighter.trait} introduction"
                    )
                camp_intro = engine.commentary_camp_intro(fighter)
                if camp_intro:
                    camp_intro_expected += 1
                    camp_retained = camp_intro in detailed and camp_intro in broadcast
                    camp_intro_broadcast += int(camp_retained)
                    if not camp_retained:
                        failures.append(
                            f"{spec['id']} seed {seed}: Broadcast omitted {fighter.camp} introduction"
                        )

            if any(TECHNICAL_SUFFIX_PATTERN.search(str(line)) for line in broadcast):
                failures.append(f"{spec['id']} seed {seed}: Broadcast leaked a technical suffix")
            if any("composed survival" in str(line).casefold() for line in detailed):
                failures.append(f"{spec['id']} seed {seed}: transcript leaked the composed-survival placeholder")

            feedback_prefixes = ("Corner advice -", "Technical corner -", "Corner urgency -", "Corner -")
            for feedback in (str(line) for line in detailed if str(line).startswith(feedback_prefixes)):
                coach_feedback_lines += 1
                fighter = a if f"to {a.name}:" in feedback else b if f"to {b.name}:" in feedback else None
                identity = engine.commentary_corner_identity(fighter) if fighter is not None else {}
                command_terms = (
                    "switch to", "stay with", "keep ", "slow the pace", "raise the activity",
                    "prepare for", "keep building", "turn it into", "stay balanced",
                    "different look", "contest the center", "protect the remaining gas",
                )
                complete = bool(
                    fighter is not None
                    and identity.get("coach") and identity["coach"].casefold() in feedback.casefold()
                    and identity.get("camp") and identity["camp"].casefold() in feedback.casefold()
                    and any(term in feedback.casefold() for term in command_terms)
                    and not any(term in feedback.casefold() for term in (
                        "observable round evidence", "deficit", "confidence", "adaptability",
                        "discipline rating", "no pre-fight tactical instruction",
                    ))
                )
                coach_feedback_complete += int(complete)
                if not complete:
                    failures.append(
                        f"{spec['id']} seed {seed}: coach feedback lost speaker, fighter, action, or natural wording: {feedback}"
                    )
                    break

            repeat_counts = Counter()
            for line in broadcast:
                text = str(line)
                upper = text.strip().upper()
                if (re.match(r"^(?:ROUND|PERIOD)\s+\d+", upper) or " SUMMARY:" in upper
                        or upper.startswith(("RESULT:", "OFFICIAL RESULT", "MATCH CLOCK"))):
                    repeat_counts.clear()
                    continue
                if "Broadcast note:" in text or any(term in text.casefold() for term in CRITICAL_TERMS):
                    continue
                if CLOCK_PATTERN.match(text):
                    repeat_counts[repeat_key(text)] += 1
                    repeated_max = max(repeated_max, repeat_counts[repeat_key(text)])

            trace = list(result.trace)
            trait_context_by_corner = {"a": [], "b": []}
            camp_context_by_corner = {"a": [], "b": []}
            previous_domain = None
            previous_shape = None
            for event in trace:
                if event.get("type") != "exchange":
                    continue
                lane = engine.exchange_commentary_kind(event)
                domain = engine.exchange_commentary_domain(event)
                lane_counts[lane] += 1
                domain_counts[domain] += 1
                call = str((event.get("commentary") or [""])[0])
                shape = normalized_exchange_call(event, call)
                lane_call_shapes.setdefault((domain, lane), Counter())[shape] += 1
                if previous_domain == domain:
                    adjacent_domain_pairs[domain] += 1
                    if previous_shape == shape:
                        immediate_repeat[domain] += 1
                previous_domain, previous_shape = domain, shape
                if event.get("actor_commentary_profile") and event.get("defender_commentary_profile"):
                    profile_events += 1
                if event.get("trait_commentary"):
                    trait_context_by_corner.setdefault(str(event.get("actor") or ""), []).append(event)
                    trait_context_events += 1
                    trait_line = str(event.get("trait_commentary") or "")
                    retained = bool(
                        (event.get("actor_name") or event.get("defender_name"))
                        and any(
                            str(name).casefold() in trait_line.casefold()
                            for name in (event.get("actor_name"), event.get("defender_name")) if name
                        )
                        and any(trait_line in str(line) for line in (event.get("commentary") or []))
                    )
                    trait_context_complete += int(retained)
                    if not retained:
                        failures.append(
                            f"{spec['id']} seed {seed}: contextual trait line lost actor or exchange attachment"
                        )
                    if not trait_context_has_support(engine, event):
                        failures.append(
                            f"{spec['id']} seed {seed}: contextual {((event.get('actor_commentary_profile') or {}).get('trait'))} call lacks trace support"
                        )
                if event.get("camp_commentary"):
                    camp_context_by_corner.setdefault(str(event.get("actor") or ""), []).append(event)
                    camp_context_events += 1
                    camp_line = str(event.get("camp_commentary") or "")
                    supported = bool(
                        event.get("actor_name") and event.get("actor_camp")
                        and str(event["actor_name"]).casefold() in camp_line.casefold()
                        and str(event["actor_camp"]).casefold() in camp_line.casefold()
                        and any(camp_line in str(line) for line in (event.get("commentary") or []))
                        and camp_context_has_support(engine, event)
                    )
                    camp_context_complete += int(supported)
                    if not supported:
                        failures.append(
                            f"{spec['id']} seed {seed}: contextual camp call lacks actor, camp, attachment, or specialty evidence"
                        )
                damage_lines = list(event.get("damage_narrative", []) or [])
                damage_rows = list(event.get("visible_damage_events", []) or [])
                visible_damage_events += len(damage_rows)
                for damage_row, damage_line in zip(damage_rows, damage_lines):
                    keyword = str(damage_row.get("narrative_keyword") or "").casefold()
                    complete = bool(
                        event.get("actor_name")
                        and str(event["actor_name"]).casefold() in damage_line.casefold()
                        and
                        event.get("defender_name")
                        and str(event["defender_name"]).casefold() in damage_line.casefold()
                        and keyword and keyword in damage_line.casefold()
                    )
                    visible_damage_complete += int(complete)
                    retained = any(damage_line in str(line) for line in broadcast)
                    visible_damage_broadcast += int(retained)
                    if not complete:
                        failures.append(
                            f"{spec['id']} seed {seed}: visible damage lost its fighter or symptom fact: {damage_line}"
                        )
                        break

                    if not retained:
                        failures.append(
                            f"{spec['id']} seed {seed}: Broadcast removed visible damage: {damage_line}"
                        )
                        break
                    if any(term in damage_line.casefold() for term in (
                            "fracture", "broken rib", "torn ligament", "organ injury", "concussion",
                            "lead leg", "nose", "mouth", "eyebrow", "calf", "thigh")):
                        failures.append(
                            f"{spec['id']} seed {seed}: broad trauma invented a diagnosis or location: {damage_line}"
                        )
                        break
                cut_rows = list(((event.get("cut_events") or {}).get(event.get("defender"), []) or []))
                cut_lines = damage_lines[len(damage_rows):]
                structured_cut_events += len(cut_rows)
                for cut, cut_line in zip(cut_rows, cut_lines):
                    location = str(cut.get("location") or "").casefold()
                    complete = bool(
                        event.get("actor_name")
                        and str(event["actor_name"]).casefold() in cut_line.casefold()
                        and event.get("defender_name")
                        and str(event["defender_name"]).casefold() in cut_line.casefold()
                        and location and location in cut_line.casefold()
                        and "cut" in cut_line.casefold()
                    )
                    structured_cut_complete += int(complete)
                    if not complete:
                        failures.append(
                            f"{spec['id']} seed {seed}: cut narrative omitted exact location or cut fact: {cut_line}"
                        )
                        break
                    if not any(cut_line in str(line) for line in broadcast):
                        failures.append(
                            f"{spec['id']} seed {seed}: Broadcast removed structured cut evidence: {cut_line}"
                        )
                        break
                if any(bad in call.casefold() for bad in (
                        ".!", "defensive defensive", "grips cleared;", "position retained")):
                    failures.append(f"{spec['id']} seed {seed}: unnatural exchange copy: {call}")
                    break
                if lane == "referee_standup":
                    if "referee" not in call.casefold() or not any(
                            term in call.casefold() for term in ("stand", "feet", "range", "waves it up")):
                        failures.append(
                            f"{spec['id']} seed {seed}: referee stand-up lost its officiating fact: {call}"
                        )
                        break
                    continue
                actor = str(event.get("actor_name") or "The attacker")
                move = engine.exchange_display_move(event)
                if actor.casefold() not in call.casefold() or move.casefold() not in call.casefold():
                    failures.append(
                        f"{spec['id']} seed {seed}: {lane} call omitted actor or move: {call}"
                    )
                    break
                if event.get("outcome") == "defended":
                    defense = str((event.get("defense") or {}).get("name") or "")
                    if defense and defense.casefold() not in call.casefold():
                        failures.append(f"{spec['id']} seed {seed}: defended call omitted {defense}")
                        break
                    if any(claim in call.casefold() for claim in ("lands the", "gets through", "scores with")):
                        failures.append(f"{spec['id']} seed {seed}: defended call claimed a landing: {call}")
                        break
                if event.get("outcome") == "submission_attempt" and event.get("submission_escape"):
                    submission_escape_events += 1
                    technique = str((event.get("submission_technique") or {}).get("name") or "")
                    defense = str((event.get("defense") or {}).get("name") or "")
                    consequence = str((event.get("submission_escape") or {}).get("consequence") or "")
                    complete = bool(
                        technique and defense and consequence
                        and technique.casefold() in call.casefold()
                        and defense.casefold() in call.casefold()
                    )
                    submission_escape_complete += int(complete)
                    if not complete:
                        failures.append(
                            f"{spec['id']} seed {seed}: submission sequence omitted technique, defense, or consequence: {call}"
                        )
                        break
                    technique_folded = technique.casefold()
                    leg_technique = any(term in technique_folded for term in (
                        "heel", "knee", "ankle", "toe hold", "slicer", "cloverleaf",
                    ))
                    if not leg_technique and str(event.get("defense_id") or "") == "knee_line_escape":
                        failures.append(
                            f"{spec['id']} seed {seed}: non-leg submission used a knee-line defense: {call}"
                        )
                        break
                if (str(event.get("action") or "") == "advance_position"
                        and event.get("position_before") != event.get("position_after")):
                    display_move = engine.exchange_display_move(event).casefold()
                    after = str(event.get("position_after") or "")
                    if ("back-take" in display_move and after != "back control") or (
                            "mount" in display_move and after != "mount"):
                        failures.append(
                            f"{spec['id']} seed {seed}: transition name contradicted {after}: {call}"
                        )
                        break

            for corner, trait_rows in trait_context_by_corner.items():
                trait_rounds = [int(row.get("round", 0) or 0) for row in trait_rows]
                if len(trait_rows) > 2 or len(trait_rounds) != len(set(trait_rounds)):
                    failures.append(
                        f"{spec['id']} seed {seed}: {corner} exceeded the contextual trait call cap"
                    )
            for corner, camp_rows in camp_context_by_corner.items():
                camp_rounds = [int(row.get("round", 0) or 0) for row in camp_rows]
                if len(camp_rows) > 2 or len(camp_rounds) != len(set(camp_rounds)):
                    failures.append(
                        f"{spec['id']} seed {seed}: {corner} exceeded the contextual camp call cap"
                    )

            if result.method in FINISH_METHODS:
                joined = "\n".join(detailed)
                if joined.casefold().count("official result:") != 1:
                    failures.append(
                        f"{spec['id']} seed {seed}: finish has {joined.casefold().count('official result:')} official results"
                    )
                if result.method in {"KO", "TKO"}:
                    winner_key = "a" if result.winner_id == a.fighter_id else "b"
                    causal = causal_trace_event(trace, winner_key, result.round_no)
                    if causal:
                        move = engine.exchange_display_move(causal)
                        official_line = next(
                            (str(line) for line in detailed if "official result:" in str(line).casefold()),
                            "",
                        )
                        if move.casefold() not in official_line.casefold():
                            failures.append(
                                f"{spec['id']} seed {seed}: {result.method} omitted causal move {move}"
                            )

    if repeated_max > 2:
        failures.append(f"Broadcast retained {repeated_max} identical low-value calls in one round")
    if not suppressed_fights:
        failures.append("Representative corpus never exercised Broadcast compaction")
    total_exchanges = max(1, sum(domain_counts.values()))
    if profile_events != total_exchanges:
        failures.append(
            f"Only {profile_events}/{total_exchanges} exchanges retained both fighter commentary profiles"
        )
    if submission_escape_complete != submission_escape_events:
        failures.append(
            f"Only {submission_escape_complete}/{submission_escape_events} failed submissions retained complete reaction facts"
        )
    if visible_damage_complete != visible_damage_events:
        failures.append(
            f"Only {visible_damage_complete}/{visible_damage_events} visible-damage events retained complete facts"
        )
    if visible_damage_broadcast != visible_damage_events:
        failures.append(
            f"Broadcast retained only {visible_damage_broadcast}/{visible_damage_events} visible-damage events"
        )
    if structured_cut_complete != structured_cut_events:
        failures.append(
            f"Only {structured_cut_complete}/{structured_cut_events} cut events named their exact location"
        )
    if trait_intro_complete != len(TRAITS):
        failures.append(
            f"Only {trait_intro_complete}/{len(TRAITS)} supported traits have complete introductions"
        )
    if trait_intro_broadcast != trait_intro_expected:
        failures.append(
            f"Broadcast retained only {trait_intro_broadcast}/{trait_intro_expected} trait introductions"
        )
    if trait_context_complete != trait_context_events:
        failures.append(
            f"Only {trait_context_complete}/{trait_context_events} contextual trait calls retained actor and exchange facts"
        )
    if not trait_context_events:
        failures.append("Representative varied-trait corpus produced no contextual trait calls")
    if camp_intro_broadcast != camp_intro_expected:
        failures.append(
            f"Broadcast retained only {camp_intro_broadcast}/{camp_intro_expected} camp introductions"
        )
    if camp_context_complete != camp_context_events:
        failures.append(
            f"Only {camp_context_complete}/{camp_context_events} contextual camp calls retained complete evidence"
        )
    if not camp_context_events:
        failures.append("Representative varied-camp corpus produced no contextual camp calls")
    if coach_feedback_complete != coach_feedback_lines:
        failures.append(
            f"Only {coach_feedback_complete}/{coach_feedback_lines} coach-feedback lines retained verified identity and an action"
        )
    if not coach_feedback_lines:
        failures.append("Representative corpus produced no between-round coach feedback")
    standing_survived = lane_call_shapes.get(("standing", "survived"), Counter())
    standing_survived_top_share = (
        max(standing_survived.values(), default=0) / max(1, sum(standing_survived.values())) * 100
    )
    if standing_survived and standing_survived_top_share > 20:
        failures.append(
            f"Standing survival's most common normalized call reached {standing_survived_top_share:.2f}%"
        )
    immediate_repeat_pct = {
        domain: round(immediate_repeat[domain] / max(1, adjacent_domain_pairs[domain]) * 100, 2)
        for domain in ("standing", "ground")
    }
    if immediate_repeat_pct["standing"] > 5:
        failures.append(
            f"Standing immediately repeated normalized calls {immediate_repeat_pct['standing']:.2f}% of adjacent exchanges"
        )
    lane_variety = {}
    for (domain, lane), counts in sorted(lane_call_shapes.items()):
        total = sum(counts.values())
        lane_variety[f"{domain}:{lane}"] = {
            "events": total,
            "normalized_calls": len(counts),
            "largest_call_share_pct": round(max(counts.values(), default=0) / max(1, total) * 100, 2),
        }
    fights = max(1, totals["fights"])
    report = {
        "fights": totals["fights"],
        "voices": list(FIGHT_COMMENTARY_PERSONALITIES),
        "mean_detailed_lines": round(totals["detailed_lines"] / fights, 2),
        "mean_broadcast_lines": round(totals["broadcast_lines"] / fights, 2),
        "line_reduction_pct": round(
            (totals["detailed_lines"] - totals["broadcast_lines"])
            / max(1, totals["detailed_lines"]) * 100,
            2,
        ),
        "fights_with_compaction": suppressed_fights,
        "maximum_low_value_repeat_per_round": repeated_max,
        "domain_exchanges": dict(sorted(domain_counts.items())),
        "profile_coverage_pct": round(profile_events / total_exchanges * 100, 2),
        "submission_escape_fact_coverage_pct": round(
            submission_escape_complete / max(1, submission_escape_events) * 100, 2,
        ),
        "visible_damage_events": visible_damage_events,
        "visible_damage_fact_coverage_pct": round(
            visible_damage_complete / max(1, visible_damage_events) * 100, 2,
        ),
        "visible_damage_broadcast_retention_pct": round(
            visible_damage_broadcast / max(1, visible_damage_events) * 100, 2,
        ),
        "structured_cut_location_coverage_pct": round(
            structured_cut_complete / max(1, structured_cut_events) * 100, 2,
        ),
        "trait_intro_coverage_pct": round(trait_intro_complete / max(1, len(TRAITS)) * 100, 2),
        "trait_intro_broadcast_retention_pct": round(
            trait_intro_broadcast / max(1, trait_intro_expected) * 100, 2,
        ),
        "contextual_trait_events": trait_context_events,
        "contextual_trait_fact_coverage_pct": round(
            trait_context_complete / max(1, trait_context_events) * 100, 2,
        ),
        "camp_intro_broadcast_retention_pct": round(
            camp_intro_broadcast / max(1, camp_intro_expected) * 100, 2,
        ),
        "contextual_camp_events": camp_context_events,
        "contextual_camp_fact_coverage_pct": round(
            camp_context_complete / max(1, camp_context_events) * 100, 2,
        ),
        "coach_feedback_lines": coach_feedback_lines,
        "coach_feedback_quality_pct": round(
            coach_feedback_complete / max(1, coach_feedback_lines) * 100, 2,
        ),
        "immediate_repeat_pct": immediate_repeat_pct,
        "standing_survived_largest_call_share_pct": round(standing_survived_top_share, 2),
        "lane_variety": lane_variety,
        "outcome_lanes": dict(sorted(lane_counts.items())),
        "failures": failures[:50],
        "failure_count": len(failures),
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds-per-matchup", type=int, default=8,
        help="Deterministic samples for each of the 32 representative matchup specifications.",
    )
    args = parser.parse_args()
    report = build_report(max(1, args.seeds_per_matchup))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
