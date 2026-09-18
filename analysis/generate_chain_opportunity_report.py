"""Read-only chain interruptions and optimistic action-coverage diagnostics.

The denominator matches the coverage report, including interrupted roots. The
three-action ceiling is conditional on this observed root cohort, not proof that
another catalogue or lifecycle can never achieve the phase target. It ignores
move/skill/style/target/rarity and DAG restrictions. A second bound selects up
to three actual registry IDs with legal source/result positions, ownership and
incoming targets. It still ignores skills, style, rarity, ranking and DAG rules.
Neither bound changes observed root membership or proves universal feasibility.
The stage breakdown distinguishes declared action families only; traces do not
prove why a named successor failed eligibility, ranking or mechanical identity.
"""
import argparse
from collections import Counter, defaultdict
from itertools import combinations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fight_engine_audit import FightAuditHarness, move_report_specs, run_audited_fight, synthetic_fighter
from fight_moves.chains import sequence_actor_role
from fight_moves.chains import sequence_role_allows
from fight_moves import legal_moves
import fight_moves


def declared_successor_actions(root):
    """Recover runtime-legal root branches, or None for unavailable evidence.

    Use recorded branches, never today's potentially changed root definition.
    Resolve target IDs through the active registry (including audit candidates).
    Missing/unknown IDs are not evidence that an action was undeclared.
    """
    move = root.get("move") or {}
    if "follow_up_ids" in move:
        ids = move["follow_up_ids"]
    elif move.get("follow_up_id"):
        ids = (move["follow_up_id"],)
    else:
        return None
    if not isinstance(ids, (tuple, list)) or any(
            not isinstance(key, str) or key not in fight_moves.MOVE_REGISTRY for key in ids):
        return None
    position = root["position_after"]
    return {definition.parent_action for key in ids
            for definition in (fight_moves.MOVE_REGISTRY[key],)
            if not definition.deprecated and position in definition.positions
            and sequence_role_allows(definition.parent_action, position, root["actor"],
                                     root.get("top_after"), root.get("bottom_after"))}


def maximum_three_move_coverage(opportunities):
    """Exact best union of up to three IDs, without summing overlapping cases."""
    masks = defaultdict(int)
    for index, ids in enumerate(opportunities):
        for move_id in ids:
            masks[move_id] |= 1 << index
    unique = set(masks.values())
    # Equal/dominated masks cannot improve any three-choice union.
    maximal = [mask for mask in unique if not any(mask != other and mask | other == other for other in unique)]
    if not maximal:
        return 0
    return max((a | b | c).bit_count() for a, b, c in combinations([0, 0, *maximal], 3))


def inspect_trace(trace):
    events = [e for e in trace if e.get("type") == "exchange"]
    if not any(e.get("round", 0) >= 2 for e in events):
        return []
    occurrences = {}
    for index, event in enumerate(events):
        occurrence = event.get("sequence_occurrence_id")
        depth = int(event.get("chain_depth", 0) or 0)
        if not occurrence or not (depth >= 2 or (event.get("move_sequence") or {}).get("continuation_available")):
            continue
        row = occurrences.setdefault(occurrence, {"index": index, "depth": depth})
        row["depth"] = max(row["depth"], depth)
    next_by_actor, next_index = {}, {}
    for index in range(len(events) - 1, -1, -1):
        actor = events[index]["actor"]
        next_index[index] = next_by_actor.get(actor)
        next_by_actor[actor] = index
    rows = []
    for row in occurrences.values():
        index = row["index"]
        root = events[index]
        next_own = next_index[index]
        following = events[next_own] if next_own is not None else None
        reason, opportunity = "", ""
        root_role = sequence_actor_role(root["position_after"], root["actor"], root.get("top_after"), root.get("bottom_after"))
        if following is None:
            reason = "fight_ended_before_next_own_action"
        elif following["round"] != root["round"]:
            reason = "round_boundary"
        elif not 0 < following["tick"] - root["tick"] <= 2:
            reason = "two_tick_expiry"
        elif any(e.get("neutral_scramble_reset") for e in events[index + 1:next_own + 1]):
            # Either actor's neutral restart invalidates both pending chains.
            # Include a reset on the next own exchange: it cannot complete the
            # selected successor and must not inflate the optimistic bound.
            reason = "neutral_restart"
        elif root_role and root_role != sequence_actor_role(
                following["position_before"], root["actor"], following.get("top_before"), following.get("bottom_before")):
            reason = "ownership_role_changed"
        else:
            opportunity = following["action"]
            reason = "next_action_not_completed_as_declared_successor"
        eligible_ids = []
        if opportunity:
            target = (following.get("move") or {}).get("target", "")
            for definition in legal_moves(opportunity, following["position_before"], target):
                if (root["position_after"] in definition.positions
                        and sequence_role_allows(definition.parent_action, root["position_after"], root["actor"],
                                                 root.get("top_after"), root.get("bottom_after"))
                        and sequence_role_allows(definition.parent_action, following["position_before"], root["actor"],
                                                 following.get("top_before"), following.get("bottom_before"))):
                    eligible_ids.append(definition.move_id)
        stage = "completed" if row["depth"] >= 2 else reason
        if row["depth"] < 2 and opportunity:
            declared = declared_successor_actions(root)
            if declared is None:
                stage = "branch_evidence_unavailable"
            elif opportunity in declared:
                stage = "declared_action_no_named_completion"
            else:
                stage = "undeclared_survive" if opportunity == "survive" else "undeclared_other_action"
        declared = declared_successor_actions(root)
        gas_after = (root.get("actor_gas_after")
                     if root.get("actor_gas_after") is not None
                     else (root.get("gas_after") or {}).get(root.get("actor")))
        rows.append({"root_move_id": root["move_id"], "depth": row["depth"],
                     "completed": row["depth"] >= 2,
                     "reason": "completed" if row["depth"] >= 2 else reason,
                     "stage_loss_reason": stage,
                     "root_position": str(root.get("position_after") or ""),
                     "root_outcome": str(root.get("outcome") or ""),
                     "root_actor_streak": max(0, int(root.get("actor_streak", 0) or 0)),
                     "root_actor_gas_after": round(float(gas_after), 3) if gas_after is not None else None,
                     "declared_successor_action_count": len(declared) if declared is not None else None,
                     "timely_same_role_next_action": opportunity,
                     "timely_next_position": following["position_before"] if opportunity else "",
                     "timely_next_target": ((following.get("move") or {}).get("target", "") if opportunity else ""),
                     "position_target_legal_next_ids": eligible_ids})
    return rows


def summarize(rows):
    actions, counts, legal_opportunities = defaultdict(Counter), Counter(), defaultdict(list)
    move_opportunities, move_contexts = Counter(), defaultdict(Counter)
    root_move_opportunities = defaultdict(Counter)
    root_move_contexts = defaultdict(lambda: defaultdict(Counter))
    root_action_coverage = defaultdict(Counter)
    for row in rows:
        key = row["root_move_id"]
        counts[key] += 1
        legal_opportunities[key].append(row.get("position_target_legal_next_ids", ()))
        if row["timely_same_role_next_action"]:
            actions[key][row["timely_same_role_next_action"]] += 1
        # This is per-ID eligible-case frequency. One observed exchange may be
        # eligible for several IDs and is intentionally counted once for each;
        # it is not a disjoint completion estimate or a universal opportunity.
        eligible_by_action = defaultdict(set)
        for move_id in set(row.get("position_target_legal_next_ids") or ()):
            if not isinstance(move_id, str) or move_id not in fight_moves.MOVE_REGISTRY:
                continue
            parent_action = fight_moves.MOVE_REGISTRY[move_id].parent_action
            move_opportunities[move_id] += 1
            root_move_opportunities[key][move_id] += 1
            context = (str(row.get("timely_same_role_next_action") or ""),
                       str(row.get("timely_next_position") or ""),
                       str(row.get("timely_next_target") or ""))
            move_contexts[move_id][context] += 1
            root_move_contexts[key][move_id][context] += 1
            eligible_by_action[parent_action].add(move_id)
        # Union coverage is once per observed root case/action, regardless of
        # how many candidate IDs in that action were legal for the same case.
        for parent_action in eligible_by_action:
            root_action_coverage[key][parent_action] += 1
    completed = sum(row["completed"] for row in rows)
    cohort_counts = defaultdict(lambda: [0, 0])
    for row in rows:
        gas = row.get("root_actor_gas_after")
        dimensions = {
            "position": str(row.get("root_position") or "unknown"),
            "outcome": str(row.get("root_outcome") or "unknown"),
            "actor_streak": ("3+" if int(row.get("root_actor_streak", 0) or 0) >= 3
                             else str(int(row.get("root_actor_streak", 0) or 0))),
            "gas": ("unknown" if gas is None else "60+" if gas >= 60
                    else "35-59" if gas >= 35 else "under-35"),
            "successor_actions": ("unknown" if row.get("declared_successor_action_count") is None
                                  else str(row["declared_successor_action_count"])),
        }
        for dimension, value in dimensions.items():
            cohort_counts[(dimension, value)][0] += 1
            cohort_counts[(dimension, value)][1] += int(row["completed"])
    upper_bound = sum(sum(value for _, value in counter.most_common(3)) for counter in actions.values())
    move_bound = sum(maximum_three_move_coverage(cases) for cases in legal_opportunities.values())
    return {"attempted_roots": len(rows), "completed_roots": completed,
            "completion_pct": round(100 * completed / max(1, len(rows)), 2),
            "loss_reasons": dict(sorted(Counter(row["reason"] for row in rows).items())),
            "stage_loss_breakdown": dict(sorted(Counter(
                row.get("stage_loss_reason", row["reason"]) for row in rows).items())),
            "optimistic_three_action_completions_fixed_cohort": upper_bound,
            "optimistic_three_action_pct_fixed_cohort": round(100 * upper_bound / max(1, len(rows)), 2),
            "optimistic_three_existing_move_completions_fixed_cohort": move_bound,
            "optimistic_three_existing_move_pct_fixed_cohort": round(100 * move_bound / max(1, len(rows)), 2),
            "root_completion_cohorts": [
                {"dimension": dimension, "value": value, "attempted": counts[0],
                 "completed": counts[1],
                 "completion_pct": round(100 * counts[1] / max(1, counts[0]), 2)}
                for (dimension, value), counts in sorted(cohort_counts.items())
            ],
            "timely_existing_move_opportunities": [
                {"move_id": move_id, "parent_action": fight_moves.MOVE_REGISTRY[move_id].parent_action,
                 "eligible_case_count": count,
                 "recommended_contexts": [
                     {"action": context[0], "position": context[1], "target": context[2], "count": value}
                     for context, value in sorted(move_contexts[move_id].items(),
                                                  key=lambda item: (-item[1], item[0]))
                 ]}
                for move_id, count in sorted(move_opportunities.items(), key=lambda item: (-item[1], item[0]))
            ],
            "root_existing_move_opportunities": [
                {"root_move_id": root_id, "attempted": count,
                 "current_registered_follow_ups": list(
                     fight_moves.MOVE_REGISTRY[root_id].follow_ups
                     if root_id in fight_moves.MOVE_REGISTRY else ()),
                 "current_registered_parent_actions": sorted({
                     fight_moves.MOVE_REGISTRY[move_id].parent_action
                     for move_id in (fight_moves.MOVE_REGISTRY[root_id].follow_ups
                                     if root_id in fight_moves.MOVE_REGISTRY else ())
                     if move_id in fight_moves.MOVE_REGISTRY
                 }),
                 "candidate_action_coverage": [
                     {"parent_action": action, "eligible_case_count": value}
                     for action, value in sorted(root_action_coverage[root_id].items(),
                                                 key=lambda item: (-item[1], item[0]))
                 ],
                 "candidate_moves": [
                     {"move_id": move_id, "parent_action": fight_moves.MOVE_REGISTRY[move_id].parent_action,
                      "eligible_case_count": value,
                      "already_declared": move_id in (fight_moves.MOVE_REGISTRY[root_id].follow_ups
                                                      if root_id in fight_moves.MOVE_REGISTRY else ()),
                      "recommended_contexts": [
                          {"action": context[0], "position": context[1], "target": context[2], "count": frequency}
                          for context, frequency in sorted(root_move_contexts[root_id][move_id].items(),
                                                           key=lambda item: (-item[1], item[0]))
                      ]}
                     for move_id, value in sorted(root_move_opportunities[root_id].items(),
                                                   key=lambda item: (-item[1], item[0]))]
                 }
                for root_id, count in counts.most_common()
            ],
            "root_opportunities": [{"move_id": key, "attempted": count,
                                     "timely_next_actions": dict(actions[key].most_common())}
                                    for key, count in counts.most_common()]}


def build_report(fights=300):
    if type(fights) is not int or fights < 1:
        raise ValueError("A positive integer fight count is required")
    engine, specs, rows = FightAuditHarness(), move_report_specs(), []
    for index in range(fights):
        spec_index, seed_index = index % len(specs), index // len(specs)
        spec = specs[spec_index]
        a = synthetic_fighter(f"Move audit {spec['id']} A", spec["a_level"], spec["a_style"], spec["a_behaviour"], 0)
        b = synthetic_fighter(f"Move audit {spec['id']} B", spec["b_level"], spec["b_style"], spec["b_behaviour"], 1)
        a.stance, b.stance = spec.get("a_stance", a.stance), spec.get("b_stance", b.stance)
        audit = run_audited_fight(engine, a, b, 9_310_000 + spec_index * 10_000 + seed_index, spec["fight"])
        rows.extend(inspect_trace(audit["trace"]))
    return {"fights": fights, "scope": "Observed roots; optimistic ceiling is not a universal feasibility proof",
            **summarize(rows)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fights", type=int, default=300)
    parser.add_argument("--top-roots", type=int, default=20, help="Number of root rows to print; 0 prints all")
    args = parser.parse_args()
    if args.top_roots < 0:
        parser.error("--top-roots must be nonnegative")
    report = build_report(args.fights)
    if args.top_roots:
        report["root_opportunities"] = report["root_opportunities"][:args.top_roots]
    print(json.dumps(report, indent=2))
