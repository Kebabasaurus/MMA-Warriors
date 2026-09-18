"""Natural Catch matchup evidence, supplementary to canonical acceptance."""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fight_moves
from analysis.cradle_setup_candidate import validate_cradle_setups, HOLD, MOVE_ID
from analysis.fight_candidate_context import candidate_context
from analysis.generate_variety_opportunity_report import TerminalRngHarness, source_fingerprints
from fight_engine_audit import run_audited_fight, synthetic_fighter
from tools.move_registry_parity import build_dump, canonical_bytes

OPPONENTS = (('BJJ', 'Control'), ('Wrestler', 'Control'),
             ('Submission Grappler', 'Submission Hunter'), ('MMA Generalist', 'Pressure'))
ARMS = ('hold_transitions', 'hold_transitions_cradle')
CHAIN_IDS = ('top_submission_chain', 'guard_submission_chain')


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sources():
    result = source_fingerprints()
    paths = list((ROOT / 'analysis').glob('*candidate*.py'))
    paths += [Path(__file__), ROOT / 'tools/move_registry_parity.py']
    for path in paths:
        result[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def fixture_schedule():
    result = []
    for tier_index, level in enumerate((55, 70, 85)):
        for opponent_index, (style, behaviour) in enumerate(OPPONENTS):
            spec_id = f'catch-natural-{level}-{opponent_index}'
            for repetition in range(20):
                result.append(dict(spec_id=spec_id, level=level, a_style='Catch Wrestler',
                    a_behaviour='Control', b_style=style, b_behaviour=behaviour,
                    a_name=f'Catch Natural {level} {opponent_index} A',
                    b_name=f'Catch Natural {level} {opponent_index} B',
                    seed=12000000 + tier_index * 100000 + opponent_index * 1000 + repetition,
                    repetition=repetition, fight=dict(title=False, main=False)))
    return result


def observations(audit, enabled):
    trace = audit['trace']
    counts = validate_cradle_setups(trace) if enabled else dict(roots=0, used=0, named=0, invalid=0)
    actual_holds = sum((event.get('submission_technique') or {}).get('name') == HOLD[0] for event in trace)
    actual_named = sum(event.get('move_id') == MOVE_ID for event in trace)
    if enabled and (counts['used'] != actual_holds or counts['named'] != actual_named):
        raise AssertionError('Cradle observations do not reconcile to actual holds and named selections')
    if not enabled and (actual_holds or actual_named or any(event.get('cradle_setup') for event in trace)):
        raise AssertionError('Default arm unexpectedly contains cradle development evidence')
    if counts['invalid']:
        raise AssertionError('Invalid cradle provenance in natural matchup')
    examples = []
    for index, event in enumerate(trace):
        if (event.get('cradle_setup') or {}).get('status') in ('created', 'used'):
            examples.append(dict(trace_index=index, event=event,
                                 next_event=trace[index + 1] if index + 1 < len(trace) else None))
    return counts, examples


def build_report(*, fights=None, progress=None):
    schedule = fixture_schedule()
    if fights is not None:
        if type(fights) is not int or not 1 <= fights <= len(schedule):
            raise ValueError('Diagnostic limit must be an integer from 1 to 240')
        schedule = schedule[:fights]
    fingerprint, rng = sources(), random.getstate()
    registry_before = digest(build_dump(fight_moves))
    arms = {}
    for name in ARMS:
        enabled = name == ARMS[1]
        totals = Counter(dict(roots=0, used=0, named=0, invalid=0))
        methods, examples = Counter(), []
        chain_totals = Counter(dict.fromkeys(CHAIN_IDS, 0))
        arm_rows = []
        with candidate_context(entries=True, chains=True, draft_content=True, gift_wrap_mount=True,
                               heel_hook_identity=True, hold_transitions=True, cradle_setup=enabled):
            registry_hash = digest(build_dump(fight_moves))
            engine = TerminalRngHarness()
            for index, fixture in enumerate(schedule):
                before_fighter_rng = random.getstate()
                a = synthetic_fighter(fixture['a_name'], fixture['level'], fixture['a_style'], fixture['a_behaviour'], 0)
                b = synthetic_fighter(fixture['b_name'], fixture['level'], fixture['b_style'], fixture['b_behaviour'], 1)
                if random.getstate() != before_fighter_rng:
                    raise AssertionError('Synthetic defaults changed caller RNG')
                input_hash = digest((asdict(a), asdict(b), fixture))
                audit = run_audited_fight(engine, a, b, fixture['seed'], fixture['fight'])
                if input_hash != digest((asdict(a), asdict(b), fixture)) or random.getstate() != before_fighter_rng:
                    raise AssertionError('Natural matchup input or caller RNG mutated')
                counts, found = observations(audit, enabled)
                chain_counts = {move_id: sum(event.get('move_id') == move_id for event in audit['trace'])
                                for move_id in CHAIN_IDS}
                chain_totals.update(chain_counts)
                totals.update(counts)
                methods[audit['method']] += 1
                identity = dict(index=index, spec_id=fixture['spec_id'], seed=fixture['seed'])
                examples.extend(dict(identity, **example) for example in found)
                arm_rows.append(dict(identity, input_sha256=input_hash, method=audit['method'],
                    round=audit['round'], winner_id=audit['winner_id'], counts=counts, chain_selections=chain_counts,
                    audit_sha256=digest(audit), terminal_rng_sha256=digest(engine.terminal_rng_states)))
                if progress and (index + 1) % 20 == 0:
                    progress(name, index + 1, len(schedule))
            if registry_hash != digest(build_dump(fight_moves)):
                raise AssertionError('Natural matchup registry mutated')
        arms[name] = dict(methods=dict(sorted(methods.items())), counts=dict(totals),
                          chain_selections=dict(chain_totals), registry_sha256=registry_hash,
                          bouts=arm_rows, examples=examples)
    for control, trial in zip(arms[ARMS[0]]['bouts'], arms[ARMS[1]]['bouts']):
        if any(control[key] != trial[key] for key in ('index', 'spec_id', 'seed', 'input_sha256')):
            raise AssertionError('Paired matchup input mismatch')
    if random.getstate() != rng or sources() != fingerprint or digest(build_dump(fight_moves)) != registry_before:
        raise AssertionError('Source, registry or caller RNG drift during collection')
    return dict(scope='Supplementary natural Catch matchups; not canonical calibration or release acceptance',
                corpus='catch_natural_matchups_240' if fights is None else 'catch_natural_matchup_prefix',
                fights_per_arm=len(schedule), scheduled_rounds=3, schedule=schedule,
                schedule_sha256=digest(schedule), source_sha256=fingerprint,
                original_registry_sha256=registry_before, arms=arms)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fights', type=int, help='Optional prefix for diagnostic tooling checks, never a full corpus')
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(args.output)
    report = build_report(fights=args.fights,
                          progress=lambda arm, done, count: print(f'{arm}: {done}/{count}', flush=True))
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({arm: row['counts'] for arm, row in report['arms'].items()}, indent=2))


if __name__ == '__main__':
    main()
