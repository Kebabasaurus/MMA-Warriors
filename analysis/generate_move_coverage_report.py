"""Audit move eligibility against deterministic complete-fight selection opportunities."""
import argparse
from collections import Counter, deque
import json
import hashlib
import math
from pathlib import Path
from statistics import median
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fight_engine_audit import FightAuditHarness, move_report_specs, run_audited_fight, synthetic_fighter
from analysis.prepared_submission_diagnostics import PreparedFightAuditHarness
from analysis.submission_chain_candidate import validate_hold_transitions
from analysis.von_flue_angle_provenance import validate_von_flue_angles
from fight_moves.coverage import coverage_report, unreachable_moves
from fight_moves.catalogue.top_submissions import PHASE_29
from fight_moves.submission_identity import SUBMISSION_PARENT_ACTIONS, compatible_submission_ids
from fight_moves.submission_pool import submission_ticket_family


def summarize_variety(selection_counts, fighter_move_counts, chained_selections):
    """Explicit denominators for the plan's ordinary-fight variety targets."""
    total = sum(selection_counts.values())
    return {
        "total_move_selections": total,
        "mean_distinct_moves_per_fighter": round(sum(fighter_move_counts) / max(1, len(fighter_move_counts)), 4),
        "top_ten_move_share_pct": round(100 * sum(sorted(selection_counts.values(), reverse=True)[:10]) / max(1, total), 2),
        "chained_selection_pct": round(100 * chained_selections / max(1, total), 2),
    }


def summarize_positions(position_counts):
    """Use exchange occupancy, not distinct context tuples, for distance evidence."""
    standing = position_counts.get("range", 0) + position_counts.get("pocket", 0)
    return {"exchange_position_counts": dict(sorted(position_counts.items())),
            "standing_exchange_count": standing,
            "pocket_exchange_share_pct": round(100 * position_counts.get("pocket", 0) / max(1, standing), 2)}


def pocket_residence(trace):
    """Count observed pre-selection beats per pocket episode, including zero-beat entries.

    A horn/finish can end residence before another selection. Such episodes stay
    in the denominator; a position-after tag alone contributes no occupied beat.
    """
    lengths, exits = [], Counter()
    active, beats, last_round, entries = False, 0, None, 0

    def close(reason):
        nonlocal active, beats
        lengths.append(beats)
        exits[reason] += 1
        active, beats = False, 0

    for event in trace:
        if event.get("type") != "exchange":
            continue
        if active and event.get("round") != last_round:
            close("round_boundary")
        before, after = event.get("position_before"), event.get("position_after")
        if active and before != "pocket":
            close("unobserved_exit")
        if before == "pocket":
            active = True
            beats += 1
            if after != "pocket":
                close(str(after or "unknown"))
        elif after == "pocket":
            entries += 1
            active, beats = True, 0
        last_round = event.get("round")
    if active:
        close("fight_end")
    return {"entries": entries, "lengths": lengths, "exits": dict(exits)}


def submission_identity_observation(event):
    """Separate honest generic fallback from an incompatible named claim."""
    if event.get("type") != "exchange" or event.get("action") not in SUBMISSION_PARENT_ACTIONS:
        return None
    technique = event.get("submission_technique") or {}
    name = str(technique.get("name") or "unknown") if isinstance(technique, dict) else "unknown"
    payload = event.get("move") or {}
    move_id = str(event.get("move_id") or payload.get("move_id") or "")
    generic = bool(payload.get("generic")) or move_id.startswith("generic_")
    has_technique = isinstance(technique, dict) and isinstance(technique.get("name"), str) and bool(technique["name"].strip())
    status = "missing" if not has_technique else "generic" if generic else "named" if move_id in compatible_submission_ids(technique) else "incompatible"
    return (str(event["action"]), str(event.get("position_before") or "unknown"), name, status)


def contradictory_submission_defense(event):
    """A leg-only escape cannot defend a confirmed non-leg submission."""
    if event.get("type") != "exchange" or event.get("action") not in SUBMISSION_PARENT_ACTIONS:
        return False
    technique = event.get("submission_technique")
    if not isinstance(technique, dict) or not isinstance(technique.get("name"), str) or not technique["name"].strip():
        return False  # Missing technique evidence has its own required gate.
    leg = submission_ticket_family((technique["name"], technique.get("choke", False)))[1]
    return not leg and "leg-lock" in (event.get("defense") or {}).get("tags", ())


def top_leg_entry_observation(event):
    """Count actual entry/denial facts only when trace position and owners agree."""
    fact = event.get("top_leg_entry")
    if fact is None:
        return None
    if not isinstance(fact, dict) or type(fact.get("success")) is not bool:
        return "invalid"
    actor = event.get("actor")
    expected = "leg entanglement" if fact["success"] else "guard"
    technique = event.get("submission_technique") or {}
    valid = (event.get("type") == "exchange" and event.get("action") == "submission"
             and actor in ("a", "b") and event.get("top_before") == actor
             and event.get("top_after") == actor
             and event.get("bottom_before") == ("b" if actor == "a" else "a")
             and event.get("bottom_after") == event.get("bottom_before")
             and event.get("position_before") == fact.get("position_before") == "guard"
             and event.get("position_after") == fact.get("position_after") == expected
             and fact.get("controller") == (actor if fact["success"] else None)
             and fact.get("technique") == "straight ankle lock"
             and isinstance(technique, dict) and technique.get("name") == "straight ankle lock"
             and event.get("outcome") == ("position_change" if fact["success"] else "defended"))
    return ("entered" if fact["success"] else "denied") if valid else "invalid"


def control_award_observation(event):
    """Reconcile physical control at its credit point, before a referee reset."""
    if "control_award" not in event:
        return None
    fact = event["control_award"]
    delta = event.get("control_delta")
    if not isinstance(fact, dict) or not isinstance(delta, dict) or event.get("type") != "exchange":
        return "invalid"
    position, controller = fact.get("position"), fact.get("controller")
    top, bottom, clinch = fact.get("top"), fact.get("bottom"), fact.get("clinch_controller")
    physical_ground = {"guard", "half guard", "side control", "mount", "back control", "front headlock", "turtle"}
    if position in physical_ground or position == "leg entanglement":
        valid = top in ("a", "b") and bottom == ("b" if top == "a" else "a") and clinch is None
        expected = top if position in physical_ground else None
    elif position in {"clinch", "cage", "failed shot", "standing back control"}:
        valid = top is None and bottom is None and clinch in (None, "a", "b")
        expected = clinch
    elif position in {"range", "pocket"}:
        valid = top is None and bottom is None and clinch is None
        expected = None
    else:
        return "invalid"
    valid = valid and controller == expected and all(
        type(delta.get(slot)) is int and delta[slot] == int(slot == expected) for slot in ("a", "b"))
    if (event.get("referee_ground_action") or {}).get("type") == "standup":
        valid = (valid and position in physical_ground | {"leg entanglement"}
                 and event.get("position_after") == "range" and event.get("top_after") is None
                 and event.get("bottom_after") is None and event.get("clinch_after") is None)
    else:
        valid = (valid and event.get("position_after") == position and event.get("top_after") == top
                 and event.get("bottom_after") == bottom and event.get("clinch_after") == clinch)
    return (position if expected else "uncontrolled") if valid else "invalid"


def bottom_leg_entry_observation(event):
    """A knee-line entry is neither a submission roll nor a physical sweep."""
    fact = event.get('bottom_leg_entry')
    if fact is None:
        if (event.get('type') == 'exchange' and event.get('action') == 'sweep'
                and event.get('position_before') == 'guard'
                and event.get('position_after') == 'leg entanglement'):
            return 'invalid'
        return None
    if not isinstance(fact, dict) or type(fact.get('success')) is not bool:
        return 'invalid'
    actor = event.get('actor')
    other = 'b' if actor == 'a' else 'a'
    edge, margin = fact.get('intent_edge'), fact.get('entry_margin')
    if not all(type(x) in (int, float) and math.isfinite(x) for x in (edge, margin)):
        return 'invalid'
    success = fact['success']
    position = 'leg entanglement' if success else 'guard'
    move = event.get('move') or {}
    valid = (event.get('type') == 'exchange' and event.get('action') == 'sweep'
             and actor in ('a', 'b') and fact.get('actor') == actor
             and fact.get('source') == 'bottom_guard_sweep_intent'
             and type(fact.get('round')) is int and fact['round'] == event.get('round')
             and type(fact.get('tick')) is int and fact['tick'] == event.get('tick')
             and edge > 0 and success == (margin > 10)
             and event.get('position_before') == fact.get('position_before') == 'guard'
             and event.get('position_after') == fact.get('position_after') == position
             and event.get('top_before') == other and event.get('bottom_before') == actor
             and event.get('top_after') == (actor if success else other)
             and event.get('bottom_after') == (other if success else actor)
             and fact.get('controller') == (actor if success else None)
             and event.get('outcome') == ('position_change' if success else 'defended')
             and event.get('sub_att_delta') == 0 and event.get('td_delta') == 0
             and event.get('td_att_delta') == 0 and event.get('move_mastery') == 0
             and (event.get('round_metric_delta') or {}).get(actor, {}).get('control') == 0
             and (event.get('control_delta') or {}).get(actor) == 0
             and not event.get('submission_technique')
             and event.get('move_id') == move.get('move_id') == 'generic_bottom_leg_entry'
             and move.get('generic') is True and not move.get('signature')
             and not move.get('sequence_source_id') and not move.get('sequence_step'))
    return ('entered' if success else 'denied') if valid else 'invalid'


def guillotine_defense_observation(event):
    """Validate strong-denial grip/angle evidence separately from choke pressure."""
    if "guillotine_defense" not in event:
        return None
    fact = event["guillotine_defense"]
    if not isinstance(fact, dict):
        return "invalid"
    scores = [fact.get(key) for key in ("adjusted_margin", "retention_margin", "shoulder_margin")]
    if not all(type(value) in (int, float) and math.isfinite(value) for value in scores):
        return "invalid"
    margin, retention, shoulder = scores
    retained, angled = retention > 0, retention > 0 and shoulder >= 0
    top, bottom = fact.get("top"), fact.get("bottom")
    technique = event.get("submission_technique") or {}
    valid = (event.get("type") == "exchange" and event.get("action") == "bottom_submission"
             and top in ("a", "b") and bottom == ("b" if top == "a" else "a")
             and event.get("actor") == bottom and event.get("top_before") == event.get("top_after") == top
             and event.get("bottom_before") == event.get("bottom_after") == bottom
             and event.get("position_before") == event.get("position_after") == fact.get("position") == "half guard"
             and event.get("round") == fact.get("round") and event.get("tick") == fact.get("tick")
             and isinstance(technique, dict) and technique.get("name") == "guillotine choke"
             and technique.get("choke") is True and margin < -10
             and fact.get("pressure_stopped") is True and fact.get("top_control_consolidated") is True
             and fact.get("neck_wrap_retained") is retained
             and fact.get("shoulder_angle_established") is angled)
    setup = event.get("von_flue_setup") or {}
    if angled:
        valid = (valid and isinstance(setup, dict) and setup.get("status") == "created"
                 and setup.get("top") == top and setup.get("bottom") == bottom
                 and setup.get("position") == "half guard" and setup.get("round") == fact.get("round")
                 and setup.get("created_tick") == fact.get("tick"))
    else:
        valid = valid and not setup
    if not valid:
        return "invalid"
    return "von_flue_ready" if angled else "wrap_retained" if retained else "grip_cleared"


def von_flue_setup_counts(trace):
    """Verify that every used wrap follows the immediately preceding creation."""
    angle = validate_von_flue_angles(trace)
    return _submission_setup_counts(trace, field="von_flue_setup", position="half guard",
                                    created_action="bottom_submission", created_name="guillotine choke",
                                    used_name="Von Flue choke", creator_role="bottom", choke=True,
                                    allow_cancelled=True, alternative_creation_keys=angle['valid_creation_keys'])


def scarf_hold_setup_counts(trace):
    """Ordinary scarf isolation must precede its armbar without false named credit."""
    return _submission_setup_counts(trace, field="scarf_hold_setup", position="side control",
                                    created_action="ground_control", created_name=None,
                                    used_name="scarf-hold straight armbar", creator_role="top", choke=False,
                                    require_generic=True, allow_cancelled=True)


def _submission_setup_counts(trace, *, field, position, created_action, created_name,
                             used_name, creator_role, choke, require_generic=False, allow_cancelled=False,
                             alternative_creation_keys=()):
    counts, pending = Counter(), None
    keys = ("top", "bottom", "position", "round", "created_tick", "source", "origin_tick")
    for event in trace:
        if event.get("type") != "exchange":
            pending = None
            continue
        fact = event.get(field) or {}
        technique = event.get("submission_technique") or {}
        name = technique.get("name") if isinstance(technique, dict) else None
        status = fact.get("status") if isinstance(fact, dict) else None
        owners = (isinstance(fact, dict) and fact.get("top") in ("a", "b")
                  and fact.get("bottom") == ("b" if fact.get("top") == "a" else "a")
                  and event.get("top_before") == fact.get("top")
                  and event.get("bottom_before") == fact.get("bottom")
                  and event.get("position_before") == fact.get("position") == position
                  and event.get("round") == fact.get("round"))
        if status == "created" or (allow_cancelled and status == "cancelled"):
            alternative = (owners and (event.get('round'), event.get('tick'), fact.get('top'), fact.get('bottom'))
                           in alternative_creation_keys and event.get('actor') == fact.get('top')
                           and event.get('action') == 'ground_control' and name is None)
            ordinary = (owners and event.get("actor") == fact[creator_role]
                        and event.get("action") == created_action and name == created_name
                        and (created_name is None or technique.get("choke") is choke))
            valid = (owners and (ordinary or alternative)
                     and (not (require_generic or alternative) or ((event.get("move") or {}).get("generic") is True
                                                  and not (event.get("move") or {}).get("signature")
                                                  and not event.get("signature")
                                                  and not event.get("move_mastery")
                                                  and not event.get("sequence_source_id")
                                                  and not (event.get("move") or {}).get("sequence_source_id")))
                     and event.get("tick") == fact.get("created_tick"))
            if status == "cancelled":
                valid = (valid and fact.get("reason") == "referee_standup"
                         and (event.get("referee_ground_action") or {}).get("type") == "standup"
                         and event.get("position_after") == "range"
                         and event.get("top_after") is None and event.get("bottom_after") is None)
            else:
                valid = (valid and event.get("position_after") == position
                         and event.get("top_after") == fact["top"]
                         and event.get("bottom_after") == fact["bottom"])
            counts[status if valid else "invalid"] += 1
            pending = {key: fact.get(key) for key in keys} if valid and status == "created" else None
            continue
        if status == "used" or name == used_name:
            valid = (status == "used" and owners and pending is not None
                     and {key: fact.get(key) for key in keys} == pending
                     and type(fact.get("created_tick")) is int
                     and event.get("tick") == fact["created_tick"] + 1
                     and event.get("actor") == fact["top"] and event.get("action") == "submission"
                     and name == used_name and technique.get("choke") is choke)
            counts["used" if valid else "invalid"] += 1
        elif fact:
            counts["invalid"] += 1
        pending = None  # Any intervening exchange consumes the opportunity.
    return dict(counts)


def setup_followthrough_counts(trace, field):
    """Account for every created opportunity without hiding interrupted setups."""
    counts, pending = Counter(), None
    for event in trace:
        fact = event.get(field) or {}
        if pending is not None:
            if event.get("type") != "exchange":
                outcome = "non_exchange_boundary"
            elif (event.get("round") != pending.get("round")
                  or event.get("tick") != pending.get("created_tick", -2) + 1
                  or event.get("position_before") != pending.get("position")
                  or event.get("top_before") != pending.get("top")
                  or event.get("bottom_before") != pending.get("bottom")):
                outcome = "context_changed"
            elif event.get("actor") != pending.get("top"):
                outcome = "opponent_intervened"
            elif event.get("action") != "submission":
                outcome = "top_other_action"
            elif fact.get("status") == "used":
                outcome = "used"
            else:
                outcome = "top_other_submission"
            counts[outcome] += 1
            pending = None
        if event.get("type") == "exchange" and fact.get("status") == "created":
            pending = fact
    if pending is not None:
        counts["unobserved"] += 1
    return dict(counts)


class DefenseRepetitionWindow:
    """Peak per-clause repetition in any consecutive 300 bouts, not the whole run."""
    def __init__(self):
        self.bouts = deque()
        self.counts = Counter()
        self.maximum = 0

    def observe(self, clauses):
        self.bouts.append(dict(clauses))
        self.counts.update(clauses)
        if len(self.bouts) > 300:
            for clause, count in self.bouts.popleft().items():
                self.counts[clause] -= count
                if self.counts[clause] == 0:
                    del self.counts[clause]
        self.maximum = max(self.maximum, max((self.counts[clause] for clause in clauses), default=0))


def build_report(fight_count=300, *, definitions=None):
    if fight_count < 1:
        raise ValueError("Coverage evidence requires at least one complete fight")
    if definitions is None:
        from fight_moves import MOVE_DEFINITIONS
        definitions = MOVE_DEFINITIONS
    experimental = getattr(FightAuditHarness, "_experimental_specialist_entries", False)
    engine = PreparedFightAuditHarness() if experimental else FightAuditHarness()
    specs = move_report_specs()
    fighters, contexts, seen = [], set(), set()
    submission_moves = Counter()
    defense_clauses = Counter()
    defense_window = DefenseRepetitionWindow()
    observed_defenses = Counter()
    bottom_variety = []
    mechanical_signatures = []
    selection_counts, fighter_move_counts, chained_selections = Counter(), [], 0
    position_counts, action_counts = Counter(), Counter()
    pocket_entries, pocket_lengths, pocket_exits = 0, [], Counter()
    submission_identities = Counter()
    incompatible_submission_defenses = 0
    top_leg_entries = Counter()
    bottom_leg_entries = Counter()
    von_flue_setups = Counter()
    scarf_hold_setups = Counter()
    guillotine_defenses = Counter()
    von_flue_angles = Counter()
    control_awards = Counter()
    missing_control_awards = 0
    von_flue_followthrough, scarf_followthrough = Counter(), Counter()
    prepared_summary, prepared_observations = {}, []
    hold_transitions = Counter()
    cradle_setups = Counter()
    survival_expansion_counts = Counter()
    attempted_chain_depths, completed_chain_depths = [], []
    for index in range(fight_count):
        spec_index, seed_index = index % len(specs), index // len(specs)
        spec = specs[spec_index]
        a = synthetic_fighter(f"Move audit {spec['id']} A", spec["a_level"], spec["a_style"], spec["a_behaviour"], 0)
        b = synthetic_fighter(f"Move audit {spec['id']} B", spec["b_level"], spec["b_style"], spec["b_behaviour"], 1)
        a.stance = spec.get("a_stance", a.stance)
        b.stance = spec.get("b_stance", b.stance)
        fighters.extend((a, b))
        audit = run_audited_fight(engine, a, b, 9_310_000 + spec_index * 10_000 + seed_index, spec["fight"])
        if getattr(engine, '_survival_expansion_enabled', False):
            from analysis.survival_expansion_candidate import validate_survival_trace
            survival_expansion_counts.update(validate_survival_trace(audit['trace']))
        if getattr(engine, '_submission_chain_trial', False):
            hold_transitions.update(validate_hold_transitions(audit['trace']))
        from analysis import cradle_setup_candidate
        if cradle_setup_candidate._active or getattr(engine, '_cradle_setup_trial', False):
            cradle_setups.update(cradle_setup_candidate.validate_cradle_setups(audit['trace']))
        if experimental:
            prepared = engine.prepared_submission_diagnostics()
            for kind, counts in prepared["by_setup"].items():
                prepared_summary.setdefault(kind, Counter()).update(counts)
            prepared_observations.extend(dict(row, bout_index=index, spec_id=spec["id"],
                                              seed=9_310_000 + spec_index * 10_000 + seed_index)
                                         for row in prepared["observations"])
        von_flue_setups.update(von_flue_setup_counts(audit["trace"]))
        von_flue_angles.update(validate_von_flue_angles(audit['trace'])['counts'])
        scarf_hold_setups.update(scarf_hold_setup_counts(audit["trace"]))
        von_flue_followthrough.update(setup_followthrough_counts(audit["trace"], "von_flue_setup"))
        scarf_followthrough.update(setup_followthrough_counts(audit["trace"], "scarf_hold_setup"))
        residence = pocket_residence(audit["trace"])
        pocket_entries += residence["entries"]
        pocket_lengths.extend(residence["lengths"])
        pocket_exits.update(residence["exits"])
        clauses_in_bout = set()
        bottom_ids = {"a": set(), "b": set()}
        fighter_ids = {"a": set(), "b": set()}
        occurrence_depths = {}
        for event in audit["trace"]:
            if event.get("type") == "exchange":
                if getattr(engine, "_experimental_specialist_entries", False) and "control_award" not in event:
                    missing_control_awards += 1
                control_award = control_award_observation(event)
                if control_award is not None:
                    control_awards[control_award] += 1
                grip_assessment = guillotine_defense_observation(event)
                if grip_assessment is not None:
                    guillotine_defenses[grip_assessment] += 1
                identity = submission_identity_observation(event)
                incompatible_submission_defenses += contradictory_submission_defense(event)
                entry = top_leg_entry_observation(event)
                if entry is not None:
                    top_leg_entries[entry] += 1
                bottom_entry = bottom_leg_entry_observation(event)
                if bottom_entry is not None:
                    bottom_leg_entries[bottom_entry] += 1
                if identity is not None:
                    submission_identities[identity] += 1
                position_counts[event["position_before"]] += 1
                action_counts[event["action"]] += 1
                contexts.add((event["action"], event["position_before"], (event.get("move") or {}).get("target", "")))
                seen.add(event.get("move_id", ""))
                selection_counts[event.get("move_id", "")] += 1
                fighter_ids[event["actor"]].add(event.get("move_id", ""))
                chained_selections += bool(event.get("sequence_source_id"))
                sequence = event.get("move_sequence") or {}
                occurrence = event.get("sequence_occurrence_id")
                depth = int(event.get("chain_depth", 0) or 0)
                if occurrence and (depth >= 2 or sequence.get("continuation_available")):
                    occurrence_depths[occurrence] = max(depth, occurrence_depths.get(occurrence, 0))
                observed_defenses[event.get("defense_id", "")] += 1
                if event["action"] in {"recover_guard", "sweep", "stand_up", "cling"}:
                    bottom_ids[event["actor"]].add(event.get("move_id", ""))
                clauses_in_bout.add(engine.commentary_defense_clause(
                    event, event["defender_name"], (event.get("defense") or {}).get("name", "defense")).casefold())
                if event["action"] == "submission":
                    submission_moves[event.get("move_id", "")] += 1
        rendered = "\n".join(engine._last_fight_result.commentary).casefold()
        bout_clauses = {clause: rendered.count(clause) for clause in clauses_in_bout if clause in rendered}
        defense_clauses.update(bout_clauses)
        defense_window.observe(bout_clauses)
        bottom_variety.extend(len(ids) for ids in bottom_ids.values())
        fighter_move_counts.extend(len(ids) for ids in fighter_ids.values())
        if any(e.get("type") == "exchange" and e.get("round", 0) >= 2 for e in audit["trace"]):
            attempted_chain_depths.extend(occurrence_depths.values())
            completed_chain_depths.extend(d for d in occurrence_depths.values() if d >= 2)
        mechanical = {key: audit[key] for key in ("winner_id", "loser_id", "method", "round", "scorecards")}
        mechanical["events"] = [{k: v for k, v in event.items() if k != "result"} for event in audit["events"]]
        mechanical_signatures.append(hashlib.sha256(json.dumps(mechanical, sort_keys=True).encode()).hexdigest())
    skill_keys = {key for fighter in fighters for key in fighter.detailed_skills}
    skills = {key: median(f.detailed_skills.get(key, 0) for f in fighters) for key in skill_keys}
    reasons = unreachable_moves({p for _, p, _ in contexts}, {a for a, _, _ in contexts}, skills,
                                reachable_contexts=contexts, definitions=definitions)
    return {"fight_count": fight_count, "scope": "observed selection opportunities, not proof of absolute unreachability",
            "hold_transition_counts": dict(hold_transitions), "cradle_setup_counts": dict(cradle_setups),
            **summarize_variety(selection_counts, fighter_move_counts, chained_selections),
            **summarize_positions(position_counts),
            "pocket_entry_count": pocket_entries,
            "pocket_observed_episodes": len(pocket_lengths),
            "pocket_mean_residence_beats": round(sum(pocket_lengths) / max(1, len(pocket_lengths)), 4),
            "pocket_residence_histogram": dict(sorted(Counter(pocket_lengths).items())),
            "pocket_exit_counts": dict(sorted(pocket_exits.items())),
            "submission_attempt_identity_count": sum(submission_identities.values()),
            "incompatible_submission_defense_count": incompatible_submission_defenses,
            "top_leg_entry_counts": dict(top_leg_entries),
            "bottom_leg_entry_counts": dict(bottom_leg_entries),
            "von_flue_setup_counts": dict(von_flue_setups),
            "scarf_hold_setup_counts": dict(scarf_hold_setups),
            "generic_submission_identity_count": sum(count for key, count in submission_identities.items() if key[3] == "generic"),
            "incompatible_submission_identity_count": sum(count for key, count in submission_identities.items() if key[3] == "incompatible"),
            "missing_submission_technique_count": sum(count for key, count in submission_identities.items() if key[3] == "missing"),
            "submission_identity_contexts": [dict(action=action, position=position, technique=name, status=status, count=count)
                                             for (action, position, name, status), count in sorted(submission_identities.items())],
            "guillotine_defense_counts": dict(sorted(guillotine_defenses.items())),
            "von_flue_angle_counts": dict(sorted(von_flue_angles.items())),
            "control_award_counts": dict(sorted(control_awards.items())),
            "missing_control_award_count": missing_control_awards,
            "von_flue_followthrough_counts": dict(sorted(von_flue_followthrough.items())),
            "scarf_hold_followthrough_counts": dict(sorted(scarf_followthrough.items())),
            "prepared_submission_diagnostics": {
                "scope": "Conditional on observed live setup opportunities; not an unconditional forecast or acceptance gate",
                "by_setup": {kind: dict(counts) for kind, counts in sorted(prepared_summary.items())},
                "observations": prepared_observations,
            },
            "action_selection_counts": dict(sorted(action_counts.items())),
            "move_selection_counts": dict(sorted(selection_counts.items())),
            "survival_expansion_counts": dict(survival_expansion_counts),
            "attempted_chain_occurrences_round2_fights": len(attempted_chain_depths),
            "completed_chain_occurrences_round2_fights": len(completed_chain_depths),
            "median_attempted_chain_length_round2_fights": median(attempted_chain_depths) if attempted_chain_depths else 0,
            "median_completed_chain_length_round2_fights": median(completed_chain_depths) if completed_chain_depths else 0,
            "contexts": sorted(contexts), "observed_move_ids": sorted(seen),
            "eligibility_warnings": reasons, "coverage": coverage_report(contexts, definitions=definitions),
            "top_submission_selections": dict(sorted(submission_moves.items())),
            "top_submission_largest_share_pct": round(100 * max(submission_moves.values(), default=0)
                                                        / max(1, sum(submission_moves.values())), 2),
            "observed_defenses": dict(sorted(observed_defenses.items())),
            "maximum_identical_defense_clause": defense_window.maximum,
            "defense_repetition_window_fights": 300,
            "aggregate_maximum_identical_defense_clause": max(defense_clauses.values(), default=0),
            "most_repeated_defense_clauses": defense_clauses.most_common(5),
            "mean_distinct_bottom_moves_per_fighter": round(sum(bottom_variety) / len(bottom_variety), 4),
            "mechanical_signatures": mechanical_signatures}


def compare_coverage(actual, reference):
    failures = []
    for move_id, reasons in actual["eligibility_warnings"].items():
        new = set(reasons) - set(reference["eligibility_warnings"].get(move_id, ()))
        if new:
            failures.append(f"{move_id}: new eligibility gap {sorted(new)}")
    previous = {(p["action"], p["position"]): p["depth"] for p in reference["coverage"]["pools"]}
    for pool in actual["coverage"]["pools"]:
        floor = min(pool["minimum"], previous.get((pool["action"], pool["position"]), pool["minimum"]))
        if pool["depth"] < floor:
            failures.append(f"{pool['action']} / {pool['position']}: pool depth {pool['depth']} below {floor}")
    for style, count in actual["coverage"]["style_counts"].items():
        floor = min(18, reference["coverage"]["style_counts"].get(style, 18))
        if count < floor:
            failures.append(f"{style}: authored depth {count} below {floor}")
    return failures


def phase_29_failures(report):
    failures = []
    selected = report["top_submission_selections"]
    for move in PHASE_29:
        if not selected.get(move.move_id):
            failures.append(f"Phase 29 move absent from ordinary fights: {move.move_id}")
    if report["top_submission_largest_share_pct"] > 25:
        failures.append("Phase 29 top submission concentration exceeds 25%")
    pools = {(p["action"], p["position"]): p["depth"] for p in report["coverage"]["pools"]}
    for position in ("guard", "half guard"):
        if pools.get(("submission", position), 0) < 6:
            failures.append(f"Phase 29 submission pool below six: {position}")
    return failures


def phase_30_33_failures(report):
    from fight_moves import MOVE_DEFINITIONS, DEFENSE_DEFINITIONS, GROUND_POSITIONS, legal_moves
    from fight_moves.catalogue.bottom_development import PHASE_30
    failures = [f"Phase 30 move absent: {m.move_id}" for m in PHASE_30
                if m.move_id not in report["observed_move_ids"]]
    for position in GROUND_POSITIONS:
        if len(legal_moves("recover_guard", position)) < 4:
            failures.append(f"Fewer than four recoveries in {position}")
    for family in {f for m in MOVE_DEFINITIONS for f in m.defense_families}:
        if sum(family in d.families for d in DEFENSE_DEFINITIONS) < 2:
            failures.append(f"Fewer than two named defenses for {family}")
    if report["maximum_identical_defense_clause"] >= 10:
        failures.append("Identical rendered defense clause appears ten or more times")
    return failures


def slice_5_failures(report):
    from fight_moves.catalogue import (POWER_PUNCH_DEVELOPMENT, JAB_DEVELOPMENT,
                                       SLICE_5_KICKS, CLINCH_DEVELOPMENT)
    additions = POWER_PUNCH_DEVELOPMENT + JAB_DEVELOPMENT + SLICE_5_KICKS + CLINCH_DEVELOPMENT
    return [f"Slice 5 move absent: {m.move_id}" for m in additions
            if m.move_id not in report["observed_move_ids"]]


def slice_6_failures(report):
    from fight_moves.catalogue import (WRESTLING_DEVELOPMENT, GROUND_TOP_DEVELOPMENT,
                                       BOTTOM_SUBMISSION_DEVELOPMENT)
    additions = WRESTLING_DEVELOPMENT + GROUND_TOP_DEVELOPMENT + BOTTOM_SUBMISSION_DEVELOPMENT
    return [f"Slice 6 move absent: {m.move_id}" for m in additions
            if m.move_id not in report["observed_move_ids"]]


def phase_31_failures(report):
    """Development acceptance includes interrupted starts, not only successful chains."""
    from fight_moves import MOVE_DEFINITIONS
    from fight_moves.legacy_ids import LEGACY_MOVE_IDS
    failures = []
    if sum(bool(m.follow_ups) for m in MOVE_DEFINITIONS if m.move_id in LEGACY_MOVE_IDS) < 150:
        failures.append("Phase 31 fewer than 150 original moves have successors")
    if report.get("chained_selection_pct", 0) < 12:
        failures.append("Phase 31 chained selection share below 12%")
    return failures


def phase_31_advisories(report):
    """User-approved temporary waiver; preserve attempted-root measurement."""
    return (["Attempted-chain median below two (accepted for now by user)"]
            if report.get("median_attempted_chain_length_round2_fights", 0) < 2 else [])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fights", type=int, default=300)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--capture-reference", action="store_true")
    parser.add_argument("--require-phase31", action="store_true",
                        help="Enforce the still-in-development chain acceptance targets")
    args = parser.parse_args()
    if args.verify and args.output.resolve() == args.verify.resolve():
        parser.error("Verification output must not overwrite its reference")
    reference = json.loads(args.verify.read_text(encoding="utf-8")) if args.verify else None
    report = build_report(reference["fight_count"] if reference else args.fights)
    report["phase_31_acceptance_failures"] = phase_31_failures(report)
    report["phase_31_advisories"] = phase_31_advisories(report)
    failures = compare_coverage(report, reference) if reference else []
    if args.verify:
        failures.extend(phase_29_failures(report))
        failures.extend(phase_30_33_failures(report))
        failures.extend(slice_5_failures(report))
        failures.extend(slice_6_failures(report))
    if args.require_phase31:
        failures.extend(report["phase_31_acceptance_failures"])
    report["failures"] = failures
    with args.output.open("x" if args.capture_reference else "w", encoding="utf-8") as stream:
        stream.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"fights": report["fight_count"], "contexts": len(report["contexts"]),
                      "warnings": len(report["eligibility_warnings"]), "failures": failures}))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
