"""Maximum distinct IDs within observed final selector pools, not acceptance.

This fixed-trajectory bound holds observed states/pools constant. Selecting other
IDs can change later reads, chains, plans and mechanics: it is NOT a universal
feasibility bound or a replacement for any coverage/calibration gate.
"""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fight_engine
import fight_moves
from fight_engine_audit import FightAuditHarness, run_audited_fight, synthetic_fighter
from analysis.compare_candidate_striking import fixture_schedule
from analysis.fight_candidate_context import candidate_context
from tools.move_registry_parity import build_dump, canonical_bytes
from fight_moves.selection_pool import ordinary_selection_pool


def final_selection_pool(eligible, active_counter, signature_moves, chain_candidates, active_chain, *, expanded=False):
    """Observe the exact current final pool without sorting/mutating caller rows."""
    rows = sorted(eligible, key=lambda row: (-row[0], row[1].move_id))
    if not rows:
        return (), "empty"
    if active_counter:
        counters = [row for row in rows if fight_engine.COUNTER_TAG in row[1].tags]
        if counters:
            rows = counters
    top = rows[0][1]
    authored = bool(set(top.tags).intersection({fight_engine.STYLE_COMBINATION_TAG,
                                               fight_engine.STYLE_FINISHER_TAG})) or top.move_id in signature_moves
    pool, kind = ((rows[:1], "authored") if authored else
                  ordinary_selection_pool(rows, chain_candidates, active_chain, expanded=expanded))
    return tuple(row[1].move_id for row in pool), kind


class TerminalRngHarness(FightAuditHarness):
    """Capture terminal streams before simulate_fight restores its RNG bindings."""
    def _simulate_fight_with_caches(self, *args):
        result = super()._simulate_fight_with_caches(*args)
        self.terminal_rng_states = tuple(getattr(self, f"_fight_{name}_rng").getstate()
                                         for name in ("mechanics", "officiating", "judging", "presentation"))
        return result


class VarietyOpportunityHarness(TerminalRngHarness):
    def _simulate_fight_with_caches(self, *args):
        self.observed_pools = {}
        self.pool_kinds = Counter()
        return super()._simulate_fight_with_caches(*args)

    def _select_from_pool(self, eligible, active_counter, signature_moves, chain_candidates,
                          active_chain, identity, action, position, target, state):
        pool, kind = final_selection_pool(eligible, active_counter, signature_moves, chain_candidates, active_chain,
                                         expanded=getattr(self, '_experimental_chain_action_weighting', False))
        key = (state["round"], state["tick"], identity)
        if key in self.observed_pools:
            raise ValueError(f"Duplicate selector observation: {key}")
        # The original selector is called exactly once with unchanged arguments.
        selected = super()._select_from_pool(eligible, active_counter, signature_moves, chain_candidates,
                                            active_chain, identity, action, position, target, state)
        if selected.move_id not in pool:
            raise ValueError("Original selector chose outside reconstructed pool")
        self.observed_pools[key] = pool
        self.pool_kinds[kind] += 1
        return selected


def maximum_distinct_matching(pools):
    """Maximum exchange-to-ID matching; overlapping ID sets count only once."""
    owners = {}
    def augment(index, seen):
        for move_id in pools[index]:
            if move_id in seen:
                continue
            seen.add(move_id)
            if move_id not in owners or augment(owners[move_id], seen):
                owners[move_id] = index
                return True
        return False
    return sum(augment(index, set()) for index in range(len(pools)))


def inspect_bout(trace, observed_pools, identities):
    """Both slots remain present, including fighters with no exchanges."""
    by_slot = {"a": [], "b": []}
    counts, sizes, singletons, consumed = Counter(), Counter(), Counter(), set()
    unwrapped = 0
    for event in trace:
        if event.get("type") != "exchange":
            continue
        slot, move_id = event["actor"], event["move_id"]
        key = (event["round"], event["tick"], identities[slot])
        if key in consumed:
            raise ValueError("Duplicate exchange identity")
        consumed.add(key)
        pool = observed_pools.get(key)
        if pool is None:
            pool = (move_id,)
            unwrapped += 1
        if not pool or move_id not in pool:
            raise ValueError("Trace move missing from observed final pool")
        by_slot[slot].append((move_id, pool))
        sizes[len(pool)] += 1
        if len(pool) == 1:
            singletons[move_id] += 1
        counts[move_id] += 1
    if set(observed_pools) - consumed:
        raise ValueError("Selector observations missing from trace")
    fighters = []
    for slot, observations in by_slot.items():
        actual = len({move for move, _ in observations})
        bound = maximum_distinct_matching([pool for _, pool in observations])
        if not actual <= bound <= len(observations):
            raise ValueError("Inconsistent variety matching bound")
        fighters.append(dict(slot=slot, selections=len(observations), actual_distinct=actual,
                             observed_pool_max_distinct=bound))
    return dict(fighters=fighters, selection_counts=counts, pool_sizes=sizes, singleton_move_counts=singletons,
                unwrapped_singletons=unwrapped)


def source_fingerprints():
    names = {
        "constants.py", "models.py", "fight_engine.py", "fight_engine_audit.py", "analysis/fight_candidate_context.py",
        "analysis/compare_candidate_striking.py", "analysis/generate_variety_opportunity_report.py",
    }
    names.update(path.relative_to(ROOT).as_posix() for path in (ROOT / "fight_moves").rglob("*.py"))
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(names)}


def build_report(fights=44, *, combined=True):
    if type(fights) is not int or fights < 1:
        raise ValueError("fights must be a positive integer")
    if type(combined) is not bool:
        raise ValueError("combined must be a boolean")
    schedule = fixture_schedule(fights)
    sources = source_fingerprints()
    fighters, counts, sizes, kinds = [], Counter(), Counter(), Counter()
    unwrapped = 0
    singletons = Counter()
    bouts = []
    with candidate_context(entries=combined, chains=combined, draft_content=combined):
        registry_sha256 = hashlib.sha256(canonical_bytes(build_dump(fight_moves))).hexdigest()
        for index, fixture in enumerate(schedule):
            spec = fixture["spec"]
            a = synthetic_fighter(fixture["a_name"], spec["a_level"], spec["a_style"], spec["a_behaviour"], 0)
            b = synthetic_fighter(fixture["b_name"], spec["b_level"], spec["b_style"], spec["b_behaviour"], 1)
            a.stance, b.stance = spec.get("a_stance", a.stance), spec.get("b_stance", b.stance)
            inputs_before = canonical_bytes(dict(a=asdict(a), b=asdict(b), fixture=fixture))
            engine = VarietyOpportunityHarness()
            audit = run_audited_fight(engine, a, b, fixture["seed"], spec["fight"])
            if inputs_before != canonical_bytes(dict(a=asdict(a), b=asdict(b), fixture=fixture)):
                raise ValueError("Diagnostic fighter or fixture input mutated during bout")
            bouts.append(dict(bout_index=index, spec_id=spec["id"], seed=fixture["seed"],
                              input_sha256=hashlib.sha256(inputs_before).hexdigest(),
                              trace_sha256=hashlib.sha256(canonical_bytes(audit["trace"])).hexdigest(),
                              inputs_unchanged=True))
            row = inspect_bout(audit["trace"], engine.observed_pools,
                               {"a": str(a.fighter_id or a.name), "b": str(b.fighter_id or b.name)})
            fighters.extend(dict(item, bout_index=index, spec_id=spec["id"], seed=fixture["seed"])
                            for item in row["fighters"])
            counts.update(row["selection_counts"])
            sizes.update(row["pool_sizes"])
            singletons.update(row["singleton_move_counts"])
            kinds.update(engine.pool_kinds)
            unwrapped += row["unwrapped_singletons"]
    if sources != source_fingerprints():
        raise ValueError("Diagnostic source changed during run")
    denominator = len(fighters)
    total = sum(counts.values())
    return dict(scope=__doc__, acceptance_gate=False, combined_candidate=combined, fights=fights,
                fighter_count=denominator, zero_opportunity_fighters=sum(row["selections"] == 0 for row in fighters),
                total_move_selections=total, mean_selections_per_fighter=total / denominator,
                mean_distinct_moves_per_fighter=sum(row["actual_distinct"] for row in fighters) / denominator,
                observed_fixed_pool_max_mean_distinct=sum(row["observed_pool_max_distinct"] for row in fighters) / denominator,
                actual_top_ten_share_pct=100 * sum(value for _, value in counts.most_common(10)) / max(1, total),
                pool_kinds=dict(kinds), pool_sizes=dict(sorted(sizes.items())),
                singleton_move_counts=dict(singletons.most_common()),
                unwrapped_singletons=unwrapped, fighters=fighters, bouts=bouts,
                registry_sha256=registry_sha256, source_sha256=sources)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fights", type=int, default=44)
    parser.add_argument("--normal", action="store_true", help="Observe normal instead of combined candidate")
    parser.add_argument("--output", type=Path, help="NEW diagnostic JSON only; never overwrite")
    args = parser.parse_args()
    if args.output and args.output.exists():
        raise FileExistsError(args.output)
    report = build_report(args.fights, combined=not args.normal)
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
