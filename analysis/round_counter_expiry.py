"""Audit-only removal of prior-round counter windows before initiative."""
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import random
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis import evaluate_joint_fight_candidate as evaluator
from analysis.compare_candidate_striking import fixture_schedule
from fight_engine_audit import FightAuditHarness
from tools.move_registry_parity import canonical_bytes


@contextmanager
def round_counter_trial(enabled=False):
    """Clear only proven prior-round windows, before either initiative score.

    The harness has no round-start state hook. The first initiative call is
    after round initialization and before any combat choice. No same-round
    age policy, ordinary production behavior or RNG draw is changed.
    """
    original, rng = FightAuditHarness.initiative, random.getstate()

    def adjusted(engine, fighter, opponent, state):
        window = state.get('counter_window') or {}
        created, current = window.get('created_round'), state.get('round')
        if (getattr(engine, '_experimental_specialist_entries', False)
                and getattr(engine, '_experimental_chain_action_weighting', False)
                and state.get('tick') == 1
                and type(created) is int and type(current) is int
                and 0 < created < current):
            state['counter_window'] = None
        return original(engine, fighter, opponent, state)

    adjusted._round_counter_expiry = True
    try:
        if enabled and not getattr(original, '_round_counter_expiry', False):
            with patch.object(FightAuditHarness, 'initiative', adjusted):
                yield
        else:
            yield
    finally:
        random.setstate(rng)


def build_report(coverage=False):
    """Retain full calibration groups or the unchanged five-arm coverage schedule."""
    rng = random.getstate()
    paths = [ROOT / name for name in (
        'fight_engine.py', 'fight_engine_audit.py', 'constants.py', 'models.py',
        'analysis/fight_candidate_context.py', 'analysis/evaluate_joint_fight_candidate.py',
        'analysis/compare_candidate_striking.py', 'analysis/round_counter_expiry.py',
        'analysis/generate_move_coverage_report.py', 'analysis/prepared_submission_diagnostics.py',
        'analysis/von_flue_angle_provenance.py')]
    paths += sorted((ROOT / 'fight_moves').rglob('*.py'))
    hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    reference = ROOT / 'analysis/fight_engine_baseline.json'
    reference_hash = hashlib.sha256(reference.read_bytes()).hexdigest()
    try:
        with round_counter_trial(True):
            result = evaluator.coverage_trial() if coverage else evaluator.calibration_trial()
        if hashlib.sha256(reference.read_bytes()).hexdigest() != reference_hash:
            raise RuntimeError('Calibration reference changed during trial')
        if not coverage and result['reference_sha256'] != reference_hash:
            raise RuntimeError('Calibration reference changed during trial')
        if any(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != value for name, value in hashes.items()):
            raise RuntimeError('Source changed during trial')
        result.update(scope='Audit-only round counter expiry; not release acceptance',
                      source_sha256=hashes, reference_sha256=reference_hash,
                      configuration={'combined_candidate_only': True, 'prior_round_only': True,
                                     'same_round_age_unchanged': True})
        if not coverage:
            result['input_schedule_sha256'] = hashlib.sha256(canonical_bytes(
                fixture_schedule(calibration_corpus=True))).hexdigest()
        return result
    finally:
        random.setstate(rng)


def report_failures(result):
    """Diagnostic process completion must not look like content acceptance."""
    failures = list(result.get('failures', []))
    for name, arm in result.get('arms', {}).items():
        for field in ('content_gate_failures', 'chain_gate_failures', 'measured_final_target_failures'):
            failures.extend(f'{name}: {failure}' for failure in arm.get(field, []))
    return failures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coverage', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError(args.output)
    result = build_report(args.coverage)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(result, output, indent=2)
    summary = {'failures': report_failures(result)}
    if 'overall' in result:
        summary['overall'] = result['overall']
    print(json.dumps(summary, indent=2))
    return int(bool(summary['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
