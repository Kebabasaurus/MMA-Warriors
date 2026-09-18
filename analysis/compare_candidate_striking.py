"""Read-only paired current-normal/combined diagnostic, not calibration acceptance."""
import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import random
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.fight_candidate_context import candidate_context
from fight_engine_audit import (FightAuditHarness, move_report_specs, matchup_specs, build_baseline,
                               summarize_results, ACCEPTED_RESULT_CALIBRATION,
                               run_audited_fight, synthetic_fighter)
from tools.move_registry_parity import build_dump, canonical_bytes


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


@contextmanager
def standing_chain_ablation(enabled=False):
    """Disposable single-thread audit only; preserve every non-standing menu."""
    rng = random.getstate()
    original = FightAuditHarness._chain_action_weights
    def bypass(engine, fighter, opponent, state, weights, round_no, tick):
        if state.get('position') in ('range', 'pocket'):
            return weights
        return original(engine, fighter, opponent, state, weights, round_no, tick)
    try:
        if enabled:
            with patch.object(FightAuditHarness, '_chain_action_weights', bypass):
                yield
        else:
            yield
    finally:
        random.setstate(rng)


@contextmanager
def failed_shot_retention_ablation(enabled=False):
    """Use the legacy denied-shot gate only, inside a disposable audit.

    resolve_takedown consults this switch only after successful/cage branches.
    Restore the instance override even if resolution raises or contexts nest.
    This is attribution, not a proposed removal of specialist positions.
    """
    rng = random.getstate()
    original = FightAuditHarness.resolve_takedown
    def legacy_retention(engine, actor, defender, margin, state, round_stats):
        entries = getattr(engine, '_experimental_specialist_entries', False)
        set_position = engine.set_fight_position
        def preserve_setup_cleanup(*args, **kwargs):
            # The position setter also reads the entry flag. Its private setup
            # invalidation belongs to the candidate and is not part of this ablation.
            with patch.object(engine, '_experimental_specialist_entries', entries, create=True):
                return set_position(*args, **kwargs)
        with patch.object(engine, '_experimental_specialist_entries', False, create=True), \
                patch.object(engine, 'set_fight_position', preserve_setup_cleanup):
            return original(engine, actor, defender, margin, state, round_stats)
    try:
        if enabled:
            with patch.object(FightAuditHarness, 'resolve_takedown', legacy_retention):
                yield
        else:
            yield
    finally:
        random.setstate(rng)


def summarize_audits(audits):
    """Aggregate native exchange facts without changing or annotating the input."""
    totals, actions, positions, contexts, quality_contexts, action_styles, methods, bout_outcomes = (
        Counter(), {}, {}, {}, {}, {}, Counter(), Counter()
    )
    bouts = 0
    standing_exits, standing_shots_without_takedown = Counter(), Counter()
    for audit in audits:
        bouts += 1
        method = audit['method']
        methods[method] += 1
        exchanges = [event for event in audit['trace'] if event.get('type') == 'exchange']
        bout_knockdowns = sum(sum(int(value) for value in event.get('knockdown_delta', {}).values())
                              for event in exchanges)
        ko_tko = method in ('KO', 'TKO')
        bout_outcomes['bouts_with_knockdown'] += int(bout_knockdowns > 0)
        bout_outcomes['bouts_with_ko_tko'] += int(ko_tko)
        bout_outcomes['knockdown_bouts_with_ko_tko'] += int(bout_knockdowns > 0 and ko_tko)
        bout_outcomes['knockdown_bouts_without_ko_tko'] += int(bout_knockdowns > 0 and not ko_tko)
        bout_outcomes['ko_tko_bouts_without_knockdown'] += int(ko_tko and bout_knockdowns == 0)
        for event in audit['trace']:
            if event.get('type') != 'exchange':
                continue
            actor = event['actor']
            other = 'b' if actor == 'a' else 'a'
            values = Counter(exchanges=1, attempts=event['sig_att_delta'], landed=event['sig_delta'])
            for part in ('head', 'body', 'leg', 'damage', 'knockdown'):
                delta = event[part + '_delta']
                values[part] = sum(delta.values())
                values[part + '_to_actor'] = delta[actor] if part != 'knockdown' else delta[other]
                values[part + '_to_opponent'] = delta[other] if part != 'knockdown' else delta[actor]
            values['net_hurt_change'] = sum(event['hurt_delta'].values())
            values['referee_standups'] = int((event.get('referee_ground_action') or {}).get('type') == 'standup')
            values['neutral_resets'] = int(event.get('outcome') == 'neutral_reset')
            values['finishing_exchanges'] = int(bool(event.get('stoppage')))
            values['finishing_knockdowns'] = int(bool(event.get('stoppage')) and values['knockdown'] > 0)
            values['knockdowns_in_ko_tko_bouts'] = values['knockdown'] if ko_tko else 0
            values['knockdowns_in_other_bouts'] = values['knockdown'] if not ko_tko else 0
            action, position = event['action'], event['position_before']
            if position in ('range', 'pocket'):
                destination = event.get('position_after') or 'unknown'
                if destination not in ('range', 'pocket'):
                    standing_exits[f'{action}|{destination}'] += 1
                if action in ('shoot', 'takedown') and event.get('td_delta') == 0:
                    standing_shots_without_takedown[destination] += 1
            gas = float(event.get('actor_gas_after', 0) or 0)
            gas_band = '<35' if gas < 35 else '35-59' if gas < 60 else '60+'
            streak = int(event.get('actor_streak', 0) or 0)
            streak_band = '1' if streak <= 1 else '2' if streak == 2 else '3+'
            totals.update(values)
            actions.setdefault(action, Counter()).update(values)
            positions.setdefault(position, Counter()).update(values)
            contexts.setdefault((action, position), Counter()).update(values)
            quality_contexts.setdefault(
                (action, position, gas_band, streak_band, bool(event.get('counter'))), Counter()
            ).update(values)
            action_styles.setdefault((action, str(event.get('actor_style') or 'Unknown')), Counter()).update(values)
    return {'bouts': bouts, 'methods': dict(sorted(methods.items())),
            'standing_exits': dict(sorted(standing_exits.items())),
            'standing_shots_without_takedown': dict(sorted(standing_shots_without_takedown.items())),
            'bout_outcomes': dict(bout_outcomes), 'totals': dict(totals),
            'by_action': {k: dict(v) for k, v in sorted(actions.items())},
            'by_pre_position': {k: dict(v) for k, v in sorted(positions.items())},
            'by_action_pre_position': [dict(action=a, position=p, **v) for (a, p), v in sorted(contexts.items())],
            'by_action_style': [dict(action=a, actor_style=s, **v)
                                for (a, s), v in sorted(action_styles.items())],
            'by_action_quality_context': [
                dict(action=a, position=p, gas_band=g, streak_band=s, counter=c, **v)
                for (a, p, g, s, c), v in sorted(quality_contexts.items())
            ]}


def fixture_schedule(fight_count=None, *, calibration_corpus=False):
    """Exact corpus metadata, independently inspectable without simulating fights."""
    if calibration_corpus:
        if fight_count is not None:
            raise ValueError('Calibration corpus cannot be shortened or combined with fight_count')
        specs = matchup_specs()
        seeds = inspect.signature(build_baseline).parameters['seeds_per_matchup'].default
        if len(specs) * seeds != ACCEPTED_RESULT_CALIBRATION['fight_count']:
            raise ValueError('Canonical fixture schedule no longer matches the locked full corpus')
        indices = ((i, seed) for i in range(len(specs)) for seed in range(seeds))
    else:
        fight_count = 300 if fight_count is None else fight_count
        if type(fight_count) is not int or fight_count < 1:
            raise ValueError('fight_count must be a positive integer')
        specs = move_report_specs()
        indices = ((i % len(specs), i // len(specs)) for i in range(fight_count))
    rows = []
    for spec_index, seed_index in indices:
        spec = deepcopy(specs[spec_index])
        prefix = 'Audit' if calibration_corpus else 'Move audit'
        groups = tuple(summarize_results([dict(spec, method='Draw', round=1,
            scheduled_rounds=5 if spec['fight'].get('title') or spec['fight'].get('main') else 3)]))
        rows.append(dict(spec=spec, seed=(8_210_000 if calibration_corpus else 9_310_000) + spec_index * 10_000 + seed_index,
                         a_name=f"{prefix} {spec['id']} A", b_name=f"{prefix} {spec['id']} B", groups=groups))
    return rows


def merge_summaries(target, source):
    """Merge already summarized bouts; never repeatedly walk their traces."""
    if not target:
        target.update(deepcopy(source))
        return
    target['bouts'] += source['bouts']
    for field in ('methods', 'totals', 'standing_exits', 'standing_shots_without_takedown'):
        for key, value in source[field].items():
            target[field][key] = target[field].get(key, 0) + value
    for key, value in source['bout_outcomes'].items():
        target['bout_outcomes'][key] = target['bout_outcomes'].get(key, 0) + value
    for field in ('by_action', 'by_pre_position'):
        for key, values in source[field].items():
            row = target[field].setdefault(key, {})
            for metric, value in values.items():
                row[metric] = row.get(metric, 0) + value
    contexts = {(r['action'], r['position']): r for r in target['by_action_pre_position']}
    for row in source['by_action_pre_position']:
        key = (row['action'], row['position'])
        if key not in contexts:
            contexts[key] = deepcopy(row)
        else:
            for metric, value in row.items():
                if metric not in ('action', 'position'):
                    contexts[key][metric] += value
    target['by_action_pre_position'] = [contexts[key] for key in sorted(contexts)]
    action_styles = {(r['action'], r['actor_style']): r for r in target['by_action_style']}
    for row in source['by_action_style']:
        key = (row['action'], row['actor_style'])
        if key not in action_styles:
            action_styles[key] = deepcopy(row)
        else:
            for metric, value in row.items():
                if metric not in ('action', 'actor_style'):
                    action_styles[key][metric] += value
    target['by_action_style'] = [action_styles[key] for key in sorted(action_styles)]
    quality = {
        (r['action'], r['position'], r['gas_band'], r['streak_band'], r['counter']): r
        for r in target['by_action_quality_context']
    }
    for row in source['by_action_quality_context']:
        key = (row['action'], row['position'], row['gas_band'], row['streak_band'], row['counter'])
        if key not in quality:
            quality[key] = deepcopy(row)
        else:
            for metric, value in row.items():
                if metric not in ('action', 'position', 'gas_band', 'streak_band', 'counter'):
                    quality[key][metric] += value
    target['by_action_quality_context'] = [quality[key] for key in sorted(quality)]


def build_comparison(fight_count=None, *, calibration_corpus=False, ablate_standing_chains=False,
                     ablate_pocket_action_bias=False, ablate_failed_shot_retention=False):
    if sum(bool(value) for value in (ablate_standing_chains, ablate_pocket_action_bias,
                                    ablate_failed_shot_retention)) > 1:
        raise ValueError('Select only one candidate ablation per paired comparison')
    schedule = fixture_schedule(fight_count, calibration_corpus=calibration_corpus)
    fight_count = len(schedule)
    if type(fight_count) is not int or fight_count < 1:
        raise ValueError('fight_count must be a positive integer')
    rng = random.getstate()
    try:
        sources = [ROOT / name for name in ('fight_engine.py', 'fight_engine_audit.py', 'constants.py',
                   'models.py', 'analysis/fight_candidate_context.py', 'analysis/compare_candidate_striking.py')]
        sources += sorted((ROOT / 'fight_moves').rglob('*.py'))
        hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
        fixtures = []
        for row in schedule:
            spec = row['spec']
            a = synthetic_fighter(row['a_name'], spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
            b = synthetic_fighter(row['b_name'], spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
            if not calibration_corpus:
                a.stance, b.stance = spec.get('a_stance', a.stance), spec.get('b_stance', b.stance)
            fixtures.append((a, b, row['seed'], deepcopy(spec['fight'])))
        inputs = [deepcopy((vars(a), vars(b), seed, fight)) for a, b, seed, fight in fixtures]
        arms, paired = {}, [{'index': i, 'seed': f[2], 'spec_id': schedule[i]['spec']['id']} for i, f in enumerate(fixtures)]
        if ablate_standing_chains:
            configurations = (('combined_candidate', True, False, True),
                              ('standing_chain_ablated_candidate', True, True, True))
        elif ablate_pocket_action_bias:
            configurations = (('combined_candidate', True, False, True),
                              ('pocket_action_bias_ablated_candidate', True, False, False))
        elif ablate_failed_shot_retention:
            configurations = (('combined_candidate', True, False, True),
                              ('failed_shot_retention_ablated_candidate', True, False, True))
        else:
            configurations = (('current_normal', False, False, True),
                              ('combined_candidate', True, False, True))
        for name, enabled, ablated, pocket_bias in configurations:
            with candidate_context(entries=enabled, chains=enabled, draft_content=enabled,
                                   pocket_action_bias=pocket_bias), standing_chain_ablation(ablated), \
                    failed_shot_retention_ablation(name == 'failed_shot_retention_ablated_candidate'):
                import fight_moves
                registry_hash = digest(build_dump(fight_moves))
                engine = FightAuditHarness()
                groups = {}
                def audited_bouts():
                    for i, (a, b, seed, fight) in enumerate(fixtures):
                        audit = run_audited_fight(engine, a, b, seed, fight)
                        paired[i][name] = {'method': audit['method'], 'round': audit['round'],
                                           'trace_sha256': digest(audit['trace'])}
                        summary = summarize_audits([audit])
                        for group in schedule[i]['groups']:
                            merge_summaries(groups.setdefault(group, {}), summary)
                        yield audit
                arms[name] = dict(summarize_audits(audited_bouts()), registry_sha256=registry_hash, groups=groups,
                    configuration={'specialist_entries': enabled, 'chain_action_weighting': enabled,
                                   'draft_content': enabled, 'bypass_standing_chain_weights': ablated,
                                   'pocket_action_bias': pocket_bias,
                                   'legacy_failed_shot_retention': name == 'failed_shot_retention_ablated_candidate'})
        if inputs != [(vars(a), vars(b), seed, fight) for a, b, seed, fight in fixtures]:
            raise AssertionError('Diagnostic mutated input fighters or fight configuration')
        if any(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != value for name, value in hashes.items()):
            raise RuntimeError('Source changed while collecting paired evidence; rerun against a settled revision')
        scope = ('Combined candidate versus standing-only chain-weight ablation; diagnostic, not calibration acceptance'
                 if ablate_standing_chains else
                 'Combined candidate versus legacy denied-shot retention; diagnostic, not calibration acceptance'
                 if ablate_failed_shot_retention else
                 'Combined candidate versus pocket action-bias ablation; diagnostic, not calibration acceptance'
                 if ablate_pocket_action_bias else
                 'Matched current normal versus combined candidate; not legacy baseline or calibration acceptance')
        comparison = ('standing_chain_ablation' if ablate_standing_chains else
                      'failed_shot_retention_ablation' if ablate_failed_shot_retention else
                      'pocket_action_bias_ablation' if ablate_pocket_action_bias else
                      'current_normal_vs_candidate')
        return {'scope': scope, 'comparison': comparison,
                'corpus': 'full_calibration_3840' if calibration_corpus else 'move_coverage',
                'fights_per_arm': fight_count, 'engine_sha256': hashes['fight_engine.py'], 'source_sha256': hashes,
                'metric_scope': {'attempts_and_landed': 'Acting-fighter significant-strike deltas, not all technique attempts',
                    'standing_exits': 'Recorded range/pocket to non-standing settled destinations, keyed action|destination; unknown remains explicit',
                    'standing_shots_without_takedown': 'Standing shot exchanges with recorded zero actor takedowns, including cage progress; not inferred failure semantics',
                    'damage': 'Both fighters summed; received-damage actor/opponent splits are exchange attribution, not technique causality',
                    'knockdown': 'Knockdowns scored; to_actor/to_opponent denote recipient, reversing scored-slot identity',
                    'net_hurt_change': 'Net native exchange delta only; not isolated recovery or pressure-reset attribution',
                    'limits': 'No unrecorded stoppage checks, pressure resets, or finish-branch attribution inferred from final methods'},
                'input_sha256': digest(inputs), 'arms': arms, 'paired_bouts': paired}
    finally:
        random.setstate(rng)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    corpus = parser.add_mutually_exclusive_group()
    corpus.add_argument('--fights', type=int, help='Coverage fights per arm; defaults to 300')
    corpus.add_argument('--calibration-corpus', action='store_true', help='Entire canonical 3,840-bout schedule per arm')
    ablation = parser.add_mutually_exclusive_group()
    ablation.add_argument('--standing-chain-ablation', dest='ablate_standing_chains', action='store_true',
                          help='Compare combined candidate with only range/pocket chain-weight redistribution bypassed')
    ablation.add_argument('--pocket-action-bias-ablation', dest='ablate_pocket_action_bias', action='store_true',
                          help='Compare combined candidate with only pocket power/kick/clinch selection bias bypassed')
    ablation.add_argument('--failed-shot-retention-ablation', dest='ablate_failed_shot_retention', action='store_true',
                          help='Compare combined candidate with only denied-shot retention using its legacy gate')
    parser.add_argument('--output', type=Path, help='Optional NEW JSON file; never overwritten')
    args = parser.parse_args(argv)
    if args.output and args.output.exists():
        raise FileExistsError(args.output)
    options = ({'ablate_standing_chains': True} if args.ablate_standing_chains else
               {'ablate_failed_shot_retention': True} if args.ablate_failed_shot_retention else
               {'ablate_pocket_action_bias': True} if args.ablate_pocket_action_bias else {})
    result = (build_comparison(calibration_corpus=True, **options) if args.calibration_corpus
              else build_comparison(300 if args.fights is None else args.fights, **options))
    if args.output:
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
