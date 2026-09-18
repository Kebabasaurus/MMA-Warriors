"""Source-bound complete-bout comparison: accepted trial versus native release.

Only the reference arm enters a disposable audit context. The release arm runs
after that context has exited, with its actual application profile and no patches.
"""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import sys
from time import process_time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.fight_candidate_context import candidate_context
from analysis.compare_candidate_striking import fixture_schedule
from analysis.generate_variety_opportunity_report import TerminalRngHarness
from analysis.cradle_setup_candidate import validate_cradle_setups
from analysis.submission_chain_candidate import validate_hold_transitions
from analysis.survival_expansion_candidate import validate_survival_trace
from fight_engine_audit import (run_audited_fight, synthetic_fighter, summarize_results,
                               compare_to_baseline, compare_to_accepted_calibration)
from fight_release import ReleaseFightEngineMixin
from tools.move_registry_parity import canonical_bytes

RECIPE = dict(entries=True, chains=True, draft_content=True, gift_wrap_mount=True,
              heel_hook_identity=True, hold_transitions=True, cradle_setup=True,
              standing_head_damage=True, kick_power=True, survival_expansion=True)


class NativeHarness(ReleaseFightEngineMixin, TerminalRngHarness):
    pass


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sources():
    paths = list(ROOT.glob('*.py'))
    for directory in ('fight_moves', 'analysis', 'tools'):
        paths += list((ROOT / directory).rglob('*.py'))
    return {str(path.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(set(paths))}


def verify(fights=44, *, calibration=False):
    schedule = fixture_schedule(None if calibration else fights, calibration_corpus=calibration)
    before, rng = sources(), random.getstate()
    references = {name: hashlib.sha256((ROOT / 'analysis' / name).read_bytes()).hexdigest()
                  for name in ('fight_engine_baseline.json', 'survival_expansion_440_calibration.json')}
    pairs, results, inputs = [], [], []
    times = Counter()
    validations = {key: Counter() for key in ('cradle', 'holds', 'survival')}
    for index, item in enumerate(schedule):
        spec = item['spec']
        a = synthetic_fighter(item['a_name'], spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
        b = synthetic_fighter(item['b_name'], spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
        if not calibration:
            a.stance, b.stance = spec.get('a_stance', a.stance), spec.get('b_stance', b.stance)
        original = digest((asdict(a), asdict(b), item))
        with candidate_context(**RECIPE):
            reference = TerminalRngHarness()
            start = process_time()
            expected = run_audited_fight(reference, a, b, item['seed'], spec['fight'])
            times['candidate'] += process_time() - start
            expected_rng = reference.terminal_rng_states
        native = NativeHarness()
        start = process_time()
        actual = run_audited_fight(native, a, b, item['seed'], spec['fight'])
        times['native'] += process_time() - start
        if actual != expected or native.terminal_rng_states != expected_rng:
            different = [key for key in actual if actual[key] != expected.get(key)]
            raise ValueError(f'Native parity failed at {index}, seed {item["seed"]}: {different}')
        if digest((asdict(a), asdict(b), item)) != original:
            raise ValueError('Input mutation')
        inputs.append(original)
        pairs.append(dict(seed=item['seed'], spec_id=spec['id'], audit_sha256=digest(actual),
                          terminal_rng_sha256=digest(native.terminal_rng_states)))
        for key, validator in (('cradle', validate_cradle_setups), ('holds', validate_hold_transitions),
                               ('survival', validate_survival_trace)):
            validations[key].update(validator(actual['trace']))
        results.append(dict(spec_id=spec['id'], seed=item['seed'], tier=spec['tier'], matchup=spec['matchup'],
            a_style=spec['a_style'], b_style=spec['b_style'], a_behaviour=spec['a_behaviour'],
            b_behaviour=spec['b_behaviour'], method=actual['method'], round=actual['round'],
            winner_id=actual['winner_id'], scheduled_rounds=5 if spec['fight'].get('title') or spec['fight'].get('main') else 3))
        if (index + 1) % 120 == 0:
            print(f'Native complete-bout/RNG parity: {index + 1}/{len(schedule)}', flush=True)
    if sources() != before or random.getstate() != rng:
        raise ValueError('Source or caller RNG changed during collection')
    if any(hashlib.sha256((ROOT / 'analysis' / name).read_bytes()).hexdigest() != value
           for name, value in references.items()):
        raise ValueError('Calibration reference changed during collection')
    groups = summarize_results(results)
    failures = [f'{key} provenance failed' for key, values in validations.items() if values.get('invalid', 0)]
    advisories = []
    if calibration:
        baseline = json.loads((ROOT / 'analysis/fight_engine_baseline.json').read_text(encoding='utf-8'))
        report = dict(fight_count=len(results), groups=groups)
        findings = compare_to_baseline(report, baseline) + compare_to_accepted_calibration(report)
        for finding in findings:
            if finding == 'Middle finish timing moved by more than 2.0 percentage points':
                advisories.append(finding + ' (user accepted)')
            else:
                failures.append(finding)
        retained = json.loads((ROOT / 'analysis/survival_expansion_440_calibration.json').read_text(encoding='utf-8'))
        if groups != retained['groups']:
            failures.append('Native canonical groups differ from the retained 440 candidate')
    return dict(scope='Complete native versus accepted trial audit, trace and four terminal RNG streams',
        fights=len(schedule), calibration_corpus=calibration, source_sha256=before,
        schedule_sha256=digest(schedule), fixture_sha256=digest(inputs), pairs=pairs,
        reference_sha256=references,
        all_complete_bouts_and_rng_equal=True, groups=groups, validations=validations,
        cpu_seconds=times, balance_advisories=advisories, failures=failures)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--fights', type=int, default=44)
    group.add_argument('--calibration-corpus', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = verify(args.fights, calibration=args.calibration_corpus)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps({key: report[key] for key in ('fights', 'all_complete_bouts_and_rng_equal', 'cpu_seconds', 'failures')}))
    return bool(report['failures'])


if __name__ == '__main__':
    raise SystemExit(main())
