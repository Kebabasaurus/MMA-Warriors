"""Observe counter-window ages at initiative calls; never change fight choices."""
import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import random
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis import compare_candidate_striking as paired


def classify_call(engine, fighter, opponent, state):
    """Disjoint native-fact bins, plus an explicitly limited guard observation."""
    actor = engine.fight_state_key(fighter, state)
    other = engine.fight_state_key(opponent, state)
    position = state.get('position') or 'unknown'
    window = state.get('counter_window')
    owner, age = 'no_window', 'no_window'
    if window:
        window = window if isinstance(window, dict) else {}
        owner = ('own' if window.get('fighter') == actor else
                 'opponent' if window.get('fighter') == other else 'unknown')
        current_round, current_tick = state.get('round'), state.get('tick')
        created_round, created_tick = window.get('created_round'), window.get('created_tick')
        metadata = (current_round, current_tick, created_round, created_tick)
        if not all(type(value) is int and value > 0 for value in metadata):
            age = 'unknown'
        elif created_round < current_round:
            age = 'previous_round'
        elif created_round > current_round or created_tick > current_tick:
            age = 'future_metadata'
        else:
            age = 'same_round_age_gt_2' if current_tick - created_tick > 2 else 'same_round_age_0_to_2'
    stale_guard = (getattr(engine, '_experimental_chain_action_weighting', False)
                   and position in ('range', 'pocket') and owner == 'opponent'
                   and age in ('previous_round', 'same_round_age_gt_2'))
    gas, hurt = state.get('gas', {}).get(actor), state.get('hurt', {}).get(actor)
    ready = (all(isinstance(value, (int, float)) and math.isfinite(value) for value in (gas, hurt))
             and gas > 22 and hurt <= fighter.toughness * 0.65)
    return position, owner, age, bool(stale_guard), bool(stale_guard and ready)


@contextmanager
def observe_initiative(engine, counts):
    """Single-call instance wrapper; restore inherited/overridden methods and RNG."""
    original, rng = engine.initiative, random.getstate()
    def observe(fighter, opponent, state):
        counts[classify_call(engine, fighter, opponent, state)] += 1
        return original(fighter, opponent, state)
    try:
        with patch.object(engine, 'initiative', observe):
            yield
    finally:
        random.setstate(rng)


def summarize(counts):
    rows = [dict(position=p, owner=o, age=a, stale_opponent_guard=g,
                 otherwise_ready_stale_guard=r, initiative_calls=n)
            for (p, o, a, g, r), n in sorted(counts.items())]
    return dict(initiative_calls=sum(counts.values()),
                stale_opponent_guard_calls=sum(row['initiative_calls'] for row in rows if row['stale_opponent_guard']),
                otherwise_ready_stale_guard_calls=sum(row['initiative_calls'] for row in rows if row['otherwise_ready_stale_guard']),
                observations=rows)


def build_report(fight_count=300):
    schedule = paired.fixture_schedule(fight_count)
    rng = random.getstate()
    try:
        sources = [ROOT / name for name in ('fight_engine.py', 'fight_engine_audit.py', 'constants.py', 'models.py',
                   'analysis/fight_candidate_context.py', 'analysis/compare_candidate_striking.py',
                   'analysis/standing_counter_diagnostics.py')]
        sources += sorted((ROOT / 'fight_moves').rglob('*.py'))
        hashes = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
        fixtures = []
        for row in schedule:
            spec = row['spec']
            a = paired.synthetic_fighter(row['a_name'], spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
            b = paired.synthetic_fighter(row['b_name'], spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
            a.stance, b.stance = spec.get('a_stance', a.stance), spec.get('b_stance', b.stance)
            fixtures.append((a, b, row['seed'], deepcopy(spec['fight'])))
        inputs = deepcopy([(vars(a), vars(b), seed, fight) for a, b, seed, fight in fixtures])
        arms = {}
        for name, enabled in (('current_normal', False), ('combined_candidate', True)):
            with paired.candidate_context(entries=enabled, chains=enabled, draft_content=enabled):
                import fight_moves
                registry_hash = paired.digest(paired.build_dump(fight_moves))
                engine, totals, bouts = paired.FightAuditHarness(), Counter(), []
                for index, (a, b, seed, fight) in enumerate(fixtures):
                    counts = Counter()
                    with observe_initiative(engine, counts):
                        audit = paired.run_audited_fight(engine, a, b, seed, fight)
                    totals.update(counts)
                    bouts.append(dict(index=index, seed=seed, spec_id=schedule[index]['spec']['id'],
                                      method=audit['method'], round=audit['round'],
                                      audit_sha256=paired.digest(audit), trace_sha256=paired.digest(audit['trace']),
                                      **summarize(counts)))
                arms[name] = dict(registry_sha256=registry_hash,
                                 configuration=dict(specialist_entries=enabled, chain_action_weighting=enabled,
                                                    draft_content=enabled), bouts=bouts, **summarize(totals))
        if inputs != [(vars(a), vars(b), seed, fight) for a, b, seed, fight in fixtures]:
            raise AssertionError('Counter observation mutated fixture inputs')
        if any(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != value for name, value in hashes.items()):
            raise RuntimeError('Source changed while collecting counter observations')
        return dict(scope='Move-coverage initiative-opportunity diagnostic; not finish calibration or counterfactual outcomes',
                    fights_per_arm=len(fixtures), corpus='move_coverage', source_sha256=hashes,
                    input_sha256=paired.digest(inputs), arms=arms,
                    metric_scope=dict(denominator='Initiative calls, both fighters; not exchanges or selected actions',
                        age='Same-round integer tick age; previous rounds separate; missing/invalid metadata unknown',
                        guard='Candidate standing opponent-window early guard with age >2 or a previous round',
                        readiness='Guard observations with gas >22 and hurt <= toughness*0.65; no legal-chain preview',
                        limit='No inferred lost positive bonus, actor swap, attack, knockdown or finish'))
    finally:
        random.setstate(rng)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fights', type=int, default=300)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if args.output and args.output.exists():
        raise FileExistsError(args.output)
    report = build_report(args.fights)
    if args.output:
        with args.output.open('x', encoding='utf-8') as output:
            json.dump(report, output, indent=2)
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
