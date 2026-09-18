"""Paired mount versus mount-plus-jab paths; attribution, not acceptance."""
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
from constants import FINISH_METHODS
from analysis.compare_candidate_striking import fixture_schedule
from analysis.fight_candidate_context import candidate_context
from analysis.repertoire_readaptation_candidate import repertoire_readaptation_trial
from analysis.generate_variety_opportunity_report import TerminalRngHarness, source_fingerprints
from fight_engine_audit import run_audited_fight, synthetic_fighter, summarize_results
from tools.move_registry_parity import build_dump, canonical_bytes


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sources():
    result = source_fingerprints()
    for name in ('analysis/jab_timing_diagnostics.py', 'analysis/repertoire_readaptation_candidate.py',
                 'analysis/gift_wrap_mount_candidate.py'):
        result[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    return result


def timing(row):
    if row['method'] not in FINISH_METHODS:
        return 'Nonfinish'
    progress = row['round'] / row['scheduled_rounds']
    return 'Early' if progress <= 1 / 3 else 'Middle' if progress <= 2 / 3 else 'Late'


def compact(event):
    if event is None:
        return None
    keys = ('round', 'tick', 'actor', 'action', 'move_id', 'outcome', 'position_before',
            'position_after', 'top_before', 'top_after', 'plan', 'plan_change', 'counter',
            'actor_streak', 'actor_gas_after', 'defender_gas_after', 'damage_delta',
            'knockdown_delta', 'sequence_source_id', 'sequence_step', 'move_sequence', 'result',
            'bottom_after', 'gas_delta', 'hurt_delta', 'sig_delta', 'td_delta', 'sub_att_delta')
    return {key: event[key] for key in keys if key in event}


def divergences(left, right):
    """Selected-field differences only, not a claim to project every mechanic.

    Plan comparisons require aligned actor/round/tick; tails are length evidence,
    not named choices or tactical adaptation. Every compared field is retained.
    """
    keys = {
        'named': ('move_id',),
        'mechanical_projection': ('round', 'tick', 'actor', 'action', 'outcome', 'position_before',
                       'position_after', 'top_after', 'bottom_after', 'gas_delta', 'damage_delta',
                       'hurt_delta', 'knockdown_delta', 'sig_delta', 'td_delta', 'sub_att_delta'),
        'plan': ('plan', 'plan_change'),
    }
    result = {}
    if len(left) != len(right):
        result['trace_length'] = dict(control=len(left), jab=len(right))
    for i, (a, b) in enumerate(zip(left, right)):
        for name, fields in keys.items():
            if name == 'plan' and any(a.get(key) != b.get(key) for key in ('actor', 'round', 'tick')):
                continue
            changed = [key for key in fields if a.get(key) != b.get(key)]
            if name not in result and changed:
                result[name] = dict(index=i, differing_fields=changed, control=compact(a), jab=compact(b))
    if 'named' in result:
        index = result['named']['index']
        result['named_window'] = {name: [compact(e) for e in events[max(0, index-1):index+5]]
                                  for name, events in (('control', left), ('jab', right))}
    return result


def transitions(pairs):
    matrix, outcomes = Counter(), Counter()
    for pair in pairs:
        matrix[(timing(pair['control']), timing(pair['jab']))] += 1
        outcomes[(pair['control']['method'], pair['jab']['method'])] += 1
    return dict(timing=[dict(control=a, jab=b, bouts=n) for (a,b),n in sorted(matrix.items())],
                methods=[dict(control=a, jab=b, bouts=n) for (a,b),n in sorted(outcomes.items())])


def build_report(*, coverage_fights=None):
    schedule = fixture_schedule(coverage_fights, calibration_corpus=coverage_fights is None)
    fingerprints, rng = sources(), random.getstate()
    pairs, rows = [], {'control': [], 'jab': []}
    with candidate_context(entries=True, chains=True, draft_content=True, gift_wrap_mount=True):
        registry_hash = digest(build_dump(fight_moves))
        engines = {name: TerminalRngHarness() for name in rows}
        for index, fixture in enumerate(schedule):
            spec = fixture['spec']
            a = synthetic_fighter(fixture['a_name'], spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
            b = synthetic_fighter(fixture['b_name'], spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
            if coverage_fights is not None:
                a.stance, b.stance = spec.get('a_stance', a.stance), spec.get('b_stance', b.stance)
            input_hash = digest((asdict(a), asdict(b), fixture))
            pair = dict(index=index, seed=fixture['seed'], spec_id=spec['id'], groups=fixture['groups'],
                        input_sha256=input_hash)
            audits = {}
            for name in rows:
                with repertoire_readaptation_trial(name == 'jab', actions={'jab'}):
                    engine = engines[name]
                    audit = run_audited_fight(engine, a, b, fixture['seed'], spec['fight'])
                row = dict(spec_id=spec['id'], seed=fixture['seed'], tier=spec['tier'],
                           matchup=spec['matchup'], a_style=spec['a_style'], b_style=spec['b_style'],
                           a_behaviour=spec['a_behaviour'], b_behaviour=spec['b_behaviour'],
                           method=audit['method'], round=audit['round'], winner_id=audit['winner_id'],
                           scheduled_rounds=5 if spec['fight'].get('title') or spec['fight'].get('main') else 3)
                rows[name].append(row)
                pair[name] = dict(row, audit_sha256=digest(audit),
                                  terminal_rng_sha256=digest(engine.terminal_rng_states))
                audits[name] = [e for e in audit['trace'] if e.get('type') == 'exchange']
            pair['divergences'] = divergences(audits['control'], audits['jab'])
            if digest((asdict(a), asdict(b), fixture)) != input_hash:
                raise AssertionError('Paired input mutated')
            pairs.append(pair)
        if digest(build_dump(fight_moves)) != registry_hash:
            raise AssertionError('Registry mutated')
    if random.getstate() != rng or sources() != fingerprints:
        raise AssertionError('Source or caller RNG drift during collection')
    groups = {name: summarize_results(values) for name, values in rows.items()}
    reference_hashes = {}
    if coverage_fights is None:
        for name, filename in (('control', 'joint_candidate_gift_wrap_mount_calibration.json'),
                               ('jab', 'joint_candidate_mount_jab_calibration.json')):
            path = ROOT / 'analysis' / filename
            reference = json.loads(path.read_text(encoding='utf-8'))
            if groups[name] != reference['groups']:
                raise AssertionError(f'{name} does not reproduce all canonical reference groups')
            reference_hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(scope='Paired path attribution; no calibration acceptance or altered release gates',
                corpus='full_calibration' if coverage_fights is None else 'coverage_diagnostic',
                fights_per_arm=len(schedule), source_sha256=fingerprints, registry_sha256=registry_hash,
                reference_sha256=reference_hashes, groups=groups, paired_bouts=pairs,
                all_bouts=transitions(pairs), competitive=transitions(
                    [p for p in pairs if 'Competitive' in p['groups']]))


def recheck_changed_outcomes(prior):
    """Re-read changed outcome paths, retaining and validating the full parent evidence.

    Only this diagnostic's source may differ; both fresh full-audit fingerprints
    must still match each parent bout. This cannot recalibrate a mechanical edit.
    """
    fingerprints, rng = sources(), random.getstate()
    expected_keys = set(fingerprints)
    if set(prior['source_sha256']) != expected_keys or any(
            name != 'analysis/jab_timing_diagnostics.py' and prior['source_sha256'][name] != value
            for name, value in fingerprints.items()):
        raise ValueError('Parent mechanical sources differ; collect a fresh full pair')
    schedule = fixture_schedule(calibration_corpus=True)
    if prior['corpus'] != 'full_calibration' or prior['fights_per_arm'] != len(schedule):
        raise ValueError('Recheck requires the complete calibration parent')
    pairs = prior['paired_bouts']
    if len(pairs) != len(schedule):
        raise ValueError('Incomplete parent fixtures')
    for name, filename in (('control', 'joint_candidate_gift_wrap_mount_calibration.json'),
                           ('jab', 'joint_candidate_mount_jab_calibration.json')):
        path = ROOT / 'analysis' / filename
        if hashlib.sha256(path.read_bytes()).hexdigest() != prior['reference_sha256'][filename]:
            raise ValueError('Parent calibration reference changed')
        rebuilt = summarize_results([p[name] for p in pairs])
        if rebuilt != prior['groups'][name] or rebuilt != json.loads(path.read_text())['groups']:
            raise ValueError('Parent canonical groups do not reconcile')
    checked = []
    with candidate_context(entries=True, chains=True, draft_content=True, gift_wrap_mount=True):
        if digest(build_dump(fight_moves)) != prior['registry_sha256']:
            raise ValueError('Parent registry differs')
        for index, (fixture, pair) in enumerate(zip(schedule, pairs)):
            if (pair['index'], pair['seed'], pair['spec_id'], tuple(pair['groups'])) != (
                    index, fixture['seed'], fixture['spec']['id'], fixture['groups']):
                raise ValueError('Parent schedule/order differs')
            if all(pair['control'][key] == pair['jab'][key] for key in ('method', 'round', 'winner_id')):
                continue
            spec = fixture['spec']
            a = synthetic_fighter(fixture['a_name'], spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
            b = synthetic_fighter(fixture['b_name'], spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
            if digest((asdict(a), asdict(b), fixture)) != pair['input_sha256']:
                raise ValueError('Parent fighter input differs')
            audits = {}
            for name in ('control', 'jab'):
                engine = TerminalRngHarness()
                with repertoire_readaptation_trial(name == 'jab', actions={'jab'}):
                    audit = run_audited_fight(engine, a, b, fixture['seed'], spec['fight'])
                if (digest(audit) != pair[name]['audit_sha256'] or
                        digest(engine.terminal_rng_states) != pair[name]['terminal_rng_sha256']):
                    raise AssertionError('Fresh bout/RNG differs from parent')
                audits[name] = [e for e in audit['trace'] if e.get('type') == 'exchange']
            if digest((asdict(a), asdict(b), fixture)) != pair['input_sha256']:
                raise AssertionError('Recheck mutated input')
            checked.append(dict(pair, divergences=divergences(audits['control'], audits['jab'])))
        if digest(build_dump(fight_moves)) != prior['registry_sha256']:
            raise AssertionError('Registry mutated')
    if sources() != fingerprints or random.getstate() != rng:
        raise AssertionError('Recheck source or RNG drift')
    return dict(scope='Changed method/round/winner paths only; full parent timing totals retained, not new calibration',
                parent_report_sha256=digest(prior), source_sha256=fingerprints,
                full_parent_fights=len(schedule), rechecked_bouts=len(checked), paired_bouts=checked,
                all_bouts=transitions(pairs), competitive=transitions(
                    [p for p in pairs if 'Competitive' in p['groups']]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coverage-fights', type=int, help='Explicit short diagnostic, not full calibration')
    parser.add_argument('--recheck-changed', type=Path, help='Recheck changed outcomes from an unchanged full parent')
    parser.add_argument('--output', type=Path, required=True, help='New artifact only')
    args = parser.parse_args()
    if args.recheck_changed and args.coverage_fights is not None:
        parser.error('Recheck requires a full parent, not coverage')
    if args.output.exists():
        raise FileExistsError(args.output)
    result = (recheck_changed_outcomes(json.loads(args.recheck_changed.read_text(encoding='utf-8')))
              if args.recheck_changed else build_report(coverage_fights=args.coverage_fights))
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(fights_per_arm=result.get('fights_per_arm', result.get('full_parent_fights')),
                         all_bouts=result['all_bouts']), indent=2))


if __name__ == '__main__':
    main()
