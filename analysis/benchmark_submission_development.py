"""Paired whole-bout CPU profiling, including the new audit-context wrappers."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from analysis.fight_candidate_context import candidate_context


def sources():
    names = ['fight_engine.py', 'fight_engine_audit.py', 'analysis/fight_candidate_context.py',
             'analysis/submission_chain_candidate.py', 'analysis/cradle_setup_candidate.py',
             'analysis/benchmark_submission_development.py', 'tools/benchmark_move_selector.py']
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT / 'fight_moves').rglob('*.py')]
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}


def build_report():
    fingerprints, arms = sources(), {}
    for name, enabled in (('control', False), ('submission_development', True)):
        with candidate_context(entries=True, chains=True, draft_content=True, gift_wrap_mount=True,
                               heel_hook_identity=True, hold_transitions=enabled, cradle_setup=enabled):
            from tools import benchmark_move_selector
            arms[name] = benchmark_move_selector.benchmark()
    if sources() != fingerprints:
        raise RuntimeError('Sources changed during profiling')
    return dict(scope='800-move whole-bout CPU includes wrappers; selector-only shares exclude wrappers, '
                      'changed trajectories confound overhead; not whole-career speed acceptance',
                source_sha256=fingerprints, arms=arms,
                median_cpu_change_pct=100 * (arms['submission_development']['median_cpu_seconds'] /
                                            arms['control']['median_cpu_seconds'] - 1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = build_report()
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(report, output, indent=2)
    print(report['median_cpu_change_pct'])


if __name__ == '__main__':
    main()
