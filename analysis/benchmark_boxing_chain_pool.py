"""Count boxing preview work as well as named selection in the 800-move trial."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from analysis.fight_candidate_context import candidate_context


def sources():
    names = ['fight_engine.py', 'fight_engine_audit.py', 'analysis/fight_candidate_context.py',
             'analysis/boxing_chain_pool_candidate.py', 'analysis/gift_wrap_mount_candidate.py',
             'analysis/benchmark_boxing_chain_pool.py', 'tools/benchmark_move_selector.py', 'constants.py', 'models.py']
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT / 'fight_moves').rglob('*.py')]
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}


def preview_stats(stats):
    rows = [value for key, value in stats.stats.items()
            if Path(key[0]).resolve() == ROOT / 'analysis/boxing_chain_pool_candidate.py' and key[2] == 'boxing_pool']
    if len(rows) > 1:
        raise AssertionError('Ambiguous boxing preview profile')
    primitive, calls, own, cumulative, _ = rows[0] if rows else (0, 0, 0.0, 0.0, {})
    return dict(calls=calls, primitive_calls=primitive, self_seconds=own, cumulative_seconds=cumulative)


def build_report():
    fingerprints = sources()
    arms = {}
    for name, enabled in (('mount_control', False), ('boxing_pool_trial', True)):
        with candidate_context(entries=True, chains=True, draft_content=True, gift_wrap_mount=True,
                               boxing_chain_pool=enabled):
            from tools import benchmark_move_selector as benchmark
            original, previews = benchmark._function_stats, []
            def observed(stats, function):
                if function == 'select_exchange_move':
                    previews.append(preview_stats(stats))
                return original(stats, function)
            with patch.object(benchmark, '_function_stats', observed):
                report = benchmark.benchmark()
        for sample, preview in zip(report['samples'], previews):
            sample['boxing_preview'] = preview
            sample['selector_plus_preview_share_pct'] = 100 * (
                sample['selector']['cumulative_seconds'] + preview['cumulative_seconds']) / sample['simulation']['cumulative_seconds']
        assert len(previews) == len(report['samples']) == 3
        assert all((p['calls'] > 0) == enabled for p in previews)
        assert report['original_moves'] == 400 and report['profiled_moves'] == 800
        report['median_selector_plus_preview_share_pct'] = median(s['selector_plus_preview_share_pct'] for s in report['samples'])
        report['within_combined_15_percent_target'] = report['median_selector_plus_preview_share_pct'] <= 15
        arms[name] = report
    if sources() != fingerprints:
        raise AssertionError('Sources changed during benchmark')
    return dict(scope='800-move complete-fight profiling; includes added preview cost, not whole-career speed acceptance',
                source_sha256=fingerprints, arms=arms)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = build_report()
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(report, output, indent=2)
        output.write('\n')
    print(json.dumps({name: value['median_selector_plus_preview_share_pct'] for name, value in report['arms'].items()}))


if __name__ == '__main__':
    main()
